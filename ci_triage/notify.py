"""Chat notifications for default-branch breaks (Slack or Teams incoming webhooks)."""

from __future__ import annotations

import os

import httpx

from .comment import JobVerdict
from .config import Config
from .policy import TITLES


def notification_text(repo: str, run_url: str, verdicts: list[JobVerdict]) -> str:
    jobs = "; ".join(f"{v.failure.job_name}: {TITLES.get(v.outcome.category, v.outcome.category).lower()}" for v in verdicts if v.outcome.notify)
    branch = verdicts[0].failure.branch if verdicts else ""
    step = next((v.outcome.next_step for v in verdicts if v.outcome.notify), "")
    return f"CI is red on {repo} {branch}: {jobs}. {step} {run_url}".strip()


def send_notifications(repo: str, run_url: str, verdicts: list[JobVerdict], cfg: Config, dry_run: bool = False) -> list[str]:
    """Posts to every configured webhook when a job asks for it. Returns the channels notified (or that would be)."""
    if not any(v.outcome.notify for v in verdicts):
        return []
    text = notification_text(repo, run_url, verdicts)
    sent: list[str] = []
    for channel, env in (("slack", cfg.notify.slack_webhook_env), ("teams", cfg.notify.teams_webhook_env)):
        url = os.environ.get(env, "")
        if not url:
            continue
        if not dry_run:
            httpx.post(url, json={"text": text}, timeout=10).raise_for_status()
        sent.append(channel)
    return sent
