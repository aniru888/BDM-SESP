"""
SESP Model — Smart Energy-Saver Subscription Program
====================================================

A pricing simulation and optimization model for IoT-enabled
home appliances (AC and Refrigerator) in India.

Key Components:
- pricing: Bucket-based subscription model (hours, not kWh)
- adjustments: India-specific adjustments (seasonality, GST, NPV)
- alternatives: Cost calculators for purchase/EMI/rental/SESP
- constraints: Participation and Incentive Compatibility checkers

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "SESP Team"
