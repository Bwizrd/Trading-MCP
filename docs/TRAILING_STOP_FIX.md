# Trailing Stop Fix

## Issue Summary

The trailing stop functionality was not working properly in the MCP backtest engine because the `trailing_stop` configuration from the strategy JSON was not being passed to the `BacktestConfiguration` object.

## Root Cause

The Stochastic Quad Rotation strategy JSON correctly defines trailing stop configuration:

```json
"risk_management": {
  "stop_loss_pips": 8,
  "take_profit_pips": 8,
  "trailing_stop": {
    "enabled": true,
    "activation_pips": 4,
    "trail_distance_pips": 2
  }
}
```

The DSL strategy loader correctly reads this into `self.trailing_stop`, but the MCP server handlers were NOT passing this configuration to the `BacktestConfiguration` object when creating it.

## The Fix

Updated three handlers in `mcp_servers/universal_backtest_engine.py`:

### 1. `handle_run_backtest` (line ~550)
**Before:**
```python
strategy = registry.create_strategy(strategy_name, strategy_parameters)

config = BacktestConfiguration(
    symbol=symbol,
    timeframe=timeframe,
    start_date=start_date,
    end_date=end_date,
    initial_balance=initial_balance,
    risk_per_trade=risk_per_trade,
    stop_loss_pips=stop_loss_pips,
    take_profit_pips=take_profit_pips,
    use_tick_data=use_tick_data
)
```

**After:**
```python
strategy = registry.create_strategy(strategy_name, strategy_parameters)

# Get trailing stop configuration from strategy if available
trailing_stop_config = getattr(strategy, 'trailing_stop', None)

config = BacktestConfiguration(
    symbol=symbol,
    timeframe=timeframe,
    start_date=start_date,
    end_date=end_date,
    initial_balance=initial_balance,
    risk_per_trade=risk_per_trade,
    stop_loss_pips=stop_loss_pips,
    take_profit_pips=take_profit_pips,
    use_tick_data=use_tick_data,
    trailing_stop=trailing_stop_config
)
```

### 2. `handle_compare_strategies` (line ~693)
**Before:**
```python
strategy = registry.create_strategy(strategy_name)
config = BacktestConfiguration(
    symbol=symbol,
    timeframe=timeframe,
    start_date=start_date,
    end_date=end_date,
    initial_balance=initial_balance,
    stop_loss_pips=stop_loss_pips,
    take_profit_pips=take_profit_pips
)
```

**After:**
```python
strategy = registry.create_strategy(strategy_name)

# Get trailing stop configuration from strategy if available
trailing_stop_config = getattr(strategy, 'trailing_stop', None)

config = BacktestConfiguration(
    symbol=symbol,
    timeframe=timeframe,
    start_date=start_date,
    end_date=end_date,
    initial_balance=initial_balance,
    stop_loss_pips=stop_loss_pips,
    take_profit_pips=take_profit_pips,
    trailing_stop=trailing_stop_config
)
```

### 3. `handle_bulk_backtest` (line ~1009)
**Before:**
```python
config = BacktestConfiguration(
    symbol=symbol,
    timeframe=timeframe,
    start_date=start_date,
    end_date=end_date,
    initial_balance=10000,
    risk_per_trade=0.02,
    stop_loss_pips=stop_loss,
    take_profit_pips=take_profit
)

strategy = registry.create_strategy(strategy_name)
```

**After:**
```python
# Get strategy first to access trailing stop config
strategy = registry.create_strategy(strategy_name)

# Get trailing stop configuration from strategy if available
trailing_stop_config = getattr(strategy, 'trailing_stop', None)

config = BacktestConfiguration(
    symbol=symbol,
    timeframe=timeframe,
    start_date=start_date,
    end_date=end_date,
    initial_balance=10000,
    risk_per_trade=0.02,
    stop_loss_pips=stop_loss,
    take_profit_pips=take_profit,
    trailing_stop=trailing_stop_config
)
```

## How Trailing Stops Work

Once the `trailing_stop` configuration is properly passed to `BacktestConfiguration`:

1. **Trade Creation**: When a trade is opened, if trailing stops are enabled, the take profit is set to `float('inf')` so it never hits (lines 543, 681, 961 in `shared/backtest_engine.py`)

2. **Activation**: The trailing stop activates once the trade reaches the `activation_pips` threshold (e.g., 4 pips in profit)

3. **Trailing**: Once activated, the stop loss trails the price by `trail_distance_pips` (e.g., 2 pips)
   - For BUY trades: Stop trails below the high
   - For SELL trades: Stop trails above the low

4. **Exit**: The trade closes when:
   - The trailing stop is hit (profit locked in)
   - The original stop loss is hit (before activation)
   - End of day

## Configuration Parameters

```json
"trailing_stop": {
  "enabled": true,              // Enable/disable trailing stops
  "activation_pips": 4,          // Pips in profit before trailing starts
  "trail_distance_pips": 2       // Distance to trail behind price
}
```

### Example Scenario (BUY trade):
- Entry: 25650.00
- Fixed SL: 25642.00 (8 pips)
- Fixed TP: 25658.00 (8 pips) → Set to infinity with trailing stops

**Price Movement:**
1. Price reaches 25654.00 (+4 pips) → Trailing stop ACTIVATES
2. Trailing SL set to: 25654.00 - 2 pips = 25652.00
3. Price reaches 25660.00 (+10 pips)
4. Trailing SL moves to: 25660.00 - 2 pips = 25658.00
5. Price pulls back to 25658.00
6. Trade exits at 25658.00 for +8 pips profit

**Without trailing stops**, the trade would have exited at 25658.00 (fixed TP) for +8 pips.
**With trailing stops**, the trade captured +8 pips but could have captured more if price continued higher.

## Benefits

- **Profit Protection**: Locks in profits as price moves favorably
- **Unlimited Upside**: No fixed take profit, allowing trades to run
- **Configurable**: Activation and trail distance can be tuned per strategy
- **Risk Management**: Original stop loss protects against immediate losses

## Testing

To test trailing stops are working:

```python
mcp_universal_backtest_engine_run_strategy_backtest(
    strategy_name="Stochastic Quad Rotation",
    symbol="US500_SB",
    timeframe="1m",
    start_date="2026-01-09",
    end_date="2026-01-09",
    stop_loss_pips=8,
    take_profit_pips=8,
    auto_chart=true
)
```

Check the results:
- Trades should show `trailing_stop_level` values when activated
- Some trades should exit with profits > 8 pips (beyond fixed TP)
- Trade exit prices should reflect trailing stop hits, not fixed TP hits

## Files Modified

- `mcp_servers/universal_backtest_engine.py` - Added trailing_stop parameter passing in 3 handlers:
  - `handle_run_backtest` (line ~553)
  - `handle_compare_strategies` (line ~701)
  - `handle_bulk_backtest` (line ~1024)

- `mcp_servers/modular_chart_engine.py` - Added trailing_stop parameter passing in 4 locations:
  - `create_chart_from_backtest_json` - Reconstruct from saved JSON (line ~285)
  - `create_strategy_chart` - New backtest for chart (line ~465)
  - `create_performance_chart` - Performance analysis (line ~611)
  - `compare_strategies_chart` - Strategy comparison (line ~695)

## Files Already Correct

- `mcp_servers/universal_backtest_mcp.py` - Already has trailing_stop parameter passing (was fixed previously)
- `shared/backtest_engine.py` - Trailing stop logic already implemented correctly
- `shared/strategies/dsl_interpreter/dsl_strategy.py` - Already reads trailing_stop from JSON
- `shared/strategy_interface.py` - BacktestConfiguration already has trailing_stop field
- `shared/models/__init__.py` - Trade model already has trailing_stop_level field

## Date

January 10, 2026
