# SESP PROJECT — FINALIZED EXECUTION TODOLIST (PATCHED)

## ⚠️ PRE-REQUISITE: READ THESE FIRST

Before starting ANY task:
1. Read `CRITICAL_INSIGHTS.md` — Understand errors to avoid
2. Read `PATCHES.md` — Know the corrections to apply
3. Load `config/pricing_formula_PATCHED.json` — Use corrected parameters

---

## DELIVERABLE CHECKLIST

| # | Deliverable | Tasks | Status |
|---|-------------|-------|--------|
| 1 | Pricing formula + rationale | 1.1, 1.2, 1.3 | ☐ |
| 2 | Reward-penalty structure + justification | 2.1, 2.2, 2.3, 2.4 | ☐ |
| 3 | Simulation results with hypothetical data | 4.1, 4.2, 4.3, 4.4 | ☐ |
| 4 | Code/analysis in separate file | All code files | ☐ |
| 5 | Profitability comparison (before vs after) | 3.1, 3.2, 3.3 | ☐ |
| 6 | Moral hazard measures | 2.5, 2.6 | ☐ |
| 7 | Participation + IC constraint discussion | 1.4, 1.5, 2.3 | ☐ |
| 8 | Practical recommendations for India | 5.1, 5.2, 5.3 | ☐ |

---

## PHASE 1: PRICING MECHANISM DESIGN

### Task 1.1: Implement Bucket-Based Pricing Model ✏️ PATCHED v2

**Key change:** Use "Mobile Data" style hour buckets, NOT tier premiums or kWh-based fees.

**The Model (CORRECTED):**
```
Customer CHOOSES a plan based on their needs:
  Light:    ₹499/month → 150 hours included
  Moderate: ₹649/month → 225 hours included  
  Heavy:    ₹899/month → 350 hours included

Within hours: Usage feels "free" (already paid for access)
Beyond hours: Overage fee (wear & tear, like mobile data)
Reward: Efficiency Score DISCOUNT (behavior-based, not usage-based)
```

**Why hours, not kWh?**
- Hours = runtime = wear on OUR machine (our cost domain)
- kWh = electricity = Discom's domain (customer pays separately)
- No double-charging: we charge for ACCESS, Discom charges for POWER

**Sub-tasks:**

| # | Task | Output | Validation |
|---|------|--------|------------|
| 1.1.1 | Define plan structure (hours, fees) | `SUBSCRIPTION_PLANS` config | Plans make economic sense |
| 1.1.2 | Implement `calculate_overage()` | Function | Caps at max, clear messaging |
| 1.1.3 | Implement `calculate_efficiency_score()` | Function | Measures behavior, not just usage |
| 1.1.4 | Implement `calculate_efficiency_discount()` | Function | Positive framing (discount) |
| 1.1.5 | Implement `calculate_monthly_bill()` | Function | Base + Overage - Discount + GST |
| 1.1.6 | Implement `validate_no_double_charging()` | Function | Confirms we charge hours, not kWh |
| 1.1.7 | Document self-selection energy savings | Markdown | How bucket choice saves energy |

**Hypothetical data (PATCHED v2):**
```python
SUBSCRIPTION_PLANS = {
    'light': {
        'monthly_fee': 499,
        'hours_included': 150,
        'overage_per_hour': 5,
        'max_overage': 200
    },
    'moderate': {
        'monthly_fee': 649,
        'hours_included': 225,
        'overage_per_hour': 4,
        'max_overage': 250
    },
    'heavy': {
        'monthly_fee': 899,
        'hours_included': 350,
        'overage_per_hour': 3,
        'max_overage': 300
    }
}

# Self-selection creates energy savings:
# Customer picks cheaper plan → budgets usage → saves energy voluntarily
```

**Output file:** `src/pricing/bucket_model.py`

---

### Task 1.2: Implement India-Specific Adjustments

**Sub-tasks:**

| # | Task | Output | Validation |
|---|------|--------|------------|
| 1.2.1 | Implement `apply_seasonality()` for AC | Function | Summer months = 1.5-1.7x |
| 1.2.2 | Implement `calculate_gst_consistent()` | Function | 18% on ALL services |
| 1.2.3 | Implement `npv_customer()` with segment rate | Function | Uses 16-28% rate |
| 1.2.4 | Implement `npv_firm()` | Function | Uses 12% rate |
| 1.2.5 | Implement `calculate_electricity_cost_slabs()` | Function | Slab-based calculation |
| 1.2.6 | Implement `adjusted_purchase_cost_with_terminal()` | Function | Subtracts resale value |

**GST consistency check (CRITICAL):**
```python
def validate_gst_consistency(sesp_costs, purchase_costs):
    """Ensure GST applied to ALL service components in BOTH scenarios"""
    
    # SESP side
    assert sesp_costs['upfront_gst_applied'] == True
    assert sesp_costs['monthly_gst_applied'] == True
    
    # Purchase side (often forgotten!)
    assert purchase_costs['amc_gst_applied'] == True
    assert purchase_costs['repair_gst_applied'] == True
    assert purchase_costs['extended_warranty_gst_applied'] == True
    
    return True
```

**Output file:** `src/adjustments/india_specific.py`

---

### Task 1.3: Create Alternative Cost Calculators

**Sub-tasks:**

| # | Task | Output | Validation |
|---|------|--------|------------|
| 1.3.1 | `calculate_purchase_cost()` | Function | Includes GST on AMC, repairs |
| 1.3.2 | `calculate_emi_cost()` | Function | Interest + processing fee |
| 1.3.3 | `calculate_rental_cost()` | Function | Monthly × tenure + deposit |
| 1.3.4 | `calculate_sesp_cost()` | Function | Upfront + monthly (both with GST) |
| 1.3.5 | `compare_alternatives()` | Function | Returns comparison table |

**Example output:**
```
Alternative Comparison (24-month horizon, Moderate user):
┌──────────────┬───────────────┬──────────────┐
│ Alternative  │ Total Cost    │ vs SESP      │
├──────────────┼───────────────┼──────────────┤
│ SESP         │ ₹52,800       │ —            │
│ Purchase     │ ₹55,400       │ +₹2,600      │
│ EMI (24m)    │ ₹54,200       │ +₹1,400      │
│ Rental       │ ₹41,400       │ -₹11,400     │
└──────────────┴───────────────┴──────────────┘
Note: Rental is cheaper but uses refurbished goods
```

**Output file:** `src/alternatives/calculators.py`

---

### Task 1.4: Implement Participation Constraint Checker

**Mathematical formulation:**
```
NPV_customer(SESP) < NPV_customer(Purchase) × (1 - threshold)
threshold = 0.10 (must be at least 10% better)

Use CUSTOMER's discount rate (16-28% depending on segment)
```

**Sub-tasks:**

| # | Task | Output | Validation |
|---|------|--------|------------|
| 1.4.1 | `check_pc_vs_purchase()` | Function | Returns satisfied + margin |
| 1.4.2 | `check_pc_vs_emi()` | Function | Returns satisfied + margin |
| 1.4.3 | `validate_participation()` | Function | Aggregate check |
| 1.4.4 | `find_pc_boundary()` | Function | Where constraint flips |

**Output file:** `src/constraints/participation.py`

---

### Task 1.5: Implement Incentive Compatibility Checker

**Mathematical formulation:**
```
For each segment θ ∈ {Light, Moderate, Heavy}:
  U(θ, Plan_θ) ≥ U(θ, Plan_other) for all other plans

Utility = -Total_Cost + Service_Value
```

**Sub-tasks:**

| # | Task | Output | Validation |
|---|------|--------|------------|
| 1.5.1 | `calculate_utility()` | Function | Cost + value for segment × plan |
| 1.5.2 | `check_ic_light()` | Function | Light prefers Light plan |
| 1.5.3 | `check_ic_moderate()` | Function | Moderate prefers Moderate |
| 1.5.4 | `check_ic_heavy()` | Function | Heavy prefers Heavy |
| 1.5.5 | `validate_ic()` | Function | All segments self-select correctly |
| 1.5.6 | `identify_ic_violations()` | Function | Flag problematic pricing |

**Output file:** `src/constraints/incentive_compatibility.py`

---

## PHASE 2: REWARD-PENALTY MECHANISM

### Task 2.1: Implement Efficiency Score Reward ✏️ PATCHED v2

**Key change:** Reward BEHAVIOR (efficiency), not OUTCOME (low usage).

**Why this matters:**
- Old model: "You used less kWh → here's a reward" (punishes people who NEED AC)
- New model: "You used efficiently (24°C, timer) → here's a discount" (rewards smart behavior)

**Efficiency Score components:**

| Factor | Weight | What it measures |
|--------|--------|------------------|
| Temperature discipline | 60% | Set temp 24°C+ vs 16°C |
| Schedule discipline | 25% | Timer/scheduling usage |
| Anomaly avoidance | 15% | No door-open-while-running, etc. |

**Sub-tasks:**

| # | Task | Output | Validation |
|---|------|--------|------------|
| 2.1.1 | Define efficiency score algorithm | Function | 0-100 score |
| 2.1.2 | Define temperature scoring | Function | 24°C+ = 100, 16°C = 0 |
| 2.1.3 | Define schedule scoring | Function | Timer usage % |
| 2.1.4 | Define anomaly penalties | Function | -3 per event |
| 2.1.5 | Define discount tiers | Config | 90+ = 20% off, 75+ = 12%, etc. |
| 2.1.6 | Implement positive framing | Messages | "You earned ₹X!" not "Penalty avoided" |

**Efficiency Score → Discount Tiers:**
```python
EFFICIENCY_TIERS = {
    'champion': {'threshold': 90, 'discount': 0.20, 'badge': '🏆'},
    'star':     {'threshold': 75, 'discount': 0.12, 'badge': '⭐'},
    'aware':    {'threshold': 60, 'discount': 0.05, 'badge': '🌱'},
    'improve':  {'threshold': 0,  'discount': 0.00, 'badge': '📈'}
}

# Message framing (CRITICAL):
# ❌ "Penalty for inefficiency: ₹100"
# ✅ "Your Efficiency Score: 82! You earned ₹78 off! 🎉"
```

**Output file:** `src/incentives/efficiency_score.py`

---

### Task 2.2: Implement Overage Structure ✏️ PATCHED v2

**Key change:** Overage for exceeding HOURS (like mobile data), NOT penalty for using electricity.

**Why this works:**
- "You exceeded your data plan" → understood and accepted
- "You used too much electricity" → feels like punishment for living

**Sub-tasks:**

| # | Task | Output | Validation |
|---|------|--------|------------|
| 2.2.1 | Define overage rates by plan | Config | Light: ₹5/hr, Mod: ₹4/hr, Heavy: ₹3/hr |
| 2.2.2 | Implement `calculate_overage()` | Function | Correct calculation |
| 2.2.3 | Implement overage cap | Function | Prevents bill shock |
| 2.2.4 | Implement plan upgrade recommendation | Logic | If consistent overage → suggest upgrade |
| 2.2.5 | Test with example scenarios | Tests | Edge cases pass |

**Overage formula:**
```python
def calculate_overage(plan, actual_hours):
    hours_included = PLANS[plan]['hours_included']
    
    if actual_hours <= hours_included:
        return {'overage': 0, 'message': 'Within your plan! 👍'}
    
    excess_hours = actual_hours - hours_included
    rate = PLANS[plan]['overage_per_hour']
    max_overage = PLANS[plan]['max_overage']
    
    overage = min(excess_hours * rate, max_overage)
    
    return {
        'excess_hours': excess_hours,
        'overage': overage,
        'message': f'You used {actual_hours} hours (plan: {hours_included}). Extra: ₹{overage}'
    }
```

**Upgrade recommendation logic:**
```python
def should_recommend_upgrade(plan, last_3_months_hours):
    avg_hours = sum(last_3_months_hours) / 3
    hours_included = PLANS[plan]['hours_included']
    
    if avg_hours > hours_included * 1.2:  # Consistently 20%+ over
        next_plan = get_next_plan(plan)
        savings = calculate_savings_if_upgrade(plan, next_plan, avg_hours)
        if savings > 0:
            return True, f"Upgrade to {next_plan} to save ₹{savings}/month"
    
    return False, None
```

**Output file:** `src/incentives/overage.py`

---

### Task 2.3: Implement Anti-Gaming Verification

**Sub-tasks:**

| # | Task | Output | Validation |
|---|------|--------|------------|
| 2.3.1 | Model gaming scenario: Heavy→Light | Analysis | Utility comparison |
| 2.3.2 | Model gaming scenario: Light→Heavy | Analysis | Utility comparison |
| 2.3.3 | Model gaming scenario: Baseline stuffing | Analysis | Cap prevents gaming |
| 2.3.4 | Document anti-gaming proof | Markdown | Written justification |

**Output file:** `src/constraints/anti_gaming.py` + `docs/anti_gaming_analysis.md`

---

### Task 2.4: Implement Baseline Setting ✏️ PATCHED

**CRITICAL CHANGE:** Add hard cap and use median, not mean.

**Sub-tasks:**

| # | Task | Output | Validation |
|---|------|--------|------------|
| 2.4.1 | Define default baselines by segment | Config | From appliances.json |
| 2.4.2 | Implement `calculate_personalized_baseline()` | Function | With hard cap |
| 2.4.3 | Implement weather normalization (CDD) | Function | Optional adjustment |
| 2.4.4 | Implement anomaly flagging | Function | Flag if > 150% default |
| 2.4.5 | Test baseline with gaming attempts | Tests | Gaming prevented |

**Anti-gaming baseline (PATCHED):**
```python
def calculate_personalized_baseline(usage_m2, usage_m3, segment, appliance):
    """
    ANTI-GAMING baseline calculation.
    """
    SEGMENT_DEFAULTS = {
        'AC': {'light': 42, 'moderate': 92, 'heavy': 150},  # Monthly kWh
        'FRIDGE': {'light': 18, 'moderate': 25, 'heavy': 33}
    }
    
    segment_default = SEGMENT_DEFAULTS[appliance][segment]
    
    # Use MEDIAN of M2-M3 (resistant to gaming)
    raw_baseline = statistics.median([usage_m2, usage_m3])
    
    # HARD CAP: Cannot exceed default by more than 20%
    max_allowed = segment_default * 1.20
    baseline = min(raw_baseline, max_allowed)
    
    # Flag anomalies
    anomaly = raw_baseline > segment_default * 1.50
    
    return {
        'baseline': baseline,
        'was_capped': raw_baseline > max_allowed,
        'anomaly_flag': anomaly
    }
```

**Output file:** `src/incentives/baseline.py`

---

### Task 2.5: Document Moral Hazard Risks

**Moral hazard matrix:**

| Risk | Likelihood | Impact | Detection | Mitigation |
|------|------------|--------|-----------|------------|
| Overuse (24/7 AC) | High | High | Usage monitoring | Progressive penalties |
| Misuse (commercial) | Low | High | Pattern detection | Terms + penalties |
| Free-riding (service) | Medium | Medium | Visit frequency | Co-pay after 2/year |
| Tampering (sensor) | Low | High | Heartbeat monitoring | Alert + penalties |
| Baseline stuffing | Medium | Medium | Hard cap | 120% cap on baseline |

**Sub-tasks:**

| # | Task | Output |
|---|------|--------|
| 2.5.1 | Create complete risk matrix | Table |
| 2.5.2 | Score likelihood × impact | Risk ranking |
| 2.5.3 | Map detection mechanisms | Detection table |
| 2.5.4 | Prioritize for mitigation | Action list |

**Output file:** `docs/moral_hazard_analysis.md`

---

### Task 2.6: Design Moral Hazard Mitigations

**Sub-tasks:**

| # | Task | Output |
|---|------|--------|
| 2.6.1 | Design mitigation for each risk | Mitigation table |
| 2.6.2 | Estimate mitigation cost | Cost table |
| 2.6.3 | Document IC alignment | How mitigations support IC |
| 2.6.4 | Implement key checks in code | `moral_hazard_checks()` |

**Output file:** `src/risk/moral_hazard.py` + `docs/moral_hazard_mitigation.md`

---

## PHASE 3: PROFITABILITY ANALYSIS

### Task 3.1: Model Traditional Sales (Before SESP)

**Sub-tasks:**

| # | Task | Output |
|---|------|--------|
| 3.1.1 | Define traditional revenue model | Revenue function |
| 3.1.2 | Define traditional cost model | Cost function |
| 3.1.3 | Calculate per-unit margin | Margin table |
| 3.1.4 | Calculate traditional CLV | CLV figure |

**Traditional model parameters:**
```python
TRADITIONAL = {
    'mrp': 45000,
    'dealer_margin': 0.18,
    'manufacturer_revenue': 36900,
    'manufacturing_cost': 30000,
    'gross_margin': 6900,
    'warranty_claims': 0.12 * 3500,  # 12% rate × ₹3500 avg
    'amc_attach_rate': 0.25,
    'amc_margin': 1300,  # Per customer who takes AMC
    'net_margin_per_unit': 6900 - 420 + (0.25 * 1300)
}
```

**Output file:** `src/profitability/traditional.py`

---

### Task 3.2: Model SESP (After)

**Sub-tasks:**

| # | Task | Output |
|---|------|--------|
| 3.2.1 | Define SESP revenue model | Revenue function |
| 3.2.2 | Define SESP cost model | Cost function |
| 3.2.3 | Calculate per-unit margin | Margin table |
| 3.2.4 | Calculate SESP CLV | CLV figure |
| 3.2.5 | Model churn/default impact | Risk-adjusted CLV |

**Output file:** `src/profitability/sesp.py`

---

### Task 3.3: Create Before vs After Comparison

**Comparison table structure:**
```
┌───────────────────────┬─────────────┬──────────┬─────────┐
│ Metric                │ Traditional │ SESP     │ Delta   │
├───────────────────────┼─────────────┼──────────┼─────────┤
│ Revenue per unit      │ ₹36,900     │ ₹44,500  │ +₹7,600 │
│ Cost per unit         │ ₹30,420     │ ₹37,100  │ +₹6,680 │
│ Gross margin          │ ₹6,480      │ ₹7,400   │ +₹920   │
│ Margin %              │ 17.6%       │ 16.6%    │ -1.0%   │
│ CLV (5 year)          │ ₹7,800      │ ₹12,400  │ +₹4,600 │
│ Warranty savings      │ —           │ ₹600     │ +₹600   │
│ Customer relationship │ Low         │ High     │ —       │
│ Data asset            │ None        │ Yes      │ —       │
└───────────────────────┴─────────────┴──────────┴─────────┘
```

**Sub-tasks:**

| # | Task | Output |
|---|------|--------|
| 3.3.1 | Build comparison table | Table |
| 3.3.2 | Calculate warranty cost reduction | ₹ value |
| 3.3.3 | Calculate CLV improvement | ₹ value |
| 3.3.4 | Create waterfall chart | Visualization |
| 3.3.5 | Sensitivity analysis | What drives difference |

**Output file:** `src/profitability/comparison.py` + `docs/profitability_report.md`

---

## PHASE 4: SIMULATION ✏️ PATCHED (VECTORIZED)

### Task 4.1: Generate Synthetic Customer Data

**Sub-tasks:**

| # | Task | Output |
|---|------|--------|
| 4.1.1 | Define generation parameters | Config |
| 4.1.2 | Generate 1000 customer records | DataFrame |
| 4.1.3 | Assign usage behaviors | Column |
| 4.1.4 | Assign risk factors | Columns |
| 4.1.5 | Validate distributions | Distribution plots |

**Output file:** `src/simulation/data_generator.py` + `data/customers.csv`

---

### Task 4.2: Simulate Customer Journeys ✏️ PATCHED

**CRITICAL:** Use vectorized operations, not nested loops.

**Sub-tasks:**

| # | Task | Output |
|---|------|--------|
| 4.2.1 | Create month-customer grid (vectorized) | DataFrame |
| 4.2.2 | Apply seasonality (vectorized) | Column |
| 4.2.3 | Generate usage with noise (vectorized) | Column |
| 4.2.4 | Calculate rewards/penalties (vectorized) | Columns |
| 4.2.5 | Handle churn events (vectorized) | Column |
| 4.2.6 | Calculate bills and margins (vectorized) | Columns |

**Vectorized approach:**
```python
def simulate_portfolio(customers_df, params, tenure_months=24):
    """VECTORIZED simulation - no nested loops."""
    
    n = len(customers_df)
    
    # Expand to customer × month grid
    grid = pd.DataFrame({
        'customer_id': np.repeat(customers_df['id'].values, tenure_months),
        'month': np.tile(range(tenure_months), n),
        'segment': np.repeat(customers_df['segment'].values, tenure_months),
        'usage_factor': np.repeat(customers_df['usage_factor'].values, tenure_months)
    })
    
    # Vectorized seasonality lookup
    grid['seasonality'] = grid['month'].map(lambda m: SEASONALITY[m % 12])
    
    # Vectorized baseline
    grid['baseline'] = grid['segment'].map(SEGMENT_BASELINES)
    
    # Vectorized actual usage
    noise = np.random.normal(1, 0.1, len(grid))
    grid['actual_usage'] = grid['baseline'] * grid['seasonality'] * grid['usage_factor'] * noise
    
    # Vectorized reward/penalty
    grid['deviation'] = (grid['actual_usage'] - grid['baseline']) / grid['baseline']
    grid['reward_penalty'] = grid.apply(calc_rp_row, axis=1)
    
    # Vectorized financials
    grid['customer_bill'] = (params['fee'] + grid['reward_penalty']) * 1.18
    grid['company_revenue'] = (params['fee'] + grid['reward_penalty']) / 1.18
    
    return grid
```

**Output file:** `src/simulation/simulator.py` + `data/simulation_results.csv`

---

### Task 4.3: Aggregate Results

**Sub-tasks:**

| # | Task | Output |
|---|------|--------|
| 4.3.1 | Aggregate by customer | Customer summary |
| 4.3.2 | Aggregate by segment | Segment metrics |
| 4.3.3 | Aggregate by month | Time series |
| 4.3.4 | Aggregate portfolio total | Summary metrics |

**Output file:** `src/simulation/aggregator.py`

---

### Task 4.4: Generate Visualizations

**Required charts:**

| # | Chart | Type |
|---|-------|------|
| 4.4.1 | Usage distribution by segment | Histogram |
| 4.4.2 | Reward vs penalty distribution | Histogram |
| 4.4.3 | Customer tenure distribution | Histogram |
| 4.4.4 | Monthly cash flow timeline | Line |
| 4.4.5 | Cumulative profit curve | Line |
| 4.4.6 | Segment comparison | Grouped bar |
| 4.4.7 | Seasonality impact | Line |
| 4.4.8 | Before vs after waterfall | Waterfall |

**Output file:** `src/visualization/charts.py` + `outputs/charts/`

---

## PHASE 5: INDIA-SPECIFIC RECOMMENDATIONS

### Task 5.1: Regional Strategy

| Region | Strategy |
|--------|----------|
| Metro | Standard pricing, premium features available |
| Tier-2 | Moderate subsidy increase, basic features |
| Tier-3 | Higher subsidy, longer tenure, voltage protection |

**Output file:** `docs/regional_strategy.md`

---

### Task 5.2: Address Ownership Preference

**Features to counter subscription resistance:**
- Rent-to-own option (buyout after 36m)
- "Your AC, our service" messaging
- Clear transferability rules
- Reasonable exit terms

**Output file:** `docs/ownership_strategy.md`

---

### Task 5.3: Launch Recommendations

**Recommendation summary:**
- Start: Delhi NCR, Moderate segment, AC product
- Pricing: ₹32,000 upfront + ₹549/month
- Tenure: 24 months default
- Channel: Brand stores + select dealers
- Pilot: 3 months, 500 customers
- Scale: Based on pilot learnings

**Output file:** `docs/launch_recommendations.md`

---

## PHASE 6: FINAL ASSEMBLY

### Task 6.1: Compile Report

**Structure:**
1. Executive Summary (1 page)
2. Introduction (2 pages)
3. Pricing Mechanism (4 pages)
4. Reward-Penalty Structure (3 pages)
5. Constraint Satisfaction (3 pages)
6. Moral Hazard Analysis (2 pages)
7. Profitability Analysis (4 pages)
8. Simulation Results (4 pages)
9. India Recommendations (3 pages)
10. Conclusion (1 page)
11. Appendix

**Output file:** `outputs/SESP_Final_Report.md`

---

### Task 6.2: Package Code

**Structure:**
```
SESP_Code/
├── README.md
├── requirements.txt
├── config/
├── src/
│   ├── pricing/
│   ├── adjustments/
│   ├── alternatives/
│   ├── constraints/
│   ├── incentives/
│   ├── profitability/
│   ├── simulation/
│   ├── risk/
│   └── visualization/
├── data/
├── outputs/
├── tests/
└── main.py
```

**Output:** `SESP_Code/` folder

---

## VALIDATION CHECKLIST

Run these checks at each phase completion:

### After Phase 1:
- [ ] Plans are bucket-based (hours included, not kWh rates)
- [ ] Monthly fee is ₹499-899 range (reasonable for Indian market)
- [ ] NO kWh × rate components (no double-charging for electricity)
- [ ] Overage is per hour exceeded, capped to prevent bill shock
- [ ] GST applied to ALL service costs (both SESP and alternatives)
- [ ] Participation constraint passes for target segment
- [ ] Self-selection mechanism creates energy savings incentive

### After Phase 2:
- [ ] Efficiency Score measures BEHAVIOR (temp, timer), not just low usage
- [ ] Reward is framed as DISCOUNT (gain), not penalty avoidance (pain)
- [ ] Overage is framed as "exceeded plan" (like mobile data)
- [ ] Baseline anti-gaming protections in place (cap, median, flag)
- [ ] Moral hazard risks documented
- [ ] Message framing is positive ("You earned ₹X!")

### After Phase 3:
- [ ] Traditional margin is 15-20%
- [ ] SESP margin is 15-25%
- [ ] CLV improvement is positive
- [ ] Comparison table complete

### After Phase 4:
- [ ] Simulation uses vectorized code (not nested loops)
- [ ] Simulation tracks HOURS (not kWh) for overage
- [ ] Efficiency score calculated for each customer-month
- [ ] Results pass sanity checks
- [ ] All charts generated
- [ ] Aggregations complete

### After Phase 5:
- [ ] Regional strategies documented
- [ ] Ownership concerns addressed
- [ ] Launch plan actionable

### After Phase 6:
- [ ] Report covers all deliverables
- [ ] Code is organized and documented
- [ ] All files in correct locations

---

## MODEL SUMMARY (Final)

| Component | Old (Wrong) | New (Correct) |
|-----------|-------------|---------------|
| **Pricing** | Base + kWh rate | Bucket (hours included) |
| **Metric** | kWh consumed | Runtime hours |
| **Reward** | Low usage | Efficiency Score (behavior) |
| **Penalty** | High usage | Overage (exceeded plan) |
| **Framing** | Penalty/fee | Discount/earned |
| **Psychology** | Pain avoidance | Gain seeking |
| **Energy saving** | Punish usage | Self-selection + behavior reward |

---

## ESTIMATED TIME

| Phase | Tasks | Hours |
|-------|-------|-------|
| Phase 1 | 1.1-1.5 | 10-12 |
| Phase 2 | 2.1-2.6 | 8-10 |
| Phase 3 | 3.1-3.3 | 6-8 |
| Phase 4 | 4.1-4.4 | 10-12 |
| Phase 5 | 5.1-5.3 | 4-6 |
| Phase 6 | 6.1-6.2 | 6-8 |
| **Total** | | **44-56 hours** |

---

## WHEN STUCK

1. Re-read `CRITICAL_INSIGHTS.md`
2. Check if error matches known issues
3. Run sanity checks
4. Update `CRITICAL_INSIGHTS.md` with new learnings
