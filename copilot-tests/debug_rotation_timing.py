#!/usr/bin/env python3
"""
Debug script to verify the timing of previous_indicator_values updates.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from shared.data_connector import DataConnector
from shared.strategies.dsl_interpreter.dsl_loader import load_dsl_strategy
from shared.strategy_interface import StrategyContext
from shared.models import Candle

def debug_rotation_timing():
    """Test the timing of indicator value updates."""
    
    # Clear debug files
    for debug_file in ['/tmp/rotation_debug.txt', '/tmp/indicator_values_debug.txt', '/tmp/evaluate_conditions_debug.txt']:
        try:
            with open(debug_file, 'w') as f:
                f.write(f"=== Debug Rotation Timing Test ===\n\n")
        except:
            pass
    
    # Load strategy
    strategy_path = Path(__file__).parent.parent / "shared/strategies/dsl_strategies/stochastic_quad_rotation.json"
    strategy = load_dsl_strategy(str(strategy_path))
    
    print(f"Strategy loaded: {strategy.get_name()}")
    
    # Get data for December 30, 2025
    connector = DataConnector()
    start_date = datetime(2025, 12, 30, 0, 0)
    end_date = datetime(2025, 12, 30, 23, 59)
    
    print(f"\nFetching data for GER40_SB from {start_date} to {end_date}...")
    candles = connector.get_historical_data(
        symbol="GER40_SB",
        timeframe="1m",
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"Got {len(candles)} candles")
    
    # Process first 10 candles and track indicator values
    signal_count = 0
    
    for i, candle in enumerate(candles[:20]):  # First 20 candles
        # Create context
        context = StrategyContext(
            current_candle=candle,
            historical_candles=candles[:i+1],
            indicators={},
            current_position=None,
            symbol="GER40_SB",
            timeframe="1m"
        )
        
        print(f"\n{'='*80}")
        print(f"Candle {i+1}: {candle.timestamp}")
        print(f"  OHLC: {candle.open:.2f} / {candle.high:.2f} / {candle.low:.2f} / {candle.close:.2f}")
        
        # Check indicator values BEFORE processing
        print(f"  BEFORE on_candle_processed:")
        print(f"    indicator_values: {strategy.indicator_values if hasattr(strategy, 'indicator_values') else 'N/A'}")
        print(f"    previous_indicator_values: {strategy.previous_indicator_values if hasattr(strategy, 'previous_indicator_values') else 'N/A'}")
        
        # Process candle (calculates indicators)
        strategy.on_candle_processed(context)
        
        # Check indicator values AFTER processing
        print(f"  AFTER on_candle_processed:")
        if hasattr(strategy, 'indicator_values') and strategy.indicator_values:
            print(f"    indicator_values:")
            for key, val in strategy.indicator_values.items():
                print(f"      {key}: {val:.2f}")
        if hasattr(strategy, 'previous_indicator_values') and strategy.previous_indicator_values:
            print(f"    previous_indicator_values:")
            for key, val in strategy.previous_indicator_values.items():
                print(f"      {key}: {val:.2f}")
        
        # Try to generate signal
        signal = strategy.generate_signal(context)
        
        if signal:
            signal_count += 1
            print(f"  *** SIGNAL {signal_count}: {signal.direction} @ {signal.price:.2f} ***")
        else:
            print(f"  No signal")
    
    print(f"\n{'='*80}")
    print(f"Total signals in first 20 candles: {signal_count}")
    
    # Read debug files
    print(f"\n{'='*80}")
    print("Debug file contents:")
    
    for debug_file in ['/tmp/rotation_debug.txt', '/tmp/indicator_values_debug.txt']:
        try:
            with open(debug_file, 'r') as f:
                content = f.read()
                if content.strip():
                    print(f"\n{debug_file}:")
                    print(content[:2000])  # First 2000 chars
        except:
            pass

if __name__ == "__main__":
    debug_rotation_timing()
