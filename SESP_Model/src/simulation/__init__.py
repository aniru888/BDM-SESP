"""
Simulation Module
=================

Phase 4 implementation: Customer journey simulation for SESP pricing model.

This module provides:
- data_generator.py: Synthetic customer data generation
- simulator.py: Vectorized month-by-month simulation
- aggregator.py: Result aggregation by customer/segment/month/portfolio

Key Design Principles:
1. VECTORIZED operations (no nested loops) using pandas/numpy
2. Hours-based simulation (NOT kWh) - consistent with bucket model
3. Efficiency score rewards BEHAVIOR, not low usage
4. Uses seasonality from src/adjustments/india_specific.py
"""

from .data_generator import (
    generate_customers,
    CUSTOMER_SEGMENTS,
    SEGMENT_DISTRIBUTIONS,
    PLAN_MAPPING,
    validate_customer_data,
)

from .simulator import (
    simulate_portfolio,
    simulate_single_customer,
    PLAN_FEES,
    PLAN_HOURS,
    OVERAGE_RATES,
    OVERAGE_CAPS,
    EFFICIENCY_TIERS,
    # Seasonal Hours (Budget Effect for energy efficiency)
    SEASONS,
    SEASONAL_PLAN_HOURS,
    get_seasonal_hours,
)

from .aggregator import (
    aggregate_by_customer,
    aggregate_by_segment,
    aggregate_by_month,
    aggregate_portfolio,
    calculate_simulation_summary,
)

__all__ = [
    # Data Generator
    'generate_customers',
    'CUSTOMER_SEGMENTS',
    'SEGMENT_DISTRIBUTIONS',
    'PLAN_MAPPING',
    'validate_customer_data',
    # Simulator
    'simulate_portfolio',
    'simulate_single_customer',
    'PLAN_FEES',
    'PLAN_HOURS',
    'OVERAGE_RATES',
    'OVERAGE_CAPS',
    'EFFICIENCY_TIERS',
    # Seasonal Hours (Budget Effect)
    'SEASONS',
    'SEASONAL_PLAN_HOURS',
    'get_seasonal_hours',
    # Aggregator
    'aggregate_by_customer',
    'aggregate_by_segment',
    'aggregate_by_month',
    'aggregate_portfolio',
    'calculate_simulation_summary',
]
