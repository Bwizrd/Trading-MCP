# Universal Backtest Engine & Modular Chart Engine Architecture Report

## Executive Summary

This report documents the architecture and workflow of the trading system's backtesting and charting infrastructure, specifically focusing on how the Universal Backtest Engine, Modular Chart Engine, and DSL Strategy system work together to produce comprehensive backtest results with interactive visualizations.

## System Architecture Overview

The system follows a clean modular architecture with clear separation of concerns:

```
Strategy Cartridges → Universal Backtest Engine → Chart Engine → Interactive HTML Charts
```

### Core Components

1. **Universal Backtest Engine** (`shared/backtest_engine.py`)
2. **Modular Chart Engine MCP Server** (`mcp_servers/modular_chart_engine.py`)
3. **Chart Engine** (`shared/chart_engine.py`)
4. **DSL Strategy System** (`shared/strategies/dsl_interpreter/dsl_strategy.py`)
5. **Strategy Registry** (`shared/strategy_registry.py`)
6. **Data Connector** (`shared/data_connector.py`)

## Universal Backtest Engine

### Purpose
The Universal Backtest Engine serves as the "console" that can run any strategy "cartridge" implementing the `TradingStrategy` interface. It provides standardized backtesting with consistent results across all strategies.

### Key Functions

#### `UniversalBacktestEngine.__init__(data_connector)` 
**File:** `shared/backtest_engine.py`

Initializes the engine with a data connector and indicator registry.

#### `async run_backtest(strategy, config, execution_timeframe)`
**File:** `shared/backtest_engine.py`

The main backtesting function that:
1. Validates inputs and initializes the strategy
2. Fetches market data for the specified symbol and timeframe
3. Calculates required technical indicators
4. Runs dual-timeframe simulation (strategy signals on higher timeframe, execution on 1-minute data)
5. Calculates performance statistics
6. Returns standardized `BacktestResults` object

**Key Steps:**
- Calls `strategy.requires_indicators()` to determine which indicators to calculate
- Uses `_calculate_indicators()` to compute indicator values
- Executes `_run_dual_timeframe_simulation()` for trade simulation
- Computes statistics via `_calculate_performance_stats()`

#### `_calculate_indicators(candles, required_indicators)`
**File:** `shared/backtest_engine.py`

Calculates technical indicators (MACD, RSI, SMA, etc.) for the strategy. Returns a dictionary mapping indicator names to their time-series values.

#### `_run_dual_timeframe_simulation(strategy, strategy_candles, execution_candles, indicators_data, config)`
**File:** `shared/backtest_engine.py`

Simulates trading by:
1. Iterating through strategy timeframe candles
2. Calling `strategy.generate_signal()` at each candle
3. Executing trades with stop-loss and take-profit on 1-minute data
4. Tracking all trades and their outcomes

### Data Flow

```
Market Data → Indicator Calculation → Signal Generation → Trade Execution → Results
```

## DSL Strategy System

### Purpose
The DSL (Domain Specific Language) Strategy system allows traders to define strategies using JSON configuration files without writing Python code. These strategies are "cartridges" that plug into the Universal Backtest Engine.

### Key Components

#### `DSLStrategy` Class
**File:** `shared/strategies/dsl_interpreter/dsl_strategy.py`

Implements the `TradingStrategy` interface to execute JSON-configured trading logic.

**Key Methods:**

##### `__init__(dsl_config)`
Validates and initializes the strategy from JSON configuration. Supports both time-based and indicator-based strategies.

##### `requires_indicators()`
Extracts indicator requirements from the DSL configuration. For MACD Crossover Strategy, this returns `['MACD']`.

**Critical Implementation:**
```python
def requires_indicators(self) -> List[str]:
    if not hasattr(self, 'dsl_config') or 'indicators' not in self.dsl_config:
        return []
    
    required = []
    for indicator_config in self.dsl_config['indicators']:
        indicator_type = indicator_config.get('type', '').upper()
        if indicator_type:
            required.append(indicator_type)
    
    return required
```

##### `get_indicator_series(candles)`
Calculates full indicator time-series for chart visualization. This is called by the chart engine to get indicator data for plotting.

##### `generate_signal(context)`
Evaluates trading conditions and generates BUY/SELL/HOLD signals based on indicator values and configured conditions.

### MACD Crossover Strategy Configuration
**File:** `shared/strategies/dsl_strategies/macd_crossover_strategy.json`

Example DSL configuration:
```json
{
  "name": "MACD Crossover Strategy",
  "version": "1.0.0",
  "description": "Trades MACD line crossovers with signal line",
  "indicators": [
    {
      "type": "MACD",
      "parameters": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9
      }
    }
  ],
  "conditions": {
    "buy": {
      "compare": "macd > macd_signal AND previous_macd <= previous_macd_signal"
    },
    "sell": {
      "compare": "macd < macd_signal AND previous_macd >= previous_macd_signal"
    }
  }
}
```

## Modular Chart Engine MCP Server

### Purpose
Provides MCP (Model Context Protocol) endpoints for chart generation, acting as the interface between the backtest engine and chart visualization.

### Key Functions

#### `create_chart_from_backtest_json(json_filename)`
**File:** `mcp_servers/modular_chart_engine.py`

Pure modular approach - creates charts from pre-generated backtest JSON files without re-running the backtest. This demonstrates complete separation between backtesting and visualization.

**Workflow:**
1. Reads backtest JSON file from `optimization_results/` directory
2. Reconstructs `Candle` and `Trade` objects from JSON data
3. Gets strategy from registry to calculate indicators via `strategy.get_indicator_series()`
4. Calls `chart_engine.create_comprehensive_chart()` to generate visualization
5. Returns path to interactive HTML chart

**Critical Code:**
```python
# Get strategy from registry to calculate indicators
strategy = registry.create_strategy(strategy_name)
if hasattr(strategy, 'get_indicator_series'):
    strategy_indicators = strategy.get_indicator_series(candles)
    indicators[display_name] = ind_values
```

#### `create_strategy_chart(input_data)`
**File:** `mcp_servers/modular_chart_engine.py`

Runs backtest and generates chart in one operation. Used for quick visualization during strategy development.

#### `list_backtest_json_files()`
**File:** `mcp_servers/modular_chart_engine.py`

Lists all available backtest JSON files with metadata (strategy name, symbol, performance, date).

## Chart Engine

### Purpose
Pure visualization engine that creates interactive HTML charts from backtest results. Contains NO strategy logic - only visualization.

### Key Functions

#### `create_comprehensive_chart(candles, backtest_results, indicators, title)`
**File:** `shared/chart_engine.py`

Main chart generation function that creates multi-subplot interactive charts.

**Workflow:**
1. Determines subplot layout based on indicator types via `_determine_subplot_layout()`
2. Calculates row heights via `_calculate_row_heights()`
3. Creates Plotly figure with `make_subplots()`
4. Adds candlestick chart to price subplot
5. Routes indicators to appropriate subplots via `_route_indicator_to_subplot()`
6. Adds trade signals and P&L visualization
7. Saves as interactive HTML file

#### `_determine_subplot_layout(indicators)`
**File:** `shared/chart_engine.py`

Analyzes indicators and determines subplot structure:
- Price chart: Always row 1
- Oscillators (MACD, RSI, Stochastic): Sequential rows (row 2, 3, etc.)
- Volume: Second-to-last row
- P&L: Last row

Returns mapping like: `{"price": 1, "oscillator_1": 2, "volume": 3, "pnl": 4}`

#### `_calculate_row_heights(layout)`
**File:** `shared/chart_engine.py`

Allocates vertical space:
- Price chart: 50% (or 80% if no oscillators)
- Oscillators: 30% total (divided equally among all oscillators)
- Volume: 10%
- P&L: 10%

**Recent Fix:** Adjusted vertical spacing calculation to prevent subplot overlap:
```python
if total_rows == 4:
    v_spacing = 0.06  # 6% spacing for 4 rows (price + MACD + volume + P&L)
```

#### `_route_indicator_to_subplot(fig, indicator_name, values, timestamps, layout)`
**File:** `shared/chart_engine.py`

Routes indicators to correct subplots based on metadata:
- Queries `indicators_metadata.py` registry
- OVERLAY indicators (SMA, VWAP) → Price chart
- OSCILLATOR indicators (MACD, RSI) → Dedicated subplots

#### `_add_macd_components(fig, macd_values, timestamps, row, metadata)`
**File:** `shared/chart_engine.py`

Special handling for MACD visualization with three components:
1. MACD line (blue)
2. Signal line (red)
3. Histogram (gray bars)

Retrieves signal and histogram from `_current_indicators` dictionary populated by the backtest engine.

## Complete Workflow: MACD Strategy Backtest to Chart

### Step 1: Strategy Registration
**File:** `shared/strategy_registry.py`

The MACD Crossover Strategy is registered and available for use:
```python
registry = StrategyRegistry()
strategy = registry.create_strategy('MACD Crossover Strategy')
```

### Step 2: Backtest Execution
**File:** `mcp_servers/universal_backtest_engine.py` → `shared/backtest_engine.py`

1. User calls `run_strategy_backtest` MCP tool with parameters
2. MCP server creates `BacktestConfiguration` object
3. Calls `backtest_engine.run_backtest(strategy, config)`
4. Engine calls `strategy.requires_indicators()` → Returns `['MACD']`
5. Engine calculates MACD indicator (line, signal, histogram)
6. Engine runs simulation, generating trades
7. Returns `BacktestResults` with trades, statistics, and indicator data

### Step 3: JSON Export
**File:** `mcp_servers/universal_backtest_engine.py`

Backtest results are saved to JSON file in `optimization_results/`:
```json
{
  "strategy_name": "MACD Crossover Strategy",
  "trades": [...],
  "market_data": [...],
  "summary": {...},
  "indicators": {
    "macd": [...],
    "macd_signal": [...],
    "macd_histogram": [...]
  }
}
```

### Step 4: Chart Generation
**File:** `mcp_servers/modular_chart_engine.py` → `shared/chart_engine.py`

1. Chart engine reads JSON file or receives backtest results
2. Calls `strategy.get_indicator_series(candles)` to get indicator data
3. Calls `chart_engine.create_comprehensive_chart()`
4. Chart engine determines layout: 4 rows (price, MACD, volume, P&L)
5. Routes MACD to oscillator subplot via `_route_indicator_to_subplot()`
6. Calls `_add_macd_components()` to render MACD line, signal, and histogram
7. Adds trade markers and P&L visualization
8. Saves interactive HTML chart to `data/charts/`

### Step 5: User Interaction
User opens HTML file in browser to explore:
- Candlestick price chart with trade markers
- MACD oscillator in separate subplot with all three components
- Volume bars
- Cumulative P&L tracking
- Interactive hover details and zoom

## Key Design Principles

### 1. Separation of Concerns
- **Backtest Engine:** Trade simulation and statistics
- **Chart Engine:** Pure visualization
- **Strategy:** Signal generation logic
- **Data Connector:** Market data retrieval

### 2. Strategy Cartridge System
Any strategy implementing `TradingStrategy` interface can plug into the engine:
```python
class TradingStrategy(ABC):
    @abstractmethod
    def generate_signal(self, context: StrategyContext) -> Signal:
        pass
    
    @abstractmethod
    def requires_indicators(self) -> List[str]:
        pass
```

### 3. Metadata-Driven Visualization
**File:** `shared/indicators_metadata.py`

Indicators are registered with metadata defining:
- Type (OVERLAY vs OSCILLATOR)
- Scaling (FIXED, AUTO, PRICE)
- Components (line, signal, histogram)
- Reference lines (zero line, overbought/oversold)

This allows the chart engine to automatically route and style indicators correctly.

### 4. Modular Architecture Benefits
- Backtest once, visualize many times
- JSON export enables offline analysis
- Strategies are reusable across different engines
- Chart engine can visualize any strategy's results

## File Reference Summary

### Core Engine Files
- `shared/backtest_engine.py` - Universal Backtest Engine
- `shared/chart_engine.py` - Chart visualization engine
- `shared/data_connector.py` - Market data retrieval
- `shared/strategy_interface.py` - Strategy interface definitions

### MCP Server Files
- `mcp_servers/universal_backtest_engine.py` - Backtest MCP endpoints
- `mcp_servers/modular_chart_engine.py` - Chart generation MCP endpoints

### Strategy Files
- `shared/strategies/dsl_interpreter/dsl_strategy.py` - DSL strategy implementation
- `shared/strategies/dsl_strategies/macd_crossover_strategy.json` - MACD strategy config
- `shared/strategy_registry.py` - Strategy registration and discovery

### Supporting Files
- `shared/indicators_metadata.py` - Indicator metadata registry
- `shared/indicators.py` - Indicator calculation functions
- `shared/models.py` - Data models (Candle, Trade, etc.)

## Conclusion

The Universal Backtest Engine and Modular Chart Engine work together through a clean, modular architecture that separates strategy logic, backtesting, and visualization. The DSL Strategy system allows traders to define strategies in JSON, which are then executed by the backtest engine and visualized by the chart engine. This design enables rapid strategy development, consistent backtesting, and flexible visualization without code duplication or tight coupling between components.

The MACD Crossover Strategy demonstrates this architecture perfectly: defined in JSON, executed by the universal engine, and visualized with proper subplot layout showing the MACD oscillator with all three components (line, signal, histogram) in a dedicated subplot below the price chart.
