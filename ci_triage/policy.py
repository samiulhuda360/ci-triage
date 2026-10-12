"""The policy in code: what to do with one failed job, given the typed answers. No model is involved here."""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import Config
from .models import Decision, Failure

TITLES = {
    "flaky_test": "Flaky test",
    "test_failure": "Test failure",
    "compile_error": "Compile or type error",
    "lint_format": "Lint or format",
    "dependency": "Dependency or lockfile",
    "infrastructure": "Infrastructure or runner",
    "configuration": "Configuration or secrets",
    "unknown": "Unknown",
}
NEXT_STEPS = {
    "flaky_test": "Re-run the failed job. If the same test fails again, quarantine or fix it: it has failed without a related change.",
    "test_failure": "Reproduce the failing test locally and fix the code or the test; a re-run will fail the same way.",
    "compile_error": "Fix the build or type error shown above; run the project's build or type check locally before pushing.",
    "lint_format": "Run the project's formatter or linter locally (for example `pre-commit run --all-files`) and commit the result.",
    "dependency": "Update the lockfile or fix the version constraint (run the package manager's install or lock command and commit it).",
    "infrastructure": "Re-run the failed job. If it keeps failing, check the runner, the network or the external service it depends on.",
    "configuration": "Check the repository's secrets, tokens and workflow permissions; forks do not receive secrets.",
    "unknown": "Open the job log: the excerpt does not show enough to classify this failure.",
}
URGENCY = ["low", "medium", "high"]


def label_for(category: str, cfg: Config) -> str:
    return cfg.labels.prefix + category.replace("_", "-")


@dataclass
class Outcome:
    """What ci-triage decided for one failed job."""

    category: str
    action: str  # rerun | report
    rerun_eligible: bool
    needs_human: bool
    urgency: int
    labels: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    next_step: str = ""
    notify: bool = False


def apply_policy(f: Failure, d: Decision, cfg: Config, reruns_today: int = 0) -> Outcome:
    r = cfg.rerun
    category, conf = d.category, d.category_confidence
    reasons: list[str] = []
    blockers: list[str] = []
    if not r.enabled:
        blockers.append("automatic re-runs are turned off")
    if category not in r.categories:
        blockers.append(f"category is {TITLES.get(category, category).lower()}")
    if conf < r.min_confidence:
        blockers.append(f"category confidence {conf:.2f} is below {r.min_confidence:.2f}")
    if d.p("safe_to_rerun") < r.min_safe_to_rerun:
        blockers.append(f"P(re-run passes) {d.p('safe_to_rerun'):.2f} is below {r.min_safe_to_rerun:.2f}")
    if d.p("caused_by_commit") >= r.max_caused_by_commit:
        blockers.append(f"P(caused by this commit) {d.p('caused_by_commit'):.2f} is not below {r.max_caused_by_commit:.2f}")
    if r.only_first_attempt and f.run_attempt > 1:
        blockers.append(f"this is already attempt {f.run_attempt}")
    if reruns_today >= r.max_per_day:
        blockers.append(f"the daily re-run cap ({r.max_per_day}) is reached")
    eligible = not blockers
    needs_human = conf < cfg.needs_human_confidence or category == "unknown"
    if eligible:
        reasons.append(f"{TITLES[category].lower()} with confidence {conf:.2f}, P(re-run passes) {d.p('safe_to_rerun'):.2f}")
    else:
        reasons += blockers if category in r.categories else blockers[:1]
    labels = [label_for(category, cfg)] if cfg.labels.enabled else []
    if eligible and cfg.labels.enabled:
        labels.append(cfg.labels.rerun)
    if needs_human and cfg.labels.enabled:
        labels.append(cfg.labels.needs_human)
    urgency = d.urgency
    notify = urgency >= cfg.notify.min_urgency and (f.on_default_branch or not cfg.notify.default_branch_only) and not eligible
    return Outcome(
        category=category,
        action="rerun" if eligible else "report",
        rerun_eligible=eligible,
        needs_human=needs_human,
        urgency=urgency,
        labels=labels,
        reasons=reasons,
        next_step=NEXT_STEPS.get(category, NEXT_STEPS["unknown"]),
        notify=notify,
    )


def run_action(outcomes: list[Outcome]) -> str:
    """A run is re-run only when every failed job in it qualifies: re-running would otherwise retry a real failure too."""
    return "rerun" if outcomes and all(o.rerun_eligible for o in outcomes) else "report"
