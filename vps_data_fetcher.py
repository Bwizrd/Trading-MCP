#!/usr/bin/env python3
"""
Simple script to fetch tick data from VPS TypeScript API.
"""

import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional


class VPSDataFetcher:
    """Fetch data from VPS API."""
    
    # Symbol ID mapping (from your cTrader setup)
    SYMBOL_IDS = {
        "US500_SB": 220,
        "UK100_SB": 217,
        "GER40_SB": 200,
        "US30_SB": 219,
        "EURUSD": 185,
        "GBPUSD": 199,
        "USDJPY": 226,
    }
    
    def __init__(self, vps_url: str = "http://localhost:8020", api_key: Optional[str] = None):
        """
        Initialize VPS data fetcher.
        
        Args:
            vps_url: Base URL of your VPS API (tunneled to localhost:8000)
            api_key: Optional API key for authentication
        """
        self.vps_url = vps_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def fetch_tick_data(
        self, 
        symbol: str, 
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        max_ticks: int = 50000
    ) -> dict:
        """
        Fetch tick data from VPS using /getTickDataFromDB endpoint.
        
        Args:
            symbol: Trading symbol (e.g., 'US500_SB')
            start_time: Start time in ISO format (e.g., '2026-01-09T08:00:00.000Z')
            end_time: End time in ISO format
            max_ticks: Max number of ticks (default: 50000)
            
        Returns:
            Dictionary with tick data
        """
        # Get symbol ID
        pair_id = self.SYMBOL_IDS.get(symbol)
        if not pair_id:
            return {"error": f"Unknown symbol: {symbol}. Available: {list(self.SYMBOL_IDS.keys())}"}
        
        # Use the actual endpoint
        endpoint = f"{self.vps_url}/getTickDataFromDB"
        
        params = {
            "pair": pair_id,
            "maxTicks": max_ticks
        }
        
        if start_time:
            params["startDate"] = start_time
        if end_time:
            params["endDate"] = end_time
        
        try:
            print(f"Fetching from: {endpoint}")
            print(f"Parameters: {params}")
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"Response keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching tick data: {e}")
            return {"error": str(e)}
    
    def fetch_tick_data_today(self, symbol: str, start_hour: int = 8, end_hour: int = 16) -> dict:
        """
        Fetch all tick data for today (market hours).
        
        Args:
            symbol: Trading symbol
            start_hour: Start hour (default: 8 for 8am)
            end_hour: End hour (default: 16 for 4pm)
            
        Returns:
            Dictionary with today's tick data
        """
        today = datetime.now().date()
        start_time = f"{today}T{start_hour:02d}:00:00.000Z"
        end_time = f"{today}T{end_hour:02d}:30:00.000Z"
        
        print(f"Fetching tick data for {symbol} today ({today})")
        print(f"Time range: {start_time} to {end_time}")
        
        return self.fetch_tick_data(symbol, start_time, end_time, max_ticks=50000)
    
    def fetch_candles(
        self,
        symbol: str,
        timeframe: str = "1m",
        days_back: int = 1
    ) -> dict:
        """
        Fetch OHLCV candle data.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (e.g., '1m', '5m', '15m')
            days_back: Number of days to fetch
            
        Returns:
            Dictionary with candle data
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        
        # Adjust endpoint to match your API
        endpoint = f"{self.vps_url}/api/candles/{symbol}"
        
        params = {
            "timeframe": timeframe,
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        }
        
        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching candles: {e}")
            return {"error": str(e)}
    
    def test_connection(self) -> dict:
        """Test connection to VPS API."""
        try:
            # Test with a simple query for today
            today = datetime.now().date()
            start = f"{today}T08:00:00.000Z"
            end = f"{today}T09:00:00.000Z"
            
            url = f"{self.vps_url}/getTickDataFromDB?pair=220&startDate={start}&endDate={end}&maxTicks=10"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return {"success": True, "message": "Connection successful", "sample_data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def ticks_to_dataframe(self, tick_data: dict) -> pd.DataFrame:
        """
        Convert tick data to pandas DataFrame.
        
        Args:
            tick_data: Raw tick data from API
            
        Returns:
            DataFrame with tick data
        """
        if "error" in tick_data:
            print(f"Error in tick data: {tick_data['error']}")
            return pd.DataFrame()
        
        # Your API might return data directly as a list or under a key
        # Adjust based on actual response structure
        if isinstance(tick_data, list):
            ticks = tick_data
        else:
            ticks = tick_data.get("data", tick_data.get("ticks", []))
        
        if not ticks:
            print(f"No ticks found in response. Keys: {tick_data.keys() if isinstance(tick_data, dict) else 'N/A'}")
            return pd.DataFrame()
        
        df = pd.DataFrame(ticks)
        
        print(f"DataFrame columns: {df.columns.tolist()}")
        
        # Convert timestamp to datetime - adjust column name as needed
        time_col = None
        for col in ["timestamp", "time", "date", "datetime"]:
            if col in df.columns:
                time_col = col
                break
        
        if time_col:
            df[time_col] = pd.to_datetime(df[time_col], unit='ms')  # Convert milliseconds to datetime
            df.set_index(time_col, inplace=True)
        
        return df
    
    def candles_to_dataframe(self, candle_data: dict) -> pd.DataFrame:
        """
        Convert candle data to pandas DataFrame.
        
        Args:
            candle_data: Raw candle data from API
            
        Returns:
            DataFrame with OHLCV data
        """
        if "error" in candle_data:
            print(f"Error in candle data: {candle_data['error']}")
            return pd.DataFrame()
        
        candles = candle_data.get("candles", [])
        if not candles:
            print("No candles found in response")
            return pd.DataFrame()
        
        df = pd.DataFrame(candles)
        
        # Ensure standard OHLCV columns
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
            df.set_index("time", inplace=True)
        
        return df


# Example usage
if __name__ == "__main__":
    # Configure your VPS details (tunneled to localhost)
    VPS_URL = "http://localhost:8020"
    API_KEY = None
    
    # Initialize fetcher
    fetcher = VPSDataFetcher(vps_url=VPS_URL, api_key=API_KEY)
    
    # Test connection
    print("=" * 60)
    print("Testing VPS connection...")
    print("=" * 60)
    result = fetcher.test_connection()
    print(f"Connection result: {json.dumps(result, indent=2)}\n")
    
    if not result.get("success"):
        print("⚠️  Connection failed! Make sure SSH tunnel is running:")
        print("   ssh -L 8000:localhost:8020 user@vps-ip")
        exit(1)
    
    # Fetch today's tick data for US500_SB (pair ID 220)
    print("=" * 60)
    print("Fetching US500_SB tick data from 2:30pm to 8:00pm...")
    print("=" * 60)
    
    today = datetime.now().date()
    start_time = f"{today}T14:30:00.000Z"
    end_time = f"{today}T20:00:00.000Z"
    
    tick_data = fetcher.fetch_tick_data("US500_SB", start_time, end_time, max_ticks=100000)
    
    if "error" in tick_data:
        print(f"❌ Error: {tick_data['error']}")
    else:
        # Show raw response structure
        print(f"Response type: {type(tick_data)}")
        if isinstance(tick_data, dict):
            print(f"Response keys: {tick_data.keys()}")
        
        # Convert to DataFrame
        df_ticks = fetcher.ticks_to_dataframe(tick_data)
        
        if not df_ticks.empty:
            print("\n✅ Tick data loaded successfully!")
            print(f"Total ticks: {len(df_ticks)}")
            print(f"\nFirst 10 ticks:")
            print(df_ticks.head(10))
            print(f"\nLast 10 ticks:")
            print(df_ticks.tail(10))
            print(f"\nData info:")
            print(df_ticks.info())
        else:
            print("⚠️  No tick data in DataFrame")
            print(f"Raw data sample: {str(tick_data)[:500]}")
