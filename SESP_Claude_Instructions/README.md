# SESP Pricing Model - Context for Claude Code

## Overview

This folder contains all context, parameters, and instructions needed to build a **dynamic pricing simulation and optimization dashboard** for the Smart Energy-Saver Subscription Program (SESP).

## ⚠️ CRITICAL: Read Order

**YOU MUST READ FILES IN THIS ORDER:**

1. **`CRITICAL_INSIGHTS.md`** — Errors to avoid and why (READ FIRST)
2. **`PATCHES.md`** — Code fixes that override original instructions
3. **`config/pricing_formula_PATCHED.json`** — Corrected pricing parameters
4. **`claude.md`** — Original detailed instructions (apply patches on top)
5. **Config files** — Parameters and data

## Business Model Summary

1. Customer pays **subsidized upfront cost** for new smart appliance (e.g., ₹32,000 instead of ₹45,000 MRP)
2. Customer pays **monthly subscription fee** (e.g., ₹550/month) for **SERVICES**
3. **Services include:** maintenance, extended warranty, IoT monitoring, priority support
4. **Customer pays electricity SEPARATELY to utility** — subscription is NOT an electricity charge
5. **Goal**: Subscription value > subscription cost from customer perspective; company recovers deficit + profit over tenure

## Critical Corrections Applied

| # | Issue | Correction |
|---|-------|------------|
| 1 | **Double-charging for electricity** | Subscription is for SERVICES, not energy. Tier premium based on wear/service intensity. |
| 2 | **Recovery factor math error** | Use deficit recovery + service cost model, not arbitrary factors. |
| 3 | **Baseline gaming loophole** | Hard cap at 120% of segment default, median not mean, weather normalization. |
| 4 | **GST inconsistency** | Apply 18% GST to ALL services in ALL scenarios. |
| 5 | **Simulation performance** | Use vectorized Pandas, not nested for-loops. |

## File Structure

```
SESP_Claude_Instructions/
├── CRITICAL_INSIGHTS.md           # ⚠️ READ FIRST - Errors to avoid
├── PATCHES.md                     # Code corrections to apply
├── README.md                      # This file
├── claude.md                      # Original detailed instructions
└── config/
    ├── pricing_formula_PATCHED.json  # ✅ CORRECTED pricing logic
    ├── appliances.json               # AC and Fridge specifications
    ├── market_params.json            # Electricity rates, competitors, risks
    ├── customer_segments.json        # Usage segments, discount rates
    └── decision_variables.json       # What to optimize, constraints, scenarios
```

## How to Use

1. **Read `CRITICAL_INSIGHTS.md`** — Understand the errors we're avoiding
2. **Read `PATCHES.md`** — Exact code changes to apply
3. **Load `pricing_formula_PATCHED.json`** — Use this instead of old pricing logic
4. **Reference `claude.md`** for detailed task breakdown — but apply patches
5. **Build modules in order** — Test each before proceeding
6. **Run sanity checks** — Validate numbers make sense

## Key Constraints (All Must Be Satisfied)

| Constraint | Condition |
|------------|-----------|
| Participation | SESP NPV < Purchase NPV × 0.90 (10% better) |
| Profitability | Firm margin >= 15% |
| Cash Flow | Max negative <= ₹10,000/unit |
| Incentive Compatibility | Each segment prefers their intended plan |
| Moral Hazard | Penalty deters overuse |

## Reference Appliances

- **AC**: 1.5T 5-Star Inverter Split AC (MRP ₹45,000)
- **Fridge**: 280L Frost-Free Double Door (MRP ₹30,000)

## Customer Segments

| Segment | Proportion | AC kWh/year | Price Sensitivity |
|---------|------------|-------------|-------------------|
| Light | 30% | 500 | High |
| Moderate | 50% | 1,100 | Medium |
| Heavy | 20% | 1,800 | Low |

## Expected Outputs

1. **Optimal pricing parameters** (subsidy, fee, tenure, deposit, reward/penalty rates)
2. **Sensitivity analysis** (which parameters matter most)
3. **Cash flow projection** (monthly, with seasonality)
4. **Constraint satisfaction status** (green/red indicators)
5. **Comparison charts** (SESP vs alternatives)
6. **Monte Carlo risk distribution** (profit probability)

## Questions?

If any parameter is unclear or seems wrong, **ask the user** before assuming. Better to clarify than build on wrong foundations.
