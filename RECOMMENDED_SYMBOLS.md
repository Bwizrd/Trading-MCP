# Recommended Symbols for Bulk Backtest

## Currently Collecting Tick Data
- **205** - NAS100
- **220** - US500  
- **217** - UK100
- **200** - GER40
- **219** - US30

---

## Recommended for Bulk Backtest (1m database bars)

### Priority 1: Major Indices (Similar to NAS100/US500)
These behave like broad market indices with good volatility:

| ID  | Symbol | Description | Why? |
|-----|--------|-------------|------|
| 188 | FRA40_SB | France 40 Index | European major index |
| 201 | HK50_SB | Hong Kong 50 Index | Asia-Pacific exposure |
| 159 | AUS200_SB | Australia 200 Index | Asia-Pacific hours |
| 215 | SPA35_SB | Spain 35 Index | European alternative |

### Priority 2: Precious Metals (Trend-following)
Gold and Silver are great for stochastic strategies:

| ID  | Symbol | Description | Why? |
|-----|--------|-------------|------|
| **241** | **XAUUSD_SB** | Gold vs US Dollar | **⭐ Top pick - strong trends** |
| **238** | **XAGUSD_SB** | Silver vs US Dollar | **⭐ Top pick - volatile** |
| 240 | XAUEUR_SB | Gold vs EUR | Alternative currency pair |
| 237 | XAGEUR_SB | Silver vs EUR | European hours |

### ❌ Crypto (Not Available)
Bitcoin symbols exist but are **NOT ENABLED** in your broker:
- 160 BTCUSD_SB (disabled)
- 128 BTCUSD (disabled)

---

## Recommended Testing Strategy

### Step 1: Quick Test (Top 6)
Test the most promising symbols first:
```python
symbols = ['FRA40', 'HK50', 'AUS200', 'XAUUSD', 'XAGUSD', 'SPA35']
symbol_ids = [188, 201, 159, 241, 238, 215]
```

### Step 2: Full Test (All Major Indices + Metals)
If results are good, expand:
```python
all_symbols = [
    188, 201, 159, 215,  # Indices
    241, 238, 240, 237   # Metals (Gold/Silver)
]
```

### Step 3: Add to Tick Collection
Based on backtest results, add winners to tick data collection:
- Current: NAS100, US500, UK100, GER40, US30
- Candidates: XAUUSD, XAGUSD, FRA40, HK50

---

## Symbol Characteristics

### Best for Stochastic Quad Rotation:
1. **Strong intraday trends** (not choppy)
2. **Good volatility** (moves at least 20-30 pips in direction)
3. **Clear reversals** (stochastics work best with momentum)
4. **Liquid markets** (tight spreads, good tick data)

### Expected Performance:
- **Indices** (FRA40, HK50, AUS200): Similar to US500/NAS100
- **Gold/Silver**: Often better than indices for trend strategies
- **Avoid**: Crypto (disabled), exotic pairs, low liquidity

---

## Next Steps

1. Run bulk backtest on Priority 1 symbols (4 indices)
2. Run bulk backtest on Priority 2 symbols (Gold/Silver)
3. Compare win rates and profit factors
4. Select top 2-3 performers
5. Add to tick data collection list
6. Re-run with tick data for validation

---

## Bulk Backtest Command

```python
# Test top candidates
mcp_universalback_bulk_backtest_strategy(
    strategy_name="Stochastic Quad Rotation",
    symbols=[
        'FRA40', 'HK50', 'AUS200', 'SPA35',  # Indices
        'XAUUSD', 'XAGUSD'                    # Metals
    ],
    timeframes=['1m'],
    start_date='2026-01-09',
    end_date='2026-01-09',
    sl_tp_combinations=[
        {"stop_loss_pips": 8, "take_profit_pips": 8}
    ]
)
```

---

## Why These Symbols?

### Similar to US500/NAS100:
- **FRA40**: CAC 40, Paris - European equivalent of S&P 500
- **HK50**: Hang Seng - Major Asian index, good volatility
- **AUS200**: ASX 200 - Australian market, different timezone
- **SPA35**: IBEX 35, Spain - Southern European exposure

### Gold & Silver:
- **XAUUSD**: Gold - King of trend-following, strong directional moves
- **XAGUSD**: Silver - More volatile than gold, better for short-term
- Both have excellent liquidity and tick data quality
- Often outperform indices for stochastic strategies

