# Backtest Comparison: Before vs After "One Trade at a Time" Fix

## Test Date: December 11, 2025
**Symbol:** US500_SB  
**Timeframe:** 1m  
**Strategy:** Stochastic Quad Rotation  
**Trading Hours:** 14:30 - 21:00 UTC (US Market Hours)

---

## BEFORE FIX (Overlapping Trades Allowed)

### Performance Metrics
- **Total Trades:** 31
- **Winning Trades:** 10 (32.3%)
- **Losing Trades:** 21
- **Total Pips:** -20.0 pips
- **Win Rate:** 32.3%
- **Profit Factor:** ~0.7

### Critical Issues
- ❌ **30 out of 31 trades were OVERLAPPING**
- ❌ Multiple positions open simultaneously
- ❌ Some trades ran concurrently for over 2 hours
- ❌ Unrealistic trading scenario
- ❌ Does not match manual trading behavior

### Example Overlapping Trades
```
Trade #6:  Entry: 15:25, Exit: 17:42 (137 minutes)
Trade #7:  Entry: 15:28, Exit: 15:30 (2 minutes)   ← Overlaps with #6
Trade #8:  Entry: 15:29, Exit: 15:31 (2 minutes)   ← Overlaps with #6 and #7
Trade #9:  Entry: 15:30, Exit: 15:32 (2 minutes)   ← Overlaps with #6 and #8
```

---

## AFTER FIX (One Trade at a Time)

### Performance Metrics
- **Total Trades:** 4
- **Winning Trades:** 1 (25.0%)
- **Losing Trades:** 3
- **Total Pips:** -20.0 pips
- **Win Rate:** 25.0%
- **Average Win:** +25.0 pips
- **Average Loss:** -15.0 pips
- **Profit Factor:** 0.56
- **Max Drawdown:** 30.0 pips

### Trade Details
```
Trade #1: BUY  @ 14:31 → 14:53 = -15.0 pips (LOSS) [22 min]
Trade #2: BUY  @ 14:58 → 15:12 = +25.0 pips (WIN)  [14 min]
Trade #3: SELL @ 15:25 → 17:42 = -15.0 pips (LOSS) [137 min]
Trade #4: SELL @ 18:10 → 21:06 = -15.0 pips (LOSS) [176 min]
```

### Key Improvements
- ✅ **0 overlapping trades** - all sequential
- ✅ Each trade completes before the next starts
- ✅ Realistic trading scenario
- ✅ Matches manual trading behavior
- ✅ Proper position management

### Backtest Engine Logs
```
Skipping signal generation @ 14:32 - active position exists (entry: 14:31, direction: BUY)
Skipping signal generation @ 14:33 - active position exists (entry: 14:31, direction: BUY)
...
Trade closed: BUY @ 14:53 (before current candle @ 14:53)
Signal generated: BUY @ 14:58
```

---

## Analysis

### Trade Count Reduction
- **Before:** 31 trades (mostly overlapping)
- **After:** 4 trades (all sequential)
- **Reduction:** 87% fewer trades

This dramatic reduction is expected and correct because:
1. The fast stochastic can cross the threshold multiple times
2. Without position tracking, each crossover generated a new signal
3. With position tracking, new signals are blocked while a trade is active
4. This matches real manual trading where you can only hold one position

### Win Rate Change
- **Before:** 32.3% (10 wins / 31 trades)
- **After:** 25.0% (1 win / 4 trades)

The win rate decreased slightly, but this is more realistic because:
1. We're no longer taking quick scalp trades during an active position
2. We're holding positions longer (average 87 minutes vs mixed durations)
3. The sample size is smaller (4 vs 31), so variance is higher

### Total Pips
- **Before:** -20.0 pips
- **After:** -20.0 pips

Interestingly, the total pips remained the same! This suggests:
1. The overlapping trades were mostly break-even or small losses
2. The main losses came from the longer-duration trades
3. The strategy needs further optimization for better performance

---

## Conclusion

The "one trade at a time" fix successfully:
- ✅ Eliminates unrealistic overlapping positions
- ✅ Provides accurate backtest results
- ✅ Matches manual trading behavior
- ✅ Properly tracks position lifecycle

The strategy now generates realistic signals and maintains proper position management. The next step is to optimize the strategy parameters (stop loss, take profit, indicator settings) to improve the win rate and profitability.

---

## Technical Implementation

**File Modified:** `shared/backtest_engine.py`  
**Method:** `_run_signal_driven_simulation`  
**Key Changes:**
1. Added `active_trades` list to track open positions
2. Check trade closure before each candle
3. Populate `context.current_position` with first active trade
4. Skip signal generation when position exists
5. Add completed trades to active list

**Test File:** `copilot-tests/test_one_trade_at_a_time.py`  
**Documentation:** `docs/ONE_TRADE_AT_A_TIME_FIX.md`

---

**Date:** December 12, 2025  
**Fix Verified:** ✅ Working correctly
