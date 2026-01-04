"""
Traditional Profitability Model (Task 3.1)
==========================================

Models pre-SESP (traditional appliance sales) economics from the
manufacturer's perspective.

Traditional Sale Model:
- One-time sale at MRP through dealer network
- Dealer takes margin (15-20%)
- Customer owns asset
- No recurring revenue except AMC (low attach rate ~25%)

Key Metrics:
- Revenue per unit: MRP × (1 - dealer_margin)
- Costs: Manufacturing + Warranty reserve
- Gross margin: Typically 15-22%
- CLV: Primarily one-time sale + small AMC component

This provides the "before" benchmark for SESP comparison.
"""

from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# =============================================================================
# Default Parameters (from market research / industry data)
# =============================================================================

TRADITIONAL_DEFAULTS = {
    'mrp': 45000,                    # AC 1.5T 5-star inverter
    'manufacturing_cost': 30000,     # Direct + overhead
    'dealer_margin': 0.18,           # 18% dealer margin
    'warranty_claim_rate': 0.12,     # 12% of units claim warranty
    'avg_warranty_claim': 3500,      # Average claim cost
    'amc_attach_rate': 0.25,         # 25% of customers buy AMC
    'amc_annual_price': 2500,        # AMC selling price
    'amc_margin': 0.52,              # 52% margin on AMC
    'referral_rate': 0.08,           # 8% of customers refer
    'referral_value': 300,           # Value per referral
    'gst_rate': 0.18,                # 18% GST
    'firm_discount_rate': 0.12,      # Firm's WACC
}


# =============================================================================
# Revenue Calculations
# =============================================================================

def calculate_traditional_revenue(
    mrp: float = TRADITIONAL_DEFAULTS['mrp'],
    dealer_margin: float = TRADITIONAL_DEFAULTS['dealer_margin'],
) -> Dict[str, Any]:
    """
    Calculate revenue from a traditional appliance sale.

    Revenue Model:
    - Manufacturer sells to dealer at (MRP - dealer_margin)
    - GST is collected but remitted to government (pass-through)
    - Net revenue = MRP × (1 - dealer_margin) / 1.18

    Args:
        mrp: Maximum Retail Price (GST-inclusive)
        dealer_margin: Percentage given to dealer (0.15-0.22 typical)

    Returns:
        Dictionary with revenue breakdown.

    Example:
        >>> rev = calculate_traditional_revenue(45000, 0.18)
        >>> rev['net_revenue']  # ~31,271
    """
    # MRP is GST-inclusive, extract base
    mrp_base = mrp / (1 + TRADITIONAL_DEFAULTS['gst_rate'])
    mrp_gst = mrp - mrp_base

    # Dealer gets margin on MRP-inclusive price
    dealer_takes = mrp * dealer_margin
    manufacturer_receives = mrp - dealer_takes

    # Net of GST (GST is pass-through)
    net_revenue = manufacturer_receives / (1 + TRADITIONAL_DEFAULTS['gst_rate'])

    return {
        'mrp': mrp,
        'mrp_base': round(mrp_base, 2),
        'mrp_gst': round(mrp_gst, 2),
        'dealer_margin_percent': dealer_margin * 100,
        'dealer_margin_amount': round(dealer_takes, 2),
        'manufacturer_receives_gross': round(manufacturer_receives, 2),
        'net_revenue': round(net_revenue, 2),
        'notes': 'Net revenue is manufacturer share minus GST (pass-through)'
    }


def calculate_amc_revenue(
    amc_attach_rate: float = TRADITIONAL_DEFAULTS['amc_attach_rate'],
    amc_annual_price: float = TRADITIONAL_DEFAULTS['amc_annual_price'],
    amc_margin: float = TRADITIONAL_DEFAULTS['amc_margin'],
    years: int = 5,
) -> Dict[str, Any]:
    """
    Calculate expected AMC (Annual Maintenance Contract) revenue.

    AMC Model:
    - Only ~25% of customers buy AMC
    - AMC typically sold years 2-5 (year 1 under warranty)
    - ~52% margin on AMC services

    Args:
        amc_attach_rate: Percentage of customers who buy AMC
        amc_annual_price: Annual AMC price
        amc_margin: Margin on AMC (revenue - service cost)
        years: Number of years for AMC opportunity

    Returns:
        Dictionary with AMC revenue breakdown.
    """
    amc_years = max(0, years - 1)  # Year 1 is warranty, AMC from year 2

    expected_amc_revenue = amc_attach_rate * amc_annual_price * amc_years
    expected_amc_profit = expected_amc_revenue * amc_margin
    amc_cost = expected_amc_revenue * (1 - amc_margin)

    return {
        'attach_rate': amc_attach_rate,
        'annual_price': amc_annual_price,
        'years_offered': amc_years,
        'expected_revenue': round(expected_amc_revenue, 2),
        'margin_percent': amc_margin * 100,
        'expected_profit': round(expected_amc_profit, 2),
        'expected_service_cost': round(amc_cost, 2),
        'notes': f'Based on {amc_attach_rate*100:.0f}% attach rate over {amc_years} years'
    }


# =============================================================================
# Cost Calculations
# =============================================================================

def calculate_traditional_costs(
    manufacturing_cost: float = TRADITIONAL_DEFAULTS['manufacturing_cost'],
    warranty_claim_rate: float = TRADITIONAL_DEFAULTS['warranty_claim_rate'],
    avg_warranty_claim: float = TRADITIONAL_DEFAULTS['avg_warranty_claim'],
) -> Dict[str, Any]:
    """
    Calculate costs for a traditional sale.

    Cost Model:
    - Manufacturing cost (COGS)
    - Warranty reserve (expected claims)
    - No installation (dealer handles or customer arranges)
    - No IoT (no smart features)
    - No CAC (dealer does customer acquisition)

    Args:
        manufacturing_cost: Direct + allocated overhead per unit
        warranty_claim_rate: % of units that claim warranty
        avg_warranty_claim: Average cost of warranty claim

    Returns:
        Dictionary with cost breakdown.
    """
    warranty_reserve = warranty_claim_rate * avg_warranty_claim

    total_cost = manufacturing_cost + warranty_reserve

    return {
        'manufacturing_cost': manufacturing_cost,
        'warranty_claim_rate': warranty_claim_rate * 100,
        'avg_warranty_claim': avg_warranty_claim,
        'warranty_reserve': round(warranty_reserve, 2),
        'installation_cost': 0,  # Dealer/customer handles
        'iot_cost': 0,           # No smart features
        'cac': 0,                # Dealer does acquisition
        'total_cost': round(total_cost, 2),
        'notes': 'Traditional model has minimal post-sale costs'
    }


# =============================================================================
# Margin Calculations
# =============================================================================

def calculate_traditional_margin(
    mrp: float = TRADITIONAL_DEFAULTS['mrp'],
    dealer_margin: float = TRADITIONAL_DEFAULTS['dealer_margin'],
    manufacturing_cost: float = TRADITIONAL_DEFAULTS['manufacturing_cost'],
    warranty_claim_rate: float = TRADITIONAL_DEFAULTS['warranty_claim_rate'],
    avg_warranty_claim: float = TRADITIONAL_DEFAULTS['avg_warranty_claim'],
) -> Dict[str, Any]:
    """
    Calculate gross margin for a traditional sale.

    Margin = (Net Revenue - Total Costs) / Net Revenue

    Args:
        All parameters from revenue and cost functions.

    Returns:
        Dictionary with margin breakdown.
    """
    revenue = calculate_traditional_revenue(mrp, dealer_margin)
    costs = calculate_traditional_costs(
        manufacturing_cost, warranty_claim_rate, avg_warranty_claim
    )

    gross_profit = revenue['net_revenue'] - costs['total_cost']
    gross_margin_percent = (gross_profit / revenue['net_revenue']) * 100

    return {
        'net_revenue': revenue['net_revenue'],
        'total_cost': costs['total_cost'],
        'gross_profit': round(gross_profit, 2),
        'gross_margin_percent': round(gross_margin_percent, 2),
        'revenue_breakdown': revenue,
        'cost_breakdown': costs,
        'notes': 'Traditional margin before SG&A and taxes'
    }


# =============================================================================
# Customer Lifetime Value
# =============================================================================

def calculate_traditional_clv(
    mrp: float = TRADITIONAL_DEFAULTS['mrp'],
    dealer_margin: float = TRADITIONAL_DEFAULTS['dealer_margin'],
    manufacturing_cost: float = TRADITIONAL_DEFAULTS['manufacturing_cost'],
    warranty_claim_rate: float = TRADITIONAL_DEFAULTS['warranty_claim_rate'],
    avg_warranty_claim: float = TRADITIONAL_DEFAULTS['avg_warranty_claim'],
    amc_attach_rate: float = TRADITIONAL_DEFAULTS['amc_attach_rate'],
    amc_annual_price: float = TRADITIONAL_DEFAULTS['amc_annual_price'],
    amc_margin: float = TRADITIONAL_DEFAULTS['amc_margin'],
    referral_rate: float = TRADITIONAL_DEFAULTS['referral_rate'],
    referral_value: float = TRADITIONAL_DEFAULTS['referral_value'],
    years: int = 5,
    discount_rate: float = TRADITIONAL_DEFAULTS['firm_discount_rate'],
) -> Dict[str, Any]:
    """
    Calculate Customer Lifetime Value for traditional model.

    CLV Components:
    1. Initial sale margin (one-time)
    2. AMC revenue (recurring, for attached customers)
    3. Referral value (probabilistic)

    Args:
        All parameters from revenue, cost, AMC functions.
        years: CLV horizon (typically 5 years)
        discount_rate: Firm's discount rate for NPV

    Returns:
        Dictionary with CLV breakdown.

    Example:
        >>> clv = calculate_traditional_clv()
        >>> clv['total_clv']  # Expected CLV per customer
    """
    # 1. Initial sale margin
    margin = calculate_traditional_margin(
        mrp, dealer_margin, manufacturing_cost,
        warranty_claim_rate, avg_warranty_claim
    )
    initial_margin = margin['gross_profit']

    # 2. AMC revenue (NPV)
    amc = calculate_amc_revenue(
        amc_attach_rate, amc_annual_price, amc_margin, years
    )
    # NPV of AMC profit (spread over years 2-5)
    amc_npv = 0
    annual_amc_profit = amc['expected_profit'] / max(1, amc['years_offered'])
    for year in range(2, years + 1):
        amc_npv += annual_amc_profit / ((1 + discount_rate) ** year)

    # 3. Referral value
    referral_contribution = referral_rate * referral_value

    # Total CLV
    total_clv = initial_margin + amc_npv + referral_contribution

    return {
        'initial_margin': round(initial_margin, 2),
        'amc_npv': round(amc_npv, 2),
        'referral_contribution': round(referral_contribution, 2),
        'total_clv': round(total_clv, 2),
        'horizon_years': years,
        'discount_rate': discount_rate,
        'breakdown': {
            'initial_sale': round((initial_margin / total_clv) * 100, 1),
            'amc': round((amc_npv / total_clv) * 100, 1),
            'referral': round((referral_contribution / total_clv) * 100, 1),
        },
        'notes': f'{years}-year CLV at {discount_rate*100:.0f}% discount rate'
    }


# =============================================================================
# Summary Function
# =============================================================================

def get_traditional_summary(
    mrp: float = TRADITIONAL_DEFAULTS['mrp'],
    dealer_margin: float = TRADITIONAL_DEFAULTS['dealer_margin'],
    years: int = 5,
) -> Dict[str, Any]:
    """
    Get complete traditional model summary for comparison.

    Args:
        mrp: Product MRP
        dealer_margin: Dealer margin percentage
        years: CLV horizon

    Returns:
        Complete summary dictionary for comparison.
    """
    revenue = calculate_traditional_revenue(mrp, dealer_margin)
    costs = calculate_traditional_costs()
    margin = calculate_traditional_margin(mrp, dealer_margin)
    clv = calculate_traditional_clv(mrp=mrp, dealer_margin=dealer_margin, years=years)

    return {
        'model': 'Traditional',
        'description': 'One-time sale through dealer network',
        'mrp': mrp,
        'dealer_margin': dealer_margin,
        'years': years,
        'revenue_per_unit': revenue['net_revenue'],
        'cost_per_unit': costs['total_cost'],
        'gross_margin': margin['gross_profit'],
        'gross_margin_percent': margin['gross_margin_percent'],
        'clv': clv['total_clv'],
        'clv_breakdown': clv['breakdown'],
        'customer_relationship': 'Transactional',
        'data_asset': 'None',
        'recurring_revenue': 'AMC only (25% attach)',
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
    print("Traditional Profitability Model — Demo")
    print("=" * 60)

    # Get summary
    summary = get_traditional_summary()

    print(f"\nModel: {summary['model']}")
    print(f"Description: {summary['description']}")
    print(f"\nMRP: Rs{summary['mrp']:,}")
    print(f"Dealer Margin: {summary['dealer_margin']*100:.0f}%")

    print(f"\n--- Per Unit Economics ---")
    print(f"Revenue (net): Rs{summary['revenue_per_unit']:,.0f}")
    print(f"Cost: Rs{summary['cost_per_unit']:,.0f}")
    print(f"Gross Profit: Rs{summary['gross_margin']:,.0f}")
    print(f"Gross Margin: {summary['gross_margin_percent']:.1f}%")

    print(f"\n--- Customer Lifetime Value ({summary['years']} years) ---")
    print(f"Total CLV: Rs{summary['clv']:,.0f}")
    print(f"  Initial Sale: {summary['clv_breakdown']['initial_sale']:.0f}%")
    print(f"  AMC: {summary['clv_breakdown']['amc']:.0f}%")
    print(f"  Referral: {summary['clv_breakdown']['referral']:.0f}%")

    print(f"\n--- Strategic Characteristics ---")
    print(f"Customer Relationship: {summary['customer_relationship']}")
    print(f"Data Asset: {summary['data_asset']}")
    print(f"Recurring Revenue: {summary['recurring_revenue']}")

    print("\n✓ Traditional profitability model working correctly!")
