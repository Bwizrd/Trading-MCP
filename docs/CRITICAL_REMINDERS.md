# CRITICAL REMINDERS - READ BEFORE EVERY RESPONSE

## USER'S CORE REQUIREMENTS (DO NOT FORGET!)

### ARCHITECTURE MUST BE MODULAR:
```
DATA CONNECTOR → BACKTEST ENGINE → STRATEGY CARTRIDGE → JSON RESULTS → CHART ENGINE
```

### DATA CONNECTION RULES:
- **NO DIRECT DATABASE CONNECTIONS EVER**
- **ALL API CALLS GO THROUGH EXISTING DATA CONNECTORS**
- **API Server on port 8000 handles InfluxDB and cTrader**
- **Use existing `_fetch_historical_data()` function**

### CORRECT API ENDPOINTS (ALL GET REQUESTS):
- **InfluxDB Cache**: `http://localhost:8000/getDataFromDB?pair=189&timeframe=30m&bars=100`
- **Live Data Range**: `http://localhost:8000/getData?pair=220&timeframe=15m&range=-7d`
- **Date Range**: `http://localhost:8000/getDataByDates?pair=220&timeframe=15m&startDate=2025-10-20T00:00:00.000Z&endDate=2025-10-24T23:59:59.000Z`
- **Symbols**: `http://localhost:8000/symbols`
- **EURUSD = pair 189**
- **Dates MUST be ISO format with Z suffix**

### WORKING SYSTEM STATUS:
- ✅ API Server running on port 8000
- ✅ Data connectors work (influxdb.py, ctrader.py) 
- ✅ Claude Desktop connection stable
- ✅ Strategy cartridges exist (VWAP Momentum, VWAP Reversal)
- ✅ NEW DataConnector in shared/data_connector.py IS WORKING - returns 57 candles from InfluxDB
- ✅ Modular chart engine MCP server working
- ✅ Universal backtest engine MCP server available

### USER'S PAIN POINTS:
- **STOP BREAKING CLAUDE DESKTOP CONNECTION**
- **STOP CREATING NEW DATA ABSTRACTIONS**
- **USE EXISTING WORKING CODE**
- **NO MORE CIRCULAR REFACTORING**

### FINAL OUTPUT REQUIREMENTS:
1. **JSON FILE** with candles, entries, exits, parameters
2. **CHART** with candlesticks + trade markers
3. **CUMULATIVE P&L** chart below
4. **TRADE TABLE** below that
5. **TOTAL PIPS SUMMARY** at bottom

### APPROACH:
- **Phase 1**: Fix data connector to use existing `_fetch_historical_data()`
- **Phase 2**: Get universal backtest engine working with real data
- **Phase 3**: Add JSON export (non-breaking)
- **Phase 4**: Add chart generation from JSON

### WHAT NOT TO DO:
- ❌ Break Claude Desktop connection
- ❌ Create new data source abstractions
- ❌ Direct database connections
- ❌ Rewrite working code
- ❌ Go in circles
- ❌ NEVER USE `timeout` IN COMMANDS - DOES NOT WORK ON MAC

### CURRENT TASK:
✅ DataConnector in `shared/data_connector.py` IS WORKING - returns 57 candles from InfluxDB
🚀 NOW TEST THE UNIVERSAL BACKTEST ENGINE MCP SERVER WITH THE WORKING DATA CONNECTOR
📋 Focus on MCP server interface: mcp_servers/universal_backtest_engine.py