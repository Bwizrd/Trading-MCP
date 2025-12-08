# System Architecture - VWAP Trading Strategy MCP Server

## Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           USER                                   │
│                  (Natural Language Queries)                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CLAUDE AI / MCP CLIENT                       │
│                                                                   │
│  • Understands user intent                                       │
│  • Calls appropriate MCP tools                                   │
│  • Formats and explains results                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ MCP Protocol (stdio/HTTP)
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              TRADING STRATEGY MCP SERVER                         │
│                  (trading_strategy_mcp.py)                       │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  TOOLS                                                   │   │
│  │  • backtest_vwap_strategy                               │   │
│  │  • get_current_market_signal                            │   │
│  │  • analyze_strategy_performance                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  STRATEGY LOGIC                                          │   │
│  │  • VWAP Calculation                                      │   │
│  │  • Signal Generation (BUY/SELL)                          │   │
│  │  • Trade Simulation                                      │   │
│  │  • Performance Analysis                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  DATA PROVIDERS                                          │   │
│  │  • _fetch_historical_data()  ← YOUR API HERE            │   │
│  │  • _fetch_current_price()    ← YOUR API HERE            │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   YOUR TRADING DATA API                          │
│                                                                   │
│  • Historical price data (OHLCV)                                 │
│  • Real-time quotes (bid/ask)                                    │
│  • Market data feed                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Example: Backtesting

```
1. USER: "Backtest the VWAP strategy for the past 30 days"
   ↓
2. CLAUDE: Understands intent, extracts parameters
   ↓
3. CLAUDE: Calls backtest_vwap_strategy tool
   Parameters: {
     start_date: "2024-09-24",
     end_date: "2024-10-24",
     symbol: "EUR/USD",
     stop_loss_pips: 10,
     take_profit_pips: 15
   }
   ↓
4. MCP SERVER: Receives tool call
   ↓
5. MCP SERVER: Calls _fetch_historical_data()
   ↓
6. DATA API: Returns 30 days of OHLCV data
   ↓
7. MCP SERVER: For each day:
   - Calculate VWAP
   - Generate signal (BUY/SELL)
   - Simulate trade execution
   - Track results
   ↓
8. MCP SERVER: Calculate statistics:
   - Win rate: 65%
   - Total pips: +125
   - Profit factor: 1.85
   - Trade list with results
   ↓
9. MCP SERVER: Format response (Markdown or JSON)
   ↓
10. CLAUDE: Receives formatted results
   ↓
11. CLAUDE: Presents results to user with insights:
    "The strategy performed well with a 65% win rate
     over the past 30 days, generating +125 pips profit.
     Here are the detailed results..."
   ↓
12. USER: Sees comprehensive analysis and trade history
```

## Component Details

### MCP Server Components

```
trading_strategy_mcp.py
│
├── CONFIGURATION
│   ├── Constants (CHARACTER_LIMIT, SIGNAL_TIME, etc.)
│   ├── Enums (ResponseFormat, TradeDirection, TradeResult)
│   └── Server initialization (FastMCP)
│
├── INPUT VALIDATION (Pydantic Models)
│   ├── BacktestInput
│   ├── CurrentMarketInput
│   └── StrategyPerformanceInput
│
├── DATA MODELS
│   └── Trade class (represents a single trade)
│
├── DATA PROVIDERS (Connect YOUR API here)
│   ├── _fetch_historical_data() ← Replace with your API
│   └── _fetch_current_price()   ← Replace with your API
│
├── STRATEGY LOGIC
│   ├── _calculate_vwap()
│   ├── _generate_signal()
│   ├── _calculate_stop_and_target()
│   ├── _simulate_trade_exit()
│   └── _calculate_performance_stats()
│
├── FORMATTING
│   ├── _format_backtest_markdown()
│   ├── _format_backtest_json()
│   └── _format_current_market_markdown()
│
├── ERROR HANDLING
│   └── _handle_error()
│
└── MCP TOOLS (Exposed to Claude)
    ├── @backtest_vwap_strategy
    ├── @get_current_market_signal
    └── @analyze_strategy_performance
```

## Integration Points

### 1. Claude Desktop Integration

```
Claude Desktop App
    ↓ reads
claude_desktop_config.json
    ↓ contains
{
  "mcpServers": {
    "trading-strategy": {
      "command": "python",
      "args": ["/path/to/trading_strategy_mcp.py"]
    }
  }
}
    ↓ launches
MCP Server Process (stdio transport)
    ↓ communicates via
JSON-RPC over stdin/stdout
```

### 2. Data API Integration (Your Part)

```
MCP Server
    ↓ calls
_fetch_historical_data(symbol, start_date, end_date)
    ↓ makes HTTP request to
YOUR_API_ENDPOINT/historical
    ↓ with parameters
{
  symbol: "EUR/USD",
  start: "2024-09-24",
  end: "2024-10-24",
  timeframe: "1D"
}
    ↓ returns
[
  {date, open, high, low, close, volume},
  {date, open, high, low, close, volume},
  ...
]
```

## Strategy Execution Flow

```
START: New trading day
    ↓
1. Fetch historical data (previous periods)
    ↓
2. Calculate VWAP
   VWAP = Σ(Price × Volume) / Σ(Volume)
    ↓
3. Check time = 8:30 AM
    ↓
4. Get current price
    ↓
5. Compare: Price vs VWAP
    ├─→ Price > VWAP → SELL signal
    └─→ Price < VWAP → BUY signal
    ↓
6. Calculate entry levels
    ├─→ Entry Price = Current Price
    ├─→ Stop Loss = Entry ± (stop_pips × pip_size)
    └─→ Take Profit = Entry ± (target_pips × pip_size)
    ↓
7. Create Trade object
    ↓
8. Simulate trade during the day
    ├─→ Check if Stop Loss hit → Close at loss
    ├─→ Check if Take Profit hit → Close at profit
    └─→ Neither hit → Close at EOD
    ↓
9. Record result (win/loss/breakeven)
    ↓
10. Update statistics
    ↓
END: Trade complete
```

## Conversation Flow Examples

### Example 1: Simple Backtest

```
User Input:
"Test the strategy for last month"
    ↓
Claude Processing:
- Understands: backtest request
- Extracts: time period = "last month"
- Calculates dates: 2024-09-24 to 2024-10-24
- Selects tool: backtest_vwap_strategy
    ↓
Tool Call:
backtest_vwap_strategy({
  start_date: "2024-09-24",
  end_date: "2024-10-24",
  symbol: "EUR/USD"  // default
})
    ↓
MCP Server Processing:
- Validates inputs ✓
- Fetches 30 days of data
- Runs 20 simulated trades
- Calculates statistics
- Formats as Markdown
    ↓
Returns to Claude:
"# Backtest Results
 Win Rate: 65%
 Total Pips: +125
 [detailed trade list]"
    ↓
Claude Response:
"I've backtested the VWAP strategy...
 The results show strong performance with
 a 65% win rate and +125 pips profit..."
```

### Example 2: Complex Query

```
User Input:
"Compare strategy with 10 pip vs 20 pip stops"
    ↓
Claude Processing:
- Understands: comparison needed
- Plans: run 2 backtests with different params
    ↓
Tool Call 1:
backtest_vwap_strategy({
  stop_loss_pips: 10,
  take_profit_pips: 15
})
    ↓
Tool Call 2:
backtest_vwap_strategy({
  stop_loss_pips: 20,
  take_profit_pips: 30
})
    ↓
Claude Analyzes:
- Compares win rates
- Compares total pips
- Compares profit factors
- Determines which is better
    ↓
Claude Response:
"I tested both configurations:

10 pip stops: 65% win rate, +125 pips
20 pip stops: 58% win rate, +140 pips

While 20 pip stops have lower win rate,
they generate more profit overall due to
larger wins. Recommendation: use 20 pip
stops for better risk/reward."
```

## Extension Architecture

Easy to add new features:

```
New Feature: RSI Strategy
    ↓
1. Create RSIInput Pydantic model
    ↓
2. Write RSI calculation function
    ↓
3. Add @mcp.tool decorator
    ↓
4. Implement backtest_rsi_strategy()
    ↓
5. Restart MCP server
    ↓
6. Claude can now use it!
```

## Deployment Scenarios

### Scenario 1: Personal Use (Current)
```
Your Computer
├── Claude Desktop App
└── MCP Server (local process)
    └── Your Data API (or mock data)
```

### Scenario 2: Team Use
```
Team Members' Computers
├── Claude Desktop App (each)
│   └── Connects to →
└── Shared MCP Server (internal network)
    └── Shared Data API
```

### Scenario 3: SaaS Product
```
Customer's Claude Desktop
    ↓ connects to
Your Cloud MCP Server (HTTP/SSE)
    ↓ connects to
Your Trading Data Service
    ↓ connects to
Multiple Broker APIs
```

## Security Architecture

```
┌─────────────────────────────────────┐
│  Environment Variables              │
│  (API Keys, Secrets)                │
└──────────────┬──────────────────────┘
               │ loaded at startup
               ▼
┌─────────────────────────────────────┐
│  MCP Server                          │
│  • Read-only operations              │
│  • Input validation (Pydantic)       │
│  • Error handling                    │
│  • Rate limiting (optional)          │
└──────────────┬──────────────────────┘
               │ authenticated requests
               ▼
┌─────────────────────────────────────┐
│  External APIs                       │
│  • HTTPS only                        │
│  • Token-based auth                  │
│  • Rate limited                      │
└─────────────────────────────────────┘
```

---

## Quick Reference: File Locations

```
project/
├── trading_strategy_mcp.py       # Main MCP server
├── requirements.txt              # Python dependencies
├── README.md                     # Full documentation
├── QUICKSTART.md                 # 5-min setup guide
├── PROJECT_SUMMARY.md            # This summary
└── claude_desktop_config.example.json  # Config template
```

## Quick Reference: Key Functions

| Function | Purpose | Location |
|----------|---------|----------|
| `backtest_vwap_strategy()` | Main backtesting tool | Line ~500 |
| `get_current_market_signal()` | Current signal tool | Line ~600 |
| `_fetch_historical_data()` | Data provider (REPLACE) | Line ~130 |
| `_fetch_current_price()` | Price provider (REPLACE) | Line ~175 |
| `_calculate_vwap()` | VWAP calculation | Line ~200 |
| `_generate_signal()` | Signal logic | Line ~220 |

---

**This architecture provides:**
✅ Clean separation of concerns
✅ Easy to test each component
✅ Simple to extend with new features
✅ Secure by design (read-only)
✅ Scalable architecture
