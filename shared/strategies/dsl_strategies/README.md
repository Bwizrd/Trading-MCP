# DSL Strategy System

## Overview

The DSL (Domain Specific Language) Strategy System allows AI tools to create trading strategies by generating JSON configurations instead of writing code. This extends the existing modular architecture without breaking any existing functionality.

## Architecture

```
DSL STRATEGY WORKFLOW:
JSON Config → DSL Interpreter → TradingStrategy Interface → Backtest Engine → Results
```

The DSL system integrates seamlessly with:
- ✅ Existing DataConnector (uses working `shared/data_connector.py`)
- ✅ Universal Backtest Engine MCP server
- ✅ Strategy Registry (shows DSL + code strategies together)
- ✅ Chart Engine (same JSON output format)
- ✅ Claude Desktop MCP connection

## Components

### 1. **DSL Strategy Class** (`dsl_strategy.py`)
- Implements `TradingStrategy` interface
- Executes JSON-configured trading logic
- Supports time-based conditions and price comparisons

### 2. **Schema Validator** (`schema_validator.py`)
- Validates JSON configurations against schema
- Ensures all required fields are present
- Provides detailed error messages

### 3. **DSL Loader** (`dsl_loader.py`)
- Discovers JSON strategy files
- Integrates with StrategyRegistry
- Manages DSL strategy lifecycle

## DSL Schema

### Minimum Required JSON Structure:
```json
{
  "name": "Strategy Name",
  "version": "1.0.0",
  "description": "Strategy description",
  "timing": {
    "reference_time": "09:30",
    "reference_price": "close",
    "signal_time": "10:00"
  },
  "conditions": {
    "buy": {"compare": "signal_price > reference_price"},
    "sell": {"compare": "signal_price < reference_price"}
  },
  "risk_management": {
    "stop_loss_pips": 15,
    "take_profit_pips": 25
  }
}
```

### Full Schema Features:
- **Timing**: Reference time vs signal time logic
- **Conditions**: Buy/sell comparison expressions
- **Risk Management**: Stop loss, take profit, daily limits
- **Parameters**: Custom strategy parameters
- **Metadata**: Author, tags, notes

## Usage Examples

### 1. **Time-Based Strategy**
```json
{
  "timing": {
    "reference_time": "09:30",
    "reference_price": "close",
    "signal_time": "10:00"
  },
  "conditions": {
    "buy": {"compare": "signal_price > reference_price"},
    "sell": {"compare": "signal_price < reference_price"}
  }
}
```

### 2. **Advanced Conditions**
```json
{
  "conditions": {
    "buy": {
      "compare": "signal_price > reference_price",
      "additional_conditions": ["volume > 1000"]
    }
  }
}
```

### 3. **Custom Risk Management**
```json
{
  "risk_management": {
    "stop_loss_pips": 20,
    "take_profit_pips": 40,
    "max_daily_trades": 2,
    "min_pip_distance": 0.0005
  }
}
```

## Integration with MCP

The DSL system extends the Universal Backtest Engine MCP server with:

1. **Enhanced `list_strategy_cartridges()`**: Shows both code and DSL strategies
2. **New `create_strategy_from_dsl()`**: Creates DSL strategies from JSON
3. **Compatible `run_strategy_backtest()`**: Runs DSL strategies like code strategies

## File Structure

```
shared/strategies/
├── dsl_interpreter/           # DSL system components
│   ├── __init__.py
│   ├── dsl_strategy.py        # DSL strategy implementation
│   ├── schema_validator.py    # JSON validation
│   └── dsl_loader.py          # Strategy discovery
├── dsl_strategies/            # JSON strategy storage
│   ├── __init__.py
│   ├── 10am_vs_930am.json     # Example strategy
│   └── README.md              # This file
└── vwap_strategy.py           # Existing code strategies (unchanged)
```

## Benefits

1. **AI-Friendly**: AI tools can generate JSON instead of complex code
2. **Modular**: Extends existing architecture without breaking anything
3. **Consistent**: Uses same interfaces and outputs as code strategies
4. **Validated**: Schema validation prevents configuration errors
5. **Integrated**: Works with all existing MCP tools and chart generation

## Example Workflow

1. AI generates DSL strategy JSON
2. JSON is validated against schema
3. DSL strategy appears in `list_strategy_cartridges()`
4. Can run backtest: `run_strategy_backtest(strategy_name="10am vs 9:30am Price Compare")`
5. Outputs JSON results to `optimization_results/`
6. Generates charts using modular chart engine
7. Everything works with Claude Desktop MCP connection

## Validation

The schema validator ensures:
- ✅ Required fields present
- ✅ Valid time formats (HH:MM)
- ✅ Logical time ordering (signal_time > reference_time)
- ✅ Valid comparison expressions
- ✅ Reasonable risk management values
- ✅ Semantic versioning

## Error Handling

- Clear validation error messages
- Graceful fallback for invalid JSON
- Non-breaking integration (DSL errors don't affect code strategies)
- Detailed logging for debugging

## Future Extensions

The DSL system is designed to be extensible:
- Additional condition types
- More complex timing logic
- Indicator integration
- Market session awareness
- Portfolio management rules

## Testing

Test the system with:
1. `list_strategy_cartridges()` - Should show DSL + code strategies
2. `run_strategy_backtest(strategy_name="10am vs 9:30am Price Compare")` - Should work
3. Chart generation should work automatically
4. Claude Desktop connection should remain stable