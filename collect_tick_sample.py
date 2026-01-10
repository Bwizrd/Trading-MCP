#!/usr/bin/env python3
"""
Collect a 10-minute tick data sample and aggregate to 1-minute bars.
"""

import sys
import pandas as pd
import json
from datetime import datetime, timedelta
from vps_data_fetcher import VPSDataFetcher


def aggregate_ticks_to_1m_bars(df_ticks: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate tick data into 1-minute OHLCV bars.
    
    Args:
        df_ticks: DataFrame with tick data (indexed by timestamp, with bid/ask columns)
    
    Returns:
        DataFrame with 1-minute OHLCV bars
    """
    # Use mid price (average of bid/ask) for OHLC
    df_ticks['mid'] = (df_ticks['bid'] + df_ticks['ask']) / 2
    
    # Resample to 1-minute bars
    bars = df_ticks['mid'].resample('1min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    })
    
    # Add volume (tick count per bar)
    bars['volume'] = df_ticks['mid'].resample('1min').count()
    
    # Calculate bid/ask OHLC as well
    bars['bid_open'] = df_ticks['bid'].resample('1min').first()
    bars['bid_high'] = df_ticks['bid'].resample('1min').max()
    bars['bid_low'] = df_ticks['bid'].resample('1min').min()
    bars['bid_close'] = df_ticks['bid'].resample('1min').last()
    
    bars['ask_open'] = df_ticks['ask'].resample('1min').first()
    bars['ask_high'] = df_ticks['ask'].resample('1min').max()
    bars['ask_low'] = df_ticks['ask'].resample('1min').min()
    bars['ask_close'] = df_ticks['ask'].resample('1min').last()
    
    # Drop rows with no ticks
    bars = bars.dropna()
    
    return bars


def main():
    # Initialize fetcher
    fetcher = VPSDataFetcher()
    
    # Yesterday's date
    yesterday = datetime.now().date() - timedelta(days=1)
    
    # Collect 10 minutes during US500 market hours (15:00 to 15:10, 3pm-3:10pm)
    start_time = f"{yesterday}T15:00:00.000Z"
    end_time = f"{yesterday}T15:10:00.000Z"
    
    print("=" * 70)
    print(f"Collecting 10-minute tick data sample for US500_SB")
    print(f"Date: {yesterday}")
    print(f"Time: 15:00:00 to 15:10:00 (3:00pm - 3:10pm)")
    print("=" * 70)
    
    # Fetch tick data
    tick_data = fetcher.fetch_tick_data("US500_SB", start_time, end_time, max_ticks=50000)
    
    if "error" in tick_data:
        print(f"❌ Error fetching data: {tick_data['error']}")
        return
    
    # Convert to DataFrame
    df_ticks = fetcher.ticks_to_dataframe(tick_data)
    
    if df_ticks.empty:
        print("❌ No tick data received")
        return
    
    print(f"\n✅ Received {len(df_ticks)} ticks")
    print(f"Time range: {df_ticks.index[0]} to {df_ticks.index[-1]}")
    print(f"\nFirst few ticks:")
    print(df_ticks.head())
    
    # Save raw tick data to CSV
    tick_filename = f"us500_ticks_{yesterday.strftime('%Y%m%d')}_1500-1510.csv"
    df_ticks.to_csv(tick_filename)
    print(f"\n💾 Saved raw ticks to: {tick_filename}")
    
    # Aggregate to 1-minute bars
    print("\n" + "=" * 70)
    print("Aggregating ticks to 1-minute bars...")
    print("=" * 70)
    
    df_1m_bars = aggregate_ticks_to_1m_bars(df_ticks)
    
    print(f"\n✅ Created {len(df_1m_bars)} 1-minute bars")
    print(f"\n1-Minute Bars (Mid Price):")
    print(df_1m_bars[['open', 'high', 'low', 'close', 'volume']])
    
    # Save 1-minute bars to CSV
    bars_filename = f"us500_1m_bars_{yesterday.strftime('%Y%m%d')}_1500-1510.csv"
    df_1m_bars.to_csv(bars_filename)
    print(f"\n💾 Saved 1-minute bars to: {bars_filename}")
    
    # Save as JSON for HTML serving
    bars_json = {
        "symbol": "US500_SB",
        "date": str(yesterday),
        "time_range": "15:00:00 to 15:10:00",
        "tick_count": len(df_ticks),
        "bar_count": len(df_1m_bars),
        "bars": df_1m_bars.reset_index().to_dict(orient='records')
    }
    
    json_filename = f"us500_1m_bars_{yesterday.strftime('%Y%m%d')}_1500-1510.json"
    with open(json_filename, 'w') as f:
        json.dump(bars_json, f, indent=2, default=str)
    
    print(f"💾 Saved JSON data to: {json_filename}")
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("Summary Statistics:")
    print("=" * 70)
    print(f"Total ticks: {len(df_ticks)}")
    print(f"Total bars: {len(df_1m_bars)}")
    print(f"Avg ticks per bar: {len(df_ticks) / len(df_1m_bars):.1f}")
    print(f"Price range: {df_1m_bars['low'].min():.2f} - {df_1m_bars['high'].max():.2f}")
    print(f"Total price movement: {df_1m_bars['high'].max() - df_1m_bars['low'].min():.2f} points")
    
    print("\n✅ Done! Files ready for HTML visualization.")


if __name__ == "__main__":
    main()
