# How to Run a Bulk Backtest

## 📋 Overview

This guide explains how to run bulk backtests using the Universal Backtest Engine MCP tool. A bulk backtest tests one strategy across multiple symbols, timeframes, and SL/TP combinations simultaneously, generating a comprehensive HTML report for comparison.

**Use bulk backtests to:**
- Test multiple symbols at once
- Compare different timeframes
- Optimize SL/TP parameters
- Find the best strategy configuration

---

## 🚀 Quick Start

### Basic Command
```
mcp_universal_backtest_engine_bulk_backtest_strategy(
    strategy_name="Stochastic Quad Rotation",
    symbols=["NAS100_SB", "US30_SB", "US500_SB"],
    timeframes=["1m"],
    start_date="2025-12-01",
    end_date="2025-12-31",
    sl_tp_combinations=[
        {"stop_loss_pips": 15, "take_profit_pips": 15}
    ]
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

#### symbols (array of strings)
**Description:** List of trading symbols to test  
**Format:** Array of `"SYMBOL_SB"` strings

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

**Examples:**
```python
# Single symbol
symbols=["NAS100_SB"]

# Multiple US indices
symbols=["NAS100_SB", "US30_SB", "US500_SB"]

# All indices
symbols=["NAS100_SB", "US30_SB", "US500_SB", "UK100_SB", "GER40_SB"]

# Forex pairs
symbols=["EURUSD_SB", "GBPJPY_SB", "EURCAD_SB", "AUDUSD_SB"]
```

---

#### timeframes (array of strings)
**Description:** List of timeframes to test  
**Available Timeframes:**
- `"1m"` - 1 minute (recommended for Stochastic Quad Rotation)
- `"5m"` - 5 minutes
- `"15m"` - 15 minutes
- `"30m"` - 30 minutes
- `"1h"` - 1 hour
- `"4h"` - 4 hours
- `"1d"` - 1 day

**Examples:**
```python
# Single timeframe
timeframes=["1m"]

# Multiple timeframes
timeframes=["1m", "5m", "15m"]

# Intraday timeframes
timeframes=["15m", "30m", "1h"]
```

---

#### start_date (string)
**Description:** Start date for all backtests  
**Format:** `"YYYY-MM-DD"`

**Examples:**
```python
start_date="2025-12-01"  # December 1st, 2025
start_date="2025-11-12"  # November 12th, 2025
```

---

#### end_date (string)
**Description:** End date for all backtests  
**Format:** `"YYYY-MM-DD"`

**Examples:**
```python
end_date="2025-12-31"  # December 31st, 2025
end_date="2025-12-19"  # December 19th, 2025
```

---

#### sl_tp_combinations (array of objects)
**Description:** List of stop loss and take profit combinations to test  
**Format:** Array of objects with `stop_loss_pips` and `take_profit_pips`

**Examples:**
```python
# Single combination
sl_tp_combinations=[
    {"stop_loss_pips": 15, "take_profit_pips": 15}
]

# Multiple combinations
sl_tp_combinations=[
    {"stop_loss_pips": 10, "take_profit_pips": 10},
    {"stop_loss_pips": 15, "take_profit_pips": 15},
    {"stop_loss_pips": 20, "take_profit_pips": 20}
]

# Asymmetric risk/reward
sl_tp_combinations=[
    {"stop_loss_pips": 10, "take_profit_pips": 15},
    {"stop_loss_pips": 10, "take_profit_pips": 20},
    {"stop_loss_pips": 15, "take_profit_pips": 25}
]

# Wide range for optimization
sl_tp_combinations=[
    {"stop_loss_pips": 5, "take_profit_pips": 10},
    {"stop_loss_pips": 10, "take_profit_pips": 15},
    {"stop_loss_pips": 15, "take_profit_pips": 20},
    {"stop_loss_pips": 20, "take_profit_pips": 25},
    {"stop_loss_pips": 25, "take_profit_pips": 30}
]
```

---

## 📝 Complete Examples

### Example 1: Test Multiple Symbols (Single Day)
Test all US indices on Friday December 19th, 2025:

```python
mcp_universal_backtest_engine_bulk_backtest_strategy(
    strategy_name="Stochastic Quad Rotation",
    symbols=["NAS100_SB", "US30_SB", "US500_SB"],
    timeframes=["1m"],
    start_date="2025-12-19",
    end_date="2025-12-19",
    sl_tp_combinations=[
        {"stop_loss_pips": 15, "take_profit_pips": 15}
    ]
)
```

**Total Tests:** 3 (3 symbols × 1 timeframe × 1 SL/TP)

---

### Example 2: Optimize SL/TP Parameters
Test 9 different SL/TP combinations on NAS100:

```python
mcp_universal_backtest_engine_bulk_backtest_strategy(
    strategy_name="Stochastic Quad Rotation",
    symbols=["NAS100_SB"],
    timeframes=["1m"],
    start_date="2025-12-09",
    end_date="2025-12-11",
    sl_tp_combinations=[
        {"stop_loss_pips": 10, "take_profit_pips": 10},
        {"stop_loss_pips": 10, "take_profit_pips": 15},
        {"stop_loss_pips": 10, "take_profit_pips": 20},
        {"stop_loss_pips": 15, "take_profit_pips": 15},
        {"stop_loss_pips": 15, "take_profit_pips": 20},
        {"stop_loss_pips": 15, "take_profit_pips": 25},
        {"stop_loss_pips": 20, "take_profit_pips": 20},
        {"stop_loss_pips": 20, "take_profit_pips": 25},
        {"stop_loss_pips": 20, "take_profit_pips": 30}
    ]
)
```

**Total Tests:** 9 (1 symbol × 1 timeframe × 9 SL/TP)

---

### Example 3: Multi-Timeframe Analysis
Compare strategy performance across different timeframes:

```python
mcp_universal_backtest_engine_bulk_backtest_strategy(
    strategy_name="Stochastic Quad Rotation",
    symbols=["NAS100_SB"],
    timeframes=["1m", "5m", "15m"],
    start_date="2025-12-01",
    end_date="2025-12-31",
    sl_tp_combinations=[
        {"stop_loss_pips": 15, "take_profit_pips": 15}
    ]
)
```

**Total Tests:** 3 (1 symbol × 3 timeframes × 1 SL/TP)

---

### Example 4: Comprehensive Multi-Symbol Test
Test all indices with multiple SL/TP combinations:

```python
mcp_universal_backtest_engine_bulk_backtest_strategy(
    strategy_name="Stochastic Quad Rotation",
    symbols=["NAS100_SB", "US30_SB", "US500_SB", "UK100_SB", "GER40_SB"],
    timeframes=["1m"],
    start_date="2025-11-12",
    end_date="2025-12-11",
    sl_tp_combinations=[
        {"stop_loss_pips": 10, "take_profit_pips": 10},
        {"stop_loss_pips": 15, "take_profit_pips": 15},
        {"stop_loss_pips": 20, "take_profit_pips": 20}
    ]
)
```

**Total Tests:** 15 (5 symbols × 1 timeframe × 3 SL/TP)

---

### Example 5: Full Optimization Matrix
Test everything - symbols, timeframes, and SL/TP:

```python
mcp_universal_backtest_engine_bulk_backtest_strategy(
    strategy_name="Stochastic Quad Rotation",
    symbols=["NAS100_SB", "US30_SB"],
    timeframes=["1m", "5m"],
    start_date="2025-12-01",
    end_date="2025-12-15",
    sl_tp_combinations=[
        {"stop_loss_pips": 10, "take_profit_pips": 15},
        {"stop_loss_pips": 15, "take_profit_pips": 15},
        {"stop_loss_pips": 15, "take_profit_pips": 20}
    ]
)
```

**Total Tests:** 12 (2 symbols × 2 timeframes × 3 SL/TP)

---

## 📊 Understanding Results

### Console Output
After running a bulk backtest, you'll see:

```
🚀 BULK BACKTEST STARTED
Strategy: Stochastic Quad Rotation
Symbols: ['NAS100_SB', 'US30_SB', 'US500_SB']
Timeframes: ['1m']
SL/TP Combinations: 1
Total Tests: 3

Running backtest 1/3: NAS100_SB (1m) SL:15 TP:15
✅ Complete: +180.0 pips, 15 trades, 80.0% WR

Running backtest 2/3: US30_SB (1m) SL:15 TP:15
✅ Complete: +225.0 pips, 18 trades, 83.3% WR

Running backtest 3/3: US500_SB (1m) SL:15 TP:15
✅ Complete: +45.0 pips, 4 trades, 75.0% WR

📊 BULK BACKTEST COMPLETE
Total Tests: 3
Successful: 3
Failed: 0
Total Profit: +450.0 pips

📁 HTML Report Generated:
File: /path/to/bulk_backtest_Stochastic_Quad_Rotation_20251219_120000.html

⏱️ Total Execution Time: 2m 15s
```

---

### HTML Report

The bulk backtest generates a comprehensive HTML report with:

#### 1. Summary Table
Sortable table showing all test results:
- Symbol
- Timeframe
- SL/TP values
- Total trades
- Win rate
- Total pips
- Profit factor
- Max drawdown
- Sharpe ratio

#### 2. Performance Rankings
- Best by total pips
- Best by win rate
- Best by profit factor
- Best by Sharpe ratio

#### 3. Visual Charts
- Profit comparison bar chart
- Win rate comparison
- Trade count distribution
- Risk/reward analysis

#### 4. Detailed Statistics
- Average performance across all tests
- Success rate (profitable tests)
- Total trades executed
- Aggregate profit/loss

---

## 📈 Analyzing the HTML Report

### Opening the Report
1. Copy the HTML file path from the results
2. Open in your browser:
   - **Mac:** `open /path/to/report.html`
   - **Windows:** Double-click the file
   - **Linux:** `xdg-open /path/to/report.html`

### Sorting Results
Click any column header to sort:
- **Total Pips** - Find most profitable configurations
- **Win Rate** - Find most consistent configurations
- **Profit Factor** - Find best risk/reward
- **Trades** - Find most active configurations

### Filtering Results
Use browser search (Ctrl+F / Cmd+F) to filter:
- Search for specific symbols: "NAS100"
- Search for specific SL/TP: "15/15"
- Search for profitable only: "+"

---

## 🎯 Optimization Strategies

### 1. Symbol Selection
**Goal:** Find which symbols work best with your strategy

```python
symbols=["NAS100_SB", "US30_SB", "US500_SB", "UK100_SB", "GER40_SB"],
timeframes=["1m"],
sl_tp_combinations=[{"stop_loss_pips": 15, "take_profit_pips": 15}]
```

**Look for:**
- Highest total pips
- Consistent win rate (>60%)
- Sufficient trade count (>20)

---

### 2. SL/TP Optimization
**Goal:** Find optimal risk/reward parameters

```python
symbols=["NAS100_SB"],
timeframes=["1m"],
sl_tp_combinations=[
    {"stop_loss_pips": 10, "take_profit_pips": 10},
    {"stop_loss_pips": 10, "take_profit_pips": 15},
    {"stop_loss_pips": 10, "take_profit_pips": 20},
    {"stop_loss_pips": 15, "take_profit_pips": 15},
    {"stop_loss_pips": 15, "take_profit_pips": 20},
    {"stop_loss_pips": 20, "take_profit_pips": 20}
]
```

**Look for:**
- Best profit factor
- Lowest max drawdown
- Balance between win rate and profit

---

### 3. Timeframe Analysis
**Goal:** Find which timeframe suits your strategy

```python
symbols=["NAS100_SB"],
timeframes=["1m", "5m", "15m", "30m"],
sl_tp_combinations=[{"stop_loss_pips": 15, "take_profit_pips": 15}]
```

**Look for:**
- Trade frequency vs accuracy
- Execution feasibility
- Profit consistency

---

### 4. Comprehensive Optimization
**Goal:** Find the absolute best configuration

```python
symbols=["NAS100_SB", "US30_SB"],
timeframes=["1m", "5m"],
sl_tp_combinations=[
    {"stop_loss_pips": 10, "take_profit_pips": 15},
    {"stop_loss_pips": 15, "take_profit_pips": 15},
    {"stop_loss_pips": 15, "take_profit_pips": 20},
    {"stop_loss_pips": 20, "take_profit_pips": 25}
]
```

**Total Tests:** 16 (2 × 2 × 4)

**Look for:**
- Overall best performer
- Consistent across variations
- Practical for live trading

---

## ⚠️ Common Issues

### Issue: Too Many Tests
**Cause:** Large combination of parameters  
**Example:** 5 symbols × 4 timeframes × 9 SL/TP = 180 tests  
**Solution:**
- Start with fewer combinations
- Test symbols separately first
- Use shorter date ranges for initial tests

### Issue: Slow Execution
**Cause:** 1m timeframe with long date ranges  
**Solution:**
- Test shorter periods (1-2 weeks)
- Use larger timeframes for longer periods
- Run overnight for comprehensive tests

### Issue: No Signals on Some Tests
**Cause:** Strategy conditions not met or trading hours restriction  
**Solution:**
- Check if symbols are active during test period
- Verify trading hours match symbol's market hours
- Review strategy requirements (e.g., trend filter)

### Issue: Report Not Generated
**Cause:** All tests failed or file write error  
**Solution:**
- Check console for error messages
- Verify at least one test completed successfully
- Check disk space and write permissions

---

## 💡 Best Practices

### 1. Start Small
Begin with a few tests to verify everything works:
```python
symbols=["NAS100_SB"],
timeframes=["1m"],
sl_tp_combinations=[{"stop_loss_pips": 15, "take_profit_pips": 15}]
```

### 2. Test Incrementally
Build up complexity gradually:
1. Test single symbol, single SL/TP
2. Add more symbols
3. Add SL/TP variations
4. Add timeframe variations

### 3. Use Meaningful Date Ranges
- **Short-term (1-3 days):** Quick parameter testing
- **Medium-term (1-2 weeks):** Validation testing
- **Long-term (1 month+):** Comprehensive analysis

### 4. Organize Your Tests
Keep track of what you're testing:
```python
# Test 1: Symbol comparison
# Test 2: SL/TP optimization
# Test 3: Timeframe analysis
# Test 4: Final validation
```

### 5. Document Your Findings
After each bulk test:
- Note the best configurations
- Document why certain combinations work
- Save HTML reports with descriptive names
- Create comparison documents

---

## 📊 Interpreting Results

### Key Metrics to Compare

#### Total Pips
- **What it shows:** Absolute profitability
- **Good value:** Positive and substantial
- **Use for:** Finding most profitable configurations

#### Win Rate
- **What it shows:** Consistency and reliability
- **Good value:** >60% for reversal strategies
- **Use for:** Assessing strategy stability

#### Profit Factor
- **What it shows:** Risk/reward efficiency
- **Good value:** >2.0 (excellent: >3.0)
- **Use for:** Comparing risk-adjusted returns

#### Max Drawdown
- **What it shows:** Worst consecutive loss
- **Good value:** Lower is better
- **Use for:** Risk management planning

#### Trade Count
- **What it shows:** Strategy activity level
- **Good value:** Depends on timeframe and period
- **Use for:** Assessing statistical significance

---

## 🔍 Real-World Example

### Scenario: Finding Best Index for Stochastic Quad Rotation

**Step 1: Run bulk test on all indices**
```python
mcp_universal_backtest_engine_bulk_backtest_strategy(
    strategy_name="Stochastic Quad Rotation",
    symbols=["NAS100_SB", "US30_SB", "US500_SB", "UK100_SB", "GER40_SB"],
    timeframes=["1m"],
    start_date="2025-11-12",
    end_date="2025-12-11",
    sl_tp_combinations=[{"stop_loss_pips": 15, "take_profit_pips": 15}]
)
```

**Step 2: Review HTML report**
- Sort by "Total Pips"
- Check win rates
- Note trade counts

**Step 3: Results**
```
1. NAS100_SB: +1,845 pips, 80% WR, 205 trades ⭐ BEST
2. US30_SB: +2,040 pips, 77.9% WR, 244 trades ⭐ BEST
3. GER40_SB: +656 pips, 65.7% WR, 140 trades
4. UK100_SB: +122 pips, 69.6% WR, 23 trades
5. US500_SB: +167 pips, 68.8% WR, 32 trades
```

**Step 4: Optimize top performers**
```python
mcp_universal_backtest_engine_bulk_backtest_strategy(
    strategy_name="Stochastic Quad Rotation",
    symbols=["NAS100_SB", "US30_SB"],
    timeframes=["1m"],
    start_date="2025-11-12",
    end_date="2025-12-11",
    sl_tp_combinations=[
        {"stop_loss_pips": 10, "take_profit_pips": 15},
        {"stop_loss_pips": 15, "take_profit_pips": 15},
        {"stop_loss_pips": 15, "take_profit_pips": 20},
        {"stop_loss_pips": 20, "take_profit_pips": 25}
    ]
)
```

**Step 5: Select final configuration**
Based on results, choose:
- **Symbol:** NAS100_SB or US30_SB
- **Timeframe:** 1m
- **SL/TP:** Best performing combination
- **Forward test:** Validate on recent unseen data

---

## 🎯 Next Steps

After running bulk backtests:

1. **Analyze HTML Report** - Review all test results
2. **Identify Top Performers** - Note best configurations
3. **Validate Results** - Run single backtests with charts
4. **Forward Test** - Test on recent unseen data
5. **Paper Trade** - Test in live market conditions
6. **Document Findings** - Create strategy documentation

---

## 📚 Related Documentation

- **HOW_TO_RUN_BACKTEST.md** - Single backtest guide
- **STOCHASTIC_QUAD_ROTATION_COMPLETE_GUIDE.md** - Strategy details
- **MULTI_SYMBOL_COMPARISON.md** - Symbol performance analysis
- **BULK_BACKTEST_STOCHASTIC_RESULTS.md** - Example bulk test results

---

## 📁 File Locations

### HTML Reports
**Location:** `data/bulk/bulk_backtest_STRATEGY_TIMESTAMP.html`

**Example:**
```
data/bulk/bulk_backtest_Stochastic_Quad_Rotation_20251219_120000.html
```

### Individual Backtest JSONs
**Location:** `optimization_results/backtest_SYMBOL_TIMESTAMP.json`

**Example:**
```
optimization_results/backtest_NAS100_SB_20251219_120001.json
optimization_results/backtest_US30_SB_20251219_120002.json
```

---

**Last Updated:** December 22, 2025  
**Version:** 1.0
