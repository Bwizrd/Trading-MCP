# 🎯 Using Your New Data Connectors

## ✅ **Now You Can Do Both!**

### 📊 **Strategy-Focused Requests** (like before):
```
"Backtest EURUSD from October 20-24th and export to CSV and create the chart with the trades"
```
- Uses the **VWAP Strategy** server
- Includes full strategy analysis, charts, and CSV export

### 📈 **Pure Data Requests** (NEW!):
```
"Get me the OHLCV values for GBPUSD for the past 7 days on the daily timeframe from the DB"
```
- Uses the **InfluxDB Connector** or **cTrader Connector**
- Returns raw market data without strategy analysis

## 🛠️ **Available Data Connector Tools:**

### InfluxDB Connector (`influxdb-connector`)
- **Tool:** `fetch_market_data`
- **Features:** 
  - Fast InfluxDB retrieval first
  - Falls back to cTrader API if needed
  - Raw OHLCV data output

### cTrader Connector (`ctrader-connector`)  
- **Tool:** `fetch_market_data`
- **Features:**
  - Direct cTrader API access
  - Raw OHLCV data output
  - Multiple timeframes supported

## 📋 **Example Requests You Can Now Make:**

### Raw Data Requests:
- "Get EURUSD hourly data for the last 3 days"
- "Fetch GBPUSD daily candles for the past month"
- "Show me USDJPY 15-minute data from the database"
- "Get the latest week of AUDUSD data in JSON format"

### Strategy Requests (still work as before):
- "Backtest VWAP strategy on GBPUSD this week"
- "Analyze EURUSD performance with VWAP signals"
- "Create comprehensive chart with trades for USDJPY"

## 🎯 **The Beauty of Separation:**

1. **Data Connectors** = Pure data fetching (reusable by any strategy)
2. **Strategy Servers** = Trading logic + analysis
3. **Chart Servers** = Visualization

Now you can ask for raw data from any connector, and it will work independently! 🚀

## 🔧 **Parameters for Data Fetching:**

- **symbol**: Trading pair (e.g., "GBPUSD", "EURUSD")
- **days**: Number of days (1-90, default: 7)  
- **timeframe**: "1m", "5m", "15m", "30m", "1h", "4h", "1d"
- **format**: "markdown" (default) or "json"

Your request should work perfectly now! 🎉