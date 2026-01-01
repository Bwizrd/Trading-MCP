#!/usr/bin/env python3
"""
Quick backtest to test the SSH upload feature.
Runs NAS100 1m for 2025-12-31 with 8 pip SL/TP.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from shared.backtest_engine import UniversalBacktestEngine
from shared.chart_engine import ChartEngine
from shared.models import BacktestConfiguration, TradeDirection
from shared.strategy_registry import StrategyRegistry

def main():
    """Run a test backtest for NAS100."""

    print("\n" + "="*80)
    print("TEST BACKTEST - NAS100 1m")
    print("="*80)
    print("Symbol: NAS100")
    print("Date: 2025-12-31")
    print("Timeframe: 1m")
    print("SL/TP: 8/8 pips")
    print("="*80 + "\n")

    # Load strategy
    registry = StrategyRegistry()
    strategy = registry.get_strategy("MACD Crossover")

    if not strategy:
        print("❌ MACD Crossover strategy not found. Using default.")
        # Try DSL strategy
        from shared.strategies.dsl_interpreter.dsl_strategy import DSLStrategy
        strategy = DSLStrategy("macd_crossover")

    # Create configuration
    config = BacktestConfiguration(
        symbol="NAS100",
        timeframe="1m",
        start_date=datetime(2025, 12, 31, 0, 0, 0),
        end_date=datetime(2025, 12, 31, 23, 59, 59),
        stop_loss_pips=8.0,
        take_profit_pips=8.0
    )

    print("⚙️  Configuration loaded")
    print(f"   Strategy: {strategy.__class__.__name__}")
    print(f"   Period: {config.start_date} to {config.end_date}")
    print(f"   SL/TP: {config.stop_loss_pips}/{config.take_profit_pips} pips\n")

    # Create engine
    engine = UniversalBacktestEngine()

    print("🚀 Starting backtest...\n")

    # Run backtest
    results = engine.run_backtest(strategy, config)

    print(f"\n✅ Backtest complete!")
    print(f"   Total trades: {results.total_trades}")
    print(f"   Winners: {results.winning_trades}")
    print(f"   Losers: {results.losing_trades}")
    print(f"   Win rate: {results.win_rate:.1f}%")
    print(f"   Total pips: {results.total_pips:.1f}")

    # Generate chart
    print(f"\n📊 Generating chart...")
    chart_engine = ChartEngine()
    chart_path = chart_engine.create_comprehensive_chart(
        backtest_results=results,
        strategy_name="MACD Crossover",
        symbol="NAS100",
        timeframe="1m"
    )

    print(f"\n✅ Chart saved: {chart_path}")
    print(f"\n{'='*80}")
    print(f"NEXT STEPS:")
    print(f"1. Start the API server: python api_server.py")
    print(f"2. Open the chart in your browser: {chart_path}")
    print(f"3. Click the '🚀 Send to SSH' button")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
