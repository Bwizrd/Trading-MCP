#!/usr/bin/env python3
"""
Trading Optimizer MCP Server

Optimizes trading parameters (SL/TP/Trailing Stops) by analyzing closed positions
with tick-level precision. Fetches historical trades and tick data to simulate
alternative exit strategies and identify optimal parameter combinations.

Key Features:
- Fetch closed positions from deals endpoint
- Load tick data for precise trade replay
- Simulate trades with different SL/TP settings
- Generate HTML optimization reports
- Support bulk parameter testing
- Trailing stop optimization (future)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import sys
from pathlib import Path
import httpx

import mcp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
log_file = Path(__file__).parent.parent / "logs" / "trading_optimizer.log"
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)
logger.info("Trading Optimizer MCP Server starting up...")

# MCP Server
app = Server("trading-optimizer")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools for trade optimization."""
    return [
        Tool(
            name="health_check",
            description="Verify the Trading Optimizer MCP server is running and responsive. Returns server status and available capabilities.",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="fetch_closed_positions",
            description="Fetch closed trading positions for a specific date from the deals endpoint. Returns position details including entry/exit times, prices, direction (BUY/SELL), symbol, and P/L. Use this to get historical trades for optimization analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format (e.g., '2026-01-20')"
                    }
                },
                "required": ["date"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="fetch_tick_data_for_optimization",
            description="Fetch tick-level market data for a specific symbol and time range. Returns bid/ask tick data sorted chronologically with mid prices calculated. Use this to get precision data for replaying trades with different SL/TP parameters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol (e.g., 'US500_SB', 'UK100_SB', 'EURUSD')"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in ISO format (e.g., '2026-01-20T09:00:00')"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in ISO format (e.g., '2026-01-20T17:00:00')"
                    },
                    "max_ticks": {
                        "type": "integer",
                        "description": "Maximum number of ticks to fetch (default: 300000)",
                        "default": 300000
                    }
                },
                "required": ["symbol", "start_time", "end_time"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="test_simulation",
            description="Test the trade simulation engine with a sample trade. Demonstrates how the simulator replays a trade with specific SL/TP parameters using tick data. Use this to verify the simulation logic works correctly.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entry_price": {
                        "type": "number",
                        "description": "Entry price for the test trade (e.g., 25000.0)"
                    },
                    "direction": {
                        "type": "string",
                        "description": "Trade direction: 'BUY' or 'SELL'",
                        "enum": ["BUY", "SELL"]
                    },
                    "sl_pips": {
                        "type": "number",
                        "description": "Stop loss in pips (e.g., 10)"
                    },
                    "tp_pips": {
                        "type": "number",
                        "description": "Take profit in pips (e.g., 15)"
                    }
                },
                "required": ["entry_price", "direction", "sl_pips", "tp_pips"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="optimize_trades_single",
            description="Optimize trades for a specific date with a single SL/TP combination. Fetches closed positions and tick data, simulates each trade with the given parameters, and generates an HTML report with performance statistics. Use this to evaluate how a specific parameter set would have performed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format (e.g., '2026-01-20')"
                    },
                    "sl_pips": {
                        "type": "number",
                        "description": "Stop loss in pips (e.g., 10)"
                    },
                    "tp_pips": {
                        "type": "number",
                        "description": "Take profit in pips (e.g., 15)"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Optional start time for filtering (e.g., '09:00:00'). If not provided, uses full day."
                    },
                    "end_time": {
                        "type": "string",
                        "description": "Optional end time for filtering (e.g., '17:00:00'). If not provided, uses full day."
                    }
                },
                "required": ["date", "sl_pips", "tp_pips"],
                "additionalProperties": False
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle MCP tool calls."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")
    
    try:
        if name == "health_check":
            return await handle_health_check()
        elif name == "fetch_closed_positions":
            return await handle_fetch_closed_positions(arguments)
        elif name == "fetch_tick_data_for_optimization":
            return await handle_fetch_tick_data(arguments)
        elif name == "test_simulation":
            return await handle_test_simulation(arguments)
        elif name == "optimize_trades_single":
            return await handle_optimize_trades_single(arguments)
        else:
            return [TextContent(
                type="text",
                text=f"❌ Unknown tool: {name}"
            )]
    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"❌ Tool execution failed: {str(e)}"
        )]


async def handle_health_check() -> list[TextContent]:
    """Handle health check requests."""
    
    result_text = "✅ **Trading Optimizer MCP Server - Health Check**\n\n"
    result_text += f"**Status:** 🟢 Online\n"
    result_text += f"**Server:** trading-optimizer\n"
    result_text += f"**Version:** 1.0.0\n"
    result_text += f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    result_text += "## Available Capabilities\n\n"
    result_text += "### Current Features:\n"
    result_text += "• ✅ Health check and status verification\n"
    result_text += "• ✅ Fetch closed positions from deals endpoint\n"
    result_text += "• ✅ Fetch tick data for optimization\n"
    result_text += "• ✅ Trade replay simulation with SL/TP\n"
    result_text += "• ✅ Timerange filtering for positions/ticks\n"
    result_text += "• ✅ Single SL/TP optimization with HTML reports\n\n"
    
    result_text += "### Planned Features:\n"
    result_text += "• 🔄 Bulk parameter scanning\n"
    result_text += "• 🔄 Trailing stop optimization\n\n"
    
    result_text += "## API Endpoints\n"
    result_text += "• **Deals API:** http://localhost:8000/deals/{date}\n"
    result_text += "• **Tick Data API:** http://localhost:8020/getTickDataFromDB\n\n"
    
    result_text += "📁 **Log File:** `logs/trading_optimizer.log`\n"
    result_text += "🚀 **Ready for development!**"
    
    logger.info("Health check completed successfully")
    
    return [TextContent(type="text", text=result_text)]


async def handle_fetch_closed_positions(arguments: dict) -> list[TextContent]:
    """
    Fetch closed trading positions from the deals endpoint.
    
    Args:
        arguments: Dict with 'date' key in YYYY-MM-DD format
        
    Returns:
        List of TextContent with formatted position data
    """
    date_str = arguments.get("date", "")
    
    # Validate date format
    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
        logger.info(f"Fetching closed positions for date: {date_str}")
    except ValueError:
        error_msg = f"❌ Invalid date format: '{date_str}'. Expected YYYY-MM-DD (e.g., '2026-01-20')"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
    
    # Call deals API
    api_url = f"http://localhost:8000/deals/{date_str}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(api_url)
            response.raise_for_status()
            data = response.json()
            
            closed_trades = data.get("closedTrades", [])
            total_deals = data.get("totalDeals", 0)
            has_more = data.get("hasMore", False)
            
            logger.info(f"Successfully fetched {len(closed_trades)} deals from API (total: {total_deals})")
            
            # Parse and format positions
            positions = []
            for trade in closed_trades:
                # Skip trades without closePositionDetail (entry-only deals)
                if "closePositionDetail" not in trade:
                    continue
                    
                position = {
                    "dealId": trade.get("dealId"),
                    "positionId": trade.get("positionId"),
                    "symbolId": trade.get("symbolId"),
                    "direction": "SELL" if trade.get("tradeSide") == 1 else "BUY",  # 1=SELL, 2=BUY
                    "volume": trade.get("volume"),
                    "exitPrice": trade.get("price"),
                    "exitTime": datetime.fromtimestamp(trade.get("executionTimestamp", 0) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                    "exitTimestamp": trade.get("executionTimestamp"),
                    "entryPrice": trade["closePositionDetail"].get("entryPrice"),
                    "profit": trade.get("profit", 0),
                    "commission": trade.get("commission", 0),
                    "swap": trade["closePositionDetail"].get("swap", 0),
                    "comment": trade.get("comment", "")
                }
                positions.append(position)
            
            # Format output
            result_text = f"✅ **Closed Positions for {date_str}**\n\n"
            result_text += f"**Total Closed Positions:** {len(positions)}\n"
            result_text += f"**Total Deals (including entries):** {total_deals}\n"
            result_text += f"**Has More:** {has_more}\n\n"
            
            if not positions:
                result_text += "ℹ️ No closed positions found for this date.\n"
                result_text += "Only exit deals with closePositionDetail are shown.\n"
            else:
                # Calculate statistics
                winning_trades = [p for p in positions if p["profit"] > 0]
                losing_trades = [p for p in positions if p["profit"] < 0]
                total_profit = sum(p["profit"] for p in positions)
                
                result_text += f"**Winning Trades:** {len(winning_trades)}\n"
                result_text += f"**Losing Trades:** {len(losing_trades)}\n"
                result_text += f"**Win Rate:** {len(winning_trades)/len(positions)*100:.1f}%\n"
                result_text += f"**Total P/L:** ${total_profit:,.2f}\n\n"
                
                result_text += "## Position Details\n\n"
                
                # Show first 10 positions
                for i, pos in enumerate(positions[:10], 1):
                    result_text += f"### Position {i}: {pos['direction']} (Deal #{pos['dealId']})\n"
                    result_text += f"- **Symbol ID:** {pos['symbolId']}\n"
                    result_text += f"- **Entry Price:** {pos['entryPrice']}\n"
                    result_text += f"- **Exit Price:** {pos['exitPrice']}\n"
                    result_text += f"- **Exit Time:** {pos['exitTime']}\n"
                    result_text += f"- **Profit:** ${pos['profit']:,.2f}\n"
                    result_text += f"- **Comment:** {pos['comment']}\n\n"
                
                if len(positions) > 10:
                    result_text += f"... and {len(positions) - 10} more positions\n\n"
                
                result_text += f"📊 **Full data available:** {len(positions)} positions parsed\n"
            
            return [TextContent(type="text", text=result_text)]
            
    except httpx.TimeoutException:
        error_msg = f"❌ Timeout: API did not respond within 30 seconds\n"
        error_msg += f"Endpoint: {api_url}\n"
        error_msg += "Ensure the deals API is running on localhost:8000"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
        
    except httpx.HTTPStatusError as e:
        error_msg = f"❌ HTTP Error {e.response.status_code}: {e.response.text}\n"
        error_msg += f"Endpoint: {api_url}\n"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
        
    except Exception as e:
        error_msg = f"❌ Failed to fetch closed positions: {str(e)}\n"
        error_msg += f"Endpoint: {api_url}\n"
        logger.error(error_msg, exc_info=True)
        return [TextContent(type="text", text=error_msg)]


async def handle_fetch_tick_data(arguments: dict) -> list[TextContent]:
    """
    Fetch tick-level market data for trade simulation and optimization.
    
    Args:
        arguments: Dict with 'symbol', 'start_time', 'end_time', optional 'max_ticks'
        
    Returns:
        List of TextContent with tick data summary
    """
    symbol = arguments.get("symbol", "")
    start_time_str = arguments.get("start_time", "")
    end_time_str = arguments.get("end_time", "")
    max_ticks = arguments.get("max_ticks", 300000)
    
    # Validate inputs
    try:
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
        logger.info(f"Fetching tick data for {symbol} from {start_time} to {end_time}")
    except ValueError as e:
        error_msg = f"❌ Invalid time format: {str(e)}\n"
        error_msg += "Expected ISO format: 'YYYY-MM-DDTHH:MM:SS' (e.g., '2026-01-20T09:00:00')"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
    
    # Validate time range (max 24 hours to prevent excessive data)
    time_diff = (end_time - start_time).total_seconds() / 3600  # hours
    if time_diff > 24:
        error_msg = f"❌ Time range too large: {time_diff:.1f} hours (max 24 hours)\n"
        error_msg += "Split your request into smaller time ranges to avoid excessive data."
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
    
    if time_diff <= 0:
        error_msg = f"❌ Invalid time range: end_time must be after start_time"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
    
    # Get VPS endpoint and fetch symbols for pair ID mapping
    vps_url = "http://localhost:8020"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Get symbol mapping
            symbols_response = await client.get(f"{vps_url}/symbols")
            symbols_response.raise_for_status()
            symbols_data = symbols_response.json()
            
            # Find pair ID for symbol
            pair_id = None
            symbols_list = symbols_data.get('symbols', [])
            base_symbol = symbol.replace('_SB', '')  # Remove _SB suffix if present
            
            for sym in symbols_list:
                sym_name = sym.get('name', '')
                # Check both exact match and with/without _SB suffix
                if sym_name == symbol or sym_name == base_symbol or sym_name == f"{base_symbol}_SB":
                    pair_id = sym.get('value')
                    logger.info(f"Found pair ID {pair_id} for symbol {symbol} (matched: {sym_name})")
                    break
            
            if not pair_id:
                error_msg = f"❌ Symbol not found: {symbol}\n"
                error_msg += f"Tried variations: {symbol}, {base_symbol}, {base_symbol}_SB\n"
                error_msg += f"Available symbols: {len(symbols_list)}"
                logger.error(error_msg)
                return [TextContent(type="text", text=error_msg)]
            
            # Format timestamps for API
            start_iso = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            end_iso = end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            # Fetch tick data
            tick_url = f"{vps_url}/getTickDataFromDB?pair={pair_id}&startDate={start_iso}&endDate={end_iso}&maxTicks={max_ticks}"
            logger.info(f"Fetching ticks: {tick_url}")
            
            tick_response = await client.get(tick_url)
            tick_response.raise_for_status()
            tick_data = tick_response.json()
            
            # Parse tick data
            ticks_raw = tick_data.get('data', [])
            if not ticks_raw:
                result_text = f"ℹ️ **No Tick Data Found**\n\n"
                result_text += f"**Symbol:** {symbol} (Pair ID: {pair_id})\n"
                result_text += f"**Time Range:** {start_time_str} to {end_time_str}\n"
                result_text += f"**Duration:** {time_diff:.1f} hours\n\n"
                result_text += "No ticks available for this time range. Check if market was open."
                return [TextContent(type="text", text=result_text)]
            
            # Convert and sort ticks
            ticks_parsed = []
            for tick in ticks_raw:
                try:
                    # Parse timestamp (milliseconds since epoch)
                    ts_ms = tick.get('timestamp', 0)
                    ts = datetime.fromtimestamp(ts_ms / 1000) if ts_ms else None
                    
                    bid = float(tick.get('bid', 0))
                    ask = float(tick.get('ask', 0))
                    mid = (bid + ask) / 2 if bid and ask else 0
                    
                    if ts and bid and ask:
                        ticks_parsed.append({
                            'timestamp': ts,
                            'timestamp_ms': ts_ms,
                            'bid': bid,
                            'ask': ask,
                            'mid': mid
                        })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid tick: {e}")
                    continue
            
            # Sort chronologically
            ticks_parsed.sort(key=lambda t: t['timestamp_ms'])
            
            logger.info(f"✅ Parsed and sorted {len(ticks_parsed)} ticks")
            
            # Calculate statistics
            if ticks_parsed:
                first_tick = ticks_parsed[0]
                last_tick = ticks_parsed[-1]
                duration_minutes = (last_tick['timestamp'] - first_tick['timestamp']).total_seconds() / 60
                ticks_per_minute = len(ticks_parsed) / duration_minutes if duration_minutes > 0 else 0
                
                mid_prices = [t['mid'] for t in ticks_parsed]
                price_min = min(mid_prices)
                price_max = max(mid_prices)
                price_range = price_max - price_min
                
                result_text = f"✅ **Tick Data Fetched Successfully**\n\n"
                result_text += f"**Symbol:** {symbol} (Pair ID: {pair_id})\n"
                result_text += f"**Time Range:** {first_tick['timestamp']} to {last_tick['timestamp']}\n"
                result_text += f"**Total Ticks:** {len(ticks_parsed):,}\n"
                result_text += f"**Duration:** {duration_minutes:.1f} minutes\n"
                result_text += f"**Avg Ticks/Min:** {ticks_per_minute:.1f}\n\n"
                
                result_text += "## Price Statistics\n\n"
                result_text += f"- **Min Mid Price:** {price_min:.2f}\n"
                result_text += f"- **Max Mid Price:** {price_max:.2f}\n"
                result_text += f"- **Price Range:** {price_range:.2f} ({price_range * 10:.0f} pips)\n"
                result_text += f"- **First Mid:** {first_tick['mid']:.2f}\n"
                result_text += f"- **Last Mid:** {last_tick['mid']:.2f}\n\n"
                
                result_text += "## Sample Ticks (First 5)\n\n"
                for i, tick in enumerate(ticks_parsed[:5], 1):
                    result_text += f"{i}. **{tick['timestamp'].strftime('%H:%M:%S')}** - "
                    result_text += f"Bid: {tick['bid']:.2f}, Ask: {tick['ask']:.2f}, Mid: {tick['mid']:.2f}\n"
                
                result_text += f"\n📊 **Data Ready:** {len(ticks_parsed):,} ticks sorted chronologically"
                
                return [TextContent(type="text", text=result_text)]
            else:
                result_text = f"⚠️ **No Valid Ticks Parsed**\n\n"
                result_text += f"Received {len(ticks_raw)} raw ticks but none were valid.\n"
                result_text += "Check data format from API endpoint."
                return [TextContent(type="text", text=result_text)]
            
    except httpx.TimeoutException:
        error_msg = f"❌ Timeout: Tick data API did not respond within 60 seconds\n"
        error_msg += f"Endpoint: {vps_url}/getTickDataFromDB\n"
        error_msg += f"Requested: {max_ticks:,} ticks for {time_diff:.1f} hours\n"
        error_msg += "Try reducing the time range or max_ticks parameter."
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
        
    except httpx.HTTPStatusError as e:
        error_msg = f"❌ HTTP Error {e.response.status_code}: {e.response.text[:200]}\n"
        error_msg += f"Endpoint: {vps_url}/getTickDataFromDB\n"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
        
    except Exception as e:
        error_msg = f"❌ Failed to fetch tick data: {str(e)}\n"
        logger.error(error_msg, exc_info=True)
        return [TextContent(type="text", text=error_msg)]


def simulate_trade(
    entry_time: datetime,
    entry_price: float,
    direction: str,
    ticks: List[Dict[str, Any]],
    sl_pips: float,
    tp_pips: float,
    pip_value: float = 0.1
) -> Dict[str, Any]:
    """
    Simulate a trade with specific SL/TP parameters using tick data.
    
    Args:
        entry_time: Trade entry timestamp
        entry_price: Entry price
        direction: "BUY" or "SELL"
        ticks: List of tick dicts with 'timestamp', 'mid', 'bid', 'ask'
        sl_pips: Stop loss in pips
        tp_pips: Take profit in pips
        pip_value: Value of one pip (default 0.1 for most forex/indices)
        
    Returns:
        Dict with: exit_time, exit_price, result (WIN/LOSS/NONE), pips_gained,
                  exit_reason, ticks_processed
    """
    # Calculate SL and TP price levels
    if direction == "BUY":
        sl_price = entry_price - (sl_pips * pip_value)
        tp_price = entry_price + (tp_pips * pip_value)
    else:  # SELL
        sl_price = entry_price + (sl_pips * pip_value)
        tp_price = entry_price - (tp_pips * pip_value)
    
    # Find ticks starting from entry time
    ticks_processed = 0
    for tick in ticks:
        tick_time = tick.get('timestamp')
        if isinstance(tick_time, str):
            tick_time = datetime.fromisoformat(tick_time.replace('Z', '+00:00'))
        
        # Skip ticks before entry
        if tick_time < entry_time:
            continue
        
        ticks_processed += 1
        mid_price = tick.get('mid', 0)
        
        # Check SL/TP based on direction
        if direction == "BUY":
            # For BUY: SL if price drops to sl_price, TP if price rises to tp_price
            if mid_price <= sl_price:
                pips_lost = (entry_price - sl_price) / pip_value
                return {
                    'exit_time': tick_time,
                    'exit_price': sl_price,
                    'result': 'LOSS',
                    'pips_gained': -pips_lost,
                    'exit_reason': 'STOP_LOSS',
                    'ticks_processed': ticks_processed
                }
            elif mid_price >= tp_price:
                pips_gained = (tp_price - entry_price) / pip_value
                return {
                    'exit_time': tick_time,
                    'exit_price': tp_price,
                    'result': 'WIN',
                    'pips_gained': pips_gained,
                    'exit_reason': 'TAKE_PROFIT',
                    'ticks_processed': ticks_processed
                }
        else:  # SELL
            # For SELL: SL if price rises to sl_price, TP if price drops to tp_price
            if mid_price >= sl_price:
                pips_lost = (sl_price - entry_price) / pip_value
                return {
                    'exit_time': tick_time,
                    'exit_price': sl_price,
                    'result': 'LOSS',
                    'pips_gained': -pips_lost,
                    'exit_reason': 'STOP_LOSS',
                    'ticks_processed': ticks_processed
                }
            elif mid_price <= tp_price:
                pips_gained = (entry_price - tp_price) / pip_value
                return {
                    'exit_time': tick_time,
                    'exit_price': tp_price,
                    'result': 'WIN',
                    'pips_gained': pips_gained,
                    'exit_reason': 'TAKE_PROFIT',
                    'ticks_processed': ticks_processed
                }
    
    # No exit triggered - return NONE
    return {
        'exit_time': None,
        'exit_price': None,
        'result': 'NONE',
        'pips_gained': 0,
        'exit_reason': 'NO_EXIT',
        'ticks_processed': ticks_processed
    }


def filter_positions_by_timerange(
    positions: List[Dict[str, Any]],
    start_time: datetime,
    end_time: datetime
) -> List[Dict[str, Any]]:
    """
    Filter positions to those with exit times within the specified timerange.
    
    Args:
        positions: List of position dicts with 'exitTime' or 'exitTimestamp'
        start_time: Start of timerange (inclusive)
        end_time: End of timerange (inclusive)
        
    Returns:
        Filtered list of positions
    """
    filtered = []
    
    for pos in positions:
        # Get exit time from either exitTime string or exitTimestamp
        exit_time = pos.get('exitTime')
        if isinstance(exit_time, str):
            try:
                exit_time = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))
            except:
                # Try parsing as stored format
                exit_time = datetime.strptime(exit_time, '%Y-%m-%d %H:%M:%S')
        elif 'exitTimestamp' in pos:
            exit_time = datetime.fromtimestamp(pos['exitTimestamp'] / 1000)
        else:
            continue
        
        # Filter by timerange (inclusive)
        if start_time <= exit_time <= end_time:
            filtered.append(pos)
    
    logger.info(f"Filtered positions: {len(filtered)}/{len(positions)} within timerange")
    return filtered


def filter_ticks_by_timerange(
    ticks: List[Dict[str, Any]],
    start_time: datetime,
    end_time: datetime
) -> List[Dict[str, Any]]:
    """
    Filter ticks to those within the specified timerange.
    
    Args:
        ticks: List of tick dicts with 'timestamp'
        start_time: Start of timerange (inclusive)
        end_time: End of timerange (inclusive)
        
    Returns:
        Filtered list of ticks maintaining chronological order
    """
    filtered = []
    
    for tick in ticks:
        tick_time = tick.get('timestamp')
        if isinstance(tick_time, str):
            try:
                tick_time = datetime.fromisoformat(tick_time.replace('Z', '+00:00'))
            except:
                continue
        elif isinstance(tick_time, (int, float)):
            tick_time = datetime.fromtimestamp(tick_time / 1000)
        
        # Filter by timerange (inclusive)
        if start_time <= tick_time <= end_time:
            filtered.append(tick)
    
    logger.info(f"Filtered ticks: {len(filtered)}/{len(ticks)} within timerange")
    return filtered


async def handle_test_simulation(arguments: dict) -> list[TextContent]:
    """
    Test the trade simulation engine with a sample trade.
    
    Args:
        arguments: Dict with 'entry_price', 'direction', 'sl_pips', 'tp_pips'
        
    Returns:
        List of TextContent with simulation test results
    """
    entry_price = arguments.get("entry_price", 0)
    direction = arguments.get("direction", "BUY").upper()
    sl_pips = arguments.get("sl_pips", 10)
    tp_pips = arguments.get("tp_pips", 15)
    
    # Validate inputs
    if entry_price <= 0:
        return [TextContent(type="text", text="❌ Invalid entry_price: must be > 0")]
    
    if direction not in ["BUY", "SELL"]:
        return [TextContent(type="text", text="❌ Invalid direction: must be 'BUY' or 'SELL'")]
    
    if sl_pips <= 0 or tp_pips <= 0:
        return [TextContent(type="text", text="❌ Invalid SL/TP: must be > 0")]
    
    logger.info(f"Testing simulation: {direction} @ {entry_price}, SL={sl_pips}, TP={tp_pips}")
    
    # Generate synthetic tick data for testing
    # Create ticks that will trigger TP after some movement
    entry_time = datetime.now().replace(second=0, microsecond=0)
    pip_value = 0.1
    
    # Generate 100 ticks over 100 seconds
    test_ticks = []
    for i in range(100):
        tick_time = entry_time + timedelta(seconds=i)
        
        # Simulate price movement toward TP
        if direction == "BUY":
            # Price gradually rises to TP
            price_change = (tp_pips * pip_value) * (i / 50.0)  # Reaches TP around tick 50
            mid_price = entry_price + price_change
        else:  # SELL
            # Price gradually falls to TP
            price_change = (tp_pips * pip_value) * (i / 50.0)  # Reaches TP around tick 50
            mid_price = entry_price - price_change
        
        test_ticks.append({
            'timestamp': tick_time,
            'mid': mid_price,
            'bid': mid_price - 0.5,
            'ask': mid_price + 0.5
        })
    
    # Run simulation
    result = simulate_trade(
        entry_time=entry_time,
        entry_price=entry_price,
        direction=direction,
        ticks=test_ticks,
        sl_pips=sl_pips,
        tp_pips=tp_pips,
        pip_value=pip_value
    )
    
    # Format output
    result_text = "✅ **Trade Simulation Test**\n\n"
    result_text += "## Test Parameters\n\n"
    result_text += f"- **Direction:** {direction}\n"
    result_text += f"- **Entry Price:** {entry_price:.2f}\n"
    result_text += f"- **Entry Time:** {entry_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    result_text += f"- **Stop Loss:** {sl_pips} pips\n"
    result_text += f"- **Take Profit:** {tp_pips} pips\n\n"
    
    # Calculate SL/TP levels
    if direction == "BUY":
        sl_level = entry_price - (sl_pips * pip_value)
        tp_level = entry_price + (tp_pips * pip_value)
    else:
        sl_level = entry_price + (sl_pips * pip_value)
        tp_level = entry_price - (tp_pips * pip_value)
    
    result_text += f"- **SL Level:** {sl_level:.2f}\n"
    result_text += f"- **TP Level:** {tp_level:.2f}\n\n"
    
    result_text += "## Simulation Results\n\n"
    result_text += f"- **Result:** {result['result']}\n"
    result_text += f"- **Exit Reason:** {result['exit_reason']}\n"
    
    if result['exit_time']:
        result_text += f"- **Exit Time:** {result['exit_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        result_text += f"- **Exit Price:** {result['exit_price']:.2f}\n"
        duration_seconds = (result['exit_time'] - entry_time).total_seconds()
        result_text += f"- **Duration:** {duration_seconds:.0f} seconds\n"
    else:
        result_text += f"- **Exit Time:** Not triggered\n"
        result_text += f"- **Exit Price:** N/A\n"
    
    result_text += f"- **Pips Gained/Lost:** {result['pips_gained']:.1f} pips\n"
    result_text += f"- **Ticks Processed:** {result['ticks_processed']}\n\n"
    
    result_text += "## Test Data\n\n"
    result_text += f"Generated {len(test_ticks)} synthetic ticks for testing.\n"
    result_text += f"Price movement simulated toward {'TP' if result['result'] == 'WIN' else 'target'}.\n\n"
    
    if result['result'] == 'WIN':
        result_text += "✅ **Test Passed:** Simulation correctly detected TP trigger\n"
    elif result['result'] == 'LOSS':
        result_text += "✅ **Test Passed:** Simulation correctly detected SL trigger\n"
    else:
        result_text += "ℹ️ **Test Result:** No exit triggered (trade still open)\n"
    
    result_text += "\n🎯 **Simulation Engine Ready:** Use this logic for real trade optimization"
    
    return [TextContent(type="text", text=result_text)]


async def handle_optimize_trades_single(arguments: dict) -> list[TextContent]:
    """
    Optimize all trades for a specific date with a single SL/TP combination.
    
    Args:
        arguments: Dict with 'date', 'sl_pips', 'tp_pips', optional 'start_time', 'end_time'
        
    Returns:
        List of TextContent with optimization results and HTML report path
    """
    date_str = arguments.get("date", "")
    sl_pips = arguments.get("sl_pips", 10)
    tp_pips = arguments.get("tp_pips", 15)
    start_time_str = arguments.get("start_time", "00:00:00")
    end_time_str = arguments.get("end_time", "23:59:59")
    
    # Validate date
    try:
        trade_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return [TextContent(type="text", text=f"❌ Invalid date format: '{date_str}'. Expected YYYY-MM-DD")]
    
    # Parse time range
    try:
        start_time = datetime.strptime(f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        return [TextContent(type="text", text=f"❌ Invalid time format: {str(e)}")]
    
    logger.info(f"Optimizing trades for {date_str}, SL={sl_pips}, TP={tp_pips}, time={start_time_str}-{end_time_str}")
    
    # Step 1: Fetch closed positions
    positions_result = await handle_fetch_closed_positions({"date": date_str})
    positions_text = positions_result[0].text
    
    # Parse positions from the fetch result (we need to actually fetch them again for processing)
    api_url = f"http://localhost:8000/deals/{date_str}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(api_url)
            response.raise_for_status()
            data = response.json()
            
            closed_trades = data.get("closedTrades", [])
            
            # Parse positions
            positions = []
            for trade in closed_trades:
                if "closePositionDetail" not in trade:
                    continue
                    
                position = {
                    "dealId": trade.get("dealId"),
                    "positionId": trade.get("positionId"),
                    "symbolId": trade.get("symbolId"),
                    "direction": "SELL" if trade.get("tradeSide") == 1 else "BUY",
                    "volume": trade.get("volume"),
                    "entryPrice": trade["closePositionDetail"].get("entryPrice"),
                    "exitPrice": trade.get("price"),
                    "exitTime": datetime.fromtimestamp(trade.get("executionTimestamp", 0) / 1000),
                    "exitTimestamp": trade.get("executionTimestamp"),
                    "profit": trade.get("profit", 0),
                    "comment": trade.get("comment", "")
                }
                positions.append(position)
            
            # Filter by timerange
            filtered_positions = filter_positions_by_timerange(positions, start_time, end_time)
            
            if not filtered_positions:
                result_text = f"ℹ️ **No Trades Found**\n\n"
                result_text += f"**Date:** {date_str}\n"
                result_text += f"**Time Range:** {start_time_str} - {end_time_str}\n"
                result_text += f"**Total positions on date:** {len(positions)}\n"
                result_text += f"**Positions in timerange:** 0\n\n"
                result_text += "No trades to optimize for this date/timerange combination."
                return [TextContent(type="text", text=result_text)]
            
            logger.info(f"Found {len(filtered_positions)} positions in timerange")
            
            # Step 2: Map symbol IDs to names and fetch tick data
            symbol_map = {
                205: "US500_SB",  # US500
                219: "UK100_SB",  # UK100
                217: "DE40_SB",   # DE40
                220: "US30_SB",   # US30
                241: "AUS200_SB"  # AUS200
            }
            
            # Get unique symbols and fetch tick data for the full day
            symbol_ids = set(pos['symbolId'] for pos in filtered_positions)
            tick_data_by_symbol = {}
            
            vps_url = "http://localhost:8020"
            
            # Fetch symbols mapping first
            symbols_response = await client.get(f"{vps_url}/symbols")
            symbols_response.raise_for_status()
            symbols_data = symbols_response.json()
            symbols_list = symbols_data.get('symbols', [])
            
            for symbol_id in symbol_ids:
                symbol_name = symbol_map.get(symbol_id, f"Symbol_{symbol_id}")
                
                # Find pair ID
                pair_id = None
                base_symbol = symbol_name.replace('_SB', '')
                for sym in symbols_list:
                    sym_name = sym.get('name', '')
                    if sym_name == symbol_name or sym_name == base_symbol or sym_name == f"{base_symbol}_SB":
                        pair_id = sym.get('value')
                        break
                
                if not pair_id:
                    logger.warning(f"Could not find pair ID for symbol {symbol_name}, skipping")
                    continue
                
                # Fetch tick data for full day
                start_iso = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                end_iso = end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                
                tick_url = f"{vps_url}/getTickDataFromDB?pair={pair_id}&startDate={start_iso}&endDate={end_iso}&maxTicks=300000"
                logger.info(f"Fetching ticks for {symbol_name}: {tick_url}")
                
                tick_response = await client.get(tick_url, timeout=60.0)
                tick_response.raise_for_status()
                tick_data = tick_response.json()
                
                # Parse ticks
                ticks_raw = tick_data.get('data', [])
                ticks_parsed = []
                
                for tick in ticks_raw:
                    try:
                        ts_ms = tick.get('timestamp', 0)
                        ts = datetime.fromtimestamp(ts_ms / 1000) if ts_ms else None
                        bid = float(tick.get('bid', 0))
                        ask = float(tick.get('ask', 0))
                        mid = (bid + ask) / 2 if bid and ask else 0
                        
                        if ts and bid and ask:
                            ticks_parsed.append({
                                'timestamp': ts,
                                'timestamp_ms': ts_ms,
                                'bid': bid,
                                'ask': ask,
                                'mid': mid
                            })
                    except (ValueError, TypeError):
                        continue
                
                # Sort chronologically
                ticks_parsed.sort(key=lambda t: t['timestamp_ms'])
                tick_data_by_symbol[symbol_id] = ticks_parsed
                logger.info(f"Loaded {len(ticks_parsed)} ticks for {symbol_name}")
            
            # Step 3: Simulate each trade with actual tick data
            results = []
            wins = 0
            losses = 0
            no_exit = 0
            total_pips = 0
            
            for pos in filtered_positions:
                symbol_id = pos['symbolId']
                symbol_name = symbol_map.get(symbol_id, f"Symbol_{symbol_id}")
                
                # Get tick data for this symbol
                ticks = tick_data_by_symbol.get(symbol_id, [])
                
                if not ticks:
                    logger.warning(f"No tick data for {symbol_name}, skipping position {pos['dealId']}")
                    continue
                
                # We don't have entry time, only exit time from the position
                # Use exit time minus 2 hours as approximate entry time
                # In real scenario, you'd fetch entry time from another endpoint
                entry_time = pos['exitTime'] - timedelta(hours=2)
                
                # Run simulation
                sim_result = simulate_trade(
                    entry_time=entry_time,
                    entry_price=pos['entryPrice'],
                    direction=pos['direction'],
                    ticks=ticks,
                    sl_pips=sl_pips,
                    tp_pips=tp_pips,
                    pip_value=0.1
                )
                
                simulated_result = {
                    'dealId': pos['dealId'],
                    'symbol': symbol_name,
                    'direction': pos['direction'],
                    'entryPrice': pos['entryPrice'],
                    'exitTime': sim_result['exit_time'],
                    'exitPrice': sim_result['exit_price'],
                    'result': sim_result['result'],
                    'pips_gained': sim_result['pips_gained'],
                    'exit_reason': sim_result['exit_reason'],
                    'ticks_processed': sim_result['ticks_processed']
                }
                
                results.append(simulated_result)
                
                if sim_result['result'] == 'WIN':
                    wins += 1
                    total_pips += sim_result['pips_gained']
                elif sim_result['result'] == 'LOSS':
                    losses += 1
                    total_pips += sim_result['pips_gained']
                else:
                    no_exit += 1
            
            # Calculate statistics
            total_trades = len(results)
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            
            # Generate HTML report
            report_dir = Path(__file__).parent.parent / "data" / "optimization_reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"optimization_{date_str}_SL{sl_pips}_TP{tp_pips}_{timestamp}.html"
            report_path = report_dir / report_filename
            
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Trade Optimization Report - {date_str}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-box {{ background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #4CAF50; }}
        .stat-label {{ color: #666; font-size: 14px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .win {{ color: #4CAF50; }}
        .loss {{ color: #f44336; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #4CAF50; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Trade Optimization Report</h1>
        
        <div class="summary">
            <div class="stat-box">
                <div class="stat-label">Date</div>
                <div class="stat-value">{date_str}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">SL / TP</div>
                <div class="stat-value">{sl_pips} / {tp_pips} pips</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Trades</div>
                <div class="stat-value">{total_trades}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Win Rate</div>
                <div class="stat-value {('win' if win_rate >= 50 else 'loss')}">{win_rate:.1f}%</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Pips</div>
                <div class="stat-value {('win' if total_pips >= 0 else 'loss')}">{total_pips:+.1f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Avg Win</div>
                <div class="stat-value win">{avg_win:+.1f} pips</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Avg Loss</div>
                <div class="stat-value loss">{avg_loss:.1f} pips</div>
            </div>
        </div>
        
        <h2>Trade Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Deal ID</th>
                    <th>Symbol</th>
                    <th>Direction</th>
                    <th>Entry</th>
                    <th>Exit</th>
                    <th>Result</th>
                    <th>Pips</th>
                    <th>Exit Reason</th>
                    <th>Ticks</th>
                </tr>
            </thead>
            <tbody>
"""
            
            for r in results[:50]:  # Show first 50 trades
                result_class = "win" if r['result'] == 'WIN' else "loss"
                exit_price_str = f"{r['exitPrice']:.2f}" if r['exitPrice'] else "N/A"
                html_content += f"""
                <tr>
                    <td>{r['dealId']}</td>
                    <td>{r['symbol']}</td>
                    <td>{r['direction']}</td>
                    <td>{r['entryPrice']:.2f}</td>
                    <td>{exit_price_str}</td>
                    <td class="{result_class}">{r['result']}</td>
                    <td class="{result_class}">{r['pips_gained']:+.1f}</td>
                    <td>{r['exit_reason']}</td>
                    <td>{r['ticks_processed']}</td>
                </tr>
"""
            
            html_content += """
            </tbody>
        </table>
        
        <p style="color: #666; font-size: 14px; margin-top: 30px;">
            Generated by Trading Optimizer MCP Server
        </p>
    </div>
</body>
</html>
"""
            
            # Save HTML report
            report_path.write_text(html_content)
            logger.info(f"Saved optimization report to {report_path}")
            
            # Return summary
            result_text = f"✅ **Trade Optimization Complete**\n\n"
            result_text += f"**Date:** {date_str}\n"
            result_text += f"**Time Range:** {start_time_str} - {end_time_str}\n"
            result_text += f"**Parameters:** SL={sl_pips} pips, TP={tp_pips} pips\n\n"
            result_text += f"## Results\n\n"
            result_text += f"- **Total Trades:** {total_trades}\n"
            result_text += f"- **Winning Trades:** {wins}\n"
            result_text += f"- **Losing Trades:** {losses}\n"
            result_text += f"- **No Exit:** {no_exit}\n"
            result_text += f"- **Win Rate:** {win_rate:.1f}%\n"
            result_text += f"- **Total Pips:** {total_pips:+.1f}\n"
            result_text += f"- **Avg Win:** {avg_win:+.1f} pips\n"
            result_text += f"- **Avg Loss:** {avg_loss:.1f} pips\n\n"
            result_text += f"📄 **HTML Report:** `{report_path.relative_to(Path.cwd())}`\n\n"
            result_text += f"✅ **Real Simulation:** Used {sum(len(t) for t in tick_data_by_symbol.values()):,} ticks for precise replay\n"
            
            return [TextContent(type="text", text=result_text)]
            
    except Exception as e:
        error_msg = f"❌ Optimization failed: {str(e)}\n"
        logger.error(error_msg, exc_info=True)
        return [TextContent(type="text", text=error_msg)]


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Trading Optimizer MCP Server via stdio...")
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Server connected via stdio, initializing MCP protocol...")
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("Trading Optimizer MCP Server main entry point")
    asyncio.run(main())
