#!/usr/bin/env python3
"""
Strategy Builder MCP Server

Provides MCP tools for the Transcript Strategy Builder workflow:
- validate_dsl_strategy: Validate DSL JSON against schema
- save_dsl_strategy: Save validated DSL JSON to dsl_strategies directory
- list_dsl_strategies: List all available DSL strategy cartridges
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import mcp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Configure logging to file for debugging
log_file = Path(__file__).parent.parent.parent / "logs" / "strategy_builder.log"
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)
logger.info("Strategy Builder MCP Server starting up...")

# MCP Server
app = Server("strategy-builder")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools for the strategy builder."""
    return [
        Tool(
            name="validate_dsl_strategy",
            description="Validate DSL JSON against the schema. Checks for required fields, correct syntax, and returns specific error messages if validation fails.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dsl_json": {
                        "type": "string",
                        "description": "The DSL JSON as a string"
                    }
                },
                "required": ["dsl_json"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="save_dsl_strategy",
            description="Save validated DSL JSON to the dsl_strategies directory. Automatically generates filename from strategy name if not provided.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dsl_json": {
                        "type": "string",
                        "description": "The DSL JSON as a string"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional filename (auto-generated from strategy name if not provided)"
                    }
                },
                "required": ["dsl_json"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="list_dsl_strategies",
            description="List all available DSL strategy cartridges with their metadata (name, type, version, description).",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls for the strategy builder."""
    
    try:
        if name == "validate_dsl_strategy":
            return await handle_validate_dsl_strategy(arguments)
            
        elif name == "save_dsl_strategy":
            return await handle_save_dsl_strategy(arguments)
            
        elif name == "list_dsl_strategies":
            return await handle_list_dsl_strategies(arguments)
            
        else:
            return [TextContent(
                type="text",
                text=f"❌ Unknown tool: {name}"
            )]
            
    except Exception as e:
        logger.error(f"Tool call failed: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]


async def handle_validate_dsl_strategy(arguments: dict) -> list[TextContent]:
    """Handle DSL strategy validation."""
    from mcp_servers.strategy_builder.validators import validate_dsl_json
    
    try:
        # Validate input parameters
        if "dsl_json" not in arguments:
            return [TextContent(
                type="text",
                text="❌ Error: Missing required parameter 'dsl_json'"
            )]
        
        dsl_json = arguments["dsl_json"]
        
        # Validate the DSL JSON
        result = validate_dsl_json(dsl_json)
        
        # Format response based on validation result
        if result["valid"]:
            response = f"""✅ **Validation Successful**

**Strategy Name:** {result['strategy_name']}
**Strategy Type:** {result['strategy_type']}

{result.get('message', 'Strategy is valid and ready for use.')}

You can now save this strategy using the `save_dsl_strategy` tool."""
        else:
            errors_formatted = "\n".join(f"  • {error}" for error in result["errors"])
            response = f"""❌ **Validation Failed**

**Strategy Name:** {result['strategy_name']}
**Strategy Type:** {result['strategy_type']}

**Errors:**
{errors_formatted}

Please fix these errors and validate again."""
        
        logger.info(f"Validation result: valid={result['valid']}, strategy={result['strategy_name']}")
        
        return [TextContent(
            type="text",
            text=response
        )]
        
    except Exception as e:
        logger.error(f"Validation handler failed: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"❌ Validation error: {str(e)}"
        )]


async def handle_save_dsl_strategy(arguments: dict) -> list[TextContent]:
    """Handle saving DSL strategy to file."""
    from mcp_servers.strategy_builder.file_operations import save_dsl_strategy_to_file
    
    try:
        # Validate input parameters
        if "dsl_json" not in arguments:
            return [TextContent(
                type="text",
                text="❌ Error: Missing required parameter 'dsl_json'"
            )]
        
        dsl_json = arguments["dsl_json"]
        filename = arguments.get("filename")  # Optional
        
        # Save the DSL strategy
        result = save_dsl_strategy_to_file(dsl_json, filename)
        
        # Format response based on save result
        if result["success"]:
            response = f"""✅ **Strategy Saved Successfully**

{result['message']}

**File Path:** `{result['file_path']}`

You can now:
1. List all strategies using `list_dsl_strategies` tool
2. Run a backtest using `run_strategy_backtest` from the universal-backtest-engine
3. Create a chart using `create_strategy_chart` from the modular-chart-engine"""
        else:
            response = f"""❌ **Save Failed**

{result['message']}

Please fix the errors and try again."""
        
        logger.info(f"Save result: success={result['success']}, path={result['file_path']}")
        
        return [TextContent(
            type="text",
            text=response
        )]
        
    except Exception as e:
        logger.error(f"Save handler failed: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"❌ Save error: {str(e)}"
        )]


async def handle_list_dsl_strategies(arguments: dict) -> list[TextContent]:
    """Handle listing DSL strategies."""
    from mcp_servers.strategy_builder.file_operations import list_dsl_strategies
    
    try:
        # List all DSL strategies
        result = list_dsl_strategies()
        
        # Format response based on result
        if result["count"] == 0:
            response = """📋 **No DSL Strategies Found**

The dsl_strategies directory is empty or does not exist.

To create a new strategy:
1. Use the Transcript Strategy Builder workflow
2. Generate DSL JSON using the prompt templates
3. Validate using `validate_dsl_strategy` tool
4. Save using `save_dsl_strategy` tool"""
        else:
            # Build formatted list of strategies
            strategies_list = []
            for strategy in result["strategies"]:
                strategies_list.append(
                    f"""**{strategy['name']}** (v{strategy['version']})
  • Type: {strategy['type']}
  • File: {strategy['filename']}
  • Description: {strategy['description']}"""
                )
            
            strategies_formatted = "\n\n".join(strategies_list)
            
            response = f"""📋 **Available DSL Strategies** ({result['count']} found)

{strategies_formatted}

To use a strategy:
• Run backtest: `run_strategy_backtest` with strategy_name
• Create chart: `create_strategy_chart` with strategy_name"""
        
        logger.info(f"Listed {result['count']} strategies")
        
        return [TextContent(
            type="text",
            text=response
        )]
        
    except Exception as e:
        logger.error(f"List handler failed: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"❌ List error: {str(e)}"
        )]


async def main():
    """Main server entry point."""
    try:
        logger.info("Starting Strategy Builder MCP Server...")
        
        # Run the MCP server
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
            
    except Exception as e:
        logger.error(f"Server failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
