"""
Analyze VPS tick data for gaps and aggregate to 1m candles.
This will help us understand why tick-based backtests differ from database bars.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json

def fetch_tick_data(symbol_id, start_date, end_date, max_ticks=100000):
    """Fetch tick data from VPS API."""
    url = f"http://localhost:8020/getTickDataFromDB"
    params = {
        'pair': symbol_id,
        'startDate': start_date,
        'endDate': end_date,
        'maxTicks': max_ticks
    }
    
    print(f"Fetching tick data from {start_date} to {end_date}...")
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if 'data' in data:
            print(f"✅ Received {len(data['data'])} ticks")
            return data['data']
    
    print(f"❌ Failed to fetch tick data: {response.status_code}")
    return []

def analyze_tick_data(ticks):
    """Analyze tick data for gaps and statistics."""
    if not ticks:
        print("No tick data to analyze")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(ticks)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['mid'] = (df['bid'] + df['ask']) / 2
    
    print("\n" + "="*80)
    print("TICK DATA ANALYSIS")
    print("="*80)
    
    # Basic stats
    print(f"\n📊 Basic Statistics:")
    print(f"   Total ticks: {len(df):,}")
    print(f"   First tick:  {df['timestamp'].iloc[0]}")
    print(f"   Last tick:   {df['timestamp'].iloc[-1]}")
    print(f"   Duration:    {df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]}")
    
    # Analyze tick frequency
    df['time_diff'] = df['timestamp'].diff()
    print(f"\n⏱️  Tick Frequency:")
    print(f"   Min gap:     {df['time_diff'].min()}")
    print(f"   Max gap:     {df['time_diff'].max()}")
    print(f"   Mean gap:    {df['time_diff'].mean()}")
    print(f"   Median gap:  {df['time_diff'].median()}")
    
    # Find large gaps (>1 minute)
    large_gaps = df[df['time_diff'] > pd.Timedelta(minutes=1)]
    print(f"\n🕳️  Large Gaps (>1 minute): {len(large_gaps)}")
    if len(large_gaps) > 0:
        print("   Top 10 largest gaps:")
        for idx, row in large_gaps.nlargest(10, 'time_diff').iterrows():
            print(f"      {row['time_diff']} at {row['timestamp']}")
    
    # Analyze by hour
    df['hour'] = df['timestamp'].dt.hour
    ticks_by_hour = df.groupby('hour').size()
    print(f"\n🕐 Ticks by Hour (GMT):")
    for hour, count in ticks_by_hour.items():
        bar = '█' * (count // 1000)
        print(f"   {hour:02d}:00 - {count:6,} ticks {bar}")
    
    # Identify market hours
    active_hours = ticks_by_hour[ticks_by_hour > 100].index.tolist()
    print(f"\n💹 Active Hours (>100 ticks/hour): {sorted(active_hours)}")
    
    return df

def aggregate_to_1m(ticks):
    """Aggregate tick data to 1-minute OHLCV candles."""
    if not ticks:
        print("No tick data to aggregate")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(ticks)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['mid'] = (df['bid'] + df['ask']) / 2
    df = df.set_index('timestamp')
    
    # Resample to 1-minute candles
    print("\n" + "="*80)
    print("AGGREGATING TO 1-MINUTE CANDLES")
    print("="*80)
    
    ohlc = df['mid'].resample('1T').agg(['first', 'max', 'min', 'last', 'count'])
    ohlc.columns = ['open', 'high', 'low', 'close', 'ticks']
    
    # Remove candles with no ticks
    ohlc = ohlc[ohlc['ticks'] > 0]
    
    print(f"\n📊 1-Minute Candles:")
    print(f"   Total candles:      {len(ohlc):,}")
    print(f"   First candle:       {ohlc.index[0]}")
    print(f"   Last candle:        {ohlc.index[-1]}")
    print(f"   Candles with data:  {len(ohlc):,}")
    
    # Check for gaps
    ohlc_reset = ohlc.reset_index()
    ohlc_reset['time_diff'] = ohlc_reset['timestamp'].diff()
    gaps = ohlc_reset[ohlc_reset['time_diff'] > pd.Timedelta(minutes=1)]
    
    print(f"\n🕳️  Missing Minutes (gaps): {len(gaps)}")
    if len(gaps) > 0:
        print("   Top 10 largest gaps:")
        for idx, row in gaps.nlargest(10, 'time_diff').iterrows():
            gap_minutes = int(row['time_diff'].total_seconds() / 60)
            print(f"      {gap_minutes:4d} minutes at {row['timestamp']}")
    
    # Ticks per candle statistics
    print(f"\n📈 Ticks per 1-Minute Candle:")
    print(f"   Min:    {ohlc['ticks'].min():.0f}")
    print(f"   Max:    {ohlc['ticks'].max():.0f}")
    print(f"   Mean:   {ohlc['ticks'].mean():.1f}")
    print(f"   Median: {ohlc['ticks'].median():.0f}")
    
    # Save to CSV
    output_file = 'tick_data_1m_aggregated.csv'
    ohlc.to_csv(output_file)
    print(f"\n💾 Saved to: {output_file}")
    
    return ohlc

def compare_with_database_bars(aggregated_1m, symbol="US500", date="2026-01-09"):
    """Compare aggregated tick data with database bars."""
    print("\n" + "="*80)
    print("COMPARING WITH DATABASE BARS")
    print("="*80)
    
    # Fetch database bars
    url = f"http://localhost:8020/getDataFromDB"
    params = {
        'pair': 220,  # US500
        'timeframe': '1m',
        'bars': 1500
    }
    
    print(f"\nFetching database 1m bars...")
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if 'data' in data:
            db_df = pd.DataFrame(data['data'])
            db_df['timestamp'] = pd.to_datetime(db_df['timestamp'], unit='ms')
            db_df = db_df.set_index('timestamp')
            
            # Filter to same date
            date_filter = db_df.index.date == pd.to_datetime(date).date()
            db_df = db_df[date_filter]
            
            print(f"✅ Database bars: {len(db_df)}")
            print(f"✅ Tick-aggregated bars: {len(aggregated_1m)}")
            print(f"✅ Difference: {len(db_df) - len(aggregated_1m)} bars")
            
            # Find common timestamps
            common = aggregated_1m.index.intersection(db_df.index)
            print(f"\n🔗 Common timestamps: {len(common)}")
            
            if len(common) > 0:
                # Compare OHLC values
                comparison = pd.DataFrame({
                    'tick_open': aggregated_1m.loc[common, 'open'],
                    'db_open': db_df.loc[common, 'open'],
                    'tick_close': aggregated_1m.loc[common, 'close'],
                    'db_close': db_df.loc[common, 'close'],
                })
                comparison['open_diff'] = abs(comparison['tick_open'] - comparison['db_open'])
                comparison['close_diff'] = abs(comparison['tick_close'] - comparison['db_close'])
                
                print(f"\n📊 OHLC Differences (tick vs database):")
                print(f"   Open  - Mean diff: {comparison['open_diff'].mean():.4f} pips")
                print(f"   Open  - Max diff:  {comparison['open_diff'].max():.4f} pips")
                print(f"   Close - Mean diff: {comparison['close_diff'].mean():.4f} pips")
                print(f"   Close - Max diff:  {comparison['close_diff'].max():.4f} pips")
                
                # Show examples of large differences
                large_diffs = comparison[comparison['close_diff'] > 1.0]
                if len(large_diffs) > 0:
                    print(f"\n⚠️  Large differences (>1.0 pips): {len(large_diffs)} candles")
                    print(large_diffs.head(10))
            
            return db_df
    
    print("❌ Failed to fetch database bars")
    return None

def main():
    """Main analysis routine."""
    print("\n" + "="*80)
    print("VPS TICK DATA ANALYSIS")
    print("="*80)
    
    # US500 = pair 220
    symbol_id = 220
    start_date = "2026-01-09T00:00:00.000Z"
    end_date = "2026-01-09T23:59:59.999Z"
    
    # Fetch tick data
    ticks = fetch_tick_data(symbol_id, start_date, end_date, max_ticks=100000)
    
    if not ticks:
        print("No data fetched. Exiting.")
        return
    
    # Analyze ticks
    tick_df = analyze_tick_data(ticks)
    
    # Aggregate to 1m
    aggregated = aggregate_to_1m(ticks)
    
    # Compare with database
    if aggregated is not None:
        compare_with_database_bars(aggregated)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nKey Findings:")
    print("1. Check 'Ticks by Hour' to see when market is actually active")
    print("2. Check 'Large Gaps' to identify data quality issues")
    print("3. Check '1-Minute Candles' count vs database bars count")
    print("4. Review OHLC differences to understand signal discrepancies")
    print("\n")

if __name__ == "__main__":
    main()
