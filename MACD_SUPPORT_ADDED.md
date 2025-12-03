# MACD Support Added to DSL System

## Summary

MACD (Moving Average Convergence Divergence) indicator support has been successfully added to the DSL trading strategy system. Users can now create MACD-based strategies using the Transcript Strategy Builder workflow.

## Changes Made

### 1. Indicator Calculation (`shared/indicators.py`)
**Added:** `MACDCalculator` class

**Features:**
- Calculates MACD line (fast EMA - slow EMA)
- Calculates signal line (EMA of MACD)
- Calculates histogram (MACD - signal)
- Configurable periods (default: 12, 26, 9)
- Returns all three values for strategy use

**Usage:**
```python
from shared.indicators import MACDCalculator

macd = MACDCalculator(fast_period=12, slow_period=26, signal_period=9)
macd_values = macd.calculate(candles)
signal_line = macd.get_signal_line()
histogram = macd.get_histogram()
```

### 2. DSL Schema Validation (`shared/strategies/dsl_interpreter/schema_validator.py`)
**Updated:** `_validate_indicators_configuration()`

**Changes:**
- Added "MACD" to valid indicator types: `["SMA", "EMA", "RSI", "MACD"]`
- Made `period` field optional (not required for MACD)
- Added validation for MACD-specific fields:
  - `fast_period` (optional, default: 12)
  - `slow_period` (optional, default: 26)
  - `signal_period` (optional, default: 9)

**Example MACD Indicator Config:**
```json
{
  "type": "MACD",
  "alias": "macd",
  "fast_period": 12,
  "slow_period": 26,
  "signal_period": 9
}
```

### 3. DSL Strategy Interpreter (`shared/strategies/dsl_interpreter/dsl_strategy.py`)
**Updated:** `_calculate_indicators()` and `get_indicator_series()`

**Changes:**
- Added MACD calculation using `ta.trend.MACD`
- Stores three values per MACD indicator:
  - `{alias}`: MACD line
  - `{alias}_signal`: Signal line
  - `{alias}_histogram`: Histogram
- Supports custom MACD parameters
- Works with crossover detection

**Available MACD Values in Conditions:**
```json
{
  "conditions": {
    "buy": {"compare": "macd > macd_signal", "crossover": true},
    "sell": {"compare": "macd < macd_signal", "crossover": true}
  }
}
```

### 4. Prompt Templates (`mcp_servers/strategy_builder/prompt_templates.py`)
**Updated:** Stage 3 prompt template

**Changes:**
- Added MACD to supported indicator types
- Added MACD-specific field documentation
- Added MACD usage notes:
  - Signal line crossover
  - Zero line filtering
  - Histogram analysis
- Added complete MACD strategy example

**Example MACD Strategy from Prompt:**
```json
{
  "name": "MACD Crossover Strategy",
  "version": "1.0.0",
  "description": "MACD signal line crossover with zero line filter",
  "indicators": [
    {"type": "MACD", "alias": "macd"}
  ],
  "conditions": {
    "buy": {"compare": "macd > macd_signal", "crossover": true},
    "sell": {"compare": "macd < macd_signal", "crossover": true}
  },
  "risk_management": {
    "stop_loss_pips": 25,
    "take_profit_pips": 40,
    "max_daily_trades": 5
  }
}
```

### 5. HTML Interface (`transcript_strategy_builder.html`)
**Updated:** Stage 3 indicator type list

**Changes:**
- Updated indicator types from `("SMA", "EMA", or "RSI")` to `("SMA", "EMA", "RSI", or "MACD")`

## MACD Strategy Patterns

### Pattern 1: Signal Line Crossover
```json
{
  "indicators": [{"type": "MACD", "alias": "macd"}],
  "conditions": {
    "buy": {"compare": "macd > macd_signal", "crossover": true},
    "sell": {"compare": "macd < macd_signal", "crossover": true}
  }
}
```

### Pattern 2: Zero Line Filter
```json
{
  "indicators": [{"type": "MACD", "alias": "macd"}],
  "conditions": {
    "buy": {"compare": "macd > 0", "crossover": false},
    "sell": {"compare": "macd < 0", "crossover": false}
  }
}
```

### Pattern 3: Histogram Analysis
```json
{
  "indicators": [{"type": "MACD", "alias": "macd"}],
  "conditions": {
    "buy": {"compare": "macd_histogram > 0", "crossover": false},
    "sell": {"compare": "macd_histogram < 0", "crossover": false}
  }
}
```

### Pattern 4: Combined Conditions
```json
{
  "indicators": [{"type": "MACD", "alias": "macd"}],
  "conditions": {
    "buy": {"compare": "macd > macd_signal", "crossover": true},
    "sell": {"compare": "macd < macd_signal", "crossover": true}
  }
}
```
Note: For combined conditions, you can add additional logic in the compare string.

## Testing

Comprehensive test suite created: `test_macd_support.py`

**Test Coverage:**
- ✅ Basic MACD strategy validation
- ✅ MACD with custom parameters
- ✅ MACD with zero line filter
- ✅ MACD histogram strategy
- ✅ MACD strategy save functionality
- ✅ Invalid indicator type rejection

**Test Results:**
```
============================================================
✅ ALL MACD SUPPORT TESTS PASSED!
============================================================

MACD indicator is now fully supported:
  ✅ Schema validation accepts MACD
  ✅ MACD strategies can be saved
  ✅ MACD line, signal, and histogram available
  ✅ Custom MACD parameters supported
  ✅ Invalid indicators are rejected
```

## Usage in Transcript Strategy Builder

### Step 1: Extract Trading Logic
When the LLM extracts strategy logic, it will now recognize MACD indicators:

```
INDICATORS:
- MACD (12, 26, 9): For trend identification
- Signal line crossover for entry/exit
```

### Step 2: Clarify Ambiguities
The LLM will ask about MACD-specific details:
- Which MACD values to use (line, signal, histogram)?
- Should it use crossover detection?
- Any zero line filtering?

### Step 3: Generate DSL JSON
The LLM will now generate valid MACD strategies:

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

### Step 4: Validate and Save
The validation and save tools now accept MACD strategies without errors.

## Next Steps

You can now:
1. ✅ Use the Transcript Strategy Builder with MACD strategies
2. ✅ Create MACD-based trading strategies via the workflow
3. ✅ Backtest MACD strategies using the universal backtest engine
4. ✅ Generate charts for MACD strategies

## Future Enhancements

The same pattern can be used to add more indicators:
- Bollinger Bands (already in indicators.py, needs DSL integration)
- Stochastic Oscillator
- ATR (Average True Range)
- ADX (Average Directional Index)
- Ichimoku Cloud
- Custom indicators

Each new indicator requires:
1. Calculator class in `shared/indicators.py`
2. Validation in `schema_validator.py`
3. Calculation in `dsl_strategy.py`
4. Documentation in prompt templates
5. Example in HTML interface

## Conclusion

MACD support is now fully integrated into the DSL system. The Transcript Strategy Builder can now handle MACD-based strategies from YouTube transcripts, making it much more versatile for real-world trading strategies.
