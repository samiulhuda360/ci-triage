"""Turns a raw GitHub Actions job log into a short excerpt around the first failure.

A job log is often megabytes long. Only the region that explains the failure is kept: the failing step, the first
assertion, stack trace or compiler error in it, and the exit-code lines GitHub adds at the end. Everything is
redacted before it leaves the machine (see `redact.py`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_TIMESTAMP = re.compile(r"^\ufeff?\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z ?")
_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07")
_STEP = re.compile(r"^##\[group\](?:Run |)(.*)$")
_ERROR_ANNOTATION = re.compile(r"^##\[error\]")
_NOISE = re.compile(
    r"^(##\[endgroup\]|##\[debug\]|\s*$|.*\b(Downloading|Downloaded|Unpacking|Receiving objects|Resolving deltas|remote: (Counting|Compressing))\b|"
    r"\s*(shell|env|with):\s*$|shell: /|\s{2}[A-Z_][A-Z0-9_]*: .*$|.*\|\s*Progress: resolved|[\s·.\-*•]{20,}(?: \.\.\.)?$)"
)

# Lines that mark the start of a failure, roughly from the most to the least specific.
FAILURE_MARKERS: list[re.Pattern[str]] = [
    re.compile(r"Traceback \(most recent call last\)"),
    re.compile(r"^\s*(?:_{3,} .* _{3,}|={3,} FAILURES ={3,})"),
    re.compile(r"^FAILED \S+::"),
    re.compile(r"^\s*E\s{2,}\S"),
    re.compile(r"\bAssertionError\b|\bassert(?:ion)? failed\b", re.I),
    re.compile(r"^\s*●\s\S"),
    re.compile(r"^\s*(?:FAIL|✕|×)\s+\S"),
    re.compile(r"^--- FAIL: "),
    re.compile(r"panicked at"),
    re.compile(r"^error(?:\[E\d{4}\])?: "),
    re.compile(r"\berror TS\d{3,5}\b"),
    re.compile(r"^\S+\.(?:py|ts|tsx|js|jsx|go|rs|java|kt|c|cc|cpp|h)[:(]\d+[:,]?\d*\)?:?\s*(?:error|E\d{3}|F\d{3}|W\d{3})", re.I),
    re.compile(r"^npm ERR! |^npm error |ERR_PNPM_|^error An unexpected error|^YN\d{4}:.*(?:error|fail)", re.I),
    re.compile(r"\b(?:No space left on device|ENOSPC|ETIMEDOUT|ECONNRESET|ECONNREFUSED|EAI_AGAIN|503 Service Unavailable|502 Bad Gateway)\b"),
    re.compile(r"\b(?:BUILD FAILED|FAILURE: Build failed|Compilation failed|compilation error)\b", re.I),
    re.compile(r"^(?:Error|ERROR|Fatal|FATAL|fatal)[:!]\s"),
    re.compile(r"\b\w+(?:Error|Exception): "),
    re.compile(r"^\s*\d+\) "),
    re.compile(r"\b(?:FAILED|FAILURE)\b"),
]

_KEY_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"^##\[error\]"), 5),
    (re.compile(r"\b(?:AssertionError|assert|expected|Expected|received|Received|to (?:be|equal)|!=|==)\b"), 4),
    (re.compile(r"\berror(?:\[E\d+\])?:|\berror TS\d+|\bError: |Exception: |panicked at"), 5),
    (re.compile(r"^FAILED |--- FAIL|●|✕| FAILED\b|\bFAIL\b"), 4),
    (
        re.compile(
            r"\b(?:timed? ?out|timeout|ETIMEDOUT|ECONNRESET|No space left|ENOSPC|rate limit|503|502|killed|OOM|out of memory|shutdown signal|lost communication)\b",
            re.I,
        ),
        4,
    ),
    (re.compile(r"\b(?:failed|failure|cannot|could not|unable to|not found|denied)\b", re.I), 2),
    (re.compile(r"\b(?:lockfile|lock file|ERESOLVE|ResolutionImpossible|peer dep|Could not resolve|version solving failed|--locked|--frozen)\b", re.I), 4),
    (re.compile(r"\b(?:secret|token|credential|permission|unauthori[sz]ed|forbidden|403|401|not accessible by integration|Input required)\b", re.I), 3),
    (re.compile(r"exit code \d+|exited with|Process completed with exit code"), 2),
    (re.compile(r"^[-+](?![-+])\S"), 1),
    (re.compile(r"\b(?:would reformat|reformatted|lint|eslint|ruff|flake8|prettier|clippy|gofmt|black)\b", re.I), 3),
]


@dataclass
class Excerpt:
    """The trimmed failure region of one job log."""

    text: str
    failed_step: str = ""
    first_failure: str = ""
    exit_codes: list[str] = field(default_factory=list)
    total_lines: int = 0
    kept_lines: int = 0


def clean_lines(raw: str) -> list[str]:
    """Strips GitHub's timestamps and ANSI colour codes, and drops very long lines' tails."""
    out = []
    for raw_line in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = _ANSI.sub("", _TIMESTAMP.sub("", raw_line)).rstrip()
        out.append(line[:400] + " ..." if len(line) > 400 else line)
    return out


def _is_marker(line: str) -> bool:
    return any(p.search(line) for p in FAILURE_MARKERS)


def extract_error_region(raw: str, before: int = 12, after: int = 45, max_chars: int = 5000) -> Excerpt:
    """Keeps the failing step's first failure with some context, plus GitHub's `##[error]` lines."""
    lines = clean_lines(raw)
    errors = [i for i, line in enumerate(lines) if _ERROR_ANNOTATION.match(line)]
    end = errors[0] if errors else len(lines) - 1
    # The failing step starts at the last "##[group]Run ..." before the first error annotation.
    start = 0
    step = ""
    for i in range(end, -1, -1):
        m = _STEP.match(lines[i])
        if m and lines[i].startswith("##[group]Run "):
            start, step = i, m.group(1).strip()
            break
    first = next((i for i in range(start + 1, end) if _is_marker(lines[i]) and not _ERROR_ANNOTATION.match(lines[i])), None)
    if first is None:
        first = max(start, end - after)
    lo = max(start, first - before)
    hi = min(end, first + after)
    keep = []
    for i in range(lo, hi):
        line = lines[i]
        if i == start and step:
            continue
        if _NOISE.match(line) or (step and i == start + 1 and line.strip() == step):
            continue
        keep.append(line)
    if step:
        keep.insert(0, f"[step] {step[:200]}")
    if hi < end:
        keep.append("...")
    tail = [lines[i] for i in errors[:6]]
    if not errors and lines:
        tail = [line for line in lines[-8:] if line.strip()]
    body = "\n".join(keep)
    if len(body) > max_chars:
        body = body[: max_chars - 4] + "\n..."
    text = body + ("\n" + "\n".join(tail) if tail else "")
    return Excerpt(
        text=text.strip("\n"),
        failed_step=step,
        first_failure=lines[first].strip() if 0 <= first < len(lines) else "",
        exit_codes=[re.sub(r"^##\[error\]", "", t) for t in tail if "exit code" in t],
        total_lines=len(lines),
        kept_lines=len(keep) + len(tail),
    )


def key_lines(excerpt: str, n: int = 5) -> list[str]:
    """The `n` most telling lines of an excerpt, in their original order (for the PR comment)."""
    scored = []
    seen: set[str] = set()
    for i, line in enumerate(excerpt.splitlines()):
        s = line.strip()
        if not s or s == "..." or s in seen or s.startswith("[step]"):
            continue
        seen.add(s)
        score = sum(w for p, w in _KEY_PATTERNS if p.search(s))
        if _is_marker(s):
            score += 2
        if score:
            scored.append((score, i, s[:240]))
    top = sorted(scored, key=lambda t: (-t[0], t[1]))[:n]
    return [s for _, _, s in sorted(top, key=lambda t: t[1])]


_TEST_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^FAILED (\S+::\S+)"),
    re.compile(r"^--- FAIL: (\S+)"),
    re.compile(r"^\s*●\s+(.+?)\s*$"),
    re.compile(r"^test (\S+) \.\.\. FAILED"),
    re.compile(r"^\s*(\S+ > \S+(?: > \S+)?) FAILED"),
    re.compile(r"^\s*(?:FAIL|✕|×)\s+(\S+\.(?:test|spec)\.\w+(?: > .+)?)$"),
    re.compile(r"^\s*\[FAIL\]\s+(.+)$"),
]


def failing_tests(text: str, limit: int = 10) -> list[str]:
    """Names of failing tests found in a log (pytest, Go, Jest/Vitest, cargo, Gradle/JUnit)."""
    found: list[str] = []
    for line in text.splitlines():
        for p in _TEST_PATTERNS:
            m = p.search(line)
            if m:
                name = m.group(1).strip()[:200]
                if name and name not in found and not name.lower().startswith(("console.", "test suite failed")):
                    found.append(name)
                break
        if len(found) >= limit:
            break
    return found
