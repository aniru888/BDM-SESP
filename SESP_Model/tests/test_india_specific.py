"""
Tests for India-Specific Adjustments
=====================================

Test Cases:
1. Seasonality application (AC and Fridge)
2. GST calculations (consistency check)
3. NPV calculations (customer vs firm)
4. Electricity slab calculations
5. Terminal value adjustments

Run with: pytest tests/test_india_specific.py -v
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adjustments.india_specific import (
    apply_seasonality,
    get_seasonality_profile,
    apply_seasonality_to_series,
    calculate_gst,
    calculate_gst_on_services,
    validate_gst_consistency,
    npv_customer,
    npv_firm,
    calculate_npv_arbitrage,
    calculate_electricity_cost_slabs,
    get_terminal_value_local,
    adjusted_purchase_cost_with_terminal,
    generate_monthly_projections,
    SEASONALITY_PROFILES,
    CUSTOMER_DISCOUNT_RATES,
    FIRM_DISCOUNT_RATE,
)


class TestSeasonality:
    """Test seasonality adjustments."""

    def test_north_india_summer_peak(self):
        """North India should peak in May (index 4) at 1.70."""
        profile = get_seasonality_profile('north', 'AC')
        assert profile[4] == 1.70  # May

    def test_north_india_winter_low(self):
        """North India winter should be near zero (0.05)."""
        profile = get_seasonality_profile('north', 'AC')
        assert profile[0] == 0.05   # January
        assert profile[11] == 0.05  # December

    def test_apply_seasonality_summer(self):
        """Summer should increase baseline significantly."""
        baseline = 150
        may_hours = apply_seasonality(baseline, 4, 'north', 'AC')
        assert may_hours == 255.0  # 150 × 1.70

    def test_apply_seasonality_winter(self):
        """Winter should drastically reduce baseline."""
        baseline = 150
        dec_hours = apply_seasonality(baseline, 11, 'north', 'AC')
        assert dec_hours == 7.5  # 150 × 0.05

    def test_fridge_seasonality_minimal(self):
        """Fridge seasonality should be nearly flat."""
        profile = get_seasonality_profile('north', 'FRIDGE')
        # All values should be between 0.95 and 1.10
        assert all(0.95 <= v <= 1.10 for v in profile)

    def test_all_regions_exist(self):
        """All four regions should have profiles."""
        for region in ['north', 'south', 'west', 'east']:
            profile = get_seasonality_profile(region, 'AC')
            assert len(profile) == 12

    def test_seasonality_series(self):
        """Test generating a seasonal series."""
        series = apply_seasonality_to_series(100, 12, 0, 'north', 'AC')
        assert len(series) == 12
        # May (index 4) should be highest
        assert series[4] == max(series)
        # December (index 11) should be lowest
        assert series[11] == min(series)

    def test_invalid_month_raises_error(self):
        """Invalid month index should raise error."""
        with pytest.raises(ValueError):
            apply_seasonality(100, 15, 'north', 'AC')

    def test_invalid_region_raises_error(self):
        """Invalid region should raise error."""
        with pytest.raises(ValueError):
            apply_seasonality(100, 5, 'invalid', 'AC')


class TestGSTCalculations:
    """Test GST calculation and consistency."""

    def test_gst_exclusive(self):
        """GST added to base amount."""
        result = calculate_gst(649)
        assert result['base'] == 649
        assert result['gst'] == pytest.approx(116.82, abs=0.01)
        assert result['total'] == pytest.approx(765.82, abs=0.01)

    def test_gst_inclusive(self):
        """GST extracted from inclusive amount."""
        result = calculate_gst(45000, inclusive=True)
        assert result['total'] == 45000
        assert result['base'] == pytest.approx(38135.59, abs=0.01)
        assert result['gst'] == pytest.approx(6864.41, abs=0.01)

    def test_gst_on_multiple_services(self):
        """GST applied to multiple services."""
        result = calculate_gst_on_services({
            'amc': 2500,
            'repair': 3000
        })

        assert result['amc']['gst'] == 450
        assert result['repair']['gst'] == 540
        assert result['totals']['gst'] == 990

    def test_gst_consistency_check_passes(self):
        """Valid GST application should pass consistency check."""
        sesp = {'gst_amount': 116.82}
        purchase = {'amc_gst': 450, 'amc_annual': 2500, 'repair_gst': 0, 'expected_repairs': 0}

        is_consistent, issues = validate_gst_consistency(sesp, purchase)
        assert is_consistent is True
        assert len(issues) == 0

    def test_gst_consistency_check_fails(self):
        """Missing GST should fail consistency check."""
        sesp = {'gst_amount': 0}  # Missing GST
        purchase = {'amc_gst': 0, 'amc_annual': 2500}  # Missing GST on AMC

        is_consistent, issues = validate_gst_consistency(sesp, purchase)
        assert is_consistent is False
        assert len(issues) >= 1


class TestNPVCalculations:
    """Test NPV calculations for customer and firm."""

    def test_customer_discount_rates(self):
        """Customer discount rates should be segment-specific."""
        assert CUSTOMER_DISCOUNT_RATES['light'] == 0.28
        assert CUSTOMER_DISCOUNT_RATES['moderate'] == 0.22
        assert CUSTOMER_DISCOUNT_RATES['heavy'] == 0.16

    def test_firm_discount_rate(self):
        """Firm discount rate should be 12%."""
        assert FIRM_DISCOUNT_RATE == 0.12

    def test_npv_customer_monthly_payments(self):
        """NPV of monthly payments from customer perspective."""
        # 24 months of ₹649 + GST
        monthly = 649 * 1.18
        cash_flows = [-monthly] * 24

        npv = npv_customer(cash_flows, 'moderate')
        # Should be negative (outflows) and less than simple sum
        assert npv < 0
        assert abs(npv) < monthly * 24  # Discounted < sum

    def test_npv_firm_higher_than_customer(self):
        """Firm NPV should be higher than customer NPV (value arbitrage)."""
        cash_flows = [649] * 24

        firm_value = npv_firm(cash_flows)
        customer_value = npv_customer(cash_flows, 'moderate')

        # Same cash flows, but firm values them more (lower rate)
        assert firm_value > customer_value

    def test_npv_arbitrage_positive(self):
        """NPV arbitrage should be positive (firm benefits)."""
        cash_flows = [649] * 24
        arbitrage = calculate_npv_arbitrage(cash_flows, 'moderate')

        assert arbitrage['firm_npv'] > 0
        assert arbitrage['customer_npv'] > 0
        assert arbitrage['arbitrage'] > 0
        assert arbitrage['arbitrage_percent'] > 0

    def test_higher_customer_rate_means_lower_npv(self):
        """Light users (higher rate) should have lower NPV."""
        cash_flows = [100] * 24

        npv_light = npv_customer(cash_flows, 'light')      # 28%
        npv_moderate = npv_customer(cash_flows, 'moderate')  # 22%
        npv_heavy = npv_customer(cash_flows, 'heavy')      # 16%

        assert npv_light < npv_moderate < npv_heavy


class TestElectricitySlabs:
    """Test electricity slab-based cost calculations."""

    def test_first_slab_only(self):
        """Usage in first slab only."""
        result = calculate_electricity_cost_slabs(150)
        assert result['total_kwh'] == 150
        assert result['total_cost'] == 525.0  # 150 × 3.5
        assert result['average_rate'] == 3.5

    def test_multiple_slabs(self):
        """Usage spanning multiple slabs."""
        result = calculate_electricity_cost_slabs(450)
        # 200 @ 3.5 = 700
        # 200 @ 5.0 = 1000
        # 50 @ 6.5 = 325
        # Total = 2025
        assert result['total_cost'] == 2025.0

    def test_high_usage(self):
        """High usage reaching top slab."""
        result = calculate_electricity_cost_slabs(1000)
        # 200 @ 3.5 = 700
        # 200 @ 5.0 = 1000
        # 400 @ 6.5 = 2600
        # 200 @ 7.5 = 1500
        # Total = 5800
        assert result['total_cost'] == 5800.0

    def test_slab_breakdown_structure(self):
        """Slab breakdown should have correct structure."""
        result = calculate_electricity_cost_slabs(300)
        assert 'slab_breakdown' in result
        assert len(result['slab_breakdown']) == 2  # Two slabs used


class TestTerminalValue:
    """Test terminal value adjustments."""

    def test_ac_terminal_values(self):
        """AC terminal values should decrease over time."""
        year_3 = get_terminal_value_local('AC', 3)
        year_5 = get_terminal_value_local('AC', 5)
        year_7 = get_terminal_value_local('AC', 7)

        assert year_3 > year_5 > year_7

    def test_fridge_terminal_values(self):
        """Fridge terminal values should exist."""
        value = get_terminal_value_local('FRIDGE', 5)
        assert value > 0

    def test_adjusted_purchase_cost(self):
        """Adjusted purchase cost should be less than MRP."""
        result = adjusted_purchase_cost_with_terminal(45000, 2, 'moderate', 'AC')

        # Effective MRP should be less than MRP (terminal value subtracted)
        assert result['effective_mrp'] < result['mrp']

        # Terminal PV should be positive
        assert result['terminal_pv'] > 0

    def test_adjusted_purchase_includes_amc(self):
        """Adjusted cost should include AMC if specified."""
        with_amc = adjusted_purchase_cost_with_terminal(
            45000, 2, 'moderate', 'AC', include_amc=True
        )
        without_amc = adjusted_purchase_cost_with_terminal(
            45000, 2, 'moderate', 'AC', include_amc=False
        )

        assert with_amc['total_cost'] > without_amc['total_cost']
        assert with_amc['amc_total'] > 0
        assert without_amc['amc_total'] == 0

    def test_terminal_value_decreases_with_tenure(self):
        """Longer tenure should have lower terminal value."""
        cost_2y = adjusted_purchase_cost_with_terminal(45000, 2, 'moderate', 'AC')
        cost_5y = adjusted_purchase_cost_with_terminal(45000, 5, 'moderate', 'AC')

        # Terminal PV should be lower for longer tenure
        assert cost_2y['terminal_pv'] > cost_5y['terminal_pv']


class TestMonthlyProjections:
    """Test monthly projection generation."""

    def test_projection_length(self):
        """Projections should match tenure length."""
        projections = generate_monthly_projections(150, 24, 0, 'north', 'AC')
        assert len(projections) == 24

    def test_projection_structure(self):
        """Each projection should have required fields."""
        projections = generate_monthly_projections(150, 12, 0, 'north', 'AC')

        for proj in projections:
            assert 'period' in proj
            assert 'month_index' in proj
            assert 'month_name' in proj
            assert 'seasonal_factor' in proj
            assert 'adjusted_hours' in proj

    def test_projection_seasonality_applied(self):
        """Projections should have seasonality applied."""
        projections = generate_monthly_projections(150, 12, 0, 'north', 'AC')

        # May (period 5, index 4) should be highest
        may_proj = projections[4]
        assert may_proj['seasonal_factor'] == 1.70
        assert may_proj['adjusted_hours'] == 255.0

    def test_projection_start_month_offset(self):
        """Start month should offset the sequence."""
        # Start in April (index 3)
        projections = generate_monthly_projections(100, 6, 3, 'north', 'AC')

        # First month should be April
        assert projections[0]['month_name'] == 'Apr'
        # Second should be May (peak)
        assert projections[1]['month_name'] == 'May'
        assert projections[1]['seasonal_factor'] == 1.70


class TestSanityChecks:
    """Sanity checks per VERIFICATION_CHECKLIST.md."""

    def test_north_india_extreme_seasonality(self):
        """North India should have extreme variation (stress test)."""
        profile = get_seasonality_profile('north', 'AC')
        ratio = max(profile) / min(profile)
        # Should be at least 30x variation (1.70 / 0.05 = 34)
        assert ratio >= 30

    def test_gst_rate_is_18_percent(self):
        """GST rate should be 18%."""
        result = calculate_gst(100)
        assert result['gst'] == 18.0

    def test_customer_rates_higher_than_firm(self):
        """All customer rates should be higher than firm rate."""
        for segment, rate in CUSTOMER_DISCOUNT_RATES.items():
            assert rate > FIRM_DISCOUNT_RATE, f"{segment} rate should exceed firm rate"

    def test_electricity_rates_realistic(self):
        """Electricity rates should be in ₹3-8 range."""
        result = calculate_electricity_cost_slabs(1000)
        avg_rate = result['average_rate']
        assert 3 <= avg_rate <= 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
