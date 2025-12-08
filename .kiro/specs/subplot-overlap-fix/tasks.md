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

- [x] 1. Rewrite `create_comprehensive_chart()` using POC approach
  - Replace the entire subplot creation section with POC-based implementation
  - Copy the working spacing and height calculation logic directly from POC
  - Keep the existing indicator routing and rendering logic intact
  - Use simple, inline calculations instead of complex method calls
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2_

- [x] 1.1 Extract and adapt POC spacing calculation
  - Copy the spacing calculation from poc_subplot_spacing.py
  - Adapt it to use the actual num_rows from the chart layout
  - Use exact POC formula: 2 rows=0.12, 3 rows=0.10, 4 rows=0.08, 5+ rows=0.06
  - Keep it inline and simple - no separate method calls initially
  - _Requirements: 1.1, 1.4_

- [x] 1.2 Extract and adapt POC height calculation
  - Copy the height calculation logic from poc_subplot_spacing.py
  - Calculate available_space = 1.0 - (num_rows - 1) * spacing
  - Allocate heights from available space (price 45%, oscillators 35%, volume 10%, P&L 10%)
  - Build heights list exactly as POC does
  - _Requirements: 2.1, 2.2, 2.4_

- [x] 1.3 Replace make_subplots call with POC version
  - Remove the current make_subplots call and all its complexity
  - Use the simple POC version: make_subplots(rows=num_rows, cols=1, row_heights=heights, vertical_spacing=spacing, subplot_titles=titles, shared_xaxes=True)
  - Remove the specs parameter that POC doesn't use
  - Remove complex error handling initially - keep it simple
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 1.4 Test the rewritten chart creation
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

- [x] 2.1 Add basic validation before make_subplots
  - Check that heights list is not empty
  - Check that spacing is positive
  - Log a warning if values look suspicious but proceed anyway
  - Only fail if values are clearly invalid (negative, NaN, etc.)
  - _Requirements: 2.5, 3.3_

- [x] 2.2 Add try-except around make_subplots
  - Wrap make_subplots in try-except
  - Log the exact configuration on error
  - Provide a simple fallback (2 rows: price + P&L)
  - _Requirements: 1.2, 1.3, 3.2_

- [x] 2.3 Add informational logging
  - Log spacing and heights at INFO level
  - Log total allocated space for verification
  - Keep logs concise and readable
  - _Requirements: 3.1_

- [x] 2.4 Test error handling
  - Run backtests with various configurations
  - Verify logging is helpful
  - Verify fallback works if needed
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [-] 3. Write integration tests
  - Create tests that verify charts render correctly with various configurations
  - Test 2-row, 4-row, and 6-row layouts
  - Verify spacing is appropriate for each
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 3.1 Write test for 2-row layout (price + P&L)
  - Generate chart with simple 2-row configuration
  - Verify chart renders successfully
  - Verify spacing is visible (0.12)
  - Save chart for manual inspection
  - _Requirements: 1.1, 1.2_

- [ ] 3.2 Write test for 4-row layout (price + MACD + volume + P&L)
  - Generate chart with MACD indicator
  - Verify all 4 subplots are clearly separated
  - Verify spacing is appropriate (0.08)
  - Save chart for manual inspection
  - _Requirements: 1.1, 1.2, 1.4_

- [ ] 3.3 Write test for 6-row layout (price + 3 oscillators + volume + P&L)
  - Generate chart with multiple oscillators
  - Verify all oscillators get equal space
  - Verify spacing is tighter but still visible (0.06)
  - Save chart for manual inspection
  - _Requirements: 1.1, 1.2, 1.4, 2.4_

- [ ] 3.4 Run integration tests and verify results
  - Execute all integration tests
  - Review generated charts visually
  - Verify spacing is correct in all cases
  - Compare with POC charts to confirm similarity
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 4. Update existing tests if needed
  - Review existing chart tests for compatibility
  - Update any tests that make assumptions about old layout
  - Ensure all tests pass with new implementation
  - _Requirements: All_

- [ ] 4.1 Check and update test_subplot_layout.py
  - Review tests for compatibility with new layout
  - Update any hardcoded spacing or height values if needed
  - Ensure tests pass
  - _Requirements: 2.1, 2.2_

- [ ] 4.2 Check and update test_macd_visualization.py
  - Ensure MACD chart tests work with new spacing
  - Update any assertions about subplot positions if needed
  - Ensure tests pass
  - _Requirements: 1.2, 1.4_

- [ ] 4.3 Run full test suite
  - Execute all chart-related tests
  - Fix any tests broken by the layout changes
  - Ensure 100% test pass rate
  - _Requirements: All_

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Documentation and cleanup
  - Add inline comments explaining the POC-based approach
  - Update docstrings for modified methods
  - Document the spacing formula
  - _Requirements: All_

- [ ] 6.1 Add inline comments to spacing calculation
  - Comment the spacing formula from POC
  - Explain why these specific values work
  - Reference the POC file
  - _Requirements: 2.1, 2.2_

- [ ] 6.2 Add inline comments to height calculation
  - Comment the available space calculation
  - Explain the height distribution percentages
  - Reference the POC file
  - _Requirements: 2.1, 2.2_

- [ ] 6.3 Update method docstring for create_comprehensive_chart
  - Document the POC-based approach
  - Explain the spacing and height calculation
  - Note that this fixes the overlap issue
  - _Requirements: All_

- [ ] 7. Final verification with multiple strategies
  - Run backtests with different strategies and configurations
  - Verify all charts have proper spacing
  - Test with different timeframes and symbols
  - Confirm the subplot overlap issue is completely resolved
  - _Requirements: All_

- [ ] 7.1 Test with MACD strategy
  - Run backtest with MACD on EURUSD 15m
  - Verify 4-row layout (price + MACD + volume + P&L) has proper spacing
  - Save chart for documentation
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 7.2 Test with multiple oscillators
  - Run backtest with strategy that has 3+ oscillators
  - Verify 6+ row layout has proper spacing
  - Verify all oscillators get equal space
  - Save chart for documentation
  - _Requirements: 1.1, 1.2, 1.4, 2.4_

- [ ] 7.3 Test with simple strategy (no oscillators)
  - Run backtest with strategy that has no oscillators
  - Verify 3-row layout (price + volume + P&L) has proper spacing
  - Save chart for documentation
  - _Requirements: 1.1, 1.2_

- [ ] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
