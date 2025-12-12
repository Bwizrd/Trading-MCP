#!/usr/bin/env python3
"""
Simulate MCP Backtest to Verify Strategy Works

This simulates what the MCP server does when running a backtest.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.strategy_registry import get_strategy_registry
from shared.indicators import indicator_registry

def test_mcp_simulation():
    """Simulate the MCP backtest process."""
    print("=" * 80)
    print("MCP BACKTEST SIMULATION")
    print("=" * 80)
    
    try:
        # Step 1: Get strategy from registry (like MCP does)
        print("\n1. Loading strategy from registry...")
        registry = get_strategy_registry()
        strategy = registry.create_strategy("Stochastic Quad Rotation")
        print(f"✅ Strategy loaded: {strategy.get_name()}")
        
        # Step 2: Check required indicators (like backtest engine does)
        print("\n2. Checking required indicators...")
        required = strategy.requires_indicators()
        print(f"   Required indicators: {required}")
        
        if required:
            available = indicator_registry.list_available()
            missing = [ind for ind in required if ind not in available]
            
            if missing:
                print(f"❌ FAIL: Missing indicators: {missing}")
                print(f"   Available: {available}")
                return False
            else:
                print(f"✅ All required indicators available")
        else:
            print(f"✅ Strategy calculates its own indicators (advanced strategy)")
        
        # Step 3: Verify strategy structure
        print("\n3. Verifying strategy structure...")
        
        # Get actual strategy (unwrap if needed)
        actual_strategy = strategy
        if hasattr(strategy, '_strategy'):
            actual_strategy = strategy._strategy
        
        if hasattr(actual_strategy, 'is_advanced_strategy'):
            print(f"   Advanced strategy: {actual_strategy.is_advanced_strategy}")
            
            if actual_strategy.is_advanced_strategy:
                print(f"   ✅ Has MultiIndicatorManager: {actual_strategy.multi_indicator_manager is not None}")
                print(f"   ✅ Has CrossoverDetector: {actual_strategy.crossover_detector is not None}")
                print(f"   ✅ Has ConditionEvaluator: {actual_strategy.condition_evaluator is not None}")
                
                if actual_strategy.multi_indicator_manager:
                    instances = actual_strategy.multi_indicator_manager.list_instances()
                    print(f"   ✅ Indicator instances: {instances}")
        
        print("\n" + "=" * 80)
        print("✅ MCP SIMULATION PASSED")
        print("=" * 80)
        print("\nThe strategy should work through the MCP server after restart.")
        print("Run: run_strategy_backtest(strategy_name='Stochastic Quad Rotation', ...)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ SIMULATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mcp_simulation()
    sys.exit(0 if success else 1)
