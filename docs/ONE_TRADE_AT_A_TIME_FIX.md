# One Trade at a Time Fix

## Problem
The Stochastic Quad Rotation strategy was generating 31 trades on Dec 11, 2025, with 30 out of 31 trades overlapping. Analysis showed trades running concurrently for over 2 hours.

The strategy had a check in place:
```python
if context.current_position is not None:
    return None
```

However, this check was ineffective because `context.current_position` was always `None` during signal generation.

## Root Cause
The backtest engine's `_run_signal_driven_simulation` method was not tracking active trades across strategy candles. The signal-driven approach processes each strategy candle independently:

1. Generate signal on strategy timeframe
2. Fetch execution window (1m data)
3. Execute trade within window
4. Complete trade immediately

This meant multiple signals could be generated even though trades from previous signals were still "active" in real time.

## Solution
Modified `shared/backtest_engine.py` in the `_run_signal_driven_simulation` method:

### Changes Made:

1. **Added Active Trade Tracking**:
   ```python
   active_trades = []  # Track all trades that haven't closed yet
   ```

2. **Check Trade Closure Before Each Candle**:
   ```python
   # Check if any active trades should be closed by this candle's timestamp
   still_active = []
   for trade in active_trades:
       if trade.exit_time and trade.exit_time <= candle.timestamp:
           # Trade has closed before or at this candle
           logger.debug(f"Trade closed: {trade.direction.name} @ {trade.exit_time}")
       else:
           # Trade is still active
           still_active.append(trade)
   active_trades = still_active
   ```

3. **Populate context.current_position**:
   ```python
   # Determine current position (first active trade, or None)
   current_position = active_trades[0] if active_trades else None
   
   # Create strategy context with current position
   context = StrategyContext(
       current_candle=candle,
       historical_candles=historical_candles.copy(),
       indicators=current_indicators,
       current_position=current_position,  # Now properly populated!
       symbol=config.symbol,
       timeframe=config.timeframe
   )
   ```

4. **Track New Trades**:
   ```python
   if trade_result:
       trades.append(trade_result)
       active_trades.append(trade_result)  # Add to active trades
   ```

5. **Added Debug Logging**:
   ```python
   logger.debug(f"Skipping signal generation @ {candle.timestamp} - active position exists")
   ```

## Results

### Before Fix:
- **31 trades** generated on Dec 11, 2025
- **30 out of 31 trades overlapping**
- Some trades ran concurrently for over 2 hours
- Win rate: ~32%

### After Fix:
- **4 trades** generated on Dec 11, 2025
- **0 overlapping trades** - all sequential
- Each trade completes before the next one starts
- Win rate: 25% (1 win, 3 losses)

## Verification

Test output shows the fix working correctly:

```
Skipping signal generation @ 2025-12-11 14:32:00 - active position exists (entry: 2025-12-11 14:31:00, direction: BUY)
Skipping signal generation @ 2025-12-11 14:33:00 - active position exists (entry: 2025-12-11 14:31:00, direction: BUY)
...
Trade closed: BUY @ 2025-12-11 14:53:00 (before current candle @ 2025-12-11 14:53:00)
Signal generated: BUY @ 2025-12-11 14:58:00
```

## Trade Timeline (Dec 11, 2025)

1. **Trade #1**: BUY @ 14:31 → 14:53 = -15.0 pips (LOSS)
2. **Trade #2**: BUY @ 14:58 → 15:12 = +25.0 pips (WIN)
3. **Trade #3**: SELL @ 15:25 → 17:42 = -15.0 pips (LOSS)
4. **Trade #4**: SELL @ 18:10 → 21:06 = -15.0 pips (LOSS)

All trades are sequential with no overlaps.

## Impact

This fix ensures realistic backtesting that matches manual trading behavior where only one position is held at a time. The strategy now:

- Generates signals only when no active position exists
- Properly tracks trade lifecycle across strategy candles
- Prevents unrealistic concurrent positions
- Provides accurate performance metrics

## Files Modified

- `shared/backtest_engine.py` - Modified `_run_signal_driven_simulation` method
- `copilot-tests/test_one_trade_at_a_time.py` - Test to verify the fix

## Date
December 12, 2025
