"""
Enhanced data connector system with InfluxDB primary and cTrader fallback.
Inspired by the Full System architecture but simplified for current needs.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import asyncio
import httpx
import pandas as pd
from dataclasses import dataclass
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Data source types."""
    INFLUXDB = "influxdb"
    CTRADER = "ctrader"


@dataclass
class DataRequest:
    """Standard data request format."""
    symbol: str
    timeframe: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    bars: Optional[int] = None
    range_str: Optional[str] = None  # e.g., "-7d"


@dataclass
class DataResponse:
    """Standard data response format."""
    data: pd.DataFrame
    source: DataSourceType
    symbol: str
    timeframe: str
    request_time: datetime
    cached: bool = False


class DataSourceError(Exception):
    """Base exception for data source errors."""
    pass


class DataSource(ABC):
    """Abstract base class for data sources."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        self._symbol_cache = {}
        self._symbol_cache_time = None
        self.cache_duration = timedelta(hours=1)
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    @abstractmethod
    async def get_data(self, request: DataRequest) -> DataResponse:
        """Get market data for the given request."""
        pass
    
    @abstractmethod
    async def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get the latest candle for a symbol."""
        pass
    
    async def get_symbols(self) -> Dict[str, Any]:
        """Get available symbols with caching."""
        if (self._symbol_cache and self._symbol_cache_time and
            datetime.now() - self._symbol_cache_time < self.cache_duration):
            return self._symbol_cache
        
        try:
            if not self.client:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{self.base_url}/symbols")
            else:
                response = await self.client.get(f"{self.base_url}/symbols")
            
            response.raise_for_status()
            symbols = response.json()
            
            self._symbol_cache = symbols
            self._symbol_cache_time = datetime.now()
            
            return symbols
            
        except Exception as e:
            logger.error(f"Failed to fetch symbols: {e}")
            if self._symbol_cache:
                logger.warning("Using cached symbols due to fetch failure")
                return self._symbol_cache
            raise DataSourceError(f"Failed to fetch symbols: {e}")
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate market data integrity."""
        if data.empty:
            return False
        
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            return False
        
        # Check for null values in critical columns
        if data[required_columns].isnull().any().any():
            return False
        
        # Validate OHLC relationships
        invalid_high_low = data['high'] < data['low']
        if invalid_high_low.any():
            return False
        
        # Check if open/close are within high/low range
        invalid_open = (data['open'] < data['low']) | (data['open'] > data['high'])
        invalid_close = (data['close'] < data['low']) | (data['close'] > data['high'])
        
        if invalid_open.any() or invalid_close.any():
            return False
        
        return True


class InfluxDBDataSource(DataSource):
    """InfluxDB data source implementation."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        self.source_type = DataSourceType.INFLUXDB
    
    async def get_data(self, request: DataRequest) -> DataResponse:
        """Get data from InfluxDB via /getDataFromDB endpoint."""
        try:
            # Convert symbol to pair ID if needed
            symbols = await self.get_symbols()
            pair_id = self._symbol_to_pair_id(request.symbol, symbols)
            
            # Prepare parameters
            params = {
                "pair": pair_id,
                "timeframe": request.timeframe
            }
            
            # Calculate bars parameter - InfluxDB endpoint requires it
            if request.bars:
                params["bars"] = request.bars
            elif request.start_date and request.end_date:
                # Calculate approximate bars needed based on date range and timeframe
                bars = self._calculate_bars_from_date_range(
                    request.start_date, request.end_date, request.timeframe
                )
                params["bars"] = bars
            else:
                # Default to reasonable number of bars
                params["bars"] = 500
            
            logger.info(f"InfluxDB request: {params}")
            
            if not self.client:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{self.base_url}/getDataFromDB", params=params)
            else:
                response = await self.client.get(f"{self.base_url}/getDataFromDB", params=params)
            
            response.raise_for_status()
            data_json = response.json()
            
            # Convert to DataFrame
            df = self._json_to_dataframe(data_json)
            
            if not self.validate_data(df):
                raise DataSourceError("Invalid data received from InfluxDB")
            
            return DataResponse(
                data=df,
                source=self.source_type,
                symbol=request.symbol,
                timeframe=request.timeframe,
                request_time=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"InfluxDB data fetch failed: {e}")
            raise DataSourceError(f"InfluxDB fetch failed: {e}")
    
    async def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get latest candle from InfluxDB."""
        try:
            symbols = await self.get_symbols()
            pair_id = self._symbol_to_pair_id(symbol, symbols)
            
            params = {
                "pair": pair_id,
                "timeframe": timeframe
            }
            
            if not self.client:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{self.base_url}/getLatestCandle", params=params)
            else:
                response = await self.client.get(f"{self.base_url}/getLatestCandle", params=params)
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"InfluxDB latest candle fetch failed: {e}")
            return None
    
    def _symbol_to_pair_id(self, symbol: str, symbols: Dict[str, Any]) -> int:
        """Convert symbol to pair ID."""
        # This will need to be implemented based on your symbols API response format
        # For now, assuming symbols is a dict with symbol->id mapping
        if isinstance(symbols, dict):
            for key, value in symbols.items():
                if isinstance(value, dict) and value.get('symbol') == symbol:
                    return int(key)
                elif key == symbol:
                    return int(value) if isinstance(value, (int, str)) else int(key)
        
        # Fallback: try to parse symbol as number or use default mapping
        try:
            return int(symbol)
        except ValueError:
            # Default mappings for common symbols
            symbol_mapping = {
                'EURUSD': 189,
                'GBPUSD': 220,
                'USDJPY': 217,
                'AUDUSD': 218,
                'USDCHF': 219
            }
            return symbol_mapping.get(symbol.upper(), 189)  # Default to EURUSD
    
    def _json_to_dataframe(self, data_json: Dict[str, Any]) -> pd.DataFrame:
        """Convert JSON response to DataFrame."""
        if 'data' in data_json:
            data = data_json['data']
        else:
            data = data_json
        
        if not data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Ensure required columns exist and are properly typed
        if 'timestamp' in df.columns:
            # Handle various timestamp formats
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce', utc=True)
            # If that fails, try regular datetime parsing
            mask = df['timestamp'].isna()
            if mask.any():
                df.loc[mask, 'timestamp'] = pd.to_datetime(df.loc[mask, 'timestamp'], errors='coerce')
        
        # Ensure numeric columns are float
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df

    def _calculate_bars_from_date_range(self, start_date: datetime, end_date: datetime, timeframe: str) -> int:
        """Calculate approximate number of bars needed for date range."""
        # Calculate time difference
        time_diff = end_date - start_date
        total_minutes = time_diff.total_seconds() / 60
        
        # Map timeframe to minutes
        timeframe_minutes = {
            '1m': 1, '2m': 2, '3m': 3, '5m': 5, '10m': 10, '15m': 15, '30m': 30,
            '1h': 60, '2h': 120, '4h': 240, '6h': 360, '8h': 480, '12h': 720,
            '1d': 1440, '1w': 10080
        }
        
        timeframe_mins = timeframe_minutes.get(timeframe, 30)  # Default to 30m
        
        # Calculate bars (add buffer for weekends/holidays)
        bars = int(total_minutes / timeframe_mins)
        # Add 20% buffer for market gaps
        bars = int(bars * 1.2)
        
        # Ensure reasonable limits
        bars = max(10, min(bars, 5000))  # Between 10 and 5000 bars
        
        logger.info(f"Calculated {bars} bars for {timeframe} from {start_date} to {end_date}")
        return bars


class CTraderDataSource(DataSource):
    """cTrader data source implementation."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        self.source_type = DataSourceType.CTRADER
    
    async def get_data(self, request: DataRequest) -> DataResponse:
        """Get data from cTrader via various endpoints."""
        try:
            symbols = await self.get_symbols()
            pair_id = self._symbol_to_pair_id(request.symbol, symbols)
            
            # Choose appropriate endpoint based on request
            if request.start_date and request.end_date:
                # Use date range endpoint
                params = {
                    "pair": pair_id,
                    "timeframe": request.timeframe,
                    "startDate": request.start_date.isoformat() + "Z",
                    "endDate": request.end_date.isoformat() + "Z"
                }
                endpoint = "/getDataByDates"
            elif request.range_str:
                # Use range endpoint
                params = {
                    "pair": pair_id,
                    "timeframe": request.timeframe,
                    "range": request.range_str
                }
                endpoint = "/getData"
            else:
                # Use bars endpoint with default range
                params = {
                    "pair": pair_id,
                    "timeframe": request.timeframe,
                    "range": "-7d"  # Default to 7 days
                }
                endpoint = "/getData"
            
            logger.info(f"cTrader request: {endpoint} with {params}")
            
            if not self.client:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{self.base_url}{endpoint}", params=params)
            else:
                response = await self.client.get(f"{self.base_url}{endpoint}", params=params)
            
            response.raise_for_status()
            data_json = response.json()
            
            # Convert to DataFrame
            df = self._json_to_dataframe(data_json)
            
            if not self.validate_data(df):
                raise DataSourceError("Invalid data received from cTrader")
            
            return DataResponse(
                data=df,
                source=self.source_type,
                symbol=request.symbol,
                timeframe=request.timeframe,
                request_time=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"cTrader data fetch failed: {e}")
            raise DataSourceError(f"cTrader fetch failed: {e}")
    
    async def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get latest candle from cTrader."""
        try:
            symbols = await self.get_symbols()
            pair_id = self._symbol_to_pair_id(symbol, symbols)
            
            params = {
                "pair": pair_id,
                "timeframe": timeframe
            }
            
            if not self.client:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{self.base_url}/getLatestCandle", params=params)
            else:
                response = await self.client.get(f"{self.base_url}/getLatestCandle", params=params)
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"cTrader latest candle fetch failed: {e}")
            return None
    
    def _symbol_to_pair_id(self, symbol: str, symbols: Dict[str, Any]) -> int:
        """Convert symbol to pair ID - same logic as InfluxDB."""
        if isinstance(symbols, dict):
            for key, value in symbols.items():
                if isinstance(value, dict) and value.get('symbol') == symbol:
                    return int(key)
                elif key == symbol:
                    return int(value) if isinstance(value, (int, str)) else int(key)
        
        try:
            return int(symbol)
        except ValueError:
            symbol_mapping = {
                'EURUSD': 189,
                'GBPUSD': 220,
                'USDJPY': 217,
                'AUDUSD': 218,
                'USDCHF': 219
            }
            return symbol_mapping.get(symbol.upper(), 189)
    
    def _json_to_dataframe(self, data_json: Dict[str, Any]) -> pd.DataFrame:
        """Convert JSON response to DataFrame."""
        if 'data' in data_json:
            data = data_json['data']
        else:
            data = data_json
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        if 'timestamp' in df.columns:
            # Handle various timestamp formats
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce', utc=True)
            # If that fails, try regular datetime parsing
            mask = df['timestamp'].isna()
            if mask.any():
                df.loc[mask, 'timestamp'] = pd.to_datetime(df.loc[mask, 'timestamp'], errors='coerce')
        
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df