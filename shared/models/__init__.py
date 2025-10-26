"""
Common Pydantic models shared across MCP servers.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class TradeDirection(str, Enum):
    """Trade direction."""
    BUY = "BUY"
    SELL = "SELL"


class TradeResult(str, Enum):
    """Trade outcome."""
    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"
    EOD_CLOSE = "eod_close"


class Candle(BaseModel):
    """OHLC candle data model."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


class Trade(BaseModel):
    """Trade execution model."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    entry_time: datetime
    exit_time: Optional[datetime] = None
    direction: TradeDirection
    entry_price: float
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    result: Optional[TradeResult] = None
    pips: Optional[float] = None
    profit_loss: Optional[float] = None


class BacktestInput(BaseModel):
    """Input model for backtesting strategies."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    symbol: str = Field(
        ...,
        description="Trading symbol (e.g., EURUSD, GBPUSD)",
        pattern=r"^[A-Z]{3}[A-Z]{3}$|^[A-Z]{2,6}\d{2,3}$"
    )
    start_date: str = Field(
        ...,
        description="Start date in YYYY-MM-DD format",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    end_date: str = Field(
        ...,
        description="End date in YYYY-MM-DD format", 
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    timeframe: str = Field(
        default="1h",
        description="Chart timeframe (e.g., 1m, 5m, 15m, 30m, 1h, 4h, 1d)"
    )
    stop_loss_pips: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Stop loss distance in pips"
    )
    take_profit_pips: int = Field(
        default=15,
        ge=1,
        le=1000,
        description="Take profit distance in pips"
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Response format"
    )


class ChartInput(BaseModel):
    """Input model for chart generation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    symbol: str = Field(
        ...,
        description="Trading symbol (e.g., EURUSD, GBPUSD)",
        pattern=r"^[A-Z]{3}[A-Z]{3}$|^[A-Z]{2,6}\d{2,3}$"
    )
    start_date: str = Field(
        ...,
        description="Start date in YYYY-MM-DD format",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    end_date: str = Field(
        ...,
        description="End date in YYYY-MM-DD format", 
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    timeframe: str = Field(
        default="30m",
        description="Chart timeframe (e.g., 15m, 30m, 1h, 4h, 1d)"
    )
    chart_type: str = Field(
        default="comprehensive",
        description="Chart type: candlestick, performance, comprehensive"
    )