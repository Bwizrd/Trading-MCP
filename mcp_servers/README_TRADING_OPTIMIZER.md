# Trading Optimizer MCP Server

## Overview

The Trading Optimizer MCP Server is a Model Context Protocol server that analyzes closed trading positions and optimizes exit parameters (Stop Loss, Take Profit, Trailing Stops) using tick-level precision data.

## Purpose

Traditional backtesting uses historical candles, but real trades execute at tick-level precision. This optimizer:

1. **Fetches your actual closed positions** from the deals endpoint
2. **Loads tick data** for those trades' timeframes
3. **Replays each trade** with different SL/TP/Trailing Stop settings
4. **Identifies optimal parameters** that would have maximized returns

## Key Features

### Current (v1.0.0)
- ✅ MCP server structure with health check
- ✅ Logging to `logs/trading_optimizer.log`

### Coming Soon
- 🔄 Fetch closed positions from `GET http://localhost:8000/deals/{date}`
- 🔄 Load tick data from `GET http://localhost:8020/getTickDataFromDB`
- 🔄 Timerange filtering for focused analysis
- 🔄 Trade simulation with custom SL/TP
- 🔄 HTML reports with optimization results
- 🔄 Bulk parameter scanning (test multiple SL/TP combinations)
- 🔄 Trailing stop support and optimization

## Installation

The server is part of the Trading-MCP project. Ensure dependencies are installed:

```bash
cd /Users/paul/Sites/PythonProjects/Trading-MCP
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Add to `mcp.json`:

```json
{
  "servers": {
    "tradingOptimizer": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/bin/python",
      "args": [
        "${workspaceFolder}/mcp_servers/trading_optimizer_mcp.py"
      ]
    }
  }
}
```

## Usage

### Health Check

Verify the server is running:

```python
# Via MCP
health_check()
```

Returns server status, version, and available capabilities.

## API Requirements

The server requires two local API endpoints:

### 1. Deals API (Closed Positions)
- **Endpoint:** `GET http://localhost:8000/deals/{date}`
- **Format:** `YYYY-MM-DD`
- **Returns:** List of closed positions with entry/exit details

### 2. Tick Data API
- **Endpoint:** `GET http://localhost:8020/getTickDataFromDB`
- **Parameters:** `pair`, `startDate`, `endDate`, `maxTicks`
- **Returns:** Tick-level bid/ask data

## Architecture

```
trading_optimizer_mcp.py          # MCP server entry point
├── Tool: health_check            # Server status
├── Tool: fetch_closed_positions  # (Coming in TM-002)
├── Tool: fetch_tick_data         # (Coming in TM-003)
├── Tool: optimize_single         # (Coming in TM-006)
└── Tool: optimize_bulk           # (Coming in TM-007)
```

## Development

The server is being developed using an agent-driven approach with user stories in `agents/prd.json`.

### Current Progress
- ✅ TM-001: Base MCP server structure

### Next Steps
- 🔄 TM-002: Implement closed positions fetching
- 🔄 TM-003: Implement tick data fetching
- 🔄 TM-004: Trade replay simulation logic

## Logging

All operations are logged to:
- **File:** `logs/trading_optimizer.log`
- **Console:** stderr (for debugging)

## Example Workflow (Future)

```python
# 1. Fetch your trades from yesterday
positions = fetch_closed_positions(date="2026-01-19")

# 2. Test with specific SL/TP
results = optimize_trades_single(
    date="2026-01-19",
    symbol="US500_SB",
    sl_pips=20,
    tp_pips=40,
    start_time="14:30",
    end_time="21:00"
)
# → Generates HTML report showing how each trade would have performed

# 3. Find optimal parameters
best = optimize_trades_bulk(
    date="2026-01-19",
    symbol="US500_SB",
    sl_range=[10, 15, 20, 25, 30],
    tp_range=[20, 30, 40, 50, 60]
)
# → Tests all combinations, ranks by profit, generates comparison report
```

## Troubleshooting

### Server won't start
- Check Python virtual environment is activated
- Verify `mcp.json` configuration is correct
- Check `logs/trading_optimizer.log` for errors

### API connection issues
- Ensure `http://localhost:8000` (deals API) is running
- Ensure `http://localhost:8020` (VPS/tick data API) is running
- Test endpoints with curl:
  ```bash
  curl http://localhost:8000/deals/2026-01-20
  curl "http://localhost:8020/getTickDataFromDB?pair=220&startDate=2026-01-20T12:00:00.000Z&endDate=2026-01-20T16:00:00.000Z&maxTicks=10000"
  ```

## License

Part of the Trading-MCP project.
