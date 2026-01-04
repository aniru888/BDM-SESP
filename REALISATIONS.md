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

---

## Dashboard Metrics Rationale (2026-01-04)

### Realisation 6: Why 20% Discount Rate for Indian Consumers?

**Date:** 2026-01-04
**Source:** NPV calculation for Participation Constraint (Customer Savings)

**Finding:**
The SESP model uses a 20% annual discount rate for customer NPV calculations. This is intentional and grounded in Indian consumer behavior.

**Rationale:**

1. **Opportunity cost of capital** — Middle-income Indian households typically face high borrowing costs:
   - Personal loans: 12-18% APR
   - Credit cards: 24-36% APR
   - The 20% represents their implicit cost of capital when they could alternatively invest that money

2. **Cash-constrained behavior** — Indian consumers heavily discount future payments because cash today is significantly more valuable than cash in 5 years. This is called "high time preference" in economics.

3. **Model consistency** — The SESP simulation uses 20% as the customer discount rate (from `CLAUDE.md` specification: `DISCOUNT_RATE_CUSTOMER["upper_middle"]: 0.20`). This matches the target segment.

4. **Economic impact** — At 20% discount rate:
   - Rs 599 paid in month 60 = ~Rs 222 in today's value
   - This is why LONGER tenures HELP customer savings under NPV
   - Future monthly payments are heavily discounted, making SESP more attractive

**Formula Applied:**
```python
NPV = sum(payment_t / (1 + monthly_rate)^t for t in 1 to tenure)
where monthly_rate = 0.20 / 12 = 0.0167
```

---

### Realisation 7: Company Margin Formula Fix (Double-Counting Bug)

**Date:** 2026-01-04
**Source:** Dashboard calculation verification

**Finding:**
The original dashboard formula had a double-counting bug:

**BUGGY FORMULA:**
```python
margin = total_revenue - upfront_deficit - recurring_cost + bank_subsidy
# where total_revenue = upfront_net + monthly_revenue
# and upfront_deficit = upfront_cost - upfront_net

# Expanding algebraically:
# margin = (upfront_net + monthly) - (upfront_cost - upfront_net) - recurring + bank
# margin = 2×upfront_net + monthly - upfront_cost - recurring + bank  ← DOUBLE COUNT!
```

**Result:** Dashboard showed Rs 21,067 margin instead of Rs 6,454 (inflated by ~3.3×)

**CORRECTED FORMULA:**
```python
margin = total_revenue - total_cost + bank_subsidy
# where total_cost = upfront_cost + recurring_cost (no intermediate deficit)
```

**Business Implication:**
> Always trace formula algebra when intermediate variables reference each other.
> The deficit concept was useful for break-even but caused errors when mixed with
> revenue that already included upfront_net.

---

### Realisation 8: Summer Overage Reduction (58%) Explained

**Date:** 2026-01-04
**Source:** Simulation results comparing fixed vs seasonal hours

**Finding:**
With seasonal hours allocation, summer overage dropped from 49% to 20.6% — a 58% reduction.

**The Problem (Fixed Hours Model):**
- 200 hours/month allocated year-round
- Summer AC usage: 300+ hours → 49% of bills had overage
- Winter AC usage: 50 hours → Only 0.1% overage
- Result: Unfair "bill shock" in summer months

**The Solution (Seasonal Hours Model):**
- Winter: 70 hours (low need, Dec-Feb)
- Shoulder: 180 hours (medium need, Mar-Apr, Sep-Nov)
- Summer: 280 hours (high need, May-Aug)
- **Same annual total:** 2,120 hours (identical to fixed model)

**Why It Works:**

1. **Budget Effect** — Visible allocation creates self-rationing behavior. Customers seeing "140/280 hours used" naturally conserve.

2. **Anchoring** — The allocation number anchors expectations. 280 hours in summer feels fair and achievable.

3. **Fair Perception** — More hours when genuinely needed (summer AC) feels equitable to customers.

4. **Revenue Neutral** — Only -0.5% revenue impact from simulation (Rs 34,906 → Rs 34,732).

**Evidence from Simulation (1,000 customers × 60 months):**
| Metric | Fixed Hours | Seasonal Hours | Change |
|--------|-------------|----------------|--------|
| Summer Overage Rate | 49% | 20.6% | **-58%** |
| Winter Overage Rate | 0.1% | 0.3% | +200% (negligible) |
| Total Revenue/Customer | Rs 34,906 | Rs 34,732 | -0.5% |
| Overage Revenue | Rs 1,154 | Rs 924 | -20% |

**Business Implication:**
> Seasonal hours is a Pareto improvement: customers feel treated fairly, overage
> complaints drop dramatically, and revenue impact is negligible. This should be
> the default configuration.

---

### Realisation 9: Break-even Month Depends Heavily on Subsidy

**Date:** 2026-01-04
**Source:** Dashboard break-even verification

**Finding:**
Break-even month varies dramatically with subsidy level:

| Subsidy | Upfront Deficit | Monthly Contribution | Break-even |
|---------|-----------------|----------------------|------------|
| 20% | Rs 7,559 | Rs 315 | Month 24 |
| 30% | Rs 11,356 | Rs 315 | Month 36 |
| 40% | Rs 15,153 | Rs 315 | Month 48 |
| 50% | Rs 18,949 | Rs 315 | Month 60 |
| 60% | Rs 22,746 | Rs 315 | Month 72+ |

**Formula:**
```
Break-even = ceil(Upfront Deficit / Monthly Contribution) + 1
where:
- Upfront Deficit = Upfront Cost - Customer Payment (net of GST)
- Monthly Contribution = (Monthly Fee × 0.847) - Rs 192 recurring
```

**Business Implication:**
> At 50% subsidy with Rs 599/month fee, break-even is at Month 60 — exactly at the
> end of a 5-year tenure. This means the company barely breaks even on an individual
> customer basis before the subscription ends. Higher subsidies push break-even beyond
> tenure (loss-making) unless tenure is extended.

---

## Version History

| Date | Change | Source |
|------|--------|--------|
| 2026-01-04 | Initial creation with MCDM findings | Tasks 2.0.1, 2.0.2, 2.0.3 |
| 2026-01-04 | Added Dashboard Metrics Rationale | Dashboard verification & fixes |
