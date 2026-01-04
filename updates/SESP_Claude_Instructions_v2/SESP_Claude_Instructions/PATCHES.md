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

### Overage Justification (Why Customer Accepts It):

```
Company: "You picked the Light Plan (150 hours). You used 180 hours.
          The extra 30 hours = extra wear on compressor, extra service cost.
          Overage: 30 × ₹5 = ₹150"
          
Customer: "Fair enough. I exceeded my plan. Like when I use extra mobile data."
          (No resentment — they understand the logic)
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
    4. Smart features adoption: Using app, following tips
    """
    
    # 1. Temperature Discipline (60% weight)
    # Compare set temp to ambient - closer = more efficient
    avg_set_temp = iot_data['avg_set_temperature']
    avg_ambient = ambient_conditions['avg_outdoor_temp']
    
    # Ideal: Set temp within 8-10°C of ambient
    temp_diff = avg_ambient - avg_set_temp
    
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
    scheduling_score = min(100, timer_usage * 1.2)  # Bonus for using timers
    
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
    People LOVE earning discounts. They HATE paying penalties.
    """
    
    # Tiered discount structure
    if efficiency_score >= 90:
        discount_rate = 0.20  # "Gold" - 20% off
        tier_name = "Efficiency Champion"
    elif efficiency_score >= 75:
        discount_rate = 0.12  # "Silver" - 12% off  
        tier_name = "Efficiency Star"
    elif efficiency_score >= 60:
        discount_rate = 0.05  # "Bronze" - 5% off
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

### The Psychological Power of Positive Framing:

```
❌ OLD MESSAGE (Negative - Penalty Avoidance):
   "You used 120 kWh against baseline of 100 kWh. 
    Penalty: ₹50"
   
   Customer feeling: "I'm being punished for cooling my home!"
   Behavior: Resentment, may cancel subscription

✅ NEW MESSAGE (Positive - Reward Achievement):
   "Amazing! Your Efficiency Score this month: 87/100! 🌟
    You're an 'Efficiency Star'!
    
    Here's your ₹80 discount! Your bill: ₹569 instead of ₹649.
    
    Tip: Set temp to 24°C instead of 22°C next month to reach 'Champion' level!"
   
   Customer feeling: "I EARNED that! Let me try harder next month!"
   Behavior: Engagement, loyalty, actually saves energy
```

### How Efficiency Score Achieves Energy Savings:

| Behavior | Impact on Score | Customer Motivation |
|----------|-----------------|---------------------|
| Set temp 24°C vs 18°C | +40 points | "Easy points!" |
| Use timer feature | +15 points | "Set it and forget it" |
| Don't run with door open | +10 points | "Makes sense anyway" |
| Avoid extreme cooling | +20 points | "Didn't know 16°C was bad" |

**Result:** Customer actively chases the high score → energy savings achieved

### ❌ REMOVE THIS:
```python
# OLD (VULNERABLE TO GAMING)
def calculate_personalized_baseline(usage_history, segment, appliance):
    """Use average of months 1-3 data"""
    return mean(usage_history[0:3])
```

### ✅ REPLACE WITH:
```python
# NEW (ANTI-GAMING)
def calculate_personalized_baseline(usage_history, segment, appliance, weather_data=None):
    """
    Calculate personalized baseline with anti-gaming protections.
    
    Protections:
    1. Hard cap at Segment_Default × 1.20
    2. Use median of M2-M3 (not mean of M1-M3)
    3. Weather normalization if available
    4. Anomaly flagging
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
    
    # Weather normalization (if data available)
    if weather_data:
        # Normalize to standard Cooling Degree Days
        standard_cdd = 200  # Expected CDD for trial months
        actual_cdd = weather_data['cdd_month2'] + weather_data['cdd_month3']
        cdd_factor = standard_cdd / max(actual_cdd, 50)  # Prevent division by tiny numbers
        raw_baseline = raw_baseline * cdd_factor
    
    # HARD CAP: Cannot exceed segment default by more than 20%
    max_allowed = segment_default_monthly * 1.20
    personalized_baseline = min(raw_baseline, max_allowed)
    
    # Flag anomalies for review
    anomaly_flag = False
    if raw_baseline > segment_default_monthly * 1.50:
        anomaly_flag = True
        # Log: "Trial usage significantly exceeds segment norm - review before confirming baseline"
    
    return {
        'raw_calculated': raw_baseline,
        'capped_baseline': personalized_baseline,
        'was_capped': raw_baseline > max_allowed,
        'anomaly_flag': anomaly_flag,
        'segment_default': segment_default_monthly
    }
```

### Anti-gaming rules to document:
| Rule | Implementation | Rationale |
|------|---------------|-----------|
| Hard cap | Baseline ≤ Default × 1.20 | Prevents baseline stuffing |
| Median not mean | median(M2, M3) | Resistant to one outlier month |
| Weather normalization | Adjust by CDD | Prevents gaming by choosing hot months |
| Anomaly flagging | Flag if > 150% of default | Manual review before confirmation |
| Exclude M1 | Use M2-M3 only | M1 has settling-in noise |

---

## PATCH 3: GST Consistency (Overrides Task 1.3 and Task 3.2)

### ❌ ENSURE THIS IS NOT HAPPENING:
```python
# INCONSISTENT (WRONG)
sesp_monthly_to_customer = fee * 1.18  # GST applied
purchase_amc_cost = 2500  # GST forgotten!
```

### ✅ REPLACE WITH:
```python
# CONSISTENT (CORRECT)
def calculate_purchase_scenario_cost(mrp, tenure_years, segment):
    """
    Calculate total cost of purchase with ALL GST applied consistently.
    """
    # MRP is typically GST-inclusive for appliances
    upfront = mrp
    
    # AMC - MUST add GST
    amc_annual_base = 2500
    amc_with_gst = amc_annual_base * 1.18
    amc_total = amc_with_gst * tenure_years
    
    # Ad-hoc repairs - MUST add GST
    repair_probability = 0.15  # Per year after year 2
    avg_repair_cost_base = 3000
    repair_with_gst = avg_repair_cost_base * 1.18
    expected_repairs = repair_probability * (tenure_years - 2) * repair_with_gst
    expected_repairs = max(0, expected_repairs)
    
    # Extended warranty (if purchased) - MUST add GST
    extended_warranty_base = 4000
    extended_warranty_with_gst = extended_warranty_base * 1.18
    
    # Terminal value (no GST - this is resale)
    terminal_value = get_terminal_value(tenure_years)
    
    total_cost = upfront + amc_total + expected_repairs - terminal_value
    
    return {
        'upfront': upfront,
        'amc_total': amc_total,
        'expected_repairs': expected_repairs,
        'terminal_value': terminal_value,
        'total_cost': total_cost,
        'gst_note': 'All service costs include 18% GST'
    }


def calculate_sesp_scenario_cost(subsidy, monthly_fee, tenure_months, deposit):
    """
    Calculate total SESP cost with ALL GST applied consistently.
    """
    # Upfront with GST
    upfront_base = params['mrp'] - subsidy
    upfront_with_gst = upfront_base * 1.18
    
    # Monthly with GST
    monthly_with_gst = monthly_fee * 1.18
    total_monthly = monthly_with_gst * tenure_months
    
    # Deposit (returned at end, but has opportunity cost)
    # Not a cost, but lock-up
    
    total_cost = upfront_with_gst + total_monthly
    
    return {
        'upfront_with_gst': upfront_with_gst,
        'monthly_with_gst': monthly_with_gst,
        'total_monthly': total_monthly,
        'total_cost': total_cost,
        'gst_note': 'All amounts include 18% GST'
    }
```

---

## PATCH 4: Simulation Performance (Overrides Task 4.2)

### ❌ AVOID THIS:
```python
# SLOW - Nested loops
results = []
for customer in range(1000):
    for month in range(36):
        # Calculate each customer-month individually
        results.append(calculate_single_month(...))
```

### ✅ USE THIS:
```python
# FAST - Vectorized operations
import numpy as np
import pandas as pd

def simulate_portfolio_vectorized(customers_df, params, tenure_months):
    """
    Vectorized simulation for performance.
    """
    n_customers = len(customers_df)
    
    # Create month-customer grid
    months = np.arange(tenure_months)
    customer_ids = customers_df['customer_id'].values
    
    # Create full grid using meshgrid or repeat
    n_records = n_customers * tenure_months
    
    results = pd.DataFrame({
        'customer_id': np.repeat(customer_ids, tenure_months),
        'month': np.tile(months, n_customers),
        'segment': np.repeat(customers_df['segment'].values, tenure_months),
        'region': np.repeat(customers_df['region'].values, tenure_months)
    })
    
    # Vectorized calculations
    # Get baselines
    results['baseline_monthly'] = results.apply(
        lambda r: get_monthly_baseline(r['segment'], r['month'], r['region']), 
        axis=1
    )
    
    # Generate usage with noise (vectorized)
    usage_factors = np.repeat(customers_df['usage_factor'].values, tenure_months)
    noise = np.random.normal(1, 0.1, n_records)
    results['actual_usage'] = results['baseline_monthly'] * usage_factors * noise
    
    # Calculate rewards/penalties (vectorized)
    results['deviation'] = (results['actual_usage'] - results['baseline_monthly']) / results['baseline_monthly']
    results['reward_penalty'] = results.apply(calculate_reward_penalty_row, axis=1)
    
    # Calculate bills and margins (vectorized)
    results['monthly_fee'] = params['monthly_fee']
    results['customer_bill'] = (results['monthly_fee'] + results['reward_penalty']) * 1.18
    results['company_revenue'] = (results['monthly_fee'] + results['reward_penalty']) / 1.18
    
    # Handle churn (vectorized)
    churn_probs = np.repeat(customers_df['churn_probability'].values / 12, tenure_months)
    churn_events = np.random.random(n_records) < churn_probs
    
    # Mark all months after churn as inactive
    results['churned'] = churn_events
    results['cumulative_churn'] = results.groupby('customer_id')['churned'].cumsum()
    results['active'] = results['cumulative_churn'] == 0
    
    # Zero out inactive months
    results.loc[~results['active'], ['customer_bill', 'company_revenue']] = 0
    
    return results


# For development/testing, use smaller sample
DEV_MODE = True
N_CUSTOMERS = 100 if DEV_MODE else 1000
```

---

## PATCH 5: Validate Double-Charging is NOT Happening

### Add this validation function:
```python
def validate_no_double_charging(pricing_structure):
    """
    CRITICAL: Ensure we are not charging customer for electricity twice.
    
    Customer pays electricity to utility (Discom) based on their consumption.
    Customer pays SESP for services (maintenance, monitoring, support).
    
    SESP fee should NOT scale linearly with kWh consumed.
    If it does, we are double-charging.
    """
    
    # Check: Is there a component that multiplies kWh by a rate?
    if 'usage_rate_per_kwh' in pricing_structure:
        raise ValueError(
            "ERROR: pricing_structure contains 'usage_rate_per_kwh'. "
            "This would double-charge customers for electricity. "
            "Remove this component. Use tier-based fixed premiums instead."
        )
    
    # Check: Does the fee scale directly with energy consumption?
    light_fee = pricing_structure.get_fee('light')
    heavy_fee = pricing_structure.get_fee('heavy')
    light_kwh = 500
    heavy_kwh = 1800
    
    # If fee difference proportional to kWh difference, we're double-charging
    fee_ratio = heavy_fee / light_fee
    kwh_ratio = heavy_kwh / light_kwh  # 3.6x
    
    if abs(fee_ratio - kwh_ratio) < 0.5:
        raise ValueError(
            f"WARNING: Fee ratio ({fee_ratio:.1f}x) closely tracks kWh ratio ({kwh_ratio:.1f}x). "
            "This suggests we may be double-charging for electricity. "
            "Tier premiums should reflect SERVICE cost differences, not energy consumption."
        )
    
    print("✓ Validation passed: No double-charging detected")
    return True
```

---

## PATCH 6: Economic Sanity Checks

### Add these checks at the end of each calculation:

```python
def sanity_check_unit_economics(economics):
    """
    Verify numbers make sense before proceeding.
    """
    issues = []
    
    # Check 1: Margins should be 10-35%
    if economics['margin_percent'] < 10:
        issues.append(f"Margin too low: {economics['margin_percent']:.1f}% (min 10%)")
    if economics['margin_percent'] > 35:
        issues.append(f"Margin suspiciously high: {economics['margin_percent']:.1f}% (max realistic ~35%)")
    
    # Check 2: Break-even should be 12-30 months
    if economics['breakeven_months'] < 12:
        issues.append(f"Break-even too fast: {economics['breakeven_months']} months (check if costs are missing)")
    if economics['breakeven_months'] > 30:
        issues.append(f"Break-even too slow: {economics['breakeven_months']} months (business may not be viable)")
    
    # Check 3: Customer savings should be 5-25% vs purchase
    if economics['customer_savings_percent'] < 5:
        issues.append(f"Customer savings too low: {economics['customer_savings_percent']:.1f}% (may not attract customers)")
    if economics['customer_savings_percent'] > 30:
        issues.append(f"Customer savings too high: {economics['customer_savings_percent']:.1f}% (check if company is profitable)")
    
    # Check 4: Monthly fee should be ₹300-1000 for AC
    if economics['monthly_fee'] < 300:
        issues.append(f"Monthly fee too low: ₹{economics['monthly_fee']} (may not cover costs)")
    if economics['monthly_fee'] > 1000:
        issues.append(f"Monthly fee too high: ₹{economics['monthly_fee']} (may exceed customer willingness to pay)")
    
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
| Recovery_Factor concept | Deficit recovery + service cost model | Makes economic sense |
| Usage_Rate × kWh | Tier-based fixed premium | Avoids double-charging |
| Trial baseline = mean(M1-M3) | median(M2-M3) with hard cap | Prevents gaming |
| GST on some items | GST on ALL items | Fair comparison |
| Nested for-loops | Vectorized pandas | Performance |
| No validation | Sanity checks | Catch errors early |

---

## FILES TO READ IN ORDER

1. `CRITICAL_INSIGHTS.md` — Understand the errors and why
2. `PATCHES.md` (this file) — Exact code changes
3. `config/pricing_formula_PATCHED.json` — Corrected parameters
4. `claude.md` — Original instructions (apply patches on top)

---

## WHEN IMPLEMENTING EACH TASK

Before writing code for any task, check:

1. ✅ Am I double-charging for electricity? (NO usage × rate formulas)
2. ✅ Am I applying GST consistently? (All services get 18%)
3. ✅ Can this baseline be gamed? (Hard caps, median, normalization)
4. ✅ Will this code be slow? (Vectorize where possible)
5. ✅ Do the numbers pass sanity checks? (Run validation)

If any check fails, STOP and fix before proceeding.
