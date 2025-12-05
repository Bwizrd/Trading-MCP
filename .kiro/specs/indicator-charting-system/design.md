# Design Document

## Overview

The indicator charting system provides automatic visualization routing for technical indicators based on their characteristics. The system introduces a metadata registry that defines how each indicator should be displayed (overlay on price chart vs. separate subplot), enabling proper scaling and readability for all indicator types.

The core innovation is separating visualization concerns from calculation logic while maintaining backward compatibility with existing strategies. The Chart Engine becomes self-configuring by querying indicator metadata to determine subplot placement and styling.

## Architecture

### Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    Chart Engine                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Subplot Manager                                        │ │
│  │  - Creates price chart (row 1)                         │ │
│  │  - Creates oscillator subplots (rows 2+)               │ │
│  │  - Manages vertical spacing and sizing                 │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Indicator Router                                       │ │
│  │  - Queries indicator metadata                          │ │
│  │  - Routes OVERLAY → price chart                        │ │
│  │  - Routes OSCILLATOR → oscillator subplot              │ │
│  │  - Applies appropriate scaling                         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Indicator Metadata Registry                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Metadata Store                                         │ │
│  │  - MACD: OSCILLATOR, auto-scale, zero line            │ │
│  │  - RSI: OSCILLATOR, 0-100 scale, 30/70 lines          │ │
│  │  - Stochastic: OSCILLATOR, 0-100 scale, 20/80 lines   │ │
│  │  - SMA/EMA: OVERLAY, price scale                      │ │
│  │  - VWAP: OVERLAY, price scale                         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│              Indicator Calculators                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  MACDCalculator                                         │ │
│  │  - calculate() → MACD values                           │ │
│  │  - get_chart_config() → metadata                       │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  RSICalculator, SMACalculator, etc.                    │ │
│  │  - calculate() → indicator values                      │ │
│  │  - get_chart_config() → metadata                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Backtest Execution**: Strategy runs and calculates indicators
2. **Chart Generation Request**: Chart Engine receives candles, trades, and indicators
3. **Metadata Query**: Chart Engine queries metadata for each indicator
4. **Subplot Creation**: Chart Engine creates appropriate subplots based on metadata
5. **Indicator Routing**: Each indicator is routed to its designated subplot
6. **Rendering**: Chart is rendered with proper scaling and styling

## Components and Interfaces

### 1. Indicator Metadata Registry (`shared/indicators_metadata.py`)

```python
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

class IndicatorType(Enum):
    """Types of indicators based on visualization requirements."""
    OVERLAY = "overlay"      # Plot on price chart (same scale)
    OSCILLATOR = "oscillator"  # Plot in separate subplot (different scale)
    VOLUME = "volume"        # Plot in volume subplot

class ScaleType(Enum):
    """Y-axis scaling strategies."""
    AUTO = "auto"           # Auto-scale based on values
    FIXED = "fixed"         # Fixed min/max range
    PRICE = "price"         # Use same scale as price

@dataclass
class ReferenceLine:
    """Configuration for horizontal reference lines."""
    value: float
    color: str
    label: str
    style: str = "dash"  # solid, dash, dot

@dataclass
class ComponentStyle:
    """Styling for indicator components (lines, histograms)."""
    color: str
    label: str
    line_type: str = "line"  # line, bar, area
    width: float = 2.0
    dash: Optional[str] = None  # None, dash, dot

@dataclass
class IndicatorMetadata:
    """Complete metadata for an indicator's visualization."""
    name: str
    indicator_type: IndicatorType
    scale_type: ScaleType
    scale_min: Optional[float] = None
    scale_max: Optional[float] = None
    zero_line: bool = False
    reference_lines: List[ReferenceLine] = None
    components: Dict[str, ComponentStyle] = None
    
    def __post_init__(self):
        if self.reference_lines is None:
            self.reference_lines = []
        if self.components is None:
            self.components = {}

class IndicatorMetadataRegistry:
    """Central registry for indicator visualization metadata."""
    
    def __init__(self):
        self._metadata: Dict[str, IndicatorMetadata] = {}
        self._register_default_metadata()
    
    def _register_default_metadata(self):
        """Register metadata for all built-in indicators."""
        # MACD - Oscillator with zero line
        self.register(IndicatorMetadata(
            name="MACD",
            indicator_type=IndicatorType.OSCILLATOR,
            scale_type=ScaleType.AUTO,
            zero_line=True,
            components={
                "macd": ComponentStyle(color="#2196F3", label="MACD", width=2.5),
                "signal": ComponentStyle(color="#FF5722", label="Signal", width=2.0),
                "histogram": ComponentStyle(color="#9E9E9E", label="Histogram", line_type="bar")
            }
        ))
        
        # RSI - Oscillator with 0-100 scale and overbought/oversold lines
        self.register(IndicatorMetadata(
            name="RSI",
            indicator_type=IndicatorType.OSCILLATOR,
            scale_type=ScaleType.FIXED,
            scale_min=0,
            scale_max=100,
            reference_lines=[
                ReferenceLine(value=70, color="#F44336", label="Overbought"),
                ReferenceLine(value=30, color="#4CAF50", label="Oversold")
            ],
            components={
                "rsi": ComponentStyle(color="#9C27B0", label="RSI", width=2.5)
            }
        ))
        
        # Stochastic - Oscillator with 0-100 scale and 20/80 lines
        self.register(IndicatorMetadata(
            name="Stochastic",
            indicator_type=IndicatorType.OSCILLATOR,
            scale_type=ScaleType.FIXED,
            scale_min=0,
            scale_max=100,
            reference_lines=[
                ReferenceLine(value=80, color="#F44336", label="Overbought"),
                ReferenceLine(value=20, color="#4CAF50", label="Oversold")
            ],
            components={
                "k": ComponentStyle(color="#2196F3", label="%K", width=2.5),
                "d": ComponentStyle(color="#FF9800", label="%D", width=2.0, dash="dash")
            }
        ))
        
        # SMA - Overlay on price chart
        self.register(IndicatorMetadata(
            name="SMA",
            indicator_type=IndicatorType.OVERLAY,
            scale_type=ScaleType.PRICE,
            components={
                "sma": ComponentStyle(color="#2196F3", label="SMA", width=2.0)
            }
        ))
        
        # EMA - Overlay on price chart
        self.register(IndicatorMetadata(
            name="EMA",
            indicator_type=IndicatorType.OVERLAY,
            scale_type=ScaleType.PRICE,
            components={
                "ema": ComponentStyle(color="#FF9800", label="EMA", width=2.0)
            }
        ))
        
        # VWAP - Overlay on price chart
        self.register(IndicatorMetadata(
            name="VWAP",
            indicator_type=IndicatorType.OVERLAY,
            scale_type=ScaleType.PRICE,
            components={
                "vwap": ComponentStyle(color="#FF9800", label="VWAP", width=2.5)
            }
        ))
    
    def register(self, metadata: IndicatorMetadata):
        """Register metadata for an indicator."""
        self._metadata[metadata.name] = metadata
    
    def get(self, indicator_name: str) -> Optional[IndicatorMetadata]:
        """Get metadata for an indicator by name."""
        # Handle variations like "SMA20", "SMA50" → "SMA"
        base_name = self._extract_base_name(indicator_name)
        return self._metadata.get(base_name)
    
    def _extract_base_name(self, indicator_name: str) -> str:
        """Extract base indicator name from variations like SMA20 → SMA."""
        # Remove numbers and underscores to get base name
        import re
        base = re.sub(r'\d+', '', indicator_name)
        base = re.sub(r'_.*', '', base)
        return base.upper()
    
    def is_oscillator(self, indicator_name: str) -> bool:
        """Check if indicator is an oscillator."""
        metadata = self.get(indicator_name)
        return metadata and metadata.indicator_type == IndicatorType.OSCILLATOR
    
    def is_overlay(self, indicator_name: str) -> bool:
        """Check if indicator is an overlay."""
        metadata = self.get(indicator_name)
        return metadata and metadata.indicator_type == IndicatorType.OVERLAY

# Global registry instance
metadata_registry = IndicatorMetadataRegistry()
```

### 2. Indicator Calculator Updates (`shared/indicators.py`)

Add `get_chart_config()` method to each calculator:

```python
class MACDCalculator(IndicatorCalculator):
    # ... existing code ...
    
    def get_chart_config(self) -> IndicatorMetadata:
        """Return chart configuration metadata."""
        from shared.indicators_metadata import metadata_registry
        return metadata_registry.get("MACD")

class RSICalculator(IndicatorCalculator):
    # ... existing code ...
    
    def get_chart_config(self) -> IndicatorMetadata:
        """Return chart configuration metadata."""
        from shared.indicators_metadata import metadata_registry
        return metadata_registry.get("RSI")

# Similar for SMACalculator, EMACalculator, VWAPCalculator, etc.
```

### 3. Chart Engine Updates (`shared/chart_engine.py`)

#### New Methods

```python
class ChartEngine:
    def _determine_subplot_layout(self, indicators: Dict[str, List[float]]) -> Dict[str, int]:
        """
        Determine subplot layout based on indicator types.
        
        Returns:
            Dict mapping subplot names to row numbers
            Example: {"price": 1, "oscillator_1": 2, "oscillator_2": 3, "volume": 4}
        """
        from shared.indicators_metadata import metadata_registry
        
        layout = {"price": 1}
        current_row = 2
        
        # Check for oscillators
        oscillator_count = 0
        for indicator_name in indicators.keys():
            if metadata_registry.is_oscillator(indicator_name):
                oscillator_count += 1
                layout[f"oscillator_{oscillator_count}"] = current_row
                current_row += 1
        
        # Add volume subplot if needed
        layout["volume"] = current_row
        current_row += 1
        
        # Add P&L subplot
        layout["pnl"] = current_row
        
        return layout
    
    def _calculate_row_heights(self, layout: Dict[str, int]) -> List[float]:
        """
        Calculate proportional heights for each subplot row.
        
        Price chart gets 50%, oscillators share 30%, volume 10%, P&L 10%.
        """
        total_rows = max(layout.values())
        oscillator_rows = [k for k in layout.keys() if k.startswith("oscillator_")]
        
        heights = []
        for row in range(1, total_rows + 1):
            if row == layout["price"]:
                heights.append(0.5)  # 50% for price
            elif any(layout[osc] == row for osc in oscillator_rows):
                # Divide 30% among oscillators
                heights.append(0.3 / len(oscillator_rows))
            elif row == layout.get("volume"):
                heights.append(0.1)  # 10% for volume
            elif row == layout.get("pnl"):
                heights.append(0.1)  # 10% for P&L
        
        return heights
    
    def _route_indicator_to_subplot(
        self,
        fig,
        indicator_name: str,
        values: List[float],
        timestamps: List[datetime],
        layout: Dict[str, int]
    ):
        """
        Route indicator to appropriate subplot based on metadata.
        """
        from shared.indicators_metadata import metadata_registry
        
        metadata = metadata_registry.get(indicator_name)
        
        if not metadata:
            # Fallback: assume overlay
            self._add_indicator_trace(fig, indicator_name, values, timestamps, layout["price"])
            return
        
        if metadata.indicator_type == IndicatorType.OVERLAY:
            # Add to price chart
            self._add_indicator_trace(fig, indicator_name, values, timestamps, layout["price"])
        
        elif metadata.indicator_type == IndicatorType.OSCILLATOR:
            # Find which oscillator subplot to use
            oscillator_index = self._get_oscillator_index(indicator_name, layout)
            row = layout[f"oscillator_{oscillator_index}"]
            
            # Add indicator trace
            self._add_oscillator_trace(fig, indicator_name, values, timestamps, row, metadata)
            
            # Add reference lines (zero line, overbought/oversold)
            if metadata.zero_line:
                fig.add_hline(y=0, line_dash="dash", line_color="gray", row=row, col=1)
            
            for ref_line in metadata.reference_lines:
                fig.add_hline(
                    y=ref_line.value,
                    line_dash=ref_line.style,
                    line_color=ref_line.color,
                    annotation_text=ref_line.label,
                    row=row,
                    col=1
                )
    
    def _add_oscillator_trace(
        self,
        fig,
        indicator_name: str,
        values: List[float],
        timestamps: List[datetime],
        row: int,
        metadata: IndicatorMetadata
    ):
        """Add oscillator indicator with proper styling."""
        # Get component style
        component_key = list(metadata.components.keys())[0] if metadata.components else "default"
        style = metadata.components.get(component_key, ComponentStyle(color="#2196F3", label=indicator_name))
        
        if style.line_type == "bar":
            fig.add_trace(
                go.Bar(
                    x=timestamps,
                    y=values,
                    name=style.label,
                    marker_color=style.color
                ),
                row=row, col=1
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=values,
                    mode='lines',
                    name=style.label,
                    line=dict(color=style.color, width=style.width, dash=style.dash)
                ),
                row=row, col=1
            )
        
        # Set y-axis range if fixed scale
        if metadata.scale_type == ScaleType.FIXED:
            fig.update_yaxes(
                range=[metadata.scale_min, metadata.scale_max],
                row=row,
                col=1
            )
```

#### Modified Methods

Update `create_comprehensive_chart()` to use new subplot system:

```python
def create_comprehensive_chart(
    self,
    candles: List[Candle],
    backtest_results: BacktestResults,
    indicators: Dict[str, List[float]] = None,
    title: str = "Trading Strategy Results"
) -> str:
    """Create comprehensive chart with automatic subplot routing."""
    
    # Determine subplot layout based on indicators
    layout = self._determine_subplot_layout(indicators or {})
    row_heights = self._calculate_row_heights(layout)
    
    # Create subplots with dynamic layout
    total_rows = max(layout.values())
    subplot_titles = self._generate_subplot_titles(layout, title)
    
    fig = make_subplots(
        rows=total_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=subplot_titles,
        row_heights=row_heights
    )
    
    # Add candlestick chart
    self._add_candlestick_chart(fig, df, row=layout["price"])
    
    # Route indicators to appropriate subplots
    if indicators:
        for indicator_name, values in indicators.items():
            self._route_indicator_to_subplot(
                fig, indicator_name, values, df['timestamp'].tolist(), layout
            )
    
    # Add trades, volume, P&L as before
    self._add_trade_signals(fig, backtest_results.trades, row=layout["price"])
    self._add_volume_chart(fig, df, row=layout["volume"])
    self._add_pnl_chart(fig, backtest_results.trades, row=layout["pnl"])
    
    # ... rest of method
```

## Data Models

### IndicatorMetadata

```python
@dataclass
class IndicatorMetadata:
    name: str                              # Base indicator name (e.g., "MACD")
    indicator_type: IndicatorType          # OVERLAY or OSCILLATOR
    scale_type: ScaleType                  # AUTO, FIXED, or PRICE
    scale_min: Optional[float]             # Min value for FIXED scale
    scale_max: Optional[float]             # Max value for FIXED scale
    zero_line: bool                        # Show zero reference line
    reference_lines: List[ReferenceLine]   # Additional reference lines
    components: Dict[str, ComponentStyle]  # Styling for each component
```

### ReferenceLine

```python
@dataclass
class ReferenceLine:
    value: float      # Y-axis value
    color: str        # Line color
    label: str        # Label text
    style: str        # Line style (solid, dash, dot)
```

### ComponentStyle

```python
@dataclass
class ComponentStyle:
    color: str           # Line/bar color
    label: str           # Legend label
    line_type: str       # "line", "bar", "area"
    width: float         # Line width
    dash: Optional[str]  # Dash style
```

## Correctness Properties


*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Subplot Routing Properties

**Property 1: Oscillators route to separate subplots**
*For any* backtest result containing oscillator indicators (MACD, RSI, Stochastic), when the Chart Engine creates a chart, each oscillator should appear in a subplot separate from the price chart.
**Validates: Requirements 1.1, 1.2, 1.3, 4.3**

**Property 2: Overlays route to price chart**
*For any* backtest result containing overlay indicators (SMA, EMA, VWAP), when the Chart Engine creates a chart, all overlays should appear on the same subplot as the candlestick price data.
**Validates: Requirements 2.1, 2.2, 2.3, 4.2**

**Property 3: Multiple oscillators get distinct subplots**
*For any* backtest result with N oscillator indicators, the Chart Engine should create N separate oscillator subplots, each containing exactly one oscillator.
**Validates: Requirements 1.5**

**Property 4: No empty subplots**
*For any* backtest result, the number of subplots created should equal the number of distinct subplot types needed (price + oscillators + volume + P&L), with no empty subplots.
**Validates: Requirements 6.3**

### Scaling Properties

**Property 5: Fixed scale indicators use specified range**
*For any* indicator with FIXED scale type (RSI, Stochastic), the y-axis range of its subplot should be [scale_min, scale_max] as specified in metadata.
**Validates: Requirements 1.2, 1.3, 8.1, 9.1, 4.4**

**Property 6: Auto-scale indicators encompass all values**
*For any* indicator with AUTO scale type (MACD), the y-axis range should encompass all indicator values with appropriate padding.
**Validates: Requirements 1.4, 4.4**

**Property 7: Overlay indicators share price scale**
*For any* overlay indicator, its y-axis scale should match the price chart's y-axis scale, allowing direct visual comparison with price.
**Validates: Requirements 2.4**

### Metadata Registry Properties

**Property 8: Registered metadata is retrievable**
*For any* indicator metadata registered in the registry, calling get() with the indicator name should return the same metadata object.
**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

**Property 9: Base name extraction is consistent**
*For any* indicator name variation (e.g., "SMA20", "SMA50", "SMA200"), the registry should extract the same base name ("SMA") and return the same metadata.
**Validates: Requirements 3.4**

**Property 10: Calculator metadata matches registry**
*For any* indicator calculator with get_chart_config() method, the returned metadata should match the metadata in the registry for that indicator type.
**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

### Visual Styling Properties

**Property 11: MACD components have correct styling**
*For any* chart containing MACD, the MACD line should be blue, the signal line should be red, and the histogram should be rendered as bars.
**Validates: Requirements 5.1, 5.2, 5.3**

**Property 12: Zero line appears for oscillators**
*For any* oscillator with zero_line=True in metadata (MACD), the subplot should contain a horizontal dashed line at y=0.
**Validates: Requirements 1.6, 5.4**

**Property 13: Reference lines appear at correct positions**
*For any* indicator with reference lines in metadata (RSI at 30/70, Stochastic at 20/80), the subplot should contain horizontal dashed lines at the specified y-values with correct labels.
**Validates: Requirements 8.2, 8.3, 8.5, 9.4, 9.5**

**Property 14: Multiple overlays have distinct colors**
*For any* chart with multiple overlay indicators, each indicator should have a unique color to enable visual distinction.
**Validates: Requirements 2.5, 8.4**

### Component Completeness Properties

**Property 15: MACD calculator returns all components**
*For any* set of candles, when MACDCalculator.calculate() is called, the calculator should provide access to MACD line, signal line, and histogram values.
**Validates: Requirements 5.5**

**Property 16: Multi-line indicators render all lines**
*For any* indicator with multiple components in metadata (Stochastic with %K and %D), all components should be rendered in the subplot.
**Validates: Requirements 9.2, 9.3**

### Backward Compatibility Properties

**Property 17: Subplot heights sum to 1.0**
*For any* chart layout, the sum of all row heights should equal 1.0, ensuring proper vertical space allocation.
**Validates: Requirements 4.5**

**Property 18: Price chart maintains prominence**
*For any* chart layout, the price chart should occupy at least 40% of the vertical space, ensuring it remains the primary focus.
**Validates: Requirements 4.5**

## Error Handling

### Missing Metadata

When an indicator lacks metadata in the registry:
- **Fallback Behavior**: Treat as OVERLAY indicator
- **Logging**: Log warning message indicating missing metadata
- **User Impact**: Chart still generates, indicator appears on price chart
- **Recovery**: User can register metadata and regenerate chart

### Invalid Metadata

When metadata contains invalid values:
- **Validation**: Validate metadata on registration
- **Error Type**: Raise `ValueError` with descriptive message
- **Prevention**: Use dataclass validation and type hints
- **Recovery**: Fix metadata definition and re-register

### Subplot Creation Failure

When Plotly subplot creation fails:
- **Detection**: Catch exceptions from `make_subplots()`
- **Fallback**: Create simple 2-row layout (price + P&L)
- **Logging**: Log error with full traceback
- **User Impact**: Simplified chart without oscillator subplots

### Indicator Data Mismatch

When indicator data length doesn't match candle data:
- **Detection**: Check lengths before plotting
- **Handling**: Truncate or pad to match candle timestamps
- **Logging**: Log warning about data mismatch
- **User Impact**: Indicator may have gaps or missing values

## Testing Strategy

### Unit Testing

**Metadata Registry Tests**:
- Test registration and retrieval of metadata
- Test base name extraction for variations (SMA20, SMA50)
- Test is_oscillator() and is_overlay() methods
- Test handling of unknown indicators

**Subplot Layout Tests**:
- Test layout determination with various indicator combinations
- Test row height calculation
- Test subplot title generation
- Test edge cases (no indicators, all overlays, all oscillators)

**Indicator Routing Tests**:
- Test routing of overlay indicators to price chart
- Test routing of oscillator indicators to separate subplots
- Test handling of multiple oscillators
- Test fallback behavior for unknown indicators

**Component Styling Tests**:
- Test MACD component colors and types
- Test RSI reference lines
- Test Stochastic %K and %D lines
- Test zero line rendering

### Integration Testing

**End-to-End Chart Generation**:
- Test MA Crossover strategy (overlays only)
- Test MACD Crossover strategy (oscillator only)
- Test mixed strategy (overlays + oscillators)
- Test multiple oscillators (MACD + RSI)

**Backward Compatibility Tests**:
- Compare MA Crossover charts before/after changes
- Compare VWAP strategy charts before/after changes
- Verify no visual regressions in existing strategies

**Calculator Integration Tests**:
- Test get_chart_config() on all calculators
- Test metadata consistency between calculator and registry
- Test calculator data integration with chart engine

### Property-Based Testing

Property-based tests will use the `hypothesis` library for Python to generate random test cases.

**Test Configuration**:
- Minimum 100 iterations per property test
- Use custom generators for Candle, Trade, and indicator data
- Seed random generator for reproducibility

**Property Test Examples**:

```python
from hypothesis import given, strategies as st
import hypothesis.strategies as st

@given(
    oscillator_count=st.integers(min_value=1, max_value=5),
    overlay_count=st.integers(min_value=0, max_value=5)
)
def test_property_1_oscillators_route_to_separate_subplots(oscillator_count, overlay_count):
    """Property 1: Oscillators route to separate subplots"""
    # Generate backtest results with specified indicator counts
    # Create chart
    # Verify each oscillator is in a separate subplot
    pass

@given(
    indicator_values=st.lists(st.floats(min_value=-100, max_value=100), min_size=10, max_size=100)
)
def test_property_6_auto_scale_encompasses_values(indicator_values):
    """Property 6: Auto-scale indicators encompass all values"""
    # Create chart with MACD using generated values
    # Extract y-axis range from MACD subplot
    # Verify min(values) >= y_min and max(values) <= y_max
    pass
```

## Performance Considerations

### Subplot Creation Overhead

- **Impact**: Creating multiple subplots increases rendering time
- **Mitigation**: Cache subplot layout calculations
- **Benchmark**: Target < 2 seconds for charts with 5 subplots

### Metadata Lookup Performance

- **Impact**: Querying metadata for each indicator
- **Mitigation**: Use dictionary lookup (O(1))
- **Optimization**: Cache metadata lookups within chart generation

### Memory Usage

- **Impact**: Multiple subplots increase memory footprint
- **Mitigation**: Limit maximum oscillator subplots to 5
- **Monitoring**: Log memory usage for large charts

## Migration Path

### Phase 1: Add Metadata System (Non-Breaking)

1. Create `shared/indicators_metadata.py`
2. Add metadata for existing indicators
3. Add `get_chart_config()` to calculators
4. No changes to Chart Engine yet

### Phase 2: Update Chart Engine (Backward Compatible)

1. Add subplot layout determination
2. Add indicator routing logic
3. Maintain fallback to current behavior
4. Test with existing strategies

### Phase 3: Enable New Behavior (Opt-In)

1. Add flag to enable new subplot system
2. Test with MACD strategies
3. Verify backward compatibility
4. Document migration guide

### Phase 4: Make Default (Breaking Change)

1. Enable new subplot system by default
2. Update all documentation
3. Regenerate example charts
4. Announce breaking change

## Future Enhancements

### Additional Indicator Types

- **Volume Indicators**: Separate volume subplot with custom styling
- **Breadth Indicators**: Market breadth visualization
- **Custom Indicators**: User-defined indicator types

### Advanced Styling

- **Themes**: Dark mode, light mode, custom color schemes
- **Annotations**: Automatic annotation of key levels
- **Interactive Controls**: Toggle indicators on/off

### Performance Optimization

- **Lazy Rendering**: Only render visible subplots
- **Data Decimation**: Reduce data points for large datasets
- **WebGL Rendering**: Use WebGL for faster rendering

### DSL Integration

- **Chart Config in DSL**: Allow strategies to specify chart preferences
- **Custom Layouts**: User-defined subplot arrangements
- **Export Options**: PNG, SVG, PDF export from DSL
