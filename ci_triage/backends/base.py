"""The decision-backend interface and the confidence formulas every backend shares."""

from __future__ import annotations

import os
from typing import Protocol

from ..models import Decision, Failure


class BackendError(RuntimeError):
    """The backend could not produce a decision."""


class CacheMiss(BackendError):
    """Offline mode is on and the response is not in the cache."""


class Backend(Protocol):
    name: str
    model: str

    def decide(self, failure: Failure) -> Decision: ...


def offline() -> bool:
    """CI and replay runs set CI_TRIAGE_OFFLINE=1 so no live API is ever called."""
    return os.environ.get("CI_TRIAGE_OFFLINE", "") not in ("", "0", "false")


def choice_confidence(probs: dict[str, float]) -> float:
    """TypeSafe's Choice confidence: how far the top probability sits above an even split."""
    n = len(probs)
    if n < 2:
        return 1.0
    top = max(probs.values())
    return max(0.0, min(1.0, (top - 1 / n) / (1 - 1 / n)))


def score_confidence(probs: list[float]) -> float:
    """TypeSafe's Score confidence: 1 - (expected distance from the peak / mean distance from the middle level)."""
    n = len(probs)
    if n < 2:
        return 1.0
    total = sum(probs) or 1.0
    p = [x / total for x in probs]
    peak = max(range(n), key=lambda i: p[i])
    spread = sum(x * abs(i - peak) for i, x in enumerate(p))
    even = sum(abs(i - (n - 1) / 2) for i in range(n)) / n
    return max(0.0, min(1.0, 1 - spread / even)) if even else 1.0


def noul_confidence(p: float) -> float:
    """|2p - 1|: the Choice formula applied to a yes/no question."""
    return abs(2 * p - 1)


def normalise(values: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, v) for v in values.values())
    if total <= 0:
        return {k: 1 / len(values) for k in values}
    return {k: max(0.0, v) / total for k, v in values.items()}
