from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from ci_triage.config import Config
from ci_triage.github import GitHub
from ci_triage.server import targets, verify_signature
from ci_triage.store import Store
from ci_triage.triage import triage_run

from .conftest import PYTEST_LOG, FakeBackend, make_decision

REPO = "acme/orders"


class FakeApi:
    """Just enough of the GitHub REST API for one failed workflow run on a pull request."""

    def __init__(self, conclusion: str = "failure", attempt: int = 1) -> None:
        self.writes: list[tuple[str, str, Any]] = []
        self.labels = [{"name": "ci:lint-format"}, {"name": "bug"}]
        self.comments: list[dict[str, Any]] = []
        self.run = {
            "id": 42,
            "name": "CI",
            "workflow_id": 7,
            "event": "pull_request",
            "head_branch": "fix-refunds",
            "head_sha": "abc123",
            "run_attempt": attempt,
            "conclusion": conclusion,
            "created_at": "2026-10-12T10:00:00Z",
            "html_url": "https://github.com/acme/orders/actions/runs/42",
            "pull_requests": [{"number": 7}],
            "repository": {"default_branch": "main"},
            "head_commit": {"message": "Round refunds to cents\n\nlonger body"},
        }

    def handler(self, request: httpx.Request) -> httpx.Response:
        path, method = request.url.path, request.method
        if method != "GET":
            body = json.loads(request.content) if request.content else None
            self.writes.append((method, path, body))
            if path.endswith("/comments") and method == "POST":
                self.comments.append({"id": 1, "body": body["body"]})
            return httpx.Response(201 if method == "POST" else 204, json={})
        routes: dict[str, Any] = {
            f"/repos/{REPO}/actions/runs/42": self.run,
            f"/repos/{REPO}/actions/runs/42/jobs": {
                "jobs": [
                    {
                        "id": 501,
                        "name": "test (3.12)",
                        "conclusion": "failure",
                        "html_url": "https://example.test/job/501",
                        "steps": [{"name": "Run tests", "conclusion": "failure"}],
                    },
                    {"id": 502, "name": "build", "conclusion": "success", "steps": []},
                ]
            },
            f"/repos/{REPO}/commits/abc123": {"files": [{"filename": "orders/refunds.py"}, {"filename": "tests/test_refunds.py"}]},
            f"/repos/{REPO}/actions/workflows/7/runs": {
                "workflow_runs": [{"id": 40, "created_at": "2026-10-11T10:00:00Z"}, {"id": 41, "created_at": "2026-10-11T12:00:00Z"}]
            },
            f"/repos/{REPO}/actions/runs/40/jobs": {"jobs": [{"name": "test (3.12)", "conclusion": "failure"}]},
            f"/repos/{REPO}/actions/runs/41/jobs": {"jobs": [{"name": "test (3.12)", "conclusion": "success"}]},
            f"/repos/{REPO}/issues/7/labels": self.labels,
            f"/repos/{REPO}/issues/7/comments": self.comments,
        }
        if path == f"/repos/{REPO}/actions/jobs/501/logs":
            return httpx.Response(200, text=PYTEST_LOG)
        if path in routes:
            return httpx.Response(200, json=routes[path])
        return httpx.Response(404, json={"message": "Not Found"})


def _gh(api: FakeApi) -> GitHub:
    return GitHub(token="test-token-not-real", api_url="https://api.test", client=httpx.Client(transport=httpx.MockTransport(api.handler)))


def test_real_failure_gets_labels_and_one_comment(tmp_path: Path) -> None:
    api = FakeApi()
    backend = FakeBackend(make_decision("test_failure", 0.9, urgency=1, caused_by_commit=0.9, safe_to_rerun=0.05, needs_code_change=0.95))
    cfg = Config(audit_log=str(tmp_path / "audit.jsonl"))
    store = Store(tmp_path / "flaky.db")
    result = triage_run(_gh(api), REPO, 42, cfg, backend, store)
    assert result.action == "report" and result.pr_number == 7
    seen = backend.seen[0]
    assert seen.job_name == "test (3.12)" and seen.failed_step == "Run tests"
    assert "assert 14 == 15" in seen.excerpt
    assert seen.changed_files == ["orders/refunds.py", "tests/test_refunds.py"]
    assert (seen.history_checked, seen.history_failed) == (2, 1)
    assert seen.failing_tests == ["tests/test_refunds.py::test_refund_total"]
    methods = [(m, p) for m, p, _ in api.writes]
    assert ("DELETE", f"/repos/{REPO}/issues/7/labels/ci:lint-format") in methods  # stale ci-triage label removed, "bug" kept
    assert ("POST", f"/repos/{REPO}/issues/7/labels") in methods
    assert ("POST", f"/repos/{REPO}/issues/7/comments") in methods
    assert not any("rerun" in p for _, p in methods)
    audit = [json.loads(line) for line in (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
    assert audit[0]["category"] == "test_failure" and audit[0]["run_action"] == "report"
    # A second run updates the same comment instead of adding another.
    triage_run(_gh(api), REPO, 42, cfg, backend, store)
    assert sum(1 for m, p, _ in api.writes if m == "POST" and p.endswith("/comments")) == 1
    assert any(m == "PATCH" for m, _, _ in api.writes)
    store.close()


def test_flaky_failure_is_rerun_once_and_counted(tmp_path: Path) -> None:
    api = FakeApi()
    cfg = Config(audit_log="")
    store = Store(tmp_path / "flaky.db")
    result = triage_run(_gh(api), REPO, 42, cfg, FakeBackend(make_decision("flaky_test", 0.9)), store)
    assert result.action == "rerun"
    assert ("POST", f"/repos/{REPO}/actions/runs/42/rerun-failed-jobs", None) in api.writes
    assert not any(p.endswith("/comments") for _, p, _ in api.writes)  # a re-run gets a label, not a comment
    assert store.reruns_today(REPO) == 1
    assert store.top_flaky()[0].test == "tests/test_refunds.py::test_refund_total"
    # The re-run attempt fails again: no second re-run.
    api2 = FakeApi(attempt=2)
    again = triage_run(_gh(api2), REPO, 42, cfg, FakeBackend(make_decision("flaky_test", 0.9)), store)
    assert again.action == "report" and not any("rerun" in p for _, p, _ in api2.writes)
    store.close()


def test_dry_run_changes_nothing(tmp_path: Path) -> None:
    api = FakeApi()
    result = triage_run(_gh(api), REPO, 42, Config(audit_log=""), FakeBackend(make_decision("flaky_test", 0.9)), Store(":memory:"), dry_run=True)
    assert result.action == "rerun" and api.writes == []
    assert "would re-run the failed jobs" in result.actions and "dry run" in result.comment


def test_successful_run_is_skipped() -> None:
    api = FakeApi(conclusion="success")
    result = triage_run(_gh(api), REPO, 42, Config(audit_log=""), FakeBackend(make_decision()), None)
    assert result.action == "skipped" and api.writes == []


def test_webhook_signature_and_targets() -> None:
    secret, body = "test-secret-not-real", b'{"a": 1}'
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(secret, body, sig)
    assert not verify_signature(secret, body + b" ", sig)
    assert not verify_signature("", body, sig)
    assert not verify_signature(secret, body, "sha1=abc")
    payload = {"action": "completed", "repository": {"full_name": REPO}, "workflow_run": {"id": 42, "conclusion": "failure"}}
    assert targets("workflow_run", payload) == [(REPO, 42)]
    assert targets("workflow_run", {**payload, "workflow_run": {"id": 42, "conclusion": "success"}}) == []
    assert targets("workflow_run", {**payload, "action": "requested"}) == []
    assert targets("push", payload) == []


@pytest.mark.parametrize("prs", [[], None])
def test_fork_pull_request_is_found_by_branch(prs: list[Any] | None) -> None:
    run = {"event": "pull_request", "head_branch": "patch-1", "pull_requests": prs, "head_repository": {"owner": {"login": "someone"}}}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["head"] == "someone:patch-1"
        return httpx.Response(200, json=[{"number": 99}])

    gh = GitHub(token="", api_url="https://api.test", client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert gh.find_pr(REPO, run) == 99
