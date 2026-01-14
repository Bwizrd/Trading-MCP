# VPS API Endpoints (Port 8020)

**IMPORTANT:** All data fetching should use `http://localhost:8020` (VPS server), NOT port 8000.

---

## Primary Endpoints

### 1. getData - Auto-populate InfluxDB + Fetch Data
**URL:** `http://localhost:8020/getData?pair=220&timeframe=1m&range=-1d`

**Purpose:** 
- Fetches historical OHLCV data
- **Automatically populates InfluxDB** if data doesn't exist
- Use this FIRST before trying getDataByDates

**Parameters:**
- `pair` - Symbol ID (e.g., 220 for US500_SB, 238 for XAGUSD_SB)
- `timeframe` - Data resolution (1m, 5m, 15m, 30m, 1h, 4h, 1d)
- `range` - Lookback period (e.g., -1d, -5d, -7d, -30d)

**Example:**
```bash
curl "http://localhost:8020/getData?pair=220&timeframe=1m&range=-1d"
curl "http://localhost:8020/getData?pair=238&timeframe=1m&range=-5d"
```

**Response:**
```json
{
  "startDate": "2026-01-09",
  "endDate": "2026-01-10",
  "entriesCount": 302,
  "symbolName": "US500_SB",
  "data": [
    {
      "timestamp": 1767977160000,
      "open": 6956.3,
      "high": 6956.3,
      "low": 6955.1,
      "close": 6955.8,
      "volume": 58
    }
  ]
}
```

---

### 2. getDataByDates - Fetch from InfluxDB (Date Range)
**URL:** `http://localhost:8020/getDataByDates?pair=220&timeframe=1m&startDate=2026-01-09T00:00:00.000Z&endDate=2026-01-09T23:59:59.000Z`

**Purpose:**
- Fetches OHLCV data from InfluxDB for specific date range
- **Requires data to already exist in InfluxDB**
- Use getData first to populate if needed

**Parameters:**
- `pair` - Symbol ID
- `timeframe` - Data resolution
- `startDate` - ISO timestamp format (YYYY-MM-DDTHH:MM:SS.000Z)
- `endDate` - ISO timestamp format (YYYY-MM-DDTHH:MM:SS.000Z)

**Example:**
```bash
curl "http://localhost:8020/getDataByDates?pair=220&timeframe=1m&startDate=2026-01-09T00:00:00.000Z&endDate=2026-01-09T23:59:59.000Z"
```

---

### 3. getTickDataFromDB - Fetch Tick Data
**URL:** `http://localhost:8020/getTickDataFromDB?pair=220&startDate=2026-01-09T08:00:00.000Z&endDate=2026-01-09T16:30:00.000Z&maxTicks=50000`

**Purpose:**
- Fetches raw tick data (bid/ask quotes) from InfluxDB
- Used for precise execution simulation
- **Only available for dates where tick collection was running**

**Parameters:**
- `pair` - Symbol ID
- `startDate` - ISO timestamp format
- `endDate` - ISO timestamp format
- `maxTicks` - Maximum number of ticks to return (default: 50000, max: 300000)

**Example:**
```bash
curl "http://localhost:8020/getTickDataFromDB?pair=220&startDate=2026-01-09T08:00:00.000Z&endDate=2026-01-09T16:30:00.000Z&maxTicks=50000"
```

**Note:** Tick data collection started for symbols 238, 201, 241, 188 on [date]. Historical tick data NOT available before collection started.

---

## Symbol ID Reference

### Currently Collecting Tick Data
- **205** - NAS100
- **220** - US500_SB
- **217** - UK100_SB
- **200** - GER40_SB
- **219** - US30_SB
- **238** - XAGUSD_SB (Silver) ⭐
- **201** - HK50_SB ⭐
- **241** - XAUUSD_SB (Gold) ⭐
- **188** - FRA40_SB ⭐

### Available in API (1m data only)
- **159** - AUS200_SB
- **215** - SPA35_SB
- **240** - XAUEUR_SB
- **237** - XAGEUR_SB

---

## Workflow

### For Backtesting with 1m Candles:
1. **First:** Call `getData` to populate InfluxDB
   ```bash
   curl "http://localhost:8020/getData?pair=238&timeframe=1m&range=-5d"
   ```

2. **Then:** Run backtest (Universal Backtest MCP will use getDataByDates internally)
   ```python
   mcp_universalback_run_strategy_backtest(
       symbol="XAGUSD_SB",  # or use symbol ID: "238"
       timeframe="1m",
       use_tick_data=False  # Use 1m candles only
   )
   ```

### For Backtesting with Tick Data:
1. **First:** Ensure tick data was collected for the date
2. **Then:** Run backtest with tick data enabled
   ```python
   mcp_universalback_run_strategy_backtest(
       symbol="US500_SB",
       timeframe="1m",
       use_tick_data=True  # Use ticks for execution
   )
   ```

---

## Common Errors

### "No strategy data available"
- InfluxDB doesn't have data for that symbol/date
- **Solution:** Call `getData` endpoint first to populate

### "Failed to fetch historical data"
- Symbol ID might not be supported
- Check symbols endpoint: `curl http://localhost:8020/symbols`

### Empty tick data
- Tick collection wasn't running for that date
- **Solution:** Use `use_tick_data=False` for candle-only backtest
