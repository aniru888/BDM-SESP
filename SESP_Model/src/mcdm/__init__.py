"""
MCDM (Multi-Criteria Decision Making) Module
=============================================

This module implements three MCDM methods for the SESP pricing model:

1. AHP (Analytic Hierarchy Process)
   - Derive criteria weights from pairwise comparisons
   - Validate consistency (CR < 0.10)

2. TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)
   - Rank alternatives using weighted criteria
   - Find closeness to ideal/negative-ideal solutions

3. DEA (Data Envelopment Analysis)
   - Evaluate efficiency of subscription plans
   - Identify efficient frontier and improvement targets

Applications:
- Task 2.0.1: AHP for incentive mechanism criteria
- Task 2.0.2: TOPSIS for pricing scenario ranking
- Task 2.0.3: DEA for plan efficiency
- Task 5.0.1: AHP for regional launch criteria
- Task 5.0.2: TOPSIS for regional ranking
"""

from .mcdm_utils import (
    # AHP functions
    ahp_weights,
    ahp_consistency_ratio,
    create_comparison_matrix,
    # TOPSIS functions
    topsis_rank,
    normalize_matrix,
    weighted_matrix,
    ideal_solutions,
    separation_measures,
    closeness_scores,
    # DEA functions
    dea_efficiency,
    dea_efficiency_all,
)

from .ahp_incentive import (
    run_ahp_incentive,
    INCENTIVE_CRITERIA,
    get_incentive_weights,
)

from .topsis_pricing import (
    run_topsis_pricing,
    PRICING_SCENARIOS,
    derive_scenario_metrics,
)

from .dea_plan_efficiency import (
    run_dea_analysis,
    PLAN_DATA,
    get_efficiency_scores,
)

__all__ = [
    # Utils
    'ahp_weights',
    'ahp_consistency_ratio',
    'create_comparison_matrix',
    'topsis_rank',
    'normalize_matrix',
    'weighted_matrix',
    'ideal_solutions',
    'separation_measures',
    'closeness_scores',
    'dea_efficiency',
    'dea_efficiency_all',
    # AHP Incentive
    'run_ahp_incentive',
    'INCENTIVE_CRITERIA',
    'get_incentive_weights',
    # TOPSIS Pricing
    'run_topsis_pricing',
    'PRICING_SCENARIOS',
    'derive_scenario_metrics',
    # DEA
    'run_dea_analysis',
    'PLAN_DATA',
    'get_efficiency_scores',
]
