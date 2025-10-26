# cTrader API Integration Setup Guide

## What Changed

The MCP server now connects to **YOUR actual cTrader API** instead of using mock data! 🎉

## New File

Use **`trading_strategy_mcp_ctrader.py`** instead of the original `trading_strategy_mcp.py`

## Quick Setup

### 1. Set Environment Variables

The server needs to know how to connect to your cTrader API:

**Mac/Linux:**
```bash
export CTRADER_API_URL="http://localhost:8000"
export CTRADER_API_USERNAME="admin"
export CTRADER_API_PASSWORD="password"
```

**Windows (PowerShell):**
```powershell
$env:CTRADER_API_URL="http://localhost:8000"
$env:CTRADER_API_USERNAME="admin"
$env:CTRADER_API_PASSWORD="password"
```

**Windows (CMD):**
```cmd
set CTRADER_API_URL=http://localhost:8000
set CTRADER_API_USERNAME=admin
set CTRADER_API_PASSWORD=password
```

### 2. Update Claude Desktop Config

Edit your `claude_desktop_config.json`:

**Mac/Linux:**
```json
{
  "mcpServers": {
    "trading-strategy": {
      "command": "python",
      "args": ["/full/path/to/trading_strategy_mcp_ctrader.py"],
      "env": {
        "CTRADER_API_URL": "http://localhost:8000",
        "CTRADER_API_USERNAME": "admin",
        "CTRADER_API_PASSWORD": "password"
      }
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "trading-strategy": {
      "command": "python",
      "args": ["C:\\full\\path\\to\\trading_strategy_mcp_ctrader.py"],
      "env": {
        "CTRADER_API_URL": "http://localhost:8000",
        "CTRADER_API_USERNAME": "admin",
        "CTRADER_API_PASSWORD": "password"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

Completely quit and restart Claude Desktop.

### 4. Test It!

```
"Backtest the VWAP strategy for EURUSD on 30m timeframe for the past 7 days"
```

```
"What's the current VWAP signal for GBPAUD?"
```

---

## Supported Symbols

The server is pre-configured with these symbols (from your API):

| Symbol | ID | Name |
|--------|----|----- |
| EURUSD | 1 | Euro vs US Dollar |
| GBPUSD | 14 | British Pound vs US Dollar |
| USDJPY | 18 | US Dollar vs Japanese Yen |
| AUDUSD | 2 | Australian Dollar vs US Dollar |
| USDCAD | 17 | US Dollar vs Canadian Dollar |
| GBPAUD | 189 | British Pound vs Australian Dollar |
| EURJPY | 7 | Euro vs Japanese Yen |
| GBPJPY | 16 | British Pound vs Japanese Yen |

**To add more symbols:**

1. Find the symbol ID from your API: `GET /symbols`
2. Add to `SYMBOL_IDS` dictionary in the code (line ~29):

```python
SYMBOL_IDS = {
    "EURUSD": 1,
    "GBPUSD": 14,
    "YOURNEWSYMBOL": 123,  # Add here
    # ...
}
```

---

## Supported Timeframes

All cTrader timeframes are supported:
- `1m` - 1 minute
- `5m` - 5 minutes
- `15m` - 15 minutes
- `30m` - 30 minutes
- `1h` - 1 hour
- `4h` - 4 hours
- `1d` - 1 day

---

## How It Works

### API Endpoints Used

**For Backtesting:**
- `GET /getDataByDates` - Fetches historical candle data

**For Current Signals:**
- `GET /getLatestCandle` - Gets current live or last closed candle

### Authentication

Uses HTTP Basic Authentication with credentials from environment variables.

### Data Flow

```
Claude Request
    ↓
MCP Server (trading_strategy_mcp_ctrader.py)
    ↓
cTrader API (http://localhost:8000)
    ↓
Real Market Data
    ↓
Strategy Analysis
    ↓
Results back to Claude
```

---

## Example Queries

### Backtest with Real Data

**You:** "Backtest the VWAP strategy for EURUSD on 30m timeframe from October 1st to October 24th"

**Claude will:**
1. Fetch real historical data from your cTrader API
2. Calculate VWAP for each trading day
3. Simulate trades based on the strategy
4. Return performance statistics

### Current Market Signal

**You:** "What's the current VWAP signal for GBPAUD on 1h timeframe?"

**Claude will:**
1. Fetch current live candle from cTrader
2. Calculate VWAP from recent data
3. Determine BUY or SELL signal
4. Show current market conditions

### Performance Analysis

**You:** "Analyze GBPUSD performance on 15m timeframe for the last 14 days"

**Claude will:**
1. Calculate date range (last 14 days)
2. Fetch historical data
3. Run backtest
4. Show win rate, pips, and trade history

---

## Advanced Configuration

### Different API URL

If your cTrader API is on a different machine or port:

```json
"env": {
  "CTRADER_API_URL": "http://192.168.1.100:8000"
}
```

### Different Credentials

If you changed the default admin credentials:

```json
"env": {
  "CTRADER_API_USERNAME": "your_username",
  "CTRADER_API_PASSWORD": "your_password"
}
```

---

## Troubleshooting

### "Cannot connect to cTrader API"

**Check:**
1. Is your cTrader API server running? (`http://localhost:8000/health`)
2. Is the URL correct in environment variables?
3. Can you access the API directly in a browser?

**Test API directly:**
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "ok",
  "port": 8000,
  "timestamp": "..."
}
```

### "API authentication failed"

**Check:**
1. Are username and password correct?
2. Did you restart Claude Desktop after changing config?

**Test authentication:**
```bash
curl -u admin:password http://localhost:8000/status
```

### "Unknown symbol"

**Check:**
1. Is the symbol name correct? (Use uppercase: EURUSD, not eurusd)
2. Is the symbol ID in the `SYMBOL_IDS` dictionary?
3. Check available symbols: `GET /symbols`

**Add missing symbol:**
1. Find symbol ID from `/symbols` endpoint
2. Add to `SYMBOL_IDS` in line ~29 of the code

### "No trading data found"

**Check:**
1. Does your cTrader API have data for that date range?
2. Is the timeframe supported for that symbol?
3. Try a shorter date range

**Test data availability:**
```bash
curl "http://localhost:8000/countDataFromDB?pair=1&timeframe=30m"
```

---

## What's Different from Mock Version

| Feature | Mock Version | cTrader Version |
|---------|-------------|-----------------|
| Data Source | Simulated data | Real cTrader API |
| Symbols | Any string | Predefined symbol IDs |
| Timeframes | Default 30m | All cTrader timeframes |
| Authentication | None | HTTP Basic Auth |
| Live Data | No | Yes (via /getLatestCandle) |
| Historical Accuracy | Fake patterns | Real market data |

---

## Performance Notes

### Data Fetching

- Historical data fetched per backtest
- Not cached (always fresh data)
- Large date ranges may take longer

### Rate Limiting

If you see rate limit errors, reduce:
- Date range size
- Number of concurrent requests
- Query frequency

---

## Security Best Practices

### 1. Environment Variables

Always use environment variables for credentials, never hardcode:

```python
# Good ✅
API_USERNAME = os.environ.get("CTRADER_API_USERNAME")

# Bad ❌
API_USERNAME = "admin"  # Don't do this!
```

### 2. Config File Security

Your `claude_desktop_config.json` contains credentials. On Unix systems:

```bash
chmod 600 ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### 3. Local Network Only

Your cTrader API should only be accessible locally:
- Use `localhost` or `127.0.0.1`
- Don't expose to the internet
- Use firewall rules if needed

---

## Next Steps

### 1. Test Basic Functionality
- Backtest a simple date range
- Check current signals
- Verify data is real

### 2. Validate Results
- Compare backtest results with manual analysis
- Verify VWAP calculations
- Check signal accuracy

### 3. Customize Strategy
- Adjust stop loss/take profit
- Add more symbols
- Experiment with timeframes

### 4. Extend Functionality
- Add more technical indicators
- Create multi-timeframe analysis
- Add risk management tools

---

## Support

### cTrader API Issues
- Check your cTrader API logs
- Verify endpoints with curl/Postman
- Check authentication status: `GET /status`

### MCP Server Issues
- Check Claude Desktop logs
- Test Python syntax: `python -m py_compile trading_strategy_mcp_ctrader.py`
- Verify environment variables are set

### Strategy Issues
- Review backtest results
- Compare with manual calculations
- Test on different timeframes/symbols

---

## Quick Reference

### Test API Connection
```bash
curl http://localhost:8000/health
```

### Test Authentication
```bash
curl -u admin:password http://localhost:8000/status
```

### Get Available Symbols
```bash
curl http://localhost:8000/symbols
```

### Get Historical Data
```bash
curl "http://localhost:8000/getDataByDates?pair=1&timeframe=30m&startDate=1696118400000&endDate=1698710400000"
```

### Get Current Candle
```bash
curl "http://localhost:8000/getLatestCandle?pair=189&timeframe=30m"
```

---

**You're now connected to REAL market data! 🎉📈**

Start by testing with a small date range, then expand as you validate the results!
