#!/usr/bin/env python3
"""
Test if TradingView uses inverted stochastic formula.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import pandas as pd
from datetime import datetime
from shared.data_connector import DataConnector

async def test_inverted_stochastic():
    """Test inverted stochastic formula."""
    
    # Fetch 1m data for today
    connector = DataConnector()
    
    response = await connector.get_market_data(
        symbol="US500_SB",
        timeframe="1m",
        start_date=datetime(2025, 12, 11),
        end_date=datetime(2025, 12, 11)
    )
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'timestamp': c.timestamp,
        'open': c.open,
        'high': c.high,
        'low': c.low,
        'close': c.close,
        'volume': c.volume
    } for c in response.data])
    
    df = df.sort_values('timestamp')
    
    # Find 10:28
    target_time = datetime(2025, 12, 11, 10, 28)
    target_idx = df[df['timestamp'] == target_time].index[0]
    
    print(f"Testing at 10:28 (index {target_idx})")
    print(f"Close: {df.loc[target_idx, 'close']:.2f}\n")
    
    # Test fast stochastic (9,1,3)
    k_period = 9
    
    df_calc = df.copy()
    df_calc['lowest_low'] = df_calc['low'].rolling(window=k_period).min()
    df_calc['highest_high'] = df_calc['high'].rolling(window=k_period).max()
    df_calc['range'] = df_calc['highest_high'] - df_calc['lowest_low']
    df_calc['range'] = df_calc['range'].replace(0, 1e-10)
    
    # Standard formula
    df_calc['k_standard'] = ((df_calc['close'] - df_calc['lowest_low']) / df_calc['range']) * 100
    
    # Inverted formula
    df_calc['k_inverted'] = ((df_calc['highest_high'] - df_calc['close']) / df_calc['range']) * 100
    
    # Alternative: 100 - standard
    df_calc['k_complement'] = 100 - df_calc['k_standard']
    
    standard = df_calc.loc[target_idx, 'k_standard']
    inverted = df_calc.loc[target_idx, 'k_inverted']
    complement = df_calc.loc[target_idx, 'k_complement']
    
    lowest = df_calc.loc[target_idx, 'lowest_low']
    highest = df_calc.loc[target_idx, 'highest_high']
    close = df_calc.loc[target_idx, 'close']
    
    print(f"Range: Low={lowest:.2f}, High={highest:.2f}, Close={close:.2f}")
    print(f"\nStandard formula:  %K = {standard:.2f}")
    print(f"Inverted formula:  %K = {inverted:.2f}")
    print(f"Complement (100-K): %K = {complement:.2f}")
    print(f"\nTradingView shows: %K ≈ 89.65")
    
    # Check which matches
    tv_value = 89.65
    diff_standard = abs(standard - tv_value)
    diff_inverted = abs(inverted - tv_value)
    diff_complement = abs(complement - tv_value)
    
    print(f"\nDifferences from TradingView:")
    print(f"Standard:   {diff_standard:.2f}")
    print(f"Inverted:   {diff_inverted:.2f}")
    print(f"Complement: {diff_complement:.2f}")
    
    if diff_complement < 5:
        print(f"\n✅ MATCH! TradingView appears to use: 100 - standard_stochastic")
        print(f"   This means we need to invert our calculation!")

if __name__ == "__main__":
    asyncio.run(test_inverted_stochastic())
