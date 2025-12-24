#!/usr/bin/env python3
"""
Modular Chart Engine

Pure visualization engine that receives backtest results and creates charts.
NO STRATEGY LOGIC - only consumes results from the Universal Backtest Engine.

Architecture:
Strategy Cartridges → Backtest Engine → Chart Engine → HTML/PNG Charts

Uses POC-validated spacing calculation for proper subplot separation.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging

# Chart libraries
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import pandas as pd

# Project imports
from shared.models import Candle, Trade, TradeDirection
from shared.strategy_interface import BacktestResults
from shared.utils import ensure_directory_exists, sanitize_symbol, format_timestamp

logger = logging.getLogger(__name__)


class ChartEngine:
    """
    Pure chart engine that visualizes backtest results.
    
    Takes backtest results as input and generates interactive charts.
    Contains NO trading strategy logic - only visualization logic.
    """
    
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            # Use absolute path relative to project root
            project_root = Path(__file__).parent.parent
            output_dir = project_root / "data" / "charts"
        self.output_dir = Path(output_dir)
        ensure_directory_exists(str(self.output_dir))
        
        # Chart styling
        self.chart_theme = "plotly_white"
        self.colors = {
            'buy_signal': '#00FF00',
            'sell_signal': '#FF0000',
            'buy_line': '#4CAF50',
            'sell_line': '#F44336',
            'win_trade': '#4CAF50',
            'loss_trade': '#F44336',
            'vwap': '#FF9800',
            'candle_up': '#4CAF50',
            'candle_down': '#F44336',
            'sma20 (fast)': '#2196F3',  # Blue for fast MA
            'sma50 (slow)': '#FF9800',  # Orange for slow MA
            'fast_ma': '#2196F3',       # Alternative naming
            'slow_ma': '#FF9800',       # Alternative naming
        }
    
    def _determine_subplot_layout(self, indicators: Dict[str, List[float]]) -> Dict[str, int]:
        """
        Determine subplot layout based on indicator types.
        
        Analyzes indicators and returns a mapping of subplot names to row numbers.
        Price chart is always row 1, oscillators get sequential rows, followed by
        volume and P&L.
        
        Handles multiple instances of the same oscillator type by giving each its
        own subplot. For example, 4 Stochastic indicators with different parameters
        will each get their own subplot with descriptive titles.
        
        Includes error handling for metadata lookup failures.
        
        Args:
            indicators: Dictionary of indicator names to their values
            
        Returns:
            Dict mapping subplot names to row numbers
            Example: {"price": 1, "oscillator_1": 2, "oscillator_2": 3, "volume": 4, "pnl": 5}
        """
        from shared.indicators_metadata import metadata_registry
        
        layout = {"price": 1}
        current_row = 2
        
        # Track oscillator count for naming
        oscillator_count = 0
        oscillator_mapping = {}  # Map indicator name to oscillator index
        
        # Check for oscillators and assign them to subplots
        # Each oscillator gets its own subplot, even if they're the same type
        if indicators:
            # Sort for consistent ordering
            for indicator_name in sorted(indicators.keys()):
                try:
                    # Skip MACD signal and histogram - they're rendered with the main MACD line
                    if indicator_name.endswith('_signal') or indicator_name.endswith('_histogram'):
                        continue
                    
                    # Skip stochastic %D - it's rendered with the %K line
                    if indicator_name.endswith('_d'):
                        continue
                    
                    # Check if oscillator with error handling
                    is_oscillator = False
                    try:
                        is_oscillator = metadata_registry.is_oscillator(indicator_name)
                    except Exception as e:
                        logger.error(f"Error checking if '{indicator_name}' is oscillator: {e}")
                        # Assume not an oscillator if we can't determine
                        is_oscillator = False
                    
                    if is_oscillator:
                        oscillator_count += 1
                        layout[f"oscillator_{oscillator_count}"] = current_row
                        oscillator_mapping[indicator_name] = oscillator_count
                        current_row += 1
                        logger.info(f"Assigned {indicator_name} to oscillator_{oscillator_count} (row {current_row - 1})")
                        
                except Exception as e:
                    logger.error(f"Error processing indicator '{indicator_name}' in layout determination: {e}")
                    continue
        
        # Add volume subplot
        layout["volume"] = current_row
        current_row += 1
        
        # Add P&L subplot
        layout["pnl"] = current_row
        
        # Store oscillator mapping for later use in title generation
        self._oscillator_mapping = oscillator_mapping
        
        logger.info(f"Subplot layout determined: {layout}")
        logger.info(f"Oscillator mapping: {oscillator_mapping}")
        
        return layout
    
    def _calculate_row_heights(self, layout: Dict[str, int], vertical_spacing: float) -> List[float]:
        """
        Calculate proportional heights for each subplot row accounting for vertical spacing.
        
        CRITICAL: Row heights must sum to (1.0 - total_spacing), NOT 1.0!
        This is the key insight from the POC that fixes the overlap issue.
        
        Allocates vertical space according to the design:
        - Price chart: 45% of available space
        - Oscillators: 35% of available space (divided equally among all oscillators)
        - Volume: 10% of available space
        - P&L: 10% of available space
        
        Available space = 1.0 - (num_rows - 1) × vertical_spacing
        
        When there are no oscillators, the 35% is redistributed to the price chart.
        
        Args:
            layout: Subplot layout mapping from _determine_subplot_layout()
            vertical_spacing: Spacing between rows (from create_comprehensive_chart)
            
        Returns:
            List of height proportions for each row (must sum to available_space)
        """
        total_rows = max(layout.values())
        oscillator_rows = [k for k in layout.keys() if k.startswith("oscillator_")]
        num_oscillators = len(oscillator_rows)
        
        # Calculate available space after accounting for spacing
        total_spacing = (total_rows - 1) * vertical_spacing
        available_space = 1.0 - total_spacing
        
        logger.info(f"Row height calculation: {total_rows} rows, spacing={vertical_spacing:.3f}")
        logger.info(f"Total spacing: {total_spacing:.3f}, Available space: {available_space:.3f}")
        
        # Adjust price chart height based on whether we have oscillators
        if num_oscillators > 0:
            price_pct = 0.45  # 45% of available space
            oscillator_pct = 0.35  # 35% of available space
        else:
            price_pct = 0.8  # 80% of available space (takes the 35% that would go to oscillators)
            oscillator_pct = 0.0
        
        # Calculate actual heights from available space
        price_height = price_pct * available_space
        oscillator_total = oscillator_pct * available_space
        volume_height = 0.10 * available_space
        pnl_height = 0.10 * available_space
        
        heights = []
        for row in range(1, total_rows + 1):
            if row == layout["price"]:
                heights.append(price_height)
            elif any(layout[osc] == row for osc in oscillator_rows):
                # Divide oscillator space equally among all oscillators
                heights.append(oscillator_total / num_oscillators)
            elif row == layout.get("volume"):
                heights.append(volume_height)
            elif row == layout.get("pnl"):
                heights.append(pnl_height)
            else:
                # Fallback for any unexpected rows
                heights.append(0.05 * available_space)
        
        # Verify the math
        heights_sum = sum(heights)
        logger.info(f"Heights sum: {heights_sum:.4f}, Expected: {available_space:.4f}")
        logger.info(f"Total allocation: {heights_sum:.4f} + {total_spacing:.4f} = {heights_sum + total_spacing:.4f}")
        
        if abs(heights_sum - available_space) > 0.0001:
            logger.warning(f"Heights sum ({heights_sum:.4f}) doesn't match available space ({available_space:.4f})")
        
        return heights
    
    def _generate_subplot_titles(self, layout: Dict[str, int], main_title: str, indicators: Dict[str, List[float]] = None) -> List[str]:
        """
        Generate titles for each subplot based on the layout.
        
        Improved to show actual indicator names for oscillator subplots instead of
        generic "Oscillator 1", "Oscillator 2". For example:
        - "MACD" for MACD indicator
        - "RSI (14)" for RSI with period 14
        - "Stochastic (14,3,3)" for Stochastic with parameters
        
        Handles multiple instances of the same oscillator type by showing parameters.
        
        Args:
            layout: Subplot layout mapping from _determine_subplot_layout()
            main_title: Main chart title
            indicators: Dictionary of indicator names to values (optional)
            
        Returns:
            List of subplot titles in row order
        """
        total_rows = max(layout.values())
        titles = [""] * total_rows
        
        # Create reverse mapping: oscillator_index -> indicator_name
        oscillator_to_indicator = {}
        if indicators and hasattr(self, '_oscillator_mapping'):
            for indicator_name, osc_index in self._oscillator_mapping.items():
                oscillator_to_indicator[osc_index] = indicator_name
        
        for subplot_name, row_num in layout.items():
            row_index = row_num - 1  # Convert to 0-based index
            
            if subplot_name == "price":
                titles[row_index] = f"{main_title} - Price Action"
            elif subplot_name.startswith("oscillator_"):
                # Extract oscillator number
                osc_num = int(subplot_name.split("_")[1])
                
                # Try to get the actual indicator name
                if osc_num in oscillator_to_indicator:
                    indicator_name = oscillator_to_indicator[osc_num]
                    # Format the indicator name nicely
                    titles[row_index] = self._format_indicator_title(indicator_name)
                else:
                    # Fallback to generic name
                    titles[row_index] = f"Oscillator {osc_num}"
            elif subplot_name == "volume":
                titles[row_index] = "Volume"
            elif subplot_name == "pnl":
                titles[row_index] = "Cumulative P&L"
            else:
                titles[row_index] = subplot_name.replace("_", " ").title()
        
        return titles
    
    def _format_indicator_title(self, indicator_name: str) -> str:
        """
        Format indicator name into a nice title for subplot.
        
        Examples:
        - "macd" -> "MACD"
        - "rsi_14" -> "RSI (14)"
        - "stochastic_14_3_3" -> "Stochastic (14,3,3)"
        - "macd_12_26_9" -> "MACD (12,26,9)"
        
        Args:
            indicator_name: Raw indicator name from strategy
            
        Returns:
            Formatted title string
        """
        # Split on underscores
        parts = indicator_name.split('_')
        
        # First part is the base indicator name
        base_name = parts[0].upper()
        
        # Remaining parts are parameters
        params = parts[1:]
        
        # Filter out non-numeric parameters (like "signal", "histogram")
        numeric_params = [p for p in params if p.replace('.', '').replace('-', '').isdigit()]
        
        if numeric_params:
            # Format with parameters
            params_str = ','.join(numeric_params)
            return f"{base_name} ({params_str})"
        else:
            # Just the base name
            return base_name
    
    def _get_oscillator_index(self, indicator_name: str, layout: Dict[str, int]) -> int:
        """
        Get the oscillator subplot index for a given indicator.
        
        Args:
            indicator_name: Name of the indicator
            layout: Subplot layout mapping
            
        Returns:
            Oscillator index (1-based) for the indicator
        """
        # Use the mapping created in _determine_subplot_layout
        if hasattr(self, '_oscillator_mapping') and indicator_name in self._oscillator_mapping:
            return self._oscillator_mapping[indicator_name]
        
        # Fallback: find first available oscillator subplot
        oscillator_keys = [k for k in layout.keys() if k.startswith("oscillator_")]
        if oscillator_keys:
            # Extract the number from "oscillator_1", "oscillator_2", etc.
            return int(oscillator_keys[0].split("_")[1])
        
        # Default to 1 if no oscillators found
        return 1
    
    def create_comprehensive_chart(
        self,
        candles: List[Candle],
        backtest_results: BacktestResults,
        indicators: Dict[str, List[float]] = None,
        title: str = "Trading Strategy Results"
    ) -> str:
        """
        Create a comprehensive trading chart with all results.
        
        Uses dynamic layout based on indicators - oscillators get their own subplots,
        overlays appear on the price chart. Maintains backward compatibility by
        handling cases with no indicators.
        
        Args:
            candles: Market data (OHLCV)
            backtest_results: Results from Universal Backtest Engine
            indicators: Technical indicators (VWAP, SMA, MACD, RSI, etc.)
            title: Chart title
            
        Returns:
            Path to generated HTML chart file
        """
        logger.info(f"Creating comprehensive chart with {len(candles)} candles and {len(backtest_results.trades)} trades")
        
        # Convert candles to DataFrame for easier processing
        df = self._candles_to_dataframe(candles)
        
        # Determine subplot layout based on indicators with error handling
        try:
            layout = self._determine_subplot_layout(indicators or {})
            
            # Get total number of rows
            total_rows = max(layout.values())
            
            # Calculate appropriate vertical spacing based on number of rows
            # EXACT FORMULA FROM POC (poc_subplot_spacing.py)
            # This spacing calculation is proven to work correctly
            if total_rows <= 1:
                spacing = 0.0
            elif total_rows == 2:
                spacing = 0.12  # 12% spacing for 2 rows
            elif total_rows == 3:
                spacing = 0.10  # 10% spacing for 3 rows
            elif total_rows == 4:
                spacing = 0.08  # 8% spacing for 4 rows
            else:  # 5 or more rows
                spacing = 0.06  # 6% spacing for 5+ rows
            
            # Calculate row heights accounting for spacing (CRITICAL FIX!)
            row_heights = self._calculate_row_heights(layout, spacing)
            
            # Store layout for use in _add_indicators
            self._current_layout = layout
            
            # Generate subplot titles with indicator names
            subplot_titles = self._generate_subplot_titles(layout, title, indicators)
            
            logger.info(f"Creating chart with {total_rows} rows: {list(layout.keys())}")
            logger.info(f"Vertical spacing: {spacing:.3f}")
            logger.info(f"Row heights: {[f'{h:.4f}' for h in row_heights]}")
            logger.info(f"Subplot titles: {subplot_titles}")
            
        except Exception as e:
            logger.error(f"Error determining subplot layout: {e}. Falling back to simple 2-row layout.")
            # Fallback to simple 2-row layout (price + P&L)
            layout = {"price": 1, "pnl": 2}
            total_rows = 2
            spacing = 0.12
            row_heights = self._calculate_row_heights(layout, spacing)
            subplot_titles = [f"{title} - Price Action", "Cumulative P&L"]
            self._current_layout = layout
        
        # Validate layout before creating subplots
        # Basic sanity checks - only fail on clearly invalid values
        if not row_heights or len(row_heights) == 0:
            logger.error("Row heights list is empty! Using fallback.")
            layout = {"price": 1, "pnl": 2}
            total_rows = 2
            spacing = 0.12
            row_heights = self._calculate_row_heights(layout, spacing)
            subplot_titles = [f"{title} - Price Action", "Cumulative P&L"]
            self._current_layout = layout
        
        if spacing < 0:
            logger.warning(f"Negative spacing detected ({spacing:.3f}), using 0.08 instead")
            spacing = 0.08
        
        if any(h <= 0 for h in row_heights):
            logger.warning(f"Non-positive height detected in {row_heights}, this may cause issues")
        
        # Log final configuration for debugging
        logger.info(f"Final layout validation: {total_rows} rows, spacing={spacing:.3f}, heights sum={sum(row_heights):.4f}")
        
        # Create subplots with error handling
        # Using POC approach: simple, direct call without specs parameter
        try:
            fig = make_subplots(
                rows=total_rows,
                cols=1,
                row_heights=row_heights,
                vertical_spacing=spacing,
                subplot_titles=subplot_titles,
                shared_xaxes=True
            )
        except Exception as e:
            logger.error(f"Error creating subplots with {total_rows} rows: {e}")
            logger.error(f"Failed configuration: rows={total_rows}, spacing={spacing:.3f}, heights={row_heights}")
            logger.error(f"Falling back to simple 2-row layout (price + P&L)")
            
            # Fallback to simple 2-row layout
            layout = {"price": 1, "pnl": 2}
            row_heights = [0.8, 0.2]
            subplot_titles = [f"{title} - Price Action", "Cumulative P&L"]
            total_rows = 2
            spacing = 0.12
            self._current_layout = layout
            
            try:
                fig = make_subplots(
                    rows=total_rows,
                    cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.03,
                    subplot_titles=subplot_titles,
                    row_heights=row_heights
                )
            except Exception as fallback_error:
                logger.error(f"Fallback subplot creation also failed: {fallback_error}")
                raise RuntimeError(f"Unable to create chart subplots: {fallback_error}")
        
        # 1. Candlestick chart (always on price row)
        try:
            self._add_candlestick_chart(fig, df, row=layout["price"])
            # Disable range slider to prevent overlap with subplots below
            fig.update_xaxes(rangeslider_visible=False, row=layout["price"], col=1)
        except Exception as e:
            logger.error(f"Error adding candlestick chart: {e}")
            raise RuntimeError(f"Failed to create candlestick chart: {e}")
        
        # 2. Add technical indicators using routing logic
        if indicators:
            # Store indicators dictionary so MACD can access signal/histogram
            self._current_indicators = indicators
            
            timestamps = df['timestamp'].tolist()
            for indicator_name, values in indicators.items():
                try:
                    # Skip MACD signal and histogram - they'll be added with the main MACD line
                    if indicator_name.endswith('_signal') or indicator_name.endswith('_histogram'):
                        base_name = indicator_name.replace('_signal', '').replace('_histogram', '')
                        if base_name in indicators or 'macd' in base_name.lower():
                            logger.info(f"Skipping {indicator_name} - will be rendered with MACD line")
                            continue
                    
                    # Skip stochastic %D - it'll be added with the %K line
                    if indicator_name.endswith('_d'):
                        base_name = indicator_name.replace('_d', '')
                        if base_name in indicators:
                            logger.info(f"Skipping {indicator_name} - will be rendered with {base_name} %K line")
                            continue
                    
                    # Validate indicator data
                    if not values:
                        logger.warning(f"Indicator '{indicator_name}' has no data, skipping")
                        continue
                    
                    if not isinstance(values, (list, tuple)):
                        logger.warning(f"Indicator '{indicator_name}' data is not a list/tuple, skipping")
                        continue
                    
                    # Check length mismatch
                    if len(values) != len(timestamps):
                        logger.warning(f"Indicator '{indicator_name}' length ({len(values)}) does not match "
                                     f"candle data length ({len(timestamps)}). Data will be aligned.")
                    
                    self._route_indicator_to_subplot(
                        fig, indicator_name, values, timestamps, layout
                    )
                except Exception as e:
                    logger.error(f"Error adding indicator '{indicator_name}': {e}. Skipping this indicator.")
                    continue
        
        # 3. Add trade signals and lines (on price chart)
        try:
            self._add_trade_signals(fig, backtest_results.trades, row=layout["price"])
            self._add_trade_lines(fig, backtest_results.trades, row=layout["price"])
        except Exception as e:
            logger.error(f"Error adding trade signals/lines: {e}")
            # Non-critical, continue without trade markers
        
        # 4. Volume chart (if volume subplot exists in layout)
        if "volume" in layout:
            try:
                self._add_volume_chart(fig, df, row=layout["volume"])
            except Exception as e:
                logger.error(f"Error adding volume chart: {e}")
                # Non-critical, continue without volume
        
        # 5. P&L chart
        try:
            self._add_pnl_chart(fig, backtest_results.trades, row=layout["pnl"])
        except Exception as e:
            logger.error(f"Error adding P&L chart: {e}")
            # Non-critical, continue without P&L
        
        # 6. Update layout
        try:
            self._update_layout(fig, title, backtest_results)
        except Exception as e:
            logger.error(f"Error updating chart layout: {e}")
            # Non-critical, continue with default layout
        
        # 7. Save chart
        try:
            chart_path = self._save_chart(fig, title, backtest_results)
        except Exception as e:
            logger.error(f"Error saving chart: {e}")
            raise RuntimeError(f"Failed to save chart: {e}")
        
        # Clean up temporary attributes
        if hasattr(self, '_current_layout'):
            delattr(self, '_current_layout')
        if hasattr(self, '_oscillator_mapping'):
            delattr(self, '_oscillator_mapping')
        if hasattr(self, '_current_indicators'):
            delattr(self, '_current_indicators')
        
        return chart_path
    
    def create_performance_summary_chart(
        self,
        backtest_results: BacktestResults,
        title: str = "Strategy Performance"
    ) -> str:
        """
        Create a performance-focused chart with statistics.
        
        Args:
            backtest_results: Results from Universal Backtest Engine
            title: Chart title
            
        Returns:
            Path to generated HTML chart file
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Trade Distribution',
                'P&L Over Time',
                'Win/Loss Analysis',
                'Monthly Performance'
            ]
        )
        
        trades = backtest_results.trades
        
        # 1. Trade distribution histogram
        pips = [trade.pips for trade in trades]
        fig.add_trace(
            go.Histogram(x=pips, name="Trade Distribution", nbinsx=20),
            row=1, col=1
        )
        
        # 2. Cumulative P&L
        cumulative_pnl = []
        running_total = 0
        for trade in trades:
            running_total += trade.pips
            cumulative_pnl.append(running_total)
        
        fig.add_trace(
            go.Scatter(
                y=cumulative_pnl,
                mode='lines',
                name="Cumulative P&L",
                line=dict(color=self.colors['buy_line'])
            ),
            row=1, col=2
        )
        
        # 3. Win/Loss pie chart
        wins = len([t for t in trades if t.pips > 0])
        losses = len(trades) - wins
        
        fig.add_trace(
            go.Pie(
                labels=['Wins', 'Losses'],
                values=[wins, losses],
                marker_colors=[self.colors['win_trade'], self.colors['loss_trade']]
            ),
            row=2, col=1
        )
        
        # 4. Monthly performance (if enough data)
        if len(trades) > 0:
            monthly_data = self._calculate_monthly_performance(trades)
            fig.add_trace(
                go.Bar(
                    x=list(monthly_data.keys()),
                    y=list(monthly_data.values()),
                    name="Monthly P&L"
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            title=title,
            showlegend=True,
            theme=self.chart_theme,
            height=800
        )
        
        # Save chart
        chart_path = self._save_chart(fig, f"{title}_performance", backtest_results)
        
        return chart_path
    
    def _candles_to_dataframe(self, candles: List[Candle]) -> pd.DataFrame:
        """Convert list of Candle objects to DataFrame."""
        data = []
        for candle in candles:
            data.append({
                'timestamp': candle.timestamp,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume
            })
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.sort_values('timestamp')
    
    def _add_candlestick_chart(self, fig, df: pd.DataFrame, row: int):
        """Add candlestick chart to subplot."""
        fig.add_trace(
            go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name="Price",
                increasing_line_color=self.colors['candle_up'],
                decreasing_line_color=self.colors['candle_down']
            ),
            row=row, col=1
        )
    
    def _route_indicator_to_subplot(
        self,
        fig,
        indicator_name: str,
        values: List[float],
        timestamps: List,
        layout: Dict[str, int]
    ):
        """
        Route indicator to appropriate subplot based on metadata.
        
        This method queries the indicator metadata registry to determine whether
        an indicator should be displayed as an overlay on the price chart or in
        a separate oscillator subplot. It then applies the appropriate styling
        and scaling based on the metadata.
        
        Includes error handling:
        - Falls back to OVERLAY type if metadata is missing
        - Validates indicator data length matches candle data
        - Handles exceptions during routing gracefully
        
        Args:
            fig: Plotly figure object
            indicator_name: Name of the indicator (e.g., "MACD", "SMA20")
            values: List of indicator values
            timestamps: List of timestamps corresponding to values
            layout: Subplot layout mapping from _determine_subplot_layout()
        """
        from shared.indicators_metadata import metadata_registry, IndicatorType, ScaleType
        
        try:
            # Validate indicator data length
            if len(values) != len(timestamps):
                logger.warning(f"Indicator '{indicator_name}' data length ({len(values)}) does not match "
                             f"timestamp length ({len(timestamps)}). Will attempt to align data.")
                # Truncate to shorter length to avoid index errors
                min_length = min(len(values), len(timestamps))
                values = values[:min_length]
                timestamps = timestamps[:min_length]
            
            # Query metadata for this indicator with error handling
            metadata = None
            try:
                metadata = metadata_registry.get(indicator_name)
            except Exception as e:
                logger.error(f"Error querying metadata for '{indicator_name}': {e}")
            
            if not metadata:
                # Fallback: assume overlay and log warning
                logger.warning(f"No metadata found for indicator '{indicator_name}', treating as OVERLAY (fallback behavior)")
                try:
                    self._add_indicator_trace(fig, indicator_name, values, timestamps, layout["price"])
                except Exception as e:
                    logger.error(f"Error adding indicator '{indicator_name}' to price chart: {e}")
                return
        
            # Route based on indicator type
            if metadata.indicator_type == IndicatorType.OVERLAY:
                # Add to price chart
                logger.info(f"Routing {indicator_name} to price chart (OVERLAY)")
                try:
                    self._add_indicator_trace(fig, indicator_name, values, timestamps, layout["price"])
                except Exception as e:
                    logger.error(f"Error adding overlay indicator '{indicator_name}': {e}")
            
            elif metadata.indicator_type == IndicatorType.OSCILLATOR:
                try:
                    # Find which oscillator subplot to use
                    oscillator_index = self._get_oscillator_index(indicator_name, layout)
                    row = layout[f"oscillator_{oscillator_index}"]
                    
                    logger.info(f"Routing {indicator_name} to oscillator subplot {oscillator_index} (row {row})")
                    
                    # Add oscillator trace with proper styling
                    self._add_oscillator_trace(fig, indicator_name, values, timestamps, row, metadata)
                    
                    # Add reference lines (zero line, overbought/oversold)
                    if metadata.zero_line:
                        logger.info(f"Adding zero line for {indicator_name}")
                        try:
                            fig.add_hline(
                                y=0,
                                line_dash="dash",
                                line_color="gray",
                                line_width=1,
                                row=row,
                                col=1
                            )
                        except Exception as e:
                            logger.error(f"Error adding zero line for '{indicator_name}': {e}")
                    
                    # Add additional reference lines (e.g., RSI 30/70, Stochastic 20/80)
                    for ref_line in metadata.reference_lines:
                        logger.info(f"Adding reference line at {ref_line.value} for {indicator_name}")
                        try:
                            fig.add_hline(
                                y=ref_line.value,
                                line_dash=ref_line.style,
                                line_color=ref_line.color,
                                line_width=1,
                                annotation_text=ref_line.label,
                                annotation_position="right",
                                row=row,
                                col=1
                            )
                        except Exception as e:
                            logger.error(f"Error adding reference line at {ref_line.value} for '{indicator_name}': {e}")
                    
                    # Apply y-axis scaling based on metadata
                    try:
                        self._apply_scaling(fig, metadata, values, row)
                    except Exception as e:
                        logger.error(f"Error applying scaling for '{indicator_name}': {e}")
                        
                except Exception as e:
                    logger.error(f"Error adding oscillator indicator '{indicator_name}': {e}")
                    # Fallback: try to add to price chart
                    logger.info(f"Attempting fallback: adding '{indicator_name}' to price chart")
                    try:
                        self._add_indicator_trace(fig, indicator_name, values, timestamps, layout["price"])
                    except Exception as fallback_error:
                        logger.error(f"Fallback also failed for '{indicator_name}': {fallback_error}")
        
        except Exception as e:
            logger.error(f"Unexpected error routing indicator '{indicator_name}': {e}")
            # Final fallback: try to add to price chart
            try:
                self._add_indicator_trace(fig, indicator_name, values, timestamps, layout.get("price", 1))
            except Exception as final_error:
                logger.error(f"Final fallback failed for '{indicator_name}': {final_error}")
    
    def _apply_scaling(
        self,
        fig,
        metadata,
        values: List[float],
        row: int
    ):
        """
        Apply y-axis scaling based on indicator metadata.
        
        Supports three scale types:
        - FIXED: Set y-axis to [scale_min, scale_max] from metadata
        - AUTO: Calculate range from indicator values with padding
        - PRICE: Share y-axis with price chart (no action needed)
        
        Includes error handling for invalid values and edge cases.
        
        Args:
            fig: Plotly figure object
            metadata: IndicatorMetadata object with scale configuration
            values: List of indicator values (for AUTO scaling)
            row: Row number for the subplot
        """
        from shared.indicators_metadata import ScaleType
        
        try:
            if metadata.scale_type == ScaleType.FIXED:
                # Apply fixed scale from metadata
                logger.info(f"Applying FIXED scale [{metadata.scale_min}, {metadata.scale_max}] for {metadata.name}")
                try:
                    fig.update_yaxes(
                        range=[metadata.scale_min, metadata.scale_max],
                        row=row,
                        col=1
                    )
                except Exception as e:
                    logger.error(f"Error applying FIXED scale for {metadata.name}: {e}")
            
            elif metadata.scale_type == ScaleType.AUTO:
                # Calculate range from indicator values with padding
                logger.info(f"Applying AUTO scale for {metadata.name}")
                
                try:
                    # Filter out None and NaN values
                    valid_values = [v for v in values if v is not None and not (isinstance(v, float) and v != v)]
                    
                    if valid_values:
                        min_val = min(valid_values)
                        max_val = max(valid_values)
                        
                        # Add 10% padding on each side for better visualization
                        value_range = max_val - min_val
                        if value_range > 0:
                            padding = value_range * 0.1
                            y_min = min_val - padding
                            y_max = max_val + padding
                        else:
                            # If all values are the same, add fixed padding
                            y_min = min_val - 0.1
                            y_max = max_val + 0.1
                        
                        logger.info(f"AUTO scale calculated: [{y_min:.5f}, {y_max:.5f}] from values [{min_val:.5f}, {max_val:.5f}]")
                        
                        fig.update_yaxes(
                            range=[y_min, y_max],
                            row=row,
                            col=1
                        )
                    else:
                        logger.warning(f"No valid values for AUTO scaling of {metadata.name}")
                except Exception as e:
                    logger.error(f"Error calculating AUTO scale for {metadata.name}: {e}")
            
            elif metadata.scale_type == ScaleType.PRICE:
                # PRICE scale means the indicator shares the y-axis with the price chart
                # This is handled by adding the indicator to the price chart subplot
                # No explicit scaling needed here as it will use the price chart's scale
                logger.info(f"Using PRICE scale for {metadata.name} (shares price chart scale)")
                pass
            else:
                logger.warning(f"Unknown scale type for {metadata.name}: {metadata.scale_type}")
                
        except Exception as e:
            logger.error(f"Unexpected error applying scaling for {metadata.name}: {e}")
    
    def _add_oscillator_trace(
        self,
        fig,
        indicator_name: str,
        values: List[float],
        timestamps: List,
        row: int,
        metadata
    ):
        """
        Add oscillator indicator with proper styling.
        
        This method handles the rendering of oscillator indicators in their
        dedicated subplots. It supports multiple component types (lines, bars)
        and applies styling from the metadata.
        
        Special handling for MACD:
        - MACD line (blue)
        - Signal line (red)
        - Histogram (gray bars)
        
        Args:
            fig: Plotly figure object
            indicator_name: Name of the indicator
            values: List of indicator values (MACD line for MACD indicator)
            timestamps: List of timestamps
            row: Row number for the subplot
            metadata: IndicatorMetadata object with styling information
        """
        from shared.indicators_metadata import ComponentStyle
        
        # Check if this is a MACD indicator (special multi-component handling)
        base_name = metadata.name if metadata else indicator_name
        is_macd = base_name.upper() == "MACD"
        
        if is_macd:
            # Special handling for MACD with three components
            logger.info(f"Adding MACD indicator with three components (line, signal, histogram)")
            self._add_macd_components(fig, indicator_name, values, timestamps, row, metadata)
        else:
            # Standard single-component oscillator
            self._add_single_oscillator_trace(fig, indicator_name, values, timestamps, row, metadata)
    
    def _add_macd_components(
        self,
        fig,
        indicator_name: str,
        macd_values: List[float],
        timestamps: List,
        row: int,
        metadata
    ):
        """
        Add MACD indicator with all three components: line, signal, and histogram.
        
        This method supports two ways to get signal line and histogram:
        1. From stored calculator instance (_macd_calculator attribute)
        2. From separate indicator entries (e.g., "macd_signal", "macd_histogram")
        
        Args:
            fig: Plotly figure object
            indicator_name: Name of the indicator
            macd_values: List of MACD line values
            timestamps: List of timestamps
            row: Row number for the subplot
            metadata: IndicatorMetadata object with MACD styling
        """
        from shared.indicators_metadata import ComponentStyle
        
        signal_values = None
        histogram_values = None
        
        # Approach 1: Try to get from stored calculator instance
        macd_calculator = getattr(self, '_macd_calculator', None)
        if macd_calculator is not None:
            try:
                signal_line_dict = macd_calculator.get_signal_line()
                histogram_dict = macd_calculator.get_histogram()
                
                # Convert dictionaries to lists aligned with timestamps
                signal_values = [signal_line_dict.get(ts) for ts in timestamps]
                histogram_values = [histogram_dict.get(ts) for ts in timestamps]
                
                logger.info(f"Retrieved MACD components from calculator instance")
            except Exception as e:
                logger.warning(f"Could not retrieve MACD components from calculator: {e}")
        
        # Approach 2: Try to get from separate indicator entries (for DSL strategies)
        if signal_values is None or histogram_values is None:
            # Look for companion indicators with _signal and _histogram suffixes
            # This works with DSL strategies that provide these as separate indicators
            stored_indicators = getattr(self, '_current_indicators', {})
            
            # Try different naming conventions
            base_name = indicator_name.lower().replace("macd", "").strip("_") or "macd"
            signal_key = f"{base_name}_signal" if base_name != "macd" else "macd_signal"
            histogram_key = f"{base_name}_histogram" if base_name != "macd" else "macd_histogram"
            
            if signal_key in stored_indicators and histogram_key in stored_indicators:
                signal_values = stored_indicators[signal_key]
                histogram_values = stored_indicators[histogram_key]
                logger.info(f"Retrieved MACD components from separate indicators ({signal_key}, {histogram_key})")
            else:
                logger.warning(f"MACD signal/histogram not found. Looked for: {signal_key}, {histogram_key}")
                logger.warning(f"Available indicators: {list(stored_indicators.keys())}")
        
        # If we still don't have signal/histogram, fall back to single line
        if signal_values is None or histogram_values is None:
            logger.warning("MACD signal line and histogram not available, falling back to single line display")
            self._add_single_oscillator_trace(fig, indicator_name, macd_values, timestamps, row, metadata)
            return
        
        logger.info(f"MACD components: {len(macd_values)} MACD, {len(signal_values)} signal, {len(histogram_values)} histogram")
        
        # Get component styles from metadata
        macd_style = metadata.components.get("macd", ComponentStyle(color="#2196F3", label="MACD", width=2.5))
        signal_style = metadata.components.get("signal", ComponentStyle(color="#FF5722", label="Signal", width=2.0))
        histogram_style = metadata.components.get("histogram", ComponentStyle(color="#9E9E9E", label="Histogram", line_type="bar"))
        
        # Filter and add MACD line (blue)
        filtered_macd = []
        filtered_signal = []
        filtered_histogram = []
        filtered_timestamps = []
        
        for i, ts in enumerate(timestamps):
            macd_val = macd_values[i] if i < len(macd_values) else None
            signal_val = signal_values[i] if i < len(signal_values) else None
            histogram_val = histogram_values[i] if i < len(histogram_values) else None
            
            # Only include if all three components are valid
            if (macd_val is not None and not (isinstance(macd_val, float) and macd_val != macd_val) and
                signal_val is not None and not (isinstance(signal_val, float) and signal_val != signal_val) and
                histogram_val is not None and not (isinstance(histogram_val, float) and histogram_val != histogram_val)):
                filtered_macd.append(macd_val)
                filtered_signal.append(signal_val)
                filtered_histogram.append(histogram_val)
                filtered_timestamps.append(ts)
        
        if len(filtered_timestamps) == 0:
            logger.warning(f"No valid MACD values, skipping")
            return
        
        logger.info(f"Adding MACD line with {len(filtered_macd)} points")
        # Add MACD line (blue)
        fig.add_trace(
            go.Scatter(
                x=filtered_timestamps,
                y=filtered_macd,
                mode='lines',
                name=macd_style.label,
                line=dict(color=macd_style.color, width=macd_style.width),
                hovertemplate=f'{macd_style.label}: %{{y:.5f}}<extra></extra>',
                showlegend=True
            ),
            row=row, col=1
        )
        
        logger.info(f"Adding Signal line with {len(filtered_signal)} points")
        # Add Signal line (red)
        fig.add_trace(
            go.Scatter(
                x=filtered_timestamps,
                y=filtered_signal,
                mode='lines',
                name=signal_style.label,
                line=dict(color=signal_style.color, width=signal_style.width),
                hovertemplate=f'{signal_style.label}: %{{y:.5f}}<extra></extra>',
                showlegend=True
            ),
            row=row, col=1
        )
        
        logger.info(f"Adding Histogram with {len(filtered_histogram)} points")
        # Add Histogram (gray bars)
        fig.add_trace(
            go.Bar(
                x=filtered_timestamps,
                y=filtered_histogram,
                name=histogram_style.label,
                marker_color=histogram_style.color,
                showlegend=True,
                hovertemplate=f'{histogram_style.label}: %{{y:.5f}}<extra></extra>'
            ),
            row=row, col=1
        )
        
        logger.info(f"Successfully added all three MACD components")
    
    def _add_single_oscillator_trace(
        self,
        fig,
        indicator_name: str,
        values: List[float],
        timestamps: List,
        row: int,
        metadata
    ):
        """
        Add oscillator indicator with proper component handling.
        
        For stochastic indicators, this adds BOTH %K and %D lines.
        For other oscillators (RSI, etc.), this adds a single line.
        
        Args:
            fig: Plotly figure object
            indicator_name: Name of the indicator
            values: List of indicator values (%K for stochastic)
            timestamps: List of timestamps
            row: Row number for the subplot
            metadata: IndicatorMetadata object with styling information
        """
        from shared.indicators_metadata import ComponentStyle
        
        # Check if this is a stochastic indicator (has both k and d components)
        is_stochastic = 'k' in metadata.components and 'd' in metadata.components
        
        if is_stochastic:
            # Special handling for stochastic - add both %K and %D lines
            logger.info(f"Adding stochastic indicator {indicator_name} with %K and %D lines")
            self._add_stochastic_components(fig, indicator_name, values, timestamps, row, metadata)
        else:
            # Standard single-line oscillator (RSI, etc.)
            self._add_standard_oscillator_line(fig, indicator_name, values, timestamps, row, metadata)
    
    def _add_stochastic_components(
        self,
        fig,
        indicator_name: str,
        k_values: List[float],
        timestamps: List,
        row: int,
        metadata
    ):
        """
        Add stochastic indicator with both %K and %D lines.
        
        Looks for the %D values in the stored indicators dictionary using the
        naming convention: if indicator is "fast", %D is "fast_d".
        
        Args:
            fig: Plotly figure object
            indicator_name: Name of the indicator (e.g., "fast", "med_fast")
            k_values: List of %K values
            timestamps: List of timestamps
            row: Row number for the subplot
            metadata: IndicatorMetadata object with styling
        """
        from shared.indicators_metadata import ComponentStyle
        
        # Get %D values from stored indicators
        d_values = None
        stored_indicators = getattr(self, '_current_indicators', {})
        d_key = f"{indicator_name}_d"
        
        if d_key in stored_indicators:
            d_values = stored_indicators[d_key]
            logger.info(f"Found %D values for {indicator_name} at key {d_key}")
        else:
            logger.warning(f"No %D values found for {indicator_name} (looked for {d_key})")
            logger.warning(f"Available indicators: {list(stored_indicators.keys())}")
            # Fall back to single line
            self._add_standard_oscillator_line(fig, indicator_name, k_values, timestamps, row, metadata)
            return
        
        # Get component styles
        k_style = metadata.components.get("k", ComponentStyle(color="#2196F3", label="%K", width=2.5))
        d_style = metadata.components.get("d", ComponentStyle(color="#FF9800", label="%D", width=2.0, dash="dash"))
        
        # Filter and align data
        filtered_k = []
        filtered_d = []
        filtered_timestamps = []
        
        for i, ts in enumerate(timestamps):
            k_val = k_values[i] if i < len(k_values) else None
            d_val = d_values[i] if i < len(d_values) else None
            
            # Only include if both values are valid
            if (k_val is not None and not (isinstance(k_val, float) and k_val != k_val) and
                d_val is not None and not (isinstance(d_val, float) and d_val != d_val)):
                filtered_k.append(k_val)
                filtered_d.append(d_val)
                filtered_timestamps.append(ts)
        
        if len(filtered_timestamps) == 0:
            logger.warning(f"No valid stochastic values for {indicator_name}, skipping")
            return
        
        logger.info(f"Adding %K line for {indicator_name} with {len(filtered_k)} points")
        # Add %K line
        fig.add_trace(
            go.Scatter(
                x=filtered_timestamps,
                y=filtered_k,
                mode='lines',
                name=k_style.label,
                line=dict(color=k_style.color, width=k_style.width),
                hovertemplate=f'{k_style.label}: %{{y:.2f}}<extra></extra>',
                showlegend=True
            ),
            row=row, col=1
        )
        
        logger.info(f"Adding %D line for {indicator_name} with {len(filtered_d)} points")
        # Add %D line
        fig.add_trace(
            go.Scatter(
                x=filtered_timestamps,
                y=filtered_d,
                mode='lines',
                name=d_style.label,
                line=dict(color=d_style.color, width=d_style.width, dash=d_style.dash),
                hovertemplate=f'{d_style.label}: %{{y:.2f}}<extra></extra>',
                showlegend=True
            ),
            row=row, col=1
        )
        
        logger.info(f"Successfully added both %K and %D lines for {indicator_name}")
    
    def _add_standard_oscillator_line(
        self,
        fig,
        indicator_name: str,
        values: List[float],
        timestamps: List,
        row: int,
        metadata
    ):
        """
        Add a standard single-line oscillator (RSI, etc.).
        
        Args:
            fig: Plotly figure object
            indicator_name: Name of the indicator
            values: List of indicator values
            timestamps: List of timestamps
            row: Row number for the subplot
            metadata: IndicatorMetadata object with styling
        """
        from shared.indicators_metadata import ComponentStyle
        
        # Filter out NaN/None values
        filtered_values = []
        filtered_timestamps = []
        
        for i, value in enumerate(values):
            if i < len(timestamps) and value is not None and not (isinstance(value, float) and value != value):  # Check for NaN
                filtered_values.append(value)
                filtered_timestamps.append(timestamps[i])
        
        if len(filtered_values) == 0:
            logger.warning(f"No valid values for {indicator_name}, skipping")
            return
        
        # Get component style (use first component if available)
        if metadata.components:
            component_key = list(metadata.components.keys())[0]
            style = metadata.components[component_key]
        else:
            # Fallback style
            style = ComponentStyle(color="#2196F3", label=indicator_name, line_type="line", width=2.0)
        
        # Add trace based on line type
        if style.line_type == "bar":
            logger.info(f"Adding {indicator_name} as bar chart")
            fig.add_trace(
                go.Bar(
                    x=filtered_timestamps,
                    y=filtered_values,
                    name=style.label,
                    marker_color=style.color,
                    showlegend=True
                ),
                row=row, col=1
            )
        else:  # line or area
            logger.info(f"Adding {indicator_name} as line chart")
            fig.add_trace(
                go.Scatter(
                    x=filtered_timestamps,
                    y=filtered_values,
                    mode='lines',
                    name=style.label,
                    line=dict(color=style.color, width=style.width, dash=style.dash),
                    hovertemplate=f'{style.label}: %{{y:.5f}}<extra></extra>',
                    showlegend=True
                ),
                row=row, col=1
            )
    
    def _add_indicator_trace(
        self,
        fig,
        indicator_name: str,
        values: List[float],
        timestamps: List,
        row: int
    ):
        """
        Add indicator trace to a subplot (typically the price chart for overlays).
        
        This is a helper method for adding overlay indicators to the price chart.
        
        Args:
            fig: Plotly figure object
            indicator_name: Name of the indicator
            values: List of indicator values
            timestamps: List of timestamps
            row: Row number for the subplot
        """
        # Filter out NaN/zero values for cleaner display
        filtered_values = []
        filtered_timestamps = []
        
        for i, value in enumerate(values):
            if i < len(timestamps) and value is not None and value > 0:  # Only show non-zero values
                filtered_values.append(value)
                filtered_timestamps.append(timestamps[i])
        
        if len(filtered_values) == 0:
            logger.warning(f"No valid values for {indicator_name}, skipping")
            return
        
        # Smart color selection based on indicator name
        color = self.colors.get(indicator_name.lower(), '#FF9800')
        
        # Enhanced styling for MA lines
        line_width = 2.5 if 'sma' in indicator_name.lower() else 2
        line_dash = None
        
        if 'fast' in indicator_name.lower() or 'sma20' in indicator_name.lower():
            color = '#2196F3'  # Blue for fast MA
        elif 'slow' in indicator_name.lower() or 'sma50' in indicator_name.lower():
            color = '#FF5722'  # Orange-red for slow MA
        
        fig.add_trace(
            go.Scatter(
                x=filtered_timestamps,
                y=filtered_values,
                mode='lines',
                name=indicator_name,
                line=dict(color=color, width=line_width, dash=line_dash),
                hovertemplate=f'{indicator_name}: %{{y:.5f}}<extra></extra>',
                showlegend=True
            ),
            row=row, col=1
        )
        
        logger.info(f"Added {indicator_name} with {len(filtered_values)} points to row {row}")
    
    def _add_indicators(self, fig, df: pd.DataFrame, indicators: Dict[str, List[float]], row: int):
        """
        Add technical indicators to chart using routing logic.
        
        This method has been updated to use the metadata-based routing system.
        Indicators are automatically routed to the correct subplot based on their type.
        
        Note: This method is kept for backward compatibility but now delegates to
        _route_indicator_to_subplot() for the actual routing logic.
        """
        logger.info(f"Adding {len(indicators)} indicators to chart using metadata routing")
        
        # Store indicators dictionary so MACD can access signal/histogram
        self._current_indicators = indicators
        
        # Get the layout that was created in create_comprehensive_chart
        # For now, we'll use the simple routing for backward compatibility
        # The full routing will be used when create_comprehensive_chart is updated
        
        # Track which indicators we've already added (to avoid duplicates for MACD components)
        added_indicators = set()
        
        for indicator_name, values in indicators.items():
            # Skip MACD signal and histogram - they'll be added with the main MACD line
            if indicator_name.endswith('_signal') or indicator_name.endswith('_histogram'):
                base_name = indicator_name.replace('_signal', '').replace('_histogram', '')
                if base_name in indicators or 'macd' in base_name.lower():
                    logger.info(f"Skipping {indicator_name} - will be rendered with MACD line")
                    continue
            
            # Skip if already added
            if indicator_name in added_indicators:
                continue
            
            # Use the new routing logic
            timestamps = df['timestamp'].tolist()
            
            # For backward compatibility, we need to check if we have a layout
            # If not, fall back to the old behavior (add to price chart)
            if hasattr(self, '_current_layout'):
                self._route_indicator_to_subplot(
                    fig, indicator_name, values, timestamps, self._current_layout
                )
            else:
                # Fallback: old behavior for backward compatibility
                self._add_indicator_to_price_chart(fig, df, indicator_name, values, row)
            
            added_indicators.add(indicator_name)
    
    def _add_indicator_to_price_chart(self, fig, df: pd.DataFrame, indicator_name: str, values: List[float], row: int):
        """
        Legacy method to add indicator directly to price chart.
        Used for backward compatibility when layout is not available.
        """
        # Filter out NaN/zero values for cleaner display
        filtered_values = []
        filtered_timestamps = []
        
        for i, value in enumerate(values):
            if i < len(df) and value > 0:  # Only show non-zero values
                filtered_values.append(value)
                filtered_timestamps.append(df.iloc[i]['timestamp'])
        
        if len(filtered_values) > 0:
            # Smart color selection based on indicator name
            color = self.colors.get(indicator_name.lower(), '#FF9800')
            
            # Enhanced styling for MA lines
            line_width = 2.5 if 'sma' in indicator_name.lower() else 2
            line_dash = None
            
            if 'fast' in indicator_name.lower() or 'sma20' in indicator_name.lower():
                color = '#2196F3'  # Blue for fast MA
            elif 'slow' in indicator_name.lower() or 'sma50' in indicator_name.lower():
                color = '#FF5722'  # Orange-red for slow MA
            
            fig.add_trace(
                go.Scatter(
                    x=filtered_timestamps,
                    y=filtered_values,
                    mode='lines',
                    name=indicator_name,
                    line=dict(color=color, width=line_width, dash=line_dash),
                    hovertemplate=f'{indicator_name}: %{{y:.5f}}<extra></extra>',
                    showlegend=True
                ),
                row=row, col=1
            )
            
            logger.info(f"Added {indicator_name} with {len(filtered_values)} points, color: {color}")
    
    def _add_trade_signals(self, fig, trades: List[Trade], row: int):
        """Add trade entry signals as markers."""
        buy_entries = []
        sell_entries = []
        buy_times = []
        sell_times = []
        buy_text = []
        sell_text = []
        
        for i, trade in enumerate(trades, 1):
            if trade.direction == TradeDirection.BUY:
                buy_entries.append(trade.entry_price)
                buy_times.append(trade.entry_time)
                buy_text.append(f"#{i} BUY<br>{trade.pips:+.1f} pips")
            else:
                sell_entries.append(trade.entry_price)
                sell_times.append(trade.entry_time)
                sell_text.append(f"#{i} SELL<br>{trade.pips:+.1f} pips")
        
        # Add BUY signals
        if buy_entries:
            fig.add_trace(
                go.Scatter(
                    x=buy_times,
                    y=buy_entries,
                    mode='markers',
                    name='BUY Signals',
                    marker=dict(
                        symbol='triangle-up',
                        size=18,
                        color=self.colors['buy_signal']
                    ),
                    text=buy_text,
                    hovertemplate='%{text}<extra></extra>'
                ),
                row=row, col=1
            )
        
        # Add SELL signals
        if sell_entries:
            fig.add_trace(
                go.Scatter(
                    x=sell_times,
                    y=sell_entries,
                    mode='markers',
                    name='SELL Signals',
                    marker=dict(
                        symbol='triangle-down',
                        size=18,
                        color=self.colors['sell_signal']
                    ),
                    text=sell_text,
                    hovertemplate='%{text}<extra></extra>'
                ),
                row=row, col=1
            )
    
    def _add_trade_lines(self, fig, trades: List[Trade], row: int):
        """Add lines connecting entry and exit points."""
        for i, trade in enumerate(trades):
            color = self.colors['win_trade'] if trade.pips > 0 else self.colors['loss_trade']
            
            fig.add_trace(
                go.Scatter(
                    x=[trade.entry_time, trade.exit_time],
                    y=[trade.entry_price, trade.exit_price],
                    mode='lines',
                    line=dict(color=color, width=2, dash='dot'),
                    name=f'Trade #{i+1}',
                    showlegend=False,
                    hovertemplate=f'Trade #{i+1}<br>%{{y:.5f}}<extra></extra>'
                ),
                row=row, col=1
            )
    
    def _add_volume_chart(self, fig, df: pd.DataFrame, row: int):
        """Add volume bar chart."""
        colors = [
            self.colors['candle_up'] if close >= open else self.colors['candle_down']
            for close, open in zip(df['close'], df['open'])
        ]
        
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['volume'],
                name='Volume',
                marker_color=colors,
                showlegend=False
            ),
            row=row, col=1
        )
    
    def _add_pnl_chart(self, fig, trades: List[Trade], row: int):
        """Add cumulative P&L chart."""
        if not trades:
            return
        
        cumulative_pnl = []
        timestamps = []
        running_total = 0
        
        for trade in trades:
            running_total += trade.pips
            cumulative_pnl.append(running_total)
            timestamps.append(trade.exit_time)
        
        # Add line
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=cumulative_pnl,
                mode='lines+markers',
                name='Cumulative P&L',
                line=dict(color=self.colors['buy_line'], width=3),
                marker=dict(size=6),
                hovertemplate='P&L: %{y:+.1f} pips<extra></extra>'
            ),
            row=row, col=1
        )
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=row, col=1)
    
    def _add_red_spacers(self, fig, layout: Dict[str, int]):
        """
        Add red rectangle spacers between subplots to visualize spacing.
        This is a debugging/proof-of-concept feature.
        """
        # Get all subplot rows in order
        rows = sorted(set(layout.values()))
        
        # Add red rectangles between consecutive rows
        for i in range(len(rows) - 1):
            current_row = rows[i]
            next_row = rows[i + 1]
            
            # Calculate approximate y positions (these are estimates based on row_heights)
            # In a 1000px figure with our row heights, we can estimate positions
            # This is a visual proof - exact positions would require accessing fig.layout.yaxis domains
            
            # For demonstration, place rectangles at estimated gap positions
            # Row 1 (price): ~0.7-1.0, Row 2 (MACD): ~0.4-0.65, etc.
            if current_row == 1 and next_row == 2:
                # Between price chart and first oscillator
                y0, y1 = 0.65, 0.70  # 5% gap = 50px in 1000px figure
            elif current_row == 2 and next_row == 3:
                # Between oscillator and volume
                y0, y1 = 0.35, 0.40
            elif current_row == 3 and next_row == 4:
                # Between volume and P&L
                y0, y1 = 0.15, 0.20
            else:
                # Generic spacing for other gaps
                y0 = 1.0 - (next_row * 0.25)
                y1 = y0 + 0.05
            
            fig.add_shape(
                type="rect",
                xref="paper", yref="paper",
                x0=0, x1=1,
                y0=y0, y1=y1,
                fillcolor="red",
                opacity=0.3,
                layer="below",
                line=dict(color="darkred", width=2)
            )
            
            # Add text label on the spacer
            fig.add_annotation(
                xref="paper", yref="paper",
                x=0.5, y=(y0 + y1) / 2,
                text=f"SPACER: Row {current_row} → Row {next_row}",
                showarrow=False,
                font=dict(size=10, color="white"),
                bgcolor="rgba(139, 0, 0, 0.8)",
                borderpad=4
            )
    
    def _update_layout(self, fig, title: str, backtest_results: BacktestResults):
        """Update chart layout with styling and annotations."""
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'font': {'size': 20}
            },
            template=self.chart_theme,
            showlegend=True,
            height=1400,  # Increased from 1000 to give more vertical space
            hovermode='x unified',
            xaxis_rangeslider_visible=False,  # POC approach: disable globally
            margin=dict(t=100, b=50, l=80, r=80)  # Explicit margins, reduced bottom since no range slider
        )
        
        # Hide weekend gaps by configuring rangebreaks for all x-axes
        # This removes gaps when the market is closed (weekends)
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"])  # Hide Saturday and Sunday
            ]
        )
        

        # Add performance summary as annotation
        summary_text = (
            f"📊 Performance Summary<br>"
            f"Total Trades: {len(backtest_results.trades)}<br>"
            f"Win Rate: {backtest_results.win_rate:.1%}<br>"
            f"Total P&L: {backtest_results.total_pips:+.1f} pips<br>"
            f"Profit Factor: {backtest_results.profit_factor:.2f}"
        )
        
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.98, y=0.98,  # Top-right corner
            xanchor="right",
            yanchor="top",
            text=summary_text,
            showarrow=False,
            font=dict(size=10),
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#4CAF50",
            borderwidth=2,
            borderpad=6
        )
    
    def _calculate_monthly_performance(self, trades: List[Trade]) -> Dict[str, float]:
        """Calculate monthly P&L breakdown."""
        monthly_pnl = {}
        
        for trade in trades:
            month_key = trade.entry_time.strftime('%Y-%m')
            if month_key not in monthly_pnl:
                monthly_pnl[month_key] = 0
            monthly_pnl[month_key] += trade.pips
        
        return monthly_pnl
    
    def _save_chart(self, fig, title: str, backtest_results: BacktestResults) -> str:
        """Save chart to HTML file with trades table."""
        # Generate filename (browser-friendly, no spaces or special chars)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Get symbol and strategy name from backtest results
        symbol = backtest_results.configuration.symbol if hasattr(backtest_results, 'configuration') else 'UNKNOWN'
        strategy_name = backtest_results.strategy_name if hasattr(backtest_results, 'strategy_name') else title
        
        # Create clean filename
        clean_symbol = sanitize_symbol(symbol)
        clean_strategy = strategy_name.replace(' ', '_').replace('-', '_').upper()
        filename = f"{clean_symbol}_{clean_strategy}_{timestamp}.html"
        
        chart_path = self.output_dir / filename
        
        # Use Plotly's write_html which works correctly
        fig.write_html(
            str(chart_path),
            include_plotlyjs='cdn',
            config={'responsive': True}
        )
        
        # Now append the trades table to the HTML
        trades_table_html = self._generate_trades_table(backtest_results.trades)
        
        # Read the generated HTML
        with open(chart_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Insert trades table before closing body tag
        trades_section = f"""
    <div style="margin: 60px 20px 20px 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 20px;">
        <h2>📊 Trade History & Performance</h2>
        <button class="download-btn" onclick="downloadTradesAsText()">📥 Download Trades as Text File</button>
        {trades_table_html}
    </div>
    <style>
        .trades-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .trades-table th, .trades-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .trades-table th {{
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            text-align: center;
            padding: 12px 8px;
        }}
        .trades-table tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .trades-table tr:hover {{
            background-color: #e8f5e8;
        }}
        .win {{ color: #4CAF50; font-weight: bold; }}
        .loss {{ color: #f44336; font-weight: bold; }}
        .breakeven {{ color: #FF9800; font-weight: bold; }}
        .buy {{ color: #2196F3; }}
        .sell {{ color: #FF5722; }}
        .download-btn {{
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transition: all 0.2s;
        }}
        .download-btn:hover {{
            background: linear-gradient(135deg, #45a049 0%, #3d8b40 100%);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }}
        .download-btn:active {{
            transform: translateY(0);
        }}
    </style>
    <script>
        function downloadTradesAsText() {{
            const table = document.querySelector('.trades-table');
            const rows = table.querySelectorAll('tr');
            let textContent = '';
            
            // Add header with backtest info
            textContent += '=' .repeat(100) + '\\n';
            textContent += 'BACKTEST TRADE HISTORY\\n';
            textContent += '=' .repeat(100) + '\\n';
            textContent += 'Strategy: {strategy_name}\\n';
            textContent += 'Symbol: {symbol}\\n';
            textContent += 'Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n';
            textContent += '=' .repeat(100) + '\\n\\n';
            
            // Add summary from the paragraph at bottom of table
            const summaryP = document.querySelector('.trades-table').nextElementSibling;
            if (summaryP) {{
                textContent += 'SUMMARY\\n';
                textContent += '-' .repeat(100) + '\\n';
                textContent += summaryP.textContent.trim().replace(/\\s+/g, ' ') + '\\n';
                textContent += '=' .repeat(100) + '\\n\\n';
            }}
            
            // Add table data
            textContent += 'TRADE DETAILS\\n';
            textContent += '-' .repeat(100) + '\\n';
            
            rows.forEach((row, index) => {{
                const cells = row.querySelectorAll('th, td');
                const rowData = Array.from(cells).map(cell => {{
                    let text = cell.textContent.trim();
                    // Pad cells for alignment
                    if (index === 0) {{
                        // Header row
                        return text.padEnd(20);
                    }} else {{
                        return text.padEnd(20);
                    }}
                }}).join(' | ');
                
                textContent += rowData + '\\n';
                
                // Add separator after header
                if (index === 0) {{
                    textContent += '-' .repeat(100) + '\\n';
                }}
            }});
            
            textContent += '=' .repeat(100) + '\\n';
            textContent += 'End of Report\\n';
            
            // Create blob and download
            const blob = new Blob([textContent], {{ type: 'text/plain' }});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'trades_{clean_symbol}_{clean_strategy}_{timestamp}.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }}
    </script>
"""
        
        html_content = html_content.replace('</body>', f'{trades_section}</body>')
        
        # Write back the modified HTML
        with open(chart_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Chart saved: {chart_path}")
        return str(chart_path)
    
    def _generate_trades_table(self, trades: List) -> str:
        """Generate HTML table for trades."""
        if not trades:
            return "<p>No trades executed.</p>"
        
        table_rows = []
        for i, trade in enumerate(trades, 1):
            # Calculate duration
            if hasattr(trade, 'entry_time') and hasattr(trade, 'exit_time'):
                duration = trade.exit_time - trade.entry_time
                duration_str = str(duration).split('.')[0]  # Remove microseconds
            else:
                duration_str = "N/A"
            
            # Determine result class for styling
            result_class = "win" if trade.pips > 0 else "loss" if trade.pips < 0 else "breakeven"
            direction_class = "buy" if trade.direction.value == "BUY" else "sell"
            
            # Format exit reason
            exit_reason = getattr(trade, 'exit_reason', 'Unknown')
            if hasattr(trade, 'result') and trade.result:
                result_name = trade.result.name if hasattr(trade.result, 'name') else str(trade.result).upper()
                if result_name == 'WIN':
                    exit_reason = 'Take Profit'
                elif result_name == 'LOSS':
                    exit_reason = 'Stop Loss'
                elif result_name == 'EOD_CLOSE':
                    exit_reason = 'EOD'
                elif result_name == 'BREAKEVEN':
                    exit_reason = 'Breakeven'
            
            table_rows.append(f"""
                <tr>
                    <td>{i}</td>
                    <td>{getattr(trade, 'entry_time', 'N/A')}</td>
                    <td class="{direction_class}">{trade.direction.value}</td>
                    <td>{trade.entry_price:.5f}</td>
                    <td>{getattr(trade, 'exit_time', 'N/A')}</td>
                    <td>{trade.exit_price:.5f}</td>
                    <td>{duration_str}</td>
                    <td class="{result_class}">{trade.pips:+.1f}</td>
                    <td>{exit_reason}</td>
                </tr>
            """)
        
        return f"""
        <table class="trades-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Entry Time</th>
                    <th>Direction</th>
                    <th>Entry Price</th>
                    <th>Exit Time</th>
                    <th>Exit Price</th>
                    <th>Duration</th>
                    <th>Pips</th>
                    <th>Exit Reason</th>
                </tr>
            </thead>
            <tbody>
                {"".join(table_rows)}
            </tbody>
        </table>
        <p><strong>Total Trades:</strong> {len(trades)} | 
           <strong>Winners:</strong> <span class="win">{len([t for t in trades if t.pips > 0])}</span> | 
           <strong>Losers:</strong> <span class="loss">{len([t for t in trades if t.pips < 0])}</span> |
           <strong>Total P&L:</strong> <span class="{'win' if sum(t.pips for t in trades) > 0 else 'loss'}">{sum(t.pips for t in trades):+.1f} pips</span>
        </p>
        """


# Utility functions for backward compatibility
def create_trading_chart_from_backtest(
    candles: List[Candle],
    backtest_results: BacktestResults,
    indicators: Dict[str, List[float]] = None,
    title: str = "Strategy Results"
) -> str:
    """
    Convenience function to create a chart from backtest results.
    
    This is the main entry point for chart generation.
    """
    engine = ChartEngine()
    return engine.create_comprehensive_chart(candles, backtest_results, indicators, title)


def create_performance_chart(backtest_results: BacktestResults, title: str = "Performance") -> str:
    """
    Convenience function to create a performance summary chart.
    """
    engine = ChartEngine()
    return engine.create_performance_summary_chart(backtest_results, title)