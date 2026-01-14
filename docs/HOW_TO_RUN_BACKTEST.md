# How to Run a Single Backtest

## 📋 Overview

This guide explains how to run a single backtest using the Universal Backtest Engine MCP tool. A single backtest tests one strategy on one symbol with one set of parameters over a specific date range.

---

## 🚀 Quick Start

### CRITICAL: How to Call the MCP Tool

**DO NOT wrap parameters in a `params` object!** Call the tool with parameters directly as separate `<parameter>` tags:

**CORRECT ✅:**
```xml
<invoke name="mcp_universal_backtest_engine_run_strategy_backtest">
  <parameter name="strategy_name">Stochastic Quad Rotation</parameter>
  <parameter name="symbol">NAS100_SB</parameter>
  <parameter name="timeframe">1m</parameter>
  <parameter name="start_date">2025-12-01</parameter>
  <parameter name="end_date">2025-12-31</parameter>
  <parameter name="stop_loss_pips">15</parameter>
  <parameter name="take_profit_pips">15</parameter>
</invoke>
```

**WRONG ❌:**
```xml
<invoke name="mcp_universal_backtest_engine_run_strategy_backtest">
  <parameter name="params">{"strategy_name": "...", "symbol": "..."}</parameter>
</invoke>
```

### Basic Example
```xml
<invoke name="mcp_universal_backtest_engine_run_strategy_backtest">
  <parameter name="strategy_name">Stochastic Quad Rotation</parameter>
  <parameter name="symbol">US500_SB</parameter>
  <parameter name="timeframe">1m</parameter>
  <parameter name="start_date">2026-01-09</parameter>
  <parameter name="end_date">2026-01-09</parameter>
  <parameter name="stop_loss_pips">8</parameter>
  <parameter name="take_profit_pips">8</parameter>
  <parameter name="auto_chart">true</parameter>
</invoke>
```

---

## 🎯 Trailing Stops

### What Are Trailing Stops?

Trailing stops allow trades to capture more profit by:
1. **Activating** once the trade reaches a profit threshold (e.g., 4 pips)
2. **Trailing** the stop loss behind price by a fixed distance (e.g., 2 pips)
3. **Locking in profits** as price moves favorably
4. **No fixed take profit** - trades can run indefinitely

### How Trailing Stops Work in This System

**The Stochastic Quad Rotation strategy has trailing stops BUILT-IN** via its JSON configuration:

```json
"trailing_stop": {
  "enabled": true,
  "activation_pips": 4,
  "trail_distance_pips": 2
}
```

**You don't need to do anything special** - just run the backtest normally and trailing stops will be used automatically!

### Example: Trade with Trailing Stop

**BUY Entry:** 25650.00
- **Fixed SL:** 25642.00 (8 pips below)
- **Fixed TP:** Disabled (set to infinity)
- **Trailing Stop:** Activates at +4 pips profit

**Price Movement:**
1. Price reaches 25654.00 (+4 pips) → **Trailing stop ACTIVATES**
2. Trailing SL set to: 25654.00 - 2 pips = **25652.00**
3. Price reaches 25660.00 (+10 pips)
4. Trailing SL moves to: 25660.00 - 2 pips = **25658.00**
5. Price reaches 25665.00 (+15 pips)
6. Trailing SL moves to: 25665.00 - 2 pips = **25663.00**
7. Price pulls back to 25663.00
8. **Trade exits at 25663.00 for +13 pips profit**

**Without trailing stops:** Trade would exit at 25658.00 (fixed TP) for +8 pips
**With trailing stops:** Trade captured +13 pips (62% more profit!)

### Running Backtest WITH Trailing Stops (Default)

**No special parameters needed** - trailing stops are enabled by default in the strategy:

```xml
<invoke name="mcp_universal_backtest_engine_run_strategy_backtest">
  <parameter name="strategy_name">Stochastic Quad Rotation</parameter>
  <parameter name="symbol">US500_SB</parameter>
  <parameter name="timeframe">1m</parameter>
  <parameter name="start_date">2026-01-09</parameter>
  <parameter name="end_date">2026-01-09</parameter>
  <parameter name="stop_loss_pips">8</parameter>
  <parameter name="take_profit_pips">8</parameter>
</invoke>
```

The `take_profit_pips` parameter is still required but will be ignored (set to infinity internally) when trailing stops are enabled.

### Checking if Trailing Stops Are Working

After running a backtest, check the results:

1. **Look for trades with profits > fixed TP:**
   - If fixed TP is 8 pips, but you see trades with +10, +12, +15 pips → Trailing stops are working!

2. **Check the JSON output:**
   - Open the saved JSON file
   - Look for `"trailing_stop_level"` in trade objects
   - If present and not null, trailing stops were activated

3. **Review the chart:**
   - Trades should show exit points beyond the fixed TP level
   - Some trades will exit at varying profit levels (not all at exactly 8 pips)

---

## 📊 Parameters

### Required Parameters

#### strategy_name (string)
**Description:** Name of the strategy to backtest  
**Available Strategies:**
- `"Stochastic Quad Rotation"` - Multi-period stochastic reversal strategy (HAS TRAILING STOPS)
- `"MACD Crossover Strategy"` - MACD-based trend following
- `"MA Crossover Strategy"` - Moving average crossover

**Example:**
```xml
<parameter name="strategy_name">Stochastic Quad Rotation</parameter>
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

**Commodities:**
- `"XAGUSD_SB"` - Silver/US Dollar
- `"XAUUSD_SB"` - Gold/US Dollar

**Example:**
```xml
<parameter name="symbol">NAS100_SB</parameter>
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
```xml
<parameter name="timeframe">1m</parameter>
```

---

#### start_date (string)
**Description:** Start date for the backtest  
**Format:** `"YYYY-MM-DD"`

**Examples:**
```xml
<parameter name="start_date">2025-12-01</parameter>
<parameter name="start_date">2026-01-09</parameter>
```

---

#### end_date (string)
**Description:** End date for the backtest  
**Format:** `"YYYY-MM-DD"`

**Examples:**
```xml
<parameter name="end_date">2025-12-31</parameter>
<parameter name="end_date">2026-01-09</parameter>
```

---

### Optional Parameters

#### stop_loss_pips (number)
**Description:** Stop loss in pips  
**Default:** Strategy default (8 for Stochastic Quad Rotation)  
**Range:** 1-100 pips

**Examples:**
```xml
<parameter name="stop_loss_pips">15</parameter>
<parameter name="stop_loss_pips">10</parameter>
<parameter name="stop_loss_pips">20</parameter>
```

---

#### take_profit_pips (number)
**Description:** Take profit in pips  
**Default:** Strategy default (8 for Stochastic Quad Rotation)  
**Range:** 1-200 pips

**Note:** When trailing stops are enabled (like in Stochastic Quad Rotation), this parameter is ignored and TP is set to infinity.

**Examples:**
```xml
<parameter name="take_profit_pips">15</parameter>
<parameter name="take_profit_pips">20</parameter>
<parameter name="take_profit_pips">10</parameter>
```

---

#### auto_chart (boolean)
**Description:** Automatically generate interactive chart after backtest  
**Default:** `true`  
**Options:** `true` or `false`

**Examples:**
```xml
<parameter name="auto_chart">true</parameter>
<parameter name="auto_chart">false</parameter>
```

---

#### initial_balance (number)
**Description:** Starting account balance  
**Default:** 10000  
**Range:** 100+

**Examples:**
```xml
<parameter name="initial_balance">10000</parameter>
<parameter name="initial_balance">5000</parameter>
```

---

#### risk_per_trade (number)
**Description:** Risk percentage per trade  
**Default:** 0.02 (2%)  
**Range:** 0.001-0.1 (0.1% to 10%)

**Examples:**
```xml
<parameter name="risk_per_trade">0.02</parameter>
<parameter name="risk_per_trade">0.01</parameter>
<parameter name="risk_per_trade">0.05</parameter>
```

---

## 📝 Complete Examples

### Example 1: Single Day Backtest (With Trailing Stops)
Test Friday January 9th, 2026 on US500:

```xml
<invoke name="mcp_universal_backtest_engine_run_strategy_backtest">
  <parameter name="strategy_name">Stochastic Quad Rotation</parameter>
  <parameter name="symbol">US500_SB</parameter>
  <parameter name="timeframe">1m</parameter>
  <parameter name="start_date">2026-01-09</parameter>
  <parameter name="end_date">2026-01-09</parameter>
  <parameter name="stop_loss_pips">8</parameter>
  <parameter name="take_profit_pips">8</parameter>
  <parameter name="auto_chart">true</parameter>
</invoke>
```

---

### Example 2: Silver Backtest (With Trailing Stops)
Test Silver on January 9th, 2026:

```xml
<invoke name="mcp_universal_backtest_engine_run_strategy_backtest">
  <parameter name="strategy_name">Stochastic Quad Rotation</parameter>
  <parameter name="symbol">XAGUSD_SB</parameter>
  <parameter name="timeframe">1m</parameter>
  <parameter name="start_date">2026-01-09</parameter>
  <parameter name="end_date">2026-01-09</parameter>
  <parameter name="stop_loss_pips">8</parameter>
  <parameter name="take_profit_pips">8</parameter>
  <parameter name="auto_chart">true</parameter>
</invoke>
```

---

### Example 3: One Week Backtest
Test a full week on NAS100:

```xml
<invoke name="mcp_universal_backtest_engine_run_strategy_backtest">
  <parameter name="strategy_name">Stochastic Quad Rotation</parameter>
  <parameter name="symbol">NAS100_SB</parameter>
  <parameter name="timeframe">1m</parameter>
  <parameter name="start_date">2025-12-09</parameter>
  <parameter name="end_date">2025-12-13</parameter>
  <parameter name="stop_loss_pips">8</parameter>
  <parameter name="take_profit_pips">8</parameter>
  <parameter name="auto_chart">true</parameter>
</invoke>
```

---

### Example 4: One Month Backtest (No Chart for Speed)
Test a full month on US500:

```xml
<invoke name="mcp_universal_backtest_engine_run_strategy_backtest">
  <parameter name="strategy_name">Stochastic Quad Rotation</parameter>
  <parameter name="symbol">US500_SB</parameter>
  <parameter name="timeframe">1m</parameter>
  <parameter name="start_date">2025-11-12</parameter>
  <parameter name="end_date">2025-12-11</parameter>
  <parameter name="stop_loss_pips">8</parameter>
  <parameter name="take_profit_pips">8</parameter>
  <parameter name="auto_chart">false</parameter>
</invoke>
```

---

## 📊 Understanding Results

### Console Output
After running a backtest, you'll see:

```
✅ BACKTEST COMPLETE: Stochastic Quad Rotation

Strategy Executed: Stochastic Quad Rotation (v1.0.0)
Symbol: US500_SB
Timeframe: 1m
Period: 2026-01-09 to 2026-01-09
Candles Analyzed: 1307
Signals Generated: 6

💰 Performance
• Total Return: +16.0 pips
• Initial Balance: $10,000.00
• Risk per Trade: 2.0%

📋 Trade Summary
• Total Trades: 6
• Winning Trades: 4 (66.7%)
• Losing Trades: 2
• Average Win: +8.0 pips
• Average Loss: +8.0 pips
• Profit Factor: 2.00
• Max Drawdown: 16.0 pips

🔍 Recent Trades
• ✅ BUY @ 6918.30 → 6926.30 (+8.0 pips)
• ✅ SELL @ 6956.10 → 6948.10 (+8.0 pips)
• ❌ SELL @ 6954.30 → 6962.30 (-8.0 pips)

⏱️ Execution Time: 7.04 seconds

📁 Results Saved:
File: /path/to/backtest_US500_SB_20260110_172625.json

🎨 Chart Created:
File: /path/to/US500_SB_STOCHASTIC_QUAD_ROTATION_20260110_172625.html
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
- Stochastic indicators (4 oscillators)

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
- Trailing stop levels (if activated)

---

## ⚠️ Common Issues

### Issue: No Signals Generated
**Cause:** Strategy conditions not met or trading hours restriction  
**Solution:**
- Check if date range includes trading days
- Verify symbol is active during test period
- Review strategy trading hours (14:30-21:00 EST for US indices)

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
```xml
<parameter name="start_date">2026-01-09</parameter>
<parameter name="end_date">2026-01-09</parameter>
```

### 2. Test Multiple Periods
Test different market conditions:
- Trending days
- Range-bound days
- High volatility days
- Low volatility days

### 3. Compare Symbols
Test the same strategy on different symbols to find the best fit.

### 4. Verify Trailing Stops
Check that some trades exit with profits > fixed TP to confirm trailing stops are working.

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
3. **Verify Trailing Stops** - Confirm trades captured extra profits
4. **Run Bulk Backtest** - Test multiple parameters (see HOW_TO_RUN_BULK_BACKTEST.md)
5. **Optimize Strategy** - Adjust parameters based on results
6. **Forward Test** - Test on recent unseen data

---

## 📚 Related Documentation

- **TRAILING_STOP_FIX.md** - Technical details on trailing stop implementation
- **HOW_TO_RUN_BULK_BACKTEST.md** - Test multiple parameters at once
- **STOCHASTIC_QUAD_ROTATION_COMPLETE_GUIDE.md** - Strategy details
- **MULTI_SYMBOL_COMPARISON.md** - Symbol performance comparison

---

**Last Updated:** January 10, 2026  
**Version:** 2.0 (Added trailing stop documentation)
