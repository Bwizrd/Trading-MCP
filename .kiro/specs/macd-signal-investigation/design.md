# Design Document: MACD Signal Investigation

## Overview

This investigation addresses a critical bug where the MACD Crossover Strategy generates 0 trades despite visible crossovers on charts. The root cause lies in the signal generation logic within the DSL interpreter, specifically in how crossover detection is implemented and how indicator values are compared.

The investigation will follow a systematic debugging approach:
1. Add comprehensive logging to trace signal generation
2. Create test cases with synthetic crossover data
3. Compare DSL implementation with direct Python implementation
4. Identify and fix the root cause
5. Verify the fix with backtests

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Investigation Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Logging & Diagnostics                                   │
│     ├─ DSL Strategy Signal Generation                       │
│     ├─ Indicator Calculation                                │
│     └─ Crossover Detection Logic                            │
│                                                               │
│  2. Test Data Generation                                     │
│     ├─ Synthetic MACD Crossovers                            │
│     ├─ Known Signal Points                                  │
│     └─ Edge Cases (NaN, zero values)                        │
│                                                               │
│  3. Implementation Comparison                                │
│     ├─ DSL Strategy (JSON-based)                            │
│     ├─ Direct Python Strategy                               │
│     └─ Difference Analysis                                  │
│                                                               │
│  4. Root Cause Analysis                                      │
│     ├─ Condition Evaluation                                 │
│     ├─ Crossover Detection                                  │
│     └─ Data Flow Validation                                 │
│                                                               │
│  5. Fix Implementation & Verification                        │
│     ├─ Code Corrections                                     │
│     ├─ Unit Tests                                           │
│     └─ Integration Tests                                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **DSL Strategy (`shared/strategies/dsl_interpreter/dsl_strategy.py`)**
   - Implements indicator-based signal generation
   - Handles crossover detection via `_check_indicator_condition()`
   - Evaluates conditions with `_evaluate_condition()`

2. **Backtest Engine (`shared/backtest_engine.py`)**
   - Orchestrates strategy execution
   - Manages candle processing
   - Tracks trade lifecycle

3. **MACD Strategy Configuration (`shared/strategies/dsl_strategies/macd_crossover_strategy.json`)**
   - Defines MACD indicator parameters
   - Specifies buy/sell conditions with crossover flags
   - Sets risk management parameters

## Components and Interfaces

### 1. Diagnostic Logging System

**Purpose**: Capture detailed execution traces to identify where signal generation fails.

**Interface**:
```python
class DiagnosticLogger:
    def log_indicator_values(timestamp, macd, signal, histogram)
    def log_condition_evaluation(condition_str, context, result)
    def log_crossover_check(current_state, previous_state, crossover_detected)
    def log_signal_generation(signal_or_none, reason)
```

**Implementation Strategy**:
- Add logging at key decision points in DSL strategy
- Write to dedicated debug log file (`/tmp/dsl_debug.log`)
- Include timestamps, indicator values, and evaluation results
- Avoid contaminating JSON output

### 2. Test Data Generator

**Purpose**: Create synthetic market data with known MACD crossovers for testing.

**Interface**:
```python
class MACDTestDataGenerator:
    def generate_bullish_crossover(num_candles_before, num_candles_after) -> List[Candle]
    def generate_bearish_crossover(num_candles_before, num_candles_after) -> List[Candle]
    def generate_multiple_crossovers(count) -> List[Candle]
    def generate_edge_cases() -> List[Candle]  # NaN, zeros, etc.
```

**Data Characteristics**:
- Smooth price transitions to create predictable MACD behavior
- Clear crossover points with sufficient separation
- Realistic price ranges (e.g., 1.0500 - 1.0600 for EURUSD)
- Sufficient history for MACD calculation (26+ candles)

### 3. Strategy Comparison Framework

**Purpose**: Run identical data through both DSL and Python implementations to identify discrepancies.

**Interface**:
```python
class StrategyComparator:
    def run_dsl_strategy(candles, config) -> List[Signal]
    def run_python_strategy(candles, config) -> List[Signal]
    def compare_results(dsl_signals, python_signals) -> ComparisonReport
    def identify_discrepancies() -> List[Discrepancy]
```

**Comparison Metrics**:
- Signal count (DSL vs Python)
- Signal timing (timestamps match)
- Signal direction (BUY vs SELL)
- Entry prices
- Indicator values at signal points

### 4. Root Cause Analyzer

**Purpose**: Systematically identify the source of the bug.

**Analysis Areas**:
1. **Indicator Calculation**
   - Verify MACD formula: EMA(12) - EMA(26)
   - Verify signal line: EMA(9) of MACD
   - Check for NaN handling
   - Validate sufficient data points

2. **Condition Evaluation**
   - Parse condition string: `"macd > macd_signal"`
   - Variable substitution correctness
   - Comparison operator handling
   - Boolean result accuracy

3. **Crossover Detection**
   - Current condition: `macd > macd_signal` → True
   - Previous condition: `macd > macd_signal` → False
   - Crossover flag: `"crossover": true`
   - State tracking between candles

4. **Data Flow**
   - Candle history accumulation
   - Indicator value storage
   - Previous value preservation
   - Context passing to evaluation

## Data Models

### Diagnostic Log Entry
```python
@dataclass
class DiagnosticLogEntry:
    timestamp: datetime
    candle_index: int
    macd_value: Optional[float]
    signal_value: Optional[float]
    histogram_value: Optional[float]
    condition_evaluated: str
    condition_result: bool
    previous_condition_result: Optional[bool]
    crossover_detected: bool
    signal_generated: Optional[Signal]
    reason: str
```

### Test Case
```python
@dataclass
class MACDTestCase:
    name: str
    description: str
    candles: List[Candle]
    expected_signals: List[ExpectedSignal]
    expected_crossover_indices: List[int]
```

### Expected Signal
```python
@dataclass
class ExpectedSignal:
    candle_index: int
    direction: TradeDirection
    approximate_price: float
    tolerance: float = 0.0001
```

### Comparison Report
```python
@dataclass
class ComparisonReport:
    dsl_signal_count: int
    python_signal_count: int
    matching_signals: int
    dsl_only_signals: List[Signal]
    python_only_signals: List[Signal]
    timing_discrepancies: List[TimingDiscrepancy]
    root_cause_hypothesis: str
```

## Error Handling

### Error Categories

1. **Indicator Calculation Errors**
   - Insufficient data points (< 26 candles for MACD)
   - NaN values in price data
   - Invalid EMA parameters
   - **Handling**: Log warning, skip signal generation for that candle

2. **Condition Evaluation Errors**
   - Invalid condition syntax
   - Missing indicator values
   - Type conversion failures
   - **Handling**: Log error, return False (no signal)

3. **Crossover Detection Errors**
   - Missing previous indicator values
   - State tracking failures
   - **Handling**: Log warning, skip crossover check

4. **Test Data Generation Errors**
   - Invalid parameters
   - Insufficient candle count
   - **Handling**: Raise ValueError with descriptive message

### Error Recovery Strategy

- **Graceful Degradation**: Continue processing remaining candles even if one fails
- **Detailed Logging**: Capture full context for debugging
- **User Notification**: Report errors in test output
- **No Silent Failures**: Every error must be logged or reported

## Testing Strategy

### Unit Testing

Unit tests will verify individual components in isolation:

1. **MACD Calculation Tests**
   - Test EMA calculation accuracy
   - Test MACD line formula
   - Test signal line calculation
   - Test histogram derivation
   - Test NaN handling

2. **Condition Evaluation Tests**
   - Test simple comparisons (`>`, `<`, `==`)
   - Test variable substitution
   - Test edge cases (equal values, NaN)
   - Test invalid syntax handling

3. **Crossover Detection Tests**
   - Test bullish crossover detection
   - Test bearish crossover detection
   - Test no-crossover scenarios
   - Test state preservation

4. **Test Data Generator Tests**
   - Verify generated crossovers are detectable
   - Verify candle count and structure
   - Verify price realism

### Integration Testing

Integration tests will verify end-to-end signal generation:

1. **Synthetic Data Tests**
   - Run DSL strategy on generated crossover data
   - Verify expected signals are generated
   - Verify signal timing and direction

2. **Historical Data Tests**
   - Run on real market data with known crossovers
   - Compare against manual analysis
   - Verify chart markers match signals

3. **Comparison Tests**
   - Run both DSL and Python implementations
   - Verify identical signal generation
   - Identify any remaining discrepancies

### Test Execution Order

1. Unit tests for indicator calculation
2. Unit tests for condition evaluation
3. Unit tests for crossover detection
4. Integration tests with synthetic data
5. Integration tests with historical data
6. Comparison tests (DSL vs Python)

### Success Criteria

- All unit tests pass
- Synthetic data generates expected signals
- DSL and Python implementations produce identical results
- Historical backtest generates >0 trades on data with visible crossovers
- Chart markers align with visual crossover points


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Crossover Detection Completeness

*For any* MACD data with a crossover (where MACD line crosses above or below the signal line), the strategy SHALL generate a signal at the crossover point with the correct direction (BUY for bullish crossover, SELL for bearish crossover).

**Validates: Requirements 1.1, 1.2, 4.2**

### Property 2: Diagnostic Logging Completeness

*For any* candle processed during strategy execution, the system SHALL log the MACD value, signal line value, condition evaluation result, and any crossover detection to the debug log.

**Validates: Requirements 1.3, 2.2, 2.4, 2.5, 5.3**

### Property 3: Numerical Comparison Correctness

*For any* two numeric values A and B, the condition evaluation SHALL correctly determine whether A > B, A < B, or A == B, including edge cases where values differ by less than floating-point epsilon.

**Validates: Requirements 2.3**

### Property 4: MACD Calculation Correctness

*For any* sequence of price candles with sufficient history (≥26 candles), the calculated MACD line SHALL equal EMA(12) - EMA(26), and the signal line SHALL equal EMA(9) of the MACD line, matching standard technical analysis formulas.

**Validates: Requirements 3.1, 3.2**

### Property 5: Chart-Signal Consistency

*For any* backtest execution, the indicator values used for signal generation SHALL match the indicator values displayed on the generated chart.

**Validates: Requirements 3.3**

### Property 6: Sufficient Data Validation

*For any* strategy execution, if insufficient candles exist for MACD calculation (< 26 candles), the system SHALL skip signal generation and log a warning rather than producing invalid results.

**Validates: Requirements 3.5**

### Property 7: Implementation Equivalence

*For any* market data input, the DSL strategy implementation and direct Python implementation SHALL generate identical signals (same count, same timestamps, same directions, same prices).

**Validates: Requirements 5.1, 5.4**

### Property 8: Chart Marker Presence

*For any* generated signal, the chart output SHALL contain a corresponding marker at the signal timestamp with the correct direction indicator.

**Validates: Requirements 1.5**

### Example Test Cases

The following are specific examples that should be verified:

**Example 1: Backtest Output Format**
- Given a completed backtest
- The output SHALL include a "total_trades" or "signal_count" field
- **Validates: Requirements 1.4**

**Example 2: Configuration Access**
- Given a DSL strategy file path
- The system SHALL successfully read and parse the JSON configuration
- **Validates: Requirements 2.1**

**Example 3: Missed Crossover Reporting**
- Given a test with 3 expected crossovers where only 2 are detected
- The test output SHALL report "Crossover #2 at index 45 was not detected"
- **Validates: Requirements 4.3**

**Example 4: Test Pass Confirmation**
- Given all crossover detection tests passing
- The output SHALL include "✅ All crossover detection tests passed"
- **Validates: Requirements 4.4**

**Example 5: Test Failure Diagnostics**
- Given a failed crossover detection test
- The output SHALL include indicator values, condition results, and expected vs actual signals
- **Validates: Requirements 4.5**

**Example 6: Comparison Difference Highlighting**
- Given DSL generating 0 signals and Python generating 3 signals
- The comparison output SHALL highlight "DSL: 0 signals, Python: 3 signals - MISMATCH"
- **Validates: Requirements 5.2**

**Example 7: Root Cause Identification**
- Given a discrepancy between implementations
- The system SHALL report whether the issue is in "DSL parsing", "condition evaluation", or "data handling"
- **Validates: Requirements 5.5**

### Edge Cases

The following edge cases will be handled by the property-based test generators:

- **NaN Values**: MACD calculations with NaN price data (Requirements 3.4)
- **Null Values**: Missing indicator values in condition evaluation (Requirements 3.4)
- **Zero Values**: MACD and signal line both at zero
- **Very Close Values**: MACD and signal line differing by < 0.00001
- **Rapid Crossovers**: Multiple crossovers within a few candles
- **Insufficient Data**: Attempting signal generation with < 26 candles

## Implementation Plan

### Phase 1: Diagnostic Infrastructure (Investigation)

1. **Add Comprehensive Logging**
   - Instrument `_generate_indicator_signal()` with entry/exit logging
   - Log indicator values at each candle
   - Log condition evaluation steps
   - Log crossover detection logic
   - Write to `/tmp/dsl_debug.log`

2. **Create Debug Utilities**
   - Function to pretty-print indicator values
   - Function to visualize crossover points
   - Function to compare expected vs actual signals

### Phase 2: Test Data Generation

1. **Implement MACDTestDataGenerator**
   - Generate smooth price curves
   - Create predictable MACD crossovers
   - Support multiple crossover scenarios
   - Handle edge cases

2. **Create Test Cases**
   - Single bullish crossover
   - Single bearish crossover
   - Multiple alternating crossovers
   - No crossover (parallel lines)
   - Edge cases (NaN, zeros, close values)

### Phase 3: Root Cause Analysis

1. **Run Diagnostic Tests**
   - Execute DSL strategy on synthetic data
   - Analyze debug logs
   - Identify where signal generation fails

2. **Compare Implementations**
   - Create direct Python MACD strategy
   - Run both on identical data
   - Identify discrepancies

3. **Analyze Findings**
   - Review condition evaluation logic
   - Review crossover detection logic
   - Review indicator value storage
   - Review state preservation

### Phase 4: Fix Implementation

1. **Implement Corrections**
   - Fix identified bugs in DSL strategy
   - Update condition evaluation if needed
   - Fix crossover detection if needed
   - Fix state tracking if needed

2. **Verify Fix**
   - Re-run synthetic data tests
   - Verify signals are generated
   - Verify signal count matches expected

### Phase 5: Validation

1. **Run Historical Backtests**
   - Test on real market data
   - Verify trades are generated
   - Verify chart markers appear

2. **Compare with Manual Analysis**
   - Visually identify crossovers on chart
   - Verify signals match visual crossovers
   - Confirm timing accuracy

3. **Performance Testing**
   - Run on extended date ranges
   - Verify consistent behavior
   - Check for edge case handling

## Success Metrics

1. **Diagnostic Logs**: Complete execution trace showing indicator values and decisions
2. **Test Data**: Synthetic crossovers are correctly detected (100% detection rate)
3. **Implementation Match**: DSL and Python produce identical results
4. **Historical Data**: Backtest generates >0 trades on data with visible crossovers
5. **Chart Accuracy**: Signal markers align with visual crossover points
6. **Edge Case Handling**: No crashes or silent failures on edge cases

## Dependencies

- **pandas**: For data manipulation in test data generation
- **ta (Technical Analysis Library)**: For MACD calculation verification
- **pytest**: For unit and integration testing
- **logging**: For diagnostic output

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Root cause is in indicator calculation | High | Verify against known-good MACD implementation |
| Multiple bugs compound the issue | High | Fix and test incrementally, one issue at a time |
| Fix breaks other strategies | Medium | Run regression tests on MA Crossover and VWAP strategies |
| Edge cases remain unhandled | Medium | Comprehensive edge case testing in Phase 5 |
| Performance degradation from logging | Low | Use conditional logging, disable in production |

## Future Enhancements

1. **Real-time Debugging UI**: Web interface to visualize indicator values and signals
2. **Automated Regression Testing**: CI/CD integration for strategy testing
3. **Performance Profiling**: Identify bottlenecks in signal generation
4. **Strategy Comparison Tool**: Generic framework for comparing any two strategies
