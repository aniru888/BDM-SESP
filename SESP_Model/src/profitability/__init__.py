"""
Profitability Analysis Module
=============================

This module provides before/after profitability comparison:
- traditional.py: Pre-SESP (traditional sales) economics
- sesp.py: SESP subscription model economics
- comparison.py: Side-by-side comparison and analysis

Phase 3 Tasks:
- 3.1: Traditional profitability model (traditional.py)
- 3.2: SESP profitability model (sesp.py)
- 3.3: Before vs After comparison (comparison.py)
"""

from .traditional import (
    calculate_traditional_revenue,
    calculate_traditional_costs,
    calculate_traditional_margin,
    calculate_traditional_clv,
)

from .sesp import (
    calculate_sesp_revenue,
    calculate_sesp_costs,
    calculate_sesp_margin,
    calculate_sesp_clv,
)

from .comparison import (
    compare_profitability,
    generate_comparison_table,
    calculate_delta_metrics,
    calculate_service_value_delivered,
    SERVICE_VALUE_ANNUAL,
    SERVICE_VALUE_COMPONENTS,
    # Phase 3c additions
    IOT_VALUE_ADDITIONS,
    IOT_VALUE_ANNUAL,
    TOTAL_SERVICE_VALUE_ANNUAL,
    CREDIT_CARD_CUSTOMER_VALUE,
    CREDIT_CARD_VALUE_ANNUAL,
    CREDIT_CARD_COMPANY_BENEFITS,
    BANK_CAC_SUBSIDY,
    # Phase 5 optional IoT additions
    OPTIONAL_IOT_ADDITIONS,
    OPTIONAL_IOT_VALUE_ANNUAL,
    OPTIONAL_IOT_COST_ANNUAL,
)

from .sensitivity_analysis import (
    run_tenure_sensitivity,
    run_dealer_margin_sensitivity,
    run_full_sensitivity_comparison,
    run_extended_tenure_test,
    BEFORE_PARAMS,
    AFTER_PARAMS,
    # Phase 3c additions
    SUBSIDY_OPTIONS,
    TIERED_PLANS,
    run_subsidy_sensitivity,
    run_tiered_plan_analysis,
    run_combined_sensitivity,
)

__all__ = [
    # Traditional
    'calculate_traditional_revenue',
    'calculate_traditional_costs',
    'calculate_traditional_margin',
    'calculate_traditional_clv',
    # SESP
    'calculate_sesp_revenue',
    'calculate_sesp_costs',
    'calculate_sesp_margin',
    'calculate_sesp_clv',
    # Comparison
    'compare_profitability',
    'generate_comparison_table',
    'calculate_delta_metrics',
    # Service Value (Phase 3b)
    'calculate_service_value_delivered',
    'SERVICE_VALUE_ANNUAL',
    'SERVICE_VALUE_COMPONENTS',
    # IoT Value Additions (Phase 3c)
    'IOT_VALUE_ADDITIONS',
    'IOT_VALUE_ANNUAL',
    'TOTAL_SERVICE_VALUE_ANNUAL',
    # Credit Card Partnership (Phase 3c)
    'CREDIT_CARD_CUSTOMER_VALUE',
    'CREDIT_CARD_VALUE_ANNUAL',
    'CREDIT_CARD_COMPANY_BENEFITS',
    'BANK_CAC_SUBSIDY',
    # Optional IoT Additions (Phase 5)
    'OPTIONAL_IOT_ADDITIONS',
    'OPTIONAL_IOT_VALUE_ANNUAL',
    'OPTIONAL_IOT_COST_ANNUAL',
    # Sensitivity Analysis (Phase 3b)
    'run_tenure_sensitivity',
    'run_dealer_margin_sensitivity',
    'run_full_sensitivity_comparison',
    'run_extended_tenure_test',
    'BEFORE_PARAMS',
    'AFTER_PARAMS',
    # Subsidy Sensitivity (Phase 3c)
    'SUBSIDY_OPTIONS',
    'TIERED_PLANS',
    'run_subsidy_sensitivity',
    'run_tiered_plan_analysis',
    'run_combined_sensitivity',
]
