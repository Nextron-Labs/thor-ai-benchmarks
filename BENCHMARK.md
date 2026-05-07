# THOR Finding Triage Benchmark

This benchmark evaluates LLM models on their ability to triage THOR findings — classifying each finding as True Positive (TP), False Positive (FP), or Inconclusive (Inc) based on enriched THOR event context.

## Overview

THOR is a forensic scanner that detects potentially malicious activity on endpoints. Each detection (finding) requires human triage to determine if it represents a real threat, a benign artifact, or if the evidence is insufficient to decide.

This benchmark measures how well LLMs perform this triage task when given the same enriched THOR event context provided to all benchmarked models. The goal is to compare models on a level playing field, measuring their direct triage ability based on enriched THOR context without model-specific prompt tuning or external tool integrations.

## Input Data

### Ground Truth

Human expert classifications and expert priority scores define the reference answer for each finding. Ground truth files contain:
- Finding ID
- Ground truth classification (TP/FP/Inc)
- Human expert priority score

Ground truth is maintained separately for each report (R1 through R7).

### THOR Reports

Input data comes from THOR JSONL reports. Each report contains events that may be flagged as findings. The benchmark only scores "seed" findings (`is_seed: true`) — these are the detections that THOR identified as potentially significant.

Models receive the full event context including:
- Detection rule name and category
- Event metadata (timestamps, paths, hashes)
- Related context events
- Native THOR scoring

## Scoring Methodology

### Primary Metric: CW% (Confidence-Weighted Accuracy)

The CW score weighs each classification by both correctness and confidence. Confidence is dampened so that calibrated confidence matters, but low-confidence hedging is not rewarded too strongly:
- Exact match (TP→TP, FP→FP, Inc→Inc): full credit
- Minor miss (distance 1): partial credit (e.g., TP↔Inc, FP↔Inc)
- Hard error (distance 2): penalty (TP↔FP)

This means confident correct answers receive more credit than hesitant correct answers, while confident wrong answers are penalized more strongly. Confidence influences the score, but it does not dominate the underlying classification distance.

### Secondary Metrics

| Metric | Description |
|--------|-------------|
| **Ord%** | Ordinal accuracy — simpler scoring without confidence weighting |
| **MAE** | Mean Absolute Error between the model's priority score and the human expert score |
| **RMSE** | Root Mean Square Error — penalizes large score deviations more heavily |

### Classification Accuracy Breakdown

The charts show how each model's classifications break down:

| Category | Meaning | Distance |
|----------|---------|----------|
| **Exact match** | Correct classification | 0 |
| **Minor miss** | Off by one step (TP↔Inc, FP↔Inc) | 1 |
| **Missed threat** | TP classified as FP — real threat dismissed | 2 |
| **Over-call** | FP classified as TP — false alarm escalated | 2 |
| **LLM error** | Model failed to respond | — |
| **Other (unclassified)** | Residual bucket for findings that could not be mapped cleanly into the standard categories | — |

`Other (unclassified)` is not a separate ordinal distance category. With the benchmark scale FP(0), Inc(1), TP(2), the only distance-2 transitions are FP→TP and TP→FP. If this bucket appears in a chart, it represents findings that could not be mapped cleanly into the standard buckets, for example because of parsing or labeling inconsistencies.

### Ground Truth Counts

| Report | Findings |
|--------|----------|
| R1 | 16 |
| R2 | 7 |
| R3 | 21 |
| R4 | 6 |
| R5 | 23 |
| R6 | 68 |
| R7 | 16 |
| **Total** | **157** |

## Timing & Cost

Each model's speed is measured as `avg_seconds_per_event` — the total elapsed processing time divided by the number of findings reviewed.

Timing data is extracted from mjolnir-ai's built-in statistics:
- `elapsed_seconds` — total runtime
- `events_reviewed` — number of findings processed
- `total_tokens` — token consumption

This allows comparison of both quality (CW%) and efficiency (speed, estimated cost) across models. Cost is derived from token usage together with model pricing, not from token counts alone.

## Charts Explained

### CW% Leaderboard
Overall ranking by confidence-weighted accuracy. Higher is better.

### CW vs MAE
Plots quality (CW%) against score prediction accuracy (MAE). Lower MAE = better score prediction.

### Classification Breakdown
Stacked bars showing how each model's classifications are distributed across accuracy categories. More green (exact) and blue (minor) is better.

### Quality vs Cost
CW% plotted against estimated cost per benchmark run, derived from token usage and model pricing. Shows which models give the best quality per dollar.

### Quality vs Speed
CW% plotted against processing time. Shows which models are fastest while maintaining accuracy.

### Tier Breakdowns
Separate charts for closed-source, open-source-pro, and open-source-consumer tiers to enable fair comparisons within each category.

---

## Prompt Design

We intentionally use a simple and fairly neutral prompt.

The goal is to compare the models on the same plain surface, with as little additional influence as possible from model-specific prompt tuning. A very detailed or strongly opinionated prompt can change how a model behaves. It may push one model closer to the expected answer while making another model perform worse, simply because different models react differently to instructions, wording and examples.

That would make the benchmark less about the model's own triage ability and more about how well the prompt happens to fit a certain model family.

For this reason, the prompt provides the task, the expected output structure and the classification options, but avoids heavy steering. We do not try to "coach" the model into a specific analyst style. The model should assess the finding based on the provided event context, not based on a long list of hints that already encode parts of the answer.

This does not mean prompt tuning is unimportant in production. It is very important. But for this benchmark, we want the prompt to be stable, simple and comparable across models.

---

## No External Tool Use

We also intentionally do not allow external tool use during the benchmark.

Each model receives the same enriched THOR event context and has to assess it from that input alone. There is no VirusTotal lookup, no sandbox query, no SIEM search, no EDR artifact retrieval and no internal knowledge base lookup during scoring.

The reason is similar to the prompt decision: once tools are added, the benchmark no longer measures only the model's triage ability. It starts measuring a combined system of model, prompt, tool selection, tool quality, available data and integration design.

That may be closer to a real SOC workflow, but it is much harder to compare fairly. Every organization has a different tool stack, different telemetry, different asset context and different enrichment quality. There is no realistic "average SOC toolset" that would make such a benchmark generally comparable.

Tool use can absolutely improve results in practice, especially when the tools provide high-quality context. But then the result depends heavily on the tools and not only on the model. For this benchmark, we want to measure how well the model interprets the enriched THOR event context itself.
