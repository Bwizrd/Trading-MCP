#!/usr/bin/env python3
"""
End-to-end test for indicator routing with actual chart generation.

This test creates a real chart with mixed indicators to verify the routing
logic works correctly in a real-world scenario.
"""

from datetime import datetime, timedelta
from shared.chart_engine import ChartEngine
from shared.models import Candle, Trade, TradeDirection
from shared.strategy_interface import BacktestResults
import os


def create_test_data():
    """Create realistic test data."""
    # Create 100 candles
    candles = []
    base_time = datetime(2024, 1, 1, 9, 0)
    base_price = 1.15
    
    for i in range(100):
        price = base_price + (i * 0.0001)
        candles.append(Candle(
            timestamp=base_time + timedelta(minutes=i*15),
            open=price,
            high=price + 0.0005,
            low=price - 0.0005,
            close=price + 0.0002,
            volume=1000 + (i * 10)
        ))
    
    # Create some trades
    trades = []
    for i in range(5):
        trade = Trade(
            direction=TradeDirection.BUY if i % 2 == 0 else TradeDirection.SELL,
            entry_time=base_time + timedelta(hours=i*2),
            entry_price=base_price + (i * 0.001),
            exit_time=base_time + timedelta(hours=i*2+1),
            exit_price=base_price + (i * 0.001) + (0.0005 if i % 2 == 0 else -0.0003),
            pips=5.0 if i % 2 == 0 else -3.0
        )
        trades.append(trade)
    
    # Create backtest results
    from shared.strategy_interface import BacktestConfiguration
    
    config = BacktestConfiguration(
        symbol="EURUSD",
        timeframe="15m",
        start_date="2024-01-01",
        end_date="2024-01-02",
        initial_balance=10000,
        risk_per_trade=0.02,
        stop_loss_pips=15,
        take_profit_pips=25
    )
    
    backtest_results = BacktestResults(
        strategy_name="Test Mixed Strategy",
        strategy_version="1.0.0",
        configuration=config,
        trades=trades,
        total_trades=len(trades),
        winning_trades=3,
        losing_trades=2,
        total_pips=7.0,
        win_rate=0.60,
        profit_factor=1.67,
        average_win=5.0,
        average_loss=-3.0,
        largest_win=5.0,
        largest_loss=-3.0,
        max_drawdown=-3.0,
        max_consecutive_losses=1,
        max_consecutive_wins=2,
        start_time=base_time,
        end_time=base_time + timedelta(hours=10),
        execution_time_seconds=0.5,
        data_source="test",
        total_candles_processed=100,
        market_data=candles
    )
    
    # Create indicators
    indicators = {
        "SMA20": [base_price + (i * 0.0001) for i in range(100)],
        "EMA50": [base_price - 0.001 + (i * 0.0001) for i in range(100)],
        "MACD": [0.001 + (i * 0.00001) - 0.0015 for i in range(100)],
        "RSI": [50.0 + (i * 0.2) - 10 for i in range(100)],
        "VWAP": [base_price + 0.0005 + (i * 0.0001) for i in range(100)]
    }
    
    return candles, backtest_results, indicators


def test_end_to_end_chart_generation():
    """Test complete chart generation with routing."""
    print("\n" + "=" * 70)
    print("End-to-End Test: Chart Generation with Indicator Routing")
    print("=" * 70)
    
    # Create test data
    candles, backtest_results, indicators = create_test_data()
    
    print(f"\nTest data created:")
    print(f"  - Candles: {len(candles)}")
    print(f"  - Trades: {len(backtest_results.trades)}")
    print(f"  - Indicators: {list(indicators.keys())}")
    
    # Create chart engine
    engine = ChartEngine()
    
    # Store the layout for routing
    layout = engine._determine_subplot_layout(indicators)
    engine._current_layout = layout
    
    print(f"\nSubplot layout:")
    for name, row in sorted(layout.items(), key=lambda x: x[1]):
        print(f"  Row {row}: {name}")
    
    # Generate chart
    print("\nGenerating chart...")
    try:
        chart_path = engine.create_comprehensive_chart(
            candles=candles,
            backtest_results=backtest_results,
            indicators=indicators,
            title="Test Mixed Strategy with Routing"
        )
        
        print(f"\n✓ Chart generated successfully!")
        print(f"  Path: {chart_path}")
        
        # Verify file exists
        if os.path.exists(chart_path):
            file_size = os.path.getsize(chart_path)
            print(f"  Size: {file_size:,} bytes")
            print(f"\n✓ Chart file exists and is valid")
        else:
            print(f"\n✗ Chart file not found at {chart_path}")
            return False
        
        print("\n" + "=" * 70)
        print("End-to-end test PASSED! ✓")
        print("=" * 70)
        print(f"\nYou can open the chart in your browser:")
        print(f"  file://{chart_path}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error generating chart: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_end_to_end_chart_generation()
    exit(0 if success else 1)
