# Labelling guide

Every item in `data/failures.jsonl` is one failed CI job: a trimmed, redacted log excerpt plus the metadata ci-triage
collects (workflow, job, failing step, event and branch, commit message, changed files, and how often the same job
failed in the last 10 runs on the default branch). Each item gets five labels in `data/labels.jsonl`. They were
assigned by reading the excerpt and the metadata, with the rules below, by one labeller.

The labeller also saw one piece of evidence the backends never see: **whether the same commit later passed when the
run was re-run** (`kind: rerun_passed` in the data, from GitHub's run attempts). In real use that outcome is unknown
at decision time, which is exactly why ci-triage has to predict it.

## 1. Category

Pick the category of the **root cause**, not of the final `Process completed with exit code 1` line. When several
apply, the first matching rule in this order wins.

1. **Infrastructure or runner** (`infrastructure`). The job failed for a reason outside the code and outside the test
   logic: the runner lost communication or shut down, the job hit the workflow or step time limit, it was cancelled
   by a timeout, out of disk (`No space left on device`) or memory (`exit code 137`, `Killed`), a network or DNS
   error while downloading tools, images or packages (`ECONNRESET`, `502`, `503`, `Could not resolve host`), a rate
   limit of an external service, or an outage of a service the job calls (a registry, an upload service).
2. **Configuration or secrets** (`configuration`). A secret, token or credential is missing or invalid (typical on
   pull requests from forks, which receive no secrets), the token lacks a permission (`Resource not accessible by
   integration`, `403`), an action input is missing, or the workflow, environment or tool is misconfigured (a wrong
   path, a missing environment, an unsupported option in a CI config file). Pull-request process checks that fail
   on metadata rather than on code (a required label, milestone, linked issue, approval or template section) also
   count here.
3. **Dependency or lockfile** (`dependency`). Installing or resolving packages failed for a reason in the
   dependency set: an outdated or inconsistent lockfile (`--frozen-lockfile`, `--locked`, `uv lock --check`), a
   version conflict (`ERESOLVE`, `ResolutionImpossible`), a package or version that does not exist, or a new release
   of a dependency that breaks the build or tests (when the log makes that clear, for example a deprecation turned
   error from a library upgrade picked up without a code change).
4. **Lint or format** (`lint_format`). A linter, formatter, spell checker, type-stub or style check, a generated file
   or a docs check that compares output with the committed files (`git diff --exit-code` after a generator), a
   commit-message, sign-off (DCO) or PR-title check, or a changelog check.
5. **Compile, build or type error** (`compile_error`). Compiler errors, TypeScript or mypy-style type errors reported
   by the compiler, bundler errors, syntax errors, missing imports or symbols at build time.
6. **Flaky test** (`flaky_test`). A test failed and **at least one** of these holds: the same commit passed when
   re-run; the same job also failed now and then on the default branch without a related change; or the failure is
   characteristic of non-determinism (a timing assertion, a timeout inside a test, a port or file already in use, an
   ordering or race message) and the changed files do not touch the failing area.
7. **Real test failure** (`test_failure`). A test assertion or test error with no sign of flakiness: deterministic
   output differences (snapshots, expected vs received values, a missing case), on a commit that touches related code
   or on the default branch right after such a change.
8. **Unknown** (`unknown`). The excerpt does not show what failed (for example only `exit code 1` with no error
   text), and the metadata does not settle it.

Notes:

- A timeout **of the whole job** is infrastructure. A timeout **inside one test** (`Test timed out in 5000ms`) is a
  flaky test unless the change clearly made that test slower or hang.
- A failing **end-to-end test** that times out waiting for a page or a service is a flaky test when the same commit
  passed on re-run, and a real test failure otherwise only if the log shows a deterministic assertion.
- Benchmarks or size checks that fail on a threshold count as real test failures.
- When `kind` is `rerun_passed`, the category must be flaky test or infrastructure (or configuration, if a secret or
  token was temporarily unavailable).

## 2. Caused by the changes in this commit (`caused_by_commit`)

`true` when the failure comes from the code, tests, lockfile or configuration changed in this commit (or pull
request): real test failures, compile errors, lint failures, and dependency or configuration failures introduced by
the changed files. `false` for flaky tests, infrastructure, a missing secret on a fork pull request, failures that
also happen on the default branch for the same reason, and failures caused by a new upstream release.

## 3. Safe to re-run (`safe_to_rerun`)

`true` when re-running the job without any change would most likely pass: flaky tests and infrastructure failures
(and a transient credential or rate-limit problem). `false` for every deterministic failure.

## 4. Needs a code change (`needs_code_change`)

`true` when making the job pass needs a commit to the repository: real test failures, compile errors, lint and
format failures, lockfile and dependency fixes, and configuration errors in files inside the repository (workflow
files, tool configs). `false` for flaky tests (a re-run passes), infrastructure, and secrets or permissions that are
set in the repository or organisation settings rather than in code.

## 5. Urgency (`urgency`, 0 to 2)

- **2, high:** the failure is on the default branch, a release, a merge queue or a scheduled build, and it is not a
  flaky test or an infrastructure blip.
- **0, low:** a flaky test or an infrastructure failure, on any branch.
- **1, medium:** everything else (a deterministic failure on a pull request or feature branch, or an unknown failure).

## Selection and balance

Candidates were collected from the failed and re-run jobs of about 60 public repositories (`scripts/harvest.py`).
Items were selected to balance the categories and to cover many repositories, languages and tools; within a
category, items were chosen without looking at any backend's answer. Categories that are rare in public logs were
topped up with invented excerpts written for this evaluation, marked `"invented": true` in `failures.jsonl`; their
share is reported in `results.md`.
