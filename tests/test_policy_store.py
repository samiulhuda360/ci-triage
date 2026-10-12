from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ci_triage.comment import MARKER, JobVerdict, render_comment
from ci_triage.config import Config, load_config
from ci_triage.models import Failure
from ci_triage.policy import apply_policy, run_action
from ci_triage.store import Store, weekly_report

from .conftest import make_decision


def test_flaky_and_confident_is_rerun(failure: Failure) -> None:
    out = apply_policy(failure, make_decision("flaky_test", 0.9), Config())
    assert out.action == "rerun" and out.rerun_eligible
    assert out.labels == ["ci:flaky-test", "ci:auto-rerun"]
    assert not out.needs_human and not out.notify


@pytest.mark.parametrize(
    ("decision", "blocker"),
    [
        (make_decision("test_failure", 0.9, caused_by_commit=0.9, safe_to_rerun=0.05), "category is test failure"),
        (make_decision("flaky_test", 0.3), "category confidence"),
        (make_decision("infrastructure", 0.9, safe_to_rerun=0.4), "P(re-run passes)"),
        (make_decision("flaky_test", 0.9, caused_by_commit=0.6), "P(caused by this commit)"),
    ],
)
def test_rerun_blockers(failure: Failure, decision, blocker: str) -> None:  # type: ignore[no-untyped-def]
    out = apply_policy(failure, decision, Config())
    assert out.action == "report" and not out.rerun_eligible
    assert any(blocker in r for r in out.reasons), out.reasons


def test_rerun_only_once_and_daily_cap(failure: Failure) -> None:
    d = make_decision("flaky_test", 0.9)
    failure.run_attempt = 2
    assert not apply_policy(failure, d, Config()).rerun_eligible
    failure.run_attempt = 1
    cfg = Config()
    cfg.rerun.max_per_day = 3
    assert apply_policy(failure, d, cfg, reruns_today=2).rerun_eligible
    out = apply_policy(failure, d, cfg, reruns_today=3)
    assert not out.rerun_eligible and "daily re-run cap" in out.reasons[0]


def test_needs_human_and_notify_on_default_branch(failure: Failure) -> None:
    out = apply_policy(failure, make_decision("unknown", 0.3, urgency=1), Config())
    assert out.needs_human and "ci:needs-human" in out.labels
    failure.event, failure.branch = "push", "main"
    out = apply_policy(failure, make_decision("compile_error", 0.9, urgency=2, caused_by_commit=0.9, safe_to_rerun=0.05), Config())
    assert out.notify and out.urgency == 2


def test_run_is_rerun_only_when_every_job_qualifies(failure: Failure) -> None:
    flaky = apply_policy(failure, make_decision("flaky_test", 0.9), Config())
    real = apply_policy(failure, make_decision("test_failure", 0.9, caused_by_commit=0.9, safe_to_rerun=0.05), Config())
    assert run_action([flaky, flaky]) == "rerun"
    assert run_action([flaky, real]) == "report"
    assert run_action([]) == "report"


def test_config_file_and_unknown_keys(tmp_path: Path) -> None:
    p = tmp_path / "ci-triage.yml"
    p.write_text("rerun:\n  min_confidence: 0.8\n  max_per_day: 2\nlabels:\n  prefix: 'triage/'\ndry_run: true\n", encoding="utf-8")
    cfg = load_config(p)
    assert cfg.rerun.min_confidence == 0.8 and cfg.rerun.max_per_day == 2 and cfg.labels.prefix == "triage/" and cfg.dry_run
    assert load_config(tmp_path / "missing.yml").rerun.min_confidence == Config().rerun.min_confidence
    with pytest.raises(ValueError, match=r"rerun\.nope"):
        load_config(text="rerun:\n  nope: 1\n")
    with pytest.raises(ValueError, match="unknown keys"):
        load_config(text="reruns: {}\n")


def test_comment_has_category_lines_and_next_step(failure: Failure) -> None:
    d = make_decision("test_failure", 0.9, caused_by_commit=0.9, safe_to_rerun=0.05, needs_code_change=0.95)
    out = apply_policy(failure, d, Config())
    text = render_comment([JobVerdict(failure, d, out, suggestion="Check the rounding in refunds.py.")], "report")
    assert text.startswith(MARKER)
    assert "Test failure" in text and "FAILED tests/test_refunds.py" in text
    assert "Next step:" in text and "AI-generated suggestion" in text
    assert "Caused by this commit:** 90%" in text


def test_store_counts_reruns_and_reports_flaky_tests(tmp_path: Path) -> None:
    store = Store(tmp_path / "flaky.db")
    now = datetime(2026, 10, 12, 12, tzinfo=UTC)
    for day in range(3):
        store.record("acme/web", 100 + day, "e2e", ["checkout.spec.ts > pays"], "flaky_test", "main", 0.9, rerun=True, ts=now - timedelta(days=day))
    store.record("acme/web", 200, "e2e", ["login.spec.ts > logs in"], "flaky_test", "pr-1", 0.8, rerun=False, ts=now)
    store.record("acme/web", 201, "lint", [], "lint_format", "pr-2", 0.9, rerun=False, ts=now)
    store.record("acme/web", 300, "e2e", ["old.spec.ts"], "flaky_test", "main", 0.9, rerun=False, ts=now - timedelta(days=30))
    top = store.top_flaky(7, 10, now)
    assert [(r.test, r.failures, r.reruns) for r in top] == [("checkout.spec.ts > pays", 3, 3), ("login.spec.ts > logs in", 1, 0)]
    assert store.category_counts(7, now) == {"flaky_test": 4, "lint_format": 1}
    assert store.reruns_today("acme/web", now) == 0
    assert store.add_rerun("acme/web", now) == 1 and store.add_rerun("acme/web", now) == 2
    report = weekly_report(store, 7, 10, now)
    assert "`checkout.spec.ts > pays` | acme/web | 3 | 3" in report and "old.spec.ts" not in report
    store.close()
    assert "No failures recorded" in weekly_report(Store(":memory:"))
