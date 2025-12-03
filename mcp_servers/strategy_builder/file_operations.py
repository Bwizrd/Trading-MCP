"""
DSL Strategy File Operations

Handles saving and listing DSL strategy cartridges.
"""

import json
import re
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from mcp_servers.strategy_builder.validators import validate_dsl_json


# Get the absolute path to the dsl_strategies directory
DSL_STRATEGIES_DIR = Path(__file__).parent.parent.parent / "shared" / "strategies" / "dsl_strategies"


def sanitize_filename(name: str) -> str:
    """
    Sanitize a strategy name to create a valid filename.
    
    Removes or replaces invalid filename characters and ensures the result
    is a valid filename across different operating systems.
    
    Args:
        name: Strategy name to sanitize
        
    Returns:
        Sanitized filename (without .json extension)
    """
    # First, strip leading/trailing whitespace
    sanitized = name.strip()
    
    # Replace spaces with underscores
    sanitized = sanitized.replace(" ", "_")
    
    # Remove or replace invalid filename characters
    # Invalid characters: / \ : * ? " < > |
    invalid_chars = r'[/\\:*?"<>|]'
    sanitized = re.sub(invalid_chars, '', sanitized)
    
    # Remove leading/trailing dots and underscores
    sanitized = sanitized.strip('._')
    
    # Ensure the filename is not empty
    if not sanitized:
        sanitized = "unnamed_strategy"
    
    # Limit length to reasonable size (max 100 characters)
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    # Convert to lowercase for consistency
    sanitized = sanitized.lower()
    
    return sanitized


def generate_filename_from_strategy(strategy_config: Dict[str, Any]) -> str:
    """
    Generate a filename from a strategy configuration.
    
    Args:
        strategy_config: Parsed DSL strategy configuration
        
    Returns:
        Filename with .json extension
    """
    # Extract strategy name
    strategy_name = strategy_config.get("name", "unnamed_strategy")
    
    # Sanitize the name
    sanitized = sanitize_filename(strategy_name)
    
    # Add .json extension
    return f"{sanitized}.json"


def save_dsl_strategy_to_file(
    dsl_json_str: str,
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Save DSL strategy JSON to the dsl_strategies directory.
    
    Args:
        dsl_json_str: The DSL JSON as a string
        filename: Optional filename (auto-generated if not provided)
        
    Returns:
        Dictionary with save results:
        {
            "success": bool,
            "file_path": str,  # Full absolute path to saved file
            "message": str
        }
    """
    # Step 1: Validate the DSL JSON first
    validation_result = validate_dsl_json(dsl_json_str)
    
    if not validation_result["valid"]:
        errors_formatted = "\n".join(f"  • {error}" for error in validation_result["errors"])
        return {
            "success": False,
            "file_path": "",
            "message": f"Cannot save invalid strategy. Validation errors:\n{errors_formatted}"
        }
    
    # Step 2: Parse the JSON
    try:
        strategy_config = json.loads(dsl_json_str)
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "file_path": "",
            "message": f"Invalid JSON: {str(e)}"
        }
    
    # Step 3: Generate filename if not provided
    if filename:
        # Sanitize provided filename
        if not filename.endswith(".json"):
            filename = f"{filename}.json"
        # Sanitize the base name
        base_name = filename[:-5]  # Remove .json
        sanitized_base = sanitize_filename(base_name)
        final_filename = f"{sanitized_base}.json"
    else:
        # Auto-generate from strategy name
        final_filename = generate_filename_from_strategy(strategy_config)
    
    # Step 4: Ensure the dsl_strategies directory exists
    DSL_STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 5: Construct full file path
    file_path = DSL_STRATEGIES_DIR / final_filename
    
    # Step 6: Check if file already exists
    file_exists = file_path.exists()
    
    # Step 7: Write the file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(strategy_config, f, indent=2, ensure_ascii=False)
        
        # Step 8: Return success with full path
        strategy_name = strategy_config.get("name", "unknown")
        action = "updated" if file_exists else "created"
        
        return {
            "success": True,
            "file_path": str(file_path.absolute()),
            "message": f"Strategy '{strategy_name}' successfully {action} at: {file_path.absolute()}"
        }
        
    except IOError as e:
        return {
            "success": False,
            "file_path": str(file_path.absolute()),
            "message": f"Failed to write file: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "file_path": str(file_path.absolute()),
            "message": f"Unexpected error while saving: {str(e)}"
        }


def list_dsl_strategies() -> Dict[str, Any]:
    """
    List all available DSL strategy cartridges.
    
    Scans the dsl_strategies directory and extracts metadata from each JSON file.
    
    Returns:
        Dictionary with list results:
        {
            "strategies": List[Dict],  # List of strategy info
            "count": int
        }
        
        Each strategy dict contains:
        {
            "name": str,
            "filename": str,
            "type": str,  # "time-based" or "indicator-based"
            "version": str,
            "description": str
        }
    """
    # Ensure the directory exists
    if not DSL_STRATEGIES_DIR.exists():
        return {
            "strategies": [],
            "count": 0,
            "message": f"DSL strategies directory not found: {DSL_STRATEGIES_DIR}"
        }
    
    strategies = []
    
    # Scan directory for JSON files
    for json_file in DSL_STRATEGIES_DIR.glob("*.json"):
        try:
            # Read and parse the JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                strategy_config = json.load(f)
            
            # Determine strategy type
            if "timing" in strategy_config:
                strategy_type = "time-based"
            elif "indicators" in strategy_config:
                strategy_type = "indicator-based"
            else:
                strategy_type = "unknown"
            
            # Extract metadata
            strategy_info = {
                "name": strategy_config.get("name", "Unknown Strategy"),
                "filename": json_file.name,
                "type": strategy_type,
                "version": strategy_config.get("version", "unknown"),
                "description": strategy_config.get("description", "No description available")
            }
            
            strategies.append(strategy_info)
            
        except json.JSONDecodeError as e:
            # Skip invalid JSON files but log the issue
            print(f"Warning: Skipping invalid JSON file {json_file.name}: {str(e)}")
            continue
        except Exception as e:
            # Skip files that cause other errors
            print(f"Warning: Error reading {json_file.name}: {str(e)}")
            continue
    
    # Sort strategies by name for consistent ordering
    strategies.sort(key=lambda x: x["name"].lower())
    
    return {
        "strategies": strategies,
        "count": len(strategies)
    }
