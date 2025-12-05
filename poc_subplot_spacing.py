#!/usr/bin/env python3
"""
Proof of Concept: Plotly Subplot Spacing Test

This standalone script creates a complete backtest chart using synthetic data
to validate the mathematical model for subplot spacing before integrating
with the real backtest system.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from plotly.subplots import make_subplots
import plotly.graph_objects as go


# ============================================================================
# SUBTASK 0.1: Synthetic Data Generation Functions
# ============================================================================

def generate_ohlcv_data(num_candles=100, start_price=1.1000):
    """
    Generate synthetic OHLCV candlestick data.
    
    Args:
        num_candles: Number of candles to generate
        start_price: Starting price for the series
        
    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
    """
    np.random.seed(42)  # For reproducibility
    
    timestamps = [datetime.now() - timedelta(minutes=15*i) for i in range(num_candles)]
    timestamps.reverse()
    
    prices = [start_price]
    for _ in range(num_candles - 1):
        # Random walk with slight upward bias
        change = np.random.normal(0.0001, 0.0005)
        prices.append(prices[-1] + change)
    
    data = []
    for i, ts in enumerate(timestamps):
        close = prices[i]
        open_price = close + np.random.normal(0, 0.0002)
        high = max(open_price, close) + abs(np.random.normal(0, 0.0003))
        low = min(open_price, close) - abs(np.random.normal(0, 0.0003))
        volume = np.random.randint(1000, 10000)
        
        data.append({
            'timestamp': ts,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    return pd.DataFrame(data)


def generate_macd_data(close_prices):
    """
    Generate synthetic MACD indicator values.
    
    Args:
        close_prices: Series of close prices
        
    Returns:
        DataFrame with columns: macd_line, signal_line, histogram
    """
    # Simple exponential moving averages
    ema_12 = close_prices.ewm(span=12, adjust=False).mean()
    ema_26 = close_prices.ewm(span=26, adjust=False).mean()
    
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return pd.DataFrame({
        'macd_line': macd_line,
        'signal_line': signal_line,
        'histogram': histogram
    })


def generate_stochastic_data(high_prices, low_prices, close_prices, k_period=14, d_period=3):
    """
    Generate synthetic Stochastic oscillator values.
    
    Args:
        high_prices: Series of high prices
        low_prices: Series of low prices
        close_prices: Series of close prices
        k_period: Period for %K calculation
        d_period: Period for %D calculation
        
    Returns:
        DataFrame with columns: k_line, d_line
    """
    # Calculate %K
    lowest_low = low_prices.rolling(window=k_period).min()
    highest_high = high_prices.rolling(window=k_period).max()
    
    k_line = 100 * (close_prices - lowest_low) / (highest_high - lowest_low)
    d_line = k_line.rolling(window=d_period).mean()
    
    return pd.DataFrame({
        'k_line': k_line,
        'd_line': d_line
    })


def generate_rsi_data(close_prices, period=14):
    """
    Generate synthetic RSI indicator values.
    
    Args:
        close_prices: Series of close prices
        period: RSI period
        
    Returns:
        Series of RSI values
    """
    delta = close_prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def generate_trade_signals(df, num_trades=10):
    """
    Generate synthetic trade entry/exit signals.
    
    Args:
        df: DataFrame with OHLCV data
        num_trades: Number of trades to generate
        
    Returns:
        List of trade dictionaries with entry/exit info
    """
    np.random.seed(42)
    trades = []
    
    available_indices = list(range(10, len(df) - 10))
    
    for i in range(num_trades):
        if len(available_indices) < 2:
            break
            
        entry_idx = np.random.choice(available_indices)
        available_indices.remove(entry_idx)
        
        # Exit 3-10 candles after entry
        exit_offset = np.random.randint(3, 11)
        exit_idx = min(entry_idx + exit_offset, len(df) - 1)
        
        # Random buy or sell
        is_buy = np.random.choice([True, False])
        
        entry_price = df.iloc[entry_idx]['close']
        exit_price = df.iloc[exit_idx]['close']
        
        if is_buy:
            pnl_pips = (exit_price - entry_price) * 10000
        else:
            pnl_pips = (entry_price - exit_price) * 10000
        
        trades.append({
            'entry_idx': entry_idx,
            'exit_idx': exit_idx,
            'entry_time': df.iloc[entry_idx]['timestamp'],
            'exit_time': df.iloc[exit_idx]['timestamp'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'direction': 'BUY' if is_buy else 'SELL',
            'pnl_pips': pnl_pips
        })
    
    return sorted(trades, key=lambda x: x['entry_idx'])


def generate_cumulative_pnl(trades, df):
    """
    Generate cumulative P&L data aligned with timestamps.
    
    Args:
        trades: List of trade dictionaries
        df: DataFrame with OHLCV data
        
    Returns:
        Series of cumulative P&L values
    """
    pnl = pd.Series(0.0, index=df.index)
    cumulative = 0.0
    
    for trade in trades:
        exit_idx = trade['exit_idx']
        cumulative += trade['pnl_pips']
        pnl.iloc[exit_idx:] = cumulative
    
    return pnl


# ============================================================================
# SUBTASK 0.2: Spacing Calculation
# ============================================================================

def calculate_vertical_spacing(num_rows):
    """
    Calculate appropriate vertical spacing based on number of rows.
    
    Design guidelines:
    - 2 rows: 0.12 (12% spacing)
    - 3 rows: 0.10 (10% spacing)
    - 4 rows: 0.08 (8% spacing)
    - 5+ rows: 0.06 (6% spacing)
    
    Args:
        num_rows: Number of subplot rows
        
    Returns:
        Spacing as a proportion of total figure height
    """
    if num_rows <= 1:
        return 0.0
    elif num_rows == 2:
        return 0.12
    elif num_rows == 3:
        return 0.10
    elif num_rows == 4:
        return 0.08
    else:  # 5 or more rows
        return 0.06


# ============================================================================
# SUBTASK 0.3: Row Height Calculation
# ============================================================================

def calculate_row_heights(num_rows, num_oscillators):
    """
    Calculate row heights accounting for vertical spacing.
    
    For 6 rows (price + 3 oscillators + volume + P&L):
    - Spacing: 0.06
    - Available space: 1.0 - (6-1) * 0.06 = 1.0 - 0.30 = 0.70
    - Price: 45% of available = 0.315
    - Each oscillator: 35%/3 of available = 0.0817 each
    - Volume: 10% of available = 0.07
    - P&L: 10% of available = 0.07
    
    Args:
        num_rows: Total number of rows
        num_oscillators: Number of oscillator subplots
        
    Returns:
        List of height proportions
    """
    spacing = calculate_vertical_spacing(num_rows)
    total_spacing = (num_rows - 1) * spacing
    available_space = 1.0 - total_spacing
    
    print(f"\nLayout Calculation:")
    print(f"  Number of rows: {num_rows}")
    print(f"  Spacing per gap: {spacing:.3f}")
    print(f"  Total spacing: {total_spacing:.3f} ({num_rows-1} gaps)")
    print(f"  Available space: {available_space:.3f}")
    
    # Allocate space according to design percentages
    price_height = 0.45 * available_space
    oscillator_total = 0.35 * available_space
    volume_height = 0.10 * available_space
    pnl_height = 0.10 * available_space
    
    # Divide oscillator space equally
    oscillator_height = oscillator_total / num_oscillators if num_oscillators > 0 else 0
    
    # Build heights list in order: price, oscillators, volume, P&L
    heights = [price_height]
    for _ in range(num_oscillators):
        heights.append(oscillator_height)
    heights.append(volume_height)
    heights.append(pnl_height)
    
    # Verify sum
    heights_sum = sum(heights)
    print(f"\nHeight Allocation:")
    print(f"  Price: {price_height:.4f} (45% of available)")
    if num_oscillators > 0:
        print(f"  Each oscillator: {oscillator_height:.4f} (35%/{num_oscillators} of available)")
    print(f"  Volume: {volume_height:.4f} (10% of available)")
    print(f"  P&L: {pnl_height:.4f} (10% of available)")
    print(f"  Sum of heights: {heights_sum:.4f}")
    print(f"  Expected: {available_space:.4f}")
    print(f"  Match: {'✓' if abs(heights_sum - available_space) < 0.0001 else '✗'}")
    
    return heights


# ============================================================================
# SUBTASKS 0.4-0.13: Chart Creation and Visualization
# ============================================================================

def add_debug_spacing_indicators(fig, num_rows, spacing, heights):
    """
    SUBTASK 0.14: Add visual spacing indicators for debugging.
    
    Adds colored rectangles and annotations to show spacing gaps.
    
    Args:
        fig: Plotly figure object
        num_rows: Number of rows
        spacing: Vertical spacing value
        heights: List of row heights
    """
    # Calculate y-positions for each row
    y_positions = []
    current_y = 1.0  # Start from top
    
    for i, height in enumerate(heights):
        row_top = current_y
        row_bottom = current_y - height
        y_positions.append((row_top, row_bottom))
        current_y = row_bottom - spacing  # Move down by spacing for next row
    
    # Add colored rectangles in the spacing gaps
    for i in range(len(y_positions) - 1):
        gap_top = y_positions[i][1]  # Bottom of current row
        gap_bottom = y_positions[i + 1][0]  # Top of next row
        gap_height = gap_top - gap_bottom
        
        # Add a semi-transparent rectangle to show the gap
        fig.add_shape(
            type="rect",
            xref="paper",
            yref="paper",
            x0=0,
            x1=1,
            y0=gap_bottom,
            y1=gap_top,
            fillcolor="rgba(255, 165, 0, 0.2)",  # Orange with transparency
            line=dict(color="rgba(255, 0, 0, 0.5)", width=2, dash="dash"),
            layer="below"
        )
        
        # Add annotation showing spacing measurement
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.98,
            y=(gap_top + gap_bottom) / 2,
            text=f"Gap {i+1}: {gap_height:.3f}",
            showarrow=False,
            font=dict(size=10, color="red"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="red",
            borderwidth=1
        )
    
    print(f"\n✓ Added {len(y_positions) - 1} debug spacing indicators")
    return fig


def create_poc_chart(df, macd_df, stoch_df, rsi, trades, pnl, debug_mode=False):
    """
    Create the proof-of-concept chart with all subplots.
    
    Args:
        df: OHLCV DataFrame
        macd_df: MACD indicator DataFrame
        stoch_df: Stochastic indicator DataFrame
        rsi: RSI Series
        trades: List of trade dictionaries
        pnl: Cumulative P&L Series
        debug_mode: If True, add visual spacing indicators
        
    Returns:
        Plotly figure object
    """
    # SUBTASK 0.4: Create multi-subplot chart
    num_rows = 6
    num_oscillators = 3
    
    spacing = calculate_vertical_spacing(num_rows)
    heights = calculate_row_heights(num_rows, num_oscillators)
    
    subplot_titles = [
        "Price Action",
        "MACD",
        "Stochastic",
        "RSI",
        "Volume",
        "Cumulative P&L"
    ]
    
    print(f"\nCreating subplot figure with {num_rows} rows...")
    print(f"Vertical spacing: {spacing}")
    print(f"Row heights: {[f'{h:.4f}' for h in heights]}")
    
    fig = make_subplots(
        rows=num_rows,
        cols=1,
        row_heights=heights,
        vertical_spacing=spacing,
        subplot_titles=subplot_titles,
        shared_xaxes=True
    )
    
    # SUBTASK 0.5: Add candlestick chart to price subplot
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color='green',
            decreasing_line_color='red'
        ),
        row=1, col=1
    )
    
    # SUBTASK 0.6: Add buy/sell signal markers
    buy_trades = [t for t in trades if t['direction'] == 'BUY']
    sell_trades = [t for t in trades if t['direction'] == 'SELL']
    
    if buy_trades:
        fig.add_trace(
            go.Scatter(
                x=[t['entry_time'] for t in buy_trades],
                y=[t['entry_price'] for t in buy_trades],
                mode='markers',
                marker=dict(
                    symbol='triangle-up',
                    size=12,
                    color='green',
                    line=dict(width=1, color='darkgreen')
                ),
                name='Buy Signal',
                hovertemplate='<b>BUY</b><br>Price: %{y:.5f}<br>Time: %{x}<extra></extra>'
            ),
            row=1, col=1
        )
    
    if sell_trades:
        fig.add_trace(
            go.Scatter(
                x=[t['entry_time'] for t in sell_trades],
                y=[t['entry_price'] for t in sell_trades],
                mode='markers',
                marker=dict(
                    symbol='triangle-down',
                    size=12,
                    color='red',
                    line=dict(width=1, color='darkred')
                ),
                name='Sell Signal',
                hovertemplate='<b>SELL</b><br>Price: %{y:.5f}<br>Time: %{x}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # SUBTASK 0.7: Add MACD indicator
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=macd_df['macd_line'],
            mode='lines',
            name='MACD Line',
            line=dict(color='blue', width=1.5)
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=macd_df['signal_line'],
            mode='lines',
            name='Signal Line',
            line=dict(color='red', width=1.5)
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=df['timestamp'],
            y=macd_df['histogram'],
            name='MACD Histogram',
            marker_color='gray',
            opacity=0.5
        ),
        row=2, col=1
    )
    
    # Add zero line for MACD
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=2, col=1)
    
    # SUBTASK 0.8: Add Stochastic indicator
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=stoch_df['k_line'],
            mode='lines',
            name='%K',
            line=dict(color='blue', width=1.5)
        ),
        row=3, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=stoch_df['d_line'],
            mode='lines',
            name='%D',
            line=dict(color='orange', width=1.5, dash='dash')
        ),
        row=3, col=1
    )
    
    # Add reference lines for Stochastic
    fig.add_hline(y=80, line_dash="dot", line_color="red", opacity=0.5, row=3, col=1)
    fig.add_hline(y=20, line_dash="dot", line_color="green", opacity=0.5, row=3, col=1)
    
    # Set fixed scale for Stochastic
    fig.update_yaxes(range=[0, 100], row=3, col=1)
    
    # SUBTASK 0.9: Add RSI indicator
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=rsi,
            mode='lines',
            name='RSI',
            line=dict(color='purple', width=1.5)
        ),
        row=4, col=1
    )
    
    # Add reference lines for RSI
    fig.add_hline(y=70, line_dash="dot", line_color="red", opacity=0.5, row=4, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", opacity=0.5, row=4, col=1)
    
    # Set fixed scale for RSI
    fig.update_yaxes(range=[0, 100], row=4, col=1)
    
    # SUBTASK 0.10: Add volume chart
    colors = ['green' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'red' 
              for i in range(len(df))]
    
    fig.add_trace(
        go.Bar(
            x=df['timestamp'],
            y=df['volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.7
        ),
        row=5, col=1
    )
    
    # SUBTASK 0.11: Add cumulative P&L chart
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=pnl,
            mode='lines+markers',
            name='Cumulative P&L',
            line=dict(color='green', width=2),
            marker=dict(size=4)
        ),
        row=6, col=1
    )
    
    # Add zero line for P&L
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=6, col=1)
    
    # Add markers at trade exit points
    exit_times = [t['exit_time'] for t in trades]
    exit_pnl = [pnl[df[df['timestamp'] == t['exit_time']].index[0]] for t in trades]
    
    fig.add_trace(
        go.Scatter(
            x=exit_times,
            y=exit_pnl,
            mode='markers',
            name='Trade Exit',
            marker=dict(size=8, color='darkgreen', symbol='circle'),
            showlegend=False
        ),
        row=6, col=1
    )
    
    # SUBTASK 0.12: Configure chart layout and styling
    title = "Proof of Concept - Subplot Spacing Test"
    if debug_mode:
        title += " [DEBUG MODE]"
    
    fig.update_layout(
        height=1400,
        title=title,
        template="plotly_white",
        showlegend=True,
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )
    
    # Update all x-axes to share
    fig.update_xaxes(showticklabels=True)
    
    # SUBTASK 0.14: Add debug spacing indicators if requested
    if debug_mode:
        fig = add_debug_spacing_indicators(fig, num_rows, spacing, heights)
    
    return fig


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PROOF OF CONCEPT: Subplot Spacing Test")
    print("=" * 70)
    
    print("\n[SUBTASK 0.1] Generating synthetic data...")
    
    # Generate OHLCV data
    df = generate_ohlcv_data(num_candles=100)
    print(f"✓ Generated {len(df)} OHLCV candles")
    
    # Generate indicators
    macd_df = generate_macd_data(df['close'])
    print(f"✓ Generated MACD data")
    
    stoch_df = generate_stochastic_data(df['high'], df['low'], df['close'])
    print(f"✓ Generated Stochastic data")
    
    rsi = generate_rsi_data(df['close'])
    print(f"✓ Generated RSI data")
    
    # Generate trades
    trades = generate_trade_signals(df, num_trades=10)
    print(f"✓ Generated {len(trades)} trades")
    
    # Generate P&L
    pnl = generate_cumulative_pnl(trades, df)
    print(f"✓ Generated cumulative P&L")
    
    print("\n[SUBTASKS 0.2-0.3] Calculating layout...")
    
    # Create the chart (normal version)
    print("\n[SUBTASKS 0.4-0.12] Creating chart...")
    fig = create_poc_chart(df, macd_df, stoch_df, rsi, trades, pnl, debug_mode=False)
    
    # SUBTASK 0.13: Save chart and verify spacing
    print("\n[SUBTASK 0.13] Saving chart...")
    output_path = "data/charts/poc_spacing_test.html"
    fig.write_html(output_path)
    print(f"✓ Chart saved to: {output_path}")
    
    # SUBTASK 0.14: Create debug version with spacing indicators
    print("\n[SUBTASK 0.14] Creating debug version with spacing indicators...")
    fig_debug = create_poc_chart(df, macd_df, stoch_df, rsi, trades, pnl, debug_mode=True)
    output_path_debug = "data/charts/poc_spacing_test_debug.html"
    fig_debug.write_html(output_path_debug)
    print(f"✓ Debug chart saved to: {output_path_debug}")
    
    print("\n" + "=" * 70)
    print("VERIFICATION CHECKLIST:")
    print("=" * 70)
    print("1. Open the chart in your browser")
    print("2. Verify all 6 subplots are clearly separated with visible gaps")
    print("3. Verify no overlapping between subplots")
    print("4. Check that all indicators are properly displayed")
    print("5. Verify buy/sell signals are visible on price chart")
    print("6. Check that P&L chart shows trade exits")
    print("\nIf spacing looks good, the mathematical model is validated!")
    print("=" * 70)
