#!/usr/bin/env python3
"""
Direct Test of MACD Component Rendering

This test directly calls the _add_oscillator_trace method to verify
that MACD's three components are properly rendered.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.chart_engine import ChartEngine
from shared.models import Candle
from shared.indicators import MACDCalculator
from shared.indicators_metadata import metadata_registry


def create_test_candles(count: int = 100) -> list:
    """Create test candle data with realistic price movement."""
    candles = []
    base_price = 1.1000
    timestamp = datetime(2024, 1, 1, 9, 0)
    
    for i in range(count):
        # Create some price movement
        price_change = (i % 10 - 5) * 0.0001
        price = base_price + price_change
        
        candles.append(Candle(
            timestamp=timestamp,
            open=price,
            high=price + 0.0002,
            low=price - 0.0002,
            close=price + 0.0001,
            volume=1000.0
        ))
        
        timestamp += timedelta(minutes=15)
    
    return candles


def test_macd_oscillator_trace():
    """Test that _add_oscillator_trace properly handles MACD with three components."""
    print("\n" + "=" * 70)
    print("Test: MACD Oscillator Trace Direct Test")
    print("=" * 70)
    
    # Create test data
    candles = create_test_candles(100)
    
    # Calculate MACD
    print("\n1. Calculating MACD...")
    macd_calc = MACDCalculator(12, 26, 9)
    macd_values_dict = macd_calc.calculate(candles)
    
    # Convert to list
    macd_values_list = [macd_values_dict.get(c.timestamp, None) for c in candles]
    timestamps = [c.timestamp for c in candles]
    
    # Filter out None values
    filtered_macd = []
    filtered_timestamps = []
    for i, val in enumerate(macd_values_list):
        if val is not None:
            filtered_macd.append(val)
            filtered_timestamps.append(timestamps[i])
    
    print(f"  ✓ MACD calculated: {len(filtered_macd)} valid points")
    
    # Get MACD metadata
    print("\n2. Getting MACD metadata...")
    metadata = metadata_registry.get("MACD")
    assert metadata is not None, "MACD metadata should exist"
    print(f"  ✓ MACD metadata retrieved")
    print(f"    - Type: {metadata.indicator_type}")
    print(f"    - Scale: {metadata.scale_type}")
    print(f"    - Zero line: {metadata.zero_line}")
    print(f"    - Components: {list(metadata.components.keys())}")
    
    # Create a figure with 2 rows (price + oscillator)
    print("\n3. Creating figure with oscillator subplot...")
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=['Price Chart', 'MACD Oscillator'],
        row_heights=[0.7, 0.3]
    )
    
    # Create chart engine
    engine = ChartEngine()
    
    # Store the MACD calculator instance so the chart engine can access signal/histogram
    engine._macd_calculator = macd_calc
    
    # Call _add_oscillator_trace directly
    print("\n4. Calling _add_oscillator_trace for MACD...")
    try:
        engine._add_oscillator_trace(
            fig=fig,
            indicator_name="MACD",
            values=filtered_macd,
            timestamps=filtered_timestamps,
            row=2,  # Oscillator subplot
            metadata=metadata
        )
        print("  ✓ _add_oscillator_trace completed successfully")
    except Exception as e:
        print(f"  ❌ Error calling _add_oscillator_trace: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Check that the figure has the expected traces
    print("\n5. Verifying traces in figure...")
    trace_names = [trace.name for trace in fig.data]
    print(f"  Traces found: {trace_names}")
    
    # Check for all three MACD components
    has_macd = any("MACD" in name for name in trace_names)
    has_signal = any("Signal" in name for name in trace_names)
    has_histogram = any("Histogram" in name for name in trace_names)
    
    print(f"  MACD line: {'✓' if has_macd else '❌'}")
    print(f"  Signal line: {'✓' if has_signal else '❌'}")
    print(f"  Histogram: {'✓' if has_histogram else '❌'}")
    
    if not (has_macd and has_signal and has_histogram):
        print("\n❌ Not all MACD components were added!")
        return False
    
    # Save the figure to verify visually
    print("\n6. Saving figure for visual verification...")
    output_path = Path("data/charts/test_macd_components_direct.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig.update_layout(
        title="MACD Three Components Test",
        showlegend=True,
        height=800
    )
    
    fig.write_html(str(output_path))
    print(f"  ✓ Chart saved: {output_path}")
    
    print("\n" + "=" * 70)
    print("✅ MACD Oscillator Trace Test PASSED")
    print("=" * 70)
    print(f"\n📊 Open the chart to verify visually:")
    print(f"   {output_path}")
    print("\nExpected visualization:")
    print("  • MACD line in BLUE")
    print("  • Signal line in RED")
    print("  • Histogram as GRAY BARS")
    
    return True


def main():
    """Run MACD component test."""
    print("\n" + "=" * 70)
    print("MACD COMPONENT DIRECT TEST")
    print("=" * 70)
    
    success = test_macd_oscillator_trace()
    
    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
