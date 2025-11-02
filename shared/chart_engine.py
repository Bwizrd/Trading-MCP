#!/usr/bin/env python3
"""
Modular Chart Engine

Pure visualization engine that receives backtest results and creates charts.
NO STRATEGY LOGIC - only consumes results from the Universal Backtest Engine.

Architecture:
Strategy Cartridges → Backtest Engine → Chart Engine → HTML/PNG Charts
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
            'candle_down': '#F44336'
        }
    
    def create_comprehensive_chart(
        self,
        candles: List[Candle],
        backtest_results: BacktestResults,
        indicators: Dict[str, List[float]] = None,
        title: str = "Trading Strategy Results"
    ) -> str:
        """
        Create a comprehensive trading chart with all results.
        
        Args:
            candles: Market data (OHLCV)
            backtest_results: Results from Universal Backtest Engine
            indicators: Technical indicators (VWAP, SMA, etc.)
            title: Chart title
            
        Returns:
            Path to generated HTML chart file
        """
        logger.info(f"Creating comprehensive chart with {len(candles)} candles and {len(backtest_results.trades)} trades")
        
        # Convert candles to DataFrame for easier processing
        df = self._candles_to_dataframe(candles)
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,  # Fixed parameter name
            vertical_spacing=0.05,
            subplot_titles=[
                f'{title} - Price Action',
                'Volume',
                'Cumulative P&L'
            ],
            row_heights=[0.6, 0.2, 0.2]
        )
        
        # 1. Candlestick chart
        self._add_candlestick_chart(fig, df, row=1)
        
        # 2. Add technical indicators
        if indicators:
            self._add_indicators(fig, df, indicators, row=1)
        
        # 3. Add trade signals and lines
        self._add_trade_signals(fig, backtest_results.trades, row=1)
        self._add_trade_lines(fig, backtest_results.trades, row=1)
        
        # 4. Volume chart
        self._add_volume_chart(fig, df, row=2)
        
        # 5. P&L chart
        self._add_pnl_chart(fig, backtest_results.trades, row=3)
        
        # 6. Update layout
        self._update_layout(fig, title, backtest_results)
        
        # 7. Save chart
        chart_path = self._save_chart(fig, title, backtest_results)
        
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
    
    def _add_indicators(self, fig, df: pd.DataFrame, indicators: Dict[str, List[float]], row: int):
        """Add technical indicators to price chart."""
        for indicator_name, values in indicators.items():
            if len(values) == len(df):
                color = self.colors.get(indicator_name.lower(), '#FF9800')
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=values,
                        mode='lines',
                        name=indicator_name,
                        line=dict(color=color, width=2)
                    ),
                    row=row, col=1
                )
    
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
                        size=12,
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
                        size=12,
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
            height=1000,
            hovermode='x unified'
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
            x=0.02, y=0.98,
            text=summary_text,
            showarrow=False,
            font=dict(size=12),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1
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
        """Save chart to HTML file."""
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        symbol = getattr(backtest_results, 'symbol', 'UNKNOWN')
        filename = f"{sanitize_symbol(symbol)}_{sanitize_symbol(title)}_{timestamp}.html"
        
        chart_path = self.output_dir / filename
        
        # Save as HTML
        fig.write_html(
            str(chart_path),
            include_plotlyjs='cdn',  # Use CDN for smaller file size
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d']
            }
        )
        
        logger.info(f"Chart saved: {chart_path}")
        return str(chart_path)


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