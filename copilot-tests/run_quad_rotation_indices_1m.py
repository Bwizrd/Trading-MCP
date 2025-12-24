#!/usr/bin/env python3
"""
Run bulk backtest for Stochastic Quad Rotation strategy on indices with 1-minute timeframe.
Testing 2025-12-18 data.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.universal_backtest_engine import handle_bulk_backtest
from shared.strategy_registry import StrategyRegistry
from mcp_servers.universal_backtest_engine import UniversalBacktestEngine
from shared.data_connector import DataConnector


async def main():
    """Run bulk backtest for Stochastic Quad Rotation on indices."""
    
    # Initialize components
    registry = StrategyRegistry()
    data_connector = DataConnector()
    engine = UniversalBacktestEngine(data_connector=data_connector)
    
    # Test date range: December 9-11, 2025 (known to have data)
    start_date = "2025-12-09"
    end_date = "2025-12-11"
    
    # All index symbols
    symbols = [
        "US500_SB",    # S&P 500
        "NAS100_SB",   # Nasdaq 100
        "GER40_SB",    # DAX 40
    ]
    
    # Timeframe
    timeframes = ["1m"]
    
    # SL/TP: 15 pips each (1:1 ratio)
    sl_tp_combinations = [
        {"stop_loss_pips": 15, "take_profit_pips": 15}
    ]
    
    print("=" * 80)
    print("🚀 STOCHASTIC QUAD ROTATION - INDICES BULK BACKTEST")
    print("=" * 80)
    print(f"Strategy: Stochastic Quad Rotation")
    print(f"Date: {start_date} to {end_date}")
    print(f"Timeframe: 1-minute")
    print(f"SL/TP: 15 pips / 15 pips (1:1 ratio)")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Total Tests: {len(symbols) * len(timeframes)}")
    print("=" * 80)
    print()
    
    # Create arguments dictionary
    arguments = {
        "strategy_name": "Stochastic Quad Rotation",
        "symbols": symbols,
        "timeframes": timeframes,
        "start_date": start_date,
        "end_date": end_date,
        "sl_tp_combinations": sl_tp_combinations
    }
    
    # Debug: Check strategy before running
    print("\n🔍 DEBUG: Checking strategy...")
    test_strategy = registry.create_strategy("Stochastic Quad Rotation")
    print(f"   Strategy type: {type(test_strategy)}")
    print(f"   Strategy name: {test_strategy.get_name()}")
    if hasattr(test_strategy, '_strategy'):
        print(f"   Wrapped strategy: {type(test_strategy._strategy)}")
        if hasattr(test_strategy._strategy, 'multi_indicator_manager'):
            print(f"   Has MultiIndicatorManager: {test_strategy._strategy.multi_indicator_manager is not None}")
    print()
    
    # Run bulk backtest
    try:
        results = await handle_bulk_backtest(registry, engine, arguments)
        
        # Display results
        print("\n" + "=" * 80)
        print("📊 RESULTS")
        print("=" * 80)
        for result in results:
            print(result.text)
            print()
        
    except Exception as e:
        print(f"\n❌ Error during bulk backtest: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
