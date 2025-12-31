#!/usr/bin/env python3
"""
Manual Stochastic Strategy Backtest Runner

This script runs the Stochastic Quad Rotation strategy directly without using MCP tools.
It uses the core backtest engine, data connector, and DSL strategy components.

Usage:
    python run_stochastic_manual.py [options]

Options:
    --symbol SYMBOL         Trading symbol (default: GER40_SB)
    --timeframe TIMEFRAME   Timeframe (default: 1m)
    --start-date DATE       Start date YYYY-MM-DD (default: 7 days ago)
    --end-date DATE         End date YYYY-MM-DD (default: today)
    --stop-loss PIPS        Stop loss in pips (default: 15.0)
    --take-profit PIPS      Take profit in pips (default: 25.0)
    --help                  Show this help message

Examples:
    # Run with defaults (last 7 days on GER40_SB)
    python run_stochastic_manual.py
    
    # Custom symbol and dates
    python run_stochastic_manual.py --symbol EURUSD_SB --start-date 2025-12-01 --end-date 2025-12-15
    
    # Custom risk parameters
    python run_stochastic_manual.py --stop-loss 20 --take-profit 30
    
    # Full custom run
    python run_stochastic_manual.py --symbol GBPUSD_SB --timeframe 5m --start-date 2025-12-20 --end-date 2025-12-27 --stop-loss 10 --take-profit 20
"""

import asyncio
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.backtest_engine import UniversalBacktestEngine
from shared.data_connector import DataConnector
from shared.strategy_interface import BacktestConfiguration
from shared.strategies.dsl_interpreter.dsl_strategy import DSLStrategy


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Run Stochastic Quad Rotation strategy backtest',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with defaults (last 7 days on GER40_SB)
  python run_stochastic_manual.py
  
  # Custom symbol and dates
  python run_stochastic_manual.py --symbol EURUSD_SB --start-date 2025-12-01 --end-date 2025-12-15
  
  # Custom risk parameters
  python run_stochastic_manual.py --stop-loss 20 --take-profit 30
  
  # Full custom run
  python run_stochastic_manual.py --symbol GBPUSD_SB --timeframe 5m --start-date 2025-12-20 --end-date 2025-12-27 --stop-loss 10 --take-profit 20
        """
    )
    
    # Calculate default dates
    default_end = datetime.now()
    default_start = default_end - timedelta(days=7)
    
    parser.add_argument(
        '--symbol',
        type=str,
        default='GER40_SB',
        help='Trading symbol (default: GER40_SB)'
    )
    
    parser.add_argument(
        '--timeframe',
        type=str,
        default='1m',
        choices=['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
        help='Timeframe for analysis (default: 1m)'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        default=default_start.strftime('%Y-%m-%d'),
        help=f'Start date in YYYY-MM-DD format (default: {default_start.strftime("%Y-%m-%d")})'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        default=default_end.strftime('%Y-%m-%d'),
        help=f'End date in YYYY-MM-DD format (default: {default_end.strftime("%Y-%m-%d")})'
    )
    
    parser.add_argument(
        '--stop-loss',
        type=float,
        default=15.0,
        help='Stop loss in pips (default: 15.0)'
    )
    
    parser.add_argument(
        '--take-profit',
        type=float,
        default=25.0,
        help='Take profit in pips (default: 25.0)'
    )
    
    return parser.parse_args()


async def run_manual_backtest(args):
    """Run a manual backtest of the stochastic strategy."""
    
    print("=" * 80)
    print("MANUAL STOCHASTIC STRATEGY BACKTEST")
    print("=" * 80)
    
    # 1. Load the stochastic strategy
    print("\n1. Loading Stochastic Quad Rotation strategy...")
    strategy_path = Path(__file__).parent.parent / "shared" / "strategies" / "dsl_strategies" / "stochastic_quad_rotation.json"
    
    with open(strategy_path, 'r') as f:
        strategy_config = json.load(f)
    
    strategy = DSLStrategy(strategy_config)
    print(f"   ✓ Strategy loaded: {strategy.get_name()} v{strategy.get_version()}")
    print(f"   Description: {strategy.get_description()}")
    
    # 2. Initialize data connector
    print("\n2. Initializing data connector...")
    data_connector = DataConnector()
    print("   ✓ Data connector initialized")
    
    # 3. Initialize backtest engine
    print("\n3. Initializing backtest engine...")
    engine = UniversalBacktestEngine(data_connector=data_connector)
    print("   ✓ Backtest engine initialized")
    
    # 4. Configure backtest parameters
    print("\n4. Configuring backtest parameters...")
    
    # Parse dates from command line arguments
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    except ValueError as e:
        print(f"   ❌ Invalid date format: {e}")
        print("   Please use YYYY-MM-DD format (e.g., 2025-12-25)")
        return None
    
    # Validate date range (allow same day)
    if start_date > end_date:
        print(f"   ❌ Start date must be before or equal to end date")
        return None
    
    # If same day, extend end date to end of day
    if start_date == end_date:
        end_date = end_date.replace(hour=23, minute=59, second=59)
    
    config = BacktestConfiguration(
        symbol=args.symbol,
        timeframe=args.timeframe,
        start_date=start_date,
        end_date=end_date,
        initial_balance=10000.0,
        stop_loss_pips=args.stop_loss,
        take_profit_pips=args.take_profit,
        risk_per_trade=0.02,  # 2% risk per trade
        max_open_trades=1
    )
    
    print(f"   Symbol: {config.symbol}")
    print(f"   Timeframe: {config.timeframe}")
    print(f"   Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"   Days: {(end_date - start_date).days}")
    print(f"   Initial Balance: ${config.initial_balance:,.2f}")
    print(f"   Stop Loss: {config.stop_loss_pips} pips")
    print(f"   Take Profit: {config.take_profit_pips} pips")
    
    # 5. Run the backtest
    print("\n5. Running backtest...")
    print("   This may take a few moments...")
    
    try:
        results = await engine.run_backtest(
            strategy=strategy,
            config=config,
            execution_timeframe="1m"
        )
        
        # 6. Display results
        print("\n" + "=" * 80)
        print("BACKTEST RESULTS")
        print("=" * 80)
        
        print(f"\nStrategy: {results.strategy_name} v{results.strategy_version}")
        print(f"Data Source: {results.data_source}")
        print(f"Execution Time: {results.execution_time_seconds:.2f} seconds")
        print(f"Candles Processed: {results.total_candles_processed:,}")
        
        print(f"\n--- TRADE STATISTICS ---")
        print(f"Total Trades: {results.total_trades}")
        print(f"Winning Trades: {results.winning_trades}")
        print(f"Losing Trades: {results.losing_trades}")
        print(f"Win Rate: {results.win_rate:.1%}")
        
        print(f"\n--- PERFORMANCE ---")
        print(f"Total Pips: {results.total_pips:+.1f}")
        print(f"Profit Factor: {results.profit_factor:.2f}")
        print(f"Average Win: {results.average_win:.1f} pips")
        print(f"Average Loss: {results.average_loss:.1f} pips")
        print(f"Largest Win: {results.largest_win:.1f} pips")
        print(f"Largest Loss: {results.largest_loss:.1f} pips")
        
        print(f"\n--- RISK METRICS ---")
        print(f"Max Drawdown: {results.max_drawdown:.1f} pips")
        print(f"Max Consecutive Wins: {results.max_consecutive_wins}")
        print(f"Max Consecutive Losses: {results.max_consecutive_losses}")
        
        # 7. Display trade details
        if results.trades:
            print(f"\n--- TRADE DETAILS ---")
            print(f"{'#':<4} {'Entry Time':<20} {'Dir':<5} {'Entry':<10} {'Exit':<10} {'Pips':<8} {'Result':<10}")
            print("-" * 80)
            
            for i, trade in enumerate(results.trades[:10], 1):  # Show first 10 trades
                entry_time_str = trade.entry_time.strftime('%Y-%m-%d %H:%M')
                direction_str = trade.direction.name
                entry_price_str = f"{trade.entry_price:.5f}"
                exit_price_str = f"{trade.exit_price:.5f}" if trade.exit_price else "N/A"
                pips_str = f"{trade.pips:+.1f}" if trade.pips else "N/A"
                result_str = trade.result.name if trade.result else "OPEN"
                
                print(f"{i:<4} {entry_time_str:<20} {direction_str:<5} {entry_price_str:<10} {exit_price_str:<10} {pips_str:<8} {result_str:<10}")
            
            if len(results.trades) > 10:
                print(f"... and {len(results.trades) - 10} more trades")
        
        print("\n" + "=" * 80)
        print("BACKTEST COMPLETE")
        print("=" * 80)
        
        return results
        
    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()
    
    # Run the async backtest
    results = asyncio.run(run_manual_backtest(args))
    
    # Exit with appropriate code
    sys.exit(0 if results else 1)
