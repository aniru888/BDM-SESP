"""
Tests for visualization module.

Tests chart generation functions to ensure they:
1. Can be called without error
2. Return valid matplotlib figure objects
3. Handle edge cases properly
"""

import pytest
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt
import tempfile
import os


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_grid():
    """Create a small sample simulation grid for testing."""
    from src.simulation.data_generator import generate_customers
    from src.simulation.simulator import simulate_portfolio

    customers = generate_customers(100, random_seed=42)
    grid = simulate_portfolio(customers, tenure_months=12, random_seed=42)
    return grid


@pytest.fixture
def sample_params():
    """Default cost parameters for visualization functions."""
    # These match what the chart functions expect
    return {
        'upfront_deficit_per_customer': 16932,  # From Phase 3c
        'monthly_recurring_cost': 192,
        'bank_cac_subsidy': 2000,
        # For aggregator compatibility
        'subsidy_percent': 0.50,
        'mrp': 45000,
        'manufacturing_cost': 30000,
        'iot_cost': 1500,
        'installation_cost': 2500,
        'cac': 2000,
        'warranty_reserve': 2000,
    }


# =============================================================================
# TEST IMPORTS
# =============================================================================

class TestVisualizationImports:
    """Test that visualization module imports correctly."""

    def test_import_visualization_module(self):
        """Can import visualization module."""
        from src import visualization
        assert hasattr(visualization, 'create_all_charts')

    def test_import_all_chart_functions(self):
        """All chart functions are exported."""
        from src.visualization import (
            create_all_charts,
            plot_usage_distribution,
            plot_bill_distribution,
            plot_efficiency_vs_discount,
            plot_monthly_cashflow,
            plot_cumulative_profit,
            plot_segment_comparison,
            plot_seasonality_impact,
            plot_margin_waterfall,
            set_presentation_style,
        )
        assert callable(create_all_charts)
        assert callable(plot_usage_distribution)
        assert callable(plot_bill_distribution)


# =============================================================================
# TEST INDIVIDUAL CHART FUNCTIONS
# =============================================================================

class TestUsageDistribution:
    """Test plot_usage_distribution function."""

    def test_returns_figure(self, sample_grid):
        """Returns a matplotlib figure."""
        from src.visualization import plot_usage_distribution

        fig = plot_usage_distribution(sample_grid)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_handles_small_dataset(self):
        """Works with minimal data."""
        from src.visualization import plot_usage_distribution

        # Minimal valid grid
        grid = pd.DataFrame({
            'segment': ['light', 'moderate', 'heavy'] * 10,
            'actual_hours': np.random.uniform(50, 300, 30),
        })

        fig = plot_usage_distribution(grid)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestBillDistribution:
    """Test plot_bill_distribution function."""

    def test_returns_figure(self, sample_grid):
        """Returns a matplotlib figure."""
        from src.visualization import plot_bill_distribution

        fig = plot_bill_distribution(sample_grid)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestEfficiencyVsDiscount:
    """Test plot_efficiency_vs_discount function."""

    def test_returns_figure(self, sample_grid):
        """Returns a matplotlib figure."""
        from src.visualization import plot_efficiency_vs_discount

        fig = plot_efficiency_vs_discount(sample_grid)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestMonthlyCashflow:
    """Test plot_monthly_cashflow function."""

    def test_returns_figure(self, sample_grid):
        """Returns a matplotlib figure."""
        from src.visualization import plot_monthly_cashflow

        fig = plot_monthly_cashflow(sample_grid)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestCumulativeProfit:
    """Test plot_cumulative_profit function."""

    def test_returns_figure(self, sample_grid, sample_params):
        """Returns a matplotlib figure."""
        from src.visualization import plot_cumulative_profit

        fig = plot_cumulative_profit(sample_grid, sample_params)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestSegmentComparison:
    """Test plot_segment_comparison function."""

    def test_returns_figure(self, sample_grid):
        """Returns a matplotlib figure."""
        from src.visualization import plot_segment_comparison

        fig = plot_segment_comparison(sample_grid)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestSeasonalityImpact:
    """Test plot_seasonality_impact function."""

    def test_returns_figure(self, sample_grid):
        """Returns a matplotlib figure."""
        from src.visualization import plot_seasonality_impact

        fig = plot_seasonality_impact(sample_grid)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestMarginWaterfall:
    """Test plot_margin_waterfall function."""

    def test_returns_figure(self, sample_grid, sample_params):
        """Returns a matplotlib figure."""
        from src.visualization import plot_margin_waterfall

        # plot_margin_waterfall takes grid and params
        fig = plot_margin_waterfall(sample_grid, sample_params)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


# =============================================================================
# TEST CREATE_ALL_CHARTS
# =============================================================================

class TestCreateAllCharts:
    """Test the master create_all_charts function."""

    def test_returns_dict_of_paths(self, sample_grid, sample_params):
        """Returns dictionary of file paths."""
        from src.visualization import create_all_charts

        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_all_charts(
                sample_grid,
                output_dir=tmpdir,
                params=sample_params,
                show=False
            )

            assert isinstance(result, dict)
            assert len(result) == 8  # 8 charts
            for key, path in result.items():
                assert isinstance(path, str), f"Chart {key} path is not a string"
                assert os.path.exists(path), f"Chart {key} file does not exist: {path}"

    def test_saves_to_directory(self, sample_grid, sample_params):
        """Saves chart files when output_dir is provided."""
        from src.visualization import create_all_charts

        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_all_charts(
                sample_grid,
                output_dir=tmpdir,
                params=sample_params,
                show=False
            )

            # Should return paths
            assert isinstance(result, dict)

            # Check files were created
            files = os.listdir(tmpdir)
            assert len(files) == 8, f"Expected 8 chart files, got {len(files)}: {files}"

            # All should be PNG files
            for f in files:
                assert f.endswith('.png'), f"Expected PNG file: {f}"

    def test_chart_filenames_meaningful(self, sample_grid, sample_params):
        """Chart filenames are descriptive."""
        from src.visualization import create_all_charts

        with tempfile.TemporaryDirectory() as tmpdir:
            create_all_charts(
                sample_grid,
                output_dir=tmpdir,
                params=sample_params,
                show=False
            )

            files = os.listdir(tmpdir)
            expected_patterns = [
                'usage', 'bill', 'efficiency', 'cashflow',
                'profit', 'segment', 'seasonal', 'waterfall'
            ]

            for pattern in expected_patterns:
                matching = [f for f in files if pattern in f.lower()]
                assert len(matching) >= 1, f"No file matching '{pattern}' pattern"


# =============================================================================
# TEST PRESENTATION STYLE
# =============================================================================

class TestPresentationStyle:
    """Test set_presentation_style function."""

    def test_sets_style(self):
        """Style function executes without error."""
        from src.visualization import set_presentation_style

        # Should not raise
        set_presentation_style()

    def test_style_affects_figure(self, sample_grid):
        """Style is applied to generated figures."""
        from src.visualization import set_presentation_style, plot_usage_distribution

        set_presentation_style()
        fig = plot_usage_distribution(sample_grid)

        # Check figure has reasonable size (presentation-ready)
        width, height = fig.get_size_inches()
        assert width >= 8, f"Figure width too small: {width}"
        assert height >= 5, f"Figure height too small: {height}"

        plt.close(fig)


# =============================================================================
# TEST EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_grid_raises_error(self):
        """Empty grid raises appropriate error."""
        from src.visualization import plot_usage_distribution

        empty_grid = pd.DataFrame()

        with pytest.raises(Exception):  # Can be KeyError, ValueError, etc.
            plot_usage_distribution(empty_grid)

    def test_single_segment_works(self, sample_grid):
        """Works with filtered data (e.g., single segment)."""
        from src.visualization import plot_usage_distribution

        # Filter to single segment from real grid
        single_segment = sample_grid[sample_grid['segment'] == 'moderate'].copy()

        # Should work with subset of data
        fig = plot_usage_distribution(single_segment)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_works_with_one_month(self):
        """Works with single month of data."""
        from src.simulation.data_generator import generate_customers
        from src.simulation.simulator import simulate_portfolio
        from src.visualization import plot_monthly_cashflow

        customers = generate_customers(50, random_seed=42)
        grid = simulate_portfolio(customers, tenure_months=1, random_seed=42)

        # Should work even with 1 month
        fig = plot_monthly_cashflow(grid)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
