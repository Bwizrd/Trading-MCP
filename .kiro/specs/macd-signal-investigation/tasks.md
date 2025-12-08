# Implementation Plan: MACD Signal Investigation

## Overview

This plan systematically investigates and fixes the MACD crossover signal generation bug through diagnostic logging, test data generation, root cause analysis, and verification.

## 🎯 ROOT CAUSE IDENTIFIED (Task 1 Complete)

**Bug Location**: `_evaluate_condition()` method in `shared/strategies/dsl_interpreter/dsl_strategy.py`

**Issue**: Variable replacement uses simple string replace, causing:
- `'macd > macd_signal'` → `'6.713e-05 > 6.713e-05_signal'`
- Leaves `_signal` as unresolved variable
- Condition evaluation always returns False

**Fix**: Sort context variables by length (longest first) before replacement to ensure `macd_signal` is replaced before `macd`.

**Evidence**: See `/tmp/dsl_debug.log` and `TASK_1_DIAGNOSTIC_LOGGING_SUMMARY.md`

---

## Tasks

- [x] 1. Set up diagnostic logging infrastructure
  - Add comprehensive logging to DSL strategy signal generation
  - Create debug log file at `/tmp/dsl_debug.log`
  - Log indicator values, condition evaluations, and crossover checks
  - _Requirements: 1.3, 2.2, 2.4, 2.5, 5.3_

- [ ]* 1.1 Write property test for diagnostic logging completeness
  - **Property 2: Diagnostic Logging Completeness**
  - **Validates: Requirements 1.3, 2.2, 2.4, 2.5, 5.3**

- [ ] 2. Create test data generator for MACD crossovers
  - Implement `MACDTestDataGenerator` class
  - Generate synthetic price data with predictable MACD behavior
  - Create methods for bullish crossover, bearish crossover, and multiple crossovers
  - Include edge case generation (NaN, zeros, very close values)
  - _Requirements: 4.1_

- [ ]* 2.1 Write property test for test data generator
  - **Property 4: MACD Calculation Correctness**
  - **Validates: Requirements 3.1, 3.2**

- [ ] 3. Implement diagnostic test script
  - Create script to run DSL strategy on synthetic crossover data
  - Capture and analyze debug logs
  - Report expected vs actual signal counts
  - Identify specific candles where crossovers should occur
  - _Requirements: 4.2, 4.3_

- [ ]* 3.1 Write property test for crossover detection
  - **Property 1: Crossover Detection Completeness**
  - **Validates: Requirements 1.1, 1.2, 4.2**

- [ ] 4. Create direct Python MACD strategy for comparison
  - Implement MACD crossover logic without DSL
  - Use same indicator calculation (ta library)
  - Implement same crossover detection logic
  - Ensure identical risk management parameters
  - _Requirements: 5.1_

- [ ]* 4.1 Write property test for implementation equivalence
  - **Property 7: Implementation Equivalence**
  - **Validates: Requirements 5.1, 5.4**

- [ ] 5. Implement strategy comparison framework
  - Create `StrategyComparator` class
  - Run both DSL and Python strategies on identical data
  - Compare signal counts, timestamps, directions, and prices
  - Generate detailed comparison report
  - _Requirements: 5.1, 5.2, 5.4, 5.5_

- [ ] 6. Run initial diagnostic tests
  - Execute DSL strategy on synthetic data with known crossovers
  - Analyze debug logs to identify failure points
  - Document findings in investigation notes
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 7. Analyze root cause from diagnostic data
  - ✅ **ROOT CAUSE IDENTIFIED**: Variable replacement bug in `_evaluate_condition()`
  - **Bug**: Simple string replace of `macd` also affects `macd_signal`
  - **Result**: `'macd > macd_signal'` becomes `'6.713e-05 > 6.713e-05_signal'`
  - **Impact**: Leaves `_signal` as unresolved variable, condition always fails
  - **Fix needed**: Use word-boundary matching or sort variables by length (longest first)
  - _Requirements: 5.5_

- [-] 8. Implement bug fix in DSL strategy
  - Fix variable replacement in `_evaluate_condition()` method
  - **Solution**: Sort context variables by length (longest first) before replacement
  - This ensures `macd_signal` is replaced before `macd`
  - Add inline comments explaining the fix
  - Ensure fix doesn't break time-based strategies (test MA Crossover)
  - _Requirements: 1.1, 1.2_

- [ ]* 8.1 Write property test for numerical comparison correctness
  - **Property 3: Numerical Comparison Correctness**
  - **Validates: Requirements 2.3**

- [ ] 9. Verify fix with synthetic data tests
  - Re-run diagnostic tests on synthetic crossover data
  - Verify 100% crossover detection rate
  - Verify signal directions are correct
  - Verify signal timing is accurate
  - _Requirements: 4.2, 4.4, 4.5_

- [ ] 10. Run comparison tests (DSL vs Python)
  - Execute both implementations on identical data
  - Verify signal counts match
  - Verify signal timestamps match
  - Verify signal directions match
  - Document any remaining discrepancies
  - _Requirements: 5.1, 5.2, 5.4_

- [ ] 11. Test with historical market data
  - Run backtest on EURUSD 15m data with known crossovers
  - Verify trades are generated (>0 trades)
  - Verify chart markers appear at crossover points
  - Compare visual crossovers with generated signals
  - _Requirements: 1.4, 1.5_

- [ ]* 11.1 Write property test for chart-signal consistency
  - **Property 5: Chart-Signal Consistency**
  - **Validates: Requirements 3.3**

- [ ]* 11.2 Write property test for chart marker presence
  - **Property 8: Chart Marker Presence**
  - **Validates: Requirements 1.5**

- [ ] 12. Test edge case handling
  - Test with insufficient data (< 26 candles)
  - Test with NaN values in price data
  - Test with null indicator values
  - Test with MACD and signal line at zero
  - Test with very close values (< 0.00001 difference)
  - Test with rapid multiple crossovers
  - _Requirements: 3.4, 3.5_

- [ ]* 12.1 Write property test for sufficient data validation
  - **Property 6: Sufficient Data Validation**
  - **Validates: Requirements 3.5**

- [ ] 13. Run regression tests on other strategies
  - Test MA Crossover strategy still works
  - Test VWAP strategy still works
  - Test time-based DSL strategies still work
  - Ensure no breaking changes introduced
  - _Requirements: N/A (regression testing)_

- [ ] 14. Document findings and solution
  - Write summary of root cause
  - Document the fix applied
  - Update code comments
  - Create test cases for future regression prevention
  - _Requirements: All_

- [ ] 15. Final verification checkpoint
  - Ensure all tests pass, ask the user if questions arise.
  - Confirm MACD strategy generates trades on historical data
  - Confirm chart markers align with visual crossovers
  - Confirm no regression in other strategies

---

## Notes

- **Investigation Focus**: This is a debugging task, not new feature development
- **Incremental Approach**: Fix and verify one issue at a time
- **Logging Strategy**: Use file-based logging to avoid JSON output contamination
- **Test Data**: Synthetic data allows controlled testing of specific scenarios
- **Comparison**: Direct Python implementation provides ground truth for validation
- **Edge Cases**: Comprehensive edge case testing prevents future issues

## Fast-Track Option

Since the root cause has been identified in Task 1, you can:
1. **Skip to Task 8**: Implement the fix directly
2. **Then Task 9**: Verify with synthetic data
3. **Then Task 11**: Test with historical data
4. **Skip Tasks 2-7**: These were for investigation (already complete)

Or follow the full plan for comprehensive validation.
