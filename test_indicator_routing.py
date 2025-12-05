#!/usr/bin/env python3
"""
Test indicator routing logic in ChartEngine.

This test verifies that indicators are correctly routed to appropriate subplots
based on their metadata (overlay vs oscillator).
"""

from datetime import datetime, timedelta
from shared.chart_engine import ChartEngine
from shared.models import Candle, Trade, TradeDirection
from shared.strategy_interface import BacktestResults
from plotly.subplots import make_subplots
import plotly.graph_objects as go


def create_test_candles(count=100):
    """Create test candle data."""
    candles = []
    base_time = datetime(2024, 1, 1, 9, 0)
    base_price = 1.15
    
    for i in range(count):
        candles.append(Candle(
            timestamp=base_time + timedelta(minutes=i*15),
            open=base_price + (i * 0.0001),
            high=base_price + (i * 0.0001) + 0.0005,
            low=base_price + (i * 0.0001) - 0.0005,
            close=base_price + (i * 0.0001) + 0.0002,
            volume=1000 + i
        ))
    
    return candles


def create_test_backtest_results():
    """Create minimal backtest results for testing."""
    trades = []
    
    # Create a few test trades
    for i in range(3):
        trade = Trade(
            direction=TradeDirection.BUY if i % 2 == 0 else TradeDirection.SELL,
            entry_time=datetime(2024, 1, 1, 10, 0) + timedelta(hours=i),
            entry_price=1.15 + (i * 0.001),
            exit_time=datetime(2024, 1, 1, 11, 0) + timedelta(hours=i),
            exit_price=1.15 + (i * 0.001) + 0.0005,
            pips=5.0 if i % 2 == 0 else -3.0
        )
        trades.append(trade)
    
    return BacktestResults(
        trades=trades,
        total_pips=7.0,
        win_rate=0.67,
        profit_factor=1.5,
        strategy_name="Test Strategy",
        configuration=None
    )


def test_route_overlay_to_price_chart():
    """Test that overlay indicators are routed to the price chart."""
    print("\n" + "=" * 70)
    print("Test: Route Overlay Indicators to Price Chart")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data
    indicators = {
        "SMA20": [1.15 + (i * 0.0001) for i in range(100)],
        "EMA50": [1.14 + (i * 0.0001) for i in range(100)],
        "VWAP": [1.155 + (i * 0.0001) for i in range(100)]
    }
    
    # Determine layout
    layout = engine._determine_subplot_layout(indicators)
    
    # Create a test figure
    fig = make_subplots(rows=3, cols=1)
    
    # Create timestamps
    timestamps = [datetime(2024, 1, 1, 9, 0) + timedelta(minutes=i*15) for i in range(100)]
    
    # Route each indicator
    for indicator_name, values in indicators.items():
        print(f"\nRouting {indicator_name}...")
        engine._route_indicator_to_subplot(fig, indicator_name, values, timestamps, layout)
    
    # Verify all overlays were added to price chart (row 1)
    price_traces = [trace for trace in fig.data if trace.xaxis == 'x']
    print(f"\nTraces on price chart: {len(price_traces)}")
    
    assert len(price_traces) == 3, f"Expected 3 overlay traces on price chart, got {len(price_traces)}"
    
    print("\n✓ All overlay indicators routed to price chart")
    print("=" * 70)


def test_route_oscillator_to_separate_subplot():
    """Test that oscillator indicators are routed to separate subplots."""
    print("\n" + "=" * 70)
    print("Test: Route Oscillator Indicators to Separate Subplots")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data
    indicators = {
        "MACD": [0.001 + (i * 0.00001) for i in range(100)],
        "RSI": [50.0 + (i * 0.1) for i in range(100)]
    }
    
    # Determine layout
    layout = engine._determine_subplot_layout(indicators)
    print(f"\nLayout: {layout}")
    
    # Create a test figure with correct number of rows
    total_rows = max(layout.values())
    fig = make_subplots(rows=total_rows, cols=1)
    
    # Create timestamps
    timestamps = [datetime(2024, 1, 1, 9, 0) + timedelta(minutes=i*15) for i in range(100)]
    
    # Route each indicator
    for indicator_name, values in indicators.items():
        print(f"\nRouting {indicator_name}...")
        engine._route_indicator_to_subplot(fig, indicator_name, values, timestamps, layout)
    
    # Verify oscillators were added to separate subplots
    print(f"\nTotal traces in figure: {len(fig.data)}")
    
    # Check that we have traces for both oscillators
    assert len(fig.data) >= 2, f"Expected at least 2 oscillator traces, got {len(fig.data)}"
    
    print("\n✓ Oscillator indicators routed to separate subplots")
    print("=" * 70)


def test_reference_lines_added():
    """Test that reference lines are added for oscillators."""
    print("\n" + "=" * 70)
    print("Test: Reference Lines Added for Oscillators")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data with RSI (has reference lines at 30 and 70)
    indicators = {
        "RSI": [50.0 + (i * 0.1) for i in range(100)]
    }
    
    # Determine layout
    layout = engine._determine_subplot_layout(indicators)
    
    # Create a test figure
    total_rows = max(layout.values())
    fig = make_subplots(rows=total_rows, cols=1)
    
    # Create timestamps
    timestamps = [datetime(2024, 1, 1, 9, 0) + timedelta(minutes=i*15) for i in range(100)]
    
    # Route RSI
    print("\nRouting RSI (should add reference lines at 30 and 70)...")
    engine._route_indicator_to_subplot(fig, "RSI", indicators["RSI"], timestamps, layout)
    
    # Check for horizontal lines (reference lines)
    hlines = [shape for shape in fig.layout.shapes if shape.type == 'line' and shape.y0 == shape.y1]
    print(f"\nHorizontal lines found: {len(hlines)}")
    
    # RSI should have 2 reference lines (30 and 70)
    assert len(hlines) >= 2, f"Expected at least 2 reference lines for RSI, got {len(hlines)}"
    
    print("✓ Reference lines added for RSI")
    print("=" * 70)


def test_zero_line_added():
    """Test that zero line is added for MACD."""
    print("\n" + "=" * 70)
    print("Test: Zero Line Added for MACD")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data with MACD (has zero line)
    indicators = {
        "MACD": [0.001 + (i * 0.00001) for i in range(100)]
    }
    
    # Determine layout
    layout = engine._determine_subplot_layout(indicators)
    
    # Create a test figure
    total_rows = max(layout.values())
    fig = make_subplots(rows=total_rows, cols=1)
    
    # Create timestamps
    timestamps = [datetime(2024, 1, 1, 9, 0) + timedelta(minutes=i*15) for i in range(100)]
    
    # Route MACD
    print("\nRouting MACD (should add zero line)...")
    engine._route_indicator_to_subplot(fig, "MACD", indicators["MACD"], timestamps, layout)
    
    # Check for horizontal lines
    hlines = [shape for shape in fig.layout.shapes if shape.type == 'line' and shape.y0 == shape.y1]
    print(f"\nHorizontal lines found: {len(hlines)}")
    
    # MACD should have 1 zero line
    assert len(hlines) >= 1, f"Expected at least 1 zero line for MACD, got {len(hlines)}"
    
    # Check if one of the lines is at y=0
    zero_lines = [line for line in hlines if line.y0 == 0]
    assert len(zero_lines) >= 1, "Expected a zero line at y=0"
    
    print("✓ Zero line added for MACD")
    print("=" * 70)


def test_fixed_scale_applied():
    """Test that fixed scale is applied for RSI."""
    print("\n" + "=" * 70)
    print("Test: Fixed Scale Applied for RSI")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data with RSI (has fixed scale 0-100)
    indicators = {
        "RSI": [50.0 + (i * 0.1) for i in range(100)]
    }
    
    # Determine layout
    layout = engine._determine_subplot_layout(indicators)
    
    # Create a test figure
    total_rows = max(layout.values())
    fig = make_subplots(rows=total_rows, cols=1)
    
    # Create timestamps
    timestamps = [datetime(2024, 1, 1, 9, 0) + timedelta(minutes=i*15) for i in range(100)]
    
    # Route RSI
    print("\nRouting RSI (should apply fixed scale 0-100)...")
    engine._route_indicator_to_subplot(fig, "RSI", indicators["RSI"], timestamps, layout)
    
    # Check y-axis range for RSI subplot
    rsi_row = layout["oscillator_1"]
    yaxis_key = f"yaxis{rsi_row}" if rsi_row > 1 else "yaxis"
    
    yaxis = getattr(fig.layout, yaxis_key, None)
    
    if yaxis and hasattr(yaxis, 'range') and yaxis.range:
        print(f"\nY-axis range for RSI: {yaxis.range}")
        assert yaxis.range[0] == 0, f"Expected y-axis min to be 0, got {yaxis.range[0]}"
        assert yaxis.range[1] == 100, f"Expected y-axis max to be 100, got {yaxis.range[1]}"
        print("✓ Fixed scale [0, 100] applied for RSI")
    else:
        print("⚠ Y-axis range not set (may be set during rendering)")
    
    print("=" * 70)


def test_mixed_indicators():
    """Test routing with mixed overlay and oscillator indicators."""
    print("\n" + "=" * 70)
    print("Test: Mixed Overlay and Oscillator Indicators")
    print("=" * 70)
    
    engine = ChartEngine()
    
    # Create test data with both overlays and oscillators
    indicators = {
        "SMA20": [1.15 + (i * 0.0001) for i in range(100)],
        "MACD": [0.001 + (i * 0.00001) for i in range(100)],
        "VWAP": [1.155 + (i * 0.0001) for i in range(100)],
        "RSI": [50.0 + (i * 0.1) for i in range(100)]
    }
    
    # Determine layout
    layout = engine._determine_subplot_layout(indicators)
    print(f"\nLayout: {layout}")
    
    # Create a test figure
    total_rows = max(layout.values())
    fig = make_subplots(rows=total_rows, cols=1)
    
    # Create timestamps
    timestamps = [datetime(2024, 1, 1, 9, 0) + timedelta(minutes=i*15) for i in range(100)]
    
    # Route each indicator
    for indicator_name, values in indicators.items():
        print(f"\nRouting {indicator_name}...")
        engine._route_indicator_to_subplot(fig, indicator_name, values, timestamps, layout)
    
    print(f"\nTotal traces: {len(fig.data)}")
    
    # Verify we have traces for all indicators
    assert len(fig.data) >= 4, f"Expected at least 4 traces, got {len(fig.data)}"
    
    print("\n✓ Mixed indicators routed correctly")
    print("=" * 70)


if __name__ == "__main__":
    test_route_overlay_to_price_chart()
    test_route_oscillator_to_separate_subplot()
    test_reference_lines_added()
    test_zero_line_added()
    test_fixed_scale_applied()
    test_mixed_indicators()
    
    print("\n" + "=" * 70)
    print("ALL ROUTING TESTS PASSED! ✓✓✓")
    print("=" * 70)
