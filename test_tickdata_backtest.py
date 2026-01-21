#!/usr/bin/env python3
"""
Test tick data backtesting with the universal backtest engine.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_connector import DataConnector
from shared.strategy_registry import StrategyRegistry
from shared.backtest_engine import UniversalBacktestEngine
from shared.strategy_interface import BacktestConfiguration


async def test_tick_data_backtest():
    """Test backtesting with tick data."""
    
    print("=" * 80)
    print("Testing Tick Data Backtesting")
    print("=" * 80)
    
    # Initialize components
    print("\n1️⃣ Initializing components...")
    connector = DataConnector()
    registry = StrategyRegistry()
    engine = UniversalBacktestEngine(connector)
    
    # Test parameters
    strategy_name = "stochastic_quad_rotation"
    symbol = "US500_SB"
    timeframe = "1m"  # Strategy signals on 1m
    
    # Test with a short time period (today)
    start_date = "2026-01-20"
    end_date = "2026-01-20"
    
    print(f"\n2️⃣ Test Configuration:")
    print(f"   Strategy: {strategy_name}")
    print(f"   Symbol: {symbol}")
    print(f"   Timeframe: {timeframe}")
    print(f"   Date Range: {start_date} to {end_date}")
    print(f"   Use Tick Data: TRUE")
    
    # Create strategy
    print(f"\n3️⃣ Creating strategy instance...")
    strategy = registry.create_strategy(strategy_name, {})
    print(f"   ✅ Strategy created: {type(strategy).__name__}")
    
    # Create backtest configuration WITH tick data
    print(f"\n4️⃣ Creating backtest configuration...")
    config = BacktestConfiguration(
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        initial_balance=10000,
        risk_per_trade=0.02,
        stop_loss_pips=15,
        take_profit_pips=25,
        use_tick_data=True  # CRITICAL: Enable tick data
    )
    print(f"   ✅ Config created with use_tick_data={config.use_tick_data}")
    
    # Run backtest
    print(f"\n5️⃣ Running backtest...")
    print(f"   (This will fetch tick data and convert to 1-second candles)")
    
    try:
        results = await engine.run_backtest(strategy, config)
        
        print(f"\n6️⃣ Backtest Results:")
        print(f"   Data Source: {results.data_source}")
        print(f"   Candles: {len(results.market_data)}")
        print(f"   Trades: {results.total_trades}")
        print(f"   Win Rate: {results.win_rate:.1%}")
        print(f"   Total Pips: {results.total_pips:+.1f}")
        
        if results.trades:
            print(f"\n   First 3 trades:")
            for i, trade in enumerate(results.trades[:3], 1):
                print(f"   {i}. {trade.direction.name} @ {trade.entry_price:.2f} → {trade.exit_price:.2f} = {trade.pips:+.1f} pips")
        
        print(f"\n✅ TEST PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED!")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_without_tick_data():
    """Test backtesting WITHOUT tick data for comparison."""
    
    print("\n" + "=" * 80)
    print("Testing WITHOUT Tick Data (Regular Backtest)")
    print("=" * 80)
    
    # Initialize components
    connector = DataConnector()
    registry = StrategyRegistry()
    engine = UniversalBacktestEngine(connector)
    
    strategy_name = "stochastic_quad_rotation"
    symbol = "US500_SB"
    timeframe = "15m"  # Use 15m for regular backtest
    start_date = "2026-01-20"
    end_date = "2026-01-20"
    
    print(f"\n   Strategy: {strategy_name}")
    print(f"   Symbol: {symbol}")
    print(f"   Timeframe: {timeframe}")
    print(f"   Use Tick Data: FALSE")
    
    strategy = registry.create_strategy(strategy_name, {})
    
    config = BacktestConfiguration(
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        initial_balance=10000,
        risk_per_trade=0.02,
        stop_loss_pips=15,
        take_profit_pips=25,
        use_tick_data=False  # Regular backtest
    )
    
    try:
        results = await engine.run_backtest(strategy, config)
        
        print(f"\n   Data Source: {results.data_source}")
        print(f"   Candles: {len(results.market_data)}")
        print(f"   Trades: {results.total_trades}")
        
        print(f"\n✅ Regular backtest works fine")
        return True
        
    except Exception as e:
        print(f"\n❌ Regular backtest failed: {e}")
        return False


async def main():
    """Run all tests."""
    
    # Test 1: Regular backtest (baseline)
    regular_ok = await test_without_tick_data()
    
    # Test 2: Tick data backtest
    tick_ok = await test_tick_data_backtest()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Regular Backtest: {'✅ PASS' if regular_ok else '❌ FAIL'}")
    print(f"Tick Data Backtest: {'✅ PASS' if tick_ok else '❌ FAIL'}")
    
    if regular_ok and tick_ok:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed - check output above")


if __name__ == "__main__":
    asyncio.run(main())
