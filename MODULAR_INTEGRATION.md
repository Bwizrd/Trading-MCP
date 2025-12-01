# Modular Cartridge System Integration Guide

## Overview

This guide explains how to integrate the new modular cartridge-based trading system alongside the existing working MCP servers. The goal is to **ADD** the modular system as additional tools, not REPLACE the working system.

## Architecture Overview

### Current Working System
- **trading_charts_mcp.py** - Chart generation with hardcoded VWAP strategy
- **vwap_strategy/core.py** - Traditional VWAP strategy implementation  
- **ctrader.py** - cTrader data connector
- **influxdb.py** - InfluxDB data connector

### New Modular System
- **universal_backtest_engine.py** - Strategy-agnostic backtest engine
- **modular_chart_engine.py** - Visualization engine that uses backtest results
- **Strategy Cartridges** - Pluggable strategy implementations

## System Flow

### Traditional Flow (Working)
```
User Request → MCP Server → Hardcoded Strategy Logic → Chart Generation
```

### New Modular Flow (Additional)
```
User Request → Universal Backtest Engine → Strategy Cartridge → JSON Export → Chart Engine → Visualization
```

## Integration Steps

### 1. Verify Current System Works
```bash
# Test that original tools are available in Claude Desktop
# Should see: VWAP strategy tools, chart generation, data connectors
```

### 2. Add New MCP Servers to Claude Desktop

Edit your Claude Desktop config at:
`~/Library/Application Support/Claude/claude_desktop_config.json`

Add these new servers to the `mcpServers` section:

```json
{
  "mcpServers": {
    "trading-charts": {
      "command": "python",
      "args": ["/Users/paul/Sites/PythonProjects/Trading-MCP/mcp_servers/charts/trading_charts_mcp.py"]
    },
    "vwap-strategy": {
      "command": "python", 
      "args": ["/Users/paul/Sites/PythonProjects/Trading-MCP/mcp_servers/strategies/vwap_strategy/core.py"]
    },
    "ctrader-connector": {
      "command": "python",
      "args": ["/Users/paul/Sites/PythonProjects/Trading-MCP/mcp_servers/data_connectors/ctrader.py"]
    },
    "influxdb-connector": {
      "command": "python",
      "args": ["/Users/paul/Sites/PythonProjects/Trading-MCP/mcp_servers/data_connectors/influxdb.py"]
    },
    "universal-backtest-engine": {
      "command": "python",
      "args": ["/Users/paul/Sites/PythonProjects/Trading-MCP/mcp_servers/universal_backtest_engine.py"]
    },
    "modular-chart-engine": {
      "command": "python",
      "args": ["/Users/paul/Sites/PythonProjects/Trading-MCP/mcp_servers/modular_chart_engine.py"]
    }
  }
}
```

### 3. Restart Claude Desktop

After adding the servers:
1. Quit Claude Desktop completely
2. Relaunch Claude Desktop
3. Check available tools - you should now see both old and new tools

### 4. Test Integration

#### Test Original Tools (Should Still Work)
- VWAP strategy analysis
- Chart generation  
- Data connector functionality

#### Test New Modular Tools
- List available strategy cartridges
- Run universal backtest engine
- Generate modular charts

## Benefits of This Approach

### Preserved Functionality
- ✅ Original working tools remain untouched
- ✅ No risk of breaking existing workflows
- ✅ Immediate fallback if modular system has issues

### Enhanced Capabilities  
- 🆕 Strategy cartridge system for easy strategy development
- 🆕 JSON export workflow for data portability
- 🆕 Modular architecture for better separation of concerns
- 🆕 Universal backtest engine that works with any strategy

## Usage Patterns

### For Existing Workflows
Continue using the original VWAP tools for proven, stable analysis.

### For New Development
Use the modular system for:
- Testing new strategies
- Comparative analysis  
- Advanced backtesting scenarios
- JSON-based data workflows

## Troubleshooting

### If New Tools Don't Appear
1. Check Claude Desktop config syntax is valid JSON
2. Verify file paths are correct and absolute
3. Check that Python can import all required modules
4. Restart Claude Desktop completely

### If Original Tools Stop Working
1. This integration should NOT affect original tools
2. If they break, remove the new server entries from config
3. The original tools were working before integration

### Import Errors
The modular system requires:
- All files in `shared/` directory
- Compatible `data_connector.py` (already created)  
- Strategy cartridge files

## Next Steps

1. **Immediate**: Add servers to Claude Desktop config and test
2. **Short-term**: Develop additional strategy cartridges
3. **Long-term**: Consider migrating proven workflows to modular system

## File Status

### Extracted and Ready
- ✅ `universal_backtest_engine.py` - Cleaned and ready
- ✅ `modular_chart_engine.py` - Cleaned and ready  
- ✅ `shared/data_connector.py` - Created for compatibility

### In Git Stash (Available for extraction)
- `shared/strategy_registry.py`
- `shared/backtest_engine.py`
- `shared/strategy_interface.py`
- `shared/chart_engine.py`
- Various strategy cartridge files

The integration preserves your working system while adding powerful new capabilities!