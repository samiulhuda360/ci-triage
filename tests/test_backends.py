from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from ci_triage.backends import CacheMiss, JevBackend, LlmBackend, RulesBackend, get_backend
from ci_triage.backends.base import choice_confidence, noul_confidence, score_confidence
from ci_triage.backends.llm import build_prompt, parse_reply
from ci_triage.backends.rules import classify
from ci_triage.models import CATEGORIES, Failure
from ci_triage.questions import jev_questions
from ci_triage.state import prepare_state

JEV_RESPONSE = {
    "model": "jev-1.13.0",
    "answers": {
        "category": {"choice": "test_failure", "confidence": 0.82, "probabilities": {**dict.fromkeys(CATEGORIES, 0.02), "test_failure": 0.86}},
        "urgency": {"score": 1, "confidence": 0.7, "legend": {}, "probabilities": {"0": 0.1, "1": 0.8, "2": 0.1}},
        "caused_by_commit": {"noul": 0.91},
        "safe_to_rerun": {"noul": 0.04},
        "needs_code_change": {"noul": 0.95},
    },
    "usage": {"input_tokens": 1200, "output_tokens": 30},
}


class _Resp:
    def __init__(self, status: int, body: dict[str, Any]) -> None:
        self.status_code = status
        self._body = body
        self.text = json.dumps(body)
        self.headers: dict[str, str] = {}

    def json(self) -> dict[str, Any]:
        return self._body


def test_confidence_formulas() -> None:
    assert choice_confidence({"a": 0.5, "b": 0.5}) == 0.0
    assert choice_confidence({"a": 1.0, "b": 0.0}) == 1.0
    assert noul_confidence(0.5) == 0.0 and noul_confidence(0.95) == pytest.approx(0.9)
    assert score_confidence([0.0, 1.0, 0.0]) == 1.0
    assert score_confidence([1 / 3, 1 / 3, 1 / 3]) < 0.1


def test_questions_have_criteria() -> None:
    q = jev_questions()
    assert set(q) == {"category", "urgency", "caused_by_commit", "safe_to_rerun", "needs_code_change"}
    assert list(q["category"]["criteria"]) == list(CATEGORIES)
    assert len(q["urgency"]["criteria"]) == 3
    assert "criteria" not in q["safe_to_rerun"]


def test_jev_parses_records_and_replays(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failure: Failure) -> None:
    calls: list[dict[str, Any]] = []

    def fake_post(url: str, json: dict[str, Any], headers: dict[str, str], timeout: float) -> _Resp:
        calls.append(json)
        assert headers["Authorization"] == "Bearer test-key-not-real"
        return _Resp(200, JEV_RESPONSE)

    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key-not-real")
    monkeypatch.setattr(httpx, "post", fake_post)
    backend = JevBackend(cache_path=tmp_path / "jev.jsonl")
    d = backend.decide(failure)
    assert d.category == "test_failure" and d.category_confidence == 0.82
    assert d.urgency == 1 and d.p("safe_to_rerun") == 0.04
    assert d.input_tokens == 1200 and d.cost_usd == pytest.approx(1200 * 0.042 / 1e6)
    assert calls[0]["model"] == "jev-latest" and set(calls[0]["questions"]) == set(jev_questions())
    # Replay: offline and from a fresh backend, the cached answer comes back with no HTTP call.
    monkeypatch.setenv("CI_TRIAGE_OFFLINE", "1")
    again = JevBackend(cache_path=tmp_path / "jev.jsonl").decide(failure)
    assert again.cached and again.category == "test_failure" and len(calls) == 1


def test_offline_cache_miss(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failure: Failure) -> None:
    monkeypatch.setenv("CI_TRIAGE_OFFLINE", "1")
    with pytest.raises(CacheMiss):
        JevBackend(cache_path=tmp_path / "jev.jsonl").decide(failure)
    with pytest.raises(CacheMiss):
        LlmBackend(cache_path=tmp_path / "llm.jsonl").decide(failure)


def test_jev_retries_on_429(monkeypatch: pytest.MonkeyPatch, failure: Failure) -> None:
    replies = [_Resp(429, {}), _Resp(200, JEV_RESPONSE)]
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key-not-real")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: replies.pop(0))
    monkeypatch.setattr("time.sleep", lambda s: None)
    assert JevBackend().decide(failure).category == "test_failure"


def test_llm_prompt_and_reply(failure: Failure) -> None:
    state, _ = prepare_state(failure)
    prompt = build_prompt(state)
    assert '"flaky_test": p' in prompt and "log_excerpt" in prompt
    reply = json.dumps(
        {
            "category": {"flaky_test": 0.7, "test_failure": 0.2, "infrastructure": 0.1},
            "urgency": {"0": 0.8, "1": 0.2, "2": 0},
            "caused_by_commit": 0.1,
            "safe_to_rerun": "0.85",
            "needs_code_change": None,
        }
    )
    answers = parse_reply("```json\n" + reply + "\n```")
    assert answers["category"].value == "flaky_test"
    assert answers["category"].probabilities["flaky_test"] == pytest.approx(0.7)
    assert answers["urgency"].value == 0
    assert answers["safe_to_rerun"].value == 0.85 and answers["needs_code_change"].value == 0.5


def test_llm_accepts_a_bare_label() -> None:
    answers = parse_reply('{"category": "lint_format", "urgency": {"1": 1}, "caused_by_commit": 0.9, "safe_to_rerun": 0.1, "needs_code_change": 0.9}')
    assert answers["category"].value == "lint_format"


@pytest.mark.parametrize(
    ("text", "category"),
    [
        ("##[error]No space left on device", "infrastructure"),
        ("The runner has received a shutdown signal.", "infrastructure"),
        ("Error: Timeout of 2000ms exceeded. For async tests ...", "flaky_test"),
        ("Error: Input required and not supplied: token", "configuration"),
        ("ERR_PNPM_OUTDATED_LOCKFILE Cannot install with frozen-lockfile", "dependency"),
        ("Would reformat: src/app.py\n1 file would be reformatted (ruff format)", "lint_format"),
        ("src/app.ts(3,7): error TS2322: Type 'string' is not assignable", "compile_error"),
        ("FAILED tests/test_a.py::test_x - AssertionError", "test_failure"),
        ("##[error]Process completed with exit code 1.", "unknown"),
    ],
)
def test_rules_patterns(text: str, category: str) -> None:
    assert classify(text) == category


def test_rules_backend_uses_history(failure: Failure) -> None:
    rules = RulesBackend()
    assert rules.decide(failure).category == "test_failure"
    failure.history_checked, failure.history_failed = 10, 2
    d = rules.decide(failure)
    assert d.category == "flaky_test" and d.p("safe_to_rerun") > 0.5 and d.urgency == 0


def test_get_backend_auto(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    assert get_backend("auto").name == "rules"
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key-not-real")
    assert get_backend("auto").name == "jev"
    with pytest.raises(ValueError, match="unknown backend"):
        get_backend("nope")
