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
import logging
from pathlib import Path

# Indicator calculation imports are done conditionally in methods that need them

from shared.models import Candle, TradeDirection
from shared.strategy_interface import TradingStrategy, StrategyContext, Signal, SignalStrength
from .schema_validator import validate_dsl_strategy, DSLValidationError

# Configure diagnostic logging
DEBUG_LOG_PATH = '/tmp/dsl_debug.log'

def setup_diagnostic_logger():
    """Set up file-based diagnostic logger for DSL strategy debugging."""
    logger = logging.getLogger('dsl_diagnostic')
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create file handler
    fh = logging.FileHandler(DEBUG_LOG_PATH, mode='a')
    fh.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.propagate = False  # Don't propagate to root logger
    
    return logger

# Initialize diagnostic logger
diagnostic_logger = setup_diagnostic_logger()


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
        
        # Initialize diagnostic logging for this strategy instance
        self._init_diagnostic_logging()
        
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
        
    def _init_diagnostic_logging(self) -> None:
        """Initialize diagnostic logging for this strategy instance."""
        # Clear the debug log file at the start of each strategy initialization
        try:
            with open(DEBUG_LOG_PATH, 'w') as f:
                f.write(f"=== DSL Strategy Diagnostic Log ===\n")
                f.write(f"Strategy: {self.dsl_config.get('name', 'Unknown')}\n")
                f.write(f"Version: {self.dsl_config.get('version', 'Unknown')}\n")
                f.write(f"Initialized at: {datetime.now()}\n")
                f.write(f"=" * 50 + "\n\n")
            diagnostic_logger.info(f"Diagnostic logging initialized for strategy: {self.dsl_config.get('name', 'Unknown')}")
        except Exception as e:
            diagnostic_logger.error(f"Failed to initialize diagnostic log file: {e}")
    
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
        """
        Return list of indicators required by this DSL strategy.
        Extracts indicator types from the DSL configuration.
        """
        if not hasattr(self, 'dsl_config') or 'indicators' not in self.dsl_config:
            return []
        
        required = []
        for indicator_config in self.dsl_config['indicators']:
            indicator_type = indicator_config.get('type', '').upper()
            if indicator_type:
                required.append(indicator_type)
        
        return required
    
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
            alias = indicator['alias']
            
            try:
                if ind_type == 'SMA':
                    period = indicator['period']
                    if len(df) >= period:
                        sma_series = ta.trend.sma_indicator(df['close'], window=period)
                        indicator_series[f"{alias}"] = sma_series.fillna(0).tolist()
                elif ind_type == 'EMA':
                    period = indicator['period']
                    if len(df) >= period:
                        ema_series = ta.trend.ema_indicator(df['close'], window=period)
                        indicator_series[f"{alias}"] = ema_series.fillna(0).tolist()
                elif ind_type == 'RSI':
                    period = indicator['period']
                    if len(df) >= period:
                        rsi_series = ta.momentum.rsi(df['close'], window=period)
                        indicator_series[f"{alias}"] = rsi_series.fillna(0).tolist()
                elif ind_type == 'MACD':
                    fast_period = indicator.get('fast_period', 12)
                    slow_period = indicator.get('slow_period', 26)
                    signal_period = indicator.get('signal_period', 9)
                    
                    if len(df) >= slow_period + signal_period:
                        macd_indicator = ta.trend.MACD(
                            df['close'],
                            window_slow=slow_period,
                            window_fast=fast_period,
                            window_sign=signal_period
                        )
                        indicator_series[f"{alias}"] = macd_indicator.macd().fillna(0).tolist()
                        indicator_series[f"{alias}_signal"] = macd_indicator.macd_signal().fillna(0).tolist()
                        indicator_series[f"{alias}_histogram"] = macd_indicator.macd_diff().fillna(0).tolist()
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
        
        diagnostic_logger.debug(f"=== _generate_indicator_signal START ===")
        diagnostic_logger.debug(f"Timestamp: {candle.timestamp}")
        diagnostic_logger.debug(f"Candle: O={candle.open:.5f} H={candle.high:.5f} L={candle.low:.5f} C={candle.close:.5f}")
        diagnostic_logger.debug(f"Has indicators: {bool(self.indicator_values)}")
        diagnostic_logger.debug(f"Has previous indicators: {bool(self.previous_indicator_values)}")
        
        # Check daily trade limit
        if self.last_trade_date == current_date and self.daily_trade_count >= self.max_daily_trades:
            diagnostic_logger.debug(f"Daily trade limit reached: {self.daily_trade_count}/{self.max_daily_trades}")
            return None
            
        # Skip if already in position
        if context.current_position:
            diagnostic_logger.debug(f"Already in position, skipping signal generation")
            return None
            
        # Need indicators calculated
        if not self.indicator_values:
            diagnostic_logger.debug(f"No indicator values available yet")
            return None
        
        # Log current indicator values
        diagnostic_logger.debug(f"Current indicator values:")
        for key, value in self.indicator_values.items():
            diagnostic_logger.debug(f"  {key} = {value}")
        
        # Log previous indicator values
        if self.previous_indicator_values:
            diagnostic_logger.debug(f"Previous indicator values:")
            for key, value in self.previous_indicator_values.items():
                diagnostic_logger.debug(f"  {key} = {value}")
        else:
            diagnostic_logger.debug(f"No previous indicator values available")
            
        # Evaluate indicator conditions (includes crossover detection)
        diagnostic_logger.debug(f"Evaluating indicator conditions...")
        signal_direction = self._evaluate_indicator_conditions()
        
        if signal_direction:
            diagnostic_logger.info(f"*** SIGNAL DETECTED: {signal_direction} at {candle.timestamp} ***")
        else:
            diagnostic_logger.debug(f"No signal generated (conditions not met)")
        
        if signal_direction is None:
            diagnostic_logger.debug(f"=== _generate_indicator_signal END (no signal) ===")
            return None
            
        # Calculate signal strength - for indicators, use distance between MAs
        strength = self._calculate_indicator_signal_strength()
        diagnostic_logger.debug(f"Signal strength: {strength}")
        
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
        
        diagnostic_logger.info(f"SIGNAL CREATED: {signal.direction} @ {signal.price:.5f}")
        diagnostic_logger.debug(f"Signal reason: {signal.reason}")
        
        # Update trade tracking
        if self.last_trade_date != current_date:
            self.daily_trade_count = 0
            self.last_trade_date = current_date
        
        self.daily_trade_count += 1
        diagnostic_logger.debug(f"Daily trade count: {self.daily_trade_count}")
        
        diagnostic_logger.debug(f"=== _generate_indicator_signal END (signal returned) ===")
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
        diagnostic_logger.debug(f"--- _evaluate_indicator_conditions START ---")
        
        # Need current and previous values for crossover detection
        if not self.indicator_values or not self.previous_indicator_values:
            diagnostic_logger.debug(f"Missing indicator values for condition evaluation")
            diagnostic_logger.debug(f"  Current values: {bool(self.indicator_values)}")
            diagnostic_logger.debug(f"  Previous values: {bool(self.previous_indicator_values)}")
            return None
            
        # Check buy condition
        buy_config = self.dsl_config["conditions"]["buy"]
        diagnostic_logger.debug(f"Checking BUY condition: {buy_config}")
        buy_result = self._check_indicator_condition(buy_config)
        diagnostic_logger.debug(f"BUY condition result: {buy_result}")
        
        if buy_result:
            diagnostic_logger.info(f"BUY condition MET!")
            diagnostic_logger.debug(f"--- _evaluate_indicator_conditions END (BUY) ---")
            return TradeDirection.BUY
            
        # Check sell condition
        sell_config = self.dsl_config["conditions"]["sell"]
        diagnostic_logger.debug(f"Checking SELL condition: {sell_config}")
        sell_result = self._check_indicator_condition(sell_config)
        diagnostic_logger.debug(f"SELL condition result: {sell_result}")
        
        if sell_result:
            diagnostic_logger.info(f"SELL condition MET!")
            diagnostic_logger.debug(f"--- _evaluate_indicator_conditions END (SELL) ---")
            return TradeDirection.SELL
        
        diagnostic_logger.debug(f"No conditions met")
        diagnostic_logger.debug(f"--- _evaluate_indicator_conditions END (None) ---")
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
        
        diagnostic_logger.debug(f"  _check_indicator_condition:")
        diagnostic_logger.debug(f"    Compare string: '{compare_str}'")
        diagnostic_logger.debug(f"    Needs crossover: {needs_crossover}")
        
        # Evaluate current condition
        current_result = self._evaluate_condition(compare_str, self.indicator_values)
        diagnostic_logger.debug(f"    Current condition result: {current_result}")
        
        if not needs_crossover:
            diagnostic_logger.debug(f"    No crossover needed, returning: {current_result}")
            return current_result
            
        # For crossover, check that condition is true now but was false before
        if not current_result:
            diagnostic_logger.debug(f"    Current condition is False, no crossover possible")
            return False
            
        # Check previous condition was false (crossover occurred)
        previous_result = self._evaluate_condition(compare_str, self.previous_indicator_values)
        diagnostic_logger.debug(f"    Previous condition result: {previous_result}")
        
        crossover_detected = not previous_result
        diagnostic_logger.debug(f"    Crossover detected: {crossover_detected}")
        
        if crossover_detected:
            diagnostic_logger.info(f"    *** CROSSOVER DETECTED ***")
            diagnostic_logger.info(f"      Condition: {compare_str}")
            diagnostic_logger.info(f"      Previous: {previous_result} -> Current: {current_result}")
        
        return crossover_detected
    
    def _evaluate_condition(self, condition_str: str, context: Dict[str, float]) -> bool:
        """
        Safely evaluate a condition string with given context.
        
        Args:
            condition_str: Condition to evaluate (e.g., "signal_price > reference_price")
            context: Dictionary with variable values
            
        Returns:
            bool: True if condition is met
        """
        diagnostic_logger.debug(f"      _evaluate_condition:")
        diagnostic_logger.debug(f"        Condition string: '{condition_str}'")
        diagnostic_logger.debug(f"        Context: {context}")
        
        try:
            # Replace variables with actual values
            # CRITICAL FIX: Sort variables by length (longest first) to prevent partial replacements
            # Example: Replace 'macd_signal' before 'macd' to avoid breaking compound names
            # Without this, 'macd > macd_signal' becomes '6.7e-05 > 6.7e-05_signal' (broken!)
            expression = condition_str
            sorted_vars = sorted(context.items(), key=lambda x: len(x[0]), reverse=True)
            
            for var_name, var_value in sorted_vars:
                if var_value is not None:
                    old_expr = expression
                    expression = expression.replace(var_name, str(var_value))
                    if old_expr != expression:
                        diagnostic_logger.debug(f"        Replaced '{var_name}' with {var_value}")
            
            diagnostic_logger.debug(f"        Final expression: '{expression}'")
            
            # Check if all variables were replaced
            # Note: 'e' in scientific notation (e.g., 1.23e-05) is not a variable
            import re
            remaining_vars = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', expression)
            # Filter out 'e' when it's part of scientific notation (preceded by digit)
            actual_vars = []
            for match in re.finditer(r'[a-zA-Z_][a-zA-Z0-9_]*', expression):
                var = match.group()
                # Check if this is 'e' in scientific notation
                if var == 'e' and match.start() > 0 and expression[match.start()-1].isdigit():
                    continue  # Skip 'e' in scientific notation
                actual_vars.append(var)
            
            if any(var not in ['and', 'or', 'not'] for var in actual_vars):
                # Some variables not replaced, condition can't be evaluated
                diagnostic_logger.warning(f"        Unresolved variables: {actual_vars}")
                return False
            
            # Validate expression contains only allowed characters
            # Allow 'e' and 'E' for scientific notation (e.g., 1.23e-05)
            allowed_pattern = r'^[\d\.eE\+\-\*\/\(\)\s><!=]+$'
            if not re.match(allowed_pattern, expression):
                diagnostic_logger.error(f"        Invalid characters in expression: {expression}")
                raise ValueError(f"Invalid characters in condition: {expression}")
            
            # Evaluate safely (only simple mathematical/comparison expressions)
            result = eval(expression, {"__builtins__": {}}, {})
            bool_result = bool(result)
            diagnostic_logger.debug(f"        Evaluation result: {bool_result}")
            return bool_result
            
        except Exception as e:
            diagnostic_logger.error(f"        Condition evaluation failed: {e}")
            diagnostic_logger.error(f"        Condition: '{condition_str}'")
            diagnostic_logger.error(f"        Context: {context}")
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
            diagnostic_logger.debug(f"New trading day: {current_date}, reset trade count")
        
        if self.is_indicator_based:
            # Calculate indicators for indicator-based strategies
            self._calculate_indicators(context.current_candle)
        else:
            # Reset reference price at start of new day for time-based strategies
            if current_date != self.last_reference_date:
                self.reference_price = None
                diagnostic_logger.debug(f"New day for time-based strategy, reset reference price")

    def _calculate_indicators(self, candle) -> None:
        """Calculate indicators for indicator-based strategies."""
        diagnostic_logger.debug(f">>> _calculate_indicators START >>>")
        diagnostic_logger.debug(f"Candle timestamp: {candle.timestamp}")
        
        # Import libraries when needed
        try:
            import pandas as pd
            import ta
        except ImportError as e:
            diagnostic_logger.error(f"Missing required libraries: {e}")
            return
            
        # Store candle in history
        self.candle_history.append({
            'open': candle.open,
            'high': candle.high,
            'low': candle.low,
            'close': candle.close,
            'volume': getattr(candle, 'volume', 0)
        })
        
        diagnostic_logger.debug(f"Candle history length: {len(self.candle_history)}")
        
        # Keep max 300 candles for memory efficiency
        if len(self.candle_history) > 300:
            self.candle_history = self.candle_history[-300:]
            diagnostic_logger.debug(f"Trimmed history to 300 candles")
        
        # Need enough data for calculations
        if len(self.candle_history) < 2:
            diagnostic_logger.debug(f"Insufficient candle history (need >= 2, have {len(self.candle_history)})")
            return
        
        # Convert to DataFrame for TA library
        df = pd.DataFrame(self.candle_history)
        
        # Store previous values for crossover detection
        self.previous_indicator_values = self.indicator_values.copy()
        diagnostic_logger.debug(f"Stored previous indicator values: {self.previous_indicator_values}")
        
        # Calculate each indicator defined in the configuration
        if 'indicators' in self.dsl_config:
            diagnostic_logger.debug(f"Calculating {len(self.dsl_config['indicators'])} indicators")
            
            for indicator in self.dsl_config['indicators']:
                ind_type = indicator['type']
                alias = indicator['alias']
                
                diagnostic_logger.debug(f"  Calculating {ind_type} as '{alias}'")
                
                try:
                    if ind_type == 'SMA':
                        period = indicator['period']
                        if len(df) >= period:
                            sma = ta.trend.sma_indicator(df['close'], window=period)
                            self.indicator_values[alias] = float(sma.iloc[-1])
                            diagnostic_logger.debug(f"    {alias} = {self.indicator_values[alias]:.6f}")
                        else:
                            diagnostic_logger.debug(f"    Insufficient data for SMA (need {period}, have {len(df)})")
                            
                    elif ind_type == 'EMA':
                        period = indicator['period']
                        if len(df) >= period:
                            ema = ta.trend.ema_indicator(df['close'], window=period)
                            self.indicator_values[alias] = float(ema.iloc[-1])
                            diagnostic_logger.debug(f"    {alias} = {self.indicator_values[alias]:.6f}")
                        else:
                            diagnostic_logger.debug(f"    Insufficient data for EMA (need {period}, have {len(df)})")
                            
                    elif ind_type == 'RSI':
                        period = indicator['period']
                        if len(df) >= period:
                            rsi = ta.momentum.rsi(df['close'], window=period)
                            self.indicator_values[alias] = float(rsi.iloc[-1])
                            diagnostic_logger.debug(f"    {alias} = {self.indicator_values[alias]:.6f}")
                        else:
                            diagnostic_logger.debug(f"    Insufficient data for RSI (need {period}, have {len(df)})")
                            
                    elif ind_type == 'MACD':
                        # MACD has optional parameters
                        fast_period = indicator.get('fast_period', 12)
                        slow_period = indicator.get('slow_period', 26)
                        signal_period = indicator.get('signal_period', 9)
                        
                        diagnostic_logger.debug(f"    MACD params: fast={fast_period}, slow={slow_period}, signal={signal_period}")
                        
                        if len(df) >= slow_period + signal_period:
                            macd_indicator = ta.trend.MACD(
                                df['close'],
                                window_slow=slow_period,
                                window_fast=fast_period,
                                window_sign=signal_period
                            )
                            # Store MACD line, signal line, and histogram
                            self.indicator_values[alias] = float(macd_indicator.macd().iloc[-1])
                            self.indicator_values[f"{alias}_signal"] = float(macd_indicator.macd_signal().iloc[-1])
                            self.indicator_values[f"{alias}_histogram"] = float(macd_indicator.macd_diff().iloc[-1])
                            
                            diagnostic_logger.debug(f"    {alias} = {self.indicator_values[alias]:.8f}")
                            diagnostic_logger.debug(f"    {alias}_signal = {self.indicator_values[f'{alias}_signal']:.8f}")
                            diagnostic_logger.debug(f"    {alias}_histogram = {self.indicator_values[f'{alias}_histogram']:.8f}")
                        else:
                            diagnostic_logger.debug(f"    Insufficient data for MACD (need {slow_period + signal_period}, have {len(df)})")
                            
                except Exception as e:
                    diagnostic_logger.error(f"    Error calculating {alias} ({ind_type}): {e}")
        
        diagnostic_logger.debug(f">>> _calculate_indicators END >>>")
        diagnostic_logger.debug(f"")
                    
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