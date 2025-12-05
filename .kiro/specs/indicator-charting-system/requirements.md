# Requirements Document

## Introduction

The indicator charting system enables proper visualization of different types of technical indicators in trading strategy backtests. Currently, all indicators are plotted on the price chart regardless of their value ranges, making oscillator indicators (like MACD with values ~0.001) unreadable when displayed alongside price data (values ~1.15). This system will automatically route indicators to appropriate chart locations based on their visualization requirements.

## Glossary

- **Chart Engine**: The component responsible for generating interactive HTML charts from backtest results
- **Indicator**: A mathematical calculation applied to price/volume data (e.g., MACD, SMA, RSI)
- **Overlay Indicator**: An indicator that shares the same scale as price data and should be plotted on the price chart (e.g., SMA, EMA, VWAP)
- **Oscillator Indicator**: An indicator with a different scale than price data that should be plotted in a separate subplot (e.g., MACD, RSI, Stochastic)
- **Stochastic Oscillator**: A momentum indicator that shows the location of the close relative to the high-low range, typically displayed with %K and %D lines and 20/80 reference levels
- **Subplot**: A separate chart panel with independent y-axis scaling
- **Indicator Metadata**: Configuration data that defines how an indicator should be visualized
- **DSL Strategy**: A trading strategy defined using the Domain-Specific Language JSON format

## Requirements

### Requirement 1

**User Story:** As a trader, I want oscillator indicators to display in separate subplots with appropriate scaling, so that I can read their values and analyze their signals effectively.

#### Acceptance Criteria

1. WHEN a strategy uses MACD THEN the Chart Engine SHALL display MACD in a separate subplot below the price chart
2. WHEN a strategy uses RSI THEN the Chart Engine SHALL display RSI in a separate subplot with 0-100 scale
3. WHEN a strategy uses Stochastic THEN the Chart Engine SHALL display Stochastic in a separate subplot with 0-100 scale
4. WHEN oscillator indicators are displayed THEN the Chart Engine SHALL apply auto-scaling based on the indicator's value range
5. WHEN multiple oscillator indicators are used THEN the Chart Engine SHALL display each in its own subplot
6. WHEN an oscillator subplot is rendered THEN the Chart Engine SHALL include a zero line for reference

### Requirement 2

**User Story:** As a trader, I want overlay indicators to continue displaying on the price chart, so that I can see their relationship to price movements directly.

#### Acceptance Criteria

1. WHEN a strategy uses SMA THEN the Chart Engine SHALL display SMA on the price chart
2. WHEN a strategy uses EMA THEN the Chart Engine SHALL display EMA on the price chart
3. WHEN a strategy uses VWAP THEN the Chart Engine SHALL display VWAP on the price chart
4. WHEN overlay indicators are displayed THEN the Chart Engine SHALL use the same y-axis scale as the price data
5. WHEN multiple overlay indicators are used THEN the Chart Engine SHALL display all of them on the price chart with distinct colors

### Requirement 3

**User Story:** As a developer, I want a centralized indicator metadata registry, so that I can define visualization requirements once and have them applied consistently across all charts.

#### Acceptance Criteria

1. WHEN an indicator is registered THEN the system SHALL store its visualization type (OVERLAY or OSCILLATOR)
2. WHEN an indicator is registered THEN the system SHALL store its scale configuration
3. WHEN an indicator is registered THEN the system SHALL store its visual styling properties
4. WHEN the Chart Engine needs indicator metadata THEN the system SHALL provide the metadata from the registry
5. WHEN a new indicator is added THEN the system SHALL require metadata registration before charting

### Requirement 4

**User Story:** As a developer, I want the Chart Engine to automatically route indicators to the correct subplot, so that I don't need to manually configure chart layouts for each strategy.

#### Acceptance Criteria

1. WHEN the Chart Engine receives indicator data THEN the system SHALL query the indicator metadata registry
2. WHEN an indicator has OVERLAY type THEN the Chart Engine SHALL add it to the price chart
3. WHEN an indicator has OSCILLATOR type THEN the Chart Engine SHALL create or use an oscillator subplot
4. WHEN routing indicators THEN the Chart Engine SHALL apply the correct y-axis scaling for each subplot
5. WHEN creating subplots THEN the Chart Engine SHALL maintain proper vertical spacing and sizing

### Requirement 5

**User Story:** As a trader, I want MACD indicators to display with their signal line and histogram, so that I can identify crossover signals and momentum changes.

#### Acceptance Criteria

1. WHEN MACD is displayed THEN the Chart Engine SHALL plot the MACD line in blue
2. WHEN MACD is displayed THEN the Chart Engine SHALL plot the signal line in red
3. WHEN MACD is displayed THEN the Chart Engine SHALL plot the histogram as bars
4. WHEN MACD is displayed THEN the Chart Engine SHALL include a zero line for reference
5. WHEN MACD values are calculated THEN the system SHALL include all three components (MACD, signal, histogram)

### Requirement 6

**User Story:** As a developer maintaining existing strategies, I want the charting system to remain backward compatible, so that existing MA Crossover and VWAP strategies continue to work without modifications.

#### Acceptance Criteria

1. WHEN an existing MA Crossover strategy is charted THEN the Chart Engine SHALL display SMA and EMA on the price chart as before
2. WHEN an existing VWAP strategy is charted THEN the Chart Engine SHALL display VWAP on the price chart as before
3. WHEN strategies without oscillator indicators are charted THEN the Chart Engine SHALL not create empty subplots
4. WHEN the Chart Engine is updated THEN all existing chart generation code paths SHALL continue to function
5. WHEN existing strategies are run THEN the system SHALL produce visually identical charts to previous versions

### Requirement 7

**User Story:** As a developer, I want indicator calculators to provide their own metadata, so that the charting configuration is co-located with the calculation logic.

#### Acceptance Criteria

1. WHEN an indicator calculator is implemented THEN the calculator SHALL provide a get_chart_config() method
2. WHEN get_chart_config() is called THEN the calculator SHALL return its visualization type
3. WHEN get_chart_config() is called THEN the calculator SHALL return its scale configuration
4. WHEN get_chart_config() is called THEN the calculator SHALL return its styling properties
5. WHEN the Chart Engine queries indicator metadata THEN the system SHALL use the calculator's get_chart_config() method

### Requirement 8

**User Story:** As a trader, I want RSI indicators to display with overbought and oversold reference lines, so that I can quickly identify extreme market conditions.

#### Acceptance Criteria

1. WHEN RSI is displayed THEN the Chart Engine SHALL use a fixed 0-100 y-axis scale
2. WHEN RSI is displayed THEN the Chart Engine SHALL draw a horizontal line at 70 labeled "Overbought"
3. WHEN RSI is displayed THEN the Chart Engine SHALL draw a horizontal line at 30 labeled "Oversold"
4. WHEN RSI is displayed THEN the Chart Engine SHALL use a distinct color from other indicators
5. WHEN RSI reference lines are drawn THEN the Chart Engine SHALL use dashed line style for clarity

### Requirement 9

**User Story:** As a trader, I want Stochastic oscillator to display with %K and %D lines and reference levels, so that I can identify overbought and oversold conditions and momentum changes.

#### Acceptance Criteria

1. WHEN Stochastic is displayed THEN the Chart Engine SHALL use a fixed 0-100 y-axis scale
2. WHEN Stochastic is displayed THEN the Chart Engine SHALL plot the %K line
3. WHEN Stochastic is displayed THEN the Chart Engine SHALL plot the %D line
4. WHEN Stochastic is displayed THEN the Chart Engine SHALL draw a horizontal line at 80 labeled "Overbought"
5. WHEN Stochastic is displayed THEN the Chart Engine SHALL draw a horizontal line at 20 labeled "Oversold"
