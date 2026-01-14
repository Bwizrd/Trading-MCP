# TradingView to Pepperstone cTrader Webhook Bridge - Project Prompt

## Project Overview

Build a TypeScript/Node.js webhook receiver that connects TradingView Pine Script strategy alerts to Pepperstone cTrader for automated trading across multiple symbols simultaneously.

---

## Core Requirements

### 1. Webhook Receiver (Express.js)
- REST API endpoint to receive TradingView webhook alerts
- Validate incoming webhook signatures/tokens for security
- Parse JSON payload from TradingView alerts
- Queue system for handling multiple simultaneous alerts
- Logging system for all incoming alerts and actions

### 2. cTrader Integration
- Connect to Pepperstone cTrader via cTrader Open API (REST/WebSocket)
- Place market orders with SL/TP
- Manage open positions (modify SL/TP, close positions)
- Handle trailing stops (custom logic since TradingView can't manage after entry)
- Support multiple symbols simultaneously (US500, NAS100, EURUSD, etc.)

### 3. Position Management
- Track all open positions per symbol
- Implement trailing stop logic:
  - Monitor position profit in real-time
  - Activate trailing stop after X points profit
  - Move stop loss Y points behind current price
  - Update stop loss on cTrader via API
- Handle Safety Net exits (optional):
  - Monitor stochastic indicator values
  - Close position when opposite rotation detected

### 4. Multi-Symbol Support
- Run strategy on multiple symbols concurrently
- Separate position tracking per symbol
- Independent risk management per symbol
- Symbol-specific configuration (lot size, SL/TP distances)

---

## Technical Stack

**Required:**
- TypeScript
- Node.js + Express.js
- cTrader Open API SDK (or REST client)
- WebSocket for real-time price updates
- SQLite or JSON file for position state persistence
- PM2 or similar for process management

**Optional:**
- Redis for queue management
- PostgreSQL for trade history
- Docker for deployment

---

## TradingView Alert Payload Format

```json
{
  "strategy": "Stochastic Quad Rotation",
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.action}}",
  "price": "{{close}}",
  "time": "{{time}}",
  "contracts": "{{strategy.order.contracts}}",
  "stop_loss_points": 8,
  "take_profit_points": 8,
  "trailing_enabled": true,
  "trailing_activation_points": 10,
  "trailing_distance_points": 15
}
```

**Actions:**
- `buy` - Enter long position
- `sell` - Enter short position
- `exit` - Close position (optional, can rely on broker SL/TP)

---

## cTrader API Requirements

### Authentication
- OAuth2 or API token authentication
- Store credentials securely (environment variables)

### Order Placement
```typescript
interface OrderRequest {
  symbolName: string;        // "US500", "NAS100", etc.
  tradeSide: "BUY" | "SELL";
  volume: number;            // Lot size (0.01 = micro lot)
  stopLoss?: number;         // Absolute price
  takeProfit?: number;       // Absolute price
  label?: string;            // Order label for tracking
}
```

### Position Monitoring
- Get all open positions
- Get position by ID or label
- Modify position SL/TP
- Close position

### Real-time Price Updates
- WebSocket connection for live price feeds
- Subscribe to symbols being traded
- Calculate trailing stop updates based on live prices

---

## Trailing Stop Logic

```typescript
interface TrailingStopConfig {
  enabled: boolean;
  activationPoints: number;  // Profit required before trailing activates
  distancePoints: number;    // Distance to trail behind price
}

// Example for LONG position:
// Entry: 6900.00
// Current Price: 6915.00 (+15 points profit)
// Activation: 10 points
// Distance: 15 points
// 
// If profit >= 10 points:
//   New SL = Current Price - 15 points = 6900.00
//   Update SL on cTrader if new SL > current SL
```

**Implementation:**
1. Monitor position profit every tick (or every second)
2. Check if profit >= activation threshold
3. Calculate new stop loss = current price - distance
4. Only update if new SL is better than current SL
5. Send modify order request to cTrader API

---

## Multi-Symbol Architecture

```typescript
interface SymbolConfig {
  symbol: string;           // "US500", "NAS100"
  enabled: boolean;
  lotSize: number;          // 0.01, 0.1, 1.0
  stopLossPoints: number;   // 8, 15, 25
  takeProfitPoints: number;
  trailingStop: TrailingStopConfig;
  maxPositions: number;     // 1 (one trade at a time per symbol)
}

// Config file: config/symbols.json
{
  "US500": {
    "enabled": true,
    "lotSize": 0.1,
    "stopLossPoints": 8,
    "takeProfitPoints": 8,
    "trailingStop": {
      "enabled": true,
      "activationPoints": 10,
      "distancePoints": 15
    },
    "maxPositions": 1
  },
  "NAS100": {
    "enabled": true,
    "lotSize": 0.05,
    "stopLossPoints": 15,
    "takeProfitPoints": 15,
    "trailingStop": {
      "enabled": true,
      "activationPoints": 20,
      "distancePoints": 25
    },
    "maxPositions": 1
  }
}
```

---

## Project Structure

```
tradingview-ctrader-bridge/
├── src/
│   ├── server.ts              # Express webhook server
│   ├── ctrader/
│   │   ├── client.ts          # cTrader API client
│   │   ├── orders.ts          # Order placement logic
│   │   ├── positions.ts       # Position management
│   │   └── websocket.ts       # Real-time price feed
│   ├── trading/
│   │   ├── trailingStop.ts    # Trailing stop logic
│   │   ├── positionManager.ts # Track open positions
│   │   └── riskManager.ts     # Risk checks
│   ├── config/
│   │   ├── symbols.json       # Symbol configurations
│   │   └── settings.json      # Global settings
│   ├── utils/
│   │   ├── logger.ts          # Logging
│   │   └── validator.ts       # Webhook validation
│   └── types/
│       └── index.ts           # TypeScript interfaces
├── tests/
├── logs/
├── .env                       # API credentials
├── package.json
└── tsconfig.json
```

---

## Key Features to Implement

### Phase 1: Basic Webhook + Order Placement
1. Express server receiving webhooks
2. Parse TradingView alerts
3. Place market orders on cTrader with fixed SL/TP
4. Log all actions

### Phase 2: Position Management
1. Track open positions in memory/database
2. Prevent duplicate entries (one position per symbol)
3. Handle position close events from cTrader

### Phase 3: Trailing Stop
1. Real-time price monitoring via WebSocket
2. Calculate trailing stop updates
3. Modify SL on cTrader when trailing activates
4. Log all trailing stop adjustments

### Phase 4: Multi-Symbol Support
1. Load symbol configs from JSON
2. Independent position tracking per symbol
3. Symbol-specific risk parameters
4. Dashboard/API to view all positions

### Phase 5: Safety Features
1. Maximum daily loss limit
2. Maximum positions per symbol
3. Trading hours restrictions
4. Emergency stop-all button
5. Webhook signature verification

---

## TradingView Pine Script Alert Setup

In your Pine Script strategy, add this to the alert:

```pine
// In strategy.entry() or strategy.exit()
alert_message = '{"strategy":"Stochastic Quad Rotation","symbol":"' + syminfo.ticker + '","action":"{{strategy.order.action}}","price":' + str.tostring(close) + ',"time":"{{time}}","stop_loss_points":8,"take_profit_points":8,"trailing_enabled":true,"trailing_activation_points":10,"trailing_distance_points":15}'

strategy.entry("Long", strategy.long, alert_message=alert_message)
```

**Alert Configuration:**
- Condition: Strategy order fills
- Webhook URL: `https://your-server.com/webhook/tradingview`
- Message: Use the alert_message from strategy

---

## Security Considerations

1. **Webhook Authentication:**
   - Use secret token in webhook URL or header
   - Validate TradingView IP addresses
   - Rate limiting to prevent abuse

2. **API Credentials:**
   - Store in environment variables
   - Never commit to git
   - Use separate demo/live credentials

3. **Risk Management:**
   - Maximum position size limits
   - Daily loss limits
   - Maximum concurrent positions
   - Trading hours restrictions

4. **Error Handling:**
   - Retry logic for failed API calls
   - Alert on critical errors (email/SMS)
   - Graceful degradation if cTrader API is down

---

## Testing Strategy

1. **Unit Tests:**
   - Trailing stop calculations
   - Position tracking logic
   - Risk management rules

2. **Integration Tests:**
   - Mock TradingView webhooks
   - Mock cTrader API responses
   - Test multi-symbol scenarios

3. **Demo Trading:**
   - Run on cTrader demo account first
   - Test with small position sizes
   - Monitor for 1-2 weeks before going live

---

## Deployment

**Options:**
1. **VPS (Recommended):**
   - DigitalOcean/AWS/Vultr
   - Ubuntu 22.04 LTS
   - PM2 for process management
   - Nginx reverse proxy
   - SSL certificate (Let's Encrypt)

2. **Local Machine:**
   - Must be always-on
   - Port forwarding for webhooks
   - Dynamic DNS if IP changes

3. **Docker:**
   - Containerized deployment
   - Easy to scale and manage

---

## Monitoring & Logging

**Required Logs:**
- All incoming webhooks (timestamp, symbol, action, price)
- All orders placed (order ID, symbol, side, price, SL, TP)
- All position modifications (trailing stop updates)
- All errors and exceptions
- Daily P&L summary

**Monitoring:**
- Health check endpoint (`/health`)
- Position status endpoint (`/positions`)
- Daily email summary of trades
- Alert on errors (Telegram/Discord/Email)

---

## Example Workflow

1. **TradingView generates signal:**
   - Stochastic Quad Rotation detects entry on US500
   - Sends webhook: `{"action":"buy","symbol":"US500","price":6900.00}`

2. **Webhook receiver:**
   - Validates webhook signature
   - Checks if US500 position already exists (no)
   - Loads US500 config (lot size: 0.1, SL: 8 points, TP: 8 points)

3. **Order placement:**
   - Calculates SL: 6900.00 - 8 = 6892.00
   - Calculates TP: 6900.00 + 8 = 6908.00
   - Places market BUY order on cTrader
   - Stores position in database

4. **Trailing stop monitoring:**
   - WebSocket receives price updates
   - Current price: 6915.00 (+15 points profit)
   - Activation threshold: 10 points (met!)
   - New SL: 6915.00 - 15 = 6900.00
   - Updates SL on cTrader (from 6892.00 to 6900.00)

5. **Position close:**
   - Price hits TP at 6908.00 OR
   - Trailing stop hit at 6900.00 OR
   - TradingView sends exit signal
   - Position closed, P&L logged

---

## Quick Start Commands

```bash
# Initialize project
npm init -y
npm install express typescript ts-node @types/node @types/express
npm install dotenv axios ws
npm install --save-dev nodemon

# Create tsconfig.json
npx tsc --init

# Run development server
npm run dev

# Build for production
npm run build

# Run production
npm start
```

---

## Environment Variables (.env)

```env
# Server
PORT=3000
NODE_ENV=production
WEBHOOK_SECRET=your-secret-token-here

# cTrader API
CTRADER_API_URL=https://api.ctrader.com
CTRADER_CLIENT_ID=your-client-id
CTRADER_CLIENT_SECRET=your-client-secret
CTRADER_ACCESS_TOKEN=your-access-token
CTRADER_ACCOUNT_ID=your-account-id

# Risk Management
MAX_DAILY_LOSS=500
MAX_POSITIONS_PER_SYMBOL=1
TRADING_START_HOUR=0
TRADING_END_HOUR=23

# Logging
LOG_LEVEL=info
LOG_FILE=./logs/trading.log
```

---

## Success Criteria

✅ Receives TradingView webhooks reliably
✅ Places orders on cTrader with correct SL/TP
✅ Manages trailing stops in real-time
✅ Supports multiple symbols simultaneously
✅ Prevents duplicate positions per symbol
✅ Logs all actions for audit trail
✅ Handles errors gracefully
✅ Runs 24/7 without manual intervention

---

## Next Steps After Implementation

1. Test on demo account for 2 weeks
2. Verify trailing stop logic with real market conditions
3. Monitor spread impact on profitability
4. Optimize trailing stop parameters per symbol
5. Add Safety Net exit logic (stochastic-based)
6. Implement web dashboard for monitoring
7. Add mobile notifications (Telegram bot)
8. Scale to more symbols

---

## Additional Resources

- **cTrader Open API Docs:** https://help.ctrader.com/open-api/
- **TradingView Webhooks:** https://www.tradingview.com/support/solutions/43000529348-about-webhooks/
- **Express.js:** https://expressjs.com/
- **TypeScript:** https://www.typescriptlang.org/

---

**IMPORTANT:** Start with demo account only. Test thoroughly before risking real money. Automated trading carries significant risk.
