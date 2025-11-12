#!/usr/bin/env python3
'''
MCP Server for cTrader Data Integration.

This server provides tools to fetch market data from cTrader API.
It can be used by any trading strategy that needs real market data.

Features:
- Real-time price data
- Historical candle data  
- Multiple timeframes
- Symbol management
'''

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timedelta, time as dt_time
import json
import httpx
import re
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP
from shared.models import BacktestInput, TradeDirection, TradeResult, ResponseFormat
from shared.utils import (get_config, calculate_pips, format_timestamp, 
                         DEFAULT_STOP_LOSS_PIPS, DEFAULT_TAKE_PROFIT_PIPS, 
                         DEFAULT_SIGNAL_TIME, CHARACTER_LIMIT)
from config.settings import CTRADER_API_CONFIG

# Initialize the MCP server
mcp = FastMCP("ctrader_data_connector")

# Constants
config = get_config()
API_BASE_URL = config["ctrader_api_url"]
API_USERNAME = config["ctrader_api_username"] 
API_PASSWORD = config["ctrader_api_password"]

# Symbol ID mapping (from your API)
SYMBOL_IDS = {
    "EURUSD": 185,  # EURUSD_SB
    "GBPUSD": 199,  # GBPUSD_SB
    "USDJPY": 226,  # USDJPY_SB
    "AUDUSD": 158,  # AUDUSD_SB
    "USDCAD": 221,  # USDCAD_SB
    "USDCHF": 222,  # USDCHF_SB
    "NZDUSD": 211,  # NZDUSD_SB
    "EURGBP": 175,  # EURGBP_SB
    "EURJPY": 177,  # EURJPY_SB
    "EURCHF": 173,  # EURCHF_SB
    "EURAUD": 171,  # EURAUD_SB
    "EURCAD": 172,  # EURCAD_SB
    "EURNZD": 180,  # EURNZD_SB
    "GBPJPY": 192,  # GBPJPY_SB
    "GBPCHF": 191,  # GBPCHF_SB
    "GBPAUD": 189,  # GBPAUD_SB
    "GBPCAD": 190,  # GBPCAD_SB
    "GBPNZD": 195,  # GBPNZD_SB
    "AUDJPY": 155,  # AUDJPY_SB
    "AUDNZD": 156,  # AUDNZD_SB
    "AUDCAD": 153,  # AUDCAD_SB
    "NZDJPY": 210,  # NZDJPY_SB
    "CADJPY": 162,  # CADJPY_SB
    "CHFJPY": 163,  # CHFJPY_SB
    "GER40": 200,   # GER40_SB (DAX index)
    "UK100": 217,   # UK100_SB (FTSE index)
    "US30": 219,    # US30_SB (Dow Jones index)
}

# Timeframe mapping (from your API)
TIMEFRAMES = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d"
}

# Enums
class ResponseFormat(str, Enum):
    '''Output format for tool responses.'''
    MARKDOWN = "markdown"
    JSON = "json"

class TradeDirection(str, Enum):
    '''Trade direction.'''
    BUY = "BUY"
    SELL = "SELL"

class TradeResult(str, Enum):
    '''Trade outcome.'''
    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"

# Pydantic Models for Input Validation
class BacktestInput(BaseModel):
    '''Input for backtesting the VWAP strategy.'''
    model_config = ConfigDict(str_strip_whitespace=True)
    
    start_date: str = Field(
        description="Start date for optimization (YYYY-MM-DD format, or flexible formats like 'October 20', '10-20')",
        examples=["2025-10-01", "October 20", "10-20", "2025-10-15"]
    )
    end_date: str = Field(
        description="End date for optimization (YYYY-MM-DD format, or flexible formats like 'October 25', '10-25')", 
        examples=["2025-10-25", "October 25", "10-25", "2025-10-31"]
    )
    symbol: str = Field(
        default="EURUSD",
        description="Currency pair to backtest",
        examples=["EURUSD", "GBPUSD", "USDJPY"]
    )
    timeframe: str = Field(
        default="30m",
        description="Timeframe for backtesting",
        examples=["15m", "30m", "1h"]
    )
    stop_loss_pips: int = Field(
        default=DEFAULT_STOP_LOSS_PIPS,
        description="Stop loss in pips",
        ge=1,
        le=100
    )
    take_profit_pips: int = Field(
        default=DEFAULT_TAKE_PROFIT_PIPS,
        description="Take profit in pips",
        ge=1,
        le=200
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Format for the response"
    )
    export_csv: bool = Field(
        default=False,
        description="Export trade details to CSV file"
    )

class CurrentMarketInput(BaseModel):
    '''Input model for getting current market conditions.'''
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    symbol: str = Field(
        default="EURUSD",
        description="Trading pair symbol (e.g., 'EURUSD', 'GBPUSD')",
        min_length=6,
        max_length=20
    )
    timeframe: str = Field(
        default="30m",
        description="Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)",
        pattern=r'^(1m|5m|15m|30m|1h|4h|1d)$'
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

class StrategyPerformanceInput(BaseModel):
    '''Input model for strategy performance analysis.'''
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    days: int = Field(
        default=30,
        description="Number of days to analyze (e.g., 7, 30, 90)",
        ge=1,
        le=365
    )
    symbol: str = Field(
        default="EURUSD",
        description="Trading pair symbol",
        min_length=6,
        max_length=20
    )
    timeframe: str = Field(
        default="30m",
        description="Timeframe for analysis",
        pattern=r'^(1m|5m|15m|30m|1h|4h|1d)$'
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )

# Helper Classes
class Trade:
    '''Represents a single trade.'''
    def __init__(
        self,
        date: str,
        direction: TradeDirection,
        entry_price: float,
        vwap: float,
        stop_loss: float,
        take_profit: float
    ):
        self.date = date
        self.direction = direction
        self.entry_price = entry_price
        self.vwap = vwap
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.exit_price: Optional[float] = None
        self.pips: Optional[float] = None
        self.result: Optional[TradeResult] = None

    def close(self, exit_price: float, pip_size: float = 0.0001):
        '''Close the trade and calculate P&L.'''
        self.exit_price = exit_price
        
        if self.direction == TradeDirection.BUY:
            self.pips = (exit_price - self.entry_price) / pip_size
        else:  # SELL
            self.pips = (self.entry_price - exit_price) / pip_size
        
        if self.pips > 0.5:
            self.result = TradeResult.WIN
        elif self.pips < -0.5:
            self.result = TradeResult.LOSS
        else:
            self.result = TradeResult.BREAKEVEN

    def to_dict(self) -> Dict[str, Any]:
        '''Convert trade to dictionary.'''
        return {
            "date": self.date,
            "direction": self.direction.value,
            "entry_price": round(self.entry_price, 5),
            "vwap": round(self.vwap, 5),
            "stop_loss": round(self.stop_loss, 5),
            "take_profit": round(self.take_profit, 5),
            "exit_price": round(self.exit_price, 5) if self.exit_price else None,
            "pips": round(self.pips, 2) if self.pips else None,
            "result": self.result.value if self.result else None
        }

# API Helper Functions
def _get_symbol_id(symbol: str) -> Optional[int]:
    '''Get symbol ID from symbol name.'''
    return SYMBOL_IDS.get(symbol.upper())

# Helper Functions
def _parse_flexible_date(date_str: str) -> str:
    '''Parse various date formats and default to current year (2025).'''
    current_year = datetime.now().year  # 2025
    
    # If already in YYYY-MM-DD format, return as-is
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # If in MM-DD format, add current year
    if re.match(r'^\d{1,2}-\d{1,2}$', date_str):
        parts = date_str.split('-')
        month = parts[0].zfill(2)
        day = parts[1].zfill(2)
        return f"{current_year}-{month}-{day}"
    
    # Handle natural language dates like "October 20", "Oct 20", etc.
    month_names = {
        'january': '01', 'jan': '01',
        'february': '02', 'feb': '02',
        'march': '03', 'mar': '03',
        'april': '04', 'apr': '04',
        'may': '05',
        'june': '06', 'jun': '06',
        'july': '07', 'jul': '07',
        'august': '08', 'aug': '08',
        'september': '09', 'sep': '09', 'sept': '09',
        'october': '10', 'oct': '10',
        'november': '11', 'nov': '11',
        'december': '12', 'dec': '12'
    }
    
    # Try to parse "Month DD" format
    for month_name, month_num in month_names.items():
        pattern = rf'{month_name}\s+(\d{{1,2}})'
        match = re.search(pattern, date_str.lower())
        if match:
            day = match.group(1).zfill(2)
            return f"{current_year}-{month_num}-{day}"
    
    # Try to parse "MM/DD" format
    if re.match(r'^\d{1,2}/\d{1,2}$', date_str):
        parts = date_str.split('/')
        month = parts[0].zfill(2)
        day = parts[1].zfill(2)
        return f"{current_year}-{month}-{day}"
    
    # Try to parse "DD/MM" format (less common but possible)
    # This is ambiguous, so we'll stick with MM/DD assumption
    
    # If we can't parse it, try datetime parsing with current year
    try:
        # Try various formats
        for fmt in ['%B %d', '%b %d', '%m/%d', '%m-%d']:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # Replace year with current year
                parsed_date = parsed_date.replace(year=current_year)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
    except:
        pass
    
    # If all else fails, return the original string (might cause an error later, but that's better than silent wrong year)
    return date_str

async def _make_api_request(
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    require_auth: bool = True
) -> Dict[str, Any]:
    '''Make authenticated request to cTrader API.'''
    auth = (API_USERNAME, API_PASSWORD) if require_auth else None
    
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{API_BASE_URL}{endpoint}",
            params=params,
            json=json_data,
            auth=auth,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()

# Data Provider Functions (Using YOUR cTrader API)
async def _fetch_historical_data(
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str = "30m"
) -> List[Dict[str, Any]]:
    '''
    Fetch historical price data from cTrader API.
    Uses /getDataByDates endpoint.
    
    FIXED: Ensures data consistency with direct API calls
    '''
    symbol_id = _get_symbol_id(symbol)
    if not symbol_id:
        raise ValueError(f"Unknown symbol: {symbol}. Available: {list(SYMBOL_IDS.keys())}")
    
    # Convert dates to ISO format for cTrader API
    # Parse flexible date formats and default to current year
    parsed_start_date = _parse_flexible_date(start_date)
    parsed_end_date = _parse_flexible_date(end_date)
    
    start_dt = datetime.strptime(parsed_start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(parsed_end_date, '%Y-%m-%d')
    
    # Format dates correctly for cTrader API (full ISO format with time)
    start_iso = start_dt.strftime('%Y-%m-%dT00:00:00.000Z')
    end_iso = end_dt.strftime('%Y-%m-%dT23:59:59.000Z')
    
    # CRITICAL FIX: Call API exactly as we verified works correctly
    data = await _make_api_request(
        "/getDataByDates",
        method="GET",
        params={
            "pair": symbol_id,
            "timeframe": timeframe,
            "startDate": start_iso,
            "endDate": end_iso
        },
        require_auth=False
    )
    
    # Validate API response structure
    if not data or "data" not in data:
        raise ValueError(f"Invalid API response for {symbol}: {data}")
    
    # Log for debugging (can remove later)
    print(f"DEBUG: Fetched {len(data.get('data', []))} candles for {symbol} from {start_iso} to {end_iso}")
    
    # Transform to expected format with validation
    candles = []
    if "data" in data and data["data"]:
        for item in data["data"]:
            # Validate candle data
            required_fields = ['timestamp', 'open', 'high', 'low', 'close']
            if not all(field in item for field in required_fields):
                print(f"WARNING: Invalid candle data: {item}")
                continue
                
            # Convert timestamp from milliseconds to datetime
            dt = datetime.fromtimestamp(item["timestamp"] / 1000)
            candles.append({
                "date": dt.strftime('%Y-%m-%d'),
                "timestamp": item["timestamp"],
                "open": float(item["open"]),  # Ensure numeric types
                "high": float(item["high"]),
                "low": float(item["low"]), 
                "close": float(item["close"]),
                "volume": int(item.get("volume", 0))
            })
    
    # Log critical info for debugging
    if candles:
        print(f"DEBUG: First candle: {candles[0]}")
        print(f"DEBUG: Last candle: {candles[-1]}")
        # Check for 8:30 AM candle if it's in the data
        for candle in candles:
            candle_dt = datetime.fromtimestamp(candle["timestamp"] / 1000)
            if candle_dt.hour == 8 and candle_dt.minute == 30:
                print(f"DEBUG: Found 8:30 AM candle: {candle}")
                break
    
    return candles

async def _fetch_current_price(symbol: str, timeframe: str = "30m") -> Dict[str, Any]:
    '''
    Fetch current market price from cTrader API.
    Uses /getLatestCandle endpoint.
    '''
    symbol_id = _get_symbol_id(symbol)
    if not symbol_id:
        raise ValueError(f"Unknown symbol: {symbol}")
    
    data = await _make_api_request(
        "/getLatestCandle",
        params={
            "pair": symbol_id,
            "timeframe": timeframe
        }
    )
    
    # Extract latest candle (live or last completed)
    latest = data.get("latest", {})
    
    return {
        "symbol": symbol,
        "bid": latest.get("close", 0),  # Using close as bid approximation
        "ask": latest.get("close", 0),  # Using close as ask approximation
        "timestamp": datetime.fromtimestamp(latest.get("timestamp", 0) / 1000).isoformat(),
        "isLive": latest.get("isLive", False),
        "isComplete": latest.get("isComplete", False)
    }

async def _fetch_last_closed_candle(symbol: str, timeframe: str = "30m") -> Dict[str, Any]:
    '''
    Fetch the last closed/completed candle.
    Uses /getLastClosedCandle endpoint.
    '''
    symbol_id = _get_symbol_id(symbol)
    if not symbol_id:
        raise ValueError(f"Unknown symbol: {symbol}")
    
    data = await _make_api_request(
        "/getLastClosedCandle",
        params={
            "pair": symbol_id,
            "timeframe": timeframe
        }
    )
    
    return data.get("candle", {})

# Strategy Logic Functions
def _calculate_vwap(candles: List[Dict[str, Any]]) -> float:
    '''Calculate VWAP from a list of candles.'''
    if not candles:
        return 0.0
    
    total_volume = sum(c.get('volume', 0) for c in candles)
    if total_volume == 0:
        # Fallback to simple average if no volume data
        return sum((c['high'] + c['low'] + c['close']) / 3 for c in candles) / len(candles)
    
    vwap = sum(
        ((c['high'] + c['low'] + c['close']) / 3) * c.get('volume', 0)
        for c in candles
    ) / total_volume
    
    return vwap

def _generate_signal(price: float, vwap: float) -> TradeDirection:
    '''Generate trading signal based on price vs VWAP.'''
    if price > vwap:
        return TradeDirection.SELL
    else:
        return TradeDirection.BUY

def _calculate_stop_and_target(
    entry_price: float,
    direction: TradeDirection,
    stop_loss_pips: int,
    take_profit_pips: int,
    pip_size: float = 0.0001
) -> tuple[float, float]:
    '''Calculate stop loss and take profit levels.'''
    if direction == TradeDirection.BUY:
        stop_loss = entry_price - (stop_loss_pips * pip_size)
        take_profit = entry_price + (take_profit_pips * pip_size)
    else:  # SELL
        stop_loss = entry_price + (stop_loss_pips * pip_size)
        take_profit = entry_price - (take_profit_pips * pip_size)
    
    return stop_loss, take_profit

def _simulate_trade_exit(
    trade: Trade,
    day_candles: List[Dict[str, Any]],
    pip_size: float = 0.0001
) -> None:
    '''Simulate trade exit based on intraday price action.'''
    for candle in day_candles:
        high = candle['high']
        low = candle['low']
        
        if trade.direction == TradeDirection.BUY:
            if low <= trade.stop_loss:
                trade.close(trade.stop_loss, pip_size)
                return
            if high >= trade.take_profit:
                trade.close(trade.take_profit, pip_size)
                return
        else:  # SELL
            if high >= trade.stop_loss:
                trade.close(trade.stop_loss, pip_size)
                return
            if low <= trade.take_profit:
                trade.close(trade.take_profit, pip_size)
                return
    
    # If neither hit, close at end of day
    trade.close(day_candles[-1]['close'], pip_size)

def _calculate_performance_stats(trades: List[Trade]) -> Dict[str, Any]:
    '''Calculate comprehensive performance statistics.'''
    if not trades:
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "breakeven": 0,
            "win_rate": 0.0,
            "total_pips": 0.0,
            "avg_win_pips": 0.0,
            "avg_loss_pips": 0.0,
            "largest_win_pips": 0.0,
            "largest_loss_pips": 0.0,
            "profit_factor": 0.0
        }
    
    wins = [t for t in trades if t.result == TradeResult.WIN]
    losses = [t for t in trades if t.result == TradeResult.LOSS]
    breakeven = [t for t in trades if t.result == TradeResult.BREAKEVEN]
    
    total_pips = sum(t.pips for t in trades if t.pips)
    total_win_pips = sum(t.pips for t in wins if t.pips)
    total_loss_pips = abs(sum(t.pips for t in losses if t.pips))
    
    return {
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "breakeven": len(breakeven),
        "win_rate": len(wins) / len(trades) if trades else 0.0,
        "total_pips": round(total_pips, 2),
        "avg_win_pips": round(total_win_pips / len(wins), 2) if wins else 0.0,
        "avg_loss_pips": round(total_loss_pips / len(losses), 2) if losses else 0.0,
        "largest_win_pips": round(max((t.pips for t in wins if t.pips), default=0), 2),
        "largest_loss_pips": round(min((t.pips for t in losses if t.pips), default=0), 2),
        "profit_factor": round(total_win_pips / total_loss_pips, 2) if total_loss_pips > 0 else 0.0
    }

# Format Functions
def _format_backtest_markdown(
    stats: Dict[str, Any],
    trades: List[Trade],
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str
) -> str:
    '''Format backtest results as markdown.'''
    lines = [
        f"# VWAP Strategy Backtest Results",
        f"",
        f"**Symbol**: {symbol}",
        f"**Timeframe**: {timeframe}",
        f"**Period**: {start_date} to {end_date}",
        f"**Strategy**: At 8:30, BUY if price < VWAP, SELL if price > VWAP",
        f"**Data Source**: cTrader API (Real Market Data)",
        f"",
        f"## Performance Summary",
        f"",
        f"- **Total Trades**: {stats['total_trades']}",
        f"- **Wins**: {stats['wins']} ({stats['win_rate']:.1%})",
        f"- **Losses**: {stats['losses']}",
        f"- **Net Pips**: {stats['total_pips']:+.1f}",
        f"- **Average Win**: +{stats['avg_win_pips']:.1f} pips",
        f"- **Average Loss**: {stats['avg_loss_pips']:.1f} pips",
        f"- **Largest Win**: +{stats['largest_win_pips']:.1f} pips",
        f"- **Largest Loss**: {stats['largest_loss_pips']:.1f} pips",
        f"- **Profit Factor**: {stats['profit_factor']:.2f}",
        f"",
        f"## Trade History",
        f""
    ]
    
    displayed_trades = trades[:50]
    for i, trade in enumerate(displayed_trades, 1):
        result_emoji = "✅" if trade.result == TradeResult.WIN else "❌" if trade.result == TradeResult.LOSS else "⚖️"
        lines.append(
            f"{i}. **{trade.date}** | {trade.direction.value} at {trade.entry_price:.5f} "
            f"(VWAP: {trade.vwap:.5f}) → {trade.exit_price:.5f} | "
            f"{trade.pips:+.1f} pips {result_emoji}"
        )
    
    if len(trades) > 50:
        lines.append(f"")
        lines.append(f"*Showing first 50 of {len(trades)} trades*")
    
    return "\n".join(lines)

def _format_backtest_json(
    stats: Dict[str, Any],
    trades: List[Trade],
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str
) -> str:
    '''Format backtest results as JSON.'''
    result = {
        "symbol": symbol,
        "timeframe": timeframe,
        "start_date": start_date,
        "end_date": end_date,
        "data_source": "cTrader API",
        "performance": stats,
        "trades": [t.to_dict() for t in trades]
    }
    return json.dumps(result, indent=2)

def _format_current_market_markdown(
    symbol: str,
    timeframe: str,
    current_price: Dict[str, Any],
    vwap: float,
    signal: TradeDirection
) -> str:
    '''Format current market conditions as markdown.'''
    mid_price = (current_price['bid'] + current_price['ask']) / 2
    spread_pips = (current_price['ask'] - current_price['bid']) / 0.0001
    
    signal_emoji = "🔴" if signal == TradeDirection.SELL else "🟢"
    live_indicator = "🔴 LIVE" if current_price.get('isLive') else "📊 Last Closed"
    
    lines = [
        f"# Current Market Analysis - {symbol}",
        f"",
        f"**Timeframe**: {timeframe}",
        f"**Status**: {live_indicator}",
        f"**Current Price**: {mid_price:.5f}",
        f"**Bid**: {current_price['bid']:.5f} | **Ask**: {current_price['ask']:.5f}",
        f"**Spread**: {spread_pips:.1f} pips",
        f"**VWAP**: {vwap:.5f}",
        f"**Data Source**: cTrader API",
        f"",
        f"## Trading Signal {signal_emoji}",
        f"",
        f"**Direction**: {signal.value}",
        f"**Reason**: Price ({mid_price:.5f}) is {'above' if signal == TradeDirection.SELL else 'below'} VWAP ({vwap:.5f})",
        f"",
        f"*Strategy: At 8:30, the strategy would {'SELL' if signal == TradeDirection.SELL else 'BUY'} based on current conditions*"
    ]
    
    return "\n".join(lines)

# Error Handling
def _handle_error(e: Exception) -> str:
    '''Consistent error formatting across all tools.'''
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 404:
            return "Error: Data not found. Please check the symbol and date range."
        elif e.response.status_code == 401:
            return "Error: API authentication failed. Please check CTRADER_API_USERNAME and CTRADER_API_PASSWORD environment variables."
        elif e.response.status_code == 429:
            return "Error: Rate limit exceeded. Please wait before making more requests."
        return f"Error: API request failed with status {e.response.status_code}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    elif isinstance(e, ValueError):
        return f"Error: Invalid input - {str(e)}"
    elif isinstance(e, httpx.ConnectError):
        return f"Error: Cannot connect to cTrader API at {API_BASE_URL}. Please check the API is running."
    return f"Error: {type(e).__name__}: {str(e)}"

# MCP Tools
@mcp.tool(
    name="get_historical_data_for_strategy",
    annotations={
        "title": "Backtest VWAP Trading Strategy (cTrader Data)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def get_historical_data_for_strategy(params: BacktestInput) -> str:
    '''
    Fetch historical data from cTrader API for strategy backtesting.
    
    This is a STRATEGY-AGNOSTIC data provider that simply fetches and returns
    historical market data. Strategy logic should be implemented in dedicated
    strategy MCP servers.
    
    Args:
        params (BacktestInput): Parameters containing symbol, dates, and timeframe
    
    Returns:
        str: JSON-formatted historical data for strategy processing
    '''
    try:
        # Fetch historical data from cTrader API
        historical_data = await _fetch_historical_data(
            params.symbol,
            params.start_date,
            params.end_date,
            params.timeframe
        )
        
        if not historical_data:
            return f"No trading data found for {params.symbol} between {params.start_date} and {params.end_date}"
        
        # Return raw data for strategy servers to process
        import json
        return json.dumps({
            "symbol": params.symbol,
            "start_date": params.start_date,
            "end_date": params.end_date,
            "timeframe": params.timeframe,
            "data": historical_data,
            "data_points": len(historical_data)
        }, indent=2)
        
    except Exception as e:
        return _handle_error(e)

@mcp.tool(
    name="get_current_market_data",
    annotations={
        "title": "Get Current Market Signal (cTrader Live Data)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def get_current_market_data(params: CurrentMarketInput) -> str:
    '''
    Get the current VWAP trading signal using live cTrader data.
    
    This tool fetches current market data from cTrader and calculates whether
    the strategy would generate a BUY or SELL signal right now.
    
    Args:
        params (CurrentMarketInput): Validated input parameters containing:
            - symbol (str): Trading pair (EURUSD, GBPUSD, etc.)
            - timeframe (str): Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Current market analysis with live signal
    '''
    try:
        # Fetch current price
        current_price = await _fetch_current_price(params.symbol, params.timeframe)
        
        # Fetch recent data for VWAP calculation
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        historical_data = await _fetch_historical_data(
            params.symbol,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            params.timeframe
        )
        
        if not historical_data:
            return f"Unable to calculate VWAP for {params.symbol}. No recent data available."
        
        # Calculate VWAP
        vwap = _calculate_vwap(historical_data)
        
        # Calculate mid price
        mid_price = (current_price['bid'] + current_price['ask']) / 2
        
        # Generate signal
        signal = _generate_signal(mid_price, vwap)
        
        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            return _format_current_market_markdown(
                params.symbol, params.timeframe, current_price, vwap, signal
            )
        else:
            result = {
                "symbol": params.symbol,
                "timeframe": params.timeframe,
                "current_price": {
                    "bid": current_price['bid'],
                    "ask": current_price['ask'],
                    "mid": round(mid_price, 5)
                },
                "vwap": round(vwap, 5),
                "signal": signal.value,
                "timestamp": current_price['timestamp'],
                "isLive": current_price.get('isLive', False),
                "data_source": "cTrader API"
            }
            return json.dumps(result, indent=2)
        
    except Exception as e:
        return _handle_error(e)

@mcp.tool(
    name="analyze_strategy_performance",
    annotations={
        "title": "Analyze Strategy Performance (cTrader Data)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def analyze_strategy_performance(params: StrategyPerformanceInput) -> str:
    '''
    Analyze VWAP strategy performance over recent period using cTrader data.
    
    Convenience tool that automatically backtests the strategy for the
    specified number of recent days.
    
    Args:
        params (StrategyPerformanceInput): Validated input parameters
    '''
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=params.days)
        
        # Create backtest parameters
        backtest_params = BacktestInput(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            symbol=params.symbol,
            timeframe=params.timeframe,
            response_format=params.response_format
        )
        
        # Run backtest
        return await get_historical_data_for_strategy(backtest_params)
        
    except Exception as e:
        return _handle_error(e)

# Optimization Input Model
class OptimizationInput(BaseModel):
    '''Input for strategy optimization.'''
    model_config = ConfigDict(str_strip_whitespace=True)
    
    start_date: str = Field(
        description="Start date for optimization (YYYY-MM-DD format)",
        examples=["2024-10-01", "2024-09-15"]
    )
    end_date: str = Field(
        description="End date for optimization (YYYY-MM-DD format)",
        examples=["2024-10-25", "2024-10-31"]
    )
    symbol: str = Field(
        default="EURUSD",
        description="Currency pair or symbol",
        examples=["EURUSD", "GBPUSD", "USDJPY"]
    )
    timeframe: str = Field(
        default="30m",
        description="Timeframe for analysis",
        examples=["15m", "30m", "1h"]
    )
    sl_range: str = Field(
        default="5-20",
        description="Stop loss range in pips (start-end)",
        examples=["5-20", "10-30"]
    )
    tp_range: str = Field(
        default="10-25", 
        description="Take profit range in pips (start-end)",
        examples=["10-25", "15-35"]
    )
    step: int = Field(
        default=5,
        description="Step size for optimization",
        examples=[1, 2, 5]
    )
    export_csv: bool = Field(
        default=True,
        description="Export results to CSV file"
    )

@mcp.tool(
    name="optimize_strategy_parameters",
    annotations={
        "title": "Optimize VWAP Strategy Parameters (cTrader Data)",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def optimize_strategy_parameters(params: OptimizationInput) -> str:
    '''
    Optimize VWAP strategy by testing multiple stop loss and take profit combinations.
    
    Tests all combinations of SL and TP within specified ranges and finds the optimal
    parameters based on various performance metrics.
    
    Args:
        params (OptimizationInput): Optimization parameters
    '''
    try:
        # Parse ranges
        sl_start, sl_end = map(int, params.sl_range.split('-'))
        tp_start, tp_end = map(int, params.tp_range.split('-'))
        
        # Generate parameter combinations
        combinations = []
        for sl in range(sl_start, sl_end + 1, params.step):
            for tp in range(tp_start, tp_end + 1, params.step):
                combinations.append((sl, tp))
        
        results = []
        
        # Test each combination
        for i, (sl, tp) in enumerate(combinations):
            try:
                # Run backtest with current parameters
                backtest_result = await _run_backtest_internal(
                    params.symbol, params.start_date, params.end_date,
                    params.timeframe, sl, tp
                )
                
                if backtest_result:
                    results.append({
                        'stop_loss': sl,
                        'take_profit': tp,
                        'total_trades': backtest_result['total_trades'],
                        'wins': backtest_result['wins'],
                        'losses': backtest_result['losses'],
                        'win_rate': backtest_result['win_rate'],
                        'net_pips': backtest_result['net_pips'],
                        'avg_win': backtest_result['avg_win'],
                        'avg_loss': backtest_result['avg_loss'],
                        'profit_factor': backtest_result['profit_factor'],
                        'largest_win': backtest_result['largest_win'],
                        'largest_loss': backtest_result['largest_loss']
                    })
                
            except Exception as e:
                # Skip failed combinations
                continue
        
        if not results:
            return "No successful backtest results found. Check your parameters and data availability."
        
        # Sort by different metrics
        best_net_pips = max(results, key=lambda x: x['net_pips'])
        best_win_rate = max(results, key=lambda x: x['win_rate'])
        best_profit_factor = max(results, key=lambda x: x['profit_factor'] if x['profit_factor'] != float('inf') else 0)
        
        # Export to CSV if requested
        csv_path = None
        winning_trades_csv = None
        
        if params.export_csv:
            import csv
            import os
            
            # Create results directory
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent
            results_dir = str(project_root / "optimization_results") if os.path.exists("/mnt/user-data") else "/Users/paul/Sites/PythonProjects/Trading-MCP/optimization_results"
            os.makedirs(results_dir, exist_ok=True)
            
            # Export optimization results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_path = f"{results_dir}/optimization_{params.symbol}_{timestamp}.csv"
            
            with open(csv_path, 'w', newline='') as csvfile:
                fieldnames = results[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            
            # Export ALL trades for best combination
            best_combo = best_net_pips
            all_trades = await _get_all_trades(
                params.symbol, params.start_date, params.end_date,
                params.timeframe, best_combo['stop_loss'], best_combo['take_profit']
            )
            
            if all_trades:
                winning_trades_csv = f"{results_dir}/all_trades_{params.symbol}_{timestamp}.csv"
                with open(winning_trades_csv, 'w', newline='') as csvfile:
                    fieldnames = ['trade_id', 'date', 'entry_time', 'exit_time', 'signal', 'entry_price', 'exit_price', 'pips', 'vwap', 'result']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(all_trades)
        
        # Format results
        result_text = f"""# VWAP Strategy Optimization Results

**Symbol**: {params.symbol}
**Period**: {params.start_date} to {params.end_date}
**Timeframe**: {params.timeframe}
**Combinations Tested**: {len(results)}
**Data Source**: cTrader API (Real Market Data)

## Best Combinations by Metric

### 🏆 Best Net Pips: SL={best_net_pips['stop_loss']}, TP={best_net_pips['take_profit']}
- **Net Pips**: {best_net_pips['net_pips']:.1f}
- **Win Rate**: {best_net_pips['win_rate']:.1f}%
- **Total Trades**: {best_net_pips['total_trades']}
- **Profit Factor**: {best_net_pips['profit_factor']:.2f}

### 📈 Best Win Rate: SL={best_win_rate['stop_loss']}, TP={best_win_rate['take_profit']}
- **Win Rate**: {best_win_rate['win_rate']:.1f}%
- **Net Pips**: {best_win_rate['net_pips']:.1f}
- **Total Trades**: {best_win_rate['total_trades']}
- **Profit Factor**: {best_win_rate['profit_factor']:.2f}

### ⚡ Best Profit Factor: SL={best_profit_factor['stop_loss']}, TP={best_profit_factor['take_profit']}
- **Profit Factor**: {best_profit_factor['profit_factor']:.2f}
- **Net Pips**: {best_profit_factor['net_pips']:.1f}
- **Win Rate**: {best_profit_factor['win_rate']:.1f}%
- **Total Trades**: {best_profit_factor['total_trades']}

## Top 5 Combinations (by Net Pips)

"""
        
        # Add top 5 results
        top_5 = sorted(results, key=lambda x: x['net_pips'], reverse=True)[:5]
        for i, combo in enumerate(top_5, 1):
            result_text += f"{i}. **SL={combo['stop_loss']}, TP={combo['take_profit']}**: {combo['net_pips']:.1f} pips ({combo['win_rate']:.1f}% win rate, {combo['total_trades']} trades)\n"
        
        if csv_path:
            result_text += f"\n## 📊 Export Files\n\n"
            result_text += f"- **Optimization Results**: `{csv_path}`\n"
            if winning_trades_csv:
                result_text += f"- **All Trades (Best Combo)**: `{winning_trades_csv}`\n"
        
        return result_text
        
    except Exception as e:
        return _handle_error(e)

# Helper function for internal backtest (without formatting)
async def _run_backtest_internal(symbol: str, start_date: str, end_date: str, 
                               timeframe: str, stop_loss_pips: int, take_profit_pips: int):
    '''Internal backtest function that returns raw data.'''
    try:
        # Get historical data
        historical_data = await _fetch_historical_data(symbol, start_date, end_date, timeframe)
        
        if not historical_data:
            return None
        
        # Run strategy analysis (replicating logic from backtest_vwap_strategy)
        # Group by date
        dates_data = {}
        for candle in historical_data:
            date = candle['date']
            if date not in dates_data:
                dates_data[date] = []
            dates_data[date].append(candle)

        trades = []
        
        # Process each trading day
        for date, day_candles in sorted(dates_data.items()):
            if not day_candles:
                continue
            
            # Calculate VWAP for the day
            vwap = _calculate_vwap(day_candles)
            
            # Get price at 8:30 AM (find closest candle to 8:30)
            target_time = DEFAULT_SIGNAL_TIME  # 8:30 AM
            entry_candle = None
            min_time_diff = float('inf')
            
            for candle in day_candles:
                candle_time = datetime.fromtimestamp(candle["timestamp"] / 1000).time()
                # Calculate time difference from 8:30
                candle_minutes = candle_time.hour * 60 + candle_time.minute
                target_minutes = target_time.hour * 60 + target_time.minute
                time_diff = abs(candle_minutes - target_minutes)
                
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    entry_candle = candle
            
            # Use first candle if no good match found (fallback)
            if entry_candle is None:
                entry_candle = day_candles[0]
            
            entry_price = entry_candle['open']
            
            # Generate signal
            signal = _generate_signal(entry_price, vwap)
            
            # Calculate stop loss and take profit
            stop_loss, take_profit = _calculate_stop_and_target(
                entry_price,
                signal,
                stop_loss_pips,
                take_profit_pips
            )
            
            # Create trade
            trade = Trade(
                date=date,
                direction=signal,
                entry_price=entry_price,
                vwap=vwap,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            # Simulate trade exit
            _simulate_trade_exit(trade, day_candles)
            
            # Convert to dict for easier processing
            trade_dict = {
                'date': trade.date,
                'signal': trade.direction.value,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'pips': trade.pips,
                'vwap': trade.vwap
            }
            trades.append(trade_dict)
        
        if not trades:
            return None
        
        # Calculate performance metrics
        wins = [t for t in trades if t['pips'] > 0]
        losses = [t for t in trades if t['pips'] < 0]
        
        total_trades = len(trades)
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        net_pips = sum(t['pips'] for t in trades)
        avg_win = sum(t['pips'] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t['pips'] for t in losses) / len(losses) if losses else 0
        
        largest_win = max((t['pips'] for t in wins), default=0)
        largest_loss = min((t['pips'] for t in losses), default=0)
        
        total_win_pips = sum(t['pips'] for t in wins) if wins else 0
        total_loss_pips = abs(sum(t['pips'] for t in losses)) if losses else 1
        profit_factor = total_win_pips / total_loss_pips if total_loss_pips > 0 else float('inf')
        
        return {
            'total_trades': total_trades,
            'wins': win_count,
            'losses': loss_count,
            'win_rate': win_rate,
            'net_pips': net_pips,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'trades': trades
        }
        
    except Exception:
        return None

# Helper function to get all trades details
async def _get_all_trades(symbol: str, start_date: str, end_date: str, 
                         timeframe: str, stop_loss_pips: int, take_profit_pips: int):
    '''Get detailed trade information for ALL trades for CSV export.'''
    try:
        result = await _run_backtest_internal(symbol, start_date, end_date, timeframe, 
                                            stop_loss_pips, take_profit_pips)
        
        if not result or not result['trades']:
            return []
        
        # Format ALL trades for CSV export
        all_trades = []
        for i, trade in enumerate(result['trades'], 1):
            # Determine result category
            if trade['pips'] > 0:
                result_type = 'WIN'
            elif trade['pips'] < 0:
                result_type = 'LOSS'
            else:
                result_type = 'BREAK_EVEN'
                
            all_trades.append({
                'trade_id': i,
                'date': trade['date'],
                'entry_time': '08:30:00',  # Strategy enters at 8:30 AM
                'exit_time': 'Intraday',  # Consistent with main CSV export
                'signal': trade['signal'],
                'entry_price': round(trade['entry_price'], 5),
                'exit_price': round(trade['exit_price'], 5),
                'pips': round(trade['pips'], 1),
                'vwap': round(trade['vwap'], 5),
                'result': result_type
            })
        
        return all_trades
        
    except Exception:
        return []

# Generic data fetching tool
class DataFetchInput(BaseModel):
    '''Input model for fetching raw market data.'''
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    symbol: str = Field(
        ...,
        description="Trading symbol (e.g., 'GBPUSD', 'EURUSD')"
    )
    days: int = Field(
        default=7,
        description="Number of days to fetch (1-90)",
        ge=1,
        le=90
    )
    timeframe: str = Field(
        default="1d",
        description="Timeframe (e.g., '1m', '5m', '15m', '30m', '1h', '4h', '1d')"
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Response format: 'markdown' or 'json'"
    )

@mcp.tool(
    name="fetch_market_data",
    annotations={
        "title": "Fetch Market Data (cTrader API)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fetch_market_data(params: DataFetchInput) -> str:
    '''
    Fetch raw OHLCV market data directly from cTrader API.
    
    Returns raw OHLCV data without any strategy analysis.
    
    Args:
        params (DataFetchInput): Parameters for data fetching
        
    Returns:
        str: OHLCV data in requested format
    '''
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=params.days)
        
        # Format dates
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Fetch data from cTrader API
        data = await _fetch_historical_data(
            params.symbol, 
            start_str, 
            end_str, 
            params.timeframe
        )
        
        if not data:
            return f"❌ No data found for {params.symbol} from {start_str} to {end_str}"
        
        # Format response
        if params.format == ResponseFormat.JSON:
            return json.dumps({
                "symbol": params.symbol,
                "timeframe": params.timeframe,
                "start_date": start_str,
                "end_date": end_str,
                "data_points": len(data),
                "data": data
            }, indent=2, default=str)
        
        # Markdown format
        result = f"# 📊 Market Data: {params.symbol} (cTrader API)\n\n"
        result += f"**Timeframe:** {params.timeframe}\n"
        result += f"**Period:** {start_str} to {end_str}\n"
        result += f"**Data Points:** {len(data)}\n\n"
        
        result += "## 📈 OHLCV Data\n\n"
        result += "| Date | Open | High | Low | Close | Volume |\n"
        result += "|------|------|------|-----|-------|--------|\n"
        
        for candle in data[-10:]:  # Show last 10 candles
            date_str = candle.get('timestamp', candle.get('date', 'N/A'))
            if isinstance(date_str, datetime):
                date_str = date_str.strftime('%Y-%m-%d %H:%M')
            
            result += f"| {date_str} | {candle.get('open', 'N/A')} | {candle.get('high', 'N/A')} | {candle.get('low', 'N/A')} | {candle.get('close', 'N/A')} | {candle.get('volume', 'N/A')} |\n"
        
        if len(data) > 10:
            result += f"\n*Showing last 10 of {len(data)} data points*\n"
        
        return result
        
    except Exception as e:
        return _handle_error(e)

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
