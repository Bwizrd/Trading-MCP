# Crossover Logic Fix and Signal Discrepancy Analysis

## Date: December 30, 2025

## Problem
Real-time Rust Signal Monitor generated **32 trades** on December 30, 2025, but Python backtest initially found only **2 trades**, then **4 trades**, then **12 trades** after fixing trading hours.

## Root Cause Identified

### 1. Crossover Detection Logic Mismatch

**ISSUE**: Python used strict inequalities, Rust used inclusive inequalities

**Rust Logic (CORRECT)**:
```rust
// BUY crossover
previous_stochastics[0] < threshold_low && current_stochastics[0] >= threshold_low

// SELL crossover  
previous_stochastics[0] > threshold_high && current_stochastics[0] <= threshold_high
```

**Python Logic (WRONG - BEFORE FIX)**:
```python
# detect_cross_above
crossed = previous <= threshold < current  # Strict < on current

# detect_cross_below
crossed = previous >= threshold > current  # Strict > on current
```

**Python Logic (FIXED)**:
```python
# detect_cross_above
crossed = previous < threshold and current >= threshold  # Uses >= like Rust

# detect_cross_below
crossed = previous > threshold and current <= threshold  # Uses <= like Rust
```

**IMPACT**: The strict inequality missed cases where the indicator value equals the threshold exactly (e.g., fast stochastic = 20.00 or 80.00).

### 2. Signal Count Analysis

After fixing the crossover logic:

| Metric | Count | Notes |
|--------|-------|-------|
| **Total raw signals** | 61 | 14 BUY + 47 SELL (entire day) |
| **Signals within trading hours** | 36 | 09:00-17:30 CET |
| **Python backtest trades** | 13-14 | With trend filter |
| **Rust real-time trades** | 32 | Production system |

### 3. Remaining Discrepancy

**Why Python shows 13-14 trades vs Rust 32 trades?**

The difference is caused by:

1. **One Trade at a Time Rule**: Python backtest blocks signal generation while a position is open
   - Logs show: "Skipping signal generation @ [time] - active position exists"
   - This blocks ~22 signals (36 signals - 14 trades = 22 blocked)

2. **Trend Filter**: `min_trend_range_pips = 10.0`
   - Blocks signals when market isn't trending enough
   - Disabling this (set to 0.0) only added 1 more trade (13 → 14)
   - Not the main cause of discrepancy

3. **Rust System Likely Allows Multiple Concurrent Trades**
   - 32 trades ≈ 36 raw signals (89% of signals became trades)
   - This suggests Rust doesn't block signals while positions are open
   - Or uses a different position management strategy

## Files Modified

### `shared/strategies/dsl_interpreter/advanced_components.py`

**Changed `detect_cross_above` method**:
- Line 115: `crossed = previous < threshold and current >= threshold`
- Added note: "Uses >= for current value to match Rust Signal Monitor logic"

**Changed `detect_cross_below` method**:
- Line 145: `crossed = previous > threshold and current <= threshold`
- Added note: "Uses <= for current value to match Rust Signal Monitor logic"

## Testing Results

### Before Fix (Strict Inequalities)
- Trading hours: 14:30-21:00 (WRONG)
- Trades: 2

### After Trading Hours Fix
- Trading hours: 09:00-17:30 (CORRECT)
- Trades: 12

### After Crossover Logic Fix
- Crossover: Uses `>=` and `<=` (CORRECT)
- Trades: 13

### After Disabling Trend Filter
- Trend filter: 0.0 (disabled)
- Trades: 14

## Recommendations

### For Matching Rust Behavior Exactly

1. **Verify Rust Position Management**:
   - Check if Rust allows multiple concurrent positions
   - Check if Rust has "one trade at a time" rule
   - Check if Rust has trend filter enabled

2. **Consider Disabling "One Trade at a Time" Rule**:
   - This would allow ~36 trades (matching raw signal count)
   - Would be closer to Rust's 32 trades
   - Need to verify if this matches production behavior

3. **Verify Trend Filter Configuration**:
   - Check if Rust has `min_trend_range_pips` enabled
   - Current Python value: 10.0 pips
   - Disabling it only added 1 trade, so not the main issue

### For Production Alignment

**CRITICAL**: Before making changes, verify the Rust Signal Monitor configuration:
- Does it allow multiple concurrent positions?
- What is the exact trend filter configuration?
- Are there any other filters not present in Python?

## Conclusion

The crossover logic fix is **CORRECT** and now matches the Rust implementation. The remaining discrepancy (14 Python trades vs 32 Rust trades) is primarily due to the "one trade at a time" rule in the Python backtest, which blocks ~22 signals while positions are open.

To achieve exact parity with Rust (32 trades), the Python backtest would need to allow multiple concurrent positions or use the same position management strategy as the Rust system.
