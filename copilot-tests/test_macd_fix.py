#!/usr/bin/env python3
"""
Test the MACD crossover fix with real backtest.
"""

import sys
sys.path.insert(0, 'mcp_servers')
from universal_backtest_engine import run_strategy_backtest

# Run a backtest with the MACD strategy
result = run_strategy_backtest({
    "strategy_name": "MACD Crossover Strategy",
    "symbol": "EURUSD",
    "timeframe": "15m",
    "days_back": 7,
    "stop_loss_pips": 15,
    "take_profit_pips": 25,
    "auto_chart": False  # Don't create chart, just test signal generation
})

print("\n" + "="*60)
print("MACD CROSSOVER FIX TEST RESULTS")
print("="*60)
print(f"Total Trades: {result.get('total_trades', 0)}")
print(f"Win Rate: {result.get('win_rate', 0):.1f}%")
print(f"Total Pips: {result.get('total_pips', 0):.1f}")
print("="*60)

if result.get('total_trades', 0) > 0:
    print("\n✅ SUCCESS! MACD crossover detection is working!")
    print(f"   Generated {result['total_trades']} trades")
else:
    print("\n❌ ISSUE: No trades generated")
    print("   Check /tmp/dsl_debug.log for details")

print("\nDiagnostic log location: /tmp/dsl_debug.log")
