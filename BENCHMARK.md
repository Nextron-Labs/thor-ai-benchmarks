# THOR Finding Triage Benchmark

This benchmark evaluates LLM models on their ability to triage THOR forensic findings — classifying each finding as True Positive (TP), False Positive (FP), or Inconclusive (Inc) based on the event context.

## Overview

THOR is a forensic analysis tool that detects potentially malicious activity on endpoints. Each detection (finding) requires human triage to determine if it represents a real threat, a benign artifact, or if the evidence is insufficient to decide.

This benchmark measures how well LLMs perform this triage task when given the same enriched context that a human analyst would see. The goal is to compare models on a level playing field, measuring their raw classification ability without prompt engineering tricks or external tool integrations.

## Input Data

### Ground Truth

Expert classifications (Florian's assessments) define the correct answer for each finding. Ground truth files contain:
- Finding ID
- Ground truth classification (TP/FP/Inc)
- Analyst confidence score (Florian's personal assessment weight)

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

The CW score weighs each classification by both correctness and confidence:
- Exact match (TP→TP, FP→FP, Inc→Inc): full credit
- Minor miss (distance 1): partial credit (e.g., TP↔Inc, FP↔Inc)
- Hard error (distance 2): penalty (TP↔FP)

The confidence weighting means models that express uncertainty when unsure can score higher than models that confidently give wrong answers.

### Secondary Metrics

| Metric | Description |
|--------|-------------|
| **Ord%** | Ordinal accuracy — simpler scoring without confidence weighting |
| **MAE** | Mean Absolute Error between model's priority score and analyst's score |
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
| **Other (unclassified)** | Hard errors not in TP↔FP category | 2 |

Hard errors (distance 2) that don't fall into TP↔FP transitions (e.g., FP→Inc, Inc→TP) appear as "unclassified" since they're less severe than missing a real threat or escalating a false one.

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

This allows comparison of both quality (CW%) and efficiency (speed, cost) across models.

## Charts Explained

### CW% Leaderboard
Overall ranking by confidence-weighted accuracy. Higher is better.

### CW vs MAE
Plots quality (CW%) against score prediction accuracy (MAE). Lower MAE = better score prediction.

### Classification Breakdown
Stacked bars showing how each model's classifications are distributed across accuracy categories. More green (exact) and blue (minor) is better.

### Quality vs Cost
CW% plotted against token usage. Shows which models give the best quality per dollar.

### Quality vs Speed
CW% plotted against processing time. Shows which models are fastest while maintaining accuracy.

### Tier Breakdowns
Separate charts for closed-source, open-source-pro, and open-source-consumer tiers to enable fair comparisons within each category.

---

## Prompt Design

We intentionally use a simple and fairly neutral prompt.

The goal is to compare the models on the same plain surface, with as little additional influence as possible from prompt engineering. A very detailed or strongly opinionated prompt can change how a model behaves. It may push one model closer to the expected answer while making another model perform worse, simply because different models react differently to instructions, wording and examples.

That would make the benchmark less about the model's own triage ability and more about how well the prompt happens to fit a certain model family.

For this reason, the prompt provides the task, the expected output structure and the classification options, but avoids heavy steering. We do not try to "coach" the model into a specific analyst style. The model should assess the finding based on the provided event context, not based on a long list of hints that already encode parts of the answer.

This does not mean prompt engineering is unimportant in production. It is very important. But for this benchmark, we want the prompt to be stable, simple and comparable across models.

---

## No External Tool Use

We also intentionally do not allow external tool use during the benchmark.

Each model receives the same enriched THOR finding and has to assess it from that input alone. There is no VirusTotal lookup, no sandbox query, no SIEM search, no EDR artifact retrieval and no internal knowledge base lookup during scoring.

The reason is similar to the prompt decision: once tools are added, the benchmark no longer measures only the model's triage ability. It starts measuring a combined system of model, prompt, tool selection, tool quality, available data and integration design.

That may be closer to a real SOC workflow, but it is much harder to compare fairly. Every organization has a different tool stack, different telemetry, different asset context and different enrichment quality. There is no realistic "average SOC toolset" that would make such a benchmark generally comparable.

Tool use can absolutely improve results in practice, especially when the tools provide high-quality context. But then the result depends heavily on the tools and not only on the model. For this benchmark, we want to measure how well the model interprets the THOR finding itself.