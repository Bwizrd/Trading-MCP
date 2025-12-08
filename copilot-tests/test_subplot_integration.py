#!/usr/bin/env python3
"""
Integration test for subplot layout methods working together.
"""

from shared.chart_engine import ChartEngine


def test_full_integration():
    """Test all four methods working together."""
    engine = ChartEngine()
    
    # Scenario: Mixed strategy with overlays and oscillators
    indicators = {
        "SMA20": [1.15] * 100,
        "EMA50": [1.14] * 100,
        "MACD": [0.001] * 100,
        "RSI": [55.0] * 100,
        "VWAP": [1.155] * 100
    }
    
    print("=" * 70)
    print("Integration Test: Full Subplot Layout Workflow")
    print("=" * 70)
    print(f"\nIndicators: {list(indicators.keys())}")
    
    # Step 1: Determine layout
    layout = engine._determine_subplot_layout(indicators)
    print(f"\n1. Layout determined:")
    for name, row in sorted(layout.items(), key=lambda x: x[1]):
        print(f"   Row {row}: {name}")
    
    # Step 2: Calculate heights
    heights = engine._calculate_row_heights(layout)
    print(f"\n2. Row heights calculated:")
    for i, height in enumerate(heights, 1):
        subplot_name = [k for k, v in layout.items() if v == i][0]
        print(f"   Row {i} ({subplot_name}): {height:.1%}")
    print(f"   Total: {sum(heights):.1%}")
    
    # Step 3: Generate titles
    titles = engine._generate_subplot_titles(layout, "Mixed Strategy Test")
    print(f"\n3. Subplot titles generated:")
    for i, title in enumerate(titles, 1):
        print(f"   Row {i}: {title}")
    
    # Step 4: Get oscillator indices
    print(f"\n4. Oscillator indices:")
    for indicator_name in ["MACD", "RSI"]:
        index = engine._get_oscillator_index(indicator_name, layout)
        print(f"   {indicator_name} → oscillator_{index}")
    
    # Verify correctness
    print(f"\n5. Verification:")
    
    # Check layout structure
    assert layout["price"] == 1, "Price should be row 1"
    assert "oscillator_1" in layout, "Should have oscillator_1"
    assert "oscillator_2" in layout, "Should have oscillator_2"
    assert layout["volume"] == 4, "Volume should be row 4"
    assert layout["pnl"] == 5, "P&L should be row 5"
    print("   ✓ Layout structure correct")
    
    # Check heights sum to 1.0
    assert abs(sum(heights) - 1.0) < 0.01, "Heights should sum to 1.0"
    print("   ✓ Heights sum to 1.0")
    
    # Check price chart gets 50%
    assert heights[0] == 0.5, "Price chart should get 50%"
    print("   ✓ Price chart gets 50%")
    
    # Check oscillators share 30%
    oscillator_heights = [heights[layout[k] - 1] for k in layout if k.startswith("oscillator_")]
    assert abs(sum(oscillator_heights) - 0.3) < 0.01, "Oscillators should share 30%"
    print("   ✓ Oscillators share 30%")
    
    # Check volume and P&L get 10% each
    assert heights[layout["volume"] - 1] == 0.1, "Volume should get 10%"
    assert heights[layout["pnl"] - 1] == 0.1, "P&L should get 10%"
    print("   ✓ Volume and P&L each get 10%")
    
    # Check titles are correct
    assert len(titles) == 5, "Should have 5 titles"
    assert "Mixed Strategy Test - Price Action" in titles[0]
    print("   ✓ Titles are correct")
    
    print("\n" + "=" * 70)
    print("Integration test PASSED! ✓")
    print("=" * 70)


def test_edge_case_no_oscillators():
    """Test edge case with no oscillators."""
    engine = ChartEngine()
    
    indicators = {
        "SMA20": [1.15] * 100,
        "EMA50": [1.14] * 100,
        "VWAP": [1.155] * 100
    }
    
    print("\n" + "=" * 70)
    print("Edge Case Test: No Oscillators")
    print("=" * 70)
    
    layout = engine._determine_subplot_layout(indicators)
    heights = engine._calculate_row_heights(layout)
    titles = engine._generate_subplot_titles(layout, "Overlay Only Strategy")
    
    print(f"\nLayout: {layout}")
    print(f"Heights: {heights}")
    print(f"Titles: {titles}")
    
    # Verify no oscillator subplots
    oscillator_count = len([k for k in layout.keys() if k.startswith("oscillator_")])
    assert oscillator_count == 0, "Should have no oscillator subplots"
    print("\n✓ No oscillator subplots created")
    
    # Verify only 3 rows (price, volume, pnl)
    assert len(heights) == 3, "Should have only 3 rows"
    print("✓ Only 3 rows created")
    
    print("\nEdge case test PASSED! ✓")
    print("=" * 70)


def test_edge_case_only_oscillators():
    """Test edge case with only oscillators."""
    engine = ChartEngine()
    
    indicators = {
        "MACD": [0.001] * 100,
        "RSI": [55.0] * 100,
        "Stochastic": [60.0] * 100
    }
    
    print("\n" + "=" * 70)
    print("Edge Case Test: Only Oscillators")
    print("=" * 70)
    
    layout = engine._determine_subplot_layout(indicators)
    heights = engine._calculate_row_heights(layout)
    titles = engine._generate_subplot_titles(layout, "Oscillator Only Strategy")
    
    print(f"\nLayout: {layout}")
    print(f"Heights: {heights}")
    print(f"Titles: {titles}")
    
    # Verify 3 oscillator subplots
    oscillator_count = len([k for k in layout.keys() if k.startswith("oscillator_")])
    assert oscillator_count == 3, "Should have 3 oscillator subplots"
    print("\n✓ 3 oscillator subplots created")
    
    # Verify 6 rows (price, 3 oscillators, volume, pnl)
    assert len(heights) == 6, "Should have 6 rows"
    print("✓ 6 rows created")
    
    # Verify each oscillator gets 10% (30% / 3)
    for i in range(1, 4):
        osc_height = heights[layout[f"oscillator_{i}"] - 1]
        assert abs(osc_height - 0.1) < 0.01, f"Oscillator {i} should get 10%"
    print("✓ Each oscillator gets 10% (30% / 3)")
    
    print("\nEdge case test PASSED! ✓")
    print("=" * 70)


if __name__ == "__main__":
    test_full_integration()
    test_edge_case_no_oscillators()
    test_edge_case_only_oscillators()
    
    print("\n" + "=" * 70)
    print("ALL INTEGRATION TESTS PASSED! ✓✓✓")
    print("=" * 70)
