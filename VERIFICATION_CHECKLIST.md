# Stochastic Quad Rotation - Verification Checklist

## Pre-Backtest Verification ✅

- [x] Strategy loads from JSON configuration
- [x] Schema validation passes
- [x] Strategy appears in registry
- [x] Stochastic calculator works (0-100 bounds)
- [x] Multi-indicator manager registers 4 instances
- [x] Crossover detector tracks state
- [x] Condition evaluator handles rotation logic
- [x] Backward compatibility maintained (all existing strategies work)
- [x] Unit tests pass
- [x] Integration tests pass
- [x] MCP simulation test passes

## MCP Server Backtest Verification ⏳

**Status**: Waiting for MCP server restart

**Required Action**: Restart MCP servers to pick up latest code changes

**Once restarted, run**:
```
run_strategy_backtest(
    strategy_name="Stochastic Quad Rotation",
    symbol="EURUSD_SB",
    timeframe="1m",
    days_back=3,
    stop_loss_pips=15,
    take_profit_pips=25,
    auto_chart=true
)
```

**Expected Results**:
- [ ] Backtest completes without errors
- [ ] Trades are generated (may be 0 if conditions not met, which is valid)
- [ ] Chart displays 4 stochastic lines
- [ ] Chart shows reference lines at 20 and 80
- [ ] Trade signals match rotation logic (all below 20, fast crosses above)

## Post-Backtest Verification

Once backtest runs successfully:

- [ ] Review trade history to verify signal logic
- [ ] Check chart visualization shows all 4 stochastics
- [ ] Verify stochastic values stay in 0-100 range
- [ ] Confirm rotation conditions triggered correctly
- [ ] Test on different symbols (GBPUSD_SB, USDJPY_SB)
- [ ] Test on different timeframes (5m, 15m, 30m)

## Known Issues & Solutions

### Issue 1: "Required indicators not available"
**Cause**: MCP server using old code that checks for indicators
**Solution**: Restart MCP servers (DONE - code updated to return empty list for advanced strategies)

### Issue 2: No trades generated
**Cause**: Rotation conditions are strict (all 4 stochastics must be in zone)
**Solution**: This is expected behavior. Try longer time periods or different symbols.

### Issue 3: Strategy not in registry
**Cause**: MCP server hasn't picked up new JSON file
**Solution**: Restart MCP servers

## Code Changes Made

### Latest Fix (2025-12-09)
**File**: `shared/strategies/dsl_interpreter/dsl_strategy.py`
**Change**: Modified `requires_indicators()` to return empty list for advanced strategies
**Reason**: Advanced strategies calculate their own indicators with custom parameters

### Why This Fix Was Needed
- Advanced strategies use multiple instances of same indicator (e.g., 4 stochastics)
- Each instance has different parameters (9-1-3, 14-1-3, 40-1-4, 60-1-10)
- Indicator registry only has single "STOCH" with default parameters
- Strategy must calculate its own indicators internally
- Backtest engine checks `requires_indicators()` before running
- Returning empty list bypasses this check for advanced strategies

## Testing Commands

### 1. Verify Strategy Loads
```bash
python copilot-tests/test_stochastic_quad_rotation.py
```

### 2. Verify Backward Compatibility
```bash
python copilot-tests/test_backward_compatibility.py
```

### 3. Simulate MCP Backtest
```bash
python copilot-tests/test_mcp_backtest_simulation.py
```

### 4. Run Actual Backtest (after MCP restart)
Use MCP tool: `run_strategy_backtest`

## Success Criteria

The spec is complete when:
1. ✅ All unit tests pass
2. ✅ All integration tests pass
3. ✅ Backward compatibility verified
4. ✅ MCP simulation passes
5. ⏳ **MCP backtest runs without errors** (PENDING - needs server restart)
6. ⏳ **Chart displays correctly** (PENDING - needs server restart)

## Next Steps

1. **Restart MCP servers** (user action required)
2. **Run backtest** through MCP tool
3. **Verify results** match expected behavior
4. **Test on multiple symbols/timeframes**
5. **Close spec** once verified

## Notes

- The strategy may generate 0 trades on short time periods - this is normal
- Rotation conditions are strict by design (all 4 indicators must align)
- For testing, try 7-30 days of data to see more signals
- 1m timeframe generates more data points but may have fewer signals
- 15m or 30m timeframes may show clearer rotation patterns
