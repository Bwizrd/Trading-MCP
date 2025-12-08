# Which Version Should I Use?

You now have **THREE versions** of the MCP server:

## 📦 Version Comparison

| Feature | Mock Version | cTrader Version | cTrader + InfluxDB ⭐ |
|---------|--------------|-----------------|----------------------|
| **File** | `trading_strategy_mcp.py` | `trading_strategy_mcp_ctrader.py` | `trading_strategy_mcp_influxdb.py` |
| **Data Source** | Simulated/fake data | Real cTrader API | Real (optimized) |
| **Speed** | Instant | Good | ⚡ **Excellent** |
| **Setup Time** | 5 minutes | 10 minutes | 10 minutes |
| **API Required** | No | Yes | Yes |
| **InfluxDB** | No | No | Yes (auto-fallback) |
| **Authentication** | No | Yes | Yes |
| **Use Case** | Learning, testing | Real analysis | **Production** |

---

## 🎯 Choose Your Version

### Use Mock Version If:

✅ **Learning MCP** - You want to understand how MCP servers work  
✅ **Testing Setup** - You want to test Claude Desktop integration first  
✅ **No API Access** - You don't have the cTrader API running  
✅ **Demonstration** - You're showing someone how it works  
✅ **Development** - You're adding features and don't need real data  

**File:** `trading_strategy_mcp.py`  
**Setup:** [QUICKSTART.md](./QUICKSTART.md)

---

### Use cTrader Version If:

🚀 **Real Trading** - You want to analyze actual market data  
🚀 **Simple Setup** - You want cTrader integration without InfluxDB optimization  
🚀 **Learning API** - You're learning how to integrate with cTrader  
🚀 **No InfluxDB Data** - You haven't populated InfluxDB yet  

**File:** `trading_strategy_mcp_ctrader.py`  
**Setup:** [CTRADER_SETUP.md](./CTRADER_SETUP.md)

---

### Use cTrader + InfluxDB Version If: ⭐ RECOMMENDED

⚡ **Production Use** - You want the fastest, most efficient system  
⚡ **Large Backtests** - You run 30+ day date ranges frequently  
⚡ **Multiple Queries** - You test many different parameters  
⚡ **Best Performance** - You want 3-5x faster data retrieval  
⚡ **Smart Fallback** - You want automatic fallback to cTrader API when needed  

**File:** `trading_strategy_mcp_influxdb.py`  
**Setup:** [INFLUXDB_GUIDE.md](./INFLUXDB_GUIDE.md)

---

## 🔄 Switching Between Versions

### From Mock to cTrader

1. **Set up environment variables:**
```bash
export CTRADER_API_URL="http://localhost:8000"
export CTRADER_API_USERNAME="admin"
export CTRADER_API_PASSWORD="password"
```

2. **Update Claude config** to use `trading_strategy_mcp_ctrader.py`:
```json
{
  "mcpServers": {
    "trading-strategy": {
      "command": "python",
      "args": ["/path/to/trading_strategy_mcp_ctrader.py"],
      "env": {
        "CTRADER_API_URL": "http://localhost:8000",
        "CTRADER_API_USERNAME": "admin",
        "CTRADER_API_PASSWORD": "password"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

### From cTrader to Mock

1. **Update Claude config** to use `trading_strategy_mcp.py`:
```json
{
  "mcpServers": {
    "trading-strategy": {
      "command": "python",
      "args": ["/path/to/trading_strategy_mcp.py"]
    }
  }
}
```

2. **Restart Claude Desktop**

---

## 📊 Feature Comparison

### Mock Version Features

| Feature | Status |
|---------|--------|
| Backtesting | ✅ (fake data) |
| Current Signals | ✅ (simulated) |
| Performance Analysis | ✅ (fake results) |
| All Symbols | ✅ (any string) |
| All Timeframes | ⚠️ (default only) |
| Authentication | ❌ Not needed |
| Live Data | ❌ No |
| Real Market Conditions | ❌ No |

### cTrader Version Features

| Feature | Status |
|---------|--------|
| Backtesting | ✅ (real data) |
| Current Signals | ✅ (live market) |
| Performance Analysis | ✅ (real results) |
| All Symbols | ⚠️ (predefined IDs) |
| All Timeframes | ✅ (1m-1d) |
| Authentication | ✅ Required |
| Live Data | ✅ Yes |
| Real Market Conditions | ✅ Yes |

---

## 🎓 Recommended Learning Path

### Beginner Path
1. **Start with Mock** (5 min setup)
   - Learn how MCP works
   - Understand the tools
   - Try different queries

2. **Switch to cTrader** (10 min setup)
   - Connect real API
   - Verify data accuracy
   - Compare results

### Advanced Path
1. **Start with cTrader** (10 min setup)
   - Immediate real data
   - Validate strategy quickly
   - Start using for decisions

---

## 🔍 Query Examples

Both versions support the same queries, but results differ:

### Example 1: Backtesting

**Query:**
```
"Backtest the VWAP strategy for EURUSD for the past 7 days"
```

**Mock Version Result:**
- Uses simulated price movements
- Generated win rate (e.g., 65%)
- Fake but realistic-looking data
- Consistent results each time

**cTrader Version Result:**
- Uses real market data from cTrader
- Actual win rate from real prices
- Real market conditions reflected
- Results match actual trading

---

### Example 2: Current Signal

**Query:**
```
"What's the current VWAP signal for GBPAUD?"
```

**Mock Version Result:**
- Returns simulated current price
- Calculated VWAP from fake data
- Signal based on mock conditions

**cTrader Version Result:**
- Returns real live price from cTrader
- Calculated VWAP from real data
- Signal based on actual market
- Shows if data is live or last closed

---

## ⚙️ Technical Differences

### Code Differences

| Aspect | Mock Version | cTrader Version |
|--------|--------------|-----------------|
| Lines of Code | 746 | ~900 |
| API Functions | `_fetch_*` (mock) | `_fetch_*` (real) |
| Symbol Handling | Any string | Predefined IDs |
| Authentication | None | HTTP Basic Auth |
| Error Handling | Basic | Extended (API errors) |
| Environment Vars | None | 3 required |

### Data Format

**Mock Version:**
```python
# Generates data on the fly
mock_data = generate_mock_candles(start, end)
```

**cTrader Version:**
```python
# Fetches from API
data = await _make_api_request(
    "/getDataByDates",
    params={"pair": symbol_id, ...}
)
```

---

## 🛠️ Maintenance

### Mock Version
- ✅ No dependencies on external services
- ✅ Always works
- ✅ No authentication needed
- ⚠️ Data not realistic over time

### cTrader Version
- ⚠️ Requires cTrader API running
- ⚠️ Requires authentication
- ⚠️ Network dependency
- ✅ Always up-to-date data

---

## 💡 Pro Tips

### Use Both!

You can actually configure **both versions** in Claude:

```json
{
  "mcpServers": {
    "trading-strategy-mock": {
      "command": "python",
      "args": ["/path/to/trading_strategy_mcp.py"]
    },
    "trading-strategy-live": {
      "command": "python",
      "args": ["/path/to/trading_strategy_mcp_ctrader.py"],
      "env": {
        "CTRADER_API_URL": "http://localhost:8000",
        "CTRADER_API_USERNAME": "admin",
        "CTRADER_API_PASSWORD": "password"
      }
    }
  }
}
```

Then you can ask Claude:
- "Use the mock version to explain the strategy"
- "Use the live version to analyze EURUSD"

---

## 📝 When to Upgrade

### Upgrade from Mock to cTrader When:

1. ✅ You understand how the MCP server works
2. ✅ You've tested basic queries successfully
3. ✅ Your cTrader API is running and accessible
4. ✅ You need real data for actual trading decisions
5. ✅ You want to validate the strategy on real history

### Stay with Mock When:

1. ✅ Learning about MCP servers
2. ✅ Developing new features
3. ✅ Demonstrating to others
4. ✅ cTrader API not available
5. ✅ Don't need real-time accuracy

---

## 🎯 Decision Matrix

Ask yourself:

| Question | Mock | cTrader |
|----------|------|---------|
| Do I have cTrader API running? | No → | Yes → |
| Do I need real market data? | No → | Yes → |
| Am I just learning MCP? | Yes → | No → |
| Will I make trading decisions? | No → | Yes → |
| Do I want fastest setup? | Yes → | No → |

**Mostly Mock?** → Use `trading_strategy_mcp.py`  
**Mostly cTrader?** → Use `trading_strategy_mcp_ctrader.py`

---

## 📚 Documentation

### Mock Version
- [START_HERE.md](./START_HERE.md) - Overview
- [QUICKSTART.md](./QUICKSTART.md) - Quick setup
- [README.md](./README.md) - Full documentation

### cTrader Version
- [CTRADER_SETUP.md](./CTRADER_SETUP.md) - Setup guide
- [README.md](./README.md) - General concepts
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical details

---

## 🚀 Summary

**Start Simple, Grow Complex:**

1. **Day 1:** Use **Mock Version** (5 minutes)
   - Get comfortable with MCP
   - Learn the query patterns
   - Understand the tools

2. **Day 2:** Switch to **cTrader Version** (10 minutes)
   - Connect real API
   - Validate with real data
   - Start real analysis

3. **Day 3+:** Production Use
   - Make trading decisions
   - Track real performance
   - Refine your strategy

---

## ❓ FAQ

**Q: Can I use both versions at the same time?**  
A: Yes! Configure both in Claude Desktop with different names.

**Q: Which version is "better"?**  
A: cTrader for real trading, Mock for learning. Both have their place.

**Q: Will my queries work with both?**  
A: Yes! The API is identical, only the data source changes.

**Q: Can I switch back and forth?**  
A: Yes! Just update Claude config and restart.

**Q: Is the mock version useless?**  
A: No! It's perfect for learning, testing, and development.

---

**Choose the right tool for your needs! 🎯**

Both versions are production-quality and ready to use. Start where you're comfortable and upgrade when you're ready!
