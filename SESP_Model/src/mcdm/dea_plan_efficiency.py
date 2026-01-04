"""
DEA for Plan Efficiency Analysis (Task 2.0.3)
=============================================

Purpose:
    Evaluate the efficiency of Light/Moderate/Heavy subscription plans
    using Data Envelopment Analysis (DEA) with full LP formulation.

DMUs (Decision Making Units):
    - Light Plan: Low commitment, basic service
    - Moderate Plan: Balanced offering
    - Heavy Plan: Premium service, high commitment

Inputs (Resources Consumed):
    I1: Company cost per customer per year (₹)
    I2: Service visits allocated per year

Outputs (Value Produced):
    O1: Customer satisfaction score (0-100)
    O2: Annual revenue per customer (₹)
    O3: Expected retention rate at 12 months (%)

Method:
    CCR DEA Model (Charnes-Cooper-Rhodes)
    Output-oriented with Constant Returns to Scale (CRS)

Output:
    Efficiency scores, frontier identification, improvement targets
"""

import numpy as np
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .mcdm_utils import dea_efficiency, dea_efficiency_all


# =============================================================================
# Plan Data Definition
# =============================================================================

# Data derived from SESP pricing model and industry benchmarks
PLAN_DATA = {
    'Light': {
        'description': 'Entry-level plan for light AC users (120 hrs/month)',
        'monthly_fee': 499,
        'hours_included': 150,
        'target_segment': 'light',
        # Inputs
        'cost_per_customer': 8000,   # Annual: lower service commitment
        'service_visits': 2,          # Basic 2 visits/year
        # Outputs
        'satisfaction_score': 72,     # Lower due to limited service
        'annual_revenue': 5988,       # 499 × 12
        'retention_rate': 82,         # %: Some churn due to basic offering
    },
    'Moderate': {
        'description': 'Balanced plan for average users (200 hrs/month)',
        'monthly_fee': 649,
        'hours_included': 225,
        'target_segment': 'moderate',
        # Inputs
        'cost_per_customer': 10500,  # Annual: standard service
        'service_visits': 3,          # Standard 3 visits/year
        # Outputs
        'satisfaction_score': 81,     # Good satisfaction
        'annual_revenue': 7788,       # 649 × 12
        'retention_rate': 88,         # %: Solid retention
    },
    'Heavy': {
        'description': 'Premium plan for heavy users (320 hrs/month)',
        'monthly_fee': 899,
        'hours_included': 350,
        'target_segment': 'heavy',
        # Inputs
        'cost_per_customer': 14000,  # Annual: premium service
        'service_visits': 4,          # Premium 4 visits/year
        # Outputs
        'satisfaction_score': 88,     # High satisfaction
        'annual_revenue': 10788,      # 899 × 12
        'retention_rate': 92,         # %: Excellent retention
    }
}

# Input and Output labels
INPUT_LABELS = ['Cost/Customer (₹)', 'Service Visits']
OUTPUT_LABELS = ['Satisfaction', 'Revenue (₹)', 'Retention (%)']


# =============================================================================
# Data Extraction
# =============================================================================

def get_input_matrix() -> np.ndarray:
    """
    Extract input matrix from plan data.

    Returns:
        (3, 2) array: 3 DMUs × 2 inputs
    """
    inputs = []
    for plan_name in ['Light', 'Moderate', 'Heavy']:
        plan = PLAN_DATA[plan_name]
        inputs.append([
            plan['cost_per_customer'],
            plan['service_visits']
        ])
    return np.array(inputs)


def get_output_matrix() -> np.ndarray:
    """
    Extract output matrix from plan data.

    Returns:
        (3, 3) array: 3 DMUs × 3 outputs
    """
    outputs = []
    for plan_name in ['Light', 'Moderate', 'Heavy']:
        plan = PLAN_DATA[plan_name]
        outputs.append([
            plan['satisfaction_score'],
            plan['annual_revenue'],
            plan['retention_rate']
        ])
    return np.array(outputs)


def get_dmu_names() -> List[str]:
    """Get list of DMU names."""
    return ['Light', 'Moderate', 'Heavy']


# =============================================================================
# DEA Analysis
# =============================================================================

def run_dea_analysis(
    orientation: str = 'output',
    verbose: bool = True
) -> Dict:
    """
    Run complete DEA analysis for subscription plans.

    Args:
        orientation: 'output' (expand outputs) or 'input' (reduce inputs)
        verbose: If True, print detailed output

    Returns:
        Dict with:
        - efficiencies: Efficiency scores for each plan
        - frontier_plans: Plans on the efficient frontier
        - improvement_targets: Targets for inefficient plans
        - individual_results: Detailed DEA results per plan
    """
    inputs = get_input_matrix()
    outputs = get_output_matrix()
    dmu_names = get_dmu_names()

    # Run DEA for all DMUs
    result = dea_efficiency_all(
        inputs=inputs,
        outputs=outputs,
        dmu_names=dmu_names,
        orientation=orientation
    )

    # Add metadata
    result['inputs'] = inputs
    result['outputs'] = outputs
    result['input_labels'] = INPUT_LABELS
    result['output_labels'] = OUTPUT_LABELS
    result['plan_data'] = PLAN_DATA
    result['orientation'] = orientation

    if verbose:
        print_dea_report(result)

    return result


def get_efficiency_scores() -> Dict[str, float]:
    """
    Get efficiency scores as a labeled dictionary.

    Returns:
        Dict mapping plan names to efficiency scores
    """
    result = run_dea_analysis(verbose=False)
    return {
        name: float(eff)
        for name, eff in zip(get_dmu_names(), result['efficiencies'])
    }


def analyze_inefficiency(plan_name: str) -> Dict:
    """
    Analyze why a specific plan is inefficient (if applicable).

    Args:
        plan_name: Name of the plan to analyze

    Returns:
        Dict with inefficiency analysis
    """
    result = run_dea_analysis(verbose=False)
    dmu_names = get_dmu_names()

    if plan_name not in dmu_names:
        return {'error': f'Unknown plan: {plan_name}'}

    idx = dmu_names.index(plan_name)
    individual = result['results'][idx]

    if individual['is_efficient']:
        return {
            'plan': plan_name,
            'status': 'EFFICIENT',
            'message': f'{plan_name} is on the efficient frontier. No improvements needed.'
        }

    # Get improvement targets
    improvement = result['improvement_targets'].get(plan_name, {})

    # Identify peers (reference DMUs)
    peers = individual.get('peers', [])
    peer_names = [dmu_names[p] for p in peers]

    # Calculate specific recommendations
    current_outputs = result['outputs'][idx]
    if 'target_outputs' in improvement:
        target_outputs = improvement['target_outputs']
        output_gaps = np.array(target_outputs) - current_outputs

        recommendations = []
        for i, (label, gap) in enumerate(zip(OUTPUT_LABELS, output_gaps)):
            if gap > 0:
                pct_increase = (gap / current_outputs[i]) * 100
                recommendations.append({
                    'metric': label,
                    'current': current_outputs[i],
                    'target': target_outputs[i],
                    'gap': gap,
                    'increase_percent': pct_increase
                })
    else:
        recommendations = []

    return {
        'plan': plan_name,
        'status': 'INEFFICIENT',
        'efficiency_score': individual['efficiency'],
        'inefficiency_percent': (1 - individual['efficiency']) * 100,
        'reference_plans': peer_names,
        'recommendations': recommendations,
        'message': f'{plan_name} can improve outputs by {improvement.get("improvement_percent", 0):.1f}% to reach the frontier.'
    }


# =============================================================================
# Alternative Input-Output Specifications
# =============================================================================

def run_dea_with_custom_data(
    inputs: np.ndarray,
    outputs: np.ndarray,
    dmu_names: List[str],
    input_labels: List[str],
    output_labels: List[str],
    orientation: str = 'output',
    verbose: bool = True
) -> Dict:
    """
    Run DEA with custom input-output data.

    Useful for sensitivity analysis or alternative specifications.

    Args:
        inputs: (n_dmus, n_inputs) array
        outputs: (n_dmus, n_outputs) array
        dmu_names: Names for each DMU
        input_labels: Labels for inputs
        output_labels: Labels for outputs
        orientation: 'output' or 'input'
        verbose: If True, print output

    Returns:
        DEA results
    """
    result = dea_efficiency_all(inputs, outputs, dmu_names, orientation)

    result['inputs'] = inputs
    result['outputs'] = outputs
    result['input_labels'] = input_labels
    result['output_labels'] = output_labels
    result['orientation'] = orientation

    if verbose:
        print_dea_report(result)

    return result


def sensitivity_analysis_inputs() -> Dict:
    """
    Analyze how efficiency changes with different input specifications.

    Tests:
    1. Base case (cost + visits)
    2. Cost only
    3. Visits only

    Returns:
        Dict with sensitivity results
    """
    outputs = get_output_matrix()
    dmu_names = get_dmu_names()

    results = {}

    # Base case: Cost + Visits
    inputs_base = get_input_matrix()
    result_base = dea_efficiency_all(inputs_base, outputs, dmu_names, 'output')
    results['base'] = {
        'inputs': 'Cost + Visits',
        'efficiencies': result_base['efficiencies'].tolist(),
        'frontier': result_base['frontier_names']
    }

    # Cost only
    inputs_cost = inputs_base[:, 0:1]
    result_cost = dea_efficiency_all(inputs_cost, outputs, dmu_names, 'output')
    results['cost_only'] = {
        'inputs': 'Cost only',
        'efficiencies': result_cost['efficiencies'].tolist(),
        'frontier': result_cost['frontier_names']
    }

    # Visits only
    inputs_visits = inputs_base[:, 1:2]
    result_visits = dea_efficiency_all(inputs_visits, outputs, dmu_names, 'output')
    results['visits_only'] = {
        'inputs': 'Visits only',
        'efficiencies': result_visits['efficiencies'].tolist(),
        'frontier': result_visits['frontier_names']
    }

    return results


# =============================================================================
# Reporting
# =============================================================================

def print_dea_report(result: Dict) -> None:
    """Print formatted DEA analysis report."""
    print("\n" + "=" * 70)
    print("DEA ANALYSIS: Subscription Plan Efficiency")
    print("=" * 70)

    print("\n## Plan Overview")
    for plan_name, plan in PLAN_DATA.items():
        print(f"  {plan_name}: {plan['description']}")
        print(f"    Fee: ₹{plan['monthly_fee']} | Hours: {plan['hours_included']}")

    print("\n## Input-Output Specification")
    print("  INPUTS (resources consumed):")
    for label in result['input_labels']:
        print(f"    - {label}")
    print("  OUTPUTS (value produced):")
    for label in result['output_labels']:
        print(f"    - {label}")

    print("\n## Data Matrix")
    dmu_names = get_dmu_names()

    # Inputs
    print("\n  INPUTS:")
    print(f"    {'Plan':<12s} | " + " | ".join(f"{l:>15s}" for l in result['input_labels']))
    print("    " + "-" * 50)
    for i, name in enumerate(dmu_names):
        row = f"    {name:<12s} | "
        row += " | ".join(f"{result['inputs'][i, j]:>15,.0f}" for j in range(result['inputs'].shape[1]))
        print(row)

    # Outputs
    print("\n  OUTPUTS:")
    print(f"    {'Plan':<12s} | " + " | ".join(f"{l:>15s}" for l in result['output_labels']))
    print("    " + "-" * 60)
    for i, name in enumerate(dmu_names):
        row = f"    {name:<12s} | "
        row += " | ".join(f"{result['outputs'][i, j]:>15,.0f}" for j in range(result['outputs'].shape[1]))
        print(row)

    print("\n## Efficiency Scores")
    print(f"  Orientation: {result['orientation']}-oriented")
    print(f"  Model: CCR (Constant Returns to Scale)")
    print()

    for i, (name, eff) in enumerate(zip(dmu_names, result['efficiencies'])):
        is_efficient = np.isclose(eff, 1.0, atol=1e-6)
        status = "✅ ON FRONTIER" if is_efficient else f"❌ {(1-eff)*100:.1f}% below frontier"
        print(f"    {name:<12s}: θ = {eff:.4f}  {status}")

    print(f"\n## Efficient Frontier")
    print(f"  Plans on frontier: {', '.join(result['frontier_names'])}")

    if result['improvement_targets']:
        print("\n## Improvement Targets")
        for plan_name, targets in result['improvement_targets'].items():
            print(f"\n  {plan_name}:")
            if 'target_outputs' in targets:
                print(f"    Can increase outputs by {targets['improvement_percent']:.1f}%")
                for j, label in enumerate(result['output_labels']):
                    current = targets['current_outputs'][j]
                    target = targets['target_outputs'][j]
                    improvement = targets['improvement_needed'][j]
                    print(f"      {label}: {current:,.0f} → {target:,.0f} (+{improvement:,.0f})")

    print("\n## Strategic Interpretation")
    efficiencies = result['efficiencies']
    if np.all(np.isclose(efficiencies, 1.0, atol=1e-6)):
        print("  All plans are on the efficient frontier.")
        print("  This suggests well-balanced pricing across tiers.")
    else:
        inefficient = [dmu_names[i] for i, e in enumerate(efficiencies) if not np.isclose(e, 1.0, atol=1e-6)]
        print(f"  Inefficient plans: {', '.join(inefficient)}")
        print("  Consider:")
        for plan in inefficient:
            analysis = analyze_inefficiency(plan)
            if analysis['recommendations']:
                print(f"    {plan}: Focus on improving {analysis['recommendations'][0]['metric']}")

    print("\n" + "=" * 70)


def generate_dea_report_section() -> str:
    """Generate markdown content for the MCDM Analysis Report section."""
    result = run_dea_analysis(verbose=False)
    dmu_names = get_dmu_names()

    md = []
    md.append("## 7.3 DEA for Plan Efficiency Analysis\n")

    md.append("### Input-Output Specification\n")
    md.append("**Inputs (resources consumed):**\n")
    for label in INPUT_LABELS:
        md.append(f"- {label}\n")
    md.append("\n**Outputs (value produced):**\n")
    for label in OUTPUT_LABELS:
        md.append(f"- {label}\n")

    md.append("\n### Data Matrix\n")
    md.append("| Plan | " + " | ".join(INPUT_LABELS) + " | " + " | ".join(OUTPUT_LABELS) + " |\n")
    md.append("|---|" + "|".join(["---"] * (len(INPUT_LABELS) + len(OUTPUT_LABELS))) + "|\n")
    for i, name in enumerate(dmu_names):
        row = f"| {name} |"
        for j in range(result['inputs'].shape[1]):
            row += f" {result['inputs'][i, j]:,.0f} |"
        for j in range(result['outputs'].shape[1]):
            row += f" {result['outputs'][i, j]:,.0f} |"
        md.append(row + "\n")

    md.append("\n### Efficiency Scores\n")
    md.append("| Plan | Efficiency | Status |\n")
    md.append("|---|---|---|\n")
    for name, eff in zip(dmu_names, result['efficiencies']):
        is_eff = np.isclose(eff, 1.0, atol=1e-6)
        status = "On Frontier" if is_eff else f"{(1-eff)*100:.1f}% below"
        md.append(f"| {name} | {eff:.4f} | {status} |\n")

    md.append(f"\n### Efficient Frontier\n")
    md.append(f"Plans on frontier: **{', '.join(result['frontier_names'])}**\n")

    if result['improvement_targets']:
        md.append("\n### Improvement Targets\n")
        for plan_name, targets in result['improvement_targets'].items():
            md.append(f"\n**{plan_name}** (can improve by {targets.get('improvement_percent', 0):.1f}%):\n")
            if 'target_outputs' in targets:
                for j, label in enumerate(OUTPUT_LABELS):
                    current = targets['current_outputs'][j]
                    target = targets['target_outputs'][j]
                    md.append(f"- {label}: {current:,.0f} → {target:,.0f}\n")

    return "".join(md)


if __name__ == "__main__":
    # Run analysis
    result = run_dea_analysis(verbose=True)

    # Analyze inefficient plans
    print("\n\n## Detailed Inefficiency Analysis")
    for name in get_dmu_names():
        analysis = analyze_inefficiency(name)
        print(f"\n{name}: {analysis['status']}")
        if analysis['status'] == 'INEFFICIENT':
            print(f"  Efficiency: {analysis['efficiency_score']:.4f}")
            print(f"  Reference plans: {analysis['reference_plans']}")
            for rec in analysis['recommendations']:
                print(f"  → {rec['metric']}: {rec['current']:.0f} → {rec['target']:.0f} (+{rec['increase_percent']:.1f}%)")

    # Sensitivity analysis
    print("\n\n## Sensitivity Analysis (Input Specifications)")
    sensitivity = sensitivity_analysis_inputs()
    for spec, data in sensitivity.items():
        print(f"  {data['inputs']:20s}: Frontier = {data['frontier']}")
