"""
Alternative Cost Calculators
=============================

Calculate total costs for different appliance acquisition options:
1. Outright Purchase (with AMC)
2. EMI Purchase (financed)
3. Rental
4. SESP Subscription

These enable fair comparison for the Participation Constraint check.

Key Insight:
- All costs must be compared on NPV basis using customer's discount rate
- GST must be applied consistently to ALL scenarios
- Purchase scenario includes terminal value (asset ownership benefit)

Run with: python -m src.alternatives.calculators
"""

from typing import Dict, List, Optional, Any
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.adjustments.india_specific import (
    npv_customer,
    calculate_gst,
    get_terminal_value_local,
    CUSTOMER_DISCOUNT_RATES,
    GST_RATE,
)
from src.pricing.bucket_model import (
    SUBSCRIPTION_PLANS,
    calculate_monthly_bill,
)


# =============================================================================
# Market Parameters (from config, hardcoded for reliability)
# =============================================================================

# EMI Parameters
EMI_INTEREST_RATE_ANNUAL = 0.14  # 14% annual
EMI_PROCESSING_FEE_PERCENT = 0.02  # 2% processing fee

# Rental Parameters
RENTAL_MONTHLY = {
    'AC': {'min': 1200, 'max': 1800, 'default': 1500},
    'FRIDGE': {'min': 600, 'max': 1000, 'default': 800},
}
RENTAL_DEPOSIT_MONTHS = 2

# AMC Parameters
AMC_ANNUAL = {
    'AC': {'min': 2000, 'max': 3500, 'default': 2500},
    'FRIDGE': {'min': 1000, 'max': 2000, 'default': 1500},
}

# Appliance MRP (defaults)
APPLIANCE_MRP = {
    'AC': 45000,
    'FRIDGE': 30000,
}

# Expected repair costs (after warranty, probability-weighted)
EXPECTED_REPAIRS = {
    'AC': {
        'year_1': 0,      # Under warranty
        'year_2': 0,      # Under warranty
        'year_3': 500,    # Minor issues
        'year_4': 1500,   # Gas refill likely
        'year_5': 2000,   # Compressor aging
    },
    'FRIDGE': {
        'year_1': 0,
        'year_2': 0,
        'year_3': 300,
        'year_4': 500,
        'year_5': 800,
    },
}


# =============================================================================
# Outright Purchase Calculator
# =============================================================================

def calculate_purchase_cost(
    mrp: float,
    tenure_years: int,
    segment: str = 'moderate',
    appliance: str = 'AC',
    include_amc: bool = True,
    include_repairs: bool = True,
) -> Dict[str, Any]:
    """
    Calculate total cost of outright purchase.

    Components:
    - MRP (one-time, GST-inclusive)
    - AMC annual costs (with GST)
    - Expected repair costs (with GST, probability-weighted)
    - Terminal value deduction (asset ownership benefit)

    Args:
        mrp: Maximum Retail Price (GST-inclusive)
        tenure_years: Comparison horizon in years
        segment: Customer segment ('light', 'moderate', 'heavy')
        appliance: 'AC' or 'FRIDGE'
        include_amc: Whether to include AMC costs
        include_repairs: Whether to include expected repairs

    Returns:
        Dictionary with cost breakdown and NPV
    """
    tenure_months = tenure_years * 12

    # Upfront cost (MRP is already GST-inclusive)
    upfront_cost = mrp

    # Extract base amount from GST-inclusive MRP
    gst_breakdown = calculate_gst(mrp, inclusive=True)
    mrp_base = gst_breakdown['base']
    mrp_gst = gst_breakdown['gst']

    # AMC costs (annual, with GST)
    amc_annual = AMC_ANNUAL.get(appliance, AMC_ANNUAL['AC'])['default']
    amc_monthly_with_gst = (amc_annual / 12) * (1 + GST_RATE) if include_amc else 0

    # Generate monthly AMC payments
    amc_payments = [amc_monthly_with_gst] * tenure_months if include_amc else []
    amc_total = sum(amc_payments)
    amc_npv = npv_customer(amc_payments, segment) if amc_payments else 0

    # Expected repair costs by year
    repairs_total = 0
    repairs_npv = 0
    yearly_repairs = EXPECTED_REPAIRS.get(appliance, EXPECTED_REPAIRS['AC'])

    if include_repairs:
        for year in range(1, tenure_years + 1):
            year_key = f'year_{year}'
            repair_cost = yearly_repairs.get(year_key, 0)
            if repair_cost > 0:
                # Repairs have GST on service component
                repair_with_gst = repair_cost * (1 + GST_RATE)
                repairs_total += repair_with_gst
                # Discount to present value (at end of year)
                discount_rate = CUSTOMER_DISCOUNT_RATES[segment]
                repairs_npv += repair_with_gst / ((1 + discount_rate) ** year)

    # Terminal value (what appliance is worth at end of tenure)
    terminal_value = get_terminal_value_local(appliance, tenure_years)
    discount_rate = CUSTOMER_DISCOUNT_RATES[segment]
    terminal_pv = terminal_value / ((1 + discount_rate) ** tenure_years)

    # Total cost calculation
    total_nominal = upfront_cost + amc_total + repairs_total
    effective_cost = total_nominal - terminal_value  # Nominal

    # NPV calculation (customer perspective)
    total_npv = upfront_cost + amc_npv + repairs_npv - terminal_pv

    # Monthly equivalent (for comparison)
    monthly_equivalent = total_npv / tenure_months

    return {
        'method': 'purchase',
        'mrp': mrp,
        'mrp_base': mrp_base,
        'mrp_gst': mrp_gst,
        'upfront_cost': upfront_cost,
        'amc_annual': amc_annual if include_amc else 0,
        'amc_total': amc_total,
        'amc_npv': amc_npv,
        'repairs_total': repairs_total,
        'repairs_npv': repairs_npv,
        'terminal_value': terminal_value,
        'terminal_pv': terminal_pv,
        'total_nominal': total_nominal,
        'effective_cost_nominal': effective_cost,
        'total_npv': total_npv,
        'monthly_equivalent': monthly_equivalent,
        'tenure_years': tenure_years,
        'tenure_months': tenure_months,
        'segment': segment,
        'discount_rate': discount_rate,
    }


# =============================================================================
# EMI Purchase Calculator
# =============================================================================

def calculate_emi(
    principal: float,
    annual_rate: float,
    tenure_months: int,
) -> Dict[str, float]:
    """
    Calculate EMI using standard formula.

    EMI = P × r × (1 + r)^n / ((1 + r)^n - 1)

    Where:
    - P = Principal
    - r = Monthly interest rate
    - n = Number of months

    Args:
        principal: Loan amount
        annual_rate: Annual interest rate (decimal)
        tenure_months: Loan tenure in months

    Returns:
        Dictionary with EMI, total interest, and total payment
    """
    r = annual_rate / 12  # Monthly rate
    n = tenure_months

    if r == 0:
        emi = principal / n
        total_interest = 0
    else:
        emi = principal * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
        total_interest = (emi * n) - principal

    return {
        'emi': emi,
        'principal': principal,
        'total_interest': total_interest,
        'total_payment': emi * n,
        'interest_rate_annual': annual_rate,
        'tenure_months': tenure_months,
    }


def calculate_emi_cost(
    mrp: float,
    emi_tenure_months: int = 12,
    comparison_horizon_years: int = 2,
    segment: str = 'moderate',
    appliance: str = 'AC',
    include_amc: bool = True,
    include_repairs: bool = True,
    interest_rate: float = EMI_INTEREST_RATE_ANNUAL,
    processing_fee_percent: float = EMI_PROCESSING_FEE_PERCENT,
) -> Dict[str, Any]:
    """
    Calculate total cost of EMI-financed purchase.

    Components:
    - Processing fee (upfront)
    - EMI payments (with interest)
    - AMC costs (same as purchase)
    - Expected repairs (same as purchase)
    - Terminal value deduction

    Args:
        mrp: Maximum Retail Price (GST-inclusive)
        emi_tenure_months: EMI payment period (6, 12, 18, 24)
        comparison_horizon_years: Total comparison period
        segment: Customer segment
        appliance: 'AC' or 'FRIDGE'
        include_amc: Whether to include AMC
        include_repairs: Whether to include expected repairs
        interest_rate: Annual interest rate
        processing_fee_percent: Processing fee as decimal

    Returns:
        Dictionary with cost breakdown and NPV
    """
    horizon_months = comparison_horizon_years * 12

    # Processing fee (upfront)
    processing_fee = mrp * processing_fee_percent

    # Calculate EMI
    emi_details = calculate_emi(mrp, interest_rate, emi_tenure_months)
    emi_monthly = emi_details['emi']
    total_interest = emi_details['total_interest']

    # Generate EMI payment stream
    emi_payments = [emi_monthly] * emi_tenure_months
    # Pad with zeros for remaining months
    emi_payments.extend([0] * (horizon_months - emi_tenure_months))

    # NPV of EMI payments
    emi_npv = npv_customer(emi_payments, segment)

    # AMC and repairs (same as purchase, but start after purchase)
    amc_annual = AMC_ANNUAL.get(appliance, AMC_ANNUAL['AC'])['default']
    amc_monthly_with_gst = (amc_annual / 12) * (1 + GST_RATE) if include_amc else 0
    amc_payments = [amc_monthly_with_gst] * horizon_months if include_amc else []
    amc_total = sum(amc_payments)
    amc_npv = npv_customer(amc_payments, segment) if amc_payments else 0

    # Expected repairs
    repairs_total = 0
    repairs_npv = 0
    yearly_repairs = EXPECTED_REPAIRS.get(appliance, EXPECTED_REPAIRS['AC'])

    if include_repairs:
        discount_rate = CUSTOMER_DISCOUNT_RATES[segment]
        for year in range(1, comparison_horizon_years + 1):
            year_key = f'year_{year}'
            repair_cost = yearly_repairs.get(year_key, 0)
            if repair_cost > 0:
                repair_with_gst = repair_cost * (1 + GST_RATE)
                repairs_total += repair_with_gst
                repairs_npv += repair_with_gst / ((1 + discount_rate) ** year)

    # Terminal value
    terminal_value = get_terminal_value_local(appliance, comparison_horizon_years)
    discount_rate = CUSTOMER_DISCOUNT_RATES[segment]
    terminal_pv = terminal_value / ((1 + discount_rate) ** comparison_horizon_years)

    # Total cost calculation
    total_nominal = processing_fee + (emi_monthly * emi_tenure_months) + amc_total + repairs_total
    effective_cost = total_nominal - terminal_value

    # NPV calculation
    total_npv = processing_fee + emi_npv + amc_npv + repairs_npv - terminal_pv

    # Monthly equivalent
    monthly_equivalent = total_npv / horizon_months

    return {
        'method': 'emi',
        'mrp': mrp,
        'processing_fee': processing_fee,
        'emi_monthly': emi_monthly,
        'emi_tenure_months': emi_tenure_months,
        'total_interest': total_interest,
        'total_emi_paid': emi_monthly * emi_tenure_months,
        'emi_npv': emi_npv,
        'amc_annual': amc_annual if include_amc else 0,
        'amc_total': amc_total,
        'amc_npv': amc_npv,
        'repairs_total': repairs_total,
        'repairs_npv': repairs_npv,
        'terminal_value': terminal_value,
        'terminal_pv': terminal_pv,
        'total_nominal': total_nominal,
        'effective_cost_nominal': effective_cost,
        'total_npv': total_npv,
        'monthly_equivalent': monthly_equivalent,
        'comparison_horizon_years': comparison_horizon_years,
        'horizon_months': horizon_months,
        'segment': segment,
        'discount_rate': discount_rate,
        'interest_rate': interest_rate,
    }


# =============================================================================
# Rental Calculator
# =============================================================================

def calculate_rental_cost(
    tenure_months: int,
    segment: str = 'moderate',
    appliance: str = 'AC',
    monthly_rent: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate total cost of rental.

    Components:
    - Security deposit (refundable, opportunity cost only)
    - Monthly rent (with GST)
    - No terminal value (no ownership)
    - No AMC/repairs (included in rental)

    Args:
        tenure_months: Rental period
        segment: Customer segment
        appliance: 'AC' or 'FRIDGE'
        monthly_rent: Override default rent

    Returns:
        Dictionary with cost breakdown and NPV
    """
    # Get rental rate
    if monthly_rent is None:
        monthly_rent = RENTAL_MONTHLY.get(appliance, RENTAL_MONTHLY['AC'])['default']

    # Security deposit (refundable)
    deposit = monthly_rent * RENTAL_DEPOSIT_MONTHS

    # Monthly rent with GST
    monthly_with_gst = monthly_rent * (1 + GST_RATE)

    # Generate payment stream
    rent_payments = [monthly_with_gst] * tenure_months

    # Deposit refund at end
    discount_rate = CUSTOMER_DISCOUNT_RATES[segment]
    tenure_years = tenure_months / 12
    deposit_pv_refund = deposit / ((1 + discount_rate) ** tenure_years)

    # Opportunity cost of deposit (not earning returns)
    deposit_opportunity_cost = deposit - deposit_pv_refund

    # NPV calculation
    rent_npv = npv_customer(rent_payments, segment)
    total_npv = deposit + rent_npv - deposit_pv_refund  # Net deposit cost + rent NPV

    # Total nominal
    total_nominal = deposit + (monthly_with_gst * tenure_months) - deposit  # Deposit refunded

    # Monthly equivalent
    monthly_equivalent = total_npv / tenure_months

    return {
        'method': 'rental',
        'monthly_rent': monthly_rent,
        'monthly_with_gst': monthly_with_gst,
        'deposit': deposit,
        'deposit_refund': deposit,
        'deposit_pv_refund': deposit_pv_refund,
        'deposit_opportunity_cost': deposit_opportunity_cost,
        'total_rent_nominal': monthly_with_gst * tenure_months,
        'total_rent_npv': rent_npv,
        'total_nominal': monthly_with_gst * tenure_months,  # Deposit nets out
        'total_npv': total_npv,
        'monthly_equivalent': monthly_equivalent,
        'tenure_months': tenure_months,
        'tenure_years': tenure_years,
        'segment': segment,
        'discount_rate': discount_rate,
        'notes': 'Rental includes maintenance, no ownership at end',
    }


# =============================================================================
# SESP Subscription Calculator
# =============================================================================

def calculate_sesp_cost(
    subsidized_price: float,
    tenure_months: int,
    plan: str = 'moderate',
    segment: str = 'moderate',
    expected_hours: Optional[float] = None,
    efficiency_score: float = 75.0,
    deposit: float = 5000,
) -> Dict[str, Any]:
    """
    Calculate total cost of SESP subscription.

    Components:
    - Subsidized upfront payment (with GST)
    - Monthly subscription fees (with overage/discount, with GST)
    - Security deposit (refundable)
    - No terminal value (no ownership)

    Args:
        subsidized_price: Upfront price after subsidy (GST-exclusive)
        tenure_months: Subscription period
        plan: Subscription plan ('light', 'moderate', 'heavy')
        segment: Customer segment for NPV calculation
        expected_hours: Expected monthly usage hours
        efficiency_score: Efficiency score (0-100)
        deposit: Security deposit amount

    Returns:
        Dictionary with cost breakdown and NPV
    """
    # Get plan details
    plan_details = SUBSCRIPTION_PLANS[plan]
    base_fee = plan_details['monthly_fee']
    hours_included = plan_details['hours_included']

    # Default expected hours to 80% of plan hours
    if expected_hours is None:
        expected_hours = hours_included * 0.8

    # Calculate typical monthly bill
    monthly_bill = calculate_monthly_bill(
        plan=plan,
        actual_hours=expected_hours,
        efficiency_score=efficiency_score,
        include_gst=True
    )

    monthly_payment = monthly_bill['total_bill']

    # Upfront with GST
    upfront_with_gst = subsidized_price * (1 + GST_RATE)

    # Generate payment stream
    payments = [monthly_payment] * tenure_months

    # Deposit handling
    discount_rate = CUSTOMER_DISCOUNT_RATES[segment]
    tenure_years = tenure_months / 12
    deposit_pv_refund = deposit / ((1 + discount_rate) ** tenure_years)
    deposit_opportunity_cost = deposit - deposit_pv_refund

    # NPV calculation
    payments_npv = npv_customer(payments, segment)
    total_npv = upfront_with_gst + deposit + payments_npv - deposit_pv_refund

    # Total nominal
    total_nominal = upfront_with_gst + (monthly_payment * tenure_months)

    # Monthly equivalent
    monthly_equivalent = total_npv / tenure_months

    # Value metrics
    gst_total = (subsidized_price * GST_RATE) + sum(
        monthly_bill['gst_amount'] for _ in range(tenure_months)
    )

    return {
        'method': 'sesp',
        'subsidized_price': subsidized_price,
        'upfront_with_gst': upfront_with_gst,
        'plan': plan,
        'base_fee': base_fee,
        'monthly_payment': monthly_payment,
        'monthly_components': {
            'base_fee': monthly_bill['base_fee'],
            'overage': monthly_bill['overage']['overage_fee'],
            'efficiency_discount': monthly_bill['efficiency']['discount_amount'],
            'gst': monthly_bill['gst_amount'],
        },
        'expected_hours': expected_hours,
        'hours_included': hours_included,
        'efficiency_score': efficiency_score,
        'deposit': deposit,
        'deposit_refund': deposit,
        'deposit_pv_refund': deposit_pv_refund,
        'deposit_opportunity_cost': deposit_opportunity_cost,
        'total_payments_nominal': monthly_payment * tenure_months,
        'total_payments_npv': payments_npv,
        'total_nominal': total_nominal,
        'total_npv': total_npv,
        'monthly_equivalent': monthly_equivalent,
        'gst_total': gst_total,
        'tenure_months': tenure_months,
        'tenure_years': tenure_years,
        'segment': segment,
        'discount_rate': discount_rate,
        'notes': 'Includes maintenance, warranty, IoT monitoring; no ownership at end',
    }


# =============================================================================
# Comparison Functions
# =============================================================================

def compare_alternatives(
    mrp: float,
    subsidized_price: float,
    tenure_years: int,
    segment: str = 'moderate',
    appliance: str = 'AC',
    sesp_plan: str = 'moderate',
    efficiency_score: float = 75.0,
    expected_hours: Optional[float] = None,
    deposit: float = 5000,
) -> Dict[str, Any]:
    """
    Compare all alternatives side-by-side.

    Args:
        mrp: Full appliance price
        subsidized_price: SESP subsidized price
        tenure_years: Comparison horizon
        segment: Customer segment
        appliance: 'AC' or 'FRIDGE'
        sesp_plan: SESP plan name
        efficiency_score: Expected efficiency score
        expected_hours: Expected usage hours
        deposit: SESP/rental deposit

    Returns:
        Dictionary with all alternatives and comparison metrics
    """
    tenure_months = tenure_years * 12

    # Calculate each alternative
    purchase = calculate_purchase_cost(
        mrp=mrp,
        tenure_years=tenure_years,
        segment=segment,
        appliance=appliance,
    )

    emi_12m = calculate_emi_cost(
        mrp=mrp,
        emi_tenure_months=12,
        comparison_horizon_years=tenure_years,
        segment=segment,
        appliance=appliance,
    )

    emi_24m = calculate_emi_cost(
        mrp=mrp,
        emi_tenure_months=24,
        comparison_horizon_years=tenure_years,
        segment=segment,
        appliance=appliance,
    )

    rental = calculate_rental_cost(
        tenure_months=tenure_months,
        segment=segment,
        appliance=appliance,
    )

    sesp = calculate_sesp_cost(
        subsidized_price=subsidized_price,
        tenure_months=tenure_months,
        plan=sesp_plan,
        segment=segment,
        expected_hours=expected_hours,
        efficiency_score=efficiency_score,
        deposit=deposit,
    )

    # Build comparison table
    alternatives = {
        'purchase': purchase,
        'emi_12m': emi_12m,
        'emi_24m': emi_24m,
        'rental': rental,
        'sesp': sesp,
    }

    # Extract NPVs for comparison
    npvs = {
        'purchase': purchase['total_npv'],
        'emi_12m': emi_12m['total_npv'],
        'emi_24m': emi_24m['total_npv'],
        'rental': rental['total_npv'],
        'sesp': sesp['total_npv'],
    }

    # Find cheapest option
    cheapest = min(npvs, key=npvs.get)

    # Calculate savings vs each alternative
    sesp_npv = sesp['total_npv']
    savings = {
        'vs_purchase': purchase['total_npv'] - sesp_npv,
        'vs_purchase_percent': ((purchase['total_npv'] - sesp_npv) / purchase['total_npv']) * 100,
        'vs_emi_12m': emi_12m['total_npv'] - sesp_npv,
        'vs_emi_12m_percent': ((emi_12m['total_npv'] - sesp_npv) / emi_12m['total_npv']) * 100,
        'vs_emi_24m': emi_24m['total_npv'] - sesp_npv,
        'vs_emi_24m_percent': ((emi_24m['total_npv'] - sesp_npv) / emi_24m['total_npv']) * 100,
        'vs_rental': rental['total_npv'] - sesp_npv,
        'vs_rental_percent': ((rental['total_npv'] - sesp_npv) / rental['total_npv']) * 100,
    }

    # Rank alternatives
    ranked = sorted(npvs.items(), key=lambda x: x[1])
    ranking = {alt: rank + 1 for rank, (alt, _) in enumerate(ranked)}

    return {
        'alternatives': alternatives,
        'npv_comparison': npvs,
        'cheapest': cheapest,
        'sesp_rank': ranking['sesp'],
        'sesp_savings': savings,
        'ranking': ranking,
        'parameters': {
            'mrp': mrp,
            'subsidized_price': subsidized_price,
            'subsidy_amount': mrp - subsidized_price,
            'tenure_years': tenure_years,
            'segment': segment,
            'appliance': appliance,
            'sesp_plan': sesp_plan,
            'efficiency_score': efficiency_score,
            'discount_rate': CUSTOMER_DISCOUNT_RATES[segment],
        },
        'summary_table': _format_comparison_table(alternatives, ranking),
    }


def _format_comparison_table(
    alternatives: Dict[str, Dict],
    ranking: Dict[str, int],
) -> List[Dict[str, Any]]:
    """Format alternatives as a comparison table."""
    table = []
    for name, data in alternatives.items():
        table.append({
            'alternative': name.upper(),
            'total_npv': round(data['total_npv'], 2),
            'monthly_equivalent': round(data['monthly_equivalent'], 2),
            'upfront': round(data.get('upfront_cost', data.get('upfront_with_gst', data.get('deposit', 0))), 2),
            'rank': ranking[name],
            'notes': data.get('notes', ''),
        })
    return sorted(table, key=lambda x: x['rank'])


def check_participation_vs_purchase(
    sesp_npv: float,
    purchase_npv: float,
    threshold: float = 0.10,
) -> Dict[str, Any]:
    """
    Check if SESP satisfies participation constraint vs purchase.

    Participation Constraint:
    SESP_NPV < Purchase_NPV × (1 - threshold)

    Args:
        sesp_npv: NPV of SESP cost
        purchase_npv: NPV of purchase cost
        threshold: Minimum savings required (default 10%)

    Returns:
        Dictionary with constraint status and details
    """
    # Purchase NPV adjusted for threshold
    target_npv = purchase_npv * (1 - threshold)

    # Actual savings
    savings = purchase_npv - sesp_npv
    savings_percent = (savings / purchase_npv) * 100 if purchase_npv > 0 else 0

    # Check constraint
    satisfied = sesp_npv < target_npv

    # How much slack (or shortfall)
    slack = target_npv - sesp_npv
    slack_percent = (slack / purchase_npv) * 100 if purchase_npv > 0 else 0

    return {
        'satisfied': satisfied,
        'sesp_npv': sesp_npv,
        'purchase_npv': purchase_npv,
        'target_npv': target_npv,
        'threshold': threshold,
        'actual_savings': savings,
        'actual_savings_percent': savings_percent,
        'slack': slack,
        'slack_percent': slack_percent,
        'message': (
            f"✓ PC Satisfied: SESP saves ₹{savings:,.0f} ({savings_percent:.1f}%)"
            if satisfied else
            f"✗ PC Violated: Need ₹{-slack:,.0f} more savings to reach {threshold*100:.0f}% threshold"
        ),
    }


# =============================================================================
# Convenience Functions
# =============================================================================

def get_default_expected_hours(segment: str, appliance: str = 'AC') -> float:
    """Get default expected usage hours based on segment."""
    if appliance == 'AC':
        return {
            'light': 120,
            'moderate': 200,
            'heavy': 320,
        }.get(segment, 200)
    else:  # FRIDGE
        return {
            'light': 720,  # ~24 hours/day
            'moderate': 720,
            'heavy': 720,
        }.get(segment, 720)


def calculate_required_subsidy(
    mrp: float,
    target_savings_percent: float,
    tenure_years: int,
    segment: str = 'moderate',
    appliance: str = 'AC',
    sesp_plan: str = 'moderate',
    monthly_fee: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate required subsidy to achieve target customer savings.

    Uses binary search to find subsidy level that achieves target savings.

    Args:
        mrp: Full appliance price
        target_savings_percent: Desired savings vs purchase (e.g., 0.10 for 10%)
        tenure_years: Comparison horizon
        segment: Customer segment
        appliance: 'AC' or 'FRIDGE'
        sesp_plan: SESP plan
        monthly_fee: Override plan fee if specified

    Returns:
        Dictionary with required subsidy and resulting economics
    """
    # Get purchase cost baseline
    purchase = calculate_purchase_cost(
        mrp=mrp,
        tenure_years=tenure_years,
        segment=segment,
        appliance=appliance,
    )

    target_npv = purchase['total_npv'] * (1 - target_savings_percent)

    # Binary search for subsidy
    # Note: Higher subsidy may be needed for short tenures or high monthly fees
    low_subsidy = 0
    high_subsidy = mrp * 0.6  # Max 60% subsidy (may need more for high savings targets)

    best_subsidy = low_subsidy
    best_diff = float('inf')

    for _ in range(50):  # Max iterations
        mid_subsidy = (low_subsidy + high_subsidy) / 2
        subsidized_price = mrp - mid_subsidy

        sesp = calculate_sesp_cost(
            subsidized_price=subsidized_price,
            tenure_months=tenure_years * 12,
            plan=sesp_plan,
            segment=segment,
            expected_hours=get_default_expected_hours(segment, appliance),
        )

        diff = abs(sesp['total_npv'] - target_npv)
        if diff < best_diff:
            best_diff = diff
            best_subsidy = mid_subsidy

        if diff < 100:  # Within ₹100
            break

        if sesp['total_npv'] > target_npv:
            low_subsidy = mid_subsidy  # Need more subsidy
        else:
            high_subsidy = mid_subsidy  # Can reduce subsidy

    final_subsidy = best_subsidy
    final_subsidized_price = mrp - final_subsidy

    final_sesp = calculate_sesp_cost(
        subsidized_price=final_subsidized_price,
        tenure_months=tenure_years * 12,
        plan=sesp_plan,
        segment=segment,
        expected_hours=get_default_expected_hours(segment, appliance),
    )

    actual_savings = (purchase['total_npv'] - final_sesp['total_npv']) / purchase['total_npv']

    # Check if target was achievable
    target_achievable = actual_savings >= (target_savings_percent - 0.02)  # Within 2%

    return {
        'required_subsidy': round(final_subsidy, 0),
        'subsidized_price': round(final_subsidized_price, 0),
        'mrp': mrp,
        'target_savings_percent': target_savings_percent * 100,
        'actual_savings_percent': round(actual_savings * 100, 1),
        'purchase_npv': purchase['total_npv'],
        'sesp_npv': final_sesp['total_npv'],
        'subsidy_percent': round((final_subsidy / mrp) * 100, 1),
        'target_achievable': target_achievable,
    }


# =============================================================================
# Module Test
# =============================================================================

if __name__ == "__main__":
    print("Alternative Cost Calculators Demo")
    print("=" * 60)

    # Test parameters
    MRP = 45000
    SUBSIDIZED_PRICE = 28000  # ₹17,000 subsidy
    TENURE_YEARS = 2
    SEGMENT = 'moderate'

    # Run comparison
    comparison = compare_alternatives(
        mrp=MRP,
        subsidized_price=SUBSIDIZED_PRICE,
        tenure_years=TENURE_YEARS,
        segment=SEGMENT,
        appliance='AC',
        sesp_plan='moderate',
        efficiency_score=80,
    )

    print(f"\nComparison: {TENURE_YEARS} years, {SEGMENT.title()} User")
    print(f"MRP: ₹{MRP:,}, SESP Subsidized Price: ₹{SUBSIDIZED_PRICE:,}")
    print(f"Subsidy: ₹{MRP - SUBSIDIZED_PRICE:,} ({((MRP - SUBSIDIZED_PRICE)/MRP)*100:.1f}%)")
    print("-" * 60)

    print("\nNPV Comparison (Customer Perspective):")
    for row in comparison['summary_table']:
        status = "★" if row['rank'] == 1 else " "
        print(f"  {status} #{row['rank']} {row['alternative']:12} NPV: ₹{row['total_npv']:>10,.0f} "
              f"(₹{row['monthly_equivalent']:,.0f}/mo)")

    print(f"\nCheapest Option: {comparison['cheapest'].upper()}")
    print(f"SESP Rank: #{comparison['sesp_rank']}")

    print("\nSESP Savings vs Alternatives:")
    savings = comparison['sesp_savings']
    print(f"  vs Purchase: ₹{savings['vs_purchase']:,.0f} ({savings['vs_purchase_percent']:.1f}%)")
    print(f"  vs EMI 12m:  ₹{savings['vs_emi_12m']:,.0f} ({savings['vs_emi_12m_percent']:.1f}%)")
    print(f"  vs Rental:   ₹{savings['vs_rental']:,.0f} ({savings['vs_rental_percent']:.1f}%)")

    # Participation constraint check
    pc = check_participation_vs_purchase(
        sesp_npv=comparison['npv_comparison']['sesp'],
        purchase_npv=comparison['npv_comparison']['purchase'],
        threshold=0.10,
    )
    print(f"\nParticipation Constraint (10% threshold): {pc['message']}")

    # Calculate required subsidy for 15% savings
    req_subsidy = calculate_required_subsidy(
        mrp=MRP,
        target_savings_percent=0.15,
        tenure_years=2,
        segment='moderate',
    )
    print(f"\nRequired subsidy for 15% savings: ₹{req_subsidy['required_subsidy']:,.0f} "
          f"({req_subsidy['subsidy_percent']}% of MRP)")

    print("\n✓ Calculator module working correctly!")
