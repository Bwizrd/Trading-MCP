# Advanced DSL Strategy Guide

## Overview

The Advanced DSL system allows you to create complex multi-indicator trading strategies using JSON configuration files. This guide shows you how to use the new features.

## Quick Start

### 1. Simple Strategy (Original)

```json
{
  "name": "MA Crossover Strategy",
  "version": "1.0.0",
  "description": "Buy when fast MA crosses above slow MA",
  "indicators": [
    {"type": "SMA", "alias": "fast_ma", "period": 20},
    {"type": "SMA", "alias": "slow_ma", "period": 50}
  ],
  "conditions": {
    "buy": {
      "compare": "fast_ma > slow_ma",
      "crossover": true
    },
    "sell": {
      "compare": "fast_ma < slow_ma",
      "crossover": true
    }
  },
  "risk_management": {
    "stop_loss_pips": 15,
    "take_profit_pips": 25
  }
}
```

### 2. Advanced Strategy (Rotation)

```json
{
  "name": "Stochastic Quad Rotation",
  "version": "1.0.0",
  "description": "Multi-period stochastic rotation strategy",
  "indicators": [
    {
      "type": "STOCHASTIC",
      "alias": "fast",
      "params": {"k_period": 9, "k_smoothing": 1, "d_smoothing": 3}
    },
    {
      "type": "STOCHASTIC",
      "alias": "slow",
      "params": {"k_period": 60, "k_smoothing": 1, "d_smoothing": 10}
    }
  ],
  "conditions": {
    "buy": {
      "type": "rotation",
      "zone": {
        "all_below": 20,
        "indicators": ["fast", "slow"]
      },
      "trigger": {
        "indicator": "fast",
        "crosses_above": 20
      }
    },
    "sell": {
      "type": "rotation",
      "zone": {
        "all_above": 80,
        "indicators": ["fast", "slow"]
      },
      "trigger": {
        "indicator": "fast",
        "crosses_below": 80
      }
    }
  },
  "risk_management": {
    "stop_loss_pips": 15,
    "take_profit_pips": 25
  }
}
```

## Supported Indicators

### Moving Averages
- **SMA**: Simple Moving Average
  - Parameters: `period` (integer)
  - Example: `{"type": "SMA", "alias": "sma20", "period": 20}`

- **EMA**: Exponential Moving Average
  - Parameters: `period` (integer)
  - Example: `{"type": "EMA", "alias": "ema50", "period": 50}`

### Oscillators
- **RSI**: Relative Strength Index
  - Parameters: `period` (integer, default: 14)
  - Example: `{"type": "RSI", "alias": "rsi", "period": 14}`

- **STOCHASTIC**: Stochastic Oscillator
  - Parameters:
    - `k_period`: Period for %K calculation (default: 14)
    - `k_smoothing`: Smoothing for %K (default: 1)
    - `d_smoothing`: Smoothing for %D signal line (default: 3)
  - Example: `{"type": "STOCHASTIC", "alias": "stoch", "params": {"k_period": 14, "k_smoothing": 1, "d_smoothing": 3}}`

### Trend Indicators
- **MACD**: Moving Average Convergence Divergence
  - Parameters:
    - `fast_period`: Fast EMA period (default: 12)
    - `slow_period`: Slow EMA period (default: 26)
    - `signal_period`: Signal line period (default: 9)
  - Example: `{"type": "MACD", "alias": "macd", "fast_period": 12, "slow_period": 26, "signal_period": 9}`

## Condition Types

### Simple Conditions (Original)

Use comparison operators with indicator aliases:

```json
{
  "buy": {
    "compare": "fast_ma > slow_ma",
    "crossover": true
  }
}
```

**Operators**: `>`, `<`, `>=`, `<=`, `==`, `!=`

**Crossover**: Set to `true` to only trigger when condition becomes true (was false before)

### Rotation Conditions (Advanced)

Rotation conditions combine zone checks with crossover triggers:

```json
{
  "buy": {
    "type": "rotation",
    "zone": {
      "all_below": 20,
      "indicators": ["fast", "med_fast", "med_slow", "slow"]
    },
    "trigger": {
      "indicator": "fast",
      "crosses_above": 20
    }
  }
}
```

**Zone Options**:
- `all_below`: All indicators must be below this threshold
- `all_above`: All indicators must be above this threshold
- `indicators`: List of indicator aliases to check

**Trigger Options**:
- `indicator`: Which indicator to watch for crossover
- `crosses_above`: Trigger when indicator crosses above this level
- `crosses_below`: Trigger when indicator crosses below this level

## Multi-Instance Indicators

You can use multiple instances of the same indicator with different parameters:

```json
{
  "indicators": [
    {"type": "STOCHASTIC", "alias": "fast", "params": {"k_period": 9}},
    {"type": "STOCHASTIC", "alias": "med", "params": {"k_period": 14}},
    {"type": "STOCHASTIC", "alias": "slow", "params": {"k_period": 60}}
  ]
}
```

Each instance needs a unique `alias` for reference in conditions.

## Risk Management

All strategies require risk management parameters:

```json
{
  "risk_management": {
    "stop_loss_pips": 15,
    "take_profit_pips": 25,
    "max_daily_trades": 3,
    "min_pip_distance": 0.0001,
    "execution_window_minutes": 1440
  }
}
```

**Parameters**:
- `stop_loss_pips`: Stop loss in pips (required)
- `take_profit_pips`: Take profit in pips (required)
- `max_daily_trades`: Maximum trades per day (default: 1)
- `min_pip_distance`: Minimum price movement to trigger (default: 0.0001)
- `execution_window_minutes`: How long signal is valid (default: 1440 = 24 hours)

## Strategy Examples

### Example 1: RSI Oversold/Overbought

```json
{
  "name": "RSI Reversal",
  "version": "1.0.0",
  "description": "Buy when RSI crosses above 30, sell when crosses below 70",
  "indicators": [
    {"type": "RSI", "alias": "rsi", "period": 14}
  ],
  "conditions": {
    "buy": {
      "type": "rotation",
      "zone": {"all_below": 30, "indicators": ["rsi"]},
      "trigger": {"indicator": "rsi", "crosses_above": 30}
    },
    "sell": {
      "type": "rotation",
      "zone": {"all_above": 70, "indicators": ["rsi"]},
      "trigger": {"indicator": "rsi", "crosses_below": 70}
    }
  },
  "risk_management": {
    "stop_loss_pips": 20,
    "take_profit_pips": 30
  }
}
```

### Example 2: Multi-Timeframe Stochastic

```json
{
  "name": "Multi-TF Stochastic",
  "version": "1.0.0",
  "description": "Trade when fast and slow stochastics align",
  "indicators": [
    {"type": "STOCHASTIC", "alias": "fast", "params": {"k_period": 5}},
    {"type": "STOCHASTIC", "alias": "slow", "params": {"k_period": 21}}
  ],
  "conditions": {
    "buy": {
      "type": "rotation",
      "zone": {"all_below": 20, "indicators": ["fast", "slow"]},
      "trigger": {"indicator": "fast", "crosses_above": 20}
    },
    "sell": {
      "type": "rotation",
      "zone": {"all_above": 80, "indicators": ["fast", "slow"]},
      "trigger": {"indicator": "fast", "crosses_below": 80}
    }
  },
  "risk_management": {
    "stop_loss_pips": 15,
    "take_profit_pips": 25
  }
}
```

### Example 3: MACD with RSI Filter

```json
{
  "name": "MACD RSI Combo",
  "version": "1.0.0",
  "description": "MACD crossover with RSI confirmation",
  "indicators": [
    {"type": "MACD", "alias": "macd"},
    {"type": "RSI", "alias": "rsi", "period": 14}
  ],
  "conditions": {
    "buy": {
      "compare": "macd > macd_signal and rsi > 50",
      "crossover": true
    },
    "sell": {
      "compare": "macd < macd_signal and rsi < 50",
      "crossover": true
    }
  },
  "risk_management": {
    "stop_loss_pips": 15,
    "take_profit_pips": 25
  }
}
```

## Testing Your Strategy

### 1. Validate Configuration

Save your strategy as a JSON file in `shared/strategies/dsl_strategies/`

The system will automatically validate:
- Required fields are present
- Indicator types are valid
- Aliases are unique
- Conditions reference valid indicators
- Risk management parameters are valid

### 2. Run Backtest

```python
# Through MCP server
run_strategy_backtest(
    strategy_name="Your Strategy Name",
    symbol="EURUSD_SB",
    timeframe="15m",
    days_back=30,
    stop_loss_pips=15,
    take_profit_pips=25
)
```

### 3. View Results

The backtest will return:
- Total trades
- Win rate
- Total pips
- Profit/loss
- Trade history
- Interactive chart (if auto_chart=true)

## Best Practices

### 1. Start Simple
Begin with 1-2 indicators and simple conditions. Add complexity gradually.

### 2. Use Meaningful Aliases
Choose descriptive aliases like "fast_stoch" instead of "s1".

### 3. Test Thoroughly
Backtest on multiple symbols and timeframes before live trading.

### 4. Document Your Logic
Use clear descriptions explaining your strategy's logic.

### 5. Manage Risk
Always set appropriate stop loss and take profit levels.

### 6. Avoid Over-Optimization
Don't create strategies that only work on historical data.

## Troubleshooting

### Strategy Not Found
- Check the JSON file is in `shared/strategies/dsl_strategies/`
- Verify the file name ends with `.json`
- Restart MCP servers to pick up new strategies

### Validation Errors
- Read the error message carefully - it tells you what's wrong
- Check indicator types are spelled correctly (case-sensitive)
- Verify all aliases are unique
- Ensure conditions reference existing indicators

### No Signals Generated
- Check your conditions aren't too restrictive
- Verify indicators have enough data (check `requires_periods()`)
- Use diagnostic logging to see indicator values

### Unexpected Results
- Review the trade history to understand what happened
- Check the chart to visualize indicator behavior
- Verify your condition logic matches your intent

## Advanced Topics

### Custom Indicator Parameters

Each indicator type has specific parameters:

```json
{
  "type": "STOCHASTIC",
  "alias": "custom_stoch",
  "params": {
    "k_period": 21,
    "k_smoothing": 3,
    "d_smoothing": 5
  }
}
```

### Multiple Conditions

Combine multiple checks in one condition:

```json
{
  "compare": "fast_ma > slow_ma and rsi > 50 and macd > 0"
}
```

### Zone Thresholds

Common threshold levels:
- **Stochastic/RSI**: 20/80 (oversold/overbought), 30/70 (moderate)
- **MACD**: 0 (zero line crossover)

## Support

For issues or questions:
1. Check this guide first
2. Review the spec files in `.kiro/specs/advanced-dsl-stochastic-strategy/`
3. Run the test files in `copilot-tests/`
4. Check the diagnostic log at `/tmp/dsl_debug.log`

## Version History

- **v1.0.0** (2025-12-09): Initial release with rotation conditions and multi-instance support
