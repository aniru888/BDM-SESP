"""
MCDM Utilities — Core Algorithms
================================

This module provides the core algorithms for:
1. AHP (Analytic Hierarchy Process) — Eigenvector method with consistency check
2. TOPSIS — Vector normalization, ideal solutions, closeness scores
3. DEA (Data Envelopment Analysis) — Full LP formulation using scipy

References:
- Saaty, T.L. (1980). The Analytic Hierarchy Process.
- Hwang, C.L. & Yoon, K. (1981). TOPSIS method.
- Charnes, A., Cooper, W.W. & Rhodes, E. (1978). DEA model.
"""

import numpy as np
from scipy.optimize import linprog
from typing import Dict, List, Tuple, Optional, Union


# =============================================================================
# AHP (Analytic Hierarchy Process)
# =============================================================================

# Random Index (RI) values for consistency check (Saaty, 1980)
# Index corresponds to matrix size n
RANDOM_INDEX = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
}


def create_comparison_matrix(comparisons: Dict[Tuple[int, int], float], n: int) -> np.ndarray:
    """
    Create a pairwise comparison matrix from a dictionary of comparisons.

    Args:
        comparisons: Dict mapping (i, j) pairs to comparison values.
                     Only upper triangle needed; lower triangle is reciprocal.
        n: Matrix size (number of criteria)

    Returns:
        n×n comparison matrix

    Example:
        comparisons = {
            (0, 1): 3,    # C0 is 3x more important than C1
            (0, 2): 2,    # C0 is 2x more important than C2
            (1, 2): 1/2,  # C1 is half as important as C2
        }
        matrix = create_comparison_matrix(comparisons, 3)
    """
    matrix = np.ones((n, n))

    for (i, j), value in comparisons.items():
        if i < j:
            matrix[i, j] = value
            matrix[j, i] = 1 / value
        elif i > j:
            matrix[i, j] = value
            matrix[j, i] = 1 / value

    return matrix


def ahp_weights(comparison_matrix: np.ndarray) -> Tuple[np.ndarray, float, float]:
    """
    Calculate AHP priority weights using the eigenvector method.

    Args:
        comparison_matrix: n×n pairwise comparison matrix (Saaty scale 1-9)

    Returns:
        Tuple of (weights, lambda_max, consistency_index)
        - weights: Priority vector (sums to 1.0)
        - lambda_max: Principal eigenvalue
        - ci: Consistency Index

    Method:
        1. Calculate principal eigenvector of comparison matrix
        2. Normalize to get priority weights
        3. Calculate λ_max for consistency check
    """
    n = comparison_matrix.shape[0]

    # Calculate eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eig(comparison_matrix)

    # Find principal (largest real) eigenvalue
    max_idx = np.argmax(eigenvalues.real)
    lambda_max = eigenvalues[max_idx].real

    # Get corresponding eigenvector (priority weights)
    principal_eigenvector = eigenvectors[:, max_idx].real

    # Normalize to sum to 1
    weights = principal_eigenvector / np.sum(principal_eigenvector)

    # Ensure all positive (eigenvector can have arbitrary sign)
    if np.any(weights < 0):
        weights = -weights

    # Calculate Consistency Index
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0

    return weights, lambda_max, ci


def ahp_consistency_ratio(comparison_matrix: np.ndarray) -> Dict:
    """
    Calculate AHP weights with full consistency analysis.

    Args:
        comparison_matrix: n×n pairwise comparison matrix

    Returns:
        Dict with:
        - weights: Priority vector
        - lambda_max: Principal eigenvalue
        - ci: Consistency Index
        - ri: Random Index for matrix size
        - cr: Consistency Ratio (must be < 0.10)
        - is_consistent: Boolean (CR < 0.10)
        - message: Human-readable interpretation
    """
    n = comparison_matrix.shape[0]
    weights, lambda_max, ci = ahp_weights(comparison_matrix)

    ri = RANDOM_INDEX.get(n, 1.49)  # Default to n=10 value for larger matrices
    cr = ci / ri if ri > 0 else 0

    is_consistent = cr < 0.10

    if is_consistent:
        message = f"Consistent (CR={cr:.4f} < 0.10)"
    else:
        message = f"INCONSISTENT! CR={cr:.4f} >= 0.10. Revise judgments."

    return {
        'weights': weights,
        'lambda_max': lambda_max,
        'ci': ci,
        'ri': ri,
        'cr': cr,
        'is_consistent': is_consistent,
        'message': message
    }


def ahp_sensitivity_analysis(
    comparison_matrix: np.ndarray,
    vary_indices: List[Tuple[int, int]],
    variation_range: float = 0.2
) -> Dict:
    """
    Perform sensitivity analysis on AHP weights.

    Args:
        comparison_matrix: Base comparison matrix
        vary_indices: List of (i, j) pairs to vary
        variation_range: Percentage to vary (0.2 = ±20%)

    Returns:
        Dict with sensitivity results for each varied judgment
    """
    base_result = ahp_consistency_ratio(comparison_matrix)
    base_weights = base_result['weights']

    results = {
        'base_weights': base_weights,
        'variations': {}
    }

    for (i, j) in vary_indices:
        original_value = comparison_matrix[i, j]

        # Vary up and down
        for factor in [1 - variation_range, 1 + variation_range]:
            varied_matrix = comparison_matrix.copy()
            new_value = original_value * factor
            varied_matrix[i, j] = new_value
            varied_matrix[j, i] = 1 / new_value

            varied_result = ahp_consistency_ratio(varied_matrix)

            key = f"({i},{j})_x{factor:.2f}"
            results['variations'][key] = {
                'new_value': new_value,
                'weights': varied_result['weights'],
                'weight_change': varied_result['weights'] - base_weights,
                'cr': varied_result['cr'],
                'is_consistent': varied_result['is_consistent']
            }

    return results


# =============================================================================
# TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)
# =============================================================================

def normalize_matrix(decision_matrix: np.ndarray) -> np.ndarray:
    """
    Normalize decision matrix using vector normalization.

    Args:
        decision_matrix: m×n matrix (m alternatives, n criteria)

    Returns:
        Normalized matrix where each column has unit vector length

    Formula: r_ij = x_ij / sqrt(sum(x_ij^2))
    """
    # Calculate column norms
    col_norms = np.sqrt(np.sum(decision_matrix ** 2, axis=0))

    # Avoid division by zero
    col_norms = np.where(col_norms == 0, 1, col_norms)

    return decision_matrix / col_norms


def weighted_matrix(normalized_matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """
    Apply weights to normalized decision matrix.

    Args:
        normalized_matrix: Normalized decision matrix
        weights: Criteria weights (must sum to 1.0)

    Returns:
        Weighted normalized matrix
    """
    return normalized_matrix * weights


def ideal_solutions(
    weighted_matrix: np.ndarray,
    criteria_types: List[str]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Find ideal (A*) and negative-ideal (A') solutions.

    Args:
        weighted_matrix: Weighted normalized matrix
        criteria_types: List of 'benefit' or 'cost' for each criterion
                        'benefit' = higher is better
                        'cost' = lower is better

    Returns:
        Tuple of (ideal_solution, negative_ideal_solution)
    """
    n_criteria = weighted_matrix.shape[1]
    ideal = np.zeros(n_criteria)
    negative_ideal = np.zeros(n_criteria)

    for j in range(n_criteria):
        col = weighted_matrix[:, j]
        if criteria_types[j].lower() == 'benefit':
            ideal[j] = np.max(col)
            negative_ideal[j] = np.min(col)
        else:  # cost
            ideal[j] = np.min(col)
            negative_ideal[j] = np.max(col)

    return ideal, negative_ideal


def separation_measures(
    weighted_matrix: np.ndarray,
    ideal: np.ndarray,
    negative_ideal: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate separation measures from ideal and negative-ideal solutions.

    Args:
        weighted_matrix: Weighted normalized matrix
        ideal: Ideal solution A*
        negative_ideal: Negative-ideal solution A'

    Returns:
        Tuple of (S_plus, S_minus) arrays for each alternative
        S_plus = distance to ideal
        S_minus = distance to negative-ideal
    """
    # Euclidean distance to ideal
    s_plus = np.sqrt(np.sum((weighted_matrix - ideal) ** 2, axis=1))

    # Euclidean distance to negative-ideal
    s_minus = np.sqrt(np.sum((weighted_matrix - negative_ideal) ** 2, axis=1))

    return s_plus, s_minus


def closeness_scores(s_plus: np.ndarray, s_minus: np.ndarray) -> np.ndarray:
    """
    Calculate relative closeness to ideal solution.

    Args:
        s_plus: Distance to ideal solution
        s_minus: Distance to negative-ideal solution

    Returns:
        Closeness scores C* in [0, 1] (higher = better)

    Formula: C* = S- / (S+ + S-)
    """
    denominator = s_plus + s_minus
    # Avoid division by zero
    denominator = np.where(denominator == 0, 1, denominator)

    return s_minus / denominator


def topsis_rank(
    decision_matrix: np.ndarray,
    weights: np.ndarray,
    criteria_types: List[str],
    alternative_names: Optional[List[str]] = None
) -> Dict:
    """
    Perform complete TOPSIS analysis.

    Args:
        decision_matrix: m×n matrix (m alternatives, n criteria)
        weights: Criteria weights (should sum to 1.0)
        criteria_types: List of 'benefit' or 'cost' for each criterion
        alternative_names: Optional names for alternatives

    Returns:
        Dict with:
        - normalized_matrix: After vector normalization
        - weighted_matrix: After applying weights
        - ideal: Ideal solution A*
        - negative_ideal: Negative-ideal solution A'
        - s_plus: Distances to ideal
        - s_minus: Distances to negative-ideal
        - closeness: Relative closeness scores
        - ranking: Indices sorted by closeness (best first)
        - ranked_alternatives: Names in ranked order (if provided)
    """
    m = decision_matrix.shape[0]

    # Normalize weights if not already
    weights = np.array(weights)
    if not np.isclose(weights.sum(), 1.0):
        weights = weights / weights.sum()

    # Step 1: Normalize
    norm_matrix = normalize_matrix(decision_matrix)

    # Step 2: Weight
    w_matrix = weighted_matrix(norm_matrix, weights)

    # Step 3: Ideal solutions
    ideal, negative_ideal = ideal_solutions(w_matrix, criteria_types)

    # Step 4: Separation measures
    s_plus, s_minus = separation_measures(w_matrix, ideal, negative_ideal)

    # Step 5: Closeness scores
    c_scores = closeness_scores(s_plus, s_minus)

    # Step 6: Rank (descending by closeness)
    ranking = np.argsort(-c_scores)  # Negative for descending

    # Prepare alternative names
    if alternative_names is None:
        alternative_names = [f"Alternative_{i}" for i in range(m)]

    return {
        'normalized_matrix': norm_matrix,
        'weighted_matrix': w_matrix,
        'ideal': ideal,
        'negative_ideal': negative_ideal,
        's_plus': s_plus,
        's_minus': s_minus,
        'closeness': c_scores,
        'ranking': ranking,
        'ranked_alternatives': [alternative_names[i] for i in ranking],
        'ranked_scores': c_scores[ranking]
    }


# =============================================================================
# DEA (Data Envelopment Analysis) — Full LP Formulation
# =============================================================================

def dea_efficiency(
    inputs: np.ndarray,
    outputs: np.ndarray,
    dmu_index: int,
    orientation: str = 'output'
) -> Dict:
    """
    Calculate DEA efficiency for a specific DMU using Linear Programming.

    This implements the CCR model (Charnes, Cooper, Rhodes) with CRS
    (Constant Returns to Scale).

    Args:
        inputs: (n_dmus, n_inputs) array — resources consumed
        outputs: (n_dmus, n_outputs) array — value produced
        dmu_index: Index of DMU to evaluate (0-based)
        orientation: 'output' (expand outputs) or 'input' (reduce inputs)

    Returns:
        Dict with:
        - efficiency: Efficiency score (1.0 = on frontier)
        - phi: Raw LP solution (for output orientation)
        - lambdas: Reference weights for peer DMUs
        - slack_inputs: Input slack values
        - slack_outputs: Output slack values
        - is_efficient: Boolean (efficiency == 1.0)
        - peers: Indices of reference DMUs (lambda > 0)

    Mathematical formulation (output-oriented):
        max φ
        s.t. Σ(λ_j × x_ij) ≤ x_ik       for all inputs i
             Σ(λ_j × y_rj) ≥ φ × y_rk   for all outputs r
             λ_j ≥ 0                     for all j
    """
    inputs = np.array(inputs)
    outputs = np.array(outputs)

    n_dmus = inputs.shape[0]
    n_inputs = inputs.shape[1]
    n_outputs = outputs.shape[1]

    # Target DMU's data
    x_k = inputs[dmu_index]
    y_k = outputs[dmu_index]

    if orientation == 'output':
        # Variables: [phi, lambda_0, lambda_1, ..., lambda_{n-1}]
        # Objective: maximize phi → minimize -phi
        c = np.array([-1.0] + [0.0] * n_dmus)

        # Inequality constraints: A_ub @ x <= b_ub
        # Input constraints: Σ(λ_j × x_ij) <= x_ik
        # Rewrite as: -phi * 0 + λ @ X[i] <= x_k[i]
        A_ub_input = np.zeros((n_inputs, 1 + n_dmus))
        for i in range(n_inputs):
            A_ub_input[i, 0] = 0  # phi coefficient
            A_ub_input[i, 1:] = inputs[:, i]  # lambda coefficients
        b_ub_input = x_k

        # Output constraints: Σ(λ_j × y_rj) >= φ × y_rk
        # Rewrite as: -Σ(λ_j × y_rj) + φ × y_rk <= 0
        # Or: φ × y_rk - λ @ Y[r] <= 0
        A_ub_output = np.zeros((n_outputs, 1 + n_dmus))
        for r in range(n_outputs):
            A_ub_output[r, 0] = y_k[r]  # phi coefficient
            A_ub_output[r, 1:] = -outputs[:, r]  # lambda coefficients
        b_ub_output = np.zeros(n_outputs)

        # Combine constraints
        A_ub = np.vstack([A_ub_input, A_ub_output])
        b_ub = np.concatenate([b_ub_input, b_ub_output])

        # Bounds: phi >= 1, lambda_j >= 0
        bounds = [(1.0, None)] + [(0, None)] * n_dmus

        # Solve LP
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

        if result.success:
            phi = result.x[0]
            lambdas = result.x[1:]
            efficiency = 1.0 / phi  # Convert to [0, 1] scale

            # Calculate slacks
            slack_inputs = x_k - inputs.T @ lambdas
            slack_outputs = phi * y_k - outputs.T @ lambdas

            # Identify peers (DMUs with lambda > small threshold)
            peers = np.where(lambdas > 1e-6)[0].tolist()

            return {
                'efficiency': efficiency,
                'phi': phi,
                'lambdas': lambdas,
                'slack_inputs': slack_inputs,
                'slack_outputs': slack_outputs,
                'is_efficient': np.isclose(efficiency, 1.0, atol=1e-6),
                'peers': peers,
                'status': 'optimal'
            }
        else:
            return {
                'efficiency': None,
                'phi': None,
                'lambdas': None,
                'slack_inputs': None,
                'slack_outputs': None,
                'is_efficient': None,
                'peers': None,
                'status': f'failed: {result.message}'
            }

    else:  # input orientation
        # Variables: [theta, lambda_0, lambda_1, ..., lambda_{n-1}]
        # Objective: minimize theta
        c = np.array([1.0] + [0.0] * n_dmus)

        # Input constraints: Σ(λ_j × x_ij) <= θ × x_ik
        # Rewrite as: λ @ X[i] - θ × x_k[i] <= 0
        A_ub_input = np.zeros((n_inputs, 1 + n_dmus))
        for i in range(n_inputs):
            A_ub_input[i, 0] = -x_k[i]  # theta coefficient
            A_ub_input[i, 1:] = inputs[:, i]  # lambda coefficients
        b_ub_input = np.zeros(n_inputs)

        # Output constraints: Σ(λ_j × y_rj) >= y_rk
        # Rewrite as: -λ @ Y[r] <= -y_rk
        A_ub_output = np.zeros((n_outputs, 1 + n_dmus))
        for r in range(n_outputs):
            A_ub_output[r, 0] = 0  # theta coefficient
            A_ub_output[r, 1:] = -outputs[:, r]  # lambda coefficients
        b_ub_output = -y_k

        # Combine constraints
        A_ub = np.vstack([A_ub_input, A_ub_output])
        b_ub = np.concatenate([b_ub_input, b_ub_output])

        # Bounds: 0 <= theta <= 1, lambda_j >= 0
        bounds = [(0, 1)] + [(0, None)] * n_dmus

        # Solve LP
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

        if result.success:
            theta = result.x[0]
            lambdas = result.x[1:]
            efficiency = theta

            # Calculate slacks
            slack_inputs = theta * x_k - inputs.T @ lambdas
            slack_outputs = outputs.T @ lambdas - y_k

            # Identify peers
            peers = np.where(lambdas > 1e-6)[0].tolist()

            return {
                'efficiency': efficiency,
                'theta': theta,
                'lambdas': lambdas,
                'slack_inputs': slack_inputs,
                'slack_outputs': slack_outputs,
                'is_efficient': np.isclose(efficiency, 1.0, atol=1e-6),
                'peers': peers,
                'status': 'optimal'
            }
        else:
            return {
                'efficiency': None,
                'theta': None,
                'lambdas': None,
                'slack_inputs': None,
                'slack_outputs': None,
                'is_efficient': None,
                'peers': None,
                'status': f'failed: {result.message}'
            }


def dea_efficiency_all(
    inputs: np.ndarray,
    outputs: np.ndarray,
    dmu_names: Optional[List[str]] = None,
    orientation: str = 'output'
) -> Dict:
    """
    Calculate DEA efficiency for all DMUs.

    Args:
        inputs: (n_dmus, n_inputs) array
        outputs: (n_dmus, n_outputs) array
        dmu_names: Optional names for DMUs
        orientation: 'output' or 'input'

    Returns:
        Dict with:
        - efficiencies: Array of efficiency scores
        - results: List of individual DEA results
        - frontier_dmus: List of efficient DMU indices
        - ranking: DMUs ranked by efficiency (highest first)
        - improvement_targets: For inefficient DMUs
    """
    inputs = np.array(inputs)
    outputs = np.array(outputs)
    n_dmus = inputs.shape[0]

    if dmu_names is None:
        dmu_names = [f"DMU_{i}" for i in range(n_dmus)]

    results = []
    efficiencies = []

    for i in range(n_dmus):
        result = dea_efficiency(inputs, outputs, i, orientation)
        results.append(result)
        efficiencies.append(result['efficiency'] if result['efficiency'] is not None else 0)

    efficiencies = np.array(efficiencies)
    ranking = np.argsort(-efficiencies)  # Descending
    frontier_dmus = np.where(np.isclose(efficiencies, 1.0, atol=1e-6))[0].tolist()

    # Calculate improvement targets for inefficient DMUs
    improvement_targets = {}
    for i in range(n_dmus):
        if not results[i]['is_efficient'] and results[i]['efficiency'] is not None:
            if orientation == 'output':
                # Output targets = current outputs * phi
                phi = results[i]['phi']
                target_outputs = outputs[i] * phi
                improvement = target_outputs - outputs[i]
                improvement_targets[dmu_names[i]] = {
                    'current_outputs': outputs[i].tolist(),
                    'target_outputs': target_outputs.tolist(),
                    'improvement_needed': improvement.tolist(),
                    'improvement_percent': ((phi - 1) * 100)
                }
            else:
                # Input targets = current inputs * theta
                theta = results[i]['theta']
                target_inputs = inputs[i] * theta
                reduction = inputs[i] - target_inputs
                improvement_targets[dmu_names[i]] = {
                    'current_inputs': inputs[i].tolist(),
                    'target_inputs': target_inputs.tolist(),
                    'reduction_needed': reduction.tolist(),
                    'reduction_percent': ((1 - theta) * 100)
                }

    return {
        'efficiencies': efficiencies,
        'results': results,
        'frontier_dmus': frontier_dmus,
        'frontier_names': [dmu_names[i] for i in frontier_dmus],
        'ranking': ranking,
        'ranked_names': [dmu_names[i] for i in ranking],
        'ranked_efficiencies': efficiencies[ranking],
        'improvement_targets': improvement_targets
    }
