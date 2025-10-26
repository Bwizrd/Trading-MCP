# 📁 Project Structure Guide

This document explains the improved folder structure for the Trading MCP project, designed to accommodate multiple strategies and proper organization of MCP servers.

## 🏗️ New Structure Overview

```
Trading-MCP/
├── mcp_servers/                    # All MCP server implementations
│   ├── __init__.py                # MCP servers package init
│   ├── charts/                    # Chart generation servers
│   │   ├── __init__.py           # Charts package init
│   │   └── trading_charts_mcp.py # Main chart generation server
│   ├── data_connectors/          # Data source connectors (shared by all strategies)
│   │   ├── __init__.py           # Data connectors package init
│   │   ├── ctrader.py           # cTrader API connector
│   │   └── influxdb.py          # InfluxDB + cTrader connector
│   └── strategies/                # Trading strategy servers
│       ├── __init__.py           # Strategies package init
│       └── vwap_strategy/         # VWAP strategy implementation
│           ├── __init__.py       # VWAP strategy package init
│           └── core.py          # Core VWAP strategy logic
├── shared/                        # Shared modules and utilities
│   ├── __init__.py               # Shared package init
│   ├── models/                   # Common Pydantic models
│   │   └── __init__.py          # All shared models (Trade, Candle, etc.)
│   └── utils/                    # Utility functions
│       └── __init__.py          # Helper functions and constants
├── config/                        # Configuration files
│   └── settings.py              # Application settings and constants
├── data/                         # Generated data and outputs
│   ├── charts/                  # Generated chart HTML files
│   └── optimization_results/    # Backtest CSV and analysis files
├── requirements.txt              # Python dependencies
└── documentation files...       # README, guides, etc.
```

## 🎯 Design Principles

### 1. **Separation of Concerns**
- **MCP Servers**: All server implementations grouped by function
- **Data Connectors**: Reusable data fetching servers (cTrader, InfluxDB, etc.)
- **Strategies**: Each trading strategy gets its own folder
- **Charts**: Visualization servers separate from strategy logic
- **Shared**: Common code to avoid duplication

### 2. **Scalability**
- Easy to add new strategies: create new folder under `strategies/`
- Easy to add new chart types: add to `charts/` folder
- Shared models and utilities prevent code duplication

### 3. **Maintainability**
- Clear import paths using project root
- Consistent structure across all modules
- Proper Python package structure with `__init__.py` files

## 🔧 Key Components

### MCP Servers (`mcp_servers/`)

#### Charts (`mcp_servers/charts/`)
- **Purpose**: Chart generation and visualization
- **Main File**: `trading_charts_mcp.py`
- **Responsibilities**:
  - Generate candlestick charts with VWAP
  - Create performance analysis charts
  - Export charts to HTML/PNG formats
  - Handle chart styling and configuration

#### Strategies (`mcp_servers/strategies/`)
- **Purpose**: Trading strategy implementations
- **Structure**: Each strategy gets its own subfolder

##### VWAP Strategy (`mcp_servers/strategies/vwap_strategy/`)
- **core.py**: Basic VWAP strategy with mock data (good for testing)
- **ctrader.py**: VWAP strategy with real cTrader API integration
- **influxdb.py**: VWAP strategy with InfluxDB for efficient data storage

### Shared Modules (`shared/`)

#### Models (`shared/models/`)
Common Pydantic models used across servers:
- `ResponseFormat`: Output format enum
- `TradeDirection`: BUY/SELL enum
- `TradeResult`: WIN/LOSS/BREAKEVEN/EOD_CLOSE enum
- `Candle`: OHLC candle data model
- `Trade`: Trade execution model
- `BacktestInput`: Backtesting input validation
- `ChartInput`: Chart generation input validation

#### Utils (`shared/utils/`)
Utility functions and constants:
- `get_config()`: Environment variable configuration
- `calculate_pips()`: Pip calculation for different symbol types
- `format_timestamp()`: Consistent timestamp formatting
- `sanitize_symbol()`: Clean symbols for file names
- `ensure_directory_exists()`: Directory creation helper

### Configuration (`config/`)

#### Settings (`config/settings.py`)
- Project paths and directories
- API configuration templates
- Trading strategy defaults
- Supported symbols and timeframes
- Chart styling configuration

## 🚀 Adding New Strategies

To add a new trading strategy (e.g., "RSI Strategy"):

1. **Create Strategy Folder**:
   ```bash
   mkdir -p mcp_servers/strategies/rsi_strategy
   ```

2. **Create Strategy Files**:
   ```bash
   # Core implementation
   touch mcp_servers/strategies/rsi_strategy/core.py
   
   # Data source integrations (optional)
   touch mcp_servers/strategies/rsi_strategy/ctrader.py
   touch mcp_servers/strategies/rsi_strategy/influxdb.py
   
   # Package init
   touch mcp_servers/strategies/rsi_strategy/__init__.py
   ```

3. **Implement Strategy**:
   - Use shared models from `shared.models`
   - Use shared utilities from `shared.utils`
   - Follow naming convention: `rsi_strategy_core`, `rsi_strategy_ctrader`, etc.

4. **Update Configuration**:
   Add to `claude_desktop_config.json`:
   ```json
   "rsi-strategy-core": {
     "command": "python",
     "args": ["/path/to/Trading-MCP/mcp_servers/strategies/rsi_strategy/core.py"]
   }
   ```

## 🎨 Adding New Chart Types

To add new chart functionality:

1. **Add to Charts Folder**:
   ```bash
   # For a new chart type
   touch mcp_servers/charts/technical_indicators_mcp.py
   ```

2. **Use Shared Resources**:
   - Import chart models from `shared.models`
   - Use chart configuration from `config.settings`
   - Use shared utilities for file handling

3. **Register in Claude**:
   Add new chart server to Claude Desktop config.

## 📋 Migration Benefits

### Before (Old Structure)
```
Trading-MCP/
├── trading_charts_mcp.py          # ❌ Root level clutter
├── trading_strategy_mcp.py        # ❌ No organization
├── trading_strategy_mcp_ctrader.py # ❌ Long filenames
├── trading_strategy_mcp_influxdb.py # ❌ Hard to group
├── charts/                        # ❌ Mixed with code
└── optimization_results/          # ❌ Mixed with code
```

### After (New Structure)
```
Trading-MCP/
├── mcp_servers/                   # ✅ Clear organization
│   ├── charts/                   # ✅ Grouped by function
│   └── strategies/               # ✅ Scalable structure
│       └── vwap_strategy/        # ✅ Strategy-specific
├── shared/                       # ✅ Reusable code
├── config/                       # ✅ Centralized settings
└── data/                        # ✅ Clear data separation
```

## 🎯 Best Practices

### Import Structure
```python
# Add project root to path (top of each MCP server file)
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import shared resources
from shared.models import BacktestInput, Trade, TradeDirection
from shared.utils import get_config, calculate_pips
from config.settings import STRATEGY_DEFAULTS
```

### Naming Conventions
- **MCP Server Names**: `strategy_name_data_source` (e.g., `vwap_strategy_core`)
- **File Names**: `descriptive_name.py` (e.g., `core.py`, `ctrader.py`)
- **Folder Names**: `snake_case` (e.g., `vwap_strategy`, `rsi_strategy`)

### Configuration Management
- Use `config/settings.py` for constants and defaults
- Use environment variables for sensitive data (API keys)
- Use `shared/utils/get_config()` for consistent configuration access

## 🔍 Testing the Structure

After reorganization:

1. **Test Import Paths**:
   ```bash
   python -c "from shared.models import Trade; print('✅ Imports working')"
   ```

2. **Test MCP Servers**:
   ```bash
   python mcp_servers/strategies/vwap_strategy/core.py
   python mcp_servers/charts/trading_charts_mcp.py
   ```

3. **Verify Claude Integration**:
   Update Claude Desktop config and restart Claude Desktop.

This new structure provides a solid foundation for scaling the trading MCP project with multiple strategies and proper code organization!