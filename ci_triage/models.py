"""The data that flows through ci-triage: one failed job, the typed answers about it, and the decision."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# The eight failure categories, in the order they are offered to every backend.
CATEGORIES: dict[str, str] = {
    "flaky_test": "Flaky test: a test that fails intermittently for reasons unrelated to the change, such as a race, timing, ordering or a "
    "shared resource; the same test passes when re-run, or has failed on the default branch before.",
    "test_failure": "Real test failure: a test assertion or test error that the change causes and that would fail again on every re-run.",
    "compile_error": "Compile, build or type error: the code does not compile, bundle or type-check (compiler errors, TypeScript errors, "
    "missing imports or symbols, syntax errors).",
    "lint_format": "Lint or format: a linter, formatter, spell checker or style check failed (ruff, eslint, prettier, clippy, gofmt, "
    "a generated file or docs being out of date).",
    "dependency": "Dependency or lockfile: package installation or resolution failed, a lockfile is out of date, a version conflict, "
    "or a package was not found in its registry.",
    "infrastructure": "Infrastructure or runner: a timeout, cancellation, network or download error, rate limit, out of disk or memory, "
    "a runner lost or shut down, or an external service outage.",
    "configuration": "Configuration or secrets: a missing or invalid secret, token or credential, missing permissions, or a wrong "
    "workflow, environment or tool configuration.",
    "unknown": "Unknown: the log excerpt does not show enough to tell what failed.",
}
RERUNNABLE = ("flaky_test", "infrastructure")
URGENCY_LEVELS = [
    "Low: can wait. A flaky test or a runner or network blip that a re-run fixes, on any branch.",
    "Medium: blocks one pull request or feature branch until someone fixes it.",
    "High: breaks the default branch, a release or a scheduled build that everyone depends on.",
]
NOULS: dict[str, str] = {
    "caused_by_commit": "The failure is caused by the changes in this commit (the files in changed_files), not by a flaky test, the "
    "CI infrastructure or something outside the repository.",
    "safe_to_rerun": "Re-running the failed job without any change would most likely pass, because the failure is intermittent "
    "(flaky test, timeout, network or runner problem) rather than deterministic.",
    "needs_code_change": "Making this job pass needs a change committed to the repository: source code, tests, lockfile, formatting or configuration files.",
}


@dataclass
class Failure:
    """One failed CI job, with the metadata ci-triage collects about it."""

    job_name: str
    excerpt: str
    repo: str = ""
    workflow: str = ""
    failed_step: str = ""
    event: str = ""
    branch: str = ""
    default_branch: str = "main"
    head_sha: str = ""
    commit_message: str = ""
    changed_files: list[str] = field(default_factory=list)
    changed_files_total: int = 0
    failing_tests: list[str] = field(default_factory=list)
    history_checked: int = 0
    history_failed: int = 0
    run_id: int = 0
    run_attempt: int = 1
    run_url: str = ""
    job_id: int = 0
    job_url: str = ""
    pr_number: int | None = None
    id: str = ""

    @property
    def on_default_branch(self) -> bool:
        return bool(self.branch) and self.branch == self.default_branch and self.event in ("push", "schedule", "workflow_dispatch", "merge_group", "")

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Failure:
        hist = d.get("default_branch_history") or {}
        return cls(
            job_name=d.get("job_name", ""),
            excerpt=d.get("excerpt", ""),
            repo=d.get("repo", ""),
            workflow=d.get("workflow", ""),
            failed_step=d.get("failed_step", ""),
            event=d.get("event", ""),
            branch=d.get("branch", ""),
            default_branch=d.get("default_branch", "main"),
            head_sha=d.get("head_sha", ""),
            commit_message=d.get("commit_message", ""),
            changed_files=list(d.get("changed_files", [])),
            changed_files_total=int(d.get("changed_files_total", len(d.get("changed_files", [])))),
            failing_tests=list(d.get("failing_tests", [])),
            history_checked=int(hist.get("runs_checked", 0)),
            history_failed=int(hist.get("job_failed", 0)),
            run_id=int(d.get("run_id", 0) or 0),
            run_attempt=int(d.get("run_attempt", 1) or 1),
            run_url=d.get("run_url", ""),
            job_id=int(d.get("job_id", 0) or 0),
            job_url=d.get("job_url", ""),
            pr_number=d.get("pr_number"),
            id=d.get("id", ""),
        )


@dataclass
class Answer:
    kind: str  # choice | score | noul
    value: Any  # the chosen option, the score level, or P(yes)
    confidence: float
    probabilities: dict[str, float] = field(default_factory=dict)


@dataclass
class Decision:
    backend: str
    model: str
    answers: dict[str, Answer]
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    cached: bool = False
    redactions: int = 0

    @property
    def category(self) -> str:
        return str(self.answers["category"].value)

    @property
    def category_confidence(self) -> float:
        return self.answers["category"].confidence

    @property
    def urgency(self) -> int:
        return int(self.answers["urgency"].value)

    def p(self, noul: str) -> float:
        return float(self.answers[noul].value)
