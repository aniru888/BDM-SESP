# SESP MODEL PATCHES — APPLY BEFORE STARTING

## ⚠️ MANDATORY: READ FIRST

These patches correct critical economic logic errors in the original `claude.md`.
**Apply these changes before implementing any task.**

Also read: `CRITICAL_INSIGHTS.md` for full context on why these changes are necessary.

---

## PATCH 1: Pricing Formula — BUCKET MODEL (Overrides Task 1.1)

### ❌ REMOVE THIS (Taxi Meter Model):
```python
# OLD (WRONG) - Variable fee based on consumption
RECOVERY_FACTORS = {...}
USAGE_RATES = {'light': 0.50, 'moderate': 0.45, 'heavy': 0.40}

Monthly_Fee = Base_Component + Usage_Component + Feature_Premium
Usage_Component = Baseline_kWh × Usage_Rate  # DOUBLE CHARGING!
```

### ❌ ALSO REMOVE THIS (Still Wrong — Tier Premium):
```python
# PARTIALLY WRONG - Fixed tier premium still feels like usage tax
TIER_PREMIUMS = {'light': 0, 'moderate': 100, 'heavy': 200}
fee = service_base + tier_premium  # Customer thinks: "Why pay more because I use more?"
```

### ✅ REPLACE WITH: Mobile Data Bucket Model
```python
"""
CORRECT MODEL: "Mobile Data" Style Buckets

Key insight:
- Customer pays for ACCESS (runtime hours), not for electricity
- Within their bucket, usage feels "free"
- Overage = exceeded their plan (understood, like mobile data)
- Metric is HOURS (our wear & tear cost), not kWh (Discom's domain)
"""

# Plan structure (AC)
SUBSCRIPTION_PLANS = {
    'light': {
        'name': 'Light User Plan',
        'monthly_fee': 499,
        'hours_included': 150,  # ~5 hours/day for 30 days
        'overage_fee_per_hour': 5,
        'max_overage_fee': 200,  # Cap to prevent bill shock
        'target_customer': 'Bedroom only, working couple, mild climate'
    },
    'moderate': {
        'name': 'Comfort Plan',
        'monthly_fee': 649,
        'hours_included': 225,  # ~7.5 hours/day
        'overage_fee_per_hour': 4,
        'max_overage_fee': 250,
        'target_customer': 'Family with kids, hot climate, main living area'
    },
    'heavy': {
        'name': 'Power User Plan',
        'monthly_fee': 899,
        'hours_included': 350,  # ~11.5 hours/day
        'overage_fee_per_hour': 3,
        'max_overage_fee': 300,
        'target_customer': 'WFH, joint family, extreme climate, multiple rooms'
    }
}

def calculate_monthly_bill(plan, actual_hours, efficiency_score):
    """
    Calculate monthly bill using bucket model.

    1. Base fee for the plan (covers: maintenance, warranty, IoT, support)
    2. Overage fee if hours exceeded (covers: extra wear & tear)
    3. Efficiency discount if score is high (reward for BEHAVIOR, not low usage)
    """

    base_fee = SUBSCRIPTION_PLANS[plan]['monthly_fee']
    hours_included = SUBSCRIPTION_PLANS[plan]['hours_included']

    # Overage calculation
    if actual_hours > hours_included:
        excess_hours = actual_hours - hours_included
        overage_rate = SUBSCRIPTION_PLANS[plan]['overage_fee_per_hour']
        max_overage = SUBSCRIPTION_PLANS[plan]['max_overage_fee']
        overage_fee = min(excess_hours * overage_rate, max_overage)
    else:
        overage_fee = 0

    # Efficiency reward (discount, NOT penalty avoidance)
    efficiency_discount = calculate_efficiency_reward(efficiency_score, base_fee)

    # Final bill
    bill_before_gst = base_fee + overage_fee - efficiency_discount
    bill_with_gst = bill_before_gst * 1.18

    return {
        'base_fee': base_fee,
        'hours_included': hours_included,
        'actual_hours': actual_hours,
        'overage_fee': overage_fee,
        'efficiency_score': efficiency_score,
        'efficiency_discount': efficiency_discount,
        'bill_before_gst': bill_before_gst,
        'bill_with_gst': bill_with_gst
    }
```

### Why This Works (The Psychology):

| Aspect | Old Model (Wrong) | New Model (Right) |
|--------|-------------------|-------------------|
| **Feels like** | Taxi meter (pay per use) | Mobile data plan (budget your use) |
| **Within limit** | Still paying per kWh | "Free" usage (already paid for) |
| **Over limit** | Harsh penalty | Understandable overage (like mobile) |
| **Customer control** | None — just pays more | Chooses plan that fits their life |
| **Energy saving** | Punished for using | Self-selects into efficient plan |

### Self-Selection Creates Energy Savings:

```
Customer thinking:
"If I pick Light (₹499) instead of Moderate (₹649), I save ₹150/month.
 But I need to stay under 150 hours... let me turn off AC when not home,
 use the timer, maybe set temp to 24°C instead of 20°C..."

Result: Customer voluntarily reduces usage to fit in cheaper plan.
        Company achieves energy saving WITHOUT punishing anyone.
```

---

## PATCH 2: Reward Mechanism — EFFICIENCY SCORE (Overrides Task 2.1)

### ❌ REMOVE THIS (Usage-Based Reward):
```python
# OLD (WRONG) - Rewards low usage (punishes people who NEED to use AC)
def calculate_reward(actual_usage, baseline, monthly_fee, segment):
    savings_percent = (baseline - actual_usage) / baseline
    reward = monthly_fee * reward_rate * savings_percent
    return min(reward, max_reward)
```

### ✅ REPLACE WITH: Efficiency Score System
```python
"""
CORRECT MODEL: Efficiency Score

Key insight:
- Reward BEHAVIOR (efficiency), not OUTCOME (low usage)
- A Chennai family using AC 10 hours efficiently should be rewarded
- A Delhi family running AC at 16°C for 2 hours should NOT be rewarded

Efficiency Score measures HOW they used, not HOW MUCH.
"""

def calculate_efficiency_score(iot_data, ambient_conditions):
    """
    Calculate efficiency score (0-100) based on usage BEHAVIOR.

    Components:
    1. Temperature discipline: Set temp relative to ambient
    2. Timer/schedule usage: Automated efficiency
    3. Anomaly events: Door opens, unusual patterns
    """

    # 1. Temperature Discipline (60% weight)
    avg_set_temp = iot_data['avg_set_temperature']

    if avg_set_temp >= 24:
        temp_score = 100  # Excellent - 24°C or higher
    elif avg_set_temp >= 22:
        temp_score = 80   # Good
    elif avg_set_temp >= 20:
        temp_score = 50   # Fair
    elif avg_set_temp >= 18:
        temp_score = 25   # Poor
    else:
        temp_score = 0    # 16°C is wasteful

    # 2. Schedule Discipline (25% weight)
    timer_usage = iot_data.get('timer_usage_percent', 0)
    scheduling_score = min(100, timer_usage * 1.2)

    # 3. Anomaly Penalty (15% weight)
    door_open_events = iot_data.get('door_open_while_running', 0)
    extreme_temp_hours = iot_data.get('hours_below_20c', 0)
    anomaly_penalty = min(100, door_open_events * 3 + extreme_temp_hours * 2)
    behavior_score = 100 - anomaly_penalty

    # 4. Weighted final score
    efficiency_score = (
        temp_score * 0.60 +
        scheduling_score * 0.25 +
        behavior_score * 0.15
    )

    return max(0, min(100, round(efficiency_score)))


def calculate_efficiency_reward(efficiency_score, base_fee):
    """
    Convert efficiency score to DISCOUNT (positive framing).

    CRITICAL: Frame as DISCOUNT (gain), not penalty avoided (loss).
    """

    if efficiency_score >= 90:
        discount_rate = 0.20  # "Champion" - 20% off
        tier_name = "Efficiency Champion"
    elif efficiency_score >= 75:
        discount_rate = 0.12  # "Star" - 12% off
        tier_name = "Efficiency Star"
    elif efficiency_score >= 60:
        discount_rate = 0.05  # "Aware" - 5% off
        tier_name = "Efficiency Aware"
    else:
        discount_rate = 0.0
        tier_name = "Room to Improve"

    discount_amount = base_fee * discount_rate

    return {
        'efficiency_score': efficiency_score,
        'tier_name': tier_name,
        'discount_rate': discount_rate,
        'discount_amount': discount_amount,
        'message': f"Congrats! Your Efficiency Score of {efficiency_score} earned you ₹{discount_amount:.0f} off!"
    }
```

### Anti-Gaming Baseline (PATCHED):
```python
def calculate_personalized_baseline(usage_history, segment, appliance):
    """
    ANTI-GAMING baseline calculation.

    Protections:
    1. Hard cap at Segment_Default × 1.20
    2. Use median of M2-M3 (not mean of M1-M3)
    3. Anomaly flagging
    """

    SEGMENT_DEFAULTS = {
        'AC': {'light': 500, 'moderate': 1100, 'heavy': 1800},  # Annual kWh
        'FRIDGE': {'light': 220, 'moderate': 300, 'heavy': 400}
    }

    segment_default = SEGMENT_DEFAULTS[appliance][segment]
    segment_default_monthly = segment_default / 12

    # Use months 2-3 only (exclude month 1 settling period)
    trial_usage_m2 = usage_history[1]
    trial_usage_m3 = usage_history[2]

    # Use median (more resistant to gaming than mean)
    raw_baseline = statistics.median([trial_usage_m2, trial_usage_m3])

    # HARD CAP: Cannot exceed segment default by more than 20%
    max_allowed = segment_default_monthly * 1.20
    personalized_baseline = min(raw_baseline, max_allowed)

    # Flag anomalies for review
    anomaly_flag = raw_baseline > segment_default_monthly * 1.50

    return {
        'raw_calculated': raw_baseline,
        'capped_baseline': personalized_baseline,
        'was_capped': raw_baseline > max_allowed,
        'anomaly_flag': anomaly_flag
    }
```

---

## PATCH 3: GST Consistency

### ✅ ENSURE CONSISTENT GST APPLICATION:
```python
def calculate_purchase_scenario_cost(mrp, tenure_years, segment):
    """Total cost of purchase with ALL GST applied consistently."""
    upfront = mrp  # Usually GST-inclusive

    # AMC - MUST add GST
    amc_with_gst = 2500 * 1.18
    amc_total = amc_with_gst * tenure_years

    # Repairs - MUST add GST
    repair_with_gst = 3000 * 1.18
    expected_repairs = 0.15 * (tenure_years - 2) * repair_with_gst

    terminal_value = get_terminal_value(tenure_years)

    return upfront + amc_total + max(0, expected_repairs) - terminal_value


def calculate_sesp_scenario_cost(subsidy, monthly_fee, tenure_months):
    """Total SESP cost with ALL GST applied consistently."""
    upfront_with_gst = (45000 - subsidy) * 1.18
    monthly_with_gst = monthly_fee * 1.18
    total_monthly = monthly_with_gst * tenure_months

    return upfront_with_gst + total_monthly
```

---

## PATCH 4: Simulation Performance

### ✅ USE VECTORIZED OPERATIONS:
```python
import numpy as np
import pandas as pd

def simulate_portfolio_vectorized(customers_df, params, tenure_months):
    """Vectorized simulation - no nested loops."""

    n_customers = len(customers_df)
    n_records = n_customers * tenure_months

    results = pd.DataFrame({
        'customer_id': np.repeat(customers_df['customer_id'].values, tenure_months),
        'month': np.tile(range(tenure_months), n_customers),
        'segment': np.repeat(customers_df['segment'].values, tenure_months)
    })

    # Vectorized calculations
    noise = np.random.normal(1, 0.1, n_records)
    results['actual_usage'] = results['baseline'] * noise

    return results
```

---

## PATCH 5: Economic Sanity Checks

```python
def sanity_check_unit_economics(economics):
    """Verify numbers make sense."""
    issues = []

    if economics['margin_percent'] < 10 or economics['margin_percent'] > 35:
        issues.append(f"Margin outside 10-35%: {economics['margin_percent']:.1f}%")

    if economics['breakeven_months'] < 12 or economics['breakeven_months'] > 30:
        issues.append(f"Break-even outside 12-30 months: {economics['breakeven_months']}")

    if economics['customer_savings_percent'] < 5 or economics['customer_savings_percent'] > 30:
        issues.append(f"Customer savings outside 5-30%: {economics['customer_savings_percent']:.1f}%")

    if issues:
        print("⚠️ SANITY CHECK WARNINGS:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("✓ Sanity checks passed")
    return True
```

---

## SUMMARY OF CHANGES

| Original | Patched | Why |
|----------|---------|-----|
| kWh × rate pricing | Bucket hours model | Avoids double-charging |
| Usage-volume rewards | Efficiency Score | Rewards behavior, not just low usage |
| Mean baseline | Median + 120% cap | Prevents gaming |
| Inconsistent GST | GST on ALL services | Fair comparison |
| Nested loops | Vectorized pandas | Performance |

---

## WHEN IMPLEMENTING EACH TASK

Before writing code for any task, check:

1. ✅ Am I double-charging for electricity? (NO usage × rate formulas)
2. ✅ Am I applying GST consistently? (All services get 18%)
3. ✅ Can this baseline be gamed? (Hard caps, median, normalization)
4. ✅ Will this code be slow? (Vectorize where possible)
5. ✅ Do the numbers pass sanity checks? (Run validation)

If any check fails, STOP and fix before proceeding.
