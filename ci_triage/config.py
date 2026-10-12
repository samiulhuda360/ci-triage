"""Per-repository policy, read from `.github/ci-triage.yml`. Every key is optional."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = ".github/ci-triage.yml"


@dataclass
class Rerun:
    enabled: bool = True
    categories: list[str] = field(default_factory=lambda: ["flaky_test", "infrastructure"])
    min_confidence: float = 0.6  # category confidence needed to re-run without a person
    min_safe_to_rerun: float = 0.7  # P(a re-run would pass)
    max_caused_by_commit: float = 0.3  # P(the commit caused it) must stay below this
    max_per_day: int = 10  # per repository
    only_first_attempt: bool = True  # re-run once, never loop


@dataclass
class Labels:
    enabled: bool = True
    prefix: str = "ci:"  # ci:flaky-test, ci:test-failure, ...
    needs_human: str = "ci:needs-human"
    rerun: str = "ci:auto-rerun"


@dataclass
class Notify:
    default_branch_only: bool = True  # only main-branch breaks
    min_urgency: int = 2
    slack_webhook_env: str = "CI_TRIAGE_SLACK_WEBHOOK"
    teams_webhook_env: str = "CI_TRIAGE_TEAMS_WEBHOOK"


@dataclass
class Flaky:
    store: str = ".ci-triage/flaky.db"
    report_days: int = 7
    report_top: int = 10


@dataclass
class Suggest:
    enabled: bool = False  # the optional LLM fix suggestion
    categories: list[str] = field(default_factory=lambda: ["test_failure", "compile_error", "lint_format", "dependency"])
    cache_dir: str = ".ci-triage/suggestions"


@dataclass
class Config:
    backend: str = "auto"
    dry_run: bool = False
    needs_human_confidence: float = 0.5
    comment: bool = True
    step_summary: bool = True
    key_lines: int = 5
    max_jobs: int = 4  # failed jobs judged per run
    history_runs: int = 10  # default-branch runs checked for the same job
    ignore_jobs: list[str] = field(default_factory=list)
    rerun: Rerun = field(default_factory=Rerun)
    labels: Labels = field(default_factory=Labels)
    notify: Notify = field(default_factory=Notify)
    flaky: Flaky = field(default_factory=Flaky)
    suggest: Suggest = field(default_factory=Suggest)
    audit_log: str = ".ci-triage/audit.jsonl"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        cfg = cls()
        nested: dict[str, Any] = {"rerun": cfg.rerun, "labels": cfg.labels, "notify": cfg.notify, "flaky": cfg.flaky, "suggest": cfg.suggest}
        for f in fields(cls):
            if f.name not in data:
                continue
            if f.name in nested:
                target = nested[f.name]
                for key, value in (data[f.name] or {}).items():
                    if not hasattr(target, key):
                        raise ValueError(f"unknown key {f.name}.{key} in the ci-triage policy")
                    setattr(target, key, value)
            else:
                setattr(cfg, f.name, data[f.name])
        unknown = set(data) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError(f"unknown keys in the ci-triage policy: {', '.join(sorted(unknown))}")
        return cfg


def load_config(path: str | Path | None = None, text: str | None = None) -> Config:
    """Loads the policy from a file or from YAML text; a missing file gives the defaults."""
    if text is None:
        p = Path(path or DEFAULT_CONFIG_PATH)
        if not p.exists():
            return Config()
        text = p.read_text(encoding="utf-8")
    return Config.from_dict(yaml.safe_load(text) or {})
