# Backtest Diagnostics Tool

## Overview

The diagnostic tool exports detailed CSV files during backtests, containing OHLCV data, all indicator values, trend filter data, and trade markers. This is useful for:

- Debugging strategy logic
- Analyzing indicator behavior
- Verifying trade execution
- Comparing backtest results with live trading
- Creating custom analysis in Excel/Python

## How to Enable

Set the environment variable before running backtests:

### macOS/Linux
```bash
export BACKTEST_DIAGNOSTICS=true
```

### Windows (PowerShell)
```powershell
$env:BACKTEST_DIAGNOSTICS="true"
```

### Windows (CMD)
```cmd
set BACKTEST_DIAGNOSTICS=true
```

## Running with Diagnostics

Once enabled, run any backtest as normal:

```bash
# The diagnostic CSV will be automatically created
export BACKTEST_DIAGNOSTICS=true

# Run your backtest via MCP or directly
# Diagnostic CSV will be saved to: optimization_results/diagnostics/
```

## Output Format

The diagnostic CSV includes:

### Basic Columns
- `timestamp` - ISO format timestamp
- `date` - Date in YYYY-MM-DD format
- `time` - Time in HH:MM:SS format
- `open`, `high`, `low`, `close` - OHLCV price data
- `volume` - Trading volume

### Indicator Columns
For Stochastic Quad Rotation strategy:
- `fast_k`, `fast_d` - Fast stochastic (9-period)
- `med_fast_k`, `med_fast_d` - Medium-fast stochastic (14-period)
- `med_slow_k`, `med_slow_d` - Medium-slow stochastic (40-period)
- `slow_k`, `slow_d` - Slow stochastic (60-period)

### Filter Columns
- `trend_filter_pips` - Trend strength filter value (when available)

### Trade Marker Columns
- `trade_entry` - "ENTRY" when a trade is opened
- `trade_direction` - "BUY" or "SELL"
- `entry_price` - Entry price
- `trade_exit` - "EXIT" when a trade is closed
- `exit_price` - Exit price
- `exit_reason` - "Take Profit", "Stop Loss", etc.
- `pips` - Profit/loss in pips (e.g., +8.0, -8.0)

## Example Usage

### Enable and Run Backtest
```bash
export BACKTEST_DIAGNOSTICS=true

# Via Claude/MCP
# "Run backtest for NAS100 1m yesterday with 8 pip SL/TP"
```

### Output Location
```
optimization_results/diagnostics/
  ├── diagnostic_NAS100_Stochastic_Quad_Rotation_20260101_135353.csv
  ├── diagnostic_NAS100_Stochastic_Quad_Rotation_20260101_140810.csv
  └── ...
```

### Analyzing in Python
```python
import pandas as pd

# Load diagnostic CSV
df = pd.read_csv('optimization_results/diagnostics/diagnostic_NAS100_Stochastic_Quad_Rotation_20260101_135353.csv')

# View trades only
trades = df[df['trade_entry'] == 'ENTRY']
print(trades[['timestamp', 'trade_direction', 'entry_price', 'pips']])

# Analyze stochastic values at entry points
print(trades[['fast_k', 'med_fast_k', 'med_slow_k', 'slow_k']])

# Check trend filter at trade times
print(trades[['timestamp', 'trend_filter_pips']])
```

### Analyzing in Excel
1. Open the CSV file in Excel
2. Use filters to show only rows with "ENTRY" or "EXIT"
3. Create pivot tables to analyze indicators by trade outcome
4. Plot indicator values alongside price action

## Verification

The diagnostic CSV should match:
- **Trade count** - Same number of entries as in JSON results
- **Trade times** - Exact timestamps match HTML table
- **Trade outcomes** - Same pips and win/loss as JSON
- **Indicator values** - Should align with chart visualizations

## Disabling Diagnostics

To disable and avoid creating CSV files:

```bash
unset BACKTEST_DIAGNOSTICS
# or
export BACKTEST_DIAGNOSTICS=false
```

## Performance Impact

- **Minimal** - CSV export happens after backtest completes
- **No slowdown** - Does not affect backtest calculation speed
- **File size** - ~100KB per 1000 candles with all indicators

## Troubleshooting

### CSV not being created
- Check environment variable: `echo $BACKTEST_DIAGNOSTICS`
- Ensure it's set to `true`, `1`, or `yes`
- Check logs for diagnostic export messages

### Missing indicator columns
- Verify strategy uses indicators
- Check that `get_indicator_series()` is implemented
- Review logs for indicator extraction warnings

### Trade markers don't match JSON
- Verify timestamps are exact (no rounding)
- Check timezone consistency
- Compare entry/exit times between CSV and JSON

## Advanced Usage

### Custom Analysis Scripts
```python
# Calculate win rate by time of day
df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
entries = df[df['trade_entry'] == 'ENTRY']
win_rate_by_hour = entries.groupby('hour')['pips'].apply(lambda x: (x > 0).sum() / len(x))
print(win_rate_by_hour)

# Find optimal stochastic thresholds
winning_trades = entries[entries['pips'] > 0]
losing_trades = entries[entries['pips'] < 0]
print("Winning trade stochastic averages:")
print(winning_trades[['fast_k', 'med_fast_k', 'med_slow_k', 'slow_k']].mean())
print("\nLosing trade stochastic averages:")
print(losing_trades[['fast_k', 'med_fast_k', 'med_slow_k', 'slow_k']].mean())
```

## Related Files

- Implementation: `shared/diagnostics.py`
- Integration: `shared/backtest_engine.py`
- Strategy docs: `docs/STOCHASTIC_QUAD_ROTATION_STRATEGY.md`
