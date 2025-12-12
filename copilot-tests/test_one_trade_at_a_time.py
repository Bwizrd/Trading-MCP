#!/usr/bin/env python3
"""
Test: One Trade at a Time Rule

Verify that the backtest engine properly populates context.current_position
and prevents overlapping trades when the strategy checks for active positions.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.backtest_engine import UniversalBacktestEngine
from shared.data_connector import DataConnector
from shared.strategies.dsl_interpreter.dsl_strategy import DSLStrategy
from shared.strategy_interface import BacktestConfiguration


async def test_one_trade_at_a_time():
    """Test that only one trade is active at a time."""
    
    print("=" * 80)
    print("TEST: One Trade at a Time Rule")
    print("=" * 80)
    
    # Load DSL strategy configuration
    strategy_path = Path(__file__).parent.parent / "shared" / "strategies" / "dsl_strategies" / "stochastic_quad_rotation.json"
    with open(strategy_path, 'r') as f:
        dsl_config = json.load(f)
    
    # Create strategy instance
    strategy = DSLStrategy(dsl_config)
    
    # Create configuration
    config = BacktestConfiguration(
        symbol="US500_SB",
        timeframe="1m",
        start_date="2025-12-11",
        end_date="2025-12-11",
        stop_loss_pips=15,
        take_profit_pips=25
    )
    
    # Create data connector and backtest engine
    data_connector = DataConnector()
    engine = UniversalBacktestEngine(data_connector)
    
    # Run backtest
    print("\nRunning backtest...")
    results = await engine.run_backtest(strategy, config)
    
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    
    # Convert to dict
    result_data = results.to_dict(include_market_data=False)
    
    total_trades = result_data['summary']['total_trades']
    trades = result_data['trades']
    
    print(f"\nTotal Trades: {total_trades}")
    print(f"Win Rate: {result_data['summary']['win_rate']:.1%}")
    print(f"Total Pips: {result_data['summary']['total_pips']:+.1f}")
    
    # Check for overlapping trades
    print("\n" + "=" * 80)
    print("CHECKING FOR OVERLAPPING TRADES")
    print("=" * 80)
    
    overlaps = []
    for i, trade1 in enumerate(trades):
        entry1 = trade1['entry_time']
        exit1 = trade1['exit_time']
        
        for j, trade2 in enumerate(trades):
            if i >= j:
                continue
            
            entry2 = trade2['entry_time']
            exit2 = trade2['exit_time']
            
            # Check if trades overlap
            if entry2 < exit1 and entry1 < exit2:
                overlaps.append((i+1, j+1, entry1, exit1, entry2, exit2))
    
    if overlaps:
        print(f"\n❌ FOUND {len(overlaps)} OVERLAPPING TRADES:")
        for idx1, idx2, entry1, exit1, entry2, exit2 in overlaps:
            print(f"  Trade #{idx1} ({entry1} -> {exit1}) overlaps with")
            print(f"  Trade #{idx2} ({entry2} -> {exit2})")
    else:
        print(f"\n✅ NO OVERLAPPING TRADES - All trades are sequential!")
    
    # Show trade timeline
    print("\n" + "=" * 80)
    print("TRADE TIMELINE")
    print("=" * 80)
    
    for i, trade in enumerate(trades[:10], 1):  # Show first 10 trades
        entry = trade['entry_time']
        exit = trade['exit_time']
        direction = trade['direction']
        pips = trade['pips']
        result = trade['result']
        
        print(f"Trade #{i}: {direction} @ {entry} -> {exit} = {pips:+.1f} pips ({result})")
    
    if len(trades) > 10:
        print(f"... and {len(trades) - 10} more trades")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    # Verify the fix worked
    if overlaps:
        print("\n❌ TEST FAILED: Trades are still overlapping")
        print("The backtest engine is not properly tracking active trades.")
    else:
        print("\n✅ TEST PASSED: One trade at a time rule is working!")
        print("The backtest engine correctly prevents overlapping positions.")


if __name__ == "__main__":
    asyncio.run(test_one_trade_at_a_time())
