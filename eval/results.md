# Evaluation results

200 CI failure excerpts: 196 real failed jobs from public GitHub Actions runs of 61 MIT or Apache-2.0 repositories, and 4 invented excerpts (2.0%) for categories that are rare in public logs (marked `invented` in the data). Labelled by the rules in [LABELLING.md](LABELLING.md).

Gold categories: flaky test 25, test failure 25, compile error 25 (2 invented), lint format 25, dependency 25 (1 invented), infrastructure 25, configuration 25, unknown 25 (1 invented).

Every number below comes from recorded real API responses (`eval/cache/`), replayed by `ci-triage eval`.

## All 200 failures: Regex rules, Jev

### Headline

Default policy: re-run automatically only when the category is flaky test or infrastructure with confidence of at least 0.6, P(safe to re-run) is at least 0.7 and P(caused by this commit) is below 0.3. A *wrong* re-run is one whose gold category is anything else: a real failure that will fail again.

| | Regex rules | Jev |
|---|---|---|
| Category accuracy | 40.0% | 69.5% |
| Category macro-F1 | 0.414 | 0.692 |
| Automatic re-runs (default policy) | 38 | 18 |
| **Wrong automatic re-runs** (real failures re-run) | **17** | **1** |
| Flaky/infra failures re-run automatically (recall) | 42.0% | 34.0% |
| Decided automatically (confidence >= 0.6) | 87.5% | 77.5% |
| Accuracy on the automatic share | 44.0% | 76.8% |
| Brier score, category (lower is better) | 0.360 | 0.195 |
| Latency p50 / p95 | under 20 ms (local) / under 20 ms (local) | 467 ms / 583 ms |
| Cost per 1,000 failures | $0.0000 | $0.0817 |

### Automation at different confidence thresholds

The threshold is the minimum category confidence. Below it the failure is labelled `ci:needs-human` (escalated) and never re-run. The other re-run conditions stay at their defaults.

**Regex rules**

| Min confidence | Decided automatically | Accuracy on that share | Escalated | Auto re-runs | Wrong re-runs | Flaky/infra re-run |
|---|---|---|---|---|---|---|
| 0.3 | 175 (87.5%) | 44.0% | 25 | 38 | 17 | 42.0% |
| 0.4 | 175 (87.5%) | 44.0% | 25 | 38 | 17 | 42.0% |
| 0.5 | 175 (87.5%) | 44.0% | 25 | 38 | 17 | 42.0% |
| 0.6 | 175 (87.5%) | 44.0% | 25 | 38 | 17 | 42.0% |
| 0.7 | 175 (87.5%) | 44.0% | 25 | 38 | 17 | 42.0% |
| 0.8 | 0 (0.0%) | n/a | 200 | 0 | 0 | 0.0% |
| 0.9 | 0 (0.0%) | n/a | 200 | 0 | 0 | 0.0% |

**Jev**

| Min confidence | Decided automatically | Accuracy on that share | Escalated | Auto re-runs | Wrong re-runs | Flaky/infra re-run |
|---|---|---|---|---|---|---|
| 0.3 | 187 (93.5%) | 70.1% | 13 | 19 | 1 | 36.0% |
| 0.4 | 180 (90.0%) | 72.8% | 20 | 19 | 1 | 36.0% |
| 0.5 | 174 (87.0%) | 73.6% | 26 | 18 | 1 | 34.0% |
| 0.6 | 155 (77.5%) | 76.8% | 45 | 18 | 1 | 34.0% |
| 0.7 | 147 (73.5%) | 78.2% | 53 | 18 | 1 | 34.0% |
| 0.8 | 136 (68.0%) | 82.4% | 64 | 17 | 1 | 32.0% |
| 0.9 | 121 (60.5%) | 85.1% | 79 | 16 | 1 | 30.0% |

### The re-run gate

Same default policy, changing only the minimum P(safe to re-run). Lower gates re-run more of the flaky and infrastructure failures, at the risk of re-running real ones.

| Min P(safe to re-run) | Regex rules: re-runs / wrong / flaky-infra recall | Jev: re-runs / wrong / flaky-infra recall |
|---|---|---|
| 0.5 | 38 / 17 / 42.0% | 30 / 3 / 54.0% |
| 0.6 | 38 / 17 / 42.0% | 30 / 3 / 54.0% |
| 0.7 (default) | 38 / 17 / 42.0% | 18 / 1 / 34.0% |
| 0.8 | 38 / 17 / 42.0% | 5 / 1 / 8.0% |

### Per category (F1)

| Category (gold count) | Regex rules | Jev |
|---|---|---|
| flaky test (25) | 0.28 (P 0.28, R 0.28) | 0.46 (P 0.44, R 0.48) |
| test failure (25) | 0.24 (P 0.19, R 0.32) | 0.50 (P 0.43, R 0.60) |
| compile error (25) | 0.63 (P 0.65, R 0.60) | 0.86 (P 0.76, R 1.00) |
| lint format (25) | 0.45 (P 0.36, R 0.60) | 0.86 (P 0.88, R 0.84) |
| dependency (25) | 0.33 (P 0.55, R 0.24) | 0.75 (P 0.78, R 0.72) |
| infrastructure (25) | 0.62 (P 0.86, R 0.48) | 0.79 (P 0.83, R 0.76) |
| configuration (25) | 0.65 (P 0.78, R 0.56) | 0.89 (P 0.95, R 0.84) |
| unknown (25) | 0.12 (P 0.12, R 0.12) | 0.42 (P 0.62, R 0.32) |

### The yes/no questions and urgency

| | Regex rules | Jev |
|---|---|---|
| `caused_by_commit` accuracy / F1 / Brier | 67.0% / 0.683 / 0.237 | 82.5% / 0.793 / 0.128 |
| `safe_to_rerun` accuracy / F1 / Brier | 77.5% / 0.494 / 0.184 | 85.5% / 0.688 / 0.096 |
| `needs_code_change` accuracy / F1 / Brier | 63.0% / 0.724 / 0.270 | 79.0% / 0.832 / 0.150 |
| Urgency exact accuracy | 75.0% | 59.5% |
| Urgency mean absolute error | 0.29 | 0.41 |
| Real excerpts only: category accuracy / macro-F1 | 39.3% / 0.405 | 68.9% / 0.685 |

### Calibration

Brier score: the mean squared gap between the stated probability and what was true (lower is better).

| | Regex rules | Jev |
|---|---|---|
| Brier, category (top probability vs correct) | 0.360 | 0.195 |
| Brier, the three yes/no questions pooled | 0.230 | 0.125 |

Reliability of the category answer: stated top probability vs how often it was right.

| Bin | Regex rules (n, stated, observed) | Jev (n, stated, observed) |
|---|---|---|
| 0.0-0.3 | - | - |
| 0.3-0.5 | - | 10, 0.42, 0.00 |
| 0.5-0.7 | 25, 0.50, 0.12 | 33, 0.60, 0.52 |
| 0.7-0.8 | - | 15, 0.75, 0.40 |
| 0.8-0.9 | 175, 0.80, 0.44 | 19, 0.85, 0.63 |
| 0.9-1.0 | - | 123, 0.98, 0.85 |

### Confusion (rows: gold, columns: predicted)

**Regex rules**

| gold \ predicted | flaky | test | compi | lint | depen | infra | confi | unkno |
|---|---|---|---|---|---|---|---|---|
| flaky_test | 7 | 11 | 1 | 2 | 1 | 1 | 1 | 1 |
| test_failure | 6 | 8 | 0 | 10 | 0 | 0 | 0 | 1 |
| compile_error | 0 | 2 | 15 | 4 | 2 | 0 | 0 | 2 |
| lint_format | 1 | 2 | 0 | 15 | 0 | 0 | 2 | 5 |
| dependency | 1 | 2 | 5 | 3 | 6 | 0 | 0 | 8 |
| infrastructure | 2 | 5 | 2 | 1 | 1 | 12 | 0 | 2 |
| configuration | 2 | 3 | 0 | 2 | 0 | 1 | 14 | 3 |
| unknown | 6 | 9 | 0 | 5 | 1 | 0 | 1 | 3 |

**Jev**

| gold \ predicted | flaky | test | compi | lint | depen | infra | confi | unkno |
|---|---|---|---|---|---|---|---|---|
| flaky_test | 12 | 9 | 0 | 0 | 0 | 3 | 0 | 1 |
| test_failure | 7 | 15 | 1 | 0 | 1 | 0 | 0 | 1 |
| compile_error | 0 | 0 | 25 | 0 | 0 | 0 | 0 | 0 |
| lint_format | 1 | 1 | 0 | 21 | 0 | 0 | 0 | 2 |
| dependency | 0 | 0 | 6 | 1 | 18 | 0 | 0 | 0 |
| infrastructure | 1 | 0 | 0 | 0 | 4 | 19 | 0 | 1 |
| configuration | 0 | 1 | 1 | 1 | 0 | 1 | 21 | 0 |
| unknown | 6 | 9 | 0 | 1 | 0 | 0 | 1 | 8 |

### Speed and cost

| | Regex rules | Jev |
|---|---|---|
| Latency p50 | under 20 ms (local) | 467 ms |
| Latency p95 | under 20 ms (local) | 583 ms |
| Input tokens per failure (mean) | 0 | 1946 |
| Output tokens per failure (mean) | 0 | 154 |
| Cost per 1,000 failures | $0.0000 | $0.0817 |

## All backends on the 74 failures every backend answered

LLM (Gemini Flash-Lite) answered 74 of the 200 failures (the free-tier request quota of its API), so this section compares every backend on the same 74 failures.
They are the first items of the data file, so they are not balanced: flaky test 2, compile error 23, dependency 24, configuration 25. Re-run numbers on this subset say little, because it holds almost no flaky or infrastructure failures.

### Headline

Default policy: re-run automatically only when the category is flaky test or infrastructure with confidence of at least 0.6, P(safe to re-run) is at least 0.7 and P(caused by this commit) is below 0.3. A *wrong* re-run is one whose gold category is anything else: a real failure that will fail again.

| | Regex rules | Jev | LLM (Gemini Flash-Lite) |
|---|---|---|---|
| Category accuracy | 44.6% | 83.8% | 82.4% |
| Category macro-F1 | 0.426 | 0.819 | 0.641 |
| Automatic re-runs (default policy) | 4 | 1 | 0 |
| **Wrong automatic re-runs** (real failures re-run) | **4** | **0** | **0** |
| Flaky/infra failures re-run automatically (recall) | 0.0% | 50.0% | 0.0% |
| Decided automatically (confidence >= 0.6) | 81.1% | 90.5% | 100.0% |
| Accuracy on the automatic share | 55.0% | 88.1% | 82.4% |
| Brier score, category (lower is better) | 0.299 | 0.105 | 0.165 |
| Latency p50 / p95 | under 20 ms (local) / under 20 ms (local) | 472 ms / 589 ms | 1731 ms / 3159 ms |
| Cost per 1,000 failures | $0.0000 | $0.0755 | $0.2437 |

### Automation at different confidence thresholds

The threshold is the minimum category confidence. Below it the failure is labelled `ci:needs-human` (escalated) and never re-run. The other re-run conditions stay at their defaults.

**Regex rules**

| Min confidence | Decided automatically | Accuracy on that share | Escalated | Auto re-runs | Wrong re-runs | Flaky/infra re-run |
|---|---|---|---|---|---|---|
| 0.3 | 60 (81.1%) | 55.0% | 14 | 4 | 4 | 0.0% |
| 0.4 | 60 (81.1%) | 55.0% | 14 | 4 | 4 | 0.0% |
| 0.5 | 60 (81.1%) | 55.0% | 14 | 4 | 4 | 0.0% |
| 0.6 | 60 (81.1%) | 55.0% | 14 | 4 | 4 | 0.0% |
| 0.7 | 60 (81.1%) | 55.0% | 14 | 4 | 4 | 0.0% |
| 0.8 | 0 (0.0%) | n/a | 74 | 0 | 0 | 0.0% |
| 0.9 | 0 (0.0%) | n/a | 74 | 0 | 0 | 0.0% |

**Jev**

| Min confidence | Decided automatically | Accuracy on that share | Escalated | Auto re-runs | Wrong re-runs | Flaky/infra re-run |
|---|---|---|---|---|---|---|
| 0.3 | 74 (100.0%) | 83.8% | 0 | 1 | 0 | 50.0% |
| 0.4 | 71 (95.9%) | 87.3% | 3 | 1 | 0 | 50.0% |
| 0.5 | 71 (95.9%) | 87.3% | 3 | 1 | 0 | 50.0% |
| 0.6 | 67 (90.5%) | 88.1% | 7 | 1 | 0 | 50.0% |
| 0.7 | 63 (85.1%) | 90.5% | 11 | 1 | 0 | 50.0% |
| 0.8 | 60 (81.1%) | 91.7% | 14 | 1 | 0 | 50.0% |
| 0.9 | 53 (71.6%) | 90.6% | 21 | 0 | 0 | 0.0% |

**LLM (Gemini Flash-Lite)**

| Min confidence | Decided automatically | Accuracy on that share | Escalated | Auto re-runs | Wrong re-runs | Flaky/infra re-run |
|---|---|---|---|---|---|---|
| 0.3 | 74 (100.0%) | 82.4% | 0 | 0 | 0 | 0.0% |
| 0.4 | 74 (100.0%) | 82.4% | 0 | 0 | 0 | 0.0% |
| 0.5 | 74 (100.0%) | 82.4% | 0 | 0 | 0 | 0.0% |
| 0.6 | 74 (100.0%) | 82.4% | 0 | 0 | 0 | 0.0% |
| 0.7 | 73 (98.6%) | 82.2% | 1 | 0 | 0 | 0.0% |
| 0.8 | 71 (95.9%) | 83.1% | 3 | 0 | 0 | 0.0% |
| 0.9 | 64 (86.5%) | 85.9% | 10 | 0 | 0 | 0.0% |

### The re-run gate

Same default policy, changing only the minimum P(safe to re-run). Lower gates re-run more of the flaky and infrastructure failures, at the risk of re-running real ones.

| Min P(safe to re-run) | Regex rules: re-runs / wrong / flaky-infra recall | Jev: re-runs / wrong / flaky-infra recall | LLM (Gemini Flash-Lite): re-runs / wrong / flaky-infra recall |
|---|---|---|---|
| 0.5 | 4 / 4 / 0.0% | 2 / 1 / 50.0% | 0 / 0 / 0.0% |
| 0.6 | 4 / 4 / 0.0% | 2 / 1 / 50.0% | 0 / 0 / 0.0% |
| 0.7 (default) | 4 / 4 / 0.0% | 1 / 0 / 50.0% | 0 / 0 / 0.0% |
| 0.8 | 4 / 4 / 0.0% | 0 / 0 / 0.0% | 0 / 0 / 0.0% |

### Per category (F1)

| Category (gold count) | Regex rules | Jev | LLM (Gemini Flash-Lite) |
|---|---|---|---|
| flaky test (2) | 0.00 (P 0.00, R 0.00) | 0.67 (P 1.00, R 0.50) | 0.00 (P 0.00, R 0.00) |
| compile error (23) | 0.65 (P 0.70, R 0.61) | 0.87 (P 0.77, R 1.00) | 0.84 (P 0.72, R 1.00) |
| dependency (24) | 0.33 (P 0.83, R 0.21) | 0.83 (P 1.00, R 0.71) | 0.77 (P 1.00, R 0.62) |
| configuration (25) | 0.72 (P 1.00, R 0.56) | 0.91 (P 1.00, R 0.84) | 0.96 (P 1.00, R 0.92) |

### The yes/no questions and urgency

| | Regex rules | Jev | LLM (Gemini Flash-Lite) |
|---|---|---|---|
| `caused_by_commit` accuracy / F1 / Brier | 79.7% / 0.815 / 0.174 | 89.2% / 0.886 / 0.098 | 85.1% / 0.871 / 0.131 |
| `safe_to_rerun` accuracy / F1 / Brier | 91.9% / 0.000 / 0.070 | 94.6% / 0.333 / 0.038 | 97.3% / 0.000 / 0.024 |
| `needs_code_change` accuracy / F1 / Brier | 70.3% / 0.823 / 0.176 | 94.6% / 0.964 / 0.076 | 79.7% / 0.878 / 0.186 |
| Urgency exact accuracy | 87.8% | 58.1% | 95.9% |
| Urgency mean absolute error | 0.15 | 0.42 | 0.04 |
| Real excerpts only: category accuracy / macro-F1 | 44.6% / 0.426 | 83.8% / 0.819 | 82.4% / 0.641 |

### Calibration

Brier score: the mean squared gap between the stated probability and what was true (lower is better).

| | Regex rules | Jev | LLM (Gemini Flash-Lite) |
|---|---|---|---|
| Brier, category (top probability vs correct) | 0.299 | 0.105 | 0.165 |
| Brier, the three yes/no questions pooled | 0.140 | 0.071 | 0.114 |

Reliability of the category answer: stated top probability vs how often it was right.

| Bin | Regex rules (n, stated, observed) | Jev (n, stated, observed) | LLM (Gemini Flash-Lite) (n, stated, observed) |
|---|---|---|---|
| 0.0-0.3 | - | - | - |
| 0.3-0.5 | - | 3, 0.41, 0.00 | - |
| 0.5-0.7 | 14, 0.50, 0.00 | 7, 0.63, 0.57 | - |
| 0.7-0.8 | - | 3, 0.75, 0.67 | 1, 0.70, 1.00 |
| 0.8-0.9 | 60, 0.80, 0.55 | 8, 0.85, 1.00 | 2, 0.80, 0.50 |
| 0.9-1.0 | - | 53, 0.98, 0.91 | 71, 0.99, 0.83 |

### Confusion (rows: gold, columns: predicted)

**Regex rules**

| gold \ predicted | flaky | test | compi | lint | depen | infra | confi | unkno |
|---|---|---|---|---|---|---|---|---|
| flaky_test | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 |
| compile_error | 0 | 2 | 14 | 4 | 1 | 0 | 0 | 2 |
| dependency | 1 | 2 | 5 | 3 | 5 | 0 | 0 | 8 |
| configuration | 2 | 3 | 0 | 2 | 0 | 1 | 14 | 3 |

**Jev**

| gold \ predicted | flaky | test | compi | lint | depen | infra | confi | unkno |
|---|---|---|---|---|---|---|---|---|
| flaky_test | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| compile_error | 0 | 0 | 23 | 0 | 0 | 0 | 0 | 0 |
| dependency | 0 | 0 | 6 | 1 | 17 | 0 | 0 | 0 |
| configuration | 0 | 1 | 1 | 1 | 0 | 1 | 21 | 0 |

**LLM (Gemini Flash-Lite)**

| gold \ predicted | flaky | test | compi | lint | depen | infra | confi | unkno |
|---|---|---|---|---|---|---|---|---|
| flaky_test | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| compile_error | 0 | 0 | 23 | 0 | 0 | 0 | 0 | 0 |
| dependency | 0 | 0 | 8 | 1 | 15 | 0 | 0 | 0 |
| configuration | 0 | 0 | 0 | 2 | 0 | 0 | 23 | 0 |

### Speed and cost

| | Regex rules | Jev | LLM (Gemini Flash-Lite) |
|---|---|---|---|
| Latency p50 | under 20 ms (local) | 472 ms | 1731 ms |
| Latency p95 | under 20 ms (local) | 589 ms | 3159 ms |
| Input tokens per failure (mean) | 0 | 1798 | 1741 |
| Output tokens per failure (mean) | 0 | 154 | 174 |
| Cost per 1,000 failures | $0.0000 | $0.0755 | $0.2437 |

Jev pricing: $0.042 per million input tokens, output free. The LLM cost uses an assumed list price of $0.10 / $0.40 per million input / output tokens
for the default model (the evaluation ran on a free tier). The regex baseline makes no API call.
