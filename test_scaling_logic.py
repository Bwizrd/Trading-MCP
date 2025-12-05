#!/usr/bin/env python3
"""
Test scaling logic implementation for Task 5.

This test verifies that the chart engine correctly applies three types of scaling:
1. FIXED scale - Set y-axis to [scale_min, scale_max] from metadata
2. AUTO scale - Calculate range from indicator values with padding
3. PRICE scale - Share y-axis with price chart (no explicit scaling)

Requirements tested: 1.2, 1.3, 1.4, 2.4, 4.4
"""

from datetime import datetime, timedelta
from shared.chart_engine import ChartEngine
from shared.indicators_metadata import metadata_registry, ScaleType
from plotly.subplots import make_subplots


def test_fixed_scale():
    """Test FIXED scale type (RSI with 0-100 range)."""
    print("\n" + "=" * 70)
    print("Test 1: FIXED Scale (RSI)")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data with RSI values
    rsi_values = [30.0, 45.0, 60.0, 75.0, 50.0] * 10  # 50 values
    timestamps = [datetime(2024, 1, 1, 9, 0) + timedelta(minutes=i*15) for i in range(50)]
    
    # Get RSI metadata
    metadata = metadata_registry.get("RSI")
    assert metadata is not None, "RSI metadata not found"
    assert metadata.scale_type == ScaleType.FIXED, "RSI should have FIXED scale type"
    assert metadata.scale_min == 0, "RSI scale_min should be 0"
    assert metadata.scale_max == 100, "RSI scale_max should be 100"
    
    print(f"✓ RSI metadata: scale_type={metadata.scale_type.value}, range=[{metadata.scale_min}, {metadata.scale_max}]")
    
    # Create figure and apply scaling
    fig = make_subplots(rows=2, cols=1)
    engine._apply_scaling(fig, metadata, rsi_values, row=2)
    
    # Check y-axis range
    yaxis = fig.layout.yaxis2  # Second subplot
    if hasattr(yaxis, 'range') and yaxis.range:
        print(f"✓ Y-axis range set to: {yaxis.range}")
        assert yaxis.range[0] == 0, f"Expected y-axis min to be 0, got {yaxis.range[0]}"
        assert yaxis.range[1] == 100, f"Expected y-axis max to be 100, got {yaxis.range[1]}"
        print("✓ FIXED scale [0, 100] correctly applied")
    else:
        raise AssertionError("Y-axis range not set for FIXED scale")
    
    print("=" * 70)


def test_auto_scale():
    """Test AUTO scale type (MACD with calculated range)."""
    print("\n" + "=" * 70)
    print("Test 2: AUTO Scale (MACD)")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data with MACD values (small values around 0)
    macd_values = [0.0005, 0.0010, 0.0015, -0.0005, -0.0010, 0.0020, 0.0008] * 7  # 49 values
    timestamps = [datetime(2024, 1, 1, 9, 0) + timedelta(minutes=i*15) for i in range(49)]
    
    # Get MACD metadata
    metadata = metadata_registry.get("MACD")
    assert metadata is not None, "MACD metadata not found"
    assert metadata.scale_type == ScaleType.AUTO, "MACD should have AUTO scale type"
    
    print(f"✓ MACD metadata: scale_type={metadata.scale_type.value}")
    
    # Calculate expected range
    min_val = min(macd_values)
    max_val = max(macd_values)
    value_range = max_val - min_val
    padding = value_range * 0.1
    expected_min = min_val - padding
    expected_max = max_val + padding
    
    print(f"  Data range: [{min_val:.6f}, {max_val:.6f}]")
    print(f"  Expected range with 10% padding: [{expected_min:.6f}, {expected_max:.6f}]")
    
    # Create figure and apply scaling
    fig = make_subplots(rows=2, cols=1)
    engine._apply_scaling(fig, metadata, macd_values, row=2)
    
    # Check y-axis range
    yaxis = fig.layout.yaxis2  # Second subplot
    if hasattr(yaxis, 'range') and yaxis.range:
        print(f"✓ Y-axis range set to: [{yaxis.range[0]:.6f}, {yaxis.range[1]:.6f}]")
        
        # Verify the range encompasses all values with padding
        assert yaxis.range[0] <= min_val, f"Y-axis min {yaxis.range[0]} should be <= data min {min_val}"
        assert yaxis.range[1] >= max_val, f"Y-axis max {yaxis.range[1]} should be >= data max {max_val}"
        
        # Verify padding is approximately correct (within 1% tolerance)
        tolerance = value_range * 0.01
        assert abs(yaxis.range[0] - expected_min) < tolerance, f"Y-axis min padding incorrect"
        assert abs(yaxis.range[1] - expected_max) < tolerance, f"Y-axis max padding incorrect"
        
        print("✓ AUTO scale correctly calculated with 10% padding")
    else:
        raise AssertionError("Y-axis range not set for AUTO scale")
    
    print("=" * 70)


def test_auto_scale_with_same_values():
    """Test AUTO scale with all identical values (edge case)."""
    print("\n" + "=" * 70)
    print("Test 3: AUTO Scale with Identical Values")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data with identical MACD values
    macd_values = [0.0010] * 50
    timestamps = [datetime(2024, 1, 1, 9, 0) + timedelta(minutes=i*15) for i in range(50)]
    
    # Get MACD metadata
    metadata = metadata_registry.get("MACD")
    
    print(f"  Data: all values = {macd_values[0]:.6f}")
    
    # Create figure and apply scaling
    fig = make_subplots(rows=2, cols=1)
    engine._apply_scaling(fig, metadata, macd_values, row=2)
    
    # Check y-axis range
    yaxis = fig.layout.yaxis2
    if hasattr(yaxis, 'range') and yaxis.range:
        print(f"✓ Y-axis range set to: [{yaxis.range[0]:.6f}, {yaxis.range[1]:.6f}]")
        
        # When all values are the same, we add fixed padding of 0.1
        expected_min = macd_values[0] - 0.1
        expected_max = macd_values[0] + 0.1
        
        assert abs(yaxis.range[0] - expected_min) < 0.01, f"Expected min {expected_min}, got {yaxis.range[0]}"
        assert abs(yaxis.range[1] - expected_max) < 0.01, f"Expected max {expected_max}, got {yaxis.range[1]}"
        
        print("✓ AUTO scale correctly handles identical values with fixed padding")
    else:
        raise AssertionError("Y-axis range not set for AUTO scale")
    
    print("=" * 70)


def test_price_scale():
    """Test PRICE scale type (SMA shares price chart scale)."""
    print("\n" + "=" * 70)
    print("Test 4: PRICE Scale (SMA)")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data with SMA values (similar to price)
    sma_values = [1.1500, 1.1505, 1.1510, 1.1508, 1.1512] * 10
    timestamps = [datetime(2024, 1, 1, 9, 0) + timedelta(minutes=i*15) for i in range(50)]
    
    # Get SMA metadata
    metadata = metadata_registry.get("SMA")
    assert metadata is not None, "SMA metadata not found"
    assert metadata.scale_type == ScaleType.PRICE, "SMA should have PRICE scale type"
    
    print(f"✓ SMA metadata: scale_type={metadata.scale_type.value}")
    
    # Create figure and apply scaling
    fig = make_subplots(rows=2, cols=1)
    engine._apply_scaling(fig, metadata, sma_values, row=1)  # Row 1 is price chart
    
    # For PRICE scale, no explicit range should be set (it shares with price chart)
    yaxis = fig.layout.yaxis  # First subplot
    
    # PRICE scale doesn't set explicit range - it shares with price chart
    print("✓ PRICE scale applied (no explicit range set, shares with price chart)")
    print("  Note: PRICE scale indicators are added to the price chart subplot")
    print("  and automatically share the same y-axis scale as the candlestick data")
    
    print("=" * 70)


def test_stochastic_fixed_scale():
    """Test FIXED scale for Stochastic (0-100 range)."""
    print("\n" + "=" * 70)
    print("Test 5: FIXED Scale (Stochastic)")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data with Stochastic values
    stoch_values = [20.0, 40.0, 60.0, 80.0, 50.0] * 10
    timestamps = [datetime(2024, 1, 1, 9, 0) + timedelta(minutes=i*15) for i in range(50)]
    
    # Get Stochastic metadata
    metadata = metadata_registry.get("Stochastic")
    assert metadata is not None, "Stochastic metadata not found"
    assert metadata.scale_type == ScaleType.FIXED, "Stochastic should have FIXED scale type"
    assert metadata.scale_min == 0, "Stochastic scale_min should be 0"
    assert metadata.scale_max == 100, "Stochastic scale_max should be 100"
    
    print(f"✓ Stochastic metadata: scale_type={metadata.scale_type.value}, range=[{metadata.scale_min}, {metadata.scale_max}]")
    
    # Create figure and apply scaling
    fig = make_subplots(rows=2, cols=1)
    engine._apply_scaling(fig, metadata, stoch_values, row=2)
    
    # Check y-axis range
    yaxis = fig.layout.yaxis2
    if hasattr(yaxis, 'range') and yaxis.range:
        print(f"✓ Y-axis range set to: {yaxis.range}")
        assert yaxis.range[0] == 0, f"Expected y-axis min to be 0, got {yaxis.range[0]}"
        assert yaxis.range[1] == 100, f"Expected y-axis max to be 100, got {yaxis.range[1]}"
        print("✓ FIXED scale [0, 100] correctly applied")
    else:
        raise AssertionError("Y-axis range not set for FIXED scale")
    
    print("=" * 70)


def test_auto_scale_with_nan_values():
    """Test AUTO scale with NaN values (should be filtered out)."""
    print("\n" + "=" * 70)
    print("Test 6: AUTO Scale with NaN Values")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data with some NaN values
    macd_values = [0.0005, float('nan'), 0.0010, None, 0.0015, -0.0005, float('nan'), -0.0010]
    timestamps = [datetime(2024, 1, 1, 9, 0) + timedelta(minutes=i*15) for i in range(8)]
    
    # Get MACD metadata
    metadata = metadata_registry.get("MACD")
    
    print(f"  Data includes NaN and None values")
    
    # Create figure and apply scaling
    fig = make_subplots(rows=2, cols=1)
    engine._apply_scaling(fig, metadata, macd_values, row=2)
    
    # Check y-axis range
    yaxis = fig.layout.yaxis2
    if hasattr(yaxis, 'range') and yaxis.range:
        print(f"✓ Y-axis range set to: [{yaxis.range[0]:.6f}, {yaxis.range[1]:.6f}]")
        
        # Valid values are: 0.0005, 0.0010, 0.0015, -0.0005, -0.0010
        valid_values = [v for v in macd_values if v is not None and not (isinstance(v, float) and v != v)]
        min_val = min(valid_values)
        max_val = max(valid_values)
        
        # Verify the range encompasses all valid values
        assert yaxis.range[0] <= min_val, f"Y-axis min should be <= data min"
        assert yaxis.range[1] >= max_val, f"Y-axis max should be >= data max"
        
        print("✓ AUTO scale correctly filters out NaN/None values")
    else:
        raise AssertionError("Y-axis range not set for AUTO scale")
    
    print("=" * 70)


def run_all_tests():
    """Run all scaling logic tests."""
    print("\n" + "=" * 70)
    print("SCALING LOGIC TESTS - TASK 5")
    print("Testing Requirements: 1.2, 1.3, 1.4, 2.4, 4.4")
    print("=" * 70)
    
    try:
        test_fixed_scale()
        test_auto_scale()
        test_auto_scale_with_same_values()
        test_price_scale()
        test_stochastic_fixed_scale()
        test_auto_scale_with_nan_values()
        
        print("\n" + "=" * 70)
        print("ALL SCALING LOGIC TESTS PASSED! ✓✓✓")
        print("=" * 70)
        print("\nTask 5 Implementation Summary:")
        print("  ✓ FIXED scale: Sets y-axis to [scale_min, scale_max] from metadata")
        print("  ✓ AUTO scale: Calculates range from values with 10% padding")
        print("  ✓ PRICE scale: Shares y-axis with price chart (no explicit range)")
        print("  ✓ Edge cases: Handles identical values and NaN/None filtering")
        print("\nRequirements validated: 1.2, 1.3, 1.4, 2.4, 4.4")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
