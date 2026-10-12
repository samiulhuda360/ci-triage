"""One triage run: collect the failed jobs, ask the backend, apply the policy, act, notify, record and audit."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from .audit import audit_record, write_audit
from .backends import Backend
from .comment import JobVerdict, render_comment
from .config import Config
from .github import GitHub
from .logs import extract_error_region, failing_tests
from .models import Failure
from .notify import send_notifications
from .policy import apply_policy, run_action
from .redact import redact
from .store import Store
from .suggest import suggest_fix

log = logging.getLogger("ci_triage")


@dataclass
class RunResult:
    repo: str
    run_id: int
    run_url: str
    action: str  # rerun | report | skipped
    verdicts: list[JobVerdict] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    comment: str = ""
    pr_number: int | None = None


def failure_from_job(gh: GitHub, repo: str, run: dict[str, Any], job: dict[str, Any], cfg: Config, pr: int | None) -> Failure:
    """Downloads one failed job's log, trims and redacts it, and adds the commit and default-branch history."""
    ex = extract_error_region(gh.job_log(repo, int(job["id"])))
    text, _ = redact(ex.text)
    files, total = gh.commit_files(repo, run.get("head_sha", ""))
    default = (run.get("repository") or {}).get("default_branch") or "main"
    try:
        checked, failed = gh.job_history(
            repo, int(run["workflow_id"]), default, job.get("name", ""), run.get("created_at", ""), cfg.history_runs, int(run["id"])
        )
    except (httpx.HTTPError, KeyError):
        checked = failed = 0
    return Failure(
        job_name=job.get("name", ""),
        excerpt=text,
        repo=repo,
        workflow=run.get("name", ""),
        failed_step=next((s["name"] for s in job.get("steps", []) if s.get("conclusion") == "failure"), ex.failed_step),
        event=run.get("event", ""),
        branch=run.get("head_branch") or "",
        default_branch=default,
        head_sha=run.get("head_sha", ""),
        commit_message=((run.get("head_commit") or {}).get("message") or "").split("\n")[0][:200],
        changed_files=files,
        changed_files_total=total,
        failing_tests=failing_tests(text),
        history_checked=checked,
        history_failed=failed,
        run_id=int(run["id"]),
        run_attempt=int(run.get("run_attempt", 1) or 1),
        run_url=run.get("html_url", ""),
        job_id=int(job["id"]),
        job_url=job.get("html_url", ""),
        pr_number=pr,
    )


def judge(failures: list[Failure], cfg: Config, backend: Backend, reruns_today: int = 0, cache_dir: Path | None = None) -> tuple[str, list[JobVerdict]]:
    verdicts = []
    for f in failures:
        d = backend.decide(f)
        verdicts.append(JobVerdict(f, d, apply_policy(f, d, cfg, reruns_today)))
    action = run_action([v.outcome for v in verdicts])
    if cfg.suggest.enabled and action == "report":
        for v in verdicts:
            if v.outcome.category in cfg.suggest.categories:
                v.suggestion = suggest_fix(v.failure, v.decision, cache_dir or Path(cfg.suggest.cache_dir))
    return action, verdicts


def triage_run(gh: GitHub, repo: str, run_id: int, cfg: Config, backend: Backend, store: Store | None = None, dry_run: bool = False) -> RunResult:
    run = gh.get_run(repo, run_id)
    result = RunResult(repo, run_id, run.get("html_url", ""), "skipped")
    if run.get("conclusion") not in ("failure", "timed_out"):
        result.actions.append(f"run conclusion is {run.get('conclusion')}: nothing to triage")
        return result
    jobs = [j for j in gh.failed_jobs(repo, run_id) if j.get("name") not in cfg.ignore_jobs][: cfg.max_jobs]
    if not jobs:
        result.actions.append("no failed jobs found")
        return result
    pr = gh.find_pr(repo, run)
    result.pr_number = pr
    failures = [failure_from_job(gh, repo, run, job, cfg, pr) for job in jobs]
    reruns = store.reruns_today(repo) if store else 0
    action, verdicts = judge(failures, cfg, backend, reruns)
    result.action, result.verdicts = action, verdicts
    result.comment = render_comment(verdicts, action, dry_run, cfg.key_lines)
    acts = result.actions
    if action == "rerun":
        if dry_run:
            acts.append("would re-run the failed jobs")
        else:
            gh.rerun_failed_jobs(repo, run_id)
            acts.append("re-ran the failed jobs")
            if store:
                store.add_rerun(repo)
    labels = sorted({label for v in verdicts for label in v.outcome.labels})
    if pr and cfg.labels.enabled:
        if dry_run:
            acts.append(f"would label PR #{pr}: {', '.join(labels)}")
        else:
            acts += gh.set_labels(repo, pr, labels, cfg.labels.prefix, {cfg.labels.needs_human, cfg.labels.rerun})
    if pr and cfg.comment and action == "report":
        if dry_run:
            acts.append(f"would comment on PR #{pr}")
        else:
            acts.append(gh.upsert_comment(repo, pr, result.comment))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary and cfg.step_summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(result.comment + "\n")
        acts.append("wrote the run summary")
    for channel in send_notifications(repo, result.run_url, verdicts, cfg, dry_run):
        acts.append(f"{'would notify' if dry_run else 'notified'} {channel}")
    if store:
        for v in verdicts:
            f = v.failure
            store.record(repo, run_id, f.job_name, f.failing_tests, v.outcome.category, f.branch, v.decision.category_confidence, action == "rerun")
    if cfg.audit_log:
        for v in verdicts:
            write_audit(cfg.audit_log, audit_record(v, action, acts, dry_run))
    log.info("%s run %s: %s (%s)", repo, run_id, action, "; ".join(acts))
    return result
