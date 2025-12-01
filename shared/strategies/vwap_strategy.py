#!/usr/bin/env python3
"""
VWAP Strategy Implementation - New Interface

This is the first strategy "cartridge" that implements the new TradingStrategy
interface. It can be plugged into the universal backtest engine.

Phase 1 of gradual migration - new VWAP strategy alongside existing implementation.
"""

from typing import Dict, Any, List, Optional
from datetime import time

from shared.models import Candle, TradeDirection
from shared.strategy_interface import TradingStrategy, StrategyContext, Signal, SignalStrength


class VWAPReversalStrategy(TradingStrategy):
    """
    VWAP Reversal Strategy - New Interface Implementation
    
    This strategy implements our classic VWAP logic:
    - At 8:30 AM, compare price to VWAP
    - If price > VWAP → SELL signal (expecting reversal)
    - If price < VWAP → BUY signal (expecting reversal)
    
    This is a "cartridge" that plugs into the universal backtest engine.
    """
    
    def __init__(self):
        super().__init__()
        self.entry_time = time(8, 30)  # 8:30 AM entry time
        self.signal_generated_today = False
        self.last_signal_date = None
    
    def get_name(self) -> str:
        return "VWAP Reversal"
    
    def get_description(self) -> str:
        return (
            "At 8:30 AM each trading day, compare current price to VWAP. "
            "Generate BUY signal if price is below VWAP (expecting bounce up), "
            "or SELL signal if price is above VWAP (expecting pullback down). "
            "This is a mean-reversion strategy based on VWAP levels."
        )
    
    def get_version(self) -> str:
        return "2.0.0"  # New interface version
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "entry_time": "08:30",
            "signal_logic": "reversal",  # vs "momentum"
            "min_vwap_distance": 0.0001,  # Minimum distance from VWAP to generate signal
            "confidence_threshold": 0.5,  # Minimum confidence to generate signal
            "max_signals_per_day": 1  # Only one signal per trading day
        }
    
    def requires_indicators(self) -> List[str]:
        return ["VWAP"]
    
    def initialize(self, parameters: Dict[str, Any] = None) -> None:
        """Initialize strategy with parameters."""
        super().initialize(parameters)
        
        # Parse entry time from parameters
        entry_time_str = self.get_parameters().get("entry_time", "08:30")
        hour, minute = map(int, entry_time_str.split(":"))
        self.entry_time = time(hour, minute)
        
        # Reset state
        self.signal_generated_today = False
        self.last_signal_date = None
    
    def generate_signal(self, context: StrategyContext) -> Optional[Signal]:
        """
        Generate VWAP reversal signal based on current market context.
        
        Args:
            context: Current market context with candle, indicators, and position info
            
        Returns:
            Signal or None if no signal should be generated
        """
        candle = context.current_candle
        
        # Only generate signals at the specified entry time (8:30 AM)
        if candle.timestamp.time() != self.entry_time:
            return None
        
        # Only one signal per trading day
        current_date = candle.timestamp.date()
        if current_date == self.last_signal_date:
            return None
        
        # Skip if already in position
        if context.current_position:
            return None
        
        # Get VWAP value
        vwap = context.get_indicator("VWAP")
        if vwap is None:
            return None
        
        current_price = candle.close
        min_distance = self.get_parameters().get("min_vwap_distance", 0.0001)
        
        # Check if price is far enough from VWAP to generate meaningful signal
        price_vwap_distance = abs(current_price - vwap)
        if price_vwap_distance < min_distance:
            return None
        
        # Calculate signal strength based on distance from VWAP
        strength = self._calculate_signal_strength(current_price, vwap, context)
        
        # Check confidence threshold
        confidence_threshold = self.get_parameters().get("confidence_threshold", 0.5)
        if strength.value < confidence_threshold:
            return None
        
        # Generate reversal signal
        signal = None
        
        if current_price < vwap:
            # Price below VWAP → BUY signal (expecting bounce up)
            signal = Signal(
                direction=TradeDirection.BUY,
                price=current_price,
                strength=strength,
                confidence=strength.value,
                reason=f"VWAP Reversal: Price {current_price:.5f} below VWAP {vwap:.5f} by {(vwap - current_price):.5f} ({((vwap - current_price) / vwap * 100):.2f}%)",
                timestamp=candle.timestamp,
                metadata={
                    "vwap_value": vwap,
                    "price_vwap_distance": price_vwap_distance,
                    "distance_percentage": (price_vwap_distance / vwap) * 100,
                    "entry_time": self.entry_time.strftime("%H:%M")
                }
            )
        
        elif current_price > vwap:
            # Price above VWAP → SELL signal (expecting pullback down)
            signal = Signal(
                direction=TradeDirection.SELL,
                price=current_price,
                strength=strength,
                confidence=strength.value,
                reason=f"VWAP Reversal: Price {current_price:.5f} above VWAP {vwap:.5f} by {(current_price - vwap):.5f} ({((current_price - vwap) / vwap * 100):.2f}%)",
                timestamp=candle.timestamp,
                metadata={
                    "vwap_value": vwap,
                    "price_vwap_distance": price_vwap_distance,
                    "distance_percentage": (price_vwap_distance / vwap) * 100,
                    "entry_time": self.entry_time.strftime("%H:%M")
                }
            )
        
        # Mark that we've generated a signal for this date
        if signal:
            self.last_signal_date = current_date
        
        return signal
    
    def _calculate_signal_strength(self, current_price: float, vwap: float, context: StrategyContext) -> SignalStrength:
        """
        Calculate signal strength based on various factors.
        
        Args:
            current_price: Current market price
            vwap: VWAP value
            context: Market context for additional analysis
            
        Returns:
            SignalStrength: Calculated strength level
        """
        # Base strength on distance from VWAP
        distance_percentage = abs(current_price - vwap) / vwap * 100
        
        # Strength thresholds (in percentage distance from VWAP)
        if distance_percentage >= 0.5:  # 0.5% or more
            return SignalStrength.VERY_STRONG
        elif distance_percentage >= 0.3:  # 0.3% to 0.5%
            return SignalStrength.STRONG
        elif distance_percentage >= 0.15:  # 0.15% to 0.3%
            return SignalStrength.MODERATE
        else:  # Less than 0.15%
            return SignalStrength.WEAK
    
    def on_trade_opened(self, trade, context: StrategyContext) -> None:
        """Called when a trade is opened based on this strategy's signal."""
        print(f"VWAP Strategy: Trade opened - {trade.direction.value} {context.symbol} at {trade.entry_price:.5f}")
        print(f"  VWAP: {context.get_indicator('VWAP'):.5f}")
        print(f"  Stop Loss: {trade.stop_loss:.5f}, Take Profit: {trade.take_profit:.5f}")
    
    def on_trade_closed(self, trade, context: StrategyContext) -> None:
        """Called when a trade is closed."""
        result_emoji = "✅" if trade.result.value == "WIN" else "❌" if trade.result.value == "LOSS" else "⚖️"
        print(f"VWAP Strategy: Trade closed - {trade.direction.value} {context.symbol} {result_emoji}")
        print(f"  Entry: {trade.entry_price:.5f} → Exit: {trade.exit_price:.5f}")
        print(f"  Result: {trade.pips:+.1f} pips ({trade.result.value})")
    
    def on_candle_processed(self, context: StrategyContext) -> None:
        """Called after each candle is processed."""
        # Reset daily signal flag at start of new day
        current_date = context.current_candle.timestamp.date()
        if self.last_signal_date and current_date != self.last_signal_date and context.current_candle.timestamp.time() == time(0, 0):
            self.signal_generated_today = False


class VWAPMomentumStrategy(VWAPReversalStrategy):
    """
    VWAP Momentum Strategy - Alternative Implementation
    
    Same as reversal strategy but follows momentum instead:
    - If price > VWAP → BUY signal (momentum continuation)
    - If price < VWAP → SELL signal (momentum continuation)
    """
    
    def get_name(self) -> str:
        return "VWAP Momentum"
    
    def get_description(self) -> str:
        return (
            "At 8:30 AM each trading day, compare current price to VWAP. "
            "Generate BUY signal if price is above VWAP (following momentum up), "
            "or SELL signal if price is below VWAP (following momentum down). "
            "This is a trend-following strategy based on VWAP levels."
        )
    
    def get_default_parameters(self) -> Dict[str, Any]:
        params = super().get_default_parameters()
        params["signal_logic"] = "momentum"
        return params
    
    def generate_signal(self, context: StrategyContext) -> Optional[Signal]:
        """Generate momentum signal (opposite of reversal logic)."""
        candle = context.current_candle
        
        # Same timing and validation logic as parent
        if candle.timestamp.time() != self.entry_time:
            return None
        
        current_date = candle.timestamp.date()
        if current_date == self.last_signal_date:
            return None
        
        if context.current_position:
            return None
        
        vwap = context.get_indicator("VWAP")
        if vwap is None:
            return None
        
        current_price = candle.close
        min_distance = self.get_parameters().get("min_vwap_distance", 0.0001)
        
        price_vwap_distance = abs(current_price - vwap)
        if price_vwap_distance < min_distance:
            return None
        
        strength = self._calculate_signal_strength(current_price, vwap, context)
        
        confidence_threshold = self.get_parameters().get("confidence_threshold", 0.5)
        if strength.value < confidence_threshold:
            return None
        
        # Generate momentum signal (opposite of reversal)
        signal = None
        
        if current_price > vwap:
            # Price above VWAP → BUY signal (momentum continuation)
            signal = Signal(
                direction=TradeDirection.BUY,
                price=current_price,
                strength=strength,
                confidence=strength.value,
                reason=f"VWAP Momentum: Price {current_price:.5f} above VWAP {vwap:.5f}, following upward momentum",
                timestamp=candle.timestamp,
                metadata={
                    "vwap_value": vwap,
                    "price_vwap_distance": price_vwap_distance,
                    "distance_percentage": (price_vwap_distance / vwap) * 100,
                    "signal_type": "momentum"
                }
            )
        
        elif current_price < vwap:
            # Price below VWAP → SELL signal (momentum continuation)
            signal = Signal(
                direction=TradeDirection.SELL,
                price=current_price,
                strength=strength,
                confidence=strength.value,
                reason=f"VWAP Momentum: Price {current_price:.5f} below VWAP {vwap:.5f}, following downward momentum",
                timestamp=candle.timestamp,
                metadata={
                    "vwap_value": vwap,
                    "price_vwap_distance": price_vwap_distance,
                    "distance_percentage": (price_vwap_distance / vwap) * 100,
                    "signal_type": "momentum"
                }
            )
        
        if signal:
            self.last_signal_date = current_date
        
        return signal