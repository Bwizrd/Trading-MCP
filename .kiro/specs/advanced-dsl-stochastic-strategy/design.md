# Design Document

## Overview

This design extends the DSL strategy system to support advanced multi-indicator strategies while maintaining backward compatibility with existing simple strategies. The enhancement enables complex logic patterns, multiple indicator instances, zone-based conditions, and crossover detection.

The Stochastic Quad Rotation strategy serves as the reference implementation, demonstrating all new capabilities.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DSL Strategy System                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ JSON Config  │─────▶│  Schema      │                    │
│  │              │      │  Validator   │                    │
│  └──────────────┘      └──────────────┘                    │
│                               │                              │
│                               ▼                              │
│                    ┌──────────────────┐                     │
│                    │  DSL Strategy    │                     │
│                    │  (Enhanced)      │                     │
│                    └──────────────────┘                     │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐            │
│         ▼                   ▼                  ▼            │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────┐    │
│  │ Multi-      │   │ Condition    │   │ Crossover   │    │
│  │ Indicator   │   │ Evaluator    │   │ Detector    │    │
│  │ Manager     │   │ (AND/OR)     │   │             │    │
│  └─────────────┘   └──────────────┘   └─────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │  Indicator Registry  │
                   │  (Stochastic added)  │
                   └──────────────────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │   Chart Engine       │
                   │  (Multi-line subplot)│
                   └──────────────────────┘
```

### Component Interactions

1. **JSON Config** → **Schema Validator**: Validates advanced DSL syntax
2. **DSL Strategy** → **Multi-Indicator Manager**: Creates and tracks indicator instances
3. **DSL Strategy** → **Condition Evaluator**: Processes complex boolean logic
4. **DSL Strategy** → **Crossover Detector**: Tracks state and detects threshold crossings
5. **Indicator Registry** → **Stochastic Calculator**: Provides stochastic calculations
6. **Chart Engine** → **Multi-line Rendering**: Displays all indicator instances

## Components and Interfaces

### 1. Enhanced DSL Schema

**Purpose**: Define and validate advanced strategy configurations

**New Schema Elements**:

```json
{
  "indicators": [
    {
      "type": "STOCHASTIC",
      "alias": "fast",
      "params": {
        "k_period": 9,
        "k_smoothing": 1,
        "d_smoothing": 3
      }
    }
  ],
  "conditions": {
    "buy": {
      "type": "rotation",
      "zone": {
        "all_below": 20,
        "indicators": ["fast", "med_fast", "med_slow", "slow"]
      },
      "trigger": {
        "indicator": "fast",
        "crosses_above": 20
      }
    }
  }
}
```

**Interface**:
```python
def validate_advanced_dsl(config: Dict) -> bool:
    """Validate advanced DSL configuration"""
    # Validate indicator instances
    # Validate zone conditions
    # Validate crossover triggers
    # Validate boolean logic
```

### 2. Multi-Indicator Manager

**Purpose**: Create and manage multiple instances of the same indicator type

**Responsibilities**:
- Create indicator instances with unique aliases
- Track indicator values per instance
- Provide value lookup by alias
- Handle indicator lifecycle

**Interface**:
```python
class MultiIndicatorManager:
    def register_instance(self, type: str, alias: str, params: Dict):
        """Register a new indicator instance"""
    
    def get_value(self, alias: str, timestamp: datetime) -> float:
        """Get indicator value by alias"""
    
    def get_all_values(self, timestamp: datetime) -> Dict[str, float]:
        """Get all indicator values for a timestamp"""
    
    def calculate_all(self, candles: List[Candle]) -> Dict[str, Dict[datetime, float]]:
        """Calculate all registered indicators"""
```

### 3. Condition Evaluator

**Purpose**: Evaluate complex boolean logic with multiple conditions

**Responsibilities**:
- Parse condition trees (AND/OR)
- Evaluate zone conditions
- Evaluate comparison conditions
- Short-circuit evaluation

**Interface**:
```python
class ConditionEvaluator:
    def evaluate(self, condition: Dict, indicator_values: Dict[str, float]) -> bool:
        """Evaluate a condition tree"""
    
    def evaluate_zone(self, zone_spec: Dict, values: Dict[str, float]) -> bool:
        """Check if indicators are in specified zone"""
    
    def evaluate_comparison(self, comp_spec: Dict, value: float) -> bool:
        """Evaluate a comparison (>, <, ==, etc.)"""
```

### 4. Crossover Detector

**Purpose**: Detect when indicators cross thresholds

**Responsibilities**:
- Track previous indicator values
- Detect upward crossovers (below → above)
- Detect downward crossovers (above → below)
- Prevent duplicate signals

**Interface**:
```python
class CrossoverDetector:
    def __init__(self):
        self._previous_values: Dict[str, float] = {}
    
    def detect_cross_above(self, alias: str, current: float, threshold: float) -> bool:
        """Detect if indicator crossed above threshold"""
    
    def detect_cross_below(self, alias: str, current: float, threshold: float) -> bool:
        """Detect if indicator crossed below threshold"""
    
    def update(self, alias: str, value: float):
        """Update tracked value for next iteration"""
```

### 5. Stochastic Calculator

**Purpose**: Calculate Stochastic Oscillator (%K and %D lines)

**Formula**:
- %K = ((Close - Lowest Low) / (Highest High - Lowest Low)) * 100
- %K Smoothed = SMA(%K, k_smoothing)
- %D = SMA(%K Smoothed, d_smoothing)

**Interface**:
```python
class StochasticCalculator(IndicatorCalculator):
    def __init__(self, k_period: int, k_smoothing: int, d_smoothing: int):
        """Initialize with periods"""
    
    def calculate(self, candles: List[Candle]) -> Dict[datetime, float]:
        """Calculate %K values"""
    
    def get_k_values(self) -> Dict[datetime, float]:
        """Get %K line"""
    
    def get_d_values(self) -> Dict[datetime, float]:
        """Get %D signal line"""
```

## Data Models

### Enhanced DSL Configuration

```python
@dataclass
class IndicatorInstance:
    type: str  # "STOCHASTIC", "RSI", etc.
    alias: str  # "fast", "slow", etc.
    params: Dict[str, Any]  # {"k_period": 9, ...}

@dataclass
class ZoneCondition:
    all_above: Optional[float]
    all_below: Optional[float]
    indicators: List[str]  # List of aliases

@dataclass
class CrossoverTrigger:
    indicator: str  # Alias
    crosses_above: Optional[float]
    crosses_below: Optional[float]

@dataclass
class RotationCondition:
    zone: ZoneCondition
    trigger: CrossoverTrigger

@dataclass
class AdvancedDSLConfig:
    name: str
    version: str
    description: str
    indicators: List[IndicatorInstance]
    conditions: Dict[str, RotationCondition]
    risk_management: Dict[str, float]
```

### Stochastic Quad Rotation Configuration

```json
{
  "name": "Stochastic Quad Rotation",
  "version": "1.0.0",
  "description": "Multi-timeframe stochastic rotation strategy",
  "indicators": [
    {
      "type": "STOCHASTIC",
      "alias": "fast",
      "params": {"k_period": 9, "k_smoothing": 1, "d_smoothing": 3}
    },
    {
      "type": "STOCHASTIC",
      "alias": "med_fast",
      "params": {"k_period": 14, "k_smoothing": 1, "d_smoothing": 3}
    },
    {
      "type": "STOCHASTIC",
      "alias": "med_slow",
      "params": {"k_period": 40, "k_smoothing": 1, "d_smoothing": 4}
    },
    {
      "type": "STOCHASTIC",
      "alias": "slow",
      "params": {"k_period": 60, "k_smoothing": 1, "d_smoothing": 10}
    }
  ],
  "conditions": {
    "buy": {
      "type": "rotation",
      "zone": {
        "all_below": 20,
        "indicators": ["fast", "med_fast", "med_slow", "slow"]
      },
      "trigger": {
        "indicator": "fast",
        "crosses_above": 20
      }
    },
    "sell": {
      "type": "rotation",
      "zone": {
        "all_above": 80,
        "indicators": ["fast", "med_fast", "med_slow", "slow"]
      },
      "trigger": {
        "indicator": "fast",
        "crosses_below": 80
      }
    }
  },
  "risk_management": {
    "stop_loss_pips": 15,
    "take_profit_pips": 25
  }
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Indicator Instance Uniqueness
*For any* DSL strategy with multiple indicator instances, each alias must be unique and resolve to exactly one indicator configuration.
**Validates: Requirements 1.1, 1.2**

### Property 2: Zone Condition Correctness
*For any* zone condition specifying "all_below" threshold, all specified indicators must have values below that threshold for the condition to be true.
**Validates: Requirements 3.1, 3.2**

### Property 3: Crossover Detection Accuracy
*For any* crossover trigger, a signal should only be generated when the previous value was on one side of the threshold and the current value is on the other side.
**Validates: Requirements 4.1, 4.2, 4.4**

### Property 4: Stochastic Calculation Bounds
*For any* stochastic calculation, the %K and %D values must be between 0 and 100 inclusive.
**Validates: Requirements 5.1, 5.2, 5.3**

### Property 5: Rotation Signal Precision
*For any* rotation signal, it must only trigger when both the zone condition is met AND the crossover occurs, not either condition alone.
**Validates: Requirements 6.2, 6.3**

### Property 6: Backward Compatibility
*For any* existing DSL strategy (MA Crossover, MACD Crossover), the enhanced system must produce identical results to the current system.
**Validates: Requirements 9.1, 9.2**

### Property 7: State Consistency
*For any* crossover detection, the previous value stored must match the current value from the previous candle.
**Validates: Requirements 4.5, 6.5**

### Property 8: Chart Rendering Completeness
*For any* strategy with N indicator instances, the chart must display exactly N distinct lines with unique colors.
**Validates: Requirements 7.1, 7.2**

## Error Handling

### Validation Errors
- **Invalid Indicator Alias**: Throw `DSLValidationError` with message indicating duplicate or missing alias
- **Unknown Indicator Type**: Throw `DSLValidationError` listing available indicator types
- **Invalid Zone Specification**: Throw `DSLValidationError` if both all_above and all_below are specified
- **Missing Trigger Indicator**: Throw `DSLValidationError` if trigger references non-existent alias

### Runtime Errors
- **Insufficient Data**: Return None signal if not enough candles for indicator calculation
- **Missing Previous Value**: Initialize crossover detector state on first candle
- **Indicator Calculation Failure**: Log error and skip signal generation for that candle
- **Division by Zero**: Handle zero-range stochastic calculation by returning 50 (neutral)

### Chart Rendering Errors
- **Too Many Indicators**: Warn if more than 6 indicators in subplot (performance concern)
- **Color Exhaustion**: Cycle through color palette if more indicators than colors
- **Subplot Overflow**: Automatically adjust subplot height if content doesn't fit

## Testing Strategy

### Unit Tests
- Test `StochasticCalculator` with known input/output pairs
- Test `CrossoverDetector` with sequences of values crossing thresholds
- Test `ConditionEvaluator` with various boolean logic combinations
- Test `MultiIndicatorManager` instance registration and lookup
- Test DSL schema validation with valid and invalid configurations

### Integration Tests
- Test complete Stochastic Quad Rotation strategy on sample data
- Test backward compatibility with existing MA Crossover strategy
- Test chart rendering with 4 stochastic instances
- Test backtest execution end-to-end

### Property-Based Tests
- Generate random indicator configurations and verify uniqueness (Property 1)
- Generate random stochastic values and verify 0-100 bounds (Property 4)
- Generate random crossover sequences and verify detection accuracy (Property 3)
- Generate random zone conditions and verify all-indicators logic (Property 2)

## Performance Considerations

### Optimization Strategies
1. **Indicator Caching**: Calculate each indicator once per candle, cache results
2. **Short-Circuit Evaluation**: Exit zone checks early if any indicator fails
3. **Lazy Calculation**: Only calculate indicators needed for current strategy
4. **Efficient State Storage**: Store only previous value, not full history

### Performance Targets
- **Indicator Calculation**: < 1ms per indicator per candle
- **Condition Evaluation**: < 0.1ms per condition
- **Crossover Detection**: < 0.05ms per check
- **Total Overhead**: < 10% compared to simple strategies

### Memory Management
- Limit state storage to O(N) where N = number of indicators
- Clear old indicator values after chart generation
- Use generators for large candle datasets
- Avoid copying full candle lists

## Migration Path

### Phase 1: Add New Components (Non-Breaking)
- Add `StochasticCalculator` to indicator registry
- Add `MultiIndicatorManager` class
- Add `ConditionEvaluator` class
- Add `CrossoverDetector` class

### Phase 2: Extend DSL Strategy (Backward Compatible)
- Detect advanced vs simple strategy format
- Route simple strategies through existing code path
- Route advanced strategies through new components
- Maintain identical behavior for existing strategies

### Phase 3: Implement Stochastic Quad Rotation
- Create JSON configuration file
- Test with sample data
- Verify chart rendering
- Run bulk backtests for validation

### Phase 4: Documentation and Examples
- Document new DSL syntax
- Provide migration examples
- Create tutorial for advanced strategies
- Update API documentation

## Dependencies

### Existing Components (No Changes)
- `TradingStrategy` interface
- `BacktestEngine`
- `DataConnector`
- `StrategyRegistry`

### Modified Components
- `DSLStrategy` class (enhanced logic)
- `IndicatorRegistry` (add Stochastic)
- `ChartEngine` (multi-line subplot support)
- DSL schema validator (extended validation)

### New Components
- `StochasticCalculator`
- `MultiIndicatorManager`
- `ConditionEvaluator`
- `CrossoverDetector`

## Future Enhancements

### Potential Extensions
1. **More Indicator Types**: Bollinger Bands, ATR, ADX
2. **Advanced Logic**: NOT operator, nested conditions
3. **Time-Based Filters**: Only trade during specific hours
4. **Volume Conditions**: Require minimum volume for signals
5. **Multi-Timeframe**: Reference higher timeframe indicators
6. **Dynamic Parameters**: Adjust SL/TP based on volatility
