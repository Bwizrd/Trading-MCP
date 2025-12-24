# How to Run a Single Backtest

## 📋 Overview

This guide explains how to run a single backtest using the Universal Backtest Engine MCP tool. A single backtest tests one strategy on one symbol with one set of parameters over a specific date range.

---

## 🚀 Quick Start

### Basic Command
```
mcp_universal_backtest_engine_run_strategy_backtest(
    strategy_name="Stochastic Quad Rotation",
    symbol="NAS100_SB",
    timeframe="1m",
    start_date="2025-12-01",
    end_date="2025-12-31",
    stop_loss_pips=15,
    take_profit_pips=15
)
```

---

## 📊 Parameters

### Required Parameters

#### strategy_name (string)
**Description:** Name of the strategy to backtest  
**Available Strategies:**
- `"Stochastic Quad Rotation"` - Multi-period stochastic reversal strategy
- `"MACD Crossover Strategy"` - MACD-based trend following
- `"MA Crossover Strategy"` - Moving average crossover

**Example:**
```python
strategy_name="Stochastic Quad Rotation"
```

---

#### symbol (string)
**Description:** Trading symbol to backtest  
**Format:** `SYMBOL_SB` (SB = Spread Betting)

**Available Symbols:**

**US Indices:**
- `"US500_SB"` - S&P 500
- `"US30_SB"` - Dow Jones
- `"NAS100_SB"` - Nasdaq 100

**European Indices:**
- `"UK100_SB"` - FTSE 100
- `"GER40_SB"` - DAX 40

**Forex Pairs:**
- `"EURUSD_SB"` - Euro/US Dollar
- `"GBPJPY_SB"` - British Pound/Japanese Yen
- `"EURCAD_SB"` - Euro/Canadian Dollar
- `"AUDUSD_SB"` - Australian Dollar/US Dollar

**Example:**
```python
symbol="NAS100_SB"
```

---

#### timeframe (string)
**Description:** Candle timeframe for the backtest  
**Available Timeframes:**
- `"1m"` - 1 minute (recommended for Stochastic Quad Rotation)
- `"5m"` - 5 minutes
- `"15m"` - 15 minutes
- `"30m"` - 30 minutes
- `"1h"` - 1 hour
- `"4h"` - 4 hours
- `"1d"` - 1 day

**Example:**
```python
timeframe="1m"
```

---

#### start_date (string)
**Description:** Start date for the backtest  
**Format:** `"YYYY-MM-DD"`

**Examples:**
```python
start_date="2025-12-01"  # December 1st, 2025
start_date="2025-11-15"  # November 15th, 2025
```

---

#### end_date (string)
**Description:** End date for the backtest  
**Format:** `"YYYY-MM-DD"`

**Examples:**
```python
end_date="2025-12-31"  # December 31st, 2025
end_date="2025-12-19"  # December 19th, 2025
```

---

### Optional Parameters

#### stop_loss_pips (number)
**Description:** Stop loss in pips  
**Default:** Strategy default (15 for Stochastic Quad Rotation)  
**Range:** 1-100 pips

**Examples:**
```python
stop_loss_pips=15  # 15 pip stop loss
stop_loss_pips=10  # Tighter stop
stop_loss_pips=20  # Wider stop
```

---

#### take_profit_pips (number)
**Description:** Take profit in pips  
**Default:** Strategy default (15 for Stochastic Quad Rotation)  
**Range:** 1-200 pips

**Examples:**
```python
take_profit_pips=15  # 15 pip target
take_profit_pips=20  # Larger target
take_profit_pips=10  # Smaller target
```

---

#### auto_chart (boolean)
**Description:** Automatically generate interactive chart after backtest  
**Default:** `true`  
**Options:** `true` or `false`

**Examples:**
```python
auto_chart=true   # Generate chart (default)
auto_chart=false  # Skip chart generation (faster)
```

---

#### initial_balance (number)
**Description:** Starting account balance  
**Default:** 10000  
**Range:** 100+

**Examples:**
```python
initial_balance=10000  # $10,000 account
initial_balance=5000   # $5,000 account
```

---

#### risk_per_trade (number)
**Description:** Risk percentage per trade  
**Default:** 0.02 (2%)  
**Range:** 0.001-0.1 (0.1% to 10%)

**Examples:**
```python
risk_per_trade=0.02  # 2% risk per trade
risk_per_trade=0.01  # 1% risk (conservative)
risk_per_trade=0.05  # 5% risk (aggressive)
```

---

## 📝 Complete Examples

### Example 1: Single Day Backtest
Test Friday December 19th, 2025 on NAS100:

```python
mcp_universal_backtest_engine_run_strategy_backtest(
    strategy_name="Stochastic Quad Rotation",
    symbol="NAS100_SB",
    timeframe="1m",
    start_date="2025-12-19",
    end_date="2025-12-19",
    stop_loss_pips=15,
    take_profit_pips=15,
    auto_chart=true
)
```

---

### Example 2: One Week Backtest
Test a full week on US30:

```python
mcp_universal_backtest_engine_run_strategy_backtest(
    strategy_name="Stochastic Quad Rotation",
    symbol="US30_SB",
    timeframe="1m",
    start_date="2025-12-09",
    end_date="2025-12-13",
    stop_loss_pips=15,
    take_profit_pips=15,
    auto_chart=true
)
```

---

### Example 3: One Month Backtest
Test a full month on US500:

```python
mcp_universal_backtest_engine_run_strategy_backtest(
    strategy_name="Stochastic Quad Rotation",
    symbol="US500_SB",
    timeframe="1m",
    start_date="2025-11-12",
    end_date="2025-12-11",
    stop_loss_pips=15,
    take_profit_pips=15,
    auto_chart=false  # Skip chart for speed
)
```

---

### Example 4: Custom Risk Parameters
Test with tighter stops and smaller account:

```python
mcp_universal_backtest_engine_run_strategy_backtest(
    strategy_name="Stochastic Quad Rotation",
    symbol="NAS100_SB",
    timeframe="1m",
    start_date="2025-12-01",
    end_date="2025-12-31",
    stop_loss_pips=10,
    take_profit_pips=10,
    initial_balance=5000,
    risk_per_trade=0.01,
    auto_chart=true
)
```

---

## 📊 Understanding Results

### Console Output
After running a backtest, you'll see:

```
✅ BACKTEST COMPLETE: Stochastic Quad Rotation

Strategy Executed: Stochastic Quad Rotation (v1.0.0)
Symbol: NAS100_SB
Timeframe: 1m
Period: 2025-12-19 to 2025-12-19
Candles Analyzed: 1379
Signals Generated: 15

💰 Performance
• Total Return: +180.0 pips
• Initial Balance: $10,000.00
• Risk per Trade: 2.0%

📋 Trade Summary
• Total Trades: 15
• Winning Trades: 12 (80.0%)
• Losing Trades: 3
• Average Win: +15.0 pips
• Average Loss: -15.0 pips
• Profit Factor: 4.00
• Max Drawdown: 30.0 pips

🔍 Recent Trades
• ✅ BUY @ 25651.60 → 25666.60 (+15.0 pips)
• ✅ SELL @ 25693.20 → 25678.20 (+15.0 pips)
• ❌ SELL @ 25694.70 → 25709.70 (-15.0 pips)

⏱️ Execution Time: 18.45 seconds

📁 Results Saved:
File: /path/to/backtest_NAS100_SB_20251219_120000.json

🎨 Chart Created:
File: /path/to/NAS100_SB_STOCHASTIC_QUAD_ROTATION_20251219_120001.html
```

---

### Key Metrics Explained

**Total Return:** Total profit/loss in pips  
**Win Rate:** Percentage of winning trades  
**Profit Factor:** Gross profit / Gross loss (>1 = profitable)  
**Max Drawdown:** Largest consecutive loss in pips  
**Average Win/Loss:** Average pips per winning/losing trade

---

## 📈 Viewing Charts

### Opening the Chart
1. Copy the chart file path from the results
2. Open in your browser:
   - **Mac:** `open /path/to/chart.html`
   - **Windows:** Double-click the file
   - **Linux:** `xdg-open /path/to/chart.html`

### Chart Features
- Interactive candlestick chart
- Trade entry/exit markers
- Profit/loss visualization
- Cumulative P&L curve
- Zoom and pan controls

---

## 🔍 Analyzing Results

### JSON Output File
The backtest saves detailed results to a JSON file:

**Location:** `optimization_results/backtest_SYMBOL_TIMESTAMP.json`

**Contains:**
- Complete trade history
- All candle data
- Performance metrics
- Strategy configuration
- Execution details

### Using Results for Analysis
```python
import json

# Load backtest results
with open('optimization_results/backtest_NAS100_SB_20251219_120000.json', 'r') as f:
    results = json.load(f)

# Access trade data
trades = results['trades']
summary = results['summary']

print(f"Win Rate: {summary['win_rate'] * 100}%")
print(f"Total Pips: {summary['total_pips']}")
```

---

## ⚠️ Common Issues

### Issue: No Signals Generated
**Cause:** Strategy conditions not met or trading hours restriction  
**Solution:**
- Check if date range includes trading days
- Verify symbol is active during test period
- Review strategy trading hours (14:30-21:00 EST for Stochastic Quad Rotation)

### Issue: Slow Execution
**Cause:** Large date range with 1m timeframe  
**Solution:**
- Set `auto_chart=false` for faster execution
- Test shorter date ranges first
- Use larger timeframes (5m, 15m) for longer periods

### Issue: Chart Not Generated
**Cause:** `auto_chart=false` or chart generation error  
**Solution:**
- Set `auto_chart=true`
- Manually generate chart using modular chart engine
- Check JSON file was created successfully

---

## 💡 Best Practices

### 1. Start Small
Begin with single-day backtests to verify strategy behavior:
```python
start_date="2025-12-19"
end_date="2025-12-19"
```

### 2. Test Multiple Periods
Test different market conditions:
- Trending days
- Range-bound days
- High volatility days
- Low volatility days

### 3. Compare Symbols
Test the same strategy on different symbols to find the best fit.

### 4. Optimize Parameters
Test different SL/TP combinations to find optimal settings.

### 5. Validate Results
- Check if results make sense
- Review individual trades
- Analyze chart patterns
- Compare to expected behavior

---

## 🎯 Next Steps

After running a single backtest:

1. **Review Results** - Analyze performance metrics
2. **Check Chart** - Visualize trades and patterns
3. **Run Bulk Backtest** - Test multiple parameters (see HOW_TO_RUN_BULK_BACKTEST.md)
4. **Optimize Strategy** - Adjust parameters based on results
5. **Forward Test** - Test on recent unseen data

---

## 📚 Related Documentation

- **HOW_TO_RUN_BULK_BACKTEST.md** - Test multiple parameters at once
- **STOCHASTIC_QUAD_ROTATION_COMPLETE_GUIDE.md** - Strategy details
- **MULTI_SYMBOL_COMPARISON.md** - Symbol performance comparison

---

**Last Updated:** December 20, 2025  
**Version:** 1.0
