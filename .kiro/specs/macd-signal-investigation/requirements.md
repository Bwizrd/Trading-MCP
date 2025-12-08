# Requirements Document

## Introduction

The MACD Crossover Strategy is currently generating 0 trades despite visible MACD line and signal line crossovers being present on the generated charts. This investigation aims to identify why the strategy is not detecting these crossovers and generating trade signals as expected.

## Glossary

- **MACD (Moving Average Convergence Divergence)**: A trend-following momentum indicator that shows the relationship between two moving averages of a security's price
- **MACD Line**: The difference between the 12-period and 26-period exponential moving averages (EMA)
- **Signal Line**: A 9-period EMA of the MACD line
- **Crossover**: When the MACD line crosses above (bullish) or below (bearish) the signal line
- **DSL Strategy**: Domain-Specific Language strategy defined in JSON format
- **Signal Generation**: The process of detecting trading conditions and creating buy/sell signals
- **Backtest Engine**: The system that executes strategies against historical data

## Requirements

### Requirement 1

**User Story:** As a trader, I want the MACD Crossover Strategy to detect and generate trade signals when crossovers occur, so that I can backtest the strategy's performance.

#### Acceptance Criteria

1. WHEN the MACD line crosses above the signal line THEN the Strategy SHALL generate a BUY signal
2. WHEN the MACD line crosses below the signal line THEN the Strategy SHALL generate a SELL signal
3. WHEN a crossover occurs THEN the Strategy SHALL log the detection for debugging purposes
4. WHEN the backtest completes THEN the System SHALL report the number of signals generated
5. WHEN signals are generated THEN the System SHALL display them on the chart as markers

### Requirement 2

**User Story:** As a developer, I want to understand the signal generation logic, so that I can identify why crossovers are not being detected.

#### Acceptance Criteria

1. WHEN investigating the strategy THEN the System SHALL provide access to the DSL strategy configuration
2. WHEN the strategy executes THEN the System SHALL log the MACD and signal line values at each candle
3. WHEN comparing values THEN the System SHALL use appropriate numerical comparison logic
4. WHEN a potential crossover is detected THEN the System SHALL log the before and after values
5. WHEN debugging THEN the System SHALL provide visibility into the DSL interpreter's decision-making process

### Requirement 3

**User Story:** As a system maintainer, I want to verify the MACD calculation is correct, so that I can rule out indicator calculation errors.

#### Acceptance Criteria

1. WHEN MACD values are calculated THEN the System SHALL use the standard formula (EMA12 - EMA26)
2. WHEN the signal line is calculated THEN the System SHALL use a 9-period EMA of the MACD line
3. WHEN comparing calculated values to chart display THEN the System SHALL ensure consistency
4. WHEN MACD values are generated THEN the System SHALL handle NaN and null values appropriately
5. WHEN the calculation completes THEN the System SHALL validate that sufficient data points exist

### Requirement 4

**User Story:** As a quality assurance tester, I want test cases that verify crossover detection, so that I can ensure the strategy works correctly.

#### Acceptance Criteria

1. WHEN creating test data THEN the System SHALL generate synthetic MACD crossovers
2. WHEN running tests THEN the System SHALL verify that known crossovers are detected
3. WHEN a crossover is missed THEN the System SHALL report which crossover was not detected
4. WHEN tests pass THEN the System SHALL confirm the strategy logic is correct
5. WHEN tests fail THEN the System SHALL provide diagnostic information about the failure

### Requirement 5

**User Story:** As a developer, I want to compare the DSL strategy implementation with a direct Python implementation, so that I can identify discrepancies.

#### Acceptance Criteria

1. WHEN comparing implementations THEN the System SHALL run both DSL and Python versions on the same data
2. WHEN results differ THEN the System SHALL highlight the differences in signal generation
3. WHEN the DSL interpreter processes conditions THEN the System SHALL log each evaluation step
4. WHEN the comparison completes THEN the System SHALL report whether implementations match
5. WHEN discrepancies exist THEN the System SHALL identify the root cause (DSL parsing, condition evaluation, or data handling)
