"""
India-Specific Adjustments
==========================

This module handles critical India-specific factors that affect the
SESP pricing model:

1. SEASONALITY: AC usage varies dramatically by month and region
   - North India: Summer 1.7x, Winter 0.05x
   - South India: More moderate variation

2. GST: 18% on ALL services (must be consistent across SESP AND alternatives)

3. DUAL DISCOUNT RATES:
   - Customer: 16-28% (cash-constrained, high implicit rate)
   - Firm: 12% (WACC, can finance cheaply)

4. ELECTRICITY SLABS: Progressive tariff structure (₹3.5-7.5/kWh)

5. TERMINAL VALUE: Purchased assets have resale value; subscriptions don't

These adjustments are CRITICAL for accurate model comparisons.
Without them, participation constraints and profitability calculations
will be unrealistic.
"""

from typing import Dict, List, Any, Optional, Tuple
import sys
from pathlib import Path

# Add config to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.loader import (
    get_seasonality,
    get_discount_rate,
    get_terminal_value,
    get_market_params,
    GST_RATE,
)


# =============================================================================
# SEASONALITY
# =============================================================================

# Default seasonality profiles (can also be loaded from config)
SEASONALITY_PROFILES = {
    'north': [0.05, 0.15, 0.60, 1.40, 1.70, 1.30, 0.80, 0.70, 0.80, 0.50, 0.15, 0.05],
    'south': [0.40, 0.50, 0.80, 1.20, 1.30, 1.10, 0.90, 0.90, 0.90, 0.70, 0.50, 0.40],
    'west': [0.20, 0.30, 0.70, 1.30, 1.50, 1.20, 0.80, 0.80, 0.90, 0.60, 0.30, 0.20],
    'east': [0.15, 0.25, 0.65, 1.35, 1.60, 1.25, 0.85, 0.85, 0.90, 0.55, 0.25, 0.15],
    'fridge': [0.95, 0.95, 1.00, 1.05, 1.10, 1.10, 1.05, 1.05, 1.00, 1.00, 0.95, 0.95],
}

# Month names for reference
MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def apply_seasonality(
    baseline_value: float,
    month_index: int,
    region: str = 'north',
    appliance: str = 'AC'
) -> float:
    """
    Apply seasonal adjustment to a baseline value.

    Args:
        baseline_value: Monthly baseline value (hours, kWh, or any metric)
        month_index: 0-based month index (Jan=0, Dec=11)
        region: 'north', 'south', 'west', or 'east'
        appliance: 'AC' or 'FRIDGE'

    Returns:
        Seasonally adjusted value.

    Example:
        >>> baseline_hours = 150  # Monthly baseline
        >>> apply_seasonality(baseline_hours, 4, 'north', 'AC')  # May
        255.0  # 150 × 1.70 (peak summer)
        >>> apply_seasonality(baseline_hours, 11, 'north', 'AC')  # December
        7.5  # 150 × 0.05 (winter)
    """
    if month_index < 0 or month_index > 11:
        raise ValueError(f"month_index must be 0-11, got {month_index}")

    if appliance.upper() == 'FRIDGE':
        profile = SEASONALITY_PROFILES['fridge']
    else:
        region_key = region.lower()
        if region_key not in SEASONALITY_PROFILES:
            raise ValueError(
                f"Unknown region: {region}. "
                f"Use: {list(SEASONALITY_PROFILES.keys())}"
            )
        profile = SEASONALITY_PROFILES[region_key]

    return baseline_value * profile[month_index]


def get_seasonality_profile(
    region: str = 'north',
    appliance: str = 'AC'
) -> List[float]:
    """
    Get the full 12-month seasonality profile.

    Args:
        region: 'north', 'south', 'west', or 'east'
        appliance: 'AC' or 'FRIDGE'

    Returns:
        List of 12 monthly multipliers.
    """
    if appliance.upper() == 'FRIDGE':
        return SEASONALITY_PROFILES['fridge'].copy()

    region_key = region.lower()
    if region_key not in SEASONALITY_PROFILES:
        raise ValueError(f"Unknown region: {region}")

    return SEASONALITY_PROFILES[region_key].copy()


def apply_seasonality_to_series(
    baseline_monthly: float,
    tenure_months: int,
    start_month: int = 0,
    region: str = 'north',
    appliance: str = 'AC'
) -> List[float]:
    """
    Apply seasonality to generate a monthly series.

    Args:
        baseline_monthly: Base monthly value
        tenure_months: Number of months
        start_month: Starting month (0=Jan)
        region: Region for AC seasonality
        appliance: 'AC' or 'FRIDGE'

    Returns:
        List of monthly values with seasonality applied.
    """
    values = []
    for i in range(tenure_months):
        month = (start_month + i) % 12
        values.append(apply_seasonality(baseline_monthly, month, region, appliance))
    return values


# =============================================================================
# GST CALCULATIONS
# =============================================================================

def calculate_gst(amount: float, inclusive: bool = False) -> Dict[str, float]:
    """
    Calculate GST on an amount.

    CRITICAL: GST must be applied consistently to BOTH SESP AND alternatives.
    Inconsistent GST application is a common error that skews comparisons.

    Args:
        amount: The base amount
        inclusive: If True, amount already includes GST

    Returns:
        Dictionary with base, gst, and total amounts.

    Example:
        >>> calculate_gst(649)  # Monthly fee
        {'base': 649, 'gst': 116.82, 'total': 765.82}

        >>> calculate_gst(45000, inclusive=True)  # MRP (GST-inclusive)
        {'base': 38135.59, 'gst': 6864.41, 'total': 45000}
    """
    if inclusive:
        # Extract GST from inclusive amount
        base = amount / (1 + GST_RATE)
        gst = amount - base
        total = amount
    else:
        # Add GST to base amount
        base = amount
        gst = amount * GST_RATE
        total = amount + gst

    return {
        'base': round(base, 2),
        'gst': round(gst, 2),
        'total': round(total, 2)
    }


def calculate_gst_on_services(
    amounts: Dict[str, float],
    apply_gst: bool = True
) -> Dict[str, Dict[str, float]]:
    """
    Apply GST to multiple service amounts.

    Args:
        amounts: Dictionary of service names to amounts
        apply_gst: Whether to apply GST (for comparison)

    Returns:
        Dictionary with GST breakdown for each service.

    Example:
        >>> calculate_gst_on_services({'amc': 2500, 'repair': 3000})
        {
            'amc': {'base': 2500, 'gst': 450, 'total': 2950},
            'repair': {'base': 3000, 'gst': 540, 'total': 3540},
            'totals': {'base': 5500, 'gst': 990, 'total': 6490}
        }
    """
    result = {}
    total_base = 0
    total_gst = 0
    total_amount = 0

    for service, amount in amounts.items():
        if apply_gst:
            breakdown = calculate_gst(amount)
        else:
            breakdown = {'base': amount, 'gst': 0, 'total': amount}

        result[service] = breakdown
        total_base += breakdown['base']
        total_gst += breakdown['gst']
        total_amount += breakdown['total']

    result['totals'] = {
        'base': round(total_base, 2),
        'gst': round(total_gst, 2),
        'total': round(total_amount, 2)
    }

    return result


def validate_gst_consistency(
    sesp_costs: Dict[str, Any],
    purchase_costs: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate that GST is applied consistently to both scenarios.

    This is a CRITICAL check. Inconsistent GST makes SESP look 18% more
    expensive than it really is (relative to alternatives).

    Args:
        sesp_costs: Cost breakdown for SESP scenario
        purchase_costs: Cost breakdown for purchase scenario

    Returns:
        Tuple of (is_consistent, list of issues)
    """
    issues = []

    # Check SESP has GST on services
    if 'gst' not in str(sesp_costs).lower() or sesp_costs.get('gst_amount', 0) == 0:
        issues.append("SESP: GST not applied to subscription fees")

    # Check purchase has GST on AMC
    amc_gst = purchase_costs.get('amc_gst', 0)
    if amc_gst == 0 and purchase_costs.get('amc_annual', 0) > 0:
        issues.append("Purchase: GST not applied to AMC")

    # Check purchase has GST on repairs
    repair_gst = purchase_costs.get('repair_gst', 0)
    if repair_gst == 0 and purchase_costs.get('expected_repairs', 0) > 0:
        issues.append("Purchase: GST not applied to repairs")

    is_consistent = len(issues) == 0
    return is_consistent, issues


# =============================================================================
# NPV CALCULATIONS
# =============================================================================

# Default discount rates
FIRM_DISCOUNT_RATE = 0.12  # 12% WACC
CUSTOMER_DISCOUNT_RATES = {
    'light': 0.28,      # Cash-constrained, high implicit rate
    'moderate': 0.22,   # Moderate savings
    'heavy': 0.16       # Affluent, lower rate
}


def npv_customer(
    cash_flows: List[float],
    segment: str = 'moderate',
    annual_rate: Optional[float] = None
) -> float:
    """
    Calculate NPV from customer's perspective.

    Customers have HIGH discount rates (16-28%) because they are
    cash-constrained and value money today much more than future savings.

    Args:
        cash_flows: List of monthly cash flows (negative = outflow)
        segment: 'light', 'moderate', or 'heavy'
        annual_rate: Override annual discount rate (optional)

    Returns:
        Net Present Value from customer's perspective.

    Example:
        >>> monthly_fee = 649 * 1.18  # With GST
        >>> cash_flows = [-monthly_fee] * 24
        >>> npv_customer(cash_flows, 'moderate')
        -14567.32  # Present value of 24 months of payments
    """
    if annual_rate is None:
        annual_rate = CUSTOMER_DISCOUNT_RATES.get(segment, 0.22)

    monthly_rate = annual_rate / 12

    npv = 0.0
    for t, cf in enumerate(cash_flows):
        npv += cf / ((1 + monthly_rate) ** t)

    return round(npv, 2)


def npv_firm(
    cash_flows: List[float],
    annual_rate: Optional[float] = None
) -> float:
    """
    Calculate NPV from firm's perspective.

    Firms have LOW discount rates (~12% WACC) because they can access
    capital markets and finance cheaply. This creates "value arbitrage" —
    the same cash flow is worth more to the firm than to the customer.

    Args:
        cash_flows: List of monthly cash flows (negative = outflow)
        annual_rate: Override annual discount rate (optional)

    Returns:
        Net Present Value from firm's perspective.

    Example:
        >>> monthly_revenue = 649 * 0.847  # Net of GST
        >>> cash_flows = [monthly_revenue] * 24
        >>> npv_firm(cash_flows)
        11843.67  # Present value of 24 months of revenue
    """
    if annual_rate is None:
        annual_rate = FIRM_DISCOUNT_RATE

    monthly_rate = annual_rate / 12

    npv = 0.0
    for t, cf in enumerate(cash_flows):
        npv += cf / ((1 + monthly_rate) ** t)

    return round(npv, 2)


def calculate_npv_arbitrage(
    cash_flows: List[float],
    segment: str = 'moderate'
) -> Dict[str, Any]:
    """
    Calculate the NPV arbitrage between firm and customer.

    This arbitrage is the economic engine of subscription models.
    The firm values future payments more than the customer, enabling
    the subsidy model to work.

    Args:
        cash_flows: Monthly cash flow stream
        segment: Customer segment for discount rate

    Returns:
        Dictionary with NPV for both parties and arbitrage amount.
    """
    customer_npv = npv_customer(cash_flows, segment)
    firm_npv = npv_firm(cash_flows)

    return {
        'customer_npv': customer_npv,
        'firm_npv': firm_npv,
        'arbitrage': round(firm_npv - abs(customer_npv), 2),
        'arbitrage_percent': round((firm_npv / abs(customer_npv) - 1) * 100, 1),
        'customer_rate': CUSTOMER_DISCOUNT_RATES.get(segment, 0.22),
        'firm_rate': FIRM_DISCOUNT_RATE
    }


# =============================================================================
# ELECTRICITY COST CALCULATIONS
# =============================================================================

# Default slab structure (can be loaded from config)
ELECTRICITY_SLABS = [
    {'limit': 200, 'rate': 3.5},    # 0-200 units
    {'limit': 400, 'rate': 5.0},    # 201-400 units
    {'limit': 800, 'rate': 6.5},    # 401-800 units
    {'limit': float('inf'), 'rate': 7.5}  # 800+ units
]


def calculate_electricity_cost_slabs(
    monthly_kwh: float,
    slabs: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Calculate electricity cost using slab-based tariff.

    This is for reference only — SESP does NOT charge for electricity
    (that's Discom's domain). This function helps estimate customer's
    total energy cost for value proposition comparisons.

    Args:
        monthly_kwh: Monthly electricity consumption in kWh
        slabs: Optional custom slab structure

    Returns:
        Dictionary with cost breakdown by slab.

    Example:
        >>> calculate_electricity_cost_slabs(450)
        {
            'total_kwh': 450,
            'total_cost': 2375.0,
            'average_rate': 5.28,
            'slab_breakdown': [
                {'slab': '0-200', 'units': 200, 'rate': 3.5, 'cost': 700},
                {'slab': '201-400', 'units': 200, 'rate': 5.0, 'cost': 1000},
                {'slab': '401-800', 'units': 50, 'rate': 6.5, 'cost': 325}
            ]
        }
    """
    if slabs is None:
        slabs = ELECTRICITY_SLABS

    remaining = monthly_kwh
    total_cost = 0.0
    breakdown = []
    prev_limit = 0

    for slab in slabs:
        if remaining <= 0:
            break

        slab_capacity = slab['limit'] - prev_limit
        units_in_slab = min(remaining, slab_capacity)

        cost = units_in_slab * slab['rate']
        total_cost += cost

        if units_in_slab > 0:
            breakdown.append({
                'slab': f"{prev_limit}-{slab['limit'] if slab['limit'] != float('inf') else '∞'}",
                'units': units_in_slab,
                'rate': slab['rate'],
                'cost': round(cost, 2)
            })

        remaining -= units_in_slab
        prev_limit = slab['limit']

    average_rate = total_cost / monthly_kwh if monthly_kwh > 0 else 0

    return {
        'total_kwh': monthly_kwh,
        'total_cost': round(total_cost, 2),
        'average_rate': round(average_rate, 2),
        'slab_breakdown': breakdown
    }


# =============================================================================
# TERMINAL VALUE ADJUSTMENT
# =============================================================================

# Default terminal values (can be loaded from config)
TERMINAL_VALUES = {
    'AC': {
        'year_3': 12000,
        'year_5': 5000,
        'year_7': 2500,
        'year_10': 1500
    },
    'FRIDGE': {
        'year_3': 9000,
        'year_5': 6000,
        'year_7': 4000,
        'year_10': 2500
    }
}


def get_terminal_value_local(
    appliance: str,
    tenure_years: int
) -> float:
    """
    Get terminal (resale) value for an appliance.

    When a customer buys an appliance, they own an asset with residual value.
    Subscription does NOT create this asset ownership.
    This must be factored into participation constraint comparisons.

    Args:
        appliance: 'AC' or 'FRIDGE'
        tenure_years: Number of years

    Returns:
        Terminal value in INR.
    """
    appliance_key = appliance.upper()
    if appliance_key not in TERMINAL_VALUES:
        raise ValueError(f"Unknown appliance: {appliance}")

    values = TERMINAL_VALUES[appliance_key]

    # Find closest year <= tenure_years
    available_years = sorted([int(k.split('_')[1]) for k in values.keys()])

    for year in reversed(available_years):
        if year <= tenure_years:
            return values[f'year_{year}']

    # If tenure is shorter than minimum, use highest value
    return values[f'year_{available_years[0]}']


def adjusted_purchase_cost_with_terminal(
    mrp: float,
    tenure_years: int,
    segment: str = 'moderate',
    appliance: str = 'AC',
    include_amc: bool = True,
    amc_annual: float = 2500
) -> Dict[str, Any]:
    """
    Calculate the TRUE cost of purchasing, accounting for terminal value.

    This is crucial for fair participation constraint comparison.
    Without adjusting for terminal value, we overstate subscription's
    attractiveness because customer intuitively knows they "own something".

    Formula:
        Adjusted_Cost = MRP + AMC - PV(Terminal_Value)

    Args:
        mrp: Maximum Retail Price (GST-inclusive)
        tenure_years: Comparison period in years
        segment: Customer segment for discount rate
        appliance: 'AC' or 'FRIDGE'
        include_amc: Whether to include AMC costs
        amc_annual: Annual AMC cost (pre-GST)

    Returns:
        Dictionary with complete cost breakdown.

    Example:
        >>> adjusted_purchase_cost_with_terminal(45000, 2, 'moderate', 'AC')
        {
            'mrp': 45000,
            'amc_total': 5900,  # 2500 × 2 × 1.18
            'terminal_value': 12000,
            'terminal_pv': 8100,  # PV at customer rate
            'total_cost': 42800,  # 45000 + 5900 - 8100
            'effective_mrp': 36900  # MRP - PV(terminal)
        }
    """
    discount_rate = CUSTOMER_DISCOUNT_RATES.get(segment, 0.22)

    # Get terminal value
    terminal_value = get_terminal_value_local(appliance, tenure_years)

    # Calculate PV of terminal value
    terminal_pv = terminal_value / ((1 + discount_rate) ** tenure_years)

    # AMC costs (with GST, spread over tenure)
    if include_amc:
        amc_with_gst = amc_annual * (1 + GST_RATE)
        amc_total = amc_with_gst * tenure_years
    else:
        amc_total = 0

    # Total adjusted cost
    total_cost = mrp + amc_total - terminal_pv

    return {
        'mrp': mrp,
        'amc_annual_with_gst': round(amc_annual * (1 + GST_RATE), 2) if include_amc else 0,
        'amc_total': round(amc_total, 2),
        'terminal_value': terminal_value,
        'terminal_pv': round(terminal_pv, 2),
        'total_cost': round(total_cost, 2),
        'effective_mrp': round(mrp - terminal_pv, 2),
        'discount_rate': discount_rate,
        'tenure_years': tenure_years
    }


# =============================================================================
# COMBINED ANALYSIS
# =============================================================================

def generate_monthly_projections(
    baseline_monthly_hours: float,
    tenure_months: int,
    start_month: int = 0,
    region: str = 'north',
    appliance: str = 'AC'
) -> List[Dict[str, Any]]:
    """
    Generate monthly projections with seasonality applied.

    Args:
        baseline_monthly_hours: Expected average monthly runtime hours
        tenure_months: Contract duration
        start_month: Starting month (0=Jan)
        region: Region for AC seasonality
        appliance: 'AC' or 'FRIDGE'

    Returns:
        List of monthly projection dictionaries.
    """
    projections = []
    profile = get_seasonality_profile(region, appliance)

    for i in range(tenure_months):
        month = (start_month + i) % 12
        seasonal_factor = profile[month]
        adjusted_hours = baseline_monthly_hours * seasonal_factor

        projections.append({
            'period': i + 1,
            'month_index': month,
            'month_name': MONTH_NAMES[month],
            'seasonal_factor': seasonal_factor,
            'baseline_hours': baseline_monthly_hours,
            'adjusted_hours': round(adjusted_hours, 1)
        })

    return projections


# =============================================================================
# MODULE INFO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("India-Specific Adjustments — Demo")
    print("=" * 60)

    # Seasonality demo
    print("\n--- Seasonality (North India AC) ---")
    for month in range(12):
        hours = apply_seasonality(150, month, 'north', 'AC')
        print(f"{MONTH_NAMES[month]:3}: {hours:.1f} hours (factor: {SEASONALITY_PROFILES['north'][month]})")

    # GST demo
    print("\n--- GST Calculation ---")
    gst_result = calculate_gst(649)
    print(f"Monthly fee ₹649 + GST = ₹{gst_result['total']:.2f}")

    # NPV arbitrage demo
    print("\n--- NPV Arbitrage ---")
    cash_flows = [649 * 1.18] * 24
    arbitrage = calculate_npv_arbitrage(cash_flows, 'moderate')
    print(f"Customer NPV: ₹{arbitrage['customer_npv']:.2f}")
    print(f"Firm NPV: ₹{arbitrage['firm_npv']:.2f}")
    print(f"Arbitrage: ₹{arbitrage['arbitrage']:.2f} ({arbitrage['arbitrage_percent']:.1f}%)")

    # Electricity slabs demo
    print("\n--- Electricity Cost (450 kWh) ---")
    elec = calculate_electricity_cost_slabs(450)
    print(f"Total: ₹{elec['total_cost']:.2f} (avg ₹{elec['average_rate']:.2f}/kWh)")

    # Terminal value demo
    print("\n--- Terminal Value Adjustment ---")
    purchase = adjusted_purchase_cost_with_terminal(45000, 2, 'moderate', 'AC')
    print(f"MRP: ₹{purchase['mrp']}")
    print(f"Terminal PV: ₹{purchase['terminal_pv']:.0f}")
    print(f"Adjusted cost: ₹{purchase['total_cost']:.0f}")
