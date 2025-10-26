"""
VWAP (Volume Weighted Average Price) Trading Strategy.

This strategy generates signals based on price relationship to VWAP:
- At 8:30, if price is above VWAP, generate SELL signal
- At 8:30, if price is below VWAP, generate BUY signal

The core.py file contains the strategy logic and uses data connectors
from the mcp_servers/data_connectors/ folder.
"""