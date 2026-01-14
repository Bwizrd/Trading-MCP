# Trading US500 & NAS100 with Stochastic Quad Rotation

## Quick Setup for Indices

### 1. Essential Settings

**Pip Calculation Mode**: `Index/Stock (1.0)`
- For indices, 1 pip = 1 point
- This is CRITICAL - without this, your stops/targets will be wrong

### 2. Recommended Parameters for US500 (S&P 500)

| Parameter | Recommended Value | Notes |
|-----------|------------------|-------|
| **Timeframe** | 5m, 15m, or 30m | 5m for day trading, 15m-30m for swing |
| **Stop Loss** | 15-20 points | Adjust based on volatility |
| **Take Profit** | 25-35 points | 1.5:1 to 2:1 R/R ratio |
| **Swing Offset** | 2-3 points | Buffer beyond swing high/low |
| **Safety Net Oversold** | 20 | Exit shorts when fast D reaches 20 |
| **Safety Net Overbought** | 80 | Exit longs when fast D reaches 80 |
| **Trailing Distance** | 10-12 points | If using trailing stop |
| **Trailing Activation** | 8-10 points | Profit before trailing activates |

### 3. Recommended Parameters for NAS100 (Nasdaq 100)

| Parameter | Recommended Value | Notes |
|-----------|------------------|-------|
| **Timeframe** | 5m, 15m, or 30m | More volatile than US500 |
| **Stop Loss** | 20-30 points | NAS100 moves faster |
| **Take Profit** | 35-50 points | Larger targets for volatility |
| **Swing Offset** | 3-5 points | More buffer needed |
| **Safety Net Oversold** | 20 | Exit shorts when fast D reaches 20 |
| **Safety Net Overbought** | 80 | Exit longs when fast D reaches 80 |
| **Trailing Distance** | 15-20 points | Wider for volatility |
| **Trailing Activation** | 12-15 points | Higher threshold |

## Trading Hours

### US500 & NAS100 Active Hours (UTC)

| Session | Time (UTC) | Notes |
|---------|-----------|-------|
| **Pre-Market** | 08:00-13:30 | Lower volume, wider spreads |
| **Regular Hours** | 13:30-20:00 | BEST for trading - highest volume |
| **After Hours** | 20:00-00:00 | Lower volume |
| **Overnight** | 00:00-08:00 | Very low volume, avoid |

**Recommendation**: 
- Enable Time Filter: YES
- Start Time: 13:30 UTC (market open)
- End Time: 20:00 UTC (market close)
- Or use 14:00-19:00 for core hours only

## Strategy Settings by Trading Style

### Day Trading (5-minute chart)
```
Timeframe: 5m
Stop Loss: 15 points (US500) / 25 points (NAS100)
Take Profit: 25 points (US500) / 40 points (NAS100)
Swing Stop: Enabled (3 bars lookback, 2 points offset)
Safety Net: Enabled (20/80)
Trailing Stop: Optional (10 points distance, 8 points activation)
Time Filter: 13:30-20:00 UTC
Trend Filter: Disabled (or 5 points minimum)
Max Wait Bars: 8
```

### Scalping (1-3 minute chart)
```
Timeframe: 1m or 3m
Stop Loss: 8-10 points (US500) / 15-20 points (NAS100)
Take Profit: 12-15 points (US500) / 25-30 points (NAS100)
Swing Stop: Enabled (3 bars, 1 point offset)
Safety Net: Enabled (25/75 for faster exits)
Trailing Stop: Disabled (too tight for scalping)
Time Filter: 13:30-20:00 UTC (core hours only)
Trend Filter: Disabled
Max Wait Bars: 5 (faster signals)
```

### Swing Trading (30-minute to 1-hour chart)
```
Timeframe: 30m or 1h
Stop Loss: 25-30 points (US500) / 40-50 points (NAS100)
Take Profit: 40-50 points (US500) / 60-80 points (NAS100)
Swing Stop: Enabled (10 bars, 3 points offset)
Safety Net: Disabled (let winners run)
Trailing Stop: Enabled (15 points distance, 12 points activation)
Time Filter: Disabled (hold overnight if needed)
Trend Filter: Enabled (10 points minimum)
Max Wait Bars: 10
```

## Common Issues & Solutions

### Issue: All trades exiting at same price
**Solution**: Check Pip Calculation Mode is set to "Index/Stock (1.0)"

### Issue: Too many signals
**Solutions**:
- Reduce Max Wait Bars to 5-6
- Enable Trend Filter (10 points minimum)
- Enable Time Filter (trade only core hours)
- Increase oversold/overbought levels (15/85)

### Issue: Not enough signals
**Solutions**:
- Increase Max Wait Bars to 10-12
- Disable Time Filter
- Disable Trend Filter
- Decrease oversold/overbought levels (25/75)

### Issue: Stops too tight, getting stopped out
**Solutions**:
- Increase Stop Loss (20-25 points for US500, 30-40 for NAS100)
- Increase Swing Offset (3-5 points)
- Use longer Swing Lookback (7-10 bars)

### Issue: Targets not being hit
**Solutions**:
- Reduce Take Profit (20-25 points for US500, 30-40 for NAS100)
- Enable Trailing Stop to capture partial profits
- Enable Safety Net for momentum-based exits

## Performance Tips

1. **Backtest First**: Run at least 1 month of data before live trading
2. **Check Win Rate**: Aim for 50%+ win rate with 1.5:1+ R/R
3. **Monitor Drawdown**: Max drawdown should be < 20% of account
4. **Adjust for Volatility**: Widen stops/targets during high volatility (news events)
5. **Session Matters**: Best results during regular trading hours (13:30-20:00 UTC)

## News Events to Avoid

Major market-moving events (widen stops or avoid trading):
- FOMC Announcements (14:00 UTC)
- Non-Farm Payrolls (12:30 UTC, first Friday of month)
- CPI/Inflation Data (12:30 UTC)
- GDP Reports (12:30 UTC)
- Earnings Season (especially big tech for NAS100)

## Example Trade Setup

**US500 Long Entry**:
1. All 4 stochastics reach oversold (below 20)
2. Fast stochastic crosses above 20 within 8 bars
3. Time is 15:30 UTC (during regular hours)
4. Entry: 5850.00
5. Swing Stop: 5835.00 (15 points below recent swing low)
6. Target: 5875.00 (25 points profit)
7. Safety Net: Exit if fast D reaches 80

**Result**: 
- Risk: 15 points
- Reward: 25 points
- R/R Ratio: 1.67:1

## Quick Checklist

Before going live:
- [ ] Pip Calculation Mode = "Index/Stock (1.0)"
- [ ] Stop Loss appropriate for symbol (15-20 US500, 20-30 NAS100)
- [ ] Take Profit appropriate for symbol (25-35 US500, 35-50 NAS100)
- [ ] Time Filter enabled for regular hours (13:30-20:00 UTC)
- [ ] Backtested on at least 1 month of data
- [ ] Win rate > 50% in backtest
- [ ] Max drawdown acceptable
- [ ] Trade Info Labels enabled (to verify prices)
- [ ] Paper trade for 1-2 weeks first

## Support

If you're getting unexpected results:
1. Enable "Show Trade Info Labels" to see exact entry/stop/target
2. Check the Strategy Tester for detailed trade history
3. Verify Pip Calculation Mode is correct
4. Review the backtest performance metrics
5. Adjust parameters based on recent market volatility
