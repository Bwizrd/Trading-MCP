#!/usr/bin/env python3
"""
Test script to run optimize_trades_single directly without MCP layer.
This bypasses any VS Code MCP tool disabling issues.
"""

import asyncio
import sys
from pathlib import Path

# Add mcp_servers to path
sys.path.insert(0, str(Path(__file__).parent / "mcp_servers"))

from trading_optimizer_mcp import handle_optimize_trades_single


async def main():
    """Run UK100_SB optimization for yesterday with SL=10, TP=20."""
    
    print("=" * 80)
    print("Testing UK100_SB Trade Optimization (2026-01-20)")
    print("Parameters: SL=10 pips, TP=20 pips, Time: 09:00-17:00")
    print("=" * 80)
    print()
    
    arguments = {
        "date": "2026-01-20",
        "sl_pips": 10,
        "tp_pips": 20,
        "start_time": "09:00:00",
        "end_time": "17:00:00"
    }
    
    try:
        result = await handle_optimize_trades_single(arguments)
        print(result)
        print()
        print("=" * 80)
        print("✅ Optimization completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
