"""The weekly flaky-test report, built from the evaluation set.

Every real failure in eval/data/ is recorded in a fresh store at the time it happened, with the category Jev gave it
(replayed from eval/cache/, no API call) and whether the default policy would have re-run it. Then the report covers
the last 14 days of that data.

    python scripts/demo_report.py
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ci_triage.backends import JevBackend
from ci_triage.config import Config
from ci_triage.evaluate import CACHE, load_items
from ci_triage.policy import apply_policy
from ci_triage.store import Store, weekly_report


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    import json

    created = {}
    for line in (ROOT / "eval" / "data" / "failures.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("created_at"):
            created[row["id"]] = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
    backend = JevBackend(cache_path=CACHE / "jev.jsonl")
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / "flaky.db")
        for item in load_items():
            if item.id not in created:
                continue
            d = backend.decide(item.failure)
            out = apply_policy(item.failure, d, Config())
            f = item.failure
            store.record(
                f.repo, f.run_id, f.job_name, f.failing_tests[:3], d.category, f.branch, d.category_confidence, out.rerun_eligible, ts=created[item.id]
            )
        now = max(created.values())
        text = weekly_report(store, days=14, top=8, now=now)
        store.close()
    print(text)
    out_path = ROOT / "docs" / "build" / "weekly-report.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
