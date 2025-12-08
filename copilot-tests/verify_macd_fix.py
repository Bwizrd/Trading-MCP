#!/usr/bin/env python3
"""
Verify that the MACD crossover bug fix is working.
"""

import json
from datetime import datetime, timedelta
from shared.strategies.dsl_interpreter.dsl_strategy import DSLStrategy
from shared.models import Candle
from shared.strategy_interface import StrategyContext

def create_candle(timestamp, close):
    return Candle(
        timestamp=timestamp,
        open=close - 0.0001,
        high=close + 0.0001,
        low=close - 0.0002,
        close=close,
        volume=1000
    )

print("="*70)
print("MACD CROSSOVER BUG FIX VERIFICATION")
print("="*70)

# Load MACD strategy
with open('shared/strategies/dsl_strategies/macd_crossover_strategy.json') as f:
    config = json.load(f)

strategy = DSLStrategy(config)
print(f"\n✓ Loaded strategy: {strategy.get_name()}")

# Generate enough candles for MACD calculation (need 35+)
print(f"\n✓ Generating test data with crossover pattern...")
start_time = datetime(2024, 1, 1, 9, 0)
base_price = 1.0500

# Create a price pattern that will cause a MACD crossover
# First 40 candles: downtrend (MACD below signal)
# Next 20 candles: uptrend (MACD crosses above signal)
candles = []
for i in range(60):
    timestamp = start_time + timedelta(minutes=15 * i)
    if i < 40:
        # Downtrend
        price = base_price - (i * 0.00002)
    else:
        # Uptrend - this should cause MACD to cross above signal
        price = base_price - (40 * 0.00002) + ((i - 40) * 0.00003)
    
    candles.append(create_candle(timestamp, price))

# Process candles and look for signals
signals_generated = []
for i, candle in enumerate(candles):
    context = StrategyContext(
        current_candle=candle,
        symbol="EURUSD",
        timeframe="15m",
        current_position=None,
        historical_candles=[],
        indicators={}
    )
    
    # Calculate indicators
    strategy.on_candle_processed(context)
    
    # Try to generate signal
    signal = strategy.generate_signal(context)
    if signal:
        signals_generated.append((i, candle.timestamp, signal.direction, candle.close))

print(f"\n✓ Processed {len(candles)} candles")
print(f"\n{'='*70}")
print(f"RESULTS:")
print(f"{'='*70}")
print(f"\nSignals Generated: {len(signals_generated)}")

if signals_generated:
    print(f"\n✅ SUCCESS! The MACD crossover detection is WORKING!")
    print(f"\nSignal Details:")
    for idx, timestamp, direction, price in signals_generated:
        print(f"  Candle {idx}: {timestamp} - {direction} @ {price:.5f}")
else:
    print(f"\n⚠️  No signals generated in test data")
    print(f"   This could mean:")
    print(f"   1. The test data didn't create a strong enough crossover")
    print(f"   2. The crossover detection logic needs more investigation")

print(f"\n{'='*70}")
print(f"DIAGNOSTIC LOG ANALYSIS:")
print(f"{'='*70}")

# Analyze the diagnostic log
import subprocess
result = subprocess.run(['grep', '-c', 'Evaluation result: True', '/tmp/dsl_debug.log'], 
                       capture_output=True, text=True)
true_evals = result.stdout.strip() if result.returncode == 0 else "0"

result = subprocess.run(['grep', '-c', 'CROSSOVER DETECTED', '/tmp/dsl_debug.log'], 
                       capture_output=True, text=True)
crossovers = result.stdout.strip() if result.returncode == 0 else "0"

result = subprocess.run(['grep', '-c', 'Unresolved variables', '/tmp/dsl_debug.log'], 
                       capture_output=True, text=True)
unresolved = result.stdout.strip() if result.returncode == 0 else "0"

print(f"\nConditions evaluated to True: {true_evals}")
print(f"Crossovers detected: {crossovers}")
print(f"Unresolved variable errors: {unresolved}")

print(f"\n{'='*70}")
print(f"BUG FIX STATUS:")
print(f"{'='*70}")

if unresolved == "0":
    print(f"\n✅ Variable replacement bug is FIXED!")
    print(f"   No 'Unresolved variables' errors in log")
else:
    print(f"\n❌ Variable replacement bug still present")
    print(f"   Found {unresolved} unresolved variable errors")

if int(true_evals) > 0:
    print(f"\n✅ Condition evaluation is WORKING!")
    print(f"   {true_evals} conditions evaluated to True")
else:
    print(f"\n⚠️  No conditions evaluated to True")

print(f"\nView full diagnostic log: cat /tmp/dsl_debug.log")
print(f"{'='*70}\n")
