#!/usr/bin/env python3
"""
Debug script to test trailing stop functionality with stochastic quad rotation strategy.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.backtest_engine import UniversalBacktestEngine
from shared.data_connector import DataConnector
from shared.strategy_registry import StrategyRegistry
from shared.strategy_interface import BacktestConfiguration

async def test_trailing_stop():
    """Test trailing stop with stochastic quad rotation strategy."""
    
    # Initialize components
    data_connector = DataConnector()
    engine = UniversalBacktestEngine(data_connector=data_connector)
    registry = StrategyRegistry()
    
    # Load stochastic quad rotation strategy
    strategy = registry.get_strategy("Stochastic Quad Rotation")
    
    if not strategy:
        print("❌ Failed to load stochastic_quad_rotation strategy")
        return
    
    print(f"✅ Loaded strategy: {strategy.__class__.__name__}")
    
    # Check trailing stop configuration
    if hasattr(strategy, 'trailing_stop'):
        print(f"📊 Trailing stop config: {strategy.trailing_stop}")
    else:
        print("⚠️  No trailing_stop attribute found on strategy")
    
    # Create backtest configuration
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)
    
    config = BacktestConfiguration(
        symbol="US500_SB",
        timeframe="1m",
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        initial_balance=10000,
        stop_loss_pips=8,
        take_profit_pips=8,
        trailing_stop=strategy.trailing_stop if hasattr(strategy, 'trailing_stop') else None
    )
    
    print(f"\n🔧 Config trailing_stop: {config.trailing_stop}")
    
    # Run backtest
    print(f"\n🚀 Running backtest from {config.start_date} to {config.end_date}...")
    results = await engine.run_backtest(strategy, config)
    
    # Analyze results
    print(f"\n📈 Results:")
    print(f"   Total trades: {results.total_trades}")
    print(f"   Win rate: {results.win_rate:.1%}")
    print(f"   Total pips: {results.total_pips:+.1f}")
    
    # Check first few trades for TP values
    print(f"\n🔍 First 5 trades:")
    for i, trade in enumerate(results.trades[:5]):
        print(f"   Trade {i+1}:")
        print(f"      Entry: {trade.entry_price:.5f} @ {trade.entry_time}")
        print(f"      Exit: {trade.exit_price:.5f} @ {trade.exit_time}")
        print(f"      SL: {trade.stop_loss:.5f}")
        print(f"      TP: {trade.take_profit}")
        print(f"      Trailing SL: {trade.trailing_stop_level}")
        print(f"      Pips: {trade.pips:+.2f}")
        print(f"      Result: {trade.result.name}")
        print()

if __name__ == "__main__":
    asyncio.run(test_trailing_stop())
