# TradingView Stochastic Quad Rotation Strategy

## Overview

This Pine Script implements the **Stochastic Quad Rotation** strategy for TradingView. It uses four stochastic oscillators with different periods to identify high-probability reversal points.

## Installation

1. Open TradingView and go to the Pine Editor (bottom of screen)
2. Click "New" to create a new script
3. Copy the entire contents of `stochastic_quad_rotation.pine`
4. Paste into the Pine Editor
5. Click "Save" and give it a name
6. Click "Add to Chart"

## Strategy Parameters

### Stochastic Settings

The strategy uses four stochastic oscillators:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Fast K Period | 9 | Most responsive to price changes |
| Fast D Smoothing | 3 | Signal line smoothing |
| Med-Fast K Period | 14 | Standard stochastic period |
| Med-Fast D Smoothing | 3 | Signal line smoothing |
| Med-Slow K Period | 40 | Filters out noise |
| Med-Slow D Smoothing | 4 | Signal line smoothing |
| Slow K Period | 60 | Confirms major trends |
| Slow D Smoothing | 10 | Signal line smoothing |

### Zone Levels

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Oversold Level | 20 | 0-50 | Threshold for oversold conditions |
| Overbought Level | 80 | 50-100 | Threshold for overbought conditions |
| Max Wait Bars After Zone | 8 | 1-20 | How long to wait for rotation after all stochastics reach zone |

**Max Wait Bars Explained**: This is crucial for getting more signals! Instead of requiring all stochastics to be in the zone on the exact previous bar, the strategy allows up to 8 bars (default) between when all stochastics reach the zone and when the fast stochastic rotates. This matches real-world manual trading where you see the setup forming and wait for the rotation.

### Risk Management

| Parameter | Default | Description |
|-----------|---------|-------------|
| Stop Loss (Pips) | 15.0 | Distance from entry for stop loss (used if swing-based disabled) |
| Take Profit (Pips) | 25.0 | Distance from entry for take profit |

**Risk/Reward Ratio**: 1:1.67

### Safety Net Exit

The Safety Net monitors the fast stochastic (9-3) D-line and exits when momentum reverses:

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Enable Safety Net Exit | true | - | Master switch for safety net exits |
| Safety Net Oversold Level | 20 | 10-30 | SHORT exits when fast D reaches this level |
| Safety Net Overbought Level | 80 | 70-90 | LONG exits when fast D reaches this level |

**Priority**: Highest (executes before trailing stop)

### Trailing Stop

Activates after reaching profit threshold and follows price to lock in gains:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Enable Trailing Stop | false | Master switch for trailing stop |
| Trailing Distance (Pips) | 8.0 | Distance behind price for trailing stop |
| Activation Profit (Pips) | 4.0 | Profit required before trailing activates |

**Priority**: Second (executes after safety net, before fixed stops)

### Swing-Based Stop Loss

Places stops based on recent swing highs/lows instead of fixed distance:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Enable Swing-Based Stop | true | Use swing highs/lows for stop placement |
| Swing Lookback Bars | 5 | Number of bars to find swing high/low |
| Swing Offset (Pips) | 1.0 | Additional buffer beyond swing point |

**How it works**:
- LONG: Stop placed below lowest low of last 5 bars + offset
- SHORT: Stop placed above highest high of last 5 bars + offset

**Priority**: Always active (baseline protection)

### Trading Hours Filter

| Parameter | Default | Description |
|-----------|---------|-------------|
| Enable Time Filter | **false** | Only trade during specified hours (disabled by default for more signals) |
| Start Hour | 14 | UTC hour to start trading (14:30) |
| Start Minute | 30 | UTC minute to start trading |
| End Hour | 21 | UTC hour to stop trading (21:00) |
| End Minute | 0 | UTC minute to stop trading |

**Default Hours**: 14:30 - 21:00 UTC (London/NY session overlap)

**Note**: Time filter is **disabled by default** to allow signals 24/7. Enable it if you only want to trade during specific sessions.

### Trend Strength Filter

| Parameter | Default | Description |
|-----------|---------|-------------|
| Enable Trend Filter | **false** | Require minimum price movement (disabled by default for more signals) |
| Min Range (Pips) | 10.0 | Minimum high-low range required |
| Lookback Bars | 10 | Number of bars to measure range |

This filter prevents trading in choppy, low-volatility conditions.

**Note**: Trend filter is **disabled by default** to allow signals in all market conditions. Enable it to filter out low-volatility periods.

### Display Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| Show Stochastics | true | Display all four stochastic lines |
| Show Zone Lines | true | Display oversold/overbought reference lines |

## How It Works

### Entry Signals

**BUY Signal** (Long Entry):
1. ✅ All 4 stochastics reach oversold zone (below 20)
2. ✅ Within max wait bars (default: 8), the fast stochastic crosses above oversold level
3. ✅ Current time is within trading hours (if enabled)
4. ✅ Price range meets minimum requirement (if enabled)

**SELL Signal** (Short Entry):
1. ✅ All 4 stochastics reach overbought zone (above 80)
2. ✅ Within max wait bars (default: 8), the fast stochastic crosses below overbought level
3. ✅ Current time is within trading hours (if enabled)
4. ✅ Price range meets minimum requirement (if enabled)

**Key Difference from Original**: The strategy now uses a "Max Wait Bars" window instead of requiring all stochastics to be in the zone on the exact previous bar. This significantly increases signal frequency while maintaining quality, matching how traders manually identify these setups.

### Exit Strategy

The strategy uses a three-tier exit system with priority levels:

**1. Safety Net Exit (Highest Priority)**
- Monitors the fast stochastic (9-3) D-line
- LONG exits when D-line reaches overbought (default: 80)
- SHORT exits when D-line reaches oversold (default: 20)
- Protects profits by exiting when momentum reverses

**2. Trailing Stop (Second Priority - Optional)**
- Activates after trade reaches profit threshold (default: 4 pips)
- Follows price at specified distance (default: 8 pips)
- Locks in profits as price moves favorably
- Only active if "Enable Trailing Stop" is ON

**3. Swing-Based Stop Loss (Always Active)**
- LONG: Placed below lowest low of last 5 bars + offset
- SHORT: Placed above highest high of last 5 bars + offset
- Provides baseline protection against adverse moves
- Can be disabled to use fixed pip-based stops instead

**4. Fixed Take Profit**
- Always active at specified distance (default: 25 pips)
- Exits are managed automatically by TradingView's strategy engine

### Visual Indicators

On the chart:
- 🟢 **Green triangle up**: Buy signal
- 🔴 **Red triangle down**: Sell signal
- 🟢 **Light green background**: All stochastics in oversold zone
- 🔴 **Light red background**: All stochastics in overbought zone
- 🔵 **Blue line**: Entry price (when in position)
- 🟠 **Orange line**: Trailing stop level (when active)

In the indicator pane:
- **Blue lines**: Fast stochastic (9-period)
- **Green lines**: Med-Fast stochastic (14-period)
- **Orange lines**: Med-Slow stochastic (40-period)
- **Red lines**: Slow stochastic (60-period)
- Solid lines = %K, Faded lines = %D (signal line)

## Recommended Settings by Market

### Forex (EURUSD, GBPUSD, etc.)
- **Pip Mode**: Forex (0.0001)
- **Timeframe**: 15m, 30m, 1h
- **Oversold/Overbought**: 20/80 (default)
- **Stop Loss**: 15 pips
- **Take Profit**: 25 pips
- **Trading Hours**: 14:30-21:00 UTC (enabled)
- **Trend Filter**: 10 pips in 10 bars (enabled)

### Indices (US500, NAS100, etc.) - **See [INDEX_TRADING_GUIDE.md](INDEX_TRADING_GUIDE.md) for detailed setup**
- **Pip Mode**: Index/Stock (1.0) ⚠️ CRITICAL
- **Timeframe**: 5m, 15m, 30m
- **Oversold/Overbought**: 20/80
- **Stop Loss**: 15-20 points (US500), 20-30 points (NAS100)
- **Take Profit**: 25-35 points (US500), 35-50 points (NAS100)
- **Swing Offset**: 2-3 points (US500), 3-5 points (NAS100)
- **Trading Hours**: 13:30-20:00 UTC (enabled for regular hours)
- **Trend Filter**: Disabled or 5 points minimum

### Crypto (BTC, ETH, etc.)
- **Timeframe**: 15m, 30m, 1h, 4h
- **Oversold/Overbought**: 20/80
- **Stop Loss**: Adjust based on volatility (20-30 pips)
- **Take Profit**: Adjust based on volatility (30-50 pips)
- **Trading Hours**: Disabled (24/7 market)
- **Trend Filter**: Increase to 15-20 pips

### Stocks/Indices
- **Timeframe**: 15m, 30m, 1h
- **Oversold/Overbought**: 20/80
- **Stop Loss**: Adjust based on symbol
- **Take Profit**: Adjust based on symbol
- **Trading Hours**: Match market hours
- **Trend Filter**: Enabled

## Backtesting Tips

1. **Test Multiple Timeframes**: Start with 15m, 30m, and 1h
2. **Adjust for Volatility**: Higher volatility = wider stops/targets
3. **Consider Spreads**: Add realistic commission/slippage in strategy settings
4. **Walk-Forward Testing**: Test on recent data, validate on older data
5. **Symbol-Specific Optimization**: Each market behaves differently

### Strategy Settings in TradingView

Go to Strategy Tester → Settings:
- **Initial Capital**: 10,000 (default)
- **Order Size**: 100% of equity (default) or fixed contracts
- **Commission**: Add your broker's commission
- **Slippage**: 1-3 ticks for realistic results
- **Verify Price for Limit Orders**: Enabled

## Performance Metrics to Watch

Key metrics in the Strategy Tester:
- **Net Profit**: Total profit/loss
- **Profit Factor**: Gross profit / Gross loss (aim for >1.5)
- **Win Rate**: Percentage of winning trades (aim for >50%)
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted returns (higher is better)
- **Total Trades**: Number of signals generated

## Optimization Guidelines

### Conservative Settings (Lower Risk)
- Oversold: 15
- Overbought: 85
- Stop Loss: 20 pips (or swing-based with 2 pip offset)
- Take Profit: 30 pips
- Trend Filter: 15 pips
- Safety Net: Enabled (20/80)
- Trailing Stop: Enabled (10 pips distance, 5 pips activation)
- Swing Stop: Enabled (5 bars, 2 pips offset)

### Aggressive Settings (Higher Risk)
- Oversold: 25
- Overbought: 75
- Stop Loss: 10 pips (or swing-based with 0.5 pip offset)
- Take Profit: 20 pips
- Trend Filter: 5 pips
- Safety Net: Enabled (25/75)
- Trailing Stop: Disabled
- Swing Stop: Enabled (3 bars, 0.5 pips offset)

### Day Trading Settings (Fast Exits)
- Oversold: 20
- Overbought: 80
- Swing Stop: Enabled (5 bars, 1 pip offset)
- Safety Net: Enabled (20/80) - Quick exits
- Trailing Stop: Enabled (6 pips distance, 3 pips activation)
- Take Profit: 20 pips

### Swing Trading Settings (Let Winners Run)
- Oversold: 20
- Overbought: 80
- Swing Stop: Enabled (10 bars, 2 pips offset)
- Safety Net: Disabled - Let trades run
- Trailing Stop: Enabled (15 pips distance, 10 pips activation)
- Take Profit: 40 pips

### Range-Bound Markets
- Tighter zones (25/75)
- Smaller stops/targets
- Disable trend filter

### Trending Markets
- Standard zones (20/80)
- Wider stops/targets
- Enable trend filter with higher threshold

## Limitations

⚠️ **Be aware of:**
- **Strong Trends**: May generate false signals during sustained trends
- **Low Volatility**: Fewer signals in calm markets
- **Whipsaws**: Can occur in choppy, sideways markets
- **Slippage**: Real execution may differ from backtest
- **Overnight Gaps**: Strategy doesn't account for gaps

## Advanced Modifications

Want to customize? Consider adding:
- **ATR-based stops**: Dynamic stop loss based on volatility
- **Partial exits**: Take profit in stages
- **Trend filter**: Only trade with higher timeframe trend
- **Volume confirmation**: Require volume spike for entries
- **Session filters**: Different settings for Asian/London/NY sessions

## Support Files

Related documentation:
- `../docs/STOCHASTIC_QUAD_ROTATION_STRATEGY.md` - Full strategy documentation
- `../docs/STOCHASTIC_DAY_TRADING_RADIO.md` - Alternative implementation
- `../shared/strategies/dsl_strategies/stochastic_quad_rotation.json` - Python DSL version

## Quick Start Checklist

- [ ] Copy Pine Script to TradingView
- [ ] Add to chart
- [ ] Select appropriate timeframe (15m, 30m, or 1h)
- [ ] Adjust stop loss/take profit for your symbol
- [ ] Enable/disable time filter based on market
- [ ] Run backtest on historical data
- [ ] Review performance metrics
- [ ] Optimize parameters if needed
- [ ] Paper trade before going live

## License

This strategy is provided as-is for educational and research purposes. Always test thoroughly before using with real money.

---

**Questions or Issues?** Check the main documentation or test the strategy on a demo account first.
