# Requirements Document

## Introduction

The backtest chart generation system currently produces charts with overlapping subplots when displaying multiple indicators (price, oscillators like MACD, volume, and P&L). The subplots visually overlap each other, making the charts difficult to read and unprofessional. This feature aims to fix the subplot spacing and layout calculations to ensure proper visual separation between all chart components.

## Glossary

- **Chart Engine**: The visualization component (`shared/chart_engine.py`) that creates interactive HTML charts from backtest results
- **Subplot**: A distinct chart panel within the overall figure (e.g., price chart, MACD oscillator, volume, P&L)
- **Vertical Spacing**: The gap between consecutive subplots, expressed as a proportion of the total figure height
- **Row Heights**: The proportional allocation of vertical space to each subplot row
- **Plotly**: The Python charting library used to create the interactive charts
- **Oscillator**: A technical indicator displayed in its own subplot with a different scale than price (e.g., MACD, RSI, Stochastic)
- **Overlay**: A technical indicator displayed on the price chart using the same scale (e.g., SMA, EMA, VWAP)

## Requirements

### Requirement 1

**User Story:** As a trader, I want to view backtest charts with clearly separated subplots, so that I can analyze price action, indicators, volume, and P&L without visual confusion.

#### Acceptance Criteria

1. WHEN a chart contains multiple subplots (price, oscillators, volume, P&L) THEN the Chart Engine SHALL render each subplot with visible spacing between them
2. WHEN subplots are rendered THEN the Chart Engine SHALL prevent any visual overlap between consecutive subplot panels
3. WHEN a chart is displayed THEN the Chart Engine SHALL ensure all subplot content (candlesticks, indicators, axes, labels) remains fully visible within its designated area
4. WHEN the number of subplots changes (2 to 5+ rows) THEN the Chart Engine SHALL dynamically adjust spacing to maintain visual separation
5. WHEN a user views the chart THEN the Chart Engine SHALL provide sufficient whitespace between subplots for comfortable visual scanning

### Requirement 2

**User Story:** As a developer, I want the subplot layout calculation to be mathematically correct, so that the spacing and heights are properly allocated across all chart components.

#### Acceptance Criteria

1. WHEN calculating row heights THEN the Chart Engine SHALL ensure the sum of all row height proportions equals 1.0
2. WHEN calculating vertical spacing THEN the Chart Engine SHALL account for the spacing in the total height allocation
3. WHEN determining subplot positions THEN the Chart Engine SHALL use Plotly's domain-based positioning system correctly
4. WHEN multiple oscillators are present THEN the Chart Engine SHALL allocate equal space to each oscillator subplot
5. WHEN row heights are calculated THEN the Chart Engine SHALL validate that no individual row height is negative or zero

### Requirement 3

**User Story:** As a system maintainer, I want clear logging and error handling for layout calculations, so that I can diagnose and fix spacing issues quickly.

#### Acceptance Criteria

1. WHEN layout calculations are performed THEN the Chart Engine SHALL log the calculated row heights and vertical spacing values
2. WHEN subplot creation fails THEN the Chart Engine SHALL log detailed error information including the attempted configuration
3. WHEN spacing validation detects issues THEN the Chart Engine SHALL log warnings with specific details about the problem
4. WHEN fallback layouts are used THEN the Chart Engine SHALL log the reason for falling back and the fallback configuration
5. WHEN debugging is enabled THEN the Chart Engine SHALL provide visual indicators of subplot boundaries and spacing

### Requirement 4

**User Story:** As a quality assurance tester, I want automated tests that verify subplot spacing, so that regressions can be caught before deployment.

#### Acceptance Criteria

1. WHEN tests are executed THEN the system SHALL verify that row heights sum to 1.0 for all layout configurations
2. WHEN tests are executed THEN the system SHALL verify that vertical spacing is appropriate for the number of rows
3. WHEN tests are executed THEN the system SHALL verify that subplot domains do not overlap
4. WHEN tests are executed THEN the system SHALL verify that all subplots are visible in the rendered chart
5. WHEN tests are executed THEN the system SHALL verify that the chart renders successfully with 2, 3, 4, and 5+ subplot configurations
