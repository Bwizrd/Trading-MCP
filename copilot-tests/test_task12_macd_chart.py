#!/usr/bin/env python3
"""
Test Task 12: MACD Crossover Strategy Chart Verification

This test verifies:
- MACD appears in separate subplot
- MACD line is blue
- Signal line is red
- Histogram is bars
- Zero line is present
- Price chart is unaffected

Requirements: 1.1, 5.1, 5.2, 5.3, 5.4
"""

import sys
import os
from datetime import datetime, timedelta
import re

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.backtest_engine import BacktestEngine
from shared.chart_engine import ChartEngine
from shared.data_connector import DataConnector


def run_macd_backtest():
    """Run MACD Crossover strategy backtest on EURUSD."""
    print("=" * 80)
    print("Task 12: Testing MACD Crossover Strategy Chart")
    print("=" * 80)
    
    # Setup
    strategy_name = "MACD Crossover Strategy"
    symbol = "EURUSD"
    timeframe = "15m"
    days_back = 7
    
    print(f"\n1. Running backtest for {strategy_name}")
    print(f"   Symbol: {symbol}")
    print(f"   Timeframe: {timeframe}")
    print(f"   Period: Last {days_back} days")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Fetch data
    print(f"\n2. Fetching market data...")
    connector = DataConnector()
    candles = connector.get_data(
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )
    
    if not candles:
        print("   ❌ Failed to fetch candles")
        return False
    
    print(f"   ✓ Fetched {len(candles)} candles")
    
    # Run backtest
    print(f"\n3. Running backtest...")
    engine = BacktestEngine()
    results = engine.run_backtest(
        strategy_name=strategy_name,
        candles=candles,
        initial_balance=10000,
        risk_per_trade=0.02
    )
    
    print(f"   ✓ Backtest complete")
    print(f"   Total trades: {results.total_trades}")
    print(f"   Win rate: {results.win_rate:.1f}%")
    
    # Generate chart
    print(f"\n4. Generating chart...")
    chart_engine = ChartEngine()
    
    # Get indicators from backtest
    indicators = results.indicators if hasattr(results, 'indicators') else {}
    
    chart_path = chart_engine.create_comprehensive_chart(
        candles=candles,
        backtest_results=results,
        indicators=indicators,
        title=f"{strategy_name} - {symbol} {timeframe}"
    )
    
    print(f"   ✓ Chart generated: {chart_path}")
    
    # Verify chart contents
    print(f"\n5. Verifying chart requirements...")
    
    with open(chart_path, 'r') as f:
        html_content = f.read()
    
    verification_results = {
        "macd_separate_subplot": False,
        "macd_line_blue": False,
        "signal_line_red": False,
        "histogram_bars": False,
        "zero_line_present": False,
        "price_chart_present": False
    }
    
    # Check for MACD in separate subplot (should have subplot title with "MACD")
    if re.search(r'subplot.*MACD', html_content, re.IGNORECASE):
        verification_results["macd_separate_subplot"] = True
        print("   ✓ MACD appears in separate subplot")
    else:
        print("   ❌ MACD not found in separate subplot")
    
    # Check for MACD line in blue (#2196F3 or similar blue)
    if re.search(r'MACD.*#2196F3|#2196F3.*MACD', html_content, re.IGNORECASE | re.DOTALL):
        verification_results["macd_line_blue"] = True
        print("   ✓ MACD line is blue")
    else:
        print("   ❌ MACD line color not verified as blue")
    
    # Check for Signal line in red (#FF5722 or similar red)
    if re.search(r'Signal.*#FF5722|#FF5722.*Signal', html_content, re.IGNORECASE | re.DOTALL):
        verification_results["signal_line_red"] = True
        print("   ✓ Signal line is red")
    else:
        print("   ❌ Signal line color not verified as red")
    
    # Check for histogram as bars (Bar trace type)
    if re.search(r'Histogram.*type.*bar|bar.*Histogram', html_content, re.IGNORECASE | re.DOTALL):
        verification_results["histogram_bars"] = True
        print("   ✓ Histogram rendered as bars")
    else:
        print("   ❌ Histogram not verified as bars")
    
    # Check for zero line (horizontal line at y=0)
    if re.search(r'hline.*y.*0|y.*0.*hline', html_content, re.IGNORECASE):
        verification_results["zero_line_present"] = True
        print("   ✓ Zero line present")
    else:
        print("   ❌ Zero line not found")
    
    # Check for price chart (candlestick)
    if 'candlestick' in html_content.lower() or 'ohlc' in html_content.lower():
        verification_results["price_chart_present"] = True
        print("   ✓ Price chart present and unaffected")
    else:
        print("   ❌ Price chart not verified")
    
    # Summary
    print(f"\n6. Verification Summary")
    print("=" * 80)
    
    passed = sum(verification_results.values())
    total = len(verification_results)
    
    for check, result in verification_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"   {status}: {check.replace('_', ' ').title()}")
    
    print(f"\n   Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n   🎉 All requirements verified successfully!")
        print(f"\n   Chart file: {chart_path}")
        print(f"   Open this file in a browser to visually inspect the chart.")
        return True
    else:
        print("\n   ⚠️  Some requirements not verified")
        print(f"   Chart file: {chart_path}")
        print(f"   Please open and manually inspect the chart.")
        return False


if __name__ == "__main__":
    success = run_macd_backtest()
    sys.exit(0 if success else 1)
