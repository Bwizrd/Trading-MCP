#!/usr/bin/env python3
"""Simple script to plot price with MA indicators"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import plotly.graph_objects as go
import pandas as pd
import ta

from shared.data_connector import DataConnector

async def main():
    # Initialize connector
    connector = DataConnector()
    
    # Fetch data
    symbol = "EURUSD_SB"
    timeframe = "15m"
    days_back = 7
    
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=days_back)
    
    print(f"Fetching {symbol} {timeframe} data for {days_back} days...")
    response = await connector.get_market_data(
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_dt,
        end_date=end_dt
    )
    
    candles = response.data
    print(f"Fetched {len(candles)} candles from {response.source}")
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'timestamp': c.timestamp,
        'open': c.open,
        'high': c.high,
        'low': c.low,
        'close': c.close,
        'volume': c.volume
    } for c in candles])
    
    # Calculate MAs
    df['SMA20'] = ta.trend.sma_indicator(df['close'], window=20)
    df['SMA50'] = ta.trend.sma_indicator(df['close'], window=50)
    
    print(f"Calculated SMA20 and SMA50")
    print(f"SMA20 valid values: {df['SMA20'].notna().sum()}")
    print(f"SMA50 valid values: {df['SMA50'].notna().sum()}")
    
    # Check for crossovers
    df['cross_above'] = (df['SMA20'] > df['SMA50']) & (df['SMA20'].shift(1) <= df['SMA50'].shift(1))
    df['cross_below'] = (df['SMA20'] < df['SMA50']) & (df['SMA20'].shift(1) >= df['SMA50'].shift(1))
    
    crossovers = df[df['cross_above'] | df['cross_below']]
    print(f"\n🎯 Found {len(crossovers)} crossovers!")
    if len(crossovers) > 0:
        for idx, row in crossovers.iterrows():
            cross_type = "ABOVE" if row['cross_above'] else "BELOW"
            print(f"  {row['timestamp']}: SMA20 crossed {cross_type} SMA50")
    
    # Create chart
    fig = go.Figure()
    
    # Add candlesticks
    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name=symbol
    ))
    
    # Add SMA20
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['SMA20'],
        mode='lines',
        name='SMA 20',
        line=dict(color='blue', width=2)
    ))
    
    # Add SMA50
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['SMA50'],
        mode='lines',
        name='SMA 50',
        line=dict(color='orange', width=2)
    ))
    
    # Add crossover markers
    if len(crossovers) > 0:
        # Buy signals (cross above)
        buy_signals = crossovers[crossovers['cross_above']]
        if len(buy_signals) > 0:
            fig.add_trace(go.Scatter(
                x=buy_signals['timestamp'],
                y=buy_signals['close'],
                mode='markers',
                name='BUY Signal',
                marker=dict(symbol='triangle-up', size=15, color='green')
            ))
        
        # Sell signals (cross below)
        sell_signals = crossovers[crossovers['cross_below']]
        if len(sell_signals) > 0:
            fig.add_trace(go.Scatter(
                x=sell_signals['timestamp'],
                y=sell_signals['close'],
                mode='markers',
                name='SELL Signal',
                marker=dict(symbol='triangle-down', size=15, color='red')
            ))
    
    # Update layout
    fig.update_layout(
        title=f"{symbol} {timeframe} with SMA 20/50 - Last {days_back} Days ({len(crossovers)} crossovers)",
        xaxis_title="Time",
        yaxis_title="Price",
        template="plotly_white",
        height=800,
        xaxis_rangeslider_visible=False
    )
    
    # Save chart
    charts_dir = Path("data/charts")
    charts_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{symbol}_{timeframe}_MA_ANALYSIS_{timestamp}.html"
    chart_path = charts_dir / filename
    
    fig.write_html(str(chart_path))
    
    print(f"\n✅ Chart created: {chart_path}")
    print(f"📊 Contains {len(candles)} candlesticks + SMA20 + SMA50")
    print(f"🎯 {len(crossovers)} crossover signals marked")
    
    # Open the chart
    import os
    os.system(f'open "{chart_path}"')

if __name__ == "__main__":
    asyncio.run(main())
