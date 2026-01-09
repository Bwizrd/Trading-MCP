"""
Analyze tick data and calculate 4 stochastics to find crossover situations.

This script:
1. Fetches tick data from InfluxDB
2. Converts to 1-second candles
3. Resamples to 1-minute candles
4. Calculates 4 stochastics (fast=9, med_fast=14, med_slow=40, slow=60)
5. Detects crossover situations for buy/sell signals
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import sys


def fetch_tick_data(symbol: str, start_date: str, end_date: str):
    """Fetch tick data from API."""
    # Map symbols to IDs
    symbol_map = {
        'NAS100': 205,
        'US500': 220,
        'US500_SB': 220,
        'UK100': 217,
        'GER40': 200,
        'US30': 219
    }
    
    symbol_id = symbol_map.get(symbol)
    if not symbol_id:
        raise ValueError(f"Unknown symbol: {symbol}. Available: {list(symbol_map.keys())}")
    
    # Adjust times based on symbol
    if symbol in ['UK100', 'GER40']:
        # UK/EU hours: 8:00 AM - 4:30 PM
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').replace(hour=8, minute=0, second=0)
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=16, minute=30, second=0)
    else:
        # US hours: 2:30 PM - 9:00 PM
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').replace(hour=14, minute=30, second=0)
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=21, minute=0, second=0)
    
    url = "http://localhost:8000/getTickDataFromDB"
    params = {
        "pair": symbol_id,
        "startDate": start_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        "endDate": end_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        "maxTicks": 50000
    }
    
    print(f"Fetching tick data for {symbol} from {start_dt} to {end_dt}...")
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    response = requests.get(url, params=params, timeout=120)
    response.raise_for_status()
    
    data = response.json()
    ticks = data.get('data', [])
    
    print(f"Received {len(ticks)} ticks")
    return ticks


def ticks_to_candles(ticks, timeframe='1S'):
    """Convert ticks to OHLCV candles."""
    if not ticks:
        return pd.DataFrame()
    
    # Create DataFrame
    df = pd.DataFrame(ticks)
    
    # Convert timestamp from milliseconds to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Calculate mid price
    df['mid'] = (df['bid'] + df['ask']) / 2
    
    # Set timestamp as index
    df.set_index('timestamp', inplace=True)
    
    # Resample to specified timeframe
    ohlcv = df['mid'].resample(timeframe).ohlc()
    ohlcv['volume'] = df['mid'].resample(timeframe).count()
    
    # Drop rows with no data
    ohlcv = ohlcv.dropna()
    
    print(f"Converted to {len(ohlcv)} {timeframe} candles")
    return ohlcv


def calculate_stochastic(df, k_period, k_smoothing=1, d_smoothing=3):
    """
    Calculate Stochastic Oscillator.
    
    Args:
        df: DataFrame with OHLC data
        k_period: Period for %K calculation
        k_smoothing: Smoothing period for %K
        d_smoothing: Smoothing period for %D
    
    Returns:
        Tuple of (K values, D values)
    """
    # Calculate raw %K
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()
    
    k_raw = 100 * (df['close'] - low_min) / (high_max - low_min)
    
    # Smooth %K if k_smoothing > 1
    if k_smoothing > 1:
        k = k_raw.rolling(window=k_smoothing).mean()
    else:
        k = k_raw
    
    # Calculate %D (smoothed %K)
    d = k.rolling(window=d_smoothing).mean()
    
    return k, d


def detect_crossovers(df):
    """
    Detect buy/sell crossover situations.
    
    Buy signal: All 4 stochastics below 20, fast crosses above 20
    Sell signal: All 4 stochastics above 80, fast crosses below 80
    """
    signals = []
    
    for i in range(1, len(df)):
        prev_row = df.iloc[i-1]
        curr_row = df.iloc[i]
        
        # Check BUY condition
        # Zone: All 4 below 20 in PREVIOUS bar
        prev_all_below_20 = (
            prev_row['fast'] < 20 and
            prev_row['med_fast'] < 20 and
            prev_row['med_slow'] < 20 and
            prev_row['slow'] < 20
        )
        
        # Trigger: Fast crosses above 20 in CURRENT bar
        fast_crosses_above_20 = prev_row['fast'] < 20 and curr_row['fast'] >= 20
        
        if prev_all_below_20 and fast_crosses_above_20:
            signals.append({
                'timestamp': curr_row.name,
                'type': 'BUY',
                'price': curr_row['close'],
                'fast': curr_row['fast'],
                'med_fast': curr_row['med_fast'],
                'med_slow': curr_row['med_slow'],
                'slow': curr_row['slow']
            })
        
        # Check SELL condition
        # Zone: All 4 above 80 in PREVIOUS bar
        prev_all_above_80 = (
            prev_row['fast'] > 80 and
            prev_row['med_fast'] > 80 and
            prev_row['med_slow'] > 80 and
            prev_row['slow'] > 80
        )
        
        # Trigger: Fast crosses below 80 in CURRENT bar
        fast_crosses_below_80 = prev_row['fast'] > 80 and curr_row['fast'] <= 80
        
        if prev_all_above_80 and fast_crosses_below_80:
            signals.append({
                'timestamp': curr_row.name,
                'type': 'SELL',
                'price': curr_row['close'],
                'fast': curr_row['fast'],
                'med_fast': curr_row['med_fast'],
                'med_slow': curr_row['med_slow'],
                'slow': curr_row['slow']
            })
    
    return signals


def main():
    symbol = "UK100"
    date = "2026-01-07"
    
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    if len(sys.argv) > 2:
        date = sys.argv[2]
    
    print("=" * 80)
    print("TICK DATA STOCHASTIC ANALYSIS")
    print("=" * 80)
    
    # Step 1: Fetch tick data
    ticks = fetch_tick_data(symbol, date, date)
    
    if not ticks:
        print("No tick data available")
        return
    
    # Step 2: Convert to 1-second candles
    print("\n" + "=" * 80)
    print("CONVERTING TO 1-SECOND CANDLES")
    print("=" * 80)
    candles_1s = ticks_to_candles(ticks, '1S')
    
    # Step 3: Resample to 1-minute candles for stochastic calculation
    print("\n" + "=" * 80)
    print("RESAMPLING TO 1-MINUTE CANDLES")
    print("=" * 80)
    candles_1m = candles_1s.resample('1T').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    print(f"Resampled to {len(candles_1m)} 1-minute candles")
    
    # Step 4: Calculate all 4 stochastics
    print("\n" + "=" * 80)
    print("CALCULATING STOCHASTICS")
    print("=" * 80)
    
    # Fast (9 period)
    print("Calculating fast stochastic (k=9, k_smooth=1, d_smooth=3)...")
    candles_1m['fast'], candles_1m['fast_d'] = calculate_stochastic(candles_1m, 9, 1, 3)
    
    # Med Fast (14 period)
    print("Calculating med_fast stochastic (k=14, k_smooth=1, d_smooth=3)...")
    candles_1m['med_fast'], candles_1m['med_fast_d'] = calculate_stochastic(candles_1m, 14, 1, 3)
    
    # Med Slow (40 period)
    print("Calculating med_slow stochastic (k=40, k_smooth=1, d_smooth=4)...")
    candles_1m['med_slow'], candles_1m['med_slow_d'] = calculate_stochastic(candles_1m, 40, 1, 4)
    
    # Slow (60 period)
    print("Calculating slow stochastic (k=60, k_smooth=1, d_smooth=10)...")
    candles_1m['slow'], candles_1m['slow_d'] = calculate_stochastic(candles_1m, 60, 1, 10)
    
    # Drop NaN rows (from indicator calculation warm-up)
    candles_1m = candles_1m.dropna()
    print(f"After dropping NaN: {len(candles_1m)} candles with complete indicators")
    
    # Step 5: Show sample data
    print("\n" + "=" * 80)
    print("SAMPLE DATA (First 10 rows with indicators)")
    print("=" * 80)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)
    print(candles_1m[['close', 'fast', 'med_fast', 'med_slow', 'slow']].head(10))
    
    print("\n" + "=" * 80)
    print("SAMPLE DATA (Last 10 rows with indicators)")
    print("=" * 80)
    print(candles_1m[['close', 'fast', 'med_fast', 'med_slow', 'slow']].tail(10))
    
    # Step 6: Detect crossovers
    print("\n" + "=" * 80)
    print("DETECTING CROSSOVER SIGNALS")
    print("=" * 80)
    signals = detect_crossovers(candles_1m)
    
    print(f"\nFound {len(signals)} signals:")
    print("-" * 80)
    
    for signal in signals:
        print(f"\n{signal['type']} SIGNAL at {signal['timestamp']}")
        print(f"  Price: {signal['price']:.2f}")
        print(f"  Fast:     {signal['fast']:.2f}")
        print(f"  MedFast:  {signal['med_fast']:.2f}")
        print(f"  MedSlow:  {signal['med_slow']:.2f}")
        print(f"  Slow:     {signal['slow']:.2f}")
    
    # Step 7: Export to CSV
    csv_file = f'tick_stochastics_{symbol}_{date}.csv'
    candles_1m.to_csv(csv_file)
    print(f"\n" + "=" * 80)
    print(f"Data exported to: {csv_file}")
    print("=" * 80)
    
    # Step 8: Summary statistics
    print("\n" + "=" * 80)
    print("STOCHASTIC STATISTICS")
    print("=" * 80)
    print("\nFast Stochastic:")
    print(f"  Min: {candles_1m['fast'].min():.2f}")
    print(f"  Max: {candles_1m['fast'].max():.2f}")
    print(f"  Mean: {candles_1m['fast'].mean():.2f}")
    print(f"  Times below 20: {(candles_1m['fast'] < 20).sum()}")
    print(f"  Times above 80: {(candles_1m['fast'] > 80).sum()}")
    
    print("\nAll 4 below 20 count:", ((candles_1m['fast'] < 20) & 
                                        (candles_1m['med_fast'] < 20) & 
                                        (candles_1m['med_slow'] < 20) & 
                                        (candles_1m['slow'] < 20)).sum())
    
    print("\nAll 4 above 80 count:", ((candles_1m['fast'] > 80) & 
                                        (candles_1m['med_fast'] > 80) & 
                                        (candles_1m['med_slow'] > 80) & 
                                        (candles_1m['slow'] > 80)).sum())


if __name__ == "__main__":
    main()
