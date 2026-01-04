"""
TOPSIS for Pricing Scenario Ranking (Task 2.0.2)
================================================

Purpose:
    Rank 4 pricing scenarios using multi-criteria decision analysis.
    Scenarios vary by subsidy level and monthly fee combinations.

Scenarios (Updated 2026-01-04 - Valid PC Parameters):
    1. Value Leader — High subsidy (70%), light plan, 24m
    2. Balanced Optimal — High subsidy (65%), moderate plan, 24m
    3. Extended Value — High subsidy (70%), moderate plan, 36m
    4. Premium Service — High subsidy (70%), heavy plan, 24m

NOTE: Original scenarios (Conservative/Balanced/Aggressive/Premium) ALL
violated the participation constraint (negative customer savings). These
new scenarios use parameters validated through grid search to satisfy
PC with >=10% customer savings.

Criteria:
    C1: Customer Savings % (vs purchase) — Benefit ↑
    C2: Company Margin % — Benefit ↑
    C3: Break-even Period (months) — Cost ↓
    C4: Churn Risk % — Cost ↓
    C5: Adoption Score — Benefit ↑

Data Source:
    Derived from Phase 1 calculators (calculators.py, participation.py)

Method:
    TOPSIS with weights from AHP (Task 2.0.1)
"""

import numpy as np
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .mcdm_utils import topsis_rank


# =============================================================================
# Pricing Scenarios Definition
# =============================================================================

# Original scenarios (ALL violated participation constraint - kept for reference)
_ORIGINAL_SCENARIOS_DEPRECATED = {
    'Conservative_OLD': {'subsidy_percent': 22.2, 'savings': -36.1},
    'Balanced_OLD': {'subsidy_percent': 33.3, 'savings': -23.2},
    'Aggressive_OLD': {'subsidy_percent': 44.4, 'savings': -10.3},
    'Premium_OLD': {'subsidy_percent': 17.8, 'savings': -56.1},
}

# NEW VALID SCENARIOS (2026-01-04) - All satisfy participation constraint
PRICING_SCENARIOS = {
    'Value_Leader': {
        'description': 'Maximum value for price-conscious customers',
        'subsidy': 31500,        # ₹31,500 subsidy (70% of ₹45K MRP)
        'subsidy_percent': 70.0,
        'monthly_fee': 499,      # Light tier fee
        'plan': 'light',
        'tenure_months': 24,     # Shorter tenure reduces fee accumulation
        'target_segment': 'light',
        'expected_savings': 22.5,  # Validated positive savings
        'rationale': 'Best value proposition for budget-conscious, low-usage customers'
    },
    'Balanced_Optimal': {
        'description': 'Optimal trade-off between value and service',
        'subsidy': 29250,        # ₹29,250 subsidy (65%)
        'subsidy_percent': 65.0,
        'monthly_fee': 649,      # Moderate tier fee
        'plan': 'moderate',
        'tenure_months': 24,
        'target_segment': 'moderate',
        'expected_savings': 19.9,
        'rationale': 'Sweet spot for mainstream families with average usage'
    },
    'Extended_Value': {
        'description': 'Long-term commitment with strong savings',
        'subsidy': 31500,        # ₹31,500 subsidy (70%)
        'subsidy_percent': 70.0,
        'monthly_fee': 649,      # Moderate tier fee
        'plan': 'moderate',
        'tenure_months': 36,     # Longer tenure for committed customers
        'target_segment': 'moderate',
        'expected_savings': 20.2,
        'rationale': 'Best for families wanting long-term relationship with brand'
    },
    'Premium_Service': {
        'description': 'Full service package for heavy users',
        'subsidy': 31500,        # ₹31,500 subsidy (70%)
        'subsidy_percent': 70.0,
        'monthly_fee': 899,      # Heavy tier fee
        'plan': 'heavy',
        'tenure_months': 24,
        'target_segment': 'heavy',
        'expected_savings': 14.1,
        'rationale': 'Premium service for WFH, joint families, heavy usage needs'
    }
}


# =============================================================================
# Criteria Definition
# =============================================================================

TOPSIS_CRITERIA = {
    0: {
        'name': 'Customer Savings %',
        'short': 'Savings',
        'type': 'benefit',  # Higher is better
        'description': 'Percentage savings vs outright purchase (NPV)'
    },
    1: {
        'name': 'Company Margin %',
        'short': 'Margin',
        'type': 'benefit',  # Higher is better
        'description': 'Net profit margin for the company'
    },
    2: {
        'name': 'Break-even Period',
        'short': 'Breakeven',
        'type': 'cost',  # Lower is better
        'description': 'Months until cumulative cash flow turns positive'
    },
    3: {
        'name': 'Churn Risk %',
        'short': 'Churn',
        'type': 'cost',  # Lower is better
        'description': 'Estimated probability of customer leaving early'
    },
    4: {
        'name': 'Adoption Score',
        'short': 'Adoption',
        'type': 'benefit',  # Higher is better
        'description': 'Composite score for market adoption potential'
    }
}


# =============================================================================
# Metric Derivation from Phase 1
# =============================================================================

def derive_scenario_metrics(
    mrp: float = 45000,
    default_segment: str = 'moderate'
) -> Dict[str, Dict]:
    """
    Derive TOPSIS criteria values for each scenario using Phase 1 calculators.

    NOTE: Each scenario now includes its own tenure_months and target_segment.
    This function uses scenario-specific parameters instead of global defaults.

    Args:
        mrp: Appliance MRP (default ₹45,000)
        default_segment: Fallback segment if not specified in scenario

    Returns:
        Dict mapping scenario names to their criteria values
    """
    try:
        from src.alternatives.calculators import (
            calculate_purchase_cost,
            calculate_sesp_cost,
            compare_alternatives
        )
        from src.constraints.participation import check_pc_vs_purchase
        from src.constraints.incentive_compatibility import validate_ic
        from src.adjustments.india_specific import npv_customer

        use_phase1 = True
    except ImportError:
        use_phase1 = False
        print("Warning: Phase 1 modules not found. Using estimated values.")

    metrics = {}

    for scenario_name, scenario in PRICING_SCENARIOS.items():
        # Use scenario-specific tenure and segment
        tenure_months = scenario.get('tenure_months', 36)  # Default 36 months
        tenure_years = tenure_months // 12
        segment = scenario.get('target_segment', default_segment)

        if use_phase1:
            # Use Phase 1 calculators with scenario-specific params
            metrics[scenario_name] = _derive_from_phase1(
                scenario, mrp, tenure_years, segment
            )
        else:
            # Use estimated values
            metrics[scenario_name] = _estimate_metrics(scenario)

    return metrics


def _derive_from_phase1(
    scenario: Dict,
    mrp: float,
    tenure_years: int,
    segment: str
) -> Dict:
    """Derive metrics using Phase 1 calculators."""
    from src.alternatives.calculators import (
        calculate_purchase_cost,
        calculate_sesp_cost,
        compare_alternatives
    )
    from src.constraints.participation import check_pc_vs_purchase
    from src.constraints.incentive_compatibility import validate_ic
    from src.adjustments.india_specific import npv_customer

    subsidized_price = mrp - scenario['subsidy']

    # Use scenario-specific tenure if available
    tenure_months = scenario.get('tenure_months', tenure_years * 12)
    actual_tenure_years = tenure_months // 12

    # 1. Customer Savings % — from participation constraint
    sesp_params = {
        'subsidized_price': subsidized_price,
        'plan': scenario['plan'],
        'efficiency_score': 75,  # Assume average efficiency
        'deposit': 5000
    }

    pc_result = check_pc_vs_purchase(
        sesp_params=sesp_params,
        mrp=mrp,
        tenure_years=actual_tenure_years,
        segment=segment
    )
    customer_savings = pc_result['actual_savings_percent']

    # 2. Company Margin % — estimated from subsidy and fees
    # Revenue = subsidized_price + monthly_fee × tenure_months × 0.847 (net GST)
    total_revenue = subsidized_price + (scenario['monthly_fee'] * 0.847 * tenure_months)

    # Cost = manufacturing + IoT + installation + maintenance + warranty + CAC
    manufacturing_cost = 30000  # From appliances.json
    iot_cost = 1500 + (600 * actual_tenure_years)  # Hardware + annual recurring
    installation = 2500
    maintenance = 1200 * actual_tenure_years
    warranty = 2000
    cac = 2000
    total_cost = manufacturing_cost + iot_cost + installation + maintenance + warranty + cac

    margin_percent = ((total_revenue - total_cost) / total_cost) * 100

    # 3. Break-even Period — simplified estimation
    # Initial outflow = manufacturing + IoT + installation + CAC - subsidized_price
    initial_outflow = manufacturing_cost + 1500 + installation + cac - subsidized_price
    monthly_net = scenario['monthly_fee'] * 0.847 - (600 + 1200) / 12  # Net revenue - recurring costs

    if monthly_net > 0:
        breakeven_months = max(1, initial_outflow / monthly_net)
    else:
        breakeven_months = 36  # Default to max tenure

    # 4. Churn Risk % — inversely related to savings and directly to fee
    # Higher savings → lower churn; Higher fee → higher churn
    base_churn = 10  # Base 10% churn
    savings_effect = -0.3 * customer_savings  # Each 1% savings reduces churn by 0.3%
    fee_effect = (scenario['monthly_fee'] - 599) / 50  # Higher than base fee increases churn

    churn_risk = max(5, min(25, base_churn + savings_effect + fee_effect))

    # 5. Adoption Score — composite of savings, IC satisfaction, and market fit
    # IC satisfaction from Phase 1
    ic_result = validate_ic()
    ic_score = (ic_result['num_passed'] / ic_result['num_total']) * 100

    # Market fit based on subsidy level
    market_fit = min(100, 50 + scenario['subsidy_percent'])

    # Raw adoption score from components
    raw_adoption = (customer_savings * 2 + ic_score * 0.5 + market_fit * 0.5) / 3
    # Bound to valid range [30, 100] — same as fallback function
    adoption_score = max(30, min(100, raw_adoption))

    return {
        'customer_savings': round(customer_savings, 1),
        'company_margin': round(margin_percent, 1),
        'breakeven_months': round(breakeven_months, 0),
        'churn_risk': round(churn_risk, 1),
        'adoption_score': round(adoption_score, 0)
    }


def _estimate_metrics(scenario: Dict) -> Dict:
    """Estimate metrics without Phase 1 (fallback)."""
    # Rough estimates based on scenario characteristics
    subsidy_pct = scenario['subsidy_percent']
    fee = scenario['monthly_fee']

    # Higher subsidy → higher savings, lower margin, longer breakeven
    customer_savings = subsidy_pct * 0.5 - (fee - 599) / 20
    company_margin = 35 - subsidy_pct * 0.4 + (fee - 599) / 30
    breakeven_months = 12 + subsidy_pct * 0.3 - (fee - 599) / 50
    churn_risk = 10 - customer_savings * 0.2 + (fee - 599) / 75
    adoption_score = 50 + customer_savings * 2 - churn_risk

    return {
        'customer_savings': round(max(0, customer_savings), 1),
        'company_margin': round(max(5, company_margin), 1),
        'breakeven_months': round(max(12, min(36, breakeven_months)), 0),
        'churn_risk': round(max(5, min(25, churn_risk)), 1),
        'adoption_score': round(max(30, min(100, adoption_score)), 0)
    }


# =============================================================================
# TOPSIS Analysis
# =============================================================================

def build_decision_matrix(metrics: Optional[Dict] = None) -> Tuple[np.ndarray, List[str]]:
    """
    Build the decision matrix for TOPSIS analysis.

    Args:
        metrics: Pre-computed metrics dict (or None to derive)

    Returns:
        Tuple of (decision_matrix, scenario_names)
    """
    if metrics is None:
        metrics = derive_scenario_metrics()

    scenario_names = list(PRICING_SCENARIOS.keys())
    n_scenarios = len(scenario_names)
    n_criteria = len(TOPSIS_CRITERIA)

    decision_matrix = np.zeros((n_scenarios, n_criteria))

    for i, name in enumerate(scenario_names):
        m = metrics[name]
        decision_matrix[i, 0] = m['customer_savings']
        decision_matrix[i, 1] = m['company_margin']
        decision_matrix[i, 2] = m['breakeven_months']
        decision_matrix[i, 3] = m['churn_risk']
        decision_matrix[i, 4] = m['adoption_score']

    return decision_matrix, scenario_names


def get_criteria_types() -> List[str]:
    """Get list of criteria types (benefit/cost)."""
    return [TOPSIS_CRITERIA[i]['type'] for i in range(len(TOPSIS_CRITERIA))]


def run_topsis_pricing(
    weights: Optional[np.ndarray] = None,
    metrics: Optional[Dict] = None,
    verbose: bool = True
) -> Dict:
    """
    Run complete TOPSIS analysis for pricing scenarios.

    Args:
        weights: Criteria weights (if None, uses AHP weights from Task 2.0.1)
        metrics: Pre-computed metrics (if None, derives from Phase 1)
        verbose: If True, print detailed output

    Returns:
        Dict with full TOPSIS results
    """
    # Get weights from AHP if not provided
    if weights is None:
        try:
            from .ahp_incentive import get_incentive_weights
            ahp_weights = get_incentive_weights()
            # Map AHP criteria to TOPSIS criteria
            # AHP: satisfaction, moral_hazard, revenue, simplicity
            # TOPSIS: savings, margin, breakeven, churn, adoption
            # Mapping based on relevance:
            weights = np.array([
                ahp_weights['satisfaction'] * 0.6,   # Savings → Satisfaction
                ahp_weights['revenue'],               # Margin → Revenue
                ahp_weights['revenue'] * 0.3,         # Breakeven → Revenue-related
                ahp_weights['moral_hazard'] * 0.5,    # Churn → Moral Hazard
                ahp_weights['satisfaction'] * 0.4,    # Adoption → Satisfaction
            ])
            weights = weights / weights.sum()  # Normalize
        except ImportError:
            # Default weights if AHP not available
            weights = np.array([0.25, 0.30, 0.15, 0.15, 0.15])

    # Build decision matrix
    if metrics is None:
        metrics = derive_scenario_metrics()

    decision_matrix, scenario_names = build_decision_matrix(metrics)
    criteria_types = get_criteria_types()

    # Run TOPSIS
    result = topsis_rank(
        decision_matrix=decision_matrix,
        weights=weights,
        criteria_types=criteria_types,
        alternative_names=scenario_names
    )

    # Add metadata
    result['metrics'] = metrics
    result['weights'] = weights
    result['criteria'] = TOPSIS_CRITERIA
    result['scenarios'] = PRICING_SCENARIOS

    if verbose:
        print_topsis_report(result)

    return result


def topsis_sensitivity_analysis(
    base_weights: np.ndarray,
    variation_pct: float = 0.10
) -> Dict:
    """
    Perform sensitivity analysis on TOPSIS weights.

    Args:
        base_weights: Base criteria weights
        variation_pct: Percentage to vary each weight

    Returns:
        Dict with sensitivity results
    """
    metrics = derive_scenario_metrics()
    decision_matrix, scenario_names = build_decision_matrix(metrics)
    criteria_types = get_criteria_types()

    results = {'base': None, 'variations': {}}

    # Base case
    base_result = topsis_rank(decision_matrix, base_weights, criteria_types, scenario_names)
    results['base'] = {
        'ranking': base_result['ranked_alternatives'],
        'scores': base_result['ranked_scores'].tolist()
    }

    # Vary each weight
    for i in range(len(base_weights)):
        for direction in ['increase', 'decrease']:
            varied_weights = base_weights.copy()
            if direction == 'increase':
                varied_weights[i] *= (1 + variation_pct)
            else:
                varied_weights[i] *= (1 - variation_pct)
            varied_weights = varied_weights / varied_weights.sum()

            varied_result = topsis_rank(decision_matrix, varied_weights, criteria_types, scenario_names)

            key = f"C{i}_{direction}"
            results['variations'][key] = {
                'weight_change': f"{TOPSIS_CRITERIA[i]['short']} {direction}d by {variation_pct*100:.0f}%",
                'ranking': varied_result['ranked_alternatives'],
                'scores': varied_result['ranked_scores'].tolist(),
                'ranking_changed': varied_result['ranked_alternatives'] != results['base']['ranking']
            }

    return results


# =============================================================================
# Reporting
# =============================================================================

def print_topsis_report(result: Dict) -> None:
    """Print formatted TOPSIS analysis report."""
    print("\n" + "=" * 70)
    print("TOPSIS ANALYSIS: Pricing Scenario Ranking")
    print("=" * 70)

    print("\n## Pricing Scenarios")
    for name, scenario in PRICING_SCENARIOS.items():
        print(f"  {name}: {scenario['description']}")
        print(f"    Subsidy: ₹{scenario['subsidy']:,} ({scenario['subsidy_percent']:.1f}%)")
        print(f"    Monthly Fee: ₹{scenario['monthly_fee']}")

    print("\n## Criteria Weights")
    for i, weight in enumerate(result['weights']):
        crit = TOPSIS_CRITERIA[i]
        print(f"  {crit['short']:12s}: {weight:.4f} ({weight*100:.1f}%) — {crit['type']}")

    print("\n## Decision Matrix (Derived from Phase 1)")
    metrics = result['metrics']
    print(f"  {'Scenario':<14s} | {'Savings%':>8s} | {'Margin%':>8s} | {'Breakeven':>9s} | {'Churn%':>7s} | {'Adoption':>8s}")
    print("  " + "-" * 70)
    for name in PRICING_SCENARIOS.keys():
        m = metrics[name]
        print(f"  {name:<14s} | {m['customer_savings']:>7.1f}% | {m['company_margin']:>7.1f}% | {m['breakeven_months']:>7.0f} mo | {m['churn_risk']:>6.1f}% | {m['adoption_score']:>8.0f}")

    print("\n## TOPSIS Results")
    print("  Closeness Scores (higher = better):")
    for i, (name, score) in enumerate(zip(result['ranked_alternatives'], result['ranked_scores'])):
        rank_emoji = "🥇" if i == 0 else ("🥈" if i == 1 else ("🥉" if i == 2 else "  "))
        print(f"    {rank_emoji} {i+1}. {name:<14s}: C* = {score:.4f}")

    print("\n## Recommendation")
    best = result['ranked_alternatives'][0]
    best_scenario = PRICING_SCENARIOS[best]
    print(f"  RECOMMENDED: {best}")
    print(f"    → {best_scenario['description']}")
    print(f"    → Subsidy: ₹{best_scenario['subsidy']:,} | Fee: ₹{best_scenario['monthly_fee']}")
    print(f"    → Rationale: {best_scenario['rationale']}")

    print("\n" + "=" * 70)


def generate_topsis_report_section() -> str:
    """Generate markdown content for the MCDM Analysis Report section."""
    result = run_topsis_pricing(verbose=False)

    md = []
    md.append("## 7.2 TOPSIS for Pricing Scenario Selection\n")

    md.append("### Pricing Scenarios\n")
    for name, scenario in PRICING_SCENARIOS.items():
        md.append(f"- **{name}**: {scenario['description']} (Subsidy: {scenario['subsidy_percent']:.1f}%, Fee: ₹{scenario['monthly_fee']})\n")

    md.append("\n### Decision Matrix\n")
    md.append("| Scenario | Savings % | Margin % | Break-even | Churn % | Adoption |\n")
    md.append("|---|---|---|---|---|---|\n")
    for name in PRICING_SCENARIOS.keys():
        m = result['metrics'][name]
        md.append(f"| {name} | {m['customer_savings']:.1f}% | {m['company_margin']:.1f}% | {m['breakeven_months']:.0f} mo | {m['churn_risk']:.1f}% | {m['adoption_score']:.0f} |\n")

    md.append("\n### Criteria Weights\n")
    for i, w in enumerate(result['weights']):
        md.append(f"- {TOPSIS_CRITERIA[i]['name']}: {w:.4f} ({TOPSIS_CRITERIA[i]['type']})\n")

    md.append("\n### TOPSIS Ranking\n")
    md.append("| Rank | Scenario | Closeness Score |\n")
    md.append("|---|---|---|\n")
    for i, (name, score) in enumerate(zip(result['ranked_alternatives'], result['ranked_scores'])):
        md.append(f"| {i+1} | {name} | {score:.4f} |\n")

    md.append(f"\n### Recommendation\n")
    best = result['ranked_alternatives'][0]
    md.append(f"**{best}** scenario is recommended based on optimal balance of criteria.\n")

    return "".join(md)


if __name__ == "__main__":
    # Run analysis
    result = run_topsis_pricing(verbose=True)

    # Sensitivity analysis
    print("\n\n## Sensitivity Analysis")
    sensitivity = topsis_sensitivity_analysis(result['weights'])
    for key, val in sensitivity['variations'].items():
        if val['ranking_changed']:
            print(f"  ⚠️  {val['weight_change']}: Ranking changed to {val['ranking']}")
        else:
            print(f"  ✓  {val['weight_change']}: Ranking stable")
