"""The regex baseline most teams start with: match well-known log patterns, first match wins. No model."""

from __future__ import annotations

import re
import time

from ..models import CATEGORIES, RERUNNABLE, Answer, Decision, Failure
from .base import choice_confidence, noul_confidence, score_confidence

# (category, pattern), checked in this order against the failing step and the log excerpt.
RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "infrastructure",
        re.compile(
            r"No space left on device|ENOSPC|runner has received a shutdown signal|lost communication with the server|The operation was canceled|"
            r"exceeded the maximum execution time|job (?:was )?cancel+ed|ETIMEDOUT|ECONNRESET|ECONNREFUSED|EAI_AGAIN|socket hang up|"
            r"503 Service Unavailable|502 Bad Gateway|504 Gateway|429 Too Many Requests|rate limit|Connection (?:reset|refused|timed out)|"
            r"Could not resolve host|TLS handshake|out of memory|OOMKilled|\bKilled\b|exit code 137|Read timed out",
            re.I,
        ),
    ),
    (
        "flaky_test",
        re.compile(r"\bflaky\b|\bflake\b|intermittent|Test timed out|Timeout of \d+ ?ms exceeded|timed out after \d+|deadlock|race condition", re.I),
    ),
    (
        "configuration",
        re.compile(
            r"Input required and not supplied|Bad credentials|Resource not accessible by integration|secret|\b401\b|\b403\b|Unauthori[sz]ed|"
            r"Forbidden|permission denied|Permission to .* denied|token (?:is )?(?:missing|invalid|required)|Invalid workflow|not configured",
            re.I,
        ),
    ),
    (
        "dependency",
        re.compile(
            r"ERESOLVE|lockfile|lock file|frozen-lockfile|ResolutionImpossible|No matching distribution|Could not find a version|version solving failed|"
            r"Cargo\.lock|--locked|npm ERR! 404|E404|missing go\.sum|go mod tidy|peer dep|dependency conflict|Unable to resolve dependency|"
            r"Could not resolve dependencies|package .* not found",
            re.I,
        ),
    ),
    (
        "lint_format",
        re.compile(
            r"\beslint\b|prettier|\bruff\b|flake8|\bblack\b|clippy|gofmt|golangci|would reformat|Code style issues|\blint\b|linter|"
            r"git diff --exit-code|spell|codespell|\bmypy\b|isort|stylelint|markdownlint|\bformat\b",
            re.I,
        ),
    ),
    (
        "compile_error",
        re.compile(
            r"error TS\d+|error\[E\d+\]|could not compile|SyntaxError|cannot find symbol|undefined reference|Compilation failed|"
            r"BUILD FAILED|Build failed|ModuleNotFoundError|ImportError|Cannot find module|is not defined|undefined: \w+|cannot find package",
            re.I,
        ),
    ),
    (
        "test_failure",
        re.compile(
            r"\bFAIL\b|\bFAILED\b|AssertionError|\bassert|Expected|--- FAIL|panicked at|Tests? failed|test result: FAILED|\d+ failed|"
            r"\bfailures?\b",
            re.I,
        ),
    ),
]


def classify(text: str) -> str:
    for category, pattern in RULES:
        if pattern.search(text):
            return category
    return "unknown"


class RulesBackend:
    name = "rules"
    model = "regex-rules"

    def decide(self, failure: Failure) -> Decision:
        start = time.perf_counter()
        category = classify(f"{failure.failed_step}\n{failure.excerpt}")
        # The other common rule of thumb: a failing test that also fails now and then on the default branch is flaky.
        if category == "test_failure" and failure.history_failed > 0:
            category = "flaky_test"
        top = 0.5 if category == "unknown" else 0.8
        cprobs = {k: (top if k == category else (1 - top) / (len(CATEGORIES) - 1)) for k in CATEGORIES}
        rerun = category in RERUNNABLE
        nouls = {
            "caused_by_commit": 0.15 if rerun else (0.4 if category in ("configuration", "unknown") else 0.8),
            "safe_to_rerun": 0.85 if rerun else 0.1,
            "needs_code_change": 0.1 if rerun else (0.5 if category in ("configuration", "unknown") else 0.9),
        }
        level = 0 if rerun else (2 if failure.on_default_branch else 1)
        uprobs = [0.9 if i == level else 0.05 for i in range(3)]
        answers = {
            "category": Answer("choice", category, choice_confidence(cprobs), cprobs),
            "urgency": Answer("score", level, score_confidence(uprobs), {str(i): p for i, p in enumerate(uprobs)}),
        }
        for name, p in nouls.items():
            answers[name] = Answer("noul", p, noul_confidence(p), {"yes": p, "no": 1 - p})
        return Decision(backend=self.name, model=self.model, answers=answers, latency_ms=(time.perf_counter() - start) * 1000)
