"""The single PR comment (or run summary): category, the five most telling log lines and a next step."""

from __future__ import annotations

from dataclasses import dataclass

from .logs import key_lines
from .models import Decision, Failure
from .policy import TITLES, URGENCY, Outcome
from .redact import redact

MARKER = "<!-- ci-triage -->"


@dataclass
class JobVerdict:
    failure: Failure
    decision: Decision
    outcome: Outcome
    suggestion: str | None = None


def _job_section(v: JobVerdict, n_lines: int) -> list[str]:
    f, d, o = v.failure, v.decision, v.outcome
    title = TITLES.get(o.category, o.category)
    link = f"[{f.job_name}]({f.job_url})" if f.job_url else f"`{f.job_name}`"
    lines = [
        f"### {link}: {title}",
        "",
        f"**Category:** {title} (confidence {d.category_confidence:.2f}) · **Urgency:** {URGENCY[o.urgency]} · "
        f"**Caused by this commit:** {d.p('caused_by_commit'):.0%} · **Safe to re-run:** {d.p('safe_to_rerun'):.0%} · "
        f"**Needs a code change:** {d.p('needs_code_change'):.0%}",
        "",
    ]
    if f.failed_step:
        lines += [f"Failed step: `{f.failed_step[:120]}`", ""]
    shown = key_lines(redact(f.excerpt)[0], n_lines)
    if shown:
        lines += ["```text", *shown, "```", ""]
    lines += [f"**Next step:** {o.next_step}", ""]
    if o.needs_human:
        lines += ["> The answer is uncertain, so this failure is labelled for a person to look at.", ""]
    if v.suggestion:
        lines += ["<details><summary>Suggested fix (AI-generated suggestion, check it before applying)</summary>", "", v.suggestion, "", "</details>", ""]
    return lines


def render_comment(verdicts: list[JobVerdict], action: str, dry_run: bool = False, n_lines: int = 5, note: str = "") -> str:
    head = "ci-triage re-ran the failed jobs" if action == "rerun" else "ci-triage: why this run failed"
    if dry_run:
        head += " (dry run: nothing was changed)"
    lines = [MARKER, f"## {head}", ""]
    if action == "rerun":
        lines += [
            "Every failed job looks like a flaky test or an infrastructure problem that this commit did not cause, so the failed jobs were re-run once.",
            "",
        ]
    if note:
        lines += [note, ""]
    for v in verdicts:
        lines += _job_section(v, n_lines)
    d = verdicts[0].decision if verdicts else None
    if d:
        lines.append(
            f"<sub>Decided by {d.backend} ({d.model}). {sum(v.decision.redactions for v in verdicts)} secret-looking values were redacted before anything was sent.</sub>"
        )
    return "\n".join(lines).rstrip() + "\n"
