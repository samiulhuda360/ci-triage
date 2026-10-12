"""The five typed questions asked about every failed job, in one Jev call."""

from __future__ import annotations

from typing import Any

from .models import CATEGORIES, NOULS, URGENCY_LEVELS

CATEGORY_INSTRUCTIONS = (
    "Classify the CI failure shown in log_excerpt. Look at failed_step and at the first error, assertion or exit message in the "
    "excerpt. Use default_branch_history: a test that also fails now and then on the default branch is likely flaky. Choose the "
    "category of the root cause, not of the final 'exit code 1' line."
)
URGENCY_INSTRUCTIONS = "How urgent is this failure for the team? branch_type says whether it ran on the default branch or a pull request."


def jev_questions() -> dict[str, Any]:
    questions: dict[str, Any] = {
        "category": {"type": "choice", "instructions": CATEGORY_INSTRUCTIONS, "criteria": dict(CATEGORIES)},
        "urgency": {"type": "score", "instructions": URGENCY_INSTRUCTIONS, "criteria": list(URGENCY_LEVELS)},
    }
    for name, statement in NOULS.items():
        questions[name] = {"type": "noul", "instructions": statement}
    return questions
