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
from datetime import datetime
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
    result_text += "• ✅ Fetch tick data for optimization\n\n"
    
    result_text += "### Planned Features:\n"
    result_text += "• 🔄 Simulate trades with different SL/TP\n"
    result_text += "• 🔄 Generate HTML optimization reports\n"
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
