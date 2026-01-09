#!/usr/bin/env python3
"""
Compare OHLC candles generated from tick data vs 1m candles from API.

This script:
1. Loads tick data and 1m candle data from JSON files
2. Converts ticks to 1-minute OHLC candles
3. Compares 10-20 minutes of data from both sources
4. Reports any differences
"""

import json
import pandas as pd
from datetime import datetime

def load_data():
    """Load tick and candle data from JSON files."""
    with open('uk100_ticks_20260107.json', 'r') as f:
        tick_response = json.load(f)
        # Handle both array and dict responses
        if isinstance(tick_response, dict):
            tick_data = tick_response.get('data', tick_response)
        else:
            tick_data = tick_response
    
    with open('uk100_1m_candles_20260107.json', 'r') as f:
        candle_response = json.load(f)
        candle_data = candle_response['data'] if isinstance(candle_response, dict) else candle_response
    
    return tick_data, candle_data

def ticks_to_1m_candles(tick_data):
    """Convert tick data to 1-minute OHLC candles."""
    # Convert to DataFrame
    records = []
    for tick in tick_data:
        records.append({
            'timestamp': pd.to_datetime(tick['timestamp'], unit='ms'),
            'price': (tick['bid'] + tick['ask']) / 2,  # Mid price
            'volume': tick.get('volume', 1)
        })
    
    df = pd.DataFrame(records)
    df = df.set_index('timestamp')
    
    # Resample to 1s candles first
    df_1s = df.resample('1S').agg({
        'price': ['first', 'max', 'min', 'last', 'count']
    }).dropna()
    df_1s.columns = ['open', 'high', 'low', 'close', 'volume']
    
    # Then resample to 1m candles
    df_1m = df_1s.resample('1T').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    return df_1m

def api_candles_to_df(candle_data):
    """Convert API candle data to DataFrame."""
    records = []
    for candle in candle_data:
        records.append({
            'timestamp': pd.to_datetime(candle['timestamp'], unit='ms'),
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close'],
            'volume': candle['volume']
        })
    
    df = pd.DataFrame(records)
    df = df.set_index('timestamp')
    return df

def compare_candles(tick_candles, api_candles, start_minute=0, num_minutes=20):
    """Compare candles from both sources for a specific time window."""
    
    # Get overlapping time range
    common_times = tick_candles.index.intersection(api_candles.index)
    
    if len(common_times) == 0:
        print("❌ No overlapping timestamps found!")
        return
    
    # Select the time window
    window_times = common_times[start_minute:start_minute + num_minutes]
    
    if len(window_times) == 0:
        print(f"❌ No data in requested window (start={start_minute}, num={num_minutes})")
        return
    
    print(f"\n{'='*80}")
    print(f"COMPARING {len(window_times)} MINUTES OF DATA")
    print(f"Time range: {window_times[0]} to {window_times[-1]}")
    print(f"{'='*80}\n")
    
    # Compare candle by candle
    differences = []
    for ts in window_times:
        tick_candle = tick_candles.loc[ts]
        api_candle = api_candles.loc[ts]
        
        # Calculate differences
        open_diff = abs(tick_candle['open'] - api_candle['open'])
        high_diff = abs(tick_candle['high'] - api_candle['high'])
        low_diff = abs(tick_candle['low'] - api_candle['low'])
        close_diff = abs(tick_candle['close'] - api_candle['close'])
        
        max_diff = max(open_diff, high_diff, low_diff, close_diff)
        
        if max_diff > 0.5:  # Significant difference threshold
            differences.append({
                'time': ts,
                'open_diff': open_diff,
                'high_diff': high_diff,
                'low_diff': low_diff,
                'close_diff': close_diff,
                'max_diff': max_diff
            })
        
        # Print comparison
        print(f"{ts.strftime('%H:%M:%S')}")
        print(f"  Tick OHLC: {tick_candle['open']:.2f} {tick_candle['high']:.2f} {tick_candle['low']:.2f} {tick_candle['close']:.2f}")
        print(f"  API  OHLC: {api_candle['open']:.2f} {api_candle['high']:.2f} {api_candle['low']:.2f} {api_candle['close']:.2f}")
        print(f"  Diff:      {open_diff:.2f} {high_diff:.2f} {low_diff:.2f} {close_diff:.2f} (max: {max_diff:.2f})")
        print()
    
    # Summary
    print(f"{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total minutes compared: {len(window_times)}")
    print(f"Minutes with differences >0.5: {len(differences)}")
    
    if differences:
        print(f"\nLargest differences:")
        sorted_diffs = sorted(differences, key=lambda x: x['max_diff'], reverse=True)
        for diff in sorted_diffs[:5]:
            print(f"  {diff['time'].strftime('%H:%M:%S')}: {diff['max_diff']:.2f} pips")
    else:
        print("\n✅ All candles match within 0.5 pips tolerance!")
    
    return differences

def main():
    print("Loading data...")
    tick_data, candle_data = load_data()
    
    print(f"Loaded {len(tick_data)} ticks")
    print(f"Loaded {len(candle_data)} 1m candles")
    
    print("\nConverting ticks to 1-minute candles...")
    tick_candles = ticks_to_1m_candles(tick_data)
    print(f"Generated {len(tick_candles)} candles from ticks")
    
    print("\nConverting API candles to DataFrame...")
    api_candles = api_candles_to_df(candle_data)
    print(f"API has {len(api_candles)} candles")
    
    # Find common time range
    common_times = tick_candles.index.intersection(api_candles.index)
    print(f"\nOverlapping time range: {len(common_times)} minutes")
    if len(common_times) > 0:
        print(f"From: {common_times[0]}")
        print(f"To:   {common_times[-1]}")
    
    # Compare first 20 minutes of overlapping data
    if len(common_times) >= 20:
        compare_candles(tick_candles, api_candles, start_minute=0, num_minutes=20)
    else:
        print(f"\n⚠️ Only {len(common_times)} overlapping minutes, comparing all...")
        compare_candles(tick_candles, api_candles, start_minute=0, num_minutes=len(common_times))

if __name__ == "__main__":
    main()
