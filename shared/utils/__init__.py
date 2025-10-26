"""
Shared utility functions for Trading MCP servers.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime, time as dt_time


# Constants
DEFAULT_STOP_LOSS_PIPS = 10
DEFAULT_TAKE_PROFIT_PIPS = 15
DEFAULT_SIGNAL_TIME = dt_time(8, 30)
CHARACTER_LIMIT = 25000


def get_config() -> Dict[str, Any]:
    """Get configuration from environment variables."""
    return {
        "ctrader_api_url": os.environ.get("CTRADER_API_URL", "http://localhost:8000"),
        "ctrader_api_username": os.environ.get("CTRADER_API_USERNAME", "admin"),
        "ctrader_api_password": os.environ.get("CTRADER_API_PASSWORD", "password"),
        "charts_output_dir": os.environ.get("CHARTS_OUTPUT_DIR", 
            "/Users/paul/Sites/PythonProjects/Trading-MCP/data/charts"),
        "data_output_dir": os.environ.get("DATA_OUTPUT_DIR", 
            "/Users/paul/Sites/PythonProjects/Trading-MCP/data/optimization_results")
    }


def calculate_pips(symbol: str, entry_price: float, exit_price: float, direction: str) -> float:
    """Calculate pip difference between entry and exit prices."""
    if symbol.startswith("JPY") or symbol.endswith("JPY"):
        pip_decimal_places = 2
        pip_size = 0.01
    else:
        pip_decimal_places = 4
        pip_size = 0.0001
    
    price_diff = exit_price - entry_price
    
    if direction.upper() == "SELL":
        price_diff = -price_diff
        
    return round(price_diff / pip_size, 1)


def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display."""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def sanitize_symbol(symbol: str) -> str:
    """Sanitize symbol for file names and IDs."""
    return symbol.upper().replace("/", "").replace(".", "")


def ensure_directory_exists(directory: str) -> None:
    """Ensure directory exists, create if not."""
    os.makedirs(directory, exist_ok=True)


def get_project_root() -> str:
    """Get the project root directory."""
    return "/Users/paul/Sites/PythonProjects/Trading-MCP"


# Import VWAP calculator
try:
    from .vwap_calculator import (
        TradingViewVWAP, 
        calculate_vwap_for_strategy, 
        get_vwap_at_time
    )
except ImportError:
    # Fallback if module not available
    TradingViewVWAP = None
    calculate_vwap_for_strategy = None
    get_vwap_at_time = None