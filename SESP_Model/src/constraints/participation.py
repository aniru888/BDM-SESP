"""
Participation Constraint Checker
================================

Ensures SESP is attractive enough for customers to participate.

Participation Constraint (PC):
    NPV_customer(SESP) < NPV_customer(Alternative) × (1 - threshold)

    Where:
    - threshold = minimum savings required (default 10%)
    - Alternative = Purchase, EMI, or Rental

Key Insight:
    The participation constraint is the customer's "rational choice" test.
    Even if SESP is profitable for the firm, customers won't sign up
    unless SESP offers meaningful savings over alternatives.

Run with: python -m src.constraints.participation
"""

from typing import Dict, List, Optional, Any, Tuple
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.alternatives.calculators import (
    calculate_purchase_cost,
    calculate_emi_cost,
    calculate_rental_cost,
    calculate_sesp_cost,
    compare_alternatives,
    get_default_expected_hours,
    APPLIANCE_MRP,
)
from src.adjustments.india_specific import CUSTOMER_DISCOUNT_RATES


# =============================================================================
# Participation Constraint Thresholds
# =============================================================================

# Default savings thresholds by alternative
DEFAULT_THRESHOLDS = {
    'purchase': 0.10,  # SESP must be at least 10% cheaper than purchase
    'emi': 0.05,       # SESP must be at least 5% cheaper than EMI
    'rental': 0.00,    # SESP can be same price as rental (offers ownership path)
}

# Segment-specific threshold adjustments
# Light users are more price-sensitive → need higher savings
# Heavy users value service more → accept lower savings
SEGMENT_THRESHOLD_MULTIPLIERS = {
    'light': 1.20,     # 20% higher threshold (need 12% savings vs purchase)
    'moderate': 1.00,  # Base threshold
    'heavy': 0.80,     # 20% lower threshold (accept 8% savings vs purchase)
}


# =============================================================================
# Core Participation Constraint Functions
# =============================================================================

def check_pc_vs_purchase(
    sesp_params: Dict[str, Any],
    mrp: float,
    tenure_years: int,
    segment: str = 'moderate',
    appliance: str = 'AC',
    threshold: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Check Participation Constraint: SESP vs Outright Purchase.

    The fundamental constraint - customer must prefer SESP over buying.

    Args:
        sesp_params: Dictionary with 'subsidized_price', 'plan', 'efficiency_score', 'deposit'
        mrp: Full appliance price
        tenure_years: Comparison horizon
        segment: Customer segment
        appliance: 'AC' or 'FRIDGE'
        threshold: Override default threshold

    Returns:
        Dictionary with constraint status, savings, and recommendations
    """
    # Get threshold
    if threshold is None:
        base_threshold = DEFAULT_THRESHOLDS['purchase']
        multiplier = SEGMENT_THRESHOLD_MULTIPLIERS.get(segment, 1.0)
        threshold = base_threshold * multiplier

    tenure_months = tenure_years * 12

    # Calculate purchase cost
    purchase = calculate_purchase_cost(
        mrp=mrp,
        tenure_years=tenure_years,
        segment=segment,
        appliance=appliance,
    )

    # Calculate SESP cost
    sesp = calculate_sesp_cost(
        subsidized_price=sesp_params.get('subsidized_price', mrp * 0.7),
        tenure_months=tenure_months,
        plan=sesp_params.get('plan', 'moderate'),
        segment=segment,
        expected_hours=sesp_params.get('expected_hours', get_default_expected_hours(segment, appliance)),
        efficiency_score=sesp_params.get('efficiency_score', 75.0),
        deposit=sesp_params.get('deposit', 5000),
    )

    # Calculate target NPV (what SESP must beat)
    target_npv = purchase['total_npv'] * (1 - threshold)

    # Calculate actual savings
    savings = purchase['total_npv'] - sesp['total_npv']
    savings_percent = (savings / purchase['total_npv']) * 100 if purchase['total_npv'] > 0 else 0

    # Check constraint
    satisfied = sesp['total_npv'] < target_npv

    # Calculate slack (positive = room to spare, negative = shortfall)
    slack = target_npv - sesp['total_npv']
    slack_percent = (slack / purchase['total_npv']) * 100 if purchase['total_npv'] > 0 else 0

    return {
        'constraint': 'PC_vs_Purchase',
        'satisfied': satisfied,
        'sesp_npv': sesp['total_npv'],
        'purchase_npv': purchase['total_npv'],
        'target_npv': target_npv,
        'threshold': threshold,
        'threshold_percent': threshold * 100,
        'actual_savings': savings,
        'actual_savings_percent': savings_percent,
        'slack': slack,
        'slack_percent': slack_percent,
        'recommendation': _get_recommendation_purchase(satisfied, slack, sesp_params, mrp),
    }


def check_pc_vs_emi(
    sesp_params: Dict[str, Any],
    mrp: float,
    tenure_years: int,
    emi_tenure_months: int = 12,
    segment: str = 'moderate',
    appliance: str = 'AC',
    threshold: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Check Participation Constraint: SESP vs EMI Purchase.

    EMI is the closest competitor - same appliance, financed payment.

    Args:
        sesp_params: SESP parameters
        mrp: Full appliance price
        tenure_years: Comparison horizon
        emi_tenure_months: EMI payment period
        segment: Customer segment
        appliance: 'AC' or 'FRIDGE'
        threshold: Override default threshold

    Returns:
        Dictionary with constraint status and details
    """
    if threshold is None:
        base_threshold = DEFAULT_THRESHOLDS['emi']
        multiplier = SEGMENT_THRESHOLD_MULTIPLIERS.get(segment, 1.0)
        threshold = base_threshold * multiplier

    tenure_months = tenure_years * 12

    # Calculate EMI cost
    emi = calculate_emi_cost(
        mrp=mrp,
        emi_tenure_months=emi_tenure_months,
        comparison_horizon_years=tenure_years,
        segment=segment,
        appliance=appliance,
    )

    # Calculate SESP cost
    sesp = calculate_sesp_cost(
        subsidized_price=sesp_params.get('subsidized_price', mrp * 0.7),
        tenure_months=tenure_months,
        plan=sesp_params.get('plan', 'moderate'),
        segment=segment,
        expected_hours=sesp_params.get('expected_hours', get_default_expected_hours(segment, appliance)),
        efficiency_score=sesp_params.get('efficiency_score', 75.0),
        deposit=sesp_params.get('deposit', 5000),
    )

    # Calculate target and savings
    target_npv = emi['total_npv'] * (1 - threshold)
    savings = emi['total_npv'] - sesp['total_npv']
    savings_percent = (savings / emi['total_npv']) * 100 if emi['total_npv'] > 0 else 0

    satisfied = sesp['total_npv'] < target_npv
    slack = target_npv - sesp['total_npv']

    return {
        'constraint': 'PC_vs_EMI',
        'satisfied': satisfied,
        'sesp_npv': sesp['total_npv'],
        'emi_npv': emi['total_npv'],
        'emi_tenure_months': emi_tenure_months,
        'target_npv': target_npv,
        'threshold': threshold,
        'threshold_percent': threshold * 100,
        'actual_savings': savings,
        'actual_savings_percent': savings_percent,
        'slack': slack,
    }


def check_pc_vs_rental(
    sesp_params: Dict[str, Any],
    tenure_years: int,
    segment: str = 'moderate',
    appliance: str = 'AC',
    threshold: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Check Participation Constraint: SESP vs Rental.

    Rental is the "no commitment" alternative. SESP offers path to ownership.

    Args:
        sesp_params: SESP parameters
        tenure_years: Comparison horizon
        segment: Customer segment
        appliance: 'AC' or 'FRIDGE'
        threshold: Override default threshold

    Returns:
        Dictionary with constraint status and details
    """
    if threshold is None:
        threshold = DEFAULT_THRESHOLDS['rental']

    tenure_months = tenure_years * 12

    # Calculate rental cost
    rental = calculate_rental_cost(
        tenure_months=tenure_months,
        segment=segment,
        appliance=appliance,
    )

    # Calculate SESP cost
    sesp = calculate_sesp_cost(
        subsidized_price=sesp_params.get('subsidized_price', APPLIANCE_MRP.get(appliance, 45000) * 0.7),
        tenure_months=tenure_months,
        plan=sesp_params.get('plan', 'moderate'),
        segment=segment,
        expected_hours=sesp_params.get('expected_hours', get_default_expected_hours(segment, appliance)),
        efficiency_score=sesp_params.get('efficiency_score', 75.0),
        deposit=sesp_params.get('deposit', 5000),
    )

    # Calculate target and savings
    target_npv = rental['total_npv'] * (1 - threshold)
    savings = rental['total_npv'] - sesp['total_npv']
    savings_percent = (savings / rental['total_npv']) * 100 if rental['total_npv'] > 0 else 0

    satisfied = sesp['total_npv'] < target_npv
    slack = target_npv - sesp['total_npv']

    return {
        'constraint': 'PC_vs_Rental',
        'satisfied': satisfied,
        'sesp_npv': sesp['total_npv'],
        'rental_npv': rental['total_npv'],
        'target_npv': target_npv,
        'threshold': threshold,
        'actual_savings': savings,
        'actual_savings_percent': savings_percent,
        'slack': slack,
        'note': 'SESP offers path to ownership; rental is pure expense',
    }


# =============================================================================
# Aggregate Validation
# =============================================================================

def validate_participation(
    sesp_params: Dict[str, Any],
    mrp: float,
    tenure_years: int,
    segment: str = 'moderate',
    appliance: str = 'AC',
    check_emi: bool = True,
    check_rental: bool = True,
) -> Dict[str, Any]:
    """
    Validate participation constraint against all alternatives.

    All constraints must pass for SESP to be viable.

    Args:
        sesp_params: SESP configuration
        mrp: Full appliance price
        tenure_years: Comparison horizon
        segment: Customer segment
        appliance: 'AC' or 'FRIDGE'
        check_emi: Whether to check vs EMI
        check_rental: Whether to check vs Rental

    Returns:
        Dictionary with overall status and individual constraint results
    """
    results = {}

    # Always check vs purchase (primary constraint)
    results['vs_purchase'] = check_pc_vs_purchase(
        sesp_params, mrp, tenure_years, segment, appliance
    )

    # Optionally check vs EMI
    if check_emi:
        results['vs_emi_12m'] = check_pc_vs_emi(
            sesp_params, mrp, tenure_years, 12, segment, appliance
        )
        results['vs_emi_24m'] = check_pc_vs_emi(
            sesp_params, mrp, tenure_years, 24, segment, appliance
        )

    # Optionally check vs rental
    if check_rental:
        results['vs_rental'] = check_pc_vs_rental(
            sesp_params, tenure_years, segment, appliance
        )

    # Aggregate result
    all_satisfied = all(r['satisfied'] for r in results.values())
    failed_constraints = [name for name, r in results.items() if not r['satisfied']]

    # Summary message
    if all_satisfied:
        message = "✓ All participation constraints satisfied"
    else:
        message = f"✗ Failed constraints: {', '.join(failed_constraints)}"

    return {
        'all_satisfied': all_satisfied,
        'failed_constraints': failed_constraints,
        'num_passed': sum(1 for r in results.values() if r['satisfied']),
        'num_total': len(results),
        'message': message,
        'individual_results': results,
        'parameters': {
            'sesp_params': sesp_params,
            'mrp': mrp,
            'tenure_years': tenure_years,
            'segment': segment,
            'appliance': appliance,
        },
    }


# =============================================================================
# Boundary Finding
# =============================================================================

def find_pc_boundary(
    mrp: float,
    tenure_years: int,
    segment: str = 'moderate',
    appliance: str = 'AC',
    sesp_plan: str = 'moderate',
    efficiency_score: float = 75.0,
    deposit: float = 5000,
    threshold: float = 0.10,
) -> Dict[str, Any]:
    """
    Find the maximum subsidized price that satisfies participation constraint.

    Uses binary search to find the price boundary.

    Args:
        mrp: Full appliance price
        tenure_years: Comparison horizon
        segment: Customer segment
        appliance: 'AC' or 'FRIDGE'
        sesp_plan: Subscription plan
        efficiency_score: Expected efficiency
        deposit: Security deposit
        threshold: Required savings threshold

    Returns:
        Dictionary with boundary price and margin details
    """
    tenure_months = tenure_years * 12

    # Get purchase baseline
    purchase = calculate_purchase_cost(mrp, tenure_years, segment, appliance)
    target_npv = purchase['total_npv'] * (1 - threshold)

    # Binary search for subsidized price
    low_price = mrp * 0.3   # Minimum 70% subsidy
    high_price = mrp * 0.95  # Maximum 5% subsidy

    for _ in range(50):
        mid_price = (low_price + high_price) / 2

        sesp = calculate_sesp_cost(
            subsidized_price=mid_price,
            tenure_months=tenure_months,
            plan=sesp_plan,
            segment=segment,
            expected_hours=get_default_expected_hours(segment, appliance),
            efficiency_score=efficiency_score,
            deposit=deposit,
        )

        if abs(sesp['total_npv'] - target_npv) < 100:
            break

        if sesp['total_npv'] > target_npv:
            high_price = mid_price  # Too expensive, need more subsidy
        else:
            low_price = mid_price  # Can afford less subsidy

    boundary_price = mid_price
    boundary_subsidy = mrp - boundary_price

    # Verify the boundary
    sesp_at_boundary = calculate_sesp_cost(
        subsidized_price=boundary_price,
        tenure_months=tenure_months,
        plan=sesp_plan,
        segment=segment,
        expected_hours=get_default_expected_hours(segment, appliance),
        efficiency_score=efficiency_score,
        deposit=deposit,
    )

    return {
        'boundary_subsidized_price': round(boundary_price, 0),
        'boundary_subsidy': round(boundary_subsidy, 0),
        'subsidy_percent': round((boundary_subsidy / mrp) * 100, 1),
        'mrp': mrp,
        'purchase_npv': purchase['total_npv'],
        'target_npv': target_npv,
        'sesp_npv_at_boundary': sesp_at_boundary['total_npv'],
        'threshold': threshold,
        'threshold_percent': threshold * 100,
        'recommendation': f"Price must be ≤₹{boundary_price:,.0f} (subsidy ≥₹{boundary_subsidy:,.0f}) "
                         f"to achieve {threshold*100:.0f}% savings",
    }


def find_pc_boundary_by_fee(
    mrp: float,
    subsidized_price: float,
    tenure_years: int,
    segment: str = 'moderate',
    appliance: str = 'AC',
    sesp_plan: str = 'moderate',
    efficiency_score: float = 75.0,
    threshold: float = 0.10,
) -> Dict[str, Any]:
    """
    Find the maximum monthly fee that satisfies participation constraint.

    Given a fixed subsidized price, find what fee is acceptable.

    Args:
        mrp: Full appliance price
        subsidized_price: Fixed upfront price
        tenure_years: Comparison horizon
        segment: Customer segment
        appliance: 'AC' or 'FRIDGE'
        sesp_plan: Subscription plan (for hours included)
        efficiency_score: Expected efficiency
        threshold: Required savings threshold

    Returns:
        Dictionary with boundary fee and margin details
    """
    from src.pricing.bucket_model import SUBSCRIPTION_PLANS

    tenure_months = tenure_years * 12

    # Get purchase baseline
    purchase = calculate_purchase_cost(mrp, tenure_years, segment, appliance)
    target_npv = purchase['total_npv'] * (1 - threshold)

    # Get plan details for overage calculation
    plan_details = SUBSCRIPTION_PLANS[sesp_plan]

    # Binary search for monthly fee
    low_fee = 199     # Minimum viable fee
    high_fee = 1499   # Maximum reasonable fee

    for _ in range(50):
        mid_fee = (low_fee + high_fee) / 2

        # Create temporary plan with modified fee for testing
        from src.pricing.bucket_model import calculate_monthly_bill

        # Calculate what monthly payment would be at this fee
        # (Note: this is approximate since we're modifying the fee)
        monthly_with_gst = mid_fee * 1.18

        # Approximate SESP NPV
        from src.adjustments.india_specific import npv_customer
        upfront_with_gst = subsidized_price * 1.18
        monthly_payments = [monthly_with_gst] * tenure_months
        sesp_npv_approx = upfront_with_gst + npv_customer(monthly_payments, segment)

        if abs(sesp_npv_approx - target_npv) < 100:
            break

        if sesp_npv_approx > target_npv:
            high_fee = mid_fee  # Fee too high
        else:
            low_fee = mid_fee   # Can afford higher fee

    boundary_fee = mid_fee

    return {
        'boundary_monthly_fee': round(boundary_fee, 0),
        'subsidized_price': subsidized_price,
        'mrp': mrp,
        'purchase_npv': purchase['total_npv'],
        'target_npv': target_npv,
        'threshold': threshold,
        'threshold_percent': threshold * 100,
        'recommendation': f"Monthly fee must be ≤₹{boundary_fee:,.0f} "
                         f"at ₹{subsidized_price:,.0f} upfront "
                         f"to achieve {threshold*100:.0f}% savings",
    }


# =============================================================================
# Recommendation Helpers
# =============================================================================

def _get_recommendation_purchase(
    satisfied: bool,
    slack: float,
    sesp_params: Dict[str, Any],
    mrp: float,
) -> str:
    """Generate recommendation based on constraint status."""
    if satisfied:
        if slack > mrp * 0.05:  # More than 5% slack
            return "PC well satisfied. Consider reducing subsidy by ~₹{:,.0f}".format(slack * 0.5)
        else:
            return "PC satisfied with tight margin. Current pricing is near optimal."
    else:
        shortfall = -slack
        if shortfall < mrp * 0.05:
            return "PC nearly satisfied. Increase subsidy by ~₹{:,.0f}".format(shortfall * 1.2)
        elif shortfall < mrp * 0.10:
            return "PC violated. Need significant subsidy increase (~₹{:,.0f}) or longer tenure".format(shortfall)
        else:
            return "PC severely violated. Consider restructuring pricing entirely."


def analyze_pc_sensitivity(
    mrp: float,
    tenure_years: int,
    segment: str = 'moderate',
    appliance: str = 'AC',
    sesp_plan: str = 'moderate',
    subsidy_range: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Analyze how participation constraint changes with subsidy level.

    Useful for understanding the subsidy-savings relationship.

    Args:
        mrp: Full appliance price
        tenure_years: Comparison horizon
        segment: Customer segment
        appliance: 'AC' or 'FRIDGE'
        sesp_plan: Subscription plan
        subsidy_range: List of subsidy amounts to test

    Returns:
        Dictionary with sensitivity analysis results
    """
    if subsidy_range is None:
        # Test subsidies from 10% to 50% of MRP
        subsidy_range = [mrp * p for p in [0.10, 0.20, 0.30, 0.40, 0.50]]

    results = []
    for subsidy in subsidy_range:
        subsidized_price = mrp - subsidy

        sesp_params = {
            'subsidized_price': subsidized_price,
            'plan': sesp_plan,
            'efficiency_score': 75.0,
            'deposit': 5000,
        }

        pc_result = check_pc_vs_purchase(
            sesp_params, mrp, tenure_years, segment, appliance
        )

        results.append({
            'subsidy': subsidy,
            'subsidy_percent': (subsidy / mrp) * 100,
            'subsidized_price': subsidized_price,
            'sesp_npv': pc_result['sesp_npv'],
            'purchase_npv': pc_result['purchase_npv'],
            'savings_percent': pc_result['actual_savings_percent'],
            'satisfied': pc_result['satisfied'],
            'slack': pc_result['slack'],
        })

    # Find breakeven subsidy
    breakeven_subsidy = None
    for r in results:
        if r['satisfied']:
            breakeven_subsidy = r['subsidy']
            break

    return {
        'sensitivity_results': results,
        'breakeven_subsidy': breakeven_subsidy,
        'breakeven_subsidy_percent': (breakeven_subsidy / mrp * 100) if breakeven_subsidy else None,
        'parameters': {
            'mrp': mrp,
            'tenure_years': tenure_years,
            'segment': segment,
            'appliance': appliance,
        },
    }


# =============================================================================
# Module Test
# =============================================================================

if __name__ == "__main__":
    print("Participation Constraint Checker Demo")
    print("=" * 60)

    # Test parameters
    MRP = 45000
    SUBSIDIZED_PRICE = 28000  # ₹17,000 subsidy
    TENURE_YEARS = 2
    SEGMENT = 'moderate'

    sesp_params = {
        'subsidized_price': SUBSIDIZED_PRICE,
        'plan': 'moderate',
        'efficiency_score': 80,
        'deposit': 5000,
    }

    print(f"\nTest Configuration:")
    print(f"  MRP: ₹{MRP:,}")
    print(f"  Subsidized Price: ₹{SUBSIDIZED_PRICE:,}")
    print(f"  Subsidy: ₹{MRP - SUBSIDIZED_PRICE:,} ({((MRP - SUBSIDIZED_PRICE)/MRP)*100:.1f}%)")
    print(f"  Tenure: {TENURE_YEARS} years")
    print(f"  Segment: {SEGMENT.title()}")

    # Check individual constraints
    print("\n" + "-" * 60)
    print("Individual Constraint Checks:")

    pc_purchase = check_pc_vs_purchase(sesp_params, MRP, TENURE_YEARS, SEGMENT)
    status = "✓ PASS" if pc_purchase['satisfied'] else "✗ FAIL"
    print(f"\n  vs Purchase: {status}")
    print(f"    Savings: ₹{pc_purchase['actual_savings']:,.0f} ({pc_purchase['actual_savings_percent']:.1f}%)")
    print(f"    Required: {pc_purchase['threshold_percent']:.0f}%")

    pc_emi = check_pc_vs_emi(sesp_params, MRP, TENURE_YEARS, 12, SEGMENT)
    status = "✓ PASS" if pc_emi['satisfied'] else "✗ FAIL"
    print(f"\n  vs EMI (12m): {status}")
    print(f"    Savings: ₹{pc_emi['actual_savings']:,.0f} ({pc_emi['actual_savings_percent']:.1f}%)")

    pc_rental = check_pc_vs_rental(sesp_params, TENURE_YEARS, SEGMENT)
    status = "✓ PASS" if pc_rental['satisfied'] else "✗ FAIL"
    print(f"\n  vs Rental: {status}")
    print(f"    Savings: ₹{pc_rental['actual_savings']:,.0f} ({pc_rental['actual_savings_percent']:.1f}%)")

    # Aggregate validation
    print("\n" + "-" * 60)
    validation = validate_participation(sesp_params, MRP, TENURE_YEARS, SEGMENT)
    print(f"\nOverall: {validation['message']}")
    print(f"  Passed: {validation['num_passed']}/{validation['num_total']} constraints")

    # Find boundary
    print("\n" + "-" * 60)
    boundary = find_pc_boundary(MRP, TENURE_YEARS, SEGMENT)
    print(f"\nPrice Boundary (10% savings threshold):")
    print(f"  {boundary['recommendation']}")

    # Sensitivity analysis
    print("\n" + "-" * 60)
    sensitivity = analyze_pc_sensitivity(MRP, TENURE_YEARS, SEGMENT)
    print(f"\nSensitivity Analysis:")
    print(f"  {'Subsidy':>10} | {'Price':>10} | {'Savings':>10} | Status")
    print(f"  {'-'*10} | {'-'*10} | {'-'*10} | ------")
    for r in sensitivity['sensitivity_results']:
        status = "✓" if r['satisfied'] else "✗"
        print(f"  ₹{r['subsidy']:>8,.0f} | ₹{r['subsidized_price']:>8,.0f} | "
              f"{r['savings_percent']:>8.1f}% | {status}")

    if sensitivity['breakeven_subsidy']:
        print(f"\n  Breakeven Subsidy: ₹{sensitivity['breakeven_subsidy']:,.0f} "
              f"({sensitivity['breakeven_subsidy_percent']:.1f}% of MRP)")

    print("\n✓ Participation constraint module working correctly!")
