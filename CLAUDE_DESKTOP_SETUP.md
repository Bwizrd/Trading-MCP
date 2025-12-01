# 🎯 Claude Desktop Integration Guide

## Step 1: Copy Configuration File

1. **Copy the configuration** to your Claude Desktop config directory:
   ```bash
   cp /Users/paul/Sites/PythonProjects/Trading-MCP/claude_desktop_config_trading_mcp.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Alternative: Manual Setup**
   - Open Finder and press `Cmd+Shift+G`
   - Go to: `~/Library/Application Support/Claude/`
   - Create or edit `claude_desktop_config.json`
   - Copy the contents from `claude_desktop_config_trading_mcp.json`

## Step 2: Restart Claude Desktop

- **Completely quit** Claude Desktop (Cmd+Q)
- **Restart** Claude Desktop application
- Look for the 🔌 MCP connection indicator

## Step 3: Test the Integration

Once Claude Desktop is restarted, you can test the trading MCP server:

### Available Tools:
1. **`list_strategy_cartridges`** - See all available trading strategies
2. **`get_strategy_info`** - Get detailed info about a specific strategy  
3. **`run_strategy_backtest`** - Run backtests with full configuration
4. **`compare_strategies`** - Compare multiple strategies side-by-side
5. **`test_data_connectivity`** - Test connection to data sources

### Example Commands:
```
Please list all available strategy cartridges
```

```
Run a backtest using the MA Crossover Strategy on EURUSD with 15M timeframe for the last 30 days
```

```
Compare all strategies on GBPUSD for the last 7 days
```

## Step 4: Verify Connection

If successful, you should see:
- ✅ MCP connection indicator in Claude Desktop
- 🎮 Strategy cartridge tools available
- 📊 Backtest and charting capabilities

## Troubleshooting

### If Connection Fails:
1. Check file paths are absolute (not relative)
2. Ensure Python environment is activated
3. Verify no JSON syntax errors in config file
4. Check Claude Desktop logs for errors

### Config File Location:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

## Features Available in Claude Desktop:

### 🎮 **Strategy Cartridge System**
- Universal backtest engine with swappable strategies
- MA Crossover, VWAP, RSI, and custom strategies
- Signal-driven execution with 1-minute precision

### 📊 **Professional Analytics**
- Automatic chart generation with interactive Plotly
- JSON export of all backtest data
- Performance metrics and risk analysis

### ⚡ **Signal-Driven Architecture** 
- 96.8% data reduction vs traditional backtesting
- Sub-3-second execution for monthly backtests
- On-demand 1M execution data fetching

### 🎯 **Claude Desktop Integration**
- Natural language strategy requests
- Automatic backtest → chart → analysis workflow
- Professional-grade results accessible via conversation

Ready to test! 🚀