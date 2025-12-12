#!/usr/bin/env python3
"""
Advanced DSL Components

Helper classes for complex multi-indicator DSL strategies:
- MultiIndicatorManager: Manages multiple instances of same indicator type
- ConditionEvaluator: Evaluates complex boolean logic with zones
- CrossoverDetector: Detects threshold crossings with state tracking
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Use diagnostic logger for detailed debugging
DEBUG_LOG_PATH = '/tmp/dsl_debug.log'

def get_diagnostic_logger():
    """Get the diagnostic logger for detailed debugging."""
    diag_logger = logging.getLogger('dsl_diagnostic_advanced')
    if not diag_logger.handlers:
        diag_logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(DEBUG_LOG_PATH, mode='a')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        diag_logger.addHandler(fh)
        diag_logger.propagate = False
    return diag_logger

diagnostic_logger = get_diagnostic_logger()


class MultiIndicatorManager:
    """
    Manages multiple instances of the same indicator type with unique aliases.
    
    Example: 4 stochastics with different periods (fast, med_fast, med_slow, slow)
    """
    
    def __init__(self):
        self._instances: Dict[str, Dict[str, Any]] = {}  # alias -> {type, params, values}
        self._current_values: Dict[str, float] = {}  # alias -> current value
    
    def register_instance(self, indicator_type: str, alias: str, params: Dict[str, Any]) -> None:
        """
        Register a new indicator instance.
        
        Args:
            indicator_type: Type of indicator (e.g., "STOCHASTIC", "RSI")
            alias: Unique alias for this instance (e.g., "fast", "slow")
            params: Parameters for this instance (e.g., {"k_period": 9})
        """
        if alias in self._instances:
            raise ValueError(f"Indicator alias '{alias}' already registered")
        
        self._instances[alias] = {
            "type": indicator_type,
            "params": params,
            "values": {}
        }
        
        logger.debug(f"Registered indicator instance: {alias} ({indicator_type}) with params {params}")
    
    def update_value(self, alias: str, timestamp: datetime, value: float) -> None:
        """Update the current value for an indicator instance."""
        if alias not in self._instances:
            raise ValueError(f"Unknown indicator alias: {alias}")
        
        self._instances[alias]["values"][timestamp] = value
        self._current_values[alias] = value
    
    def get_value(self, alias: str) -> Optional[float]:
        """Get current value for an indicator instance."""
        return self._current_values.get(alias)
    
    def get_all_values(self) -> Dict[str, float]:
        """Get all current indicator values."""
        return self._current_values.copy()
    
    def get_instance_config(self, alias: str) -> Dict[str, Any]:
        """Get configuration for an indicator instance."""
        if alias not in self._instances:
            raise ValueError(f"Unknown indicator alias: {alias}")
        return self._instances[alias].copy()
    
    def list_instances(self) -> List[str]:
        """Get list of all registered instance aliases."""
        return list(self._instances.keys())


class CrossoverDetector:
    """
    Detects when indicators cross above or below thresholds.
    
    Maintains state between candles to detect crossover events.
    """
    
    def __init__(self):
        self._previous_values: Dict[str, float] = {}
    
    def detect_cross_above(self, alias: str, current: float, threshold: float) -> bool:
        """
        Detect if indicator crossed above threshold.
        
        Args:
            alias: Indicator alias
            current: Current indicator value
            threshold: Threshold level
            
        Returns:
            True if crossed above (was below, now above)
        """
        if alias not in self._previous_values:
            # First time seeing this indicator, no crossover possible
            return False
        
        previous = self._previous_values[alias]
        crossed = previous <= threshold < current
        
        if crossed:
            logger.info(f"Crossover detected: {alias} crossed ABOVE {threshold} ({previous:.2f} -> {current:.2f})")
        
        return crossed
    
    def detect_cross_below(self, alias: str, current: float, threshold: float) -> bool:
        """
        Detect if indicator crossed below threshold.
        
        Args:
            alias: Indicator alias
            current: Current indicator value
            threshold: Threshold level
            
        Returns:
            True if crossed below (was above, now below)
        """
        diagnostic_logger.debug(f"      detect_cross_below: alias={alias}, current={current:.2f}, threshold={threshold}")
        
        if alias not in self._previous_values:
            # First time seeing this indicator, no crossover possible
            diagnostic_logger.debug(f"      No previous value for {alias}, returning False")
            return False
        
        previous = self._previous_values[alias]
        crossed = previous >= threshold > current
        
        diagnostic_logger.debug(f"      Previous: {previous:.2f}, Current: {current:.2f}")
        diagnostic_logger.debug(f"      Condition: {previous:.2f} >= {threshold} > {current:.2f} = {crossed}")
        
        if crossed:
            diagnostic_logger.info(f"      *** CROSSOVER DETECTED: {alias} crossed BELOW {threshold} ({previous:.2f} -> {current:.2f}) ***")
        
        return crossed
    
    def update(self, alias: str, value: float) -> None:
        """Update tracked value for next iteration."""
        self._previous_values[alias] = value
    
    def reset(self) -> None:
        """Reset all tracked values."""
        self._previous_values.clear()


class ConditionEvaluator:
    """
    Evaluates complex boolean logic with zone conditions.
    
    Supports:
    - Zone conditions (all indicators above/below threshold)
    - Comparison conditions (>, <, ==, etc.)
    - Boolean logic (AND/OR)
    """
    
    def evaluate_zone(self, zone_spec: Dict[str, Any], indicator_values: Dict[str, float]) -> bool:
        """
        Check if indicators are in specified zone.
        
        Args:
            zone_spec: Zone specification with "all_above" or "all_below" and "indicators" list
            indicator_values: Current indicator values by alias
            
        Returns:
            True if all specified indicators are in the zone
        """
        indicators = zone_spec.get("indicators", [])
        
        if not indicators:
            logger.warning("Zone specification has no indicators list")
            return False
        
        # Check all_below condition
        if "all_below" in zone_spec:
            threshold = zone_spec["all_below"]
            for alias in indicators:
                value = indicator_values.get(alias)
                if value is None:
                    logger.debug(f"Zone check: {alias} has no value yet")
                    return False
                if value >= threshold:
                    logger.debug(f"Zone check failed: {alias}={value:.2f} not below {threshold}")
                    return False
            logger.debug(f"Zone check passed: All indicators below {threshold}")
            return True
        
        # Check all_above condition
        if "all_above" in zone_spec:
            threshold = zone_spec["all_above"]
            for alias in indicators:
                value = indicator_values.get(alias)
                if value is None:
                    logger.debug(f"Zone check: {alias} has no value yet")
                    return False
                if value <= threshold:
                    logger.debug(f"Zone check failed: {alias}={value:.2f} not above {threshold}")
                    return False
            logger.debug(f"Zone check passed: All indicators above {threshold}")
            return True
        
        logger.warning("Zone specification has neither all_above nor all_below")
        return False
    
    def evaluate_rotation_condition(
        self,
        condition: Dict[str, Any],
        previous_indicator_values: Dict[str, float],
        current_indicator_values: Dict[str, float],
        crossover_detector: CrossoverDetector
    ) -> bool:
        """
        Evaluate a rotation condition (zone + crossover trigger).
        
        CRITICAL: Zone is checked with PREVIOUS values, crossover with CURRENT values.
        This is because the crossover moves the indicator OUT of the zone.
        
        Args:
            condition: Condition configuration with "zone" and "trigger"
            previous_indicator_values: Previous candle's indicator values (for zone check)
            current_indicator_values: Current candle's indicator values (for crossover check)
            crossover_detector: Crossover detector for trigger detection
            
        Returns:
            True if both zone and trigger conditions are met
        """
        # Check zone condition with PREVIOUS values
        zone_spec = condition.get("zone")
        if not zone_spec:
            logger.warning("Rotation condition missing 'zone' specification")
            return False
        
        zone_met = self.evaluate_zone(zone_spec, previous_indicator_values)
        
        diagnostic_logger.debug(f"    Zone condition (using previous values): {zone_met}")
        diagnostic_logger.debug(f"    Previous values: {previous_indicator_values}")
        if not zone_met:
            diagnostic_logger.debug(f"    Zone NOT met, returning False")
            return False
        diagnostic_logger.debug(f"    Zone MET! Checking crossover...")
        
        # Check trigger condition with CURRENT values
        trigger_spec = condition.get("trigger")
        if not trigger_spec:
            logger.warning("Rotation condition missing 'trigger' specification")
            return False
        
        trigger_alias = trigger_spec.get("indicator")
        if not trigger_alias:
            logger.warning("Trigger specification missing 'indicator' field")
            return False
        
        current_value = current_indicator_values.get(trigger_alias)
        if current_value is None:
            logger.debug(f"Trigger indicator {trigger_alias} has no value yet")
            return False
        
        # Check crossover direction
        if "crosses_above" in trigger_spec:
            threshold = trigger_spec["crosses_above"]
            diagnostic_logger.debug(f"    Checking crossover ABOVE {threshold} for {trigger_alias}")
            diagnostic_logger.debug(f"    Current value: {current_value}")
            result = crossover_detector.detect_cross_above(trigger_alias, current_value, threshold)
            diagnostic_logger.debug(f"    Crossover above {threshold}: {result}")
            return result
        
        if "crosses_below" in trigger_spec:
            threshold = trigger_spec["crosses_below"]
            diagnostic_logger.debug(f"    Checking crossover BELOW {threshold} for {trigger_alias}")
            diagnostic_logger.debug(f"    Current value: {current_value}")
            result = crossover_detector.detect_cross_below(trigger_alias, current_value, threshold)
            diagnostic_logger.debug(f"    Crossover below {threshold}: {result}")
            return result
        
        logger.warning("Trigger specification has neither crosses_above nor crosses_below")
        return False
