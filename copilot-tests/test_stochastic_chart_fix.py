#!/usr/bin/env python3
"""
Test stochastic chart fix - verify that 4 stochastic indicators
are properly routed to 4 separate subplots.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.strategies.dsl_interpreter.dsl_loader import DSLLoader
from shared.models import Candle
from datetime import datetime, timedelta
import random

def create_test_candles(count=100):
    """Create test candles with realistic OHLCV data."""
    candles = []
    base_price = 1.1000
    timestamp = datetime(2025, 1, 1, 9, 0)
    
    for i in range(count):
        # Random walk
        change = random.uniform(-0.0010, 0.0010)
        base_price += change
        
        open_price = base_price
        high_price = base_price + random.uniform(0, 0.0005)
        low_price = base_price - random.uniform(0, 0.0005)
        close_price = base_price + random.uniform(-0.0003, 0.0003)
        volume = random.uniform(1000, 5000)
        
        candle = Candle(
            timestamp=timestamp,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume
        )
        candles.append(candle)
        timestamp += timedelta(minutes=15)
    
    return candles

def test_metadata_registration():
    """Test that stochastic metadata is properly registered."""
    print("\n=== Testing Metadata Registration ===")
    
    # Load the strategy
    from shared.strategies.dsl_interpreter.dsl_strategy import create_dsl_strategy_from_file
    strategy_path = project_root / "shared" / "strategies" / "dsl_strategies" / "stochastic_quad_rotation.json"
    strategy = create_dsl_strategy_from_file(str(strategy_path))
    
    print(f"✓ Loaded strategy: {strategy.dsl_config['name']}")
    
    # Create test candles
    candles = create_test_candles(100)
    print(f"✓ Created {len(candles)} test candles")
    
    # Get indicator series (this should trigger metadata registration)
    indicator_series = strategy.get_indicator_series(candles)
    
    print(f"\n✓ Got indicator series with {len(indicator_series)} indicators:")
    for name in sorted(indicator_series.keys()):
        print(f"  - {name}: {len(indicator_series[name])} values")
    
    # Check that we have all expected indicators
    expected_indicators = [
        'fast', 'fast_d',
        'med_fast', 'med_fast_d',
        'med_slow', 'med_slow_d',
        'slow', 'slow_d'
    ]
    
    for expected in expected_indicators:
        if expected in indicator_series:
            print(f"✓ Found {expected}")
        else:
            print(f"✗ Missing {expected}")
            return False
    
    # Verify metadata was registered
    from shared.indicators_metadata import metadata_registry
    
    print("\n=== Checking Metadata Registry ===")
    for alias in ['fast', 'med_fast', 'med_slow', 'slow']:
        metadata = metadata_registry.get(alias)
        if metadata:
            print(f"✓ Metadata registered for '{alias}':")
            print(f"  - Type: {metadata.indicator_type.value}")
            print(f"  - Scale: {metadata.scale_type.value} ({metadata.scale_min}-{metadata.scale_max})")
            print(f"  - Components: {list(metadata.components.keys())}")
        else:
            print(f"✗ No metadata for '{alias}'")
            return False
    
    return True

def test_chart_layout():
    """Test that chart engine creates proper layout for 4 stochastics."""
    print("\n=== Testing Chart Layout ===")
    
    from shared.chart_engine import ChartEngine
    
    # Create mock indicator data
    indicators = {
        'fast': [50.0] * 100,
        'fast_d': [48.0] * 100,
        'med_fast': [55.0] * 100,
        'med_fast_d': [53.0] * 100,
        'med_slow': [60.0] * 100,
        'med_slow_d': [58.0] * 100,
        'slow': [65.0] * 100,
        'slow_d': [63.0] * 100,
    }
    
    engine = ChartEngine()
    layout = engine._determine_subplot_layout(indicators)
    
    print(f"✓ Layout determined: {layout}")
    
    # Should have: price + 4 oscillators + volume + pnl = 7 rows
    expected_rows = 7
    actual_rows = max(layout.values())
    
    if actual_rows == expected_rows:
        print(f"✓ Correct number of rows: {actual_rows}")
    else:
        print(f"✗ Wrong number of rows: expected {expected_rows}, got {actual_rows}")
        return False
    
    # Check that we have 4 oscillator subplots
    oscillator_count = len([k for k in layout.keys() if k.startswith('oscillator_')])
    if oscillator_count == 4:
        print(f"✓ Correct number of oscillator subplots: {oscillator_count}")
    else:
        print(f"✗ Wrong number of oscillator subplots: expected 4, got {oscillator_count}")
        return False
    
    return True

if __name__ == "__main__":
    print("Testing Stochastic Chart Fix")
    print("=" * 50)
    
    success = True
    
    # Test 1: Metadata registration
    if not test_metadata_registration():
        print("\n✗ Metadata registration test FAILED")
        success = False
    else:
        print("\n✓ Metadata registration test PASSED")
    
    # Test 2: Chart layout
    if not test_chart_layout():
        print("\n✗ Chart layout test FAILED")
        success = False
    else:
        print("\n✓ Chart layout test PASSED")
    
    print("\n" + "=" * 50)
    if success:
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)
