# Trailing Stop OHLC Ambiguity Bug Fix

## Date: January 10, 2026

## Problem Summary

Trailing stops were exiting trades prematurely due to a fundamental limitation of OHLC (Open-High-Low-Close) data: **we don't know the order of price movements within a candle**.

## The Core Problem: OHLC Ambiguity

### Example Trade That Exposed the Issue

**Trade #14 on US500_SB (2026-01-09 15:10:00):**

- Entry: 6918.3 @ 15:10:00 (BUY)
- Exit: 6922.6 @ 15:12:00 = +4.3 pips
- Configuration: Activation 4 pips, Trail distance 8 pips

**The 15:12:00 Candle:**
```
Open:  6922.3
High:  6930.6  (+12.3 pips from entry!)
Low:   6921.6
Close: 6930.6
Range: 9.0 pips (larger than 8-pip trail distance)
```

**What the backtest did:**
1. Saw high of 6930.6 → Set trailing stop to 6930.6 - 8 = 6922.6
2. Saw low of 6921.6 → Triggered trailing stop exit at 6922.6

**The Problem:** We don't know which happened first!

**Scenario A (what backtest assumed):**
```
Price goes to 6930.6 → Trailing stop set to 6922.6 → Price drops to 6921.6 → Stop triggered ✓
```

**Scenario B (what might have actually happened):**
```
Price drops to 6921.6 → Price rallies to 6930.6 → Trailing stop set to 6922.6 → Trade continues ✓
```

With only OHLC data, **we cannot distinguish between these scenarios**. Any candle with a range larger than the trail distance will have this ambiguity.

### Why This Matters

After the exit at 15:12:00, price continued rallying:
- 15:13:00: High 6934.8 (would have been +16.5 pips)
- 15:14:00: High 6935.8 (would have been +17.5 pips)
- 15:15:00: High 6937.1 (would have been +18.8 pips)
- 15:16:00: High 6938.8 (would have been +20.5 pips)

The trade could have captured 20+ pips instead of just 4.3 pips.

## The Solution: One-Candle Delay

To eliminate OHLC ambiguity, we implement a **one-candle delay** for trailing stop updates:

### Before (Ambiguous):
```python
for candle in candles:
    # Update trailing stop using THIS candle
    update_trailing_stop(trade, candle)
    
    # Check if THIS candle hits the stop
    if candle.low <= trailing_stop:
        exit_trade()
```

**Problem:** Both update and check use the same candle, creating ambiguity about order.

### After (Unambiguous):
```python
previous_candle = entry_candle

for candle in candles:
    # Update trailing stop using PREVIOUS candle
    update_trailing_stop(trade, previous_candle)
    
    # Check if CURRENT candle hits the stop
    if candle.low <= trailing_stop:
        exit_trade()
    
    previous_candle = candle
```

**Benefit:** Trailing stop is always set based on completed price action (previous candle), then we check if the current candle hits it. No ambiguity.

## Implementation Details

### Key Changes

1. **`_execute_trade_with_window` method:**
   - Maintains `previous_candle` variable
   - Updates trailing stop using previous candle
   - Checks exit conditions using current candle

2. **New `_check_exit_conditions_simple` method:**
   - Separated from trailing stop update logic
   - Only checks if current candle hits existing stop levels
   - No longer updates trailing stop internally

3. **`_update_trailing_stop` method:**
   - Changed from using `candle.high/low` to `candle.close`
   - More conservative and realistic
   - Represents actual market state at candle completion

### Trade #14 With The Fix

**15:10:00 (Entry):**
- Entry: 6918.3
- Trailing stop: Not activated yet

**15:11:00:**
- Previous candle (15:10) close: 6921.3 → Profit: +3.0 pips (not enough)
- Current candle (15:11) check: No exit

**15:12:00:**
- Previous candle (15:11) close: 6922.1 → Profit: +3.8 pips (not enough)
- Current candle (15:12) check: No exit
- Close: 6930.6

**15:13:00:**
- Previous candle (15:12) close: 6930.6 → Profit: +12.3 pips (ACTIVATES!)
- Trailing stop set to: 6930.6 - 8 = 6922.6
- Current candle (15:13) low: 6930.3 → No exit
- Trade continues!

**Result:** Trade stays open longer, capturing more profit.

## Why This Is The Correct Approach

### 1. Eliminates Ambiguity
- Trailing stop is always based on completed candles
- Exit checks use fresh candle data
- No overlap between update and check

### 2. Conservative But Fair
- Slightly delays trailing stop activation (by one candle)
- But prevents premature exits from OHLC ambiguity
- Net result: Better profit capture

### 3. Realistic Execution
- In real trading, you observe a candle close, then set your trailing stop
- The next candle determines if you get stopped out
- This matches real-world trading behavior

## Alternative Solutions Considered

### 1. Use Tick Data
**Pros:** Perfect accuracy, know exact order of events
**Cons:** 
- Requires tick data storage (massive data volume)
- Not available for all symbols/timeframes
- Computationally expensive

### 2. Assume Best Case
**Pros:** Maximizes backtest profits
**Cons:** 
- Unrealistic, overly optimistic
- Doesn't match real trading results
- Creates false confidence

### 3. Assume Worst Case
**Pros:** Conservative, safe
**Cons:** 
- Overly pessimistic
- May reject profitable strategies
- Doesn't match real trading results

### 4. One-Candle Delay (Our Solution)
**Pros:** 
- Eliminates ambiguity completely
- Realistic execution model
- Matches real trading behavior
- Simple to implement and understand
**Cons:** 
- Slightly delays trailing stop activation
- May miss some very short-term moves

## Files Modified

- `shared/backtest_engine.py`:
  - Updated `_execute_trade_with_window` method (lines ~950-1020)
  - Added `_check_exit_conditions_simple` method (lines ~1020-1050)
  - Updated `_update_trailing_stop` to use close price (lines 1117-1157)

## Testing Required

1. Re-run US500_SB backtest for 2026-01-09
2. Verify trade #14 captures more profit
3. Check for any trades that now stay open too long
4. Compare overall metrics (total pips, win rate, profit factor)

## Expected Results

- **Average win size:** Should increase (trades ride trends longer)
- **Largest wins:** Should increase significantly
- **Win rate:** May decrease slightly (some small wins become losses)
- **Profit factor:** Should improve overall
- **Total pips:** Should increase substantially

## Conclusion

The OHLC ambiguity problem is fundamental to backtesting with candle data. By implementing a one-candle delay for trailing stop updates, we eliminate this ambiguity while maintaining realistic execution. This ensures trailing stops work as intended, allowing trades to capture full profit potential without premature exits.

The slight delay in trailing stop activation is a small price to pay for eliminating the systematic bias that was causing early exits on every wide-range candle.
