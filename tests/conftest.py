from __future__ import annotations

import pytest

from ci_triage.backends.base import choice_confidence, noul_confidence, score_confidence
from ci_triage.models import CATEGORIES, Answer, Decision, Failure

PYTEST_LOG = """2026-10-01T10:00:00.0000000Z ##[group]Run actions/checkout@v4
2026-10-01T10:00:01.0000000Z Syncing repository: acme/orders
2026-10-01T10:00:02.0000000Z ##[endgroup]
2026-10-01T10:00:03.0000000Z ##[group]Run pytest -q
2026-10-01T10:00:03.1000000Z pytest -q
2026-10-01T10:00:03.2000000Z shell: /usr/bin/bash -e {0}
2026-10-01T10:00:03.3000000Z ##[endgroup]
2026-10-01T10:00:09.0000000Z ........F...
2026-10-01T10:00:09.1000000Z =================================== FAILURES ===================================
2026-10-01T10:00:09.2000000Z ____________________________ test_refund_total _____________________________
2026-10-01T10:00:09.3000000Z     def test_refund_total():
2026-10-01T10:00:09.4000000Z >       assert refund_total([10, 5]) == 15
2026-10-01T10:00:09.5000000Z E       assert 14 == 15
2026-10-01T10:00:09.6000000Z tests/test_refunds.py:12: AssertionError
2026-10-01T10:00:09.7000000Z =========================== short test summary info ============================
2026-10-01T10:00:09.8000000Z FAILED tests/test_refunds.py::test_refund_total - assert 14 == 15
2026-10-01T10:00:09.9000000Z 1 failed, 11 passed in 5.80s
2026-10-01T10:00:10.0000000Z ##[error]Process completed with exit code 1.
2026-10-01T10:00:11.0000000Z ##[group]Run actions/upload-artifact@v4
2026-10-01T10:00:12.0000000Z Post job cleanup.
"""


def make_decision(category: str = "flaky_test", top: float = 0.9, urgency: int = 0, **nouls: float) -> Decision:
    others = [c for c in CATEGORIES if c != category]
    cprobs = {category: top, **{c: (1 - top) / len(others) for c in others}}
    uprobs = [0.9 if i == urgency else 0.05 for i in range(3)]
    answers = {
        "category": Answer("choice", category, choice_confidence(cprobs), cprobs),
        "urgency": Answer("score", urgency, score_confidence(uprobs), {str(i): p for i, p in enumerate(uprobs)}),
    }
    defaults = {"caused_by_commit": 0.1, "safe_to_rerun": 0.9, "needs_code_change": 0.1}
    defaults.update(nouls)
    for name, p in defaults.items():
        answers[name] = Answer("noul", p, noul_confidence(p), {"yes": p, "no": 1 - p})
    return Decision(backend="fake", model="fake-1", answers=answers, latency_ms=10.0)


class FakeBackend:
    name = "fake"
    model = "fake-1"

    def __init__(self, decision: Decision) -> None:
        self.decision = decision
        self.seen: list[Failure] = []

    def decide(self, failure: Failure) -> Decision:
        self.seen.append(failure)
        return self.decision


@pytest.fixture
def failure() -> Failure:
    return Failure(
        job_name="test (3.12)",
        excerpt="[step] pytest -q\nFAILED tests/test_refunds.py::test_refund_total - assert 14 == 15\n##[error]Process completed with exit code 1.",
        repo="acme/orders",
        workflow="CI",
        failed_step="Run tests",
        event="pull_request",
        branch="fix-refunds",
        default_branch="main",
        head_sha="abc123",
        commit_message="Round refunds to cents",
        changed_files=["orders/refunds.py"],
        changed_files_total=1,
        failing_tests=["tests/test_refunds.py::test_refund_total"],
        run_id=42,
        run_attempt=1,
        pr_number=7,
    )
