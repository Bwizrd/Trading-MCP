#!/usr/bin/env python3
"""
Analyze Trade Signals - Compare Winning vs Losing Trades

Extract stochastic indicators and volume data around trade signals
to identify patterns that could filter out losing trades.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_backtest_data(json_file):
    """Load backtest results from JSON file."""
    with open(json_file, 'r') as f:
        return json.load(f)

def find_candle_index(candles, target_time):
    """Find the index of a candle by timestamp."""
    target_dt = datetime.fromisoformat(target_time.replace('Z', '+00:00'))
    for i, candle in enumerate(candles):
        candle_dt = datetime.fromisoformat(candle['timestamp'].replace('Z', '+00:00'))
        if candle_dt == target_dt:
            return i
    return None

def get_window_data(candles, indicators, center_idx, window_minutes=10):
    """Extract candle and indicator data for a time window around a signal."""
    if center_idx is None:
        return None
    
    start_idx = max(0, center_idx - window_minutes)
    end_idx = min(len(candles) - 1, center_idx + window_minutes)
    
    window_data = []
    for i in range(start_idx, end_idx + 1):
        candle = candles[i]
        timestamp = candle['timestamp']
        
        # Extract stochastic values
        fast_k = indicators.get('fast', [0] * len(candles))[i]
        fast_d = indicators.get('fast_d', [0] * len(candles))[i]
        med_fast_k = indicators.get('med_fast', [0] * len(candles))[i]
        med_fast_d = indicators.get('med_fast_d', [0] * len(candles))[i]
        med_slow_k = indicators.get('med_slow', [0] * len(candles))[i]
        med_slow_d = indicators.get('med_slow_d', [0] * len(candles))[i]
        slow_k = indicators.get('slow', [0] * len(candles))[i]
        slow_d = indicators.get('slow_d', [0] * len(candles))[i]
        
        window_data.append({
            'offset': i - center_idx,
            'timestamp': timestamp,
            'close': candle['close'],
            'volume': candle['volume'],
            'fast_k': fast_k,
            'fast_d': fast_d,
            'med_fast_k': med_fast_k,
            'med_fast_d': med_fast_d,
            'med_slow_k': med_slow_k,
            'med_slow_d': med_slow_d,
            'slow_k': slow_k,
            'slow_d': slow_d
        })
    
    return window_data

def analyze_trade(trade, candles, indicators, trade_num):
    """Analyze a single trade's signal context."""
    entry_time = trade['entry_time']
    direction = trade['direction']
    result = trade['result']
    pips = trade['pips']
    
    # Find the candle index for the entry time
    center_idx = find_candle_index(candles, entry_time)
    
    if center_idx is None:
        print(f"⚠️  Could not find candle for trade #{trade_num} @ {entry_time}")
        return None
    
    # Get window data
    window_data = get_window_data(candles, indicators, center_idx, window_minutes=10)
    
    if not window_data:
        return None
    
    # Print analysis
    result_emoji = "✅" if result == "WIN" else "❌"
    print(f"\n{'='*100}")
    print(f"{result_emoji} TRADE #{trade_num}: {direction} @ {entry_time} = {pips:+.1f} pips ({result})")
    print(f"{'='*100}")
    
    print(f"\n{'Time':<20} {'Offset':<8} {'Close':<10} {'Volume':<10} {'Fast_K':<8} {'Fast_D':<8} {'MedF_K':<8} {'MedS_K':<8} {'Slow_K':<8}")
    print("-" * 100)
    
    for data in window_data:
        offset_str = f"{data['offset']:+d}m"
        marker = " 🎯" if data['offset'] == 0 else ""
        
        print(f"{data['timestamp'][11:16]:<20} {offset_str:<8} {data['close']:<10.2f} {data['volume']:<10} "
              f"{data['fast_k']:<8.1f} {data['fast_d']:<8.1f} {data['med_fast_k']:<8.1f} "
              f"{data['med_slow_k']:<8.1f} {data['slow_k']:<8.1f}{marker}")
    
    # Calculate some statistics
    signal_data = [d for d in window_data if d['offset'] == 0][0]
    pre_signal_data = [d for d in window_data if d['offset'] < 0]
    
    if pre_signal_data:
        avg_volume_before = sum(d['volume'] for d in pre_signal_data) / len(pre_signal_data)
        volume_ratio = signal_data['volume'] / avg_volume_before if avg_volume_before > 0 else 0
        
        print(f"\n📊 STATISTICS:")
        print(f"   Signal Volume: {signal_data['volume']}")
        print(f"   Avg Volume (10m before): {avg_volume_before:.0f}")
        print(f"   Volume Ratio: {volume_ratio:.2f}x")
        
        # Check if all stochastics are in the same zone
        all_above_80 = all(signal_data[f'{s}_k'] > 80 for s in ['fast', 'med_fast', 'med_slow', 'slow'])
        all_below_20 = all(signal_data[f'{s}_k'] < 20 for s in ['fast', 'med_fast', 'med_slow', 'slow'])
        
        print(f"   All Stochastics > 80: {all_above_80}")
        print(f"   All Stochastics < 20: {all_below_20}")
        
        # Check fast stochastic momentum
        if len(pre_signal_data) >= 3:
            fast_k_3m_ago = pre_signal_data[-3]['fast_k']
            fast_k_change = signal_data['fast_k'] - fast_k_3m_ago
            print(f"   Fast %K change (3m): {fast_k_change:+.1f}")
    
    return {
        'trade_num': trade_num,
        'direction': direction,
        'result': result,
        'pips': pips,
        'signal_data': signal_data,
        'window_data': window_data
    }

def main():
    # Load the most recent backtest
    json_file = 'optimization_results/backtest_US500_SB_20251212_145653.json'
    
    print(f"Loading backtest data from: {json_file}")
    data = load_backtest_data(json_file)
    
    trades = data['trades']
    candles = data['market_data']
    indicators = data.get('indicators', {})
    
    print(f"\nFound {len(trades)} trades to analyze")
    print(f"Market data: {len(candles)} candles")
    print(f"Indicators: {list(indicators.keys())}")
    
    # Analyze each trade
    analyses = []
    for i, trade in enumerate(trades, 1):
        analysis = analyze_trade(trade, candles, indicators, i)
        if analysis:
            analyses.append(analysis)
    
    # Summary comparison
    print(f"\n{'='*100}")
    print("📈 SUMMARY: WINNING vs LOSING TRADES")
    print(f"{'='*100}")
    
    winning_trades = [a for a in analyses if a['result'] == 'WIN']
    losing_trades = [a for a in analyses if a['result'] == 'LOSS']
    
    print(f"\n✅ WINNING TRADES ({len(winning_trades)}):")
    for trade in winning_trades:
        print(f"   Trade #{trade['trade_num']}: {trade['direction']} = {trade['pips']:+.1f} pips")
    
    print(f"\n❌ LOSING TRADES ({len(losing_trades)}):")
    for trade in losing_trades:
        print(f"   Trade #{trade['trade_num']}: {trade['direction']} = {trade['pips']:+.1f} pips")
    
    print(f"\n{'='*100}")

if __name__ == "__main__":
    main()
