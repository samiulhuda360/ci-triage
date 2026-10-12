"""The committed evaluation replays from the recorded responses, with no network."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ci_triage.evaluate import CACHE, DATA, evaluate, load_items, render_markdown
from ci_triage.models import CATEGORIES, RERUNNABLE


def test_dataset_is_balanced_and_consistent() -> None:
    items = load_items()
    assert len(items) == 200
    counts = {c: sum(1 for i in items if i.gold["category"] == c) for c in CATEGORIES}
    assert set(counts.values()) == {25}
    for it in items:
        g = it.gold
        assert g["safe_to_rerun"] == (g["category"] in RERUNNABLE) or g["category"] == "configuration", it.id
        assert g["urgency"] in (0, 1, 2)
        if g["category"] in RERUNNABLE:
            assert g["urgency"] == 0 and not g["needs_code_change"], it.id
    invented = [i for i in items if i.invented]
    assert len(invented) == 4 and all(i.id.startswith("invented__") for i in invented)


def test_every_real_item_has_a_source_link() -> None:
    sources = (DATA / "SOURCES.md").read_text(encoding="utf-8")
    for line in (DATA / "failures.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if not row["invented"]:
            assert row["license"] in ("MIT", "Apache-2.0")
            assert row["run_url"].startswith("https://github.com/") and f"`{row['id']}`" in sources


@pytest.mark.skipif(not (CACHE / "jev.jsonl").exists(), reason="no recorded Jev responses")
def test_offline_replay(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CI_TRIAGE_OFFLINE", "1")
    res = evaluate(["rules", "jev"])
    assert "jev" in res["backends"], "every labelled failure must have a recorded Jev response"
    jev, rules = res["backends"]["jev"], res["backends"]["rules"]
    assert jev["policy_default"]["wrong_reruns"] <= rules["policy_default"]["wrong_reruns"]
    assert "# Evaluation results" in render_markdown(res)
