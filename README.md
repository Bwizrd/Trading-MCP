# 📊 Trading MCP Server

A comprehensive Model Context Protocol (MCP) server for trading strategy analysis and chart generation. This project provides advanced trading analytics, backtesting capabilities, and professional-grade chart visualization for forex trading strategies.

## 🚀 Features

### 📈 Comprehensive Trading Charts
- **Unified Chart System**: Single chart type with ALL advanced features
- **1-Minute Precision**: Uses 1-minute data for accurate entry/exit timing
- **Professional Visualization**: Interactive Plotly charts with multiple sections

### 🎯 Chart Components
- **Candlestick Price Action**: OHLC data with green/red coloring
- **VWAP Overlay**: Volume-weighted average price line (calculated from 1m data)
- **Entry/Exit Markers**: Numbered circles and X marks with color coding
- **Connection Lines**: Colored lines linking entries to exits (Green=profit, Red=loss, Orange=break-even)
- **Cumulative P&L**: Real-time running total of strategy performance
- **Trade Summary Table**: Complete trade details with color-coded results
- **Total P&L Display**: Prominent bottom display of net strategy performance

### 🔍 Advanced Analytics
- **VWAP Strategy**: Entry signals based on price vs VWAP relationship
- **Precise Backtesting**: Minute-level accuracy for realistic results
- **Risk Management**: Configurable stop-loss and take-profit levels
- **Performance Metrics**: Win rate, total pips, trade-by-trade analysis

## 📁 Project Structure

```
Trading-MCP/
├── mcp_servers/                    # All MCP server implementations
│   ├── charts/                    # Chart generation servers
│   │   └── trading_charts_mcp.py # Main chart server
│   └── strategies/                # Trading strategy servers
│       └── vwap_strategy/         # VWAP strategy implementations
│           ├── core.py           # Core strategy (mock data)
│           ├── ctrader.py        # cTrader integration
│           └── influxdb.py       # InfluxDB + cTrader integration
├── shared/                        # Shared modules and utilities
│   ├── models/                   # Common Pydantic models
│   └── utils/                    # Utility functions
├── config/                        # Configuration files
│   └── settings.py              # Application settings
├── data/                         # Generated data and outputs
│   ├── charts/                  # Generated chart outputs
│   └── optimization_results/    # Backtest and optimization data
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── ARCHITECTURE.md              # Technical architecture overview
├── QUICKSTART.md               # Quick setup guide
├── UNIFIED_CHARTS.md           # Chart system documentation
└── 1MINUTE_PRECISION_UPDATE.md # Latest precision improvements
```

## 🛠️ Installation

### Prerequisites
```bash
# Python 3.10 or higher required
python --version

# Install required packages
pip install -r requirements.txt
```

### Setup
1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Trading-MCP
   ```

2. **Set up environment variables:**
   ```bash
   export CTRADER_API_URL="http://localhost:8000"
   export CTRADER_API_USERNAME="your_username"
   export CTRADER_API_PASSWORD="your_password"
   ```

## 🎮 Usage

### Starting the MCP Server
```bash
python trading_charts_mcp.py
```

### Creating Charts
Use the MCP client to request charts:
```json
{
  "symbol": "EURUSD",
  "start_date": "2025-10-20",
  "end_date": "2025-10-25",
  "timeframe": "30m",
  "stop_loss_pips": 10,
  "take_profit_pips": 15
}
```

### Output
- Interactive HTML charts saved to `charts/` directory
- Complete trading analysis with all features included
- Professional-grade visualization ready for sharing

## 📊 Chart Features

### Upper Section: Price Chart with Trades
- Candlestick price action
- VWAP overlay line
- Numbered entry markers (🟢 BUY, 🔴 SELL)
- Numbered exit markers (✅ WIN, ❌ LOSS, 🟨 EOD)
- Colored connection lines between entries and exits

### Middle Section: Cumulative P&L
- Running total of strategy performance
- Visual trend analysis
- Zero reference line

### Bottom Section: Trade Summary
- Complete trade details table
- Color-coded pip results
- Entry/exit prices and times
- Win/Loss/EOD status

### Total P&L Display
- Prominent bottom summary
- Color-coded total performance
- Large, bold formatting

## 🔧 Configuration

### Supported Symbols
- Major forex pairs: EURUSD, GBPUSD, USDJPY, AUDUSD, etc.
- Indices: GER40, UK100, US30

### Timeframes
- Chart display: 15m, 30m, 1h, 4h, 1d
- Backtest precision: Always 1-minute for accuracy

### Strategy Parameters
- Configurable stop-loss (default: 10 pips)
- Configurable take-profit (default: 15 pips)
- Entry time: 8:30 AM (or closest available)

## Integration with Claude

### Claude Desktop Configuration

1. **Locate your Claude Desktop config file:**
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

2. **Add the MCP server to your config:**

```json
{
  "mcpServers": {
    "trading-charts": {
      "command": "python",
      "args": ["/full/path/to/Trading-MCP/mcp_servers/charts/trading_charts_mcp.py"]
    },
    "vwap-strategy-core": {
      "command": "python", 
      "args": ["/full/path/to/Trading-MCP/mcp_servers/strategies/vwap_strategy/core.py"]
    },
    "vwap-strategy-ctrader": {
      "command": "python", 
      "args": ["/full/path/to/Trading-MCP/mcp_servers/strategies/vwap_strategy/ctrader.py"]
    },
    "vwap-strategy-influxdb": {
      "command": "python", 
      "args": ["/full/path/to/Trading-MCP/mcp_servers/strategies/vwap_strategy/influxdb.py"]
    }
  }
}
```

**Important:** Replace `/full/path/to/` with the actual absolute path where you saved the file.

3. **Restart Claude Desktop**

## 🏗️ Architecture

### MCP Server Design
- **FastMCP**: Modern Python MCP server framework
- **Async/Await**: High-performance async operations
- **cTrader Integration**: Direct API connectivity
- **Plotly Visualization**: Professional interactive charts

### Data Flow
1. **1-Minute Data Fetch**: High-resolution data from cTrader API
2. **Chart Data Aggregation**: User timeframe for visualization
3. **Precise Backtesting**: Minute-level entry/exit detection
4. **Comprehensive Output**: Multi-section interactive chart

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Quick Start Guide](QUICKSTART.md)
- [Unified Charts System](UNIFIED_CHARTS.md)
- [1-Minute Precision Update](1MINUTE_PRECISION_UPDATE.md)

## 📞 Support

For questions or issues:
1. Check existing documentation
2. Review the code comments
3. Create an issue in the repository

---

**🎯 Professional trading analysis with institutional-grade precision!**

```bash
# Check Python version
python --version  # Should be 3.10+

# Check dependencies
pip list | grep -E "mcp|httpx|pydantic"

# Check for syntax errors
python -m py_compile trading_strategy_mcp.py
```

### Claude Can't See the Server

1. Verify config file location and syntax
2. Use absolute paths (not ~/ or relative paths)
3. Restart Claude Desktop completely
4. Check Claude Desktop logs for errors

### API Connection Issues

If using real API:
- Verify API key is valid
- Check API endpoint URLs
- Test API independently with curl/Postman
- Check for rate limiting

## Security Notes

⚠️ **Important Security Considerations:**

1. **API Keys:** Store API keys in environment variables, not hardcoded:
```python
import os
API_KEY = os.environ.get("TRADING_API_KEY")
```

2. **Read-Only Mode:** This server is designed for analysis only. For actual trade execution, additional safety measures are required.

3. **Data Validation:** All inputs are validated with Pydantic models to prevent injection attacks.

## Next Steps

1. **Connect your real data feed** - Replace mock functions
2. **Test thoroughly** - Backtest on historical data
3. **Add more strategies** - Create new tools for different approaches
4. **Add filters** - Market conditions, news events, volatility
5. **Build monitoring** - Track live performance

## Support

For questions about:
- **MCP Protocol:** https://modelcontextprotocol.io
- **Claude Integration:** https://docs.claude.com
- **This Implementation:** Review the code comments

## License

This is a demonstration project. Use at your own risk. Not financial advice.

## Config Path
~/Library/Application Support/Claude/claude_desktop_config.json