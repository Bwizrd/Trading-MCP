# Indicator Charting System - Tasks

## Problem Statement

Different indicators have different visualization requirements:
- **Overlay indicators** (SMA, EMA, VWAP): Plot on price chart (same scale as price)
- **Oscillator indicators** (MACD, RSI, Stochastic): Plot on separate subplot (different scale)
- **Volume indicators**: Plot on separate volume subplot

Currently, all indicators are plotted on the price chart, making oscillators unreadable.

## Solution: Indicator Metadata System

Create a metadata system that defines how each indicator should be charted.

---

## Task List

### Phase 1: Indicator Metadata Infrastructure

- [ ] **1.1 Create indicator metadata registry**
  - Create `shared/indicators_metadata.py`
  - Define indicator types: `OVERLAY`, `OSCILLATOR`, `VOLUME`
  - Define scale ranges for each indicator
  - Map each indicator to its visualization type

- [ ] **1.2 Add metadata to indicator calculators**
  - Update `MACDCalculator` with metadata
  - Update `RSICalculator` with metadata
  - Update `SMACalculator`, `EMACalculator` with metadata
  - Add `get_chart_config()` method to each calculator

### Phase 2: Chart Engine Updates

- [ ] **2.1 Update chart engine to support subplots**
  - Modify `shared/chart_engine.py` to create multiple subplots
  - Add subplot for oscillators (below price chart)
  - Add subplot for volume (if needed)
  - Maintain backward compatibility with existing charts

- [ ] **2.2 Implement indicator routing logic**
  - Read indicator metadata from strategy
  - Route overlay indicators to price chart
  - Route oscillator indicators to oscillator subplot
  - Apply appropriate y-axis scaling for each subplot

- [ ] **2.3 Add visual styling for different indicator types**
  - Oscillators: Different color scheme
  - Add zero line for MACD
  - Add overbought/oversold lines for RSI (30/70)
  - Add signal line for MACD

### Phase 3: DSL Integration

- [ ] **3.1 Add indicator metadata to DSL schema**
  - Extend DSL to include optional `chart_config` per indicator
  - Allow strategies to override default charting behavior
  - Validate chart config in schema validator

- [ ] **3.2 Update DSL strategy to pass metadata to chart engine**
  - Extract indicator metadata from DSL config
  - Pass metadata to chart engine during chart creation
  - Ensure backward compatibility with existing strategies

### Phase 4: Strategy Onboarding Checklist

- [ ] **4.1 Create indicator onboarding checklist document**
  - Document: `INDICATOR_ONBOARDING_CHECKLIST.md`
  - Include: Indicator calculation requirements
  - Include: Chart visualization requirements
  - Include: Testing requirements
  - Include: Example implementations

- [ ] **4.2 Add indicator validation to strategy builder**
  - Check if indicator has chart metadata defined
  - Warn if new indicator lacks charting support
  - Provide guidance on adding chart support

### Phase 5: Testing & Documentation

- [ ] **5.1 Test MACD charting**
  - Verify MACD appears in separate subplot
  - Verify MACD line, signal line, histogram all visible
  - Verify zero line is displayed
  - Verify price chart remains unaffected

- [ ] **5.2 Test RSI charting (when added)**
  - Verify RSI appears in separate subplot
  - Verify 30/70 overbought/oversold lines
  - Verify 0-100 scale

- [ ] **5.3 Test MA crossover strategy (regression)**
  - Verify SMA/EMA still plot on price chart
  - Verify existing charts still work correctly
  - Verify no visual regressions

- [ ] **5.4 Update documentation**
  - Document indicator metadata system
  - Document how to add new indicators
  - Document charting best practices
  - Add examples for each indicator type

---

## Indicator Metadata Schema

```python
# Example metadata structure
INDICATOR_METADATA = {
    "MACD": {
        "type": "OSCILLATOR",
        "subplot": "oscillator",
        "scale": "auto",  # Auto-scale based on values
        "zero_line": True,
        "components": {
            "macd": {"color": "blue", "label": "MACD"},
            "signal": {"color": "red", "label": "Signal"},
            "histogram": {"color": "gray", "label": "Histogram", "type": "bar"}
        }
    },
    "RSI": {
        "type": "OSCILLATOR",
        "subplot": "oscillator",
        "scale": {"min": 0, "max": 100},
        "reference_lines": [
            {"value": 30, "color": "green", "label": "Oversold"},
            {"value": 70, "color": "red", "label": "Overbought"}
        ]
    },
    "SMA": {
        "type": "OVERLAY",
        "subplot": "price",
        "scale": "price",  # Use same scale as price
        "color": "blue"
    },
    "EMA": {
        "type": "OVERLAY",
        "subplot": "price",
        "scale": "price",
        "color": "orange"
    }
}
```

---

## Priority

**High Priority:**
- Task 1.1, 1.2 (Metadata infrastructure)
- Task 2.1, 2.2 (Chart engine updates)
- Task 5.1 (MACD charting test)

**Medium Priority:**
- Task 3.1, 3.2 (DSL integration)
- Task 5.3 (Regression testing)

**Low Priority:**
- Task 4.1, 4.2 (Onboarding checklist)
- Task 5.4 (Documentation)

---

## Success Criteria

✅ MACD charts display in separate subplot with proper scaling
✅ MA Crossover charts continue to work without changes
✅ New indicators can be added with clear charting requirements
✅ Chart engine automatically routes indicators to correct subplot
✅ All existing strategies continue to work (backward compatible)

---

## Estimated Effort

- Phase 1: 2-3 hours
- Phase 2: 3-4 hours
- Phase 3: 1-2 hours
- Phase 4: 1 hour
- Phase 5: 2 hours

**Total: 9-12 hours**

---

## Notes

- This is a foundational improvement that will benefit all future indicators
- The metadata system makes the chart engine self-configuring
- Onboarding checklist prevents future charting issues
- Backward compatibility is critical - don't break existing charts
