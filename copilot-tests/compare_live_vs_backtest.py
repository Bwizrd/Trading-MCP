#!/usr/bin/env python3
"""
Compare live trading signals with backtest trades.

This script cross-references real-time trading signals from a live system
with backtest results to validate strategy performance.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.universal_backtest_engine import handle_bulk_backtest
from shared.strategy_registry import StrategyRegistry
from mcp_servers.universal_backtest_engine import UniversalBacktestEngine
from shared.data_connector import DataConnector


def parse_live_signals(log_text: str) -> List[Dict[str, Any]]:
    """
    Parse live trading signals from log text.
    
    Args:
        log_text: Multi-line string containing live trading logs
        
    Returns:
        List of trade dictionaries with timestamp, symbol, direction, price
    """
    trades = []
    
    for line in log_text.strip().split('\n'):
        if '✅ TRADE ENTERED' in line:
            # Example: [2025-12-19 08:44:00] ✅ TRADE ENTERED - NAS100 (205) - Sell @ 25131.80
            parts = line.split(']', 1)
            if len(parts) < 2:
                continue
                
            timestamp_str = parts[0].strip('[')
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            rest = parts[1].strip()
            # Extract symbol, direction, and price
            if '-' in rest:
                components = [c.strip() for c in rest.split('-')]
                if len(components) >= 4:
                    symbol_part = components[1]  # "NAS100 (205)"
                    symbol = symbol_part.split('(')[0].strip()
                    
                    direction = components[2].strip()  # "Sell"
                    
                    price_part = components[3].split('@')[1].strip()  # "25131.80"
                    price = float(price_part)
                    
                    trades.append({
                        'timestamp': timestamp,
                        'symbol': f"{symbol}_SB",  # Add _SB suffix for backtest comparison
                        'direction': direction.upper(),
                        'price': price
                    })
        
        elif '🚪 TRADE CLOSED' in line:
            # Example: [2025-12-19 08:50:02] 🚪 TRADE CLOSED - US30 (219) - LOSS @ 47977.10 | PnL: -18.0 pips
            parts = line.split(']', 1)
            if len(parts) < 2:
                continue
                
            timestamp_str = parts[0].strip('[')
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            rest = parts[1].strip()
            if '-' in rest and 'PnL:' in rest:
                components = [c.strip() for c in rest.split('-')]
                if len(components) >= 4:
                    symbol_part = components[1]  # "US30 (219)"
                    symbol = symbol_part.split('(')[0].strip()
                    
                    result = components[2].strip()  # "LOSS @ 47977.10 | PnL"
                    
                    # Get PnL
                    pnl_part = rest.split('PnL:')[1].strip()
                    pnl = float(pnl_part.split()[0])
                    
                    # Update the last trade for this symbol
                    for trade in reversed(trades):
                        if trade['symbol'] == f"{symbol}_SB" and 'exit_time' not in trade:
                            trade['exit_time'] = timestamp
                            trade['pnl'] = pnl
                            trade['result'] = 'WIN' if pnl > 0 else 'LOSS'
                            break
    
    return trades


def match_trades(live_trades: List[Dict], backtest_trades: List[Dict]) -> Dict[str, Any]:
    """
    Match live trades with backtest trades.
    
    Matches are based on:
    - Symbol
    - Entry time (within 1 minute tolerance)
    - Direction
    
    Args:
        live_trades: List of live trading signals
        backtest_trades: List of backtest trades
        
    Returns:
        Dictionary with matched, unmatched live, and unmatched backtest trades
    """
    matches = []
    unmatched_live = []
    matched_backtest_ids = set()
    
    for live_trade in live_trades:
        best_match = None
        min_time_diff = timedelta(minutes=2)  # 2 minute tolerance
        
        for i, bt_trade in enumerate(backtest_trades):
            if i in matched_backtest_ids:
                continue
            
            # Check symbol and direction
            if bt_trade['symbol'] != live_trade['symbol']:
                continue
            if bt_trade['direction'] != live_trade['direction']:
                continue
            
            # Check time proximity
            time_diff = abs(bt_trade['entry_time'] - live_trade['timestamp'])
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                best_match = (i, bt_trade, time_diff)
        
        if best_match:
            i, bt_trade, time_diff = best_match
            matched_backtest_ids.add(i)
            matches.append({
                'live': live_trade,
                'backtest': bt_trade,
                'time_diff_seconds': time_diff.total_seconds()
            })
        else:
            unmatched_live.append(live_trade)
    
    unmatched_backtest = [bt for i, bt in enumerate(backtest_trades) if i not in matched_backtest_ids]
    
    return {
        'matches': matches,
        'unmatched_live': unmatched_live,
        'unmatched_backtest': unmatched_backtest,
        'match_rate': len(matches) / len(live_trades) * 100 if live_trades else 0
    }


async def run_backtest_for_date(date_str: str, symbols: List[str]) -> List[Dict]:
    """
    Run backtest for a specific date and extract trades.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        symbols: List of symbols to test
        
    Returns:
        List of trade dictionaries
    """
    registry = StrategyRegistry()
    data_connector = DataConnector()
    engine = UniversalBacktestEngine(data_connector=data_connector)
    
    arguments = {
        "strategy_name": "Stochastic Quad Rotation",
        "symbols": symbols,
        "timeframes": ["1m"],
        "start_date": date_str,
        "end_date": date_str,
        "sl_tp_combinations": [
            {"stop_loss_pips": 15, "take_profit_pips": 15}
        ]
    }
    
    print(f"Running backtest for {date_str}...")
    results = await handle_bulk_backtest(registry, engine, arguments)
    
    # Extract trades from results
    # Note: The results are TextContent objects, we need to parse them
    # For now, return empty list - you'll need to access the actual BacktestResults objects
    
    print("✅ Backtest complete")
    return []


async def main():
    """Main comparison workflow."""
    
    # Your live trading log from 2025-12-19
    live_log = """[2025-12-19 08:36:00] SETUP ENTERED - US30 (219) - Sell
[2025-12-19 08:40:00] SETUP ENTERED - US500 (220) - Sell
[2025-12-19 08:43:00] SETUP ENTERED - NAS100 (205) - Sell
[2025-12-19 08:44:00] ✅ TRADE ENTERED - NAS100 (205) - Sell @ 25131.80
[2025-12-19 08:44:00] 🔔 SIGNAL - NAS100 (205) - Sell @ 25131.80
[2025-12-19 08:46:02] ✅ TRADE ENTERED - US500 (220) - Sell @ 6793.50
[2025-12-19 08:49:00] ✅ TRADE ENTERED - US30 (219) - Sell @ 47975.30
[2025-12-19 08:49:00] ✅ TRADE ENTERED - US500 (220) - Sell @ 6793.40
[2025-12-19 08:50:02] 🚪 TRADE CLOSED - US30 (219) - LOSS @ 47977.10 | PnL: -18.0 pips
[2025-12-19 08:58:00] ✅ TRADE ENTERED - NAS100 (205) - Sell @ 25143.50
[2025-12-19 08:58:12] 🚪 TRADE CLOSED - NAS100 (205) - LOSS @ 25145.00 | PnL: -15.0 pips
[2025-12-19 08:58:59] ✅ TRADE ENTERED - US500 (220) - Sell @ 6794.80
[2025-12-19 08:59:00] ✅ TRADE ENTERED - US30 (219) - Sell @ 47985.80
[2025-12-19 08:59:03] 🚪 TRADE CLOSED - US30 (219) - WIN @ 47984.10 | PnL: 17.0 pips
[2025-12-19 08:59:57] 🚪 TRADE CLOSED - US500 (220) - WIN @ 6793.30 | PnL: 15.0 pips
[2025-12-19 09:33:00] ✅ TRADE ENTERED - GER40 (200) - Sell @ 24262.80
[2025-12-19 09:34:02] 🚪 TRADE CLOSED - GER40 (200) - WIN @ 24259.40 | PnL: 34.0 pips
[2025-12-19 09:39:02] ✅ TRADE ENTERED - GER40 (200) - Sell @ 24261.90
[2025-12-19 09:39:10] 🚪 TRADE CLOSED - GER40 (200) - LOSS @ 24264.90 | PnL: -30.0 pips
[2025-12-19 09:50:00] ✅ TRADE ENTERED - GER40 (200) - Sell @ 24263.70
[2025-12-19 09:50:09] 🚪 TRADE CLOSED - GER40 (200) - WIN @ 24261.50 | PnL: 22.0 pips
[2025-12-19 09:56:01] ✅ TRADE ENTERED - UK100 (217) - Sell @ 9838.40
[2025-12-19 09:57:09] 🚪 TRADE CLOSED - UK100 (217) - LOSS @ 9840.00 | PnL: -16.0 pips
[2025-12-19 10:27:10] ✅ TRADE ENTERED - UK100 (217) - Sell @ 9840.90
[2025-12-19 10:27:32] 🚪 TRADE CLOSED - UK100 (217) - LOSS @ 9842.40 | PnL: -15.0 pips
[2025-12-19 10:53:59] ✅ TRADE ENTERED - UK100 (217) - Sell @ 9846.30
[2025-12-19 10:54:09] 🚪 TRADE CLOSED - UK100 (217) - WIN @ 9844.50 | PnL: 18.0 pips
[2025-12-19 11:05:00] ✅ TRADE ENTERED - GER40 (200) - Buy @ 24198.20
[2025-12-19 11:05:00] 🚪 TRADE CLOSED - GER40 (200) - WIN @ 24200.40 | PnL: 22.0 pips
[2025-12-19 11:11:00] ✅ TRADE ENTERED - GER40 (200) - Buy @ 24180.10
[2025-12-19 12:05:00] ✅ TRADE ENTERED - UK100 (217) - Sell @ 9841.10"""
    
    print("=" * 80)
    print("📊 LIVE vs BACKTEST TRADE COMPARISON")
    print("=" * 80)
    print()
    
    # Parse live trades
    print("📝 Parsing live trading signals...")
    live_trades = parse_live_signals(live_log)
    print(f"   Found {len(live_trades)} live trades")
    print()
    
    # Display live trades
    print("🔴 LIVE TRADES:")
    for i, trade in enumerate(live_trades, 1):
        exit_info = ""
        if 'exit_time' in trade:
            exit_info = f" → {trade['exit_time'].strftime('%H:%M:%S')} ({trade['result']}: {trade['pnl']:+.1f} pips)"
        print(f"   {i}. {trade['timestamp'].strftime('%H:%M:%S')} | {trade['symbol']:12} | {trade['direction']:4} @ {trade['price']:.2f}{exit_info}")
    print()
    
    # Run backtest for the same date
    symbols = ["US500_SB", "US30_SB", "NAS100_SB", "GER40_SB", "UK100_SB"]
    
    print(f"🔄 Running backtest for 2025-12-19 with same symbols...")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Strategy: Stochastic Quad Rotation")
    print(f"   SL/TP: 15/15 pips")
    print()
    
    backtest_trades = await run_backtest_for_date("2025-12-19", symbols)
    
    # TODO: Extract actual trade data from backtest results
    # For now, this script shows the structure
    
    print("=" * 80)
    print("✅ Comparison complete!")
    print("=" * 80)
    print()
    print("📊 Summary:")
    print(f"   Live Trades:     {len(live_trades)}")
    print(f"   Backtest Trades: {len(backtest_trades)}")
    print()
    print("💡 Next step: Extract trade data from backtest results to complete comparison")


if __name__ == "__main__":
    asyncio.run(main())
