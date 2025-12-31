#!/usr/bin/env python3
"""
Find signals using the CORRECT logic from Signal Monitor.

CORRECT LOGIC:
- BUY: Previous candle all 4 < 20, current candle fast crosses above 20
- SELL: Previous candle all 4 > 80, current candle fast crosses below 80
"""

import pandas as pd

# Load the analysis data
df = pd.read_csv('copilot-tests/stochastic_analysis_ger40_20251230.csv')

print("=" * 100)
print("CORRECT SIGNAL DETECTION - Matching Rust Signal Monitor Logic")
print("=" * 100)

buy_signals = []
sell_signals = []

# Iterate through candles (starting from index 1 to have previous candle)
for i in range(1, len(df)):
    prev = df.iloc[i-1]
    curr = df.iloc[i]
    
    # Check BUY signal
    # Previous: all 4 < 20
    prev_all_below_20 = (
        prev['fast_k'] < 20 and
        prev['med_fast_k'] < 20 and
        prev['med_slow_k'] < 20 and
        prev['slow_k'] < 20
    )
    
    # Current: fast crosses above 20
    fast_crosses_above = prev['fast_k'] < 20 and curr['fast_k'] >= 20
    
    if prev_all_below_20 and fast_crosses_above:
        buy_signals.append({
            'time': curr['timestamp'],
            'prev_fast': prev['fast_k'],
            'curr_fast': curr['fast_k'],
            'prev_all': [prev['fast_k'], prev['med_fast_k'], prev['med_slow_k'], prev['slow_k']],
            'curr_all': [curr['fast_k'], curr['med_fast_k'], curr['med_slow_k'], curr['slow_k']],
            'price': curr['close']
        })
    
    # Check SELL signal
    # Previous: all 4 > 80
    prev_all_above_80 = (
        prev['fast_k'] > 80 and
        prev['med_fast_k'] > 80 and
        prev['med_slow_k'] > 80 and
        prev['slow_k'] > 80
    )
    
    # Current: fast crosses below 80
    fast_crosses_below = prev['fast_k'] > 80 and curr['fast_k'] <= 80
    
    if prev_all_above_80 and fast_crosses_below:
        sell_signals.append({
            'time': curr['timestamp'],
            'prev_fast': prev['fast_k'],
            'curr_fast': curr['fast_k'],
            'prev_all': [prev['fast_k'], prev['med_fast_k'], prev['med_slow_k'], prev['slow_k']],
            'curr_all': [curr['fast_k'], curr['med_fast_k'], curr['med_slow_k'], curr['slow_k']],
            'price': curr['close']
        })

print(f"\n✅ BUY SIGNALS FOUND: {len(buy_signals)}")
if buy_signals:
    print("\nBUY SIGNAL DETAILS:")
    print("-" * 100)
    for sig in buy_signals:
        print(f"\nTime: {sig['time']}")
        print(f"Price: {sig['price']:.2f}")
        print(f"Previous candle stochastics: {[f'{x:.2f}' for x in sig['prev_all']]}")
        print(f"Current candle stochastics:  {[f'{x:.2f}' for x in sig['curr_all']]}")
        print(f"Fast crossed: {sig['prev_fast']:.2f} → {sig['curr_fast']:.2f}")

print(f"\n✅ SELL SIGNALS FOUND: {len(sell_signals)}")
if sell_signals:
    print("\nSELL SIGNAL DETAILS:")
    print("-" * 100)
    for sig in sell_signals:
        print(f"\nTime: {sig['time']}")
        print(f"Price: {sig['price']:.2f}")
        print(f"Previous candle stochastics: {[f'{x:.2f}' for x in sig['prev_all']]}")
        print(f"Current candle stochastics:  {[f'{x:.2f}' for x in sig['curr_all']]}")
        print(f"Fast crossed: {sig['prev_fast']:.2f} → {sig['curr_fast']:.2f}")

print("\n" + "=" * 100)
print(f"TOTAL SIGNALS: {len(buy_signals) + len(sell_signals)}")
print("=" * 100)
