#!/usr/bin/env python3
"""
DSL Strategy Implementation

This class implements the TradingStrategy interface to execute JSON-configured
trading strategies using the Domain Specific Language (DSL).

CRITICAL: This extends the existing modular architecture WITHOUT breaking anything.
It uses the same DataConnector, TradingStrategy interface, and MCP system.
"""

from typing import Dict, Any, List, Optional
from datetime import time, datetime, date
import re

# Indicator calculation imports are done conditionally in methods that need them

from shared.models import Candle, TradeDirection
from shared.strategy_interface import TradingStrategy, StrategyContext, Signal, SignalStrength
from .schema_validator import validate_dsl_strategy, DSLValidationError


class DSLStrategy(TradingStrategy):
    """
    DSL Strategy - JSON-Configured Trading Logic
    
    This strategy executes trading logic defined in JSON configuration files.
    It implements the TradingStrategy interface so it works seamlessly with
    the universal backtest engine.
    
    Key Features:
    - Time-based conditions (reference_time vs signal_time)
    - Price comparisons (>, <, ==, etc.)
    - Configurable risk management
    - Plugs into existing modular architecture
    """
    
    def __init__(self, dsl_config: Dict[str, Any]):
        """
        Initialize DSL strategy with JSON configuration.
        
        Args:
            dsl_config: Validated DSL strategy configuration
        """
        # Validate configuration first
        try:
            validate_dsl_strategy(dsl_config)
        except DSLValidationError as e:
            raise ValueError(f"Invalid DSL configuration: {e}")
        
        # Store DSL configuration BEFORE calling super().__init__()
        # because super().__init__() calls get_name() which needs dsl_config
        self.dsl_config = dsl_config
        
        super().__init__()
        
        # Determine strategy type
        self.is_indicator_based = bool("indicators" in dsl_config and dsl_config["indicators"])
        
        if self.is_indicator_based:
            # Indicator-based strategy initialization
            self._init_indicator_based(dsl_config)
        else:
            # Time-based strategy initialization (original logic)
            self._init_time_based(dsl_config)
        
        # Common initialization for both types
        # Parse conditions
        self.buy_condition = dsl_config["conditions"]["buy"]["compare"]
        self.sell_condition = dsl_config["conditions"]["sell"]["compare"]
        
        # Parse risk management
        risk_mgmt = dsl_config["risk_management"]
        self.stop_loss_pips = risk_mgmt["stop_loss_pips"]
        self.take_profit_pips = risk_mgmt["take_profit_pips"]
        self.max_daily_trades = risk_mgmt.get("max_daily_trades", 1)
        self.min_pip_distance = risk_mgmt.get("min_pip_distance", 0.0001)
        self.execution_window_minutes = risk_mgmt.get("execution_window_minutes", 1440)
        
        # Strategy state
        self.daily_trade_count = 0
        self.last_trade_date = None
        
    def _init_time_based(self, dsl_config: Dict[str, Any]) -> None:
        """Initialize time-based strategy (original logic)."""
        # Parse timing configuration
        timing = dsl_config["timing"]
        self.reference_time = self._parse_time(timing["reference_time"])
        self.signal_time = self._parse_time(timing["signal_time"])
        self.reference_price_type = timing["reference_price"]
        
        # Time-based strategy state
        self.reference_price = None
        self.last_reference_date = None
    
    def _init_indicator_based(self, dsl_config: Dict[str, Any]) -> None:
        """Initialize indicator-based strategy."""
        # No timing fields for indicator-based strategies
        self.reference_time = None
        self.signal_time = None
        self.reference_price_type = None
        self.reference_price = None
        self.last_reference_date = None
        
        # Indicator-based strategy state
        self.candle_history = []
        self.indicator_values = {}
        self.previous_indicator_values = {}
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string (HH:MM) to time object."""
        hour, minute = map(int, time_str.split(":"))
        return time(hour, minute)
    
    def get_name(self) -> str:
        return self.dsl_config["name"]
    
    def get_description(self) -> str:
        return self.dsl_config["description"]
    
    def get_version(self) -> str:
        return self.dsl_config["version"]
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Return parameters from DSL config."""
        return self.dsl_config.get("parameters", {})
    
    def get_execution_window_minutes(self) -> int:
        """Return execution window duration in minutes."""
        return getattr(self, 'execution_window_minutes', 1440)
    
    def requires_indicators(self) -> List[str]:
        """DSL strategies don't require indicators by default."""
        return []
    
    def get_indicator_series(self, candles: List) -> Dict[str, List[float]]:
        """
        Calculate full indicator series for charting.
        Returns time series data for all configured indicators.
        """
        import pandas as pd
        import ta
        
        if not candles or not hasattr(self, 'dsl_config') or 'indicators' not in self.dsl_config:
            return {}
        
        # Convert candles to DataFrame
        df = pd.DataFrame([{
            'timestamp': candle.timestamp,
            'open': candle.open,
            'high': candle.high, 
            'low': candle.low,
            'close': candle.close,
            'volume': candle.volume
        } for candle in candles])
        
        indicator_series = {}
        
        # Calculate full series for each indicator
        for indicator in self.dsl_config['indicators']:
            ind_type = indicator['type']
            period = indicator['period']
            alias = indicator['alias']
            
            try:
                if ind_type == 'SMA' and len(df) >= period:
                    sma_series = ta.trend.sma_indicator(df['close'], window=period)
                    indicator_series[f"{alias}"] = sma_series.fillna(0).tolist()
                elif ind_type == 'EMA' and len(df) >= period:
                    ema_series = ta.trend.ema_indicator(df['close'], window=period)
                    indicator_series[f"{alias}"] = ema_series.fillna(0).tolist()
                elif ind_type == 'RSI' and len(df) >= period:
                    rsi_series = ta.momentum.rsi(df['close'], window=period)
                    indicator_series[f"{alias}"] = rsi_series.fillna(0).tolist()
            except Exception as e:
                import logging
                logging.warning(f"Error calculating {alias} series ({ind_type}): {e}")
        
        return indicator_series
    
    def generate_signal(self, context: StrategyContext) -> Optional[Signal]:
        """
        Generate trading signal based on DSL configuration.
        
        For time-based strategies:
        1. Capture reference price at reference_time
        2. At signal_time, compare current price to reference price
        3. Generate signal based on conditions
        
        For indicator-based strategies:
        1. Check indicator conditions every candle
        2. Generate signal based on crossovers or threshold conditions
        
        Args:
            context: Current market context
            
        Returns:
            Signal or None if no signal should be generated
        """
        candle = context.current_candle
        current_date = candle.timestamp.date()
        
        if self.is_indicator_based:
            return self._generate_indicator_signal(context)
        else:
            return self._generate_time_based_signal(context)
            
    def _generate_indicator_signal(self, context: StrategyContext) -> Optional[Signal]:
        """Generate signal for indicator-based strategies."""
        candle = context.current_candle
        current_date = candle.timestamp.date()
        
        # DEBUG: Write to file to confirm this code is running
        with open('/tmp/dsl_debug.log', 'a') as f:
            f.write(f"_generate_indicator_signal called at {candle.timestamp}, has_indicators={bool(self.indicator_values)}\n")
        
        # Check daily trade limit
        if self.last_trade_date == current_date and self.daily_trade_count >= self.max_daily_trades:
            return None
            
        # Skip if already in position
        if context.current_position:
            return None
            
        # Need indicators calculated
        if not self.indicator_values:
            return None
            
        # Evaluate indicator conditions (includes crossover detection)
        signal_direction = self._evaluate_indicator_conditions()
        
        # DEBUG: Log signal detection
        if signal_direction:
            with open('/tmp/dsl_debug.log', 'a') as f:
                f.write(f"SIGNAL DETECTED: {signal_direction} at {candle.timestamp}\n")
        
        if signal_direction is None:
            return None
            
        # Calculate signal strength - for indicators, use distance between MAs
        strength = self._calculate_indicator_signal_strength()
        
        # Create signal
        signal = Signal(
            direction=signal_direction,
            strength=strength,
            confidence=0.8,  # High confidence for crossover signals
            price=candle.close,
            reason=self._generate_indicator_signal_reason(signal_direction),
            timestamp=candle.timestamp,
            metadata={
                "strategy_type": "indicator_crossover",
                "indicators": dict(self.indicator_values)
            }
        )
        
        # DEBUG: Log signal creation
        with open('/tmp/dsl_debug.log', 'a') as f:
            f.write(f"SIGNAL CREATED: {signal.direction} @ {signal.price} at {signal.timestamp}\n")
        
        # Update trade tracking
        if self.last_trade_date != current_date:
            self.daily_trade_count = 0
            self.last_trade_date = current_date
        
        self.daily_trade_count += 1
        
        # DEBUG: Log signal return
        with open('/tmp/dsl_debug.log', 'a') as f:
            f.write(f"RETURNING SIGNAL: {signal}\n")
        
        return signal
        
    def _generate_time_based_signal(self, context: StrategyContext) -> Optional[Signal]:
        """Generate signal for time-based strategies (original logic)."""
        candle = context.current_candle
        current_time = candle.timestamp.time()
        current_date = candle.timestamp.date()

        # Debug: Log key timing events (commented to avoid JSON contamination)
        # candle_date_str = candle.timestamp.strftime('%Y-%m-%d')
        # candle_time_str = candle.timestamp.strftime('%H:%M')
        # if candle_date_str in ['2025-11-10', '2025-11-11']:
        #     print(f"[DSL DEBUG] {candle_date_str} {candle_time_str}: ref_time={self.reference_time}, signal_time={self.signal_time}, ref_price={self.reference_price}")
        
        # Step 1: Capture reference price at reference_time
        if current_time == self.reference_time:
            self.reference_price = self._get_price_from_candle(candle, self.reference_price_type)
            self.last_reference_date = current_date
            # print(f"[DSL DEBUG] REFERENCE CAPTURED: {candle_date_str} {candle_time_str} @ {self.reference_price:.5f}")
            return None  # No signal at reference time, just capture price

        # Step 2: Generate signal at signal_time (only if we have reference price)
        if current_time != self.signal_time:
            return None

        # Must have reference price from earlier today
        if self.reference_price is None or self.last_reference_date != current_date:
            # print(f"[DSL DEBUG] NO REFERENCE: {candle_date_str} {candle_time_str}, ref_price={self.reference_price}, last_ref_date={self.last_reference_date}")
            return None        # Check daily trade limit
        if self.last_trade_date == current_date and self.daily_trade_count >= self.max_daily_trades:
            return None
        
        # Skip if already in position
        if context.current_position:
            return None
        
        # Get current price (signal price)
        signal_price = candle.close
        
        # Check minimum pip distance
        price_distance = abs(signal_price - self.reference_price)
        if price_distance < self.min_pip_distance:
            return None
        
        # Step 3: Evaluate conditions
        signal_direction = self._evaluate_conditions(signal_price, self.reference_price)
        
        # Debug prints commented to avoid JSON contamination
        # print(f"[DSL DEBUG] SIGNAL TIME: {candle_date_str} {candle_time_str}, signal_price={signal_price:.5f}, ref_price={self.reference_price:.5f}, direction={signal_direction}")
        
        if signal_direction is None:
            # print(f"[DSL DEBUG] NO SIGNAL: conditions not met")
            return None
        
        # Calculate signal strength based on price distance
        strength = self._calculate_signal_strength(price_distance, signal_price)
        
        # print(f"[DSL DEBUG] *** CREATING SIGNAL *** {str(signal_direction)} @ {signal_price:.5f} (strength: {str(strength)})")
        
        # Create signal with DSL metadata
        signal = Signal(
            direction=signal_direction,
            price=signal_price,
            strength=strength,
            confidence=strength.value,
            reason=self._generate_signal_reason(signal_direction, signal_price, self.reference_price),
            timestamp=candle.timestamp,
            metadata={
                "dsl_strategy": True,
                "reference_time": self.reference_time.strftime("%H:%M"),
                "signal_time": self.signal_time.strftime("%H:%M"),
                "reference_price": self.reference_price,
                "signal_price": signal_price,
                "price_distance": price_distance,
                "reference_price_type": self.reference_price_type,
                "condition_used": self.buy_condition if signal_direction == TradeDirection.BUY else self.sell_condition
            }
        )
        
        # Update trade tracking
        if self.last_trade_date != current_date:
            self.daily_trade_count = 0
            self.last_trade_date = current_date
        
        self.daily_trade_count += 1
        
        return signal
    
    def _get_price_from_candle(self, candle: Candle, price_type: str) -> float:
        """Extract specified price from candle."""
        if price_type == "open":
            return candle.open
        elif price_type == "high":
            return candle.high
        elif price_type == "low":
            return candle.low
        elif price_type == "close":
            return candle.close
        else:
            raise ValueError(f"Invalid price type: {price_type}")
    
    def _evaluate_conditions(self, signal_price: float, reference_price: float) -> Optional[TradeDirection]:
        """
        Evaluate DSL conditions to determine trade direction.
        
        Args:
            signal_price: Current market price
            reference_price: Reference price from earlier
            
        Returns:
            TradeDirection or None if no condition is met
        """
        if self.is_indicator_based:
            return self._evaluate_indicator_conditions()
        else:
            # Time-based strategy evaluation (original logic)
            eval_context = {
                "signal_price": signal_price,
                "reference_price": reference_price
            }
            
            # Check buy condition
            if self._evaluate_condition(self.buy_condition, eval_context):
                return TradeDirection.BUY
            
            # Check sell condition  
            if self._evaluate_condition(self.sell_condition, eval_context):
                return TradeDirection.SELL
            
            return None
            
    def _evaluate_indicator_conditions(self) -> Optional[TradeDirection]:
        """
        Evaluate indicator-based conditions with crossover detection.
        
        Returns:
            TradeDirection or None if no condition is met
        """
        # Need current and previous values for crossover detection
        if not self.indicator_values or not self.previous_indicator_values:
            return None
            
        # Check buy condition
        buy_config = self.dsl_config["conditions"]["buy"]
        if self._check_indicator_condition(buy_config):
            return TradeDirection.BUY
            
        # Check sell condition
        sell_config = self.dsl_config["conditions"]["sell"] 
        if self._check_indicator_condition(sell_config):
            return TradeDirection.SELL
            
        return None
        
    def _check_indicator_condition(self, condition_config: Dict[str, Any]) -> bool:
        """
        Check if an indicator-based condition is met, including crossover detection.
        
        Args:
            condition_config: Condition configuration from JSON
            
        Returns:
            bool: True if condition is met
        """
        compare_str = condition_config["compare"]
        needs_crossover = condition_config.get("crossover", False)
        
        # Evaluate current condition
        current_result = self._evaluate_condition(compare_str, self.indicator_values)
        
        if not needs_crossover:
            return current_result
            
        # For crossover, check that condition is true now but was false before
        if not current_result:
            return False
            
        # Check previous condition was false (crossover occurred)
        previous_result = self._evaluate_condition(compare_str, self.previous_indicator_values)
        return not previous_result
    
    def _evaluate_condition(self, condition_str: str, context: Dict[str, float]) -> bool:
        """
        Safely evaluate a condition string with given context.
        
        Args:
            condition_str: Condition to evaluate (e.g., "signal_price > reference_price")
            context: Dictionary with variable values
            
        Returns:
            bool: True if condition is met
        """
        try:
            # Replace variables with actual values
            expression = condition_str
            for var_name, var_value in context.items():
                if var_value is not None:
                    expression = expression.replace(var_name, str(var_value))
            
            # Check if all variables were replaced
            import re
            remaining_vars = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', expression)
            if any(var not in ['and', 'or', 'not'] for var in remaining_vars):
                # Some variables not replaced, condition can't be evaluated
                return False
            
            # Validate expression contains only allowed characters
            allowed_pattern = r'^[\d\.\+\-\*\/\(\)\s><!=]+$'
            if not re.match(allowed_pattern, expression):
                raise ValueError(f"Invalid characters in condition: {expression}")
            
            # Evaluate safely (only simple mathematical/comparison expressions)
            result = eval(expression, {"__builtins__": {}}, {})
            return bool(result)
            
        except Exception as e:
            # Log warning instead of printing to avoid JSON contamination
            import logging
            logging.warning(f"DSL condition evaluation failed for '{condition_str}': {e}")
            return False
    
    def _calculate_signal_strength(self, price_distance: float, signal_price: float) -> SignalStrength:
        """
        Calculate signal strength based on price distance.
        
        Args:
            price_distance: Absolute distance between prices
            signal_price: Current signal price
            
        Returns:
            SignalStrength: Calculated strength
        """
        # Calculate distance as percentage of price
        distance_percentage = (price_distance / signal_price) * 100
        
        # Map distance to strength levels
        if distance_percentage >= 0.5:  # 0.5% or more
            return SignalStrength.VERY_STRONG
        elif distance_percentage >= 0.3:  # 0.3% to 0.5%
            return SignalStrength.STRONG
        elif distance_percentage >= 0.15:  # 0.15% to 0.3%
            return SignalStrength.MODERATE
        else:  # Less than 0.15%
            return SignalStrength.WEAK
    
    def _generate_signal_reason(self, direction: TradeDirection, signal_price: float, reference_price: float) -> str:
        """Generate human-readable reason for the signal."""
        price_diff = signal_price - reference_price
        diff_pips = abs(price_diff) * 10000  # Assuming 4-decimal currency pairs
        
        direction_str = "BUY" if direction == TradeDirection.BUY else "SELL"
        comparison = "above" if price_diff > 0 else "below"
        
        return (
            f"DSL {direction_str}: {self.signal_time.strftime('%H:%M')} price ({signal_price:.5f}) "
            f"is {comparison} {self.reference_time.strftime('%H:%M')} {self.reference_price_type} "
            f"({reference_price:.5f}) by {diff_pips:.1f} pips"
        )
    
    def on_trade_opened(self, trade, context: StrategyContext) -> None:
        """Called when a trade is opened."""
        # Trade logging commented to avoid JSON contamination
        # print(f"DSL Strategy '{self.get_name()}': Trade opened - {trade.direction.value} {context.symbol} at {trade.entry_price:.5f}")
        # ref_price_str = f"{self.reference_price:.5f}" if self.reference_price else "None"
        # print(f"  Reference: {self.reference_time.strftime('%H:%M')} {self.reference_price_type} = {ref_price_str}")
        # print(f"  Signal: {self.signal_time.strftime('%H:%M')} price = {trade.entry_price:.5f}")
    
    def on_trade_closed(self, trade, context: StrategyContext) -> None:
        """Called when a trade is closed."""
        result_emoji = "✅" if trade.result.value == "WIN" else "❌" if trade.result.value == "LOSS" else "⚖️"
        # Trade result logging commented to avoid JSON contamination
        # print(f"DSL Strategy '{self.get_name()}': Trade closed {result_emoji}")
        # print(f"  Entry: {trade.entry_price:.5f} → Exit: {trade.exit_price:.5f}")
        # print(f"  Result: {trade.pips:+.1f} pips ({trade.result.value})")
    
    def on_candle_processed(self, context: StrategyContext) -> None:
        """Called after each candle is processed."""
        current_date = context.current_candle.timestamp.date()
        
        # Reset daily state at start of new day
        if current_date != self.last_trade_date:
            self.daily_trade_count = 0
        
        if self.is_indicator_based:
            # Calculate indicators for indicator-based strategies
            self._calculate_indicators(context.current_candle)
        else:
            # Reset reference price at start of new day for time-based strategies
            if current_date != self.last_reference_date:
                self.reference_price = None

    def _calculate_indicators(self, candle) -> None:
        """Calculate indicators for indicator-based strategies."""
        # Import libraries when needed
        try:
            import pandas as pd
            import ta
        except ImportError as e:
            # Log warning instead of printing to avoid JSON contamination
            import logging
            logging.warning(f"Missing required libraries for indicator calculations: {e}")
            return
            
        # Store candle in history
        self.candle_history.append({
            'open': candle.open,
            'high': candle.high,
            'low': candle.low,
            'close': candle.close,
            'volume': getattr(candle, 'volume', 0)
        })
        
        # Keep max 300 candles for memory efficiency
        if len(self.candle_history) > 300:
            self.candle_history = self.candle_history[-300:]
        
        # Need enough data for calculations
        if len(self.candle_history) < 2:
            return
        
        # Convert to DataFrame for TA library
        df = pd.DataFrame(self.candle_history)
        
        # Store previous values for crossover detection
        self.previous_indicator_values = self.indicator_values.copy()
        
        # Calculate each indicator defined in the configuration
        if 'indicators' in self.dsl_config:
            for indicator in self.dsl_config['indicators']:
                ind_type = indicator['type']
                period = indicator['period']
                alias = indicator['alias']
                
                try:
                    if ind_type == 'SMA' and len(df) >= period:
                        sma = ta.trend.sma_indicator(df['close'], window=period)
                        self.indicator_values[alias] = float(sma.iloc[-1])
                    elif ind_type == 'EMA' and len(df) >= period:
                        ema = ta.trend.ema_indicator(df['close'], window=period)
                        self.indicator_values[alias] = float(ema.iloc[-1])
                    elif ind_type == 'RSI' and len(df) >= period:
                        rsi = ta.momentum.rsi(df['close'], window=period)
                        self.indicator_values[alias] = float(rsi.iloc[-1])
                except Exception as e:
                    # Log warning instead of printing to avoid JSON contamination
                    import logging
                    logging.warning(f"Error calculating {alias} ({ind_type}): {e}")
                    
    def _calculate_indicator_signal_strength(self) -> SignalStrength:
        """Calculate signal strength for indicator-based strategies."""
        # For MA crossover, strength depends on distance between MAs
        if 'fast_ma' in self.indicator_values and 'slow_ma' in self.indicator_values:
            fast_ma = self.indicator_values['fast_ma']
            slow_ma = self.indicator_values['slow_ma']
            distance = abs(fast_ma - slow_ma)
            
            # Convert distance to strength (larger distance = stronger signal)
            if distance > 0.0050:  # 50 pips
                return SignalStrength.VERY_STRONG
            elif distance > 0.0030:  # 30 pips
                return SignalStrength.STRONG
            elif distance > 0.0015:  # 15 pips
                return SignalStrength.MODERATE
            else:
                return SignalStrength.WEAK
        
        return SignalStrength.MODERATE  # Default
        
    def _generate_indicator_signal_reason(self, direction: TradeDirection) -> str:
        """Generate human-readable reason for indicator signal."""
        if 'fast_ma' in self.indicator_values and 'slow_ma' in self.indicator_values:
            fast_ma = self.indicator_values['fast_ma']
            slow_ma = self.indicator_values['slow_ma']
            
            if direction == TradeDirection.BUY:
                return f"MA Crossover BUY: SMA20 ({fast_ma:.5f}) crossed above SMA50 ({slow_ma:.5f})"
            else:
                return f"MA Crossover SELL: SMA20 ({fast_ma:.5f}) crossed below SMA50 ({slow_ma:.5f})"
        
        return f"Indicator signal: {direction.value}"


# Helper function for creating DSL strategies from JSON
def create_dsl_strategy_from_config(dsl_config: Dict[str, Any]) -> DSLStrategy:
    """
    Create DSL strategy instance from configuration dictionary.
    
    Args:
        dsl_config: DSL strategy configuration
        
    Returns:
        DSLStrategy: Initialized strategy instance
    """
    return DSLStrategy(dsl_config)


def create_dsl_strategy_from_file(file_path: str) -> DSLStrategy:
    """
    Create DSL strategy instance from JSON file.
    
    Args:
        file_path: Path to DSL strategy JSON file
        
    Returns:
        DSLStrategy: Initialized strategy instance
    """
    import json
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            dsl_config = json.load(f)
        
        return DSLStrategy(dsl_config)
        
    except Exception as e:
        raise ValueError(f"Failed to create DSL strategy from file '{file_path}': {e}")


if __name__ == "__main__":
    # Test DSL strategy creation
    sample_config = {
        "name": "10am vs 9:30am Price Compare",
        "version": "1.0.0",
        "description": "Buy if 10am price > 9:30am close, Sell if lower",
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
    
    try:
        strategy = DSLStrategy(sample_config)
        # Success prints commented to avoid JSON contamination
        # print(f"✅ DSL Strategy created: {strategy.get_name()} v{strategy.get_version()}")
        # print(f"📝 Description: {strategy.get_description()}")
    except Exception as e:
        # print(f"❌ DSL Strategy creation failed: {e}")
        pass  # Silent failure to avoid JSON contamination