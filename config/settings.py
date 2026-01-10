"""
Configuration settings for Trading MCP servers.
"""

import os
from pathlib import Path


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHARTS_DIR = DATA_DIR / "charts"
OPTIMIZATION_RESULTS_DIR = DATA_DIR / "optimization_results"
CONFIG_DIR = PROJECT_ROOT / "config"

# API Configuration
CTRADER_API_CONFIG = {
    "url": os.environ.get("CTRADER_API_URL", "http://localhost:8000"),
    "username": os.environ.get("CTRADER_API_USERNAME", "admin"),
    "password": os.environ.get("CTRADER_API_PASSWORD", "password"),
}

# VPS Tick Data Configuration (tunneled to local port)
VPS_TICK_API_CONFIG = {
    "enabled": os.environ.get("VPS_TICK_ENABLED", "true").lower() == "true",
    "url": os.environ.get("VPS_TICK_URL", "http://localhost:8020"),
}

# Trading Strategy Defaults
STRATEGY_DEFAULTS = {
    "stop_loss_pips": 10,
    "take_profit_pips": 15,
    "signal_time": "08:30",
    "character_limit": 25000,
}

# Supported symbols and timeframes
SUPPORTED_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD",
    "EURGBP", "EURJPY", "GBPJPY", "AUDJPY",
    "GER40", "UK100", "US30", "NAS100"
]

SUPPORTED_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]

# Chart Configuration
CHART_CONFIG = {
    "width": 1200,
    "height": 800,
    "theme": "plotly_white",
    "colors": {
        "buy_entry": "green",
        "sell_entry": "red", 
        "win_exit": "darkgreen",
        "loss_exit": "darkred",
        "breakeven_exit": "orange",
        "vwap": "blue",
        "profit_line": "green",
        "loss_line": "red"
    }
}