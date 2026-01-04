#!/usr/bin/env python
"""
SESP Simulation Demo Script
===========================

Runs the full simulation pipeline:
1. Generates 1000 synthetic customers
2. Simulates 60-month customer journeys (vectorized)
3. Aggregates results by customer, segment, month, and portfolio
4. Generates all 8 presentation-ready charts
5. Exports data to CSV files
6. Prints comprehensive summary report

Usage:
    python run_simulation.py

Output:
    - data/customers.csv
    - data/simulation_full_grid.csv
    - data/simulation_by_*.csv
    - outputs/charts/*.png
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Imports
from src.simulation import (
    generate_customers,
    simulate_portfolio,
    aggregate_by_customer,
    aggregate_by_segment,
    aggregate_by_month,
    aggregate_portfolio,
    calculate_simulation_summary,
)
from src.simulation.aggregator import export_results
from src.visualization import create_all_charts


def main():
    print("=" * 70)
    print("SESP SIMULATION DEMO")
    print("=" * 70)
    print()

    # Configuration
    N_CUSTOMERS = 1000
    TENURE_MONTHS = 60
    RANDOM_SEED = 42
    OUTPUT_DIR = 'outputs/charts'
    DATA_DIR = 'data'

    # Cost parameters (from Phase 3c)
    params = {
        'subsidy_percent': 0.50,
        'mrp': 45000,
        'manufacturing_cost': 30000,
        'iot_cost': 1500,
        'installation_cost': 2500,
        'cac': 2000,
        'bank_cac_subsidy': 2000,
        'warranty_reserve': 2000,
        'monthly_recurring_cost': 192,
        # For visualization
        'upfront_deficit_per_customer': 16932,
    }

    # Step 1: Generate customers
    print(f"Step 1: Generating {N_CUSTOMERS} synthetic customers...")
    start = time.time()
    customers = generate_customers(N_CUSTOMERS, random_seed=RANDOM_SEED)
    print(f"   Done in {time.time() - start:.2f}s")
    print(f"   Shape: {customers.shape}")
    print()

    # Step 2: Run simulation
    print(f"Step 2: Running {TENURE_MONTHS}-month simulation (vectorized)...")
    start = time.time()
    grid = simulate_portfolio(customers, tenure_months=TENURE_MONTHS, random_seed=RANDOM_SEED)
    elapsed = time.time() - start
    print(f"   Done in {elapsed:.2f}s")
    print(f"   Grid shape: {grid.shape} ({len(grid):,} rows)")
    print(f"   Performance: {len(grid) / elapsed:,.0f} rows/second")
    print()

    # Step 3: Generate aggregations
    print("Step 3: Aggregating results...")
    by_customer = aggregate_by_customer(grid)
    by_segment = aggregate_by_segment(grid)
    by_month = aggregate_by_month(grid)
    portfolio = aggregate_portfolio(grid, params)
    print(f"   By customer: {len(by_customer)} rows")
    print(f"   By segment: {len(by_segment)} rows")
    print(f"   By month: {len(by_month)} rows")
    print()

    # Step 4: Export to CSV
    print(f"Step 4: Exporting data to {DATA_DIR}/...")
    # Save customers
    customers.to_csv(f'{DATA_DIR}/customers.csv', index=False)
    print(f"   - customers.csv")

    # Save simulation results
    files = export_results(grid, DATA_DIR)
    for name, path in files.items():
        print(f"   - {Path(path).name}")
    print()

    # Step 5: Generate charts
    print(f"Step 5: Generating charts to {OUTPUT_DIR}/...")
    chart_paths = create_all_charts(grid, output_dir=OUTPUT_DIR, params=params, show=False)
    print()

    # Step 6: Print summary report
    print("Step 6: Summary Report")
    print(calculate_simulation_summary(grid, params))
    print()

    # Final statistics
    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print(f"Customers simulated: {N_CUSTOMERS:,}")
    print(f"Customer-months: {len(grid):,}")
    print(f"Charts generated: {len(chart_paths)}")
    print(f"CSV files: 6")
    print()
    print("Key Results:")
    print(f"   Portfolio Margin: Rs{portfolio['margin_per_customer']:,.0f} per customer")
    print(f"   Total Portfolio Margin: Rs{portfolio['total_portfolio_margin']:,.0f}")
    print(f"   Margin %: {portfolio['margin_percent']:.1f}%")
    print()


if __name__ == "__main__":
    main()
