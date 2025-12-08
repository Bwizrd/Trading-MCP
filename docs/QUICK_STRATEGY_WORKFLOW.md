# Quick Strategy Workflow Guide

## Easy Way to Add Strategies (No Transcript Needed!)

### Step 1: Open the Strategy Saver
```bash
open save_strategy.html
```

### Step 2: Choose Your Approach

**Option A: Use Example Strategies**
1. Click one of the example buttons (MACD, MA, RSI, Time-Based)
2. Click "Validate"
3. Click "Download JSON File"
4. Move the file to `shared/strategies/dsl_strategies/`

**Option B: Paste Your Own JSON**
1. Paste your DSL JSON in the text area
2. Click "Validate" to check it
3. If valid, click "Download JSON File"
4. Move the file to `shared/strategies/dsl_strategies/`

**Option C: Create JSON Manually**
1. Create a new file in `shared/strategies/dsl_strategies/my_strategy.json`
2. Paste your DSL JSON
3. Save

### Step 3: Backtest Your Strategy

Now ask me (the LLM) to backtest it:

```
"Please backtest the MACD Crossover Strategy on EURUSD for the last 30 days using 15m timeframe"
```

I'll use the `run_strategy_backtest` tool to:
- Load your strategy from the dsl_strategies folder
- Fetch historical data
- Run the backtest
- Generate a chart
- Show you the results

## Example Strategies Included

### 1. MACD Crossover
```json
{
  "name": "MACD Crossover Strategy",
  "version": "1.0.0",
  "description": "MACD signal line crossover strategy",
  "indicators": [
    {"type": "MACD", "alias": "macd"}
  ],
  "conditions": {
    "buy": {"compare": "macd > macd_signal", "crossover": true},
    "sell": {"compare": "macd < macd_signal", "crossover": true}
  },
  "risk_management": {
    "stop_loss_pips": 25,
    "take_profit_pips": 40
  }
}
```

### 2. MA Crossover
```json
{
  "name": "MA Crossover Strategy",
  "version": "1.0.0",
  "description": "SMA 20/50 crossover",
  "indicators": [
    {"type": "SMA", "period": 20, "alias": "fast_ma"},
    {"type": "SMA", "period": 50, "alias": "slow_ma"}
  ],
  "conditions": {
    "buy": {"compare": "fast_ma > slow_ma", "crossover": true},
    "sell": {"compare": "fast_ma < slow_ma", "crossover": true}
  },
  "risk_management": {
    "stop_loss_pips": 20,
    "take_profit_pips": 30
  }
}
```

### 3. RSI Strategy
```json
{
  "name": "RSI Oversold Overbought",
  "version": "1.0.0",
  "description": "Buy RSI < 30, Sell RSI > 70",
  "indicators": [
    {"type": "RSI", "period": 14, "alias": "rsi"}
  ],
  "conditions": {
    "buy": {"compare": "rsi < 30", "crossover": false},
    "sell": {"compare": "rsi > 70", "crossover": false}
  },
  "risk_management": {
    "stop_loss_pips": 15,
    "take_profit_pips": 25
  }
}
```

## Complete Workflow Example

```bash
# 1. Open the strategy saver
open save_strategy.html

# 2. Click "MACD Crossover" example button
# 3. Click "Validate"
# 4. Click "Download JSON File"
# 5. Move downloaded file to shared/strategies/dsl_strategies/

# 6. Ask me to backtest:
```

Then in chat with me:
```
"Please backtest the MACD Crossover Strategy:
- Symbol: EURUSD
- Last 30 days
- Timeframe: 15m
- Create a chart"
```

I'll respond with:
- Total trades
- Win rate
- Profit/loss in pips
- Chart file path
- Performance analysis

## That's It!

No transcript needed. Just:
1. Create/paste JSON → Validate → Download
2. Move to dsl_strategies folder
3. Ask me to backtest

The strategy is automatically discovered and ready to use!
