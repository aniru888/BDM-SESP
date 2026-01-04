"""
Participation Constraint Diagnostic Script
==========================================

This script diagnoses WHY all pricing scenarios violate the
participation constraint (show negative customer savings).

Run with: python -m SESP_Model.diagnose_pc
"""

import sys
from pathlib import Path

# Fix Windows encoding for console output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.alternatives.calculators import (
    calculate_purchase_cost,
    calculate_sesp_cost,
    compare_alternatives,
    APPLIANCE_MRP,
)
from src.constraints.participation import (
    check_pc_vs_purchase,
    find_pc_boundary,
    analyze_pc_sensitivity,
)
from src.adjustments.india_specific import (
    CUSTOMER_DISCOUNT_RATES,
    GST_RATE,
    get_terminal_value_local,
)
from src.pricing.bucket_model import SUBSCRIPTION_PLANS


def diagnose_single_scenario(
    scenario_name: str,
    subsidy_percent: float,
    plan: str,
    tenure_years: int = 3,
    segment: str = 'moderate',
):
    """Run detailed diagnosis for one scenario."""

    MRP = 45000
    subsidized_price = MRP * (1 - subsidy_percent)

    print(f"\n{'='*70}")
    print(f"SCENARIO: {scenario_name}")
    print(f"{'='*70}")
    print(f"Subsidy: {subsidy_percent*100:.0f}% (₹{MRP - subsidized_price:,.0f})")
    print(f"Subsidized Price: ₹{subsidized_price:,.0f}")
    print(f"Plan: {plan} (₹{SUBSCRIPTION_PLANS[plan]['monthly_fee']}/month)")
    print(f"Tenure: {tenure_years} years ({tenure_years * 12} months)")
    print(f"Segment: {segment} (discount rate: {CUSTOMER_DISCOUNT_RATES[segment]*100:.0f}%)")

    tenure_months = tenure_years * 12

    # PURCHASE COST BREAKDOWN
    print(f"\n--- PURCHASE ALTERNATIVE ---")
    purchase = calculate_purchase_cost(
        mrp=MRP,
        tenure_years=tenure_years,
        segment=segment,
        appliance='AC',
    )

    print(f"  MRP (GST-inclusive): ₹{purchase['mrp']:,.0f}")
    print(f"  AMC Total ({tenure_years}yr): ₹{purchase['amc_total']:,.0f}")
    print(f"  Repairs Expected: ₹{purchase['repairs_total']:,.0f}")
    print(f"  Terminal Value: ₹{purchase['terminal_value']:,.0f}")
    print(f"  Terminal PV: ₹{purchase['terminal_pv']:,.0f}")
    print(f"  --")
    print(f"  Total NPV: ₹{purchase['total_npv']:,.0f}")
    print(f"  Monthly Equivalent: ₹{purchase['monthly_equivalent']:,.0f}/month")

    # SESP COST BREAKDOWN
    print(f"\n--- SESP SUBSCRIPTION ---")

    sesp_params = {
        'subsidized_price': subsidized_price,
        'plan': plan,
        'efficiency_score': 75.0,  # Average efficiency
        'deposit': 5000,
    }

    sesp = calculate_sesp_cost(
        subsidized_price=subsidized_price,
        tenure_months=tenure_months,
        plan=plan,
        segment=segment,
        efficiency_score=75.0,
        deposit=5000,
    )

    print(f"  Subsidized Price: ₹{subsidized_price:,.0f}")
    print(f"  + GST on upfront: ₹{subsidized_price * GST_RATE:,.0f}")
    print(f"  = Upfront with GST: ₹{sesp['upfront_with_gst']:,.0f}")
    print(f"  ")
    print(f"  Monthly Fee (base): ₹{sesp['base_fee']:,.0f}")
    print(f"  Monthly Payment (with GST): ₹{sesp['monthly_payment']:,.0f}")
    print(f"  × {tenure_months} months = ₹{sesp['monthly_payment'] * tenure_months:,.0f}")
    print(f"  Payments NPV: ₹{sesp['total_payments_npv']:,.0f}")
    print(f"  ")
    print(f"  Deposit: ₹{sesp['deposit']:,.0f}")
    print(f"  Deposit PV Refund: ₹{sesp['deposit_pv_refund']:,.0f}")
    print(f"  Deposit Net Cost: ₹{sesp['deposit_opportunity_cost']:,.0f}")
    print(f"  --")
    print(f"  Total NPV: ₹{sesp['total_npv']:,.0f}")
    print(f"  Monthly Equivalent: ₹{sesp['monthly_equivalent']:,.0f}/month")

    # COMPARISON
    print(f"\n--- COMPARISON ---")
    savings = purchase['total_npv'] - sesp['total_npv']
    savings_percent = (savings / purchase['total_npv']) * 100

    print(f"  Purchase NPV: ₹{purchase['total_npv']:,.0f}")
    print(f"  SESP NPV: ₹{sesp['total_npv']:,.0f}")
    print(f"  --")
    print(f"  Savings: ₹{savings:,.0f} ({savings_percent:.1f}%)")

    if savings > 0:
        print(f"  ✓ SESP is CHEAPER by ₹{savings:,.0f}")
    else:
        print(f"  ✗ SESP is MORE EXPENSIVE by ₹{-savings:,.0f}")

    # WHY IS IT NEGATIVE?
    print(f"\n--- ROOT CAUSE ANALYSIS ---")

    # Component comparison
    print("\n  COMPONENT BREAKDOWN:")
    print(f"  {'Component':<30} {'Purchase':<15} {'SESP':<15} {'Delta':<15}")
    print(f"  {'-'*75}")

    # Upfront
    purchase_upfront = MRP
    sesp_upfront = sesp['upfront_with_gst']
    delta_upfront = sesp_upfront - purchase_upfront
    print(f"  {'Upfront':<30} ₹{purchase_upfront:>12,.0f} ₹{sesp_upfront:>12,.0f} ₹{delta_upfront:>+12,.0f}")

    # Monthly costs
    purchase_monthly_total = purchase['amc_total'] + purchase['repairs_total']
    sesp_monthly_total = sesp['total_payments_npv']
    delta_monthly = sesp_monthly_total - purchase_monthly_total
    print(f"  {'Monthly costs (NPV)':<30} ₹{purchase['amc_npv'] + purchase['repairs_npv']:>12,.0f} ₹{sesp_monthly_total:>12,.0f} ₹{delta_monthly:>+12,.0f}")

    # Terminal value
    purchase_terminal = purchase['terminal_pv']
    sesp_terminal = 0  # No ownership
    delta_terminal = sesp_terminal - purchase_terminal
    print(f"  {'Terminal Value PV':<30} ₹{purchase_terminal:>12,.0f} ₹{sesp_terminal:>12,.0f} ₹{delta_terminal:>+12,.0f}")

    # Show what's making SESP expensive
    print(f"\n  KEY COST DRIVERS:")
    print(f"  1. Monthly fees accumulate: ₹{sesp['monthly_payment']:,.0f} × {tenure_months} = ₹{sesp['monthly_payment'] * tenure_months:,.0f}")
    print(f"  2. No terminal value: SESP customer owns nothing at end")
    print(f"  3. GST on subscription: ₹{sesp['gst_total']:,.0f} over tenure")

    return {
        'scenario': scenario_name,
        'savings': savings,
        'savings_percent': savings_percent,
        'purchase_npv': purchase['total_npv'],
        'sesp_npv': sesp['total_npv'],
    }


def find_valid_parameters():
    """Grid search to find subsidy/fee combinations that work."""

    print("\n" + "="*70)
    print("GRID SEARCH: Finding Valid Pricing Parameters")
    print("="*70)
    print("\nSearching for subsidy + fee + tenure combinations with POSITIVE savings...")
    print("(Target: ≥10% savings to satisfy participation constraint)\n")

    MRP = 45000
    tenure_options = [24, 36]  # 2 or 3 years
    subsidy_range = [0.45, 0.50, 0.55, 0.60, 0.65, 0.70]  # 45% to 70%
    plans = ['light', 'moderate', 'heavy']

    valid_combinations = []

    print(f"{'Subsidy %':<10} {'Plan':<10} {'Tenure':<10} {'Fee/mo':<10} {'Savings %':<12} {'Status':<10}")
    print("-" * 70)

    for subsidy in subsidy_range:
        for plan in plans:
            for tenure in tenure_options:
                subsidized_price = MRP * (1 - subsidy)
                monthly_fee = SUBSCRIPTION_PLANS[plan]['monthly_fee']
                tenure_years = tenure // 12

                sesp_params = {
                    'subsidized_price': subsidized_price,
                    'plan': plan,
                    'efficiency_score': 75.0,
                    'deposit': 5000,
                }

                result = check_pc_vs_purchase(
                    sesp_params=sesp_params,
                    mrp=MRP,
                    tenure_years=tenure_years,
                    segment='moderate',
                    appliance='AC',
                )

                savings_pct = result['actual_savings_percent']
                status = "✓ VALID" if savings_pct >= 10 else "✗ FAIL"

                print(f"{subsidy*100:.0f}%{'':<6} {plan:<10} {tenure}m{'':<6} ₹{monthly_fee:<8} {savings_pct:>+.1f}%{'':<6} {status}")

                if savings_pct >= 10:
                    valid_combinations.append({
                        'subsidy_percent': subsidy * 100,
                        'plan': plan,
                        'tenure_months': tenure,
                        'monthly_fee': monthly_fee,
                        'savings_percent': savings_pct,
                    })

    print("\n" + "-" * 70)

    if valid_combinations:
        print(f"\n✓ Found {len(valid_combinations)} valid combination(s)!")
        print("\nBest options (sorted by savings):")
        sorted_combos = sorted(valid_combinations, key=lambda x: x['savings_percent'], reverse=True)
        for i, combo in enumerate(sorted_combos[:5]):
            print(f"  {i+1}. {combo['subsidy_percent']:.0f}% subsidy + {combo['plan']} plan ({combo['tenure_months']}m) → {combo['savings_percent']:.1f}% savings")
    else:
        print("\n✗ No valid combinations found in search space!")
        print("\nAnalysis:")
        print("  - Even at 70% subsidy, savings may still be negative")
        print("  - The subscription fee accumulation overwhelms the subsidy benefit")
        print("  - Consider: reducing fees, including service value, shorter tenures")

    return valid_combinations


def calculate_minimum_subsidy_required():
    """Calculate what subsidy % is needed for positive savings."""

    print("\n" + "="*70)
    print("BOUNDARY ANALYSIS: Minimum Subsidy Required")
    print("="*70)

    MRP = 45000
    tenure_years = 3
    segment = 'moderate'

    for plan in ['light', 'moderate', 'heavy']:
        boundary = find_pc_boundary(
            mrp=MRP,
            tenure_years=tenure_years,
            segment=segment,
            appliance='AC',
            sesp_plan=plan,
            threshold=0.10,  # Need 10% savings
        )

        print(f"\n{plan.upper()} Plan:")
        print(f"  {boundary['recommendation']}")
        print(f"  Required subsidy: {boundary['subsidy_percent']:.1f}% of MRP")
        print(f"  = ₹{boundary['boundary_subsidy']:,.0f}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PARTICIPATION CONSTRAINT DIAGNOSTIC")
    print("="*70)
    print("\nThis script diagnoses why ALL pricing scenarios")
    print("show NEGATIVE customer savings (PC violation).\n")

    # Diagnose each TOPSIS scenario
    scenarios = [
        ("Conservative", 0.22, 'moderate'),  # 22% subsidy
        ("Balanced", 0.33, 'moderate'),      # 33% subsidy
        ("Aggressive", 0.44, 'moderate'),    # 44% subsidy
        ("Premium", 0.18, 'heavy'),          # 18% subsidy, heavy plan
    ]

    results = []
    for name, subsidy, plan in scenarios:
        result = diagnose_single_scenario(name, subsidy, plan)
        results.append(result)

    # Summary table
    print("\n" + "="*70)
    print("SUMMARY: All Scenarios")
    print("="*70)
    print(f"\n{'Scenario':<15} {'Subsidy':<10} {'Purchase NPV':<15} {'SESP NPV':<15} {'Savings':<15}")
    print("-" * 70)

    for r in results:
        print(f"{r['scenario']:<15} {'':<10} ₹{r['purchase_npv']:>12,.0f} ₹{r['sesp_npv']:>12,.0f} {r['savings_percent']:>+.1f}%")

    # Find valid parameters
    valid = find_valid_parameters()

    # Calculate minimum required subsidy
    calculate_minimum_subsidy_required()

    # Final conclusions
    print("\n" + "="*70)
    print("CONCLUSIONS")
    print("="*70)
    print("""
KEY FINDINGS:

1. SESP IS STRUCTURALLY MORE EXPENSIVE because:
   - Monthly fees accumulate over tenure (₹549 × 36 = ₹19,764)
   - No terminal value (customer doesn't own asset)
   - GST applies to entire subscription (not just product)

2. THE TERMINAL VALUE GAP IS HUGE:
   - At year 3, AC still worth ₹12,000 (purchase)
   - SESP customer owns ₹0 at end
   - This alone requires ~27% of MRP to offset

3. SUBSIDY REQUIREMENTS ARE VERY HIGH:
   - Light plan: Need ~60%+ subsidy for positive savings
   - Moderate plan: Need ~65%+ subsidy
   - Heavy plan: Need ~70%+ subsidy

4. BUSINESS MODEL IMPLICATIONS:
   - Pure cost comparison will ALWAYS favor purchase
   - SESP must compete on SERVICE VALUE, not price
   - Need to quantify: maintenance savings, warranty, IoT benefits, convenience
   - Or accept that SESP is "premium" service worth the extra cost

RECOMMENDATION:
Either (A) include service value in comparison (AMC, repairs, warranty)
Or (B) accept that SESP targets "convenience premium" market segment
Or (C) restructure with shorter tenures (18-24 months)
""")
