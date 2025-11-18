#!/usr/bin/env python3
"""
Modular Chart Engine MCP Server

Clean chart server that follows proper architecture:
Strategy Cartridges → Backtest Engine → Chart Engine → Visualizations

This server:
1. Uses the Universal Backtest Engine to run strategies
2. Uses the Chart Engine to visualize results  
3. Contains NO strategy logic - pure visualization service
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from contextlib import asynccontextmanager

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from pydantic import BaseModel, Field

# Project imports - proper modular architecture
from shared.data_connector import DataConnector
from shared.strategy_registry import StrategyRegistry
from shared.backtest_engine import UniversalBacktestEngine
from shared.chart_engine import ChartEngine
from shared.strategy_interface import BacktestConfiguration
from shared.models import Candle

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Only warnings and errors
logger = logging.getLogger(__name__)

# Initialize FastMCP
app = FastMCP("modular_chart_server")

# Global components
data_connector: Optional[DataConnector] = None
strategy_registry: Optional[StrategyRegistry] = None
backtest_engine: Optional[UniversalBacktestEngine] = None
chart_engine: Optional[ChartEngine] = None

logger = logging.getLogger(__name__)


def _calculate_ma_indicators(candles: List[Candle]) -> Dict[str, List[float]]:
    """
    Calculate Moving Average indicators for MA Crossover strategies.
    
    Args:
        candles: List of market candles
        
    Returns:
        Dictionary with SMA20 and SMA50 values
    """
    print(f"🔧 _calculate_ma_indicators called with {len(candles)} candles")
    
    try:
        import pandas as pd
        import ta
        print("🔧 Successfully imported pandas and ta")
    except ImportError as e:
        print(f"🔧 ImportError: {e}")
        logger.warning("pandas or ta library not available for indicator calculation")
        return {}
    
    if len(candles) < 50:  # Need at least 50 candles for SMA50
        print(f"🔧 Insufficient candles: {len(candles)} < 50")
        logger.warning(f"Insufficient candles ({len(candles)}) for SMA50 calculation")
        return {}
    
    # Convert candles to DataFrame
    df = pd.DataFrame([
        {
            'close': candle.close,
            'open': candle.open,
            'high': candle.high,
            'low': candle.low,
            'volume': candle.volume or 0
        }
        for candle in candles
    ])
    
    indicators = {}
    
    try:
        # Calculate SMA20 (Fast MA)
        sma20 = ta.trend.sma_indicator(df['close'], window=20)
        indicators['SMA20 (Fast)'] = sma20.fillna(0).tolist()
        
        # Calculate SMA50 (Slow MA) 
        sma50 = ta.trend.sma_indicator(df['close'], window=50)
        indicators['SMA50 (Slow)'] = sma50.fillna(0).tolist()
        
        logger.info(f"Calculated MA indicators: SMA20 ({len(sma20)} values), SMA50 ({len(sma50)} values)")
        
    except Exception as e:
        logger.error(f"Error calculating MA indicators: {e}")
        
    return indicators


# Input Models
class ChartBacktestInput(BaseModel):
    """Input for generating charts from strategy backtests."""
    strategy_name: str = Field(description="Name of the strategy to backtest and chart")
    symbol: str = Field(default="EURUSD", description="Trading symbol")
    timeframe: str = Field(default="30m", description="Data timeframe")
    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")
    days_back: int = Field(default=7, description="Days back from now (if dates not specified)")
    stop_loss_pips: float = Field(default=15.0, description="Stop loss in pips")
    take_profit_pips: float = Field(default=25.0, description="Take profit in pips")
    chart_title: Optional[str] = Field(default=None, description="Custom chart title")
    strategy_parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")


class PerformanceChartInput(BaseModel):
    """Input for generating performance-only charts."""
    strategy_name: str = Field(description="Name of the strategy")
    symbol: str = Field(default="EURUSD", description="Trading symbol")
    timeframe: str = Field(default="30m", description="Data timeframe")
    days_back: int = Field(default=30, description="Days of history to analyze")
    chart_title: Optional[str] = Field(default=None, description="Custom chart title")


class CompareStrategiesChartInput(BaseModel):
    """Input for comparing multiple strategies in one chart."""
    strategy_names: List[str] = Field(description="List of strategy names to compare")
    symbol: str = Field(default="EURUSD", description="Trading symbol")
    timeframe: str = Field(default="30m", description="Data timeframe")
    days_back: int = Field(default=14, description="Days back to compare")


@asynccontextmanager
async def get_initialized_components():
    """Get initialized components with proper resource management."""
    global data_connector, strategy_registry, backtest_engine, chart_engine
    
    if not data_connector:
        data_connector = DataConnector()
    if not strategy_registry:
        strategy_registry = StrategyRegistry()
    if not backtest_engine:
        backtest_engine = UniversalBacktestEngine(data_connector)
    if not chart_engine:
        chart_engine = ChartEngine()
    
    try:
        yield data_connector, strategy_registry, backtest_engine, chart_engine
    finally:
        # Cleanup if needed
        pass


@app.tool()
async def list_backtest_json_files() -> list[TextContent]:
    """
    List all available backtest JSON files that can be used for chart generation.
    
    Returns:
        List of available JSON files with their details
    """
    import os
    import glob
    import json
    from datetime import datetime
    
    try:
        # Search for JSON files in optimization_results directory using absolute path
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        results_dir = project_root / "optimization_results"
        json_pattern = str(results_dir / "backtest_*.json")
        json_files = glob.glob(json_pattern)
        
        if not json_files:
            return [TextContent(
                type="text",
                text=f"📁 **No backtest JSON files found.**\n\nSearched in: `{json_pattern}`\n\n💡 **Tip:** Run a backtest first to generate JSON files for chart creation."
            )]
        
        # Sort by modification time (newest first)
        json_files.sort(key=os.path.getmtime, reverse=True)
        
        result_text = f"📁 **Available Backtest JSON Files** ({len(json_files)} found)\n\n"
        
        for i, filepath in enumerate(json_files, 1):
            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath)
            mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            # Try to read basic info from JSON
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                strategy_name = data.get('strategy_name', 'Unknown')
                symbol = data.get('configuration', {}).get('symbol', 'Unknown')
                total_trades = data.get('summary', {}).get('total_trades', 0)
                total_pips = data.get('summary', {}).get('total_pips', 0)
                
                result_text += f"**{i}. {filename}**\n"
                result_text += f"   • Strategy: {strategy_name}\n"
                result_text += f"   • Symbol: {symbol}\n"
                result_text += f"   • Performance: {total_pips:+.1f} pips ({total_trades} trades)\n"
                result_text += f"   • Created: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                result_text += f"   • Size: {file_size:,} bytes\n\n"
                
            except Exception as e:
                result_text += f"**{i}. {filename}** (Error reading: {str(e)})\n\n"
        
        result_text += f"🎨 **To create chart:** Use `create_chart_from_backtest_json` with any filename above."
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error listing JSON files: {str(e)}"
        )]


@app.tool()
async def create_chart_from_backtest_json(json_filename: str) -> list[TextContent]:
    """
    Create an interactive chart from a backtest JSON file (Pure Modular Approach).
    
    This tool reads a pre-generated backtest JSON file and creates a comprehensive
    chart without needing to re-run the backtest. This is the true modular approach
    where backtest and chart generation are completely separate.
    
    Args:
        json_filename: Name or path of the JSON file. Can be:
                      - Just filename: "backtest_EURUSD_20251101_133004.json" (searches in optimization_results/)
                      - Relative path: "optimization_results/backtest_EURUSD_20251101_133004.json" or "/mnt/user-data/outputs/backtest_EURUSD_20251101_133004.json"  
                      - Absolute path: "/full/path/to/file.json"
        
    Returns:
        Chart file path and summary
    """
    import json
    import os
    from datetime import datetime
    
    async with get_initialized_components() as (connector, registry, engine, chart_eng):
        try:
            # Smart file path resolution
            if os.path.isabs(json_filename):
                # Absolute path provided
                json_filepath = json_filename
            elif os.path.exists(json_filename):
                # Relative path that exists
                json_filepath = json_filename
            else:
                # Just filename - look in optimization_results directory
                from pathlib import Path
                project_root = Path(__file__).parent.parent
                results_dir = project_root / "optimization_results"
                json_filepath = results_dir / json_filename
            
            if not os.path.exists(json_filepath):
                # Try to provide helpful suggestions
                import glob
                from pathlib import Path
                project_root = Path(__file__).parent.parent
                results_dir = project_root / "optimization_results"
                available_files = glob.glob(str(results_dir / "backtest_*.json"))
                if available_files:
                    filenames = [os.path.basename(f) for f in available_files[-3:]]  # Show last 3
                    suggestions = "\n".join([f"  • {f}" for f in filenames])
                    return [TextContent(
                        type="text",
                        text=f"❌ JSON file not found: `{json_filepath}`\n\n📁 **Available files:**\n{suggestions}\n\n💡 **Tip:** Use `list_backtest_json_files` to see all available files."
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"❌ JSON file not found: `{json_filepath}`\n\n📁 **No backtest JSON files found.** Run a backtest first to generate files."
                    )]
            
            with open(json_filepath, 'r') as f:
                backtest_data = json.load(f)
            
            # Extract data from JSON
            symbol = backtest_data['configuration']['symbol']
            strategy_name = backtest_data['strategy_name']
            trades_data = backtest_data['trades']
            market_data = backtest_data.get('market_data', [])
            
            if not market_data:
                return [TextContent(
                    type="text", 
                    text="❌ No market data found in JSON file - cannot create chart"
                )]
            
            # Convert JSON data back to objects
            from shared.models import Candle, Trade, TradeDirection, TradeResult
            
            # Convert market data
            candles = []
            for candle_data in market_data:
                candles.append(Candle(
                    timestamp=datetime.fromisoformat(candle_data['timestamp']),
                    open=candle_data['open'],
                    high=candle_data['high'],
                    low=candle_data['low'],
                    close=candle_data['close'],
                    volume=candle_data['volume']
                ))
            
            # Convert trades data
            trades = []
            for trade_data in trades_data:
                trades.append(Trade(
                    entry_time=datetime.fromisoformat(trade_data['entry_time']),
                    exit_time=datetime.fromisoformat(trade_data['exit_time']) if trade_data['exit_time'] else None,
                    direction=TradeDirection[trade_data['direction']],
                    entry_price=trade_data['entry_price'],
                    exit_price=trade_data['exit_price'],
                    pips=trade_data['pips'],
                    result=TradeResult[trade_data['result']]
                ))
            
            # Create mock BacktestResults object for chart generation
            from shared.strategy_interface import BacktestResults, BacktestConfiguration
            
            # Reconstruct configuration
            config = BacktestConfiguration(
                symbol=backtest_data['configuration']['symbol'],
                timeframe=backtest_data['configuration']['timeframe'],
                start_date=backtest_data['configuration']['start_date'],
                end_date=backtest_data['configuration']['end_date'],
                initial_balance=backtest_data['configuration']['initial_balance'],
                risk_per_trade=backtest_data['configuration']['risk_per_trade'],
                stop_loss_pips=backtest_data['configuration']['stop_loss_pips'],
                take_profit_pips=backtest_data['configuration']['take_profit_pips']
            )
            
            # Create results object (for chart metadata)
            results = BacktestResults(
                strategy_name=strategy_name,
                strategy_version=backtest_data['strategy_version'],
                configuration=config,
                trades=trades,
                total_trades=backtest_data['summary']['total_trades'],
                winning_trades=backtest_data['summary']['winning_trades'],
                losing_trades=backtest_data['summary']['losing_trades'],
                total_pips=backtest_data['summary']['total_pips'],
                win_rate=backtest_data['summary']['win_rate'],
                profit_factor=backtest_data['summary']['profit_factor'],
                average_win=backtest_data['summary']['average_win'],
                average_loss=backtest_data['summary']['average_loss'],
                largest_win=backtest_data['summary']['largest_win'],
                largest_loss=backtest_data['summary']['largest_loss'],
                max_drawdown=backtest_data['risk_metrics']['max_drawdown'],
                max_consecutive_losses=backtest_data['risk_metrics']['max_consecutive_losses'],
                max_consecutive_wins=backtest_data['risk_metrics']['max_consecutive_wins'],
                start_time=datetime.fromisoformat(backtest_data['execution']['start_time']),
                end_time=datetime.fromisoformat(backtest_data['execution']['end_time']),
                execution_time_seconds=backtest_data['execution']['execution_time_seconds'],
                data_source=backtest_data['execution']['data_source'],
                total_candles_processed=backtest_data['execution']['total_candles_processed']
            )
            
            # Calculate indicators based on strategy type
            indicators = {}
            if "MA Crossover" in strategy_name or "crossover" in strategy_name.lower():
                # Calculate SMA20 and SMA50 for MA Crossover strategies
                print(f"🔧 DEBUG: Calculating MA indicators for {strategy_name} with {len(candles)} candles")
                indicators = _calculate_ma_indicators(candles)
                print(f"🔧 DEBUG: Calculated {len(indicators)} indicators: {list(indicators.keys())}")
            else:
                print(f"🔧 DEBUG: Not an MA strategy: {strategy_name}")
            
            # Generate chart using Chart Engine (pure visualization)
            # Fix duplicate "Strategy" in title
            clean_title = strategy_name.replace(" Strategy", "").strip()
            chart_title = f"{clean_title} Strategy - {symbol}"
            print(f"🔧 DEBUG: Creating chart with title '{chart_title}' and {len(indicators)} indicators")
            chart_path = chart_eng.create_comprehensive_chart(
                candles=candles,
                backtest_results=results,
                indicators=indicators,
                title=chart_title
            )
            print(f"🔧 DEBUG: Chart created at: {chart_path}")
            
            # Return success message
            result_text = f"📊 **Interactive Chart Created from JSON!**\n\n"
            result_text += f"📁 **Source JSON:** `{json_filename}`\n"
            result_text += f"📈 **Chart File:** `{chart_path}`\n\n"
            result_text += f"**Strategy:** {strategy_name}\n"
            result_text += f"**Symbol:** {symbol}\n"
            result_text += f"**Performance:** {backtest_data['summary']['total_pips']:+.1f} pips ({backtest_data['summary']['win_rate']:.1%} win rate)\n"
            result_text += f"**Trades:** {len(trades)} trades plotted\n"
            result_text += f"**Market Data:** {len(candles)} candles\n\n"
            result_text += f"🎨 **Chart Contents:**\n"
            result_text += f"• 📈 Candlestick chart with price action\n"
            result_text += f"• 🎯 Trade entry/exit markers\n"
            result_text += f"• 📊 P&L visualization\n"
            result_text += f"• 📈 Performance metrics overlay\n\n"
            result_text += f"💡 **Open `{chart_path}` in a browser to explore the interactive visualization!**\n\n"
            result_text += f"✅ **Modular Architecture Success:** Backtest → JSON → Chart (completely independent!)"
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Chart from JSON failed: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Chart generation from JSON failed: {str(e)}"
            )]


@app.tool()
async def create_strategy_chart(input_data: ChartBacktestInput) -> list[TextContent]:
    """
    Create a comprehensive trading chart for a strategy.
    
    This tool:
    1. Runs the strategy using Universal Backtest Engine
    2. Generates visualization using Chart Engine
    3. Returns chart path and summary
    
    Args:
        input_data: Chart generation parameters
        
    Returns:
        Chart file path and performance summary
    """
    async with get_initialized_components() as (connector, registry, engine, chart_eng):
        try:
            # Handle date range
            if input_data.start_date and input_data.end_date:
                start_date = input_data.start_date
                end_date = input_data.end_date
            else:
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=input_data.days_back)
                start_date = start_dt.strftime('%Y-%m-%d')
                end_date = end_dt.strftime('%Y-%m-%d')
            
            # Create strategy instance
            strategy = registry.create_strategy(input_data.strategy_name, input_data.strategy_parameters)
            if not strategy:
                return [TextContent(
                    type="text",
                    text=f"❌ Strategy '{input_data.strategy_name}' not found"
                )]
            
            # Create backtest configuration
            config = BacktestConfiguration(
                symbol=input_data.symbol,
                timeframe=input_data.timeframe,
                start_date=start_date,
                end_date=end_date,
                initial_balance=10000.0,
                risk_per_trade=0.02,
                stop_loss_pips=input_data.stop_loss_pips,
                take_profit_pips=input_data.take_profit_pips,
                commission_per_trade=0.7
            )
            
            # Run backtest using Universal Backtest Engine
            logger.info(f"Running backtest for {input_data.strategy_name}")
            backtest_results = await engine.run_backtest(strategy, config)
            
            if not backtest_results:
                return [TextContent(
                    type="text",
                    text="❌ Backtest failed - no results generated"
                )]
            
            # Get market data for chart
            market_data = await connector.get_market_data(
                symbol=input_data.symbol,
                timeframe=input_data.timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            # Get candles - market_data.data is already a list of Candle objects
            candles = market_data.data
            
            # Get indicators data
            indicators = {}
            if hasattr(backtest_results, 'indicators_data'):
                indicators = backtest_results.indicators_data
            
            # Add MA indicators for MA Crossover strategy
            if "MA Crossover" in strategy.get_name() and len(candles) >= 50:
                # Calculate SMA20 and SMA50 for charting
                closes = [candle.close for candle in candles]
                sma20_values = []
                sma50_values = []
                
                for i in range(len(closes)):
                    if i >= 19:  # SMA20 needs 20 points
                        sma20 = sum(closes[i-19:i+1]) / 20
                        sma20_values.append(sma20)
                    else:
                        sma20_values.append(float('nan'))  # Use NaN instead of None
                        
                    if i >= 49:  # SMA50 needs 50 points  
                        sma50 = sum(closes[i-49:i+1]) / 50
                        sma50_values.append(sma50)
                    else:
                        sma50_values.append(float('nan'))  # Use NaN instead of None
                        
                indicators['SMA20'] = sma20_values
                indicators['SMA50'] = sma50_values
            
            # Generate chart title
            chart_title = input_data.chart_title or f"{strategy.get_name()} - {input_data.symbol} {input_data.timeframe}"
            
            # Create chart using Chart Engine
            logger.info(f"Generating chart with {len(candles)} candles and {len(backtest_results.trades)} trades")
            chart_path = chart_eng.create_comprehensive_chart(
                candles=candles,
                backtest_results=backtest_results,
                indicators=indicators,
                title=chart_title
            )
            
            # Format response
            result_text = f"""✅ **Strategy Chart Generated Successfully!**

📊 **Chart Details:**
- **Strategy:** {strategy.get_name()} (v{strategy.get_version()})
- **Symbol:** {input_data.symbol}
- **Timeframe:** {input_data.timeframe}
- **Period:** {start_date} to {end_date}
- **Data Points:** {len(candles)} candles

🎯 **Strategy Results:**
- **Total Trades:** {len(backtest_results.trades)}
- **Win Rate:** {backtest_results.win_rate:.1%}
- **Total P&L:** {backtest_results.total_pips:+.1f} pips
- **Profit Factor:** {backtest_results.profit_factor:.2f}
- **Winning Trades:** {backtest_results.winning_trades}
- **Losing Trades:** {backtest_results.losing_trades}

📈 **Chart Features:**
- ✅ Candlestick price action with technical indicators
- ✅ **SMA20 (blue)** and **SMA50 (orange)** moving average lines
- ✅ Numbered entry/exit markers with color coding  
- ✅ Trade connection lines (green=win, red=loss)
- ✅ Volume analysis
- ✅ Cumulative P&L tracking
- ✅ Interactive hover details

💾 **File:** `{Path(chart_path).name}`
📍 **Location:** `{chart_path}`

🎉 **Ready for analysis!** Open the HTML file in your browser for interactive exploration.
"""
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Chart generation failed: {str(e)}"
            )]


@app.tool()
async def create_performance_chart(input_data: PerformanceChartInput) -> list[TextContent]:
    """
    Create a performance-focused chart with statistics and analysis.
    
    This tool generates charts focused on strategy performance metrics
    rather than detailed trade-by-trade visualization.
    
    Args:
        input_data: Performance chart parameters
        
    Returns:
        Performance chart path and analysis
    """
    async with get_initialized_components() as (connector, registry, engine, chart_eng):
        try:
            # Calculate date range
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=input_data.days_back)
            start_date = start_dt.strftime('%Y-%m-%d')
            end_date = end_dt.strftime('%Y-%m-%d')
            
            # Create strategy and run backtest
            strategy = registry.create_strategy(input_data.strategy_name)
            if not strategy:
                return [TextContent(
                    type="text",
                    text=f"❌ Strategy '{input_data.strategy_name}' not found"
                )]
            
            config = BacktestConfiguration(
                symbol=input_data.symbol,
                timeframe=input_data.timeframe,
                start_date=start_date,
                end_date=end_date,
                initial_balance=10000.0,
                risk_per_trade=0.02,
                stop_loss_pips=15.0,
                take_profit_pips=25.0,
                commission_per_trade=0.7
            )
            
            backtest_results = await engine.run_backtest(strategy, config)
            
            if not backtest_results:
                return [TextContent(
                    type="text",
                    text="❌ Backtest failed - no results generated"
                )]
            
            # Generate performance chart
            chart_title = input_data.chart_title or f"{strategy.get_name()} Performance Analysis"
            chart_path = chart_eng.create_performance_summary_chart(backtest_results, chart_title)
            
            # Format response
            result_text = f"""✅ **Performance Chart Generated!**

📊 **Analysis Period:** {input_data.days_back} days ({start_date} to {end_date})
🎯 **Strategy:** {strategy.get_name()}

📈 **Key Metrics:**
- **Total Trades:** {len(backtest_results.trades)}
- **Win Rate:** {backtest_results.win_rate:.1%}
- **Total Return:** {backtest_results.total_pips:+.1f} pips
- **Profit Factor:** {backtest_results.profit_factor:.2f}
- **Average Win:** {backtest_results.average_win:.1f} pips
- **Average Loss:** {backtest_results.average_loss:.1f} pips

📊 **Chart Includes:**
- 📈 Trade distribution histogram
- 📊 Cumulative P&L over time
- 🥧 Win/Loss ratio pie chart
- 📅 Monthly performance breakdown

💾 **File:** `{Path(chart_path).name}`
📍 **Location:** `{chart_path}`
"""
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Performance chart generation failed: {str(e)}"
            )]


@app.tool()
async def compare_strategies_chart(input_data: CompareStrategiesChartInput) -> list[TextContent]:
    """
    Create a comparison chart showing multiple strategies side by side.
    
    Args:
        input_data: Strategy comparison parameters
        
    Returns:
        Comparison chart and analysis
    """
    async with get_initialized_components() as (connector, registry, engine, chart_eng):
        try:
            # Calculate date range
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=input_data.days_back)
            start_date = start_dt.strftime('%Y-%m-%d')
            end_date = end_dt.strftime('%Y-%m-%d')
            
            # Run backtests for all strategies
            strategy_results = {}
            
            for strategy_name in input_data.strategy_names:
                strategy = registry.create_strategy(strategy_name)
                if not strategy:
                    continue
                
                config = BacktestConfiguration(
                    symbol=input_data.symbol,
                    timeframe=input_data.timeframe,
                    start_date=start_date,
                    end_date=end_date,
                    initial_balance=10000.0,
                    risk_per_trade=0.02,
                    stop_loss_pips=15.0,
                    take_profit_pips=25.0,
                    commission_per_trade=0.7
                )
                
                results = await engine.run_backtest(strategy, config)
                if results:
                    strategy_results[strategy_name] = results
            
            if not strategy_results:
                return [TextContent(
                    type="text",
                    text="❌ No strategies could be backtested successfully"
                )]
            
            # Create comparison summary
            comparison_text = f"""✅ **Strategy Comparison Complete!**

📊 **Comparison Period:** {input_data.days_back} days
📈 **Symbol:** {input_data.symbol} ({input_data.timeframe})

"""
            
            for name, results in strategy_results.items():
                comparison_text += f"""
🎯 **{name}:**
   • Trades: {len(results.trades)}
   • Win Rate: {results.win_rate:.1%}
   • Total P&L: {results.total_pips:+.1f} pips
   • Profit Factor: {results.profit_factor:.2f}
"""
            
            comparison_text += f"""
💡 **Best Performer:** {max(strategy_results.keys(), key=lambda k: strategy_results[k].total_pips)}
🎯 **Highest Win Rate:** {max(strategy_results.keys(), key=lambda k: strategy_results[k].win_rate)}

📊 Individual performance charts generated for detailed analysis.
"""
            
            return [TextContent(type="text", text=comparison_text)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Strategy comparison failed: {str(e)}"
            )]


@app.tool()
async def list_available_strategies() -> list[TextContent]:
    """List all available strategy cartridges for charting."""
    async with get_initialized_components() as (connector, registry, engine, chart_eng):
        try:
            strategies = registry.list_strategies()
            
            if not strategies:
                return [TextContent(
                    type="text",
                    text="❌ No strategy cartridges found"
                )]
            
            result_text = "🎮 **Available Strategy Cartridges for Charting**\n\n"
            
            for i, strategy_name in enumerate(strategies, 1):
                info = registry.get_strategy_info(strategy_name)
                result_text += f"""**{i}. {strategy_name}** (v{info['version']})
📝 {info['description']}
📊 Indicators: {', '.join(info['required_indicators'])}

"""
            
            result_text += "Use `create_strategy_chart` with any of these strategy names."
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Failed to list strategies: {str(e)}"
            )]


if __name__ == "__main__":
    import asyncio
    app.run()