#!/usr/bin/env python3
"""
Test stochastic calculation at 10:28 to compare with TradingView.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import pandas as pd
import ta
from datetime import datetime
from shared.data_connector import DataConnector

async def test_stochastic_at_1028():
    """Fetch data and calculate stochastic at 10:28."""
    
    # Fetch 1m data for today
    connector = DataConnector()
    
    response = await connector.get_market_data(
        symbol="US500_SB",
        timeframe="1m",
        start_date=datetime(2025, 12, 11),
        end_date=datetime(2025, 12, 11)
    )
    
    print(f"Fetched {len(response.data)} candles")
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'timestamp': c.timestamp,
        'open': c.open,
        'high': c.high,
        'low': c.low,
        'close': c.close,
        'volume': c.volume
    } for c in response.data])
    
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    # Find 10:28 candle
    target_time = datetime(2025, 12, 11, 10, 28)
    target_idx = df[df['timestamp'] == target_time].index
    
    if len(target_idx) == 0:
        print(f"❌ No candle found at {target_time}")
        print(f"Available times around 10:28:")
        mask = (df['timestamp'] >= datetime(2025, 12, 11, 10, 25)) & (df['timestamp'] <= datetime(2025, 12, 11, 10, 30))
        print(df[mask][['timestamp', 'close']])
        return
    
    target_idx = target_idx[0]
    print(f"\n✅ Found candle at 10:28, index={target_idx}")
    print(f"Close: {df.loc[target_idx, 'close']:.2f}")
    
    # Calculate all 4 stochastics
    stoch_configs = [
        {'name': 'fast', 'k_period': 9, 'k_smoothing': 1, 'd_smoothing': 3},
        {'name': 'med_fast', 'k_period': 14, 'k_smoothing': 1, 'd_smoothing': 3},
        {'name': 'med_slow', 'k_period': 40, 'k_smoothing': 1, 'd_smoothing': 4},
        {'name': 'slow', 'k_period': 60, 'k_smoothing': 1, 'd_smoothing': 10}
    ]
    
    print(f"\n=== Stochastic Values at 10:28 ===")
    
    for config in stoch_configs:
        name = config['name']
        k_period = config['k_period']
        k_smoothing = config['k_smoothing']
        d_smoothing = config['d_smoothing']
        
        # Calculate stochastic
        df_calc = df.copy()
        df_calc['lowest_low'] = df_calc['low'].rolling(window=k_period).min()
        df_calc['highest_high'] = df_calc['high'].rolling(window=k_period).max()
        df_calc['range'] = df_calc['highest_high'] - df_calc['lowest_low']
        df_calc['range'] = df_calc['range'].replace(0, 1e-10)
        df_calc['k_raw'] = ((df_calc['close'] - df_calc['lowest_low']) / df_calc['range']) * 100
        
        # Apply %K smoothing
        if k_smoothing > 1:
            df_calc['k'] = df_calc['k_raw'].rolling(window=k_smoothing).mean()
        else:
            df_calc['k'] = df_calc['k_raw']
        
        # Calculate %D
        df_calc['d'] = df_calc['k'].rolling(window=d_smoothing).mean()
        
        k_value = df_calc.loc[target_idx, 'k']
        d_value = df_calc.loc[target_idx, 'd']
        
        print(f"{name:12} ({k_period:2},{k_smoothing},{d_smoothing:2}): %K={k_value:6.2f}  %D={d_value:6.2f}")
        
        # Show the range used for calculation
        lowest = df_calc.loc[target_idx, 'lowest_low']
        highest = df_calc.loc[target_idx, 'highest_high']
        close = df_calc.loc[target_idx, 'close']
        print(f"             Range: Low={lowest:.2f}, High={highest:.2f}, Close={close:.2f}")
    
    print(f"\n=== TradingView Values (from screenshot) ===")
    print(f"Stoch 9 1 3:   ~89.65")
    print(f"Stoch 14 1 3:  ~92.86")
    print(f"Stoch 40 1 4:  ~95.24")
    print(f"Stoch 60 1 10: ~95.94")
    
    print(f"\n=== Data around 10:28 ===")
    start_idx = max(0, target_idx - 5)
    end_idx = min(len(df), target_idx + 6)
    print(df.iloc[start_idx:end_idx][['timestamp', 'open', 'high', 'low', 'close']])

if __name__ == "__main__":
    asyncio.run(test_stochastic_at_1028())
