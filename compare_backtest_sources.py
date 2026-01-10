#!/usr/bin/env python3
"""
Compare backtest results using database bars vs tick-aggregated bars.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import pandas as pd
import json
from datetime import datetime, timedelta
from vps_data_fetcher import VPSDataFetcher
import requests


def aggregate_ticks_to_1m(df_ticks):
    """Aggregate tick data to 1-minute bars."""
    df_ticks['mid'] = (df_ticks['bid'] + df_ticks['ask']) / 2
    
    bars = df_ticks['mid'].resample('1min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    })
    
    bars['volume'] = df_ticks['mid'].resample('1min').count()
    bars = bars.dropna()
    
    return bars


def fetch_db_bars(symbol_id=220, bars=1500):
    """Fetch bars from database."""
    url = "http://localhost:8020/getDataFromDB"
    params = {"pair": symbol_id, "timeframe": "1m", "bars": bars}
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    df = pd.DataFrame(data["data"])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    return df


def calculate_stochastic(df, period=14):
    """Calculate stochastic oscillator."""
    low_min = df['low'].rolling(window=period).min()
    high_max = df['high'].rolling(window=period).max()
    
    stoch = ((df['close'] - low_min) / (high_max - low_min)) * 100
    return stoch


def run_simple_backtest(df, stop_loss_pips=8, take_profit_pips=8):
    """
    Simple backtest using Stochastic Quad Rotation logic.
    """
    # Calculate 4 stochastics with different periods
    df['stoch_5'] = calculate_stochastic(df, 5)
    df['stoch_8'] = calculate_stochastic(df, 8)
    df['stoch_13'] = calculate_stochastic(df, 13)
    df['stoch_21'] = calculate_stochastic(df, 21)
    
    trades = []
    in_trade = False
    entry_price = 0
    entry_time = None
    trade_direction = None
    
    for i in range(50, len(df)):  # Start after indicators are ready
        if in_trade:
            # Check exit conditions
            current_price = df['close'].iloc[i]
            pips_moved = current_price - entry_price if trade_direction == 'BUY' else entry_price - current_price
            
            exit_reason = None
            if pips_moved >= take_profit_pips:
                exit_reason = 'TP'
            elif pips_moved <= -stop_loss_pips:
                exit_reason = 'SL'
            
            if exit_reason:
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': df.index[i],
                    'direction': trade_direction,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pips': pips_moved,
                    'result': exit_reason
                })
                in_trade = False
        else:
            # Check entry conditions
            stoch_5 = df['stoch_5'].iloc[i]
            stoch_8 = df['stoch_8'].iloc[i]
            stoch_13 = df['stoch_13'].iloc[i]
            stoch_21 = df['stoch_21'].iloc[i]
            
            stoch_5_prev = df['stoch_5'].iloc[i-1]
            
            # BUY signal: All below 20 and fast crosses above
            if (stoch_5 > 20 and stoch_5_prev <= 20 and
                stoch_8 < 20 and stoch_13 < 20 and stoch_21 < 20):
                in_trade = True
                entry_price = df['close'].iloc[i]
                entry_time = df.index[i]
                trade_direction = 'BUY'
            
            # SELL signal: All above 80 and fast crosses below
            elif (stoch_5 < 80 and stoch_5_prev >= 80 and
                  stoch_8 > 80 and stoch_13 > 80 and stoch_21 > 80):
                in_trade = True
                entry_price = df['close'].iloc[i]
                entry_time = df.index[i]
                trade_direction = 'SELL'
    
    return trades


def analyze_results(trades, label):
    """Analyze trade results."""
    if not trades:
        return {
            'label': label,
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'total_pips': 0,
            'avg_win': 0,
            'avg_loss': 0
        }
    
    wins = [t for t in trades if t['pips'] > 0]
    losses = [t for t in trades if t['pips'] < 0]
    
    return {
        'label': label,
        'total_trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': len(wins) / len(trades) * 100 if trades else 0,
        'total_pips': sum(t['pips'] for t in trades),
        'avg_win': sum(t['pips'] for t in wins) / len(wins) if wins else 0,
        'avg_loss': sum(t['pips'] for t in losses) / len(losses) if losses else 0
    }


def main():
    print("=" * 80)
    print("BACKTEST COMPARISON: Database Bars vs Tick-Aggregated Bars")
    print("=" * 80)
    
    # Date range - yesterday
    yesterday = datetime.now().date() - timedelta(days=1)
    start_time = f"{yesterday}T14:30:00.000Z"
    end_time = f"{yesterday}T20:00:00.000Z"
    
    print(f"\nDate: {yesterday}")
    print(f"Time: 14:30 - 20:00")
    print(f"Symbol: US500_SB")
    print(f"Strategy: Stochastic Quad Rotation")
    print(f"TP/SL: 8/8 pips\n")
    
    # Fetch data from both sources
    print("1️⃣  Fetching tick data from VPS...")
    fetcher = VPSDataFetcher()
    tick_data = fetcher.fetch_tick_data("US500_SB", start_time, end_time, max_ticks=100000)
    df_ticks = fetcher.ticks_to_dataframe(tick_data)
    print(f"   ✅ Received {len(df_ticks)} ticks")
    
    print("\n2️⃣  Aggregating ticks to 1m bars...")
    df_tick_bars = aggregate_ticks_to_1m(df_ticks)
    print(f"   ✅ Created {len(df_tick_bars)} bars from ticks")
    
    print("\n3️⃣  Fetching 1m bars from database...")
    df_db_bars = fetch_db_bars(symbol_id=220, bars=1500)
    # Filter to same time range (make timezone-aware)
    start_ts = pd.Timestamp(start_time).tz_localize(None)
    end_ts = pd.Timestamp(end_time).tz_localize(None)
    df_db_bars.index = df_db_bars.index.tz_localize(None)
    df_db_bars = df_db_bars[(df_db_bars.index >= start_ts) & 
                             (df_db_bars.index <= end_ts)]
    print(f"   ✅ Received {len(df_db_bars)} bars from database")
    
    # Run backtests
    print("\n4️⃣  Running backtest on tick-aggregated bars...")
    trades_tick = run_simple_backtest(df_tick_bars, stop_loss_pips=8, take_profit_pips=8)
    results_tick = analyze_results(trades_tick, "Tick-Aggregated")
    print(f"   ✅ Completed: {results_tick['total_trades']} trades")
    
    print("\n5️⃣  Running backtest on database bars...")
    trades_db = run_simple_backtest(df_db_bars, stop_loss_pips=8, take_profit_pips=8)
    results_db = analyze_results(trades_db, "Database")
    print(f"   ✅ Completed: {results_db['total_trades']} trades")
    
    # Compare results
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    
    print(f"\n{'Metric':<25} {'Tick-Aggregated':<20} {'Database':<20} {'Difference':<20}")
    print("-" * 85)
    print(f"{'Total Trades':<25} {results_tick['total_trades']:<20} {results_db['total_trades']:<20} {results_tick['total_trades'] - results_db['total_trades']:<20}")
    print(f"{'Winning Trades':<25} {results_tick['wins']:<20} {results_db['wins']:<20} {results_tick['wins'] - results_db['wins']:<20}")
    print(f"{'Losing Trades':<25} {results_tick['losses']:<20} {results_db['losses']:<20} {results_tick['losses'] - results_db['losses']:<20}")
    print(f"{'Win Rate %':<25} {results_tick['win_rate']:<20.1f} {results_db['win_rate']:<20.1f} {results_tick['win_rate'] - results_db['win_rate']:<20.1f}")
    print(f"{'Total Pips':<25} {results_tick['total_pips']:<20.1f} {results_db['total_pips']:<20.1f} {results_tick['total_pips'] - results_db['total_pips']:<20.1f}")
    print(f"{'Avg Win (pips)':<25} {results_tick['avg_win']:<20.2f} {results_db['avg_win']:<20.2f} {results_tick['avg_win'] - results_db['avg_win']:<20.2f}")
    print(f"{'Avg Loss (pips)':<25} {results_tick['avg_loss']:<20.2f} {results_db['avg_loss']:<20.2f} {results_tick['avg_loss'] - results_db['avg_loss']:<20.2f}")
    
    # Analysis
    print("\n" + "=" * 80)
    print("IMPACT ANALYSIS")
    print("=" * 80)
    
    trade_diff_pct = abs(results_tick['total_trades'] - results_db['total_trades']) / max(results_tick['total_trades'], 1) * 100
    win_rate_diff = abs(results_tick['win_rate'] - results_db['win_rate'])
    pips_diff_pct = abs(results_tick['total_pips'] - results_db['total_pips']) / max(abs(results_tick['total_pips']), 1) * 100
    
    print(f"\n📊 Trade Count Difference: {trade_diff_pct:.1f}%")
    print(f"📊 Win Rate Difference: {win_rate_diff:.1f}%")
    print(f"📊 Total Pips Difference: {pips_diff_pct:.1f}%")
    
    print("\n💡 Recommendation:")
    if trade_diff_pct > 15 or win_rate_diff > 10 or pips_diff_pct > 20:
        print("   ⚠️  SIGNIFICANT DIFFERENCES DETECTED!")
        print("   → Use TICK DATA for accurate backtesting")
        print("   → Database bars may give misleading results")
    elif trade_diff_pct > 5 or win_rate_diff > 5 or pips_diff_pct > 10:
        print("   ⚡ MODERATE DIFFERENCES detected")
        print("   → Tick data is more accurate, but database is acceptable")
        print("   → Use tick data for final validation")
    else:
        print("   ✅ MINIMAL DIFFERENCES - Both sources are acceptable")
        print("   → Database bars are good enough for this strategy")
        print("   → Use database for faster backtesting")
    
    print("\n✅ Comparison complete!")


if __name__ == "__main__":
    main()
