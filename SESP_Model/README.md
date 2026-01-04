# SESP Model: Smart Energy-Saver Subscription Program

> **BDM Project Submission — Anirudh Mohan**
>
> This repository contains the complete code and analysis for the SESP (Smart Energy-Saver Subscription Program) pricing model. The simulation generates **hypothetical usage data** for 1,000 customers over 60 months (60,000 data points) to demonstrate the economic viability of a subscription-based appliance model.
>
> **Quick Start:**
> ```bash
> cd SESP_Model
> pip install -r requirements.txt
> python main.py
> ```
>
> **Key Outputs:**
> - `data/` — Simulation results (CSV files with customer billing data)
> - `outputs/charts/` — 8 visualizations (usage, billing, cash flow, etc.)
> - `outputs/SESP_Final_Report.md` — Full technical analysis

---

A dynamic pricing simulation and optimization model for IoT-enabled home appliances in India.

## Overview

This project implements a comprehensive subscription-based pricing model for smart appliances (AC and Refrigerator) that:

- **For Customers**: Provides Rs18,986 savings vs outright purchase over 5 years
- **For Company**: Generates Rs6,454 margin per customer (18.5%)
- **For Environment**: Creates behavioral nudges for energy efficiency

## Key Features

| Feature | Description |
|---------|-------------|
| **Bucket Pricing** | Mobile data-style hours allocation (Lite/Standard/Premium) |
| **Seasonal Hours** | Dynamic allocation matching usage patterns (58% summer overage reduction) |
| **Efficiency Score** | Behavior-based rewards (temperature, timer, anomalies) |
| **Constraint Validation** | Participation, Incentive Compatibility, Cash Flow checks |
| **Monte Carlo Simulation** | 1,000 customers × 60 months = 60,000 data points |

## Project Structure

```
SESP_Model/
├── src/
│   ├── pricing/           # Bucket model, plan structures
│   ├── adjustments/       # India-specific, efficiency score
│   ├── alternatives/      # Purchase, EMI, rental calculators
│   ├── constraints/       # PC, IC, cash flow, anti-gaming
│   ├── profitability/     # Traditional, SESP, comparison
│   ├── simulation/        # Data generator, simulator, aggregator
│   ├── optimization/      # Pricing optimizer
│   ├── visualization/     # Charts generation
│   └── mcdm/              # Multi-criteria decision making
├── tests/                 # 388 tests
├── docs/                  # Strategy documents
├── outputs/
│   ├── charts/            # 8 visualization charts
│   └── SESP_Final_Report.md
├── config/                # JSON configuration files
├── main.py                # Demo script
└── REALISATIONS.md        # Key insights and learnings
```

## Installation

```bash
# Clone or download the project
cd SESP_Model

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Run demo
python main.py
```

## Requirements

- Python 3.8+
- pandas
- numpy
- matplotlib
- pytest (for testing)

## Quick Start

```python
from src.simulation import simulate_portfolio, generate_customers
from src.visualization import generate_all_charts

# Generate 1000 synthetic customers
customers = generate_customers(n=1000, random_seed=42)

# Run 60-month simulation
results = simulate_portfolio(customers, tenure_months=60)

# Generate visualizations
generate_all_charts(results)
```

## Key Results

### Pricing Plans (Optimized)

| Plan | Monthly Fee | Seasonal Hours (W/Sh/Su) | Overage |
|------|-------------|--------------------------|---------|
| Lite | Rs449 | 35/90/140 | Rs6/hr (cap Rs150) |
| Standard | Rs599 | 70/180/280 | Rs5/hr (cap Rs200) |
| Premium | Rs799 | 120/320/480 | Unlimited |

### Financial Summary

| Metric | Value |
|--------|-------|
| Customer savings vs purchase | Rs18,986 (5 years) |
| Company margin per customer | Rs6,454 (18.5%) |
| Break-even month | 23 |
| Summer overage reduction | 58% (with seasonal hours) |

### Constraint Status

| Constraint | Status |
|------------|--------|
| Participation (PC) | ✓ Satisfied (19.4% savings) |
| Incentive Compatibility (IC) | ✓ Satisfied |
| Cash Flow | ✓ Satisfied (break-even month 23) |
| Profitability | ✓ Satisfied (18.5% margin) |

## Documentation

- **Final Report**: `outputs/SESP_Final_Report.md` (~27 pages)
- **Key Insights**: `REALISATIONS.md` (976 lines of learnings)
- **Regional Strategy**: `docs/regional_strategy.md`
- **Launch Plan**: `docs/launch_recommendations.md`
- **Ownership Strategy**: `docs/ownership_strategy.md`

## Tests

```bash
# Run all 388 tests
python -m pytest tests/ -v

# Run specific module tests
python -m pytest tests/test_simulation.py -v
python -m pytest tests/test_profitability.py -v
```

## Key Innovations

### 1. Seasonal Hours Allocation

Instead of fixed monthly hours, allocation varies by season:
- **Winter** (Jan, Feb, Nov, Dec): 70 hrs for Standard
- **Shoulder** (Mar, Apr, Sep, Oct): 180 hrs
- **Summer** (May-Aug): 280 hrs

This creates a "budget effect" that naturally nudges users toward efficiency.

### 2. Efficiency Score (Behavior-Based)

Rewards HOW users consume, not HOW MUCH:
- Temperature discipline (60%): Set temp ≥24°C = max score
- Schedule discipline (25%): Timer usage percentage
- Anomaly avoidance (15%): No door-open-while-running, etc.

### 3. Credit Card Partnership

Three-sided value creation:
- Customer: Free card + Rs1,420/year benefits
- Company: Rs2,000 CAC subsidy + guaranteed payment
- Bank: Premium customer + 60 months transactions

## Evolution: Spec → Optimized

| Parameter | Initial Spec | Optimized | Why |
|-----------|--------------|-----------|-----|
| Subsidy | 65% | 50% | 65% was -62% margin |
| Tenure | 24 months | 60 months | Needed for break-even |
| Hours | Fixed 200/mo | Seasonal 70-280 | Budget effect |
| Margin | -Rs16,785 | +Rs6,454 | Viable! |

## License

This project was developed for academic/business analysis purposes.

## Contact

For questions about the SESP model, refer to the documentation in `docs/` or the comprehensive `REALISATIONS.md` file.
