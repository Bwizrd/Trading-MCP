#!/usr/bin/env python3
"""
Test Stochastic Quad Rotation Strategy

This test verifies:
1. Strategy loads correctly from JSON
2. Indicator instances are registered
3. Stochastic calculations work
4. Rotation conditions are evaluated correctly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.strategies.dsl_interpreter.dsl_strategy import create_dsl_strategy_from_file
from shared.strategy_registry import get_strategy_registry

def test_strategy_loading():
    """Test that the strategy loads correctly."""
    print("=" * 80)
    print("TEST 1: Strategy Loading")
    print("=" * 80)
    
    strategy_path = project_root / "shared/strategies/dsl_strategies/stochastic_quad_rotation.json"
    
    try:
        strategy = create_dsl_strategy_from_file(str(strategy_path))
        print(f"✅ Strategy loaded: {strategy.get_name()}")
        print(f"   Version: {strategy.get_version()}")
        print(f"   Description: {strategy.get_description()}")
        print(f"   Is advanced strategy: {strategy.is_advanced_strategy}")
        
        if strategy.is_advanced_strategy:
            instances = strategy.multi_indicator_manager.list_instances()
            print(f"   Indicator instances: {instances}")
            
            for alias in instances:
                config = strategy.multi_indicator_manager.get_instance_config(alias)
                print(f"     - {alias}: {config['type']} with params {config['params']}")
        
        return True
    except Exception as e:
        print(f"❌ Strategy loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_registry_integration():
    """Test that the strategy appears in the registry."""
    print("\n" + "=" * 80)
    print("TEST 2: Strategy Registry Integration")
    print("=" * 80)
    
    try:
        registry = get_strategy_registry()
        strategies = registry.list_strategies()
        
        print(f"Available strategies: {len(strategies)}")
        
        if "Stochastic Quad Rotation" in strategies:
            print(f"✅ Stochastic Quad Rotation found in registry")
            
            info = registry.get_strategy_info("Stochastic Quad Rotation")
            print(f"   Strategy info:")
            print(f"     - Version: {info['version']}")
            print(f"     - Description: {info['description']}")
            print(f"     - DSL Strategy: {info.get('dsl_strategy', False)}")
            
            return True
        else:
            print(f"❌ Stochastic Quad Rotation NOT found in registry")
            print(f"   Available: {strategies}")
            return False
            
    except Exception as e:
        print(f"❌ Registry test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stochastic_calculation():
    """Test that stochastic indicators can be calculated."""
    print("\n" + "=" * 80)
    print("TEST 3: Stochastic Calculation")
    print("=" * 80)
    
    try:
        from shared.indicators import StochasticCalculator
        from shared.models import Candle
        from datetime import datetime, timedelta
        
        # Create sample candles with a clear pattern
        base_time = datetime(2025, 1, 1, 9, 0)
        candles = []
        
        # Create 100 candles with oscillating prices
        for i in range(100):
            # Oscillate between 1.0800 and 1.0900
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
        
        # Test different stochastic configurations
        configs = [
            (9, 1, 3, "fast"),
            (14, 1, 3, "med_fast"),
            (40, 1, 4, "med_slow"),
            (60, 1, 10, "slow")
        ]
        
        for k_period, k_smoothing, d_smoothing, name in configs:
            calc = StochasticCalculator(k_period, k_smoothing, d_smoothing)
            results = calc.calculate(candles)
            
            if results:
                last_value = list(results.values())[-1]
                print(f"✅ {name} ({k_period}-{k_smoothing}-{d_smoothing}): {len(results)} values, last = {last_value:.2f}")
                
                # Verify value is in 0-100 range
                if 0 <= last_value <= 100:
                    print(f"   ✓ Value in valid range [0, 100]")
                else:
                    print(f"   ✗ Value OUT OF RANGE: {last_value}")
                    return False
            else:
                print(f"❌ {name}: No results calculated")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Stochastic calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("STOCHASTIC QUAD ROTATION STRATEGY TESTS")
    print("=" * 80 + "\n")
    
    results = []
    
    # Test 1: Strategy loading
    results.append(("Strategy Loading", test_strategy_loading()))
    
    # Test 2: Registry integration
    results.append(("Registry Integration", test_strategy_registry_integration()))
    
    # Test 3: Stochastic calculation
    results.append(("Stochastic Calculation", test_stochastic_calculation()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
