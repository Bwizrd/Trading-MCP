#!/usr/bin/env python3
"""Test script to create a simple price chart"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import plotly.graph_objects as go

from shared.data_connector import DataConnector

async def main():
    # Initialize connector
    connector = DataConnector()
    
    # Fetch data
    symbol = "EURUSD"
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
    
    # Create simple candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=[c.timestamp for c in candles],
        open=[c.open for c in candles],
        high=[c.high for c in candles],
        low=[c.low for c in candles],
        close=[c.close for c in candles],
        name=symbol
    )])
    
    # Update layout
    fig.update_layout(
        title=f"{symbol} {timeframe} - Last {days_back} Days",
        xaxis_title="Time",
        yaxis_title="Price",
        template="plotly_white",
        height=600,
        xaxis_rangeslider_visible=False
    )
    
    # Save chart
    charts_dir = Path("data/charts")
    charts_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{symbol}_{timeframe}_{timestamp}.html"
    chart_path = charts_dir / filename
    
    fig.write_html(str(chart_path))
    
    print(f"\n✅ Chart created: {chart_path}")
    print(f"📊 Contains {len(candles)} candlesticks")
    
    # Open the chart
    import os
    os.system(f'open "{chart_path}"')

if __name__ == "__main__":
    asyncio.run(main())
