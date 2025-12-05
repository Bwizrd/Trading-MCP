#!/usr/bin/env python3
"""Test the spacing fix for MACD subplot"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from datetime import datetime, timedelta
from shared.data_connector import DataConnector
from shared.strategy_registry import StrategyRegistry
from shared.backtest_engine import UniversalBacktestEngine
from shared.strategy_interface import BacktestConfiguration
import asyncio

async def test_spacing():
    # Initialize components
    connector = DataConnector()
    registry = StrategyRegistry()
    engine = UniversalBacktestEngine(connector)
    
    # Create MACD strategy
    strategy = registry.create_strategy('MACD Crossover Strategy')
    
    # Configure backtest
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    config = BacktestConfiguration(
        symbol='EURUSD',
        timeframe='30m',
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        initial_balance=10000.0,
        risk_per_trade=0.02,
        stop_loss_pips=15.0,
        take_profit_pips=25.0
    )
    
    # Run backtest with auto_chart=True
    print('🔧 Running MACD backtest with improved spacing...')
    results = await engine.run_backtest(strategy, config, auto_chart=True)
    
    if results:
        print(f'✅ Backtest complete: {results.total_pips:+.1f} pips ({results.win_rate:.1%} win rate)')
        print(f'📊 Chart generated - check data/charts/ directory')
        print(f'🎯 Total trades: {results.total_trades}')
        
        # Find the most recent chart file
        from pathlib import Path
        charts_dir = Path('data/charts')
        if charts_dir.exists():
            chart_files = sorted(charts_dir.glob('*.html'), key=lambda p: p.stat().st_mtime, reverse=True)
            if chart_files:
                print(f'📁 Latest chart: {chart_files[0]}')
    else:
        print('❌ Backtest failed')

if __name__ == '__main__':
    asyncio.run(test_spacing())
