# Quick Start Guide - VWAP Trading Strategy MCP Server

## 5-Minute Setup

### Step 1: Install Dependencies

```bash
pip install mcp httpx pydantic --break-system-packages
```

### Step 2: Configure Claude Desktop

1. Find your config file location:
   - **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

2. Edit the file and add (or update `mcpServers` section):

```json
{
  "mcpServers": {
    "trading-strategy": {
      "command": "python",
      "args": ["/ABSOLUTE/PATH/TO/trading_strategy_mcp.py"]
    }
  }
}
```

**IMPORTANT:** Replace `/ABSOLUTE/PATH/TO/` with the actual full path!

Example paths:
- Mac: `"/Users/yourname/Downloads/trading_strategy_mcp.py"`
- Windows: `"C:\\Users\\yourname\\Downloads\\trading_strategy_mcp.py"`
- Linux: `"/home/yourname/trading_strategy_mcp.py"`

### Step 3: Restart Claude Desktop

Completely quit and restart Claude Desktop application.

### Step 4: Test It!

Open Claude Desktop and try these queries:

```
"What tools do you have available for trading?"
```

```
"Backtest the VWAP strategy for the past 30 days"
```

```
"What's the current trading signal?"
```

## Example Conversations

### Basic Backtest
**You:** "Test the VWAP strategy from October 1st to October 24th"

**Claude will:**
1. Call `backtest_vwap_strategy` tool
2. Show you win rate, total pips, trade history
3. Provide performance analysis

### Performance Analysis
**You:** "How has the strategy performed over the last week?"

**Claude will:**
1. Call `analyze_strategy_performance` with days=7
2. Show quick performance summary

### Current Signal
**You:** "Should I trade right now based on VWAP?"

**Claude will:**
1. Call `get_current_market_signal`
2. Show current price, VWAP, and signal

### Advanced Query
**You:** "Compare the strategy with 10 pip stops vs 20 pip stops over the last month"

**Claude will:**
1. Run multiple backtests with different parameters
2. Compare results
3. Recommend the better configuration

## Connecting Your Real Data

Currently using **mock data**. To connect your actual trading API:

1. **Open `trading_strategy_mcp.py`**

2. **Find these functions (around line 130-180):**
   - `_fetch_historical_data()`
   - `_fetch_current_price()`

3. **Replace with your API calls:**

```python
async def _fetch_historical_data(symbol: str, start_date: str, end_date: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://your-broker-api.com/historical",
            params={"symbol": symbol, "start": start_date, "end": end_date},
            headers={"Authorization": f"Bearer {YOUR_API_KEY}"}
        )
        return response.json()
```

4. **Save and restart Claude Desktop**

## Troubleshooting

### "Server not found" or "No tools available"

1. ✅ Check the path in config is **absolute** (starts with / or C:\)
2. ✅ Verify the file exists at that path
3. ✅ Restart Claude Desktop (quit completely, then reopen)
4. ✅ Check for typos in the config JSON

### "Import errors" or "Module not found"

```bash
# Install dependencies again
pip install mcp httpx pydantic --break-system-packages

# Or use a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install mcp httpx pydantic
```

Then update your config to use the venv Python:

```json
{
  "mcpServers": {
    "trading-strategy": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/trading_strategy_mcp.py"]
    }
  }
}
```

### Still having issues?

1. Test the server directly:
```bash
timeout 5s python trading_strategy_mcp.py 2>&1
```

If you see errors, those need to be fixed first.

2. Check Claude Desktop logs (varies by OS)

## What's Next?

Once it's working with mock data:

1. 🔌 **Connect your real data feed**
2. 📊 **Add more strategies** (moving averages, RSI, etc.)
3. ⚠️ **Add risk management tools**
4. 📈 **Add market condition filters**
5. 🤖 **Consider adding trade execution** (with proper safety!)

## Getting Help

- MCP Documentation: https://modelcontextprotocol.io
- Claude Documentation: https://docs.claude.com
- Review the code comments in `trading_strategy_mcp.py`

---

**Remember:** This is for analysis and backtesting only. Real trading involves risk. Always test thoroughly before putting real money at stake!
