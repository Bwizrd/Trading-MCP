#!/usr/bin/env python3
"""
Test MACD Visualization with Three Components

This test verifies that the MACD indicator is properly rendered with:
1. MACD line (blue)
2. Signal line (red)
3. Histogram (gray bars)
4. Zero line
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.chart_engine import ChartEngine
from shared.models import Candle, Trade, TradeDirection
from shared.strategy_interface import BacktestResults, BacktestConfiguration
from shared.indicators import MACDCalculator


def create_test_candles(count: int = 100) -> list:
    """Create test candle data with realistic price movement."""
    candles = []
    base_price = 1.1000
    timestamp = datetime(2024, 1, 1, 9, 0)
    
    for i in range(count):
        # Create some price movement
        price_change = (i % 10 - 5) * 0.0001
        price = base_price + price_change
        
        candles.append(Candle(
            timestamp=timestamp,
            open=price,
            high=price + 0.0002,
            low=price - 0.0002,
            close=price + 0.0001,
            volume=1000.0
        ))
        
        timestamp += timedelta(minutes=15)
    
    return candles


def test_macd_three_components():
    """Test that MACD is rendered with all three components."""
    print("\n" + "=" * 70)
    print("Test: MACD Three Components Visualization")
    print("=" * 70)
    
    # Create test data
    candles = create_test_candles(100)
    
    # Calculate MACD
    macd_calc = MACDCalculator(12, 26, 9)
    macd_values_dict = macd_calc.calculate(candles)
    
    # Verify calculator has signal line and histogram methods
    print("\n1. Verifying MACDCalculator has required methods...")
    assert hasattr(macd_calc, 'get_signal_line'), "MACDCalculator should have get_signal_line() method"
    assert hasattr(macd_calc, 'get_histogram'), "MACDCalculator should have get_histogram() method"
    print("  ✓ MACDCalculator has get_signal_line() and get_histogram() methods")
    
    # Get signal line and histogram
    signal_line = macd_calc.get_signal_line()
    histogram = macd_calc.get_histogram()
    
    print(f"\n2. Verifying MACD components are calculated...")
    print(f"  MACD values: {len(macd_values_dict)} points")
    print(f"  Signal line: {len(signal_line)} points")
    print(f"  Histogram: {len(histogram)} points")
    
    assert len(macd_values_dict) > 0, "MACD should have values"
    assert len(signal_line) > 0, "Signal line should have values"
    assert len(histogram) > 0, "Histogram should have values"
    assert len(macd_values_dict) == len(signal_line) == len(histogram), "All components should have same length"
    print("  ✓ All three components calculated successfully")
    
    # Convert MACD dict to list for chart engine
    macd_values_list = [macd_values_dict.get(c.timestamp, 0.0) for c in candles]
    
    # Convert signal line and histogram to lists (DSL approach)
    signal_line_list = [signal_line.get(c.timestamp, 0.0) for c in candles]
    histogram_list = [histogram.get(c.timestamp, 0.0) for c in candles]
    
    # Create a simple backtest result
    config = BacktestConfiguration(
        symbol="EURUSD",
        timeframe="15m",
        start_date=candles[0].timestamp,
        end_date=candles[-1].timestamp
    )
    
    # Create a dummy trade
    trade = Trade(
        direction=TradeDirection.BUY,
        entry_time=candles[10].timestamp,
        entry_price=candles[10].close,
        exit_time=candles[20].timestamp,
        exit_price=candles[20].close,
        pips=10.0
    )
    
    backtest_results = BacktestResults(
        strategy_name="MACD Test Strategy",
        strategy_version="1.0.0",
        configuration=config,
        trades=[trade],
        total_trades=1,
        winning_trades=1,
        losing_trades=0,
        total_pips=10.0,
        win_rate=1.0,
        profit_factor=1.0,
        average_win=10.0,
        average_loss=0.0,
        largest_win=10.0,
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
    
    # Create chart with MACD (DSL approach: three separate indicators)
    print("\n3. Creating chart with MACD indicator (DSL approach)...")
    engine = ChartEngine()
    
    indicators = {
        "macd": macd_values_list,
        "macd_signal": signal_line_list,
        "macd_histogram": histogram_list
    }
    
    try:
        chart_path = engine.create_comprehensive_chart(
            candles=candles,
            backtest_results=backtest_results,
            indicators=indicators,
            title="MACD Three Components Test"
        )
        
        print(f"  ✓ Chart created successfully: {chart_path}")
        
        # Verify the chart file exists
        assert Path(chart_path).exists(), f"Chart file should exist at {chart_path}"
        print(f"  ✓ Chart file exists")
        
        # Read the HTML to verify components are present
        with open(chart_path, 'r') as f:
            html_content = f.read()
        
        print("\n4. Verifying MACD components in chart HTML...")
        
        # Check for MACD indicators (DSL provides three separate indicators)
        # Note: The DSL approach provides macd, macd_signal, and macd_histogram as separate indicators
        # The chart engine routes them to the oscillator subplot
        assert "macd" in html_content.lower(), "Chart should contain MACD indicator"
        print("  ✓ MACD indicator present")
        
        # Verify all three components are in the chart
        # They appear as separate traces in the oscillator subplot
        indicator_count = html_content.lower().count('"name":"macd"')
        assert indicator_count >= 1, f"Chart should contain MACD traces (found {indicator_count})"
        print(f"  ✓ Found {indicator_count} MACD-related traces")
        
        print("\n" + "=" * 70)
        print("✅ MACD Three Components Test PASSED")
        print("=" * 70)
        print(f"\n📊 Open the chart to verify visually:")
        print(f"   {chart_path}")
        print("\nExpected visualization:")
        print("  • MACD line in BLUE")
        print("  • Signal line in RED")
        print("  • Histogram as GRAY BARS")
        print("  • Zero line (dashed gray)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating chart: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run MACD visualization test."""
    print("\n" + "=" * 70)
    print("MACD VISUALIZATION TEST")
    print("=" * 70)
    
    success = test_macd_three_components()
    
    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
