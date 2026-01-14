# Trailing Stop Bug Fix - January 10, 2026

## Problem Summary

Trailing stops were not working in the MCP backtest engine. All winning trades were exiting at exactly the fixed take profit (8 pips) instead of trailing beyond that point when the market moved favorably.

**Evidence:**
- Strategy JSON configured with: `activation_pips: 4`, `trail_distance_pips: 2`
- Expected: Trades should capture profits beyond 8 pips (e.g., 10, 12, 15 pips)
- Actual: All 28 winning trades on Silver (XAGUSD_SB) 2026-01-09 exited at exactly +8.0 pips
- Backtest JSON showed: `"trailing_stop": null`

## Root Cause

The `DSLStrategyWrapper` class in `shared/strategies/dsl_interpreter/dsl_loader.py` was NOT exposing the `trailing_stop` attribute from the underlying `DSLStrategy` instance.

**Code Flow:**
1. DSL strategy JSON contains trailing_stop configuration in `risk_management` section ✅
2. `DSLStrategy.__init__()` extracts it: `self.trailing_stop = risk_mgmt.get("trailing_stop", None)` ✅
3. `DSLStrategyWrapper` wraps the DSL strategy but doesn't expose `trailing_stop` ❌
4. MCP server tries to get it: `trailing_stop_config = getattr(strategy, 'trailing_stop', None)` ❌
5. Returns `None` because wrapper doesn't have the attribute ❌
6. BacktestConfiguration gets `trailing_stop=None` ❌
7. Backtest engine uses fixed TP instead of trailing stop ❌

## The Fix

Added a `@property` decorator to `DSLStrategyWrapper` class to expose the `trailing_stop` attribute from the underlying DSL strategy:

```python
@property
def trailing_stop(self) -> Optional[Dict[str, Any]]:
    """Expose the underlying DSL strategy's trailing stop configuration."""
    return getattr(self._dsl_strategy, 'trailing_stop', None)
```

**File Modified:** `shared/strategies/dsl_interpreter/dsl_loader.py` (line ~377)

## Verification

Tested the fix with Python script:
```python
from shared.strategies.dsl_interpreter.dsl_loader import DSLLoader
from shared.strategy_registry import StrategyRegistry
from shared.strategies.dsl_interpreter.dsl_loader import integrate_dsl_with_strategy_registry

loader = DSLLoader()
registry = StrategyRegistry()
integrate_dsl_with_strategy_registry(registry, loader)

strategy = registry.create_strategy('Stochastic Quad Rotation', {})

print(f'Has trailing_stop attr: {hasattr(strategy, "trailing_stop")}')
print(f'trailing_stop value: {strategy.trailing_stop}')
```

**Result:**
```
Has trailing_stop attr: True
trailing_stop value: {'enabled': True, 'activation_pips': 4, 'trail_distance_pips': 2}
```

✅ The property is now correctly exposing the trailing stop configuration!

## Next Steps

1. **Restart MCP Server** - The server needs to be restarted to pick up the code changes
2. **Run Test Backtest** - Test with Silver (XAGUSD_SB) on 2026-01-09 with 1m timeframe
3. **Verify Results:**
   - Check backtest JSON shows `"trailing_stop": {"enabled": true, "activation_pips": 4, "trail_distance_pips": 2}`
   - Check that some winning trades exceed 8 pips (e.g., 10, 12, 15 pips)
   - Check that trades have `trailing_stop_level` values in the JSON
   - Check logs show "TRAILING STOP DEBUG" messages with `trailing_enabled=True`

## Additional Debug Logging Added

Added debug logging to MCP server handler (`mcp_servers/universal_backtest_engine.py` line ~550):
```python
logger.info(f"🔍 TRAILING STOP DEBUG:")
logger.info(f"   Strategy type: {type(strategy).__name__}")
logger.info(f"   Has trailing_stop attr: {hasattr(strategy, 'trailing_stop')}")
logger.info(f"   trailing_stop_config: {trailing_stop_config}")
```

This will help verify the fix is working after server restart.

## Files Modified

1. `shared/strategies/dsl_interpreter/dsl_loader.py` - Added `trailing_stop` property to DSLStrategyWrapper
2. `mcp_servers/universal_backtest_engine.py` - Added debug logging (can be removed after verification)

## Expected Behavior After Fix

With trailing stops enabled (activation: 4 pips, trail: 2 pips):
- Trade enters at price X
- When profit reaches +4 pips, trailing stop activates
- Trailing stop follows price at 2 pips behind the high/low
- If price moves to +10 pips, trailing stop is at +8 pips
- If price moves to +15 pips, trailing stop is at +13 pips
- Trade exits when price retraces and hits the trailing stop
- Result: Trades can capture profits well beyond the fixed 8 pip TP

## Status

✅ **BUG FIXED** - Code changes complete
⏳ **PENDING** - MCP server restart required
⏳ **PENDING** - Verification test needed
