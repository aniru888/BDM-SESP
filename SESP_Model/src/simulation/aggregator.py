"""
Aggregator — Result Aggregation and Presentation
================================================

Aggregates simulation results for reporting and visualization.

Output Levels:
1. By Customer — Individual CLV, total paid, avg bill
2. By Segment — Segment-level metrics and profitability
3. By Month — Time series for cash flow and seasonality
4. Portfolio — Overall summary and validation

All outputs are designed to be PRESENTABLE in reports.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple

from .simulator import PLAN_FEES, PLAN_HOURS


# =============================================================================
# AGGREGATION FUNCTIONS
# =============================================================================

def aggregate_by_customer(grid: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate simulation results by customer.

    Returns one row per customer with:
    - Total revenue to company
    - Total paid by customer
    - Average monthly bill
    - Total hours used
    - Efficiency stats
    - Plan utilization

    Args:
        grid: Simulation grid from simulate_portfolio()

    Returns:
        DataFrame with one row per customer
    """
    agg = grid.groupby('customer_id').agg({
        'segment': 'first',
        'plan': 'first',
        'region': 'first',
        'has_credit_card': 'first',
        'is_plan_mismatch': 'first',

        # Revenue & billing
        'company_revenue': 'sum',
        'monthly_bill': ['sum', 'mean', 'std'],
        'gst_amount': 'sum',

        # Usage
        'actual_hours': ['sum', 'mean'],
        'hours_included': 'first',  # Same for all months
        'excess_hours': 'sum',
        'is_over_limit': 'mean',

        # Efficiency
        'efficiency_score': 'mean',
        'efficiency_discount': 'sum',
        'discount_pct': 'mean',

        # Overage
        'overage': 'sum',

        # Months
        'month': 'count',
    })

    # Flatten column names
    agg.columns = [
        'segment', 'plan', 'region', 'has_credit_card', 'is_plan_mismatch',
        'total_revenue', 'total_paid', 'avg_monthly_bill', 'bill_std',
        'total_gst', 'total_hours', 'avg_monthly_hours', 'hours_included',
        'total_excess_hours', 'pct_months_over', 'avg_efficiency_score',
        'total_discount', 'avg_discount_pct', 'total_overage', 'tenure_months',
    ]

    agg = agg.reset_index()

    # Calculate derived metrics
    agg['hours_utilization'] = agg['total_hours'] / (agg['hours_included'] * agg['tenure_months'])
    agg['revenue_per_month'] = agg['total_revenue'] / agg['tenure_months']

    return agg


def aggregate_by_segment(grid: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate simulation results by segment.

    Returns one row per segment with averages and totals.
    """
    by_customer = aggregate_by_customer(grid)

    agg = by_customer.groupby('segment').agg({
        'customer_id': 'count',
        'total_revenue': ['sum', 'mean'],
        'total_paid': 'mean',
        'avg_monthly_bill': 'mean',
        'avg_monthly_hours': 'mean',
        'avg_efficiency_score': 'mean',
        'pct_months_over': 'mean',
        'total_overage': 'mean',
        'total_discount': 'mean',
        'hours_utilization': 'mean',
    })

    # Flatten column names
    agg.columns = [
        'n_customers', 'total_segment_revenue', 'avg_revenue_per_customer',
        'avg_total_paid', 'avg_monthly_bill', 'avg_monthly_hours',
        'avg_efficiency_score', 'pct_months_over_limit', 'avg_overage_paid',
        'avg_discount_earned', 'avg_hours_utilization',
    ]

    agg = agg.reset_index()

    # Calculate segment share
    total_customers = agg['n_customers'].sum()
    agg['segment_share'] = agg['n_customers'] / total_customers

    return agg


def aggregate_by_month(grid: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate simulation results by month (time series).

    Returns one row per month with:
    - Total revenue
    - Active customers
    - Seasonal patterns
    """
    agg = grid.groupby('month').agg({
        'customer_id': 'nunique',
        'company_revenue': 'sum',
        'monthly_bill': ['sum', 'mean'],
        'actual_hours': ['sum', 'mean'],
        'seasonality': 'mean',
        'efficiency_score': 'mean',
        'overage': 'sum',
        'efficiency_discount': 'sum',
        'is_over_limit': 'mean',
    })

    # Flatten column names
    agg.columns = [
        'active_customers', 'total_revenue', 'total_billing', 'avg_bill',
        'total_hours', 'avg_hours', 'avg_seasonality', 'avg_efficiency',
        'total_overage', 'total_discounts', 'pct_over_limit',
    ]

    agg = agg.reset_index()

    # Calculate cumulative revenue
    agg['cumulative_revenue'] = agg['total_revenue'].cumsum()

    return agg


def aggregate_by_plan(grid: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate by plan type for tiered analysis.
    """
    by_customer = aggregate_by_customer(grid)

    agg = by_customer.groupby('plan').agg({
        'customer_id': 'count',
        'total_revenue': ['sum', 'mean'],
        'avg_monthly_bill': 'mean',
        'avg_monthly_hours': 'mean',
        'pct_months_over': 'mean',
        'avg_efficiency_score': 'mean',
    })

    agg.columns = [
        'n_customers', 'total_revenue', 'avg_revenue_per_customer',
        'avg_monthly_bill', 'avg_monthly_hours', 'pct_over_limit',
        'avg_efficiency',
    ]

    agg = agg.reset_index()

    # Add plan details
    agg['plan_fee'] = agg['plan'].map(PLAN_FEES)
    agg['plan_hours'] = agg['plan'].map(PLAN_HOURS)

    return agg


def aggregate_portfolio(grid: pd.DataFrame, params: Optional[Dict] = None) -> Dict:
    """
    Calculate portfolio-level summary metrics.

    Args:
        grid: Simulation grid
        params: Cost parameters for margin calculation

    Returns:
        Dictionary with all portfolio metrics
    """
    if params is None:
        params = {
            'subsidy_percent': 0.50,
            'mrp': 45000,
            'manufacturing_cost': 30000,
            'iot_cost': 1500,
            'installation_cost': 2500,
            'cac': 2000,
            'bank_cac_subsidy': 2000,
            'warranty_reserve': 2000,
            'monthly_recurring_cost': 192,
        }

    n_customers = grid['customer_id'].nunique()
    tenure_months = grid['month'].max() + 1

    # Revenue metrics
    total_revenue = grid['company_revenue'].sum()
    avg_revenue_per_customer = total_revenue / n_customers

    # Billing metrics
    total_billed = grid['monthly_bill'].sum()
    avg_monthly_bill = grid['monthly_bill'].mean()

    # Usage metrics
    avg_hours = grid['actual_hours'].mean()
    pct_over_limit = grid['is_over_limit'].mean()

    # Efficiency metrics
    avg_efficiency = grid['efficiency_score'].mean()
    total_discounts = grid['efficiency_discount'].sum()
    total_overage = grid['overage'].sum()

    # Per-customer cost calculation
    customer_pays = params['mrp'] * (1 - params['subsidy_percent'])
    upfront_net = customer_pays / 1.18

    upfront_cost = (
        params['manufacturing_cost'] +
        params['iot_cost'] +
        params['installation_cost'] +
        params['cac'] +
        params['warranty_reserve']
    )

    upfront_deficit = upfront_cost - upfront_net
    recurring_cost_total = params['monthly_recurring_cost'] * tenure_months
    bank_subsidy = params['bank_cac_subsidy']

    # Margin calculation
    margin_per_customer = avg_revenue_per_customer - upfront_deficit - recurring_cost_total + bank_subsidy
    total_margin = margin_per_customer * n_customers

    return {
        # Portfolio size
        'n_customers': n_customers,
        'tenure_months': tenure_months,
        'total_customer_months': len(grid),

        # Revenue
        'total_revenue': total_revenue,
        'avg_revenue_per_customer': avg_revenue_per_customer,
        'avg_revenue_per_month': total_revenue / tenure_months,

        # Billing
        'total_billed_to_customers': total_billed,
        'avg_monthly_bill': avg_monthly_bill,
        'total_gst_collected': grid['gst_amount'].sum(),

        # Usage
        'avg_monthly_hours': avg_hours,
        'pct_months_over_limit': pct_over_limit,
        'total_overage_revenue': total_overage,

        # Efficiency
        'avg_efficiency_score': avg_efficiency,
        'total_discounts_given': total_discounts,

        # Costs
        'upfront_cost_per_customer': upfront_cost,
        'upfront_net_per_customer': upfront_net,
        'upfront_deficit_per_customer': upfront_deficit,
        'recurring_cost_per_customer': recurring_cost_total,
        'bank_cac_subsidy_per_customer': bank_subsidy,

        # Margins
        'margin_per_customer': margin_per_customer,
        'total_portfolio_margin': total_margin,
        'margin_percent': (margin_per_customer / avg_revenue_per_customer) * 100 if avg_revenue_per_customer > 0 else 0,
    }


# =============================================================================
# PRESENTATION FUNCTIONS
# =============================================================================

def calculate_simulation_summary(grid: pd.DataFrame, params: Optional[Dict] = None) -> str:
    """
    Generate a formatted summary report of simulation results.

    Designed to be PRINTED directly or included in reports.
    """
    portfolio = aggregate_portfolio(grid, params)
    by_segment = aggregate_by_segment(grid)
    by_plan = aggregate_by_plan(grid)
    by_month = aggregate_by_month(grid)

    lines = [
        "=" * 70,
        "SESP SIMULATION RESULTS — PORTFOLIO SUMMARY",
        "=" * 70,
        "",
        "[PORTFOLIO] OVERVIEW",
        "-" * 40,
        f"Total Customers:        {portfolio['n_customers']:,}",
        f"Tenure:                 {portfolio['tenure_months']} months",
        f"Total Customer-Months:  {portfolio['total_customer_months']:,}",
        "",
        "[REVENUE] METRICS",
        "-" * 40,
        f"Total Revenue (to company):  Rs{portfolio['total_revenue']:,.0f}",
        f"Avg Revenue/Customer:        Rs{portfolio['avg_revenue_per_customer']:,.0f}",
        f"Avg Monthly Bill:            Rs{portfolio['avg_monthly_bill']:,.0f}",
        f"Total GST Collected:         Rs{portfolio['total_gst_collected']:,.0f}",
        "",
        "[USAGE] METRICS",
        "-" * 40,
        f"Avg Monthly Hours:           {portfolio['avg_monthly_hours']:.1f}",
        f"% Months Over Limit:         {portfolio['pct_months_over_limit']:.1%}",
        f"Total Overage Revenue:       Rs{portfolio['total_overage_revenue']:,.0f}",
        "",
        "[EFFICIENCY] METRICS",
        "-" * 40,
        f"Avg Efficiency Score:        {portfolio['avg_efficiency_score']:.1f}",
        f"Total Discounts Given:       Rs{portfolio['total_discounts_given']:,.0f}",
        "",
        "[MARGIN] ANALYSIS",
        "-" * 40,
        f"Upfront Cost/Customer:       Rs{portfolio['upfront_cost_per_customer']:,.0f}",
        f"Upfront Net/Customer:        Rs{portfolio['upfront_net_per_customer']:,.0f}",
        f"Upfront Deficit/Customer:    Rs{portfolio['upfront_deficit_per_customer']:,.0f}",
        f"Recurring Cost/Customer:     Rs{portfolio['recurring_cost_per_customer']:,.0f}",
        f"Bank CAC Subsidy:            Rs{portfolio['bank_cac_subsidy_per_customer']:,.0f}",
        f"",
        f"MARGIN PER CUSTOMER:         Rs{portfolio['margin_per_customer']:,.0f}",
        f"TOTAL PORTFOLIO MARGIN:      Rs{portfolio['total_portfolio_margin']:,.0f}",
        f"Margin %:                    {portfolio['margin_percent']:.1f}%",
        "",
        "=" * 70,
        "SEGMENT BREAKDOWN",
        "=" * 70,
    ]

    # Segment table
    for _, row in by_segment.iterrows():
        lines.extend([
            "",
            f"[SEGMENT] {row['segment'].upper()} ({row['segment_share']:.0%} of customers)",
            "-" * 40,
            f"  Customers:        {row['n_customers']:,}",
            f"  Avg Revenue:      Rs{row['avg_revenue_per_customer']:,.0f}",
            f"  Avg Monthly Bill: Rs{row['avg_monthly_bill']:,.0f}",
            f"  Avg Hours/Month:  {row['avg_monthly_hours']:.1f}",
            f"  Efficiency Score: {row['avg_efficiency_score']:.1f}",
            f"  % Over Limit:     {row['pct_months_over_limit']:.1%}",
        ])

    lines.extend([
        "",
        "=" * 70,
        "PLAN BREAKDOWN",
        "=" * 70,
    ])

    # Plan table
    for _, row in by_plan.iterrows():
        lines.extend([
            "",
            f"[PLAN] {row['plan'].upper()} Plan (Rs{row['plan_fee']}/month, {row['plan_hours']} hrs)",
            "-" * 40,
            f"  Customers:        {row['n_customers']:,}",
            f"  Avg Revenue:      Rs{row['avg_revenue_per_customer']:,.0f}",
            f"  Avg Monthly Bill: Rs{row['avg_monthly_bill']:,.0f}",
            f"  Avg Hours/Month:  {row['avg_monthly_hours']:.1f}",
            f"  % Over Limit:     {row['pct_over_limit']:.1%}",
        ])

    lines.extend([
        "",
        "=" * 70,
        "SEASONALITY ANALYSIS",
        "=" * 70,
        "",
    ])

    # Find peak and low months
    peak_month = by_month.loc[by_month['total_revenue'].idxmax()]
    low_month = by_month.loc[by_month['total_revenue'].idxmin()]

    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    lines.extend([
        f"Peak Month: {peak_month['month']} (Revenue: Rs{peak_month['total_revenue']:,.0f})",
        f"Low Month:  {low_month['month']} (Revenue: Rs{low_month['total_revenue']:,.0f})",
        f"Peak/Low Ratio: {peak_month['total_revenue'] / low_month['total_revenue']:.2f}x",
    ])

    lines.extend([
        "",
        "=" * 70,
        "VALIDATION vs PHASE 3c PROJECTIONS",
        "=" * 70,
        "",
        f"Phase 3c projected blended margin: Rs3,746/customer",
        f"Simulation result:                 Rs{portfolio['margin_per_customer']:,.0f}/customer",
        f"Difference:                        Rs{portfolio['margin_per_customer'] - 3746:+,.0f}",
        "",
        "=" * 70,
    ])

    return "\n".join(lines)


def export_results(grid: pd.DataFrame, output_dir: str = 'data') -> Dict[str, str]:
    """
    Export all aggregation results to CSV files.

    Args:
        grid: Simulation grid
        output_dir: Directory for output files

    Returns:
        Dictionary of file paths
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    files = {}

    # Customer-level
    by_customer = aggregate_by_customer(grid)
    path = os.path.join(output_dir, 'simulation_by_customer.csv')
    by_customer.to_csv(path, index=False)
    files['by_customer'] = path

    # Segment-level
    by_segment = aggregate_by_segment(grid)
    path = os.path.join(output_dir, 'simulation_by_segment.csv')
    by_segment.to_csv(path, index=False)
    files['by_segment'] = path

    # Month-level
    by_month = aggregate_by_month(grid)
    path = os.path.join(output_dir, 'simulation_by_month.csv')
    by_month.to_csv(path, index=False)
    files['by_month'] = path

    # Plan-level
    by_plan = aggregate_by_plan(grid)
    path = os.path.join(output_dir, 'simulation_by_plan.csv')
    by_plan.to_csv(path, index=False)
    files['by_plan'] = path

    # Full grid (optional, large file)
    path = os.path.join(output_dir, 'simulation_full_grid.csv')
    grid.to_csv(path, index=False)
    files['full_grid'] = path

    return files


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    from .data_generator import generate_customers
    from .simulator import simulate_portfolio

    # Generate and simulate
    customers = generate_customers(1000, random_seed=42)
    grid = simulate_portfolio(customers, tenure_months=60, random_seed=42)

    # Print summary
    print(calculate_simulation_summary(grid))
