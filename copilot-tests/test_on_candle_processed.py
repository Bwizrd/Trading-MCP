#!/usr/bin/env python3
"""
Test to verify on_candle_processed is being called during backtest.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from shared.strategies.dsl_interpreter.dsl_strategy import create_dsl_strategy_from_file
from shared.backtest_engine import UniversalBacktestEngine
from shared.data_connector import DataConnector

def test_on_candle_processed():
    """Test that on_candle_processed is called during backtest."""
    
    # Clear debug log
    with open('/tmp/dsl_debug.log', 'w') as f:
        f.write("=== Test on_candle_processed ===\n")
    
    # Load strategy
    strategy_path = "shared/strategies/dsl_strategies/stochastic_quad_rotation.json"
    strategy = create_dsl_strategy_from_file(strategy_path)
    
    print(f"Strategy loaded: {strategy.get_name()}")
    print(f"Is indicator based: {strategy.is_indicator_based}")
    
    # Setup backtest
    data_connector = DataConnector()
    engine = UniversalBacktestEngine(data_connector)
    
    # Run backtest for just today (2025-12-11)
    start_date = "2025-12-11"
    end_date = "2025-12-11"
    
    print(f"\nRunning backtest for {start_date}...")
    
    results = engine.run_backtest(
        strategy=strategy,
        symbol="US500_SB",
        timeframe="1m",
        start_date=start_date,
        end_date=end_date,
        initial_balance=10000,
        stop_loss_pips=15,
        take_profit_pips=25
    )
    
    print(f"\nBacktest complete!")
    print(f"Total candles processed: {results.get('total_candles', 0)}")
    print(f"Total trades: {results.get('total_trades', 0)}")
    
    # Check debug log
    print(f"\n=== Debug Log Contents ===")
    with open('/tmp/dsl_debug.log', 'r') as f:
        log_contents = f.read()
        print(log_contents)
    
    # Count how many times on_candle_processed was called
    wrapper_calls = log_contents.count("WRAPPER on_candle_processed")
    strategy_calls = log_contents.count("!!! on_candle_processed CALLED")
    calculate_calls = log_contents.count(">>> _calculate_indicators START")
    
    print(f"\n=== Call Counts ===")
    print(f"WRAPPER on_candle_processed calls: {wrapper_calls}")
    print(f"Strategy on_candle_processed calls: {strategy_calls}")
    print(f"_calculate_indicators calls: {calculate_calls}")
    
    if wrapper_calls == 0:
        print("\n❌ PROBLEM: Wrapper on_candle_processed is NOT being called!")
    elif strategy_calls == 0:
        print("\n❌ PROBLEM: Strategy on_candle_processed is NOT being called!")
    elif calculate_calls == 0:
        print("\n❌ PROBLEM: _calculate_indicators is NOT being called!")
    else:
        print("\n✅ All methods are being called correctly")

if __name__ == "__main__":
    test_on_candle_processed()
