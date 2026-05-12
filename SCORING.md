# Scoring Methodology

## Overview

Each model is scored on how well it triages THOR security scan findings compared to expert ground truth. Every seed finding receives a classification (True Positive, False Positive, or Inconclusive) from the model and from the expert. We measure how well the model's classifications match.

## Core Scoring Metrics

### 1. CW — Confidence-Weighted (Primary Metric)

This is our headline metric. It rewards correct classifications and penalizes wrong ones, with two key design decisions suited to cybersecurity triage.

#### Dampened Confidence

The model provides a confidence score (0–100%) with each classification. We **dampen** this to compress the range from [0, 1.0] to [0.5, 1.0]:

```
dampened = 0.5 + 0.5 × (confidence / 100)
```

**Why?** Without dampening, a model that calls everything "inconclusive" at 50% confidence can score nearly as well as one that correctly classifies at 90% — because the low-confidence hedge faces very small penalties even when wrong. In real triage, the difference between 60% and 90% confidence matters much less than whether you got the classification right. Dampening ensures hedging isn't artificially rewarded.

#### Asymmetric Penalties

Hard errors (classification off by 2 steps: TP↔FP) are penalized **asymmetrically**:

| Model says | Ground truth | What happened | CW score |
|-----------|-------------|---------------|----------|
| TP | TP | ✅ Correct | +1.0 + dampened |
| FP | FP | ✅ Correct | +1.0 + dampened |
| Inc | Inc | ✅ Correct | +1.0 + dampened |
| TP | Inc | ⚠️ Minor error (1 step) | +0.5 − 0.5×dampened |
| Inc | FP or TP | ⚠️ Minor error (1 step) | +0.5 − 0.5×dampened |
| FP | TP | 🔴 **Missed a real threat** | −1.5 × dampened |
| TP | FP | 🟡 Over-called a non-threat | −0.5 × dampened |

**Why asymmetric?** In cybersecurity, false negatives are far more dangerous than false positives:

- **TP→FP (missed threat):** You dismissed a real attack indicator as noise. The adversary stays undetected. This is the worst possible error — penalty **×1.5**.
- **FP→TP (over-called):** You flagged something benign as malicious. This costs analyst time to investigate, but no threat is missed. This is the least bad hard error — penalty **×0.5**.

This asymmetry reflects actual incident response priorities: it's better to over-investigate than to miss a real attack.

#### Score Ranges

| Scenario | CW score per finding | Range |
|----------|---------------------|-------|
| Exact match | 1.0 + dampened | [1.5, 2.0] |
| Minor error (1 step) | 0.5 − 0.5×dampened | [0.0, 0.5] |
| Hard: missed threat (GT=TP, model=FP) | −1.5 × dampened | [−1.5, −0.75] |
| Hard: over-called (GT=FP, model=TP) | −0.5 × dampened | [−0.5, −0.25] |

**Max per finding:** 2.0 (exact match at 100% confidence)  
**CW%:** (total / (N × 2.0)) × 100

### 2. Ordinal (2/1/0)

Simple distance-based scoring, ignoring confidence entirely:

- **2 points:** Exact classification match
- **1 point:** One category off (e.g., TP↔Inc or FP↔Inc)
- **0 points:** Two categories off (TP↔FP)

**Ordinal%:** (total / (N × 2)) × 100

### 3. MAE / RMSE (Continuous Score Accuracy)

In addition to classification, each model assigns a priority score (0–100) to each finding, and the expert does the same. MAE and RMSE measure how close the model's scores are to the expert's.

- **MAE** (Mean Absolute Error): Average absolute difference between model and expert scores
- **RMSE** (Root Mean Squared Error): Like MAE but penalizes large errors more heavily

Lower is better for both.

## Operational Metrics

CW% is useful for ranking classic classification quality, but operational model selection also needs workload and safety metrics. The README profile tables use these additional metrics:

| Metric | Meaning | Direction |
|--------|---------|-----------|
| **Balanced OTS** | Operational triage score balanced across FP, Inc, and TP classes so one dominant class does not hide weak behavior elsewhere | Higher is better |
| **Critical Miss Rate** | Share of true positives classified as false positive (`TP→FP`) | Lower is safer |
| **Threat Capture Rate** | Share of true positives still sent to review as `Inc` or `TP` | Higher is safer |
| **False Review Load** | Share of ground-truth false positives still sent to review as `Inc` or `TP` | Lower means less analyst noise |
| **False Escalation Rate** | Share of ground-truth false positives escalated all the way to `TP` | Lower is better |

The operational profile recommendations also apply guardrails. In particular, the high-safety profile requires meaningful noise reduction; a model close to the `always-inc` baseline is not recommended just because it has a low miss rate.

## Ground Truth Distribution

Across the current seven-report benchmark set (155 expert-classified seed findings):

| Category | Count | Share |
|----------|-------|-------|
| FP (False Positive) | 76 | 49.0% |
| Inc (Inconclusive) | 35 | 22.6% |
| TP (True Positive) | 44 | 28.4% |

Per-report finding counts:

| Report | Findings |
|--------|----------|
| R1 | 16 |
| R2 | 9 |
| R3 | 19 |
| R4 | 6 |
| R5 | 23 |
| R6 | 67 |
| R7 | 15 |
| **Total** | **155** |

## Why CW Over Simple Accuracy?

Simple accuracy treats all errors equally. In security triage:
- Missing a real threat (false negative) is **much worse** than investigating something benign (false positive)
- Confidence should matter — a model that commits and is right deserves more credit than one that hedges
- But confidence shouldn't dominate — whether you're 60% or 90% sure matters less than whether you called it right in the first place

CW with dampened confidence and asymmetric penalties captures these priorities. Traditional ML metrics like F1 or Cohen's kappa don't account for this asymmetry, because they treat FP and FN equally — which is wrong for cybersecurity.