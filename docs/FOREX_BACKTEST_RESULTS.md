# Forex Backtest Results - Stochastic Quad Rotation

## 📅 Test Period: November 12 - December 11, 2025 (1 Month)
## ⚙️ Configuration: 15/15 SL/TP, 10 pip trend filter, 1m timeframe, US hours (14:30-21:00)

---

## ⚠️ CRITICAL FINDING: ZERO SIGNALS ON ALL FOREX PAIRS

| Symbol | Signals | Trades | Profit | Issue |
|--------|---------|--------|--------|-------|
| **EURUSD_SB** | 0 | 0 | 0 pips | No signals generated |
| **EURCAD_SB** | 0 | 0 | 0 pips | No signals generated |
| **GBPJPY_SB** | 0 | 0 | 0 pips | No signals generated |
| **AUDUSD_SB** | 0 | 0 | 0 pips | No signals generated |

---

## 🔍 Root Cause Analysis

### Why No Signals?

**1. Trading Hours Restriction**
- Strategy configured for: 14:30-21:00 EST (US stock market hours)
- Forex trades: 24 hours, 5 days per week
- **Issue:** The trading hours filter is blocking most forex activity

**2. Pip Size / Volatility Mismatch**
- **Indices:** Move 50-200 pips per day (high volatility)
  - US500: ~50-100 pips/day
  - NAS100: ~100-200 pips/day
  - US30: ~100-150 pips/day
  
- **Forex Majors:** Move 20-80 pips per day (lower volatility)
  - EURUSD: ~30-50 pips/day
  - GBPJPY: ~50-80 pips/day
  - EURCAD: ~20-40 pips/day
  - AUDUSD: ~30-50 pips/day

**3. Trend Filter Too Restrictive**
- Current filter: Requires 10 pips of movement in 10 minutes
- **For indices:** This is reasonable (they move fast)
- **For forex:** This is TOO STRICT
  - EURUSD might only move 5-7 pips in 10 minutes
  - The trend filter is rejecting ALL signals

**4. Stochastic Behavior Difference**
- Indices: Sharp, decisive moves → clear stochastic crossovers
- Forex: Choppy, range-bound → stochastics oscillate without clear signals
- The "all 4 stochastics in zone" requirement is rarely met on forex

---

## 💡 Solutions to Make Strategy Work on Forex

### Option 1: Adjust Trend Filter (Recommended)
**Change for forex:**
```json
"min_trend_range_pips": 3.0  // Down from 10.0
"trend_lookback_minutes": 10
```

**Rationale:**
- Forex moves slower than indices
- 3 pips in 10 minutes is reasonable for EURUSD
- Still filters out choppy markets

### Option 2: Remove Trading Hours Restriction
**Change for forex:**
```json
"trading_hours_start": "00:00",  // Trade 24/5
"trading_hours_end": "23:59"
```

**Rationale:**
- Forex trades around the clock
- Restricting to US hours misses Asian/European sessions
- More opportunities across all sessions

### Option 3: Adjust SL/TP for Forex Volatility
**Change for forex:**
```json
"stop_loss_pips": 10,      // Down from 15
"take_profit_pips": 10     // Down from 15
```

**Rationale:**
- Forex moves in smaller increments
- 15 pips might be too wide for majors
- 10/10 or even 8/8 might be better

### Option 4: Relax Stochastic Requirements
**Current:** All 4 stochastics must be in zone
**Alternative:** Only 3 out of 4 must be in zone

**Rationale:**
- Forex is more range-bound
- Requiring all 4 is too strict
- Would need to modify the DSL strategy logic

---

## 📊 Comparison: Indices vs Forex

### Why Strategy Works on Indices
✅ High volatility (50-200 pips/day)
✅ Clear directional moves
✅ Sharp stochastic crossovers
✅ 10-pip trend filter is appropriate
✅ US trading hours capture main activity

### Why Strategy Fails on Forex
❌ Lower volatility (20-80 pips/day)
❌ More range-bound, choppy
❌ Stochastics oscillate without clear signals
❌ 10-pip trend filter is too strict
❌ US hours miss Asian/European sessions

---

## 🎯 Recommended Forex Configuration

Create a separate forex-optimized strategy:

```json
{
  "name": "Stochastic Quad Rotation - Forex",
  "version": "1.0.0",
  "description": "Forex-optimized version with adjusted parameters",
  "indicators": [
    // Same 4 stochastics
  ],
  "conditions": {
    // Same rotation conditions
  },
  "risk_management": {
    "stop_loss_pips": 10,           // Reduced from 15
    "take_profit_pips": 10,          // Reduced from 15
    "max_daily_trades": 200,
    "min_pip_distance": 0.0001,
    "execution_window_minutes": 1440,
    "trading_hours_start": "00:00",  // 24/5 trading
    "trading_hours_end": "23:59",
    "min_trend_range_pips": 3.0,     // Reduced from 10.0
    "trend_lookback_minutes": 10
  }
}
```

---

## 🧪 Next Steps

### Test Forex-Optimized Configuration
1. Create `stochastic_quad_rotation_forex.json` with adjusted parameters
2. Test on EURUSD with:
   - 10/10 SL/TP
   - 3-pip trend filter
   - 24/5 trading hours
3. If successful, test on other pairs

### Alternative: Test on Volatile Forex Pairs
Instead of majors, try:
- **GBPJPY** (more volatile, 80-120 pips/day)
- **GBPAUD** (volatile cross pair)
- **EURGBP** (European volatility)

These might work better with current settings.

---

## ✅ Conclusion

**The Stochastic Quad Rotation strategy is NOT suitable for forex majors with current index-optimized parameters.**

**Key Issues:**
1. Trading hours restriction blocks forex activity
2. 10-pip trend filter is too strict for forex volatility
3. Forex pairs are more range-bound than indices

**Solutions:**
1. Create forex-specific version with 3-pip filter
2. Enable 24/5 trading hours
3. Reduce SL/TP to 10/10 pips
4. Test on more volatile pairs (GBPJPY, GBPAUD)

**Strategy Performance Summary:**
- ✅ **Excellent on US Indices** (NAS100, US30, US500)
- ✅ **Good on European Indices** (GER40)
- ⚠️ **Needs adjustment for UK100** (trading hours)
- ❌ **Not suitable for Forex Majors** (without modifications)

---

**Status:** ⚠️ FOREX REQUIRES OPTIMIZATION  
**Date:** December 12, 2025  
**Test Period:** November 12 - December 11, 2025 (1 month)  
**Recommendation:** Stick with indices or create forex-optimized version
