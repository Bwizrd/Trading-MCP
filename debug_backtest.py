#!/usr/bin/env python3
"""Debug backtest to see why MA Crossover generates 0 trades"""

import asyncio
from datetime import datetime, timedelta
from shared.data_connector import DataConnector
from shared.strategy_registry import StrategyRegistry
from shared.backtest_engine import UniversalBacktestEngine
from shared.strategy_interface import BacktestConfiguration

async def main():
    # Initialize
    connector = DataConnector()
    registry = StrategyRegistry()
    engine = UniversalBacktestEngine(connector)
    
    # Create strategy
    strategy = registry.create_strategy("MA Crossover Strategy")
    print(f"Strategy: {strategy.get_name()}")
    print(f"Is indicator-based: {strategy.is_indicator_based}")
    
    # Configure backtest
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=14)
    
    config = BacktestConfiguration(
        symbol="EURUSD",
        timeframe="15m",
        start_date=start_dt.strftime('%Y-%m-%d'),
        end_date=end_dt.strftime('%Y-%m-%d'),
        initial_balance=10000,
        risk_per_trade=0.02,
        stop_loss_pips=15,
        take_profit_pips=25
    )
    
    print(f"\nRunning backtest...")
    print(f"Period: {config.start_date} to {config.end_date}")
    
    # Run backtest
    results = await engine.run_backtest(strategy, config)
    
    print(f"\n✅ Backtest complete!")
    print(f"Total trades: {results.total_trades}")
    print(f"Candles processed: {len(results.market_data)}")
    
    # Check strategy state
    print(f"\nStrategy state after backtest:")
    print(f"Indicator values: {strategy.indicator_values}")
    print(f"Previous indicator values: {strategy.previous_indicator_values}")
    print(f"Candle history length: {len(strategy.candle_history)}")
    print(f"Daily trade count: {strategy.daily_trade_count}")
    print(f"Last trade date: {strategy.last_trade_date}")

if __name__ == "__main__":
    asyncio.run(main())
