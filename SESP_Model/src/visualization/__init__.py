"""
Visualization Module
===================

Creates presentation-ready charts for SESP simulation results.

Required Charts:
1. Usage distribution by segment (histogram)
2. Monthly bill distribution (histogram)
3. Efficiency score vs discount (scatter)
4. Monthly cash flow (line)
5. Cumulative profit (line)
6. Segment comparison (grouped bar)
7. Seasonality impact (line)
8. Before vs After waterfall (waterfall)

Usage:
    from src.visualization import create_all_charts
    paths = create_all_charts(grid, output_dir='outputs/charts')
"""

from .charts import (
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

__all__ = [
    'create_all_charts',
    'plot_usage_distribution',
    'plot_bill_distribution',
    'plot_efficiency_vs_discount',
    'plot_monthly_cashflow',
    'plot_cumulative_profit',
    'plot_segment_comparison',
    'plot_seasonality_impact',
    'plot_margin_waterfall',
    'set_presentation_style',
]
