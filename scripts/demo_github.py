"""End-to-end demo of the GitHub Action code path against a local stand-in for the GitHub API.

It serves one failed workflow run built from a fixture (a real failed job from the evaluation set: its log excerpt,
commit files and default-branch history), runs `ci-triage action` exactly as the Action does, and prints every write
ci-triage made (re-run, labels, comment). Nothing on github.com is changed.

    python scripts/demo_github.py fixtures/flaky-rerun.json
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REPO = "acme/storefront"


def raw_log(fx: dict[str, Any]) -> str:
    """Rebuilds a GitHub-style job log around the fixture's excerpt (timestamps, step groups, error annotation)."""
    lines = ["##[group]Run actions/checkout@v4", "Syncing repository: " + REPO, "##[endgroup]"]
    for line in fx["excerpt"].splitlines():
        if line.startswith("[step] "):
            cmd = line.removeprefix("[step] ")
            lines += [f"##[group]Run {cmd}", cmd, "##[endgroup]"]
        else:
            lines.append(line)
    lines += ["##[group]Run actions/upload-artifact@v4", "Post job cleanup."]
    return "\n".join(f"2026-10-12T09:{i // 60 % 60:02d}:{i % 60:02d}.0000000Z {line}" for i, line in enumerate(lines)) + "\n"


def make_handler(fx: dict[str, Any], writes: list[dict[str, Any]]) -> type[BaseHTTPRequestHandler]:
    run_id, job_id, wf = 9100, 9200, 77
    pr = int(fx.get("pr_number") or 0) or None
    hist = fx.get("default_branch_history") or {"runs_checked": 0, "job_failed": 0}
    history_runs = [{"id": 8000 + i, "created_at": f"2026-10-{1 + i:02d}T08:00:00Z"} for i in range(hist["runs_checked"])]
    run = {
        "id": run_id,
        "name": fx.get("workflow", "CI"),
        "workflow_id": wf,
        "event": fx.get("event", "pull_request"),
        "head_branch": fx.get("branch", "feature"),
        "head_sha": "4f1c2e9d8b7a6c5d4e3f2a1b0c9d8e7f6a5b4c3d",
        "run_attempt": 1,
        "conclusion": "failure",
        "created_at": "2026-10-12T09:00:00Z",
        "html_url": f"https://github.com/{REPO}/actions/runs/{run_id}",
        "pull_requests": [{"number": pr}] if pr else [],
        "repository": {"default_branch": fx.get("default_branch", "main")},
        "head_commit": {"message": fx.get("commit_message", "")},
    }
    steps = [{"name": "Set up job", "conclusion": "success"}, {"name": fx.get("failed_step") or "Run tests", "conclusion": "failure"}]
    routes: dict[str, Any] = {
        f"/repos/{REPO}/actions/runs/{run_id}": run,
        f"/repos/{REPO}/actions/runs/{run_id}/jobs": {
            "jobs": [
                {
                    "id": job_id,
                    "name": fx["job_name"],
                    "conclusion": "failure",
                    "html_url": f"https://github.com/{REPO}/actions/runs/{run_id}/job/{job_id}",
                    "steps": steps,
                }
            ]
        },
        f"/repos/{REPO}/commits/{run['head_sha']}": {"files": [{"filename": f} for f in fx.get("changed_files", [])]},
        f"/repos/{REPO}/actions/workflows/{wf}/runs": {"workflow_runs": history_runs},
        f"/repos/{REPO}/issues/{pr}/labels": [{"name": "needs-review"}],
        f"/repos/{REPO}/issues/{pr}/comments": [],
    }
    for i, r in enumerate(history_runs):
        failed = i < hist["job_failed"]
        routes[f"/repos/{REPO}/actions/runs/{r['id']}/jobs"] = {"jobs": [{"name": fx["job_name"], "conclusion": "failure" if failed else "success"}]}
    log_text = raw_log(fx)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: Any, text: str | None = None) -> None:
            data = text.encode() if text is not None else json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/plain" if text is not None else "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            path = self.path.split("?")[0]
            if path == f"/repos/{REPO}/actions/jobs/{job_id}/logs":
                self._send(200, None, log_text)
            elif path in routes:
                self._send(200, routes[path])
            else:
                self._send(404, {"message": "Not Found"})

        def do_POST(self) -> None:
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            writes.append({"method": self.command, "path": self.path, "body": json.loads(raw) if raw else None})
            self._send(201, {})

        def do_PATCH(self) -> None:
            self.do_POST()

        def do_DELETE(self) -> None:
            writes.append({"method": "DELETE", "path": self.path, "body": None})
            self._send(204, {})

        def log_message(self, fmt: str, *args: Any) -> None:
            return

    return Handler


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    fixture = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "fixtures" / "flaky-rerun.json")
    fx = json.loads(fixture.read_text(encoding="utf-8"))
    writes: list[dict[str, Any]] = []
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(fx, writes))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    api = f"http://127.0.0.1:{httpd.server_address[1]}"
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        env = {
            **os.environ,
            "GITHUB_API_URL": api,
            "GITHUB_TOKEN": "demo-token-not-real",
            "GITHUB_STEP_SUMMARY": str(work / "summary.md"),
            "CI_TRIAGE_CACHE_DIR": os.environ.get("CI_TRIAGE_CACHE_DIR", str(ROOT / "eval" / "cache")),
            "PYTHONIOENCODING": "utf-8",
        }
        cmd = [sys.executable, "-m", "ci_triage", "action", "--repo", REPO, "--run-id", "9100", "--config", str(ROOT / "examples" / "ci-triage.yml")]
        cmd += ["--store", str(work / "flaky.db")]
        proc = subprocess.run(cmd, env=env, cwd=work, capture_output=True, text=True, encoding="utf-8", check=False)
        summary = (work / "summary.md").read_text(encoding="utf-8") if (work / "summary.md").exists() else ""
    httpd.shutdown()
    print(f"$ ci-triage action   # failed run of {fx['job_name']!r} in {REPO}")
    for line in proc.stdout.splitlines():
        if line.startswith(("ci-triage:", "- ")):
            print(f"  {line}")
    print(f"ci-triage exited with code {proc.returncode}; {len(writes)} writes to GitHub:")
    for w in writes:
        body = w["body"] or {}
        detail = ", ".join(body.get("labels", [])) or (f"comment, {len(body['body'])} characters" if "body" in body else "")
        print(f"  {w['method']:6s} {w['path']}  {detail}")
    if summary:
        out = ROOT / "docs" / "build" / f"demo-{fixture.stem}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(summary, encoding="utf-8", newline="\n")
        print(f"run summary saved to {out.relative_to(ROOT).as_posix()}")
    if proc.returncode != 0:
        print(proc.stderr[-2000:])
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
