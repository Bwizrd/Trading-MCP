"""
Universal Data Connector for Backtest Engine

Uses the existing working data fetching functions from the MCP data connectors.
NO NEW ABSTRACTIONS - uses proven working code.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging
import sys
from pathlib import Path
from dataclasses import dataclass
from .models import Candle

# Import the working data fetching function
sys.path.append(str(Path(__file__).parent.parent / "mcp_servers" / "data_connectors"))

# Import the working function directly
import importlib.util
spec = importlib.util.spec_from_file_location("influxdb", Path(__file__).parent.parent / "mcp_servers" / "data_connectors" / "influxdb.py")
influxdb_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(influxdb_module)

logger = logging.getLogger(__name__)


@dataclass
class MarketDataResponse:
    """Response from market data request."""
    data: List[Candle]
    source: str
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime


class DataConnector:
    """
    Universal data connector that uses the existing working _fetch_historical_data function.
    NO NEW ABSTRACTIONS - direct use of proven working code.
    """
    
    def __init__(self):
        """Initialize the data connector."""
        pass
        
    async def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> MarketDataResponse:
        """
        Get market data using the existing working _fetch_historical_data function.
        
        This method provides the interface expected by UniversalBacktestEngine.
        """
        logger.info(f"Fetching market data for {symbol} {timeframe} from {start_date} to {end_date}")
        
        try:
            # Use the correct API endpoints directly instead of broken _fetch_historical_data
            import httpx
            
            # Get symbol mapping first
            async with httpx.AsyncClient(timeout=30.0) as client:
                symbols_response = await client.get("http://localhost:8000/symbols")
                symbols_data = symbols_response.json()
                
                # Find pair ID for symbol
                pair_id = None
                symbols_list = symbols_data.get('symbols', [])
                for sym in symbols_list:
                    # Check both exact match and with _SB suffix
                    if sym.get('name') == symbol or sym.get('name') == f"{symbol}_SB":
                        pair_id = sym.get('value')
                        break
                
                if not pair_id:
                    raise Exception(f"Symbol {symbol} not found in symbols list")
                
                # Calculate proper number of bars based on timeframe and date range
                days_diff = (end_date - start_date).days if isinstance(end_date, datetime) and isinstance(start_date, datetime) else 30
                
                # Calculate bars per day based on timeframe
                bars_per_day = {
                    "1m": 1440, "5m": 288, "15m": 96, "30m": 48,
                    "1h": 24, "4h": 6, "1d": 1
                }
                estimated_bars = days_diff * bars_per_day.get(timeframe, 48)
                
                # Add buffer and limit to reasonable max
                bars = min(estimated_bars * 2, 10000)
                logger.info(f"Calculated {bars} bars for {days_diff} days of {timeframe} data")
                
                # Try InfluxDB first (fastest) - ensure lowercase timeframe
                timeframe_lower = timeframe.lower()
                influx_url = f"http://localhost:8000/getDataFromDB?pair={pair_id}&timeframe={timeframe_lower}&bars={bars}"
                logger.info(f"Trying InfluxDB: {influx_url}")
                
                influx_response = await client.get(influx_url)
                
                if influx_response.status_code == 200:
                    influx_data = influx_response.json()
                    if influx_data and 'data' in influx_data and len(influx_data['data']) > 0:
                        data_frame = influx_data['data']
                        data_source = "InfluxDB"
                    else:
                        raise Exception("No data from InfluxDB")
                else:
                    # Fallback to date range API
                    start_iso = start_date.strftime('%Y-%m-%dT00:00:00.000Z') if isinstance(start_date, datetime) else f"{start_date}T00:00:00.000Z"
                    end_iso = end_date.strftime('%Y-%m-%dT23:59:59.000Z') if isinstance(end_date, datetime) else f"{end_date}T23:59:59.000Z"
                    
                    date_url = f"http://localhost:8000/getDataByDates?pair={pair_id}&timeframe={timeframe_lower}&startDate={start_iso}&endDate={end_iso}"
                    logger.info(f"Trying date range: {date_url}")
                    
                    date_response = await client.get(date_url)
                    if date_response.status_code == 200:
                        date_data = date_response.json()
                        if 'data' in date_data and len(date_data['data']) > 0:
                            data_frame = date_data['data']
                            data_source = "cTrader API"
                        else:
                            raise Exception("No data in date range response")
                    else:
                        raise Exception(f"Date range API failed: {date_response.status_code}")
            
            if data_frame and len(data_frame) > 0:
            
                # Convert JSON data to Candle objects
                candles = []
                for item in data_frame:
                    # Convert Unix timestamp (milliseconds) to datetime
                    timestamp = datetime.fromtimestamp(item['timestamp'] / 1000)
                    
                    candle = Candle(
                        timestamp=timestamp,
                        open=float(item['open']),
                        high=float(item['high']),
                        low=float(item['low']),
                        close=float(item['close']),
                        volume=int(item.get('volume', 0))
                    )
                    candles.append(candle)
                
                logger.info(f"Successfully fetched {len(candles)} candles from {data_source}")
                return MarketDataResponse(
                    data=candles,
                    source=data_source,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date
                )
                
        except Exception as e:
            logger.error(f"Data fetching failed: {e}")
        
        # If failed, return empty response
        logger.error("Data fetching failed")
        return MarketDataResponse(
            data=[],
            source="Failed",
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
        )
    
    async def get_symbols(self) -> List[str]:
        """Get available symbols."""
        return ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "EURGBP", "EURJPY"]
    
    async def test_connectivity(self) -> Dict[str, Any]:
        """Test connectivity to the API server."""
        try:
            # Test using the existing working function
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    return {
                        "status": "connected",
                        "api_server": True,
                        "message": "✅ API Server on port 8000 responding"
                    }
        except Exception as e:
            logger.warning(f"API server test failed: {e}")
        
        return {
            "status": "disconnected", 
            "api_server": False,
            "message": "❌ API Server on port 8000 not responding"
        }