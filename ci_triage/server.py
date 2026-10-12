"""Self-hosted webhook service: GitHub sends `workflow_run` events, ci-triage triages every failed run.

Standard library only. Signatures are checked with CI_TRIAGE_WEBHOOK_SECRET; work runs on a background thread so
GitHub gets a quick 202.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .backends import get_backend
from .config import load_config
from .github import GitHub
from .store import Store
from .triage import triage_run

log = logging.getLogger("ci_triage.server")
_store_lock = threading.Lock()


def verify_signature(secret: str, body: bytes, header: str) -> bool:
    if not secret or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


def targets(event: str, payload: dict[str, Any]) -> list[tuple[str, int]]:
    """(repo, run id) pairs this event asks us to triage: completed workflow runs that failed."""
    if event != "workflow_run" or payload.get("action") != "completed":
        return []
    run = payload.get("workflow_run") or {}
    if run.get("conclusion") not in ("failure", "timed_out"):
        return []
    repo = (payload.get("repository") or {}).get("full_name", "")
    return [(repo, int(run["id"]))] if repo and run.get("id") else []


def handle(repo: str, run_id: int) -> None:
    gh = GitHub()
    text = gh.fetch_config_text(repo)
    cfg = load_config(text=text) if text is not None else load_config(os.environ.get("CI_TRIAGE_CONFIG"))
    if os.environ.get("CI_TRIAGE_AUDIT_LOG"):
        cfg.audit_log = os.environ["CI_TRIAGE_AUDIT_LOG"]
    dry = cfg.dry_run or os.environ.get("CI_TRIAGE_DRY_RUN", "") not in ("", "0", "false")
    with _store_lock:
        store = Store(os.environ.get("CI_TRIAGE_STORE", cfg.flaky.store))
        try:
            result = triage_run(gh, repo, run_id, cfg, get_backend(os.environ.get("CI_TRIAGE_BACKEND") or cfg.backend), store, dry_run=dry)
        finally:
            store.close()
    log.info("%s run %s: %s %s", repo, run_id, result.action, result.actions)


class Handler(BaseHTTPRequestHandler):
    server_version = "ci-triage"

    def _reply(self, code: int, body: dict[str, Any]) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._reply(200, {"ok": True})
        else:
            self._reply(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/webhook":
            self._reply(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length > 5_000_000:
            self._reply(413, {"error": "payload too large"})
            return
        body = self.rfile.read(length)
        if not verify_signature(os.environ.get("CI_TRIAGE_WEBHOOK_SECRET", ""), body, self.headers.get("X-Hub-Signature-256", "")):
            self._reply(401, {"error": "bad or missing signature"})
            return
        jobs = targets(self.headers.get("X-GitHub-Event", ""), json.loads(body or b"{}"))
        for repo, run_id in jobs:
            threading.Thread(target=self._safe_handle, args=(repo, run_id), daemon=True).start()
        self._reply(202, {"queued": [f"{r} run {n}" for r, n in jobs]})

    @staticmethod
    def _safe_handle(repo: str, run_id: int) -> None:
        try:
            handle(repo, run_id)
        except Exception:
            log.exception("failed to triage %s run %s", repo, run_id)

    def log_message(self, fmt: str, *args: Any) -> None:
        log.info("%s %s", self.address_string(), fmt % args)


def serve(host: str = "0.0.0.0", port: int = 8080) -> None:  # noqa: S104 - a container listens on all interfaces
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not os.environ.get("CI_TRIAGE_WEBHOOK_SECRET"):
        raise SystemExit("CI_TRIAGE_WEBHOOK_SECRET must be set: unsigned webhooks are rejected")
    httpd = ThreadingHTTPServer((host, port), Handler)
    log.info("ci-triage listening on %s:%s", host, port)
    httpd.serve_forever()
