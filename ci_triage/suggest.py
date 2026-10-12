"""The optional fix suggestion: one paragraph from an OpenAI-compatible model, for real failures only.

It is cached on disk by prompt hash, never called in offline mode, and always shown as a suggestion.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import httpx

from .backends.base import offline
from .cache import JsonlCache, cache_key
from .models import Decision, Failure
from .policy import TITLES
from .state import prepare_state

DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
DEFAULT_MODEL = "gemini-flash-lite-latest"
SYSTEM = (
    "You help developers fix failing CI jobs. Given a failure excerpt, write one short paragraph (at most 90 words) with the most "
    "likely fix. Name the file, test or command when the log shows it. If the log does not show enough, say what to check. "
    "No preamble, no code blocks longer than one line."
)


def build_prompt(failure: Failure, decision: Decision) -> str:
    state, _ = prepare_state(failure, max_excerpt=3500)
    return (
        f"Category: {TITLES.get(decision.category, decision.category)}\nJob: {state['job']}\nFailed step: {state['failed_step']}\n"
        f"Changed files: {', '.join(state['changed_files'])}\n\nLog excerpt:\n{state['log_excerpt']}"
    )


def suggest_fix(failure: Failure, decision: Decision, cache_dir: Path | None = None) -> str | None:
    """Returns the suggestion paragraph, or None when no model is configured or it fails."""
    prompt = build_prompt(failure, decision)
    model = os.environ.get("AI_MODEL", DEFAULT_MODEL)
    cache = JsonlCache(cache_dir / "suggestions.jsonl" if cache_dir else None)
    key = cache_key({"suggest": model, "prompt": prompt})
    hit = cache.get(key)
    if hit:
        return str(hit["text"])
    api_key = os.environ.get("AI_API_KEY", "")
    if offline() or not api_key:
        return None
    base = os.environ.get("AI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    body = {"model": model, "temperature": 0, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]}
    for attempt in range(3):
        try:
            resp = httpx.post(f"{base}/chat/completions", json=body, headers={"Authorization": f"Bearer {api_key}"}, timeout=60)
        except httpx.TransportError:
            return None
        if resp.status_code in (429, 503) and attempt < 2:
            time.sleep(15 * (attempt + 1))
            continue
        if resp.status_code != 200:
            return None
        text = (resp.json()["choices"][0]["message"]["content"] or "").strip()
        if not text:
            return None
        cache.put(key, {"text": text, "model": model})
        return text
    return None
