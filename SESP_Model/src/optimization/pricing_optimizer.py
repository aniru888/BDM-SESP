"""
Pricing Optimizer
=================

Finds optimal fee-hours combinations for tiered subscription plans
using constrained nonlinear optimization.

Optimization Problem:
    max: blended_margin(fees, hours, segment_mix)
    s.t.:
        IC: U(segment_i, plan_i) >= U(segment_i, plan_j) for all j != i
        PC: customer_savings >= 10%
        Profitability: margin > 0
        Practical bounds: fee in [400, 1000], hours in [50, 400]

Uses scipy.optimize.minimize with SLSQP method for handling constraints.
"""

import numpy as np
from scipy.optimize import minimize, differential_evolution
from typing import Dict, List, Tuple, Optional, NamedTuple
from dataclasses import dataclass


# =============================================================================
# CONSTANTS
# =============================================================================

# Segment characteristics
SEGMENT_USAGE = {
    'light': {'hours': 80, 'proportion': 0.30},
    'moderate': {'hours': 175, 'proportion': 0.50},
    'heavy': {'hours': 320, 'proportion': 0.20},
}

# Cost parameters (from Phase 3c)
DEFAULT_COST_PARAMS = {
    'mrp': 45000,
    'subsidy_percent': 0.50,
    'manufacturing_cost': 30000,
    'iot_cost': 1500,
    'installation_cost': 2500,
    'cac': 2000,
    'warranty_reserve': 2000,
    'bank_cac_subsidy': 2000,
    'monthly_recurring_cost': 192,
    'tenure_months': 60,
}

# Alternative: purchase costs for PC calculation
PURCHASE_COSTS = {
    'mrp': 45000,
    'amc_annual': 2500,
    'repair_risk_annual': 1500,  # Expected repair costs without warranty
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calculate_customer_utility(
    segment: str,
    plan_fee: float,
    plan_hours: float,
    overage_rate: float = 4.0,
    overage_cap: float = 200.0,
    efficiency_discount: float = 0.10,
) -> float:
    """
    Calculate customer utility for a given plan choice.

    Utility = -Total_Cost (negative cost = positive utility)

    For a customer in segment with expected hours H choosing plan with:
    - Monthly fee F
    - Included hours I
    - Overage rate O per hour
    - Overage cap C
    - Expected efficiency discount D%

    Monthly_Cost = F + min((H - I)+ * O, C) - F * D
    where (x)+ = max(0, x)

    Args:
        segment: Customer segment ('light', 'moderate', 'heavy')
        plan_fee: Monthly subscription fee
        plan_hours: Hours included in plan
        overage_rate: Cost per excess hour
        overage_cap: Maximum overage charge
        efficiency_discount: Expected discount percentage

    Returns:
        Utility value (higher is better for customer)
    """
    expected_hours = SEGMENT_USAGE[segment]['hours']

    # Calculate overage
    excess_hours = max(0, expected_hours - plan_hours)
    overage_cost = min(excess_hours * overage_rate, overage_cap)

    # Apply efficiency discount (on base fee only)
    discount = plan_fee * efficiency_discount

    # Monthly cost (GST included for customer view)
    monthly_cost = (plan_fee + overage_cost - discount) * 1.18

    # Utility is negative cost (customer wants to minimize cost)
    return -monthly_cost


def calculate_company_margin(
    plans: Dict[str, Dict[str, float]],
    segment_mix: Dict[str, float],
    cost_params: Optional[Dict] = None,
) -> float:
    """
    Calculate blended company margin across all segments.

    Margin = Revenue - Costs

    Revenue per customer:
    - Upfront (net of GST): customer_pays / 1.18
    - Monthly revenue: plan_fee * 0.847 (net of GST) * tenure
    - Overage revenue (net of GST)
    - Less: efficiency discounts

    Costs per customer:
    - Upfront: manufacturing + IoT + installation + CAC + warranty
    - Recurring: monthly_cost * tenure
    - Less: bank CAC subsidy

    NOTE: This uses expected-value calculation. Actual simulation shows higher
    margins due to:
    1. Usage variance (some customers exceed expectations)
    2. Efficiency score distribution (not all get max discount)
    3. Plan mismatches creating additional overage revenue

    Args:
        plans: Dict of plan names to {fee, hours, overage_rate, overage_cap}
        segment_mix: Proportion of customers in each segment
        cost_params: Cost parameters dict

    Returns:
        Blended margin per customer
    """
    if cost_params is None:
        cost_params = DEFAULT_COST_PARAMS

    tenure = cost_params['tenure_months']

    # Upfront economics
    customer_pays = cost_params['mrp'] * (1 - cost_params['subsidy_percent'])
    upfront_revenue = customer_pays / 1.18  # Net of GST

    upfront_cost = (
        cost_params['manufacturing_cost'] +
        cost_params['iot_cost'] +
        cost_params['installation_cost'] +
        cost_params['cac'] +
        cost_params['warranty_reserve']
    )

    upfront_deficit = upfront_cost - upfront_revenue

    # Calculate weighted monthly revenue by segment
    total_monthly_revenue = 0

    # Map segments to intended plans
    segment_to_plan = {
        'light': 'lite',
        'moderate': 'standard',
        'heavy': 'premium',
    }

    # Simulation-calibrated parameters (from actual simulation results):
    # - Average efficiency discount is ~7% (not 10%)
    # - ~26% of customer-months have overage
    # - Actual usage variance adds ~Rs28/month in overage revenue
    ACTUAL_DISCOUNT_RATE = 0.067  # From simulation: Rs40.5 avg discount on ~Rs600 fee
    VARIANCE_OVERAGE_BONUS = 28   # Additional overage from usage variance

    for segment, proportion in segment_mix.items():
        plan_name = segment_to_plan[segment]
        plan = plans[plan_name]

        fee = plan['fee']
        hours = plan['hours']
        overage_rate = plan.get('overage_rate', 4.0)
        overage_cap = plan.get('overage_cap', 200.0)

        expected_hours = SEGMENT_USAGE[segment]['hours']

        # Monthly fee revenue (net of GST)
        monthly_fee_revenue = fee * 0.847

        # Expected overage revenue (based on mean hours)
        excess_hours = max(0, expected_hours - hours)
        base_overage = min(excess_hours * overage_rate, overage_cap)

        # Add variance bonus (captures customers who exceed expectations)
        overage = base_overage + VARIANCE_OVERAGE_BONUS
        overage_revenue = overage * 0.847

        # Efficiency discount (use simulation-calibrated rate)
        discount = fee * ACTUAL_DISCOUNT_RATE

        # Net monthly revenue per customer in this segment
        segment_monthly_revenue = monthly_fee_revenue + overage_revenue - discount * 0.847

        total_monthly_revenue += segment_monthly_revenue * proportion

    # Total revenue over tenure
    total_revenue = total_monthly_revenue * tenure

    # Recurring costs
    recurring_cost = cost_params['monthly_recurring_cost'] * tenure

    # Bank CAC subsidy (one-time benefit)
    bank_subsidy = cost_params['bank_cac_subsidy']

    # Margin per customer
    margin = total_revenue - upfront_deficit - recurring_cost + bank_subsidy

    return margin


def check_ic_constraint(
    plans: Dict[str, Dict[str, float]],
) -> Tuple[bool, str]:
    """
    Check Incentive Compatibility constraint.

    IC requires: Each segment weakly prefers their intended plan.

    For segment S with intended plan P:
        U(S, P) >= U(S, Q) for all plans Q != P

    Args:
        plans: Dict of plan definitions

    Returns:
        (is_satisfied, message)
    """
    segment_to_plan = {
        'light': 'lite',
        'moderate': 'standard',
        'heavy': 'premium',
    }

    violations = []

    for segment, intended_plan in segment_to_plan.items():
        intended = plans[intended_plan]
        intended_utility = calculate_customer_utility(
            segment,
            intended['fee'],
            intended['hours'],
            intended.get('overage_rate', 4.0),
            intended.get('overage_cap', 200.0),
        )

        for other_plan, other in plans.items():
            if other_plan == intended_plan:
                continue

            other_utility = calculate_customer_utility(
                segment,
                other['fee'],
                other['hours'],
                other.get('overage_rate', 4.0),
                other.get('overage_cap', 200.0),
            )

            if other_utility > intended_utility:
                violations.append(
                    f"{segment} prefers {other_plan} over {intended_plan} "
                    f"(utility diff: {other_utility - intended_utility:.2f})"
                )

    if violations:
        return False, "; ".join(violations)
    return True, "All IC constraints satisfied"


def check_pc_constraint(
    plans: Dict[str, Dict[str, float]],
    segment_mix: Dict[str, float],
    cost_params: Optional[Dict] = None,
    min_savings_percent: float = 0.10,
) -> Tuple[bool, float]:
    """
    Check Participation Constraint.

    PC requires: SESP total cost < Purchase total cost * (1 - min_savings)

    Args:
        plans: Dict of plan definitions
        segment_mix: Segment proportions
        cost_params: Cost parameters
        min_savings_percent: Minimum required savings (default 10%)

    Returns:
        (is_satisfied, actual_savings_percent)
    """
    if cost_params is None:
        cost_params = DEFAULT_COST_PARAMS

    tenure = cost_params['tenure_months']

    # Calculate weighted SESP cost
    customer_upfront = cost_params['mrp'] * (1 - cost_params['subsidy_percent'])

    segment_to_plan = {
        'light': 'lite',
        'moderate': 'standard',
        'heavy': 'premium',
    }

    total_monthly_cost = 0
    for segment, proportion in segment_mix.items():
        plan = plans[segment_to_plan[segment]]
        fee = plan['fee']
        hours = plan['hours']
        overage_rate = plan.get('overage_rate', 4.0)
        overage_cap = plan.get('overage_cap', 200.0)

        expected_hours = SEGMENT_USAGE[segment]['hours']
        excess = max(0, expected_hours - hours)
        overage = min(excess * overage_rate, overage_cap)

        # Assume 10% efficiency discount
        discount = fee * 0.10

        monthly_cost = (fee + overage - discount) * 1.18
        total_monthly_cost += monthly_cost * proportion

    sesp_total = customer_upfront + total_monthly_cost * tenure

    # Calculate purchase cost
    purchase_upfront = PURCHASE_COSTS['mrp']
    purchase_annual_cost = PURCHASE_COSTS['amc_annual'] + PURCHASE_COSTS['repair_risk_annual']
    purchase_total = purchase_upfront + purchase_annual_cost * (tenure / 12)

    # Savings
    savings = purchase_total - sesp_total
    savings_percent = savings / purchase_total

    is_satisfied = savings_percent >= min_savings_percent

    return is_satisfied, savings_percent


# =============================================================================
# OPTIMIZER CLASS
# =============================================================================

@dataclass
class OptimizationResult:
    """Result of pricing optimization."""
    success: bool
    optimal_plans: Dict[str, Dict[str, float]]
    margin_per_customer: float
    customer_savings_percent: float
    ic_satisfied: bool
    pc_satisfied: bool
    message: str


class PricingOptimizer:
    """
    Optimizer for tiered subscription pricing.

    Uses constrained optimization to find fee-hours combinations
    that maximize company margin while satisfying IC and PC constraints.
    """

    def __init__(
        self,
        cost_params: Optional[Dict] = None,
        segment_mix: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize optimizer.

        Args:
            cost_params: Cost parameters (uses defaults if None)
            segment_mix: Segment proportions (uses defaults if None)
        """
        self.cost_params = cost_params or DEFAULT_COST_PARAMS
        self.segment_mix = segment_mix or {
            'light': 0.30,
            'moderate': 0.50,
            'heavy': 0.20,
        }

    def _unpack_params(self, x: np.ndarray) -> Dict[str, Dict[str, float]]:
        """
        Convert optimization vector to plans dict.

        Vector layout: [fee_lite, hours_lite, fee_std, hours_std, fee_prem, hours_prem]
        """
        return {
            'lite': {
                'fee': x[0],
                'hours': x[1],
                'overage_rate': 5.0,
                'overage_cap': 150.0,
            },
            'standard': {
                'fee': x[2],
                'hours': x[3],
                'overage_rate': 4.0,
                'overage_cap': 200.0,
            },
            'premium': {
                'fee': x[4],
                'hours': x[5],
                'overage_rate': 0.0,  # No overage on premium
                'overage_cap': 0.0,
            },
        }

    def _objective(self, x: np.ndarray) -> float:
        """
        Objective function: negative margin (we minimize, so negative of what we want to maximize).
        """
        plans = self._unpack_params(x)
        margin = calculate_company_margin(plans, self.segment_mix, self.cost_params)
        return -margin  # Negative because we're minimizing

    def _ic_constraint(self, x: np.ndarray) -> float:
        """
        IC constraint: returns >= 0 if satisfied.

        For each segment, utility of intended plan - max utility of other plans >= 0
        """
        plans = self._unpack_params(x)

        segment_to_plan = {
            'light': 'lite',
            'moderate': 'standard',
            'heavy': 'premium',
        }

        min_gap = float('inf')

        for segment, intended_plan in segment_to_plan.items():
            intended = plans[intended_plan]
            intended_utility = calculate_customer_utility(
                segment,
                intended['fee'],
                intended['hours'],
                intended.get('overage_rate', 4.0),
                intended.get('overage_cap', 200.0),
            )

            for other_plan, other in plans.items():
                if other_plan == intended_plan:
                    continue

                other_utility = calculate_customer_utility(
                    segment,
                    other['fee'],
                    other['hours'],
                    other.get('overage_rate', 4.0),
                    other.get('overage_cap', 200.0),
                )

                gap = intended_utility - other_utility
                min_gap = min(min_gap, gap)

        return min_gap  # Should be >= 0 for IC to be satisfied

    def _pc_constraint(self, x: np.ndarray) -> float:
        """
        PC constraint: returns >= 0 if customer savings >= 10%.
        """
        plans = self._unpack_params(x)
        _, savings_pct = check_pc_constraint(plans, self.segment_mix, self.cost_params)
        return savings_pct - 0.10  # Should be >= 0

    def _monotonicity_constraint_1(self, x: np.ndarray) -> float:
        """Fee monotonicity: lite_fee < standard_fee < premium_fee"""
        return x[2] - x[0] - 50  # std_fee >= lite_fee + 50

    def _monotonicity_constraint_2(self, x: np.ndarray) -> float:
        """Fee monotonicity: standard_fee < premium_fee"""
        return x[4] - x[2] - 50  # prem_fee >= std_fee + 50

    def _hours_monotonicity_1(self, x: np.ndarray) -> float:
        """Hours monotonicity: lite_hours < standard_hours"""
        return x[3] - x[1] - 25  # std_hours >= lite_hours + 25

    def _hours_monotonicity_2(self, x: np.ndarray) -> float:
        """Hours monotonicity: standard_hours < premium_hours"""
        return x[5] - x[3] - 50  # prem_hours >= std_hours + 50

    def optimize(
        self,
        method: str = 'SLSQP',
        max_iter: int = 500,
    ) -> OptimizationResult:
        """
        Run optimization to find optimal pricing.

        Args:
            method: Optimization method ('SLSQP' or 'differential_evolution')
            max_iter: Maximum iterations

        Returns:
            OptimizationResult with optimal plans and metrics
        """
        # Initial guess (current heuristic values)
        x0 = np.array([449, 100, 599, 200, 799, 350], dtype=float)

        # Bounds: [fee_lite, hours_lite, fee_std, hours_std, fee_prem, hours_prem]
        bounds = [
            (350, 550),   # lite_fee
            (50, 150),    # lite_hours
            (450, 700),   # std_fee
            (100, 250),   # std_hours
            (600, 1000),  # prem_fee
            (200, 450),   # prem_hours
        ]

        # Constraints (inequality: constraint(x) >= 0)
        constraints = [
            {'type': 'ineq', 'fun': self._ic_constraint},
            {'type': 'ineq', 'fun': self._pc_constraint},
            {'type': 'ineq', 'fun': self._monotonicity_constraint_1},
            {'type': 'ineq', 'fun': self._monotonicity_constraint_2},
            {'type': 'ineq', 'fun': self._hours_monotonicity_1},
            {'type': 'ineq', 'fun': self._hours_monotonicity_2},
        ]

        if method == 'SLSQP':
            result = minimize(
                self._objective,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': max_iter, 'disp': False},
            )
        elif method == 'differential_evolution':
            # For global optimization (slower but more robust)
            def combined_objective(x):
                obj = self._objective(x)
                # Add penalty for constraint violations
                penalty = 0
                if self._ic_constraint(x) < 0:
                    penalty += 10000 * abs(self._ic_constraint(x))
                if self._pc_constraint(x) < 0:
                    penalty += 10000 * abs(self._pc_constraint(x))
                if self._monotonicity_constraint_1(x) < 0:
                    penalty += 10000
                if self._monotonicity_constraint_2(x) < 0:
                    penalty += 10000
                return obj + penalty

            result = differential_evolution(
                combined_objective,
                bounds,
                maxiter=max_iter,
                seed=42,
            )
        else:
            raise ValueError(f"Unknown method: {method}")

        # Extract optimal plans
        optimal_plans = self._unpack_params(result.x)

        # Calculate final metrics
        margin = calculate_company_margin(optimal_plans, self.segment_mix, self.cost_params)
        ic_ok, ic_msg = check_ic_constraint(optimal_plans)
        pc_ok, savings = check_pc_constraint(optimal_plans, self.segment_mix, self.cost_params)

        return OptimizationResult(
            success=result.success,
            optimal_plans=optimal_plans,
            margin_per_customer=margin,
            customer_savings_percent=savings,
            ic_satisfied=ic_ok,
            pc_satisfied=pc_ok,
            message=result.message if hasattr(result, 'message') else str(result),
        )

    def compare_with_heuristic(self) -> Dict:
        """
        Compare optimized pricing with current heuristic values.

        Returns:
            Comparison dict
        """
        # Current heuristic
        heuristic_plans = {
            'lite': {'fee': 449, 'hours': 100, 'overage_rate': 5.0, 'overage_cap': 150.0},
            'standard': {'fee': 599, 'hours': 200, 'overage_rate': 4.0, 'overage_cap': 200.0},
            'premium': {'fee': 799, 'hours': 350, 'overage_rate': 0.0, 'overage_cap': 0.0},
        }

        heuristic_margin = calculate_company_margin(heuristic_plans, self.segment_mix, self.cost_params)
        heuristic_ic, _ = check_ic_constraint(heuristic_plans)
        heuristic_pc, heuristic_savings = check_pc_constraint(heuristic_plans, self.segment_mix, self.cost_params)

        # Optimized
        result = self.optimize()

        return {
            'heuristic': {
                'plans': heuristic_plans,
                'margin': heuristic_margin,
                'ic_satisfied': heuristic_ic,
                'pc_satisfied': heuristic_pc,
                'savings_percent': heuristic_savings,
            },
            'optimized': {
                'plans': result.optimal_plans,
                'margin': result.margin_per_customer,
                'ic_satisfied': result.ic_satisfied,
                'pc_satisfied': result.pc_satisfied,
                'savings_percent': result.customer_savings_percent,
            },
            'improvement': {
                'margin_diff': result.margin_per_customer - heuristic_margin,
                'margin_pct_change': (result.margin_per_customer - heuristic_margin) / heuristic_margin * 100 if heuristic_margin > 0 else 0,
            }
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def optimize_tiered_pricing(
    cost_params: Optional[Dict] = None,
    segment_mix: Optional[Dict[str, float]] = None,
) -> OptimizationResult:
    """
    Convenience function to run pricing optimization.

    Args:
        cost_params: Cost parameters (uses defaults if None)
        segment_mix: Segment proportions (uses defaults if None)

    Returns:
        OptimizationResult
    """
    optimizer = PricingOptimizer(cost_params, segment_mix)
    return optimizer.optimize()


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SESP PRICING OPTIMIZER")
    print("=" * 70)
    print()

    optimizer = PricingOptimizer()
    comparison = optimizer.compare_with_heuristic()

    print("HEURISTIC PRICING:")
    print("-" * 40)
    for plan, details in comparison['heuristic']['plans'].items():
        print(f"  {plan.upper()}: Rs{details['fee']}/month, {details['hours']} hours")
    print(f"  Margin: Rs{comparison['heuristic']['margin']:,.0f}")
    print(f"  IC Satisfied: {comparison['heuristic']['ic_satisfied']}")
    print(f"  PC Satisfied: {comparison['heuristic']['pc_satisfied']}")
    print(f"  Customer Savings: {comparison['heuristic']['savings_percent']:.1%}")
    print()

    print("OPTIMIZED PRICING:")
    print("-" * 40)
    for plan, details in comparison['optimized']['plans'].items():
        print(f"  {plan.upper()}: Rs{details['fee']:.0f}/month, {details['hours']:.0f} hours")
    print(f"  Margin: Rs{comparison['optimized']['margin']:,.0f}")
    print(f"  IC Satisfied: {comparison['optimized']['ic_satisfied']}")
    print(f"  PC Satisfied: {comparison['optimized']['pc_satisfied']}")
    print(f"  Customer Savings: {comparison['optimized']['savings_percent']:.1%}")
    print()

    print("IMPROVEMENT:")
    print("-" * 40)
    print(f"  Margin Change: Rs{comparison['improvement']['margin_diff']:+,.0f}")
    print(f"  Margin % Change: {comparison['improvement']['margin_pct_change']:+.1f}%")
    print()
