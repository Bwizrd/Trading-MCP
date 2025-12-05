#!/usr/bin/env python3
"""
Direct test of MACD backtest to debug indicator issues
"""

import asyncio
from datetime import datetime, timedelta
from shared.backtest_engine import UniversalBacktestEngine
from shared.strategy_registry import StrategyRegistry
from shared.strategy_interface import BacktestConfiguration
from shared.data_connector import DataConnector

async def main():
    print("=" * 80)
    print("Direct MACD Backtest Test")
    print("=" * 80)
    
    # Initialize components
    connector = DataConnector()
    registry = StrategyRegistry()
    engine = UniversalBacktestEngine(data_connector=connector)
    
    # Get strategy
    strategy = registry.create_strategy("MACD Crossover Strategy")
    print(f"\n1. Strategy: {strategy.get_name()}")
    print(f"   Version: {strategy.get_version()}")
    print(f"   Required indicators: {strategy.requires_indicators()}")
    
    # Configure backtest
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    config = BacktestConfiguration(
        symbol="EURUSD",
        timeframe="15m",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        initial_balance=10000,
        risk_per_trade=0.02,
        stop_loss_pips=25,
        take_profit_pips=40
    )
    
    print(f"\n2. Running backtest...")
    print(f"   Symbol: {config.symbol}")
    print(f"   Timeframe: {config.timeframe}")
    print(f"   Period: {config.start_date} to {config.end_date}")
    
    # Run backtest
    results = await engine.run_backtest(strategy, config)
    
    print(f"\n3. Backtest complete!")
    print(f"   Total trades: {results.total_trades}")
    print(f"   Candles processed: {results.total_candles_processed}")
    
    # Check indicators
    print(f"\n4. Checking indicators...")
    if hasattr(results, 'indicators') and results.indicators:
        print(f"   ✓ Indicators found: {list(results.indicators.keys())}")
        for name, values in results.indicators.items():
            print(f"     - {name}: {len(values)} values")
            if len(values) > 0:
                print(f"       First 5: {values[:5]}")
    else:
        print(f"   ❌ No indicators in results!")
        print(f"   Results attributes: {dir(results)}")
    
    # Check to_dict
    print(f"\n5. Checking to_dict()...")
    results_dict = results.to_dict(include_market_data=True)
    if 'indicators' in results_dict:
        print(f"   ✓ Indicators in dict: {list(results_dict['indicators'].keys())}")
    else:
        print(f"   ❌ No indicators in dict!")
        print(f"   Dict keys: {list(results_dict.keys())}")

if __name__ == "__main__":
    asyncio.run(main())
