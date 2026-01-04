"""
Sensitivity Analysis Module (Phase 3b)
======================================

Analyzes sensitivity of profitability to key parameters:
1. Tenure (24-48 months) - Longer tenure spreads fixed costs
2. Dealer Margin (12-18%) - Lower margin affects Traditional baseline

Also generates parallel BEFORE vs AFTER comparison showing how
optimized parameters improve SESP viability.

Key Finding from Phase 3 Core:
- Current parameters: Traditional margin Rs851 (2.7%), SESP margin Rs-16,785 (-62.4%)
- SESP is deeply unprofitable under current assumptions
- This module tests improvements to find viable parameter combinations

User-Confirmed Values (2026-01-04):
- Dealer margin: 12% (IRL is lower than 18% default)
- Tenure: Test 36m, 42m, 48m
- Service value: Rs 4,500/year (included in comparison)
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
from .comparison import (
    compare_profitability,
    calculate_delta_metrics,
    calculate_service_value_delivered,
    SERVICE_VALUE_ANNUAL,
    IOT_VALUE_ANNUAL,
    CREDIT_CARD_VALUE_ANNUAL,
    BANK_CAC_SUBSIDY,
    TOTAL_SERVICE_VALUE_ANNUAL,
)


# =============================================================================
# Configuration
# =============================================================================

# Current "BEFORE" parameters (baseline)
BEFORE_PARAMS = {
    'dealer_margin': 0.18,        # 18% - current default
    'tenure_months': 24,          # 24 months - current default
    'subsidy_percent': 0.65,      # 65% subsidy
    'monthly_fee': 649,           # Moderate plan
    'service_value_included': False,
}

# Optimized "AFTER" parameters (Phase 3c: 60-month tenure, 50% subsidy, tiered pricing)
AFTER_PARAMS = {
    'dealer_margin': 0.12,        # 12% - user confirmed IRL is lower
    'tenure_months': 60,          # 60 months (5 years) - ACs are durable
    'subsidy_percent': 0.50,      # 50% "Half Price" - catchy marketing
    'monthly_fee': 599,           # Standard plan (tiered: Lite 449, Standard 599, Premium 799)
    'service_value_included': True,
    'include_iot_additions': True,
    'include_credit_card': True,
    'bank_cac_subsidy': 2000,     # Bank pays to acquire card customer
}

# Tenure test range
TENURE_OPTIONS = [24, 30, 36, 42, 48, 60]

# Dealer margin test range
DEALER_MARGIN_OPTIONS = [0.12, 0.14, 0.16, 0.18]

# Subsidy test range (Phase 3c)
SUBSIDY_OPTIONS = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65]

# Tiered pricing plans (Phase 3c - Bucket Model)
TIERED_PLANS = {
    'lite': {
        'monthly_fee': 449,
        'hours_included': 100,
        'overage_per_hour': 6,
        'max_overage': 150,
        'segment_share': 0.30,  # 30% of customers
        'target_segment': 'Light users',
    },
    'standard': {
        'monthly_fee': 599,
        'hours_included': 200,
        'overage_per_hour': 5,
        'max_overage': 200,
        'segment_share': 0.50,  # 50% of customers
        'target_segment': 'Moderate users',
    },
    'premium': {
        'monthly_fee': 799,
        'hours_included': 350,
        'overage_per_hour': 0,  # Unlimited
        'max_overage': 0,
        'segment_share': 0.20,  # 20% of customers
        'target_segment': 'Heavy users',
    },
}


# =============================================================================
# Tenure Sensitivity Analysis
# =============================================================================

def run_tenure_sensitivity(
    mrp: float = 45000,
    subsidy_percent: float = SESP_DEFAULTS['subsidy_percent'],
    dealer_margin: float = 0.12,  # Use optimized dealer margin
    tenure_options: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across different tenure lengths.

    Why Tenure Matters:
    - Upfront costs (manufacturing, IoT, CAC) are FIXED
    - Longer tenure = more months of fee revenue
    - Spreads fixed costs over more payments
    - Monthly fee revenue compounds over time

    Args:
        mrp: Product MRP
        subsidy_percent: SESP subsidy level
        dealer_margin: Traditional dealer margin (for comparison)
        tenure_options: List of tenure months to test

    Returns:
        Dictionary with sensitivity results and analysis.

    Example:
        >>> results = run_tenure_sensitivity()
        >>> for r in results['results']:
        ...     print(f"{r['tenure']}m: Margin Rs{r['sesp_margin']:,.0f} ({r['sesp_margin_percent']:.1f}%)")
    """
    if tenure_options is None:
        tenure_options = TENURE_OPTIONS

    results = []

    # Get traditional baseline (fixed)
    traditional = get_traditional_summary(
        mrp=mrp,
        dealer_margin=dealer_margin,
    )

    for tenure in tenure_options:
        # Calculate SESP for this tenure
        sesp = get_sesp_summary(
            mrp=mrp,
            subsidy_percent=subsidy_percent,
            tenure_months=tenure,
        )

        # Calculate service value for this tenure
        service_value = calculate_service_value_delivered(tenure_months=tenure)

        # Calculate comparison metrics
        deltas = calculate_delta_metrics(traditional, sesp)

        # Monthly recurring metrics
        sesp_details = sesp['details']
        monthly_revenue = sesp_details['revenue']['effective_monthly_net']
        monthly_recurring_cost = sesp_details['costs']['recurring_total'] / tenure
        monthly_contribution = monthly_revenue - monthly_recurring_cost

        results.append({
            'tenure': tenure,
            'tenure_years': tenure / 12,
            # Traditional (constant for comparison)
            'trad_margin': traditional['gross_margin'],
            'trad_margin_percent': traditional['gross_margin_percent'],
            'trad_clv': traditional['clv'],
            # SESP metrics
            'sesp_revenue': sesp['revenue_per_unit'],
            'sesp_cost': sesp['cost_per_unit'],
            'sesp_margin': sesp['gross_margin'],
            'sesp_margin_percent': sesp['gross_margin_percent'],
            'sesp_clv': sesp['clv'],
            'breakeven_months': sesp['breakeven_months'],
            # Monthly contribution
            'monthly_revenue': round(monthly_revenue, 2),
            'monthly_cost': round(monthly_recurring_cost, 2),
            'monthly_contribution': round(monthly_contribution, 2),
            # Deltas
            'margin_delta': deltas['gross_margin']['absolute'],
            'clv_delta': deltas['clv']['absolute'],
            'clv_improvement_percent': deltas['clv']['percent'],
            # Service value
            'service_value_delivered': service_value['total_value'],
            'net_customer_value': service_value['net_customer_value'],
        })

    # Find optimal tenure
    best_margin = max(results, key=lambda x: x['sesp_margin'])
    best_clv = max(results, key=lambda x: x['sesp_clv'])
    breakeven_tenure = next(
        (r for r in results if r['sesp_margin'] >= 0),
        {'tenure': None, 'sesp_margin': None}
    )

    # Calculate improvement per month added
    if len(results) >= 2:
        margin_per_month = (results[-1]['sesp_margin'] - results[0]['sesp_margin']) / (results[-1]['tenure'] - results[0]['tenure'])
    else:
        margin_per_month = 0

    return {
        'results': results,
        'best_margin_tenure': best_margin['tenure'],
        'best_margin': best_margin['sesp_margin'],
        'best_clv_tenure': best_clv['tenure'],
        'best_clv': best_clv['clv_delta'],
        'breakeven_tenure': breakeven_tenure['tenure'],
        'margin_per_month_added': round(margin_per_month, 2),
        'parameters': {
            'mrp': mrp,
            'subsidy_percent': subsidy_percent * 100,
            'dealer_margin': dealer_margin * 100,
            'tenures_tested': tenure_options,
        },
        'notes': 'Longer tenure improves margin by spreading fixed costs',
    }


# =============================================================================
# Dealer Margin Sensitivity Analysis
# =============================================================================

def run_dealer_margin_sensitivity(
    mrp: float = 45000,
    tenure_months: int = 36,  # Use optimized tenure
    dealer_margin_options: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across different dealer margin levels.

    Why Dealer Margin Matters:
    - Lower dealer margin = Higher Traditional margin
    - If Traditional margin is HIGHER, SESP needs more value to justify
    - User confirmed IRL dealer margins are 12-14%, not 18%
    - This affects the "BEFORE" baseline we're comparing against

    Args:
        mrp: Product MRP
        tenure_months: SESP tenure for comparison
        dealer_margin_options: List of dealer margins to test

    Returns:
        Dictionary with sensitivity results.

    Example:
        >>> results = run_dealer_margin_sensitivity()
        >>> for r in results['results']:
        ...     print(f"{r['dealer_margin']*100:.0f}%: Trad margin Rs{r['trad_margin']:,.0f}")
    """
    if dealer_margin_options is None:
        dealer_margin_options = DEALER_MARGIN_OPTIONS

    results = []

    # SESP stays constant (doesn't use dealer)
    sesp = get_sesp_summary(
        mrp=mrp,
        tenure_months=tenure_months,
    )

    for dealer_margin in dealer_margin_options:
        # Calculate traditional for this dealer margin
        traditional = get_traditional_summary(
            mrp=mrp,
            dealer_margin=dealer_margin,
        )

        # Calculate comparison metrics
        deltas = calculate_delta_metrics(traditional, sesp)

        results.append({
            'dealer_margin': dealer_margin,
            'dealer_margin_percent': dealer_margin * 100,
            # Traditional metrics
            'trad_revenue': traditional['revenue_per_unit'],
            'trad_cost': traditional['cost_per_unit'],
            'trad_margin': traditional['gross_margin'],
            'trad_margin_percent': traditional['gross_margin_percent'],
            'trad_clv': traditional['clv'],
            # SESP (constant)
            'sesp_margin': sesp['gross_margin'],
            'sesp_margin_percent': sesp['gross_margin_percent'],
            'sesp_clv': sesp['clv'],
            # Deltas (how much better/worse is SESP)
            'margin_delta': deltas['gross_margin']['absolute'],
            'clv_delta': deltas['clv']['absolute'],
            'clv_improvement_percent': deltas['clv']['percent'],
            # Interpretation
            'sesp_beats_traditional': sesp['gross_margin'] > traditional['gross_margin'],
        })

    # Analysis
    highest_trad_margin = max(results, key=lambda x: x['trad_margin'])
    lowest_trad_margin = min(results, key=lambda x: x['trad_margin'])

    # How much harder is it to beat Traditional with lower dealer margin?
    margin_sensitivity = (highest_trad_margin['trad_margin'] - lowest_trad_margin['trad_margin']) / (
        highest_trad_margin['dealer_margin'] - lowest_trad_margin['dealer_margin']
    ) * -1  # Negative because lower dealer margin = higher traditional margin

    return {
        'results': results,
        'highest_traditional_margin': {
            'dealer_margin': highest_trad_margin['dealer_margin'] * 100,
            'margin': highest_trad_margin['trad_margin'],
        },
        'lowest_traditional_margin': {
            'dealer_margin': lowest_trad_margin['dealer_margin'] * 100,
            'margin': lowest_trad_margin['trad_margin'],
        },
        'margin_sensitivity_per_point': round(margin_sensitivity, 2),
        'sesp_margin': sesp['gross_margin'],  # Constant
        'parameters': {
            'mrp': mrp,
            'tenure_months': tenure_months,
            'margins_tested': [m * 100 for m in dealer_margin_options],
        },
        'notes': 'Lower dealer margin increases Traditional baseline, making SESP harder to justify',
    }


# =============================================================================
# Parallel BEFORE vs AFTER Comparison
# =============================================================================

def run_full_sensitivity_comparison(
    mrp: float = 45000,
    before_params: Optional[Dict] = None,
    after_params: Optional[Dict] = None,
    include_service_value: bool = True,
) -> Dict[str, Any]:
    """
    Generate comprehensive BEFORE vs AFTER comparison.

    BEFORE (Current Baseline):
    - Dealer margin: 18%
    - Tenure: 24 months
    - Service value: Not included

    AFTER (Optimized):
    - Dealer margin: 12% (user-confirmed IRL)
    - Tenure: 36 months (tested as optimal)
    - Service value: Rs 4,500/year included

    Args:
        mrp: Product MRP
        before_params: Override default BEFORE parameters
        after_params: Override default AFTER parameters
        include_service_value: Whether to include service value in AFTER

    Returns:
        Complete parallel comparison with analysis.

    Example:
        >>> comparison = run_full_sensitivity_comparison()
        >>> print(comparison['summary_table'])
    """
    if before_params is None:
        before_params = BEFORE_PARAMS.copy()
    if after_params is None:
        after_params = AFTER_PARAMS.copy()

    # ========================
    # BEFORE Scenario
    # ========================
    trad_before = get_traditional_summary(
        mrp=mrp,
        dealer_margin=before_params['dealer_margin'],
    )
    sesp_before = get_sesp_summary(
        mrp=mrp,
        subsidy_percent=before_params.get('subsidy_percent', 0.65),
        tenure_months=before_params['tenure_months'],
    )
    deltas_before = calculate_delta_metrics(trad_before, sesp_before)

    # ========================
    # AFTER Scenario
    # ========================
    trad_after = get_traditional_summary(
        mrp=mrp,
        dealer_margin=after_params['dealer_margin'],
    )
    sesp_after = get_sesp_summary(
        mrp=mrp,
        subsidy_percent=after_params.get('subsidy_percent', 0.65),
        tenure_months=after_params['tenure_months'],
    )
    deltas_after = calculate_delta_metrics(trad_after, sesp_after)

    # Service value (AFTER only)
    service_value_before = {'total_value': 0, 'net_customer_value': 0}
    if include_service_value:
        service_value_after = calculate_service_value_delivered(
            tenure_months=after_params['tenure_months']
        )
    else:
        service_value_after = {'total_value': 0, 'net_customer_value': 0}

    # ========================
    # Generate Summary Table
    # ========================
    summary_table = _generate_parallel_table(
        before={
            'traditional': trad_before,
            'sesp': sesp_before,
            'deltas': deltas_before,
            'params': before_params,
            'service_value': service_value_before,
        },
        after={
            'traditional': trad_after,
            'sesp': sesp_after,
            'deltas': deltas_after,
            'params': after_params,
            'service_value': service_value_after,
        },
    )

    # ========================
    # Calculate Improvements
    # ========================
    trad_margin_change = trad_after['gross_margin'] - trad_before['gross_margin']
    sesp_margin_change = sesp_after['gross_margin'] - sesp_before['gross_margin']

    # Is SESP now viable?
    sesp_viable_before = sesp_before['gross_margin'] > 0
    sesp_viable_after = sesp_after['gross_margin'] > 0

    # Insights
    insights = []

    if trad_margin_change > 0:
        insights.append(
            f"Traditional margin INCREASED by Rs{trad_margin_change:,.0f} due to lower dealer margin. "
            "This raises the bar for SESP to justify switching."
        )

    if sesp_margin_change > 0:
        insights.append(
            f"SESP margin IMPROVED by Rs{sesp_margin_change:,.0f} due to longer tenure. "
            "More months of fee revenue offset fixed costs."
        )

    if sesp_viable_after and not sesp_viable_before:
        insights.append(
            "SESP transitioned from UNPROFITABLE to PROFITABLE with optimized parameters!"
        )
    elif not sesp_viable_after:
        insights.append(
            f"SESP margin is still negative (Rs{sesp_after['gross_margin']:,.0f}). "
            "May need lower subsidy or even longer tenure."
        )

    if include_service_value:
        insights.append(
            f"Service value adds Rs{service_value_after['total_value']:,.0f} to customer value proposition, "
            "partially justifying the monthly fee."
        )

    return {
        'before': {
            'params': before_params,
            'traditional': trad_before,
            'sesp': sesp_before,
            'deltas': deltas_before,
            'service_value': service_value_before,
        },
        'after': {
            'params': after_params,
            'traditional': trad_after,
            'sesp': sesp_after,
            'deltas': deltas_after,
            'service_value': service_value_after,
        },
        'improvements': {
            'traditional_margin_change': round(trad_margin_change, 2),
            'sesp_margin_change': round(sesp_margin_change, 2),
            'sesp_viable_before': sesp_viable_before,
            'sesp_viable_after': sesp_viable_after,
        },
        'insights': insights,
        'summary_table': summary_table,
    }


def _generate_parallel_table(before: Dict, after: Dict) -> str:
    """Generate formatted BEFORE vs AFTER comparison table."""

    lines = []
    lines.append("=" * 85)
    lines.append("PARALLEL COMPARISON: BEFORE (Current) vs AFTER (Optimized)")
    lines.append("=" * 85)
    lines.append("")

    # Parameters section
    lines.append("--- Parameters ---")
    lines.append(f"{'Parameter':<30} {'BEFORE':>20} {'AFTER':>20} {'Change':>12}")
    lines.append("-" * 85)

    # Dealer margin
    dm_before = before['params']['dealer_margin'] * 100
    dm_after = after['params']['dealer_margin'] * 100
    dm_change = dm_after - dm_before
    dm_sign = '+' if dm_change >= 0 else ''
    lines.append(f"{'Dealer Margin':<30} {f'{dm_before:.0f}%':>20} {f'{dm_after:.0f}%':>20} {dm_sign + f'{dm_change:.0f}pp':>12}")

    # Tenure
    t_before = before['params']['tenure_months']
    t_after = after['params']['tenure_months']
    t_change = t_after - t_before
    t_sign = '+' if t_change >= 0 else ''
    lines.append(f"{'Tenure':<30} {f'{t_before} months':>20} {f'{t_after} months':>20} {t_sign + f'{t_change}m':>12}")

    # Service value
    sv_before = 'No'
    sv_after = 'Yes' if after['service_value']['total_value'] > 0 else 'No'
    lines.append(f"{'Service Value Included':<30} {sv_before:>20} {sv_after:>20} {'-':>12}")

    lines.append("")

    # Traditional metrics
    lines.append("--- Traditional Model ---")
    lines.append(f"{'Metric':<30} {'BEFORE':>20} {'AFTER':>20} {'Change':>12}")
    lines.append("-" * 85)

    trad_b = before['traditional']
    trad_a = after['traditional']

    # Traditional margin
    tm_before = trad_b['gross_margin']
    tm_after = trad_a['gross_margin']
    tm_change = tm_after - tm_before
    tm_sign = '+' if tm_change >= 0 else ''
    lines.append(f"{'Gross Margin':<30} {'Rs' + f'{tm_before:,.0f}':>19} {'Rs' + f'{tm_after:,.0f}':>19} {tm_sign + f'Rs{tm_change:,.0f}':>12}")

    # Traditional margin %
    tmp_before = trad_b['gross_margin_percent']
    tmp_after = trad_a['gross_margin_percent']
    tmp_change = tmp_after - tmp_before
    tmp_sign = '+' if tmp_change >= 0 else ''
    lines.append(f"{'Gross Margin %':<30} {f'{tmp_before:.1f}%':>20} {f'{tmp_after:.1f}%':>20} {tmp_sign + f'{tmp_change:.1f}pp':>12}")

    # Traditional CLV
    tc_before = trad_b['clv']
    tc_after = trad_a['clv']
    tc_change = tc_after - tc_before
    tc_sign = '+' if tc_change >= 0 else ''
    lines.append(f"{'CLV':<30} {'Rs' + f'{tc_before:,.0f}':>19} {'Rs' + f'{tc_after:,.0f}':>19} {tc_sign + f'Rs{tc_change:,.0f}':>12}")

    lines.append("")

    # SESP metrics
    lines.append("--- SESP Model ---")
    lines.append(f"{'Metric':<30} {'BEFORE':>20} {'AFTER':>20} {'Change':>12}")
    lines.append("-" * 85)

    sesp_b = before['sesp']
    sesp_a = after['sesp']

    # SESP margin
    sm_before = sesp_b['gross_margin']
    sm_after = sesp_a['gross_margin']
    sm_change = sm_after - sm_before
    sm_sign = '+' if sm_change >= 0 else ''
    lines.append(f"{'Gross Margin':<30} {'Rs' + f'{sm_before:,.0f}':>19} {'Rs' + f'{sm_after:,.0f}':>19} {sm_sign + f'Rs{sm_change:,.0f}':>12}")

    # SESP margin %
    smp_before = sesp_b['gross_margin_percent']
    smp_after = sesp_a['gross_margin_percent']
    smp_change = smp_after - smp_before
    smp_sign = '+' if smp_change >= 0 else ''
    lines.append(f"{'Gross Margin %':<30} {f'{smp_before:.1f}%':>20} {f'{smp_after:.1f}%':>20} {smp_sign + f'{smp_change:.1f}pp':>12}")

    # SESP CLV
    sc_before = sesp_b['clv']
    sc_after = sesp_a['clv']
    sc_change = sc_after - sc_before
    sc_sign = '+' if sc_change >= 0 else ''
    lines.append(f"{'CLV':<30} {'Rs' + f'{sc_before:,.0f}':>19} {'Rs' + f'{sc_after:,.0f}':>19} {sc_sign + f'Rs{sc_change:,.0f}':>12}")

    # Break-even
    be_before = sesp_b['breakeven_months']
    be_after = sesp_a['breakeven_months']
    be_change = be_after - be_before
    be_sign = '+' if be_change >= 0 else ''
    lines.append(f"{'Break-even':<30} {f'{be_before:.0f} months':>20} {f'{be_after:.0f} months':>20} {be_sign + f'{be_change:.0f}m':>12}")

    lines.append("")

    # Service value (AFTER only)
    if after['service_value']['total_value'] > 0:
        lines.append("--- Service Value (AFTER only) ---")
        sv = after['service_value']
        sv_total = sv['total_value']
        lines.append(f"{'Total Value Delivered':<30} {'-':>20} {'Rs' + f'{sv_total:,.0f}':>19} {'NEW':>12}")
        lines.append(f"{'Annual Value':<30} {'-':>20} {'Rs' + f'{SERVICE_VALUE_ANNUAL:,.0f}/yr':>19} {'NEW':>12}")
        lines.append("")

    # Delta comparison (SESP vs Traditional)
    lines.append("--- SESP vs Traditional Delta ---")
    lines.append(f"{'Metric':<30} {'BEFORE':>20} {'AFTER':>20} {'Improvement':>12}")
    lines.append("-" * 85)

    delta_b = before['deltas']
    delta_a = after['deltas']

    # Margin delta
    md_before = delta_b['gross_margin']['absolute']
    md_after = delta_a['gross_margin']['absolute']
    md_improve = md_after - md_before
    md_sign = '+' if md_before >= 0 else ''
    ma_sign = '+' if md_after >= 0 else ''
    mi_sign = '+' if md_improve >= 0 else ''
    lines.append(f"{'Margin Gap (SESP-Trad)':<30} {md_sign + 'Rs' + f'{md_before:,.0f}':>19} {ma_sign + 'Rs' + f'{md_after:,.0f}':>19} {mi_sign + f'Rs{md_improve:,.0f}':>12}")

    # CLV delta
    cd_before = delta_b['clv']['absolute']
    cd_after = delta_a['clv']['absolute']
    cd_improve = cd_after - cd_before
    cd_sign = '+' if cd_before >= 0 else ''
    ca_sign = '+' if cd_after >= 0 else ''
    ci_sign = '+' if cd_improve >= 0 else ''
    lines.append(f"{'CLV Gap (SESP-Trad)':<30} {cd_sign + 'Rs' + f'{cd_before:,.0f}':>19} {ca_sign + 'Rs' + f'{cd_after:,.0f}':>19} {ci_sign + f'Rs{cd_improve:,.0f}':>12}")

    lines.append("")
    lines.append("=" * 85)

    # Viability assessment
    sesp_viable_before = sm_before > 0
    sesp_viable_after = sm_after > 0

    if sesp_viable_after and not sesp_viable_before:
        status = "SESP BECAME VIABLE with optimized parameters!"
    elif sesp_viable_after:
        status = "SESP remains VIABLE with improved margins."
    elif not sesp_viable_after and sm_after > sm_before:
        status = f"SESP IMPROVED but still needs Rs{abs(sm_after):,.0f} more to break even."
    else:
        status = "SESP remains UNPROFITABLE - further optimization needed."

    lines.append(f"STATUS: {status}")
    lines.append("=" * 85)

    return "\n".join(lines)


# =============================================================================
# Extended Tenure Test (All Options)
# =============================================================================

def run_extended_tenure_test(
    mrp: float = 45000,
    dealer_margin: float = 0.12,
) -> Dict[str, Any]:
    """
    Test all tenure options (36m, 42m, 48m) as requested by user.

    Returns detailed analysis for each tenure option to help identify
    the optimal tenure for SESP viability.
    """
    tenure_options = [36, 42, 48]

    results = run_tenure_sensitivity(
        mrp=mrp,
        dealer_margin=dealer_margin,
        tenure_options=tenure_options,
    )

    # Add interpretation for each option
    interpretations = {}
    for r in results['results']:
        tenure = r['tenure']
        if r['sesp_margin'] > 0:
            interp = f"PROFITABLE at Rs{r['sesp_margin']:,.0f} margin"
        else:
            interp = f"LOSS of Rs{abs(r['sesp_margin']):,.0f} per unit"

        interpretations[tenure] = {
            'margin': r['sesp_margin'],
            'margin_percent': r['sesp_margin_percent'],
            'clv': r['sesp_clv'],
            'breakeven': r['breakeven_months'],
            'viable': r['sesp_margin'] > 0,
            'interpretation': interp,
        }

    return {
        'results': results['results'],
        'interpretations': interpretations,
        'recommendation': _recommend_tenure(interpretations),
    }


def _recommend_tenure(interpretations: Dict) -> str:
    """Generate tenure recommendation based on results."""
    viable = {t: i for t, i in interpretations.items() if i['viable']}

    if not viable:
        return (
            "No tested tenure achieves profitability. Consider: "
            "(1) Lower subsidy below 65%, "
            "(2) Longer tenure (54m+), or "
            "(3) Higher monthly fees."
        )

    # Find minimum viable tenure (least commitment for customer)
    min_viable = min(viable.keys())

    # Find best margin tenure
    best_margin = max(viable.keys(), key=lambda t: viable[t]['margin'])

    if min_viable == best_margin:
        return f"Recommend {min_viable} months - achieves profitability with best margin."
    else:
        return (
            f"Recommend {min_viable} months as minimum viable tenure. "
            f"{best_margin} months offers better margin (Rs{viable[best_margin]['margin']:,.0f}) "
            "if customer commitment allows."
        )


# =============================================================================
# Subsidy Sensitivity Analysis (Phase 3c)
# =============================================================================

def run_subsidy_sensitivity(
    mrp: float = 45000,
    tenure_months: int = 60,  # 5-year tenure
    dealer_margin: float = 0.12,
    subsidy_options: Optional[List[float]] = None,
    include_bank_cac: bool = True,
    bank_cac: float = BANK_CAC_SUBSIDY,
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across different subsidy levels.

    Phase 3c Key Finding:
    - 65% subsidy is too aggressive — gives away Rs29,250 that can't be recovered
    - 50% subsidy ("Half Price") is catchy marketing and more sustainable
    - With 60-month tenure + credit card partnership, 50% achieves profitability

    Args:
        mrp: Product MRP
        tenure_months: Contract duration (default 60 for durable appliances)
        dealer_margin: Traditional dealer margin for comparison
        subsidy_options: List of subsidy percentages to test
        include_bank_cac: Whether to include bank CAC subsidy from credit card partnership
        bank_cac: Bank CAC subsidy amount (default Rs2,000)

    Returns:
        Dictionary with subsidy sensitivity results.

    Example:
        >>> results = run_subsidy_sensitivity()
        >>> for r in results['results']:
        ...     print(f"{r['subsidy_percent']:.0f}%: Margin Rs{r['sesp_margin']:,.0f}")
    """
    if subsidy_options is None:
        subsidy_options = SUBSIDY_OPTIONS

    results = []

    # Get traditional baseline (fixed)
    traditional = get_traditional_summary(
        mrp=mrp,
        dealer_margin=dealer_margin,
    )

    for subsidy in subsidy_options:
        # Calculate SESP for this subsidy
        sesp = get_sesp_summary(
            mrp=mrp,
            subsidy_percent=subsidy,
            tenure_months=tenure_months,
        )

        # Calculate upfront deficit
        customer_pays = mrp * (1 - subsidy)
        customer_pays_with_gst = customer_pays * 1.18
        net_to_company = customer_pays / 1.18  # Net of GST
        upfront_costs = 36000  # Manufacturing + IoT + Install + CAC (from SESP model)
        upfront_deficit = upfront_costs - net_to_company

        # Calculate monthly contribution
        monthly_fee = 599  # Standard plan
        monthly_fee_net = monthly_fee * 0.847  # Net of GST
        monthly_recurring_cost = 192  # IoT + maintenance per month
        monthly_contribution = monthly_fee_net - monthly_recurring_cost

        # Total contribution over tenure
        total_contribution = monthly_contribution * tenure_months

        # SESP margin with/without bank CAC
        margin_without_bank = total_contribution - upfront_deficit
        margin_with_bank = margin_without_bank + (bank_cac if include_bank_cac else 0)

        # Service value delivered to customer
        service_value = calculate_service_value_delivered(
            tenure_months=tenure_months,
            include_iot_additions=True,
            include_credit_card=True,
            monthly_fee=monthly_fee,
        )

        # Participation constraint check
        # Purchase alternative (5 years)
        purchase_cost = mrp + (2500 * 5) + 3500 - 5000  # MRP + AMC + ext warranty - terminal value
        sesp_total_paid = customer_pays_with_gst + (monthly_fee * 1.18 * tenure_months)
        pc_slack = purchase_cost - (sesp_total_paid - service_value['total_value'])

        results.append({
            'subsidy_percent': subsidy * 100,
            'customer_pays': round(customer_pays, 0),
            'customer_pays_with_gst': round(customer_pays_with_gst, 0),
            'net_to_company': round(net_to_company, 0),
            'upfront_deficit': round(upfront_deficit, 0),
            # Margin calculations
            'monthly_contribution': round(monthly_contribution, 0),
            'total_contribution': round(total_contribution, 0),
            'margin_without_bank': round(margin_without_bank, 0),
            'margin_with_bank': round(margin_with_bank, 0),
            'sesp_margin': round(margin_with_bank if include_bank_cac else margin_without_bank, 0),
            'profitable': (margin_with_bank if include_bank_cac else margin_without_bank) > 0,
            # Customer perspective
            'sesp_total_paid': round(sesp_total_paid, 0),
            'service_value': round(service_value['total_value'], 0),
            'net_cost_to_customer': round(sesp_total_paid - service_value['total_value'], 0),
            'purchase_alternative': round(purchase_cost, 0),
            'pc_slack': round(pc_slack, 0),  # Positive = SESP is cheaper after value
            'pc_satisfied': pc_slack >= 0,
            # Traditional comparison
            'trad_margin': traditional['gross_margin'],
            'margin_vs_trad': round((margin_with_bank if include_bank_cac else margin_without_bank) - traditional['gross_margin'], 0),
        })

    # Find optimal subsidy (first profitable one)
    profitable_results = [r for r in results if r['profitable']]
    if profitable_results:
        # Find highest subsidy that's still profitable (most attractive to customer)
        best = max(profitable_results, key=lambda x: x['subsidy_percent'])
    else:
        # If none profitable, find closest to break-even
        best = max(results, key=lambda x: x['sesp_margin'])

    # Find break-even subsidy
    breakeven = next(
        (r for r in sorted(results, key=lambda x: -x['subsidy_percent']) if r['profitable']),
        None
    )

    return {
        'results': results,
        'best_subsidy': best['subsidy_percent'],
        'best_margin': best['sesp_margin'],
        'breakeven_subsidy': breakeven['subsidy_percent'] if breakeven else None,
        'parameters': {
            'mrp': mrp,
            'tenure_months': tenure_months,
            'dealer_margin': dealer_margin * 100,
            'include_bank_cac': include_bank_cac,
            'bank_cac': bank_cac,
            'subsidies_tested': [s * 100 for s in subsidy_options],
        },
        'notes': 'Lower subsidy improves company margin but increases customer upfront cost',
    }


# =============================================================================
# Tiered Plan Analysis (Phase 3c - Bucket Model)
# =============================================================================

def run_tiered_plan_analysis(
    mrp: float = 45000,
    tenure_months: int = 60,
    subsidy_percent: float = 0.50,
    plans: Optional[Dict] = None,
    include_bank_cac: bool = True,
    bank_cac: float = BANK_CAC_SUBSIDY,
) -> Dict[str, Any]:
    """
    Analyze profitability of tiered subscription plans (bucket model).

    Key Insight: Cross-subsidy between segments!
    - Heavy users (20%) paying Rs799 → Strong profit
    - Standard users (50%) paying Rs599 → Moderate profit
    - Lite users (30%) paying Rs449 → Small loss
    - BLENDED: Profitable due to heavy users subsidizing lite

    Args:
        mrp: Product MRP
        tenure_months: Contract duration
        subsidy_percent: Upfront subsidy (same for all tiers)
        plans: Tiered plan configuration (default TIERED_PLANS)
        include_bank_cac: Include bank CAC subsidy
        bank_cac: Bank CAC subsidy amount

    Returns:
        Dictionary with per-plan and blended analysis.

    Example:
        >>> results = run_tiered_plan_analysis()
        >>> print(f"Blended margin: Rs{results['blended_margin']:,.0f}")
    """
    if plans is None:
        plans = TIERED_PLANS

    # Fixed costs (same for all tiers)
    upfront_costs = 36000  # Manufacturing + IoT + Install + CAC
    customer_pays = mrp * (1 - subsidy_percent)
    net_to_company = customer_pays / 1.18
    upfront_deficit = upfront_costs - net_to_company

    monthly_recurring_cost = 192  # IoT + maintenance per month

    plan_results = []

    for plan_name, plan in plans.items():
        monthly_fee = plan['monthly_fee']
        monthly_fee_net = monthly_fee * 0.847
        monthly_contribution = monthly_fee_net - monthly_recurring_cost
        total_contribution = monthly_contribution * tenure_months

        # Margin for this tier
        margin_without_bank = total_contribution - upfront_deficit
        margin_with_bank = margin_without_bank + (bank_cac if include_bank_cac else 0)

        # Service value (same for all tiers)
        service_value = calculate_service_value_delivered(
            tenure_months=tenure_months,
            include_iot_additions=True,
            include_credit_card=True,
            monthly_fee=monthly_fee,
        )

        plan_results.append({
            'plan': plan_name,
            'monthly_fee': monthly_fee,
            'segment_share': plan['segment_share'],
            'hours_included': plan['hours_included'],
            'monthly_contribution': round(monthly_contribution, 0),
            'total_contribution': round(total_contribution, 0),
            'margin_without_bank': round(margin_without_bank, 0),
            'margin_with_bank': round(margin_with_bank, 0),
            'profitable': margin_with_bank > 0,
            'customer_total_paid': round((customer_pays * 1.18) + (monthly_fee * 1.18 * tenure_months), 0),
            'service_value': round(service_value['total_value'], 0),
        })

    # Calculate BLENDED margin (weighted by segment share)
    blended_margin = sum(
        r['margin_with_bank'] * r['segment_share']
        for r in plan_results
    )

    # Cross-subsidy analysis
    profitable_plans = [r for r in plan_results if r['profitable']]
    unprofitable_plans = [r for r in plan_results if not r['profitable']]

    cross_subsidy = 0
    if unprofitable_plans and profitable_plans:
        # How much do profitable tiers subsidize unprofitable ones?
        loss_from_unprofitable = sum(
            abs(r['margin_with_bank']) * r['segment_share']
            for r in unprofitable_plans
        )
        profit_from_profitable = sum(
            r['margin_with_bank'] * r['segment_share']
            for r in profitable_plans
        )
        cross_subsidy = profit_from_profitable - loss_from_unprofitable

    return {
        'plans': plan_results,
        'blended_margin': round(blended_margin, 0),
        'blended_profitable': blended_margin > 0,
        'cross_subsidy': round(cross_subsidy, 0),
        'parameters': {
            'mrp': mrp,
            'tenure_months': tenure_months,
            'subsidy_percent': subsidy_percent * 100,
            'upfront_deficit': round(upfront_deficit, 0),
            'include_bank_cac': include_bank_cac,
            'bank_cac': bank_cac,
        },
        'notes': 'Heavy users cross-subsidize lite users in blended portfolio',
    }


# =============================================================================
# Combined Sensitivity Matrix (Phase 3c)
# =============================================================================

def run_combined_sensitivity(
    mrp: float = 45000,
    subsidy_options: Optional[List[float]] = None,
    tenure_options: Optional[List[int]] = None,
    include_bank_cac: bool = True,
) -> Dict[str, Any]:
    """
    Generate subsidy × tenure sensitivity matrix.

    Shows which combinations achieve profitability.

    Args:
        mrp: Product MRP
        subsidy_options: Subsidy levels to test
        tenure_options: Tenure durations to test
        include_bank_cac: Include bank CAC subsidy

    Returns:
        Matrix of results with profitability indicators.
    """
    if subsidy_options is None:
        subsidy_options = [0.40, 0.50, 0.55, 0.65]
    if tenure_options is None:
        tenure_options = [36, 48, 60]

    matrix = []

    for subsidy in subsidy_options:
        for tenure in tenure_options:
            result = run_subsidy_sensitivity(
                mrp=mrp,
                tenure_months=tenure,
                subsidy_options=[subsidy],
                include_bank_cac=include_bank_cac,
            )
            r = result['results'][0]

            matrix.append({
                'subsidy_percent': subsidy * 100,
                'tenure_months': tenure,
                'sesp_margin': r['sesp_margin'],
                'profitable': r['profitable'],
                'pc_satisfied': r['pc_satisfied'],
                'viable': r['profitable'] and r['pc_satisfied'],
            })

    # Find all viable combinations
    viable = [m for m in matrix if m['viable']]

    # Best viable (highest subsidy that's still profitable = most customer-friendly)
    if viable:
        best = max(viable, key=lambda x: x['subsidy_percent'])
    else:
        best = None

    return {
        'matrix': matrix,
        'viable_combinations': viable,
        'best_combination': best,
        'parameters': {
            'mrp': mrp,
            'subsidies_tested': [s * 100 for s in subsidy_options],
            'tenures_tested': tenure_options,
            'include_bank_cac': include_bank_cac,
        },
    }


# =============================================================================
# Module Test
# =============================================================================

if __name__ == "__main__":
    # Set encoding for Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 85)
    print("Sensitivity Analysis Module - Demo")
    print("=" * 85)

    # Run tenure sensitivity
    print("\n" + "=" * 85)
    print("TENURE SENSITIVITY (24-48 months)")
    print("=" * 85)

    tenure_results = run_tenure_sensitivity()
    print(f"\nTested tenures: {tenure_results['parameters']['tenures_tested']}")
    print(f"Dealer margin: {tenure_results['parameters']['dealer_margin']:.0f}%")
    print(f"\n{'Tenure':<10} {'SESP Margin':>15} {'Margin %':>12} {'CLV Delta':>15}")
    print("-" * 55)

    for r in tenure_results['results']:
        print(f"{r['tenure']} months    Rs{r['sesp_margin']:>12,.0f}    {r['sesp_margin_percent']:>8.1f}%    Rs{r['clv_delta']:>12,.0f}")

    print(f"\nBest margin at: {tenure_results['best_margin_tenure']} months")
    print(f"Break-even tenure: {tenure_results['breakeven_tenure']} months" if tenure_results['breakeven_tenure'] else "Break-even not reached in tested range")

    # Run dealer margin sensitivity
    print("\n" + "=" * 85)
    print("DEALER MARGIN SENSITIVITY (12-18%)")
    print("=" * 85)

    margin_results = run_dealer_margin_sensitivity()
    print(f"\nTested margins: {margin_results['parameters']['margins_tested']}")
    print(f"SESP tenure: {margin_results['parameters']['tenure_months']} months")
    print(f"\n{'Dealer %':<12} {'Trad Margin':>15} {'SESP Margin':>15} {'SESP Beats':>12}")
    print("-" * 55)

    for r in margin_results['results']:
        beats = 'YES' if r['sesp_beats_traditional'] else 'NO'
        print(f"{r['dealer_margin_percent']:>8.0f}%    Rs{r['trad_margin']:>12,.0f}    Rs{r['sesp_margin']:>12,.0f}    {beats:>10}")

    # Run full BEFORE vs AFTER comparison
    print("\n")
    comparison = run_full_sensitivity_comparison()
    print(comparison['summary_table'])

    # Print insights
    print("\nKEY INSIGHTS:")
    for i, insight in enumerate(comparison['insights'], 1):
        print(f"  {i}. {insight}")

    print("\n" + "=" * 85)
    print("Sensitivity analysis complete!")
