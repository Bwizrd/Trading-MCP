#!/usr/bin/env python3
"""
Diagnostic Tools for Strategy Backtesting

Provides optional detailed CSV exports for debugging and analysis.
Enable by setting BACKTEST_DIAGNOSTICS=true environment variable.
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from shared.models import Candle, Trade

logger = logging.getLogger(__name__)


def is_diagnostics_enabled() -> bool:
    """Check if diagnostics are enabled via environment variable."""
    return os.getenv('BACKTEST_DIAGNOSTICS', 'false').lower() in ('true', '1', 'yes')


def export_diagnostic_csv(
    candles: List[Candle],
    trades: List[Trade],
    indicator_series: Dict[str, List[float]],
    trend_filter_data: Optional[Dict[datetime, float]] = None,
    strategy_name: str = "strategy",
    symbol: str = "SYMBOL",
    output_dir: str = "optimization_results/diagnostics"
) -> Optional[str]:
    """
    Export detailed diagnostic CSV with OHLCV, indicators, and trade markers.
    
    Args:
        candles: List of candles with OHLCV data
        trades: List of executed trades
        indicator_series: Dict of indicator name -> list of values (aligned with candles)
        trend_filter_data: Optional dict of timestamp -> trend filter value
        strategy_name: Name of the strategy
        symbol: Trading symbol
        output_dir: Directory to save the CSV
        
    Returns:
        Path to the created CSV file, or None if diagnostics disabled
    """
    if not is_diagnostics_enabled():
        logger.debug("Diagnostics disabled, skipping CSV export")
        return None
    
    try:
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"diagnostic_{symbol}_{strategy_name.replace(' ', '_')}_{timestamp}.csv"
        filepath = output_path / filename
        
        # Create trade lookup for fast access
        trade_entries = {trade.entry_time: trade for trade in trades}
        trade_exits = {trade.exit_time: trade for trade in trades}
        
        # Prepare CSV headers
        headers = [
            'timestamp', 'date', 'time',
            'open', 'high', 'low', 'close', 'volume',
        ]
        
        # Add indicator headers
        indicator_names = sorted(indicator_series.keys())
        headers.extend(indicator_names)
        
        # Add trend filter column if provided
        if trend_filter_data:
            headers.append('trend_filter_pips')
        
        # Add trade marker columns
        headers.extend([
            'trade_entry', 'trade_direction', 'entry_price',
            'trade_exit', 'exit_price', 'exit_reason', 'pips'
        ])
        
        # Write CSV
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for i, candle in enumerate(candles):
                row = {
                    'timestamp': candle.timestamp.isoformat(),
                    'date': candle.timestamp.strftime('%Y-%m-%d'),
                    'time': candle.timestamp.strftime('%H:%M:%S'),
                    'open': f"{candle.open:.5f}",
                    'high': f"{candle.high:.5f}",
                    'low': f"{candle.low:.5f}",
                    'close': f"{candle.close:.5f}",
                    'volume': candle.volume,
                }
                
                # Add indicator values
                for ind_name in indicator_names:
                    if i < len(indicator_series[ind_name]):
                        value = indicator_series[ind_name][i]
                        row[ind_name] = f"{value:.2f}" if value is not None else ''
                    else:
                        row[ind_name] = ''
                
                # Add trend filter value if available
                if trend_filter_data and candle.timestamp in trend_filter_data:
                    row['trend_filter_pips'] = f"{trend_filter_data[candle.timestamp]:.2f}"
                elif trend_filter_data:
                    row['trend_filter_pips'] = ''
                
                # Check for trade entry
                if candle.timestamp in trade_entries:
                    trade = trade_entries[candle.timestamp]
                    row['trade_entry'] = 'ENTRY'
                    row['trade_direction'] = trade.direction.value
                    row['entry_price'] = f"{trade.entry_price:.5f}"
                else:
                    row['trade_entry'] = ''
                    row['trade_direction'] = ''
                    row['entry_price'] = ''
                
                # Check for trade exit
                if candle.timestamp in trade_exits:
                    trade = trade_exits[candle.timestamp]
                    row['trade_exit'] = 'EXIT'
                    row['exit_price'] = f"{trade.exit_price:.5f}"
                    row['exit_reason'] = trade.exit_reason if hasattr(trade, 'exit_reason') else ''
                    row['pips'] = f"{trade.pips:+.1f}"
                else:
                    row['trade_exit'] = ''
                    row['exit_price'] = ''
                    row['exit_reason'] = ''
                    row['pips'] = ''
                
                writer.writerow(row)
        
        logger.info(f"✅ Diagnostic CSV exported: {filepath}")
        logger.info(f"   Rows: {len(candles)} | Trades: {len(trades)} | Indicators: {len(indicator_names)}")
        
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Failed to export diagnostic CSV: {e}", exc_info=True)
        return None


def export_stochastic_diagnostic_csv(
    candles: List[Candle],
    trades: List[Trade],
    stochastic_data: Dict[str, Dict[str, List[float]]],
    trend_filter_data: Optional[Dict[datetime, float]] = None,
    strategy_name: str = "Stochastic Quad Rotation",
    symbol: str = "SYMBOL",
    output_dir: str = "optimization_results/diagnostics"
) -> Optional[str]:
    """
    Specialized export for stochastic strategies with %K and %D values.
    
    Args:
        candles: List of candles
        trades: List of trades
        stochastic_data: Dict with structure {'fast': {'k': [...], 'd': [...]}, ...}
        trend_filter_data: Optional trend filter values
        strategy_name: Strategy name
        symbol: Trading symbol
        output_dir: Output directory
        
    Returns:
        Path to created CSV or None
    """
    # Flatten stochastic data into indicator series format
    indicator_series = {}
    for alias, data in stochastic_data.items():
        if 'k' in data:
            indicator_series[f"{alias}_k"] = data['k']
        if 'd' in data:
            indicator_series[f"{alias}_d"] = data['d']
    
    return export_diagnostic_csv(
        candles=candles,
        trades=trades,
        indicator_series=indicator_series,
        trend_filter_data=trend_filter_data,
        strategy_name=strategy_name,
        symbol=symbol,
        output_dir=output_dir
    )
