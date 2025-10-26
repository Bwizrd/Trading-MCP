#!/usr/bin/env python3
'''
MCP Server for VWAP Trading Strategy - Core Implementation.

This server provides tools to backtest and analyze a simple VWAP trading strategy:
- At 8:30, if price is above VWAP, generate SELL signal
- At 8:30, if price is below VWAP, generate BUY signal

The server integrates with your real-time data API and provides backtesting,
performance analysis, and current market condition checking.
'''

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, time as dt_time
from decimal import Decimal
import json
import httpx
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP

# Import shared models and utilities
from shared.models import (
    ResponseFormat, TradeDirection, TradeResult, Candle, Trade, BacktestInput
)
from shared.utils import (
    get_config, calculate_pips, format_timestamp, 
    DEFAULT_STOP_LOSS_PIPS, DEFAULT_TAKE_PROFIT_PIPS, DEFAULT_SIGNAL_TIME, CHARACTER_LIMIT,
    TradingViewVWAP, calculate_vwap_for_strategy, get_vwap_at_time
)
from config.settings import STRATEGY_DEFAULTS, SUPPORTED_SYMBOLS

# Initialize the MCP server
mcp = FastMCP("vwap_strategy_core")

# Additional Models specific to this server
class CurrentMarketInput(BaseModel):
    '''Input model for getting current market conditions.'''
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    symbol: str = Field(
        default="EUR/USD",
        description="Trading pair symbol (e.g., 'EUR/USD', 'GBP/USD')",
        min_length=3,
        max_length=20
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
        default="EUR/USD",
        description="Trading pair symbol",
        min_length=3,
        max_length=20
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )

# Data Provider Functions - Now using cTrader API directly
async def _fetch_historical_data(symbol: str, start_date: str, end_date: str, timeframe: str = "1m") -> List[Dict[str, Any]]:
    '''
    Fetch historical price data from cTrader API.
    
    FIXED: Now fetches real data from cTrader API instead of mock data.
    '''
    # Map symbol format
    symbol_map = {
        "EUR/USD": "EURUSD",
        "EURUSD": "EURUSD", 
        "GBP/USD": "GBPUSD",
        "GBPUSD": "GBPUSD"
    }
    
    ctrader_symbol = symbol_map.get(symbol, symbol.replace("/", ""))
    
    # Get symbol ID from cTrader API
    symbol_ids = {
        "EURUSD": 185,
        "GBPUSD": 199,
        "USDJPY": 226,
        "AUDUSD": 158,
        "USDCAD": 221,
        "USDCHF": 222,
        "NZDUSD": 211
    }
    
    symbol_id = symbol_ids.get(ctrader_symbol)
    if not symbol_id:
        raise ValueError(f"Unsupported symbol: {symbol}. Available: {list(symbol_ids.keys())}")
    
    # Format dates for cTrader API
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    start_iso = start_dt.strftime('%Y-%m-%dT00:00:00.000Z')
    end_iso = end_dt.strftime('%Y-%m-%dT23:59:59.000Z')
    
    # Call cTrader API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://127.0.0.1:8000/getDataByDates",
            params={
                "pair": symbol_id,
                "timeframe": timeframe, 
                "startDate": start_iso,
                "endDate": end_iso
            },
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
    
    # Transform cTrader API response to expected format
    candles = []
    if "data" in data and data["data"]:
        for item in data["data"]:
            dt = datetime.fromtimestamp(item["timestamp"] / 1000)
            candles.append({
                "date": dt.strftime('%Y-%m-%d'),
                "datetime": dt,
                "timestamp": item["timestamp"],
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
                "volume": int(item.get("volume", 0))
            })
    
    return candles

async def _fetch_current_price(symbol: str) -> Dict[str, Any]:
    '''
    Fetch current market price from your API.
    
    This is a MOCK function. Replace with your actual API endpoint.
    '''
    # TODO: Replace with your actual API
    # async with httpx.AsyncClient() as client:
    #     response = await client.get(f"YOUR_API_URL/quote/{symbol}")
    #     response.raise_for_status()
    #     return response.json()
    
    # Mock current price
    return {
        "symbol": symbol,
        "bid": 1.0845,
        "ask": 1.0847,
        "timestamp": datetime.now().isoformat()
    }

# Strategy Logic Functions
def _calculate_vwap_tradingview(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    '''
    Calculate VWAP using TradingView's exact method.
    Returns candles with VWAP values added.
    '''
    if not candles:
        return []
    
    # Use TradingView-compatible VWAP calculation
    if TradingViewVWAP is not None:
        return calculate_vwap_for_strategy(candles)
    else:
        # Fallback to simple calculation if TradingView module not available
        return _calculate_vwap_simple(candles)

def _calculate_vwap_simple(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    '''Fallback VWAP calculation for compatibility.'''
    result = []
    cumulative_pv = 0.0
    cumulative_volume = 0.0
    
    for candle in candles:
        # Use HL2 like TradingView
        hl2 = (candle['high'] + candle['low']) / 2.0
        volume = candle['volume']
        
        cumulative_pv += hl2 * volume
        cumulative_volume += volume
        
        vwap = cumulative_pv / cumulative_volume if cumulative_volume > 0 else hl2
        
        enhanced_candle = candle.copy()
        enhanced_candle['vwap'] = round(vwap, 5)
        result.append(enhanced_candle)
    
    return result

def _get_vwap_at_signal_time(candles_with_vwap: List[Dict[str, Any]], signal_time: dt_time = DEFAULT_SIGNAL_TIME) -> float:
    '''Get VWAP value at signal time (e.g., 8:30 AM).'''
    if get_vwap_at_time is not None:
        vwap = get_vwap_at_time(candles_with_vwap, signal_time)
        if vwap is not None:
            return vwap
    
    # Fallback: return VWAP from first available candle at or after signal time
    for candle in candles_with_vwap:
        if 'vwap' in candle:
            return candle['vwap']
    
    return 0.0

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
    '''
    Simulate trade exit based on intraday price action.
    Checks if stop loss or take profit was hit during the day.
    '''
    for candle in day_candles:
        high = candle['high']
        low = candle['low']
        
        if trade.direction == TradeDirection.BUY:
            # Check stop loss
            if low <= trade.stop_loss:
                trade.close(trade.stop_loss, pip_size)
                return
            # Check take profit
            if high >= trade.take_profit:
                trade.close(trade.take_profit, pip_size)
                return
        else:  # SELL
            # Check stop loss
            if high >= trade.stop_loss:
                trade.close(trade.stop_loss, pip_size)
                return
            # Check take profit
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
    end_date: str
) -> str:
    '''Format backtest results as markdown.'''
    lines = [
        f"# VWAP Strategy Backtest Results",
        f"",
        f"**Symbol**: {symbol}",
        f"**Period**: {start_date} to {end_date}",
        f"**Strategy**: At 8:30, BUY if price < VWAP, SELL if price > VWAP",
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
    
    # Add trade details (limit to avoid excessive output)
    displayed_trades = trades[:50]  # Show first 50 trades
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
    end_date: str
) -> str:
    '''Format backtest results as JSON.'''
    result = {
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "performance": stats,
        "trades": [t.to_dict() for t in trades]
    }
    return json.dumps(result, indent=2)

def _format_current_market_markdown(
    symbol: str,
    current_price: Dict[str, Any],
    vwap: float,
    signal: TradeDirection
) -> str:
    '''Format current market conditions as markdown.'''
    mid_price = (current_price['bid'] + current_price['ask']) / 2
    spread_pips = (current_price['ask'] - current_price['bid']) / 0.0001
    
    signal_emoji = "🔴" if signal == TradeDirection.SELL else "🟢"
    
    lines = [
        f"# Current Market Analysis - {symbol}",
        f"",
        f"**Current Price**: {mid_price:.5f}",
        f"**Bid**: {current_price['bid']:.5f} | **Ask**: {current_price['ask']:.5f}",
        f"**Spread**: {spread_pips:.1f} pips",
        f"**VWAP**: {vwap:.5f}",
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
            return "Error: API authentication failed. Please check your API credentials."
        elif e.response.status_code == 429:
            return "Error: Rate limit exceeded. Please wait before making more requests."
        return f"Error: API request failed with status {e.response.status_code}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    elif isinstance(e, ValueError):
        return f"Error: Invalid input - {str(e)}"
    return f"Error: {type(e).__name__}: {str(e)}"

# MCP Tools
@mcp.tool(
    name="backtest_vwap_strategy",
    annotations={
        "title": "Backtest VWAP Trading Strategy",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def backtest_vwap_strategy(params: BacktestInput) -> str:
    '''
    Backtest the VWAP trading strategy over a specified date range.
    
    This tool simulates the VWAP strategy by:
    1. Fetching historical price data for the specified period
    2. For each trading day, calculating VWAP at market open
    3. At 8:30, generating a signal (BUY if price < VWAP, SELL if price > VWAP)
    4. Simulating trade execution with specified stop loss and take profit
    5. Calculating comprehensive performance statistics
    
    Args:
        params (BacktestInput): Validated input parameters containing:
            - start_date (str): Start date in YYYY-MM-DD format (e.g., "2024-09-24")
            - end_date (str): End date in YYYY-MM-DD format (e.g., "2024-10-24")
            - symbol (str): Trading pair (default: "EUR/USD")
            - stop_loss_pips (int): Stop loss in pips (default: 10, range: 1-100)
            - take_profit_pips (int): Take profit in pips (default: 15, range: 1-200)
            - response_format (ResponseFormat): Output format ("markdown" or "json")
    
    Returns:
        str: Backtest results containing:
            - Performance summary (win rate, total pips, avg win/loss, profit factor)
            - Complete trade history with entry/exit prices and results
            - Statistical analysis of the strategy performance
        
        Markdown format includes emoji indicators and human-readable formatting.
        JSON format provides structured data for programmatic analysis.
    
    Examples:
        - Test last 30 days: params with start_date="2024-09-24", end_date="2024-10-24"
        - Test with custom stops: params with stop_loss_pips=20, take_profit_pips=30
        - Different symbol: params with symbol="GBP/USD"
    
    Error Handling:
        - Returns error if date format is invalid
        - Returns error if API connection fails
        - Returns error if no data available for the period
        - Handles weekends and holidays automatically
    '''
    try:
        # FIXED: Fetch 1-minute data for precise entry timing
        historical_data = await _fetch_historical_data(
            params.symbol,
            params.start_date,
            params.end_date,
            timeframe="1m"  # Use 1-minute data for accurate 8:30 AM entries
        )
        
        if not historical_data:
            return f"No trading data found for {params.symbol} between {params.start_date} and {params.end_date}"
        
        # Group candles by date
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
            
            # Calculate VWAP for the day using TradingView method
            candles_with_vwap = _calculate_vwap_tradingview(day_candles)
            
            # CRITICAL FIX: Find the correct 8:30 AM UTC candle first, then get its VWAP
            target_utc_hour = 8  # 8:30 AM UTC matches platform's 8:30 AM UK data
            target_minute = 30
            entry_candle = None
            
            for candle in candles_with_vwap:  # Use VWAP-enhanced candles
                candle_dt = candle['datetime']
                
                # Look for 8:30 AM UTC (matches cTrader platform 8:30 AM UK data)
                if candle_dt.hour == target_utc_hour and candle_dt.minute == target_minute:
                    entry_candle = candle
                    break
            
            # Fallback: if no exact match, find closest to 8:30 AM UTC
            if entry_candle is None:
                min_time_diff = float('inf')
                for candle in day_candles:
                    candle_dt = candle['datetime']
                    candle_minutes = candle_dt.hour * 60 + candle_dt.minute
                    target_minutes = target_utc_hour * 60 + target_minute
                    time_diff = abs(candle_minutes - target_minutes)
                    
                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        entry_candle = candle
            
            # Final fallback: use first candle
            if entry_candle is None:
                entry_candle = day_candles[0]
            
            # Use the candle's open price as entry (when trade would be placed)
            entry_price = entry_candle['open']
            
            # CRITICAL FIX: Get VWAP from the same candle (at 8:30 AM time)
            vwap = entry_candle.get('vwap', 0)
            
            print(f"DEBUG: {date} - 8:30 AM entry: {entry_price:.5f}, VWAP: {vwap:.5f}, Candle time: {entry_candle['datetime'].strftime('%H:%M:%S')}")
            
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
            
            # Simulate trade exit using intraday candles
            _simulate_trade_exit(trade, day_candles)
            
            trades.append(trade)
        
        # Calculate statistics
        stats = _calculate_performance_stats(trades)
        
        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            result = _format_backtest_markdown(
                stats, trades, params.symbol, params.start_date, params.end_date
            )
        else:
            result = _format_backtest_json(
                stats, trades, params.symbol, params.start_date, params.end_date
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
        "title": "Get Current Market Signal",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def get_current_market_signal(params: CurrentMarketInput) -> str:
    '''
    Get the current VWAP trading signal for a symbol.
    
    This tool fetches current market data and calculates whether the strategy
    would generate a BUY or SELL signal right now based on current price vs VWAP.
    
    Args:
        params (CurrentMarketInput): Validated input parameters containing:
            - symbol (str): Trading pair (default: "EUR/USD")
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Current market analysis including:
            - Current bid/ask prices and spread
            - Current VWAP value
            - Trading signal (BUY or SELL) with reasoning
            - Market conditions assessment
    
    Examples:
        - Check EUR/USD: params with symbol="EUR/USD"
        - Check indices: params with symbol="US30"
    
    Error Handling:
        - Returns error if symbol not found
        - Returns error if API connection fails
        - Returns error if VWAP cannot be calculated
    '''
    try:
        # Fetch current price
        current_price = await _fetch_current_price(params.symbol)
        
        # Fetch today's data for VWAP calculation
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        historical_data = await _fetch_historical_data(params.symbol, yesterday, today)
        
        if not historical_data:
            return f"Unable to calculate VWAP for {params.symbol}. No recent data available."
        
        # Calculate VWAP using TradingView method
        candles_with_vwap = _calculate_vwap_tradingview(historical_data)
        vwap = _get_vwap_at_signal_time(candles_with_vwap)
        
        # Calculate mid price
        mid_price = (current_price['bid'] + current_price['ask']) / 2
        
        # Generate signal
        signal = _generate_signal(mid_price, vwap)
        
        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            return _format_current_market_markdown(params.symbol, current_price, vwap, signal)
        else:
            result = {
                "symbol": params.symbol,
                "current_price": {
                    "bid": current_price['bid'],
                    "ask": current_price['ask'],
                    "mid": round(mid_price, 5)
                },
                "vwap": round(vwap, 5),
                "signal": signal.value,
                "timestamp": current_price['timestamp']
            }
            return json.dumps(result, indent=2)
        
    except Exception as e:
        return _handle_error(e)

@mcp.tool(
    name="analyze_strategy_performance",
    annotations={
        "title": "Analyze Strategy Performance",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def analyze_strategy_performance(params: StrategyPerformanceInput) -> str:
    '''
    Analyze the VWAP strategy performance over a recent period.
    
    This is a convenience tool that automatically backtests the strategy
    for the specified number of recent days and provides a quick performance summary.
    
    Args:
        params (StrategyPerformanceInput): Validated input parameters containing:
            - days (int): Number of recent days to analyze (1-365, default: 30)
            - symbol (str): Trading pair (default: "EUR/USD")
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Performance analysis including win rate, total pips, and trade statistics
    
    Examples:
        - Last week: params with days=7
        - Last quarter: params with days=90
        - Different symbol: params with symbol="GBP/USD", days=30
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
            response_format=params.response_format
        )
        
        # Run backtest
        return await backtest_vwap_strategy(backtest_params)
        
    except Exception as e:
        return _handle_error(e)

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
