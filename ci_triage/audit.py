"""Append-only JSONL audit log: one line per triaged job, with what was asked, answered and done."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from .comment import JobVerdict


def audit_record(v: JobVerdict, run_action: str, actions: list[str], dry_run: bool) -> dict[str, object]:
    f, d, o = v.failure, v.decision, v.outcome
    return {
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "repo": f.repo,
        "run_id": f.run_id,
        "run_attempt": f.run_attempt,
        "job": f.job_name,
        "branch": f.branch,
        "event": f.event,
        "head_sha": f.head_sha,
        "pr": f.pr_number,
        "failing_tests": f.failing_tests,
        "backend": d.backend,
        "model": d.model,
        "answers": {k: {"value": a.value, "confidence": round(a.confidence, 4)} for k, a in d.answers.items()},
        "category": o.category,
        "rerun_eligible": o.rerun_eligible,
        "needs_human": o.needs_human,
        "reasons": o.reasons,
        "run_action": run_action,
        "actions": actions,
        "suggestion": bool(v.suggestion),
        "latency_ms": round(d.latency_ms, 1),
        "input_tokens": d.input_tokens,
        "cost_usd": round(d.cost_usd, 8),
        "redactions": d.redactions,
        "dry_run": dry_run,
    }


def write_audit(path: str | Path, record: dict[str, object]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
