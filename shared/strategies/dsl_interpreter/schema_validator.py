#!/usr/bin/env python3
"""
DSL Schema Validator

Validates DSL strategy JSON configurations against defined schema.
Ensures all required fields are present and properly formatted.

CRITICAL: This is an ADDITIVE component that extends the existing strategy system.
It does NOT break the modular architecture or existing strategies.
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime


# DSL Strategy JSON Schema Definition
DSL_STRATEGY_SCHEMA = {
    "type": "object",
    "required": ["name", "version", "description", "timing", "conditions", "risk_management"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
            "description": "Human-readable strategy name"
        },
        "version": {
            "type": "string",
            "pattern": r"^\d+\.\d+\.\d+$",
            "description": "Version in semantic format (e.g., '1.0.0')"
        },
        "description": {
            "type": "string",
            "minLength": 10,
            "maxLength": 500,
            "description": "Detailed description of strategy logic"
        },
        "timing": {
            "type": "object",
            "required": ["reference_time", "reference_price", "signal_time"],
            "properties": {
                "reference_time": {
                    "type": "string",
                    "pattern": r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
                    "description": "Reference time in HH:MM format (e.g., '09:30')"
                },
                "reference_price": {
                    "type": "string",
                    "enum": ["open", "high", "low", "close"],
                    "description": "Which price to use from reference time candle"
                },
                "signal_time": {
                    "type": "string",
                    "pattern": r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$",
                    "description": "Signal generation time in HH:MM format (e.g., '10:00')"
                }
            },
            "additionalProperties": False
        },
        "conditions": {
            "type": "object",
            "required": ["buy", "sell"],
            "properties": {
                "buy": {
                    "type": "object",
                    "required": ["compare"],
                    "properties": {
                        "compare": {
                            "type": "string",
                            "description": "Comparison logic (e.g., 'signal_price > reference_price')"
                        },
                        "additional_conditions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Additional conditions for buy signal"
                        }
                    },
                    "additionalProperties": False
                },
                "sell": {
                    "type": "object",
                    "required": ["compare"],
                    "properties": {
                        "compare": {
                            "type": "string",
                            "description": "Comparison logic (e.g., 'signal_price < reference_price')"
                        },
                        "additional_conditions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Additional conditions for sell signal"
                        }
                    },
                    "additionalProperties": False
                }
            },
            "additionalProperties": False
        },
        "risk_management": {
            "type": "object",
            "required": ["stop_loss_pips", "take_profit_pips"],
            "properties": {
                "stop_loss_pips": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 1000,
                    "description": "Stop loss in pips"
                },
                "take_profit_pips": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 1000,
                    "description": "Take profit in pips"
                },
                "max_daily_trades": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 1,
                    "description": "Maximum trades per day"
                },
                "min_pip_distance": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "default": 0.0001,
                    "description": "Minimum pip distance between prices to generate signal"
                }
            },
            "additionalProperties": False
        },
        "parameters": {
            "type": "object",
            "description": "Custom strategy parameters",
            "additionalProperties": True
        },
        "metadata": {
            "type": "object",
            "properties": {
                "author": {"type": "string"},
                "created_date": {"type": "string", "format": "date"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "notes": {"type": "string"}
            },
            "additionalProperties": True
        }
    },
    "additionalProperties": False
}


class DSLValidationError(Exception):
    """Raised when DSL strategy validation fails."""
    pass


def validate_dsl_strategy(strategy_config: Dict[str, Any]) -> bool:
    """
    Validate DSL strategy configuration against schema.
    Routes to appropriate validator based on strategy type.
    
    Args:
        strategy_config: Dictionary containing DSL strategy configuration
        
    Returns:
        bool: True if valid
        
    Raises:
        DSLValidationError: If validation fails with detailed error message
    """
    try:
        # Detect strategy type
        has_indicators = "indicators" in strategy_config and strategy_config["indicators"]
        has_timing = "timing" in strategy_config and strategy_config["timing"]
        
        if has_indicators and not has_timing:
            # Indicator-based strategy
            return _validate_indicator_based_strategy(strategy_config)
        elif has_timing and not has_indicators:
            # Time-based strategy (existing)
            return _validate_time_based_strategy(strategy_config)
        else:
            raise ValueError("Strategy must be either time-based (with timing) OR indicator-based (with indicators), not both or neither")
        
    except Exception as e:
        raise DSLValidationError(f"DSL strategy validation failed: {str(e)}")


def _validate_time_based_strategy(strategy_config: Dict[str, Any]) -> bool:
    """
    Validate time-based DSL strategy (original validation logic).
    
    Args:
        strategy_config: Dictionary containing time-based DSL strategy configuration
        
    Returns:
        bool: True if valid
    """
    # Original validation logic - unchanged
    _validate_required_fields(strategy_config)
    _validate_field_types(strategy_config)
    _validate_timing_logic(strategy_config)
    _validate_conditions(strategy_config)
    _validate_risk_management(strategy_config)
    return True


def _validate_indicator_based_strategy(strategy_config: Dict[str, Any]) -> bool:
    """
    Validate indicator-based DSL strategy.
    
    Args:
        strategy_config: Dictionary containing indicator-based DSL strategy configuration
        
    Returns:
        bool: True if valid
    """
    # Validate required fields for indicator-based strategies
    _validate_indicator_required_fields(strategy_config)
    _validate_field_types(strategy_config)  # Same as time-based
    _validate_indicators_configuration(strategy_config)
    _validate_indicator_conditions(strategy_config)
    _validate_risk_management(strategy_config)  # Same as time-based
    return True


def _validate_required_fields(config: Dict[str, Any]) -> None:
    """Validate all required fields are present."""
    required_fields = ["name", "version", "description", "timing", "conditions", "risk_management"]
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
        
        if not config[field]:
            raise ValueError(f"Field '{field}' cannot be empty")


def _validate_field_types(config: Dict[str, Any]) -> None:
    """Validate field types and formats."""
    # Validate name
    if not isinstance(config["name"], str) or len(config["name"]) < 1:
        raise ValueError("'name' must be a non-empty string")
    
    # Validate version format (semantic versioning)
    import re
    version_pattern = r"^\d+\.\d+\.\d+$"
    if not isinstance(config["version"], str) or not re.match(version_pattern, config["version"]):
        raise ValueError("'version' must be in semantic format (e.g., '1.0.0')")
    
    # Validate description
    if not isinstance(config["description"], str) or len(config["description"]) < 10:
        raise ValueError("'description' must be a string with at least 10 characters")


def _validate_timing_logic(config: Dict[str, Any]) -> None:
    """Validate timing configuration."""
    timing = config["timing"]
    
    # Check required timing fields
    required_timing_fields = ["reference_time", "reference_price", "signal_time"]
    for field in required_timing_fields:
        if field not in timing:
            raise ValueError(f"Missing required timing field: {field}")
    
    # Validate time formats (HH:MM)
    import re
    time_pattern = r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
    
    for time_field in ["reference_time", "signal_time"]:
        if not re.match(time_pattern, timing[time_field]):
            raise ValueError(f"'{time_field}' must be in HH:MM format (e.g., '09:30')")
    
    # Validate reference_price
    valid_prices = ["open", "high", "low", "close"]
    if timing["reference_price"] not in valid_prices:
        raise ValueError(f"'reference_price' must be one of: {valid_prices}")
    
    # Validate signal_time is after reference_time
    ref_hour, ref_min = map(int, timing["reference_time"].split(":"))
    sig_hour, sig_min = map(int, timing["signal_time"].split(":"))
    
    ref_minutes = ref_hour * 60 + ref_min
    sig_minutes = sig_hour * 60 + sig_min
    
    if sig_minutes <= ref_minutes:
        raise ValueError("'signal_time' must be after 'reference_time'")


def _validate_conditions(config: Dict[str, Any]) -> None:
    """Validate trading conditions."""
    conditions = config["conditions"]
    
    # Check required condition fields
    if "buy" not in conditions or "sell" not in conditions:
        raise ValueError("Both 'buy' and 'sell' conditions are required")
    
    # Validate buy and sell conditions
    for condition_type in ["buy", "sell"]:
        condition = conditions[condition_type]
        
        if "compare" not in condition:
            raise ValueError(f"'{condition_type}' condition must have 'compare' field")
        
        if not isinstance(condition["compare"], str):
            raise ValueError(f"'{condition_type}' compare must be a string")
        
        # Validate comparison logic contains required variables
        compare_str = condition["compare"]
        required_vars = ["signal_price", "reference_price"]
        
        for var in required_vars:
            if var not in compare_str:
                raise ValueError(f"'{condition_type}' condition must reference '{var}'")
        
        # Validate comparison operators
        valid_operators = [">", "<", ">=", "<=", "==", "!="]
        has_operator = any(op in compare_str for op in valid_operators)
        
        if not has_operator:
            raise ValueError(f"'{condition_type}' condition must contain a comparison operator: {valid_operators}")


def _validate_risk_management(config: Dict[str, Any]) -> None:
    """Validate risk management settings."""
    risk_mgmt = config["risk_management"]
    
    # Check required risk management fields
    required_fields = ["stop_loss_pips", "take_profit_pips"]
    for field in required_fields:
        if field not in risk_mgmt:
            raise ValueError(f"Missing required risk management field: {field}")
    
    # Validate numeric fields
    for field in ["stop_loss_pips", "take_profit_pips"]:
        value = risk_mgmt[field]
        
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"'{field}' must be a positive number")
        
        if value > 1000:
            raise ValueError(f"'{field}' cannot exceed 1000 pips")
    
    # Validate optional fields
    if "max_daily_trades" in risk_mgmt:
        max_trades = risk_mgmt["max_daily_trades"]
        if not isinstance(max_trades, int) or max_trades < 1 or max_trades > 200:
            raise ValueError("'max_daily_trades' must be an integer between 1 and 200")
    
    if "min_pip_distance" in risk_mgmt:
        min_distance = risk_mgmt["min_pip_distance"]
        if not isinstance(min_distance, (int, float)) or min_distance < 0:
            raise ValueError("'min_pip_distance' must be a non-negative number")


def validate_dsl_file(file_path: str) -> Dict[str, Any]:
    """
    Validate DSL strategy from JSON file.
    
    Args:
        file_path: Path to DSL strategy JSON file
        
    Returns:
        Dict[str, Any]: Validated strategy configuration
        
    Raises:
        DSLValidationError: If file cannot be read or validation fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            strategy_config = json.load(f)
        
        # Validate the configuration
        validate_dsl_strategy(strategy_config)
        
        return strategy_config
        
    except FileNotFoundError:
        raise DSLValidationError(f"DSL strategy file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise DSLValidationError(f"Invalid JSON in DSL strategy file: {e}")
    except Exception as e:
        raise DSLValidationError(f"DSL file validation failed: {e}")


def _validate_indicator_required_fields(config: Dict[str, Any]) -> None:
    """Validate required fields for indicator-based strategies."""
    required_fields = ["name", "version", "description", "indicators", "conditions", "risk_management"]
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field for indicator-based strategy: {field}")
        
        if not config[field]:
            raise ValueError(f"Field '{field}' cannot be empty")


def _validate_indicators_configuration(config: Dict[str, Any]) -> None:
    """Validate indicators configuration for indicator-based strategies."""
    indicators = config["indicators"]
    
    if not isinstance(indicators, list) or len(indicators) == 0:
        raise ValueError("'indicators' must be a non-empty list")
    
    required_indicator_fields = ["type", "alias"]
    valid_indicator_types = ["SMA", "EMA", "RSI", "MACD", "STOCHASTIC"]
    
    aliases = set()
    for i, indicator in enumerate(indicators):
        # Check required fields
        for field in required_indicator_fields:
            if field not in indicator:
                raise ValueError(f"Indicator {i}: Missing required field '{field}'")
        
        # Validate indicator type
        if indicator["type"] not in valid_indicator_types:
            raise ValueError(f"Indicator {i}: Invalid type '{indicator['type']}'. Must be one of: {valid_indicator_types}")
        
        # Validate period (required for SMA, EMA, RSI but not MACD)
        if indicator["type"] in ["SMA", "EMA", "RSI"]:
            if "period" not in indicator:
                raise ValueError(f"Indicator {i}: '{indicator['type']}' requires 'period' field")
            if not isinstance(indicator["period"], int) or indicator["period"] < 1 or indicator["period"] > 200:
                raise ValueError(f"Indicator {i}: 'period' must be an integer between 1 and 200")
        
        # Validate MACD-specific fields
        if indicator["type"] == "MACD":
            # MACD can have optional fast_period, slow_period, signal_period
            # If not provided, defaults will be used (12, 26, 9)
            for period_field in ["fast_period", "slow_period", "signal_period"]:
                if period_field in indicator:
                    if not isinstance(indicator[period_field], int) or indicator[period_field] < 1:
                        raise ValueError(f"Indicator {i}: '{period_field}' must be a positive integer")
        
        # Validate alias
        if not isinstance(indicator["alias"], str) or len(indicator["alias"]) < 1:
            raise ValueError(f"Indicator {i}: 'alias' must be a non-empty string")
        
        # Check for duplicate aliases
        if indicator["alias"] in aliases:
            raise ValueError(f"Indicator {i}: Duplicate alias '{indicator['alias']}'")
        aliases.add(indicator["alias"])


def _validate_indicator_conditions(config: Dict[str, Any]) -> None:
    """Validate conditions for indicator-based strategies."""
    conditions = config["conditions"]
    
    # Check required condition fields
    if "buy" not in conditions or "sell" not in conditions:
        raise ValueError("Both 'buy' and 'sell' conditions are required")
    
    # Get indicator aliases for validation
    indicator_aliases = {ind["alias"] for ind in config["indicators"]}
    
    # Validate buy and sell conditions
    for condition_type in ["buy", "sell"]:
        condition = conditions[condition_type]
        
        # Check if this is a rotation-type condition (advanced)
        if condition.get("type") == "rotation":
            _validate_rotation_condition(condition, condition_type, indicator_aliases)
        else:
            # Simple condition validation (original logic)
            if "compare" not in condition:
                raise ValueError(f"'{condition_type}' condition must have 'compare' field")
            
            if not isinstance(condition["compare"], str):
                raise ValueError(f"'{condition_type}' compare must be a string")
            
            # Validate that comparison uses valid indicator aliases
            compare_str = condition["compare"]
            
            # Check that at least one indicator alias is referenced
            aliases_found = [alias for alias in indicator_aliases if alias in compare_str]
            if not aliases_found:
                raise ValueError(f"'{condition_type}' condition must reference at least one indicator alias: {list(indicator_aliases)}")
            
            # Validate comparison operators
            valid_operators = [">", "<", ">=", "<=", "==", "!="]
            has_operator = any(op in compare_str for op in valid_operators)
            
            if not has_operator:
                raise ValueError(f"'{condition_type}' condition must contain a comparison operator: {valid_operators}")


def _validate_rotation_condition(condition: Dict[str, Any], condition_type: str, indicator_aliases: set) -> None:
    """Validate a rotation-type condition (zone + crossover trigger)."""
    # Validate zone specification
    if "zone" not in condition:
        raise ValueError(f"'{condition_type}' rotation condition must have 'zone' field")
    
    zone = condition["zone"]
    
    # Must have either all_above or all_below
    if "all_above" not in zone and "all_below" not in zone:
        raise ValueError(f"'{condition_type}' zone must have either 'all_above' or 'all_below' field")
    
    # Cannot have both
    if "all_above" in zone and "all_below" in zone:
        raise ValueError(f"'{condition_type}' zone cannot have both 'all_above' and 'all_below'")
    
    # Validate threshold is a number
    threshold_key = "all_above" if "all_above" in zone else "all_below"
    threshold = zone[threshold_key]
    if not isinstance(threshold, (int, float)):
        raise ValueError(f"'{condition_type}' zone {threshold_key} must be a number")
    
    # Validate indicators list
    if "indicators" not in zone:
        raise ValueError(f"'{condition_type}' zone must have 'indicators' list")
    
    zone_indicators = zone["indicators"]
    if not isinstance(zone_indicators, list) or not zone_indicators:
        raise ValueError(f"'{condition_type}' zone indicators must be a non-empty list")
    
    # Validate all indicators exist
    for alias in zone_indicators:
        if alias not in indicator_aliases:
            raise ValueError(f"'{condition_type}' zone references unknown indicator '{alias}'. Available: {list(indicator_aliases)}")
    
    # Validate trigger specification
    if "trigger" not in condition:
        raise ValueError(f"'{condition_type}' rotation condition must have 'trigger' field")
    
    trigger = condition["trigger"]
    
    # Validate trigger indicator
    if "indicator" not in trigger:
        raise ValueError(f"'{condition_type}' trigger must have 'indicator' field")
    
    trigger_indicator = trigger["indicator"]
    if trigger_indicator not in indicator_aliases:
        raise ValueError(f"'{condition_type}' trigger references unknown indicator '{trigger_indicator}'. Available: {list(indicator_aliases)}")
    
    # Must have either crosses_above or crosses_below
    if "crosses_above" not in trigger and "crosses_below" not in trigger:
        raise ValueError(f"'{condition_type}' trigger must have either 'crosses_above' or 'crosses_below' field")
    
    # Cannot have both
    if "crosses_above" in trigger and "crosses_below" in trigger:
        raise ValueError(f"'{condition_type}' trigger cannot have both 'crosses_above' and 'crosses_below'")
    
    # Validate threshold is a number
    cross_key = "crosses_above" if "crosses_above" in trigger else "crosses_below"
    cross_threshold = trigger[cross_key]
    if not isinstance(cross_threshold, (int, float)):
        raise ValueError(f"'{condition_type}' trigger {cross_key} must be a number")


def get_dsl_schema() -> Dict[str, Any]:
    """
    Get the complete DSL strategy JSON schema.
    
    Returns:
        Dict[str, Any]: JSON schema for DSL strategies
    """
    return DSL_STRATEGY_SCHEMA.copy()


if __name__ == "__main__":
    # Test the validator with a sample configuration
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
        validate_dsl_strategy(sample_config)
        print("✅ Sample DSL configuration is valid!")
    except DSLValidationError as e:
        print(f"❌ Validation failed: {e}")