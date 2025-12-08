#!/usr/bin/env python3
"""
Test MACD Visualization with DSL-Style Indicators

This test simulates how DSL strategies provide MACD indicators:
- macd (main line)
- macd_signal (signal line)
- macd_histogram (histogram)
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


def test_macd_dsl_style():
    """Test MACD visualization with DSL-style separate indicators."""
    print("\n" + "=" * 70)
    print("Test: MACD DSL-Style Indicators")
    print("=" * 70)
    
    # Create test data
    candles = create_test_candles(100)
    
    # Calculate MACD
    print("\n1. Calculating MACD...")
    macd_calc = MACDCalculator(12, 26, 9)
    macd_values_dict = macd_calc.calculate(candles)
    signal_line_dict = macd_calc.get_signal_line()
    histogram_dict = macd_calc.get_histogram()
    
    # Convert to lists (simulating DSL strategy output)
    macd_values = [macd_values_dict.get(c.timestamp, 0.0) for c in candles]
    signal_values = [signal_line_dict.get(c.timestamp, 0.0) for c in candles]
    histogram_values = [histogram_dict.get(c.timestamp, 0.0) for c in candles]
    
    print(f"  ✓ MACD calculated: {len(macd_values)} points")
    print(f"  ✓ Signal calculated: {len(signal_values)} points")
    print(f"  ✓ Histogram calculated: {len(histogram_values)} points")
    
    # Create backtest results
    config = BacktestConfiguration(
        symbol="EURUSD",
        timeframe="15m",
        start_date=candles[0].timestamp,
        end_date=candles[-1].timestamp
    )
    
    trade = Trade(
        direction=TradeDirection.BUY,
        entry_time=candles[10].timestamp,
        entry_price=candles[10].close,
        exit_time=candles[20].timestamp,
        exit_price=candles[20].close,
        pips=10.0
    )
    
    backtest_results = BacktestResults(
        strategy_name="MACD DSL Test Strategy",
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
    
    # Create indicators dictionary (DSL style with separate entries)
    print("\n2. Creating indicators dictionary (DSL style)...")
    indicators = {
        "macd": macd_values,
        "macd_signal": signal_values,
        "macd_histogram": histogram_values
    }
    print(f"  ✓ Indicators: {list(indicators.keys())}")
    
    # Create chart
    print("\n3. Creating chart with DSL-style MACD indicators...")
    engine = ChartEngine()
    
    try:
        chart_path = engine.create_comprehensive_chart(
            candles=candles,
            backtest_results=backtest_results,
            indicators=indicators,
            title="MACD DSL Style Test"
        )
        
        print(f"  ✓ Chart created successfully: {chart_path}")
        
        # Verify the chart file exists
        assert Path(chart_path).exists(), f"Chart file should exist at {chart_path}"
        print(f"  ✓ Chart file exists")
        
        # Read the HTML to verify components are present
        with open(chart_path, 'r') as f:
            html_content = f.read()
        
        print("\n4. Verifying MACD components in chart HTML...")
        
        # Check for MACD line
        has_macd = "MACD" in html_content or "macd" in html_content
        print(f"  MACD line: {'✓' if has_macd else '❌'}")
        
        # Check for Signal line
        has_signal = "Signal" in html_content or "signal" in html_content
        print(f"  Signal line: {'✓' if has_signal else '❌'}")
        
        # Check for Histogram
        has_histogram = "Histogram" in html_content or "histogram" in html_content
        print(f"  Histogram: {'✓' if has_histogram else '❌'}")
        
        print("\n" + "=" * 70)
        if has_macd and has_signal and has_histogram:
            print("✅ MACD DSL Style Test PASSED")
        else:
            print("⚠️  MACD DSL Style Test PARTIAL - Some components missing")
        print("=" * 70)
        print(f"\n📊 Open the chart to verify visually:")
        print(f"   {chart_path}")
        print("\nExpected visualization:")
        print("  • MACD line in BLUE")
        print("  • Signal line in RED")
        print("  • Histogram as GRAY BARS")
        print("  • Zero line (dashed gray)")
        
        return has_macd and has_signal and has_histogram
        
    except Exception as e:
        print(f"\n❌ Error creating chart: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run MACD DSL style test."""
    print("\n" + "=" * 70)
    print("MACD DSL-STYLE VISUALIZATION TEST")
    print("=" * 70)
    
    success = test_macd_dsl_style()
    
    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
