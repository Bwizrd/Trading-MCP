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
    result_text += "• ✅ Fetch closed positions from deals endpoint\n\n"
    
    result_text += "### Planned Features:\n"
    result_text += "• 🔄 Load tick data for trade replay\n"
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
