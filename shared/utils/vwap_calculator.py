"""
TradingView-Compatible VWAP Calculation Module

This module implements the exact VWAP calculation from TradingView's 
"VWAP Stdev Bands v2 Mod" indicator.

Key features:
- Daily session-based VWAP reset
- Uses HL2 (high+low)/2 as typical price
- Running cumulative calculation
- Standard deviation bands support
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, time as dt_time
import math


class TradingViewVWAP:
    """
    TradingView-compatible VWAP calculator that resets daily and uses
    the exact same calculation method as the TradingView script.
    """
    
    def __init__(self, reset_time: dt_time = dt_time(0, 0)):
        """
        Initialize VWAP calculator.
        
        Args:
            reset_time: Time to reset VWAP calculation (default: midnight)
        """
        self.reset_time = reset_time
        self.reset()
    
    def reset(self):
        """Reset all VWAP calculations for new session."""
        self.vwapsum = 0.0
        self.volumesum = 0.0
        self.v2sum = 0.0
        self.current_session_date = None
        self.previous_vwap = None
    
    def is_new_session(self, timestamp: datetime) -> bool:
        """
        Check if this is a new trading session (new day).
        Equivalent to TradingView's: newSession = iff(change(start), 1, 0)
        """
        current_date = timestamp.date()
        
        if self.current_session_date is None:
            self.current_session_date = current_date
            return True
            
        if current_date != self.current_session_date:
            self.current_session_date = current_date
            return True
            
        return False
    
    def calculate_vwap(self, candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate VWAP for a series of candles using TradingView's method.
        
        Args:
            candles: List of OHLCV candle dictionaries
            
        Returns:
            List of candles with VWAP values added
        """
        result = []
        
        for candle in candles:
            # Extract OHLCV data
            high = float(candle.get('high', candle.get('h', 0)))
            low = float(candle.get('low', candle.get('l', 0)))
            close = float(candle.get('close', candle.get('c', 0)))
            volume = float(candle.get('volume', candle.get('v', 1)))
            
            # Get timestamp
            timestamp = candle.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.now()  # Fallback
            
            # Calculate HL2 (typical price in TradingView)
            hl2 = (high + low) / 2.0
            
            # Check for new session (daily reset)
            new_session = self.is_new_session(timestamp)
            
            if new_session:
                # Store previous VWAP before reset
                if hasattr(self, 'myvwap'):
                    self.previous_vwap = self.myvwap
                
                # Reset for new session (TradingView logic)
                self.vwapsum = hl2 * volume
                self.volumesum = volume
                self.v2sum = volume * hl2 * hl2
            else:
                # Accumulate (TradingView logic)
                self.vwapsum += hl2 * volume
                self.volumesum += volume
                self.v2sum += volume * hl2 * hl2
            
            # Calculate VWAP: myvwap = vwapsum/volumesum
            if self.volumesum > 0:
                self.myvwap = self.vwapsum / self.volumesum
            else:
                self.myvwap = hl2
            
            # Calculate standard deviation: dev = sqrt(max(v2sum/volumesum - myvwap*myvwap, 0))
            if self.volumesum > 0:
                variance = max(self.v2sum / self.volumesum - self.myvwap * self.myvwap, 0)
                self.dev = math.sqrt(variance)
            else:
                self.dev = 0.0
            
            # Add VWAP data to candle
            enhanced_candle = candle.copy()
            enhanced_candle.update({
                'vwap': round(self.myvwap, 5),
                'vwap_dev': round(self.dev, 5),
                'vwap_upper_1': round(self.myvwap + 1.28 * self.dev, 5),
                'vwap_lower_1': round(self.myvwap - 1.28 * self.dev, 5),
                'vwap_upper_2': round(self.myvwap + 2.01 * self.dev, 5),
                'vwap_lower_2': round(self.myvwap - 2.01 * self.dev, 5),
                'hl2': round(hl2, 5),
                'new_session': new_session,
                'previous_vwap': round(self.previous_vwap, 5) if self.previous_vwap else None
            })
            
            result.append(enhanced_candle)
        
        return result
    
    def get_current_vwap(self) -> float:
        """Get the current VWAP value."""
        return getattr(self, 'myvwap', 0.0)
    
    def get_vwap_bands(self, multipliers: List[float] = None) -> Dict[str, float]:
        """
        Get VWAP with standard deviation bands.
        
        Args:
            multipliers: List of standard deviation multipliers (default: TradingView values)
            
        Returns:
            Dictionary with VWAP and band values
        """
        if multipliers is None:
            multipliers = [1.28, 2.01, 2.51, 3.09, 4.01]
        
        if not hasattr(self, 'myvwap') or not hasattr(self, 'dev'):
            return {'vwap': 0.0}
        
        bands = {'vwap': self.myvwap}
        
        for i, mult in enumerate(multipliers, 1):
            bands[f'upper_{i}'] = self.myvwap + mult * self.dev
            bands[f'lower_{i}'] = self.myvwap - mult * self.dev
        
        return bands


def calculate_vwap_for_strategy(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function to calculate VWAP for trading strategy use.
    
    Args:
        candles: List of OHLCV candle dictionaries
        
    Returns:
        List of candles with VWAP values added
    """
    vwap_calculator = TradingViewVWAP()
    return vwap_calculator.calculate_vwap(candles)


def get_vwap_at_time(candles: List[Dict[str, Any]], target_time: dt_time) -> Optional[float]:
    """
    Get VWAP value at a specific time (e.g., 8:30 AM for strategy signals).
    
    Args:
        candles: List of candles with VWAP calculated
        target_time: Target time to find VWAP value
        
    Returns:
        VWAP value at target time, or None if not found
    """
    for candle in candles:
        timestamp = candle.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, datetime):
            candle_time = timestamp.time()
            if candle_time >= target_time:
                return candle.get('vwap')
    
    return None