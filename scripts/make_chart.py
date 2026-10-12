"""Draws the headline chart (docs/build/chart.html) from eval/results.json: re-runs that were right and wrong, and
the share of failures each backend decided on its own at the default threshold."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TITLES = {"rules": "Regex rules", "jev": "Jev", "llm": "LLM (Gemini Flash-Lite)"}
RIGHT, WRONG, AUTO = "#008f7e", "#c4622d", "#5b7f95"


def main() -> None:
    res = json.loads((ROOT / "eval" / "results.json").read_text(encoding="utf-8"))
    group = {"n": res["n"], "backends": res["backends"]}  # every backend that answered all failures
    rows = [(TITLES.get(k, k), v) for k, v in group["backends"].items()]
    n = group["n"]
    gold_rerunnable = max(
        round(v["policy_default"]["right_reruns"] / v["policy_default"]["rerun_recall"]) for _, v in rows if v["policy_default"]["rerun_recall"]
    )
    width, left, bar, gap, step = 1180, 150, 20, 4, 96
    scale = (width - left - 380) / max(n, 1)
    height = 70 + step * len(rows)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img" aria-label="Automatic re-runs and automatic decisions per backend">'
    ]
    y = 60
    for title, r in rows:
        p = r["policy_default"]
        parts.append(f'<text x="{left - 14}" y="{y + bar + 14}" text-anchor="end" class="name">{title}</text>')
        bars = (
            (p["right_reruns"], RIGHT, f"{p['right_reruns']} flaky or infrastructure failures re-run"),
            (p["wrong_reruns"], WRONG, f"{p['wrong_reruns']} real failure{'' if p['wrong_reruns'] == 1 else 's'} re-run by mistake"),
            (p["automated"], AUTO, f"{p['automated']} decided without a person ({100 * p['automated_accuracy']:.0f}% correct)"),
        )
        for i, (value, color, label) in enumerate(bars):
            by = y + i * (bar + gap)
            w = max(value * scale, 2)
            parts.append(f'<rect x="{left}" y="{by}" width="{w:.1f}" height="{bar}" rx="4" fill="{color}"><title>{title}: {label}</title></rect>')
            parts.append(f'<text x="{left + w + 8:.1f}" y="{by + 15}" class="val">{label}</text>')
        y += step
    parts.append(f'<line x1="{left}" x2="{left}" y1="50" y2="{y - 20}" class="axis"/>')
    parts.append("</svg>")
    legend = (
        f'<span class="sw" style="background:{RIGHT}"></span>Flaky or infrastructure failure, re-run automatically '
        f'<span class="sw" style="background:{WRONG};margin-left:16px"></span>Real failure re-run by mistake '
        f'<span class="sw" style="background:{AUTO};margin-left:16px"></span>Decided without a person'
    )
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>ci-triage results</title><style>
body{{margin:0;padding:24px;background:#fcfcfb;font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#1d2b29}}
h1{{font-size:20px;margin:0 0 6px}} .legend{{font-size:14px;color:#3d4f4c;margin:0 0 6px}}
.sw{{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}}
.name{{font-size:15px;fill:#1d2b29}} .val{{font-size:13px;fill:#3d4f4c}} .axis{{stroke:#9aa9a6;stroke-width:1}} .foot{{font-size:13px;color:#5f7471;margin:6px 0 0}}
</style></head><body><h1>Triaging {n} labelled CI failures: what each backend did on its own</h1><div class="legend">{legend}</div>{"".join(parts)}<p class="foot">{gold_rerunnable} of the {n} failures were flaky tests or infrastructure problems that a re-run fixes. Default policy: re-run only when the category confidence is at least 0.6, P(re-run passes) at least 0.7 and P(caused by the commit) below 0.3.</p></body></html>"""
    out = ROOT / "docs" / "build" / "chart.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
