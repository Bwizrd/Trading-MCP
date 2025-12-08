"""
Test script to verify indicator metadata infrastructure.
"""

from shared.indicators_metadata import (
    IndicatorType,
    ScaleType,
    ReferenceLine,
    ComponentStyle,
    IndicatorMetadata,
    IndicatorMetadataRegistry,
    metadata_registry
)


def test_metadata_registry():
    """Test the metadata registry functionality."""
    print("Testing Indicator Metadata Registry...")
    print("=" * 60)
    
    # Test 1: Retrieve MACD metadata
    print("\n1. Testing MACD metadata retrieval:")
    macd_metadata = metadata_registry.get("MACD")
    assert macd_metadata is not None, "MACD metadata should exist"
    assert macd_metadata.indicator_type == IndicatorType.OSCILLATOR
    assert macd_metadata.scale_type == ScaleType.AUTO
    assert macd_metadata.zero_line == True
    assert len(macd_metadata.components) == 3
    print("   ✓ MACD metadata retrieved successfully")
    print(f"   - Type: {macd_metadata.indicator_type.value}")
    print(f"   - Scale: {macd_metadata.scale_type.value}")
    print(f"   - Components: {list(macd_metadata.components.keys())}")
    
    # Test 2: Retrieve RSI metadata
    print("\n2. Testing RSI metadata retrieval:")
    rsi_metadata = metadata_registry.get("RSI")
    assert rsi_metadata is not None, "RSI metadata should exist"
    assert rsi_metadata.indicator_type == IndicatorType.OSCILLATOR
    assert rsi_metadata.scale_type == ScaleType.FIXED
    assert rsi_metadata.scale_min == 0
    assert rsi_metadata.scale_max == 100
    assert len(rsi_metadata.reference_lines) == 2
    print("   ✓ RSI metadata retrieved successfully")
    print(f"   - Scale range: [{rsi_metadata.scale_min}, {rsi_metadata.scale_max}]")
    print(f"   - Reference lines: {len(rsi_metadata.reference_lines)}")
    
    # Test 3: Retrieve Stochastic metadata
    print("\n3. Testing Stochastic metadata retrieval:")
    stoch_metadata = metadata_registry.get("Stochastic")
    assert stoch_metadata is not None, "Stochastic metadata should exist"
    assert stoch_metadata.indicator_type == IndicatorType.OSCILLATOR
    assert stoch_metadata.scale_type == ScaleType.FIXED
    assert len(stoch_metadata.components) == 2
    print("   ✓ Stochastic metadata retrieved successfully")
    print(f"   - Components: {list(stoch_metadata.components.keys())}")
    
    # Test 4: Retrieve SMA metadata
    print("\n4. Testing SMA metadata retrieval:")
    sma_metadata = metadata_registry.get("SMA")
    assert sma_metadata is not None, "SMA metadata should exist"
    assert sma_metadata.indicator_type == IndicatorType.OVERLAY
    assert sma_metadata.scale_type == ScaleType.PRICE
    print("   ✓ SMA metadata retrieved successfully")
    print(f"   - Type: {sma_metadata.indicator_type.value}")
    
    # Test 5: Retrieve EMA metadata
    print("\n5. Testing EMA metadata retrieval:")
    ema_metadata = metadata_registry.get("EMA")
    assert ema_metadata is not None, "EMA metadata should exist"
    assert ema_metadata.indicator_type == IndicatorType.OVERLAY
    print("   ✓ EMA metadata retrieved successfully")
    
    # Test 6: Retrieve VWAP metadata
    print("\n6. Testing VWAP metadata retrieval:")
    vwap_metadata = metadata_registry.get("VWAP")
    assert vwap_metadata is not None, "VWAP metadata should exist"
    assert vwap_metadata.indicator_type == IndicatorType.OVERLAY
    print("   ✓ VWAP metadata retrieved successfully")
    
    # Test 7: Base name extraction
    print("\n7. Testing base name extraction:")
    sma20_metadata = metadata_registry.get("SMA20")
    sma50_metadata = metadata_registry.get("SMA50")
    sma200_metadata = metadata_registry.get("SMA200")
    assert sma20_metadata is not None, "SMA20 should resolve to SMA"
    assert sma50_metadata is not None, "SMA50 should resolve to SMA"
    assert sma200_metadata is not None, "SMA200 should resolve to SMA"
    assert sma20_metadata.name == "SMA"
    assert sma50_metadata.name == "SMA"
    assert sma200_metadata.name == "SMA"
    print("   ✓ Base name extraction works correctly")
    print("   - SMA20 → SMA")
    print("   - SMA50 → SMA")
    print("   - SMA200 → SMA")
    
    # Test 8: is_oscillator() method
    print("\n8. Testing is_oscillator() method:")
    assert metadata_registry.is_oscillator("MACD") == True
    assert metadata_registry.is_oscillator("RSI") == True
    assert metadata_registry.is_oscillator("Stochastic") == True
    assert metadata_registry.is_oscillator("SMA") == False
    assert metadata_registry.is_oscillator("EMA") == False
    assert metadata_registry.is_oscillator("VWAP") == False
    print("   ✓ is_oscillator() works correctly")
    
    # Test 9: is_overlay() method
    print("\n9. Testing is_overlay() method:")
    assert metadata_registry.is_overlay("SMA") == True
    assert metadata_registry.is_overlay("EMA") == True
    assert metadata_registry.is_overlay("VWAP") == True
    assert metadata_registry.is_overlay("MACD") == False
    assert metadata_registry.is_overlay("RSI") == False
    print("   ✓ is_overlay() works correctly")
    
    # Test 10: Unknown indicator
    print("\n10. Testing unknown indicator:")
    unknown_metadata = metadata_registry.get("UNKNOWN")
    assert unknown_metadata is None, "Unknown indicator should return None"
    print("   ✓ Unknown indicator returns None")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    test_metadata_registry()
