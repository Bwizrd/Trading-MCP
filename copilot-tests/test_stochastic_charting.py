#!/usr/bin/env python3
"""
Test Stochastic Indicator Charting

Verify that get_indicator_series() returns stochastic data for charting.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.strategy_registry import get_strategy_registry
from shared.models import Candle

def test_stochastic_charting():
    """Test that stochastic indicators are included in chart data."""
    print("=" * 80)
    print("STOCHASTIC CHARTING TEST")
    print("=" * 80)
    
    try:
        # Load strategy
        print("\n1. Loading strategy...")
        registry = get_strategy_registry()
        strategy = registry.create_strategy("Stochastic Quad Rotation")
        print(f"✅ Strategy loaded: {strategy.get_name()}")
        
        # Create sample candles
        print("\n2. Creating sample candles...")
        base_time = datetime(2025, 1, 1, 9, 0)
        candles = []
        
        for i in range(100):
            close = 1.0800 + 0.0100 * (0.5 + 0.5 * (i % 20) / 20)
            high = close + 0.0010
            low = close - 0.0010
            
            candle = Candle(
                timestamp=base_time + timedelta(minutes=i),
                open=close,
                high=high,
                low=low,
                close=close,
                volume=1000
            )
            candles.append(candle)
        
        print(f"✅ Created {len(candles)} candles")
        
        # Get indicator series for charting
        print("\n3. Getting indicator series for charting...")
        
        # Unwrap strategy if needed
        actual_strategy = strategy
        if hasattr(strategy, '_strategy'):
            actual_strategy = strategy._strategy
        
        indicator_series = actual_strategy.get_indicator_series(candles)
        
        print(f"   Indicator series returned: {list(indicator_series.keys())}")
        
        # Check for stochastic indicators
        expected_indicators = ['fast', 'fast_d', 'med_fast', 'med_fast_d', 'med_slow', 'med_slow_d', 'slow', 'slow_d']
        
        found = []
        missing = []
        
        for ind in expected_indicators:
            if ind in indicator_series:
                series = indicator_series[ind]
                print(f"   ✅ {ind}: {len(series)} values")
                
                # Check a few values
                if series:
                    sample_values = series[-5:]  # Last 5 values
                    print(f"      Sample values: {[f'{v:.2f}' for v in sample_values]}")
                    
                    # Verify values are in 0-100 range
                    if all(0 <= v <= 100 for v in series if v is not None):
                        print(f"      ✓ All values in 0-100 range")
                    else:
                        print(f"      ✗ Some values out of range!")
                        return False
                
                found.append(ind)
            else:
                missing.append(ind)
        
        if missing:
            print(f"\n❌ MISSING INDICATORS: {missing}")
            print(f"   This means the chart will not display these stochastics!")
            return False
        
        print(f"\n✅ All {len(expected_indicators)} stochastic indicators present")
        print(f"   Found: {found}")
        
        print("\n" + "=" * 80)
        print("✅ STOCHASTIC CHARTING TEST PASSED")
        print("=" * 80)
        print("\nThe chart should now display all 4 stochastic indicators.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_stochastic_charting()
    sys.exit(0 if success else 1)
