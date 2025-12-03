# Advanced DSL Features Implementation Plan

## Goal
Implement advanced features to support full MACD Zero Line strategy:
1. **Filters** - Zero line and threshold filtering
2. **Confirmation** - Wait N candles before entry
3. **Trailing Stops** - Exit on opposite signal

## Implementation Steps

### Phase 1: Schema Updates
**File:** `shared/strategies/dsl_interpreter/schema_validator.py`

Add validation for:
- `filters` (optional array)
- `confirmation` (optional object)
- `risk_management.trailing_stop` (optional object)

### Phase 2: DSL Strategy Logic
**File:** `shared/strategies/dsl_interpreter/dsl_strategy.py`

Implement:
- Filter evaluation before signal generation
- Confirmation candle counting
- Trailing stop tracking and exit logic

### Phase 3: Prompt Templates
**File:** `mcp_servers/strategy_builder/prompt_templates.py`

Update Stage 3 prompt with:
- Filters section documentation
- Confirmation section documentation
- Trailing stop examples

### Phase 4: Testing
Create comprehensive tests for:
- Filter logic
- Confirmation wait
- Trailing stop exits

## Detailed Design

### 1. Filters Schema
```json
"filters": [
  {
    "indicator": "macd",
    "operator": ">",
    "value": 0,
    "applies_to": "buy"
  }
]
```

### 2. Confirmation Schema
```json
"confirmation": {
  "wait_candles": 2,
  "recheck_conditions": true
}
```

### 3. Trailing Stop Schema
```json
"risk_management": {
  "stop_loss_pips": 15,
  "take_profit_pips": 30,
  "trailing_stop": {
    "exit_on_opposite_signal": true
  }
}
```

## Backward Compatibility
All new fields are **optional** - existing strategies continue to work without changes.

## Implementation Time Estimate
- Phase 1: 30 minutes
- Phase 2: 60 minutes
- Phase 3: 20 minutes
- Phase 4: 30 minutes
**Total: ~2.5 hours**

## Status
🚧 Starting implementation...
