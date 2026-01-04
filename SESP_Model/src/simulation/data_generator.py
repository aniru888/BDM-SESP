"""
Data Generator — Synthetic Customer Generation
==============================================

Generates realistic customer data for SESP simulation.

Key Features:
- 30/50/20 segment distribution (light/moderate/heavy)
- Self-selection into plans with 5% mismatch rate (for IC testing)
- Regional distribution across north/south/west/east
- Usage factors, efficiency scores, churn/default risks
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List, Tuple

# =============================================================================
# CONSTANTS
# =============================================================================

# Segment distributions (from CLAUDE.md)
CUSTOMER_SEGMENTS = {
    'light': {
        'proportion': 0.30,
        'base_hours': 100,        # Monthly baseline runtime hours
        'usage_factor_range': (0.7, 1.1),  # Multiplier on baseline
        'efficiency_score_range': (55, 95),  # Higher - lighter users tend to be efficient
        'churn_risk_weights': {'low': 0.5, 'medium': 0.4, 'high': 0.1},
        'default_risk_range': (0.01, 0.03),
    },
    'moderate': {
        'proportion': 0.50,
        'base_hours': 200,
        'usage_factor_range': (0.85, 1.15),
        'efficiency_score_range': (50, 90),
        'churn_risk_weights': {'low': 0.6, 'medium': 0.35, 'high': 0.05},
        'default_risk_range': (0.015, 0.035),
    },
    'heavy': {
        'proportion': 0.20,
        'base_hours': 350,
        'usage_factor_range': (0.9, 1.3),  # Heavy users vary more
        'efficiency_score_range': (40, 85),  # Lower avg - heavy users less efficient
        'churn_risk_weights': {'low': 0.7, 'medium': 0.25, 'high': 0.05},
        'default_risk_range': (0.02, 0.05),
    }
}

# Segment proportions for quick access
SEGMENT_DISTRIBUTIONS = {
    'light': 0.30,
    'moderate': 0.50,
    'heavy': 0.20,
}

# Self-selection: which plan each segment SHOULD choose
PLAN_MAPPING = {
    'light': 'lite',
    'moderate': 'standard',
    'heavy': 'premium',
}

# Region distribution (based on AC market share)
REGION_DISTRIBUTIONS = {
    'north': 0.35,   # Delhi, UP, Punjab, Rajasthan
    'south': 0.30,   # Tamil Nadu, Karnataka, Andhra
    'west': 0.25,    # Maharashtra, Gujarat
    'east': 0.10,    # Bengal, Odisha
}

# Credit card adoption rate
CREDIT_CARD_ADOPTION_RATE = 0.70  # 70% of customers opt for credit card


# =============================================================================
# DATA GENERATION FUNCTIONS
# =============================================================================

def generate_customers(
    n_customers: int = 1000,
    plan_mismatch_rate: float = 0.05,
    random_seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic customer data for simulation.

    Args:
        n_customers: Number of customers to generate (default 1000)
        plan_mismatch_rate: Fraction who don't choose optimal plan (for IC testing)
        random_seed: Random seed for reproducibility

    Returns:
        DataFrame with customer attributes

    Example:
        >>> df = generate_customers(100, random_seed=42)
        >>> df.shape
        (100, 11)
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    # Generate segment assignments based on proportions
    segments = np.random.choice(
        list(SEGMENT_DISTRIBUTIONS.keys()),
        size=n_customers,
        p=list(SEGMENT_DISTRIBUTIONS.values())
    )

    # Generate regions
    regions = np.random.choice(
        list(REGION_DISTRIBUTIONS.keys()),
        size=n_customers,
        p=list(REGION_DISTRIBUTIONS.values())
    )

    # Initialize arrays
    plans = []
    usage_factors = []
    efficiency_scores = []
    churn_risks = []
    default_risks = []

    for segment in segments:
        seg_config = CUSTOMER_SEGMENTS[segment]

        # Plan selection with mismatch
        if np.random.random() < plan_mismatch_rate:
            # Wrong plan selection (gaming or poor choice)
            wrong_plans = [p for p in PLAN_MAPPING.values() if p != PLAN_MAPPING[segment]]
            plan = np.random.choice(wrong_plans)
        else:
            plan = PLAN_MAPPING[segment]
        plans.append(plan)

        # Usage factor (how much they deviate from segment baseline)
        uf_low, uf_high = seg_config['usage_factor_range']
        usage_factors.append(np.random.uniform(uf_low, uf_high))

        # Efficiency score (behavior quality)
        eff_low, eff_high = seg_config['efficiency_score_range']
        efficiency_scores.append(np.random.uniform(eff_low, eff_high))

        # Churn risk category
        churn_weights = seg_config['churn_risk_weights']
        churn_risks.append(np.random.choice(
            list(churn_weights.keys()),
            p=list(churn_weights.values())
        ))

        # Default risk (payment failure probability)
        dr_low, dr_high = seg_config['default_risk_range']
        default_risks.append(np.random.uniform(dr_low, dr_high))

    # Credit card adoption
    has_credit_card = np.random.random(n_customers) < CREDIT_CARD_ADOPTION_RATE

    # Signup month (for seasonality start)
    signup_months = np.random.randint(0, 12, n_customers)

    # Build DataFrame
    df = pd.DataFrame({
        'customer_id': range(1, n_customers + 1),
        'segment': segments,
        'plan': plans,
        'region': regions,
        'has_credit_card': has_credit_card,
        'usage_factor': usage_factors,
        'efficiency_score_base': efficiency_scores,
        'churn_risk': churn_risks,
        'default_risk': default_risks,
        'signup_month': signup_months,
        'is_plan_mismatch': [p != PLAN_MAPPING[s] for s, p in zip(segments, plans)],
    })

    return df


def validate_customer_data(df: pd.DataFrame) -> Dict[str, any]:
    """
    Validate generated customer data matches expected distributions.

    Args:
        df: Customer DataFrame from generate_customers()

    Returns:
        Dictionary with validation results
    """
    results = {
        'n_customers': len(df),
        'segment_proportions': {},
        'plan_proportions': {},
        'region_proportions': {},
        'mismatch_rate': 0.0,
        'credit_card_rate': 0.0,
        'validation_passed': True,
        'issues': [],
    }

    # Check segment proportions
    for seg in SEGMENT_DISTRIBUTIONS:
        actual = (df['segment'] == seg).mean()
        expected = SEGMENT_DISTRIBUTIONS[seg]
        results['segment_proportions'][seg] = {
            'actual': actual,
            'expected': expected,
            'diff': abs(actual - expected),
        }
        # Allow 5% deviation due to randomness
        if abs(actual - expected) > 0.05:
            results['issues'].append(f"Segment '{seg}' off by {abs(actual-expected):.2%}")

    # Check plan proportions
    for plan in ['lite', 'standard', 'premium']:
        actual = (df['plan'] == plan).mean()
        results['plan_proportions'][plan] = actual

    # Check region proportions
    for region in REGION_DISTRIBUTIONS:
        actual = (df['region'] == region).mean()
        expected = REGION_DISTRIBUTIONS[region]
        results['region_proportions'][region] = {
            'actual': actual,
            'expected': expected,
        }

    # Mismatch rate
    results['mismatch_rate'] = df['is_plan_mismatch'].mean()

    # Credit card adoption
    results['credit_card_rate'] = df['has_credit_card'].mean()

    # Set overall validation status
    if results['issues']:
        results['validation_passed'] = False

    return results


def get_segment_baseline_hours(segment: str) -> int:
    """Get baseline monthly hours for a segment."""
    return CUSTOMER_SEGMENTS[segment]['base_hours']


def generate_customer_summary(df: pd.DataFrame) -> str:
    """Generate a readable summary of customer data."""
    validation = validate_customer_data(df)

    lines = [
        f"Customer Data Summary",
        f"=" * 40,
        f"Total customers: {len(df):,}",
        f"",
        f"Segment Distribution:",
    ]

    for seg, data in validation['segment_proportions'].items():
        lines.append(f"  {seg}: {data['actual']:.1%} (expected {data['expected']:.1%})")

    lines.extend([
        f"",
        f"Plan Distribution:",
    ])
    for plan, pct in validation['plan_proportions'].items():
        lines.append(f"  {plan}: {pct:.1%}")

    lines.extend([
        f"",
        f"Region Distribution:",
    ])
    for region, data in validation['region_proportions'].items():
        lines.append(f"  {region}: {data['actual']:.1%}")

    lines.extend([
        f"",
        f"Plan mismatch rate: {validation['mismatch_rate']:.1%}",
        f"Credit card adoption: {validation['credit_card_rate']:.1%}",
        f"",
        f"Validation: {'PASSED' if validation['validation_passed'] else 'FAILED'}",
    ])

    if validation['issues']:
        lines.append("Issues:")
        for issue in validation['issues']:
            lines.append(f"  - {issue}")

    return "\n".join(lines)


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    # Generate sample data
    df = generate_customers(1000, random_seed=42)
    print(generate_customer_summary(df))

    # Show sample rows
    print("\nSample customers:")
    print(df.head(10).to_string())
