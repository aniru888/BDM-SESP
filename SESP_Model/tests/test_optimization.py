"""
Tests for optimization module.

Tests pricing optimizer functions to ensure they:
1. Calculate utilities correctly
2. Check constraints properly
3. Optimization runs without error
"""

import pytest
import numpy as np


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_plans():
    """Standard tiered plans for testing."""
    return {
        'lite': {'fee': 449, 'hours': 100, 'overage_rate': 5.0, 'overage_cap': 150.0},
        'standard': {'fee': 599, 'hours': 200, 'overage_rate': 4.0, 'overage_cap': 200.0},
        'premium': {'fee': 799, 'hours': 350, 'overage_rate': 0.0, 'overage_cap': 0.0},
    }


@pytest.fixture
def sample_segment_mix():
    """Standard segment distribution."""
    return {
        'light': 0.30,
        'moderate': 0.50,
        'heavy': 0.20,
    }


# =============================================================================
# TEST IMPORTS
# =============================================================================

class TestOptimizationImports:
    """Test that optimization module imports correctly."""

    def test_import_optimization_module(self):
        """Can import optimization module."""
        from src import optimization
        assert hasattr(optimization, 'PricingOptimizer')

    def test_import_all_functions(self):
        """All functions are exported."""
        from src.optimization import (
            PricingOptimizer,
            optimize_tiered_pricing,
            calculate_customer_utility,
            calculate_company_margin,
            check_ic_constraint,
            check_pc_constraint,
        )
        assert callable(PricingOptimizer)
        assert callable(optimize_tiered_pricing)
        assert callable(calculate_customer_utility)


# =============================================================================
# TEST UTILITY CALCULATIONS
# =============================================================================

class TestCustomerUtility:
    """Test customer utility calculation."""

    def test_utility_decreases_with_higher_fee(self):
        """Higher fee = lower utility."""
        from src.optimization import calculate_customer_utility

        utility_low = calculate_customer_utility('moderate', 500, 200)
        utility_high = calculate_customer_utility('moderate', 700, 200)

        assert utility_low > utility_high

    def test_utility_increases_with_more_hours(self):
        """More included hours = higher utility (less overage)."""
        from src.optimization import calculate_customer_utility

        utility_few = calculate_customer_utility('moderate', 599, 150)
        utility_many = calculate_customer_utility('moderate', 599, 250)

        assert utility_many > utility_few

    def test_light_user_prefers_lower_fee(self):
        """Light users should prefer Lite plan (lowest fee, enough hours)."""
        from src.optimization import calculate_customer_utility

        # Light user has ~80 hours expected
        utility_lite = calculate_customer_utility('light', 449, 100)
        utility_standard = calculate_customer_utility('light', 599, 200)

        # Lite should be better (lower cost, hours sufficient)
        assert utility_lite > utility_standard

    def test_heavy_user_utility_calculation(self):
        """Heavy users should have negative utility (cost)."""
        from src.optimization import calculate_customer_utility

        utility = calculate_customer_utility('heavy', 799, 350)

        # Utility is negative cost
        assert utility < 0


class TestCompanyMargin:
    """Test company margin calculation."""

    def test_margin_is_calculated(self, sample_plans, sample_segment_mix):
        """Margin calculation returns a number."""
        from src.optimization import calculate_company_margin

        margin = calculate_company_margin(sample_plans, sample_segment_mix)

        assert isinstance(margin, (int, float))

    def test_higher_fees_increase_margin(self, sample_segment_mix):
        """Higher subscription fees increase margin."""
        from src.optimization import calculate_company_margin

        low_fee_plans = {
            'lite': {'fee': 349, 'hours': 100, 'overage_rate': 5.0, 'overage_cap': 150.0},
            'standard': {'fee': 499, 'hours': 200, 'overage_rate': 4.0, 'overage_cap': 200.0},
            'premium': {'fee': 699, 'hours': 350, 'overage_rate': 0.0, 'overage_cap': 0.0},
        }

        high_fee_plans = {
            'lite': {'fee': 549, 'hours': 100, 'overage_rate': 5.0, 'overage_cap': 150.0},
            'standard': {'fee': 699, 'hours': 200, 'overage_rate': 4.0, 'overage_cap': 200.0},
            'premium': {'fee': 899, 'hours': 350, 'overage_rate': 0.0, 'overage_cap': 0.0},
        }

        margin_low = calculate_company_margin(low_fee_plans, sample_segment_mix)
        margin_high = calculate_company_margin(high_fee_plans, sample_segment_mix)

        assert margin_high > margin_low


# =============================================================================
# TEST CONSTRAINTS
# =============================================================================

class TestICConstraint:
    """Test Incentive Compatibility constraint checking."""

    def test_ic_returns_tuple(self, sample_plans):
        """IC check returns (bool, message) tuple."""
        from src.optimization import check_ic_constraint

        result = check_ic_constraint(sample_plans)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_ic_detects_violations(self):
        """IC check detects when wrong plan is preferred."""
        from src.optimization import check_ic_constraint

        # Intentionally bad pricing: Lite is too expensive
        bad_plans = {
            'lite': {'fee': 800, 'hours': 100, 'overage_rate': 5.0, 'overage_cap': 150.0},
            'standard': {'fee': 500, 'hours': 200, 'overage_rate': 4.0, 'overage_cap': 200.0},
            'premium': {'fee': 600, 'hours': 350, 'overage_rate': 0.0, 'overage_cap': 0.0},
        }

        is_satisfied, msg = check_ic_constraint(bad_plans)

        # Light users would prefer Standard over Lite
        assert is_satisfied is False
        assert 'light' in msg.lower() or 'standard' in msg.lower()


class TestPCConstraint:
    """Test Participation Constraint checking."""

    def test_pc_returns_tuple(self, sample_plans, sample_segment_mix):
        """PC check returns (bool, savings_percent) tuple."""
        from src.optimization import check_pc_constraint

        result = check_pc_constraint(sample_plans, sample_segment_mix)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], float)

    def test_pc_savings_reasonable_range(self, sample_plans, sample_segment_mix):
        """PC savings should be in realistic range (0% to 50%)."""
        from src.optimization import check_pc_constraint

        _, savings = check_pc_constraint(sample_plans, sample_segment_mix)

        assert 0 <= savings <= 0.50, f"Savings {savings:.1%} outside expected range"


# =============================================================================
# TEST OPTIMIZER
# =============================================================================

class TestPricingOptimizer:
    """Test PricingOptimizer class."""

    def test_optimizer_initializes(self):
        """Optimizer initializes without error."""
        from src.optimization import PricingOptimizer

        optimizer = PricingOptimizer()

        assert optimizer is not None
        assert hasattr(optimizer, 'optimize')

    def test_optimizer_runs(self):
        """Optimizer runs without error."""
        from src.optimization import PricingOptimizer

        optimizer = PricingOptimizer()
        result = optimizer.optimize()

        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'optimal_plans')
        assert hasattr(result, 'margin_per_customer')

    def test_optimizer_returns_valid_plans(self):
        """Optimizer returns plans with valid structure."""
        from src.optimization import PricingOptimizer

        optimizer = PricingOptimizer()
        result = optimizer.optimize()

        assert 'lite' in result.optimal_plans
        assert 'standard' in result.optimal_plans
        assert 'premium' in result.optimal_plans

        for plan_name, plan in result.optimal_plans.items():
            assert 'fee' in plan
            assert 'hours' in plan
            assert plan['fee'] >= 300  # Minimum reasonable fee
            assert plan['hours'] >= 50  # Minimum hours

    def test_optimizer_fees_monotonic(self):
        """Optimizer returns monotonically increasing fees."""
        from src.optimization import PricingOptimizer

        optimizer = PricingOptimizer()
        result = optimizer.optimize()

        lite_fee = result.optimal_plans['lite']['fee']
        std_fee = result.optimal_plans['standard']['fee']
        prem_fee = result.optimal_plans['premium']['fee']

        assert lite_fee <= std_fee, f"Lite ({lite_fee}) should be <= Standard ({std_fee})"
        assert std_fee <= prem_fee, f"Standard ({std_fee}) should be <= Premium ({prem_fee})"

    def test_optimizer_hours_monotonic(self):
        """Optimizer returns monotonically increasing hours."""
        from src.optimization import PricingOptimizer

        optimizer = PricingOptimizer()
        result = optimizer.optimize()

        lite_hrs = result.optimal_plans['lite']['hours']
        std_hrs = result.optimal_plans['standard']['hours']
        prem_hrs = result.optimal_plans['premium']['hours']

        assert lite_hrs <= std_hrs, f"Lite ({lite_hrs}) should be <= Standard ({std_hrs})"
        assert std_hrs <= prem_hrs, f"Standard ({std_hrs}) should be <= Premium ({prem_hrs})"


class TestCompareWithHeuristic:
    """Test comparison with heuristic pricing."""

    def test_comparison_returns_dict(self):
        """Comparison returns dict with expected keys."""
        from src.optimization import PricingOptimizer

        optimizer = PricingOptimizer()
        comparison = optimizer.compare_with_heuristic()

        assert 'heuristic' in comparison
        assert 'optimized' in comparison
        assert 'improvement' in comparison

    def test_comparison_heuristic_has_values(self):
        """Heuristic section has expected values."""
        from src.optimization import PricingOptimizer

        optimizer = PricingOptimizer()
        comparison = optimizer.compare_with_heuristic()

        heuristic = comparison['heuristic']
        assert 'plans' in heuristic
        assert 'margin' in heuristic
        assert 'ic_satisfied' in heuristic
        assert 'pc_satisfied' in heuristic


# =============================================================================
# TEST CONVENIENCE FUNCTION
# =============================================================================

class TestOptimizeTieredPricing:
    """Test convenience function."""

    def test_convenience_function_works(self):
        """optimize_tiered_pricing runs without error."""
        from src.optimization import optimize_tiered_pricing

        result = optimize_tiered_pricing()

        assert result is not None
        assert hasattr(result, 'optimal_plans')

    def test_accepts_custom_params(self):
        """Can pass custom cost parameters."""
        from src.optimization import optimize_tiered_pricing

        custom_params = {
            'mrp': 40000,  # Lower MRP
            'subsidy_percent': 0.45,
            'manufacturing_cost': 28000,
            'iot_cost': 1500,
            'installation_cost': 2500,
            'cac': 2000,
            'warranty_reserve': 2000,
            'bank_cac_subsidy': 2000,
            'monthly_recurring_cost': 192,
            'tenure_months': 60,
        }

        result = optimize_tiered_pricing(cost_params=custom_params)

        assert result is not None
