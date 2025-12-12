#!/usr/bin/env python3
"""
Calculate stochastic using the correct cTrader data at 10:28 UTC-5.
"""

import json
import pandas as pd
from datetime import datetime

# Load cTrader data
with open('cTraderData.json', 'r') as f:
    data = json.load(f)

candles = data['data']

# Convert to DataFrame
df = pd.DataFrame([{
    'timestamp': datetime.utcfromtimestamp(c['timestamp'] / 1000),
    'open': c['open'],
    'high': c['high'],
    'low': c['low'],
    'close': c['close'],
    'volume': c['volume']
} for c in candles])

# Find 10:28 UTC-5 (which is 15:28 UTC)
target_time = datetime(2025, 12, 11, 15, 28)
target_idx = df[df['timestamp'] == target_time].index

if len(target_idx) == 0:
    print("Target time not found!")
    exit(1)

target_idx = target_idx[0]

print(f"Found 10:28 (UTC-5) at index {target_idx}")
print(f"Close: {df.loc[target_idx, 'close']:.2f}\n")

# Calculate all 4 stochastics
stoch_configs = [
    {'name': 'fast', 'k_period': 9, 'k_smoothing': 1, 'd_smoothing': 3},
    {'name': 'med_fast', 'k_period': 14, 'k_smoothing': 1, 'd_smoothing': 3},
    {'name': 'med_slow', 'k_period': 40, 'k_smoothing': 1, 'd_smoothing': 4},
    {'name': 'slow', 'k_period': 60, 'k_smoothing': 1, 'd_smoothing': 10}
]

print("=== Stochastic Values at 10:28 (UTC-5) ===\n")

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

print("\n=== TradingView Values (from CSV) ===")
print("Stoch 1:  %D = 89.65")
print("Stoch 2:  %D = 92.96")
print("Stoch 3:  %D = 95.24")
print("Stoch 4:  %D = 95.54")
