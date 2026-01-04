"""
Simulator — Vectorized Customer Journey Simulation
==================================================

CRITICAL: Uses VECTORIZED operations (pandas/numpy), NOT nested loops.
Performance target: < 10 seconds for 1000 customers × 60 months.

Key Design:
1. Hours-based simulation (NOT kWh) - consistent with bucket model
2. Efficiency score rewards BEHAVIOR, not low usage
3. Overage caps prevent bill shock
4. Uses seasonality from src/adjustments module
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, List

# Import seasonality from adjustments module
from src.adjustments.india_specific import SEASONALITY_PROFILES, get_seasonality_profile

from .data_generator import CUSTOMER_SEGMENTS

# =============================================================================
# PLAN CONSTANTS (from Phase 3c tiered plans)
# =============================================================================

# Monthly fees by plan (Rs)
PLAN_FEES = {
    'lite': 449,
    'standard': 599,
    'premium': 799,
}

# Hours included in each plan (FIXED - kept for reference/testing)
PLAN_HOURS = {
    'lite': 100,
    'standard': 200,
    'premium': 350,
}

# =============================================================================
# SEASONAL HOURS ADJUSTMENT (Behavioral Nudge for Energy Efficiency)
# =============================================================================
# Instead of fixed monthly hours, allocate by season to match expected usage.
# This creates a "budget effect" that nudges users to stay within allocation.

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

# Seasonal hours allocation (replaces fixed PLAN_HOURS)
# Calibrated for weighted average across regions (North/South/West/East)
# Slightly generous to prevent excessive overage in flatter-seasonality regions
SEASONAL_PLAN_HOURS = {
    'lite': {
        'winter': 35,      # Low usage, but South India needs more
        'shoulder': 90,    # Transition months (increased from 75)
        'summer': 140,     # Peak season
        # Annual: 35*4 + 90*4 + 140*4 = 1,060 hrs
    },
    'standard': {
        'winter': 70,      # Raised for South India users (from 50)
        'shoulder': 180,   # Spring/fall (increased from 150)
        'summer': 280,     # Peak AC season
        # Annual: 70*4 + 180*4 + 280*4 = 2,120 hrs
    },
    'premium': {
        'winter': 120,     # Heavy users still use (from 100)
        'shoulder': 320,   # High base usage (from 280)
        'summer': 480,     # Unlimited feel
        # Annual: 120*4 + 320*4 + 480*4 = 3,680 hrs
    },
}


def get_seasonal_hours(plan: str, month: int) -> int:
    """
    Get included hours for a plan in a given month.

    This implements the seasonal hours adjustment that serves as a
    behavioral nudge for energy efficiency via the "budget effect".

    Args:
        plan: 'lite', 'standard', or 'premium'
        month: Month of year (0=Jan, 11=Dec)

    Returns:
        Number of hours included for that plan in that month

    Example:
        >>> get_seasonal_hours('standard', 5)  # June (summer)
        280
        >>> get_seasonal_hours('standard', 0)  # January (winter)
        50
    """
    season = SEASONS[month % 12]
    return SEASONAL_PLAN_HOURS[plan][season]

# Overage rate per excess hour (Rs)
OVERAGE_RATES = {
    'lite': 6,
    'standard': 5,
    'premium': 0,  # Premium is unlimited
}

# Maximum overage cap (Rs) - prevents bill shock
OVERAGE_CAPS = {
    'lite': 150,
    'standard': 200,
    'premium': 0,
}

# Efficiency tiers: score thresholds and discount percentages
EFFICIENCY_TIERS = {
    'champion': {'threshold': 90, 'discount_pct': 0.20, 'badge': '🏆'},
    'star': {'threshold': 75, 'discount_pct': 0.12, 'badge': '⭐'},
    'aware': {'threshold': 60, 'discount_pct': 0.05, 'badge': '🌱'},
    'improve': {'threshold': 0, 'discount_pct': 0.00, 'badge': '📈'},
}

# GST rate
GST_RATE = 0.18

# Segment baseline hours
SEGMENT_HOURS = {
    'light': 100,
    'moderate': 200,
    'heavy': 350,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_seasonality_array(regions: pd.Series, months_of_year: pd.Series) -> np.ndarray:
    """
    Vectorized seasonality lookup.

    Creates a lookup array for region-month combinations.
    """
    # Build a lookup table for all region-month combinations
    seasonality_lookup = {}
    for region in SEASONALITY_PROFILES.keys():
        if region != 'fridge':  # Skip fridge for AC simulation
            for month in range(12):
                seasonality_lookup[(region, month)] = SEASONALITY_PROFILES[region][month]

    # Vectorized lookup
    return np.array([
        seasonality_lookup.get((r, m), 1.0)
        for r, m in zip(regions, months_of_year)
    ])


def _get_seasonal_hours_array(plans: pd.Series, months_of_year: pd.Series) -> np.ndarray:
    """
    Vectorized seasonal hours lookup.

    Creates a lookup array for plan-month combinations using seasonal allocation.
    This implements the "budget effect" for energy efficiency nudging.

    Args:
        plans: Series of plan names ('lite', 'standard', 'premium')
        months_of_year: Series of month indices (0-11)

    Returns:
        Array of hours included for each plan-month combination
    """
    # Build a lookup table for all plan-month combinations
    hours_lookup = {}
    for plan in SEASONAL_PLAN_HOURS.keys():
        for month in range(12):
            hours_lookup[(plan, month)] = get_seasonal_hours(plan, month)

    # Vectorized lookup
    return np.array([
        hours_lookup.get((p, m), PLAN_HOURS.get(p, 200))  # Fallback to fixed hours
        for p, m in zip(plans, months_of_year)
    ])


def _calculate_efficiency_discount(scores: np.ndarray) -> np.ndarray:
    """
    Vectorized efficiency discount calculation.

    Uses np.where for fast conditional logic.
    """
    return np.where(scores >= 90, 0.20,
           np.where(scores >= 75, 0.12,
           np.where(scores >= 60, 0.05, 0.00)))


# =============================================================================
# MAIN SIMULATION FUNCTION
# =============================================================================

def simulate_portfolio(
    customers_df: pd.DataFrame,
    tenure_months: int = 60,
    random_seed: Optional[int] = None,
    include_churn: bool = False,
    noise_std: float = 0.15,
) -> pd.DataFrame:
    """
    VECTORIZED simulation of customer portfolio over tenure.

    Creates a customer × month grid and applies all calculations vectorized.
    NO nested for-loops - uses pandas/numpy broadcasting.

    Args:
        customers_df: DataFrame from generate_customers()
        tenure_months: Number of months to simulate (default 60)
        random_seed: Random seed for reproducibility
        include_churn: Whether to model customer churn (future enhancement)
        noise_std: Standard deviation for usage noise (default 0.15 = 15%)

    Returns:
        DataFrame with one row per customer-month (N × tenure rows)

    Performance:
        Target: < 10 seconds for 1000 customers × 60 months = 60,000 rows

    Example:
        >>> customers = generate_customers(100, random_seed=42)
        >>> grid = simulate_portfolio(customers, tenure_months=12)
        >>> grid.shape
        (1200, ...)
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    n = len(customers_df)
    total_rows = n * tenure_months

    # =========================================================================
    # STEP 1: Create customer × month grid (VECTORIZED)
    # =========================================================================
    grid = pd.DataFrame({
        'customer_id': np.repeat(customers_df['customer_id'].values, tenure_months),
        'month': np.tile(range(tenure_months), n),
        'segment': np.repeat(customers_df['segment'].values, tenure_months),
        'plan': np.repeat(customers_df['plan'].values, tenure_months),
        'region': np.repeat(customers_df['region'].values, tenure_months),
        'usage_factor': np.repeat(customers_df['usage_factor'].values, tenure_months),
        'efficiency_score_base': np.repeat(customers_df['efficiency_score_base'].values, tenure_months),
        'has_credit_card': np.repeat(customers_df['has_credit_card'].values, tenure_months),
        'signup_month': np.repeat(customers_df['signup_month'].values, tenure_months),
        'is_plan_mismatch': np.repeat(customers_df['is_plan_mismatch'].values, tenure_months),
    })

    # =========================================================================
    # STEP 2: Calculate month-of-year for seasonality
    # =========================================================================
    grid['month_of_year'] = (grid['signup_month'] + grid['month']) % 12

    # =========================================================================
    # STEP 3: Apply seasonality (VECTORIZED)
    # =========================================================================
    grid['seasonality'] = _get_seasonality_array(
        grid['region'],
        grid['month_of_year']
    )

    # =========================================================================
    # STEP 4: Calculate actual hours (VECTORIZED)
    # =========================================================================
    # Base hours by segment
    grid['base_hours'] = grid['segment'].map(SEGMENT_HOURS)

    # Add random noise for realistic variation
    noise = np.random.normal(1.0, noise_std, total_rows).clip(0.5, 1.5)

    # Actual hours = base × seasonality × usage_factor × noise
    grid['actual_hours'] = (
        grid['base_hours'] *
        grid['seasonality'] *
        grid['usage_factor'] *
        noise
    ).clip(0)  # No negative hours

    # =========================================================================
    # STEP 5: Calculate plan fees and hours included (VECTORIZED)
    # =========================================================================
    grid['plan_fee'] = grid['plan'].map(PLAN_FEES)

    # Use SEASONAL hours allocation (Budget Effect for energy efficiency)
    # Hours now vary by season: Winter (low) → Shoulder → Summer (high)
    grid['hours_included'] = _get_seasonal_hours_array(
        grid['plan'],
        grid['month_of_year']
    )

    # =========================================================================
    # STEP 6: Calculate overage (VECTORIZED with cap)
    # =========================================================================
    grid['excess_hours'] = (grid['actual_hours'] - grid['hours_included']).clip(lower=0)
    grid['overage_rate'] = grid['plan'].map(OVERAGE_RATES)
    grid['overage_cap'] = grid['plan'].map(OVERAGE_CAPS)

    # Overage = min(excess × rate, cap)
    grid['overage_raw'] = grid['excess_hours'] * grid['overage_rate']
    grid['overage'] = np.minimum(grid['overage_raw'], grid['overage_cap'])

    # =========================================================================
    # STEP 7: Calculate efficiency score and discount (VECTORIZED)
    # =========================================================================
    # Add monthly variation to base efficiency score
    eff_noise = np.random.normal(0, 5, total_rows)  # ±5 points variation
    grid['efficiency_score'] = (grid['efficiency_score_base'] + eff_noise).clip(0, 100)

    # Calculate discount percentage
    grid['discount_pct'] = _calculate_efficiency_discount(grid['efficiency_score'].values)

    # Discount amount (on base fee)
    grid['efficiency_discount'] = grid['plan_fee'] * grid['discount_pct']

    # =========================================================================
    # STEP 8: Calculate customer bill (with GST)
    # =========================================================================
    # Bill = (fee + overage - discount) × (1 + GST)
    grid['bill_pre_gst'] = grid['plan_fee'] + grid['overage'] - grid['efficiency_discount']
    grid['gst_amount'] = grid['bill_pre_gst'] * GST_RATE
    grid['monthly_bill'] = grid['bill_pre_gst'] + grid['gst_amount']

    # =========================================================================
    # STEP 9: Calculate company revenue (net of GST)
    # =========================================================================
    # Company receives bill_pre_gst, GST goes to government
    grid['company_revenue'] = grid['bill_pre_gst']

    # =========================================================================
    # STEP 10: Add derived metrics
    # =========================================================================
    grid['is_over_limit'] = grid['excess_hours'] > 0
    grid['hours_utilization'] = grid['actual_hours'] / grid['hours_included']

    # Assign efficiency tier label
    grid['efficiency_tier'] = np.where(grid['efficiency_score'] >= 90, 'champion',
                               np.where(grid['efficiency_score'] >= 75, 'star',
                               np.where(grid['efficiency_score'] >= 60, 'aware', 'improve')))

    return grid


def simulate_single_customer(
    customer_id: int,
    segment: str,
    plan: str,
    region: str,
    usage_factor: float = 1.0,
    efficiency_score: float = 70.0,
    signup_month: int = 0,
    tenure_months: int = 60,
) -> pd.DataFrame:
    """
    Simulate a single customer's journey (for debugging/testing).

    Args:
        customer_id: Customer identifier
        segment: 'light', 'moderate', or 'heavy'
        plan: 'lite', 'standard', or 'premium'
        region: 'north', 'south', 'west', or 'east'
        usage_factor: Multiplier on baseline usage (default 1.0)
        efficiency_score: Base efficiency score (default 70)
        signup_month: Starting month (0=Jan, default 0)
        tenure_months: Simulation duration (default 60)

    Returns:
        DataFrame with monthly simulation for this customer
    """
    # Create single-customer DataFrame
    customer_df = pd.DataFrame([{
        'customer_id': customer_id,
        'segment': segment,
        'plan': plan,
        'region': region,
        'has_credit_card': True,
        'usage_factor': usage_factor,
        'efficiency_score_base': efficiency_score,
        'churn_risk': 'low',
        'default_risk': 0.02,
        'signup_month': signup_month,
        'is_plan_mismatch': plan != {'light': 'lite', 'moderate': 'standard', 'heavy': 'premium'}[segment],
    }])

    return simulate_portfolio(customer_df, tenure_months=tenure_months)


def calculate_portfolio_margins(grid: pd.DataFrame, params: Optional[Dict] = None) -> Dict:
    """
    Calculate portfolio-level margins from simulation results.

    Args:
        grid: Simulation results from simulate_portfolio()
        params: Optional parameters (subsidy, CAC, etc.)

    Returns:
        Dictionary with margin calculations
    """
    if params is None:
        params = {
            'subsidy_percent': 0.50,
            'mrp': 45000,
            'manufacturing_cost': 30000,
            'iot_cost': 1500,
            'installation_cost': 2500,
            'cac': 2000,
            'bank_cac_subsidy': 2000,
            'warranty_reserve': 2000,
            'monthly_recurring_cost': 192,  # IoT + maintenance
        }

    n_customers = grid['customer_id'].nunique()
    tenure_months = grid['month'].max() + 1

    # Per-customer calculations
    total_revenue = grid.groupby('customer_id')['company_revenue'].sum()
    avg_revenue_per_customer = total_revenue.mean()

    # Upfront economics (per customer)
    customer_pays = params['mrp'] * (1 - params['subsidy_percent'])
    upfront_net = customer_pays / 1.18  # Net of GST

    upfront_cost = (
        params['manufacturing_cost'] +
        params['iot_cost'] +
        params['installation_cost'] +
        params['cac'] +
        params['warranty_reserve']
    )

    upfront_deficit = upfront_cost - upfront_net

    # Recurring economics
    recurring_cost_total = params['monthly_recurring_cost'] * tenure_months

    # Bank CAC subsidy (credit card partnership)
    bank_subsidy = params['bank_cac_subsidy']

    # Total margin
    total_margin = avg_revenue_per_customer - upfront_deficit - recurring_cost_total + bank_subsidy

    return {
        'n_customers': n_customers,
        'tenure_months': tenure_months,
        'avg_revenue_per_customer': avg_revenue_per_customer,
        'upfront_net': upfront_net,
        'upfront_cost': upfront_cost,
        'upfront_deficit': upfront_deficit,
        'recurring_cost_total': recurring_cost_total,
        'bank_cac_subsidy': bank_subsidy,
        'total_margin_per_customer': total_margin,
        'total_portfolio_margin': total_margin * n_customers,
    }


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    import time
    from .data_generator import generate_customers

    # Generate customers
    print("Generating 1000 customers...")
    customers = generate_customers(1000, random_seed=42)

    # Run simulation
    print("Running 60-month simulation...")
    start = time.time()
    grid = simulate_portfolio(customers, tenure_months=60, random_seed=42)
    elapsed = time.time() - start

    print(f"\nSimulation completed in {elapsed:.2f} seconds")
    print(f"Grid shape: {grid.shape} ({len(grid):,} rows)")
    print(f"\nSample output:")
    print(grid.head(10).to_string())

    # Show summary stats
    print(f"\n--- Summary Statistics ---")
    print(f"Avg monthly bill: Rs{grid['monthly_bill'].mean():.2f}")
    print(f"Avg efficiency score: {grid['efficiency_score'].mean():.1f}")
    print(f"% over plan limit: {grid['is_over_limit'].mean():.1%}")

    # Segment breakdown
    print(f"\nBy segment:")
    for seg in ['light', 'moderate', 'heavy']:
        seg_data = grid[grid['segment'] == seg]
        print(f"  {seg}: avg hours={seg_data['actual_hours'].mean():.1f}, "
              f"avg bill=Rs{seg_data['monthly_bill'].mean():.2f}")
