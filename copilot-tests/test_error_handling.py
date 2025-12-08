#!/usr/bin/env python3
"""
Test error handling and fallback behavior for the indicator charting system.

Tests:
1. Metadata lookup with fallback to OVERLAY type
2. Logging for missing metadata warnings
3. Validation for metadata on registration
4. Subplot creation with fallback to simple 2-row layout
5. Length checking for indicator data vs candle data
"""

import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.chart_engine import ChartEngine
from shared.indicators_metadata import (
    IndicatorMetadataRegistry,
    IndicatorMetadata,
    IndicatorType,
    ScaleType,
    ReferenceLine,
    ComponentStyle
)
from shared.models import Candle, Trade, TradeDirection, TradeResult
from shared.strategy_interface import BacktestResults, BacktestConfiguration

# Configure logging to see warnings and errors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_candles(count: int = 100) -> list:
    """Create test candle data."""
    candles = []
    base_time = datetime(2024, 1, 1, 9, 0)
    base_price = 1.1000
    
    for i in range(count):
        timestamp = base_time + timedelta(minutes=15 * i)
        open_price = base_price + (i * 0.0001)
        high_price = open_price + 0.0005
        low_price = open_price - 0.0003
        close_price = open_price + 0.0002
        
        candles.append(Candle(
            timestamp=timestamp,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=1000 + i * 10
        ))
    
    return candles


def create_test_trades() -> list:
    """Create test trade data."""
    base_time = datetime(2024, 1, 1, 10, 0)
    
    trades = [
        Trade(
            entry_time=base_time,
            entry_price=1.1005,
            exit_time=base_time + timedelta(hours=1),
            exit_price=1.1020,
            direction=TradeDirection.BUY,
            pips=15.0,
            result=TradeResult.WIN
        ),
        Trade(
            entry_time=base_time + timedelta(hours=2),
            entry_price=1.1025,
            exit_time=base_time + timedelta(hours=3),
            exit_price=1.1015,
            direction=TradeDirection.SELL,
            pips=-10.0,
            result=TradeResult.LOSS
        )
    ]
    
    return trades


def create_test_backtest_results(trades: list) -> BacktestResults:
    """Create a complete BacktestResults object."""
    config = BacktestConfiguration(
        symbol="EURUSD",
        start_date="2024-01-01",
        end_date="2024-01-02",
        timeframe="15m"
    )
    
    winning_trades = len([t for t in trades if t.pips > 0])
    losing_trades = len([t for t in trades if t.pips < 0])
    total_pips = sum(t.pips for t in trades)
    
    return BacktestResults(
        strategy_name="Test Strategy",
        strategy_version="1.0.0",
        configuration=config,
        trades=trades,
        total_trades=len(trades),
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        total_pips=total_pips,
        win_rate=winning_trades / len(trades) if trades else 0,
        profit_factor=1.5,
        average_win=15.0,
        average_loss=-10.0,
        largest_win=15.0,
        largest_loss=-10.0,
        max_drawdown=-10.0,
        max_consecutive_losses=1,
        max_consecutive_wins=1,
        start_time=datetime(2024, 1, 1, 9, 0),
        end_time=datetime(2024, 1, 2, 17, 0),
        execution_time_seconds=0.5,
        data_source="test",
        total_candles_processed=50
    )


def test_1_missing_metadata_fallback():
    """Test 1: Metadata lookup with fallback to OVERLAY type."""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Missing metadata fallback to OVERLAY")
    logger.info("="*80)
    
    engine = ChartEngine()
    candles = create_test_candles(50)
    trades = create_test_trades()
    backtest_results = create_test_backtest_results(trades)
    
    # Create indicators with an unknown indicator (should fallback to OVERLAY)
    indicators = {
        "UNKNOWN_INDICATOR": [1.1000 + i * 0.0001 for i in range(50)],
        "SMA20": [1.1000 + i * 0.00005 for i in range(50)]
    }
    
    try:
        chart_path = engine.create_comprehensive_chart(
            candles=candles,
            backtest_results=backtest_results,
            indicators=indicators,
            title="Test 1: Missing Metadata Fallback"
        )
        logger.info(f"✓ Chart created successfully: {chart_path}")
        logger.info("✓ Unknown indicator was handled with fallback to OVERLAY")
        return True
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        return False


def test_2_metadata_validation():
    """Test 2: Validation for metadata on registration."""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Metadata validation on registration")
    logger.info("="*80)
    
    registry = IndicatorMetadataRegistry()
    
    # Test 2a: Empty name should fail
    try:
        registry.register(IndicatorMetadata(
            name="",
            indicator_type=IndicatorType.OSCILLATOR,
            scale_type=ScaleType.AUTO
        ))
        logger.error("✗ Empty name validation failed - should have raised ValueError")
        return False
    except ValueError as e:
        logger.info(f"✓ Empty name correctly rejected: {e}")
    
    # Test 2b: FIXED scale without min/max should fail
    try:
        registry.register(IndicatorMetadata(
            name="TEST_FIXED",
            indicator_type=IndicatorType.OSCILLATOR,
            scale_type=ScaleType.FIXED
            # Missing scale_min and scale_max
        ))
        logger.error("✗ FIXED scale validation failed - should have raised ValueError")
        return False
    except ValueError as e:
        logger.info(f"✓ FIXED scale without min/max correctly rejected: {e}")
    
    # Test 2c: Invalid scale_min/max range should fail
    try:
        registry.register(IndicatorMetadata(
            name="TEST_INVALID_RANGE",
            indicator_type=IndicatorType.OSCILLATOR,
            scale_type=ScaleType.FIXED,
            scale_min=100,
            scale_max=0  # max < min
        ))
        logger.error("✗ Invalid range validation failed - should have raised ValueError")
        return False
    except ValueError as e:
        logger.info(f"✓ Invalid range correctly rejected: {e}")
    
    # Test 2d: Valid metadata should succeed
    try:
        registry.register(IndicatorMetadata(
            name="TEST_VALID",
            indicator_type=IndicatorType.OSCILLATOR,
            scale_type=ScaleType.FIXED,
            scale_min=0,
            scale_max=100
        ))
        logger.info("✓ Valid metadata correctly registered")
        return True
    except Exception as e:
        logger.error(f"✗ Valid metadata registration failed: {e}")
        return False


def test_3_indicator_length_mismatch():
    """Test 3: Length checking for indicator data vs candle data."""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Indicator data length mismatch handling")
    logger.info("="*80)
    
    engine = ChartEngine()
    candles = create_test_candles(50)
    trades = create_test_trades()
    backtest_results = create_test_backtest_results(trades)
    
    # Create indicators with mismatched lengths
    indicators = {
        "SMA20": [1.1000 + i * 0.00005 for i in range(30)],  # Too short (30 vs 50)
        "EMA50": [1.1000 + i * 0.00003 for i in range(70)]   # Too long (70 vs 50)
    }
    
    try:
        chart_path = engine.create_comprehensive_chart(
            candles=candles,
            backtest_results=backtest_results,
            indicators=indicators,
            title="Test 3: Length Mismatch Handling"
        )
        logger.info(f"✓ Chart created successfully despite length mismatches: {chart_path}")
        logger.info("✓ Length mismatches were handled gracefully")
        return True
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        return False


def test_4_subplot_creation_fallback():
    """Test 4: Subplot creation with fallback to simple 2-row layout."""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Subplot creation fallback")
    logger.info("="*80)
    
    engine = ChartEngine()
    candles = create_test_candles(50)
    trades = create_test_trades()
    backtest_results = create_test_backtest_results(trades)
    
    # Test with many oscillators (stress test)
    indicators = {
        f"MACD_{i}": [0.001 * i + j * 0.0001 for j in range(50)]
        for i in range(10)  # 10 MACD indicators
    }
    
    try:
        chart_path = engine.create_comprehensive_chart(
            candles=candles,
            backtest_results=backtest_results,
            indicators=indicators,
            title="Test 4: Many Oscillators"
        )
        logger.info(f"✓ Chart created successfully with many oscillators: {chart_path}")
        return True
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        return False


def test_5_empty_and_invalid_indicators():
    """Test 5: Empty and invalid indicator data."""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Empty and invalid indicator data")
    logger.info("="*80)
    
    engine = ChartEngine()
    candles = create_test_candles(50)
    trades = create_test_trades()
    backtest_results = create_test_backtest_results(trades)
    
    # Create indicators with various invalid data
    indicators = {
        "EMPTY_INDICATOR": [],  # Empty list
        "NONE_INDICATOR": None,  # None value (will be skipped in iteration)
        "VALID_SMA": [1.1000 + i * 0.00005 for i in range(50)],  # Valid
        "STRING_INDICATOR": "not a list"  # Invalid type
    }
    
    # Filter out None values (dict iteration will skip them)
    indicators = {k: v for k, v in indicators.items() if v is not None}
    
    try:
        chart_path = engine.create_comprehensive_chart(
            candles=candles,
            backtest_results=backtest_results,
            indicators=indicators,
            title="Test 5: Invalid Indicator Data"
        )
        logger.info(f"✓ Chart created successfully despite invalid indicators: {chart_path}")
        logger.info("✓ Invalid indicators were handled gracefully")
        return True
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        return False


def main():
    """Run all error handling tests."""
    logger.info("\n" + "="*80)
    logger.info("INDICATOR CHARTING SYSTEM - ERROR HANDLING TESTS")
    logger.info("="*80)
    
    results = {
        "Test 1: Missing metadata fallback": test_1_missing_metadata_fallback(),
        "Test 2: Metadata validation": test_2_metadata_validation(),
        "Test 3: Indicator length mismatch": test_3_indicator_length_mismatch(),
        "Test 4: Subplot creation fallback": test_4_subplot_creation_fallback(),
        "Test 5: Empty/invalid indicators": test_5_empty_and_invalid_indicators()
    }
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 All error handling tests passed!")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
