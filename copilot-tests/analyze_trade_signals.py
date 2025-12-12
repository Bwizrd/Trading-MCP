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

def calculate_trend_strength(pre_signal_data, direction):
    """
    Calculate trend strength metrics for the period BEFORE the signal.
    
    For BUY signals: We want to see a DOWNTREND before (price dropping)
    For SELL signals: We want to see an UPTREND before (price rising)
    
    Returns dict with trend metrics.
    """
    if not pre_signal_data or len(pre_signal_data) < 10:
        return None
    
    # Get price data for the 10 minutes before signal
    prices = [d['close'] for d in pre_signal_data]
    highs = [d['close'] for d in pre_signal_data]  # Using close as proxy
    lows = [d['close'] for d in pre_signal_data]
    
    # Calculate price range
    price_high = max(prices)
    price_low = min(prices)
    price_range = price_high - price_low
    avg_price = sum(prices) / len(prices)
    
    # Calculate range in pips (for US500, 1 point = 1 pip)
    range_pips = price_range
    
    # Calculate directional movement
    start_price = prices[0]
    end_price = prices[-1]
    price_change = end_price - start_price
    price_change_pips = price_change
    
    # Calculate trend strength (normalized by range)
    # Positive = upward movement, Negative = downward movement
    trend_strength = (price_change / price_range) if price_range > 0 else 0
    
    # For BUY signals, we WANT negative trend (downtrend before reversal)
    # For SELL signals, we WANT positive trend (uptrend before reversal)
    expected_direction = -1 if direction == "BUY" else 1
    trend_alignment = trend_strength * expected_direction
    
    # Calculate consistency (how many candles moved in the expected direction)
    moves_in_direction = 0
    for i in range(1, len(prices)):
        price_move = prices[i] - prices[i-1]
        if direction == "BUY" and price_move < 0:  # Downward move before BUY
            moves_in_direction += 1
        elif direction == "SELL" and price_move > 0:  # Upward move before SELL
            moves_in_direction += 1
    
    consistency = moves_in_direction / (len(prices) - 1) if len(prices) > 1 else 0
    
    return {
        'range_pips': range_pips,
        'price_change_pips': price_change_pips,
        'trend_strength': trend_strength,
        'trend_alignment': trend_alignment,
        'consistency': consistency,
        'start_price': start_price,
        'end_price': end_price
    }

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
    
    # Calculate trend strength BEFORE the signal
    trend_metrics = calculate_trend_strength(pre_signal_data, direction)
    
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
        
        # Print trend strength metrics
        if trend_metrics:
            print(f"\n🎯 TREND CONTEXT (10m before signal):")
            print(f"   Price Range: {trend_metrics['range_pips']:.1f} pips")
            print(f"   Price Change: {trend_metrics['price_change_pips']:+.1f} pips ({trend_metrics['start_price']:.1f} → {trend_metrics['end_price']:.1f})")
            print(f"   Trend Strength: {trend_metrics['trend_strength']:+.2f} ({'UP' if trend_metrics['trend_strength'] > 0 else 'DOWN'})")
            print(f"   Trend Alignment: {trend_metrics['trend_alignment']:+.2f} (want {'DOWN' if direction == 'BUY' else 'UP'} before {direction})")
            print(f"   Consistency: {trend_metrics['consistency']:.1%} (candles moving in expected direction)")
    
    return {
        'trade_num': trade_num,
        'direction': direction,
        'result': result,
        'pips': pips,
        'signal_data': signal_data,
        'window_data': window_data,
        'trend_metrics': trend_metrics
    }

def main():
    # Load the most recent backtest
    json_file = 'optimization_results/backtest_US500_SB_20251212_163027.json'
    
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
        tm = trade.get('trend_metrics')
        if tm:
            print(f"   Trade #{trade['trade_num']}: {trade['direction']} = {trade['pips']:+.1f} pips | "
                  f"Range: {tm['range_pips']:.1f}p | Change: {tm['price_change_pips']:+.1f}p | "
                  f"Alignment: {tm['trend_alignment']:+.2f} | Consistency: {tm['consistency']:.0%}")
        else:
            print(f"   Trade #{trade['trade_num']}: {trade['direction']} = {trade['pips']:+.1f} pips")
    
    print(f"\n❌ LOSING TRADES ({len(losing_trades)}):")
    for trade in losing_trades:
        tm = trade.get('trend_metrics')
        if tm:
            print(f"   Trade #{trade['trade_num']}: {trade['direction']} = {trade['pips']:+.1f} pips | "
                  f"Range: {tm['range_pips']:.1f}p | Change: {tm['price_change_pips']:+.1f}p | "
                  f"Alignment: {tm['trend_alignment']:+.2f} | Consistency: {tm['consistency']:.0%}")
        else:
            print(f"   Trade #{trade['trade_num']}: {trade['direction']} = {trade['pips']:+.1f} pips")
    
    # Calculate average metrics
    print(f"\n📊 AVERAGE TREND METRICS:")
    
    if winning_trades:
        win_metrics = [t['trend_metrics'] for t in winning_trades if t.get('trend_metrics')]
        if win_metrics:
            avg_win_range = sum(m['range_pips'] for m in win_metrics) / len(win_metrics)
            avg_win_change = sum(abs(m['price_change_pips']) for m in win_metrics) / len(win_metrics)
            avg_win_alignment = sum(m['trend_alignment'] for m in win_metrics) / len(win_metrics)
            avg_win_consistency = sum(m['consistency'] for m in win_metrics) / len(win_metrics)
            
            print(f"\n✅ WINNING TRADES:")
            print(f"   Avg Range: {avg_win_range:.1f} pips")
            print(f"   Avg Price Change: {avg_win_change:.1f} pips")
            print(f"   Avg Trend Alignment: {avg_win_alignment:+.2f}")
            print(f"   Avg Consistency: {avg_win_consistency:.0%}")
    
    if losing_trades:
        loss_metrics = [t['trend_metrics'] for t in losing_trades if t.get('trend_metrics')]
        if loss_metrics:
            avg_loss_range = sum(m['range_pips'] for m in loss_metrics) / len(loss_metrics)
            avg_loss_change = sum(abs(m['price_change_pips']) for m in loss_metrics) / len(loss_metrics)
            avg_loss_alignment = sum(m['trend_alignment'] for m in loss_metrics) / len(loss_metrics)
            avg_loss_consistency = sum(m['consistency'] for m in loss_metrics) / len(loss_metrics)
            
            print(f"\n❌ LOSING TRADES:")
            print(f"   Avg Range: {avg_loss_range:.1f} pips")
            print(f"   Avg Price Change: {avg_loss_change:.1f} pips")
            print(f"   Avg Trend Alignment: {avg_loss_alignment:+.2f}")
            print(f"   Avg Consistency: {avg_loss_consistency:.0%}")
    
    print(f"\n💡 KEY INSIGHT:")
    print(f"   Trend Alignment > 0 means price was moving in the EXPECTED direction before signal")
    print(f"   (DOWN before BUY, UP before SELL)")
    print(f"   Higher alignment = stronger trend to reverse FROM")
    
    print(f"\n{'='*100}")

if __name__ == "__main__":
    main()
