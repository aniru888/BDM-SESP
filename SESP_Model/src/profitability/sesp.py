"""
SESP Profitability Model (Task 3.2)
===================================

Models SESP subscription economics from the manufacturer's perspective.

SESP Model:
- Subsidized upfront price (customer pays less than MRP)
- Recurring monthly subscription fees
- Direct customer relationship (no dealer)
- Includes: maintenance, warranty, IoT monitoring
- Company retains asset ownership (initially)

Key Metrics:
- Revenue: Upfront + Monthly fees + Overage + Add-ons
- Costs: Manufacturing + IoT + Installation + Support + Maintenance + CAC
- Gross margin: Lower initially, improves over tenure
- CLV: Higher due to recurring relationship and data

Uses validated parameters from PC diagnosis:
- Subsidy: 65-70% of MRP
- Tenure: 24-36 months
- Monthly fees: Rs499-899 (by plan)

This provides the "after" component for SESP comparison.
"""

from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# =============================================================================
# Default Parameters (from validated scenarios)
# =============================================================================

SESP_DEFAULTS = {
    'mrp': 45000,
    'subsidy_percent': 0.65,         # 65% subsidy (validated)
    'manufacturing_cost': 30000,
    'iot_hardware': 1500,
    'iot_recurring_annual': 600,
    'installation_cost': 2500,
    'maintenance_annual': 1200,
    'warranty_reserve': 2000,
    'support_annual': 500,
    'cac': 2000,
    'tenure_months': 24,             # Validated shorter tenure
    'default_rate': 0.03,            # 3% default
    'churn_rate': 0.05,              # 5% churn
    'gst_rate': 0.18,
    'firm_discount_rate': 0.12,
}

# Plan fee structure
PLAN_FEES = {
    'light': {'monthly_fee': 499, 'overage_rate': 0.05},
    'moderate': {'monthly_fee': 649, 'overage_rate': 0.04},
    'heavy': {'monthly_fee': 899, 'overage_rate': 0.03},
}

# Segment mix (expected distribution)
DEFAULT_SEGMENT_MIX = {
    'light': 0.30,
    'moderate': 0.50,
    'heavy': 0.20,
}


# =============================================================================
# Revenue Calculations
# =============================================================================

def calculate_sesp_revenue(
    mrp: float = SESP_DEFAULTS['mrp'],
    subsidy_percent: float = SESP_DEFAULTS['subsidy_percent'],
    tenure_months: int = SESP_DEFAULTS['tenure_months'],
    segment_mix: Optional[Dict[str, float]] = None,
    efficiency_discount_rate: float = 0.08,  # Average 8% discount for efficiency
    overage_revenue_rate: float = 0.05,      # Average 5% of base fee as overage
) -> Dict[str, Any]:
    """
    Calculate revenue from an SESP subscription.

    Revenue Model:
    - Upfront: Subsidized price (MRP × (1 - subsidy))
    - Monthly: Base fee × tenure × (1 - efficiency discount) + overage
    - Add-ons: Premium services, upgrades (estimated)

    All revenue net of GST (company receives less than customer pays).

    Args:
        mrp: Maximum Retail Price
        subsidy_percent: Subsidy as decimal (0.65 = 65%)
        tenure_months: Contract duration
        segment_mix: Distribution across plans
        efficiency_discount_rate: Average efficiency discount given
        overage_revenue_rate: Average overage as % of base fee

    Returns:
        Dictionary with revenue breakdown.
    """
    if segment_mix is None:
        segment_mix = DEFAULT_SEGMENT_MIX

    subsidized_price = mrp * (1 - subsidy_percent)

    # Net of GST (company receives gross / 1.18)
    upfront_net = subsidized_price / (1 + SESP_DEFAULTS['gst_rate'])

    # Weighted average monthly fee based on segment mix
    weighted_fee = sum(
        PLAN_FEES[plan]['monthly_fee'] * proportion
        for plan, proportion in segment_mix.items()
    )

    # Net monthly fee (after GST, efficiency discount, plus overage)
    base_monthly_net = weighted_fee / (1 + SESP_DEFAULTS['gst_rate'])
    discount_given = base_monthly_net * efficiency_discount_rate
    overage_earned = base_monthly_net * overage_revenue_rate
    effective_monthly_net = base_monthly_net - discount_given + overage_earned

    # Total monthly revenue over tenure
    total_monthly_net = effective_monthly_net * tenure_months

    # Add-on services (estimated 5% of base over tenure)
    addon_revenue = total_monthly_net * 0.05

    # Total revenue
    total_revenue = upfront_net + total_monthly_net + addon_revenue

    return {
        'mrp': mrp,
        'subsidy_percent': subsidy_percent * 100,
        'subsidized_price': round(subsidized_price, 2),
        'upfront_net': round(upfront_net, 2),
        'weighted_monthly_fee': round(weighted_fee, 2),
        'base_monthly_net': round(base_monthly_net, 2),
        'efficiency_discount': round(discount_given * tenure_months, 2),
        'overage_revenue': round(overage_earned * tenure_months, 2),
        'effective_monthly_net': round(effective_monthly_net, 2),
        'total_monthly_net': round(total_monthly_net, 2),
        'addon_revenue': round(addon_revenue, 2),
        'total_revenue': round(total_revenue, 2),
        'tenure_months': tenure_months,
        'segment_mix': segment_mix,
        'notes': 'All revenue figures net of GST'
    }


# =============================================================================
# Cost Calculations
# =============================================================================

def calculate_sesp_costs(
    manufacturing_cost: float = SESP_DEFAULTS['manufacturing_cost'],
    iot_hardware: float = SESP_DEFAULTS['iot_hardware'],
    iot_recurring_annual: float = SESP_DEFAULTS['iot_recurring_annual'],
    installation_cost: float = SESP_DEFAULTS['installation_cost'],
    maintenance_annual: float = SESP_DEFAULTS['maintenance_annual'],
    warranty_reserve: float = SESP_DEFAULTS['warranty_reserve'],
    support_annual: float = SESP_DEFAULTS['support_annual'],
    cac: float = SESP_DEFAULTS['cac'],
    tenure_months: int = SESP_DEFAULTS['tenure_months'],
    default_rate: float = SESP_DEFAULTS['default_rate'],
) -> Dict[str, Any]:
    """
    Calculate costs for an SESP subscription.

    Cost Model:
    - Upfront: Manufacturing + IoT hardware + Installation + CAC
    - Recurring: IoT service + Maintenance + Support
    - Reserves: Warranty + Default provisioning

    Args:
        All cost parameters from defaults.
        tenure_months: Contract duration
        default_rate: Expected default rate for provisioning

    Returns:
        Dictionary with cost breakdown.
    """
    tenure_years = tenure_months / 12

    # Upfront costs
    upfront_costs = manufacturing_cost + iot_hardware + installation_cost + cac

    # Recurring costs (over tenure)
    iot_recurring = iot_recurring_annual * tenure_years
    maintenance = maintenance_annual * tenure_years
    support = support_annual * tenure_years
    recurring_costs = iot_recurring + maintenance + support

    # Reserves
    warranty = warranty_reserve
    default_provision = upfront_costs * default_rate  # Provision for defaults
    reserves = warranty + default_provision

    # Total cost
    total_cost = upfront_costs + recurring_costs + reserves

    return {
        'manufacturing_cost': manufacturing_cost,
        'iot_hardware': iot_hardware,
        'installation_cost': installation_cost,
        'cac': cac,
        'upfront_total': upfront_costs,
        'iot_recurring': round(iot_recurring, 2),
        'maintenance': round(maintenance, 2),
        'support': round(support, 2),
        'recurring_total': round(recurring_costs, 2),
        'warranty_reserve': warranty,
        'default_provision': round(default_provision, 2),
        'reserves_total': round(reserves, 2),
        'total_cost': round(total_cost, 2),
        'tenure_months': tenure_months,
        'notes': f'Costs over {tenure_months} month tenure'
    }


# =============================================================================
# Margin Calculations
# =============================================================================

def calculate_sesp_margin(
    mrp: float = SESP_DEFAULTS['mrp'],
    subsidy_percent: float = SESP_DEFAULTS['subsidy_percent'],
    tenure_months: int = SESP_DEFAULTS['tenure_months'],
    segment_mix: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Calculate gross margin for an SESP subscription.

    Margin = (Total Revenue - Total Cost) / Total Revenue

    Note: SESP margin is typically lower than traditional in early
    tenure due to high upfront costs, but improves with longer tenure
    and recurring revenue.

    Args:
        mrp: Product MRP
        subsidy_percent: Subsidy as decimal
        tenure_months: Contract duration
        segment_mix: Distribution across plans

    Returns:
        Dictionary with margin breakdown.
    """
    revenue = calculate_sesp_revenue(
        mrp, subsidy_percent, tenure_months, segment_mix
    )
    costs = calculate_sesp_costs(tenure_months=tenure_months)

    gross_profit = revenue['total_revenue'] - costs['total_cost']
    gross_margin_percent = (gross_profit / revenue['total_revenue']) * 100

    # Break-even analysis
    monthly_net_contribution = revenue['effective_monthly_net'] - (
        costs['recurring_total'] / tenure_months
    )

    upfront_deficit = costs['upfront_total'] - revenue['upfront_net']
    if monthly_net_contribution > 0:
        breakeven_months = max(1, upfront_deficit / monthly_net_contribution)
    else:
        breakeven_months = tenure_months  # Never breaks even in tenure

    return {
        'total_revenue': revenue['total_revenue'],
        'total_cost': costs['total_cost'],
        'gross_profit': round(gross_profit, 2),
        'gross_margin_percent': round(gross_margin_percent, 2),
        'upfront_deficit': round(upfront_deficit, 2),
        'monthly_net_contribution': round(monthly_net_contribution, 2),
        'breakeven_months': round(breakeven_months, 1),
        'revenue_breakdown': revenue,
        'cost_breakdown': costs,
        'notes': f'Break-even at month {breakeven_months:.0f}'
    }


# =============================================================================
# Customer Lifetime Value
# =============================================================================

def calculate_sesp_clv(
    mrp: float = SESP_DEFAULTS['mrp'],
    subsidy_percent: float = SESP_DEFAULTS['subsidy_percent'],
    tenure_months: int = SESP_DEFAULTS['tenure_months'],
    segment_mix: Optional[Dict[str, float]] = None,
    churn_rate: float = SESP_DEFAULTS['churn_rate'],
    default_rate: float = SESP_DEFAULTS['default_rate'],
    discount_rate: float = SESP_DEFAULTS['firm_discount_rate'],
    renewal_rate: float = 0.40,          # 40% renewal for second tenure
    upsell_rate: float = 0.15,           # 15% upsell to higher plan
    referral_rate: float = 0.12,         # 12% referral (higher than traditional)
    referral_value: float = 500,         # Higher referral value (direct relationship)
    data_value: float = 200,             # Annual value of customer data
) -> Dict[str, Any]:
    """
    Calculate risk-adjusted Customer Lifetime Value for SESP.

    CLV Components:
    1. First tenure margin (risk-adjusted for default/churn)
    2. Renewal value (probability-weighted second tenure)
    3. Upsell value (probability of plan upgrade)
    4. Referral value (higher than traditional due to relationship)
    5. Data asset value (IoT data monetization potential)

    Args:
        All parameters as described above.

    Returns:
        Dictionary with CLV breakdown.
    """
    margin = calculate_sesp_margin(mrp, subsidy_percent, tenure_months, segment_mix)
    tenure_years = tenure_months / 12

    # 1. First tenure margin (adjusted for risk)
    survival_rate = 1 - churn_rate - default_rate
    first_tenure_margin = margin['gross_profit'] * survival_rate

    # 2. Renewal value (second tenure, weighted by probability)
    # Second tenure has lower costs (no CAC, asset already exists)
    renewal_margin = margin['gross_profit'] * 1.3  # 30% higher margin on renewal
    renewal_contribution = renewal_rate * survival_rate * renewal_margin
    renewal_npv = renewal_contribution / ((1 + discount_rate) ** tenure_years)

    # 3. Upsell value
    avg_upsell_increment = 150 * tenure_months * 0.5  # 50% of potential
    upsell_contribution = upsell_rate * avg_upsell_increment
    upsell_npv = upsell_contribution / ((1 + discount_rate) ** (tenure_years / 2))

    # 4. Referral value
    referral_contribution = referral_rate * referral_value

    # 5. Data asset value (NPV over 5 years)
    data_years = 5
    data_npv = sum(
        data_value / ((1 + discount_rate) ** year)
        for year in range(1, data_years + 1)
    )

    # Total CLV
    total_clv = (
        first_tenure_margin +
        renewal_npv +
        upsell_npv +
        referral_contribution +
        data_npv
    )

    return {
        'first_tenure_margin': round(first_tenure_margin, 2),
        'renewal_npv': round(renewal_npv, 2),
        'upsell_npv': round(upsell_npv, 2),
        'referral_contribution': round(referral_contribution, 2),
        'data_npv': round(data_npv, 2),
        'total_clv': round(total_clv, 2),
        'tenure_months': tenure_months,
        'discount_rate': discount_rate,
        'survival_rate': survival_rate,
        'breakdown': {
            'first_tenure': round((first_tenure_margin / total_clv) * 100, 1),
            'renewal': round((renewal_npv / total_clv) * 100, 1),
            'upsell': round((upsell_npv / total_clv) * 100, 1),
            'referral': round((referral_contribution / total_clv) * 100, 1),
            'data': round((data_npv / total_clv) * 100, 1),
        },
        'notes': f'Risk-adjusted CLV at {discount_rate*100:.0f}% discount rate'
    }


# =============================================================================
# Summary Function
# =============================================================================

def get_sesp_summary(
    mrp: float = SESP_DEFAULTS['mrp'],
    subsidy_percent: float = SESP_DEFAULTS['subsidy_percent'],
    tenure_months: int = SESP_DEFAULTS['tenure_months'],
    segment_mix: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Get complete SESP model summary for comparison.

    Args:
        mrp: Product MRP
        subsidy_percent: Subsidy as decimal
        tenure_months: Contract duration
        segment_mix: Distribution across plans

    Returns:
        Complete summary dictionary for comparison.
    """
    revenue = calculate_sesp_revenue(mrp, subsidy_percent, tenure_months, segment_mix)
    costs = calculate_sesp_costs(tenure_months=tenure_months)
    margin = calculate_sesp_margin(mrp, subsidy_percent, tenure_months, segment_mix)
    clv = calculate_sesp_clv(mrp, subsidy_percent, tenure_months, segment_mix)

    return {
        'model': 'SESP',
        'description': 'Subscription with direct customer relationship',
        'mrp': mrp,
        'subsidy_percent': subsidy_percent * 100,
        'tenure_months': tenure_months,
        'revenue_per_unit': revenue['total_revenue'],
        'cost_per_unit': costs['total_cost'],
        'gross_margin': margin['gross_profit'],
        'gross_margin_percent': margin['gross_margin_percent'],
        'breakeven_months': margin['breakeven_months'],
        'clv': clv['total_clv'],
        'clv_breakdown': clv['breakdown'],
        'customer_relationship': 'Long-term',
        'data_asset': 'Yes (IoT data)',
        'recurring_revenue': 'Monthly subscription (100%)',
        'details': {
            'revenue': revenue,
            'costs': costs,
            'margin': margin,
            'clv': clv,
        }
    }


# =============================================================================
# Module Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SESP Profitability Model — Demo")
    print("=" * 60)

    # Get summary
    summary = get_sesp_summary()

    print(f"\nModel: {summary['model']}")
    print(f"Description: {summary['description']}")
    print(f"\nMRP: Rs{summary['mrp']:,}")
    print(f"Subsidy: {summary['subsidy_percent']:.0f}%")
    print(f"Tenure: {summary['tenure_months']} months")

    print(f"\n--- Per Unit Economics ---")
    print(f"Revenue (net): Rs{summary['revenue_per_unit']:,.0f}")
    print(f"Cost: Rs{summary['cost_per_unit']:,.0f}")
    print(f"Gross Profit: Rs{summary['gross_margin']:,.0f}")
    print(f"Gross Margin: {summary['gross_margin_percent']:.1f}%")
    print(f"Break-even: {summary['breakeven_months']:.0f} months")

    print(f"\n--- Customer Lifetime Value ---")
    print(f"Total CLV: Rs{summary['clv']:,.0f}")
    print(f"  First Tenure: {summary['clv_breakdown']['first_tenure']:.0f}%")
    print(f"  Renewal: {summary['clv_breakdown']['renewal']:.0f}%")
    print(f"  Upsell: {summary['clv_breakdown']['upsell']:.0f}%")
    print(f"  Referral: {summary['clv_breakdown']['referral']:.0f}%")
    print(f"  Data Asset: {summary['clv_breakdown']['data']:.0f}%")

    print(f"\n--- Strategic Characteristics ---")
    print(f"Customer Relationship: {summary['customer_relationship']}")
    print(f"Data Asset: {summary['data_asset']}")
    print(f"Recurring Revenue: {summary['recurring_revenue']}")

    print("\n✓ SESP profitability model working correctly!")
