#!/usr/bin/env python3
"""
Test Backward Compatibility

Verify that existing DSL strategies still work after advanced features were added.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.strategy_registry import get_strategy_registry

def test_existing_strategies():
    """Test that all existing strategies still load correctly."""
    print("=" * 80)
    print("BACKWARD COMPATIBILITY TEST")
    print("=" * 80)
    
    # List of existing strategies that should still work
    existing_strategies = [
        "MA Crossover Strategy",
        "MACD Crossover Strategy",
        "10am vs 9:30am Price Compare",
        "VWAP Momentum",
        "VWAP Reversal"
    ]
    
    registry = get_strategy_registry()
    available = registry.list_strategies()
    
    print(f"\nTotal strategies available: {len(available)}")
    print(f"Strategies to test: {len(existing_strategies)}")
    
    results = []
    
    for strategy_name in existing_strategies:
        try:
            if strategy_name not in available:
                print(f"\n⚠️  {strategy_name}: NOT FOUND in registry")
                results.append((strategy_name, False, "Not found"))
                continue
            
            # Try to create the strategy
            strategy = registry.create_strategy(strategy_name)
            
            # Verify basic properties
            name = strategy.get_name()
            version = strategy.get_version()
            description = strategy.get_description()
            
            # Check that it's not using advanced features (should be simple)
            actual_strategy = strategy
            if hasattr(strategy, '_strategy'):
                actual_strategy = strategy._strategy
            
            is_advanced = getattr(actual_strategy, 'is_advanced_strategy', False)
            
            print(f"\n✅ {strategy_name}")
            print(f"   Version: {version}")
            print(f"   Advanced: {is_advanced}")
            
            if is_advanced:
                print(f"   ⚠️  WARNING: Strategy marked as advanced (should be simple)")
            
            results.append((strategy_name, True, "OK"))
            
        except Exception as e:
            print(f"\n❌ {strategy_name}: FAILED")
            print(f"   Error: {e}")
            results.append((strategy_name, False, str(e)))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for strategy_name, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {strategy_name}")
        if not success:
            print(f"         {message}")
    
    print(f"\nTotal: {passed}/{total} strategies working")
    
    if passed == total:
        print("\n🎉 All existing strategies still work!")
        print("✅ BACKWARD COMPATIBILITY VERIFIED")
        return True
    else:
        print(f"\n⚠️  {total - passed} strategy(ies) broken")
        return False

if __name__ == "__main__":
    success = test_existing_strategies()
    sys.exit(0 if success else 1)
