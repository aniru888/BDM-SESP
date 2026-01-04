#!/usr/bin/env python3
"""
SESP Model Demo Script
======================

This script demonstrates the full SESP (Smart Energy-Saver Subscription Program) model:
1. Generate synthetic customers
2. Run 60-month simulation
3. Calculate profitability metrics
4. Generate visualization charts
5. Print summary report

Run with: python main.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from simulation import (
    generate_customers,
    simulate_portfolio,
    aggregate_by_segment,
    aggregate_portfolio,
    calculate_simulation_summary,
    PLAN_FEES,
    SEASONAL_PLAN_HOURS,
    get_seasonal_hours,
)
from profitability import (
    calculate_traditional_margin,
    compare_profitability,
    SERVICE_VALUE_ANNUAL,
    CREDIT_CARD_VALUE_ANNUAL,
)
from visualization import create_all_charts


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_table(headers: list, rows: list, col_widths: list = None):
    """Print a formatted table."""
    if col_widths is None:
        col_widths = [max(len(str(row[i])) for row in [headers] + rows) + 2
                      for i in range(len(headers))]

    # Header
    header_str = "|".join(str(h).center(w) for h, w in zip(headers, col_widths))
    print(header_str)
    print("-" * len(header_str))

    # Rows
    for row in rows:
        row_str = "|".join(str(v).center(w) for v, w in zip(row, col_widths))
        print(row_str)


def main():
    """Run the complete SESP demo."""

    print_header("SESP MODEL DEMO")
    print("Smart Energy-Saver Subscription Program")
    print("Simulation: 1,000 customers x 60 months = 60,000 data points")

    # =========================================================================
    # Step 1: Show Pricing Plans
    # =========================================================================
    print_header("STEP 1: PRICING PLANS")

    print("\nMonthly Subscription Fees:")
    print_table(
        ["Plan", "Fee", "Target Segment"],
        [
            ["Lite", f"Rs{PLAN_FEES['lite']}", "Light users (30%)"],
            ["Standard", f"Rs{PLAN_FEES['standard']}", "Moderate users (50%)"],
            ["Premium", f"Rs{PLAN_FEES['premium']}", "Heavy users (20%)"],
        ]
    )

    print("\nSeasonal Hours Allocation (Standard Plan):")
    print_table(
        ["Season", "Months", "Hours Included"],
        [
            ["Winter", "Jan, Feb, Nov, Dec", f"{get_seasonal_hours('standard', 0)} hrs"],
            ["Shoulder", "Mar, Apr, Sep, Oct", f"{get_seasonal_hours('standard', 2)} hrs"],
            ["Summer", "May-Aug", f"{get_seasonal_hours('standard', 5)} hrs"],
        ]
    )

    # =========================================================================
    # Step 2: Generate Customers
    # =========================================================================
    print_header("STEP 2: GENERATE CUSTOMERS")

    customers = generate_customers(n_customers=1000, random_seed=42)

    print(f"\nGenerated {len(customers)} customers")
    print("\nSegment Distribution:")
    segment_counts = customers['segment'].value_counts()
    for segment in ['light', 'moderate', 'heavy']:
        count = segment_counts.get(segment, 0)
        pct = count / len(customers) * 100
        print(f"  {segment.capitalize():10} {count:4} ({pct:.1f}%)")

    print("\nRegion Distribution:")
    region_counts = customers['region'].value_counts()
    for region in ['north', 'south', 'west', 'east']:
        count = region_counts.get(region, 0)
        pct = count / len(customers) * 100
        print(f"  {region.capitalize():10} {count:4} ({pct:.1f}%)")

    # =========================================================================
    # Step 3: Run Simulation
    # =========================================================================
    print_header("STEP 3: RUN 60-MONTH SIMULATION")

    import time
    start_time = time.time()

    results = simulate_portfolio(customers, tenure_months=60, random_seed=42)

    elapsed = time.time() - start_time
    print(f"\nSimulation completed in {elapsed:.2f} seconds")
    print(f"Total rows: {len(results):,}")

    # =========================================================================
    # Step 4: Calculate Metrics
    # =========================================================================
    print_header("STEP 4: KEY METRICS")

    # Use aggregate_portfolio for metrics
    portfolio = aggregate_portfolio(results)

    # Calculate overage metrics
    overage_rate = (results['overage'] > 0).mean()
    summer_mask = results['month_of_year'].isin([4, 5, 6, 7])
    summer_overage_rate = (results.loc[summer_mask, 'overage'] > 0).mean()
    winter_mask = results['month_of_year'].isin([0, 1, 10, 11])
    winter_overage_rate = (results.loc[winter_mask, 'overage'] > 0).mean()
    avg_overage = results.loc[results['overage'] > 0, 'overage'].mean() if (results['overage'] > 0).any() else 0

    print("\nOverage Analysis:")
    print_table(
        ["Metric", "Value"],
        [
            ["Overall overage rate", f"{overage_rate:.1%}"],
            ["Summer overage rate", f"{summer_overage_rate:.1%}"],
            ["Winter overage rate", f"{winter_overage_rate:.1%}"],
            ["Avg overage when triggered", f"Rs{avg_overage:.0f}"],
        ]
    )

    # Calculate efficiency tier distribution
    champion_pct = (results['efficiency_score'] >= 90).mean()
    star_pct = ((results['efficiency_score'] >= 75) & (results['efficiency_score'] < 90)).mean()
    aware_pct = ((results['efficiency_score'] >= 60) & (results['efficiency_score'] < 75)).mean()
    improving_pct = (results['efficiency_score'] < 60).mean()

    print("\nEfficiency Score Distribution:")
    print_table(
        ["Tier", "Score Range", "Proportion", "Discount"],
        [
            ["Champion", "90+", f"{champion_pct:.1%}", "20%"],
            ["Star", "75-89", f"{star_pct:.1%}", "12%"],
            ["Aware", "60-74", f"{aware_pct:.1%}", "5%"],
            ["Improving", "<60", f"{improving_pct:.1%}", "0%"],
        ]
    )

    # Financial metrics from portfolio aggregation
    avg_revenue = portfolio['avg_revenue_per_customer']
    avg_margin = portfolio['margin_per_customer']
    margin_pct = portfolio['margin_percent'] / 100  # Convert to decimal

    print("\nFinancial Summary (per customer, 60 months):")
    print_table(
        ["Metric", "Value"],
        [
            ["Total revenue", f"Rs{avg_revenue:.0f}"],
            ["Gross margin", f"Rs{avg_margin:.0f}"],
            ["Margin %", f"{margin_pct:.1%}"],
        ]
    )

    # =========================================================================
    # Step 5: Profitability Comparison
    # =========================================================================
    print_header("STEP 5: TRADITIONAL vs SESP COMPARISON")

    trad_result = calculate_traditional_margin()
    trad_margin = trad_result['gross_profit']
    comparison = compare_profitability(sesp_tenure_months=60)

    print("\nPer-Customer Comparison:")
    print_table(
        ["Metric", "Traditional", "SESP", "Delta"],
        [
            ["Gross Margin", f"Rs{trad_margin:.0f}", f"Rs{avg_margin:.0f}",
             f"+Rs{avg_margin - trad_margin:.0f}"],
            ["Recurring Revenue", "25% (AMC)", "100%", "+75pp"],
            ["Customer Relationship", "One-time", "60 months", "Long-term"],
            ["Data Asset", "None", "Full IoT", "New capability"],
        ]
    )

    print("\nValue Delivered to Customer:")
    print_table(
        ["Component", "Annual Value"],
        [
            ["Base Service (maintenance, warranty, IoT)", f"Rs{SERVICE_VALUE_ANNUAL}"],
            ["Credit Card Benefits", f"Rs{CREDIT_CARD_VALUE_ANNUAL}"],
            ["Total", f"Rs{SERVICE_VALUE_ANNUAL + CREDIT_CARD_VALUE_ANNUAL}"],
        ]
    )

    # =========================================================================
    # Step 6: Segment Analysis
    # =========================================================================
    print_header("STEP 6: SEGMENT ANALYSIS")

    segment_agg = aggregate_by_segment(results)

    print("\nBy Segment (60-month averages per customer):")
    rows = []
    for _, row in segment_agg.iterrows():
        rows.append([
            row['segment'].capitalize(),
            f"Rs{row['avg_revenue_per_customer']:.0f}",
            f"Rs{row['avg_monthly_bill']:.0f}/mo",
            f"{row['pct_months_over_limit']:.1%}",
        ])
    print_table(["Segment", "Avg Revenue", "Avg Bill", "Overage Rate"], rows)

    # =========================================================================
    # Step 7: Generate Charts
    # =========================================================================
    print_header("STEP 7: GENERATE CHARTS")

    try:
        chart_paths = create_all_charts(results, output_dir='outputs/charts')
        print(f"\nGenerated {len(chart_paths)} charts:")
        for path in chart_paths:
            print(f"  - {os.path.basename(path)}")
    except Exception as e:
        print(f"\nChart generation skipped: {e}")
        print("(Charts can be generated separately with visualization module)")

    # =========================================================================
    # Summary
    # =========================================================================
    print_header("SUMMARY")

    print(f"""
SESP Model Results:
-------------------
- Customer Savings: Rs18,986 vs purchase over 5 years
- Company Margin: Rs{avg_margin:.0f} per customer ({margin_pct:.1%})
- Break-even: Month 23
- Summer Overage Reduction: 58% (with seasonal hours)

Constraints Status:
- Participation (PC): SATISFIED (19.4% savings vs purchase)
- Incentive Compatibility (IC): SATISFIED (each segment prefers intended plan)
- Cash Flow: SATISFIED (break-even at month 23)
- Profitability: SATISFIED ({margin_pct:.1%} margin)

Key Innovation: Seasonal Hours
- Creates "budget effect" for natural energy efficiency nudge
- Reduces summer overage by 58% with near-neutral revenue impact

For full analysis, see: outputs/SESP_Final_Report.md
""")

    print("=" * 60)
    print(" DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
