"""
Simple Data Connector for Universal Backtest Engine

Compatible with the existing working system while providing
the interface needed for the modular cartridge system.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import asyncio
import logging
import httpx
import pandas as pd

logger = logging.getLogger(__name__)


class DataConnector:
    """
    Simple data connector that works with the existing system.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the data connector."""
        self.base_url = base_url
        self.client = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    async def get_symbols(self) -> List[str]:
        """Get available symbols."""
        # Return common forex symbols for now
        return ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "EURGBP", "EURJPY"]
    
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> pd.DataFrame:
        """Get historical data."""
        # For now, generate mock data similar to the working system
        # In production, this would make actual API calls
        
        logger.info(f"Getting historical data for {symbol} {timeframe} from {start_date} to {end_date}")
        
        # Generate mock data
        date_range = pd.date_range(start=start_date, end=end_date, freq='1min')
        mock_data = []
        
        base_price = 1.0500 if symbol == "EURUSD" else 1.2500
        
        for i, timestamp in enumerate(date_range[:2000]):  # Limit for performance
            price = base_price + (i % 100) * 0.0001
            mock_data.append({
                'timestamp': timestamp,
                'open': price,
                'high': price + 0.0005,
                'low': price - 0.0005,
                'close': price + 0.0002,
                'volume': 1000 + (i % 500)
            })
        
        return pd.DataFrame(mock_data)
    
    async def test_connectivity(self) -> Dict[str, Any]:
        """Test connection."""
        return {
            "status": "connected",
            "message": "DataConnector is working",
            "influxdb": True,  # Mock success
            "ctrader": True    # Mock success
        }