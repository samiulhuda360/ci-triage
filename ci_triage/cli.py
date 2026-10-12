"""Command line: `ci-triage check`, `action`, `serve`, `report`, `eval`."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .backends import BackendError, get_backend
from .comment import render_comment
from .config import load_config
from .github import GitHub
from .models import Failure
from .store import Store, weekly_report
from .triage import judge, triage_run


def cmd_check(args: argparse.Namespace) -> int:
    """Triage one failed job described in a JSON file (no GitHub needed; nothing is changed)."""
    data = json.loads(Path(args.failure).read_text(encoding="utf-8"))
    failure = Failure.from_dict(data)
    cfg = load_config(args.config)
    if args.suggest:
        cfg.suggest.enabled = True
    backend = get_backend(args.backend or cfg.backend, cache_dir=Path(args.cache) if args.cache else None)
    action, verdicts = judge([failure], cfg, backend, cache_dir=Path(args.cache) if args.cache else None)
    if args.json:
        v = verdicts[0]
        print(
            json.dumps(
                {
                    "action": action,
                    "category": v.outcome.category,
                    "labels": v.outcome.labels,
                    "reasons": v.outcome.reasons,
                    "answers": {k: {"value": a.value, "confidence": round(a.confidence, 3)} for k, a in v.decision.answers.items()},
                    "backend": v.decision.backend,
                    "model": v.decision.model,
                    "latency_ms": v.decision.latency_ms,
                },
                indent=1,
            )
        )
    else:
        comment = render_comment(verdicts, action, dry_run=True, n_lines=cfg.key_lines)
        print(comment)
        if args.out:
            Path(args.out).write_text(comment, encoding="utf-8", newline="\n")
    return 0


def _event_run() -> tuple[str, int]:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path:
        raise SystemExit("GITHUB_EVENT_PATH is not set: run this inside GitHub Actions or pass --repo and --run-id")
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    run = event.get("workflow_run") or {}
    if not run.get("id"):
        raise SystemExit("this event is not a workflow_run event")
    return repo, int(run["id"])


def cmd_action(args: argparse.Namespace) -> int:
    """GitHub Actions entry point: triage the failed workflow run that triggered this one."""
    repo, run_id = (args.repo, args.run_id) if args.repo and args.run_id else _event_run()
    cfg = load_config(args.config)
    cfg.backend = os.environ.get("CI_TRIAGE_BACKEND") or cfg.backend
    dry = args.dry_run or cfg.dry_run
    store = Store(args.store or cfg.flaky.store)
    try:
        result = triage_run(GitHub(), repo, run_id, cfg, get_backend(cfg.backend), store, dry_run=dry)
    except BackendError as exc:
        print(f"ci-triage: no decision ({exc}). Leaving the run for a person.")
        return 0
    finally:
        store.close()
    if result.comment:
        print(result.comment)
    print(f"ci-triage: {result.action} ({'dry run, nothing changed' if dry else f'{len(result.actions)} actions'}):")
    for line in result.actions:
        print(f"- {line}")
    output = os.environ.get("GITHUB_OUTPUT")
    if output and result.verdicts:
        with open(output, "a", encoding="utf-8") as fh:
            fh.write(f"action={result.action}\ncategory={result.verdicts[0].outcome.category}\n")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .server import serve

    serve(args.host, args.port)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """The weekly flaky-test report from the store."""
    cfg = load_config(args.config)
    store = Store(args.store or cfg.flaky.store)
    text = weekly_report(store, args.days or cfg.flaky.report_days, args.top or cfg.flaky.report_top)
    store.close()
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    from .evaluate import evaluate, write_results

    res = evaluate([b.strip() for b in args.backends.split(",") if b.strip()], progress=True)
    path = write_results(res)
    groups = [(f"all {res['n']} failures", res["backends"])]
    if res.get("subset"):
        groups.append((f"the {res['subset']['n']} failures every backend answered", res["subset"]["backends"]))
    for label, backends in groups:
        print(f"On {label}:")
        for name, r in backends.items():
            d = r["policy_default"]
            print(
                f"  {name:6s} category acc {r['category_accuracy']:.3f}  macro-F1 {r['category_macro_f1']:.3f}  "
                f"auto re-runs {d['reruns']} (wrong {d['wrong_reruns']})  automated {d['automated_share']:.1%} at {d['automated_accuracy']:.1%} acc  "
                f"p50 {r['latency_p50_ms']:.0f} ms  ${r['cost_per_1000_usd']:.4f}/1k"
            )
    if res["skipped"]:
        print("skipped (no cache, no key):", ", ".join(res["skipped"]))
    print(f"wrote {path.as_posix()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="ci-triage", description="Reads a failed CI run and says what kind of failure it is and what to do.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="triage one failed job from a JSON file (always a dry run)")
    c.add_argument("failure")
    c.add_argument("--backend", choices=["auto", "jev", "llm", "rules"])
    c.add_argument("--config", default=None, help="policy file (default .github/ci-triage.yml)")
    c.add_argument("--cache", help="replay/record model responses in this folder")
    c.add_argument("--suggest", action="store_true", help="add the optional LLM fix suggestion")
    c.add_argument("--json", action="store_true")
    c.add_argument("--out", help="also write the comment Markdown here")
    c.set_defaults(func=cmd_check)

    a = sub.add_parser("action", help="GitHub Actions entry point (workflow_run event)")
    a.add_argument("--config", default=None)
    a.add_argument("--dry-run", action="store_true")
    a.add_argument("--repo")
    a.add_argument("--run-id", type=int)
    a.add_argument("--store", help="SQLite store (default from the policy)")
    a.set_defaults(func=cmd_action)

    s = sub.add_parser("serve", help="run the webhook service")
    s.add_argument("--host", default="0.0.0.0")  # noqa: S104
    s.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    s.set_defaults(func=cmd_serve)

    r = sub.add_parser("report", help="weekly report: failures by category and the top flaky tests")
    r.add_argument("--config", default=None)
    r.add_argument("--store")
    r.add_argument("--days", type=int)
    r.add_argument("--top", type=int)
    r.add_argument("--out")
    r.set_defaults(func=cmd_report)

    e = sub.add_parser("eval", help="evaluate the backends on the labelled set")
    e.add_argument("--backends", default="rules,jev,llm")
    e.set_defaults(func=cmd_eval)

    args = ap.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
