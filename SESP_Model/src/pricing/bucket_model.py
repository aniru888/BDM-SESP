"""
Bucket-Based Pricing Model
==========================

This module implements the "Mobile Data" style subscription pricing for SESP.

KEY PRINCIPLES (from PATCHES.md):
1. Charge for ACCESS (runtime hours), NOT for electricity (kWh)
2. Hours = appliance wear (our cost domain), kWh = Discom's domain
3. Within bucket: usage feels "free" (already paid for access)
4. Beyond bucket: overage fee (wear & tear, like mobile data)
5. Reward BEHAVIOR (efficiency), not OUTCOME (low usage)
6. Frame as DISCOUNTS (gain), not penalties (pain)

NEVER use kWh × rate calculations — that would double-charge the customer
who already pays electricity separately to the utility.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any
from enum import Enum


# =============================================================================
# SUBSCRIPTION PLANS
# =============================================================================

# =============================================================================
# SEASONAL HOURS (synchronized with simulator.py)
# =============================================================================
# Season definitions (month index 0-11 → season)
SEASONS = {
    0: 'winter',   # Jan
    1: 'winter',   # Feb
    2: 'shoulder', # Mar
    3: 'shoulder', # Apr
    4: 'summer',   # May
    5: 'summer',   # Jun
    6: 'summer',   # Jul
    7: 'summer',   # Aug
    8: 'shoulder', # Sep
    9: 'shoulder', # Oct
    10: 'winter',  # Nov
    11: 'winter',  # Dec
}

SEASONAL_PLAN_HOURS = {
    'lite': {
        'winter': 35,
        'shoulder': 90,
        'summer': 140,
        # Annual: 35*4 + 90*4 + 140*4 = 1,060 hrs (~88 hrs/month avg)
    },
    'standard': {
        'winter': 70,
        'shoulder': 180,
        'summer': 280,
        # Annual: 70*4 + 180*4 + 280*4 = 2,120 hrs (~177 hrs/month avg)
    },
    'premium': {
        'winter': 120,
        'shoulder': 320,
        'summer': 480,
        # Annual: 120*4 + 320*4 + 480*4 = 3,680 hrs (~307 hrs/month avg)
    },
}


def get_seasonal_hours(plan: str, month: int) -> int:
    """Get included hours for a plan in a given month (0=Jan, 11=Dec)."""
    season = SEASONS[month % 12]
    return SEASONAL_PLAN_HOURS[plan][season]


SUBSCRIPTION_PLANS: Dict[str, Dict[str, Any]] = {
    'lite': {
        'name': 'Lite Plan',
        'monthly_fee': 449,
        'hours_included': 88,  # Annual average (~35+90+140)/3 seasons
        'seasonal_hours': SEASONAL_PLAN_HOURS['lite'],
        'overage_per_hour': 6,
        'max_overage': 150,  # Cap to prevent bill shock
        'target_customer': [
            'Bedroom only use',
            'Working couple (out during day)',
            'Mild climate (Bangalore, Pune)',
            'First AC, budget-conscious'
        ],
        'services_included': [
            '2 service visits per year',
            'Basic IoT monitoring',
            'Standard warranty extension',
            'Email support'
        ]
    },
    'standard': {
        'name': 'Standard Plan',
        'monthly_fee': 599,
        'hours_included': 177,  # Annual average
        'seasonal_hours': SEASONAL_PLAN_HOURS['standard'],
        'overage_per_hour': 5,
        'max_overage': 200,
        'target_customer': [
            'Family with children',
            'Hot climate (Delhi NCR, Chennai)',
            'Living room + bedroom use',
            'Replacing old AC'
        ],
        'services_included': [
            '3 service visits per year',
            'Advanced IoT with app',
            'Comprehensive warranty extension',
            'Priority phone support',
            '1 free gas top-up during tenure'
        ]
    },
    'premium': {
        'name': 'Premium Plan',
        'monthly_fee': 799,
        'hours_included': 307,  # Annual average
        'seasonal_hours': SEASONAL_PLAN_HOURS['premium'],
        'overage_per_hour': 0,  # No overage for premium
        'max_overage': 0,  # Unlimited
        'target_customer': [
            'Work from home professional',
            'Joint family / large household',
            'Extreme climate (Rajasthan, Vidarbha)',
            'Multiple rooms served',
            'Elderly with health needs'
        ],
        'services_included': [
            'Unlimited service visits',
            'Premium IoT with predictive alerts',
            'Full warranty extension',
            '4-hour response SLA',
            '2 free gas top-ups during tenure',
            'Priority replacement if repair >48hrs'
        ]
    }
}

# Backward compatibility aliases (for any code using old plan names)
SUBSCRIPTION_PLANS['light'] = SUBSCRIPTION_PLANS['lite']
SUBSCRIPTION_PLANS['moderate'] = SUBSCRIPTION_PLANS['standard']
SUBSCRIPTION_PLANS['heavy'] = SUBSCRIPTION_PLANS['premium']


# =============================================================================
# EFFICIENCY SCORE TIERS
# =============================================================================

class EfficiencyTier(Enum):
    """Efficiency tier classifications based on behavior score."""
    CHAMPION = "champion"
    STAR = "star"
    AWARE = "aware"
    IMPROVING = "improving"


EFFICIENCY_TIERS: Dict[str, Dict[str, Any]] = {
    'champion': {
        'threshold': 90,
        'discount_percent': 0.20,  # 20% off base fee
        'badge': 'Efficiency Champion 🏆',
        'message': "Amazing! You're in the top 10% of efficient users!"
    },
    'star': {
        'threshold': 75,
        'discount_percent': 0.12,  # 12% off
        'badge': 'Efficiency Star ⭐',
        'message': "Great job! You're using your AC smartly."
    },
    'aware': {
        'threshold': 60,
        'discount_percent': 0.05,  # 5% off
        'badge': 'Efficiency Aware 🌱',
        'message': "Good start! Small changes can get you to Star level."
    },
    'improving': {
        'threshold': 0,
        'discount_percent': 0.00,  # No discount
        'badge': 'Room to Improve 📈',
        'message': "Try setting temp to 24°C to start earning rewards!"
    }
}


# =============================================================================
# EFFICIENCY SCORE WEIGHTS
# =============================================================================

EFFICIENCY_WEIGHTS = {
    'temperature_discipline': 0.60,  # 60% weight — biggest factor
    'schedule_discipline': 0.25,     # 25% weight — timer usage
    'anomaly_avoidance': 0.15        # 15% weight — avoiding wasteful behaviors
}


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def calculate_overage(plan: str, actual_hours: float) -> Dict[str, Any]:
    """
    Calculate overage fee for exceeding plan hours.

    This is like mobile data overage — customer understands they exceeded their plan.
    NOT a penalty for using electricity (that would be double-charging).

    Args:
        plan: 'light', 'moderate', or 'heavy'
        actual_hours: Actual runtime hours this month

    Returns:
        Dictionary with:
        - excess_hours: Hours beyond plan limit
        - overage_fee: Fee to charge (capped at max)
        - capped: Whether the cap was applied
        - message: Customer-friendly message

    Example:
        >>> calculate_overage('light', 180)
        {'excess_hours': 30, 'overage_fee': 150, 'capped': False,
         'message': 'You used 180 hours (plan: 150). Extra usage: ₹150'}
    """
    if plan not in SUBSCRIPTION_PLANS:
        raise ValueError(f"Unknown plan: {plan}. Use 'light', 'moderate', or 'heavy'.")

    plan_config = SUBSCRIPTION_PLANS[plan]
    hours_included = plan_config['hours_included']
    overage_rate = plan_config['overage_per_hour']
    max_overage = plan_config['max_overage']

    if actual_hours <= hours_included:
        return {
            'excess_hours': 0,
            'overage_fee': 0,
            'capped': False,
            'message': f'Within your plan! Used {actual_hours:.0f} of {hours_included} hours 👍'
        }

    excess_hours = actual_hours - hours_included
    raw_overage = excess_hours * overage_rate
    overage_fee = min(raw_overage, max_overage)
    capped = raw_overage > max_overage

    if capped:
        message = (
            f"You used {actual_hours:.0f} hours (plan: {hours_included}). "
            f"Extra usage capped at ₹{overage_fee:.0f}"
        )
    else:
        message = (
            f"You used {actual_hours:.0f} hours (plan: {hours_included}). "
            f"Extra usage: ₹{overage_fee:.0f}"
        )

    return {
        'excess_hours': excess_hours,
        'overage_fee': overage_fee,
        'capped': capped,
        'message': message
    }


def calculate_efficiency_score(
    avg_set_temperature: float,
    timer_usage_percent: float,
    anomaly_events: int = 0
) -> float:
    """
    Calculate efficiency score based on BEHAVIOR, not usage volume.

    The efficiency score rewards HOW the customer uses the AC, not HOW MUCH.
    A Chennai family using AC 10 hours efficiently should be rewarded.
    A Delhi family running at 16°C for 2 hours should NOT be rewarded.

    Args:
        avg_set_temperature: Average set temperature in Celsius (16-30)
        timer_usage_percent: Percentage of usage with timer/scheduling (0-100)
        anomaly_events: Count of wasteful behaviors (door open while running, etc.)

    Returns:
        Efficiency score from 0-100.

    Scoring Logic:
        Temperature (60% weight):
        - 24°C or higher: 100 points (excellent)
        - 22-24°C: 80 points (good)
        - 20-22°C: 50 points (fair)
        - 18-20°C: 25 points (poor)
        - Below 18°C: 0 points (wasteful)

        Timer usage (25% weight):
        - Score = min(100, timer_usage × 1.2)

        Anomaly avoidance (15% weight):
        - Penalty = min(100, events × 3)
        - Score = 100 - penalty

    Example:
        >>> calculate_efficiency_score(24, 80, 2)
        89.1  # Champion tier (24°C=100, timer=96, anomaly=94)
    """
    # Temperature discipline (60% weight)
    if avg_set_temperature >= 24:
        temp_score = 100
    elif avg_set_temperature >= 22:
        temp_score = 80
    elif avg_set_temperature >= 20:
        temp_score = 50
    elif avg_set_temperature >= 18:
        temp_score = 25
    else:
        temp_score = 0

    # Schedule discipline (25% weight)
    timer_score = min(100, timer_usage_percent * 1.2)

    # Anomaly avoidance (15% weight)
    anomaly_penalty = min(100, anomaly_events * 3)
    behavior_score = 100 - anomaly_penalty

    # Weighted final score
    efficiency_score = (
        temp_score * EFFICIENCY_WEIGHTS['temperature_discipline'] +
        timer_score * EFFICIENCY_WEIGHTS['schedule_discipline'] +
        behavior_score * EFFICIENCY_WEIGHTS['anomaly_avoidance']
    )

    return round(max(0, min(100, efficiency_score)), 1)


def get_discount_tier(efficiency_score: float) -> Tuple[str, Dict[str, Any]]:
    """
    Get the discount tier for a given efficiency score.

    Args:
        efficiency_score: Score from 0-100

    Returns:
        Tuple of (tier_name, tier_config)

    Example:
        >>> tier_name, tier_config = get_discount_tier(85)
        >>> tier_name
        'star'
        >>> tier_config['discount_percent']
        0.12
    """
    for tier_name in ['champion', 'star', 'aware', 'improving']:
        tier = EFFICIENCY_TIERS[tier_name]
        if efficiency_score >= tier['threshold']:
            return tier_name, tier

    # Should never reach here, but return 'improving' as fallback
    return 'improving', EFFICIENCY_TIERS['improving']


def calculate_efficiency_discount(
    efficiency_score: float,
    base_fee: float
) -> Dict[str, Any]:
    """
    Calculate efficiency discount based on behavior score.

    CRITICAL: Frame as DISCOUNT (gain), not penalty avoidance (pain).
    People HATE fees but LOVE discounts. Same economics, better psychology.

    Args:
        efficiency_score: Score from 0-100
        base_fee: Monthly base fee for the plan

    Returns:
        Dictionary with:
        - tier_name: 'champion', 'star', 'aware', or 'improving'
        - discount_percent: Percentage discount (0.00 to 0.20)
        - discount_amount: Amount in INR
        - badge: Customer-facing badge text
        - message: Positive framing message

    Example:
        >>> calculate_efficiency_discount(92, 649)
        {'tier_name': 'champion', 'discount_percent': 0.20,
         'discount_amount': 129.8, 'badge': 'Efficiency Champion 🏆',
         'message': "Congrats! Your Efficiency Score of 92 earned you ₹130 off!"}
    """
    tier_name, tier = get_discount_tier(efficiency_score)

    discount_percent = tier['discount_percent']
    discount_amount = base_fee * discount_percent

    # Positive framing message
    if discount_amount > 0:
        message = (
            f"Congrats! Your Efficiency Score of {efficiency_score:.0f} "
            f"earned you ₹{discount_amount:.0f} off! 🎉"
        )
    else:
        message = tier['message']

    return {
        'tier_name': tier_name,
        'discount_percent': discount_percent,
        'discount_amount': round(discount_amount, 2),
        'badge': tier['badge'],
        'message': message
    }


def calculate_monthly_bill(
    plan: str,
    actual_hours: float,
    efficiency_score: float,
    include_gst: bool = True
) -> Dict[str, Any]:
    """
    Calculate complete monthly bill using bucket model.

    Formula: Bill = (Base_Fee + Overage - Efficiency_Discount) × GST

    This function brings together all components of the bucket model pricing.

    Args:
        plan: 'light', 'moderate', or 'heavy'
        actual_hours: Actual runtime hours this month
        efficiency_score: Behavior-based efficiency score (0-100)
        include_gst: Whether to include 18% GST (default True)

    Returns:
        Comprehensive bill breakdown dictionary.

    Example:
        >>> calculate_monthly_bill('moderate', 210, 85)
        {
            'plan': 'moderate',
            'base_fee': 649,
            'actual_hours': 210,
            'hours_included': 225,
            'overage': {'excess_hours': 0, 'overage_fee': 0, ...},
            'efficiency': {'tier_name': 'star', 'discount_amount': 77.88, ...},
            'subtotal': 571.12,
            'gst_amount': 102.80,
            'total_bill': 673.92
        }
    """
    GST_RATE = 0.18

    if plan not in SUBSCRIPTION_PLANS:
        raise ValueError(f"Unknown plan: {plan}. Use 'light', 'moderate', or 'heavy'.")

    plan_config = SUBSCRIPTION_PLANS[plan]
    base_fee = plan_config['monthly_fee']

    # Calculate overage (hours-based, NOT kWh)
    overage_result = calculate_overage(plan, actual_hours)
    overage_fee = overage_result['overage_fee']

    # Calculate efficiency discount (behavior-based)
    efficiency_result = calculate_efficiency_discount(efficiency_score, base_fee)
    efficiency_discount = efficiency_result['discount_amount']

    # Calculate subtotal and GST
    subtotal = base_fee + overage_fee - efficiency_discount
    subtotal = max(0, subtotal)  # Cannot be negative

    if include_gst:
        gst_amount = subtotal * GST_RATE
        total_bill = subtotal + gst_amount
    else:
        gst_amount = 0
        total_bill = subtotal

    return {
        'plan': plan,
        'plan_name': plan_config['name'],
        'base_fee': base_fee,
        'actual_hours': actual_hours,
        'hours_included': plan_config['hours_included'],
        'overage': overage_result,
        'efficiency': efficiency_result,
        'subtotal': round(subtotal, 2),
        'gst_rate': GST_RATE if include_gst else 0,
        'gst_amount': round(gst_amount, 2),
        'total_bill': round(total_bill, 2),
        'summary_message': _generate_bill_summary(
            plan_config['name'],
            total_bill,
            efficiency_result['badge'],
            efficiency_discount
        )
    }


def _generate_bill_summary(
    plan_name: str,
    total_bill: float,
    badge: str,
    discount: float
) -> str:
    """Generate a customer-friendly bill summary message."""
    if discount > 0:
        return (
            f"Your {plan_name} bill: ₹{total_bill:.0f} | "
            f"You earned ₹{discount:.0f} off with your {badge}!"
        )
    else:
        return f"Your {plan_name} bill: ₹{total_bill:.0f}"


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_no_double_charging(calculation_details: Dict[str, Any]) -> bool:
    """
    Verify that the pricing model does NOT double-charge for electricity.

    The bucket model charges for:
    - Access (hours of runtime)
    - Wear & tear (overage for excess hours)
    - Service value (maintenance, warranty, IoT)

    It does NOT charge for:
    - kWh consumed (that's Discom's domain)
    - Electricity usage rate (customer pays utility separately)

    Args:
        calculation_details: Output from calculate_monthly_bill()

    Returns:
        True if validation passes (no double-charging detected).

    Raises:
        AssertionError: If any double-charging pattern is detected.
    """
    # Verify no kWh-based calculations
    assert 'kwh' not in str(calculation_details).lower(), \
        "ERROR: kWh-based calculation detected — this would double-charge!"

    # Verify overage is hours-based
    overage = calculation_details.get('overage', {})
    if overage.get('overage_fee', 0) > 0:
        assert 'excess_hours' in overage, \
            "ERROR: Overage must be hours-based, not kWh-based!"

    # Verify base fee doesn't include usage rate
    base_fee = calculation_details.get('base_fee', 0)
    assert 400 <= base_fee <= 1000, \
        f"ERROR: Base fee ₹{base_fee} outside expected range (₹400-1000)!"

    return True


def estimate_plan_recommendation(
    actual_hours_last_3_months: list,
    current_plan: Optional[str] = None
) -> Dict[str, Any]:
    """
    Recommend a plan based on recent usage patterns.

    If customer is consistently exceeding their plan, suggest upgrade.
    If consistently under-using, suggest downgrade to save money.

    Args:
        actual_hours_last_3_months: List of 3 monthly hour counts
        current_plan: Current plan (if any)

    Returns:
        Recommendation dictionary with suggested plan and reasoning.
    """
    avg_hours = sum(actual_hours_last_3_months) / len(actual_hours_last_3_months)

    # Find best-fit plan
    recommendations = []
    for plan_name, plan_config in SUBSCRIPTION_PLANS.items():
        hours_included = plan_config['hours_included']
        monthly_fee = plan_config['monthly_fee']

        if avg_hours <= hours_included:
            # Would fit in this plan without overage
            fit_type = 'fits'
            expected_overage = 0
        else:
            # Would have overage
            excess = avg_hours - hours_included
            expected_overage = min(
                excess * plan_config['overage_per_hour'],
                plan_config['max_overage']
            )
            fit_type = 'overage'

        total_expected = monthly_fee + expected_overage

        recommendations.append({
            'plan': plan_name,
            'fit_type': fit_type,
            'monthly_fee': monthly_fee,
            'expected_overage': expected_overage,
            'total_expected': total_expected
        })

    # Sort by total expected cost
    recommendations.sort(key=lambda x: x['total_expected'])
    best_plan = recommendations[0]

    # Generate recommendation
    if current_plan and current_plan != best_plan['plan']:
        if best_plan['plan'] == 'heavy' and current_plan == 'light':
            action = 'upgrade'
            savings = None  # Would cost more but save on overage
        elif best_plan['plan'] == 'light' and current_plan == 'heavy':
            action = 'downgrade'
            current_fee = SUBSCRIPTION_PLANS[current_plan]['monthly_fee']
            savings = current_fee - best_plan['total_expected']
        else:
            action = 'consider switching'
            savings = None
    else:
        action = 'stay'
        savings = None

    return {
        'recommended_plan': best_plan['plan'],
        'reason': (
            f"Based on your average of {avg_hours:.0f} hours/month, "
            f"the {best_plan['plan'].title()} plan is optimal."
        ),
        'expected_monthly_cost': best_plan['total_expected'],
        'action': action,
        'potential_savings': savings,
        'all_options': recommendations
    }


# =============================================================================
# MODULE INFO
# =============================================================================

if __name__ == "__main__":
    # Demo the bucket model
    print("=" * 60)
    print("SESP Bucket Model — Demo")
    print("=" * 60)

    # Example 1: Efficient light user
    print("\n--- Example 1: Efficient Light User ---")
    bill1 = calculate_monthly_bill('light', 120, 92)
    print(f"Plan: {bill1['plan_name']}")
    print(f"Hours used: {bill1['actual_hours']} / {bill1['hours_included']}")
    print(f"Efficiency: {bill1['efficiency']['badge']}")
    print(f"Discount earned: ₹{bill1['efficiency']['discount_amount']:.0f}")
    print(f"Total bill: ₹{bill1['total_bill']:.0f}")

    # Example 2: Moderate user with overage
    print("\n--- Example 2: Moderate User with Overage ---")
    bill2 = calculate_monthly_bill('moderate', 260, 72)
    print(f"Plan: {bill2['plan_name']}")
    print(f"Hours used: {bill2['actual_hours']} / {bill2['hours_included']}")
    print(f"Overage: ₹{bill2['overage']['overage_fee']:.0f}")
    print(f"Efficiency: {bill2['efficiency']['badge']}")
    print(f"Total bill: ₹{bill2['total_bill']:.0f}")

    # Example 3: Heavy user at cap
    print("\n--- Example 3: Heavy User at Overage Cap ---")
    bill3 = calculate_monthly_bill('heavy', 500, 45)
    print(f"Plan: {bill3['plan_name']}")
    print(f"Hours used: {bill3['actual_hours']} / {bill3['hours_included']}")
    print(f"Overage: ₹{bill3['overage']['overage_fee']:.0f} (capped: {bill3['overage']['capped']})")
    print(f"Efficiency: {bill3['efficiency']['badge']}")
    print(f"Total bill: ₹{bill3['total_bill']:.0f}")

    # Validate no double-charging
    print("\n--- Validation ---")
    for bill in [bill1, bill2, bill3]:
        validate_no_double_charging(bill)
    print("✓ All bills pass no-double-charging validation!")
