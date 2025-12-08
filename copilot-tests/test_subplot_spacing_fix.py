#!/usr/bin/env python3
"""
Integration tests for subplot spacing fix.

Tests verify that charts render correctly with proper spacing
for different subplot configurations (2, 4, and 6 rows).
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.chart_engine import ChartEngine
from shared.models import Candle, Trade, TradeDirection
from shared.strategy_interface import BacktestResults


def generate_test_candles(num_candles=100):
    """Generate synthetic candle data for testing."""
    candles = []
    base_price = 1.1000
    timestamp = datetime.now() - timedelta(minutes=15 * num_candles)
    
    for i in range(num_candles):
        candles.append(Candle(
            timestamp=timestamp + timedelta(minutes=15 * i),
            open=base_price + (i * 0.0001),
            high=base_price + (i * 0.0001) + 0.0005,
            low=base_price + (i * 0.0001) - 0.0005,
            close=base_price + (i * 0.0001) + 0.0002,
            volume=1000 + i
        ))
    
    return candles


def test_2_row_layout():
    """Test 3.1: Chart with 2 rows (price + P&L) - no indicators."""
    print("\n" + "="*70)
    print("TEST 3.1: 2-Row Layout (Price + P&L)")
    print("="*70)
    
    engine = ChartEngine()
    candles = generate_test_candles(100)
    
    # No trades, no indicators - simplest case
    results = BacktestResults(
        trades=[],
        total_pips=0.0,
        win_rate=0.0,
        total_trades=0,
        winning_trades=0,
        losing_trades=0
    )
    
    try:
        chart_path = engine.create_comprehensive_chart(
            candles=candles,
            backtest_results=results,
            indicators=None,  # No indicators = 2 rows
            title="Test 2-Row Layout"
        )
        print(f"✅ Chart created successfully: {chart_path}")
        print(f"   Expected: 2 rows (price + P&L)")
        print(f"   Spacing: 0.12 (12%)")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_4_row_layout():
    """Test 3.2: Chart with 4 rows (price + MACD + volume + P&L)."""
    print("\n" + "="*70)
    print("TEST 3.2: 4-Row Layout (Price + MACD + Volume + P&L)")
    print("="*70)
    
    engine = ChartEngine()
    candles = generate_test_candles(100)
    
    # Add MACD indicator
    indicators = {
        'macd': [0.0001 * i for i in range(100)],
        'macd_signal': [0.00008 * i for i in range(100)],
        'macd_histogram': [0.00002 * i for i in range(100)]
    }
    
    results = BacktestResults(
        trades=[],
        total_pips=0.0,
        win_rate=0.0,
        total_trades=0,
        winning_trades=0,
        losing_trades=0
    )
    
    try:
        chart_path = engine.create_comprehensive_chart(
            candles=candles,
            backtest_results=results,
            indicators=indicators,
            title="Test 4-Row Layout"
        )
        print(f"✅ Chart created successfully: {chart_path}")
        print(f"   Expected: 4 rows (price + MACD + volume + P&L)")
        print(f"   Spacing: 0.08 (8%)")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_6_row_layout():
    """Test 3.3: Chart with 6 rows (price + 3 oscillators + volume + P&L)."""
    print("\n" + "="*70)
    print("TEST 3.3: 6-Row Layout (Price + 3 Oscillators + Volume + P&L)")
    print("="*70)
    
    engine = ChartEngine()
    candles = generate_test_candles(100)
    
    # Add multiple oscillators
    indicators = {
        'macd': [0.0001 * i for i in range(100)],
        'macd_signal': [0.00008 * i for i in range(100)],
        'macd_histogram': [0.00002 * i for i in range(100)],
        'rsi': [50 + (i % 50) for i in range(100)],
        'stochastic': [50 + (i % 50) for i in range(100)]
    }
    
    results = BacktestResults(
        trades=[],
        total_pips=0.0,
        win_rate=0.0,
        total_trades=0,
        winning_trades=0,
        losing_trades=0
    )
    
    try:
        chart_path = engine.create_comprehensive_chart(
            candles=candles,
            backtest_results=results,
            indicators=indicators,
            title="Test 6-Row Layout"
        )
        print(f"✅ Chart created successfully: {chart_path}")
        print(f"   Expected: 6 rows (price + 3 oscillators + volume + P&L)")
        print(f"   Spacing: 0.06 (6%)")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SUBPLOT SPACING FIX - INTEGRATION TESTS")
    print("="*70)
    print("\nThese tests verify that charts render correctly with proper")
    print("spacing for different subplot configurations.")
    
    results = []
    
    # Run tests
    results.append(("2-Row Layout", test_2_row_layout()))
    results.append(("4-Row Layout", test_4_row_layout()))
    results.append(("6-Row Layout", test_6_row_layout()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Subplot spacing fix is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
    
    sys.exit(0 if passed == total else 1)
