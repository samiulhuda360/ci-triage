"""Decision backends: `jev`, `llm` and `rules`, behind one interface."""

from __future__ import annotations

import os
from pathlib import Path

from .base import Backend, BackendError, CacheMiss
from .jev import JevBackend
from .llm import LlmBackend
from .rules import RulesBackend

__all__ = ["Backend", "BackendError", "CacheMiss", "JevBackend", "LlmBackend", "RulesBackend", "get_backend"]


def get_backend(name: str = "auto", cache_dir: Path | None = None) -> Backend:
    """`auto` uses Jev when TYPESAFE_API_KEY is set, and the rules baseline otherwise.

    Responses are cached in `cache_dir`, or in CI_TRIAGE_CACHE_DIR when that is set.
    """
    if cache_dir is None and os.environ.get("CI_TRIAGE_CACHE_DIR"):
        cache_dir = Path(os.environ["CI_TRIAGE_CACHE_DIR"])
    if name == "auto":
        name = "jev" if os.environ.get("TYPESAFE_API_KEY") else "rules"
    if name == "jev":
        return JevBackend(cache_path=cache_dir / "jev.jsonl" if cache_dir else None)
    if name == "llm":
        return LlmBackend(cache_path=cache_dir / "llm.jsonl" if cache_dir else None)
    if name == "rules":
        return RulesBackend()
    raise ValueError(f"unknown backend {name!r} (use jev, llm, rules or auto)")
