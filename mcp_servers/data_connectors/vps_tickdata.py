#!/usr/bin/env python3
'''
MCP Server for VPS Tick Data Integration.

Connects to TypeScript API running on VPS port 8000 to fetch tick data.
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import httpx
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("vps_tickdata_connector")

# VPS API Configuration
VPS_API_URL = os.environ.get("VPS_API_URL", "http://your-vps-ip:8000")
VPS_API_KEY = os.environ.get("VPS_API_KEY", "")  # If your API requires auth


class TickDataRequest(BaseModel):
    """Request model for tick data."""
    symbol: str = Field(description="Trading symbol (e.g., 'US500_SB', 'EURUSD')")
    start_time: Optional[str] = Field(None, description="Start time (ISO format)")
    end_time: Optional[str] = Field(None, description="End time (ISO format)")
    limit: Optional[int] = Field(10000, description="Max number of ticks to fetch")


@mcp.tool()
async def fetch_tick_data(
    symbol: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 10000
) -> str:
    """
    Fetch tick data from VPS TypeScript API.
    
    Args:
        symbol: Trading symbol (e.g., 'US500_SB', 'UK100_SB')
        start_time: Start time in ISO format (e.g., '2026-01-09T00:00:00')
        end_time: End time in ISO format
        limit: Maximum number of ticks (default: 10000)
    
    Returns:
        JSON string with tick data
    """
    try:
        # Build endpoint URL - adjust based on your API structure
        endpoint = f"{VPS_API_URL}/api/ticks/{symbol}"
        
        # Build query parameters
        params = {"limit": limit}
        if start_time:
            params["start"] = start_time
        if end_time:
            params["end"] = end_time
        
        # Set up headers if authentication is needed
        headers = {}
        if VPS_API_KEY:
            headers["Authorization"] = f"Bearer {VPS_API_KEY}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            return json.dumps({
                "success": True,
                "symbol": symbol,
                "tick_count": len(data.get("ticks", [])),
                "data": data
            }, indent=2)
            
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "success": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text}"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
async def fetch_tick_data_for_today(symbol: str) -> str:
    """
    Fetch all tick data for today from VPS.
    
    Args:
        symbol: Trading symbol (e.g., 'US500_SB')
    
    Returns:
        JSON string with today's tick data
    """
    today = datetime.now().date()
    start_time = f"{today}T00:00:00"
    end_time = f"{today}T23:59:59"
    
    return await fetch_tick_data(symbol, start_time, end_time, limit=100000)


@mcp.tool()
async def fetch_ohlcv_from_vps(
    symbol: str,
    timeframe: str = "1m",
    days_back: int = 1
) -> str:
    """
    Fetch OHLCV candle data from VPS API.
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe (e.g., '1m', '5m', '15m')
        days_back: Number of days to fetch
    
    Returns:
        JSON string with OHLCV data
    """
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        
        endpoint = f"{VPS_API_URL}/api/candles/{symbol}"
        params = {
            "timeframe": timeframe,
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        }
        
        headers = {}
        if VPS_API_KEY:
            headers["Authorization"] = f"Bearer {VPS_API_KEY}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            return json.dumps({
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "candle_count": len(data.get("candles", [])),
                "data": data
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
async def test_vps_connection() -> str:
    """
    Test connection to VPS API.
    
    Returns:
        Connection status and VPS info
    """
    try:
        endpoint = f"{VPS_API_URL}/health"  # Adjust to your health check endpoint
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(endpoint)
            response.raise_for_status()
            
            return json.dumps({
                "success": True,
                "message": "Connected to VPS successfully",
                "url": VPS_API_URL,
                "response": response.json()
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "url": VPS_API_URL,
            "message": "Failed to connect to VPS"
        })


if __name__ == "__main__":
    mcp.run()
