#!/usr/bin/env python3
"""
Export backtest trades to JSON for comparison with live trading.

Usage:
    /Users/paul/Sites/PythonProjects/Trading-MCP/.venv/bin/python \\
        copilot-tests/export_backtest_trades.py \\
        --date 2025-12-19 \\
        --symbols US500_SB,NAS100_SB,GER40_SB,UK100_SB,US30_SB
"""
import asyncio
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.strategy_registry import StrategyRegistry
from mcp_servers.universal_backtest_engine import UniversalBacktestEngine, BacktestConfiguration
from shared.data_connector import DataConnector


async def export_trades_for_date(date_str: str, symbols: list, sl_pips: int = 15, tp_pips: int = 15):
    """
    Run backtest and export all trades to JSON.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        symbols: List of symbols (e.g., ['US500_SB', 'NAS100_SB'])
        sl_pips: Stop loss in pips
        tp_pips: Take profit in pips
    """
    print("=" * 80)
    print("📊 BACKTEST TRADE EXPORT")
    print("=" * 80)
    print(f"Date: {date_str}")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"SL/TP: {sl_pips}/{tp_pips} pips")
    print("=" * 80)
    print()
    
    registry = StrategyRegistry()
    data_connector = DataConnector()
    engine = UniversalBacktestEngine(data_connector=data_connector)
    
    all_trades = []
    
    for symbol in symbols:
        print(f"Running backtest for {symbol}...")
        
        config = BacktestConfiguration(
            symbol=symbol,
            timeframe="1m",
            start_date=date_str,
            end_date=date_str,
            initial_balance=10000,
            risk_per_trade=0.02,
            stop_loss_pips=sl_pips,
            take_profit_pips=tp_pips
        )
        
        strategy = registry.create_strategy("Stochastic Quad Rotation")
        backtest_results = await engine.run_backtest(strategy, config)
        
        # Extract trades
        for trade in backtest_results.trades:
            all_trades.append({
                'symbol': symbol,
                'direction': trade.direction.name,
                'entry_time': trade.entry_time.isoformat(),
                'entry_price': trade.entry_price,
                'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                'exit_price': trade.exit_price,
                'pips': trade.pips,
                'result': trade.result.name,
                'stop_loss': trade.stop_loss,
                'take_profit': trade.take_profit
            })
        
        print(f"  ✅ {len(backtest_results.trades)} trades found")
    
    print()
    print("=" * 80)
    print(f"📝 Total trades across all symbols: {len(all_trades)}")
    print("=" * 80)
    print()
    
    # Save to JSON
    output_file = project_root / "data" / f"backtest_trades_{date_str.replace('-', '')}.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(all_trades, f, indent=2)
    
    print(f"💾 Trades exported to: {output_file}")
    print()
    
    # Display summary
    print("📊 TRADE SUMMARY:")
    for trade in all_trades:
        entry_time = datetime.fromisoformat(trade['entry_time'])
        exit_time = datetime.fromisoformat(trade['exit_time']) if trade['exit_time'] else None
        
        exit_str = f" → {exit_time.strftime('%H:%M:%S')}" if exit_time else ""
        result_str = f" ({trade['result']}: {trade['pips']:+.1f} pips)" if trade['result'] != 'PENDING' else ""
        
        print(f"  {entry_time.strftime('%H:%M:%S')} | {trade['symbol']:12} | "
              f"{trade['direction']:4} @ {trade['entry_price']:.2f}{exit_str}{result_str}")
    
    return output_file


async def main():
    parser = argparse.ArgumentParser(description='Export backtest trades to JSON')
    parser.add_argument('--date', required=True, help='Date in YYYY-MM-DD format')
    parser.add_argument('--symbols', required=True, help='Comma-separated list of symbols (e.g., US500_SB,NAS100_SB)')
    parser.add_argument('--sl', type=int, default=15, help='Stop loss in pips (default: 15)')
    parser.add_argument('--tp', type=int, default=15, help='Take profit in pips (default: 15)')
    
    args = parser.parse_args()
    
    symbols = [s.strip() for s in args.symbols.split(',')]
    
    output_file = await export_trades_for_date(args.date, symbols, args.sl, args.tp)
    
    print()
    print("✅ Export complete!")
    print(f"   Load this file in your comparison tool to validate against live trades.")


if __name__ == "__main__":
    asyncio.run(main())
