#!/usr/bin/env python3
"""
Technical Indicator Calculators

Pre-built indicator calculators that work with the strategy interface.
These can be plugged into the backtest engine to provide indicators
that strategies require.

Phase 1 of gradual migration - new indicator system.
"""

# NUCLEAR STDOUT SILENCING for MCP protocol compliance
class _NullPrint:
    """Silent print replacement to prevent stdout pollution in MCP servers."""
    def __call__(self, *args, **kwargs):
        pass

# Replace print globally in this module to prevent MCP protocol corruption
print = _NullPrint()

from typing import Dict, List
from datetime import datetime
import pandas as pd

from shared.models import Candle  
from shared.strategy_interface import IndicatorCalculator


class VWAPCalculator(IndicatorCalculator):
    """
    Volume Weighted Average Price calculator.
    
    Calculates VWAP using the same TradingView-compatible method
    as our existing implementation.
    """
    
    def get_name(self) -> str:
        return "VWAP"
    
    def requires_periods(self) -> int:
        return 1  # VWAP can be calculated from first candle
    
    def calculate(self, candles: List[Candle], **kwargs) -> Dict[datetime, float]:
        """
        Calculate VWAP for each candle using cumulative method.
        
        This matches our existing TradingView-compatible implementation.
        """
        if not candles:
            return {}
        
        results = {}
        cumulative_volume = 0.0
        cumulative_vwap_volume = 0.0
        
        for candle in candles:
            # Calculate typical price (HLC/3)
            typical_price = (candle.high + candle.low + candle.close) / 3
            
            # Update cumulative values
            volume = candle.volume if candle.volume > 0 else 1.0  # Fallback for zero volume
            cumulative_volume += volume
            cumulative_vwap_volume += typical_price * volume
            
            # Calculate VWAP
            vwap = cumulative_vwap_volume / cumulative_volume if cumulative_volume > 0 else typical_price
            
            results[candle.timestamp] = vwap
        
        return results


class SMACalculator(IndicatorCalculator):
    """
    Simple Moving Average calculator.
    """
    
    def __init__(self, period: int = 20):
        self.period = period
    
    def get_name(self) -> str:
        return f"SMA{self.period}"
    
    def requires_periods(self) -> int:
        return self.period
    
    def calculate(self, candles: List[Candle], **kwargs) -> Dict[datetime, float]:
        """Calculate Simple Moving Average."""
        if len(candles) < self.period:
            return {}
        
        results = {}
        
        # Convert to pandas for easier calculation
        df = pd.DataFrame([
            {
                'timestamp': c.timestamp,
                'close': c.close
            }
            for c in candles
        ])
        
        # Calculate SMA
        df[f'sma_{self.period}'] = df['close'].rolling(window=self.period).mean()
        
        # Convert back to dictionary, skipping NaN values
        for _, row in df.iterrows():
            if pd.notna(row[f'sma_{self.period}']):
                results[row['timestamp']] = float(row[f'sma_{self.period}'])
        
        return results


class EMACalculator(IndicatorCalculator):
    """
    Exponential Moving Average calculator.
    """
    
    def __init__(self, period: int = 20):
        self.period = period
        self.alpha = 2.0 / (period + 1)  # Smoothing factor
    
    def get_name(self) -> str:
        return f"EMA{self.period}"
    
    def requires_periods(self) -> int:
        return self.period
    
    def calculate(self, candles: List[Candle], **kwargs) -> Dict[datetime, float]:
        """Calculate Exponential Moving Average."""
        if len(candles) < self.period:
            return {}
        
        results = {}
        
        # Initialize EMA with SMA of first period
        sma_sum = sum(candle.close for candle in candles[:self.period])
        ema = sma_sum / self.period
        
        # Calculate EMA for each candle starting from period index
        for i, candle in enumerate(candles):
            if i < self.period - 1:
                continue  # Skip until we have enough data
            elif i == self.period - 1:
                # First EMA value is SMA
                results[candle.timestamp] = ema
            else:
                # Calculate EMA: EMA = (Close - Previous EMA) * α + Previous EMA
                ema = (candle.close - ema) * self.alpha + ema
                results[candle.timestamp] = ema
        
        return results


class RSICalculator(IndicatorCalculator):
    """
    Relative Strength Index calculator.
    """
    
    def __init__(self, period: int = 14):
        self.period = period
    
    def get_name(self) -> str:
        return f"RSI{self.period}"
    
    def requires_periods(self) -> int:
        return self.period + 1  # Need one extra for price change calculation
    
    def calculate(self, candles: List[Candle], **kwargs) -> Dict[datetime, float]:
        """Calculate RSI using standard Wilder's method."""
        if len(candles) < self.period + 1:
            return {}
        
        results = {}
        
        # Convert to pandas for easier calculation
        df = pd.DataFrame([
            {
                'timestamp': c.timestamp,
                'close': c.close
            }
            for c in candles
        ])
        
        # Calculate price changes
        df['price_change'] = df['close'].diff()
        df['gain'] = df['price_change'].where(df['price_change'] > 0, 0)
        df['loss'] = -df['price_change'].where(df['price_change'] < 0, 0)
        
        # Calculate initial average gain and loss
        df['avg_gain'] = df['gain'].rolling(window=self.period).mean()
        df['avg_loss'] = df['loss'].rolling(window=self.period).mean()
        
        # Apply Wilder's smoothing for subsequent values
        for i in range(self.period, len(df)):
            df.loc[i, 'avg_gain'] = (df.loc[i-1, 'avg_gain'] * (self.period - 1) + df.loc[i, 'gain']) / self.period
            df.loc[i, 'avg_loss'] = (df.loc[i-1, 'avg_loss'] * (self.period - 1) + df.loc[i, 'loss']) / self.period
        
        # Calculate RSI
        df['rs'] = df['avg_gain'] / df['avg_loss'].replace(0, 1e-10)  # Avoid division by zero
        df['rsi'] = 100 - (100 / (1 + df['rs']))
        
        # Convert back to dictionary, skipping NaN values
        for _, row in df.iterrows():
            if pd.notna(row['rsi']):
                results[row['timestamp']] = float(row['rsi'])
        
        return results


class BollingerBandsCalculator(IndicatorCalculator):
    """
    Bollinger Bands calculator.
    
    Returns middle band (SMA), upper band, and lower band.
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev
    
    def get_name(self) -> str:
        return f"BB{self.period}"
    
    def requires_periods(self) -> int:
        return self.period
    
    def calculate(self, candles: List[Candle], **kwargs) -> Dict[datetime, float]:
        """
        Calculate Bollinger Bands.
        
        Returns middle band (SMA) as the primary value.
        Upper and lower bands are available in metadata.
        """
        if len(candles) < self.period:
            return {}
        
        results = {}
        
        # Convert to pandas for easier calculation
        df = pd.DataFrame([
            {
                'timestamp': c.timestamp,
                'close': c.close
            }
            for c in candles
        ])
        
        # Calculate SMA and standard deviation
        df['sma'] = df['close'].rolling(window=self.period).mean()
        df['std'] = df['close'].rolling(window=self.period).std()
        
        # Calculate bands
        df['upper_band'] = df['sma'] + (df['std'] * self.std_dev)
        df['lower_band'] = df['sma'] - (df['std'] * self.std_dev)
        
        # Convert back to dictionary, skipping NaN values
        for _, row in df.iterrows():
            if pd.notna(row['sma']):
                # Primary value is middle band (SMA)
                results[row['timestamp']] = float(row['sma'])
        
        return results


class IndicatorRegistry:
    """
    Registry for available indicator calculators.
    
    Provides easy access to all available indicators and their instances.
    """
    
    def __init__(self):
        self._calculators = {}
        self._register_default_indicators()
    
    def _register_default_indicators(self):
        """Register all built-in indicators."""
        # VWAP
        self.register("VWAP", VWAPCalculator())
        
        # Moving Averages
        self.register("SMA20", SMACalculator(20))
        self.register("SMA50", SMACalculator(50))
        self.register("SMA200", SMACalculator(200))
        self.register("EMA20", EMACalculator(20))
        self.register("EMA50", EMACalculator(50))
        
        # Oscillators
        self.register("RSI", RSICalculator(14))
        self.register("RSI21", RSICalculator(21))
        
        # Bands
        self.register("BB20", BollingerBandsCalculator(20, 2.0))
    
    def register(self, name: str, calculator: IndicatorCalculator):
        """Register a new indicator calculator."""
        self._calculators[name] = calculator
    
    def get(self, name: str) -> IndicatorCalculator:
        """Get indicator calculator by name."""
        if name not in self._calculators:
            raise ValueError(f"Indicator '{name}' not found. Available: {list(self._calculators.keys())}")
        return self._calculators[name]
    
    def list_available(self) -> List[str]:
        """Get list of all available indicator names."""
        return list(self._calculators.keys())
    
    def calculate_indicators(self, candles: List[Candle], required_indicators: List[str]) -> Dict[str, Dict[datetime, float]]:
        """
        Calculate multiple indicators for given candles.
        
        Args:
            candles: Historical candle data
            required_indicators: List of indicator names to calculate
            
        Returns:
            Dict mapping indicator names to their calculated values
        """
        results = {}
        
        for indicator_name in required_indicators:
            if indicator_name in self._calculators:
                calculator = self._calculators[indicator_name]
                results[indicator_name] = calculator.calculate(candles)
            else:
                print(f"Warning: Indicator '{indicator_name}' not found, skipping...")
        
        return results


# Global indicator registry instance
indicator_registry = IndicatorRegistry()