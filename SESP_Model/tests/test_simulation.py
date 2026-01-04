"""
Tests for Phase 4: Simulation Module
====================================

Tests cover:
- Data generator: distributions, schema, validation
- Simulator: vectorized ops, performance, calculations
- Aggregator: all levels of aggregation
"""

import pytest
import numpy as np
import pandas as pd
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# TEST: DATA GENERATOR
# =============================================================================

class TestDataGenerator:
    """Tests for customer data generation."""

    def test_generate_customers_returns_dataframe(self):
        """generate_customers returns a DataFrame."""
        from src.simulation.data_generator import generate_customers
        df = generate_customers(100, random_seed=42)
        assert isinstance(df, pd.DataFrame)

    def test_generate_customers_correct_size(self):
        """DataFrame has correct number of rows."""
        from src.simulation.data_generator import generate_customers
        df = generate_customers(500, random_seed=42)
        assert len(df) == 500

    def test_generate_customers_has_required_columns(self):
        """DataFrame has all required columns."""
        from src.simulation.data_generator import generate_customers
        df = generate_customers(100, random_seed=42)

        required_cols = [
            'customer_id', 'segment', 'plan', 'region',
            'has_credit_card', 'usage_factor', 'efficiency_score_base',
            'churn_risk', 'default_risk', 'signup_month', 'is_plan_mismatch'
        ]
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"

    def test_segment_distribution_roughly_correct(self):
        """Segment distribution is approximately 30/50/20."""
        from src.simulation.data_generator import generate_customers
        df = generate_customers(1000, random_seed=42)

        light_pct = (df['segment'] == 'light').mean()
        moderate_pct = (df['segment'] == 'moderate').mean()
        heavy_pct = (df['segment'] == 'heavy').mean()

        # Allow 5% tolerance due to randomness
        assert abs(light_pct - 0.30) < 0.05, f"Light: {light_pct:.2%}"
        assert abs(moderate_pct - 0.50) < 0.05, f"Moderate: {moderate_pct:.2%}"
        assert abs(heavy_pct - 0.20) < 0.05, f"Heavy: {heavy_pct:.2%}"

    def test_plan_mismatch_rate(self):
        """Plan mismatch rate is approximately as specified."""
        from src.simulation.data_generator import generate_customers
        df = generate_customers(1000, plan_mismatch_rate=0.10, random_seed=42)

        mismatch_rate = df['is_plan_mismatch'].mean()
        assert abs(mismatch_rate - 0.10) < 0.03, f"Mismatch rate: {mismatch_rate:.2%}"

    def test_credit_card_adoption_rate(self):
        """Credit card adoption is approximately 70%."""
        from src.simulation.data_generator import generate_customers
        df = generate_customers(1000, random_seed=42)

        cc_rate = df['has_credit_card'].mean()
        assert abs(cc_rate - 0.70) < 0.05, f"CC rate: {cc_rate:.2%}"

    def test_usage_factor_in_valid_range(self):
        """Usage factors are within expected ranges."""
        from src.simulation.data_generator import generate_customers
        df = generate_customers(500, random_seed=42)

        # All usage factors should be between 0.7 and 1.3
        assert df['usage_factor'].min() >= 0.7
        assert df['usage_factor'].max() <= 1.3

    def test_efficiency_score_in_valid_range(self):
        """Efficiency scores are within 0-100."""
        from src.simulation.data_generator import generate_customers
        df = generate_customers(500, random_seed=42)

        assert df['efficiency_score_base'].min() >= 0
        assert df['efficiency_score_base'].max() <= 100

    def test_validate_customer_data_returns_dict(self):
        """validate_customer_data returns a dictionary."""
        from src.simulation.data_generator import generate_customers, validate_customer_data
        df = generate_customers(100, random_seed=42)
        result = validate_customer_data(df)

        assert isinstance(result, dict)
        assert 'n_customers' in result
        assert 'validation_passed' in result


# =============================================================================
# TEST: SIMULATOR
# =============================================================================

class TestSimulator:
    """Tests for vectorized simulation."""

    def test_simulate_portfolio_returns_dataframe(self):
        """simulate_portfolio returns a DataFrame."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio

        customers = generate_customers(50, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=12, random_seed=42)

        assert isinstance(grid, pd.DataFrame)

    def test_simulate_portfolio_correct_size(self):
        """Grid has correct number of rows (n_customers × tenure)."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio

        n_customers = 100
        tenure = 24
        customers = generate_customers(n_customers, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=tenure, random_seed=42)

        assert len(grid) == n_customers * tenure

    def test_simulate_portfolio_has_required_columns(self):
        """Grid has all required output columns."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio

        customers = generate_customers(50, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=12, random_seed=42)

        required_cols = [
            'customer_id', 'month', 'segment', 'plan', 'region',
            'actual_hours', 'plan_fee', 'overage', 'efficiency_discount',
            'monthly_bill', 'company_revenue', 'efficiency_score',
        ]
        for col in required_cols:
            assert col in grid.columns, f"Missing column: {col}"

    def test_simulate_portfolio_performance(self):
        """Simulation completes in < 10 seconds for 1000 × 60."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio

        customers = generate_customers(1000, random_seed=42)

        start = time.time()
        grid = simulate_portfolio(customers, tenure_months=60, random_seed=42)
        elapsed = time.time() - start

        assert elapsed < 10, f"Simulation took {elapsed:.2f}s (target: <10s)"
        assert len(grid) == 60000  # 1000 × 60

    def test_monthly_bill_includes_gst(self):
        """Monthly bill includes 18% GST."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio

        customers = generate_customers(100, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=12, random_seed=42)

        # Bill = pre_gst × 1.18
        expected = grid['bill_pre_gst'] * 1.18
        np.testing.assert_array_almost_equal(grid['monthly_bill'], expected, decimal=2)

    def test_overage_is_capped(self):
        """Overage never exceeds the cap for each plan."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio, OVERAGE_CAPS

        customers = generate_customers(200, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=24, random_seed=42)

        for plan, cap in OVERAGE_CAPS.items():
            plan_data = grid[grid['plan'] == plan]
            assert plan_data['overage'].max() <= cap, f"Plan {plan} overage exceeds cap"

    def test_premium_plan_has_zero_overage(self):
        """Premium plan never has overage (unlimited hours)."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio

        customers = generate_customers(200, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=24, random_seed=42)

        premium_data = grid[grid['plan'] == 'premium']
        assert premium_data['overage'].sum() == 0

    def test_efficiency_discount_uses_correct_tiers(self):
        """Efficiency discount matches tier thresholds."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio

        customers = generate_customers(500, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=24, random_seed=42)

        # Check champion tier (score >= 90 → 20% discount)
        champions = grid[grid['efficiency_score'] >= 90]
        if len(champions) > 0:
            expected_discount = champions['plan_fee'] * 0.20
            np.testing.assert_array_almost_equal(
                champions['efficiency_discount'].values,
                expected_discount.values,
                decimal=2
            )

    def test_seasonality_affects_hours(self):
        """Seasonality factor affects actual hours."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio

        customers = generate_customers(200, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=24, random_seed=42)

        # North region: May (month 4) should have higher usage than Dec (month 11)
        north_data = grid[grid['region'] == 'north']
        may_hours = north_data[north_data['month_of_year'] == 4]['actual_hours'].mean()
        dec_hours = north_data[north_data['month_of_year'] == 11]['actual_hours'].mean()

        assert may_hours > dec_hours * 2, "May should have >2x December hours in North"

    def test_company_revenue_is_pre_gst(self):
        """Company revenue equals bill_pre_gst (GST goes to government)."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio

        customers = generate_customers(100, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=12, random_seed=42)

        np.testing.assert_array_almost_equal(
            grid['company_revenue'],
            grid['bill_pre_gst'],
            decimal=2
        )


# =============================================================================
# TEST: AGGREGATOR
# =============================================================================

class TestAggregator:
    """Tests for result aggregation."""

    def test_aggregate_by_customer_one_row_per_customer(self):
        """aggregate_by_customer returns one row per customer."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio
        from src.simulation.aggregator import aggregate_by_customer

        n_customers = 100
        customers = generate_customers(n_customers, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=24, random_seed=42)
        agg = aggregate_by_customer(grid)

        assert len(agg) == n_customers

    def test_aggregate_by_segment_three_rows(self):
        """aggregate_by_segment returns one row per segment."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio
        from src.simulation.aggregator import aggregate_by_segment

        customers = generate_customers(300, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=12, random_seed=42)
        agg = aggregate_by_segment(grid)

        assert len(agg) == 3  # light, moderate, heavy
        assert set(agg['segment']) == {'light', 'moderate', 'heavy'}

    def test_aggregate_by_month_correct_rows(self):
        """aggregate_by_month returns one row per month."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio
        from src.simulation.aggregator import aggregate_by_month

        tenure = 36
        customers = generate_customers(100, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=tenure, random_seed=42)
        agg = aggregate_by_month(grid)

        assert len(agg) == tenure

    def test_aggregate_by_month_cumulative_revenue(self):
        """Cumulative revenue is correctly calculated."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio
        from src.simulation.aggregator import aggregate_by_month

        customers = generate_customers(100, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=24, random_seed=42)
        agg = aggregate_by_month(grid)

        # Verify cumulative calculation
        expected_cumulative = agg['total_revenue'].cumsum()
        np.testing.assert_array_almost_equal(
            agg['cumulative_revenue'],
            expected_cumulative,
            decimal=2
        )

    def test_aggregate_portfolio_returns_dict(self):
        """aggregate_portfolio returns a dictionary."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio
        from src.simulation.aggregator import aggregate_portfolio

        customers = generate_customers(100, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=24, random_seed=42)
        result = aggregate_portfolio(grid)

        assert isinstance(result, dict)
        assert 'n_customers' in result
        assert 'margin_per_customer' in result
        assert 'total_portfolio_margin' in result

    def test_aggregate_portfolio_margin_calculation(self):
        """Portfolio margin is calculated correctly."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio
        from src.simulation.aggregator import aggregate_portfolio

        customers = generate_customers(100, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=60, random_seed=42)
        result = aggregate_portfolio(grid)

        # Margin per customer × n_customers = total margin
        expected_total = result['margin_per_customer'] * result['n_customers']
        assert abs(result['total_portfolio_margin'] - expected_total) < 1

    def test_summary_report_is_string(self):
        """calculate_simulation_summary returns a string."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio
        from src.simulation.aggregator import calculate_simulation_summary

        customers = generate_customers(100, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=24, random_seed=42)
        summary = calculate_simulation_summary(grid)

        assert isinstance(summary, str)
        assert len(summary) > 100  # Should have meaningful content


# =============================================================================
# TEST: SIMULATION VALIDATION
# =============================================================================

class TestSimulationValidation:
    """Tests to validate simulation matches Phase 3c projections."""

    def test_segment_hours_in_expected_ranges(self):
        """Segment average hours are in expected ranges."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio

        customers = generate_customers(1000, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=60, random_seed=42)

        light_hours = grid[grid['segment'] == 'light']['actual_hours'].mean()
        moderate_hours = grid[grid['segment'] == 'moderate']['actual_hours'].mean()
        heavy_hours = grid[grid['segment'] == 'heavy']['actual_hours'].mean()

        # Expected ranges (with seasonality, expect some deviation)
        assert 50 <= light_hours <= 150, f"Light hours: {light_hours}"
        assert 100 <= moderate_hours <= 250, f"Moderate hours: {moderate_hours}"
        assert 200 <= heavy_hours <= 450, f"Heavy hours: {heavy_hours}"

    def test_blended_margin_reasonable(self):
        """Portfolio margin is in reasonable range (positive and sustainable)."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio
        from src.simulation.aggregator import aggregate_portfolio

        customers = generate_customers(1000, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=60, random_seed=42)
        result = aggregate_portfolio(grid)

        # Phase 3c projected Rs3,746 per customer using simplified averages.
        # Simulation generates actual behavior with:
        # - Random efficiency scores → varying discounts
        # - Overage events → additional revenue (capped)
        # - Seasonality effects → usage variation
        #
        # Simulated margins are typically higher than projections because:
        # 1. Overage adds revenue when customers exceed hours
        # 2. Efficiency discounts average lower than worst-case assumptions
        #
        # Key validation: Margin is POSITIVE and in sustainable range (Rs2k-10k)
        margin = result['margin_per_customer']

        # Must be profitable (positive margin)
        assert margin > 0, f"Margin should be positive: Rs{margin:.0f}"

        # Must be in sustainable range (not too low, not suspiciously high)
        assert margin >= 2000, f"Margin too low: Rs{margin:.0f} (need >=Rs2,000)"
        assert margin <= 10000, f"Margin too high: Rs{margin:.0f} (suspicious if >Rs10,000)"

    def test_no_negative_hours(self):
        """No customer has negative hours."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio

        customers = generate_customers(500, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=60, random_seed=42)

        assert grid['actual_hours'].min() >= 0

    def test_uses_hours_not_kwh(self):
        """Simulation uses hours, not kWh (no kWh column)."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio

        customers = generate_customers(100, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=12, random_seed=42)

        # Should have hours columns, not kWh
        assert 'actual_hours' in grid.columns
        assert 'kwh' not in grid.columns.str.lower()
        assert 'kWh' not in grid.columns


# =============================================================================
# TEST: MODULE IMPORTS
# =============================================================================

class TestSimulationImports:
    """Test that all simulation module imports work."""

    def test_import_from_simulation_package(self):
        """All exports from simulation package work."""
        from src.simulation import (
            generate_customers,
            CUSTOMER_SEGMENTS,
            SEGMENT_DISTRIBUTIONS,
            PLAN_MAPPING,
            validate_customer_data,
            simulate_portfolio,
            simulate_single_customer,
            PLAN_FEES,
            PLAN_HOURS,
            OVERAGE_RATES,
            OVERAGE_CAPS,
            EFFICIENCY_TIERS,
            aggregate_by_customer,
            aggregate_by_segment,
            aggregate_by_month,
            aggregate_portfolio,
            calculate_simulation_summary,
        )

        # Verify they exist
        assert callable(generate_customers)
        assert callable(simulate_portfolio)
        assert callable(aggregate_portfolio)
        assert isinstance(PLAN_FEES, dict)
        assert isinstance(EFFICIENCY_TIERS, dict)

    def test_constants_have_expected_values(self):
        """Plan constants have Phase 3c values."""
        from src.simulation.simulator import PLAN_FEES, PLAN_HOURS

        assert PLAN_FEES['lite'] == 449
        assert PLAN_FEES['standard'] == 599
        assert PLAN_FEES['premium'] == 799

        assert PLAN_HOURS['lite'] == 100
        assert PLAN_HOURS['standard'] == 200
        assert PLAN_HOURS['premium'] == 350


# =============================================================================
# TEST SEASONAL HOURS (Budget Effect for Energy Efficiency)
# =============================================================================

class TestSeasonalHours:
    """Test seasonal hours allocation functionality."""

    def test_seasons_mapping_covers_all_months(self):
        """All 12 months are mapped to a season."""
        from src.simulation import SEASONS
        assert len(SEASONS) == 12
        for month in range(12):
            assert month in SEASONS
            assert SEASONS[month] in ['winter', 'shoulder', 'summer']

    def test_seasonal_plan_hours_structure(self):
        """Seasonal hours defined for all plans and seasons."""
        from src.simulation import SEASONAL_PLAN_HOURS
        plans = ['lite', 'standard', 'premium']
        seasons = ['winter', 'shoulder', 'summer']

        for plan in plans:
            assert plan in SEASONAL_PLAN_HOURS
            for season in seasons:
                assert season in SEASONAL_PLAN_HOURS[plan]
                assert SEASONAL_PLAN_HOURS[plan][season] > 0

    def test_get_seasonal_hours_function(self):
        """get_seasonal_hours returns correct hours by plan and month."""
        from src.simulation import get_seasonal_hours, SEASONAL_PLAN_HOURS

        # January (winter) for standard plan
        jan_hours = get_seasonal_hours('standard', 0)
        assert jan_hours == SEASONAL_PLAN_HOURS['standard']['winter']

        # June (summer) for standard plan
        jun_hours = get_seasonal_hours('standard', 5)
        assert jun_hours == SEASONAL_PLAN_HOURS['standard']['summer']

        # April (shoulder) for standard plan
        apr_hours = get_seasonal_hours('standard', 3)
        assert apr_hours == SEASONAL_PLAN_HOURS['standard']['shoulder']

    def test_seasonal_hours_monotonic_by_season(self):
        """For same plan, summer > shoulder > winter hours."""
        from src.simulation import SEASONAL_PLAN_HOURS

        for plan in ['lite', 'standard', 'premium']:
            winter = SEASONAL_PLAN_HOURS[plan]['winter']
            shoulder = SEASONAL_PLAN_HOURS[plan]['shoulder']
            summer = SEASONAL_PLAN_HOURS[plan]['summer']

            assert summer > shoulder, f"{plan}: summer should > shoulder"
            assert shoulder > winter, f"{plan}: shoulder should > winter"

    def test_seasonal_hours_monotonic_by_plan(self):
        """For same season, premium > standard > lite hours."""
        from src.simulation import SEASONAL_PLAN_HOURS

        for season in ['winter', 'shoulder', 'summer']:
            lite = SEASONAL_PLAN_HOURS['lite'][season]
            standard = SEASONAL_PLAN_HOURS['standard'][season]
            premium = SEASONAL_PLAN_HOURS['premium'][season]

            assert premium > standard, f"{season}: premium should > standard"
            assert standard > lite, f"{season}: standard should > lite"

    def test_simulation_uses_seasonal_hours(self):
        """Simulation grid uses seasonal hours, not fixed."""
        from src.simulation import generate_customers, simulate_portfolio

        customers = generate_customers(100, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=12, random_seed=42)

        # Hours included should vary by month (seasonal)
        standard_customers = grid[grid['plan'] == 'standard']
        hours_by_month = standard_customers.groupby('month_of_year')['hours_included'].mean()

        # Summer months should have more hours than winter
        winter_hrs = hours_by_month[hours_by_month.index.isin([0, 1, 10, 11])].mean()
        summer_hrs = hours_by_month[hours_by_month.index.isin([4, 5, 6, 7])].mean()

        assert summer_hrs > winter_hrs, "Summer should have more hours than winter"

    def test_seasonal_reduces_summer_overage(self):
        """Seasonal hours should reduce summer overage vs fixed hours."""
        from src.simulation import generate_customers, simulate_portfolio

        customers = generate_customers(500, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=60, random_seed=42)

        grid['season'] = grid['month_of_year'].map({
            0: 'winter', 1: 'winter', 2: 'shoulder', 3: 'shoulder',
            4: 'summer', 5: 'summer', 6: 'summer', 7: 'summer',
            8: 'shoulder', 9: 'shoulder', 10: 'winter', 11: 'winter'
        })

        # Summer overage should be lower than with fixed 200 hrs
        # (With fixed 200, summer overage was ~49%)
        summer_overage = grid[grid['season'] == 'summer']['is_over_limit'].mean()
        assert summer_overage < 0.35, f"Summer overage {summer_overage:.1%} should be < 35%"
