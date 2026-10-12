"""A small SQLite store: every triaged failure, the daily re-run count, and the weekly flaky-test report."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS failures (
    ts TEXT NOT NULL, repo TEXT NOT NULL, run_id INTEGER, job TEXT, test TEXT, category TEXT,
    branch TEXT, confidence REAL, rerun INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS failures_repo_ts ON failures (repo, ts);
CREATE TABLE IF NOT EXISTS reruns (day TEXT NOT NULL, repo TEXT NOT NULL, count INTEGER NOT NULL, PRIMARY KEY (day, repo));
"""


@dataclass
class FlakyRow:
    repo: str
    test: str
    failures: int
    reruns: int
    last_seen: str


class Store:
    def __init__(self, path: str | Path) -> None:
        p = Path(path)
        if str(p) != ":memory:":
            p.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(p))
        self.db.executescript(SCHEMA)

    def close(self) -> None:
        self.db.close()

    def record(
        self, repo: str, run_id: int, job: str, tests: list[str], category: str, branch: str, confidence: float, rerun: bool, ts: datetime | None = None
    ) -> None:
        stamp = (ts or datetime.now(UTC)).isoformat(timespec="seconds")
        for test in tests or [job]:
            self.db.execute(
                "INSERT INTO failures (ts, repo, run_id, job, test, category, branch, confidence, rerun) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (stamp, repo, run_id, job, test, category, branch, confidence, int(rerun)),
            )
        self.db.commit()

    def reruns_today(self, repo: str, now: datetime | None = None) -> int:
        day = (now or datetime.now(UTC)).date().isoformat()
        row = self.db.execute("SELECT count FROM reruns WHERE day = ? AND repo = ?", (day, repo)).fetchone()
        return int(row[0]) if row else 0

    def add_rerun(self, repo: str, now: datetime | None = None) -> int:
        day = (now or datetime.now(UTC)).date().isoformat()
        self.db.execute(
            "INSERT INTO reruns (day, repo, count) VALUES (?, ?, 1) ON CONFLICT(day, repo) DO UPDATE SET count = count + 1",
            (day, repo),
        )
        self.db.commit()
        return self.reruns_today(repo, now)

    def top_flaky(self, days: int = 7, limit: int = 10, now: datetime | None = None) -> list[FlakyRow]:
        since = ((now or datetime.now(UTC)) - timedelta(days=days)).isoformat(timespec="seconds")
        rows = self.db.execute(
            """SELECT repo, test, COUNT(*), SUM(rerun), MAX(ts) FROM failures
               WHERE category = 'flaky_test' AND ts >= ? GROUP BY repo, test ORDER BY COUNT(*) DESC, MAX(ts) DESC LIMIT ?""",
            (since, limit),
        ).fetchall()
        return [FlakyRow(r[0], r[1], int(r[2]), int(r[3] or 0), r[4]) for r in rows]

    def category_counts(self, days: int = 7, now: datetime | None = None) -> dict[str, int]:
        since = ((now or datetime.now(UTC)) - timedelta(days=days)).isoformat(timespec="seconds")
        rows = self.db.execute(
            "SELECT category, COUNT(DISTINCT run_id || '/' || job) FROM failures WHERE ts >= ? GROUP BY category ORDER BY 2 DESC", (since,)
        ).fetchall()
        return {r[0]: int(r[1]) for r in rows}


def weekly_report(store: Store, days: int = 7, top: int = 10, now: datetime | None = None) -> str:
    """Markdown: failures by category and the most frequent flaky tests over the last `days` days."""
    counts = store.category_counts(days, now)
    flaky = store.top_flaky(days, top, now)
    lines = [f"## CI failures in the last {days} days", ""]
    if not counts:
        return "\n".join([*lines, "No failures recorded.", ""])
    lines += ["| Category | Failed jobs |", "|---|---|"]
    lines += [f"| {c.replace('_', ' ')} | {n} |" for c, n in counts.items()]
    lines += ["", f"## Top {top} flaky tests", ""]
    if not flaky:
        lines.append("No flaky tests recorded.")
    else:
        lines += ["| Test | Repository | Flaky failures | Auto re-runs | Last seen |", "|---|---|---|---|---|"]
        lines += [f"| `{r.test}` | {r.repo} | {r.failures} | {r.reruns} | {r.last_seen[:10]} |" for r in flaky]
    return "\n".join(lines) + "\n"
