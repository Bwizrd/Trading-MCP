"""
DSL Strategy Validation

Wraps the existing schema_validator to provide validation logic for MCP tools.
"""

import json
from typing import Dict, Any, List
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.strategies.dsl_interpreter.schema_validator import validate_dsl_strategy, DSLValidationError


def validate_dsl_json(dsl_json_str: str) -> Dict[str, Any]:
    """
    Validate DSL JSON string against the schema.
    
    Args:
        dsl_json_str: The DSL JSON as a string
        
    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "errors": List[str],
            "strategy_type": str,  # "time-based" or "indicator-based"
            "strategy_name": str
        }
    """
    errors = []
    strategy_type = "unknown"
    strategy_name = "unknown"
    
    # Step 1: Validate input parameter - must be a non-empty string
    if not isinstance(dsl_json_str, str):
        return {
            "valid": False,
            "errors": ["Input must be a string"],
            "strategy_type": strategy_type,
            "strategy_name": strategy_name
        }
    
    if not dsl_json_str.strip():
        return {
            "valid": False,
            "errors": ["Input cannot be empty"],
            "strategy_type": strategy_type,
            "strategy_name": strategy_name
        }
    
    # Step 2: Parse JSON
    try:
        strategy_config = json.loads(dsl_json_str)
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "errors": [f"Invalid JSON syntax: {str(e)}"],
            "strategy_type": strategy_type,
            "strategy_name": strategy_name
        }
    
    # Step 3: Extract strategy name if present
    if isinstance(strategy_config, dict) and "name" in strategy_config:
        strategy_name = strategy_config["name"]
    
    # Step 4: Determine strategy type
    has_indicators = "indicators" in strategy_config and strategy_config.get("indicators")
    has_timing = "timing" in strategy_config and strategy_config.get("timing")
    
    if has_indicators and not has_timing:
        strategy_type = "indicator-based"
    elif has_timing and not has_indicators:
        strategy_type = "time-based"
    elif has_indicators and has_timing:
        errors.append("Strategy cannot have both 'timing' and 'indicators' fields - must be either time-based OR indicator-based")
    elif not has_indicators and not has_timing:
        errors.append("Strategy must have either 'timing' field (time-based) or 'indicators' field (indicator-based)")
    
    # Step 5: Validate against schema using existing validator
    try:
        validate_dsl_strategy(strategy_config)
        
        # If we get here, validation passed
        return {
            "valid": True,
            "errors": [],
            "strategy_type": strategy_type,
            "strategy_name": strategy_name,
            "message": f"Strategy '{strategy_name}' is valid and ready for use"
        }
        
    except DSLValidationError as e:
        # Extract specific error message
        error_msg = str(e)
        # Remove the "DSL strategy validation failed: " prefix if present
        if error_msg.startswith("DSL strategy validation failed: "):
            error_msg = error_msg[len("DSL strategy validation failed: "):]
        
        errors.append(error_msg)
        
    except ValueError as e:
        # Catch ValueError from schema validator
        errors.append(str(e))
        
    except Exception as e:
        # Catch any other unexpected errors
        errors.append(f"Validation error: {str(e)}")
    
    # Return validation failure with specific errors
    return {
        "valid": False,
        "errors": errors,
        "strategy_type": strategy_type,
        "strategy_name": strategy_name
    }
