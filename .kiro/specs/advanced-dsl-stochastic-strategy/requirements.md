# Requirements Document

## Introduction

This specification covers two interconnected features:
1. **Advanced DSL Strategy System**: Enhance the DSL (Domain Specific Language) strategy system to support complex multi-indicator strategies with advanced logic
2. **Stochastic Quad Rotation Strategy**: Implement a sophisticated trading strategy using 4 stochastic oscillators with different periods

The current DSL system supports simple indicator crossover strategies (MA Crossover, MACD Crossover). This enhancement will enable complex strategies with multiple indicator instances, zone-based conditions, and state tracking.

## Glossary

- **DSL Strategy**: JSON-configured trading strategy that implements the TradingStrategy interface
- **Stochastic Oscillator**: Technical indicator measuring momentum using %K and %D lines (0-100 scale)
- **Rotation Signal**: When the fastest indicator crosses a threshold while all others are in an extreme zone
- **Zone Condition**: All indicators being above/below a specific threshold simultaneously
- **Indicator Instance**: A specific configuration of an indicator with unique parameters
- **Crossover**: When an indicator value crosses above or below a threshold level

## Requirements

### Requirement 1: Multi-Instance Indicator Support

**User Story:** As a strategy developer, I want to use multiple instances of the same indicator with different parameters, so that I can create multi-timeframe or multi-period strategies.

#### Acceptance Criteria

1. WHEN a DSL strategy specifies multiple instances of the same indicator type with different parameters THEN the system SHALL create and track each instance separately
2. WHEN calculating indicators THEN the system SHALL assign unique aliases to each instance for reference in conditions
3. WHEN accessing indicator values in conditions THEN the system SHALL correctly resolve the alias to the specific indicator instance
4. WHEN charting results THEN the system SHALL display all indicator instances with distinct visual styling

### Requirement 2: Complex Boolean Logic in Conditions

**User Story:** As a strategy developer, I want to combine multiple indicator conditions using AND/OR logic, so that I can create sophisticated entry rules.

#### Acceptance Criteria

1. WHEN a DSL strategy defines multiple conditions THEN the system SHALL support AND logic (all conditions must be true)
2. WHEN a DSL strategy defines multiple conditions THEN the system SHALL support OR logic (any condition can be true)
3. WHEN evaluating conditions THEN the system SHALL process them in the correct logical order
4. WHEN a condition fails THEN the system SHALL short-circuit evaluation for performance

### Requirement 3: Zone-Based Conditions

**User Story:** As a strategy developer, I want to check if indicators are within specific zones (above/below thresholds), so that I can identify overbought/oversold conditions.

#### Acceptance Criteria

1. WHEN a condition specifies a zone threshold THEN the system SHALL evaluate if the indicator is above, below, or within that zone
2. WHEN multiple indicators must be in a zone THEN the system SHALL verify all indicators meet the zone requirement
3. WHEN a zone condition is met THEN the system SHALL track this state for crossover detection
4. WHEN indicators exit a zone THEN the system SHALL update the zone state accordingly

### Requirement 4: Crossover Detection

**User Story:** As a strategy developer, I want to detect when an indicator crosses above or below a threshold, so that I can trigger signals at precise moments.

#### Acceptance Criteria

1. WHEN an indicator crosses above a threshold THEN the system SHALL detect the crossover event
2. WHEN an indicator crosses below a threshold THEN the system SHALL detect the crossover event
3. WHEN detecting crossovers THEN the system SHALL compare current and previous indicator values
4. WHEN a crossover occurs THEN the system SHALL only trigger once per crossover event
5. WHEN tracking crossovers THEN the system SHALL maintain state between candles

### Requirement 5: Stochastic Oscillator Indicator

**User Story:** As a strategy developer, I want to use Stochastic oscillators with configurable periods, so that I can implement momentum-based strategies.

#### Acceptance Criteria

1. WHEN calculating Stochastic THEN the system SHALL compute %K using (Close - LowestLow) / (HighestHigh - LowestLow) * 100
2. WHEN smoothing %K THEN the system SHALL apply SMA smoothing if k_smoothing > 1
3. WHEN calculating %D THEN the system SHALL compute SMA of %K values over d_smoothing period
4. WHEN charting Stochastic THEN the system SHALL display both %K and %D lines in a subplot with 0-100 range
5. WHEN charting Stochastic THEN the system SHALL show reference lines at 20, 50, and 80 levels

### Requirement 6: Stochastic Quad Rotation Strategy

**User Story:** As a trader, I want to trade rotation signals using 4 stochastic oscillators, so that I can identify high-probability reversal points.

#### Acceptance Criteria

1. WHEN the strategy initializes THEN the system SHALL create 4 stochastic instances: 9-1-3, 14-1-3, 40-1-4, 60-1-10
2. WHEN all 4 stochastics are below 20 AND the 9-1-3 crosses above 20 THEN the system SHALL generate a BUY signal
3. WHEN all 4 stochastics are above 80 AND the 9-1-3 crosses below 80 THEN the system SHALL generate a SELL signal
4. WHEN a signal is generated THEN the system SHALL use the current candle close price as entry price
5. WHEN tracking rotation state THEN the system SHALL maintain previous values for crossover detection

### Requirement 7: Multi-Stochastic Chart Visualization

**User Story:** As a trader, I want to see all 4 stochastic oscillators on the chart, so that I can visually verify the rotation signals.

#### Acceptance Criteria

1. WHEN charting the Quad Rotation strategy THEN the system SHALL display all 4 stochastics in a single subplot
2. WHEN displaying multiple stochastics THEN the system SHALL use distinct colors for each: fast (blue), med-fast (green), med-slow (orange), slow (red)
3. WHEN displaying the subplot THEN the system SHALL show reference lines at 20 and 80 levels
4. WHEN displaying the subplot THEN the system SHALL use 25% of chart height for the stochastic panel
5. WHEN hovering over lines THEN the system SHALL show tooltips identifying each stochastic instance

### Requirement 8: DSL Schema Extensions

**User Story:** As a system developer, I want the DSL schema to validate advanced strategy configurations, so that invalid strategies are rejected early.

#### Acceptance Criteria

1. WHEN validating a DSL strategy THEN the system SHALL accept indicator arrays with parameter specifications
2. WHEN validating conditions THEN the system SHALL accept zone specifications with thresholds
3. WHEN validating conditions THEN the system SHALL accept crossover specifications
4. WHEN validating conditions THEN the system SHALL accept boolean logic operators (AND/OR)
5. WHEN a strategy fails validation THEN the system SHALL provide clear error messages indicating the issue

### Requirement 9: Backward Compatibility

**User Story:** As a system maintainer, I want existing DSL strategies to continue working, so that we don't break current functionality.

#### Acceptance Criteria

1. WHEN loading existing DSL strategies (MA Crossover, MACD Crossover) THEN the system SHALL execute them without modification
2. WHEN processing simple crossover conditions THEN the system SHALL use the existing logic path
3. WHEN new features are not used THEN the system SHALL not add overhead to simple strategies
4. WHEN migrating to advanced features THEN the system SHALL provide clear documentation on the upgrade path

### Requirement 10: Performance Optimization

**User Story:** As a system user, I want complex strategies to execute efficiently, so that backtests complete in reasonable time.

#### Acceptance Criteria

1. WHEN calculating multiple indicator instances THEN the system SHALL reuse candle data across calculations
2. WHEN evaluating conditions THEN the system SHALL short-circuit boolean logic when possible
3. WHEN tracking state THEN the system SHALL use efficient data structures (not full history)
4. WHEN running backtests THEN the system SHALL complete 1000 candles in under 5 seconds
5. WHEN charting results THEN the system SHALL render all indicators without performance degradation
