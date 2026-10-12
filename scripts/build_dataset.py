"""Builds eval/data/ from the harvested candidates, the labeller's sheet and the invented excerpts.

    python scripts/build_dataset.py --candidates "tmp/cand*.jsonl" --enriched tmp/enriched.jsonl \
        --labels tmp/labels_sheet.txt --invented eval/data/invented.jsonl

The labels sheet has one line per selected item: `id | category | overrides | note`. The three yes/no labels and
the urgency follow the rules in eval/LABELLING.md from the category, the branch and the event; `overrides`
(for example `caused=0 urg=1`) records the cases where the labeller departed from those rules.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "eval" / "data"
CATEGORIES = ["flaky_test", "test_failure", "compile_error", "lint_format", "dependency", "infrastructure", "configuration", "unknown"]
RERUNNABLE = {"flaky_test", "infrastructure"}
CODE = {"test_failure", "compile_error", "lint_format", "dependency"}
HIGH_EVENTS = {"push", "schedule", "workflow_dispatch", "merge_group"}
KEEP = [
    "id",
    "repo",
    "license",
    "kind",
    "run_url",
    "job_url",
    "run_attempt",
    "workflow",
    "job_name",
    "failed_step",
    "event",
    "branch",
    "default_branch",
    "head_sha",
    "commit_message",
    "created_at",
    "changed_files",
    "changed_files_total",
    "default_branch_history",
    "failing_tests",
    "excerpt",
]


def high_branch(row: dict[str, Any]) -> bool:
    if row.get("event") not in HIGH_EVENTS:
        return False
    branch = row.get("branch") or ""
    return branch == row.get("default_branch") or row.get("event") in ("schedule", "merge_group") or bool(re.match(r"(release|v\d)", branch))


def gold(row: dict[str, Any], category: str, overrides: dict[str, int]) -> dict[str, Any]:
    labels: dict[str, Any] = {
        "category": category,
        "caused_by_commit": category in CODE,
        "safe_to_rerun": category in RERUNNABLE,
        "needs_code_change": category in CODE,
        "urgency": 0 if category in RERUNNABLE else (2 if high_branch(row) else 1),
    }
    names = {"caused": "caused_by_commit", "rerun": "safe_to_rerun", "code": "needs_code_change", "urg": "urgency"}
    for key, value in overrides.items():
        target = names[key]
        labels[target] = value if target == "urgency" else bool(value)
    return labels


def parse_sheet(path: Path) -> list[tuple[str, str, dict[str, int], str]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        item_id, category, overrides, note = (part.strip() for part in line.split("|", 3))
        if category not in CATEGORIES:
            raise SystemExit(f"{item_id}: unknown category {category!r}")
        ov = {k: int(v) for k, v in (pair.split("=") for pair in overrides.split())}
        out.append((item_id, category, ov, note))
    return out


def failed_step(row: dict[str, Any]) -> str:
    steps = row.get("failed_steps") or []
    return str(steps[0]) if steps else str(row.get("failed_step", ""))


def write_sources(rows: list[dict[str, Any]], invented: int) -> None:
    by_repo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_repo[r["repo"]].append(r)
    lines = [
        "# Data sources",
        "",
        f"`failures.jsonl` holds {len(rows)} real failed jobs from public GitHub Actions runs of {len(by_repo)} repositories licensed",
        "MIT or Apache-2.0 (the licence GitHub reports for each repository), and "
        f'{invented} invented excerpts marked `"invented": true`. Each real record links to its run and job (`run_url`, `job_url`).',
        "Logs were fetched with `gh api` (`scripts/harvest.py`), trimmed to the region around the first failure by",
        "`ci_triage/logs.py` and passed through the secret and e-mail redactor in `ci_triage/redact.py` before being stored.",
        "Excerpts are quoted unchanged apart from trimming and redaction, under each project's licence.",
        "",
        "| Repository | Licence | Failed jobs |",
        "|---|---|---|",
    ]
    for repo in sorted(by_repo, key=str.lower):
        lines.append(f"| [{repo}](https://github.com/{repo}) | {by_repo[repo][0]['license']} | {len(by_repo[repo])} |")
    lines += ["", "## Runs", ""]
    for repo in sorted(by_repo, key=str.lower):
        for r in sorted(by_repo[repo], key=lambda x: x["id"]):
            lines.append(f"- `{r['id']}`: [run]({r['run_url']}), [job]({r['job_url']}) ({r['license']})")
    (DATA / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True, help="glob of harvested candidate files")
    ap.add_argument("--enriched", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--invented", type=Path, default=DATA / "invented.jsonl")
    a = ap.parse_args()
    cands: dict[str, dict[str, Any]] = {}
    for f in glob.glob(a.candidates):
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                cands.setdefault(row["id"], row)
    enriched = {json.loads(line)["id"]: json.loads(line) for line in a.enriched.read_text(encoding="utf-8").splitlines() if line.strip()}
    rows: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    for item_id, category, overrides, note in parse_sheet(a.labels):
        src = enriched.get(item_id) or cands[item_id]
        row = {k: src.get(k) for k in KEEP}
        row["failed_step"] = failed_step(src)
        row.setdefault("changed_files", [])
        row["changed_files"] = row["changed_files"] or []
        row["changed_files_total"] = row["changed_files_total"] or 0
        row["default_branch_history"] = row["default_branch_history"] or {"runs_checked": 0, "job_failed": 0}
        if row["kind"] == "rerun_passed":
            row["run_attempt"] = 1  # the failed job comes from the first attempt of a run that later passed
        row["invented"] = False
        rows.append(row)
        labels.append({"id": item_id, "labels": gold(row, category, overrides), "overrides": overrides, "note": note})
    invented_rows = [json.loads(line) for line in a.invented.read_text(encoding="utf-8").splitlines() if line.strip()] if a.invented.exists() else []
    for inv in invented_rows:
        lab = inv.pop("label")
        inv["invented"] = True
        rows.append(inv)
        ov = lab.get("overrides", {})
        labels.append({"id": inv["id"], "labels": gold(inv, lab["category"], ov), "overrides": ov, "note": lab.get("note", "invented")})
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / "failures.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (DATA / "labels.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for lab in labels:
            fh.write(json.dumps(lab, ensure_ascii=False) + "\n")
    write_sources([r for r in rows if not r["invented"]], len(invented_rows))
    counts = Counter(lab["labels"]["category"] for lab in labels)
    print(f"{len(rows)} items ({len(invented_rows)} invented):", dict(counts))


if __name__ == "__main__":
    main()
