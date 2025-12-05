#!/usr/bin/env python3
"""
Test subplot layout determination methods.
"""

from shared.chart_engine import ChartEngine


def test_determine_subplot_layout():
    """Test _determine_subplot_layout method."""
    engine = ChartEngine()
    
    # Test 1: No indicators
    layout = engine._determine_subplot_layout({})
    print("Test 1 - No indicators:")
    print(f"  Layout: {layout}")
    assert layout["price"] == 1
    assert layout["volume"] == 2
    assert layout["pnl"] == 3
    assert len([k for k in layout.keys() if k.startswith("oscillator_")]) == 0
    print("  ✓ Passed\n")
    
    # Test 2: Only overlay indicators (SMA, EMA)
    layout = engine._determine_subplot_layout({
        "SMA20": [1.0] * 10,
        "EMA50": [1.0] * 10
    })
    print("Test 2 - Only overlay indicators:")
    print(f"  Layout: {layout}")
    assert layout["price"] == 1
    assert layout["volume"] == 2
    assert layout["pnl"] == 3
    assert len([k for k in layout.keys() if k.startswith("oscillator_")]) == 0
    print("  ✓ Passed\n")
    
    # Test 3: One oscillator (MACD)
    layout = engine._determine_subplot_layout({
        "MACD": [0.001] * 10
    })
    print("Test 3 - One oscillator (MACD):")
    print(f"  Layout: {layout}")
    assert layout["price"] == 1
    assert layout["oscillator_1"] == 2
    assert layout["volume"] == 3
    assert layout["pnl"] == 4
    print("  ✓ Passed\n")
    
    # Test 4: Multiple oscillators (MACD + RSI)
    layout = engine._determine_subplot_layout({
        "MACD": [0.001] * 10,
        "RSI": [50.0] * 10
    })
    print("Test 4 - Multiple oscillators (MACD + RSI):")
    print(f"  Layout: {layout}")
    assert layout["price"] == 1
    assert layout["oscillator_1"] == 2
    assert layout["oscillator_2"] == 3
    assert layout["volume"] == 4
    assert layout["pnl"] == 5
    print("  ✓ Passed\n")
    
    # Test 5: Mixed indicators (overlays + oscillators)
    layout = engine._determine_subplot_layout({
        "SMA20": [1.0] * 10,
        "MACD": [0.001] * 10,
        "EMA50": [1.0] * 10,
        "RSI": [50.0] * 10
    })
    print("Test 5 - Mixed indicators (overlays + oscillators):")
    print(f"  Layout: {layout}")
    assert layout["price"] == 1
    assert layout["oscillator_1"] == 2  # MACD (alphabetically first)
    assert layout["oscillator_2"] == 3  # RSI
    assert layout["volume"] == 4
    assert layout["pnl"] == 5
    print("  ✓ Passed\n")


def test_calculate_row_heights():
    """Test _calculate_row_heights method."""
    engine = ChartEngine()
    
    # Test 1: No oscillators (3 rows: price, volume, pnl)
    layout = {"price": 1, "volume": 2, "pnl": 3}
    heights = engine._calculate_row_heights(layout)
    print("Test 1 - No oscillators:")
    print(f"  Heights: {heights}")
    assert len(heights) == 3
    assert heights[0] == 0.8  # Price (gets 80% when no oscillators)
    assert heights[1] == 0.1  # Volume
    assert heights[2] == 0.1  # P&L
    assert abs(sum(heights) - 1.0) < 0.01  # Should sum to 1.0
    print("  ✓ Passed\n")
    
    # Test 2: One oscillator (4 rows)
    layout = {"price": 1, "oscillator_1": 2, "volume": 3, "pnl": 4}
    heights = engine._calculate_row_heights(layout)
    print("Test 2 - One oscillator:")
    print(f"  Heights: {heights}")
    assert len(heights) == 4
    assert heights[0] == 0.5  # Price
    assert heights[1] == 0.3  # Oscillator (gets full 30%)
    assert heights[2] == 0.1  # Volume
    assert heights[3] == 0.1  # P&L
    assert abs(sum(heights) - 1.0) < 0.01  # Should sum to 1.0
    print("  ✓ Passed\n")
    
    # Test 3: Two oscillators (5 rows)
    layout = {"price": 1, "oscillator_1": 2, "oscillator_2": 3, "volume": 4, "pnl": 5}
    heights = engine._calculate_row_heights(layout)
    print("Test 3 - Two oscillators:")
    print(f"  Heights: {heights}")
    assert len(heights) == 5
    assert heights[0] == 0.5  # Price
    assert heights[1] == 0.15  # Oscillator 1 (30% / 2)
    assert heights[2] == 0.15  # Oscillator 2 (30% / 2)
    assert heights[3] == 0.1  # Volume
    assert heights[4] == 0.1  # P&L
    assert abs(sum(heights) - 1.0) < 0.01  # Should sum to 1.0
    print("  ✓ Passed\n")


def test_generate_subplot_titles():
    """Test _generate_subplot_titles method."""
    engine = ChartEngine()
    
    # Test 1: No oscillators
    layout = {"price": 1, "volume": 2, "pnl": 3}
    titles = engine._generate_subplot_titles(layout, "Test Strategy")
    print("Test 1 - No oscillators:")
    print(f"  Titles: {titles}")
    assert len(titles) == 3
    assert "Test Strategy - Price Action" in titles[0]
    assert "Volume" in titles[1]
    assert "Cumulative P&L" in titles[2]
    print("  ✓ Passed\n")
    
    # Test 2: With oscillators
    layout = {"price": 1, "oscillator_1": 2, "oscillator_2": 3, "volume": 4, "pnl": 5}
    titles = engine._generate_subplot_titles(layout, "MACD Strategy")
    print("Test 2 - With oscillators:")
    print(f"  Titles: {titles}")
    assert len(titles) == 5
    assert "MACD Strategy - Price Action" in titles[0]
    assert "Oscillator 1" in titles[1]
    assert "Oscillator 2" in titles[2]
    assert "Volume" in titles[3]
    assert "Cumulative P&L" in titles[4]
    print("  ✓ Passed\n")


def test_get_oscillator_index():
    """Test _get_oscillator_index method."""
    engine = ChartEngine()
    
    # First, create a layout to populate the oscillator mapping
    indicators = {
        "MACD": [0.001] * 10,
        "RSI": [50.0] * 10
    }
    layout = engine._determine_subplot_layout(indicators)
    
    print("Test - Get oscillator index:")
    print(f"  Layout: {layout}")
    print(f"  Oscillator mapping: {engine._oscillator_mapping}")
    
    # Test getting indices
    macd_index = engine._get_oscillator_index("MACD", layout)
    rsi_index = engine._get_oscillator_index("RSI", layout)
    
    print(f"  MACD index: {macd_index}")
    print(f"  RSI index: {rsi_index}")
    
    assert macd_index == 1  # MACD is first alphabetically
    assert rsi_index == 2   # RSI is second
    print("  ✓ Passed\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Subplot Layout Determination Methods")
    print("=" * 60 + "\n")
    
    test_determine_subplot_layout()
    test_calculate_row_heights()
    test_generate_subplot_titles()
    test_get_oscillator_index()
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
