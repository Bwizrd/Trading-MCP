# API Endpoint Reference

## cTrader Data API (localhost:8000)

### Get Data By Dates

**Endpoint:** `/getDataByDates`

**Parameters:**
- `pair` - **Numeric symbol ID** (NOT symbol name)
- `timeframe` - Timeframe string (1m, 5m, 15m, 30m, 1h, 4h, 1d)
- `startDate` - ISO timestamp with timezone: `YYYY-MM-DDTHH:MM:SS.000Z`
- `endDate` - ISO timestamp with timezone: `YYYY-MM-DDTHH:MM:SS.000Z`

**Example:**
```
http://localhost:8000/getDataByDates?pair=220&timeframe=1m&startDate=2026-01-03T00:00:00.000Z&endDate=2026-01-03T23:59:59.000Z
```

**Symbol ID Mapping:**
- 205 = NAS100
- 220 = US500
- 217 = UK100
- 200 = GER40
- 219 = US30
- 241 = XAUUSD_SB (Gold)
- 238 = XAGUSD_SB (Silver)
- 188 = FRA40_SB
- 201 = HK50_SB
- 159 = AUS200_SB
- 215 = SPA35_SB

## Health Check

**Endpoint:** `/health`

**Example:**
```
http://localhost:8000/health
```

**Response:**
```json
{"status":"OK: running on port 8000","timestamp":"2026-01-10T15:26:18.598Z"}
```
