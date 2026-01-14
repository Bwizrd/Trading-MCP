#!/usr/bin/env python3
"""
Analyze maximum favorable and adverse excursions for trades using tick data.
Shows how far price moved in favor and against each trade within 30 minutes.
"""

import pandas as pd
import requests
from datetime import datetime, timedelta

# Configuration
CTRADER_API = "http://localhost:8020"
CSV_FILE = "tradingview/Stochastic_Quad_Rotation_-_SIMPLE_PEPPERSTONESB_UK100_2026-01-13 (1).csv"
SYMBOL = "UK100"
SYMBOL_ID = 217  # UK100 symbol ID


def load_trades_from_csv(csv_path):
    """Load entry trades from TradingView CSV."""
    df = pd.read_csv(csv_path)
    
    # Filter only entry trades
    entries = df[df['Type'].str.contains('Entry', na=False)].copy()
    
    # Parse datetime
    entries['datetime'] = pd.to_datetime(entries['Date and time'])
    
    # Determine direction
    entries['direction'] = entries['Type'].apply(lambda x: 'long' if 'long' in x.lower() else 'short')
    
    # Get entry price
    entries['entry_price'] = entries['Price GBP']
    
    return entries[['datetime', 'direction', 'entry_price', 'Trade #']].to_dict('records')


def fetch_tick_data(symbol_id, start_time, end_time):
    """Fetch tick data from cTrader API."""
    start_iso = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    end_iso = end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
    url = f"{CTRADER_API}/getTickDataFromDB"
    params = {
        'pair': symbol_id,
        'startDate': start_iso,
        'endDate': end_iso,
        'maxTicks': 50000
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if isinstance(result, dict) and 'data' in result:
                data = result['data']
                if isinstance(data, list) and len(data) > 0:
                    ticks = []
                    for tick in data:
                        ticks.append({
                            'time': pd.to_datetime(tick['timestamp'], unit='ms'),
                            'bid': tick.get('bid'),
                            'ask': tick.get('ask')
                        })
                    return pd.DataFrame(ticks)
        
        return pd.DataFrame()
        
    except Exception as e:
        print(f"  Error: {e}")
        return pd.DataFrame()


def analyze_excursions(entry_time, direction, entry_price, ticks):
    """Calculate maximum favorable and adverse excursions."""
    
    if ticks.empty:
        return None
    
    max_favorable = 0
    max_adverse = 0
    
    for idx, tick in ticks.iterrows():
        # Use bid for long exits, ask for short exits
        current_price = tick['bid'] if direction == 'long' else tick['ask']
        
        if pd.isna(current_price):
            continue
        
        if direction == 'long':
            # For longs: favorable = price going up, adverse = price going down
            profit = current_price - entry_price
            if profit > max_favorable:
                max_favorable = profit
            if profit < max_adverse:
                max_adverse = profit
        else:
            # For shorts: favorable = price going down, adverse = price going up
            profit = entry_price - current_price
            if profit > max_favorable:
                max_favorable = profit
            if profit < max_adverse:
                max_adverse = profit
    
    return {
        'max_favorable': max_favorable,
        'max_adverse': max_adverse
    }


def main():
    print("=" * 80)
    print("TRADE EXCURSION ANALYSIS")
    print("=" * 80)
    print(f"\nAnalyzing maximum price movement within 30 minutes of entry")
    print(f"Symbol: {SYMBOL}")
    print(f"Loading trades from: {CSV_FILE}\n")
    
    # Load trades
    trades = load_trades_from_csv(CSV_FILE)
    print(f"Found {len(trades)} entry trades")
    
    # Filter to last 7 days (where tick data exists)
    cutoff_date = datetime.now() - timedelta(days=7)
    recent_trades = [t for t in trades if t['datetime'] > cutoff_date]
    print(f"Analyzing {len(recent_trades)} recent trades (last 7 days)\n")
    
    if len(recent_trades) == 0:
        print("No recent trades found.")
        return
    
    # Analyze each trade
    results = []
    for i, trade in enumerate(recent_trades[:20], 1):  # Analyze up to 20 trades
        print(f"Trade {i}/{min(20, len(recent_trades))}: {trade['datetime']} | {trade['direction'].upper()} @ {trade['entry_price']}")
        
        # Fetch tick data for 30-minute window
        start_time = trade['datetime']
        end_time = start_time + timedelta(minutes=30)
        
        ticks = fetch_tick_data(SYMBOL_ID, start_time, end_time)
        
        if ticks.empty:
            print("  ⚠️  No tick data\n")
            continue
        
        print(f"  ✓ Loaded {len(ticks)} ticks")
        
        # Analyze excursions
        excursions = analyze_excursions(trade['datetime'], trade['direction'], trade['entry_price'], ticks)
        
        if excursions:
            print(f"  Max Favorable: +{excursions['max_favorable']:.1f} pips")
            print(f"  Max Adverse: {excursions['max_adverse']:.1f} pips\n")
            
            results.append({
                **trade,
                **excursions
            })
    
    # Summary statistics
    if results:
        print("=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        
        df = pd.DataFrame(results)
        
        print(f"\nTotal Trades Analyzed: {len(df)}")
        print(f"\nFavorable Excursions:")
        print(f"  Average: {df['max_favorable'].mean():.1f} pips")
        print(f"  Median: {df['max_favorable'].median():.1f} pips")
        print(f"  Min: {df['max_favorable'].min():.1f} pips")
        print(f"  Max: {df['max_favorable'].max():.1f} pips")
        
        print(f"\nAdverse Excursions:")
        print(f"  Average: {df['max_adverse'].mean():.1f} pips")
        print(f"  Median: {df['max_adverse'].median():.1f} pips")
        print(f"  Min (worst): {df['max_adverse'].min():.1f} pips")
        print(f"  Max (best): {df['max_adverse'].max():.1f} pips")
        
        # Breakdown by direction
        print(f"\n--- By Direction ---")
        for direction in ['long', 'short']:
            dir_df = df[df['direction'] == direction]
            if len(dir_df) > 0:
                print(f"\n{direction.upper()} trades ({len(dir_df)}):")
                print(f"  Avg Favorable: {dir_df['max_favorable'].mean():.1f} pips")
                print(f"  Avg Adverse: {dir_df['max_adverse'].mean():.1f} pips")
        
        # Optimal stop/target analysis
        print(f"\n--- Optimal Stop/Target Suggestions ---")
        
        # What % of trades would hit various TP levels?
        for tp in [5, 8, 10, 12, 15]:
            hit_count = len(df[df['max_favorable'] >= tp])
            pct = (hit_count / len(df)) * 100
            print(f"  {tp}-pip TP: {hit_count}/{len(df)} trades ({pct:.0f}%)")
        
        # What SL would avoid X% of adverse moves?
        print(f"\n  Stop Loss to avoid 90% of adverse moves: {df['max_adverse'].quantile(0.1):.1f} pips")
        print(f"  Stop Loss to avoid 95% of adverse moves: {df['max_adverse'].quantile(0.05):.1f} pips")


if __name__ == "__main__":
    main()
