"""Collects real CI failure excerpts from public, permissively licensed repositories with `gh api`.

Two phases:

    python scripts/harvest.py collect --out candidates.jsonl --raw-dir tmp/   # failed jobs, trimmed and redacted
    python scripts/harvest.py enrich candidates.jsonl ids.txt --out enriched.jsonl  # commit files + default-branch history

`collect` reads two kinds of run per repository: runs whose latest attempt failed, and runs that failed and then
passed on a re-run of the same commit (attempt 1 failed, a later attempt succeeded). The second kind is the evidence
the labelling guide uses for flaky and infrastructure failures. Only the trimmed, redacted excerpt is kept; raw logs
are deleted as soon as they are trimmed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ci_triage.logs import extract_error_region, failing_tests
from ci_triage.redact import redact

ALLOWED = {"MIT", "Apache-2.0"}
REPOS = [
    "vitejs/vite",
    "vitest-dev/vitest",
    "astral-sh/ruff",
    "astral-sh/uv",
    "pydantic/pydantic",
    "fastapi/fastapi",
    "langchain-ai/langchain",
    "huggingface/transformers",
    "microsoft/playwright",
    "microsoft/TypeScript",
    "vercel/next.js",
    "facebook/react",
    "withastro/astro",
    "sveltejs/svelte",
    "vuejs/core",
    "oven-sh/bun",
    "denoland/deno",
    "tokio-rs/tokio",
    "tauri-apps/tauri",
    "biomejs/biome",
    "prettier/prettier",
    "eslint/eslint",
    "typescript-eslint/typescript-eslint",
    "pnpm/pnpm",
    "nestjs/nest",
    "prisma/prisma",
    "apache/airflow",
    "apache/arrow",
    "apache/datafusion",
    "apache/iceberg",
    "mlflow/mlflow",
    "home-assistant/core",
    "open-telemetry/opentelemetry-python",
    "open-telemetry/opentelemetry-collector-contrib",
    "containerd/containerd",
    "moby/moby",
    "etcd-io/etcd",
    "prometheus/prometheus",
    "backstage/backstage",
    "argoproj/argo-cd",
    "helm/helm",
    "keycloak/keycloak",
    "quarkusio/quarkus",
    "opensearch-project/OpenSearch",
    "trinodb/trino",
    "apache/pulsar",
    "go-gitea/gitea",
    "traefik/traefik",
    "caddyserver/caddy",
    "cli/cli",
    "docker/compose",
    "ollama/ollama",
    "vllm-project/vllm",
    "pola-rs/polars",
    "duckdb/duckdb",
    "getsentry/sentry-javascript",
    "nodejs/undici",
    "fastify/fastify",
    "storybookjs/storybook",
    "mui/material-ui",
    "excalidraw/excalidraw",
    "supabase/supabase",
    "aws/aws-cdk",
    "pulumi/pulumi",
    "localstack/localstack",
    "dagster-io/dagster",
    "PrefectHQ/prefect",
]


def gh(path: str, raw: bool = False) -> Any:
    args = ["gh", "api", path]
    if raw:
        args.insert(2, "--allow-escape-sequences")
    proc = subprocess.run(args, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace")[:300])
    return proc.stdout if raw else json.loads(proc.stdout or b"null")


def failed_jobs(repo: str, run_id: int, attempt: int | None = None) -> list[dict[str, Any]]:
    path = f"repos/{repo}/actions/runs/{run_id}" + (f"/attempts/{attempt}" if attempt else "") + "/jobs?per_page=100"
    return [j for j in gh(path)["jobs"] if j.get("conclusion") in ("failure", "timed_out", "cancelled")]


def excerpt_for(repo: str, job: dict[str, Any], raw_dir: Path) -> dict[str, Any] | None:
    raw_path = raw_dir / f"{job['id']}.log"
    try:
        raw_path.write_bytes(gh(f"repos/{repo}/actions/jobs/{job['id']}/logs", raw=True))
        text = raw_path.read_text(encoding="utf-8", errors="replace")
    except RuntimeError:
        return None
    finally:
        raw_path.unlink(missing_ok=True)
    if len(text) < 200:
        return None
    ex = extract_error_region(text)
    clean, n = redact(ex.text)
    return {
        "excerpt": clean,
        "redactions": n,
        "failed_step": ex.failed_step,
        "first_failure": redact(ex.first_failure)[0],
        "total_lines": ex.total_lines,
        "failing_tests": failing_tests(clean),
    }


def record(repo: str, lic: str, default_branch: str, run: dict[str, Any], job: dict[str, Any], ex: dict[str, Any], kind: str) -> dict[str, Any]:
    return {
        "id": f"{repo.replace('/', '__')}__{job['id']}",
        "repo": repo,
        "license": lic,
        "default_branch": default_branch,
        "kind": kind,  # "failed" (latest attempt failed) or "rerun_passed" (a later attempt of the same commit passed)
        "run_id": run["id"],
        "run_url": run["html_url"],
        "run_attempt": 1 if kind == "rerun_passed" else run.get("run_attempt", 1),  # the failed job is from attempt 1
        "job_id": job["id"],
        "job_url": job.get("html_url", ""),
        "workflow": run.get("name", ""),
        "workflow_id": run.get("workflow_id"),
        "job_name": job.get("name", ""),
        "job_conclusion": job.get("conclusion"),
        "failed_steps": [s["name"] for s in job.get("steps", []) if s.get("conclusion") == "failure"],
        "event": run.get("event", ""),
        "branch": run.get("head_branch", ""),
        "head_sha": run.get("head_sha", ""),
        "commit_message": (run.get("head_commit") or {}).get("message", "").split("\n")[0][:200],
        "created_at": run.get("created_at", ""),
        "runner": ",".join(job.get("labels", [])),
        **ex,
    }


def collect(out: Path, raw_dir: Path, per_repo_failed: int, per_repo_rerun: int, repos: list[str], offset: int = 0, rerun_pages: int = 3) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        done = {json.loads(line)["repo"] for line in out.read_text(encoding="utf-8").splitlines() if line.strip()}
    with out.open("a", encoding="utf-8", newline="\n") as fh:
        for repo in repos:
            if repo in done:
                continue
            try:
                meta = gh(f"repos/{repo}")
            except RuntimeError as exc:
                print(f"{repo}: {exc}", flush=True)
                continue
            lic = ((meta.get("license") or {}).get("spdx_id")) or ""
            if lic not in ALLOWED:
                print(f"{repo}: skipped, licence {lic}", flush=True)
                continue
            kept = 0
            seen_steps: set[str] = set()
            try:
                runs = gh(f"repos/{repo}/actions/runs?status=failure&per_page=100")["workflow_runs"][offset:] if per_repo_failed else []
                passed = []
                for page in range(1, rerun_pages + 1):
                    batch = gh(f"repos/{repo}/actions/runs?status=success&per_page=100&page={page}")["workflow_runs"]
                    passed += [r for r in batch if r.get("run_attempt", 1) > 1]
                    if len(passed) >= per_repo_rerun * 2 or len(batch) < 100:
                        break
            except RuntimeError as exc:
                print(f"{repo}: {exc}", flush=True)
                continue
            plan = [(r, None, "failed") for r in runs[: per_repo_failed * 3]] + [(r, 1, "rerun_passed") for r in passed[: per_repo_rerun * 2]]
            n_failed = n_rerun = 0
            for run, attempt, kind in plan:
                if (kind == "failed" and n_failed >= per_repo_failed) or (kind == "rerun_passed" and n_rerun >= per_repo_rerun):
                    continue
                try:
                    jobs = failed_jobs(repo, run["id"], attempt)
                except RuntimeError:
                    continue
                for job in jobs:
                    steps = ",".join(s["name"] for s in job.get("steps", []) if s.get("conclusion") == "failure")
                    sig = f"{run.get('name')}|{steps}"
                    if sig in seen_steps and kind == "failed":
                        continue
                    ex = excerpt_for(repo, job, raw_dir)
                    if not ex:
                        continue
                    seen_steps.add(sig)
                    fh.write(json.dumps(record(repo, lic, meta.get("default_branch", "main"), run, job, ex, kind), ensure_ascii=False) + "\n")
                    fh.flush()
                    kept += 1
                    if kind == "failed":
                        n_failed += 1
                    else:
                        n_rerun += 1
                    break
            print(f"{repo}: {kept} excerpts ({n_failed} failed, {n_rerun} passed on re-run)", flush=True)


def enrich(candidates: Path, ids: Path, out: Path, history: int) -> None:
    """Adds the commit's changed files and how often the same job failed in the last N default-branch runs."""
    want = {line.strip() for line in ids.read_text(encoding="utf-8").splitlines() if line.strip()}
    rows = [json.loads(line) for line in candidates.read_text(encoding="utf-8").splitlines() if line.strip()]
    done = set()
    if out.exists():
        done = {json.loads(line)["id"] for line in out.read_text(encoding="utf-8").splitlines() if line.strip()}
    wf_runs: dict[tuple[str, int], list[dict[str, Any]]] = {}
    run_jobs: dict[tuple[str, int], dict[str, str]] = {}
    with out.open("a", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            if row["id"] not in want or row["id"] in done:
                continue
            repo = row["repo"]
            try:
                commit = gh(f"repos/{repo}/commits/{row['head_sha']}")
                row["changed_files"] = [f["filename"] for f in commit.get("files", [])][:40]
                row["changed_files_total"] = len(commit.get("files", []))
            except RuntimeError:
                row["changed_files"], row["changed_files_total"] = [], 0
            key = (repo, int(row["workflow_id"]))
            if key not in wf_runs:
                try:
                    wf_runs[key] = gh(f"repos/{repo}/actions/workflows/{row['workflow_id']}/runs?branch={row['default_branch']}&status=completed&per_page=40")[
                        "workflow_runs"
                    ]
                except RuntimeError:
                    wf_runs[key] = []
            prior = [r for r in wf_runs[key] if r["created_at"] < row["created_at"] and r["id"] != row["run_id"]][:history]
            checked = failed = 0
            for r in prior:
                jk = (repo, r["id"])
                if jk not in run_jobs:
                    try:
                        run_jobs[jk] = {j["name"]: j.get("conclusion") or "" for j in gh(f"repos/{repo}/actions/runs/{r['id']}/jobs?per_page=100")["jobs"]}
                    except RuntimeError:
                        run_jobs[jk] = {}
                if row["job_name"] in run_jobs[jk]:
                    checked += 1
                    failed += run_jobs[jk][row["job_name"]] in ("failure", "timed_out")
            row["default_branch_history"] = {"runs_checked": checked, "job_failed": failed}
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            print(f"{row['id']}: {len(row['changed_files'])} files, failed {failed}/{checked} on {row['default_branch']}", flush=True)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--out", type=Path, required=True)
    c.add_argument("--raw-dir", type=Path, required=True)
    c.add_argument("--failed", type=int, default=6)
    c.add_argument("--rerun", type=int, default=4)
    c.add_argument("--repos", nargs="*", default=REPOS)
    c.add_argument("--offset", type=int, default=0, help="skip the most recent N failed runs (a second pass)")
    c.add_argument("--rerun-pages", type=int, default=3, help="pages of successful runs scanned for re-run attempts")
    e = sub.add_parser("enrich")
    e.add_argument("candidates", type=Path)
    e.add_argument("ids", type=Path)
    e.add_argument("--out", type=Path, required=True)
    e.add_argument("--history", type=int, default=10)
    a = ap.parse_args()
    if a.cmd == "collect":
        collect(a.out, a.raw_dir, a.failed, a.rerun, a.repos, a.offset, a.rerun_pages)
    else:
        enrich(a.candidates, a.ids, a.out, a.history)


if __name__ == "__main__":
    main()
