"""
Configuration Loader
====================

Loads JSON configuration files from SESP_Claude_Instructions/config/.

Config Files:
- appliances.json: AC and Fridge specifications, costs, seasonality
- customer_segments.json: Segment definitions, discount rates, behaviors
- market_params.json: Electricity rates, competitor pricing, CAC
- pricing_formula_PATCHED.json: V2 bucket model pricing (CORRECT version)
- decision_variables.json: Optimization parameter ranges
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Resolve config directory relative to this file
_THIS_DIR = Path(__file__).parent
_PROJECT_ROOT = _THIS_DIR.parent.parent  # BDM folder
_CONFIG_DIR = _PROJECT_ROOT / "SESP_Claude_Instructions" / "config"


def load_config(filename: str) -> Dict[str, Any]:
    """
    Load a JSON configuration file.

    Args:
        filename: Name of the JSON file (e.g., 'appliances.json')

    Returns:
        Dictionary containing the configuration data.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    filepath = _CONFIG_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(
            f"Config file not found: {filepath}\n"
            f"Expected location: {_CONFIG_DIR}"
        )

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# Cached configs (loaded once)
_cache: Dict[str, Any] = {}


def _get_cached(filename: str) -> Dict[str, Any]:
    """Get config from cache, loading if needed."""
    if filename not in _cache:
        _cache[filename] = load_config(filename)
    return _cache[filename]


def get_appliance_config(appliance: str = "AC_1.5T_5STAR_INVERTER") -> Dict[str, Any]:
    """
    Get appliance specifications.

    Args:
        appliance: Either 'AC_1.5T_5STAR_INVERTER' or 'FRIDGE_280L_FROST_FREE'

    Returns:
        Dictionary with MRP, costs, seasonality, baselines, terminal values.
    """
    config = _get_cached("appliances.json")

    if appliance not in config:
        raise ValueError(
            f"Unknown appliance: {appliance}. "
            f"Available: {list(config.keys())}"
        )

    return config[appliance]


def get_segment_config(segment: str = "moderate") -> Dict[str, Any]:
    """
    Get customer segment configuration.

    Args:
        segment: 'light', 'moderate', or 'heavy'

    Returns:
        Dictionary with proportion, usage behavior, discount rate, churn/default risk.
    """
    config = _get_cached("customer_segments.json")
    segments = config.get("usage_segments", {})

    if segment not in segments:
        raise ValueError(
            f"Unknown segment: {segment}. "
            f"Available: {list(segments.keys())}"
        )

    return segments[segment]


def get_all_segments() -> Dict[str, Any]:
    """Get all customer segment configurations."""
    config = _get_cached("customer_segments.json")
    return config.get("usage_segments", {})


def get_market_params() -> Dict[str, Any]:
    """
    Get market parameters.

    Returns:
        Dictionary with electricity rates, competitor pricing, CAC, referral rates.
    """
    return _get_cached("market_params.json")


def get_pricing_config() -> Dict[str, Any]:
    """
    Get V2 pricing configuration (PATCHED version).

    Returns:
        Dictionary with subscription plans, efficiency score, overage mechanism.

    Important:
        This returns the CORRECTED bucket model pricing, not the old kWh-based model.
    """
    return _get_cached("pricing_formula_PATCHED.json")


def get_decision_variables() -> Dict[str, Any]:
    """
    Get decision variable ranges for optimization.

    Returns:
        Dictionary with min/max/step for subsidy, fee, tenure, deposit, etc.
    """
    return _get_cached("decision_variables.json")


def get_seasonality(region: str = "north", appliance: str = "AC") -> list:
    """
    Get monthly seasonality indices for an appliance in a region.

    Args:
        region: 'north', 'south', 'west', or 'east'
        appliance: 'AC' or 'FRIDGE'

    Returns:
        List of 12 monthly multipliers (Jan=index 0, Dec=index 11).

    Example:
        >>> get_seasonality('north', 'AC')
        [0.05, 0.15, 0.60, 1.40, 1.70, 1.30, 0.80, 0.70, 0.80, 0.50, 0.15, 0.05]
    """
    if appliance.upper() == "AC":
        config = get_appliance_config("AC_1.5T_5STAR_INVERTER")
        seasonality_data = config.get("seasonality", {})

        region_key = region.lower()
        if region_key not in seasonality_data:
            raise ValueError(
                f"Unknown region: {region}. "
                f"Available: {list(seasonality_data.keys())}"
            )

        return seasonality_data[region_key]

    elif appliance.upper() == "FRIDGE":
        # Fridge has minimal seasonality
        config = get_appliance_config("FRIDGE_280L_FROST_FREE")
        return config.get("seasonality", [1.0] * 12)

    else:
        raise ValueError(f"Unknown appliance: {appliance}. Use 'AC' or 'FRIDGE'.")


def get_discount_rate(segment: str = "moderate", entity: str = "customer") -> float:
    """
    Get discount rate for NPV calculations.

    Args:
        segment: Customer segment ('light', 'moderate', 'heavy')
        entity: 'customer' or 'firm'

    Returns:
        Annual discount rate as decimal (e.g., 0.22 for 22%).
    """
    if entity.lower() == "firm":
        config = _get_cached("customer_segments.json")
        return config.get("firm_discount_rate", 0.12)

    segment_config = get_segment_config(segment)
    return segment_config.get("discount_rate", 0.22)


def get_terminal_value(appliance: str, tenure_years: int) -> float:
    """
    Get terminal (resale) value for an appliance at end of tenure.

    Args:
        appliance: 'AC' or 'FRIDGE'
        tenure_years: Number of years

    Returns:
        Terminal value in INR.
    """
    if appliance.upper() == "AC":
        config = get_appliance_config("AC_1.5T_5STAR_INVERTER")
    elif appliance.upper() == "FRIDGE":
        config = get_appliance_config("FRIDGE_280L_FROST_FREE")
    else:
        raise ValueError(f"Unknown appliance: {appliance}")

    terminal_values = config.get("terminal_value", {})

    # Find closest year <= tenure_years
    year_key = f"year_{tenure_years}"
    if year_key in terminal_values:
        return terminal_values[year_key]

    # Find the closest available year
    available_years = sorted([int(k.split('_')[1]) for k in terminal_values.keys()])
    for year in reversed(available_years):
        if year <= tenure_years:
            return terminal_values[f"year_{year}"]

    # If tenure is shorter than minimum, use highest value
    if available_years:
        return terminal_values[f"year_{available_years[0]}"]

    return 0.0


# Convenience: GST rate (constant)
GST_RATE = 0.18


if __name__ == "__main__":
    # Quick test
    print("Testing config loader...")

    print(f"\nAppliance config keys: {list(get_appliance_config().keys())}")
    print(f"Segment config keys: {list(get_segment_config().keys())}")
    print(f"Market params keys: {list(get_market_params().keys())}")
    print(f"Pricing config keys: {list(get_pricing_config().keys())}")

    print(f"\nNorth India AC seasonality: {get_seasonality('north', 'AC')}")
    print(f"Customer discount rate (moderate): {get_discount_rate('moderate', 'customer')}")
    print(f"Firm discount rate: {get_discount_rate('moderate', 'firm')}")
    print(f"AC terminal value (5 years): {get_terminal_value('AC', 5)}")

    print("\n✓ Config loader working correctly!")
