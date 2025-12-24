#!/usr/bin/env python3
"""
Compare live trading signals with backtest results for December 19, 2025
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict

# Your live trading logs from December 19, 2025
LIVE_TRADES_LOG = """
✅ TRADE ENTERED - NAS100 (205) - Sell @ 25131.80 (SL: 25146.80 | TP: 25116.80)
2025-12-19T14:36:09.302Z 

✅ TRADE ENTERED - NAS100 (206) - Sell @ 25215.70 (SL: 25230.70 | TP: 25200.70)
2025-12-19T14:36:41.302Z 

✅ TRADE ENTERED - US500 (205) - Sell @ 6808.20 (SL: 6823.20 | TP: 6793.20)
2025-12-19T14:36:44.304Z 

✅ TRADE ENTERED - US30 (206) - Sell @ 48180.30 (SL: 48195.30 | TP: 48165.30)
2025-12-19T14:37:23.302Z 

✅ TRADE ENTERED - NAS100 (207) - Sell @ 25218.70 (SL: 25233.70 | TP: 25203.70)
2025-12-19T14:40:50.302Z 

✅ TRADE ENTERED - GER40 (206) - Sell @ 24262.50 (SL: 24277.50 | TP: 24247.50)
2025-12-19T14:32:38.302Z 

✅ TRADE ENTERED - GER40 (207) - Sell @ 24275.60 (SL: 24290.60 | TP: 24260.60)
2025-12-19T14:42:14.302Z 

✅ TRADE ENTERED - US30 (207) - Sell @ 48189.30 (SL: 48204.30 | TP: 48174.30)
2025-12-19T14:45:20.302Z 

✅ TRADE ENTERED - GER40 (208) - Sell @ 24273.40 (SL: 24288.40 | TP: 24258.40)
2025-12-19T14:45:23.303Z 

✅ TRADE ENTERED - NAS100 (208) - Sell @ 25315.90 (SL: 25330.90 | TP: 25300.90)
2025-12-19T14:51:20.302Z 

🚪 TRADE CLOSED - US500 (205) - Sell exit @ 6823.20 | Result: LOSS (-15.0 pips)
2025-12-19T14:52:14.302Z 

✅ TRADE ENTERED - US30 (208) - Sell @ 48186.80 (SL: 48201.80 | TP: 48171.80)
2025-12-19T14:54:17.302Z 

✅ TRADE ENTERED - UK100 (206) - Sell @ 9870.30 (SL: 9885.30 | TP: 9855.30)
2025-12-19T14:54:26.302Z 

✅ TRADE ENTERED - US30 (209) - Sell @ 48196.00 (SL: 48211.00 | TP: 48181.00)
2025-12-19T15:00:17.302Z 

🚪 TRADE CLOSED - US30 (209) - Sell exit @ 48211.00 | Result: LOSS (-15.0 pips)
2025-12-19T15:01:17.302Z 

✅ TRADE ENTERED - US30 (210) - Sell @ 48232.10 (SL: 48247.10 | TP: 48217.10)
2025-12-19T15:02:17.302Z 

✅ TRADE ENTERED - US30 (211) - Sell @ 48246.10 (SL: 48261.10 | TP: 48231.10)
2025-12-19T15:05:17.302Z 

🚪 TRADE CLOSED - UK100 (206) - Sell exit @ 9885.30 | Result: LOSS (-15.0 pips)
2025-12-19T15:06:26.302Z 

✅ TRADE ENTERED - UK100 (207) - Sell @ 9884.40 (SL: 9899.40 | TP: 9869.40)
2025-12-19T15:07:26.302Z
"""


def parse_live_trades(log_text: str) -> List[Dict]:
    """Parse live trading logs into structured trade data"""
    trades = []
    lines = log_text.strip().split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('✅ TRADE ENTERED'):
            # Extract trade details
            parts = line.split(' - ')
            if len(parts) >= 3:
                # Extract symbol and ID
                symbol_part = parts[1].split('(')[0].strip()
                
                # Normalize symbol names
                symbol_map = {
                    'NAS100': 'NAS100_SB',
                    'US500': 'US500_SB',
                    'US30': 'US30_SB',
                    'GER40': 'GER40_SB',
                    'UK100': 'UK100_SB'
                }
                symbol = symbol_map.get(symbol_part, symbol_part)
                
                # Extract direction and price
                trade_details = parts[2]
                direction = 'BUY' if 'Buy' in trade_details else 'SELL'
                entry_price = float(trade_details.split('@')[1].split('(')[0].strip())
                
                # Extract SL and TP
                sl_tp = trade_details.split('(SL:')[1].rstrip(')')
                sl = float(sl_tp.split('|')[0].strip())
                tp = float(sl_tp.split('TP:')[1].strip())
                
                # Get timestamp from next line
                timestamp_str = lines[i + 1].strip()
                entry_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                trades.append({
                    'symbol': symbol,
                    'direction': direction,
                    'entry_time': entry_time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'entry_price': entry_price,
                    'stop_loss': sl,
                    'take_profit': tp
                })
        
        i += 1
    
    return trades


def match_trades(live_trades: List[Dict], backtest_trades: List[Dict], 
                 time_tolerance_minutes: int = 2) -> Dict:
    """
    Match live trades with backtest trades based on:
    - Symbol
    - Direction
    - Entry time (within tolerance)
    - Entry price (approximately)
    """
    matches = []
    unmatched_live = []
    unmatched_backtest = list(backtest_trades)
    
    for live_trade in live_trades:
        live_time = datetime.fromisoformat(live_trade['entry_time'])
        best_match = None
        best_match_score = 0
        
        for bt_trade in unmatched_backtest:
            bt_time = datetime.fromisoformat(bt_trade['entry_time'])
            
            # Check basic criteria
            if (bt_trade['symbol'] == live_trade['symbol'] and 
                bt_trade['direction'] == live_trade['direction']):
                
                # Check time proximity
                time_diff = abs((live_time - bt_time).total_seconds() / 60)
                if time_diff <= time_tolerance_minutes:
                    # Check price proximity (within 2 pips)
                    price_diff = abs(bt_trade['entry_price'] - live_trade['entry_price'])
                    if price_diff <= 2.0:
                        match_score = 100 - time_diff - price_diff
                        if match_score > best_match_score:
                            best_match = bt_trade
                            best_match_score = match_score
        
        if best_match:
            matches.append({
                'live': live_trade,
                'backtest': best_match,
                'time_diff_seconds': (datetime.fromisoformat(live_trade['entry_time']) - 
                                     datetime.fromisoformat(best_match['entry_time'])).total_seconds(),
                'price_diff': abs(live_trade['entry_price'] - best_match['entry_price'])
            })
            unmatched_backtest.remove(best_match)
        else:
            unmatched_live.append(live_trade)
    
    return {
        'matches': matches,
        'unmatched_live': unmatched_live,
        'unmatched_backtest': unmatched_backtest
    }


def print_comparison_report(comparison: Dict):
    """Print a detailed comparison report"""
    matches = comparison['matches']
    unmatched_live = comparison['unmatched_live']
    unmatched_backtest = comparison['unmatched_backtest']
    
    total_live = len(matches) + len(unmatched_live)
    total_backtest = len(matches) + len(unmatched_backtest)
    match_rate = (len(matches) / total_live * 100) if total_live > 0 else 0
    
    print("\n" + "=" * 80)
    print("📊 LIVE TRADING vs BACKTEST COMPARISON - December 19, 2025")
    print("=" * 80)
    
    print(f"\n📈 SUMMARY:")
    print(f"   Live Trades: {total_live}")
    print(f"   Backtest Trades: {total_backtest}")
    print(f"   Matched Trades: {len(matches)}")
    print(f"   Match Rate: {match_rate:.1f}%")
    
    print(f"\n✅ MATCHED TRADES ({len(matches)}):")
    print("-" * 80)
    
    # Group by symbol
    by_symbol = defaultdict(list)
    for match in matches:
        by_symbol[match['live']['symbol']].append(match)
    
    for symbol in sorted(by_symbol.keys()):
        print(f"\n  {symbol}:")
        for match in by_symbol[symbol]:
            live = match['live']
            bt = match['backtest']
            time_diff = match['time_diff_seconds']
            price_diff = match['price_diff']
            
            print(f"    {live['entry_time'][11:19]} | {live['direction']:4s} | "
                  f"Live: {live['entry_price']:>10.2f} | BT: {bt['entry_price']:>10.2f} | "
                  f"Δtime: {time_diff:>5.0f}s | Δprice: {price_diff:>6.2f}")
    
    if unmatched_live:
        print(f"\n⚠️  UNMATCHED LIVE TRADES ({len(unmatched_live)}):")
        print("-" * 80)
        for trade in unmatched_live:
            print(f"    {trade['entry_time'][11:19]} | {trade['symbol']:12s} | "
                  f"{trade['direction']:4s} @ {trade['entry_price']:>10.2f}")
    
    if unmatched_backtest:
        print(f"\n🔍 BACKTEST TRADES NOT IN LIVE ({len(unmatched_backtest)}):")
        print("-" * 80)
        by_symbol = defaultdict(list)
        for trade in unmatched_backtest:
            by_symbol[trade['symbol']].append(trade)
        
        for symbol in sorted(by_symbol.keys()):
            print(f"\n  {symbol}:")
            for trade in by_symbol[symbol]:
                print(f"    {trade['entry_time'][11:19]} | {trade['direction']:4s} @ "
                      f"{trade['entry_price']:>10.2f} | Result: {trade['result']:4s} ({trade['pips']:>+6.1f} pips)")
    
    print("\n" + "=" * 80)


def main():
    # Load backtest trades
    backtest_file = '/Users/paul/Sites/PythonProjects/Trading-MCP/data/backtest_trades_20251219.json'
    with open(backtest_file, 'r') as f:
        backtest_trades = json.load(f)
    
    print(f"📁 Loaded {len(backtest_trades)} backtest trades from {backtest_file}")
    
    # Parse live trades
    live_trades = parse_live_trades(LIVE_TRADES_LOG)
    print(f"📝 Parsed {len(live_trades)} live trades from logs")
    
    # Match trades
    comparison = match_trades(live_trades, backtest_trades, time_tolerance_minutes=2)
    
    # Print report
    print_comparison_report(comparison)
    
    # Save detailed comparison to JSON
    output_file = '/Users/paul/Sites/PythonProjects/Trading-MCP/data/live_vs_backtest_comparison_20251219.json'
    with open(output_file, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"\n💾 Detailed comparison saved to: {output_file}")


if __name__ == '__main__':
    main()
