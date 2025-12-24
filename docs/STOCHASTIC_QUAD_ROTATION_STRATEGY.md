# Stochastic Quad Rotation Strategy

## Overview

The **Stochastic Quad Rotation** strategy is an advanced momentum-based trading system that uses four stochastic oscillators with different periods to identify high-probability reversal points in the market. It generates signals when all oscillators reach extreme zones and the fastest oscillator "rotates" back, indicating a potential trend reversal.

## Strategy Concept

### What is a Rotation Signal?

A rotation signal occurs when:
1. **All stochastic oscillators are in an extreme zone** (overbought or oversold)
2. **The fastest oscillator crosses back** out of that zone first

This indicates that momentum is exhausting and a reversal is likely.

### The Four Stochastic Oscillators

The strategy uses four stochastic instances with progressively longer periods:

| Alias | K Period | K Smoothing | D Smoothing | Description |
|-------|----------|-------------|-------------|-------------|
| **fast** | 9 | 1 | 3 | Fastest, most responsive to price changes |
| **med_fast** | 14 | 1 | 3 | Medium-fast, standard stochastic period |
| **med_slow** | 40 | 1 | 4 | Medium-slow, filters out noise |
| **slow** | 60 | 1 | 10 | Slowest, confirms major trends |

## Entry Rules

### Buy Signal

A **BUY** signal is generated when **ALL** of the following conditions are met:
1. ✅ **All 4 stochastics** (fast, med_fast, med_slow, slow) are **below 20** (oversold zone)
2. ✅ **The fastest stochastic** (9-period) **crosses above 20**
3. ✅ **Time is between 14:30 and 21:00 UTC** (trading hours filter)
4. ✅ **Price range in last 10 minutes ≥ 10 pips** (trend strength filter)

This indicates the market is oversold, beginning to reverse upward, and has sufficient volatility during active trading hours.

### Sell Signal

A **SELL** signal is generated when **ALL** of the following conditions are met:
1. ✅ **All 4 stochastics** (fast, med_fast, med_slow, slow) are **above 80** (overbought zone)
2. ✅ **The fastest stochastic** (9-period) **crosses below 80**
3. ✅ **Time is between 14:30 and 21:00 UTC** (trading hours filter)
4. ✅ **Price range in last 10 minutes ≥ 10 pips** (trend strength filter)

This indicates the market is overbought, beginning to reverse downward, and has sufficient volatility during active trading hours.

## Technical Details

### Stochastic Oscillator Calculation

The Stochastic Oscillator measures momentum using the position of the closing price relative to the high-low range over a period:

**%K Line (Fast Line)**:
```
%K = ((Close - Lowest Low) / (Highest High - Lowest Low)) × 100
```

**%D Line (Signal Line)**:
```
%D = SMA(%K, d_smoothing period)
```

### Key Characteristics

- **Range**: Stochastic values range from 0 to 100
- **Oversold Zone**: Below 20 (prices near the low end of the range)
- **Overbought Zone**: Above 80 (prices near the high end of the range)
- **Neutral Zone**: Between 20 and 80

### Why Multiple Periods?

Using multiple stochastic periods provides:
1. **Confluence**: All timeframes agreeing increases signal reliability
2. **Noise Filtering**: Longer periods filter out false signals
3. **Early Entry**: The fast stochastic provides timely entries
4. **Trend Confirmation**: Slower stochastics confirm the major trend

## Risk Management

### Position Management

- **Stop Loss**: 15 pips
- **Take Profit**: 25 pips
- **Risk/Reward Ratio**: 1:1.67

### Trading Filters

#### Trading Hours Restriction
The strategy only trades during specific hours to avoid low liquidity periods:
- **Start Time**: 14:30 UTC (London session continues, New York opens)
- **End Time**: 21:00 UTC (New York session active)
- **Purpose**: Trade during peak forex market activity when liquidity is highest

#### Trend Strength Filter
To avoid trading in choppy, range-bound conditions, the strategy includes a minimum trend requirement:
- **Minimum Trend Range**: 10 pips
- **Lookback Period**: 10 minutes
- **Calculation**: Measures the high-low range over the last 10 minutes
- **Purpose**: Only take trades when there's sufficient price movement

This filter ensures the strategy only trades when:
1. The market has shown at least 10 pips of movement in the last 10 minutes
2. There's enough volatility to reach the take profit target

### Additional Constraints

- **Max Daily Trades**: 200 (safety limit to prevent over-trading)
- **Min Pip Distance**: 0.0001 (minimum price movement to consider)
- **Execution Window**: 1440 minutes (24 hours - full trading day)

These parameters can be adjusted based on market volatility, symbol characteristics, and trading preferences.

## Visual Example

When charted, you'll see:
- **4 pairs of lines** (%K and %D) in the stochastic subplot
- **Different colors** for each stochastic (blue → green → orange → red, from fastest to slowest)
- **Reference lines** at levels 20, 50, and 80
- **Buy arrows** when rotation occurs from below 20
- **Sell arrows** when rotation occurs from above 80

## Implementation Architecture

### JSON Configuration

The strategy is defined using a JSON DSL (Domain Specific Language):

```json
{
  "name": "Stochastic Quad Rotation",
  "version": "1.0.0",
  "description": "Multi-timeframe stochastic rotation strategy",
  "indicators": [
    {
      "type": "STOCHASTIC",
      "alias": "fast",
      "params": {"k_period": 9, "k_smoothing": 1, "d_smoothing": 3}
    },
    {
      "type": "STOCHASTIC",
      "alias": "med_fast",
      "params": {"k_period": 14, "k_smoothing": 1, "d_smoothing": 3}
    },
    {
      "type": "STOCHASTIC",
      "alias": "med_slow",
      "params": {"k_period": 40, "k_smoothing": 1, "d_smoothing": 4}
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
        "indicators": ["fast", "med_fast", "med_slow", "slow"]
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
        "indicators": ["fast", "med_fast", "med_slow", "slow"]
      },
      "trigger": {
        "indicator": "fast",
        "crosses_below": 80
      }
    }
  },
  "risk_management": {
    "stop_loss_pips": 15,
    "take_profit_pips": 25,
    "max_daily_trades": 200,
    "min_pip_distance": 0.0001,
    "execution_window_minutes": 1440,
    "trading_hours_start": "14:30",
    "trading_hours_end": "21:00",
    "min_trend_range_pips": 10.0,
    "trend_lookback_minutes": 10
  }
}
```

### Core Components

The strategy uses several advanced DSL components:

1. **MultiIndicatorManager**: Creates and manages multiple stochastic instances
2. **ConditionEvaluator**: Evaluates zone conditions (all indicators below/above threshold)
3. **CrossoverDetector**: Detects when the fast stochastic crosses the threshold
4. **StochasticCalculator**: Computes %K and %D values for each instance

### Execution Flow

```
1. Calculate all 4 stochastics for current candle
   ↓
2. Check zone condition:
   - Are ALL stochastics below 20 (buy) or above 80 (sell)?
   ↓
3. Check crossover trigger:
   - Did the fast stochastic cross the threshold?
   ↓
4. If both conditions met → Generate signal
   ↓
5. Update state for next candle
```

## Performance Characteristics

### Optimizations

- **Indicator Caching**: Each stochastic calculated once per candle
- **Short-Circuit Evaluation**: Zone checks exit early if any indicator fails
- **Efficient State Storage**: Only stores previous values for crossover detection
- **Lazy Calculation**: Only calculates indicators needed for the strategy

### Performance Targets

- **Indicator Calculation**: < 1ms per stochastic per candle
- **Condition Evaluation**: < 0.1ms per condition
- **Crossover Detection**: < 0.05ms per check
- **Backtest Speed**: 1000 candles in under 5 seconds

## Use Cases

This strategy works best in:

- **Range-Bound Markets**: Oscillating between support and resistance
- **Mean Reversion Scenarios**: Price extremes that revert to the mean
- **Higher Timeframes**: 15m, 30m, 1h, 4h charts (avoid 1m charts due to noise)
- **Volatile Markets**: Clear overbought/oversold conditions

## Limitations

- **Trending Markets**: Can generate false signals during strong trends
- **Choppy Markets**: May whipsaw in sideways markets
- **Low Volatility**: Fewer extreme zone entries in calm markets
- **Requires Patience**: Signals are relatively infrequent (quality over quantity)

## Backtesting Considerations

When backtesting this strategy:

1. **Test Multiple Symbols**: Different markets behave differently
2. **Test Multiple Timeframes**: Find the optimal timeframe for each symbol
3. **Include Slippage**: Add realistic spread and slippage costs
4. **Consider Trading Hours**: Forex is most active during London/NY sessions
5. **Walk-Forward Testing**: Validate on out-of-sample data
6. **Parameter Optimization**: Fine-tune stochastic periods and thresholds

## Advanced Variations

Potential enhancements:
- **Dynamic Thresholds**: Adjust 20/80 levels based on volatility
- **Volume Confirmation**: Require volume spike for signal confirmation
- **Trend Filter**: Only trade in direction of higher timeframe trend
- **Partial Exits**: Take profit in stages (e.g., 50% at 15 pips, 50% at 25 pips)
- **Adaptive Stop Loss**: Adjust SL based on ATR (Average True Range)

## Related Documentation

- [Requirements Document](.kiro/specs/advanced-dsl-stochastic-strategy/requirements.md)
- [Design Document](.kiro/specs/advanced-dsl-stochastic-strategy/design.md)
- [Implementation Tasks](.kiro/specs/advanced-dsl-stochastic-strategy/tasks.md)
- [Backtest Results](docs/FOREX_BACKTEST_RESULTS.md)

## Quick Start

To use this strategy in a backtest:

```python
# Via MCP Server
result = backtest_tool(
    strategy="stochastic_quad_rotation",
    symbol="EURUSD",
    timeframe="15m",
    start_date="2024-01-01",
    end_date="2024-11-28"
)

# Generate chart
chart = generate_chart_tool(
    backtest_result=result,
    show_indicators=True
)
```

The strategy file is located at:
`shared/strategies/dsl_strategies/stochastic_quad_rotation.json`
