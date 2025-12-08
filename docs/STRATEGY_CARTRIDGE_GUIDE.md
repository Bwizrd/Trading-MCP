# 🎮 Strategy Cartridge Development Guide

This guide walks you through creating new trading strategy "cartridges" that plug into the Universal Backtest Engine. Think of it like developing a game cartridge that works in any compatible console.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Strategy Interface Overview](#strategy-interface-overview)
3. [Step-by-Step Tutorial](#step-by-step-tutorial)
4. [Advanced Features](#advanced-features)
5. [Testing Your Strategy](#testing-your-strategy)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### 1. Create Strategy File
Create a new Python file in `shared/strategies/`:
```bash
touch shared/strategies/my_new_strategy.py
```

### 2. Basic Template
```python
#!/usr/bin/env python3
"""
My New Strategy - Description of what it does
"""

from typing import Dict, Any, List, Optional
from datetime import time

from shared.models import Candle, TradeDirection
from shared.strategy_interface import TradingStrategy, StrategyContext, Signal, SignalStrength


class MyNewStrategy(TradingStrategy):
    """
    Brief description of your strategy logic.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize strategy-specific variables here
    
    def get_name(self) -> str:
        return "My New Strategy"
    
    def get_description(self) -> str:
        return "Detailed description of what your strategy does and how it works."
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def requires_indicators(self) -> List[str]:
        return ["SMA20", "RSI"]  # List indicators your strategy needs
    
    def generate_signal(self, context: StrategyContext) -> Optional[Signal]:
        """
        Your main trading logic goes here.
        
        Args:
            context: Current market context with candle, indicators, position info
            
        Returns:
            Signal or None if no signal should be generated
        """
        # Your signal generation logic here
        return None
```

### 3. Test Your Strategy
Your strategy will be auto-discovered by the registry. Test it:
```python
python demo_strategy_backtest.py
```

---

## 🏗️ Strategy Interface Overview

### Required Methods

Every strategy cartridge must implement these methods:

#### `get_name() -> str`
Return a unique name for your strategy.
```python
def get_name(self) -> str:
    return "RSI Reversal"
```

#### `get_description() -> str`
Provide a clear description of your strategy logic.
```python
def get_description(self) -> str:
    return "Buys when RSI is oversold (<30) and sells when overbought (>70)"
```

#### `get_version() -> str`
Version your strategy for tracking changes.
```python
def get_version(self) -> str:
    return "1.0.0"
```

#### `requires_indicators() -> List[str]`
List technical indicators your strategy needs.
```python
def requires_indicators(self) -> List[str]:
    return ["RSI", "SMA20", "VWAP"]
```

#### `generate_signal(context: StrategyContext) -> Optional[Signal]`
**Core method** - Your main trading logic.
```python
def generate_signal(self, context: StrategyContext) -> Optional[Signal]:
    # Access current candle
    candle = context.current_candle
    
    # Access indicators
    rsi = context.get_indicator("RSI")
    sma = context.get_indicator("SMA20")
    
    # Check if we already have a position
    if context.current_position:
        return None
    
    # Generate BUY signal
    if rsi < 30 and candle.close > sma:
        return Signal(
            direction=TradeDirection.BUY,
            price=candle.close,
            strength=SignalStrength.STRONG,
            confidence=0.8,
            reason=f"RSI oversold ({rsi:.1f}) above SMA",
            timestamp=candle.timestamp
        )
    
    return None
```

### Optional Callback Methods

#### `on_trade_opened(trade, context: StrategyContext)`
Called when a trade is opened based on your signal.
```python
def on_trade_opened(self, trade, context: StrategyContext) -> None:
    print(f"Trade opened: {trade.direction.value} {context.symbol} at {trade.entry_price}")
```

#### `on_trade_closed(trade, context: StrategyContext)`
Called when a trade is closed.
```python
def on_trade_closed(self, trade, context: StrategyContext) -> None:
    result = "WIN" if trade.pips > 0 else "LOSS"
    print(f"Trade closed: {result} - {trade.pips:+.1f} pips")
```

#### `on_candle_processed(context: StrategyContext)`
Called after each candle is processed.
```python
def on_candle_processed(self, context: StrategyContext) -> None:
    # Useful for state management or logging
    pass
```

---

## 📚 Step-by-Step Tutorial: RSI Reversal Strategy

Let's build a complete RSI reversal strategy step by step.

### Step 1: Create the File
```bash
touch shared/strategies/rsi_reversal_strategy.py
```

### Step 2: Basic Structure
```python
#!/usr/bin/env python3
"""
RSI Reversal Strategy

Buys when RSI is oversold and sells when RSI is overbought.
Classic mean reversion approach.
"""

from typing import Dict, Any, List, Optional
from datetime import time

from shared.models import Candle, TradeDirection
from shared.strategy_interface import TradingStrategy, StrategyContext, Signal, SignalStrength


class RSIReversalStrategy(TradingStrategy):
    """
    RSI-based reversal strategy for mean reversion trading.
    
    Entry Rules:
    - BUY when RSI < oversold_threshold (default 30)
    - SELL when RSI > overbought_threshold (default 70)
    """
    
    def __init__(self):
        super().__init__()
        self.oversold_threshold = 30
        self.overbought_threshold = 70
        self.min_confirmation_bars = 1
```

### Step 3: Implement Required Methods
```python
    def get_name(self) -> str:
        return "RSI Reversal"
    
    def get_description(self) -> str:
        return (
            "Mean reversion strategy based on RSI levels. "
            "Buys when RSI indicates oversold conditions (<30) "
            "and sells when overbought (>70). Expects price to "
            "revert back to mean after extreme RSI readings."
        )
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "oversold_threshold": 30,
            "overbought_threshold": 70,
            "rsi_period": 14,
            "min_confirmation_bars": 1,
            "max_signals_per_day": 2
        }
    
    def requires_indicators(self) -> List[str]:
        return ["RSI"]  # We need RSI indicator
```

### Step 4: Implement Core Logic
```python
    def initialize(self, parameters: Dict[str, Any] = None) -> None:
        """Initialize strategy with parameters."""
        super().initialize(parameters)
        
        # Get parameters with defaults
        params = self.get_parameters()
        self.oversold_threshold = params.get("oversold_threshold", 30)
        self.overbought_threshold = params.get("overbought_threshold", 70)
        self.min_confirmation_bars = params.get("min_confirmation_bars", 1)
        self.max_signals_per_day = params.get("max_signals_per_day", 2)
        
        # State tracking
        self.signals_today = 0
        self.last_signal_date = None
    
    def generate_signal(self, context: StrategyContext) -> Optional[Signal]:
        """
        Generate RSI reversal signals.
        
        Args:
            context: Current market context
            
        Returns:
            Signal or None
        """
        candle = context.current_candle
        
        # Skip if already in position
        if context.current_position:
            return None
        
        # Get RSI value
        rsi = context.get_indicator("RSI")
        if rsi is None:
            return None
        
        # Check daily signal limit
        current_date = candle.timestamp.date()
        if current_date != self.last_signal_date:
            self.signals_today = 0
            self.last_signal_date = current_date
        
        if self.signals_today >= self.max_signals_per_day:
            return None
        
        # Generate signals based on RSI levels
        signal = None
        current_price = candle.close
        
        # Oversold condition - BUY signal
        if rsi <= self.oversold_threshold:
            strength = self._calculate_signal_strength(rsi, "oversold")
            
            signal = Signal(
                direction=TradeDirection.BUY,
                price=current_price,
                strength=strength,
                confidence=self._calculate_confidence(rsi, "oversold"),
                reason=f"RSI Reversal: Oversold at {rsi:.1f} (threshold: {self.oversold_threshold})",
                timestamp=candle.timestamp,
                metadata={
                    "rsi_value": rsi,
                    "threshold": self.oversold_threshold,
                    "signal_type": "oversold_reversal"
                }
            )
        
        # Overbought condition - SELL signal
        elif rsi >= self.overbought_threshold:
            strength = self._calculate_signal_strength(rsi, "overbought")
            
            signal = Signal(
                direction=TradeDirection.SELL,
                price=current_price,
                strength=strength,
                confidence=self._calculate_confidence(rsi, "overbought"),
                reason=f"RSI Reversal: Overbought at {rsi:.1f} (threshold: {self.overbought_threshold})",
                timestamp=candle.timestamp,
                metadata={
                    "rsi_value": rsi,
                    "threshold": self.overbought_threshold,
                    "signal_type": "overbought_reversal"
                }
            )
        
        if signal:
            self.signals_today += 1
        
        return signal
```

### Step 5: Helper Methods
```python
    def _calculate_signal_strength(self, rsi: float, signal_type: str) -> SignalStrength:
        """Calculate signal strength based on RSI distance from threshold."""
        if signal_type == "oversold":
            # Stronger signal the lower RSI goes
            if rsi <= 20:
                return SignalStrength.VERY_STRONG
            elif rsi <= 25:
                return SignalStrength.STRONG
            else:
                return SignalStrength.MODERATE
        
        else:  # overbought
            # Stronger signal the higher RSI goes
            if rsi >= 80:
                return SignalStrength.VERY_STRONG
            elif rsi >= 75:
                return SignalStrength.STRONG
            else:
                return SignalStrength.MODERATE
    
    def _calculate_confidence(self, rsi: float, signal_type: str) -> float:
        """Calculate confidence level (0.0 to 1.0)."""
        if signal_type == "oversold":
            # Higher confidence for lower RSI
            return max(0.5, (30 - rsi) / 30)
        else:  # overbought
            # Higher confidence for higher RSI
            return max(0.5, (rsi - 70) / 30)
```

### Step 6: Optional Callbacks
```python
    def on_trade_opened(self, trade, context: StrategyContext) -> None:
        """Called when trade is opened."""
        rsi = context.get_indicator("RSI")
        print(f"RSI Reversal: {trade.direction.value} {context.symbol} at {trade.entry_price:.5f}")
        print(f"  RSI: {rsi:.1f}, Stop: {trade.stop_loss:.5f}, Target: {trade.take_profit:.5f}")
    
    def on_trade_closed(self, trade, context: StrategyContext) -> None:
        """Called when trade is closed."""
        result_emoji = "✅" if trade.pips > 0 else "❌"
        print(f"RSI Reversal: Trade closed {result_emoji}")
        print(f"  {trade.direction.value} {trade.entry_price:.5f} → {trade.exit_price:.5f}")
        print(f"  Result: {trade.pips:+.1f} pips")
```

---

## 🎯 Advanced Features

### Custom Parameters
Allow users to customize your strategy:

```python
def get_default_parameters(self) -> Dict[str, Any]:
    return {
        "rsi_period": 14,
        "oversold_level": 30,
        "overbought_level": 70,
        "use_sma_filter": True,
        "sma_period": 20,
        "min_trend_strength": 0.5
    }

def initialize(self, parameters: Dict[str, Any] = None) -> None:
    super().initialize(parameters)
    params = self.get_parameters()
    
    self.rsi_period = params.get("rsi_period", 14)
    self.oversold_level = params.get("oversold_level", 30)
    self.use_sma_filter = params.get("use_sma_filter", True)
    # ... etc
```

### Multiple Indicators
Use multiple indicators for better signals:

```python
def requires_indicators(self) -> List[str]:
    return ["RSI", "SMA20", "VWAP", "BB20"]

def generate_signal(self, context: StrategyContext) -> Optional[Signal]:
    rsi = context.get_indicator("RSI")
    sma = context.get_indicator("SMA20")
    vwap = context.get_indicator("VWAP")
    bb_upper, bb_lower = context.get_indicator("BB20")  # Bollinger Bands
    
    # Complex multi-indicator logic
    if (rsi < 30 and 
        candle.close > sma and 
        candle.close > vwap and
        candle.low <= bb_lower):
        # Strong BUY signal with multiple confirmations
        return Signal(...)
```

### State Management
Track strategy state across candles:

```python
def __init__(self):
    super().__init__()
    self.trend_direction = None
    self.consecutive_signals = 0
    self.last_signal_strength = None
    self.daily_pnl = 0.0

def on_candle_processed(self, context: StrategyContext) -> None:
    # Update trend direction
    sma_fast = context.get_indicator("SMA10")
    sma_slow = context.get_indicator("SMA20")
    
    if sma_fast and sma_slow:
        self.trend_direction = "UP" if sma_fast > sma_slow else "DOWN"
    
    # Reset daily counters at start of new day
    if context.current_candle.timestamp.hour == 0:
        self.daily_pnl = 0.0
```

### Time-Based Logic
Add time restrictions to your strategy:

```python
from datetime import time

def __init__(self):
    super().__init__()
    self.trading_start = time(8, 0)   # 8:00 AM
    self.trading_end = time(16, 0)    # 4:00 PM
    self.no_trade_times = [
        (time(11, 30), time(12, 30)),  # Lunch break
    ]

def generate_signal(self, context: StrategyContext) -> Optional[Signal]:
    current_time = context.current_candle.timestamp.time()
    
    # Check trading hours
    if not (self.trading_start <= current_time <= self.trading_end):
        return None
    
    # Check no-trade periods
    for start_time, end_time in self.no_trade_times:
        if start_time <= current_time <= end_time:
            return None
    
    # Your signal logic here...
```

---

## 🧪 Testing Your Strategy

### 1. Quick Test
```python
# Test strategy creation
from shared.strategy_registry import StrategyRegistry

registry = StrategyRegistry()
strategies = registry.list_strategies()
print(f"Available strategies: {strategies}")

# Test your strategy
my_strategy = registry.create_strategy("RSI Reversal")
print(f"Strategy: {my_strategy.get_name()}")
print(f"Indicators needed: {my_strategy.requires_indicators()}")
```

### 2. Demo Script Test
```python
python demo_strategy_backtest.py
# Select your strategy from the menu
```

### 3. MCP Server Test
Add to Claude Desktop config and use:
- `list_strategy_cartridges` - Should show your strategy
- `get_strategy_info` with your strategy name
- `run_strategy_backtest` with your strategy

### 4. Unit Testing
Create a test file:

```python
# test_my_strategy.py
import unittest
from datetime import datetime
from shared.strategies.rsi_reversal_strategy import RSIReversalStrategy
from shared.strategy_interface import StrategyContext
from shared.models import Candle, TradeDirection

class TestRSIReversalStrategy(unittest.TestCase):
    
    def setUp(self):
        self.strategy = RSIReversalStrategy()
        self.strategy.initialize()
    
    def test_oversold_signal(self):
        # Create test context with low RSI
        candle = Candle(
            timestamp=datetime.now(),
            open=1.1000, high=1.1010, low=1.0990, close=1.1005, volume=1000
        )
        
        context = StrategyContext(
            current_candle=candle,
            symbol="EURUSD",
            timeframe="30m",
            indicators={"RSI": 25.0}  # Oversold
        )
        
        signal = self.strategy.generate_signal(context)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.direction, TradeDirection.BUY)
        self.assertIn("Oversold", signal.reason)

if __name__ == '__main__':
    unittest.main()
```

---

## 📋 Best Practices

### 1. Strategy Design
- **Keep it simple**: Start with basic logic, add complexity gradually
- **Single responsibility**: Each strategy should have one clear purpose
- **Document thoroughly**: Clear descriptions and comments
- **Version control**: Use semantic versioning (1.0.0, 1.1.0, etc.)

### 2. Signal Generation
- **Validate inputs**: Always check if indicators are available
- **Avoid overtrading**: Implement position limits and timing restrictions
- **Risk management**: Consider market conditions and volatility
- **Clear reasoning**: Provide detailed reasons for each signal

### 3. Code Quality
- **Type hints**: Use proper type annotations
- **Error handling**: Handle missing data gracefully
- **Consistent naming**: Follow Python naming conventions
- **Modular code**: Break complex logic into helper methods

### 4. Testing
- **Test edge cases**: Missing indicators, extreme values, no data
- **Backtest thoroughly**: Test on different timeframes and symbols
- **Compare results**: Validate against expected behavior
- **Performance test**: Ensure reasonable execution speed

### 5. Parameters
- **Sensible defaults**: Choose good default values
- **Validation**: Validate parameter ranges in `initialize()`
- **Documentation**: Document what each parameter does
- **Flexibility**: Allow customization without breaking core logic

---

## 🔍 Available Indicators

Your strategy can use these pre-built indicators:

### Trend Indicators
- **`VWAP`**: Volume-Weighted Average Price
- **`SMA20`**, **`SMA50`**, **`SMA200`**: Simple Moving Averages
- **`EMA20`**, **`EMA50`**: Exponential Moving Averages

### Oscillators
- **`RSI`**: Relative Strength Index (14-period)
- **`RSI21`**: RSI with 21-period

### Volatility
- **`BB20`**: Bollinger Bands (20-period, 2 standard deviations)

### Adding Custom Indicators
To add a new indicator, edit `shared/indicators.py`:

```python
class MyCustomIndicator(IndicatorCalculator):
    def __init__(self, period: int = 20):
        self.period = period
    
    def calculate(self, candles: List[Candle]) -> Dict[datetime, float]:
        # Your calculation logic
        pass

# Register in IndicatorRegistry.__init__()
self.register("MyCustom", MyCustomIndicator(20))
```

---

## 🐛 Troubleshooting

### Strategy Not Appearing
**Problem**: Strategy doesn't show up in `list_strategy_cartridges`

**Solutions**:
1. Check file is in `shared/strategies/` directory
2. Ensure class inherits from `TradingStrategy`
3. Verify all required methods are implemented
4. Check for syntax errors in the file
5. Restart the registry: `registry.reload_strategies()`

### Import Errors
**Problem**: `ModuleNotFoundError` or import issues

**Solutions**:
1. Check file paths are correct
2. Ensure `__init__.py` exists in directories
3. Verify Python path includes project root
4. Check for circular imports

### Signal Generation Issues
**Problem**: Strategy doesn't generate expected signals

**Solutions**:
1. Add debug prints in `generate_signal()`
2. Check indicator values: `print(f"RSI: {context.get_indicator('RSI')}")`
3. Verify your logic conditions
4. Test with known data where signals should trigger

### Indicator Missing
**Problem**: `context.get_indicator("NAME")` returns `None`

**Solutions**:
1. Check indicator name matches exactly (case-sensitive)
2. Verify indicator is in `requires_indicators()` list
3. Ensure indicator is registered in `IndicatorRegistry`
4. Check if enough historical data for indicator calculation

### Performance Issues
**Problem**: Strategy runs slowly

**Solutions**:
1. Avoid complex calculations in `generate_signal()`
2. Cache expensive computations
3. Use vectorized operations for bulk data processing
4. Profile code to identify bottlenecks

---

## 📖 Example Strategies

### Simple Moving Average Crossover
```python
class SMACrossoverStrategy(TradingStrategy):
    def requires_indicators(self) -> List[str]:
        return ["SMA20", "SMA50"]
    
    def generate_signal(self, context: StrategyContext) -> Optional[Signal]:
        sma_fast = context.get_indicator("SMA20")
        sma_slow = context.get_indicator("SMA50")
        
        if not sma_fast or not sma_slow:
            return None
        
        if context.current_position:
            return None
        
        # Golden cross - BUY
        if sma_fast > sma_slow:
            # Check if this is a recent crossover
            if hasattr(self, 'last_fast_sma') and self.last_fast_sma <= self.last_slow_sma:
                return Signal(
                    direction=TradeDirection.BUY,
                    price=context.current_candle.close,
                    strength=SignalStrength.MODERATE,
                    confidence=0.7,
                    reason="Golden Cross: Fast SMA crossed above Slow SMA"
                )
        
        # Store for next comparison
        self.last_fast_sma = sma_fast
        self.last_slow_sma = sma_slow
        
        return None
```

### Bollinger Bands Breakout
```python
class BollingerBreakoutStrategy(TradingStrategy):
    def requires_indicators(self) -> List[str]:
        return ["BB20", "SMA20"]
    
    def generate_signal(self, context: StrategyContext) -> Optional[Signal]:
        bb_data = context.get_indicator("BB20")
        if not bb_data:
            return None
        
        candle = context.current_candle
        upper_band, lower_band = bb_data  # Assuming BB returns (upper, lower)
        
        # Breakout above upper band - BUY
        if candle.close > upper_band:
            return Signal(
                direction=TradeDirection.BUY,
                price=candle.close,
                strength=SignalStrength.STRONG,
                confidence=0.8,
                reason=f"Bollinger Breakout: Price {candle.close:.5f} above upper band {upper_band:.5f}"
            )
        
        # Breakdown below lower band - SELL
        elif candle.close < lower_band:
            return Signal(
                direction=TradeDirection.SELL,
                price=candle.close,
                strength=SignalStrength.STRONG,
                confidence=0.8,
                reason=f"Bollinger Breakdown: Price {candle.close:.5f} below lower band {lower_band:.5f}"
            )
        
        return None
```

---

## 🚀 Next Steps

1. **Create your first strategy** using the RSI example above
2. **Test thoroughly** with different market conditions
3. **Add custom parameters** for flexibility
4. **Implement multiple timeframe analysis**
5. **Create strategy combinations** (portfolio approach)
6. **Share your strategies** with the community

## 💡 Strategy Ideas

- **Mean Reversion**: RSI, Stochastic, CCI-based reversals
- **Trend Following**: Moving average systems, breakouts, momentum
- **Volatility**: Bollinger Band strategies, ATR-based systems
- **Time-based**: Day/night sessions, economic calendar events
- **Multi-timeframe**: Higher timeframe trend + lower timeframe entry
- **Machine Learning**: Integrate ML models for signal generation

---

Ready to build your first strategy cartridge? The universal backtest engine is waiting for your trading ideas! 🎮✨