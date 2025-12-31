#!/usr/bin/env python3
"""
Analyze Stochastic Zones for GER40 Today

This script fetches all 1-minute data for GER40 today, manually calculates
all 4 stochastics, and shows every time all 4 are in the setup zones.

Setup Zones:
- BUY: All 4 stochastics below 20
- SELL: All 4 stochastics above 80
"""

import asyncio
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.data_connector import DataConnector
from shared.indicators import StochasticCalculator
from shared.models import Candle


async def analyze_zones():
    """Analyze stochastic zones for GER40 today."""
    
    print("=" * 100)
    print("STOCHASTIC ZONE ANALYSIS - GER40_SB - December 30, 2025")
    print("=" * 100)
    
    # 1. Fetch data
    print("\n1. Fetching 1-minute data for GER40_SB today...")
    data_connector = DataConnector()
    
    start_date = datetime(2025, 12, 30, 0, 0, 0)
    end_date = datetime(2025, 12, 30, 23, 59, 59)
    
    response = await data_connector.get_market_data(
        symbol="GER40_SB",
        timeframe="1m",
        start_date=start_date,
        end_date=end_date
    )
    
    candles = response.data
    print(f"   ✓ Fetched {len(candles)} candles from {response.source}")
    if candles:
        print(f"   Time range: {candles[0].timestamp} to {candles[-1].timestamp}")
    
    # 2. Convert candles to dataframe for easier analysis
    print("\n2. Converting candles to dataframe...")
    df = pd.DataFrame([
        {
            'timestamp': c.timestamp,
            'open': c.open,
            'high': c.high,
            'low': c.low,
            'close': c.close,
            'volume': c.volume
        }
        for c in candles
    ])
    df.set_index('timestamp', inplace=True)
    print(f"   ✓ Converted {len(df)} candles to dataframe")
    
    # 3. Calculate all 4 stochastics
    print("\n3. Calculating 4 stochastics...")
    
    # Fast: k=9, k_smooth=1, d_smooth=3
    print("   - Fast (9,1,3)...")
    fast_calc = StochasticCalculator(k_period=9, k_smoothing=1, d_smoothing=3)
    fast_k_dict = fast_calc.calculate(candles)
    fast_d_dict = fast_calc.get_d_line()
    
    # Med Fast: k=14, k_smooth=1, d_smooth=3
    print("   - Med Fast (14,1,3)...")
    med_fast_calc = StochasticCalculator(k_period=14, k_smoothing=1, d_smoothing=3)
    med_fast_k_dict = med_fast_calc.calculate(candles)
    med_fast_d_dict = med_fast_calc.get_d_line()
    
    # Med Slow: k=40, k_smooth=1, d_smooth=4
    print("   - Med Slow (40,1,4)...")
    med_slow_calc = StochasticCalculator(k_period=40, k_smoothing=1, d_smoothing=4)
    med_slow_k_dict = med_slow_calc.calculate(candles)
    med_slow_d_dict = med_slow_calc.get_d_line()
    
    # Slow: k=60, k_smooth=1, d_smooth=10
    print("   - Slow (60,1,10)...")
    slow_calc = StochasticCalculator(k_period=60, k_smoothing=1, d_smoothing=10)
    slow_k_dict = slow_calc.calculate(candles)
    slow_d_dict = slow_calc.get_d_line()
    
    print("   ✓ All stochastics calculated")
    
    # 4. Create analysis dataframe
    print("\n4. Creating analysis dataframe...")
    
    # Convert dictionaries to series aligned with df index
    fast_k_series = pd.Series(fast_k_dict)
    fast_d_series = pd.Series(fast_d_dict)
    med_fast_k_series = pd.Series(med_fast_k_dict)
    med_fast_d_series = pd.Series(med_fast_d_dict)
    med_slow_k_series = pd.Series(med_slow_k_dict)
    med_slow_d_series = pd.Series(med_slow_d_dict)
    slow_k_series = pd.Series(slow_k_dict)
    slow_d_series = pd.Series(slow_d_dict)
    
    analysis_df = pd.DataFrame({
        'timestamp': df.index,
        'close': df['close'],
        'fast_k': fast_k_series,
        'fast_d': fast_d_series,
        'med_fast_k': med_fast_k_series,
        'med_fast_d': med_fast_d_series,
        'med_slow_k': med_slow_k_series,
        'med_slow_d': med_slow_d_series,
        'slow_k': slow_k_series,
        'slow_d': slow_d_series
    })
    
    print(f"   ✓ Analysis dataframe created with {len(analysis_df)} rows")
    
    # 5. Find zones where all 4 are in setup
    print("\n5. Analyzing setup zones...")
    
    # BUY zone: all 4 stochastics below 20
    buy_zone = (
        (analysis_df['fast_k'] < 20) &
        (analysis_df['med_fast_k'] < 20) &
        (analysis_df['med_slow_k'] < 20) &
        (analysis_df['slow_k'] < 20)
    )
    
    # SELL zone: all 4 stochastics above 80
    sell_zone = (
        (analysis_df['fast_k'] > 80) &
        (analysis_df['med_fast_k'] > 80) &
        (analysis_df['med_slow_k'] > 80) &
        (analysis_df['slow_k'] > 80)
    )
    
    buy_zone_count = buy_zone.sum()
    sell_zone_count = sell_zone.sum()
    
    print(f"\n   BUY Zone (all 4 below 20): {buy_zone_count} candles")
    print(f"   SELL Zone (all 4 above 80): {sell_zone_count} candles")
    
    # 6. Show BUY zone details
    if buy_zone_count > 0:
        print("\n" + "=" * 100)
        print("BUY ZONE DETAILS (All 4 Stochastics Below 20)")
        print("=" * 100)
        print(f"{'Time':<20} {'Close':<12} {'Fast':<8} {'MedFast':<8} {'MedSlow':<8} {'Slow':<8}")
        print("-" * 100)
        
        buy_df = analysis_df[buy_zone]
        for idx, row in buy_df.iterrows():
            time_str = row['timestamp'].strftime('%Y-%m-%d %H:%M')
            print(f"{time_str:<20} {row['close']:<12.2f} {row['fast_k']:<8.2f} {row['med_fast_k']:<8.2f} {row['med_slow_k']:<8.2f} {row['slow_k']:<8.2f}")
        
        # Find crossovers in BUY zone
        print("\n   Checking for fast stochastic crossing above 20 in BUY zone...")
        buy_crossovers = []
        for i in range(1, len(buy_df)):
            prev_idx = buy_df.index[i-1]
            curr_idx = buy_df.index[i]
            
            prev_fast = analysis_df.loc[prev_idx, 'fast_k']
            curr_fast = analysis_df.loc[curr_idx, 'fast_k']
            
            if prev_fast < 20 and curr_fast >= 20:
                buy_crossovers.append({
                    'time': analysis_df.loc[curr_idx, 'timestamp'],
                    'fast_k': curr_fast,
                    'close': analysis_df.loc[curr_idx, 'close']
                })
        
        if buy_crossovers:
            print(f"\n   ✓ Found {len(buy_crossovers)} BUY signals (fast crosses above 20):")
            for signal in buy_crossovers:
                print(f"      {signal['time'].strftime('%Y-%m-%d %H:%M')} - Fast: {signal['fast_k']:.2f}, Close: {signal['close']:.2f}")
        else:
            print("\n   ✗ No BUY signals found (fast never crossed above 20 in BUY zone)")
    
    # 7. Show SELL zone details
    if sell_zone_count > 0:
        print("\n" + "=" * 100)
        print("SELL ZONE DETAILS (All 4 Stochastics Above 80)")
        print("=" * 100)
        print(f"{'Time':<20} {'Close':<12} {'Fast':<8} {'MedFast':<8} {'MedSlow':<8} {'Slow':<8}")
        print("-" * 100)
        
        sell_df = analysis_df[sell_zone]
        for idx, row in sell_df.iterrows():
            time_str = row['timestamp'].strftime('%Y-%m-%d %H:%M')
            print(f"{time_str:<20} {row['close']:<12.2f} {row['fast_k']:<8.2f} {row['med_fast_k']:<8.2f} {row['med_slow_k']:<8.2f} {row['slow_k']:<8.2f}")
        
        # Find crossovers in SELL zone
        print("\n   Checking for fast stochastic crossing below 80 in SELL zone...")
        sell_crossovers = []
        for i in range(1, len(sell_df)):
            prev_idx = sell_df.index[i-1]
            curr_idx = sell_df.index[i]
            
            prev_fast = analysis_df.loc[prev_idx, 'fast_k']
            curr_fast = analysis_df.loc[curr_idx, 'fast_k']
            
            if prev_fast > 80 and curr_fast <= 80:
                sell_crossovers.append({
                    'time': analysis_df.loc[curr_idx, 'timestamp'],
                    'fast_k': curr_fast,
                    'close': analysis_df.loc[curr_idx, 'close']
                })
        
        if sell_crossovers:
            print(f"\n   ✓ Found {len(sell_crossovers)} SELL signals (fast crosses below 80):")
            for signal in sell_crossovers:
                print(f"      {signal['time'].strftime('%Y-%m-%d %H:%M')} - Fast: {signal['fast_k']:.2f}, Close: {signal['close']:.2f}")
        else:
            print("\n   ✗ No SELL signals found (fast never crossed below 80 in SELL zone)")
    
    # 8. Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Total candles analyzed: {len(analysis_df)}")
    print(f"BUY zone candles (all 4 below 20): {buy_zone_count}")
    print(f"SELL zone candles (all 4 above 80): {sell_zone_count}")
    
    if buy_zone_count == 0 and sell_zone_count == 0:
        print("\n⚠️  WARNING: No setup zones found!")
        print("   This means all 4 stochastics were NEVER simultaneously in the setup zones.")
        print("   This explains why the backtest found so few signals.")
    
    # 9. Save detailed CSV for further analysis
    output_file = "copilot-tests/stochastic_analysis_ger40_20251230.csv"
    analysis_df.to_csv(output_file, index=False)
    print(f"\n✓ Detailed analysis saved to: {output_file}")
    
    return analysis_df, buy_zone, sell_zone


if __name__ == "__main__":
    asyncio.run(analyze_zones())
