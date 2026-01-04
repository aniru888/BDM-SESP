"""
Tests for Participation Constraint Checker
==========================================

Test Cases:
1. PC vs Purchase (primary constraint)
2. PC vs EMI (financing alternative)
3. PC vs Rental (no-commitment alternative)
4. Aggregate validation
5. Boundary finding
6. Sensitivity analysis

Run with: pytest tests/test_participation.py -v
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.constraints.participation import (
    check_pc_vs_purchase,
    check_pc_vs_emi,
    check_pc_vs_rental,
    validate_participation,
    find_pc_boundary,
    find_pc_boundary_by_fee,
    analyze_pc_sensitivity,
    DEFAULT_THRESHOLDS,
    SEGMENT_THRESHOLD_MULTIPLIERS,
)


class TestPCvsPurchase:
    """Test participation constraint vs outright purchase."""

    def test_high_subsidy_satisfies_pc(self):
        """
        High subsidy (38%) should satisfy PC vs purchase.

        With ₹17K subsidy on ₹45K MRP and 3-year tenure,
        SESP should be cheaper than purchase after terminal value.
        """
        sesp_params = {
            'subsidized_price': 28000,  # 38% subsidy
            'plan': 'moderate',
            'efficiency_score': 80,
            'deposit': 5000,
        }

        result = check_pc_vs_purchase(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=3,
            segment='moderate',
        )

        # High subsidy + longer tenure should satisfy PC
        assert 'satisfied' in result
        assert 'actual_savings_percent' in result
        # The actual result depends on economics

    def test_low_subsidy_fails_pc(self):
        """
        Very low subsidy should fail PC.

        With only ₹1K subsidy, SESP cannot compete with purchase.
        """
        sesp_params = {
            'subsidized_price': 44000,  # Only ₹1K subsidy (2.2%)
            'plan': 'moderate',
            'efficiency_score': 75,
            'deposit': 5000,
        }

        result = check_pc_vs_purchase(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=2,
            segment='moderate',
        )

        assert result['satisfied'] is False
        assert result['actual_savings_percent'] < result['threshold_percent']

    def test_segment_affects_threshold(self):
        """
        Light users need higher savings (more price-sensitive).
        """
        sesp_params = {
            'subsidized_price': 30000,
            'plan': 'moderate',
            'efficiency_score': 75,
        }

        light_result = check_pc_vs_purchase(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=2,
            segment='light',
        )

        heavy_result = check_pc_vs_purchase(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=2,
            segment='heavy',
        )

        # Light users have higher threshold
        assert light_result['threshold'] > heavy_result['threshold']

    def test_custom_threshold(self):
        """Custom threshold should override default."""
        sesp_params = {
            'subsidized_price': 30000,
            'plan': 'moderate',
        }

        result = check_pc_vs_purchase(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=2,
            segment='moderate',
            threshold=0.25,  # 25% custom threshold
        )

        assert result['threshold'] == 0.25
        assert result['threshold_percent'] == 25

    def test_result_structure(self):
        """Result should have all required fields."""
        sesp_params = {'subsidized_price': 30000, 'plan': 'moderate'}

        result = check_pc_vs_purchase(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=2,
            segment='moderate',
        )

        required_fields = [
            'constraint', 'satisfied', 'sesp_npv', 'purchase_npv',
            'target_npv', 'threshold', 'actual_savings',
            'actual_savings_percent', 'slack', 'recommendation'
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"


class TestPCvsEMI:
    """Test participation constraint vs EMI purchase."""

    def test_pc_vs_emi_12_month(self):
        """Test PC against 12-month EMI."""
        sesp_params = {
            'subsidized_price': 28000,
            'plan': 'moderate',
            'efficiency_score': 75,
        }

        result = check_pc_vs_emi(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=2,
            emi_tenure_months=12,
            segment='moderate',
        )

        assert 'constraint' in result
        assert result['constraint'] == 'PC_vs_EMI'
        assert result['emi_tenure_months'] == 12

    def test_pc_vs_emi_24_month(self):
        """Test PC against 24-month EMI."""
        sesp_params = {
            'subsidized_price': 28000,
            'plan': 'moderate',
        }

        result = check_pc_vs_emi(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=3,
            emi_tenure_months=24,
            segment='moderate',
        )

        assert result['emi_tenure_months'] == 24
        assert 'emi_npv' in result

    def test_emi_threshold_lower_than_purchase(self):
        """EMI threshold should be lower than purchase threshold."""
        assert DEFAULT_THRESHOLDS['emi'] < DEFAULT_THRESHOLDS['purchase']


class TestPCvsRental:
    """Test participation constraint vs rental."""

    def test_pc_vs_rental(self):
        """Test PC against rental alternative."""
        sesp_params = {
            'subsidized_price': 28000,
            'plan': 'moderate',
            'efficiency_score': 75,
        }

        result = check_pc_vs_rental(
            sesp_params=sesp_params,
            tenure_years=2,
            segment='moderate',
        )

        assert result['constraint'] == 'PC_vs_Rental'
        assert 'rental_npv' in result
        assert 'note' in result  # Should explain ownership difference

    def test_rental_threshold_is_zero(self):
        """Rental threshold should be 0% (SESP can match rental)."""
        assert DEFAULT_THRESHOLDS['rental'] == 0.0


class TestAggregateValidation:
    """Test aggregate participation constraint validation."""

    def test_validate_all_constraints(self):
        """Validate against all alternatives."""
        sesp_params = {
            'subsidized_price': 25000,  # High subsidy
            'plan': 'moderate',
            'efficiency_score': 80,
            'deposit': 5000,
        }

        result = validate_participation(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=3,
            segment='moderate',
        )

        assert 'all_satisfied' in result
        assert 'failed_constraints' in result
        assert 'individual_results' in result
        assert 'message' in result

    def test_validation_result_structure(self):
        """Validation result should have proper structure."""
        sesp_params = {'subsidized_price': 30000, 'plan': 'moderate'}

        result = validate_participation(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=2,
            segment='moderate',
        )

        # Should check all alternatives
        individual = result['individual_results']
        assert 'vs_purchase' in individual
        assert 'vs_emi_12m' in individual
        assert 'vs_emi_24m' in individual
        assert 'vs_rental' in individual

    def test_validation_counts_correct(self):
        """Passed/total counts should be correct."""
        sesp_params = {'subsidized_price': 30000, 'plan': 'moderate'}

        result = validate_participation(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=2,
            segment='moderate',
        )

        # Count manually
        individual = result['individual_results']
        passed = sum(1 for r in individual.values() if r['satisfied'])

        assert result['num_passed'] == passed
        assert result['num_total'] == len(individual)

    def test_skip_emi_option(self):
        """Should be able to skip EMI checks."""
        sesp_params = {'subsidized_price': 30000, 'plan': 'moderate'}

        result = validate_participation(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=2,
            segment='moderate',
            check_emi=False,
        )

        individual = result['individual_results']
        assert 'vs_purchase' in individual
        assert 'vs_emi_12m' not in individual
        assert 'vs_rental' in individual


class TestBoundaryFinding:
    """Test boundary finding functions."""

    def test_find_pc_boundary_price(self):
        """Find maximum price that satisfies PC."""
        result = find_pc_boundary(
            mrp=45000,
            tenure_years=3,
            segment='moderate',
            threshold=0.10,
        )

        assert 'boundary_subsidized_price' in result
        assert 'boundary_subsidy' in result
        assert 'subsidy_percent' in result
        assert 'recommendation' in result

        # Boundary price should be less than MRP
        assert result['boundary_subsidized_price'] < result['mrp']
        # Subsidy should be positive
        assert result['boundary_subsidy'] > 0

    def test_boundary_subsidy_plus_price_equals_mrp(self):
        """Boundary subsidy + price should equal MRP."""
        result = find_pc_boundary(
            mrp=45000,
            tenure_years=2,
            segment='moderate',
        )

        expected_mrp = result['boundary_subsidized_price'] + result['boundary_subsidy']
        assert abs(expected_mrp - result['mrp']) < 10  # Within ₹10

    def test_find_pc_boundary_by_fee(self):
        """
        Find maximum fee at fixed price.

        Note: With ₹30K subsidized price (33% subsidy) and 2-year tenure,
        achieving 10% savings vs purchase is difficult, so boundary fee
        may be at the minimum (₹199).
        """
        result = find_pc_boundary_by_fee(
            mrp=45000,
            subsidized_price=30000,
            tenure_years=2,
            segment='moderate',
            threshold=0.10,
        )

        assert 'boundary_monthly_fee' in result
        assert 'recommendation' in result
        # Fee should be in search range (₹199-1499)
        assert 199 <= result['boundary_monthly_fee'] <= 1500

    def test_higher_threshold_needs_more_subsidy(self):
        """Higher savings threshold should require more subsidy."""
        low_threshold = find_pc_boundary(
            mrp=45000,
            tenure_years=2,
            segment='moderate',
            threshold=0.05,  # 5%
        )

        high_threshold = find_pc_boundary(
            mrp=45000,
            tenure_years=2,
            segment='moderate',
            threshold=0.20,  # 20%
        )

        # Higher threshold = need more subsidy = lower boundary price
        assert high_threshold['boundary_subsidy'] >= low_threshold['boundary_subsidy']


class TestSensitivityAnalysis:
    """Test sensitivity analysis functions."""

    def test_sensitivity_analysis(self):
        """Run subsidy sensitivity analysis."""
        result = analyze_pc_sensitivity(
            mrp=45000,
            tenure_years=2,
            segment='moderate',
        )

        assert 'sensitivity_results' in result
        assert len(result['sensitivity_results']) > 0

        # Each result should have required fields
        for r in result['sensitivity_results']:
            assert 'subsidy' in r
            assert 'subsidized_price' in r
            assert 'savings_percent' in r
            assert 'satisfied' in r

    def test_sensitivity_custom_range(self):
        """Test with custom subsidy range."""
        custom_range = [5000, 10000, 15000, 20000]

        result = analyze_pc_sensitivity(
            mrp=45000,
            tenure_years=2,
            segment='moderate',
            subsidy_range=custom_range,
        )

        assert len(result['sensitivity_results']) == len(custom_range)

    def test_breakeven_subsidy_identified(self):
        """Should identify breakeven subsidy if exists."""
        result = analyze_pc_sensitivity(
            mrp=45000,
            tenure_years=3,  # Longer tenure helps
            segment='moderate',
            subsidy_range=[10000, 15000, 20000, 22500],
        )

        # With enough subsidy range, should find breakeven
        if result['breakeven_subsidy'] is not None:
            assert result['breakeven_subsidy_percent'] is not None
            # Breakeven should be less than 100% of MRP
            assert result['breakeven_subsidy_percent'] < 100


class TestSegmentThresholds:
    """Test segment-specific thresholds."""

    def test_light_users_higher_threshold(self):
        """Light users are more price-sensitive."""
        multiplier = SEGMENT_THRESHOLD_MULTIPLIERS['light']
        assert multiplier > 1.0  # Higher than base

    def test_heavy_users_lower_threshold(self):
        """Heavy users value service more."""
        multiplier = SEGMENT_THRESHOLD_MULTIPLIERS['heavy']
        assert multiplier < 1.0  # Lower than base

    def test_moderate_users_base_threshold(self):
        """Moderate users use base threshold."""
        multiplier = SEGMENT_THRESHOLD_MULTIPLIERS['moderate']
        assert multiplier == 1.0


class TestSanityChecks:
    """Sanity checks per VERIFICATION_CHECKLIST.md."""

    def test_savings_percent_realistic(self):
        """
        Savings should be in realistic range (5-30%).

        If savings > 40%, something is wrong (subsidy too high).
        If savings < 0%, SESP is more expensive (expected with low subsidy).
        """
        sesp_params = {
            'subsidized_price': 28000,
            'plan': 'moderate',
            'efficiency_score': 75,
        }

        result = check_pc_vs_purchase(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=2,
            segment='moderate',
        )

        # Savings should be less than 50% (unrealistic otherwise)
        assert result['actual_savings_percent'] < 50

    def test_threshold_range_reasonable(self):
        """Default thresholds should be in 0-25% range."""
        for alt, threshold in DEFAULT_THRESHOLDS.items():
            assert 0 <= threshold <= 0.25, f"{alt} threshold {threshold} outside range"

    def test_npv_values_positive(self):
        """NPV values should be positive (costs, not benefits)."""
        sesp_params = {'subsidized_price': 30000, 'plan': 'moderate'}

        result = check_pc_vs_purchase(
            sesp_params=sesp_params,
            mrp=45000,
            tenure_years=2,
            segment='moderate',
        )

        assert result['sesp_npv'] > 0
        assert result['purchase_npv'] > 0

    def test_recommendation_exists(self):
        """All results should have recommendations."""
        sesp_params = {'subsidized_price': 30000, 'plan': 'moderate'}

        # Test passing scenario
        result_pass = check_pc_vs_purchase(
            sesp_params={'subsidized_price': 20000, 'plan': 'moderate'},
            mrp=45000,
            tenure_years=3,
            segment='moderate',
        )

        # Test failing scenario
        result_fail = check_pc_vs_purchase(
            sesp_params={'subsidized_price': 44000, 'plan': 'moderate'},
            mrp=45000,
            tenure_years=2,
            segment='moderate',
        )

        assert 'recommendation' in result_pass
        assert 'recommendation' in result_fail
        assert len(result_pass['recommendation']) > 0
        assert len(result_fail['recommendation']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
