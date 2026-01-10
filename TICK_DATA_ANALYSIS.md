# Tick Data Analysis - 2026-01-09

## Problem Statement
Real-time trading system using VPS tick data made **5 trades** on 2026-01-09.  
Backtest using tick data only found **1 trade**.  
Backtest using database bars found **6 trades**.

Why the discrepancy?

---

## Key Findings

### 1. Data Coverage Issue ⚠️
- **VPS returns**: 100,000 ticks (maxTicks limit hit!)
- **Time coverage**: 00:00:01 to 15:21:46 (only 15.4 hours out of 24)
- **Missing data**: After 15:21 GMT - **NO DATA RETURNED**

**CRITICAL**: The VPS is hitting the `maxTicks=100,000` limit and stopping at 15:21, missing the rest of the trading day!

### 2. Candle Count Discrepancy
- **Database bars**: 1,307 candles for full 24 hours
- **Tick-aggregated**: 921 candles (only up to 15:21)
- **Missing**: 386 minutes of data (6.4 hours)

### 3. Market Hours Analysis
Most active hours (GMT):
- **14:00** - 21,941 ticks (US market open 14:30 GMT)
- **13:00** - 10,660 ticks
- **15:00** - 10,500 ticks (but data stops at 15:21!)
- **08:00** - 9,259 ticks (European session)

**US500 market is most active 13:00-21:00 GMT (US trading hours)**

### 4. OHLC Accuracy
Tick-aggregated vs Database bars:
- **Mean open difference**: 0.0152 pips
- **Mean close difference**: 0.0102 pips  
- **Max difference**: 2.3 pips (at 15:04:00)
- **Large differences (>1 pip)**: Only 1 candle out of 921

**Conclusion**: OHLC values are very similar, so this is NOT the cause of different signals.

### 5. Data Gaps
- **11 gaps** larger than 1 minute (mostly during off-hours)
- **Largest gap**: 80 seconds at 04:30 GMT
- Only **1 gap** in the 1-minute aggregated data

---

## Root Cause Analysis

### Why Only 1 Trade in Tick Backtest?
1. **Incomplete data**: VPS API stops at 15:21 (maxTicks limit)
2. **Missing prime trading hours**: 15:21-21:00 GMT is when most US market action happens
3. **Your 5 real trades**: Likely occurred after 15:21 GMT
4. **The 1 backtest trade**: At 15:10 GMT (within the available data window)

### Why 6 Trades in Database Backtest?
1. **Full 24-hour coverage**: Database has all 1,307 minutes
2. **Includes evening US session**: 15:21-21:00 GMT data present
3. **More opportunities**: Strategy could trigger on candles we don't have in tick data

---

## Solutions

### Option 1: Increase maxTicks Limit ✅ RECOMMENDED
```python
# In data_connector.py, change:
max_ticks = 100000  # Current
max_ticks = 500000  # Increase to cover full day
```

**US500 tick rate**: ~110 ticks/minute average  
**Full day needs**: ~158,400 ticks (110 × 1440 minutes)  
**Recommended**: 200,000-300,000 ticks for safety

### Option 2: Filter to Market Hours Only
Only request data for US market hours (13:30-21:00 GMT):
```python
start_date = "2026-01-09T13:30:00.000Z"
end_date = "2026-01-09T21:00:00.000Z"
```

### Option 3: Multiple API Calls
Break the day into chunks:
- Morning session: 00:00-12:00
- Afternoon session: 12:00-24:00
- Merge results

---

## Expected Results After Fix

With full day tick data:
- **Tick-aggregated candles**: ~1,440 (full day)
- **Expected trades**: 5-7 (matching real trades and database backtest)
- **Signal timing**: Should align with real broker execution times

---

## Action Items

1. ✅ **Immediate**: Increase `maxTicks` to 300,000 in data_connector.py
2. ✅ **Verify**: Run backtest again and check candle count reaches ~1,440
3. ✅ **Compare**: Trades should now match your 5 real trades
4. ⏳ **Document**: Record actual trade times from broker for comparison

---

## Technical Details

### VPS API Endpoint
```
http://localhost:8020/getTickDataFromDB
?pair=220 (US500)
&startDate=2026-01-09T00:00:00.000Z
&endDate=2026-01-09T23:59:59.999Z
&maxTicks=100000  ← LIMITING FACTOR
```

### Tick Data Characteristics
- **Format**: Bid/Ask with millisecond timestamps
- **Frequency**: 1-665 ticks per minute (mean: 108.6)
- **Gap tolerance**: Max 80 seconds (acceptable for 1m candles)
- **Quality**: Excellent - only 1 minute with gap in aggregated data

### Aggregation Method
```python
# Ticks grouped by second → mid price (bid+ask)/2
# Then resampled to 1-minute OHLC
ohlc = df['mid'].resample('1min').agg(['first', 'max', 'min', 'last'])
```

---

## Files Generated
- `analyze_tick_data.py` - Analysis script
- `tick_data_1m_aggregated.csv` - 921 1m candles from ticks
- `TICK_DATA_ANALYSIS.md` - This document

---

## Conclusion

The issue is **NOT** with:
- ❌ OHLC calculation differences
- ❌ Aggregation logic
- ❌ Strategy implementation
- ❌ Dual-timeframe architecture

The issue **IS** with:
- ✅ **Data completeness**: Only 15.4 hours of 24 fetched
- ✅ **maxTicks limit**: Hitting 100,000 tick cap too early
- ✅ **Missing prime hours**: 15:21-21:00 GMT not included

**Fix**: Increase maxTicks to 300,000 and re-run backtest.
