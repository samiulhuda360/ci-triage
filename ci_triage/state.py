"""Builds the redacted state sent to a backend for one failed job."""

from __future__ import annotations

from typing import Any

from .models import Failure
from .redact import redact

MAX_FILES = 25
MAX_EXCERPT = 5000


def history_text(f: Failure) -> str:
    """The default-branch history as words, so no backend has to do arithmetic."""
    if f.history_checked == 0:
        return "unknown (no earlier runs of this job on the default branch were found)"
    bucket = "never" if f.history_failed == 0 else ("often" if f.history_failed / f.history_checked >= 0.3 else "occasionally")
    return f"{bucket}: the same job failed in {f.history_failed} of the last {f.history_checked} runs on {f.default_branch}"


def branch_type(f: Failure) -> str:
    if f.event in ("pull_request", "pull_request_target"):
        return f"pull request (branch {f.branch})"
    if f.event == "merge_group":
        return "merge queue"
    if f.event == "schedule":
        return f"scheduled build on {f.branch or f.default_branch}"
    if f.on_default_branch:
        return f"default branch ({f.default_branch})"
    if f.branch.startswith(("release", "v")) or f.event == "release":
        return f"release ({f.branch})"
    return f"branch {f.branch}" if f.branch else "unknown"


def prepare_state(f: Failure, max_excerpt: int = MAX_EXCERPT) -> tuple[dict[str, Any], int]:
    excerpt = f.excerpt if len(f.excerpt) <= max_excerpt else f.excerpt[: max_excerpt - 4] + "\n..."
    text, n1 = redact(excerpt)
    message, n2 = redact(f.commit_message)
    files = f.changed_files[:MAX_FILES]
    extra = f.changed_files_total - len(files)
    state: dict[str, Any] = {
        "workflow": f.workflow,
        "job": f.job_name,
        "failed_step": f.failed_step or "(not known)",
        "branch_type": branch_type(f),
        "commit_message": message or "(none)",
        "changed_files": [*files, f"... and {extra} more"] if extra > 0 else (files or ["(not known)"]),
        "default_branch_history": history_text(f),
        "failing_tests": f.failing_tests[:10] or "none named in the log",
        "log_excerpt": text,
    }
    return state, n1 + n2
