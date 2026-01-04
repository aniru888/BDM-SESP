# SESP PROJECT — CRITICAL INSIGHTS & LESSONS LEARNED

## Purpose
This file tracks critical errors, corrections, and insights discovered during project development.
**Claude Code must read this file before starting any task and update it if new issues are found.**

---

## CRITICAL ECONOMIC ERRORS TO AVOID

### ❌ ERROR 1: Double Payment for Electricity ("Double Jeopardy")

**Wrong thinking:**
> "Charge customer based on kWh consumed in the subscription"

**Why it's wrong:**
- Customer ALREADY pays electricity bill to Discom/utility (₹6-8/kWh)
- Adding a kWh-based subscription fee = customer pays TWICE for same energy
- Psychologically feels "financially toxic" — penalized for using what they paid for

**Analogy (Car Rental):**
```
❌ WRONG: Pay rental + pay petrol + pay ₹5 to rental company per liter of petrol
   Customer screams: "Why am I paying YOU because I drove the car?"

✅ RIGHT: Pay rental + pay petrol (separately). Rental fee covers the CAR, not the fuel.
```

**The Deeper Problem:** Even a "tier premium" tied to expected consumption still feels like a usage tax.

**THE REAL SOLUTION: "Mobile Data" Bucket Model**

Instead of variable "taxi meter" pricing, use BUCKETS like mobile data plans:

```python
# WRONG: Taxi meter (pay per unit)
fee = base_fee + (kwh_consumed * rate)  # Customer hates this

# WRONG: Tier premium based on expected usage
fee = base_fee + tier_premium[segment]  # Still feels like usage tax

# RIGHT: Mobile data bucket model
PLANS = {
    'light': {'fee': 499, 'hours_included': 150, 'overage_per_hour': 5},
    'moderate': {'fee': 649, 'hours_included': 225, 'overage_per_hour': 4},
    'heavy': {'fee': 899, 'hours_included': 300, 'overage_per_hour': 3}
}

# Within bucket: customer uses "freely" (only pays electricity to Discom)
# Beyond bucket: overage fee (wear & tear, not electricity)
```

**Why buckets work:**
1. **Self-selection**: Customers try to fit into cheaper plan → consciously budget usage → energy saving!
2. **No double tax feeling**: Within bucket, usage feels "free" (already paid for access)
3. **Overage is fair**: "You exceeded your plan" is understood (like mobile data)
4. **Metric is HOURS, not kWh**: Runtime hours = wear on machine (our cost). kWh = electricity (Discom's domain)

**Key Insight:** The goal is to stop WASTAGE, not USAGE.
- A Chennai family NEEDS 10 hours of AC daily. Don't punish them for that.
- Punish them only if they run at 16°C with doors open (wastage).

---

### ❌ ERROR 2: Subsidy Recovery Confusion

**Wrong thinking:**
> "Monthly fee must recover the subsidy given"

**Why it's wrong:**
- "Subsidy" is MRP minus what customer pays upfront
- Customer already pays a subsidized price (e.g., ₹32,000)
- Company's deficit is (Customer_Payment - Company_Cost), not the "subsidy amount"
- Subscription is for services, not capital recovery

**Correct approach:**
- Calculate Company's actual Month 0 position
- Subscription covers: Ongoing costs + Deficit recovery + Margin
- Keep subscription pricing tied to SERVICE VALUE, not capital amortization

**Example:**
```python
# WRONG
base_fee = (mrp - subsidy) * recovery_factor / tenure  # What does 0.45 mean?

# RIGHT
company_month0_deficit = (mfg_cost + iot + install + cac) - customer_upfront
ongoing_monthly_cost = (iot_recurring + maintenance + support) / 12
deficit_recovery_monthly = company_month0_deficit / tenure_months
target_margin = 0.20

minimum_fee = (ongoing_monthly_cost + deficit_recovery_monthly) * (1 + target_margin)
```

---

### ❌ ERROR 3: Baseline Gaming in Trial Period

**Wrong thinking:**
> "Let customers establish their own baseline in trial period with no penalties"

**Why it's wrong:**
- Strategic users will inflate trial usage to set high baseline
- Then "reduce" to normal and claim rewards
- Zero actual behavior change, but company pays rewards

**Correct approach:**
- Hard cap: Personalized baseline ≤ Segment_Default × 1.20
- Normalize for weather (Degree Days / Cooling Degree Days)
- Flag anomalies: If trial usage > 150% of segment average → manual review
- Use median of months 2-3, not average (resistant to outliers)

**Example:**
```python
# WRONG
baseline = mean(usage_month1, usage_month2, usage_month3)

# RIGHT
baseline = min(
    median(usage_month2, usage_month3),  # Exclude M1 settling period
    SEGMENT_DEFAULT[segment] * 1.20  # Hard cap
)
# Also apply CDH normalization if available
```

---

### ❌ ERROR 3B: Rewarding Low USAGE Instead of EFFICIENCY

**Wrong thinking:**
> "Reward customers for using less kWh than baseline"

**Why it's wrong:**
- Punishes people who NEED more usage (hot climate, large family, WFH)
- Rewards people who simply didn't use the product (not a behavior change)
- Doesn't distinguish between "efficient use" and "no use"

**The Real Goal:** Stop WASTAGE, not USAGE.

**Correct approach: EFFICIENCY SCORE**

```python
# WRONG: Raw usage reward
savings = baseline - actual_usage
reward = savings * reward_rate  # Punishes usage, not wastage

# RIGHT: Efficiency Score reward
def calculate_efficiency_score(iot_data):
    """
    Efficiency Score measures HOW they used, not HOW MUCH.

    Components:
    1. Temperature discipline: Did they keep temp at 24°C+ (vs 16-18°C)?
    2. Schedule discipline: Did they use timer/scheduling?
    3. Door events: Frequent door opens waste energy
    4. Standby behavior: Turning off when not needed
    """

    # Temperature discipline (biggest factor)
    avg_set_temp = iot_data['avg_set_temperature']
    if avg_set_temp >= 24:
        temp_score = 100
    elif avg_set_temp >= 22:
        temp_score = 80
    elif avg_set_temp >= 20:
        temp_score = 50
    else:
        temp_score = 20  # 16-18°C is wasteful

    # Schedule discipline
    used_timer = iot_data['timer_usage_percent']
    schedule_score = min(100, used_timer * 1.5)

    # Anomaly penalty (doors open, unusual patterns)
    anomaly_events = iot_data['anomaly_count']
    anomaly_penalty = min(30, anomaly_events * 5)

    # Final score (0-100)
    efficiency_score = (temp_score * 0.6 + schedule_score * 0.4) - anomaly_penalty
    return max(0, min(100, efficiency_score))


def calculate_efficiency_reward(efficiency_score, monthly_fee):
    """
    Reward based on efficiency score, NOT on low usage.

    Framed as DISCOUNT (gain), not avoided FEE (pain).
    """
    if efficiency_score >= 90:
        discount_percent = 0.25  # ₹150 off on ₹599 fee
    elif efficiency_score >= 75:
        discount_percent = 0.15
    elif efficiency_score >= 60:
        discount_percent = 0.08
    else:
        discount_percent = 0.0

    return monthly_fee * discount_percent
```

**Why this works psychologically:**
- People HATE fees (pain) → avoid using product
- People LOVE discounts (gain) → actively try to earn them
- Result: Customer fights to keep temp at 24°C to "earn" the discount
- Company gets energy savings; customer gets cheaper subscription

**Key distinction:**
```
❌ OLD: "You used 100 kWh. Pay me ₹50 penalty."
   (Customer: "I'm being punished for cooling my home!")

✅ NEW: "Your base fee is ₹649. Because you kept AC at 24°C (Efficiency Score: 92%),
         here's a ₹150 discount! Your bill: ₹499."
   (Customer: "I EARNED that discount! I'll do it again next month!")
```

---

### ❌ ERROR 4: Inconsistent GST Application

**Wrong thinking:**
> "Apply GST to subscription but forget GST on alternatives"

**Why it's wrong:**
- If SESP shows ₹599 × 1.18 = ₹707/month (with GST)
- But Purchase alternative shows AMC at ₹2,500/year (without GST)
- Comparison is unfair — SESP looks 18% more expensive than reality

**Correct approach:**
- Apply GST consistently to ALL cost components
- Purchase scenario: MRP (incl GST) + AMC × 1.18 + Repairs × 1.18
- SESP scenario: Upfront × 1.18 + Monthly × 1.18
- All comparisons GST-inclusive or all GST-exclusive, never mixed

**Checklist:**
| Component | GST Applied? |
|-----------|--------------|
| MRP (purchase) | ✓ Usually inclusive |
| AMC (purchase) | ✓ Must add 18% |
| Repairs (purchase) | ✓ Must add 18% |
| Subsidized price (SESP) | ✓ Must add 18% |
| Monthly fee (SESP) | ✓ Must add 18% |

---

## CRITICAL TECHNICAL ERRORS TO AVOID

### ❌ ERROR 5: Nested For-Loops for Simulation

**Wrong approach:**
```python
for customer in customers:  # 1000 iterations
    for month in range(36):  # 36 iterations
        # Calculate stuff
```
**Total: 36,000 iterations — slow, prevents sensitivity analysis**

**Correct approach:**
```python
# Vectorized with NumPy/Pandas
customers_df['month'] = np.tile(range(36), len(customers))
customers_df['usage'] = baseline * seasonality[month] * np.random.normal(1, 0.1, len(df))
# Process entire DataFrame at once
```

---

### ❌ ERROR 6: Hardcoded Magic Numbers

**Wrong:**
```python
fee = 599
subsidy = 13000
# Where do these come from? Why these values?
```

**Correct:**
```python
# All parameters from config, with documented rationale
fee = config['pricing']['monthly_fee']  # Derived from unit economics model
subsidy = config['pricing']['subsidy']  # Calibrated to participation constraint
```

---

## KEY ECONOMIC INSIGHTS

### Insight 1: Self-Selection Creates Energy Savings (The Mobile Data Effect)

```
When customer chooses a plan:

Light (₹499, 150 hrs) vs Moderate (₹649, 225 hrs) vs Heavy (₹899, 350 hrs)

Customer thinking:
"If I pick Light instead of Moderate, I save ₹150/month = ₹1,800/year!
 But I need to stay under 150 hours...
 → Turn off when not home
 → Use timer at night
 → Set temp to 24°C instead of 20°C
 → Close doors properly"

RESULT: Customer VOLUNTARILY reduces usage to fit cheaper plan.
        Energy savings achieved WITHOUT punishment.
```

This is the "Mobile Data Effect" — people actively manage their usage to stay within their plan, creating savings they feel good about.

---

### Insight 2: Positive Framing Drives Behavior Change

```
Psychological principle:
- PAIN (fees, penalties) → Avoidance → Resentment → Churn
- GAIN (discounts, rewards) → Pursuit → Engagement → Loyalty

Application:

❌ PAIN FRAMING:
   "You ran AC at 18°C. Inefficiency penalty: ₹100"
   Customer: "They're punishing me for cooling my home!"
   Behavior: Angry, may cancel

✅ GAIN FRAMING:
   "Your Efficiency Score: 82! 🌟
    You earned ₹78 off your bill!
    Tip: Set temp to 24°C to reach Champion level next month!"
   Customer: "I EARNED that! Let me try for Champion!"
   Behavior: Engaged, tries harder, tells friends
```

---

### Insight 3: Dual Discount Rate Creates Value Arbitrage

```
Firm's cost of capital: 12%
Customer's implicit rate: 22-28%

Same cash flow, different values:
₹599/month for 24 months

NPV to Firm (12%): ₹12,800
NPV to Customer (25%): ₹10,900

The firm can "afford" to offer more because money costs them less.
This is the economic engine of subscription models.
```

### Insight 4: Seasonality Creates Cash Flow Risk, Not Just Revenue Variation

```
AC usage by month (North India):
Jan: 5%   → Nearly zero revenue from usage-linked components
May: 170% → Peak revenue

If fee is 50% usage-linked:
January cash: ₹599 × 0.50 × 0.05 + ₹599 × 0.50 = ₹314
May cash: ₹599 × 0.50 × 1.70 + ₹599 × 0.50 = ₹809

Company must buffer 6 months of low cash flow with 6 months of high.
```

### Insight 5: Penalty Must Exceed Benefit of Overuse

```
For moral hazard to be controlled:
Expected_Penalty(overuse) > Perceived_Benefit(overuse)

If running AC extra 2 hours/day gives ₹X worth of comfort
Penalty must be > ₹X for customer to care

Proxy: ₹X ≈ Electricity cost of those 2 hours
If electricity = ₹50 for 2 extra hours, penalty must be > ₹50
```

### Insight 6: Participation Constraint Has Two Comparisons

```
SESP must beat BOTH:
1. Outright purchase (for those with cash)
2. EMI purchase (for those without cash)

Different segments compare differently:
- Affluent → Compare vs outright purchase
- Middle → Compare vs 12/24 month EMI
- Lower-middle → Compare vs rental or no-purchase

SESP pricing must work for primary target segment.
```

---

## VALIDATION CHECKPOINTS

Before finalizing any pricing:

| Check | How to Verify | Red Flag |
|-------|---------------|----------|
| Participation Constraint | NPV(SESP) < NPV(Purchase) × 0.90 | SESP more expensive |
| Profitability | Margin > 15% over tenure | Negative or <10% margin |
| Cash Flow | Max deficit < ₹10,000/unit | Deep negative early |
| Break-even | < 24 months | > 30 months |
| Incentive Compatibility | Each segment prefers own plan | Cross-segment preference |
| Moral Hazard | Penalty > 50% of overuse value | Penalty too weak |
| Baseline Gaming | Trial baseline < 120% of default | Inflated baselines |
| GST Consistency | All scenarios same treatment | Mixed application |

---

## WHEN TO UPDATE THIS FILE

Claude Code should add new entries when:
1. A calculation produces obviously wrong numbers
2. A constraint can never be satisfied
3. A logical inconsistency is discovered
4. A new edge case is found
5. External validation reveals an error

Format for new entries:
```markdown
### ❌ ERROR N: [Title]

**Wrong thinking:**
> "[The incorrect assumption]"

**Why it's wrong:**
[Explanation]

**Correct approach:**
[Solution]

**Example:**
[Code or calculation]
```

---

## MCDM ANALYSIS INSIGHTS (Added 2026-01-04)

### Insight 7: All Pricing Scenarios Violate Participation Constraint

**Source:** TOPSIS Analysis (Task 2.0.2)

**Finding:**
Every pricing scenario tested shows NEGATIVE customer savings:
- Conservative (22% subsidy): -35.9%
- Balanced (33% subsidy): -22.9%
- Aggressive (44% subsidy): -9.8%
- Premium (18% subsidy): -56.4%

**Why This Happens:**
```
Even aggressive scenario (44% subsidy):
  Upfront: Rs25,000
  Fees: Rs549 x 36 = Rs19,764
  TOTAL SESP: Rs44,764

Purchase alternative:
  MRP: Rs45,000
  Terminal value: -Rs10,000
  NET: Rs35,000

SESP costs Rs9,764 MORE (28% premium)
```

**Implication:**
SESP cannot compete on price alone. Must compete on service value or adjust parameters.

---

### Insight 8: DEA Middle-Tier Inefficiency Pattern

**Source:** DEA Analysis (Task 2.0.3)

**Finding:**
- Light Plan: 100% efficient (on frontier)
- Moderate Plan: 97.9% efficient (2.1% below frontier)
- Heavy Plan: 100% efficient (on frontier)

**Why This Pattern:**
Extreme positions (cheap-basic OR expensive-premium) tend to be efficient because
they're optimized for specific segments. Middle-ground options compromise on both.

**Implication:**
Consider polarizing offering into sharper Light/Heavy tiers, or accept Moderate
plan's 2% inefficiency as cost of serving the middle segment.

---

### Insight 9: TOPSIS Rankings Mislead When All Options Fail Constraints

**Source:** TOPSIS Analysis (Task 2.0.2)

**Finding:**
TOPSIS ranked scenarios even though all violated participation constraint:
1. Premium (C*=0.68) — worst customer value but best margins
2. Aggressive (C*=0.67) — best customer value but unprofitable

**Why This Is Problematic:**
TOPSIS ranks RELATIVELY, not absolutely. It answers "which is least bad?" not
"which should we choose?" When all options violate a critical constraint, the
ranking is operationally meaningless.

**Implication:**
Fix participation constraint FIRST, then re-run TOPSIS on valid options only.

---

## VERSION HISTORY

| Date | Change | Reason |
|------|--------|--------|
| 2026-01-04 | Added MCDM insights 7-9 | Results from Tasks 2.0.1-2.0.3 analysis |
| 2025-01-03 | Initial creation | Pre-identified flaws from expert review |
| 2025-01-03 | v2.0: Bucket model + Efficiency Score | Expert feedback: tier premium still felt like usage tax; bucket model (like mobile data) is psychologically better |
| | Added: Self-selection insight | Customer voluntarily budgets usage to fit cheaper plan |
| | Added: Positive framing insight | Discounts (gain) work better than penalties (pain) |
| | Changed: Hours metric instead of kWh | Hours = wear (our domain), kWh = electricity (Discom's domain) |
