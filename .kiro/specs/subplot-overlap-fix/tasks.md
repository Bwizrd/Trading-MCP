# Implementation Plan

- [x] 0. Create Plotly proof-of-concept with synthetic data
  - Build a standalone script that creates a complete backtest chart using only Plotly and synthetic data
  - Test the spacing and layout approach before integrating with real backtest system
  - Validate that our mathematical model works in practice
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 0.1 Create synthetic data generation functions
  - Write functions to generate fake OHLCV candlestick data (100 candles)
  - Generate synthetic MACD values (line, signal, histogram)
  - Generate synthetic Stochastic values (%K and %D lines)
  - Generate synthetic RSI values
  - Generate fake trade entries/exits with buy/sell signals
  - Generate cumulative P&L data
  - _Requirements: 1.1, 1.2_

- [x] 0.2 Implement spacing calculation for proof-of-concept
  - Create a function that calculates vertical spacing based on number of rows
  - Use the design guidelines: 6 rows (price + 3 oscillators + volume + P&L) = 0.06 spacing
  - Calculate available space: 1.0 - (6-1) * 0.06 = 0.70
  - _Requirements: 2.1, 2.2_

- [x] 0.3 Implement row height calculation for proof-of-concept
  - Calculate heights from available space (0.70)
  - Price: 45% of available = 0.315
  - Each oscillator (3): 35%/3 of available = 0.0817 each
  - Volume: 10% of available = 0.07
  - P&L: 10% of available = 0.07
  - Verify sum equals available space (0.70)
  - _Requirements: 2.1, 2.2, 2.4_

- [x] 0.4 Create the multi-subplot chart with make_subplots
  - Use make_subplots with 6 rows, 1 column
  - Pass calculated row_heights list
  - Pass calculated vertical_spacing value
  - Add subplot titles: "Price Action", "MACD", "Stochastic", "RSI", "Volume", "Cumulative P&L"
  - _Requirements: 1.1, 1.2, 1.4_

- [x] 0.5 Add candlestick chart to price subplot
  - Add candlestick trace with synthetic OHLCV data
  - Use green/red colors for up/down candles
  - Add to row 1 (price subplot)
  - Disable range slider to prevent overlap
  - _Requirements: 1.2, 1.3_

- [x] 0.6 Add buy/sell signal markers to price chart
  - Add triangle-up markers for buy signals (green)
  - Add triangle-down markers for sell signals (red)
  - Position markers at entry prices
  - Add hover text showing trade details
  - _Requirements: 1.2, 1.3_

- [x] 0.7 Add MACD indicator to oscillator subplot
  - Add MACD line (blue) to row 2
  - Add Signal line (red) to row 2
  - Add Histogram bars (gray) to row 2
  - Add zero line (dashed gray)
  - Apply AUTO scaling with padding
  - _Requirements: 1.2, 1.3, 2.3_

- [x] 0.8 Add Stochastic indicator to oscillator subplot
  - Add %K line (blue) to row 3
  - Add %D line (orange, dashed) to row 3
  - Add reference lines at 80 (overbought) and 20 (oversold)
  - Apply FIXED scaling [0, 100]
  - _Requirements: 1.2, 1.3, 2.3_

- [x] 0.9 Add RSI indicator to oscillator subplot
  - Add RSI line (purple) to row 4
  - Add reference lines at 70 (overbought) and 30 (oversold)
  - Apply FIXED scaling [0, 100]
  - _Requirements: 1.2, 1.3, 2.3_

- [x] 0.10 Add volume chart
  - Add volume bars to row 5
  - Color bars green/red based on candle direction
  - _Requirements: 1.2, 1.3_

- [x] 0.11 Add cumulative P&L chart
  - Add P&L line chart to row 6
  - Add zero line (dashed gray)
  - Use green color for line
  - Add markers at trade exit points
  - _Requirements: 1.2, 1.3_

- [x] 0.12 Configure chart layout and styling
  - Set chart height to 1400px
  - Set title to "Proof of Concept - Subplot Spacing Test"
  - Use plotly_white theme
  - Enable legend
  - Share x-axis across all subplots
  - _Requirements: 1.1, 1.2_

- [x] 0.13 Save chart and verify spacing visually
  - Save chart as HTML file: "data/charts/poc_spacing_test.html"
  - Open chart in browser
  - Verify all 6 subplots are clearly separated with visible gaps
  - Verify no overlapping between subplots
  - Document any spacing issues discovered
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 0.14 Add visual spacing indicators (optional debug feature)
  - Add colored rectangles in the spacing gaps between subplots
  - Add text annotations showing spacing measurements
  - Use red/orange colors for high visibility
  - This helps validate that spacing is where we expect it
  - _Requirements: 1.1, 1.2_

- [x] 0.15 Document findings and lessons learned
  - Create a summary of what worked and what didn't
  - Note any Plotly quirks or gotchas discovered
  - Document the exact spacing/height values that produced good results
  - Use these findings to inform the implementation of tasks 1-10
  - _Requirements: All_

- [ ] 1. Rewrite `create_comprehensive_chart()` using POC approach
  - Replace the entire subplot creation section with POC-based implementation
  - Copy the working spacing and height calculation logic directly from POC
  - Keep the existing indicator routing and rendering logic intact
  - Use simple, inline calculations instead of complex method calls
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2_

- [ ] 1.1 Extract and adapt POC spacing calculation
  - Copy the spacing calculation from poc_subplot_spacing.py
  - Adapt it to use the actual num_rows from the chart layout
  - Use exact POC formula: 2 rows=0.12, 3 rows=0.10, 4 rows=0.08, 5+ rows=0.06
  - Keep it inline and simple - no separate method calls initially
  - _Requirements: 1.1, 1.4_

- [ ] 1.2 Extract and adapt POC height calculation
  - Copy the height calculation logic from poc_subplot_spacing.py
  - Calculate available_space = 1.0 - (num_rows - 1) * spacing
  - Allocate heights from available space (price 45%, oscillators 35%, volume 10%, P&L 10%)
  - Build heights list exactly as POC does
  - _Requirements: 2.1, 2.2, 2.4_

- [ ] 1.3 Replace make_subplots call with POC version
  - Remove the current make_subplots call and all its complexity
  - Use the simple POC version: make_subplots(rows=num_rows, cols=1, row_heights=heights, vertical_spacing=spacing, subplot_titles=titles, shared_xaxes=True)
  - Remove the specs parameter that POC doesn't use
  - Remove complex error handling initially - keep it simple
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 1.4 Test the rewritten chart creation
  - Run a backtest with MACD strategy
  - Verify the chart generates without errors
  - Check that spacing is now correct (no overlaps)
  - Compare with POC chart to verify similarity
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 1.5 Write property test for space conservation
  - **Property 1: Layout Space Conservation**
  - **Validates: Requirements 2.1, 2.2**

- [ ]* 1.6 Write property test for positive heights
  - **Property 2: Positive Space Allocation**
  - **Validates: Requirements 2.5**

- [ ]* 1.7 Write property test for spacing appropriateness
  - **Property 3: Spacing Appropriateness**
  - **Validates: Requirements 1.1, 1.4**

- [ ]* 1.8 Write property test for domain non-overlap
  - **Property 4: Subplot Domain Non-Overlap**
  - **Validates: Requirements 1.2, 1.3, 2.3**

- [ ]* 1.9 Write property test for equal oscillator distribution
  - **Property 5: Equal Oscillator Space Distribution**
  - **Validates: Requirements 2.4**

- [ ] 2. Add back error handling and logging (carefully)
  - Now that the core logic works, add back safety features
  - Keep error handling minimal and non-intrusive
  - Add logging for debugging without affecting the math
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 2.1 Add basic validation before make_subplots
  - Check that heights list is not empty
  - Check that spacing is positive
  - Log a warning if values look suspicious but proceed anyway
  - Only fail if values are clearly invalid (negative, NaN, etc.)
  - _Requirements: 2.5, 3.3_

- [ ] 2.2 Add try-except around make_subplots
  - Wrap make_subplots in try-except
  - Log the exact configuration on error
  - Provide a simple fallback (2 rows: price + P&L)
  - _Requirements: 1.2, 1.3, 3.2_

- [ ] 2.3 Add informational logging
  - Log spacing and heights at INFO level
  - Log total allocated space for verification
  - Keep logs concise and readable
  - _Requirements: 3.1_

- [ ] 2.4 Test error handling
  - Run backtests with various configurations
  - Verify logging is helpful
  - Verify fallback works if needed
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 3. Add LayoutConfiguration data model
  - Create a dataclass to encapsulate layout configuration
  - Add validation method to the dataclass
  - Use this model throughout the chart engine for type safety
  - _Requirements: 2.1, 2.2, 2.5_

- [ ] 3.1 Create LayoutConfiguration dataclass
  - Add dataclass with fields: num_rows, row_mapping, row_heights, vertical_spacing, subplot_titles
  - Import dataclass decorator from dataclasses module
  - Add type hints for all fields
  - _Requirements: 2.1, 2.2_

- [ ] 3.2 Implement `validate()` method on LayoutConfiguration
  - Add method that checks mathematical correctness of the configuration
  - Verify sum(row_heights) + (num_rows-1)*vertical_spacing ≤ 1.0
  - Verify all row_heights are positive
  - Return tuple of (is_valid, error_message)
  - _Requirements: 2.1, 2.2, 2.5_

- [ ] 3.3 Implement `total_allocated_space()` helper method
  - Add method that calculates total space used by heights and spacing
  - Return sum(row_heights) + (num_rows-1)*vertical_spacing
  - Use this in validation logic
  - _Requirements: 2.2_

- [ ]* 3.4 Write unit tests for LayoutConfiguration
  - Test validation with valid configurations (should pass)
  - Test validation with invalid configurations (should fail)
  - Test total_allocated_space calculation
  - _Requirements: 2.1, 2.2, 2.5_

- [ ] 3.5 Checkpoint - Run backtest and generate chart
  - Run a backtest with MACD strategy to generate a chart
  - Verify that LayoutConfiguration dataclass is being used
  - Check logs for validation messages
  - Compare chart with previous checkpoint
  - Save chart with timestamp for comparison

- [ ] 4. Implement visual debugging features
  - Add optional debug mode that shows subplot boundaries
  - Add method to draw spacing indicators on charts
  - Make debug mode configurable via parameter
  - _Requirements: 3.5_

- [ ] 4.1 Add `_add_debug_spacing_indicators()` method
  - Add method that draws colored rectangles in spacing gaps
  - Add text annotations showing spacing measurements
  - Only execute when debug parameter is True
  - _Requirements: 3.5_

- [ ] 4.2 Add debug parameter to `create_comprehensive_chart()`
  - Add optional debug parameter (default False)
  - Pass debug flag through to _add_debug_spacing_indicators
  - Document the debug parameter in docstring
  - _Requirements: 3.5_

- [ ] 4.3 Update chart title to indicate debug mode
  - When debug=True, add "[DEBUG MODE]" to chart title
  - Make debug indicators visually distinct (bright colors)
  - _Requirements: 3.5_

- [ ] 4.4 Checkpoint - Run backtest with debug mode enabled
  - Run a backtest with MACD strategy and debug=True
  - Verify that debug spacing indicators are visible on the chart
  - Check that spacing measurements are displayed
  - Compare with non-debug chart to see the visual indicators
  - Save chart with timestamp for comparison

- [ ] 5. Add comprehensive logging
  - Add detailed logging for all layout calculations
  - Log configuration values before subplot creation
  - Log validation results and any fallback actions
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 5.1 Add logging to `_calculate_vertical_spacing()`
  - Log the number of rows and calculated spacing value
  - Use INFO level for normal operation
  - _Requirements: 3.1_

- [ ] 5.2 Add logging to `_calculate_row_heights_with_spacing()`
  - Log the layout configuration and spacing input
  - Log the calculated heights and their sum
  - Log the available space calculation
  - Use INFO level for normal operation
  - _Requirements: 3.1_

- [ ] 5.3 Add logging to `_validate_layout_math()`
  - Log validation checks and their results
  - Use WARNING level for validation failures
  - Include specific details about what failed
  - _Requirements: 3.3_

- [ ] 5.4 Add logging to error handling in `create_comprehensive_chart()`
  - Log detailed error information when subplot creation fails
  - Log the exact configuration that was attempted
  - Log fallback actions with reason
  - Use ERROR level for failures
  - _Requirements: 3.2, 3.4_

- [ ] 5.5 Checkpoint - Run backtest and review logs
  - Run a backtest with MACD strategy
  - Review the log output for all layout calculations
  - Verify that spacing, heights, and validation results are logged
  - Check that log messages are clear and informative
  - Save chart and logs with timestamp for comparison

- [ ] 6. Write integration tests
  - Create tests that generate charts with various configurations
  - Verify charts render without errors
  - Verify visual spacing is correct
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 6.1 Write test for 2-row layout (price + P&L)
  - Generate chart with simple 2-row configuration
  - Verify chart renders successfully
  - Verify spacing is visible (0.12)
  - Save chart for manual inspection
  - _Requirements: 1.1, 1.2_

- [ ] 6.2 Write test for 4-row layout (price + MACD + volume + P&L)
  - Generate chart with MACD indicator
  - Verify all 4 subplots are clearly separated
  - Verify spacing is appropriate (0.08)
  - Save chart for manual inspection
  - _Requirements: 1.1, 1.2, 1.4_

- [ ] 6.3 Write test for 6-row layout (price + 3 oscillators + volume + P&L)
  - Generate chart with multiple oscillators
  - Verify all oscillators get equal space
  - Verify spacing is tighter but still visible (0.06)
  - Save chart for manual inspection
  - _Requirements: 1.1, 1.2, 1.4, 2.4_

- [ ]* 6.4 Write test for edge cases
  - Test with 1 row (edge case)
  - Test with 10 rows (stress test)
  - Test with no indicators (fallback to simple layout)
  - Verify graceful handling of all cases
  - _Requirements: 1.4, 2.5_

- [ ] 6.5 Checkpoint - Run integration tests and review results
  - Execute all integration tests (6.1, 6.2, 6.3)
  - Review generated charts for 2-row, 4-row, and 6-row layouts
  - Verify that spacing is appropriate for each configuration
  - Compare charts side-by-side to verify consistency
  - Save all charts with timestamps for comparison

- [ ] 7. Update existing tests to work with new layout system
  - Review all existing chart tests
  - Update any tests that make assumptions about old layout calculations
  - Ensure all tests pass with new implementation
  - _Requirements: All_

- [ ] 7.1 Update test_subplot_layout.py
  - Review tests for compatibility with new layout methods
  - Update any hardcoded spacing or height values
  - Ensure tests verify the new mathematical model
  - _Requirements: 2.1, 2.2_

- [ ] 7.2 Update test_macd_visualization.py
  - Ensure MACD chart tests work with new spacing
  - Verify MACD subplot is properly separated
  - Update any assertions about subplot positions
  - _Requirements: 1.2, 1.4_

- [ ] 7.3 Run full test suite and fix any failures
  - Execute all chart-related tests
  - Fix any tests broken by the layout changes
  - Ensure 100% test pass rate before completion
  - _Requirements: All_

- [ ] 7.4 Checkpoint - Run backtest after test updates
  - Run a backtest with MACD strategy
  - Verify that all existing functionality still works
  - Check that no regressions were introduced
  - Compare chart with previous checkpoints
  - Save chart with timestamp for comparison

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Documentation and cleanup
  - Update docstrings for all modified methods
  - Add inline comments explaining the mathematical model
  - Update any relevant documentation files
  - _Requirements: All_

- [ ] 9.1 Update method docstrings
  - Add detailed docstrings to all new methods
  - Explain the mathematical formulas used
  - Include examples of input/output
  - _Requirements: All_

- [ ] 9.2 Add inline comments for complex calculations
  - Comment the space conservation formula
  - Explain the height distribution logic
  - Document any non-obvious design decisions
  - _Requirements: 2.1, 2.2_

- [ ] 9.3 Create or update architecture documentation
  - Document the new layout calculation system
  - Explain the relationship between heights and spacing
  - Include diagrams if helpful
  - _Requirements: All_

- [ ] 9.4 Checkpoint - Run backtest after documentation
  - Run a backtest with MACD strategy
  - Verify that all documentation is accurate
  - Generate final chart showing the fixed spacing
  - Compare with the very first chart to show before/after improvement
  - Save chart with timestamp for comparison

- [ ] 10. Final checkpoint - Verify fix with real backtest
  - Run multiple backtests with different strategies (MACD, RSI, multiple oscillators)
  - Verify that all charts have proper spacing with no overlaps
  - Test with different timeframes and symbols
  - Confirm that the subplot overlap issue is completely resolved
  - Save all final charts for documentation
  - Ensure all tests pass, ask the user if questions arise.
