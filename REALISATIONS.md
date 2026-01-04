# SESP PROJECT — REALISATIONS & KEY LEARNINGS

## Purpose
This file tracks important realisations, insights, and lessons learned during project development.
Each entry is date-stamped and includes evidence from the analysis.

---

## MCDM Analysis Realisations (2026-01-04)

### Realisation 1: Participation Constraint is Systematically Violated

**Date:** 2026-01-04
**Source:** TOPSIS Pricing Analysis (Task 2.0.2)

**Finding:**
ALL 4 pricing scenarios result in NEGATIVE customer savings:

| Scenario | Subsidy | Monthly Fee | Customer Savings |
|----------|---------|-------------|------------------|
| Conservative | 22% | Rs649 | **-35.9%** |
| Balanced | 33% | Rs599 | **-22.9%** |
| Aggressive | 44% | Rs549 | **-9.8%** |
| Premium | 18% | Rs749 | **-56.4%** |

**What This Means:**
- SESP is MORE EXPENSIVE than outright purchase in every scenario
- Even with 44% subsidy (Rs20,000 off Rs45,000), customer pays more
- The participation constraint is violated across the board

**Root Cause Analysis:**
1. Monthly fees accumulate: Rs549 x 36 months = Rs19,764
2. Phase 1 `check_pc_vs_purchase` includes opportunity cost + terminal value
3. Purchase alternative retains asset value; SESP does not
4. Service value (maintenance, warranty) not captured in pure cost comparison

**Business Implication:**
> SESP cannot compete on price alone. The model must compete on SERVICE VALUE
> (maintenance, warranty, IoT monitoring, convenience) that isn't captured in
> pure cost comparison.

---

### Realisation 2: AHP Weights Validate Business Priority Hierarchy

**Date:** 2026-01-04
**Source:** AHP Incentive Analysis (Task 2.0.1)

**Finding:**
Rationally derived pairwise comparisons produced consistent weights:

| Criterion | Weight | Priority |
|-----------|--------|----------|
| Customer Satisfaction | 37.3% | #1 |
| Revenue Protection | 35.5% | #2 |
| Moral Hazard Control | 19.6% | #3 |
| Operational Simplicity | 7.6% | #4 |

**Consistency Check:** CR = 0.0057 (well below 0.10 threshold)

**What This Means:**
- Satisfaction + Revenue together = 73% of decision weight
- "Get customers first AND make money" dominates all other concerns
- Moral hazard control is important but secondary (20%)
- Complexity can be tolerated if it improves other metrics (8%)

**Business Implication:**
> Don't over-engineer gaming prevention at the expense of customer experience
> or profitability. Balance all factors, but prioritize the dual goals of
> customer acquisition and revenue generation.

---

### Realisation 3: DEA Reveals "Middle Tier" Inefficiency Pattern

**Date:** 2026-01-04
**Source:** DEA Plan Efficiency Analysis (Task 2.0.3)

**Finding:**
DEA efficiency scores show a classic pattern:

| Plan | Efficiency | On Frontier |
|------|------------|-------------|
| Light | 1.00 | Yes |
| Moderate | 0.979 | No |
| Heavy | 1.00 | Yes |

**What This Means:**
- Light plan: Low cost, low output — efficient for what it is
- Heavy plan: High cost, high output — efficient for what it is
- Moderate plan: 2.1% below frontier — "stuck in the middle"

**The Pattern:**
This is a well-known DEA finding: extreme positions tend to be efficient because
they're optimized for a specific segment. Middle-ground options often show
inefficiency because they try to serve multiple objectives and compromise on both.

**Business Implication:**
> Consider either:
> 1. Differentiating Moderate more clearly from Light/Heavy
> 2. Phasing it out in favor of sharper Light/Heavy positioning
> 3. Accepting 2% inefficiency as cost of serving "middle" segment

---

### Realisation 4: TOPSIS Rankings Are Misleading When All Options Fail

**Date:** 2026-01-04
**Source:** TOPSIS Pricing Analysis (Task 2.0.2)

**Finding:**
TOPSIS produced rankings even though all scenarios violate participation constraint:

| Rank | Scenario | Closeness Score | Issue |
|------|----------|-----------------|-------|
| 1 | Premium | 0.68 | Worst customer value (-56.4%) |
| 2 | Aggressive | 0.67 | Unprofitable (-3.8% margin) |
| 3 | Conservative | 0.44 | — |
| 4 | Balanced | 0.32 | — |

**What This Means:**
- TOPSIS ranks RELATIVELY, not absolutely
- It finds the "least bad" option even when all are bad
- Premium ranks high because it has best company metrics (margin, breakeven)
- Aggressive ranks high because it has best customer metrics (savings)

**Business Implication:**
> Don't trust TOPSIS ranking until at least one option shows positive customer
> savings. The current ranking answers "which option is least bad?" not
> "which option should we choose?"

---

### Realisation 5: Tenure Length Compounds Fee Impact

**Date:** 2026-01-04
**Source:** Derived from TOPSIS metrics analysis

**Finding:**
3-year tenure makes SESP structurally expensive:

```
Aggressive Scenario (best for customer):
- Upfront payment (after 44% subsidy): Rs25,000
- Monthly fees x 36 months: Rs19,764
- TOTAL SESP COST: Rs44,764

Purchase Alternative:
- Upfront MRP: Rs45,000
- Less terminal value (year 3): Rs10,000
- NET PURCHASE COST: ~Rs35,000

SESP PREMIUM: Rs9,764 (28% more expensive!)
```

**What This Means:**
- Even aggressive subsidies can't overcome 36-month fee accumulation
- Shorter tenure (24 months) would reduce fee burden by Rs6,588
- Or: Service value must be worth at least Rs9,764 to justify SESP

**Business Implication:**
> Consider shorter default tenure (24 months) OR explicitly quantify service
> value in the participation constraint calculation.

---

## Investigation Questions for Phase 3

Based on these realisations, Phase 3 should investigate:

1. **What subsidy + fee + tenure combination achieves positive customer savings?**
   - Sensitivity analysis across the parameter space
   - Find the "break-even" point for participation constraint

2. **Should service value be included in participation constraint?**
   - Quantify: AMC avoided = Rs2,500/year = Rs7,500/3 years
   - Quantify: Warranty value = Rs3,000-5,000
   - Quantify: Repair risk avoided = Rs2,000-4,000/tenure

3. **Is the purchase alternative overly favorable?**
   - Terminal value at 3 years may be optimistic
   - AMC cost may be underestimated
   - Repair probability may be underestimated

4. **Should we offer shorter tenure options?**
   - 24-month plans would reduce fee burden
   - Trade-off: Less customer lock-in, less lifetime value

---

## How to Use This File

1. **Read before starting new tasks** — avoid repeating mistakes
2. **Update when new patterns emerge** — keep knowledge current
3. **Reference in design decisions** — explain WHY choices were made
4. **Include in final report** — demonstrates learning process

---

## Version History

| Date | Change | Source |
|------|--------|--------|
| 2026-01-04 | Initial creation with MCDM findings | Tasks 2.0.1, 2.0.2, 2.0.3 |
