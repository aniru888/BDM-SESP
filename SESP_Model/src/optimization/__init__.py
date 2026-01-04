"""
Optimization Module
==================

Contains pricing optimization algorithms using constrained optimization,
MCDM techniques, and game-theoretic analysis.

Main Components:
- PricingOptimizer: Finds optimal fee-hours combinations
- optimize_tiered_pricing: Convenience function for menu optimization
"""

from .pricing_optimizer import (
    PricingOptimizer,
    optimize_tiered_pricing,
    calculate_customer_utility,
    calculate_company_margin,
    check_ic_constraint,
    check_pc_constraint,
)

__all__ = [
    'PricingOptimizer',
    'optimize_tiered_pricing',
    'calculate_customer_utility',
    'calculate_company_margin',
    'check_ic_constraint',
    'check_pc_constraint',
]
