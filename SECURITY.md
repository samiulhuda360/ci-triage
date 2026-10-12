# Security policy

## Reporting a vulnerability

Please report security problems privately through GitHub's "Report a vulnerability" button on this repository
(Security tab), not in a public issue. You should get a first answer within five working days. Include the version
or commit, what you did, what happened and, if you can, a minimal way to reproduce it.

## Why logs need care

CI logs are one of the easiest places for a secret to leak: a debug line prints an environment variable, a failing
`curl` echoes its `Authorization` header, a stack trace includes a connection string. GitHub masks the secrets it
knows about (`***`), but not values a tool derived from them, and not secrets that never went through
`secrets.*`. ci-triage therefore treats every log as sensitive.

## What is sent, and what is not

For each failed job, ci-triage builds one small JSON "state" and sends it to the decision backend:

| Sent | Not sent |
|---|---|
| The workflow, job and failing step names | The full job log (often megabytes) |
| A trimmed excerpt of the log around the first failure: at most about 5,000 characters, redacted | Any other step's output |
| The branch type (pull request, default branch, schedule) and branch name | Your source files or the diff |
| The first line of the commit message, redacted | Environment variables or secrets |
| Up to 25 changed file paths (names only, no content) | Artifacts, caches or other runs' logs |
| How often the same job failed in the last 10 default-branch runs (two numbers) | Commit author and committer details |
| Names of failing tests found in the excerpt | |

- **Where it goes.** With the `jev` backend the state goes to the TypeSafe AI API (`api.typesafe.ai`). With the
  `llm` backend it goes to the OpenAI-compatible endpoint you configure. The `rules` backend sends nothing.
- **The optional fix suggestion** (`suggest.enabled: true`, off by default) sends the same redacted excerpt (at most
  about 3,500 characters), the job and step names and the changed file paths to the OpenAI-compatible endpoint in
  `AI_BASE_URL`. It runs only for real failures, and its answer is cached on disk and shown as a suggestion.

## What is redacted

Before anything is sent or stored, the excerpt and the commit message pass through `ci_triage/redact.py`, which
replaces likely secrets with `[REDACTED]`:

- private key blocks (`-----BEGIN ... PRIVATE KEY-----`), even when the end marker was trimmed off;
- common token formats: GitHub (`ghp_`, `gho_`, `ghs_`, `github_pat_`), GitLab, Slack (`xox?-`), OpenAI-style
  `sk-`, Google API keys, npm and PyPI tokens, AWS access key IDs, JSON Web Tokens;
- Slack and Teams incoming-webhook URLs;
- `password=`, `token:`, `api_key=`, `secret`, `client_secret`, `credentials`, `auth` style assignments (the key
  name is kept, the value replaced);
- `Bearer`, `Basic` and `token` credentials in headers;
- passwords inside URLs (`https://user:password@host`);
- long hexadecimal strings of 48 characters or more (Git commit hashes, at 40, are kept);
- e-mail addresses, replaced with `[EMAIL]` (GitHub `noreply` addresses are kept).

References such as `${{ secrets.X }}`, `$TOKEN`, `process.env.X` and `os.environ[...]`, and GitHub's own `***`
masks, are kept because they are not secrets. The comment says how many values were redacted. Redaction is a
safety net, not a guarantee: keep secrets out of logs with `::add-mask::` and by not echoing them.

## What ci-triage can do in your repository

ci-triage acts with the token you give it. With the permissions in the example workflow it can:

| Permission | Used for |
|---|---|
| `actions: write` | reading run, job and log data; re-running failed jobs; the flaky-test store in the Actions cache |
| `pull-requests: write`, `issues: write` | the `ci:*` labels and the one triage comment |
| `contents: read` | reading `.github/ci-triage.yml` |

It never pushes code and never changes workflow files. It re-runs a run at most once (`only_first_attempt`), only
when every failed job in it looks flaky or infrastructure-related, and at most `rerun.max_per_day` times per
repository per day. `dry_run: true` makes it write the run summary only.

The example workflow runs on `workflow_run`, which executes the workflow file from your default branch, so code
from a pull request (including one from a fork) is never checked out or run by ci-triage. The failed run's logs
are read as data.

## Stored data

- **Audit log.** Every decision is appended to a JSONL audit log (`.ci-triage/audit.jsonl` by default;
  `/data/audit.jsonl` in the container): repository, run, job, branch, commit SHA, failing test names, the typed
  answers and their confidence, the action taken, latency, tokens and cost. It contains no log text. Rotate or ship
  it like any other application log.
- **Flaky-test store.** A small SQLite file (`.ci-triage/flaky.db`, or `/data/flaky.db`) with one row per failed
  job or test: time, repository, run ID, job and test name, category, branch and confidence. In GitHub Actions it is
  kept in the Actions cache of the repository.
- **Response cache.** When `CI_TRIAGE_CACHE_DIR` is set, the redacted state and the backend's answer are cached on
  disk by request hash.

## Secrets ci-triage needs

`TYPESAFE_API_KEY` (or `AI_API_KEY` for the `llm` backend and the suggestion), the GitHub token, and in the service
`CI_TRIAGE_WEBHOOK_SECRET` and optional chat webhook URLs. Store them as repository or organisation secrets
(Actions) or in your secret manager (container). ci-triage never logs or prints them.

## Webhook service

The self-hosted service rejects every webhook without a valid `X-Hub-Signature-256` HMAC signature for
`CI_TRIAGE_WEBHOOK_SECRET` (compared in constant time), refuses to start without that secret, and rejects payloads
over 5 MB. Run it behind HTTPS. The container runs as an unprivileged user and writes only to `/data`.
