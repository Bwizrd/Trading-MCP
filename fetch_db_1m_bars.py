#!/usr/bin/env python3
"""
Fetch 1m bars from database and extract the same time range as tick data sample.
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta


def fetch_1m_bars_from_db(symbol_id: int = 220, bars: int = 1500):
    """
    Fetch 1m bars from database.
    
    Args:
        symbol_id: Symbol pair ID (220 = US500_SB)
        bars: Number of bars to fetch
    
    Returns:
        Dictionary with bar data
    """
    url = f"http://localhost:8020/getDataFromDB"
    params = {
        "pair": symbol_id,
        "timeframe": "1m",
        "bars": bars
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return {"error": str(e)}


def main():
    # Yesterday's date
    yesterday = datetime.now().date() - timedelta(days=1)
    
    # Target time range (same as tick data)
    target_start = datetime.strptime(f"{yesterday} 15:00:00", "%Y-%m-%d %H:%M:%S")
    target_end = datetime.strptime(f"{yesterday} 15:10:00", "%Y-%m-%d %H:%M:%S")
    
    print("=" * 70)
    print(f"Fetching 1m bars from database for US500_SB")
    print(f"Target time range: {target_start} to {target_end}")
    print("=" * 70)
    
    # Fetch bars
    data = fetch_1m_bars_from_db(symbol_id=220, bars=1500)
    
    if "error" in data:
        print(f"❌ Error: {data['error']}")
        return
    
    print(f"\nResponse keys: {data.keys()}")
    
    # Convert to DataFrame
    if "data" in data:
        bars = data["data"]
    elif "bars" in data:
        bars = data["bars"]
    elif isinstance(data, list):
        bars = data
    else:
        print(f"Unexpected data structure: {data.keys() if isinstance(data, dict) else type(data)}")
        return
    
    df = pd.DataFrame(bars)
    print(f"\n✅ Received {len(df)} bars")
    print(f"DataFrame columns: {df.columns.tolist()}")
    print(f"\nFirst few bars:")
    print(df.head())
    
    # Convert timestamp/time column to datetime
    time_col = None
    for col in ["timestamp", "time", "date", "datetime", "t"]:
        if col in df.columns:
            time_col = col
            break
    
    if time_col:
        # Check if timestamp is in milliseconds
        if df[time_col].iloc[0] > 1e12:
            df[time_col] = pd.to_datetime(df[time_col], unit='ms')
        else:
            df[time_col] = pd.to_datetime(df[time_col])
        
        df.set_index(time_col, inplace=True)
    
    print(f"\nTime range in data: {df.index[0]} to {df.index[-1]}")
    
    # Filter to target time range
    df_filtered = df[(df.index >= target_start) & (df.index <= target_end)]
    
    print(f"\n✅ Filtered to {len(df_filtered)} bars in target range")
    print(f"\nFiltered 1m bars:")
    print(df_filtered)
    
    # Save filtered bars
    csv_filename = f"us500_1m_bars_DB_{yesterday.strftime('%Y%m%d')}_1500-1510.csv"
    df_filtered.to_csv(csv_filename)
    print(f"\n💾 Saved database 1m bars to: {csv_filename}")
    
    # Save as JSON
    bars_json = {
        "symbol": "US500_SB",
        "date": str(yesterday),
        "time_range": "15:00:00 to 15:10:00",
        "source": "database",
        "bar_count": len(df_filtered),
        "bars": df_filtered.reset_index().to_dict(orient='records')
    }
    
    json_filename = f"us500_1m_bars_DB_{yesterday.strftime('%Y%m%d')}_1500-1510.json"
    with open(json_filename, 'w') as f:
        json.dump(bars_json, f, indent=2, default=str)
    
    print(f"💾 Saved JSON to: {json_filename}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    print(f"Database bars in range: {len(df_filtered)}")
    if len(df_filtered) > 0 and 'o' in df_filtered.columns:
        print(f"Price range: {df_filtered['l'].min():.2f} - {df_filtered['h'].max():.2f}")
    elif len(df_filtered) > 0 and 'open' in df_filtered.columns:
        print(f"Price range: {df_filtered['low'].min():.2f} - {df_filtered['high'].max():.2f}")
    
    print("\n✅ Done! Ready to compare with tick-aggregated bars.")


if __name__ == "__main__":
    main()
