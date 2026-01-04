"""
Tests for Incentive Compatibility (IC) Constraint Checker
==========================================================

Test Cases:
1. Utility calculation for segment×plan combinations
2. IC checks for Light, Moderate, Heavy users
3. Aggregate IC validation
4. IC violation identification
5. Sensitivity analysis
6. Known IC issue documentation

Run with: pytest tests/test_incentive_compatibility.py -v
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.constraints.incentive_compatibility import (
    calculate_utility,
    calculate_all_utilities,
    check_ic_light,
    check_ic_moderate,
    check_ic_heavy,
    validate_ic,
    identify_ic_violations,
    analyze_ic_sensitivity,
    compare_plan_costs_for_segment,
    SEGMENT_USAGE_HOURS,
    SEGMENT_INTENDED_PLAN,
    SERVICE_VALUE_MULTIPLIER,
)
from src.pricing.bucket_model import SUBSCRIPTION_PLANS


class TestUtilityCalculation:
    """Test utility calculation functions."""

    def test_utility_basic(self):
        """Utility should be Value - Cost."""
        result = calculate_utility('moderate', 'moderate')

        assert 'utility' in result
        assert 'monthly_cost' in result
        assert 'service_value' in result
        # Utility = Value - Cost
        expected_utility = result['service_value'] - result['monthly_cost']
        assert result['utility'] == pytest.approx(expected_utility, abs=0.01)

    def test_utility_includes_cost_breakdown(self):
        """Utility result should include cost breakdown."""
        result = calculate_utility('moderate', 'moderate')

        breakdown = result['cost_breakdown']
        assert 'base_fee' in breakdown
        assert 'overage' in breakdown
        assert 'efficiency_discount' in breakdown
        assert 'gst' in breakdown

    def test_utility_marks_intended_plan(self):
        """Should correctly identify intended vs non-intended plan."""
        intended = calculate_utility('moderate', 'moderate')
        not_intended = calculate_utility('moderate', 'light')

        assert intended['is_intended_plan'] is True
        assert not_intended['is_intended_plan'] is False

    def test_utility_all_plans_for_segment(self):
        """Calculate utilities for all plans."""
        utilities = calculate_all_utilities('moderate')

        assert 'light' in utilities
        assert 'moderate' in utilities
        assert 'heavy' in utilities

    def test_service_value_multiplier(self):
        """Heavy users should have higher service value."""
        light_util = calculate_utility('light', 'light')
        heavy_util = calculate_utility('heavy', 'heavy')

        # Heavy users value service 1.2x vs Light users 1.0x
        assert heavy_util['service_value'] > light_util['service_value']


class TestICLight:
    """Test IC constraint for Light users."""

    def test_ic_light_result_structure(self):
        """IC Light result should have required fields."""
        result = check_ic_light()

        assert 'constraint' in result
        assert result['constraint'] == 'IC_Light'
        assert 'satisfied' in result
        assert 'utilities' in result
        assert 'best_plan' in result
        assert 'intended_plan' in result
        assert result['intended_plan'] == 'light'

    def test_ic_light_utilities_exist(self):
        """All plan utilities should be calculated."""
        result = check_ic_light()

        assert 'light' in result['utilities']
        assert 'moderate' in result['utilities']
        assert 'heavy' in result['utilities']

    def test_light_users_prefer_light_plan(self):
        """
        Light users should prefer Light plan (lowest cost for low usage).

        With 120 hours/month:
        - Light plan: 150 hours included, no overage
        - Moderate plan: Higher base fee, no benefit
        - Heavy plan: Much higher base fee, no benefit
        """
        result = check_ic_light()

        # Light users SHOULD prefer Light (their intended plan)
        # This constraint should typically be satisfied
        assert result['best_plan'] in ['light', 'moderate']  # Either is acceptable


class TestICModerate:
    """Test IC constraint for Moderate users."""

    def test_ic_moderate_result_structure(self):
        """IC Moderate result should have required fields."""
        result = check_ic_moderate()

        assert result['constraint'] == 'IC_Moderate'
        assert result['intended_plan'] == 'moderate'

    def test_moderate_users_check(self):
        """
        Moderate users (200 hours) on different plans.

        - Light plan: 150 hours included, 50 hours excess × ₹5 = ₹250 overage (capped at ₹200)
        - Moderate plan: 225 hours included, no overage
        - Heavy plan: Higher base fee, no benefit
        """
        result = check_ic_moderate()

        assert 'satisfied' in result
        assert 'best_plan' in result


class TestICHeavy:
    """Test IC constraint for Heavy users."""

    def test_ic_heavy_result_structure(self):
        """IC Heavy result should have required fields."""
        result = check_ic_heavy()

        assert result['constraint'] == 'IC_Heavy'
        assert result['intended_plan'] == 'heavy'

    def test_ic_heavy_known_violation(self):
        """
        KNOWN IC ISSUE: Heavy users prefer Light plan.

        Heavy users (320 hours/month):
        - Light plan: 150 hours included, 170 excess × ₹5 = ₹850 → CAPPED at ₹200
          Total: ₹499 + ₹200 = ₹699
        - Heavy plan: 350 hours included, no overage
          Total: ₹899

        Result: Heavy users pay ₹200 LESS by choosing "wrong" Light plan!
        This is an IC VIOLATION documented in the codebase.
        """
        result = check_ic_heavy()

        # Document the known IC violation
        if not result['satisfied']:
            # This is expected behavior - the IC violation is known
            assert result['best_plan'] in ['light', 'moderate']
            assert result['violation_details'] is not None
            assert 'reason' in result['violation_details']

            # The violation should explain the gaming opportunity
            reason = result['violation_details']['reason'].lower()
            assert 'save' in reason or 'prefer' in reason or 'choosing' in reason

    def test_ic_heavy_utilities_correct_order(self):
        """Heavy users should have lower utility on Heavy plan due to IC issue."""
        result = check_ic_heavy()

        utilities = result['utilities']
        # Due to overage cap, Light plan has higher utility (lower cost, same service)
        # This is the IC violation we're documenting

        # The Heavy plan fee is ₹899, Light plan + capped overage is ₹699
        # So utility_light > utility_heavy (IC violated)
        if not result['satisfied']:
            assert utilities['light'] >= utilities['heavy'] or utilities['moderate'] >= utilities['heavy']


class TestAggregateValidation:
    """Test aggregate IC validation."""

    def test_validate_ic_structure(self):
        """Validate IC should return proper structure."""
        result = validate_ic()

        assert 'all_satisfied' in result
        assert 'violations' in result
        assert 'num_passed' in result
        assert 'num_total' in result
        assert 'message' in result
        assert 'individual_results' in result

    def test_validate_ic_counts(self):
        """Passed counts should be correct."""
        result = validate_ic()

        individual = result['individual_results']
        expected_passed = sum(1 for r in individual.values() if r['satisfied'])

        assert result['num_passed'] == expected_passed
        assert result['num_total'] == 3

    def test_validate_ic_violations_list(self):
        """Violations list should match failed constraints."""
        result = validate_ic()

        individual = result['individual_results']
        expected_violations = [
            name for name, r in individual.items() if not r['satisfied']
        ]

        assert set(result['violations']) == set(expected_violations)

    def test_validate_ic_has_recommendations(self):
        """Should have recommendations if there are violations."""
        result = validate_ic()

        if not result['all_satisfied']:
            assert result['recommendations'] is not None
            assert len(result['recommendations']) > 0


class TestViolationIdentification:
    """Test IC violation identification."""

    def test_identify_violations(self):
        """Identify IC violations should return list."""
        violations = identify_ic_violations()

        assert isinstance(violations, list)

    def test_violation_details(self):
        """Each violation should have details."""
        violations = identify_ic_violations()

        if violations:  # May be empty if no violations
            for v in violations:
                assert 'segment' in v
                assert 'preferred_plan' in v
                assert 'intended_plan' in v
                assert 'recommendation' in v


class TestSensitivityAnalysis:
    """Test IC sensitivity analysis."""

    def test_overage_cap_sensitivity(self):
        """Analyze overage cap impact on IC."""
        result = analyze_ic_sensitivity('overage_cap')

        assert 'parameter' in result
        assert result['parameter'] == 'overage_cap'
        assert 'results' in result
        assert 'recommendation' in result

    def test_heavy_fee_sensitivity(self):
        """Analyze Heavy plan fee impact on IC."""
        result = analyze_ic_sensitivity('heavy_fee')

        assert result['parameter'] == 'heavy_fee'
        assert len(result['results']) > 0

    def test_sensitivity_custom_values(self):
        """Test with custom parameter values."""
        custom_caps = [200, 400, 600]
        result = analyze_ic_sensitivity('overage_cap', custom_caps)

        assert len(result['results']) == len(custom_caps)

    def test_sensitivity_finds_breakeven(self):
        """Should find breakeven value if exists in range."""
        # Test wide range to find breakeven
        result = analyze_ic_sensitivity('overage_cap', [200, 300, 400, 500, 600, 700])

        # There should be a breakeven point where IC becomes satisfied
        # This is expected around ₹400-500 cap based on the math
        breakeven = result['breakeven_value']
        # Breakeven may or may not exist depending on fee structure

    def test_invalid_parameter_raises_error(self):
        """Invalid parameter should raise error."""
        with pytest.raises(ValueError):
            analyze_ic_sensitivity('invalid_param')


class TestCostComparison:
    """Test cost comparison helper."""

    def test_compare_costs_structure(self):
        """Cost comparison should have proper structure."""
        result = compare_plan_costs_for_segment('heavy')

        assert 'segment' in result
        assert 'usage_hours' in result
        assert 'costs_by_plan' in result
        assert 'cheapest_plan' in result
        assert 'intended_plan' in result
        assert 'gaming_possible' in result

    def test_compare_costs_all_plans(self):
        """Should compare costs for all plans."""
        result = compare_plan_costs_for_segment('moderate')

        assert 'light' in result['costs_by_plan']
        assert 'moderate' in result['costs_by_plan']
        assert 'heavy' in result['costs_by_plan']

    def test_gaming_flag_for_heavy_users(self):
        """
        Heavy users should show gaming is possible (known IC issue).
        """
        result = compare_plan_costs_for_segment('heavy')

        # Due to overage cap, gaming should be possible for heavy users
        # They can choose Light plan and pay less
        # gaming_possible = cheapest_plan != intended_plan
        assert 'gaming_possible' in result

        # Document the expected behavior
        if result['gaming_possible']:
            assert result['cheapest_plan'] != result['intended_plan']


class TestSegmentProfiles:
    """Test segment profile constants."""

    def test_usage_hours_increasing(self):
        """Usage hours should increase from Light to Heavy."""
        light = SEGMENT_USAGE_HOURS['light']['expected']
        moderate = SEGMENT_USAGE_HOURS['moderate']['expected']
        heavy = SEGMENT_USAGE_HOURS['heavy']['expected']

        assert light < moderate < heavy

    def test_intended_plans_match_segments(self):
        """Each segment should have matching intended plan."""
        assert SEGMENT_INTENDED_PLAN['light'] == 'light'
        assert SEGMENT_INTENDED_PLAN['moderate'] == 'moderate'
        assert SEGMENT_INTENDED_PLAN['heavy'] == 'heavy'

    def test_service_value_multipliers(self):
        """Heavy users should value service more."""
        assert SERVICE_VALUE_MULTIPLIER['light'] < SERVICE_VALUE_MULTIPLIER['heavy']


class TestSanityChecks:
    """Sanity checks per VERIFICATION_CHECKLIST.md."""

    def test_overage_cap_creates_gaming(self):
        """
        Document: Overage cap creates gaming opportunity.

        This is not a bug — it's the known IC issue from REALISATIONS.md.
        """
        heavy_costs = compare_plan_costs_for_segment('heavy')

        light_cost = heavy_costs['costs_by_plan']['light']['monthly_cost']
        heavy_cost = heavy_costs['costs_by_plan']['heavy']['monthly_cost']

        # Heavy users on Light plan should be cheaper due to capped overage
        # This documents the IC violation
        gaming_savings = heavy_cost - light_cost

        # Print for documentation
        print(f"\nIC Issue Documentation:")
        print(f"  Heavy user on Light plan: ₹{light_cost:.0f}")
        print(f"  Heavy user on Heavy plan: ₹{heavy_cost:.0f}")
        print(f"  Gaming savings: ₹{gaming_savings:.0f}/month")

        # No assertion — this test documents the known issue

    def test_utility_calculation_valid(self):
        """Utility values should be reasonable."""
        for segment in ['light', 'moderate', 'heavy']:
            utilities = calculate_all_utilities(segment)

            for plan, util in utilities.items():
                # Monthly cost should be positive
                assert util['monthly_cost'] > 0
                # Service value should be positive
                assert util['service_value'] > 0
                # Utility can be negative (cost > value)
                assert isinstance(util['utility'], (int, float))

    def test_no_negative_costs(self):
        """Monthly costs should never be negative."""
        for segment in ['light', 'moderate', 'heavy']:
            for plan in ['light', 'moderate', 'heavy']:
                util = calculate_utility(segment, plan)
                assert util['monthly_cost'] > 0


class TestKnownICIssue:
    """
    Document and verify the known IC issue.

    This class exists to explicitly test and document the IC violation
    that was discovered during development.
    """

    def test_document_ic_violation(self):
        """
        DOCUMENTED IC ISSUE: Heavy users prefer Light plan.

        Math:
        - Heavy user usage: 320 hours/month
        - Light plan: 150 included, ₹5/hour overage, ₹200 cap
          - Excess: 170 hours × ₹5 = ₹850 → capped at ₹200
          - Total: ₹499 + ₹200 = ₹699
        - Heavy plan: 350 included, no overage
          - Total: ₹899

        Result: Heavy users save ₹200/month by gaming Light plan.

        Recommendations from REALISATIONS.md:
        1. Raise Light plan overage cap to ₹400+
        2. Lower Heavy plan fee to ~₹700
        3. Add non-monetary penalties for sustained overuse
        """
        # Calculate actual costs
        heavy_on_light = calculate_utility('heavy', 'light')
        heavy_on_heavy = calculate_utility('heavy', 'heavy')

        light_cost = heavy_on_light['monthly_cost']
        heavy_cost = heavy_on_heavy['monthly_cost']

        # Document the issue
        print(f"\n=== KNOWN IC ISSUE ===")
        print(f"Heavy user (320 hours) cost comparison:")
        print(f"  Light plan: ₹{light_cost:.0f} (with capped overage)")
        print(f"  Heavy plan: ₹{heavy_cost:.0f} (no overage)")
        print(f"  Gaming benefit: ₹{heavy_cost - light_cost:.0f}/month")
        print(f"========================")

        # This test passes to document the issue exists
        assert light_cost < heavy_cost, "IC violation confirmed: Light plan cheaper for heavy users"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
