#!/usr/bin/env python3
"""
Test that calculator metadata matches registry metadata.
This validates Requirement 7.5.
"""

from shared.indicators import (
    VWAPCalculator,
    SMACalculator,
    EMACalculator,
    RSICalculator,
    MACDCalculator
)
from shared.indicators_metadata import metadata_registry


def test_calculator_metadata_matches_registry():
    """Test that calculator metadata matches registry metadata."""
    
    calculators = [
        ("VWAP", VWAPCalculator()),
        ("SMA", SMACalculator(20)),
        ("EMA", EMACalculator(20)),
        ("RSI", RSICalculator(14)),
        ("MACD", MACDCalculator(12, 26, 9))
    ]
    
    for base_name, calculator in calculators:
        calc_metadata = calculator.get_chart_config()
        registry_metadata = metadata_registry.get(base_name)
        
        # Both should return the same object (or at least equivalent data)
        assert calc_metadata is not None, f"{base_name}: Calculator metadata is None"
        assert registry_metadata is not None, f"{base_name}: Registry metadata is None"
        
        # Check that they're the same object or have the same values
        assert calc_metadata.name == registry_metadata.name, \
            f"{base_name}: Name mismatch - calc: {calc_metadata.name}, registry: {registry_metadata.name}"
        
        assert calc_metadata.indicator_type == registry_metadata.indicator_type, \
            f"{base_name}: Type mismatch - calc: {calc_metadata.indicator_type}, registry: {registry_metadata.indicator_type}"
        
        assert calc_metadata.scale_type == registry_metadata.scale_type, \
            f"{base_name}: Scale type mismatch - calc: {calc_metadata.scale_type}, registry: {registry_metadata.scale_type}"
        
        print(f"✓ {base_name}: Calculator metadata matches registry metadata")
    
    print("\n✅ All calculators return metadata consistent with registry!")


if __name__ == "__main__":
    print("Testing calculator-registry metadata consistency...\n")
    test_calculator_metadata_matches_registry()
