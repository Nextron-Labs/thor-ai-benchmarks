# Operational Profiles

This document defines three deployment profiles for THOR finding triage models, based on operational requirements rather than raw confidence-weighted score.

## Baseline Reference

| Strategy | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run |
|----------|-----|--------|----------|-----------|----------|----------|----------|
| always-inc | 22.1% | 38.3% | 0.0% | 100.0% | 100.0% | 0.0% | $0.00 |
| always-tp | 19.2% | 25.0% | 0.0% | 100.0% | 100.0% | 100.0% | $0.00 |
| always-fp | 26.9% | -58.3% | 100.0% | 0.0% | 0.0% | 0.0% | $0.00 |

**Notes:**
- `always-inc`: Call everything Inconclusive — zero risk but 100% review load
- `always-tp`: Call everything True Positive — no risk aversion, 100% review + 100% false escalation
- `always-fp`: Call everything False Positive — zero review but 100% critical miss rate

---

## Profile 1: High-Safety

**Use case:** Environments where missing any real incident is unacceptable (e.g., critical infrastructure, high-value targets).

**Requirements:**
- Critical Miss Rate ≤ 5%
- Threat Capture Rate ≥ 95%
- False Review Load < 100%

**Ranking:** Balanced OTS descending, then False Review Load ascending

| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |
|---|-------|-----|--------|----------|-----------|----------|----------|----------|---------|
| 1 | llama-3.1-8b | 28.0% | 40.0% | 2.1% | 97.9% | 88.2% | 6.6% | $0.00 | 12.65s |
| 2 | gpt-5-nano | 27.7% | 35.9% | 2.1% | 97.9% | 90.8% | 18.4% | $0.12 | 31.26s |

**Matched:** 2 / 48 models

**Recommendation:** llama-3.1-8b is the only model that beats `always-inc` on Balanced OTS while maintaining near-zero critical miss rate. It saves 12 percentage points of review load vs baseline.

---

## Profile 2: Balanced SOC

**Use case:** General SOC operations where a balance between safety and efficiency is needed.

**Requirements:**
- Critical Miss Rate ≤ 15%
- Threat Capture Rate ≥ 85%
- False Review Load ≤ 75%

**Ranking:** Balanced OTS descending

| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |
|---|-------|-----|--------|----------|-----------|----------|----------|----------|---------|
| 1 | deepseek-v3.2 | 38.8% | 37.4% | 14.6% | 85.4% | 61.8% | 14.5% | $0.32 | 73.28s |
| 2 | nemotron-3-nano-omni | 35.2% | 33.1% | 14.6% | 85.4% | 69.3% | 18.7% | $0.00 | 47.19s |
| 3 | llama-3.1-70b | 36.9% | 30.5% | 14.6% | 85.4% | 67.1% | 31.6% | $0.00 | 13.93s |
| 4 | qwen3-235b-a22b | 33.0% | 26.8% | 12.5% | 87.5% | 65.8% | 14.5% | $0.00 | 32.24s |
| 5 | minimax-m2.5 | 32.9% | 22.0% | 14.6% | 85.4% | 59.2% | 10.5% | $0.16 | 20.07s |
| 6 | gpt-oss-120b | 31.3% | 21.6% | 12.8% | 87.2% | 66.7% | 4.2% | $0.00 | 16.80s |

**Matched:** 6 / 48 models

**Recommendation:** deepseek-v3.2 provides the best balance — nearly matches `always-inc` on Balanced OTS (37.4% vs 38.3%) while reducing review load by 38 percentage points.

---

## Profile 3: Noise-Reduction

**Use case:** High-volume alert triage where reducing review load is a priority and occasional misses are acceptable.

**Requirements:**
- False Review Load ≤ 55%
- Critical Miss Rate ≤ 20%
- Balanced OTS > 0

**Ranking:** False Review Load ascending, then Balanced OTS descending

| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |
|---|-------|-----|--------|----------|-----------|----------|----------|----------|---------|
| 1 | deepseek-v4-flash | 40.9% | 26.2% | 16.7% | 83.3% | 48.7% | 19.7% | $0.10 | 24.31s |
| 2 | gemma4-31b | 40.6% | 27.1% | 18.8% | 81.2% | 52.6% | 13.2% | $0.00 | 17.21s |
| 3 | grok-4.20 | 36.0% | 22.9% | 18.8% | 81.2% | 52.6% | 9.2% | $2.23 | 9.39s |

**Matched:** 3 / 48 models

**Recommendation:** deepseek-v4-flash offers the lowest False Review Load (48.7%) while keeping Critical Miss under 17%. It reduces review load by 51 percentage points vs `always-inc`.

---

## Summary

| Profile | # Matches | Top Pick | BalOTS | CritMiss | FalseRev | Key Advantage |
|---------|-----------|----------|--------|----------|----------|---------------|
| High-safety | 2 | llama-3.1-8b | 40.0% | 2.1% | 88.2% | Beats always-inc on BalOTS, saves 12% review |
| Balanced SOC | 6 | deepseek-v3.2 | 37.4% | 14.6% | 61.8% | Near baseline quality, saves 38% review |
| Noise-reduction | 3 | deepseek-v4-flash | 26.2% | 16.7% | 48.7% | Cuts review load by 51% |

---

## Key Insights

1. **CW% ≠ Operational Quality**: The top CW% models (grok-4-fast, glm-5.1, gemini-2.5-pro) don't appear in any profile because their Critical Miss rates (16-23%) disqualify them.

2. **Only one model beats always-inc**: llama-3.1-8b is the only model that surpasses the "always call Inconclusive" baseline on Balanced OTS while meeting the high-safety requirements.

3. **Local/open-source models dominate**: 4/11 profile matches are local models (llama-3.1-8b, gemma4-31b, nemotron-3-nano-omni, qwen3-235b-a22b), offering zero marginal cost.

4. **DeepSeek dominates cost-efficiency**: deepseek-v3.2 and deepseek-v4-flash appear in multiple profiles with low per-run costs ($0.10-$0.32).