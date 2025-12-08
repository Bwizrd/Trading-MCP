#!/usr/bin/env python3
"""
Test script to verify diagnostic logging infrastructure for DSL strategy.
"""

import json
from datetime import datetime, timedelta
from shared.strategies.dsl_interpreter.dsl_strategy import DSLStrategy
from shared.models import Candle, TradeDirection
from shared.strategy_interface import StrategyContext

def create_test_candle(timestamp, close_price):
    """Create a test candle."""
    return Candle(
        timestamp=timestamp,
        open=close_price - 0.0001,
        high=close_price + 0.0001,
        low=close_price - 0.0002,
        close=close_price,
        volume=1000
    )

def test_diagnostic_logging():
    """Test that diagnostic logging is working."""
    print("Testing DSL Strategy Diagnostic Logging...")
    print("=" * 60)
    
    # Load MACD strategy configuration
    with open('shared/strategies/dsl_strategies/macd_crossover_strategy.json', 'r') as f:
        macd_config = json.load(f)
    
    print(f"Loaded strategy: {macd_config['name']}")
    print(f"Strategy type: Indicator-based")
    print()
    
    # Create strategy instance
    strategy = DSLStrategy(macd_config)
    print(f"✓ Strategy initialized")
    print(f"✓ Diagnostic log file created at: /tmp/dsl_debug.log")
    print()
    
    # Create test context
    start_time = datetime(2024, 1, 1, 9, 0)
    
    # Generate some test candles with a simple uptrend
    print("Processing test candles...")
    base_price = 1.0500
    
    for i in range(50):
        timestamp = start_time + timedelta(minutes=15 * i)
        # Create a simple price pattern
        price = base_price + (i * 0.00001)
        
        candle = create_test_candle(timestamp, price)
        context = StrategyContext(
            current_candle=candle,
            symbol="EURUSD",
            timeframe="15m",
            current_position=None,
            historical_candles=[],
            indicators={}
        )
        
        # Process candle (this will calculate indicators)
        strategy.on_candle_processed(context)
        
        # Try to generate signal
        signal = strategy.generate_signal(context)
        
        if signal:
            print(f"  Signal generated at candle {i}: {signal.direction} @ {signal.price:.5f}")
    
    print()
    print("=" * 60)
    print("Test complete!")
    print()
    print("Check the diagnostic log file:")
    print("  cat /tmp/dsl_debug.log")
    print()
    print("The log should contain:")
    print("  - Strategy initialization info")
    print("  - Indicator calculations for each candle")
    print("  - Indicator values (MACD, signal line, histogram)")
    print("  - Condition evaluations")
    print("  - Crossover detection attempts")
    print("  - Signal generation details (if any signals were generated)")
    print()
    
    # Show first few lines of the log
    print("First 30 lines of diagnostic log:")
    print("-" * 60)
    try:
        with open('/tmp/dsl_debug.log', 'r') as f:
            lines = f.readlines()
            for line in lines[:30]:
                print(line.rstrip())
    except Exception as e:
        print(f"Error reading log file: {e}")

if __name__ == "__main__":
    test_diagnostic_logging()
