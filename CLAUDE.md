# INSTRUCTIONS FOR CLAUDE CODE

## Workflow Guidelines

When you start working on this project:

- First, read all context files in /SESP_Claude_Instructions/
- Follow tasks in order — each phase depends on previous
- Create files in specified locations — maintain structure
- Test each function before moving to next task
- Document assumptions in code comments
- Generate outputs (CSVs, charts) as specified
- Validate constraints are actually satisfied
- Cross-check numbers — unit economics should be realistic (margins 15-25%, not 50%+)

## Red Flags to Watch

- If participation constraint can never be satisfied → subsidy too low or fee too high
- If profitability is negative → subsidy too high or fee too low
- If all customers are heavy users in simulation → data generation bug
- If seasonality doesn't affect cash flow → seasonality not applied

## Red Flags (V2 Extended) — CRITICAL

- **If using kWh × rate pricing** → WRONG (use bucket model with hours instead)
- **If rewards based on raw usage volume** → WRONG (use efficiency score for behavior)
- **If no overage cap** → WRONG (must have max ₹200-300)
- **If baseline uses mean instead of median** → WRONG (gaming risk)
- **If GST only on SESP, not purchase** → WRONG (apply to ALL)
- **If nested for-loops for simulation** → WRONG (use vectorized operations)
- **If customer savings > 30%** → WRONG (unrealistic, check assumptions)
- **If company margin > 40%** → WRONG (suspiciously high)

---

## CRITICAL MODEL CORRECTIONS (V2)

⚠️ **READ FIRST:** These corrections override conflicting patterns in the original specification.
See `CRITICAL_INSIGHTS.md` and `PATCHES.md` for full details.

### 1. BUCKET MODEL (Replaces kWh-Based Pricing)

**OLD (WRONG):** Charge based on kWh consumed
```python
# WRONG - Double-charges customer (they already pay Discom for electricity)
fee = base_fee + (kwh_consumed * rate)
```

**NEW (CORRECT):** Bucket model with runtime hours
```python
# CORRECT - Charge for ACCESS (hours), not electricity (kWh)
SUBSCRIPTION_PLANS = {
    'light': {'fee': 499, 'hours_included': 150, 'overage_per_hour': 5, 'max_overage': 200},
    'moderate': {'fee': 649, 'hours_included': 225, 'overage_per_hour': 4, 'max_overage': 250},
    'heavy': {'fee': 899, 'hours_included': 350, 'overage_per_hour': 3, 'max_overage': 300}
}

bill = base_fee + min(overage, max_overage) - efficiency_discount
```

**Why:** Hours = appliance wear (our domain). kWh = electricity (Discom's domain). No overlap, no double-charging.

### 2. EFFICIENCY SCORE (Replaces Usage-Volume Rewards)

**OLD (WRONG):** Reward low usage
```python
# WRONG - Punishes people who NEED to use AC (hot climate)
reward = (baseline - actual_usage) * reward_rate
```

**NEW (CORRECT):** Reward efficient BEHAVIOR
```python
# CORRECT - Reward HOW they use, not HOW MUCH
def efficiency_score(temp_discipline, timer_usage, anomaly_events):
    temp_score = 100 if avg_temp >= 24 else (80 if >= 22 else 50)  # 60% weight
    timer_score = min(100, timer_usage * 1.2)  # 25% weight
    anomaly_penalty = min(100, anomaly_events * 3)  # 15% weight
    return temp_score * 0.60 + timer_score * 0.25 + (100 - anomaly_penalty) * 0.15
```

**Why:** A Chennai family using AC 10 hours EFFICIENTLY should be rewarded. Stop WASTAGE, not USAGE.

### 3. ANTI-GAMING BASELINE

**OLD (WRONG):** Mean of trial months
```python
# WRONG - Gameable via inflated trial usage
baseline = mean(month1, month2, month3)
```

**NEW (CORRECT):** Median + hard cap
```python
# CORRECT - Resistant to gaming
baseline = min(median(month2, month3), segment_default * 1.20)
```

**Why:** Prevents strategic inflation of baseline. 120% cap ensures fairness.

### 4. POSITIVE FRAMING

**OLD (WRONG):** Penalty for overuse
```
"You ran AC at 18°C. Inefficiency penalty: ₹100"
```

**NEW (CORRECT):** Discount earned
```
"Your Efficiency Score: 92! 🏆 You earned ₹130 off your bill!"
```

**Why:** People HATE fees (pain) but LOVE discounts (gain). Same economics, better psychology.

---

## DOCUMENTATION WORKFLOW

**After implementing ANY formula or method, update DOCUMENTATION.md with:**
- The formula itself
- Why it was chosen
- Alternatives considered
- Validation results

**After gaining ANY insight, add to Key Insights section with date and evidence.**

---

## VERIFICATION FRAMEWORK

Use `VERIFICATION_CHECKLIST.md` after completing each phase. Key checkpoints:

| Checkpoint | When | What to Verify |
|------------|------|----------------|
| **1. Pre-Implementation** | Before coding | Understand bucket model, efficiency score, no double-charging |
| **2. Pricing Logic** | After pricing | Fee range ₹400-1000, overage cap exists, hours not kWh |
| **3. Reward Mechanism** | After rewards | Behavior-based score, positive framing, anti-gaming baseline |
| **4. Economic Bounds** | After simulation | Margin 10-35%, savings 5-25%, break-even 12-30 months |
| **5. Performance** | After simulation | No nested loops, vectorized operations, <10s for 1000×36 |
| **6. Outputs** | Before completion | Segment proportions match, seasonality affects cash flow |

---

# SESP Pricing Model — Claude Code Instructions

## PROJECT OVERVIEW

You are building a **dynamic pricing simulation and optimization dashboard** for the Smart Energy-Saver Subscription Program (SESP). This is a subscription-based model for IoT-enabled home appliances (AC and Refrigerator) in India.

**Business Model:**
1. Customer pays a **subsidized upfront cost** for a new smart appliance
2. Customer pays a **monthly subscription fee** for services (maintenance, warranty, IoT monitoring, energy optimization)
3. The subscription must provide **more value than it costs** from the customer's perspective
4. The company must **recover the subsidy and make profit** over the customer lifetime

**Your job:** Build a model that finds the optimal combination of:
- Subsidy level
- Monthly subscription fee
- Reward/penalty rates for energy usage
- Contract terms

...while satisfying multiple constraints (participation, profitability, incentive compatibility, cash flow).

---

## CRITICAL INDIA-SPECIFIC ADJUSTMENTS

The model MUST incorporate these four corrections. Do not build a naive model that ignores these.

### 1. SEASONALITY (AC Only)

**Problem:** AC usage is not flat. It peaks in summer and drops to near-zero in winter.

**Implementation:**
```python
# Seasonality index by month (Jan = index 0, Dec = index 11)
# This is for NORTH INDIA. Other regions need different profiles.

SEASONALITY_NORTH = [0.05, 0.15, 0.60, 1.40, 1.70, 1.30, 0.80, 0.70, 0.80, 0.50, 0.15, 0.05]
SEASONALITY_SOUTH = [0.40, 0.50, 0.80, 1.20, 1.30, 1.10, 0.90, 0.90, 0.90, 0.70, 0.50, 0.40]
SEASONALITY_WEST = [0.20, 0.30, 0.70, 1.30, 1.50, 1.20, 0.80, 0.80, 0.90, 0.60, 0.30, 0.20]
SEASONALITY_EAST = [0.15, 0.25, 0.65, 1.35, 1.60, 1.25, 0.85, 0.85, 0.90, 0.55, 0.25, 0.15]

# For refrigerator (nearly flat, slight summer increase)
SEASONALITY_FRIDGE = [0.95, 0.95, 1.00, 1.05, 1.10, 1.10, 1.05, 1.05, 1.00, 1.00, 0.95, 0.95]

# Usage calculation
def monthly_usage(baseline_annual_kwh, month_index, appliance_type, region):
    if appliance_type == "AC":
        seasonality = get_seasonality_profile(region)
    else:
        seasonality = SEASONALITY_FRIDGE

    # Baseline is annual; convert to monthly baseline first
    monthly_baseline = baseline_annual_kwh / 12

    # Apply seasonality
    return monthly_baseline * seasonality[month_index]
```

**Why this matters:**
- Cash flow: Company receives low subscription value in winter (if usage-based component exists)
- Customer perception: "Bill shock" in May when usage spikes
- Rewards/penalties: Must be calibrated against seasonal baseline, not flat annual

### 2. ASSET OWNERSHIP ADJUSTMENT

**Problem:** Buying creates an asset with residual value. Subscription does not.

**Implementation:**
```python
# Resale/terminal values (conservative estimates)
TERMINAL_VALUES = {
    "AC": {
        "year_3": 10000,
        "year_5": 5000,
        "year_7": 2500,
        "year_10": 1500  # Scrap value
    },
    "FRIDGE": {
        "year_3": 9000,
        "year_5": 6000,
        "year_7": 4000,
        "year_10": 2500
    }
}

def adjusted_purchase_cost(mrp, tenure_years, appliance_type, discount_rate):
    """
    Calculate the TRUE cost of purchasing, accounting for terminal value.

    Adjusted_Cost = MRP - PV(Terminal_Value)
    """
    terminal_value = get_terminal_value(appliance_type, tenure_years)
    pv_terminal = terminal_value / ((1 + discount_rate) ** tenure_years)

    return mrp - pv_terminal
```

**Why this matters:**
- Participation constraint comparison must be fair
- Without this, we overstate subscription's attractiveness
- Customer intuitively knows they "own something" with purchase

### 3. DUAL DISCOUNT RATES

**Problem:** Firm and customer have very different cost of capital.

**Implementation:**
```python
# Discount rates
DISCOUNT_RATE_FIRM = 0.12  # 12% — WACC for large manufacturer
DISCOUNT_RATE_CUSTOMER = {
    "affluent": 0.14,        # High income, has savings
    "upper_middle": 0.20,    # Moderate savings
    "middle": 0.25,          # Cash-constrained
    "lower_middle": 0.30     # Very cash-constrained
}

def npv_customer(cash_flows, segment):
    """Calculate NPV from customer's perspective."""
    rate = DISCOUNT_RATE_CUSTOMER[segment]
    return sum(cf / ((1 + rate/12) ** t) for t, cf in enumerate(cash_flows))

def npv_firm(cash_flows):
    """Calculate NPV from firm's perspective."""
    rate = DISCOUNT_RATE_FIRM
    return sum(cf / ((1 + rate/12) ** t) for t, cf in enumerate(cash_flows))
```

**Why this matters:**
- Creates "value arbitrage" — firm can finance cheaply, customer cannot
- Same monthly payment feels different to firm vs customer
- Enables subsidy model to work economically

### 4. GST LEAKAGE

**Problem:** Subscription attracts recurring GST; product purchase is one-time GST.

**Implementation:**
```python
GST_RATE_PRODUCT = 0.18  # 18% on appliances
GST_RATE_SERVICE = 0.18  # 18% on services

def calculate_gst_purchase(mrp):
    """GST already included in MRP for appliances."""
    # MRP is inclusive, so GST component is:
    return mrp - (mrp / 1.18)

def calculate_gst_subscription(monthly_fee, tenure_months):
    """GST on each month's subscription."""
    monthly_gst = monthly_fee * GST_RATE_SERVICE
    return monthly_gst * tenure_months

def total_gst_sesp(subsidized_price, monthly_fee, tenure_months):
    """Total GST in SESP model."""
    gst_product = calculate_gst_purchase(subsidized_price)
    gst_service = calculate_gst_subscription(monthly_fee, tenure_months)
    return gst_product + gst_service
```

**Why this matters:**
- Subscription model pays ~10-20% more GST over tenure
- Must be factored into pricing to maintain profitability
- Affects customer's true total cost

---

## CORE MODEL PARAMETERS

### A. APPLIANCE PARAMETERS

```python
APPLIANCES = {
    "AC_1.5T_5STAR_INVERTER": {
        "mrp": 45000,
        "manufacturing_cost": 30000,
        "installation_cost": 2500,
        "iot_hardware_cost": 1500,
        "iot_annual_recurring": 600,
        "annual_maintenance_cost": 1200,
        "warranty_reserve_per_unit": 2000,
        "expected_life_years": 10,
        "subscription_viable_years": 7,  # Exit before major failures
        "baseline_annual_kwh": {
            "light": 500,
            "moderate": 1100,
            "heavy": 1800
        },
        "terminal_value_year_5": 5000
    },
    "FRIDGE_280L_FROST_FREE": {
        "mrp": 30000,
        "manufacturing_cost": 19500,
        "installation_cost": 0,
        "iot_hardware_cost": 1500,
        "iot_annual_recurring": 600,
        "annual_maintenance_cost": 500,
        "warranty_reserve_per_unit": 1200,
        "expected_life_years": 12,
        "subscription_viable_years": 10,
        "baseline_annual_kwh": {
            "light": 220,
            "moderate": 300,
            "heavy": 400
        },
        "terminal_value_year_5": 6000
    }
}
```

### B. MARKET PARAMETERS

```python
MARKET_PARAMS = {
    "electricity_rate_per_kwh": {
        "slab_1": {"limit": 200, "rate": 3.5},   # 0-200 units
        "slab_2": {"limit": 400, "rate": 5.0},   # 201-400 units
        "slab_3": {"limit": 800, "rate": 6.5},   # 401-800 units
        "slab_4": {"limit": 99999, "rate": 7.5}  # 800+ units
    },
    "electricity_avg_rate": 6.0,  # Simplified average
    "electricity_annual_inflation": 0.04,  # 4% annual increase

    "competitor_rental_monthly": {"low": 1200, "high": 1800},
    "emi_12_month": {"low": 3800, "high": 4200},
    "amc_annual": {"low": 2000, "high": 3500},
    "extended_warranty_cost": {"low": 3000, "high": 5000},

    "customer_acquisition_cost": 2000,
    "referral_rate": 0.12,  # 12% of customers refer
    "referral_value": 500    # Savings per referral
}
```

### C. CUSTOMER SEGMENTS

```python
CUSTOMER_SEGMENTS = {
    "light_user": {
        "proportion": 0.30,
        "usage_profile": "light",
        "price_sensitivity": "high",
        "discount_rate": 0.25,
        "churn_risk": "medium",
        "default_risk": 0.03,
        "energy_savings_potential": 0.08  # 8% savings achievable
    },
    "moderate_user": {
        "proportion": 0.50,
        "usage_profile": "moderate",
        "price_sensitivity": "medium",
        "discount_rate": 0.22,
        "churn_risk": "low",
        "default_risk": 0.025,
        "energy_savings_potential": 0.15  # 15% savings achievable
    },
    "heavy_user": {
        "proportion": 0.20,
        "usage_profile": "heavy",
        "price_sensitivity": "low",
        "discount_rate": 0.18,
        "churn_risk": "low",
        "default_risk": 0.02,
        "energy_savings_potential": 0.20  # 20% savings achievable
    }
}
```

### D. DECISION VARIABLES (What we're optimizing)

```python
DECISION_VARIABLES = {
    "subsidy": {
        "min": 5000,
        "max": 20000,
        "step": 1000,
        "description": "Amount deducted from MRP for customer"
    },
    "monthly_fee": {
        "min": 299,
        "max": 999,
        "step": 50,
        "description": "Base monthly subscription fee"
    },
    "tenure_months": {
        "options": [12, 24, 36, 48],
        "description": "Minimum contract duration"
    },
    "deposit": {
        "min": 3000,
        "max": 10000,
        "step": 1000,
        "description": "Refundable security deposit"
    },
    # ⚠️ V2 UPDATE: reward_rate and penalty_rate are SUPERSEDED by Efficiency Score
    # See CRITICAL MODEL CORRECTIONS (V2) section above
    # Use efficiency_score-based discounts instead of usage-volume rewards
    "efficiency_discount_tiers": {
        "champion": {"score_threshold": 90, "discount_percent": 0.20},
        "star": {"score_threshold": 75, "discount_percent": 0.12},
        "aware": {"score_threshold": 60, "discount_percent": 0.05},
        "description": "% discount based on efficiency score (behavior, not usage volume)"
    },
    "overage_fee": {
        "light_per_hour": 5, "moderate_per_hour": 4, "heavy_per_hour": 3,
        "max_cap": {"light": 200, "moderate": 250, "heavy": 300},
        "description": "Fee for exceeding included runtime hours (wear & tear, not electricity)"
    }
}
```

---

## CONSTRAINTS (Must All Be Satisfied)

### Constraint 1: PARTICIPATION CONSTRAINT (Customer)

**Verbal:** Customer must prefer SESP over buying outright.

**Mathematical:**
```
NPV_customer(SESP_costs) < NPV_customer(Purchase_costs) * (1 - threshold)

Where:
- SESP_costs = Subsidized_Price + Σ(Monthly_Fee_t * (1 + GST))
- Purchase_costs = MRP + AMC_costs + Repair_risk - PV(Terminal_Value)
- threshold = 0.10 (must be at least 10% better)
```

**Implementation:**
```python
def check_participation_constraint(params, appliance, segment, threshold=0.10):
    """
    Returns True if SESP is attractive enough vs purchase.
    """
    # Customer's discount rate
    r = DISCOUNT_RATE_CUSTOMER[segment]
    tenure = params["tenure_months"]

    # SESP total cost (NPV)
    upfront = params["subsidized_price"] * 1.18  # Including GST
    monthly_payments = [params["monthly_fee"] * 1.18 for _ in range(tenure)]
    sesp_npv = upfront + npv_customer(monthly_payments, segment)

    # Purchase total cost (NPV)
    purchase_upfront = appliance["mrp"]
    amc_annual = 2500  # Conservative estimate
    amc_payments = [amc_annual/12 for _ in range(tenure)]
    terminal_value = get_terminal_value(appliance, tenure/12)
    terminal_pv = terminal_value / ((1 + r) ** (tenure/12))

    purchase_npv = purchase_upfront + npv_customer(amc_payments, segment) - terminal_pv

    # Check constraint
    return sesp_npv < purchase_npv * (1 - threshold)
```

### Constraint 2: PROFITABILITY CONSTRAINT (Firm)

**Verbal:** Company must make target margin over customer lifetime.

**Mathematical:**
```
NPV_firm(Revenue_Stream) >= NPV_firm(Cost_Stream) * (1 + target_margin)

Where:
- Revenue = Subsidized_Price + Σ(Monthly_Fee_t) + Penalty_Revenue + Add_on_Revenue
- Costs = Manufacturing + IoT + Installation + Maintenance + Warranty + Support + CAC
- target_margin = 0.15 (minimum 15%)
```

**Implementation:**
```python
def check_profitability_constraint(params, appliance, segment_mix, target_margin=0.15):
    """
    Returns True if firm achieves target margin.
    """
    tenure = params["tenure_months"]

    # Revenue stream
    upfront_revenue = params["subsidized_price"]  # Net of GST (firm receives less)
    monthly_revenue = [params["monthly_fee"] * 0.847 for _ in range(tenure)]  # Net of GST
    # Note: GST collected is passed to government, not revenue

    # Additional revenue (conservative)
    penalty_revenue = estimate_penalty_revenue(params, segment_mix, tenure)
    addon_revenue = estimate_addon_revenue(tenure)

    total_revenue_npv = upfront_revenue + npv_firm(monthly_revenue) + penalty_revenue + addon_revenue

    # Cost stream
    manufacturing = appliance["manufacturing_cost"]
    iot_hardware = appliance["iot_hardware_cost"]
    installation = appliance["installation_cost"]
    iot_recurring = [appliance["iot_annual_recurring"]/12 for _ in range(tenure)]
    maintenance = [appliance["annual_maintenance_cost"]/12 for _ in range(tenure)]
    warranty = appliance["warranty_reserve_per_unit"]
    support = 500 * (tenure / 12)  # ₹500/year
    cac = MARKET_PARAMS["customer_acquisition_cost"]

    total_cost_npv = (manufacturing + iot_hardware + installation + warranty + cac +
                      npv_firm(iot_recurring) + npv_firm(maintenance) + support)

    # Check constraint
    actual_margin = (total_revenue_npv - total_cost_npv) / total_cost_npv
    return actual_margin >= target_margin, actual_margin
```

### Constraint 3: CASH FLOW CONSTRAINT (Firm)

**Verbal:** Cumulative cash flow must not go deeply negative.

**Mathematical:**
```
For all t: Cumulative_Cash_Flow_t >= -MAX_NEGATIVE_THRESHOLD

Where MAX_NEGATIVE_THRESHOLD = per unit cash outflow limit (e.g., ₹10,000)
```

**Implementation:**
```python
def check_cashflow_constraint(params, appliance, max_negative=10000):
    """
    Returns True if cash flow stays within acceptable range.
    Also returns month of break-even.
    """
    tenure = params["tenure_months"]

    # Month 0: Big outflow
    month_0_outflow = (appliance["manufacturing_cost"] +
                       appliance["iot_hardware_cost"] +
                       appliance["installation_cost"] +
                       MARKET_PARAMS["customer_acquisition_cost"])
    month_0_inflow = params["subsidized_price"] + params["deposit"]

    cumulative = month_0_inflow - month_0_outflow
    min_cumulative = cumulative
    breakeven_month = None

    monthly_inflow = params["monthly_fee"] * 0.847  # Net of GST
    monthly_outflow = (appliance["iot_annual_recurring"] +
                       appliance["annual_maintenance_cost"]) / 12

    cash_flows = [cumulative]

    for month in range(1, tenure + 1):
        cumulative += (monthly_inflow - monthly_outflow)
        cash_flows.append(cumulative)
        min_cumulative = min(min_cumulative, cumulative)

        if breakeven_month is None and cumulative >= 0:
            breakeven_month = month

    constraint_satisfied = min_cumulative >= -max_negative

    return constraint_satisfied, breakeven_month, cash_flows, min_cumulative
```

### Constraint 4: INCENTIVE COMPATIBILITY (Self-Selection)

**Verbal:** Heavy users should not benefit from choosing Light plan. Light users should not be overcharged on Heavy plan.

**Mathematical:**
```
For Heavy user H:
U_H(Heavy_Plan) >= U_H(Light_Plan)

For Light user L:
U_L(Light_Plan) >= U_L(Heavy_Plan)
```

**Implementation:**
```python
def check_incentive_compatibility(plans, segments):
    """
    Returns True if plan design prevents gaming.
    """
    for segment_name, segment in segments.items():
        intended_plan = get_intended_plan(segment_name)
        utility_intended = calculate_utility(segment, intended_plan)

        for plan_name, plan in plans.items():
            if plan_name != intended_plan:
                utility_other = calculate_utility(segment, plan)
                if utility_other > utility_intended:
                    return False, f"{segment_name} prefers {plan_name} over {intended_plan}"

    return True, "All segments prefer their intended plan"
```

### Constraint 5: MORAL HAZARD MITIGATION

**Verbal:** Overage fee and plan structure must deter gaming.

**⚠️ V2 UPDATE:** Replaced kWh-based penalty with hours-based overage.

**Mathematical (V2):**
```
Overage_Cost(Light_plan + heavy_use) > Heavy_plan_fee

Where:
- Overage kicks in when hours > plan.hours_included
- Capped overage prevents bill shock
- Self-selection: Heavy user choosing Light plan ends up paying MORE
```

**Implementation (V2):**
```python
def check_moral_hazard_constraint_v2(plans, segment_usage):
    """
    Returns True if plan self-selection is incentive-compatible.

    V2: Uses hours-based overage, not kWh-based penalty.
    """
    # Heavy user on Light plan
    light_plan = plans['light']
    heavy_hours = segment_usage['heavy']['monthly_hours']  # e.g., 350

    if heavy_hours > light_plan['hours_included']:
        excess = heavy_hours - light_plan['hours_included']  # 350 - 150 = 200
        overage = min(excess * light_plan['overage_per_hour'], light_plan['max_overage'])  # min(1000, 200) = 200
        total_light = light_plan['fee'] + overage  # 499 + 200 = 699
    else:
        total_light = light_plan['fee']

    # Heavy user on Heavy plan (correct choice)
    total_heavy = plans['heavy']['fee']  # 899

    # For IC to work: Heavy plan should be cheaper for heavy users
    # This fails here (699 < 899), so we need higher overage or lower cap
    # Key: Overage structure must make wrong-plan-choice expensive

    return total_light >= total_heavy * 0.95  # Allow 5% tolerance
```

**V2 Key Insight:** Self-selection works when overage makes gaming unprofitable.

---

## MODEL OUTPUTS REQUIRED

### Output 1: Unit Economics Summary

```python
def generate_unit_economics(params, appliance, segment):
    """
    Returns comprehensive unit economics for one subscription.
    """
    return {
        "customer": {
            "upfront_paid": params["subsidized_price"] + params["deposit"],
            "monthly_payment": params["monthly_fee"] * 1.18,
            "total_paid_tenure": ...,
            "effective_monthly_cost": ...,
            "savings_vs_purchase": ...,
            "savings_vs_emi": ...,
        },
        "company": {
            "upfront_received": params["subsidized_price"],
            "total_revenue": ...,
            "total_cost": ...,
            "gross_margin": ...,
            "gross_margin_percent": ...,
            "breakeven_month": ...,
            "npv_profit": ...,
        },
        "value_delivered": {
            "energy_savings_annual": ...,
            "maintenance_value": ...,
            "warranty_value": ...,
            "convenience_value": ...,
            "total_value": ...,
            "value_vs_fee_ratio": ...
        }
    }
```

### Output 2: Monthly Cash Flow Projection

```python
def generate_cashflow_projection(params, appliance, tenure_months):
    """
    Returns month-by-month cash flow with seasonality.
    """
    return {
        "months": [0, 1, 2, ..., tenure_months],
        "inflows": [...],
        "outflows": [...],
        "net_cashflow": [...],
        "cumulative_cashflow": [...],
        "seasonal_revenue_adjustment": [...],  # If usage-based component
    }
```

### Output 3: Sensitivity Analysis

```python
def run_sensitivity_analysis(base_params, appliance, variable, range_values):
    """
    Returns impact of varying one parameter on key outcomes.
    """
    return {
        "variable": variable,
        "values": range_values,
        "customer_npv": [...],
        "company_margin": [...],
        "breakeven_month": [...],
        "participation_satisfied": [...],
        "profitability_satisfied": [...]
    }
```

### Output 4: Scenario Comparison

```python
def compare_scenarios(scenarios, appliance):
    """
    Returns side-by-side comparison of multiple pricing scenarios.
    """
    return {
        "scenario_names": [...],
        "customer_total_cost": [...],
        "customer_savings_vs_buy": [...],
        "company_margin": [...],
        "breakeven_months": [...],
        "constraints_satisfied": [...],
        "recommendation": "..."
    }
```

### Output 5: Optimal Pricing Recommendation

```python
def find_optimal_pricing(appliance, constraints, objective="maximize_margin"):
    """
    Returns optimal parameter combination.
    """
    return {
        "optimal_subsidy": ...,
        "optimal_monthly_fee": ...,
        "optimal_tenure": ...,
        "optimal_deposit": ...,
        "optimal_reward_rate": ...,
        "optimal_penalty_rate": ...,
        "resulting_margin": ...,
        "customer_savings": ...,
        "constraints_status": {...}
    }
```

---

## DASHBOARD VIEWS TO BUILD

### Dashboard 1: Pricing Scenario Builder

**Purpose:** Interactive exploration of pricing combinations

**Components:**
- Sliders: Subsidy, Monthly Fee, Tenure, Deposit
- Real-time unit economics display
- Constraint status indicators (green/red)
- Comparison to alternatives (purchase, EMI, rental)

### Dashboard 2: Sensitivity Analysis

**Purpose:** Understand which parameters matter most

**Components:**
- Tornado chart (ranked parameter importance)
- Spider/radar chart (multi-parameter view)
- Two-way sensitivity heatmap (Subsidy × Fee grid)

### Dashboard 3: Cash Flow Timeline

**Purpose:** Visualize monthly cash position

**Components:**
- Line chart: Monthly and cumulative cash flow
- Seasonality overlay for AC
- Break-even marker
- Risk zone highlighting (negative cash periods)

### Dashboard 4: Customer Segment Analysis

**Purpose:** Understand segment-specific economics

**Components:**
- Segment selector
- Per-segment unit economics
- Participation constraint check by segment
- Recommended pricing by segment

### Dashboard 5: Monte Carlo Risk Analysis

**Purpose:** Understand outcome distribution under uncertainty

**Components:**
- Input: Parameter distributions
- Output: Profit distribution histogram
- Probability of loss
- Key risk drivers identification

### Dashboard 6: Optimization Results

**Purpose:** Show optimal pricing and trade-offs

**Components:**
- Optimal parameter values
- Constraint satisfaction status
- Trade-off visualization (margin vs customer savings)
- Pareto frontier if multiple objectives

---

## TESTING REQUIREMENTS

### Test Case 1: Participation Constraint Validation

```python
def test_participation_constraint():
    """
    Verify that a high-subsidy, low-fee scenario passes participation constraint.
    """
    params = {
        "subsidized_price": 28000,  # ₹17,000 subsidy
        "monthly_fee": 499,
        "tenure_months": 36,
        "deposit": 5000
    }
    appliance = APPLIANCES["AC_1.5T_5STAR_INVERTER"]

    result = check_participation_constraint(params, appliance, "middle")
    assert result == True, "High subsidy should satisfy participation constraint"
```

### Test Case 2: Profitability Constraint Validation

```python
def test_profitability_constraint():
    """
    Verify that a low-subsidy, high-fee scenario passes profitability constraint.
    """
    params = {
        "subsidized_price": 40000,  # ₹5,000 subsidy
        "monthly_fee": 799,
        "tenure_months": 36,
        "deposit": 5000
    }
    appliance = APPLIANCES["AC_1.5T_5STAR_INVERTER"]

    result, margin = check_profitability_constraint(params, appliance, CUSTOMER_SEGMENTS)
    assert result == True, f"Low subsidy should be profitable. Margin: {margin}"
```

### Test Case 3: Seasonality Impact

```python
def test_seasonality_cashflow():
    """
    Verify that winter months show reduced usage-based revenue.
    """
    params = {"monthly_fee": 599, "usage_fee_rate": 0.5}  # 50% usage-based

    summer_revenue = calculate_monthly_revenue(params, month=4, region="north")
    winter_revenue = calculate_monthly_revenue(params, month=11, region="north")

    assert summer_revenue > winter_revenue * 5, "Summer revenue should be much higher"
```

### Test Case 4: GST Calculation

```python
def test_gst_leakage():
    """
    Verify GST is correctly calculated for both models.
    """
    mrp = 45000
    subsidized = 32000
    monthly_fee = 599
    tenure = 36

    gst_purchase = calculate_gst_purchase(mrp)
    gst_sesp = total_gst_sesp(subsidized, monthly_fee, tenure)

    assert gst_sesp > gst_purchase, "SESP should have higher total GST"
    print(f"GST leakage: ₹{gst_sesp - gst_purchase}")
```

---

## ITERATION WORKFLOW

1. **Start with base parameters** → Check all constraints
2. **If participation fails** → Increase subsidy OR decrease fee
3. **If profitability fails** → Decrease subsidy OR increase fee OR increase tenure
4. **If cash flow fails** → Increase deposit OR decrease subsidy OR increase upfront price
5. **Run sensitivity** → Identify which parameters have most impact
6. **Run Monte Carlo** → Understand risk profile
7. **Find Pareto optimal** → Trade-off between margin and customer savings
8. **Recommend final pricing** → With justification

---

## FILES TO CREATE

```
/SESP_Model/
├── config/
│   ├── appliances.json
│   ├── market_params.json
│   ├── customer_segments.json
│   └── seasonality.json
├── src/
│   ├── unit_economics.py
│   ├── constraints.py
│   ├── cashflow.py
│   ├── optimization.py
│   ├── simulation.py
│   └── utils.py
├── dashboard/
│   ├── app.py (Streamlit main)
│   ├── pages/
│   │   ├── pricing_builder.py
│   │   ├── sensitivity.py
│   │   ├── cashflow.py
│   │   ├── segments.py
│   │   ├── monte_carlo.py
│   │   └── optimization.py
│   └── components/
│       ├── charts.py
│       └── widgets.py
├── tests/
│   ├── test_constraints.py
│   ├── test_economics.py
│   └── test_seasonality.py
├── data/
│   └── (output files, simulation results)
├── requirements.txt
└── README.md
```

---

## NOTES FOR CLAUDE CODE

1. **Always validate constraints** before showing any "optimal" result
2. **Show warnings** when parameters are near constraint boundaries
3. **Use conservative estimates** — better to underestimate profit than overestimate
4. **Visualize trade-offs** — customer savings vs company margin is the core tension
5. **Segment matters** — never show aggregate results without segment breakdown
6. **Seasonality is critical for AC** — never use flat monthly assumptions
7. **GST is real cost** — always include in customer's view of total cost
8. **Cash flow timing matters** — NPV positive but cash flow negative in early months is a problem

---

## QUESTIONS TO ASK USER IF UNCLEAR

1. Which appliance to model first? (AC or Fridge)
2. Which region's seasonality to use? (North/South/West/East)
3. What is the target customer segment? (Middle income default)
4. What is minimum acceptable margin? (15% default)
5. What is maximum acceptable break-even period? (24 months default)
6. Should we include usage-based pricing component or pure fixed fee?

---

## PATCHES TO APPLY (V2)

⚠️ **MANDATORY:** Before implementing any task, apply the patches from `SESP_Claude_Instructions/PATCHES.md`.

### Quick Reference — What Changes

| Original Pattern | V2 Replacement | Why |
|------------------|----------------|-----|
| kWh × rate pricing | Bucket hours model | Avoids double-charging |
| Usage-volume rewards | Efficiency Score | Rewards behavior, not outcome |
| Mean baseline | Median + 120% cap | Prevents gaming |
| Inconsistent GST | GST on ALL services | Fair comparison |
| Nested loops | Vectorized pandas | Performance |
| Penalty framing | Discount framing | Better psychology |

### Sanity Check Before Coding

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

## FILE DEPENDENCIES

```
Root Directory:
├── CLAUDE.md                    # This file - main instructions
├── CRITICAL_INSIGHTS.md         # ⚠️ READ FIRST - errors to avoid
├── TODOLIST_FINAL.md            # Execution roadmap (6 phases)
├── VERIFICATION_CHECKLIST.md    # Checkpoint verification
├── DOCUMENTATION.md             # Track formulas, methods, insights
└── SESP_Claude_Instructions/
    ├── PATCHES.md               # Code corrections to apply
    ├── README.md                # Quick reference
    ├── claude.md                # Original detailed spec (apply patches)
    └── config/
        ├── pricing_formula_PATCHED.json  # ✅ Use this for pricing
        ├── appliances.json
        ├── customer_segments.json
        ├── decision_variables.json
        └── market_params.json
```

---

## VERSION HISTORY

| Date | Change | Reason |
|------|--------|--------|
| 2025-01-03 | Added V2 critical corrections | Bucket model, efficiency score, anti-gaming |
| 2025-01-03 | Added verification framework | Checkpoint-based validation |
| 2025-01-03 | Added documentation workflow | Track formulas and insights |
| 2025-01-03 | Updated moral hazard constraint | Hours-based overage, not kWh penalty |
