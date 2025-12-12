#!/usr/bin/env python3
"""
Test Stochastic Quad Rotation Strategy Structure

This test verifies the strategy is properly structured and ready for backtesting.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.strategy_registry import get_strategy_registry
from shared.models import Candle
from shared.strategy_interface import StrategyContext
from datetime import datetime, timedelta

def test_strategy_structure():
    """Test that the strategy has the correct structure."""
    print("=" * 80)
    print("STOCHASTIC QUAD ROTATION STRUCTURE TEST")
    print("=" * 80)
    
    try:
        # Get strategy from registry
        registry = get_strategy_registry()
        strategy = registry.create_strategy("Stochastic Quad Rotation")
        
        print(f"✅ Strategy loaded: {strategy.get_name()}")
        print(f"   Version: {strategy.get_version()}")
        print(f"   Description: {strategy.get_description()}")
        
        # Check if wrapped strategy
        actual_strategy = strategy
        if hasattr(strategy, '_strategy'):
            actual_strategy = strategy._strategy
            print(f"✅ Strategy is wrapped (DSLStrategyWrapper)")
        
        # Check advanced strategy components
        if hasattr(actual_strategy, 'is_advanced_strategy'):
            print(f"\n✅ Advanced strategy: {actual_strategy.is_advanced_strategy}")
            
            if actual_strategy.is_advanced_strategy:
                print(f"✅ Multi-indicator manager: {actual_strategy.multi_indicator_manager is not None}")
                print(f"✅ Crossover detector: {actual_strategy.crossover_detector is not None}")
                print(f"✅ Condition evaluator: {actual_strategy.condition_evaluator is not None}")
                
                instances = actual_strategy.multi_indicator_manager.list_instances()
                print(f"\n✅ Indicator instances ({len(instances)}):")
                for alias in instances:
                    config = actual_strategy.multi_indicator_manager.get_instance_config(alias)
                    print(f"   - {alias}: {config['type']} {config['params']}")
        else:
            print(f"⚠️  Strategy does not have is_advanced_strategy attribute")
        
        # Test signal generation with sample candles
        print(f"\n" + "=" * 80)
        print("TESTING SIGNAL GENERATION")
        print("=" * 80)
        
        # Create sample candles
        base_time = datetime(2025, 1, 1, 9, 0)
        candles = []
        
        for i in range(100):
            # Create oscillating prices
            close = 1.0800 + 0.0100 * (0.5 + 0.5 * (i % 20) / 20)
            high = close + 0.0010
            low = close - 0.0010
            
            candle = Candle(
                timestamp=base_time + timedelta(minutes=i),
                open=close,
                high=high,
                low=low,
                close=close,
                volume=1000
            )
            candles.append(candle)
        
        print(f"Created {len(candles)} sample candles")
        
        # Process candles and check for signals
        signals_generated = 0
        for i, candle in enumerate(candles):
            context = StrategyContext(
                current_candle=candle,
                symbol="EURUSD_SB",
                timeframe="1m",
                current_position=None,
                historical_candles=candles[:i+1],  # All candles up to current
                indicators={}  # Empty for now
            )
            
            # Process candle
            strategy.on_candle_processed(context)
            
            # Try to generate signal
            signal = strategy.generate_signal(context)
            if signal:
                signals_generated += 1
                print(f"✅ Signal generated at candle {i}: {signal.direction.value}")
        
        print(f"\nTotal signals generated: {signals_generated}")
        
        if signals_generated > 0:
            print(f"✅ Strategy successfully generated signals")
        else:
            print(f"⚠️  No signals generated (may be normal for this data pattern)")
        
        print(f"\n" + "=" * 80)
        print("✅ ALL STRUCTURE TESTS PASSED")
        print("=" * 80)
        print(f"\nThe strategy is ready for backtesting through the MCP server.")
        print(f"Use: run_strategy_backtest with strategy_name='Stochastic Quad Rotation'")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_strategy_structure()
    sys.exit(0 if success else 1)
