# TradingView Webhook Setup Guide

## Strategy is NOW Ready for Webhooks ✅

The Pine Script now includes alert messages with all necessary data for your webhook receiver.

---

## What Changed

**Added webhook alert messages that include:**
- Action (buy/sell/exit_long/exit_short)
- Symbol (US500, NAS100, etc.)
- Entry price
- Stop loss points
- Take profit points
- Trailing stop settings (enabled, activation, distance)
- Safety net enabled status
- Timestamp

**Important:** Trailing stops are now handled by YOUR webhook receiver, not TradingView. The strategy sends fixed SL/TP to the broker, and your receiver monitors and updates them.

---

## Multi-Symbol Setup

**TradingView does NOT support running one strategy on multiple symbols simultaneously.**

You need to:

### Option 1: Multiple Charts (Recommended)
1. Open separate chart for each symbol (US500, NAS100, EURUSD, etc.)
2. Add the strategy to each chart
3. Create ONE alert per chart (see below)
4. All alerts send to the SAME webhook URL
5. Your receiver handles symbol routing

**Pros:** 
- Easy to monitor each symbol
- Independent settings per symbol
- Can enable/disable symbols individually

**Cons:**
- Need multiple browser tabs/windows
- More manual setup

---

### Option 2: TradingView Multi-Chart Layout
1. Create a layout with 4-6 charts
2. Set each chart to different symbol
3. Add strategy to each chart
4. Create alerts for each chart
5. Save layout for easy access

**Pros:**
- All symbols visible at once
- Easier to monitor

**Cons:**
- Still need separate alerts per symbol
- Can be resource-intensive

---

## Alert Setup (Per Symbol)

### Step 1: Add Strategy to Chart
1. Open chart for symbol (e.g., US500)
2. Add "Stochastic Quad Rotation - SIMPLE" strategy
3. Configure settings (SL, TP, trailing stop, etc.)

### Step 2: Create Alert
1. Click "Alert" button (top toolbar)
2. **Condition:** Select your strategy → "Order fills only"
3. **Alert name:** `Stochastic Quad - US500` (or whatever symbol)
4. **Message:** Leave EMPTY (strategy sends its own message)
5. **Webhook URL:** `https://your-server.com/webhook/tradingview`
6. **Options:**
   - ✅ Webhook URL
   - ✅ Once Per Bar Close (IMPORTANT!)
   - ❌ Only Once (leave unchecked)
7. Click "Create"

### Step 3: Repeat for Each Symbol
- US500 → Create alert
- NAS100 → Create alert  
- EURUSD → Create alert
- etc.

---

## Example Webhook Payloads

### Entry Long (BUY)
```json
{
  "action": "buy",
  "symbol": "US500",
  "price": 6900.5,
  "stop_loss_points": 8,
  "take_profit_points": 8,
  "trailing_enabled": true,
  "trailing_activation_points": 10,
  "trailing_distance_points": 15,
  "safety_net_enabled": false,
  "time": "2026-01-12T14:30:00Z"
}
```

### Entry Short (SELL)
```json
{
  "action": "sell",
  "symbol": "NAS100",
  "price": 21500.25,
  "stop_loss_points": 15,
  "take_profit_points": 15,
  "trailing_enabled": true,
  "trailing_activation_points": 20,
  "trailing_distance_points": 25,
  "safety_net_enabled": false,
  "time": "2026-01-12T14:35:00Z"
}
```

### Exit Long (Safety Net)
```json
{
  "action": "exit_long",
  "symbol": "US500",
  "price": 6915.75,
  "reason": "safety_net",
  "time": "2026-01-12T15:00:00Z"
}
```

### Exit Short (Safety Net)
```json
{
  "action": "exit_short",
  "symbol": "NAS100",
  "price": 21485.50,
  "reason": "safety_net",
  "time": "2026-01-12T15:05:00Z"
}
```

---

## Webhook Receiver Requirements

Your TypeScript receiver must:

1. **Parse incoming JSON** from TradingView
2. **Route by symbol** (US500 → cTrader US500 account)
3. **Place order** with fixed SL/TP on cTrader
4. **Start monitoring position** for trailing stop
5. **Update SL on cTrader** when trailing activates
6. **Handle Safety Net exits** (if enabled)

---

## Important Notes

### Trailing Stops
- **TradingView does NOT send trailing stop updates**
- Your receiver must monitor positions and update SL via cTrader API
- Strategy sends `trailing_enabled`, `trailing_activation_points`, `trailing_distance_points`
- Receiver uses these values to implement trailing logic

### Safety Net Exits
- If `safety_net_enabled: true`, TradingView will send exit signals
- Receiver should close position immediately on exit signal
- If `safety_net_enabled: false`, position closes on SL/TP only

### Symbol Mapping
TradingView symbol names may differ from cTrader:
- TradingView: `US500` → cTrader: `US500` or `SPX500`
- TradingView: `NAS100` → cTrader: `NAS100` or `USTEC`
- TradingView: `EURUSD` → cTrader: `EURUSD`

Map these in your receiver config.

---

## Testing Workflow

### 1. Test Webhook Delivery
```bash
# Use webhook.site to test
# Set webhook URL to: https://webhook.site/your-unique-id
# Trigger a signal in TradingView
# Verify JSON payload arrives correctly
```

### 2. Test Receiver Parsing
```bash
# Send test webhook to your receiver
curl -X POST https://your-server.com/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{"action":"buy","symbol":"US500","price":6900,"stop_loss_points":8,"take_profit_points":8,"trailing_enabled":true,"trailing_activation_points":10,"trailing_distance_points":15,"safety_net_enabled":false,"time":"2026-01-12T14:30:00Z"}'
```

### 3. Test cTrader Order Placement
- Use cTrader DEMO account
- Verify orders are placed correctly
- Check SL/TP distances are accurate

### 4. Test Trailing Stop Logic
- Place a test order
- Manually move price in demo
- Verify SL updates correctly

### 5. Test Multi-Symbol
- Set up 2-3 symbols
- Trigger signals on different symbols
- Verify receiver handles them independently

---

## Security Checklist

✅ Use HTTPS for webhook URL (not HTTP)
✅ Add secret token to webhook URL or header
✅ Validate TradingView IP addresses
✅ Rate limit webhook endpoint
✅ Log all incoming webhooks
✅ Alert on suspicious activity

---

## Monitoring Checklist

✅ Log all webhook receives
✅ Log all orders placed
✅ Log all trailing stop updates
✅ Log all errors
✅ Daily P&L summary
✅ Alert on critical errors (email/SMS)

---

## Common Issues

### Issue: Alerts not firing
**Solution:** 
- Check "Once Per Bar Close" is enabled
- Verify strategy is generating signals (check Strategy Tester)
- Check alert is active (not expired)

### Issue: Duplicate orders
**Solution:**
- Ensure "Only Once" is UNCHECKED (we want continuous alerts)
- Receiver should check if position already exists before placing order

### Issue: Wrong symbol on cTrader
**Solution:**
- Map TradingView symbols to cTrader symbols in receiver config
- Log symbol names to verify mapping

### Issue: Trailing stop not working
**Solution:**
- Verify receiver is monitoring positions
- Check WebSocket connection to cTrader
- Verify trailing stop calculations are correct

---

## Next Steps

1. ✅ Pine Script is ready (done)
2. ⏳ Build TypeScript webhook receiver
3. ⏳ Test on demo account
4. ⏳ Monitor for 1-2 weeks
5. ⏳ Go live with small position sizes

---

## Quick Reference

**Alert Condition:** Strategy → Order fills only
**Alert Message:** Leave empty (strategy handles it)
**Webhook URL:** Your server endpoint
**Once Per Bar Close:** ✅ YES
**Only Once:** ❌ NO

**Symbols to Set Up:**
- US500 (S&P 500)
- NAS100 (Nasdaq 100)
- EURUSD (optional)
- GBPUSD (optional)
- Any other symbols you want to trade

**One alert per symbol, all pointing to same webhook URL.**
