# Design Document: Subplot Overlap Fix

## Overview

The current chart generation system has a critical visual defect where subplots overlap each other, making charts difficult to read. The root cause is an incorrect understanding of how Plotly's `make_subplots` function handles the relationship between `row_heights` and `vertical_spacing`.

**Key Issue:** The current implementation treats `row_heights` as absolute proportions that should sum to 1.0, but Plotly actually expects `row_heights` to define the relative proportions of the *available space after accounting for vertical spacing*. This mismatch causes subplots to overlap.

**Solution:** Implement a correct mathematical model for subplot layout that properly accounts for the interaction between row heights and vertical spacing, ensuring visual separation between all chart components.

## Architecture

### Current Architecture (Broken)

```
User Request → Backtest Engine → Chart Engine
                                      ↓
                                 _determine_subplot_layout()
                                      ↓
                                 _calculate_row_heights() [BROKEN]
                                      ↓
                                 make_subplots() [Receives incorrect heights]
                                      ↓
                                 Overlapping Chart ❌
```

### Fixed Architecture

```
User Request → Backtest Engine → Chart Engine
                                      ↓
                                 _determine_subplot_layout()
                                      ↓
                                 _calculate_vertical_spacing() [NEW]
                                      ↓
                                 _calculate_row_heights_with_spacing() [FIXED]
                                      ↓
                                 _validate_layout_math() [NEW]
                                      ↓
                                 make_subplots() [Receives correct heights]
                                      ↓
                                 Properly Spaced Chart ✅
```

## Components and Interfaces

### 1. Layout Calculator (Enhanced)

**Location:** `shared/chart_engine.py` - `ChartEngine` class

**Responsibilities:**
- Calculate appropriate vertical spacing based on number of rows
- Calculate row heights that account for vertical spacing
- Validate that layout mathematics are correct
- Provide fallback configurations if validation fails

**Key Methods:**

```python
def _calculate_vertical_spacing(self, num_rows: int) -> float:
    """
    Calculate appropriate vertical spacing based on number of rows.
    
    Returns spacing as a proportion of total figure height.
    More rows = less spacing per gap to fit everything.
    """
    pass

def _calculate_row_heights_with_spacing(
    self, 
    layout: Dict[str, int], 
    vertical_spacing: float
) -> List[float]:
    """
    Calculate row heights that properly account for vertical spacing.
    
    The key insight: if we have N rows and spacing S between each,
    then we have (N-1) gaps taking up (N-1)*S of the total height.
    The remaining (1 - (N-1)*S) is available for the actual rows.
    
    Returns list of proportions that sum to (1 - total_spacing).
    """
    pass

def _validate_layout_math(
    self,
    row_heights: List[float],
    vertical_spacing: float,
    num_rows: int
) -> Tuple[bool, Optional[str]]:
    """
    Validate that layout mathematics are correct.
    
    Checks:
    - Row heights sum to expected value
    - No negative or zero heights
    - Spacing is reasonable for number of rows
    - Total allocation doesn't exceed 1.0
    
    Returns (is_valid, error_message)
    """
    pass
```

### 2. Subplot Creator (Enhanced)

**Location:** `shared/chart_engine.py` - `create_comprehensive_chart()` method

**Responsibilities:**
- Use the layout calculator to get correct spacing and heights
- Create subplots with validated configuration
- Handle errors gracefully with fallback layouts
- Log all layout decisions for debugging

**Enhanced Error Handling:**
- Validate layout before creating subplots
- Catch Plotly errors and provide meaningful messages
- Fall back to simpler layouts if complex ones fail
- Log all configuration values for debugging

### 3. Visual Debugger (New)

**Location:** `shared/chart_engine.py` - `ChartEngine` class

**Responsibilities:**
- Optionally add visual indicators of subplot boundaries
- Display spacing measurements on the chart
- Help developers verify that spacing is correct

**Key Method:**

```python
def _add_debug_spacing_indicators(
    self,
    fig,
    layout: Dict[str, int],
    row_heights: List[float],
    vertical_spacing: float
):
    """
    Add visual debugging indicators to show subplot boundaries and spacing.
    
    Adds:
    - Colored rectangles showing spacing gaps
    - Text annotations with measurements
    - Boundary lines for each subplot
    
    Only enabled when debug mode is active.
    """
    pass
```

## Data Models

### LayoutConfiguration

```python
@dataclass
class LayoutConfiguration:
    """Complete configuration for subplot layout."""
    num_rows: int
    row_mapping: Dict[str, int]  # subplot_name -> row_number
    row_heights: List[float]     # Proportions for each row
    vertical_spacing: float      # Spacing between rows
    subplot_titles: List[str]    # Title for each row
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate that this configuration is mathematically correct."""
        # Check that row_heights sum correctly
        # Check that spacing is reasonable
        # Check that all values are positive
        pass
    
    def total_allocated_space(self) -> float:
        """Calculate total space allocated (heights + spacing)."""
        return sum(self.row_heights) + (self.num_rows - 1) * self.vertical_spacing
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Layout Space Conservation

*For any* valid layout configuration with N rows, the sum of row heights plus the total spacing must equal or be less than 1.0 (100% of figure height)

This property ensures that we never try to allocate more vertical space than is available in the figure. It combines the mathematical constraints from both row height calculation and spacing allocation.

**Mathematical Formula:**
```
sum(row_heights) + (N-1) * vertical_spacing ≤ 1.0
```

**Validates: Requirements 2.1, 2.2**

### Property 2: Positive Space Allocation

*For any* calculated row height in any layout configuration, the value must be strictly greater than zero

This ensures that every subplot gets some visible space and prevents degenerate layouts where a subplot has zero or negative height.

**Mathematical Formula:**
```
∀ height ∈ row_heights: height > 0
```

**Validates: Requirements 2.5**

### Property 3: Spacing Appropriateness

*For any* layout configuration with N rows where N ≥ 2, the vertical spacing must be positive and decrease or stay constant as N increases

This property ensures that spacing is always visible (positive) and that we use tighter spacing when we have more rows to fit in the same total height. It combines the requirements for visible spacing and dynamic adjustment.

**Mathematical Formula:**
```
∀ N ≥ 2: spacing(N) > 0
∀ N1, N2 where N1 < N2: spacing(N1) ≥ spacing(N2)
```

**Validates: Requirements 1.1, 1.4**

### Property 4: Subplot Domain Non-Overlap

*For any* two consecutive subplots at rows R1 and R2 where R1 < R2, when we calculate their y-axis domains from the row heights and spacing, the domains must not overlap

This is the core property that prevents the visual overlap issue. It ensures that the bottom boundary of the upper subplot is strictly above the top boundary of the lower subplot, with the spacing gap between them.

**Mathematical Formula:**
```
∀ consecutive rows R1, R2 where R1 < R2:
  domain_bottom(R1) > domain_top(R2) + spacing
```

**Validates: Requirements 1.2, 1.3, 2.3**

### Property 5: Equal Oscillator Space Distribution

*For any* layout configuration containing N oscillators where N ≥ 1, each oscillator subplot must receive equal height allocation from the total oscillator space

This ensures fair distribution of space among multiple oscillators and maintains visual consistency when comparing different oscillator indicators.

**Mathematical Formula:**
```
∀ oscillators O1, O2 in same layout:
  height(O1) = height(O2) = total_oscillator_space / num_oscillators
```

**Validates: Requirements 2.4**

## Error Handling

### Layout Calculation Errors

**Error:** Row heights sum to more than available space
**Handling:** 
- Log error with actual sum and expected value
- Fall back to equal distribution of available space
- Reduce spacing if necessary

**Error:** Negative or zero row height calculated
**Handling:**
- Log error with problematic configuration
- Fall back to minimum viable heights (5% per row)
- Warn user that chart may be cramped

### Plotly Subplot Creation Errors

**Error:** `make_subplots` raises ValueError
**Handling:**
- Log the exact configuration that failed
- Try fallback configuration (2 rows: price + P&L)
- If fallback fails, raise RuntimeError with diagnostic info

### Validation Errors

**Error:** Layout validation fails before subplot creation
**Handling:**
- Log validation failure details
- Attempt automatic correction (adjust spacing/heights)
- If correction fails, use fallback layout
- Never proceed with invalid configuration

## Testing Strategy

### Unit Tests

**Test:** `test_vertical_spacing_calculation`
- Verify spacing decreases as row count increases
- Verify spacing is always positive
- Verify spacing is reasonable (not too small or too large)

**Test:** `test_row_heights_sum_correctly`
- For 2, 3, 4, 5 row layouts
- Verify sum(heights) + (N-1)*spacing ≤ 1.0
- Verify each individual height > 0

**Test:** `test_layout_validation`
- Test with valid configurations (should pass)
- Test with invalid configurations (should fail with clear message)
- Test edge cases (1 row, 10 rows, etc.)

**Test:** `test_fallback_layouts`
- Verify fallback is triggered when validation fails
- Verify fallback configuration is always valid
- Verify fallback is logged appropriately

### Property-Based Tests

**Property Test:** `test_space_conservation_property`
- Generate random layout configurations (2-10 rows)
- For each configuration, verify Property 1 (space conservation)
- Run 100+ iterations with different random configurations

**Property Test:** `test_positive_heights_property`
- Generate random layout configurations
- For each configuration, verify Property 2 (all heights > 0)
- Run 100+ iterations

**Property Test:** `test_spacing_monotonicity_property`
- Generate pairs of configurations with different row counts
- Verify Property 3 (spacing decreases with more rows)
- Run 100+ iterations

**Property Test:** `test_domain_non_overlap_property`
- Generate random layout configurations
- Calculate subplot domains from heights and spacing
- Verify Property 4 (no overlap between consecutive subplots)
- Run 100+ iterations

### Integration Tests

**Test:** `test_chart_generation_with_multiple_layouts`
- Generate charts with 2, 3, 4, 5 subplot configurations
- Verify all charts render without errors
- Verify visual inspection shows proper spacing
- Save charts for manual review

**Test:** `test_macd_chart_spacing`
- Generate chart with price + MACD + volume + P&L (4 rows)
- Verify MACD subplot is clearly separated from price and volume
- Verify all components are visible

**Test:** `test_multiple_oscillators_spacing`
- Generate chart with price + 3 oscillators + volume + P&L (6 rows)
- Verify all oscillators are clearly separated
- Verify spacing is consistent between all subplots

## Implementation Notes

### Key Mathematical Insight

The critical insight is understanding how Plotly interprets `row_heights` and `vertical_spacing`:

```python
# WRONG (current implementation):
# Assumes row_heights should sum to 1.0
row_heights = [0.45, 0.35, 0.10, 0.10]  # Sums to 1.0
vertical_spacing = 0.08
# Result: Overlapping subplots because spacing isn't accounted for

# CORRECT (fixed implementation):
# row_heights should sum to (1.0 - total_spacing)
num_rows = 4
total_spacing = (num_rows - 1) * vertical_spacing  # 3 * 0.08 = 0.24
available_space = 1.0 - total_spacing  # 0.76
row_heights = [0.45, 0.20, 0.06, 0.05]  # Sums to 0.76
# Result: Properly spaced subplots
```

### Spacing Guidelines

Based on analysis of the current code and visual requirements:

- **2 rows:** 0.12 (12% spacing) - generous spacing for simple layouts
- **3 rows:** 0.10 (10% spacing) - comfortable spacing
- **4 rows:** 0.08 (8% spacing) - balanced spacing
- **5+ rows:** 0.06 (6% spacing) - tighter but still visible

These values should be configurable and validated to ensure they don't consume too much space.

### Height Allocation Strategy

Current strategy (to be preserved):
- **Price chart:** 45% when oscillators present, 80% when no oscillators
- **Oscillators:** 35% total (divided equally among all oscillators)
- **Volume:** 10%
- **P&L:** 10%

These percentages should be applied to the *available space* after accounting for spacing.

## Dependencies

- **Plotly:** Version 5.x for subplot creation
- **Python:** 3.8+ for type hints and dataclasses
- **Logging:** Standard library for diagnostic output
- **Pytest:** For unit and property-based testing
- **Hypothesis:** For property-based test generation (recommended)

## Migration Strategy

1. **Phase 1:** Implement new calculation methods alongside existing ones
2. **Phase 2:** Add validation and logging
3. **Phase 3:** Switch to new methods with fallback to old methods
4. **Phase 4:** Remove old methods after validation period
5. **Phase 5:** Add visual debugging features

This phased approach ensures we can roll back if issues are discovered.
