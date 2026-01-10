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
import os
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

# VPS Tick Data Configuration
VPS_TICK_ENABLED = os.environ.get("VPS_TICK_ENABLED", "true").lower() == "true"
VPS_TICK_URL = os.environ.get("VPS_TICK_URL", "http://localhost:8020")

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
        use_tick_data: bool = False,
        **kwargs
    ) -> MarketDataResponse:
        """
        Get market data using the existing working _fetch_historical_data function.
        
        This method provides the interface expected by UniversalBacktestEngine.
        """
        import sys
        print(f"🔥 DATA CONNECTOR CALLED: use_tick_data={use_tick_data}", file=sys.stderr, flush=True)
        logger.info(f"📊 get_market_data called: {symbol} {timeframe} from {start_date} to {end_date}")
        logger.info(f"🎯 TICK DATA MODE: {use_tick_data}")
        
        try:
            # Use the correct API endpoints directly instead of broken _fetch_historical_data
            import httpx
            
            # Get symbol mapping first
            async with httpx.AsyncClient(timeout=30.0) as client:
                symbols_response = await client.get("http://localhost:8000/symbols")
                symbols_data = symbols_response.json()
                
                # Find pair ID for symbol
                # InfluxDB stores symbols with _SB suffix, but cTrader API uses base symbol
                pair_id = None
                symbols_list = symbols_data.get('symbols', [])
                base_symbol = symbol.replace('_SB', '')  # Remove _SB suffix if present
                
                for sym in symbols_list:
                    sym_name = sym.get('name', '')
                    # Check both exact match and with/without _SB suffix
                    if sym_name == symbol or sym_name == base_symbol or sym_name == f"{base_symbol}_SB":
                        pair_id = sym.get('value')
                        break
                
                if not pair_id:
                    raise Exception(f"Symbol {symbol} (or {base_symbol}) not found in symbols list")
                
                # Calculate proper number of bars based on timeframe and date range
                days_diff = (end_date - start_date).days if isinstance(end_date, datetime) and isinstance(start_date, datetime) else 30
                
                # Calculate bars per day based on timeframe
                bars_per_day = {
                    "1m": 1440, "5m": 288, "15m": 96, "30m": 48,
                    "1h": 24, "4h": 6, "1d": 1
                }
                estimated_bars = days_diff * bars_per_day.get(timeframe, 48)
                
                # Add small buffer (10%) and limit to reasonable max
                bars = min(int(estimated_bars * 1.1), 10000)
                logger.info(f"Calculated {bars} bars for {days_diff} days of {timeframe} data")

                # Check if tick data is requested
                if use_tick_data:
                    logger.info("🎯 TICK DATA MODE: Fetching tick data instead of candles")
                    
                    # Use VPS endpoint if enabled, otherwise use localhost
                    base_url = VPS_TICK_URL if VPS_TICK_ENABLED else "http://localhost:8000"
                    data_source = "VPS_TickData" if VPS_TICK_ENABLED else "InfluxDB_tick_data"
                    
                    logger.info(f"📡 Using tick data endpoint: {base_url}")
                    
                    # For tick data, use warmup start time to ensure indicators have sufficient data
                    # This fetches from earlier in the day (e.g., 06:00) instead of market open (08:00)
                    start_iso = start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z') if isinstance(start_date, datetime) else f"{start_date}T00:00:00.000Z"
                    end_iso = end_date.strftime('%Y-%m-%dT23:59:59.000Z') if isinstance(end_date, datetime) else f"{end_date}T23:59:59.000Z"
                    
                    # CRITICAL: Use 300,000 maxTicks to cover full trading day
                    # US500 averages ~110 ticks/minute = ~158,400 ticks/day
                    # 300,000 provides safety margin for high-volatility periods
                    tick_url = f"{base_url}/getTickDataFromDB?pair={pair_id}&startDate={start_iso}&endDate={end_iso}&maxTicks=300000"
                    logger.info(f"Fetching tick data: {tick_url}")
                    
                    tick_response = await client.get(tick_url)
                    if tick_response.status_code == 200:
                        tick_data = tick_response.json()
                        if 'data' in tick_data and len(tick_data['data']) > 0:
                            logger.info(f"✅ Received {len(tick_data['data'])} ticks, converting to candles...")
                            # Convert ticks to 1-second candles first
                            second_candles = self._convert_ticks_to_candles(tick_data['data'])
                            
                            # For tick data mode with sub-minute timeframes, return 1-second candles directly
                            # This allows tick-level precision for trade entries
                            if timeframe.lower() in ['1s', 'tick']:
                                logger.info(f"✅ Returning {len(second_candles)} 1-second candles for tick-level precision")
                                # Warmup disabled - return all candles
                                return MarketDataResponse(
                                    data=second_candles,
                                    source="InfluxDB_tick_data",
                                    symbol=symbol,
                                    timeframe="1s",
                                    start_date=start_date,
                                    end_date=end_date
                                )
                            
                            # For minute+ timeframes, we need both:
                            # - Resampled candles for strategy signal generation
                            # - Keep second candles for tick-level execution precision
                            # Return second candles but with metadata indicating target timeframe
                            logger.info(f"✅ Converted {len(tick_data['data'])} ticks → {len(second_candles)} 1-second candles (tick precision mode)")
                            # Warmup disabled - return all candles
                            return MarketDataResponse(
                                data=second_candles,
                                source=data_source,
                                symbol=symbol,
                                timeframe=timeframe,  # Original timeframe for strategy calculations
                                start_date=start_date,
                                end_date=end_date
                            )
                        else:
                            logger.warning("⚠️ Tick data response empty, falling back to standard candles")
                    else:
                        logger.warning(f"⚠️ Tick data fetch failed (status {tick_response.status_code}), falling back to standard candles")
                
                # Fetch data at requested timeframe
                timeframe_lower = timeframe.lower()
                start_iso = start_date.strftime('%Y-%m-%dT00:00:00.000Z') if isinstance(start_date, datetime) else f"{start_date}T00:00:00.000Z"
                end_iso = end_date.strftime('%Y-%m-%dT23:59:59.000Z') if isinstance(end_date, datetime) else f"{end_date}T23:59:59.000Z"

                date_url = f"http://localhost:8000/getDataByDates?pair={pair_id}&timeframe={timeframe_lower}&startDate={start_iso}&endDate={end_iso}"
                logger.info(f"Fetching {timeframe} data: {date_url}")

                date_response = await client.get(date_url)
                if date_response.status_code == 200:
                    date_data = date_response.json()
                    if 'data' in date_data and len(date_data['data']) > 0:
                        data_frame = date_data['data']
                        data_source = "cTrader API"
                        logger.info(f"Successfully fetched {len(data_frame)} {timeframe} candles from cTrader API")
                    else:
                        # Fallback to InfluxDB if date range fails
                        logger.warning("No data from date range API, trying InfluxDB fallback")
                        influx_url = f"http://localhost:8000/getDataFromDB?pair={pair_id}&timeframe={timeframe_lower}&bars={bars}"
                        influx_response = await client.get(influx_url)

                        if influx_response.status_code == 200:
                            influx_data = influx_response.json()
                            if influx_data and 'data' in influx_data and len(influx_data['data']) > 0:
                                data_frame = influx_data['data']
                                data_source = "InfluxDB"
                                logger.info(f"Fetched {len(data_frame)} candles from InfluxDB fallback")
                            else:
                                raise Exception("No data from InfluxDB fallback")
                        else:
                            raise Exception("Both date range API and InfluxDB failed")
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
                # Warmup disabled - return all candles
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
    
    async def get_execution_window(
        self,
        symbol: str,
        signal_time: datetime,
        window_minutes: int = 15,
        pre_minutes: int = 2
    ) -> MarketDataResponse:
        """
        Get a small window of 1-minute data around a trading signal.
        
        This is optimized for signal-driven architecture where we only fetch
        the minimal data needed for precise trade execution.
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            signal_time: When the signal was generated
            window_minutes: Minutes of data to fetch after signal (default: 15)
            pre_minutes: Minutes of data to fetch before signal (default: 2)
            
        Returns:
            MarketDataResponse with 1-minute candles for the window
        """
        start_time = signal_time - timedelta(minutes=pre_minutes)
        end_time = signal_time + timedelta(minutes=window_minutes)
        
        logger.debug(f"Fetching execution window for {symbol}: {start_time} to {end_time} ({window_minutes + pre_minutes} minutes)")
        
        # Use optimized method with proper bar calculation for execution windows
        total_minutes = window_minutes + pre_minutes
        bars_needed = max(total_minutes + 5, 20)  # Ensure minimum 20 bars, add 5 buffer
        
        return await self.get_market_data_optimized(
            symbol=symbol,
            timeframe="1m",
            start_date=start_time,
            end_date=end_time,
            max_bars=bars_needed
        )
    
    async def get_market_data_optimized(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        max_bars: Optional[int] = None,
        **kwargs
    ) -> MarketDataResponse:
        """
        Optimized version of get_market_data with configurable bar limits.
        
        This version allows bypassing the 10,000 bar limit for signal-driven
        architecture where we fetch small windows of data.
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            start_date: Start date for data
            end_date: End date for data
            max_bars: Maximum bars to fetch (None = unlimited)
            
        Returns:
            MarketDataResponse with market data
        """
        logger.info(f"Fetching optimized market data for {symbol} {timeframe} from {start_date} to {end_date}")
        
        try:
            import httpx
            
            # Get symbol mapping first
            async with httpx.AsyncClient(timeout=30.0) as client:
                symbols_response = await client.get("http://localhost:8000/symbols")
                symbols_data = symbols_response.json()
                
                # Find pair ID for symbol
                # InfluxDB stores symbols with _SB suffix, but cTrader API uses base symbol
                pair_id = None
                symbols_list = symbols_data.get('symbols', [])
                base_symbol = symbol.replace('_SB', '')  # Remove _SB suffix if present
                
                for sym in symbols_list:
                    sym_name = sym.get('name', '')
                    # Check both exact match and with/without _SB suffix
                    if sym_name == symbol or sym_name == base_symbol or sym_name == f"{base_symbol}_SB":
                        pair_id = sym.get('value')
                        break
                
                if not pair_id:
                    raise Exception(f"Symbol {symbol} (or {base_symbol}) not found in symbols list")
                
                # Calculate bars needed if max_bars not specified
                if max_bars is None:
                    # For execution windows, calculate based on actual time difference
                    if isinstance(end_date, datetime) and isinstance(start_date, datetime):
                        time_diff_minutes = int((end_date - start_date).total_seconds() / 60)
                        if timeframe == "1m":
                            bars = max(time_diff_minutes + 10, 20)  # Ensure minimum 20 bars for 1m windows
                        else:
                            days_diff = (end_date - start_date).days
                            bars_per_day = {
                                "5m": 288, "15m": 96, "30m": 48,
                                "1h": 24, "4h": 6, "1d": 1
                            }
                            estimated_bars = days_diff * bars_per_day.get(timeframe, 48)
                            bars = min(estimated_bars * 2, 50000)
                    else:
                        bars = 100  # Default fallback
                else:
                    bars = max_bars
                
                logger.debug(f"Requesting {bars} bars for {timeframe} data")
                
                # For execution windows with specific date ranges, use new InfluxDB date range API
                timeframe_lower = timeframe.lower()
                
                # Format dates for API
                start_iso = start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z') if isinstance(start_date, datetime) else f"{start_date}T00:00:00.000Z"
                end_iso = end_date.strftime('%Y-%m-%dT%H:%M:%S.999Z') if isinstance(end_date, datetime) else f"{end_date}T23:59:59.999Z"
                
                # Try new InfluxDB date range API first
                influx_date_url = f"http://localhost:8000/getDataFromDBByDates?pair={pair_id}&timeframe={timeframe_lower}&startDate={start_iso}&endDate={end_iso}"
                
                influx_response = await client.get(influx_date_url)
                if influx_response.status_code == 200:
                    influx_data = influx_response.json()
                    if 'data' in influx_data and len(influx_data['data']) > 0:
                        data_frame = influx_data['data']
                        data_source = "InfluxDB (date range)"
                        logger.info(f"Fetched {len(data_frame)} candles from InfluxDB date range API")
                    else:
                        raise Exception("No data from InfluxDB date range")
                else:
                    # Fallback to cTrader API if InfluxDB doesn't have the data
                    logger.warning(f"InfluxDB date range failed (status {influx_response.status_code}), falling back to cTrader API")
                    date_url = f"http://localhost:8000/getDataByDates?pair={pair_id}&timeframe={timeframe_lower}&startDate={start_iso}&endDate={end_iso}"
                    
                    date_response = await client.get(date_url)
                    if date_response.status_code == 200:
                        date_data = date_response.json()
                        if 'data' in date_data and len(date_data['data']) > 0:
                            data_frame = date_data['data']
                            data_source = "cTrader API"
                        else:
                            raise Exception("No data in date range response")
                    else:
                        raise Exception(f"Both InfluxDB and cTrader API failed")
            
            if data_frame and len(data_frame) > 0:
                # Convert JSON data to Candle objects
                candles = []
                for item in data_frame:
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
                
                logger.debug(f"Successfully fetched {len(candles)} candles from {data_source}")
                return MarketDataResponse(
                    data=candles,
                    source=data_source,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date
                )
                
        except Exception as e:
            logger.error(f"Optimized data fetching failed: {e}")
        
        # If failed, return empty response
        return MarketDataResponse(
            data=[],
            source="Failed",
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
        )
    
    def _convert_ticks_to_candles(self, ticks: List[Dict]) -> List[Candle]:
        """
        Convert tick data (bid/ask) to 1-second OHLCV candles.
        Groups ticks by second and creates candles from mid prices.
        
        Args:
            ticks: List of tick data dictionaries with timestamp, bid, ask
            
        Returns:
            List of Candle objects aggregated to 1-second intervals
        """
        if not ticks:
            return []
        
        import pandas as pd
        from datetime import datetime as dt
        
        try:
            # Convert to DataFrame for easier grouping
            df = pd.DataFrame(ticks)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['mid'] = (df['bid'] + df['ask']) / 2  # Calculate mid price
            df['second'] = df['timestamp'].dt.floor('1s')  # Group by second
            
            # Aggregate into 1-second candles
            candles = []
            for second, group in df.groupby('second'):
                candle = Candle(
                    timestamp=second.to_pydatetime(),
                    open=float(group['mid'].iloc[0]),
                    high=float(group['mid'].max()),
                    low=float(group['mid'].min()),
                    close=float(group['mid'].iloc[-1]),
                    volume=int(len(group))  # Number of ticks as volume
                )
                candles.append(candle)
            
            # Sort by timestamp to ensure chronological order
            candles.sort(key=lambda c: c.timestamp)
            logger.info(f"Converted {len(ticks)} ticks to {len(candles)} 1-second candles")
            return candles
            
        except Exception as e:
            logger.error(f"Failed to convert ticks to candles: {e}", exc_info=True)
            return []
    
    def _resample_candles(self, candles: List[Candle], target_timeframe: str) -> List[Candle]:
        """
        Resample 1-second candles to a target timeframe (e.g., 1m, 5m, 15m).
        
        Args:
            candles: List of 1-second candle objects
            target_timeframe: Target timeframe string (e.g., '1m', '5m', '15m', '30m', '1h')
            
        Returns:
            List of resampled Candle objects
        """
        if not candles:
            return []
        
        import pandas as pd
        
        try:
            # Parse timeframe to pandas frequency
            timeframe_map = {
                '1m': '1T', '5m': '5T', '15m': '15T', '30m': '30T',
                '1h': '1H', '4h': '4H', '1d': '1D'
            }
            
            freq = timeframe_map.get(target_timeframe.lower(), '1T')
            
            # Convert candles to DataFrame
            df = pd.DataFrame([{
                'timestamp': c.timestamp,
                'open': c.open,
                'high': c.high,
                'low': c.low,
                'close': c.close,
                'volume': c.volume
            } for c in candles])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Resample to target timeframe
            resampled = df.resample(freq).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            # Convert back to Candle objects
            resampled_candles = []
            for timestamp, row in resampled.iterrows():
                candle = Candle(
                    timestamp=timestamp.to_pydatetime(),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume'])
                )
                resampled_candles.append(candle)
            
            logger.info(f"Resampled {len(candles)} 1s candles to {len(resampled_candles)} {target_timeframe} candles")
            return resampled_candles
            
        except Exception as e:
            logger.error(f"Failed to resample candles: {e}", exc_info=True)
            return candles  # Return original candles if resampling fails

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