#!/usr/bin/env python3
'''
MCP Server for cTrader + InfluxDB Data Integration.

This server provides tools to fetch market data from cTrader API with InfluxDB 
for efficient data storage and retrieval. Can be used by any trading strategy.

Data Strategy:
- Uses InfluxDB (/getDataFromDB) for fast historical data retrieval
- Falls back to cTrader API (/getDataByDates) if InfluxDB has no data
- Uses /getLatestCandle for current market signals

Features:
- High-performance data access
- Automatic fallback mechanisms
- Multiple timeframes
- Symbol management
'''

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timedelta, time as dt_time
import json
import httpx
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP
from shared.models import BacktestInput, TradeDirection, TradeResult, ResponseFormat
from shared.utils import (get_config, calculate_pips, format_timestamp,
                         DEFAULT_STOP_LOSS_PIPS, DEFAULT_TAKE_PROFIT_PIPS, 
                         DEFAULT_SIGNAL_TIME, CHARACTER_LIMIT)
from config.settings import CTRADER_API_CONFIG

# Initialize the MCP server
mcp = FastMCP("influxdb_data_connector")

# Set up logging
logger = logging.getLogger(__name__)

# Constants
config = get_config()
API_BASE_URL = config["ctrader_api_url"]
API_USERNAME = config["ctrader_api_username"]
API_PASSWORD = config["ctrader_api_password"]

# Symbol ID mapping (from your API)
SYMBOL_IDS = {
    "EURUSD": 185,
    "GBPUSD": 199,
    "USDJPY": 226,
    "USDCHF": 222,
    "AUDUSD": 158,
    "USDCAD": 221,
    "NZDUSD": 211,
    "EURGBP": 175,
    "EURJPY": 177,
    "EURCHF": 173,
    "EURAUD": 171,
    "EURCAD": 172,
    "EURNZD": 180,
    "GBPJPY": 192,
    "GBPCHF": 191,
    "GBPAUD": 189,
    "GBPCAD": 190,
    "GBPNZD": 195,
    "AUDJPY": 155,
    "AUDNZD": 156,
    "AUDCAD": 153,
    "NZDJPY": 210,
    "CADJPY": 162,
    "CHFJPY": 163,
    "GER40": 200,
    "UK100": 217,
    "US30": 219,
}

# Timeframe mapping
TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

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
    '''Input model for backtesting the VWAP strategy.'''
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    start_date: str = Field(
        ..., 
        description="Start date for backtest in YYYY-MM-DD format (e.g., '2024-09-24')",
        pattern=r'^\d{4}-\d{2}-\d{2}$'
    )
    end_date: str = Field(
        ..., 
        description="End date for backtest in YYYY-MM-DD format (e.g., '2024-10-24')",
        pattern=r'^\d{4}-\d{2}-\d{2}$'
    )
    symbol: str = Field(
        default="EURUSD",
        description="Trading pair symbol (e.g., 'EURUSD', 'GBPUSD', 'GBPAUD')",
        min_length=6,
        max_length=20
    )
    timeframe: str = Field(
        default="30m",
        description="Timeframe for analysis (1m, 5m, 15m, 30m, 1h, 4h, 1d)",
        pattern=r'^(1m|5m|15m|30m|1h|4h|1d)$'
    )
    stop_loss_pips: int = Field(
        default=DEFAULT_STOP_LOSS_PIPS,
        description="Stop loss in pips (default: 10)",
        ge=1,
        le=100
    )
    take_profit_pips: int = Field(
        default=DEFAULT_TAKE_PROFIT_PIPS,
        description="Take profit in pips (default: 15)",
        ge=1,
        le=200
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError(f"Date must be in YYYY-MM-DD format, got: {v}")

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

# Data Provider Functions
async def _check_influxdb_data_availability(
    symbol: str,
    timeframe: str
) -> Dict[str, Any]:
    '''
    Check if data is available in InfluxDB for symbol/timeframe.
    Uses /countDataFromDB endpoint.
    '''
    symbol_id = _get_symbol_id(symbol)
    if not symbol_id:
        return {"available": False, "count": 0}
    
    try:
        data = await _make_api_request(
            "/countDataFromDB",
            params={
                "pair": symbol_id,
                "timeframe": timeframe
            }
        )
        
        return {
            "available": data.get("count", 0) > 0,
            "count": data.get("count", 0),
            "earliest": data.get("earliest"),
            "latest": data.get("latest")
        }
    except Exception:
        return {"available": False, "count": 0}

async def _fetch_from_influxdb(
    symbol: str,
    timeframe: str,
    num_bars: Optional[int] = None
) -> List[Dict[str, Any]]:
    '''
    Fetch historical data from InfluxDB.
    Uses /getDataFromDB endpoint for fast retrieval.
    '''
    symbol_id = _get_symbol_id(symbol)
    if not symbol_id:
        raise ValueError(f"Unknown symbol: {symbol}")
    
    params = {
        "pair": symbol_id,
        "timeframe": timeframe
    }
    
    if num_bars:
        params["n"] = num_bars
    
    data = await _make_api_request("/getDataFromDB", params=params)
    
    # Transform to expected format
    candles = []
    if "data" in data:
        for item in data["data"]:
            dt = datetime.fromtimestamp(item["timestamp"] / 1000)
            candles.append({
                "date": dt.strftime('%Y-%m-%d'),
                "timestamp": item["timestamp"],
                "open": item["open"],
                "high": item["high"],
                "low": item["low"],
                "close": item["close"],
                "volume": item.get("volume", 0)
            })
    
    return candles

async def _fetch_from_ctrader_api(
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str = "30m"
) -> List[Dict[str, Any]]:
    '''
    Fetch historical data from cTrader API with automatic InfluxDB population.
    Uses /getData endpoint which automatically saves data to InfluxDB.
    This ensures future requests can use InfluxDB for faster retrieval.
    '''
    symbol_id = _get_symbol_id(symbol)
    if not symbol_id:
        raise ValueError(f"Unknown symbol: {symbol}")
    
    # Calculate the date range for the /getData endpoint
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    days_diff = (end_dt - start_dt).days + 1
    
    # Use range format for /getData endpoint (e.g., "-7d", "-30d")
    range_str = f"-{days_diff}d"
    
    data = await _make_api_request(
        "/getData",
        params={
            "pair": symbol_id,
            "timeframe": timeframe,
            "range": range_str
        }
    )
    
    # Transform to expected format
    candles = []
    if "data" in data:
        for item in data["data"]:
            dt = datetime.fromtimestamp(item["timestamp"] / 1000)
            candles.append({
                "date": dt.strftime('%Y-%m-%d'),
                "timestamp": item["timestamp"],
                "open": item["open"],
                "high": item["high"],
                "low": item["low"],
                "close": item["close"],
                "volume": item.get("volume", 0)
            })
    
    return candles

async def _fetch_historical_data(
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str = "30m"
) -> tuple[List[Dict[str, Any]], str]:
    '''
    Fetch historical data intelligently with automatic InfluxDB population:
    1. Check if InfluxDB has sufficient data for the requested date range
    2. If yes, use InfluxDB (faster)
    3. If no, use cTrader API (/getData) which automatically populates InfluxDB
    
    Returns: (candles, data_source)
    '''
    # Parse date range for validation
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)
    
    # First, check InfluxDB availability
    influx_info = await _check_influxdb_data_availability(symbol, timeframe)
    
    if influx_info["available"]:
        # Calculate approximate number of bars needed
        days_diff = (end_dt - start_dt).days
        
        # Estimate bars per day based on timeframe
        bars_per_day = {
            "1m": 1440, "5m": 288, "15m": 96, "30m": 48,
            "1h": 24, "4h": 6, "1d": 1
        }
        estimated_bars = days_diff * bars_per_day.get(timeframe, 48)
        
        # Add buffer and limit
        num_bars = min(estimated_bars * 2, 10000)
        
        try:
            candles = await _fetch_from_influxdb(symbol, timeframe, num_bars)
            
            # Filter candles to date range
            filtered = [
                c for c in candles
                if start_ts <= c["timestamp"] <= end_ts
            ]
            
            # Check if we have sufficient data for the date range
            # For indicator-based strategies, we need at least 50 candles for SMA50
            min_required_candles = max(50, estimated_bars // 2)
            
            if len(filtered) >= min_required_candles:
                logger.info(f"InfluxDB has sufficient data: {len(filtered)} candles for {symbol} {timeframe}")
                return filtered, "InfluxDB (fast)"
            else:
                logger.info(f"InfluxDB has insufficient data: {len(filtered)} candles, need {min_required_candles} for {symbol} {timeframe}")
        except Exception as e:
            logger.warning(f"InfluxDB fetch failed for {symbol} {timeframe}: {e}")
    
    # Fallback to cTrader API with automatic InfluxDB population
    logger.info(f"Using cTrader API to fetch and populate InfluxDB for {symbol} {timeframe}")
    candles = await _fetch_from_ctrader_api(symbol, start_date, end_date, timeframe)
    return candles, "cTrader API (auto-populated InfluxDB)"

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
        "bid": latest.get("close", 0),
        "ask": latest.get("close", 0),
        "timestamp": datetime.fromtimestamp(latest.get("timestamp", 0) / 1000).isoformat(),
        "isLive": latest.get("isLive", False),
        "isComplete": latest.get("isComplete", False)
    }

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
    timeframe: str,
    data_source: str
) -> str:
    '''Format backtest results as markdown.'''
    lines = [
        f"# VWAP Strategy Backtest Results",
        f"",
        f"**Symbol**: {symbol}",
        f"**Timeframe**: {timeframe}",
        f"**Period**: {start_date} to {end_date}",
        f"**Strategy**: At 8:30, BUY if price < VWAP, SELL if price > VWAP",
        f"**Data Source**: {data_source}",
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
    timeframe: str,
    data_source: str
) -> str:
    '''Format backtest results as JSON.'''
    result = {
        "symbol": symbol,
        "timeframe": timeframe,
        "start_date": start_date,
        "end_date": end_date,
        "data_source": data_source,
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
        f"**Data Source**: cTrader API + InfluxDB",
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
            return "Error: API authentication failed. Please check CTRADER_API_USERNAME and CTRADER_API_PASSWORD."
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
    name="backtest_vwap_strategy",
    annotations={
        "title": "Backtest VWAP Trading Strategy (cTrader + InfluxDB)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def backtest_vwap_strategy(params: BacktestInput) -> str:
    '''
    Backtest the VWAP trading strategy using cTrader API with InfluxDB optimization.
    
    Data Strategy:
    - Checks InfluxDB first for fast data retrieval (/getDataFromDB)
    - Falls back to cTrader API if InfluxDB has no data (/getDataByDates)
    - Automatically selects the best data source
    
    This tool fetches historical data and simulates the VWAP strategy by:
    1. Fetching historical price data for the specified period
    2. For each trading day, calculating VWAP at market open
    3. At 8:30, generating a signal (BUY if price < VWAP, SELL if price > VWAP)
    4. Simulating trade execution with specified stop loss and take profit
    5. Calculating comprehensive performance statistics
    
    Args:
        params (BacktestInput): Validated input parameters containing:
            - start_date (str): Start date in YYYY-MM-DD format
            - end_date (str): End date in YYYY-MM-DD format
            - symbol (str): Trading pair (EURUSD, GBPUSD, GBPAUD, etc.)
            - timeframe (str): Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d)
            - stop_loss_pips (int): Stop loss in pips (default: 10)
            - take_profit_pips (int): Take profit in pips (default: 15)
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Backtest results with performance statistics, trade history, and data source
    '''
    try:
        # Fetch historical data (automatically uses InfluxDB or cTrader API)
        historical_data, data_source = await _fetch_historical_data(
            params.symbol,
            params.start_date,
            params.end_date,
            params.timeframe
        )
        
        if not historical_data:
            return f"No trading data found for {params.symbol} between {params.start_date} and {params.end_date}"
        
        # Group by date
        dates_data = {}
        for candle in historical_data:
            date = candle['date']
            if date not in dates_data:
                dates_data[date] = []
            dates_data[date].append(candle)
        
        trades: List[Trade] = []
        
        # Process each trading day
        for date, day_candles in sorted(dates_data.items()):
            if not day_candles:
                continue
            
            # Calculate VWAP for the day
            vwap = _calculate_vwap(day_candles)
            
            # Get price at 8:30 (use first candle of the day as approximation)
            entry_price = day_candles[0]['open']
            
            # Generate signal
            signal = _generate_signal(entry_price, vwap)
            
            # Calculate stop loss and take profit
            stop_loss, take_profit = _calculate_stop_and_target(
                entry_price,
                signal,
                params.stop_loss_pips,
                params.take_profit_pips
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
            
            trades.append(trade)
        
        # Calculate statistics
        stats = _calculate_performance_stats(trades)
        
        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            result = _format_backtest_markdown(
                stats, trades, params.symbol, params.start_date, 
                params.end_date, params.timeframe, data_source
            )
        else:
            result = _format_backtest_json(
                stats, trades, params.symbol, params.start_date, 
                params.end_date, params.timeframe, data_source
            )
        
        # Check character limit
        if len(result) > CHARACTER_LIMIT:
            return result[:CHARACTER_LIMIT] + f"\n\n[Output truncated at {CHARACTER_LIMIT} characters]"
        
        return result
        
    except Exception as e:
        return _handle_error(e)

@mcp.tool(
    name="get_current_market_signal",
    annotations={
        "title": "Get Current Market Signal (cTrader Live Data)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def get_current_market_signal(params: CurrentMarketInput) -> str:
    '''
    Get the current VWAP trading signal using live cTrader data.
    
    Uses:
    - /getLatestCandle for current market price
    - InfluxDB or cTrader API for recent VWAP calculation
    
    Args:
        params (CurrentMarketInput): Validated input parameters
    
    Returns:
        str: Current market analysis with live signal
    '''
    try:
        # Fetch current price
        current_price = await _fetch_current_price(params.symbol, params.timeframe)
        
        # Fetch recent data for VWAP calculation (use InfluxDB if available)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        historical_data, _ = await _fetch_historical_data(
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
                "data_source": "cTrader API + InfluxDB"
            }
            return json.dumps(result, indent=2)
        
    except Exception as e:
        return _handle_error(e)

@mcp.tool(
    name="analyze_strategy_performance",
    annotations={
        "title": "Analyze Strategy Performance (cTrader + InfluxDB)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def analyze_strategy_performance(params: StrategyPerformanceInput) -> str:
    '''
    Analyze VWAP strategy performance over recent period using optimized data retrieval.
    
    Convenience tool that automatically backtests the strategy for the
    specified number of recent days using InfluxDB when available.
    
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
        return await backtest_vwap_strategy(backtest_params)
        
    except Exception as e:
        return _handle_error(e)

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
        "title": "Fetch Market Data (InfluxDB + cTrader)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fetch_market_data(params: DataFetchInput) -> str:
    '''
    Fetch raw OHLCV market data from InfluxDB or cTrader API.
    
    Data Strategy:
    - Tries InfluxDB first for fast retrieval (/getDataFromDB)
    - Falls back to cTrader API if needed (/getDataByDates)
    - Returns raw OHLCV data without any strategy analysis
    
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
        
        # Fetch data using the optimized data fetching logic
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
        result = f"# 📊 Market Data: {params.symbol}\n\n"
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
