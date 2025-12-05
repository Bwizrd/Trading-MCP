# Implementation Plan

- [x] 1. Create indicator metadata infrastructure
  - Create `shared/indicators_metadata.py` with IndicatorType, ScaleType, ReferenceLine, ComponentStyle, and IndicatorMetadata dataclasses
  - Implement IndicatorMetadataRegistry with registration and retrieval methods
  - Register metadata for MACD, RSI, Stochastic, SMA, EMA, and VWAP
  - Implement base name extraction logic for indicator variations (SMA20 → SMA)
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ]* 1.1 Write property test for metadata registry
  - **Property 8: Registered metadata is retrievable**
  - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

- [ ]* 1.2 Write property test for base name extraction
  - **Property 9: Base name extraction is consistent**
  - **Validates: Requirements 3.4**

- [x] 2. Add metadata methods to indicator calculators
  - Add `get_chart_config()` method to MACDCalculator returning MACD metadata
  - Add `get_chart_config()` method to RSICalculator returning RSI metadata
  - Add `get_chart_config()` method to SMACalculator returning SMA metadata
  - Add `get_chart_config()` method to EMACalculator returning EMA metadata
  - Add `get_chart_config()` method to VWAPCalculator returning VWAP metadata
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ]* 2.1 Write property test for calculator metadata consistency
  - **Property 10: Calculator metadata matches registry**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

- [x] 3. Implement subplot layout determination
  - Add `_determine_subplot_layout()` method to ChartEngine that analyzes indicators and returns subplot mapping
  - Add `_calculate_row_heights()` method that allocates vertical space (50% price, 30% oscillators, 10% volume, 10% P&L)
  - Add `_generate_subplot_titles()` method that creates titles for each subplot
  - Add helper method `_get_oscillator_index()` to map oscillators to subplot indices
  - _Requirements: 4.1, 4.5_

- [ ]* 3.1 Write property test for subplot layout
  - **Property 3: Multiple oscillators get distinct subplots**
  - **Validates: Requirements 1.5**

- [ ]* 3.2 Write property test for row heights
  - **Property 17: Subplot heights sum to 1.0**
  - **Validates: Requirements 4.5**

- [ ]* 3.3 Write property test for price chart prominence
  - **Property 18: Price chart maintains prominence**
  - **Validates: Requirements 4.5**

- [x] 4. Implement indicator routing logic
  - Add `_route_indicator_to_subplot()` method that queries metadata and routes to correct subplot
  - Add `_add_oscillator_trace()` method that adds oscillator with proper styling
  - Update `_add_indicators()` method to use routing logic instead of always adding to price chart
  - Add logic to render reference lines (zero line, overbought/oversold)
  - Add logic to apply y-axis scaling based on metadata (FIXED, AUTO, PRICE)
  - _Requirements: 4.2, 4.3, 4.4_

- [ ]* 4.1 Write property test for oscillator routing
  - **Property 1: Oscillators route to separate subplots**
  - **Validates: Requirements 1.1, 1.2, 1.3, 4.3**

- [ ]* 4.2 Write property test for overlay routing
  - **Property 2: Overlays route to price chart**
  - **Validates: Requirements 2.1, 2.2, 2.3, 4.2**

- [ ]* 4.3 Write property test for no empty subplots
  - **Property 4: No empty subplots**
  - **Validates: Requirements 6.3**

- [x] 5. Implement scaling logic
  - Add logic to apply FIXED scale (set y-axis range to [scale_min, scale_max])
  - Add logic to apply AUTO scale (calculate range from indicator values with padding)
  - Add logic to apply PRICE scale (share y-axis with price chart)
  - Update `_add_oscillator_trace()` to apply correct scale type
  - _Requirements: 1.2, 1.3, 1.4, 2.4, 4.4_

- [ ]* 5.1 Write property test for fixed scale
  - **Property 5: Fixed scale indicators use specified range**
  - **Validates: Requirements 1.2, 1.3, 8.1, 9.1, 4.4**

- [ ]* 5.2 Write property test for auto scale
  - **Property 6: Auto-scale indicators encompass all values**
  - **Validates: Requirements 1.4, 4.4**

- [ ]* 5.3 Write property test for price scale
  - **Property 7: Overlay indicators share price scale**
  - **Validates: Requirements 2.4**

- [x] 6. Implement MACD-specific visualization
  - Update `_add_oscillator_trace()` to handle MACD's three components (line, signal, histogram)
  - Add logic to render MACD line in blue
  - Add logic to render signal line in red
  - Add logic to render histogram as bars in gray
  - Add zero line to MACD subplot
  - Ensure MACDCalculator provides access to signal line and histogram via get_signal_line() and get_histogram()
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 6.1 Write property test for MACD components
  - **Property 11: MACD components have correct styling**
  - **Validates: Requirements 5.1, 5.2, 5.3**

- [ ]* 6.2 Write property test for MACD zero line
  - **Property 12: Zero line appears for oscillators**
  - **Validates: Requirements 1.6, 5.4**

- [ ]* 6.3 Write property test for MACD calculator completeness
  - **Property 15: MACD calculator returns all components**
  - **Validates: Requirements 5.5**

- [ ] 7. Implement RSI-specific visualization
  - Add logic to render RSI with fixed 0-100 scale
  - Add horizontal reference line at y=70 labeled "Overbought" in red
  - Add horizontal reference line at y=30 labeled "Oversold" in green
  - Use dashed line style for reference lines
  - Use purple color for RSI line
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 7.1 Write property test for RSI reference lines
  - **Property 13: Reference lines appear at correct positions**
  - **Validates: Requirements 8.2, 8.3, 8.5**

- [ ] 8. Implement Stochastic-specific visualization
  - Add logic to render Stochastic with fixed 0-100 scale
  - Add logic to render %K line in blue
  - Add logic to render %D line in orange with dashed style
  - Add horizontal reference line at y=80 labeled "Overbought"
  - Add horizontal reference line at y=20 labeled "Oversold"
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ]* 8.1 Write property test for multi-line indicators
  - **Property 16: Multi-line indicators render all lines**
  - **Validates: Requirements 9.2, 9.3**

- [x] 9. Update create_comprehensive_chart() method
  - Replace fixed 3-row layout with dynamic layout based on indicators
  - Call `_determine_subplot_layout()` to get subplot mapping
  - Call `_calculate_row_heights()` to get row height proportions
  - Pass layout to make_subplots() with correct row count
  - Update all subplot references to use layout dictionary (layout["price"], layout["oscillator_1"], etc.)
  - Improve `_generate_subplot_titles()` to show indicator names for oscillator subplots (e.g., "MACD", "Stochastic (14,3,3)" instead of generic "Oscillator 1", "Oscillator 2")
  - Store mapping of oscillator index to indicator name in `_determine_subplot_layout()` for title generation
  - Handle multiple instances of same oscillator type (e.g., 4 Stochastics with different parameters each get their own subplot with descriptive title)
  - Maintain backward compatibility by handling cases with no indicators
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 2.1, 2.2, 2.3_

- [x] 10. Add error handling and fallback behavior
  - Add try-catch around metadata lookup with fallback to OVERLAY type
  - Add logging for missing metadata warnings
  - Add validation for metadata on registration
  - Add try-catch around subplot creation with fallback to simple 2-row layout
  - Add length checking for indicator data vs candle data
  - _Requirements: Design - Error Handling section_

- [ ]* 10.1 Write unit tests for error handling
  - Test missing metadata fallback
  - Test invalid metadata validation
  - Test subplot creation failure recovery
  - Test indicator data mismatch handling

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Test with MACD Crossover strategy
  - Run backtest for MACD Crossover strategy on EURUSD
  - Generate chart and verify MACD appears in separate subplot
  - Verify MACD line is blue, signal line is red, histogram is bars
  - Verify zero line is present
  - Verify price chart is unaffected
  - _Requirements: 1.1, 5.1, 5.2, 5.3, 5.4_

- [ ] 13. Test backward compatibility with MA Crossover
  - Run backtest for MA Crossover strategy on EURUSD
  - Generate chart and verify SMA and EMA appear on price chart
  - Compare with previous chart version to ensure no visual regressions
  - Verify no empty subplots are created
  - _Requirements: 6.1, 6.3_

- [ ]* 13.1 Write property test for distinct overlay colors
  - **Property 14: Multiple overlays have distinct colors**
  - **Validates: Requirements 2.5, 8.4**

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
