#!/usr/bin/env python3
"""
Simple test to check if on_candle_processed is being called.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Clear debug log before test
with open('/tmp/dsl_debug.log', 'w') as f:
    f.write("=== Test Start ===\n")

# Import and run backtest via MCP tool
import asyncio
import json

async def test():
    # Import the MCP tool
    from mcp_servers.universal_backtest_engine import run_strategy_backtest
    
    # Run backtest for today only
    result = await run_strategy_backtest(
        strategy_name="stochastic_quad_rotation",
        symbol="US500_SB",
        timeframe="1m",
        start_date="2025-12-11",
        end_date="2025-12-11",
        stop_loss_pips=15,
        take_profit_pips=25,
        auto_chart=False  # Don't create chart
    )
    
    print("Backtest complete!")
    print(f"Total trades: {result.get('total_trades', 'N/A')}")
    
    # Check debug log
    print(f"\n=== Debug Log Contents ===")
    with open('/tmp/dsl_debug.log', 'r') as f:
        log_contents = f.read()
        print(log_contents)
    
    # Count calls
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
    asyncio.run(test())
