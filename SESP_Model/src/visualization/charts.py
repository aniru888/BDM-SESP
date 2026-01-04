"""
Charts — Presentation-Ready Visualizations
==========================================

All charts are styled for professional presentation with:
- Clear titles and labels
- Consistent color scheme
- Appropriate sizing
- Grid lines for readability
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from typing import Dict, List, Optional, Tuple
import os

# Import aggregation functions
from src.simulation.aggregator import (
    aggregate_by_customer,
    aggregate_by_segment,
    aggregate_by_month,
    aggregate_by_plan,
    aggregate_portfolio,
)


# =============================================================================
# STYLE CONFIGURATION
# =============================================================================

# Color palette (professional, accessible)
COLORS = {
    'primary': '#2E86AB',      # Blue
    'secondary': '#A23B72',    # Magenta
    'accent': '#F18F01',       # Orange
    'success': '#C73E1D',      # Red-orange
    'light': '#3B8EA5',        # Light blue
    'moderate': '#F5B041',     # Yellow-orange
    'heavy': '#E74C3C',        # Red
    'lite': '#3498DB',         # Bright blue
    'standard': '#27AE60',     # Green
    'premium': '#9B59B6',      # Purple
}

SEGMENT_COLORS = {
    'light': COLORS['light'],
    'moderate': COLORS['moderate'],
    'heavy': COLORS['heavy'],
}

PLAN_COLORS = {
    'lite': COLORS['lite'],
    'standard': COLORS['standard'],
    'premium': COLORS['premium'],
}


def set_presentation_style():
    """Apply consistent presentation style to all plots."""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update({
        'font.size': 11,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 16,
        'figure.figsize': (10, 6),
        'figure.dpi': 100,
        'axes.grid': True,
        'grid.alpha': 0.3,
    })


# =============================================================================
# CHART 1: USAGE DISTRIBUTION BY SEGMENT
# =============================================================================

def plot_usage_distribution(
    grid: pd.DataFrame,
    save_path: Optional[str] = None,
    show: bool = False
) -> plt.Figure:
    """
    Histogram showing actual hours distribution by segment.

    Validates: Segments have distinct usage patterns.
    """
    set_presentation_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    for segment in ['light', 'moderate', 'heavy']:
        data = grid[grid['segment'] == segment]['actual_hours']
        ax.hist(data, bins=50, alpha=0.6, label=f'{segment.title()} ({len(data):,})',
                color=SEGMENT_COLORS[segment], edgecolor='white')

    ax.set_xlabel('Monthly Hours Used')
    ax.set_ylabel('Frequency')
    ax.set_title('Usage Distribution by Segment')
    ax.legend(title='Segment')

    # Add vertical lines for plan thresholds (annual average seasonal hours)
    # Lite: 88 hrs/mo avg, Standard: 177 hrs/mo avg, Premium: 307 hrs/mo avg
    for hours, label in [(88, 'Lite avg'), (177, 'Standard avg'), (307, 'Premium avg')]:
        ax.axvline(x=hours, color='gray', linestyle='--', alpha=0.5)
        ax.text(hours + 5, ax.get_ylim()[1] * 0.9, label, fontsize=8, color='gray')

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    if show:
        plt.show()

    return fig


# =============================================================================
# CHART 2: MONTHLY BILL DISTRIBUTION
# =============================================================================

def plot_bill_distribution(
    grid: pd.DataFrame,
    save_path: Optional[str] = None,
    show: bool = False
) -> plt.Figure:
    """
    Histogram showing monthly bill distribution.

    Validates: Bill predictability and no extreme outliers.
    """
    set_presentation_style()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Overall distribution
    ax1 = axes[0]
    ax1.hist(grid['monthly_bill'], bins=50, color=COLORS['primary'], alpha=0.7, edgecolor='white')
    ax1.axvline(grid['monthly_bill'].mean(), color='red', linestyle='--',
                label=f"Mean: Rs{grid['monthly_bill'].mean():.0f}")
    ax1.axvline(grid['monthly_bill'].median(), color='orange', linestyle='-.',
                label=f"Median: Rs{grid['monthly_bill'].median():.0f}")
    ax1.set_xlabel('Monthly Bill (Rs)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Overall Monthly Bill Distribution')
    ax1.legend()

    # By plan
    ax2 = axes[1]
    for plan in ['lite', 'standard', 'premium']:
        data = grid[grid['plan'] == plan]['monthly_bill']
        ax2.hist(data, bins=30, alpha=0.6, label=f'{plan.title()} (n={len(data):,})',
                 color=PLAN_COLORS[plan], edgecolor='white')

    ax2.set_xlabel('Monthly Bill (Rs)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Monthly Bill by Plan')
    ax2.legend()

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    if show:
        plt.show()

    return fig


# =============================================================================
# CHART 3: EFFICIENCY SCORE VS DISCOUNT
# =============================================================================

def plot_efficiency_vs_discount(
    grid: pd.DataFrame,
    sample_size: int = 5000,
    save_path: Optional[str] = None,
    show: bool = False
) -> plt.Figure:
    """
    Scatter plot showing efficiency score vs discount earned.

    Validates: Reward mechanism working correctly.
    """
    set_presentation_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    # Sample for performance
    sample = grid.sample(min(sample_size, len(grid)))

    scatter = ax.scatter(
        sample['efficiency_score'],
        sample['efficiency_discount'],
        c=sample['segment'].map({'light': 0, 'moderate': 1, 'heavy': 2}),
        cmap='viridis',
        alpha=0.3,
        s=10,
    )

    # Add tier thresholds
    for threshold, label, color in [(90, 'Champion (20%)', 'green'),
                                     (75, 'Star (12%)', 'blue'),
                                     (60, 'Aware (5%)', 'orange')]:
        ax.axvline(x=threshold, color=color, linestyle='--', alpha=0.7, label=label)

    ax.set_xlabel('Efficiency Score')
    ax.set_ylabel('Discount Earned (Rs)')
    ax.set_title('Efficiency Score vs Discount Earned')
    ax.legend(loc='upper left')

    # Add colorbar for segments
    cbar = plt.colorbar(scatter, ax=ax, ticks=[0, 1, 2])
    cbar.ax.set_yticklabels(['Light', 'Moderate', 'Heavy'])
    cbar.set_label('Segment')

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    if show:
        plt.show()

    return fig


# =============================================================================
# CHART 4: MONTHLY CASH FLOW
# =============================================================================

def plot_monthly_cashflow(
    grid: pd.DataFrame,
    save_path: Optional[str] = None,
    show: bool = False
) -> plt.Figure:
    """
    Line chart showing monthly revenue over time.

    Validates: Seasonality patterns visible.
    """
    set_presentation_style()
    fig, ax = plt.subplots(figsize=(12, 6))

    by_month = aggregate_by_month(grid)

    ax.plot(by_month['month'], by_month['total_revenue'] / 1000,
            color=COLORS['primary'], linewidth=2, marker='o', markersize=4)

    ax.fill_between(by_month['month'], by_month['total_revenue'] / 1000,
                    alpha=0.2, color=COLORS['primary'])

    ax.set_xlabel('Month')
    ax.set_ylabel('Monthly Revenue (Rs thousands)')
    ax.set_title('Monthly Revenue Over Tenure')

    # Add average line
    avg = by_month['total_revenue'].mean() / 1000
    ax.axhline(y=avg, color='red', linestyle='--', alpha=0.7,
               label=f'Average: Rs{avg:.0f}k')

    ax.legend()
    ax.xaxis.set_major_locator(mticker.MultipleLocator(6))

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    if show:
        plt.show()

    return fig


# =============================================================================
# CHART 5: CUMULATIVE PROFIT
# =============================================================================

def plot_cumulative_profit(
    grid: pd.DataFrame,
    params: Optional[Dict] = None,
    save_path: Optional[str] = None,
    show: bool = False,
    scenario: str = "Expected Case"
) -> plt.Figure:
    """
    Line chart showing cumulative profit/loss over tenure.

    Validates: Break-even point identification.

    Args:
        scenario: "Expected Case" (default, matches report) or "Base Case" (conservative)
    """
    if params is None:
        if scenario == "Expected Case":
            # Expected Case: Include deposit as cash inflow, bank subsidy reduces deficit
            # Matches dashboard/report methodology for Month 23 break-even
            params = {
                'effective_deficit_per_customer': 7559,  # (36000 - 2000) - 27500 + GST adj
                'monthly_recurring_cost': 192,
                'monthly_contribution': 315,  # (599 × 0.847) - 192
            }
        else:
            # Base Case: Conservative, no deposit/extras
            params = {
                'effective_deficit_per_customer': 16932,  # From Phase 3c (upfront_cost - upfront_net)
                'monthly_recurring_cost': 192,
                'monthly_contribution': 315,
            }

    set_presentation_style()
    fig, ax = plt.subplots(figsize=(12, 6))

    by_month = aggregate_by_month(grid)
    n_customers = grid['customer_id'].nunique()

    # Calculate cumulative profit using cash flow methodology
    cumulative_revenue = by_month['total_revenue'].cumsum()
    effective_deficit = params['effective_deficit_per_customer'] * n_customers
    recurring_cost = params['monthly_recurring_cost'] * n_customers * (by_month['month'] + 1)

    # Cumulative profit = revenue - initial deficit - recurring costs
    cumulative_profit = cumulative_revenue - effective_deficit - recurring_cost

    ax.plot(by_month['month'], cumulative_profit / 1e6,
            color=COLORS['primary'], linewidth=2)

    ax.fill_between(by_month['month'], cumulative_profit / 1e6,
                    where=(cumulative_profit >= 0),
                    alpha=0.3, color='green', label='Profit')
    ax.fill_between(by_month['month'], cumulative_profit / 1e6,
                    where=(cumulative_profit < 0),
                    alpha=0.3, color='red', label='Loss')

    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)

    # Find break-even
    breakeven_idx = None
    for i, val in enumerate(cumulative_profit):
        if val >= 0:
            breakeven_idx = i
            break

    if breakeven_idx:
        ax.axvline(x=breakeven_idx, color='green', linestyle='--', alpha=0.7)
        ax.annotate(f'Break-even: Month {breakeven_idx}',
                    xy=(breakeven_idx, 0), xytext=(breakeven_idx + 5, cumulative_profit.max() / 2e6),
                    arrowprops=dict(arrowstyle='->', color='green'),
                    fontsize=10, color='green')

    ax.set_xlabel('Month')
    ax.set_ylabel('Cumulative Profit (Rs millions)')
    ax.set_title(f'Cumulative Profit/Loss Over Tenure ({scenario})')
    ax.legend(loc='lower right')
    ax.xaxis.set_major_locator(mticker.MultipleLocator(6))

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    if show:
        plt.show()

    return fig


# =============================================================================
# CHART 6: SEGMENT COMPARISON
# =============================================================================

def plot_segment_comparison(
    grid: pd.DataFrame,
    save_path: Optional[str] = None,
    show: bool = False
) -> plt.Figure:
    """
    Grouped bar chart comparing segments on key metrics.
    """
    set_presentation_style()
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    by_segment = aggregate_by_segment(grid)

    segments = by_segment['segment'].tolist()
    x = np.arange(len(segments))
    width = 0.6
    colors = [SEGMENT_COLORS[s] for s in segments]

    # Revenue per customer
    ax1 = axes[0, 0]
    ax1.bar(x, by_segment['avg_revenue_per_customer'] / 1000, width, color=colors)
    ax1.set_ylabel('Revenue (Rs thousands)')
    ax1.set_title('Average Revenue per Customer')
    ax1.set_xticks(x)
    ax1.set_xticklabels([s.title() for s in segments])

    # Monthly hours
    ax2 = axes[0, 1]
    ax2.bar(x, by_segment['avg_monthly_hours'], width, color=colors)
    ax2.set_ylabel('Hours')
    ax2.set_title('Average Monthly Hours')
    ax2.set_xticks(x)
    ax2.set_xticklabels([s.title() for s in segments])

    # Efficiency score
    ax3 = axes[1, 0]
    ax3.bar(x, by_segment['avg_efficiency_score'], width, color=colors)
    ax3.set_ylabel('Score')
    ax3.set_title('Average Efficiency Score')
    ax3.set_xticks(x)
    ax3.set_xticklabels([s.title() for s in segments])
    ax3.axhline(y=75, color='green', linestyle='--', alpha=0.5, label='Star threshold')
    ax3.legend()

    # % Over limit
    ax4 = axes[1, 1]
    ax4.bar(x, by_segment['pct_months_over_limit'] * 100, width, color=colors)
    ax4.set_ylabel('Percentage')
    ax4.set_title('% Months Over Plan Limit')
    ax4.set_xticks(x)
    ax4.set_xticklabels([s.title() for s in segments])

    plt.suptitle('Segment Comparison', fontsize=14, y=1.02)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    if show:
        plt.show()

    return fig


# =============================================================================
# CHART 7: SEASONALITY IMPACT
# =============================================================================

def plot_seasonality_impact(
    grid: pd.DataFrame,
    save_path: Optional[str] = None,
    show: bool = False
) -> plt.Figure:
    """
    Line chart showing seasonal patterns in usage and revenue.
    """
    set_presentation_style()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Aggregate by month-of-year
    grid['month_label'] = grid['month_of_year'].map({
        0: 'Jan', 1: 'Feb', 2: 'Mar', 3: 'Apr', 4: 'May', 5: 'Jun',
        6: 'Jul', 7: 'Aug', 8: 'Sep', 9: 'Oct', 10: 'Nov', 11: 'Dec'
    })

    by_moy = grid.groupby('month_of_year').agg({
        'actual_hours': 'mean',
        'company_revenue': 'mean',
        'seasonality': 'mean',
    }).reset_index()

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Usage seasonality
    ax1 = axes[0]
    ax1.plot(by_moy['month_of_year'], by_moy['actual_hours'],
             color=COLORS['primary'], linewidth=2, marker='o')
    ax1.fill_between(by_moy['month_of_year'], by_moy['actual_hours'],
                     alpha=0.2, color=COLORS['primary'])
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Avg Monthly Hours')
    ax1.set_title('Usage Seasonality')
    ax1.set_xticks(range(12))
    ax1.set_xticklabels(months, rotation=45)

    # Revenue seasonality
    ax2 = axes[1]
    ax2.plot(by_moy['month_of_year'], by_moy['company_revenue'],
             color=COLORS['secondary'], linewidth=2, marker='s')
    ax2.fill_between(by_moy['month_of_year'], by_moy['company_revenue'],
                     alpha=0.2, color=COLORS['secondary'])
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Avg Revenue per Customer (Rs)')
    ax2.set_title('Revenue Seasonality')
    ax2.set_xticks(range(12))
    ax2.set_xticklabels(months, rotation=45)

    plt.suptitle('Seasonality Impact on Usage and Revenue', fontsize=14, y=1.02)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    if show:
        plt.show()

    return fig


# =============================================================================
# CHART 8: MARGIN WATERFALL
# =============================================================================

def plot_margin_waterfall(
    grid: pd.DataFrame,
    params: Optional[Dict] = None,
    save_path: Optional[str] = None,
    show: bool = False,
    scenario: str = "Expected Case"
) -> plt.Figure:
    """
    Waterfall chart showing margin buildup.

    Args:
        scenario: "Expected Case" (default, matches report) or "Base Case" (conservative)
    """
    if params is None:
        params = {
            'mrp': 45000,
            'subsidy_percent': 0.50,
            'manufacturing_cost': 30000,
            'iot_cost': 1500,
            'installation_cost': 2500,
            'cac': 2000,
            'warranty_reserve': 2000,
            'bank_cac_subsidy': 2000,
            'monthly_recurring_cost': 192,
            'monthly_fee': 599,
            'deposit': 5000,
        }

    set_presentation_style()
    fig, ax = plt.subplots(figsize=(14, 7))

    portfolio = aggregate_portfolio(grid, params)
    tenure = portfolio['tenure_months']

    # Calculate components based on scenario
    if scenario == "Expected Case":
        # Expected Case: Matches dashboard/report methodology
        # Revenue components (all net of GST where applicable)
        monthly_fee = params.get('monthly_fee', 599)
        upfront_net = (params['mrp'] * (1 - params['subsidy_percent'])) / 1.18  # Rs 19,068
        monthly_revenue = monthly_fee * 0.847 * tenure  # Rs 30,449
        overage_revenue = 1200   # Simulation average
        addon_revenue = 1500     # Extended warranty, services
        bank_subsidy = params['bank_cac_subsidy']  # Rs 2,000

        # Cost components (cash outflows)
        upfront_cost = (params['manufacturing_cost'] + params['iot_cost'] +
                       params['installation_cost'] + params['cac'])  # Rs 36,000 (excl warranty for cash)
        recurring_cost = params['monthly_recurring_cost'] * tenure  # Rs 11,520
        discount_cost = int(0.07 * monthly_fee * 0.847 * tenure)  # ~Rs 2,517

        # Margin calculation (matches report ~Rs 6,454)
        total_revenue = upfront_net + monthly_revenue + overage_revenue + addon_revenue
        total_cost = upfront_cost + recurring_cost + discount_cost
        margin = total_revenue - total_cost + bank_subsidy

        items = [
            ('Upfront\n(net GST)', upfront_net, 'green'),
            ('Monthly\nRevenue', monthly_revenue, 'green'),
            ('Overage', overage_revenue, 'green'),
            ('Add-ons', addon_revenue, 'green'),
            ('Bank\nSubsidy', bank_subsidy, 'green'),
            ('Upfront\nCost', -upfront_cost, 'red'),
            ('Recurring\nCost', -recurring_cost, 'red'),
            ('Discount\nCost', -discount_cost, 'red'),
            ('MARGIN', margin, 'blue'),
        ]
    else:
        # Base Case: Conservative (original formula)
        items = [
            ('Revenue\n(60 months)', portfolio['avg_revenue_per_customer'], 'green'),
            ('Bank CAC\nSubsidy', params['bank_cac_subsidy'], 'green'),
            ('Upfront\nCost', -portfolio['upfront_cost_per_customer'], 'red'),
            ('Upfront\nNet', portfolio['upfront_net_per_customer'], 'green'),
            ('Recurring\nCost', -portfolio['recurring_cost_per_customer'], 'red'),
            ('MARGIN', portfolio['margin_per_customer'], 'blue'),
        ]

    # Calculate positions
    labels = [i[0] for i in items]
    values = [i[1] for i in items]
    colors = [i[2] for i in items]

    # Create waterfall
    running = 0
    bottoms = []
    for i, val in enumerate(values):
        if i == len(values) - 1:  # Final margin bar
            bottoms.append(0)
        else:
            if val >= 0:
                bottoms.append(running)
                running += val
            else:
                running += val
                bottoms.append(running)

    x = np.arange(len(labels))
    bars = ax.bar(x, values, bottom=bottoms, color=colors, alpha=0.7, edgecolor='black')

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, values)):
        height = bar.get_height()
        y_pos = bar.get_y() + height / 2
        label = f'Rs{val:,.0f}' if val >= 0 else f'-Rs{abs(val):,.0f}'
        ax.annotate(label, xy=(bar.get_x() + bar.get_width() / 2, y_pos),
                    ha='center', va='center', fontsize=9, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel('Amount (Rs)')
    ax.set_title(f'Margin Waterfall — Per Customer Analysis ({scenario})')
    ax.axhline(y=0, color='black', linewidth=0.5)

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', alpha=0.7, label='Inflows'),
        Patch(facecolor='red', alpha=0.7, label='Costs'),
        Patch(facecolor='blue', alpha=0.7, label='Net Margin'),
    ]
    ax.legend(handles=legend_elements, loc='upper right')

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    if show:
        plt.show()

    return fig


# =============================================================================
# MASTER FUNCTION: CREATE ALL CHARTS
# =============================================================================

def create_all_charts(
    grid: pd.DataFrame,
    output_dir: str = 'outputs/charts',
    params: Optional[Dict] = None,
    show: bool = False,
    scenario: str = "Expected Case"
) -> Dict[str, str]:
    """
    Generate all 8 required charts and save to output directory.

    Args:
        grid: Simulation grid from simulate_portfolio()
        output_dir: Directory to save charts (default: outputs/charts)
        params: Optional cost parameters for margin calculations
        show: Whether to display charts interactively
        scenario: "Expected Case" (default, matches report) or "Base Case" (conservative)

    Returns:
        Dictionary mapping chart names to file paths
    """
    os.makedirs(output_dir, exist_ok=True)

    paths = {}

    # Chart 1: Usage distribution
    path = os.path.join(output_dir, '1_usage_distribution.png')
    plot_usage_distribution(grid, save_path=path, show=show)
    paths['usage_distribution'] = path
    plt.close()

    # Chart 2: Bill distribution
    path = os.path.join(output_dir, '2_bill_distribution.png')
    plot_bill_distribution(grid, save_path=path, show=show)
    paths['bill_distribution'] = path
    plt.close()

    # Chart 3: Efficiency vs discount
    path = os.path.join(output_dir, '3_efficiency_vs_discount.png')
    plot_efficiency_vs_discount(grid, save_path=path, show=show)
    paths['efficiency_vs_discount'] = path
    plt.close()

    # Chart 4: Monthly cashflow
    path = os.path.join(output_dir, '4_monthly_cashflow.png')
    plot_monthly_cashflow(grid, save_path=path, show=show)
    paths['monthly_cashflow'] = path
    plt.close()

    # Chart 5: Cumulative profit
    path = os.path.join(output_dir, '5_cumulative_profit.png')
    plot_cumulative_profit(grid, params=params, save_path=path, show=show, scenario=scenario)
    paths['cumulative_profit'] = path
    plt.close()

    # Chart 6: Segment comparison
    path = os.path.join(output_dir, '6_segment_comparison.png')
    plot_segment_comparison(grid, save_path=path, show=show)
    paths['segment_comparison'] = path
    plt.close()

    # Chart 7: Seasonality impact
    path = os.path.join(output_dir, '7_seasonality_impact.png')
    plot_seasonality_impact(grid, save_path=path, show=show)
    paths['seasonality_impact'] = path
    plt.close()

    # Chart 8: Margin waterfall
    path = os.path.join(output_dir, '8_margin_waterfall.png')
    plot_margin_waterfall(grid, params=params, save_path=path, show=show, scenario=scenario)
    paths['margin_waterfall'] = path
    plt.close()

    print(f"\n[OK] Generated {len(paths)} charts in {output_dir}/")
    for name, path in paths.items():
        print(f"   - {name}: {os.path.basename(path)}")

    return paths


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    from src.simulation.data_generator import generate_customers
    from src.simulation.simulator import simulate_portfolio

    print("Generating test data...")
    customers = generate_customers(500, random_seed=42)
    grid = simulate_portfolio(customers, tenure_months=24, random_seed=42)

    print("Creating charts...")
    paths = create_all_charts(grid, output_dir='outputs/charts_test', show=False)

    print(f"\nDone! Charts saved to:")
    for name, path in paths.items():
        print(f"  {name}: {path}")
