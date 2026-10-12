"""Evaluation: every backend on the labelled set of real CI failures, the raw answers and the full re-run policy.

Responses are replayed from `eval/cache/` so the numbers are reproducible offline (CI sets CI_TRIAGE_OFFLINE=1).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .backends import Backend, CacheMiss, get_backend
from .config import Config
from .metrics import accuracy, brier, macro_f1, percentile, prf, reliability
from .models import CATEGORIES, NOULS, RERUNNABLE, Decision, Failure
from .policy import apply_policy

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "eval" / "data"
CACHE = ROOT / "eval" / "cache"
THRESHOLDS = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
SAFE_GATES = (0.5, 0.6, 0.7, 0.8)
BACKEND_TITLES = {"jev": "Jev", "llm": "LLM (Gemini Flash-Lite)", "rules": "Regex rules"}


@dataclass
class Item:
    id: str
    failure: Failure
    gold: dict[str, Any]
    invented: bool


def load_items(data_dir: Path = DATA) -> list[Item]:
    labels = {}
    for line in (data_dir / "labels.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            labels[row["id"]] = row
    items = []
    for line in (data_dir / "failures.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        lab = labels[row["id"]]
        items.append(Item(row["id"], Failure.from_dict(row), lab["labels"], bool(row.get("invented"))))
    return items


def run_backend(backend: Backend, items: list[Item], progress: bool = False) -> dict[str, Decision]:
    """Decisions by item id. Items with no recorded response (offline) are left out."""
    out: dict[str, Decision] = {}
    for i, item in enumerate(items, 1):
        try:
            out[item.id] = backend.decide(item.failure)
        except CacheMiss:
            continue
        if progress and i % 25 == 0:
            print(f"  {backend.name}: {i}/{len(items)}", flush=True)
    return out


def policy_stats(items: list[Item], decisions: list[Decision], threshold: float, min_safe: float | None = None) -> dict[str, float]:
    """The re-run policy and the 'decided automatically' share at one category-confidence threshold."""
    cfg = Config()
    cfg.rerun.min_confidence = threshold
    cfg.needs_human_confidence = threshold
    if min_safe is not None:
        cfg.rerun.min_safe_to_rerun = min_safe
    n = len(items)
    reruns = wrong = 0
    auto = auto_right = 0
    for item, dec in zip(items, decisions, strict=True):
        f = item.failure
        out = apply_policy(f, dec, cfg)
        if out.rerun_eligible:
            reruns += 1
            wrong += item.gold["category"] not in RERUNNABLE
        if not out.needs_human:
            auto += 1
            auto_right += dec.category == item.gold["category"]
    gold_rerunnable = sum(1 for i in items if i.gold["category"] in RERUNNABLE)
    return {
        "threshold": threshold,
        "reruns": reruns,
        "right_reruns": reruns - wrong,
        "wrong_reruns": wrong,
        "rerun_recall": (reruns - wrong) / gold_rerunnable if gold_rerunnable else 0.0,
        "automated": auto,
        "automated_share": auto / n if n else 0.0,
        "automated_accuracy": auto_right / auto if auto else math.nan,
        "escalated": n - auto,
    }


def score_backend(items: list[Item], decisions: list[Decision]) -> dict[str, Any]:
    labels = list(CATEGORIES)
    gold = [i.gold["category"] for i in items]
    pred = [d.category for d in decisions]
    res: dict[str, Any] = {
        "model": decisions[0].model if decisions else "",
        "n": len(items),
        "category_accuracy": accuracy(gold, pred),
        "category_macro_f1": macro_f1(gold, pred, [c for c in labels if c in gold]),
        "per_category": {},
        "confusion": {g: {p: sum(1 for a, b in zip(gold, pred, strict=True) if a == g and b == p) for p in labels} for g in labels if g in gold},
        "urgency_accuracy": accuracy([i.gold["urgency"] for i in items], [d.urgency for d in decisions]),
        "urgency_mae": sum(abs(i.gold["urgency"] - d.urgency) for i, d in zip(items, decisions, strict=True)) / len(items),
        "nouls": {},
    }
    for c in labels:
        if c not in gold:
            continue
        p, r, f = prf([g == c for g in gold], [x == c for x in pred])
        res["per_category"][c] = {"n": gold.count(c), "precision": p, "recall": r, "f1": f}
    pooled_p: list[float] = []
    pooled_y: list[bool] = []
    for name in NOULS:
        y = [bool(i.gold[name]) for i in items]
        probs = [d.p(name) for d in decisions]
        p, r, f = prf(y, [x >= 0.5 for x in probs])
        res["nouls"][name] = {
            "accuracy": accuracy(y, [x >= 0.5 for x in probs]),
            "precision": p,
            "recall": r,
            "f1": f,
            "brier": brier(probs, y),
            "positives": sum(y),
        }
        pooled_p += probs
        pooled_y += y
    top = [max(d.answers["category"].probabilities.values()) for d in decisions]
    correct = [g == p for g, p in zip(gold, pred, strict=True)]
    res["category_brier"] = brier(top, correct)
    res["noul_brier"] = brier(pooled_p, pooled_y)
    res["reliability_category"] = reliability(top, correct, edges=(0.0, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0001))
    lat = [d.latency_ms for d in decisions]
    res["latency_p50_ms"] = percentile(lat, 0.5)
    res["latency_p95_ms"] = percentile(lat, 0.95)
    res["input_tokens_mean"] = sum(d.input_tokens for d in decisions) / len(decisions)
    res["output_tokens_mean"] = sum(d.output_tokens for d in decisions) / len(decisions)
    res["input_tokens_total"] = sum(d.input_tokens for d in decisions)
    res["output_tokens_total"] = sum(d.output_tokens for d in decisions)
    res["cost_per_1000_usd"] = 1000 * sum(d.cost_usd for d in decisions) / len(decisions)
    res["policy"] = [policy_stats(items, decisions, t) for t in THRESHOLDS]
    default = Config()
    res["policy_default"] = policy_stats(items, decisions, default.rerun.min_confidence)
    res["rerun_gate"] = [policy_stats(items, decisions, default.rerun.min_confidence, s) for s in SAFE_GATES]
    real = [k for k, i in enumerate(items) if not i.invented]
    res["real_only"] = {
        "n": len(real),
        "category_accuracy": accuracy([gold[k] for k in real], [pred[k] for k in real]),
        "category_macro_f1": macro_f1([gold[k] for k in real], [pred[k] for k in real], sorted({gold[k] for k in real})),
    }
    return res


def evaluate(backends: list[str], progress: bool = False) -> dict[str, Any]:
    items = load_items()
    out: dict[str, Any] = {
        "n": len(items),
        "invented": sum(i.invented for i in items),
        "label_counts": {c: sum(1 for i in items if i.gold["category"] == c) for c in CATEGORIES},
        "invented_counts": {c: sum(1 for i in items if i.invented and i.gold["category"] == c) for c in CATEGORIES},
        "repos": len({i.failure.repo for i in items if not i.invented}),
        "backends": {},
        "partial": {},
        "subset": None,
        "skipped": [],
    }
    runs: dict[str, dict[str, Decision]] = {}
    for name in backends:
        got = run_backend(get_backend(name, cache_dir=CACHE), items, progress)
        if not got:
            out["skipped"].append(name)
            continue
        runs[name] = got
        if len(got) == len(items):
            out["backends"][name] = score_backend(items, [got[i.id] for i in items])
        else:
            out["partial"][name] = len(got)
    if out["partial"]:
        common = [i for i in items if all(i.id in got for got in runs.values())]
        out["subset"] = {"n": len(common), "backends": {name: score_backend(common, [got[i.id] for i in common]) for name, got in runs.items()}}
    return out


def _pct(x: float) -> str:
    return "n/a" if isinstance(x, float) and math.isnan(x) else f"{100 * x:.1f}%"


def _lat(r: dict[str, Any], key: str) -> str:
    """Model latency comes from the recorded calls; the local regex rules take a few milliseconds, measured afresh each run."""
    return "under 20 ms (local)" if r["model"] == "regex-rules" else f"{r[key]:.0f} ms"


def _tables(b: dict[str, Any], h: str) -> list[str]:
    names = list(b)
    head = "| | " + " | ".join(BACKEND_TITLES.get(n, n) for n in names) + " |"
    sep = "|---|" + "---|" * len(names)

    def row(label: str, fn: Any) -> str:
        return f"| {label} | " + " | ".join(fn(b[n]) for n in names) + " |"

    d = Config().rerun
    lines = [
        f"{h} Headline",
        "",
        f"Default policy: re-run automatically only when the category is flaky test or infrastructure with confidence of at least {d.min_confidence}, "
        f"P(safe to re-run) is at least {d.min_safe_to_rerun} and P(caused by this commit) is below {d.max_caused_by_commit}. "
        "A *wrong* re-run is one whose gold category is anything else: a real failure that will fail again.",
        "",
        head,
        sep,
        row("Category accuracy", lambda r: _pct(r["category_accuracy"])),
        row("Category macro-F1", lambda r: f"{r['category_macro_f1']:.3f}"),
        row("Automatic re-runs (default policy)", lambda r: str(r["policy_default"]["reruns"])),
        row("**Wrong automatic re-runs** (real failures re-run)", lambda r: f"**{r['policy_default']['wrong_reruns']}**"),
        row("Flaky/infra failures re-run automatically (recall)", lambda r: _pct(r["policy_default"]["rerun_recall"])),
        row("Decided automatically (confidence >= 0.6)", lambda r: _pct(r["policy_default"]["automated_share"])),
        row("Accuracy on the automatic share", lambda r: _pct(r["policy_default"]["automated_accuracy"])),
        row("Brier score, category (lower is better)", lambda r: f"{r['category_brier']:.3f}"),
        row("Latency p50 / p95", lambda r: _lat(r, "latency_p50_ms") + " / " + _lat(r, "latency_p95_ms")),
        row("Cost per 1,000 failures", lambda r: f"${r['cost_per_1000_usd']:.4f}"),
        "",
        f"{h} Automation at different confidence thresholds",
        "",
        "The threshold is the minimum category confidence. Below it the failure is labelled `ci:needs-human` (escalated) and never re-run. "
        "The other re-run conditions stay at their defaults.",
        "",
    ]
    for n in names:
        lines += [
            f"**{BACKEND_TITLES.get(n, n)}**",
            "",
            "| Min confidence | Decided automatically | Accuracy on that share | Escalated | Auto re-runs | Wrong re-runs | Flaky/infra re-run |",
            "|---|---|---|---|---|---|---|",
        ]
        for p in b[n]["policy"]:
            lines.append(
                f"| {p['threshold']:.1f} | {p['automated']} ({_pct(p['automated_share'])}) | {_pct(p['automated_accuracy'])} | {p['escalated']} | "
                f"{p['reruns']} | {p['wrong_reruns']} | {_pct(p['rerun_recall'])} |"
            )
        lines.append("")
    lines += [
        f"{h} The re-run gate",
        "",
        "Same default policy, changing only the minimum P(safe to re-run). Lower gates re-run more of the flaky and infrastructure failures, "
        "at the risk of re-running real ones.",
        "",
        "| Min P(safe to re-run) | " + " | ".join(f"{BACKEND_TITLES.get(n, n)}: re-runs / wrong / flaky-infra recall" for n in names) + " |",
        "|---|" + "---|" * len(names),
    ]
    for k, gate in enumerate(SAFE_GATES):
        gate_cells = [
            f"{b[n]['rerun_gate'][k]['reruns']} / {b[n]['rerun_gate'][k]['wrong_reruns']} / {_pct(b[n]['rerun_gate'][k]['rerun_recall'])}" for n in names
        ]
        lines.append(f"| {gate:.1f}{' (default)' if gate == Config().rerun.min_safe_to_rerun else ''} | " + " | ".join(gate_cells) + " |")
    lines += ["", f"{h} Per category (F1)", "", "| Category (gold count) | " + " | ".join(BACKEND_TITLES.get(n, n) for n in names) + " |", sep]
    for c in b[names[0]]["per_category"]:
        lines.append(
            f"| {c.replace('_', ' ')} ({b[names[0]]['per_category'][c]['n']}) | "
            + " | ".join(
                f"{b[n]['per_category'][c]['f1']:.2f} (P {b[n]['per_category'][c]['precision']:.2f}, R {b[n]['per_category'][c]['recall']:.2f})" for n in names
            )
            + " |"
        )
    lines += ["", f"{h} The yes/no questions and urgency", "", head, sep]
    for name in NOULS:
        lines.append(
            row(
                f"`{name}` accuracy / F1 / Brier",
                lambda r, nm=name: f"{_pct(r['nouls'][nm]['accuracy'])} / {r['nouls'][nm]['f1']:.3f} / {r['nouls'][nm]['brier']:.3f}",
            )
        )
    lines += [
        row("Urgency exact accuracy", lambda r: _pct(r["urgency_accuracy"])),
        row("Urgency mean absolute error", lambda r: f"{r['urgency_mae']:.2f}"),
        row(
            "Real excerpts only: category accuracy / macro-F1",
            lambda r: f"{_pct(r['real_only']['category_accuracy'])} / {r['real_only']['category_macro_f1']:.3f}",
        ),
        "",
        f"{h} Calibration",
        "",
        "Brier score: the mean squared gap between the stated probability and what was true (lower is better).",
        "",
        head,
        sep,
        row("Brier, category (top probability vs correct)", lambda r: f"{r['category_brier']:.3f}"),
        row("Brier, the three yes/no questions pooled", lambda r: f"{r['noul_brier']:.3f}"),
        "",
        "Reliability of the category answer: stated top probability vs how often it was right.",
        "",
        "| Bin | " + " | ".join(f"{BACKEND_TITLES.get(n, n)} (n, stated, observed)" for n in names) + " |",
        "|---|" + "---|" * len(names),
    ]
    for k in range(len(b[names[0]]["reliability_category"])):
        cells: list[str] = []
        for n in names:
            _, cnt, stated, obs = b[n]["reliability_category"][k]
            cells.append("-" if cnt == 0 else f"{cnt}, {stated:.2f}, {obs:.2f}")
        lines.append(f"| {b[names[0]]['reliability_category'][k][0]} | " + " | ".join(cells) + " |")
    lines += [
        "",
        f"{h} Confusion (rows: gold, columns: predicted)",
        "",
    ]
    short = {c: c.split("_")[0][:5] for c in CATEGORIES}
    for n in names:
        conf = b[n]["confusion"]
        lines += [
            f"**{BACKEND_TITLES.get(n, n)}**",
            "",
            "| gold \\ predicted | " + " | ".join(short[c] for c in CATEGORIES) + " |",
            "|---|" + "---|" * len(CATEGORIES),
        ]
        lines += [f"| {g} | " + " | ".join(str(conf[g][p]) for p in CATEGORIES) + " |" for g in conf]
        lines.append("")
    lines += [
        f"{h} Speed and cost",
        "",
        head,
        sep,
        row("Latency p50", lambda r: _lat(r, "latency_p50_ms")),
        row("Latency p95", lambda r: _lat(r, "latency_p95_ms")),
        row("Input tokens per failure (mean)", lambda r: f"{r['input_tokens_mean']:.0f}"),
        row("Output tokens per failure (mean)", lambda r: f"{r['output_tokens_mean']:.0f}"),
        row("Cost per 1,000 failures", lambda r: f"${r['cost_per_1000_usd']:.4f}"),
        "",
    ]
    return lines


def render_markdown(res: dict[str, Any]) -> str:
    lc = res["label_counts"]
    real = res["n"] - res["invented"]
    lines = [
        "# Evaluation results",
        "",
        f"{res['n']} CI failure excerpts: {real} real failed jobs from public GitHub Actions runs of {res['repos']} MIT or Apache-2.0 repositories, "
        f"and {res['invented']} invented excerpts ({100 * res['invented'] / res['n']:.1f}%) for categories that are rare in public logs "
        "(marked `invented` in the data). Labelled by the rules in [LABELLING.md](LABELLING.md).",
        "",
        "Gold categories: "
        + ", ".join(f"{k.replace('_', ' ')} {v}" + (f" ({res['invented_counts'][k]} invented)" if res["invented_counts"][k] else "") for k, v in lc.items())
        + ".",
        "",
        "Every number below comes from recorded real API responses (`eval/cache/`), replayed by `ci-triage eval`.",
        "",
    ]
    if res["backends"]:
        names = ", ".join(BACKEND_TITLES.get(n, n) for n in res["backends"])
        lines += [f"## All {res['n']} failures: {names}", ""]
        lines += _tables(res["backends"], "###")
    if res.get("subset"):
        sub = res["subset"]
        partial = ", ".join(f"{BACKEND_TITLES.get(n, n)} answered {k} of the {res['n']} failures" for n, k in res["partial"].items())
        lines += [
            f"## All backends on the {sub['n']} failures every backend answered",
            "",
            f"{partial} (the free-tier request quota of its API), so this section compares every backend on the same {sub['n']} failures.",
            "They are the first items of the data file, so they are not balanced: "
            + ", ".join(f"{c.replace('_', ' ')} {v['n']}" for c, v in next(iter(sub["backends"].values()))["per_category"].items())
            + ". Re-run numbers on this subset say little, because it holds almost no flaky or infrastructure failures.",
            "",
        ]
        lines += _tables(sub["backends"], "###")
    lines += [
        "Jev pricing: $0.042 per million input tokens, output free. The LLM cost uses an assumed list price of $0.10 / $0.40 per million input / output tokens",
        "for the default model (the evaluation ran on a free tier). The regex baseline makes no API call.",
    ]
    if res["skipped"]:
        lines += ["", f"Not run (no cached responses and no key): {', '.join(res['skipped'])}."]
    return "\n".join(lines) + "\n"


def write_results(res: dict[str, Any], out_dir: Path = ROOT / "eval") -> Path:
    (out_dir / "results.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    path = out_dir / "results.md"
    path.write_text(render_markdown(res), encoding="utf-8", newline="\n")
    return path
