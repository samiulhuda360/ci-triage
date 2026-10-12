"""A minimal GitHub client: read a failed workflow run, its jobs, logs, commit and history; re-run, label and comment."""

from __future__ import annotations

import os
from typing import Any

import httpx

from .comment import MARKER

FAILED = ("failure", "timed_out")


class GitHub:
    def __init__(self, token: str | None = None, api_url: str | None = None, client: httpx.Client | None = None) -> None:
        self.api_url = (api_url or os.environ.get("GITHUB_API_URL") or "https://api.github.com").rstrip("/")
        token = token if token is not None else os.environ.get("GITHUB_TOKEN", "")
        self.headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "ci-triage"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        # Log downloads redirect to blob storage; httpx drops the Authorization header on a cross-origin redirect.
        self.http = client or httpx.Client(timeout=60, follow_redirects=True)

    def _req(self, method: str, path: str, **kw: Any) -> Any:
        resp = self.http.request(method, f"{self.api_url}{path}", headers=self.headers, **kw)
        resp.raise_for_status()
        return resp.json() if resp.content else None

    # Reading

    def get_run(self, repo: str, run_id: int) -> dict[str, Any]:
        return dict(self._req("GET", f"/repos/{repo}/actions/runs/{run_id}"))

    def failed_jobs(self, repo: str, run_id: int, attempt: int | None = None) -> list[dict[str, Any]]:
        path = f"/repos/{repo}/actions/runs/{run_id}" + (f"/attempts/{attempt}" if attempt else "") + "/jobs"
        jobs = self._req("GET", path, params={"per_page": 100}).get("jobs", [])
        return [j for j in jobs if j.get("conclusion") in FAILED]

    def job_log(self, repo: str, job_id: int, max_bytes: int = 20_000_000) -> str:
        with self.http.stream("GET", f"{self.api_url}/repos/{repo}/actions/jobs/{job_id}/logs", headers=self.headers) as resp:
            resp.raise_for_status()
            chunks: list[bytes] = []
            size = 0
            for chunk in resp.iter_bytes():
                chunks.append(chunk)
                size += len(chunk)
                if size > max_bytes:  # keep the tail: the failure is near the end of a long log
                    joined = b"".join(chunks)[-max_bytes // 2 :]
                    chunks, size = [joined], len(joined)
        return b"".join(chunks).decode("utf-8", errors="replace")

    def commit_files(self, repo: str, sha: str) -> tuple[list[str], int]:
        try:
            files = self._req("GET", f"/repos/{repo}/commits/{sha}").get("files", [])
        except httpx.HTTPStatusError:
            return [], 0
        return [f["filename"] for f in files][:40], len(files)

    def job_history(self, repo: str, workflow_id: int, branch: str, job_name: str, before: str, n: int = 10, exclude_run: int = 0) -> tuple[int, int]:
        """How often the same job failed in the last `n` completed default-branch runs: (runs checked, runs failed)."""
        runs = self._req(
            "GET", f"/repos/{repo}/actions/workflows/{workflow_id}/runs", params={"branch": branch, "status": "completed", "per_page": max(n * 2, 20)}
        ).get("workflow_runs", [])
        checked = failed = 0
        for run in [r for r in runs if r.get("created_at", "") < before and r.get("id") != exclude_run][:n]:
            jobs = self._req("GET", f"/repos/{repo}/actions/runs/{run['id']}/jobs", params={"per_page": 100}).get("jobs", [])
            match = [j for j in jobs if j.get("name") == job_name]
            if match:
                checked += 1
                failed += match[0].get("conclusion") in FAILED
        return checked, failed

    def find_pr(self, repo: str, run: dict[str, Any]) -> int | None:
        prs = run.get("pull_requests") or []
        if prs:
            return int(prs[0]["number"])
        head = run.get("head_repository") or {}
        owner = (head.get("owner") or {}).get("login")
        if run.get("event") in ("pull_request", "pull_request_target") and owner and run.get("head_branch"):
            # Pull requests from forks are not listed on the run; look them up by head branch.
            found = self._req("GET", f"/repos/{repo}/pulls", params={"head": f"{owner}:{run['head_branch']}", "state": "open"})
            if found:
                return int(found[0]["number"])
        return None

    def fetch_config_text(self, repo: str, path: str = ".github/ci-triage.yml") -> str | None:
        resp = self.http.get(f"{self.api_url}/repos/{repo}/contents/{path}", headers={**self.headers, "Accept": "application/vnd.github.raw+json"})
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.text

    # Acting

    def rerun_failed_jobs(self, repo: str, run_id: int) -> None:
        self._req("POST", f"/repos/{repo}/actions/runs/{run_id}/rerun-failed-jobs")

    def set_labels(self, repo: str, number: int, wanted: list[str], prefix: str, extra_managed: set[str]) -> list[str]:
        """Adds `wanted` and removes stale ci-triage labels (those starting with `prefix`). Returns what was done."""
        done = []
        current = {label["name"] for label in self._req("GET", f"/repos/{repo}/issues/{number}/labels")}
        for stale in sorted(name for name in current if (name.startswith(prefix) or name in extra_managed) and name not in wanted):
            self._req("DELETE", f"/repos/{repo}/issues/{number}/labels/{stale}")
            done.append(f"removed label {stale}")
        new = [label for label in wanted if label not in current]
        if new:
            self._req("POST", f"/repos/{repo}/issues/{number}/labels", json={"labels": new})
            done.append(f"added labels {', '.join(new)}")
        return done

    def upsert_comment(self, repo: str, number: int, body: str) -> str:
        existing = [c for c in self._req("GET", f"/repos/{repo}/issues/{number}/comments", params={"per_page": 100}) if MARKER in (c.get("body") or "")]
        if existing:
            self._req("PATCH", f"/repos/{repo}/issues/comments/{existing[0]['id']}", json={"body": body})
            return "updated the triage comment"
        self._req("POST", f"/repos/{repo}/issues/{number}/comments", json={"body": body})
        return "posted the triage comment"
