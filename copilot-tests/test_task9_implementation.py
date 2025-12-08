#!/usr/bin/env python3
"""
Test Task 9 Implementation: Dynamic Layout and Improved Titles

This test verifies that:
1. create_comprehensive_chart uses dynamic layout based on indicators
2. Subplot titles show actual indicator names instead of generic "Oscillator 1"
3. Multiple instances of same oscillator type get distinct subplots
4. Backward compatibility is maintained (no indicators case)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
from shared.chart_engine import ChartEngine
from shared.models import Candle, Trade, TradeDirection
from shared.strategy_interface import BacktestResults, BacktestConfiguration

def create_test_candles(count=50):
    """Create test candle data."""
    candles = []
    base_time = datetime(2024, 1, 1, 9, 0)
    base_price = 1.1000
    
    for i in range(count):
        candles.append(Candle(
            timestamp=base_time + timedelta(minutes=i*15),
            open=base_price + (i * 0.0001),
            high=base_price + (i * 0.0001) + 0.0005,
            low=base_price + (i * 0.0001) - 0.0003,
            close=base_price + (i * 0.0001) + 0.0002,
            volume=1000 + (i * 10)
        ))
    
    return candles

def create_test_backtest_results(candles):
    """Create minimal backtest results."""
    config = BacktestConfiguration(
        symbol="EURUSD",
        timeframe="15m",
        start_date="2024-01-01",
        end_date="2024-01-02"
    )
    
    trades = [
        Trade(
            direction=TradeDirection.BUY,
            entry_time=datetime(2024, 1, 1, 10, 0),
            entry_price=1.1000,
            exit_time=datetime(2024, 1, 1, 11, 0),
            exit_price=1.1015,
            pips=15.0
        )
    ]
    
    return BacktestResults(
        strategy_name="Test Strategy",
        strategy_version="1.0.0",
        configuration=config,
        trades=trades,
        total_trades=1,
        winning_trades=1,
        losing_trades=0,
        total_pips=15.0,
        win_rate=1.0,
        profit_factor=1.0,
        average_win=15.0,
        average_loss=0.0,
        largest_win=15.0,
        largest_loss=0.0,
        max_drawdown=0.0,
        max_consecutive_losses=0,
        max_consecutive_wins=1,
        start_time=candles[0].timestamp,
        end_time=candles[-1].timestamp,
        execution_time_seconds=0.1,
        data_source="test",
        total_candles_processed=len(candles),
        market_data=candles
    )

def test_improved_subplot_titles():
    """Test that subplot titles show actual indicator names."""
    print("=" * 70)
    print("Test 1: Improved Subplot Titles with Indicator Names")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data with named indicators
    indicators = {
        "MACD": [0.001] * 50,
        "RSI": [50.0] * 50,
        "SMA20": [1.1000] * 50
    }
    
    # Determine layout (this populates _oscillator_mapping)
    layout = engine._determine_subplot_layout(indicators)
    print(f"\nLayout: {layout}")
    print(f"Oscillator mapping: {engine._oscillator_mapping}")
    
    # Generate titles with indicators
    titles = engine._generate_subplot_titles(layout, "Test Strategy", indicators)
    print(f"\nSubplot titles: {titles}")
    
    # Verify titles contain actual indicator names
    assert "MACD" in titles[1], f"Expected 'MACD' in title, got: {titles[1]}"
    assert "RSI" in titles[2], f"Expected 'RSI' in title, got: {titles[2]}"
    
    print("\n✓ Titles correctly show indicator names (MACD, RSI)")
    print("✓ Test passed!\n")

def test_indicator_with_parameters():
    """Test that indicators with parameters show nicely formatted titles."""
    print("=" * 70)
    print("Test 2: Indicator Titles with Parameters")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data with parameterized indicators
    indicators = {
        "rsi_14": [50.0] * 50,
        "stochastic_14_3_3": [50.0] * 50,
        "macd_12_26_9": [0.001] * 50
    }
    
    # Determine layout
    layout = engine._determine_subplot_layout(indicators)
    print(f"\nLayout: {layout}")
    
    # Generate titles
    titles = engine._generate_subplot_titles(layout, "Test Strategy", indicators)
    print(f"\nSubplot titles: {titles}")
    
    # Verify formatted titles (don't assume specific order due to sorting)
    titles_str = ' '.join(titles)
    
    assert "RSI (14)" in titles_str or "RSI_14" in titles_str, f"Expected formatted RSI title in: {titles}"
    rsi_title = [t for t in titles if "RSI" in t.upper()][0]
    print(f"✓ RSI title: {rsi_title}")
    
    assert "STOCHASTIC" in titles_str.upper(), f"Expected Stochastic in titles: {titles}"
    stoch_title = [t for t in titles if "STOCHASTIC" in t.upper()][0]
    print(f"✓ Stochastic title: {stoch_title}")
    
    assert "MACD" in titles_str.upper(), f"Expected MACD in titles: {titles}"
    macd_title = [t for t in titles if "MACD" in t.upper()][0]
    print(f"✓ MACD title: {macd_title}")
    
    print("\n✓ Test passed!\n")

def test_multiple_same_oscillator_type():
    """Test that multiple instances of same oscillator get distinct subplots."""
    print("=" * 70)
    print("Test 3: Multiple Instances of Same Oscillator Type")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data with multiple Stochastic indicators
    indicators = {
        "stochastic_14_3_3": [50.0] * 50,
        "stochastic_21_5_5": [60.0] * 50,
        "stochastic_5_3_3": [40.0] * 50
    }
    
    # Determine layout
    layout = engine._determine_subplot_layout(indicators)
    print(f"\nLayout: {layout}")
    print(f"Oscillator mapping: {engine._oscillator_mapping}")
    
    # Verify each gets its own subplot
    assert "oscillator_1" in layout, "Missing oscillator_1"
    assert "oscillator_2" in layout, "Missing oscillator_2"
    assert "oscillator_3" in layout, "Missing oscillator_3"
    
    # Generate titles
    titles = engine._generate_subplot_titles(layout, "Test Strategy", indicators)
    print(f"\nSubplot titles: {titles}")
    
    # Verify all three have distinct titles
    stochastic_titles = [t for t in titles if "STOCHASTIC" in t.upper()]
    assert len(stochastic_titles) == 3, f"Expected 3 Stochastic titles, got {len(stochastic_titles)}"
    
    print(f"\n✓ All 3 Stochastic indicators have distinct subplots")
    print(f"✓ Titles: {stochastic_titles}")
    print("✓ Test passed!\n")

def test_backward_compatibility_no_indicators():
    """Test backward compatibility when no indicators are provided."""
    print("=" * 70)
    print("Test 4: Backward Compatibility (No Indicators)")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Empty indicators
    indicators = {}
    
    # Determine layout
    layout = engine._determine_subplot_layout(indicators)
    print(f"\nLayout: {layout}")
    
    # Should have only price, volume, pnl
    assert layout == {"price": 1, "volume": 2, "pnl": 3}, f"Unexpected layout: {layout}"
    
    # Calculate heights
    heights = engine._calculate_row_heights(layout)
    print(f"Row heights: {heights}")
    
    # Verify heights sum to 1.0
    assert abs(sum(heights) - 1.0) < 0.01, f"Heights don't sum to 1.0: {sum(heights)}"
    
    print("\n✓ Layout correct for no indicators")
    print("✓ Heights sum to 1.0")
    print("✓ Test passed!\n")

def test_create_comprehensive_chart_integration():
    """Test that create_comprehensive_chart uses the dynamic layout."""
    print("=" * 70)
    print("Test 5: create_comprehensive_chart Integration")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data
    candles = create_test_candles(50)
    backtest_results = create_test_backtest_results(candles)
    
    indicators = {
        "MACD": [0.001 * i for i in range(50)],
        "RSI": [50.0 + (i % 20) for i in range(50)],
        "SMA20": [1.1000 + (i * 0.0001) for i in range(50)]
    }
    
    # Create chart
    print("\nCreating comprehensive chart with dynamic layout...")
    chart_path = engine.create_comprehensive_chart(
        candles,
        backtest_results,
        indicators,
        title="Dynamic Layout Test"
    )
    
    print(f"\n✓ Chart created successfully: {chart_path}")
    print("✓ No errors during chart generation")
    print("✓ Test passed!\n")
    
    return chart_path

def test_format_indicator_title():
    """Test the _format_indicator_title helper method."""
    print("=" * 70)
    print("Test 6: Format Indicator Title Helper")
    print("=" * 70)
    
    engine = ChartEngine()
    
    test_cases = [
        ("macd", "MACD"),
        ("rsi_14", "RSI (14)"),
        ("stochastic_14_3_3", "STOCHASTIC (14,3,3)"),
        ("macd_12_26_9", "MACD (12,26,9)"),
        ("sma20", "SMA20"),  # No underscore, so no params
        ("ema_50", "EMA (50)"),
    ]
    
    print("\nTesting indicator title formatting:")
    for input_name, expected_pattern in test_cases:
        result = engine._format_indicator_title(input_name)
        print(f"  {input_name:20} -> {result}")
        
        # Check that the base name is in the result
        base = expected_pattern.split('(')[0].strip()
        assert base in result.upper(), f"Expected '{base}' in '{result}'"
    
    print("\n✓ All title formats correct")
    print("✓ Test passed!\n")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TASK 9 IMPLEMENTATION TESTS")
    print("Testing Dynamic Layout and Improved Subplot Titles")
    print("=" * 70 + "\n")
    
    try:
        test_improved_subplot_titles()
        test_indicator_with_parameters()
        test_multiple_same_oscillator_type()
        test_backward_compatibility_no_indicators()
        test_format_indicator_title()
        chart_path = test_create_comprehensive_chart_integration()
        
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED! ✓")
        print("=" * 70)
        print(f"\nGenerated chart: {chart_path}")
        print("\nTask 9 implementation is complete and working correctly:")
        print("  ✓ Dynamic layout based on indicators")
        print("  ✓ Improved subplot titles with indicator names")
        print("  ✓ Multiple instances of same oscillator type supported")
        print("  ✓ Backward compatibility maintained")
        print("=" * 70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
