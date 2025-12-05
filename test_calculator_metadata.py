#!/usr/bin/env python3
"""
Test that all indicator calculators have get_chart_config() methods
and return correct metadata.
"""

from shared.indicators import (
    VWAPCalculator,
    SMACalculator,
    EMACalculator,
    RSICalculator,
    MACDCalculator
)
from shared.indicators_metadata import IndicatorType, ScaleType


def test_vwap_calculator_metadata():
    """Test VWAPCalculator has get_chart_config() and returns correct metadata."""
    calc = VWAPCalculator()
    metadata = calc.get_chart_config()
    
    assert metadata is not None, "VWAP metadata should not be None"
    assert metadata.name == "VWAP", f"Expected name 'VWAP', got '{metadata.name}'"
    assert metadata.indicator_type == IndicatorType.OVERLAY, "VWAP should be OVERLAY type"
    assert metadata.scale_type == ScaleType.PRICE, "VWAP should use PRICE scale"
    print("✓ VWAPCalculator.get_chart_config() works correctly")


def test_sma_calculator_metadata():
    """Test SMACalculator has get_chart_config() and returns correct metadata."""
    calc = SMACalculator(20)
    metadata = calc.get_chart_config()
    
    assert metadata is not None, "SMA metadata should not be None"
    assert metadata.name == "SMA", f"Expected name 'SMA', got '{metadata.name}'"
    assert metadata.indicator_type == IndicatorType.OVERLAY, "SMA should be OVERLAY type"
    assert metadata.scale_type == ScaleType.PRICE, "SMA should use PRICE scale"
    print("✓ SMACalculator.get_chart_config() works correctly")


def test_ema_calculator_metadata():
    """Test EMACalculator has get_chart_config() and returns correct metadata."""
    calc = EMACalculator(20)
    metadata = calc.get_chart_config()
    
    assert metadata is not None, "EMA metadata should not be None"
    assert metadata.name == "EMA", f"Expected name 'EMA', got '{metadata.name}'"
    assert metadata.indicator_type == IndicatorType.OVERLAY, "EMA should be OVERLAY type"
    assert metadata.scale_type == ScaleType.PRICE, "EMA should use PRICE scale"
    print("✓ EMACalculator.get_chart_config() works correctly")


def test_rsi_calculator_metadata():
    """Test RSICalculator has get_chart_config() and returns correct metadata."""
    calc = RSICalculator(14)
    metadata = calc.get_chart_config()
    
    assert metadata is not None, "RSI metadata should not be None"
    assert metadata.name == "RSI", f"Expected name 'RSI', got '{metadata.name}'"
    assert metadata.indicator_type == IndicatorType.OSCILLATOR, "RSI should be OSCILLATOR type"
    assert metadata.scale_type == ScaleType.FIXED, "RSI should use FIXED scale"
    assert metadata.scale_min == 0, "RSI scale_min should be 0"
    assert metadata.scale_max == 100, "RSI scale_max should be 100"
    assert len(metadata.reference_lines) == 2, "RSI should have 2 reference lines"
    print("✓ RSICalculator.get_chart_config() works correctly")


def test_macd_calculator_metadata():
    """Test MACDCalculator has get_chart_config() and returns correct metadata."""
    calc = MACDCalculator(12, 26, 9)
    metadata = calc.get_chart_config()
    
    assert metadata is not None, "MACD metadata should not be None"
    assert metadata.name == "MACD", f"Expected name 'MACD', got '{metadata.name}'"
    assert metadata.indicator_type == IndicatorType.OSCILLATOR, "MACD should be OSCILLATOR type"
    assert metadata.scale_type == ScaleType.AUTO, "MACD should use AUTO scale"
    assert metadata.zero_line == True, "MACD should have zero line"
    assert len(metadata.components) == 3, "MACD should have 3 components (macd, signal, histogram)"
    print("✓ MACDCalculator.get_chart_config() works correctly")


if __name__ == "__main__":
    print("Testing indicator calculator metadata methods...\n")
    
    test_vwap_calculator_metadata()
    test_sma_calculator_metadata()
    test_ema_calculator_metadata()
    test_rsi_calculator_metadata()
    test_macd_calculator_metadata()
    
    print("\n✅ All calculator metadata tests passed!")
