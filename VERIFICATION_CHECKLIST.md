# SESP Project — Verification Checklist

## Purpose
This checklist ensures every implementation step passes sanity checks and produces valid, reasonable outputs.
**Use this checklist after completing each phase of implementation.**

---

## CHECKPOINT 1: Pre-Implementation Sanity

Before writing ANY code, verify:

- [ ] **Understand bucket model**: Hours included, not kWh rates
- [ ] **Understand efficiency score**: Behavior metrics (temp, timer, anomaly), not just low usage
- [ ] **Confirm NO double-charging**: SESP ≠ electricity — they are different domains
- [ ] **GST applies to ALL services**: Both SESP and purchase scenarios get 18%
- [ ] **Read CRITICAL_INSIGHTS.md**: Understand the 6 errors to avoid
- [ ] **Read PATCHES.md**: Know the exact code patterns to use

---

## CHECKPOINT 2: Pricing Logic Validation

After implementing pricing:

- [ ] **Monthly fee range**: ₹400-1,000 (realistic for Indian middle class)
- [ ] **Overage cap exists**: Max ₹200-300, not unlimited
- [ ] **No kWh × rate calculations**: That's Discom's job, not ours
- [ ] **Hours-based tracking only**: Runtime hours = wear & tear (our cost)
- [ ] **Self-selection works**: Cheaper plan + overage > correct plan for heavy users
- [ ] **Tenure affects fee**: Longer tenure = lower fee (multiplier logic)

### Pricing Sanity Values
| Parameter | Min | Max | If Outside → |
|-----------|-----|-----|--------------|
| Light plan fee | 400 | 550 | Check service cost assumptions |
| Moderate plan fee | 550 | 750 | Check against segment value perception |
| Heavy plan fee | 800 | 1000 | Check premium service inclusions |
| Subsidy (AC) | 8000 | 18000 | Check NPV impact |
| Deposit | 3000 | 7000 | Check customer barrier |

---

## CHECKPOINT 3: Reward Mechanism Validation

After implementing rewards:

- [ ] **Efficiency score based on BEHAVIOR**: Temperature discipline (60%), timer usage (25%), anomaly avoidance (15%)
- [ ] **NOT based on raw usage volume**: Don't punish hot climate users
- [ ] **Positive framing**: Discounts shown as "earned", not penalties "avoided"
- [ ] **Anti-gaming baseline**: Median of M2-M3 + 120% hard cap (not mean of M1-M3)
- [ ] **Score tiers make sense**: Champion (90+), Star (75+), Aware (60+), Improving (0+)
- [ ] **Discount amounts reasonable**: 5-20% of base fee, not more

### Efficiency Score Sanity Check
| Scenario | Expected Score | If Different → |
|----------|----------------|----------------|
| 24°C avg, timer 80%, no anomalies | 90+ | Champion tier |
| 22°C avg, timer 50%, few anomalies | 70-85 | Star tier |
| 18°C avg, no timer, many anomalies | <40 | Improving tier |

---

## CHECKPOINT 4: Economic Bounds Check

After running simulation:

- [ ] **Company margin**: 10-35% (not 50%+ or negative)
- [ ] **Customer savings vs purchase**: 5-25% (not 50%+ which is unrealistic)
- [ ] **Break-even**: 12-30 months (not 3 months or never)
- [ ] **Monthly bill with overage**: ₹500-1,200 range (total customer pays)
- [ ] **Max cumulative deficit**: ≤ ₹10,000 per unit

### Economic Sanity Values
| Metric | Min | Max | If Outside → |
|--------|-----|-----|--------------|
| Company margin % | 10% | 35% | Review pricing or costs |
| Customer savings % | 5% | 25% | Review participation constraint |
| Break-even months | 12 | 30 | Review subsidy/fee balance |
| Max monthly bill | 500 | 1200 | Review overage or plan fit |

---

## CHECKPOINT 5: Simulation Performance

- [ ] **No nested for-loops** for customer × month
- [ ] **Vectorized Pandas/NumPy operations**
- [ ] **1000 customers × 36 months runs in <10 seconds**
- [ ] **Memory usage reasonable**: <500MB for typical simulation

### Performance Indicators
| Operation | Target Time | If Slower → |
|-----------|-------------|-------------|
| Single scenario calc | <100ms | Check vectorization |
| Sensitivity (10 points) | <1s | Check for loops |
| Monte Carlo (1000 runs) | <30s | Check parallelization |
| Full portfolio simulation | <10s | Check data structure |

---

## CHECKPOINT 6: Output Validation

- [ ] **Segment distribution matches input**: (30/50/20 for light/moderate/heavy)
- [ ] **Seasonality affects cash flow**: Summer ≠ winter for AC
- [ ] **Heavy users pay more than light users**: On average, after overage
- [ ] **Efficiency rewards reduce bills**: High score = lower bill
- [ ] **GST appears consistently**: All customer costs include GST
- [ ] **NPV calculations use correct rates**: Firm (12%) vs Customer (16-28%)

### Output Sanity Checks
| Output | Check | Red Flag |
|--------|-------|----------|
| Segment proportions | Sum to 100% | Any segment 0% or >60% |
| Seasonal multiplier | Summer > 1.0, winter < 1.0 | Flat across months |
| Average bill by segment | Heavy > Moderate > Light | Light highest |
| Efficiency discount | Reduces bill | Increases bill |

---

## CHECKPOINT 7: Constraint Satisfaction

All 5 constraints must pass:

### Participation Constraint
- [ ] NPV_customer(SESP) < NPV_customer(Purchase) × 0.90
- [ ] Use customer discount rate (16-28%)
- [ ] Include terminal value for purchase
- [ ] Include GST on both scenarios

### Profitability Constraint
- [ ] NPV_firm(Revenue) >= NPV_firm(Costs) × 1.15
- [ ] Use firm discount rate (12%)
- [ ] Include ALL costs (manufacturing, IoT, maintenance, CAC, default)
- [ ] Net GST properly (firm receives fee net of GST)

### Cash Flow Constraint
- [ ] Max negative cumulative < ₹10,000/unit
- [ ] Break-even month ≤ 24
- [ ] Cash flow turns positive before tenure ends

### Incentive Compatibility
- [ ] Each segment prefers their intended plan
- [ ] Heavy users don't benefit from Light plan
- [ ] Self-selection mechanism works

### Moral Hazard
- [ ] Overage fee deters excessive use
- [ ] Overage cap prevents bill shock
- [ ] Expected overage reasonable for each segment

---

## CHECKPOINT 8: Documentation Updated

After completing any implementation:

- [ ] **DOCUMENTATION.md updated** with:
  - Formula used
  - Why this approach was chosen
  - Alternatives considered
  - Validation results
- [ ] **REALISATIONS.md updated** if new insight discovered
- [ ] **Code comments** explain non-obvious logic

---

## CHECKPOINT 9: MCDM Analysis Validation (Added 2026-01-04)

### AHP Validation
- [ ] **Consistency Ratio (CR) < 0.10**: Judgments are consistent
- [ ] **Weights sum to 1.0**: Proper normalization
- [ ] **Weight rankings intuitive**: Highest priority criteria have highest weights
- [ ] **Pairwise comparisons documented**: Rationale for each judgment recorded

### TOPSIS Validation
- [ ] **All closeness scores in [0, 1]**: Valid range
- [ ] **At least one alternative has POSITIVE customer savings**: Otherwise constraint violated
- [ ] **Criteria types correct**: Benefit (higher=better) vs Cost (lower=better)
- [ ] **Weights applied correctly**: Sum to 1.0, reflect priorities

### DEA Validation
- [ ] **At least one DMU on frontier**: Efficiency = 1.0
- [ ] **All efficiency scores in [0, 1]**: Valid range
- [ ] **Inputs are resources consumed**: Cost, visits (things we want to minimize)
- [ ] **Outputs are value produced**: Satisfaction, revenue, retention (things we want to maximize)

### MCDM Red Flags
| Issue | Implication | Action |
|-------|-------------|--------|
| AHP CR >= 0.10 | Judgments inconsistent | Review pairwise comparisons |
| All TOPSIS alternatives negative savings | Participation constraint violated | Fix pricing parameters FIRST |
| No DEA DMU on frontier | Data or model error | Check inputs/outputs specification |
| TOPSIS ranking contradicts intuition | Weight or criteria type error | Review criteria_types and weights |

### Current MCDM Status (2026-01-04)
| Check | Status | Finding |
|-------|--------|---------|
| AHP CR | PASS | CR = 0.0057 < 0.10 |
| AHP weights intuitive | PASS | Satisfaction/Revenue highest, Simplicity lowest |
| TOPSIS range valid | PASS | All C* in [0, 1] |
| TOPSIS positive savings | FAIL | ALL scenarios have negative savings |
| DEA frontier exists | PASS | Light + Heavy on frontier |
| DEA range valid | PASS | All scores in [0, 1] |

---

## Quick Reference: Red Flags

### 🚨 STOP if you see:
- kWh × rate calculations for subscription fee
- Rewards based on low usage volume (not efficiency)
- Mean baseline (should be median)
- No overage cap
- GST only on SESP, not purchase
- Nested loops for simulation
- Customer savings > 30%
- Company margin > 40% or < 5%
- Break-even > 36 months

### ✅ Good signs:
- Hours-based bucket model
- Efficiency score with behavioral components
- Median + 120% cap for baseline
- Overage capped at ₹200-300
- GST on ALL services consistently
- Vectorized simulation code
- Customer savings 10-20%
- Company margin 15-25%
- Break-even 15-24 months

---

## Version History

| Date | Change | Reason |
|------|--------|--------|
| 2026-01-04 | Added MCDM Checkpoint 9 | Tasks 2.0.1-2.0.3 completed, need validation framework |
| 2025-01-03 | Initial creation | Pre-implementation verification framework |
