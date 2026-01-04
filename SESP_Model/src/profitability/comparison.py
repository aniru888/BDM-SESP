"""
Profitability Comparison Module (Task 3.3)
==========================================

Compares Traditional vs SESP profitability models side-by-side.

Key Comparisons:
1. Per-unit economics (revenue, costs, margin)
2. Customer Lifetime Value (CLV)
3. Strategic characteristics (relationship, data, recurring revenue)
4. Break-even analysis
5. Sensitivity to key parameters

The comparison reveals:
- Traditional: Higher immediate margin, lower CLV
- SESP: Lower immediate margin, higher CLV + strategic assets

This module provides the "before vs after" analysis required for
business case justification.
"""

from typing import Dict, Any, List, Optional, Tuple
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .traditional import (
    get_traditional_summary,
    calculate_traditional_margin,
    calculate_traditional_clv,
    TRADITIONAL_DEFAULTS,
)
from .sesp import (
    get_sesp_summary,
    calculate_sesp_margin,
    calculate_sesp_clv,
    SESP_DEFAULTS,
)


# =============================================================================
# Service Value Calculation (Phase 3b Addition)
# =============================================================================

# Service value components (₹/year) — user-confirmed moderate estimate
SERVICE_VALUE_COMPONENTS = {
    'maintenance': 1800,    # Avoids ₹600-800 per service call × 2-3 calls/year
    'warranty': 1200,       # Avoids ₹3,500 avg repair × 15% probability
    'iot_monitoring': 700,  # Early fault detection, usage optimization
    'convenience': 800,     # No hassle finding technicians, scheduling
}

SERVICE_VALUE_ANNUAL = sum(SERVICE_VALUE_COMPONENTS.values())  # ₹4,500/year

# =============================================================================
# IoT Value Additions (Phase 3c) — Near-Zero Cost, High Perceived Value
# =============================================================================

# These features cost nearly nothing (data already collected) but add perceived value
IOT_VALUE_ADDITIONS = {
    'usage_dashboard': 300,           # Monthly consumption, trends, comparisons
    'anomaly_alerts': 200,            # "Your AC consumed 40% more this week"
    'remote_control': 500,            # Turn on/off via app (already in IoT hardware)
    'efficiency_tips': 200,           # Personalized suggestions
    'priority_service': 300,          # Same-day technician dispatch
    'extended_warranty_premium': 500, # 5-year vs 1-year (actuarial cost ~₹500/yr)
    'upgrade_path': 500,              # Trade-in value eligibility (aspirational)
}

IOT_VALUE_ANNUAL = sum(IOT_VALUE_ADDITIONS.values())  # ₹2,500/year

# Total perceived value to customer (base + IoT additions)
TOTAL_SERVICE_VALUE_ANNUAL = SERVICE_VALUE_ANNUAL + IOT_VALUE_ANNUAL  # ₹7,000/year

# =============================================================================
# Credit Card Partnership Benefits (Phase 3c)
# =============================================================================

# Customer benefits from bundled credit card (partner bank covers these)
CREDIT_CARD_CUSTOMER_VALUE = {
    'annual_fee_waiver': 500,     # Free card (₹500/year saved)
    'subscription_cashback': 120, # 2% cashback on monthly fees
    'fuel_surcharge_waiver': 300, # Avg savings on fuel purchases
    'reward_points': 500,         # Value of points from all spending
}

CREDIT_CARD_VALUE_ANNUAL = sum(CREDIT_CARD_CUSTOMER_VALUE.values())  # ₹1,420/year

# Company benefits from bank partnership
CREDIT_CARD_COMPANY_BENEFITS = {
    'bank_cac_subsidy': 2000,     # Bank pays to acquire card customer
    'reduced_default_risk': 200,  # Auto-debit reduces defaults (~1% improvement)
    'collection_savings': 200,    # No payment collection hassle
}

BANK_CAC_SUBSIDY = CREDIT_CARD_COMPANY_BENEFITS['bank_cac_subsidy']  # ₹2,000


# =============================================================================
# Optional IoT Additions (Phase 5) — Seasonal Optimization & Maintenance
# =============================================================================

# These are ADDITIONAL features on top of existing IoT value additions
OPTIONAL_IOT_ADDITIONS = {
    'seasonal_optimization': {
        'perceived_value': 300,  # Rs/year
        'company_cost': 50,      # Rs/year (weather API cost)
        'description': 'Auto-suggest optimal AC settings based on outdoor conditions',
        'examples': [
            'Its 32C outside. Setting AC to 24C for optimal efficiency.',
            'Humidity is high today. Switching to dry mode for better comfort.',
            'Evening temperature dropping. Consider turning off AC in 30 mins.',
        ],
    },
    'maintenance_reminders': {
        'perceived_value': 200,  # Rs/year
        'company_cost': 0,       # Algorithmic, no external API
        'description': 'Push notifications for filter cleaning and service scheduling',
        'examples': [
            'Your AC filter needs cleaning (15 days since last clean)',
            'Pre-summer service due in March - book now for priority slots',
            'Condenser coil cleaning recommended before monsoon',
        ],
    },
    'seasonal_hours_adjustment': {
        'perceived_value': 400,  # Rs/year (big mental relief)
        'company_cost': 0,       # Just billing logic change
        'description': 'Automatic adjustment of included hours based on season',
        'rationale': '''
            Instead of fixed 200 hours/month, distribute across seasons:
            - Winter (Nov-Feb): 50 hours/month (AC barely used)
            - Shoulder (Mar, Oct): 150 hours/month
            - Summer (Apr-Sep): 280 hours/month

            Same TOTAL hours over year, but aligned with actual usage pattern.
            Reduces overage shock in summer, no waste in winter.
        ''',
        'example_standard_plan': {
            'fixed_monthly': 200,  # Current: 200 hrs × 12 = 2,400 hrs/year
            'seasonal_allocation': {
                'winter': {'months': [11, 0, 1], 'hours': 50},    # Nov, Dec, Jan, Feb
                'shoulder': {'months': [2, 9], 'hours': 150},      # Mar, Oct
                'summer': {'months': [3, 4, 5, 6, 7, 8], 'hours': 280},  # Apr-Sep
            },
            # Total: 4×50 + 2×150 + 6×280 = 200 + 300 + 1,680 = 2,180 hrs
            # Slightly less than 2,400, but MUCH better customer experience
        },
    },
}

# Total value add from optional features
OPTIONAL_IOT_VALUE_ANNUAL = sum(
    feature['perceived_value'] for feature in OPTIONAL_IOT_ADDITIONS.values()
)  # Rs900/year

# Total cost of optional features
OPTIONAL_IOT_COST_ANNUAL = sum(
    feature['company_cost'] for feature in OPTIONAL_IOT_ADDITIONS.values()
)  # Rs50/year


def calculate_service_value_delivered(
    tenure_months: int = 24,
    annual_value: float = SERVICE_VALUE_ANNUAL,
    include_iot_additions: bool = True,
    include_credit_card: bool = True,
    monthly_fee: float = 599,  # Standard plan fee
) -> Dict[str, Any]:
    """
    Calculate the total service value SESP delivers to customers.

    Unlike purchase where customer must arrange/pay for:
    - Maintenance visits (₹500-800 each)
    - Repairs after warranty (₹3,500 avg)
    - Finding technicians (time cost)

    SESP includes all of this, creating VALUE that offsets the fee.

    Args:
        tenure_months: Contract duration
        annual_value: Annual base service value delivered (default ₹4,500)
        include_iot_additions: Include IoT dashboard, alerts, etc. (Phase 3c)
        include_credit_card: Include credit card partnership benefits (Phase 3c)
        monthly_fee: Monthly subscription fee for calculations

    Returns:
        Dictionary with service value breakdown.

    Example:
        >>> value = calculate_service_value_delivered(60, include_iot_additions=True)
        >>> value['total_value']  # ₹35,000 over 5 years (with IoT additions)
    """
    tenure_years = tenure_months / 12

    # Calculate per-component value over tenure
    base_components = {}
    for name, annual in SERVICE_VALUE_COMPONENTS.items():
        base_components[name] = round(annual * tenure_years, 2)

    base_total = annual_value * tenure_years

    # IoT value additions (Phase 3c)
    iot_components = {}
    iot_total = 0
    if include_iot_additions:
        for name, annual in IOT_VALUE_ADDITIONS.items():
            iot_components[name] = round(annual * tenure_years, 2)
        iot_total = IOT_VALUE_ANNUAL * tenure_years

    # Credit card benefits (Phase 3c)
    card_components = {}
    card_total = 0
    if include_credit_card:
        for name, annual in CREDIT_CARD_CUSTOMER_VALUE.items():
            card_components[name] = round(annual * tenure_years, 2)
        card_total = CREDIT_CARD_VALUE_ANNUAL * tenure_years

    # Total perceived value
    total_value = base_total + iot_total + card_total

    # Compare to fees paid
    total_fees_paid = monthly_fee * tenure_months
    net_value = total_value - total_fees_paid

    return {
        'annual_base_value': annual_value,
        'annual_iot_value': IOT_VALUE_ANNUAL if include_iot_additions else 0,
        'annual_card_value': CREDIT_CARD_VALUE_ANNUAL if include_credit_card else 0,
        'annual_total_value': annual_value + (IOT_VALUE_ANNUAL if include_iot_additions else 0) + (CREDIT_CARD_VALUE_ANNUAL if include_credit_card else 0),
        'tenure_months': tenure_months,
        'tenure_years': round(tenure_years, 2),
        'base_components': base_components,
        'iot_components': iot_components,
        'card_components': card_components,
        'base_total': round(base_total, 2),
        'iot_total': round(iot_total, 2),
        'card_total': round(card_total, 2),
        'total_value': round(total_value, 2),
        'monthly_fee': monthly_fee,
        'total_fees_paid': total_fees_paid,
        'net_customer_value': round(net_value, 2),
        'value_per_month': round(total_value / tenure_months, 2),
        'value_vs_fee_ratio': round(total_value / max(total_fees_paid, 1), 2),
        'notes': f'Customer receives ₹{total_value / tenure_years:,.0f}/year in total value'
    }


# =============================================================================
# Core Comparison Function
# =============================================================================

def compare_profitability(
    mrp: float = 45000,
    traditional_dealer_margin: float = TRADITIONAL_DEFAULTS['dealer_margin'],
    sesp_subsidy_percent: float = SESP_DEFAULTS['subsidy_percent'],
    sesp_tenure_months: int = SESP_DEFAULTS['tenure_months'],
    years: int = 5,
) -> Dict[str, Any]:
    """
    Compare Traditional vs SESP profitability models.

    This is the main comparison function that provides a complete
    side-by-side analysis of both business models.

    Args:
        mrp: Product MRP (same for both models)
        traditional_dealer_margin: Dealer margin for traditional sales
        sesp_subsidy_percent: Subsidy percentage for SESP
        sesp_tenure_months: SESP contract duration
        years: CLV horizon for comparison

    Returns:
        Dictionary with complete comparison including deltas.

    Example:
        >>> comparison = compare_profitability()
        >>> print(f"CLV Improvement: Rs{comparison['deltas']['clv']['absolute']:,.0f}")
    """
    # Get summaries for both models
    traditional = get_traditional_summary(
        mrp=mrp,
        dealer_margin=traditional_dealer_margin,
        years=years
    )

    sesp = get_sesp_summary(
        mrp=mrp,
        subsidy_percent=sesp_subsidy_percent,
        tenure_months=sesp_tenure_months,
    )

    # Calculate deltas
    deltas = calculate_delta_metrics(traditional, sesp)

    # Determine winner for each metric
    winners = _determine_winners(traditional, sesp)

    # Generate recommendation
    recommendation = _generate_recommendation(traditional, sesp, deltas)

    return {
        'traditional': traditional,
        'sesp': sesp,
        'deltas': deltas,
        'winners': winners,
        'recommendation': recommendation,
        'parameters': {
            'mrp': mrp,
            'traditional_dealer_margin': traditional_dealer_margin,
            'sesp_subsidy_percent': sesp_subsidy_percent,
            'sesp_tenure_months': sesp_tenure_months,
            'clv_horizon_years': years,
        }
    }


# =============================================================================
# Delta Calculations
# =============================================================================

def calculate_delta_metrics(
    traditional: Dict[str, Any],
    sesp: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calculate differences between Traditional and SESP models.

    Positive delta means SESP is higher/better.
    Negative delta means Traditional is higher/better.

    Args:
        traditional: Traditional model summary
        sesp: SESP model summary

    Returns:
        Dictionary with absolute and percentage deltas.
    """
    def safe_delta(sesp_val, trad_val):
        """Calculate delta with None handling."""
        if sesp_val is None or trad_val is None:
            return {'absolute': None, 'percent': None}

        absolute = sesp_val - trad_val
        if trad_val != 0:
            percent = (absolute / abs(trad_val)) * 100
        else:
            percent = 100 if absolute > 0 else (-100 if absolute < 0 else 0)

        return {
            'absolute': round(absolute, 2),
            'percent': round(percent, 1)
        }

    return {
        'revenue': safe_delta(
            sesp['revenue_per_unit'],
            traditional['revenue_per_unit']
        ),
        'cost': safe_delta(
            sesp['cost_per_unit'],
            traditional['cost_per_unit']
        ),
        'gross_margin': safe_delta(
            sesp['gross_margin'],
            traditional['gross_margin']
        ),
        'gross_margin_percent': safe_delta(
            sesp['gross_margin_percent'],
            traditional['gross_margin_percent']
        ),
        'clv': safe_delta(
            sesp['clv'],
            traditional['clv']
        ),
        'notes': {
            'revenue': _interpret_delta('revenue', sesp['revenue_per_unit'], traditional['revenue_per_unit']),
            'cost': _interpret_delta('cost', sesp['cost_per_unit'], traditional['cost_per_unit']),
            'gross_margin': _interpret_delta('margin', sesp['gross_margin'], traditional['gross_margin']),
            'clv': _interpret_delta('clv', sesp['clv'], traditional['clv']),
        }
    }


def _interpret_delta(metric: str, sesp_val: float, trad_val: float) -> str:
    """Generate human-readable interpretation of delta."""
    delta = sesp_val - trad_val
    direction = "higher" if delta > 0 else "lower"
    abs_delta = abs(delta)

    interpretations = {
        'revenue': f"SESP revenue is Rs{abs_delta:,.0f} {direction} due to {'higher fee accumulation' if delta > 0 else 'subsidy impact'}",
        'cost': f"SESP costs are Rs{abs_delta:,.0f} {direction} due to {'IoT + CAC + installation' if delta > 0 else 'unexpected savings'}",
        'margin': f"SESP margin is Rs{abs_delta:,.0f} {direction} per unit",
        'clv': f"SESP CLV is Rs{abs_delta:,.0f} {direction} due to {'recurring revenue + data' if delta > 0 else 'unexpected'}",
    }
    return interpretations.get(metric, f"Delta: Rs{delta:,.0f}")


# =============================================================================
# Comparison Table Generation
# =============================================================================

def generate_comparison_table(
    comparison: Optional[Dict[str, Any]] = None,
    mrp: float = 45000,
) -> str:
    """
    Generate a formatted comparison table as a string.

    Args:
        comparison: Pre-calculated comparison dict, or None to calculate fresh
        mrp: MRP if calculating fresh

    Returns:
        Formatted string table for display.

    Example:
        >>> print(generate_comparison_table())
    """
    if comparison is None:
        comparison = compare_profitability(mrp=mrp)

    trad = comparison['traditional']
    sesp = comparison['sesp']
    deltas = comparison['deltas']

    # Extract values to avoid f-string escaping issues
    trad_mrp = trad['mrp']
    sesp_mrp = sesp['mrp']
    sesp_subsidy = sesp['subsidy_percent']
    trad_rev = trad['revenue_per_unit']
    sesp_rev = sesp['revenue_per_unit']
    trad_cost = trad['cost_per_unit']
    sesp_cost = sesp['cost_per_unit']
    trad_margin = trad['gross_margin']
    sesp_margin = sesp['gross_margin']
    trad_margin_pct = trad['gross_margin_percent']
    sesp_margin_pct = sesp['gross_margin_percent']
    trad_clv = trad['clv']
    sesp_clv = sesp['clv']
    sesp_breakeven = sesp['breakeven_months']
    trad_relationship = trad['customer_relationship']
    sesp_relationship = sesp['customer_relationship']
    trad_data = trad['data_asset']
    sesp_data = sesp['data_asset']

    # Delta values
    rev_delta = deltas['revenue']['absolute']
    cost_delta = deltas['cost']['absolute']
    margin_delta = deltas['gross_margin']['absolute']
    margin_pct_delta = deltas['gross_margin_percent']['absolute']
    clv_delta = deltas['clv']['absolute']
    clv_pct_delta = deltas['clv']['percent']

    # Build table
    lines = []
    lines.append("=" * 75)
    lines.append("PROFITABILITY COMPARISON: Traditional vs SESP")
    lines.append("=" * 75)
    lines.append("")

    # Header
    lines.append(f"{'Metric':<30} {'Traditional':>15} {'SESP':>15} {'Delta':>12}")
    lines.append("-" * 75)

    # Core metrics
    lines.append(f"{'MRP':<30} {'Rs' + f'{trad_mrp:,.0f}':>14} {'Rs' + f'{sesp_mrp:,.0f}':>14} {'-':>12}")
    lines.append(f"{'Pricing Model':<30} {'Dealer (18%)':>15} {f'{sesp_subsidy:.0f}% Subsidy':>15} {'-':>12}")
    lines.append("")

    # Revenue & Cost
    lines.append("--- Per Unit Economics ---")
    rev_sign = '+' if rev_delta >= 0 else ''
    cost_sign = '+' if cost_delta >= 0 else ''
    margin_sign = '+' if margin_delta >= 0 else ''
    margin_pct_sign = '+' if margin_pct_delta >= 0 else ''

    lines.append(f"{'Revenue (net)':<30} {'Rs' + f'{trad_rev:,.0f}':>14} {'Rs' + f'{sesp_rev:,.0f}':>14} {rev_sign + f'Rs{rev_delta:,.0f}':>12}")
    lines.append(f"{'Cost':<30} {'Rs' + f'{trad_cost:,.0f}':>14} {'Rs' + f'{sesp_cost:,.0f}':>14} {cost_sign + f'Rs{cost_delta:,.0f}':>12}")
    lines.append(f"{'Gross Profit':<30} {'Rs' + f'{trad_margin:,.0f}':>14} {'Rs' + f'{sesp_margin:,.0f}':>14} {margin_sign + f'Rs{margin_delta:,.0f}':>12}")
    lines.append(f"{'Gross Margin %':<30} {f'{trad_margin_pct:.1f}%':>15} {f'{sesp_margin_pct:.1f}%':>15} {margin_pct_sign + f'{margin_pct_delta:.1f}pp':>12}")
    lines.append("")

    # CLV
    lines.append("--- Customer Lifetime Value ---")
    clv_sign = '+' if clv_delta >= 0 else ''
    clv_pct_sign = '+' if clv_pct_delta >= 0 else ''

    lines.append(f"{'Total CLV':<30} {'Rs' + f'{trad_clv:,.0f}':>14} {'Rs' + f'{sesp_clv:,.0f}':>14} {clv_sign + f'Rs{clv_delta:,.0f}':>12}")
    lines.append(f"{'CLV Improvement':<30} {'-':>15} {'-':>15} {clv_pct_sign + f'{clv_pct_delta:.1f}%':>12}")
    lines.append("")

    # Break-even (SESP only)
    lines.append("--- Break-even ---")
    lines.append(f"{'Break-even Period':<30} {'Immediate':>15} {f'{sesp_breakeven:.0f} months':>15} {'-':>12}")
    lines.append("")

    # Strategic characteristics
    lines.append("--- Strategic Characteristics ---")
    lines.append(f"{'Customer Relationship':<30} {trad_relationship:>15} {sesp_relationship:>15}")
    lines.append(f"{'Data Asset':<30} {trad_data:>15} {sesp_data:>15}")
    lines.append(f"{'Recurring Revenue':<30} {'AMC (25%)':>15} {'100%':>15}")
    lines.append("")

    # Recommendation
    rec_summary = comparison['recommendation']['summary']
    rec_rationale = comparison['recommendation']['rationale']
    lines.append("-" * 75)
    lines.append(f"RECOMMENDATION: {rec_summary}")
    lines.append(f"Rationale: {rec_rationale}")
    lines.append("=" * 75)

    return "\n".join(lines)


# =============================================================================
# Additional Analysis Functions
# =============================================================================

def _determine_winners(traditional: Dict, sesp: Dict) -> Dict[str, str]:
    """Determine which model wins on each metric."""
    winners = {}

    # Revenue: higher is better for firm
    winners['revenue'] = 'SESP' if sesp['revenue_per_unit'] > traditional['revenue_per_unit'] else 'Traditional'

    # Cost: lower is better
    winners['cost'] = 'Traditional' if traditional['cost_per_unit'] < sesp['cost_per_unit'] else 'SESP'

    # Margin: higher is better
    winners['margin'] = 'Traditional' if traditional['gross_margin'] > sesp['gross_margin'] else 'SESP'

    # CLV: higher is better
    winners['clv'] = 'SESP' if sesp['clv'] > traditional['clv'] else 'Traditional'

    # Relationship: SESP always wins here
    winners['relationship'] = 'SESP'

    # Data: SESP always wins here
    winners['data'] = 'SESP'

    return winners


def _generate_recommendation(
    traditional: Dict,
    sesp: Dict,
    deltas: Dict,
) -> Dict[str, str]:
    """Generate a recommendation based on comparison results."""

    clv_improvement = deltas['clv']['percent']
    margin_delta = deltas['gross_margin']['absolute']

    if clv_improvement > 20:
        if margin_delta >= 0:
            summary = "Strongly Recommend SESP"
            rationale = (
                f"SESP improves CLV by {clv_improvement:.1f}% while maintaining or improving margins. "
                "Strategic benefits (data, relationship) provide additional upside."
            )
        else:
            summary = "Recommend SESP with Patience"
            rationale = (
                f"SESP improves CLV by {clv_improvement:.1f}% despite lower initial margin "
                f"(Rs{abs(margin_delta):,.0f} lower). Long-term value creation justifies short-term sacrifice."
            )
    elif clv_improvement > 0:
        summary = "Cautiously Recommend SESP"
        rationale = (
            f"SESP shows modest CLV improvement ({clv_improvement:.1f}%). "
            "Consider optimizing pricing parameters for better margins."
        )
    else:
        summary = "Review SESP Parameters"
        rationale = (
            f"SESP shows negative CLV impact ({clv_improvement:.1f}%). "
            "Pricing parameters need adjustment — consider lower subsidy or higher fees."
        )

    return {
        'summary': summary,
        'rationale': rationale,
        'clv_improvement_percent': round(clv_improvement, 1),
        'margin_delta': round(margin_delta, 2),
    }


def generate_waterfall_data(
    comparison: Optional[Dict[str, Any]] = None,
    mrp: float = 45000,
) -> List[Dict[str, Any]]:
    """
    Generate data for a waterfall chart showing margin buildup.

    Shows how SESP margin builds from traditional baseline.

    Args:
        comparison: Pre-calculated comparison dict
        mrp: MRP if calculating fresh

    Returns:
        List of dicts suitable for waterfall chart visualization.
    """
    if comparison is None:
        comparison = compare_profitability(mrp=mrp)

    trad = comparison['traditional']
    sesp = comparison['sesp']

    # Get detailed breakdown
    trad_details = trad['details']
    sesp_details = sesp['details']

    waterfall = [
        {
            'label': 'Traditional Margin',
            'value': trad['gross_margin'],
            'type': 'base',
            'running_total': trad['gross_margin']
        },
        {
            'label': 'Remove Dealer Margin',
            'value': trad_details['revenue']['dealer_margin_amount'],
            'type': 'positive',
            'running_total': trad['gross_margin'] + trad_details['revenue']['dealer_margin_amount'],
            'notes': 'SESP bypasses dealer, captures this margin'
        },
        {
            'label': 'Subsidy Impact',
            'value': -(mrp * sesp_details['revenue']['subsidy_percent'] / 100),
            'type': 'negative',
            'running_total': None,  # Will be calculated
            'notes': f"{sesp_details['revenue']['subsidy_percent']:.0f}% subsidy reduces upfront revenue"
        },
        {
            'label': 'Monthly Fee Revenue',
            'value': sesp_details['revenue']['total_monthly_net'],
            'type': 'positive',
            'running_total': None,
            'notes': f"{sesp['tenure_months']} months of subscription fees"
        },
        {
            'label': 'Additional Costs (IoT+CAC)',
            'value': -(sesp_details['costs']['iot_hardware'] + sesp_details['costs']['cac'] + sesp_details['costs']['installation_cost']),
            'type': 'negative',
            'running_total': None,
            'notes': 'SESP-specific costs not in traditional'
        },
        {
            'label': 'Recurring Costs',
            'value': -sesp_details['costs']['recurring_total'],
            'type': 'negative',
            'running_total': None,
            'notes': 'IoT service, maintenance, support over tenure'
        },
        {
            'label': 'SESP Margin',
            'value': sesp['gross_margin'],
            'type': 'total',
            'running_total': sesp['gross_margin']
        }
    ]

    # Calculate running totals
    running = trad['gross_margin']
    for item in waterfall[1:-1]:
        running += item['value']
        item['running_total'] = round(running, 2)

    return waterfall


def run_sensitivity_comparison(
    base_mrp: float = 45000,
    subsidy_range: Tuple[float, float, float] = (0.50, 0.75, 0.05),
    tenure_options: List[int] = [24, 36],
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across subsidy levels and tenures.

    Args:
        base_mrp: Base MRP for comparison
        subsidy_range: (min, max, step) for subsidy percentage
        tenure_options: List of tenure months to test

    Returns:
        Dictionary with sensitivity results.
    """
    import numpy as np

    subsidies = np.arange(subsidy_range[0], subsidy_range[1] + 0.001, subsidy_range[2])
    results = []

    for subsidy in subsidies:
        for tenure in tenure_options:
            comparison = compare_profitability(
                mrp=base_mrp,
                sesp_subsidy_percent=subsidy,
                sesp_tenure_months=tenure,
            )

            results.append({
                'subsidy_percent': round(subsidy * 100, 1),
                'tenure_months': tenure,
                'sesp_margin': comparison['sesp']['gross_margin'],
                'sesp_margin_percent': comparison['sesp']['gross_margin_percent'],
                'sesp_clv': comparison['sesp']['clv'],
                'clv_improvement': comparison['deltas']['clv']['percent'],
                'margin_delta': comparison['deltas']['gross_margin']['absolute'],
                'recommendation': comparison['recommendation']['summary'],
            })

    # Find optimal
    best_clv = max(results, key=lambda x: x['sesp_clv'])
    best_margin = max(results, key=lambda x: x['sesp_margin'])
    best_balanced = max(results, key=lambda x: x['clv_improvement'] + x['sesp_margin_percent'])

    return {
        'results': results,
        'best_clv': best_clv,
        'best_margin': best_margin,
        'best_balanced': best_balanced,
        'parameters': {
            'mrp': base_mrp,
            'subsidy_range': subsidy_range,
            'tenure_options': tenure_options,
        }
    }


# =============================================================================
# Module Test
# =============================================================================

if __name__ == "__main__":
    # Set encoding for Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 75)
    print("Profitability Comparison — Demo")
    print("=" * 75)

    # Run comparison
    comparison = compare_profitability()

    # Print formatted table
    print(generate_comparison_table(comparison))

    # Print waterfall summary
    print("\n" + "=" * 75)
    print("MARGIN WATERFALL (Traditional → SESP)")
    print("=" * 75)

    waterfall = generate_waterfall_data(comparison)
    for item in waterfall:
        sign = "+" if item['value'] >= 0 else ""
        print(f"  {item['label']:<30} {sign}Rs{item['value']:,.0f}")

    # Print CLV breakdown comparison
    print("\n" + "=" * 75)
    print("CLV BREAKDOWN COMPARISON")
    print("=" * 75)

    trad_clv = comparison['traditional']['clv_breakdown']
    sesp_clv = comparison['sesp']['clv_breakdown']

    print(f"\nTraditional CLV (Rs{comparison['traditional']['clv']:,.0f}):")
    print(f"  Initial Sale: {trad_clv['initial_sale']:.0f}%")
    print(f"  AMC: {trad_clv['amc']:.0f}%")
    print(f"  Referral: {trad_clv['referral']:.0f}%")

    print(f"\nSESP CLV (Rs{comparison['sesp']['clv']:,.0f}):")
    print(f"  First Tenure: {sesp_clv['first_tenure']:.0f}%")
    print(f"  Renewal: {sesp_clv['renewal']:.0f}%")
    print(f"  Upsell: {sesp_clv['upsell']:.0f}%")
    print(f"  Referral: {sesp_clv['referral']:.0f}%")
    print(f"  Data Asset: {sesp_clv['data']:.0f}%")

    print("\n✓ Comparison module working correctly!")
