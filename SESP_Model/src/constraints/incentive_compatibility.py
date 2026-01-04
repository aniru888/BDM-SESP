"""
Incentive Compatibility (IC) Constraint Checker
================================================

Ensures that customers self-select into the "correct" plan for their usage pattern.

IC Constraint:
    For each segment θ ∈ {Light, Moderate, Heavy}:
        U(θ, Plan_θ) ≥ U(θ, Plan_other) for all other plans

    Where:
        U(θ, Plan) = Service_Value - Total_Cost

    In simple terms:
        - Light users should prefer the Light plan
        - Moderate users should prefer the Moderate plan
        - Heavy users should prefer the Heavy plan

Key Insight:
    IC violations occur when:
    1. Overage caps are too low (heavy users game by choosing Light plan)
    2. Heavy plan fee is too high relative to Light + overage
    3. There's no effective penalty for choosing the "wrong" plan

Known IC Issue (as of 2025-01-04):
    Heavy users on Light plan: ₹499 + ₹200 (capped) = ₹699
    Heavy users on Heavy plan: ₹899 (no overage)
    Result: Heavy users prefer Light plan → IC VIOLATED

Run with: python -m src.constraints.incentive_compatibility
"""

from typing import Dict, List, Optional, Any, Tuple
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pricing.bucket_model import (
    SUBSCRIPTION_PLANS,
    calculate_monthly_bill,
)


# =============================================================================
# Usage Profiles by Segment
# =============================================================================

# Expected monthly usage hours by segment
SEGMENT_USAGE_HOURS = {
    'light': {
        'expected': 120,
        'min': 80,
        'max': 160,
        'description': 'Occasional AC use, mainly evenings/weekends',
    },
    'moderate': {
        'expected': 200,
        'min': 150,
        'max': 280,
        'description': 'Regular AC use, daily for comfort',
    },
    'heavy': {
        'expected': 320,
        'min': 280,
        'max': 450,
        'description': 'Heavy AC use, often running continuously',
    },
}

# Intended plan for each segment
SEGMENT_INTENDED_PLAN = {
    'light': 'light',
    'moderate': 'moderate',
    'heavy': 'heavy',
}

# Service value perception multiplier
# Heavy users value the service more (lower price sensitivity)
SERVICE_VALUE_MULTIPLIER = {
    'light': 1.0,
    'moderate': 1.1,
    'heavy': 1.2,
}


# =============================================================================
# Utility Calculation
# =============================================================================

def calculate_utility(
    segment: str,
    plan: str,
    efficiency_score: float = 75.0,
    service_value_base: float = 500,
) -> Dict[str, Any]:
    """
    Calculate utility of a plan for a customer segment.

    Utility = Service_Value - Monthly_Cost

    Where:
    - Service_Value = Perceived value of maintenance, warranty, IoT monitoring
    - Monthly_Cost = Base fee + Overage - Efficiency discount + GST

    Args:
        segment: Customer segment ('light', 'moderate', 'heavy')
        plan: Subscription plan ('light', 'moderate', 'heavy')
        efficiency_score: Efficiency score (0-100)
        service_value_base: Base perceived service value in ₹

    Returns:
        Dictionary with utility breakdown
    """
    # Get expected usage for this segment
    usage_hours = SEGMENT_USAGE_HOURS[segment]['expected']

    # Calculate monthly bill on this plan
    bill = calculate_monthly_bill(
        plan=plan,
        actual_hours=usage_hours,
        efficiency_score=efficiency_score,
        include_gst=True,
    )

    # Calculate perceived service value
    # Heavy users value service more (they rely on it more)
    value_multiplier = SERVICE_VALUE_MULTIPLIER.get(segment, 1.0)
    service_value = service_value_base * value_multiplier

    # Utility = Value - Cost
    utility = service_value - bill['total_bill']

    # Is this the "intended" plan for this segment?
    intended = SEGMENT_INTENDED_PLAN[segment] == plan

    return {
        'segment': segment,
        'plan': plan,
        'usage_hours': usage_hours,
        'plan_hours_included': SUBSCRIPTION_PLANS[plan]['hours_included'],
        'excess_hours': max(0, usage_hours - SUBSCRIPTION_PLANS[plan]['hours_included']),
        'monthly_cost': bill['total_bill'],
        'cost_breakdown': {
            'base_fee': bill['base_fee'],
            'overage': bill['overage']['overage_fee'],
            'efficiency_discount': bill['efficiency']['discount_amount'],
            'gst': bill['gst_amount'],
        },
        'service_value': service_value,
        'utility': utility,
        'is_intended_plan': intended,
    }


def calculate_all_utilities(
    segment: str,
    efficiency_score: float = 75.0,
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate utility for all plans for a given segment.

    Args:
        segment: Customer segment
        efficiency_score: Efficiency score

    Returns:
        Dictionary mapping plan name to utility details
    """
    utilities = {}
    for plan in SUBSCRIPTION_PLANS.keys():
        utilities[plan] = calculate_utility(segment, plan, efficiency_score)
    return utilities


# =============================================================================
# IC Constraint Checks
# =============================================================================

def check_ic_light(efficiency_score: float = 75.0) -> Dict[str, Any]:
    """
    Check if Light users prefer the Light plan.

    U_light(Light) ≥ U_light(Moderate) AND U_light(Light) ≥ U_light(Heavy)
    """
    utilities = calculate_all_utilities('light', efficiency_score)

    utility_light = utilities['light']['utility']
    utility_moderate = utilities['moderate']['utility']
    utility_heavy = utilities['heavy']['utility']

    # Light users should prefer Light plan
    prefers_light_over_moderate = utility_light >= utility_moderate
    prefers_light_over_heavy = utility_light >= utility_heavy
    satisfied = prefers_light_over_moderate and prefers_light_over_heavy

    # Find best plan for light users
    best_plan = max(utilities.items(), key=lambda x: x[1]['utility'])[0]

    return {
        'constraint': 'IC_Light',
        'segment': 'light',
        'intended_plan': 'light',
        'satisfied': satisfied,
        'utilities': {
            'light': utility_light,
            'moderate': utility_moderate,
            'heavy': utility_heavy,
        },
        'best_plan': best_plan,
        'prefers_light_over_moderate': prefers_light_over_moderate,
        'prefers_light_over_heavy': prefers_light_over_heavy,
        'violation_details': _get_violation_details('light', utilities) if not satisfied else None,
    }


def check_ic_moderate(efficiency_score: float = 75.0) -> Dict[str, Any]:
    """
    Check if Moderate users prefer the Moderate plan.

    U_moderate(Moderate) ≥ U_moderate(Light) AND U_moderate(Moderate) ≥ U_moderate(Heavy)
    """
    utilities = calculate_all_utilities('moderate', efficiency_score)

    utility_light = utilities['light']['utility']
    utility_moderate = utilities['moderate']['utility']
    utility_heavy = utilities['heavy']['utility']

    prefers_moderate_over_light = utility_moderate >= utility_light
    prefers_moderate_over_heavy = utility_moderate >= utility_heavy
    satisfied = prefers_moderate_over_light and prefers_moderate_over_heavy

    best_plan = max(utilities.items(), key=lambda x: x[1]['utility'])[0]

    return {
        'constraint': 'IC_Moderate',
        'segment': 'moderate',
        'intended_plan': 'moderate',
        'satisfied': satisfied,
        'utilities': {
            'light': utility_light,
            'moderate': utility_moderate,
            'heavy': utility_heavy,
        },
        'best_plan': best_plan,
        'prefers_moderate_over_light': prefers_moderate_over_light,
        'prefers_moderate_over_heavy': prefers_moderate_over_heavy,
        'violation_details': _get_violation_details('moderate', utilities) if not satisfied else None,
    }


def check_ic_heavy(efficiency_score: float = 75.0) -> Dict[str, Any]:
    """
    Check if Heavy users prefer the Heavy plan.

    U_heavy(Heavy) ≥ U_heavy(Light) AND U_heavy(Heavy) ≥ U_heavy(Moderate)

    NOTE: This is the most likely constraint to be violated due to overage caps.
    """
    utilities = calculate_all_utilities('heavy', efficiency_score)

    utility_light = utilities['light']['utility']
    utility_moderate = utilities['moderate']['utility']
    utility_heavy = utilities['heavy']['utility']

    prefers_heavy_over_light = utility_heavy >= utility_light
    prefers_heavy_over_moderate = utility_heavy >= utility_moderate
    satisfied = prefers_heavy_over_light and prefers_heavy_over_moderate

    best_plan = max(utilities.items(), key=lambda x: x[1]['utility'])[0]

    return {
        'constraint': 'IC_Heavy',
        'segment': 'heavy',
        'intended_plan': 'heavy',
        'satisfied': satisfied,
        'utilities': {
            'light': utility_light,
            'moderate': utility_moderate,
            'heavy': utility_heavy,
        },
        'best_plan': best_plan,
        'prefers_heavy_over_light': prefers_heavy_over_light,
        'prefers_heavy_over_moderate': prefers_heavy_over_moderate,
        'violation_details': _get_violation_details('heavy', utilities) if not satisfied else None,
    }


def _get_violation_details(
    segment: str,
    utilities: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Get details about an IC violation."""
    intended = SEGMENT_INTENDED_PLAN[segment]
    best = max(utilities.items(), key=lambda x: x[1]['utility'])
    best_plan, best_utility = best[0], best[1]

    if best_plan == intended:
        return None

    intended_utility = utilities[intended]
    utility_gap = best_utility['utility'] - intended_utility['utility']
    cost_gap = intended_utility['monthly_cost'] - best_utility['monthly_cost']

    return {
        'segment': segment,
        'intended_plan': intended,
        'preferred_plan': best_plan,
        'utility_gap': utility_gap,
        'cost_gap': cost_gap,
        'reason': f"{segment.title()} users save ₹{cost_gap:.0f}/month by choosing {best_plan.title()} instead of {intended.title()} plan",
    }


# =============================================================================
# Aggregate Validation
# =============================================================================

def validate_ic(efficiency_score: float = 75.0) -> Dict[str, Any]:
    """
    Validate IC constraint for all segments.

    Args:
        efficiency_score: Efficiency score for calculations

    Returns:
        Dictionary with overall status and individual results
    """
    results = {
        'light': check_ic_light(efficiency_score),
        'moderate': check_ic_moderate(efficiency_score),
        'heavy': check_ic_heavy(efficiency_score),
    }

    all_satisfied = all(r['satisfied'] for r in results.values())
    violations = [name for name, r in results.items() if not r['satisfied']]

    if all_satisfied:
        message = "✓ All IC constraints satisfied — customers will self-select correctly"
    else:
        message = f"✗ IC violations for: {', '.join(violations)}"

    return {
        'all_satisfied': all_satisfied,
        'violations': violations,
        'num_passed': sum(1 for r in results.values() if r['satisfied']),
        'num_total': len(results),
        'message': message,
        'individual_results': results,
        'recommendations': _generate_ic_recommendations(results) if not all_satisfied else None,
    }


def identify_ic_violations(efficiency_score: float = 75.0) -> List[Dict[str, Any]]:
    """
    Identify all IC violations and return details.

    Returns:
        List of violation details with recommendations
    """
    validation = validate_ic(efficiency_score)
    violations = []

    for segment, result in validation['individual_results'].items():
        if not result['satisfied']:
            violation = result['violation_details'].copy()
            violation['segment_utilities'] = result['utilities']
            violation['recommendation'] = _get_segment_recommendation(segment, result)
            violations.append(violation)

    return violations


def _generate_ic_recommendations(results: Dict[str, Any]) -> List[str]:
    """Generate recommendations to fix IC violations."""
    recommendations = []

    for segment, result in results.items():
        if not result['satisfied']:
            recommendations.append(_get_segment_recommendation(segment, result))

    return recommendations


def _get_segment_recommendation(segment: str, result: Dict[str, Any]) -> str:
    """Generate recommendation for a specific segment's IC violation."""
    if result['satisfied']:
        return f"{segment.title()}: No action needed"

    details = result['violation_details']
    preferred = details['preferred_plan']
    intended = details['intended_plan']
    cost_gap = details['cost_gap']

    if segment == 'heavy' and preferred == 'light':
        return (
            f"HEAVY USERS prefer Light plan due to overage cap. "
            f"Options: (1) Raise Light overage cap from ₹200 to ₹400+, "
            f"(2) Lower Heavy plan fee from ₹899 to ~₹{899 - cost_gap:.0f}, "
            f"(3) Add non-monetary penalties for sustained overuse"
        )
    elif segment == 'heavy' and preferred == 'moderate':
        return (
            f"HEAVY USERS prefer Moderate plan. "
            f"Options: (1) Lower Heavy plan fee, (2) Raise Moderate overage cap"
        )
    elif segment == 'moderate' and preferred == 'light':
        return (
            f"MODERATE USERS prefer Light plan. "
            f"Options: (1) Raise Light overage cap, (2) Lower Moderate plan fee"
        )
    elif segment == 'light' and preferred != 'light':
        return (
            f"LIGHT USERS prefer {preferred.title()} plan. "
            f"This suggests Light plan fee is too high or value proposition is unclear"
        )
    else:
        return f"{segment.title()} users prefer {preferred.title()} instead of {intended.title()}"


# =============================================================================
# IC Sensitivity Analysis
# =============================================================================

def analyze_ic_sensitivity(
    parameter: str = 'overage_cap',
    range_values: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Analyze how IC constraint changes with parameter adjustments.

    Args:
        parameter: 'overage_cap' or 'heavy_fee'
        range_values: Values to test

    Returns:
        Dictionary with sensitivity results
    """
    if parameter == 'overage_cap':
        if range_values is None:
            range_values = [100, 200, 300, 400, 500, 600]
        return _analyze_overage_cap_sensitivity(range_values)
    elif parameter == 'heavy_fee':
        if range_values is None:
            range_values = [699, 749, 799, 849, 899, 949]
        return _analyze_heavy_fee_sensitivity(range_values)
    else:
        raise ValueError(f"Unknown parameter: {parameter}")


def _analyze_overage_cap_sensitivity(cap_values: List[float]) -> Dict[str, Any]:
    """Analyze how overage cap affects IC for heavy users."""
    results = []

    for cap in cap_values:
        # Temporarily modify the plan cap
        original_cap = SUBSCRIPTION_PLANS['light']['max_overage']
        SUBSCRIPTION_PLANS['light']['max_overage'] = cap

        try:
            ic_heavy = check_ic_heavy()
            results.append({
                'overage_cap': cap,
                'ic_satisfied': ic_heavy['satisfied'],
                'utility_light': ic_heavy['utilities']['light'],
                'utility_heavy': ic_heavy['utilities']['heavy'],
                'best_plan': ic_heavy['best_plan'],
            })
        finally:
            # Restore original cap
            SUBSCRIPTION_PLANS['light']['max_overage'] = original_cap

    # Find breakeven cap
    breakeven_cap = None
    for r in results:
        if r['ic_satisfied']:
            breakeven_cap = r['overage_cap']
            break

    return {
        'parameter': 'overage_cap',
        'results': results,
        'breakeven_value': breakeven_cap,
        'recommendation': (
            f"Raise Light plan overage cap to ₹{breakeven_cap} to achieve IC"
            if breakeven_cap else
            "Even highest tested cap doesn't achieve IC — consider fee adjustments"
        ),
    }


def _analyze_heavy_fee_sensitivity(fee_values: List[float]) -> Dict[str, Any]:
    """Analyze how Heavy plan fee affects IC."""
    results = []

    for fee in fee_values:
        # Temporarily modify the Heavy plan fee
        original_fee = SUBSCRIPTION_PLANS['heavy']['monthly_fee']
        SUBSCRIPTION_PLANS['heavy']['monthly_fee'] = fee

        try:
            ic_heavy = check_ic_heavy()
            results.append({
                'heavy_fee': fee,
                'ic_satisfied': ic_heavy['satisfied'],
                'utility_light': ic_heavy['utilities']['light'],
                'utility_heavy': ic_heavy['utilities']['heavy'],
                'best_plan': ic_heavy['best_plan'],
            })
        finally:
            # Restore original fee
            SUBSCRIPTION_PLANS['heavy']['monthly_fee'] = original_fee

    # Find breakeven fee
    breakeven_fee = None
    for r in results:
        if r['ic_satisfied']:
            breakeven_fee = r['heavy_fee']
            break

    return {
        'parameter': 'heavy_fee',
        'results': results,
        'breakeven_value': breakeven_fee,
        'recommendation': (
            f"Lower Heavy plan fee to ₹{breakeven_fee} to achieve IC"
            if breakeven_fee else
            "Fee adjustments alone may not achieve IC — consider overage cap changes"
        ),
    }


# =============================================================================
# Cost Comparison Helper
# =============================================================================

def compare_plan_costs_for_segment(
    segment: str,
    efficiency_score: float = 75.0,
) -> Dict[str, Any]:
    """
    Compare monthly costs of all plans for a given segment.

    Useful for understanding why IC violations occur.

    Args:
        segment: Customer segment
        efficiency_score: Efficiency score

    Returns:
        Dictionary with cost comparison
    """
    utilities = calculate_all_utilities(segment, efficiency_score)

    costs = {}
    for plan, util in utilities.items():
        costs[plan] = {
            'monthly_cost': util['monthly_cost'],
            'base_fee': util['cost_breakdown']['base_fee'],
            'overage': util['cost_breakdown']['overage'],
            'discount': util['cost_breakdown']['efficiency_discount'],
            'gst': util['cost_breakdown']['gst'],
            'excess_hours': util['excess_hours'],
            'is_intended': util['is_intended_plan'],
        }

    # Find cheapest
    cheapest = min(costs.items(), key=lambda x: x[1]['monthly_cost'])

    return {
        'segment': segment,
        'usage_hours': SEGMENT_USAGE_HOURS[segment]['expected'],
        'costs_by_plan': costs,
        'cheapest_plan': cheapest[0],
        'cheapest_cost': cheapest[1]['monthly_cost'],
        'intended_plan': SEGMENT_INTENDED_PLAN[segment],
        'gaming_possible': cheapest[0] != SEGMENT_INTENDED_PLAN[segment],
    }


# =============================================================================
# Module Test
# =============================================================================

if __name__ == "__main__":
    print("Incentive Compatibility (IC) Constraint Checker Demo")
    print("=" * 60)

    # Run validation
    print("\nValidating IC Constraints...")
    validation = validate_ic()

    print(f"\n{validation['message']}")
    print(f"Passed: {validation['num_passed']}/{validation['num_total']} constraints")

    # Show individual results
    print("\n" + "-" * 60)
    print("Individual Segment Results:")

    for segment, result in validation['individual_results'].items():
        status = "✓" if result['satisfied'] else "✗"
        print(f"\n  {status} {segment.upper()} Users:")
        print(f"     Intended plan: {result['intended_plan'].title()}")
        print(f"     Best plan:     {result['best_plan'].title()}")
        print(f"     Utilities:     Light={result['utilities']['light']:.0f}, "
              f"Moderate={result['utilities']['moderate']:.0f}, "
              f"Heavy={result['utilities']['heavy']:.0f}")

        if not result['satisfied'] and result['violation_details']:
            print(f"     ⚠ {result['violation_details']['reason']}")

    # Show cost comparison for heavy users
    print("\n" + "-" * 60)
    print("\nCost Comparison: Heavy User on Different Plans")
    heavy_costs = compare_plan_costs_for_segment('heavy')

    print(f"\n  Usage: {heavy_costs['usage_hours']} hours/month")
    print(f"\n  {'Plan':<12} {'Cost':>10} {'Overage':>10} {'Net':>10}")
    print(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*10}")

    for plan, costs in heavy_costs['costs_by_plan'].items():
        marker = " ← Intended" if costs['is_intended'] else ""
        print(f"  {plan.title():<12} ₹{costs['base_fee']:>8.0f} "
              f"₹{costs['overage']:>8.0f} ₹{costs['monthly_cost']:>8.0f}{marker}")

    if heavy_costs['gaming_possible']:
        print(f"\n  ⚠ Gaming possible! Heavy users prefer {heavy_costs['cheapest_plan'].title()} plan")

    # Show recommendations
    if validation['recommendations']:
        print("\n" + "-" * 60)
        print("\nRecommendations to Fix IC Violations:")
        for i, rec in enumerate(validation['recommendations'], 1):
            print(f"\n  {i}. {rec}")

    # Sensitivity analysis
    print("\n" + "-" * 60)
    print("\nSensitivity Analysis: Overage Cap Impact")
    sensitivity = analyze_ic_sensitivity('overage_cap', [200, 300, 400, 500])

    print(f"\n  {'Cap':>8} | {'IC Heavy':>10} | {'Best Plan':>12}")
    print(f"  {'-'*8} | {'-'*10} | {'-'*12}")
    for r in sensitivity['results']:
        status = "✓ Pass" if r['ic_satisfied'] else "✗ Fail"
        print(f"  ₹{r['overage_cap']:>6.0f} | {status:>10} | {r['best_plan'].title():>12}")

    print(f"\n  Recommendation: {sensitivity['recommendation']}")

    print("\n✓ Incentive Compatibility module working correctly!")
