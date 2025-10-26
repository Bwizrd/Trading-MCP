# 🔄 Migration Guide: Updating Claude Desktop Configuration

## ⚠️ Action Required

Your Claude Desktop configuration needs to be updated to use the new file paths after the folder restructure.

## 📍 Before (Old Paths)
```json
{
  "mcpServers": {
    "trading-strategy": {
      "command": "python",
      "args": ["/path/to/trading_strategy_mcp.py"]
    },
    "trading-charts": {
      "command": "python",
      "args": ["/path/to/trading_charts_mcp.py"]
    }
  }
}
```

## ✅ After (New Paths)
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
    }
  }
}
```

## 📋 Steps to Update:

1. **Locate your Claude Desktop config file:**
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

2. **Update the file paths** in your config to match the new structure above

3. **Restart Claude Desktop** completely

## 🎯 What Changed:

### File Movements:
- `trading_charts_mcp.py` → `mcp_servers/charts/trading_charts_mcp.py`
- `trading_strategy_mcp.py` → `mcp_servers/strategies/vwap_strategy/core.py`
- `trading_strategy_mcp_ctrader.py` → `mcp_servers/data_connectors/ctrader.py`
- `trading_strategy_mcp_influxdb.py` → `mcp_servers/data_connectors/influxdb.py`

### New Benefits:
- **Data connectors are now separate** - can be used by any strategy
- **Each strategy has its own folder** - easier to organize
- **Shared code eliminates duplication** - more maintainable

## ✅ Verification:

After updating your config and restarting Claude Desktop:

1. **Check that Claude can see the MCP servers** in the interface
2. **Try using a chart generation tool** to verify it works
3. **Try using a strategy tool** to verify it works

## 🔧 Troubleshooting:

If servers don't appear in Claude Desktop:

1. **Check file paths are absolute** (not relative)
2. **Verify Python can find the files** by running them directly
3. **Check Claude Desktop logs** for any error messages
4. **Ensure you restarted Claude Desktop** completely

The functionality should work exactly the same as before - just with better organization! 🚀