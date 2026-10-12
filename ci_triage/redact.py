"""Secret redaction. Every log excerpt passes through here before it is sent anywhere or stored."""

from __future__ import annotations

import re

REDACTED = "[REDACTED]"

# Whole-match patterns: the full match is replaced.
_TOKEN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"-----BEGIN[ A-Z0-9_-]{0,40}PRIVATE KEY-----[\s\S]*?(?:-----END[ A-Z0-9_-]{0,40}PRIVATE KEY-----|$)"),
    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bsk-(?:live-|test-|proj-|ant-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"\bnpm_[A-Za-z0-9]{36}\b"),
    re.compile(r"\bpypi-[A-Za-z0-9_-]{50,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/_-]+"),
    re.compile(r"https://[a-z0-9.-]*webhook\.office\.com/[^\s\"']+", re.I),
]
# Keep the key name, replace the value.
_ASSIGNMENT = re.compile(
    r"""(?ix)
    (\b[\w.-]*(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|client[_-]?secret|credentials?|auth)[\w.-]*
     ["']?\s*[:=]\s*["']?)
    ([^\s"',;]{6,})
    """
)
_BEARER = re.compile(r"(?i)(\b(?:bearer|basic|token)\s+)([A-Za-z0-9._~+/=-]{12,})")
_URL_CREDENTIALS = re.compile(r"([a-z][a-z0-9+.-]*://[^\s:/@]+:)([^\s@/]+)(@)", re.I)
_EMAIL = re.compile(r"(?<![\w.%+-])(?!git@)[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com)[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_LONG_HEX = re.compile(r"(?i)\b(?=[a-f0-9]*[a-f])(?=[a-f0-9]*\d)[a-f0-9]{48,}\b")
# Values that are clearly placeholders, masks or references, not secrets.
_SAFE_VALUE = re.compile(
    r"(?i)^(?:\$\{\{.*|\$\{?[A-Z_][A-Z0-9_]*\}?|os\.environ.*|process\.env.*|env\(.*|getenv.*|<[^>]+>|x{3,}|\*{3,}|none|null|true|false|"
    r"changeme|example|placeholder|required|missing|invalid|expired|undefined|\[REDACTED\].*)"
)


def redact(text: str) -> tuple[str, int]:
    """Returns the text with likely secrets replaced, and how many were replaced."""
    count = 0

    def sub_all(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return REDACTED

    for pattern in _TOKEN_PATTERNS:
        text = pattern.sub(sub_all, text)

    def sub_value(m: re.Match[str]) -> str:
        nonlocal count
        value = m.group(2)
        if _SAFE_VALUE.match(value) or (value.isalpha() and value.islower()):
            return m.group(0)
        count += 1
        return m.group(1) + REDACTED

    text = _ASSIGNMENT.sub(sub_value, text)
    text = _BEARER.sub(sub_value, text)

    def sub_url(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return m.group(1) + REDACTED + m.group(3)

    text = _URL_CREDENTIALS.sub(sub_url, text)
    text = _LONG_HEX.sub(sub_all, text)
    text = _EMAIL.sub("[EMAIL]", text)
    return text, count
