"""
AHP for Incentive Mechanism Criteria Weights (Task 2.0.1)
=========================================================

Purpose:
    Derive priority weights for designing the SESP incentive mechanism
    (efficiency rewards, overage structure, etc.)

Criteria:
    C1: Customer Satisfaction — Drives adoption and retention
    C2: Moral Hazard Control — Prevents gaming (known IC issue)
    C3: Revenue Protection — Ensures business viability
    C4: Operational Simplicity — Ease of implementation and communication

Method:
    Analytic Hierarchy Process (AHP) with Saaty scale pairwise comparisons

Output:
    Criteria weights to be used in TOPSIS pricing scenario ranking
"""

import numpy as np
from typing import Dict, Optional
from .mcdm_utils import create_comparison_matrix, ahp_consistency_ratio, ahp_sensitivity_analysis


# =============================================================================
# Criteria Definition
# =============================================================================

INCENTIVE_CRITERIA = {
    0: {
        'name': 'Customer Satisfaction',
        'short': 'Satisfaction',
        'description': 'Drives adoption, retention, NPS scores',
        'weight_rationale': 'High priority — without customers, no business'
    },
    1: {
        'name': 'Moral Hazard Control',
        'short': 'MoralHazard',
        'description': 'Prevents gaming, overuse, IC violations',
        'weight_rationale': 'Medium priority — known IC issue from Phase 1'
    },
    2: {
        'name': 'Revenue Protection',
        'short': 'Revenue',
        'description': 'Ensures margins, cash flow predictability',
        'weight_rationale': 'High priority — sustainability requires profit'
    },
    3: {
        'name': 'Operational Simplicity',
        'short': 'Simplicity',
        'description': 'Easy to implement, explain to customers',
        'weight_rationale': 'Low priority — nice-to-have, not essential'
    }
}


# =============================================================================
# Pairwise Comparison Matrix — Rationally Justified
# =============================================================================

def get_comparison_rationale() -> Dict:
    """
    Document the rationale for each pairwise comparison.

    Returns:
        Dict mapping comparison pairs to their values and justifications
    """
    return {
        # C0 (Satisfaction) vs C1 (Moral Hazard)
        (0, 1): {
            'value': 2,
            'interpretation': 'Satisfaction is SLIGHTLY more important than Moral Hazard',
            'rationale': (
                'Customer adoption is the prerequisite for everything. '
                'Without satisfied customers, moral hazard control is irrelevant. '
                'However, the IC violation from Phase 1 shows moral hazard is still significant.'
            )
        },
        # C0 (Satisfaction) vs C2 (Revenue)
        (0, 2): {
            'value': 1,
            'interpretation': 'Satisfaction and Revenue are EQUALLY important',
            'rationale': (
                'Both are critical success factors. '
                'Satisfaction drives adoption; Revenue ensures survival. '
                'Neither can be sacrificed for the other in the long run.'
            )
        },
        # C0 (Satisfaction) vs C3 (Simplicity)
        (0, 3): {
            'value': 5,
            'interpretation': 'Satisfaction is STRONGLY more important than Simplicity',
            'rationale': (
                'Complexity can be managed internally; dissatisfied customers leave. '
                'We can invest in systems to handle complexity if it improves satisfaction.'
            )
        },
        # C1 (Moral Hazard) vs C2 (Revenue)
        (1, 2): {
            'value': 1/2,
            'interpretation': 'Revenue is SLIGHTLY more important than Moral Hazard',
            'rationale': (
                'Revenue enables scaling and investment in better moral hazard controls. '
                'Some gaming (IC violation) is acceptable if it keeps customers and revenue.'
            )
        },
        # C1 (Moral Hazard) vs C3 (Simplicity)
        (1, 3): {
            'value': 3,
            'interpretation': 'Moral Hazard is MODERATELY more important than Simplicity',
            'rationale': (
                'Gaming prevention protects the business model. '
                'Simplicity is nice but not worth allowing abuse.'
            )
        },
        # C2 (Revenue) vs C3 (Simplicity)
        (2, 3): {
            'value': 4,
            'interpretation': 'Revenue is STRONGLY/MODERATELY more important than Simplicity',
            'rationale': (
                'Revenue is a hard business requirement; simplicity is a soft preference. '
                'We accept operational complexity for better financial outcomes.'
            )
        }
    }


def build_comparison_matrix() -> np.ndarray:
    """
    Build the 4×4 pairwise comparison matrix from documented rationale.

    Returns:
        4×4 numpy array with Saaty scale values
    """
    rationale = get_comparison_rationale()

    comparisons = {
        pair: info['value']
        for pair, info in rationale.items()
    }

    return create_comparison_matrix(comparisons, n=4)


# =============================================================================
# Main AHP Analysis
# =============================================================================

def run_ahp_incentive(verbose: bool = True) -> Dict:
    """
    Run complete AHP analysis for incentive mechanism criteria.

    Args:
        verbose: If True, print detailed output

    Returns:
        Dict with:
        - comparison_matrix: The 4×4 pairwise comparison matrix
        - weights: Priority weights for each criterion
        - cr: Consistency Ratio
        - is_consistent: Boolean (CR < 0.10)
        - rationale: Documentation of each judgment
        - sensitivity: Sensitivity analysis results
    """
    # Build matrix
    comparison_matrix = build_comparison_matrix()

    # Calculate weights and consistency
    result = ahp_consistency_ratio(comparison_matrix)

    # Get rationale
    rationale = get_comparison_rationale()

    # Run sensitivity analysis on key judgments
    # Vary the most impactful comparisons: Satisfaction vs others
    sensitivity = ahp_sensitivity_analysis(
        comparison_matrix,
        vary_indices=[(0, 1), (0, 2), (1, 2)],
        variation_range=0.25  # ±25%
    )

    # Prepare output
    output = {
        'comparison_matrix': comparison_matrix,
        'weights': result['weights'],
        'weight_labels': [INCENTIVE_CRITERIA[i]['short'] for i in range(4)],
        'lambda_max': result['lambda_max'],
        'ci': result['ci'],
        'ri': result['ri'],
        'cr': result['cr'],
        'is_consistent': result['is_consistent'],
        'message': result['message'],
        'rationale': rationale,
        'sensitivity': sensitivity
    }

    if verbose:
        print_ahp_report(output)

    return output


def get_incentive_weights() -> Dict[str, float]:
    """
    Get the criteria weights as a labeled dictionary.

    Returns:
        Dict mapping criterion names to weights
    """
    result = run_ahp_incentive(verbose=False)
    weights = result['weights']

    return {
        'satisfaction': weights[0],
        'moral_hazard': weights[1],
        'revenue': weights[2],
        'simplicity': weights[3]
    }


# =============================================================================
# Reporting
# =============================================================================

def print_ahp_report(result: Dict) -> None:
    """Print formatted AHP analysis report."""
    print("\n" + "=" * 70)
    print("AHP ANALYSIS: Incentive Mechanism Criteria Weights")
    print("=" * 70)

    print("\n## Criteria")
    for i, info in INCENTIVE_CRITERIA.items():
        print(f"  C{i}: {info['name']} — {info['description']}")

    print("\n## Pairwise Comparison Matrix (Saaty Scale 1-9)")
    print_matrix(result['comparison_matrix'], [INCENTIVE_CRITERIA[i]['short'] for i in range(4)])

    print("\n## Comparison Rationale")
    for pair, info in result['rationale'].items():
        print(f"  C{pair[0]} vs C{pair[1]}: {info['value']:.2f}")
        print(f"    → {info['interpretation']}")
        print(f"    Reason: {info['rationale'][:80]}...")

    print("\n## Priority Weights")
    for i in range(4):
        print(f"  {INCENTIVE_CRITERIA[i]['short']:15s}: {result['weights'][i]:.4f} ({result['weights'][i]*100:.1f}%)")

    print(f"\n## Consistency Check")
    print(f"  λ_max = {result['lambda_max']:.4f}")
    print(f"  CI = {result['ci']:.4f}")
    print(f"  RI = {result['ri']:.2f} (for n=4)")
    print(f"  CR = {result['cr']:.4f}")
    print(f"  Status: {'✅ CONSISTENT' if result['is_consistent'] else '❌ INCONSISTENT'} (CR {'<' if result['is_consistent'] else '>='} 0.10)")

    print("\n## Weight Interpretation")
    sorted_idx = np.argsort(-result['weights'])
    print("  Priority ranking:")
    for rank, i in enumerate(sorted_idx, 1):
        print(f"    {rank}. {INCENTIVE_CRITERIA[i]['name']}: {result['weights'][i]*100:.1f}%")

    print("\n" + "=" * 70)


def print_matrix(matrix: np.ndarray, labels: list) -> None:
    """Print matrix with labels."""
    n = len(labels)
    # Header
    header = "             " + "  ".join(f"{l:>10s}" for l in labels)
    print(header)

    # Rows
    for i in range(n):
        row_str = f"{labels[i]:12s} "
        row_str += "  ".join(f"{matrix[i, j]:>10.3f}" for j in range(n))
        print(row_str)


# =============================================================================
# Analysis for Report
# =============================================================================

def generate_ahp_report_section() -> str:
    """
    Generate markdown content for the MCDM Analysis Report section.

    Returns:
        Markdown-formatted analysis
    """
    result = run_ahp_incentive(verbose=False)

    md = []
    md.append("## 7.1 AHP for Incentive Mechanism Criteria Weights\n")

    md.append("### Criteria Definition\n")
    for i, info in INCENTIVE_CRITERIA.items():
        md.append(f"- **C{i}: {info['name']}** — {info['description']}\n")

    md.append("\n### Pairwise Comparison Matrix\n")
    md.append("Using Saaty's 1-9 scale:\n")
    md.append("| | Satisfaction | MoralHazard | Revenue | Simplicity |\n")
    md.append("|---|---|---|---|---|\n")
    labels = ['Satisfaction', 'MoralHazard', 'Revenue', 'Simplicity']
    for i in range(4):
        row = f"| {labels[i]} |"
        for j in range(4):
            row += f" {result['comparison_matrix'][i,j]:.2f} |"
        md.append(row + "\n")

    md.append("\n### Judgment Rationale\n")
    for pair, info in result['rationale'].items():
        md.append(f"- **C{pair[0]} vs C{pair[1]} = {info['value']:.1f}**: {info['rationale']}\n")

    md.append("\n### Priority Weights (Eigenvector Method)\n")
    md.append("| Criterion | Weight | Interpretation |\n")
    md.append("|---|---|---|\n")
    sorted_idx = np.argsort(-result['weights'])
    for i in sorted_idx:
        md.append(f"| {INCENTIVE_CRITERIA[i]['name']} | {result['weights'][i]:.4f} ({result['weights'][i]*100:.1f}%) | Rank {np.where(sorted_idx == i)[0][0] + 1} |\n")

    md.append(f"\n### Consistency Check\n")
    md.append(f"- λ_max = {result['lambda_max']:.4f}\n")
    md.append(f"- Consistency Index (CI) = {result['ci']:.4f}\n")
    md.append(f"- Random Index (RI) = {result['ri']:.2f}\n")
    md.append(f"- **Consistency Ratio (CR) = {result['cr']:.4f}** {'✅ < 0.10' if result['is_consistent'] else '❌ >= 0.10'}\n")

    md.append("\n### Key Findings\n")
    md.append(f"1. **{INCENTIVE_CRITERIA[sorted_idx[0]]['name']}** has highest priority — essential for adoption\n")
    md.append(f"2. **{INCENTIVE_CRITERIA[sorted_idx[-1]]['name']}** has lowest priority — can be sacrificed\n")
    md.append("3. These weights will be used in TOPSIS pricing scenario ranking\n")

    return "".join(md)


if __name__ == "__main__":
    # Run analysis
    result = run_ahp_incentive(verbose=True)

    # Print weights for use in TOPSIS
    print("\n\nWeights for TOPSIS (copy-paste):")
    weights = get_incentive_weights()
    print(f"weights = {weights}")
