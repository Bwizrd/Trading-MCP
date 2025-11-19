#!/usr/bin/env python3
"""
Universal Strategy Backtest Engine MCP Server

Exposes the universal backtest engine through MCP endpoints, allowing
any strategy "cartridge" to be run via MCP calls with configurable parameters.

This is the MCP interface for the strategy cartridge system.
"""

import asyncio
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from contextlib import asynccontextmanager
import sys
from pathlib import Path

import mcp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from shared.data_connector import DataConnector
from shared.strategy_registry import StrategyRegistry
from shared.backtest_engine import UniversalBacktestEngine
from shared.strategy_interface import BacktestConfiguration
from shared.chart_engine import ChartEngine

# Configure logging to file for debugging
log_file = Path(__file__).parent.parent / "logs" / "universal_backtest_engine.log"
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)  # Also log to stderr for debugging
    ]
)
logger = logging.getLogger(__name__)
logger.info("Universal Backtest Engine starting up...")

# Global components
data_connector: Optional[DataConnector] = None
strategy_registry: Optional[StrategyRegistry] = None
backtest_engine: Optional[UniversalBacktestEngine] = None
chart_engine: Optional[ChartEngine] = None

# MCP Server
app = Server("universal-strategy-backtest")


@asynccontextmanager
async def get_initialized_components():
    """Get initialized components with proper resource management."""
    global data_connector, strategy_registry, backtest_engine, chart_engine
    
    try:
        logger.info("Initializing components...")
        
        if not data_connector:
            logger.info("Creating DataConnector...")
            data_connector = DataConnector()
            logger.info("DataConnector created successfully")
            
        if not strategy_registry:
            logger.info("Creating StrategyRegistry...")
            strategy_registry = StrategyRegistry()
            logger.info("StrategyRegistry created successfully")
            
        if not backtest_engine:
            logger.info("Creating UniversalBacktestEngine...")
            backtest_engine = UniversalBacktestEngine(data_connector)
            logger.info("UniversalBacktestEngine created successfully")
            
        if not chart_engine:
            logger.info("Creating ChartEngine...")
            chart_engine = ChartEngine()
            logger.info("ChartEngine created successfully")
            
        logger.info("All components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}", exc_info=True)
        raise
    
    try:
        yield data_connector, strategy_registry, backtest_engine, chart_engine
    finally:
        # Cleanup if needed
        pass


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools for the universal backtest engine."""
    return [
        Tool(
            name="list_strategy_cartridges",
            description="List all available strategy cartridges with their descriptions and requirements",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_strategy_info",
            description="Get detailed information about a specific strategy cartridge",
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy_name": {
                        "type": "string",
                        "description": "Name of the strategy to get information about"
                    }
                },
                "required": ["strategy_name"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="run_strategy_backtest",
            description="Run a backtest using any strategy cartridge with configurable parameters",
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy_name": {
                        "type": "string",
                        "description": "Name of the strategy cartridge to run"
                    },
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol (e.g., 'EURUSD', 'GBPUSD')",
                        "default": "EURUSD"
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Timeframe for the data (e.g., '1m', '5m', '15m', '30m', '1h', '4h', '1d')",
                        "default": "30m"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format",
                        "pattern": r"^\d{4}-\d{2}-\d{2}$"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format",
                        "pattern": r"^\d{4}-\d{2}-\d{2}$"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days to look back for data (default: 365, max: 18250 for 50 years)",
                        "minimum": 1,
                        "maximum": 18250
                    },
                    "initial_balance": {
                        "type": "number",
                        "description": "Initial balance for the backtest",
                        "minimum": 100,
                        "default": 10000
                    },
                    "risk_per_trade": {
                        "type": "number",
                        "description": "Risk per trade as a percentage (0.01 = 1%)",
                        "minimum": 0.001,
                        "maximum": 0.1,
                        "default": 0.02
                    },
                    "stop_loss_pips": {
                        "type": "number",
                        "description": "Stop loss in pips",
                        "minimum": 1,
                        "default": 15
                    },
                    "take_profit_pips": {
                        "type": "number",
                        "description": "Take profit in pips",
                        "minimum": 1,
                        "default": 25
                    },
                    "strategy_parameters": {
                        "type": "object",
                        "description": "Custom parameters for the strategy",
                        "additionalProperties": True
                    },
                    "auto_chart": {
                        "type": "boolean",
                        "description": "Automatically create chart after backtest (default: true)",
                        "default": true
                    }
                },
                "required": ["strategy_name"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="compare_strategies",
            description="Compare multiple strategies on the same data and parameters",
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy_names": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of strategy names to compare (empty = all strategies)"
                    },
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol",
                        "default": "EURUSD"
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Timeframe for the data",
                        "default": "30m"
                    },
                    "days_back": {
                        "type": "integer",
                        "description": "Number of days back from today (default: 365, max: 18250 for 50 years)",
                        "default": 365,
                        "minimum": 1,
                        "maximum": 18250
                    },
                    "initial_balance": {
                        "type": "number",
                        "default": 10000
                    },
                    "stop_loss_pips": {
                        "type": "number",
                        "default": 15
                    },
                    "take_profit_pips": {
                        "type": "number",
                        "default": 25
                    }
                },
                "additionalProperties": False
            }
        ),
        Tool(
            name="test_data_connectivity",
            description="Test connectivity to data sources and show available symbols",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="create_strategy_from_dsl",
            description="Create a new DSL trading strategy from JSON configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "dsl_config": {
                        "type": "object",
                        "description": "Complete DSL strategy configuration as JSON object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Human-readable strategy name"
                            },
                            "version": {
                                "type": "string",
                                "description": "Version in semantic format (e.g., '1.0.0')"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of strategy logic"
                            },
                            "timing": {
                                "type": "object",
                                "properties": {
                                    "reference_time": {
                                        "type": "string",
                                        "description": "Reference time in HH:MM format"
                                    },
                                    "reference_price": {
                                        "type": "string",
                                        "enum": ["open", "high", "low", "close"],
                                        "description": "Which price to use from reference time"
                                    },
                                    "signal_time": {
                                        "type": "string",
                                        "description": "Signal generation time in HH:MM format"
                                    }
                                },
                                "required": ["reference_time", "reference_price", "signal_time"]
                            },
                            "conditions": {
                                "type": "object",
                                "properties": {
                                    "buy": {
                                        "type": "object",
                                        "properties": {
                                            "compare": {"type": "string"}
                                        },
                                        "required": ["compare"]
                                    },
                                    "sell": {
                                        "type": "object",
                                        "properties": {
                                            "compare": {"type": "string"}
                                        },
                                        "required": ["compare"]
                                    }
                                },
                                "required": ["buy", "sell"]
                            },
                            "risk_management": {
                                "type": "object",
                                "properties": {
                                    "stop_loss_pips": {"type": "number"},
                                    "take_profit_pips": {"type": "number"}
                                },
                                "required": ["stop_loss_pips", "take_profit_pips"]
                            }
                        },
                        "required": ["name", "version", "description", "timing", "conditions", "risk_management"]
                    }
                },
                "required": ["dsl_config"],
                "additionalProperties": False
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls for the universal backtest engine."""
    
    try:
        async with get_initialized_components() as (connector, registry, engine, chart_engine):
            
            if name == "list_strategy_cartridges":
                return await handle_list_strategies(registry)
                
            elif name == "get_strategy_info":
                return await handle_get_strategy_info(registry, arguments)
                
            elif name == "run_strategy_backtest":
                return await handle_run_backtest(registry, engine, chart_engine, arguments)
                
            elif name == "compare_strategies":
                return await handle_compare_strategies(registry, engine, arguments)
                
            elif name == "test_data_connectivity":
                return await handle_test_connectivity(connector)
                
            elif name == "create_strategy_from_dsl":
                return await handle_create_dsl_strategy(registry, arguments)
                
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Unknown tool: {name}"
                )]
                
    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        return [TextContent(
            type="text", 
            text=f"❌ Error: {str(e)}"
        )]


async def handle_list_strategies(registry: StrategyRegistry) -> list[TextContent]:
    """Handle listing available strategy cartridges."""
    strategies = registry.list_strategies()
    
    if not strategies:
        return [TextContent(
            type="text",
            text="❌ No strategy cartridges found"
        )]
    
    result = "🎮 **Available Strategy Cartridges**\n\n"
    
    for i, strategy_name in enumerate(strategies, 1):
        info = registry.get_strategy_info(strategy_name)
        result += f"**{i}. {strategy_name}** (v{info['version']})\n"
        result += f"   📝 {info['description']}\n"
        result += f"   📊 Requires: {', '.join(info['required_indicators']) if info['required_indicators'] else 'None'}\n"
        result += f"   ⚙️ Parameters: {len(info['default_parameters'])} available\n\n"
    
    result += f"💾 **Total:** {len(strategies)} strategy cartridges available"
    
    return [TextContent(type="text", text=result)]


async def handle_get_strategy_info(registry: StrategyRegistry, arguments: dict) -> list[TextContent]:
    """Handle getting detailed strategy information."""
    strategy_name = arguments["strategy_name"]
    
    try:
        info = registry.get_strategy_info(strategy_name)
        
        result = f"📦 **{strategy_name}** (v{info['version']})\n\n"
        result += f"**Description:** {info['description']}\n\n"
        result += f"**Required Indicators:** {', '.join(info['required_indicators']) if info['required_indicators'] else 'None'}\n\n"
        result += f"**Default Parameters:**\n"
        
        for param, value in info['default_parameters'].items():
            result += f"  • `{param}`: {value}\n"
        
        result += f"\n**Module:** {info['module']}\n"
        result += f"**File:** {info['file']}"
        
        return [TextContent(type="text", text=result)]
        
    except KeyError:
        available = registry.list_strategies()
        return [TextContent(
            type="text",
            text=f"❌ Strategy '{strategy_name}' not found.\n\nAvailable strategies: {', '.join(available)}"
        )]


async def handle_run_backtest(registry: StrategyRegistry, engine: UniversalBacktestEngine, chart_engine: ChartEngine, arguments: dict) -> list[TextContent]:
    """Handle running a strategy backtest."""
    strategy_name = arguments["strategy_name"]
    
    # Extract parameters with defaults
    symbol = arguments.get("symbol", "EURUSD")
    timeframe = arguments.get("timeframe", "30m")
    initial_balance = arguments.get("initial_balance", 10000)
    risk_per_trade = arguments.get("risk_per_trade", 0.02)
    stop_loss_pips = arguments.get("stop_loss_pips", 15)
    take_profit_pips = arguments.get("take_profit_pips", 25)
    strategy_parameters = arguments.get("strategy_parameters", {})
    auto_chart = arguments.get("auto_chart", True)  # Default to True for automatic chart creation
    
    # Handle date range
    if "start_date" in arguments and "end_date" in arguments:
        start_date = arguments["start_date"]
        end_date = arguments["end_date"]
    else:
        days_back = arguments.get("days_back", 365)
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days_back)
        start_date = start_dt.strftime('%Y-%m-%d')
        end_date = end_dt.strftime('%Y-%m-%d')
    
    try:
        # Create strategy instance
        strategy = registry.create_strategy(strategy_name, strategy_parameters)
        
        # Create backtest configuration
        config = BacktestConfiguration(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            risk_per_trade=risk_per_trade,
            stop_loss_pips=stop_loss_pips,
            take_profit_pips=take_profit_pips
        )
        
        # Run backtest
        results = await engine.run_backtest(strategy, config)
        
        # Export backtest results to JSON file (modular approach)
        import json
        import os
        from datetime import datetime as dt
        
        # Create results directory using absolute path
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        results_dir = project_root / "optimization_results"
        results_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f"backtest_{symbol}_{timestamp}.json"
        json_filepath = results_dir / json_filename
        
        # Export complete results to JSON
        results_json = results.to_dict(include_market_data=True)
        with open(json_filepath, 'w') as f:
            json.dump(results_json, f, indent=2)
        
        # Format backtest results
        result_text = format_backtest_results(results)
        
        # Add the full JSON data to the response for Claude Desktop
        result_text += f"\n\n📊 **COMPLETE BACKTEST DATA (JSON):**"
        result_text += f"\n```json\n{json.dumps(results_json, indent=2)}\n```"
        
        # Add modular workflow info
        result_text += f"\n\n💾 **Backtest Results Exported (Modular Architecture):**"
        result_text += f"\n📁 **JSON File:** `{json_filepath}`"
        result_text += f"\n📊 **Contains:** Complete backtest data, all {len(results.trades)} trades, and {len(results.market_data)} market candles"
        
        # Automatically create chart if requested using Modular Chart Engine
        if auto_chart:
            result_text += f"\n\n🎨 **Calling Modular Chart Engine Service...**"
            
            try:
                # Import the modular chart engine function
                from mcp_servers.modular_chart_engine import create_chart_from_backtest_json
                
                # Call the modular chart engine with the JSON file we just created
                chart_result = await create_chart_from_backtest_json(json_filename)
                
                # Extract the chart information from the modular chart engine response
                if chart_result and len(chart_result) > 0:
                    chart_text = chart_result[0].text
                    # Extract chart path from the response
                    import re
                    chart_path_match = re.search(r'Chart File:\*\* `([^`]+)`', chart_text)
                    if chart_path_match:
                        chart_path = chart_path_match.group(1)
                        result_text += f"\n✅ **Chart Created Successfully via Modular Chart Engine!**"
                        result_text += f"\n📈 **Interactive Chart:** `{chart_path}`"
                        result_text += f"\n\n🎨 **Complete Visualization:**"
                        result_text += f"\n• 📊 Candlestick chart with {len(results.market_data)} price bars"
                        result_text += f"\n• 🎯 {len(results.trades)} trade markers with entry/exit points"
                        if "MA CROSSOVER" in strategy_name.upper():
                            result_text += f"\n• 📈 SMA20 (blue) and SMA50 (orange) moving average lines"
                        result_text += f"\n• 📈 P&L performance visualization"
                        result_text += f"\n• 📊 Cumulative profit/loss curve"
                        result_text += f"\n\n💡 **Open `{chart_path}` in your browser to explore the interactive analysis!**"
                        result_text += f"\n\n🏗️ **Modular Architecture:** Backtest → JSON Export → Modular Chart Engine → Visualization!"
                    else:
                        result_text += f"\n✅ **Chart created via Modular Chart Engine**"
                        result_text += f"\n📊 **Details:** {chart_text[:200]}..."
                else:
                    result_text += f"\n⚠️ **Chart engine returned empty result**"
                    
            except Exception as chart_error:
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"Modular chart engine call failed: {chart_error}\n{error_details}")
                result_text += f"\n⚠️ **Modular Chart Engine call failed:** {str(chart_error)}"
                result_text += f"\n🔧 **Error details:** {error_details[:200]}..."
                result_text += f"\n💡 **Manual option:** Use modular chart engine directly with file: `{json_filename}`"
        else:
            result_text += f"\n\n📊 **Chart creation skipped** (auto_chart=false)"
            result_text += f"\n💡 **Manual option:** Use modular chart engine with file: `{json_filename}`"
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Backtest failed: {str(e)}"
        )]


async def handle_compare_strategies(registry: StrategyRegistry, engine: UniversalBacktestEngine, arguments: dict) -> list[TextContent]:
    """Handle comparing multiple strategies."""
    strategy_names = arguments.get("strategy_names", [])
    
    # If no strategies specified, use all available
    if not strategy_names:
        strategy_names = registry.list_strategies()
    
    if not strategy_names:
        return [TextContent(
            type="text",
            text="❌ No strategies available for comparison"
        )]
    
    # Extract common parameters
    symbol = arguments.get("symbol", "EURUSD")
    timeframe = arguments.get("timeframe", "30m")
    days_back = arguments.get("days_back", 7)
    initial_balance = arguments.get("initial_balance", 10000)
    stop_loss_pips = arguments.get("stop_loss_pips", 15)
    take_profit_pips = arguments.get("take_profit_pips", 25)
    
    # Calculate date range
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=days_back)
    start_date = start_dt.strftime('%Y-%m-%d')
    end_date = end_dt.strftime('%Y-%m-%d')
    
    result_text = f"🔬 **Strategy Comparison**\n\n"
    result_text += f"**Symbol:** {symbol} | **Timeframe:** {timeframe} | **Period:** {days_back} days\n"
    result_text += f"**Date Range:** {start_date} to {end_date}\n\n"
    
    comparison_data = []
    
    for strategy_name in strategy_names:
        try:
            # Create strategy and config
            strategy = registry.create_strategy(strategy_name)
            config = BacktestConfiguration(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                initial_balance=initial_balance,
                stop_loss_pips=stop_loss_pips,
                take_profit_pips=take_profit_pips
            )
            
            # Run backtest
            results = await engine.run_backtest(strategy, config)
            
            comparison_data.append({
                'name': strategy_name,
                'results': results
            })
            
        except Exception as e:
            result_text += f"❌ **{strategy_name}** failed: {str(e)}\n\n"
    
    if comparison_data:
        # Sort by total return
        comparison_data.sort(key=lambda x: x['results'].total_pips, reverse=True)
        
        result_text += "## 🏆 **Results Summary**\n\n"
        
        for i, data in enumerate(comparison_data, 1):
            results = data['results']
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            
            result_text += f"{medal} **{data['name']}**\n"
            result_text += f"   💰 Total: {results.total_pips:+.1f} pips\n"
            result_text += f"   📊 Trades: {results.total_trades} | Win Rate: {results.win_rate:.1%}\n"
            result_text += f"   📈 Profit Factor: {results.profit_factor:.2f} | Max DD: {results.max_drawdown:.1f} pips\n\n"
        
        # Add detailed breakdown for top performer
        if comparison_data:
            best_results = comparison_data[0]['results']
            result_text += f"## 📋 **Best Performer Details ({comparison_data[0]['name']})**\n\n"
            result_text += format_detailed_stats(best_results)
    
    return [TextContent(type="text", text=result_text)]


async def handle_test_connectivity(connector: DataConnector) -> list[TextContent]:
    """Handle testing data connectivity."""
    try:
        # Test connectivity
        connectivity = await connector.test_connectivity()
        
        # Get symbols
        symbols_response = await connector.get_symbols()
        
        result_text = "🔌 **Data Connectivity Test**\n\n"
        result_text += f"**InfluxDB:** {'✅ Connected' if connectivity.get('influxdb', False) else '❌ Failed'}\n"
        result_text += f"**cTrader:** {'✅ Connected' if connectivity.get('ctrader', False) else '❌ Failed'}\n\n"
        
        if 'symbols' in symbols_response:
            symbols_list = symbols_response['symbols']
            symbols_count = len(symbols_list)
            
            result_text += f"**Available Symbols:** {symbols_count}\n"
            
            # Show sample symbols by category
            categories = symbols_response.get('categories', {})
            result_text += f"**Categories:** {categories}\n\n"
            
            sample_symbols = [symbol['name'].replace('_SB', '') for symbol in symbols_list[:10]]
            result_text += f"**Sample Symbols:** {', '.join(sample_symbols)}\n\n"
            
            # Show timeframes
            timeframes = symbols_response.get('supportedTimeframes', [])
            result_text += f"**Supported Timeframes:** {', '.join(timeframes)}"
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Connectivity test failed: {str(e)}"
        )]


async def handle_create_dsl_strategy(registry: StrategyRegistry, arguments: dict) -> list[TextContent]:
    """Handle creating a new DSL strategy from JSON configuration."""
    dsl_config = arguments["dsl_config"]
    
    try:
        # Import DSL components
        from shared.strategies.dsl_interpreter.dsl_loader import get_dsl_loader
        from shared.strategies.dsl_interpreter.schema_validator import validate_dsl_strategy, DSLValidationError
        
        # Validate DSL configuration
        validate_dsl_strategy(dsl_config)
        
        # Get DSL loader and create strategy file
        dsl_loader = get_dsl_loader()
        strategy_name = dsl_config["name"]
        
        # Create the DSL strategy file
        json_filepath = dsl_loader.create_dsl_strategy_file(strategy_name, dsl_config)
        
        # Reload strategies to include the new DSL strategy
        registry.reload_strategies()
        
        result_text = f"✅ **DSL Strategy Created Successfully!**\n\n"
        result_text += f"**Strategy Name:** {strategy_name}\n"
        result_text += f"**Version:** {dsl_config['version']}\n"
        result_text += f"**Description:** {dsl_config['description']}\n\n"
        
        # Show timing details
        timing = dsl_config['timing']
        result_text += f"**Timing Logic:**\n"
        result_text += f"• Reference: {timing['reference_time']} ({timing['reference_price']} price)\n"
        result_text += f"• Signal: {timing['signal_time']}\n\n"
        
        # Show conditions
        conditions = dsl_config['conditions']
        result_text += f"**Trading Conditions:**\n"
        result_text += f"• Buy: {conditions['buy']['compare']}\n"
        result_text += f"• Sell: {conditions['sell']['compare']}\n\n"
        
        # Show risk management
        risk_mgmt = dsl_config['risk_management']
        result_text += f"**Risk Management:**\n"
        result_text += f"• Stop Loss: {risk_mgmt['stop_loss_pips']} pips\n"
        result_text += f"• Take Profit: {risk_mgmt['take_profit_pips']} pips\n\n"
        
        result_text += f"📁 **File Created:** `{json_filepath}`\n"
        result_text += f"🎮 **Status:** Strategy is now available in cartridge catalog\n"
        result_text += f"🚀 **Next Step:** Use `run_strategy_backtest(strategy_name=\"{strategy_name}\")` to test it"
        
        return [TextContent(type="text", text=result_text)]
        
    except DSLValidationError as e:
        return [TextContent(
            type="text",
            text=f"❌ DSL validation failed: {str(e)}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ DSL strategy creation failed: {str(e)}"
        )]


def format_backtest_results(results) -> str:
    """Format backtest results for display."""
    result_text = f"📊 **Backtest Results: {results.strategy_name}**\n\n"
    
    result_text += f"**Strategy:** {results.strategy_name} (v{results.strategy_version})\n"
    result_text += f"**Symbol:** {results.configuration.symbol}\n"
    result_text += f"**Timeframe:** {results.configuration.timeframe}\n"
    result_text += f"**Period:** {results.configuration.start_date} to {results.configuration.end_date}\n"
    result_text += f"**Data Source:** {results.data_source}\n\n"
    
    result_text += "## 💰 **Performance**\n"
    result_text += f"• **Total Return:** {results.total_pips:+.1f} pips\n"
    result_text += f"• **Initial Balance:** ${results.configuration.initial_balance:,.2f}\n"
    result_text += f"• **Risk per Trade:** {results.configuration.risk_per_trade:.1%}\n\n"
    
    result_text += "## 📋 **Trade Summary**\n"
    result_text += f"• **Total Trades:** {results.total_trades}\n"
    result_text += f"• **Winning Trades:** {results.winning_trades} ({results.win_rate:.1%})\n"
    result_text += f"• **Losing Trades:** {results.losing_trades}\n"
    result_text += f"• **Average Win:** {results.average_win:+.1f} pips\n"
    result_text += f"• **Average Loss:** {results.average_loss:+.1f} pips\n"
    result_text += f"• **Profit Factor:** {results.profit_factor:.2f}\n"
    result_text += f"• **Max Drawdown:** {results.max_drawdown:.1f} pips\n\n"
    
    # Show recent trades
    if results.trades:
        result_text += "## 🔍 **Recent Trades**\n"
        for trade in results.trades[-5:]:
            result_emoji = "✅" if trade.result.name == "WIN" else "❌" if trade.result.name == "LOSS" else "⚖️"
            result_text += f"• {result_emoji} {trade.direction.name} @ {trade.entry_price:.5f} → {trade.exit_price:.5f} ({trade.pips:+.1f} pips)\n"
    
    result_text += f"\n⏱️ **Execution Time:** {results.execution_time_seconds:.2f} seconds"
    
    return result_text


def format_detailed_stats(results) -> str:
    """Format detailed statistics."""
    stats_text = f"• **Largest Win:** {results.largest_win:.1f} pips\n"
    stats_text += f"• **Largest Loss:** {results.largest_loss:.1f} pips\n"
    stats_text += f"• **Max Consecutive Wins:** {results.max_consecutive_wins}\n"
    stats_text += f"• **Max Consecutive Losses:** {results.max_consecutive_losses}\n"
    
    return stats_text


async def main():
    """Main server entry point."""
    # COMPLETELY SILENT - no output allowed
    
    # Initialize components
    try:
        async with get_initialized_components() as (connector, registry, engine, chart_engine):
            # Silent initialization
            pass
            
        # Run the MCP server
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
            
    except Exception as e:
        # Silent failure - no output allowed in MCP servers
        raise


if __name__ == "__main__":
    asyncio.run(main())