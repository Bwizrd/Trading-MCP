#!/usr/bin/env python3
"""
Complete MACD Strategy Workflow Test

This script demonstrates the full workflow:
1. Create MACD strategy JSON
2. Validate it
3. Save it
4. List strategies to confirm
5. Instructions for backtesting
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from mcp_servers.strategy_builder.validators import validate_dsl_json
from mcp_servers.strategy_builder.file_operations import save_dsl_strategy_to_file, list_dsl_strategies


def main():
    print("\n" + "="*60)
    print("MACD STRATEGY WORKFLOW TEST")
    print("="*60)
    
    # Step 1: Create MACD Strategy JSON (this is what Stage 3 outputs)
    print("\n📝 Step 1: Creating MACD Strategy JSON...")
    macd_strategy = {
        "name": "MACD Crossover Strategy",
        "version": "1.0.0",
        "description": "MACD signal line crossover strategy for trend following",
        "indicators": [
            {
                "type": "MACD",
                "alias": "macd"
            }
        ],
        "conditions": {
            "buy": {
                "compare": "macd > macd_signal",
                "crossover": True
            },
            "sell": {
                "compare": "macd < macd_signal",
                "crossover": True
            }
        },
        "risk_management": {
            "stop_loss_pips": 25,
            "take_profit_pips": 40,
            "max_daily_trades": 5
        }
    }
    
    macd_json = json.dumps(macd_strategy, indent=2)
    print("✅ MACD Strategy JSON created")
    print(f"\n{macd_json}\n")
    
    # Step 2: Validate the strategy
    print("\n🔍 Step 2: Validating strategy...")
    validation_result = validate_dsl_json(macd_json)
    
    if validation_result["valid"]:
        print(f"✅ Strategy is valid!")
        print(f"   Name: {validation_result['strategy_name']}")
        print(f"   Type: {validation_result['strategy_type']}")
    else:
        print(f"❌ Validation failed:")
        for error in validation_result["errors"]:
            print(f"   - {error}")
        return 1
    
    # Step 3: Save the strategy
    print("\n💾 Step 3: Saving strategy to dsl_strategies folder...")
    save_result = save_dsl_strategy_to_file(macd_json, "macd_crossover")
    
    if save_result["success"]:
        print(f"✅ Strategy saved successfully!")
        print(f"   Path: {save_result['file_path']}")
    else:
        print(f"❌ Save failed: {save_result['message']}")
        return 1
    
    # Step 4: List all strategies to confirm
    print("\n📋 Step 4: Listing all available strategies...")
    list_result = list_dsl_strategies()
    
    print(f"✅ Found {list_result['count']} strategies:")
    for strategy in list_result['strategies']:
        marker = "👉" if strategy['name'] == "MACD Crossover Strategy" else "  "
        print(f"{marker} {strategy['name']} (v{strategy['version']}) - {strategy['type']}")
    
    # Step 5: Instructions for backtesting
    print("\n" + "="*60)
    print("🎯 NEXT STEPS: Backtest Your Strategy")
    print("="*60)
    
    print("\nYour MACD strategy is ready! To backtest it, you have two options:")
    
    print("\n📊 Option 1: Using Python directly")
    print("```python")
    print("from shared.strategy_registry import StrategyRegistry")
    print("from shared.backtest_engine import UniversalBacktestEngine")
    print("from shared.data_connector import DataConnector")
    print("")
    print("# Load the strategy")
    print("registry = StrategyRegistry()")
    print("strategy = registry.get_strategy('MACD Crossover Strategy')")
    print("")
    print("# Run backtest")
    print("data_connector = DataConnector()")
    print("engine = UniversalBacktestEngine(data_connector)")
    print("results = engine.run_backtest(")
    print("    strategy=strategy,")
    print("    symbol='EURUSD',")
    print("    start_date='2024-11-01',")
    print("    end_date='2024-11-30',")
    print("    timeframe='15m'")
    print(")")
    print("```")
    
    print("\n🔧 Option 2: Using MCP Tools (if configured)")
    print("Use the universal-backtest-engine MCP tool:")
    print("  run_strategy_backtest(")
    print("    strategy_name='MACD Crossover Strategy',")
    print("    symbol='EURUSD',")
    print("    days_back=30,")
    print("    timeframe='15m'")
    print("  )")
    
    print("\n" + "="*60)
    print("✅ WORKFLOW COMPLETE!")
    print("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
