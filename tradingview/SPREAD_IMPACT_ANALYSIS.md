# Spread Impact Analysis - Stochastic Quad Rotation Strategy

## The Problem

**Backtest Results (1pt activation, 8pt trail):**
- Total Trades: 453
- Total Profit: 242.5 GBP (+9.70%)
- **BUT**: 43% of winning trades are ≤1 point profit (198 trades)
- 35% are 1-2 points (160 trades)
- Only 12% are >2 points (56 trades)

**US500 Typical Spread:** 0.5-1.0 points

**Impact:** Most small wins (0.5-1 point) will be wiped out by spread costs in live trading.

---

## Why This Happens

The 8-point trailing stop is **too tight** for US500 price action:
- US500 frequently makes 20-50 point intraday moves
- An 8-point trailing stop gets triggered by minor pullbacks
- Strategy exits too early, missing the bigger moves

**Example:**
- Entry: 6900.00
- Price moves to 6920.00 (+20 points)
- Trailing stop at 6912.00 (8 points behind)
- Minor pullback to 6912.00 → Exit with only 12 points
- Price then continues to 6940.00 (missed 28 additional points)

---

## Solutions

### Option 1: Enable Safety Net (RECOMMENDED)

**What it does:**
- Exits LONG when fast stochastic (9-period) reaches overbought (80)
- Exits SHORT when fast stochastic reaches oversold (20)
- Lets trades run until momentum reverses

**Settings:**
```pine
enable_safety_net = true  // ENABLED by default now
safety_net_oversold = 20
safety_net_overbought = 80
```

**Advantages:**
- Captures bigger moves (20-50 points)
- Exits based on momentum, not arbitrary distance
- Proven in Day Trading Radio strategy

---

### Option 2: Wider Trailing Stop

**Settings:**
```pine
use_trailing = true
trail_points = 15.0-20.0  // Wider distance
trail_offset = 10.0-15.0  // Higher activation threshold
```

**Advantages:**
- Gives trades more room to breathe
- Captures bigger moves before trailing activates
- Still protects profits with trailing

**Disadvantages:**
- Larger drawdowns if price reverses
- May give back more profit than Safety Net

---

### Option 3: Combine Both (OPTIMAL)

**Settings:**
```pine
enable_safety_net = true
use_trailing = true
trail_points = 15.0
trail_offset = 10.0
```

**How it works:**
1. Trade enters
2. Trailing stop activates after 10 points profit
3. Safety Net monitors for opposite rotation
4. **Safety Net exits first** (has priority) if rotation detected
5. Trailing stop exits if price pulls back 15 points

**Advantages:**
- Best of both worlds
- Safety Net captures big moves
- Trailing stop protects if no rotation signal

---

## Testing Recommendations

### Test 1: Safety Net Only
```pine
enable_safety_net = true
use_trailing = false
stop_loss_points = 8.0
take_profit_points = 8.0
```

**Expected Results:**
- Fewer trades (exits later)
- Bigger average win size (10-30 points)
- Better spread-adjusted profit

---

### Test 2: Wider Trailing Stop
```pine
enable_safety_net = false
use_trailing = true
trail_points = 20.0
trail_offset = 15.0
```

**Expected Results:**
- Similar trade count
- Bigger average win size
- Some trades may give back profit

---

### Test 3: Combined (RECOMMENDED)
```pine
enable_safety_net = true
use_trailing = true
trail_points = 15.0
trail_offset = 10.0
```

**Expected Results:**
- Best spread-adjusted profit
- Captures big moves via Safety Net
- Protects profits via trailing stop

---

## Spread-Adjusted Profit Calculation

**Current Backtest (1pt activation, 8pt trail):**
- 453 trades × 1.0 point spread = -453 points spread cost
- Gross profit: 242.5 GBP
- **Estimated spread cost: ~150-200 GBP**
- **Net profit after spreads: 40-90 GBP** (much lower!)

**With Safety Net Enabled:**
- Estimated: 200-250 trades (fewer, bigger wins)
- Average win: 10-15 points (vs 2-3 points)
- Spread cost: -200 to -250 points
- **Net profit after spreads: 150-200 GBP** (much better!)

---

## Next Steps

1. **Enable Safety Net** in TradingView (already default in updated script)
2. **Run new backtest** with same date range
3. **Compare results:**
   - Total trades (should be fewer)
   - Average win size (should be bigger)
   - Total profit (should be higher after spread adjustment)
4. **Test on live demo account** with real spreads

---

## Key Takeaway

**The 8-point trailing stop optimizes for high-frequency scalping, but US500 spreads make scalping unprofitable.**

**Solution:** Let winners run longer using Safety Net or wider trailing stops to capture 20-50 point moves that overcome spread costs.
