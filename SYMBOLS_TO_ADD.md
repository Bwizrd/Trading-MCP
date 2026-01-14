# Symbols to Add to cTrader API Database

## Currently Working (in API database)
- 205 - NAS100
- 220 - US500
- 217 - UK100
- 200 - GER40
- 219 - US30

---

## NEED TO ADD TO API DATABASE

### Priority 1: Major Indices
- **188** - FRA40_SB (France 40)
- **201** - HK50_SB (Hong Kong 50)
- **159** - AUS200_SB (Australia 200)
- **215** - SPA35_SB (Spain 35)

### Priority 2: Precious Metals
- **241** - XAUUSD_SB (Gold vs USD) ⭐
- **238** - XAGUSD_SB (Silver vs USD) ⭐
- **240** - XAUEUR_SB (Gold vs EUR)
- **237** - XAGEUR_SB (Silver vs EUR)

---

## Quick Copy/Paste Lists

### All Symbol IDs:
```
188, 201, 159, 215, 241, 238, 240, 237
```

### Individual Format:
```
188 (FRA40_SB)
201 (HK50_SB)
159 (AUS200_SB)
215 (SPA35_SB)
241 (XAUUSD_SB)
238 (XAGUSD_SB)
240 (XAUEUR_SB)
237 (XAGEUR_SB)
```

### For TypeScript Array:
```typescript
const newSymbolIds = [188, 201, 159, 215, 241, 238, 240, 237];
```

---

## Next Steps

1. Add these symbol IDs to cTrader API database (`getHistoricData.ts`)
2. Test with: `http://localhost:8000/getDataByDates?pair=241&timeframe=1m&startDate=2026-01-09T00:00:00.000Z&endDate=2026-01-09T23:59:59.000Z`
3. Run bulk backtest on all 8 symbols
4. Identify best performers
5. Add top performers to tick data collection (VPS server)
