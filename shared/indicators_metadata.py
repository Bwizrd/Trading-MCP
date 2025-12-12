"""
Indicator metadata infrastructure for chart visualization.

This module provides a centralized registry for indicator visualization metadata,
enabling automatic routing of indicators to appropriate chart locations (overlays
vs. oscillators) with proper scaling and styling.
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import re
import logging

logger = logging.getLogger(__name__)


class IndicatorType(Enum):
    """Types of indicators based on visualization requirements."""
    OVERLAY = "overlay"      # Plot on price chart (same scale)
    OSCILLATOR = "oscillator"  # Plot in separate subplot (different scale)
    VOLUME = "volume"        # Plot in volume subplot


class ScaleType(Enum):
    """Y-axis scaling strategies."""
    AUTO = "auto"           # Auto-scale based on values
    FIXED = "fixed"         # Fixed min/max range
    PRICE = "price"         # Use same scale as price


@dataclass
class ReferenceLine:
    """Configuration for horizontal reference lines."""
    value: float
    color: str
    label: str
    style: str = "dash"  # solid, dash, dot


@dataclass
class ComponentStyle:
    """Styling for indicator components (lines, histograms)."""
    color: str
    label: str
    line_type: str = "line"  # line, bar, area
    width: float = 2.0
    dash: Optional[str] = None  # None, dash, dot


@dataclass
class IndicatorMetadata:
    """Complete metadata for an indicator's visualization."""
    name: str
    indicator_type: IndicatorType
    scale_type: ScaleType
    scale_min: Optional[float] = None
    scale_max: Optional[float] = None
    zero_line: bool = False
    reference_lines: List[ReferenceLine] = field(default_factory=list)
    components: Dict[str, ComponentStyle] = field(default_factory=dict)


class IndicatorMetadataRegistry:
    """Central registry for indicator visualization metadata."""
    
    def __init__(self):
        self._metadata: Dict[str, IndicatorMetadata] = {}
        self._register_default_metadata()
    
    def _register_default_metadata(self):
        """Register metadata for all built-in indicators."""
        # MACD - Oscillator with zero line
        self.register(IndicatorMetadata(
            name="MACD",
            indicator_type=IndicatorType.OSCILLATOR,
            scale_type=ScaleType.AUTO,
            zero_line=True,
            components={
                "macd": ComponentStyle(color="#2196F3", label="MACD", width=2.5),
                "signal": ComponentStyle(color="#FF5722", label="Signal", width=2.0),
                "histogram": ComponentStyle(color="#9E9E9E", label="Histogram", line_type="bar")
            }
        ))
        
        # RSI - Oscillator with 0-100 scale and overbought/oversold lines
        self.register(IndicatorMetadata(
            name="RSI",
            indicator_type=IndicatorType.OSCILLATOR,
            scale_type=ScaleType.FIXED,
            scale_min=0,
            scale_max=100,
            reference_lines=[
                ReferenceLine(value=70, color="#F44336", label="Overbought"),
                ReferenceLine(value=30, color="#4CAF50", label="Oversold")
            ],
            components={
                "rsi": ComponentStyle(color="#9C27B0", label="RSI", width=2.5)
            }
        ))
        
        # Stochastic - Oscillator with 0-100 scale and 20/80 lines
        self.register(IndicatorMetadata(
            name="Stochastic",
            indicator_type=IndicatorType.OSCILLATOR,
            scale_type=ScaleType.FIXED,
            scale_min=0,
            scale_max=100,
            reference_lines=[
                ReferenceLine(value=80, color="#F44336", label="Overbought"),
                ReferenceLine(value=20, color="#4CAF50", label="Oversold")
            ],
            components={
                "k": ComponentStyle(color="#2196F3", label="%K", width=2.5),
                "d": ComponentStyle(color="#FF9800", label="%D", width=2.0, dash="dash")
            }
        ))
        
        # SMA - Overlay on price chart
        self.register(IndicatorMetadata(
            name="SMA",
            indicator_type=IndicatorType.OVERLAY,
            scale_type=ScaleType.PRICE,
            components={
                "sma": ComponentStyle(color="#2196F3", label="SMA", width=2.0)
            }
        ))
        
        # EMA - Overlay on price chart
        self.register(IndicatorMetadata(
            name="EMA",
            indicator_type=IndicatorType.OVERLAY,
            scale_type=ScaleType.PRICE,
            components={
                "ema": ComponentStyle(color="#FF9800", label="EMA", width=2.0)
            }
        ))
        
        # VWAP - Overlay on price chart
        self.register(IndicatorMetadata(
            name="VWAP",
            indicator_type=IndicatorType.OVERLAY,
            scale_type=ScaleType.PRICE,
            components={
                "vwap": ComponentStyle(color="#FF9800", label="VWAP", width=2.5)
            }
        ))
    
    def register(self, metadata: IndicatorMetadata):
        """
        Register metadata for an indicator.
        
        Validates metadata before registration to ensure it contains valid values.
        
        Args:
            metadata: IndicatorMetadata object to register
            
        Raises:
            ValueError: If metadata is invalid
        """
        # Validate metadata
        if not metadata.name:
            raise ValueError("Indicator metadata must have a non-empty name")
        
        if not isinstance(metadata.indicator_type, IndicatorType):
            raise ValueError(f"Invalid indicator_type: {metadata.indicator_type}. Must be IndicatorType enum.")
        
        if not isinstance(metadata.scale_type, ScaleType):
            raise ValueError(f"Invalid scale_type: {metadata.scale_type}. Must be ScaleType enum.")
        
        # Validate FIXED scale has min/max values
        if metadata.scale_type == ScaleType.FIXED:
            if metadata.scale_min is None or metadata.scale_max is None:
                raise ValueError(f"FIXED scale type requires scale_min and scale_max values for {metadata.name}")
            if metadata.scale_min >= metadata.scale_max:
                raise ValueError(f"scale_min must be less than scale_max for {metadata.name}")
        
        # Validate reference lines
        if metadata.reference_lines:
            for ref_line in metadata.reference_lines:
                if not isinstance(ref_line, ReferenceLine):
                    raise ValueError(f"Invalid reference line in {metadata.name}: must be ReferenceLine object")
                if ref_line.value is None:
                    raise ValueError(f"Reference line must have a value in {metadata.name}")
        
        # Validate components
        if metadata.components:
            for comp_name, comp_style in metadata.components.items():
                if not isinstance(comp_style, ComponentStyle):
                    raise ValueError(f"Invalid component style '{comp_name}' in {metadata.name}: must be ComponentStyle object")
        
        # Register the validated metadata
        self._metadata[metadata.name] = metadata
        logger.info(f"Registered metadata for indicator: {metadata.name} (type: {metadata.indicator_type.value}, scale: {metadata.scale_type.value})")
    
    def get(self, indicator_name: str) -> Optional[IndicatorMetadata]:
        """
        Get metadata for an indicator by name.
        
        Handles variations like "SMA20", "SMA50" → "SMA".
        Logs a warning if metadata is not found.
        
        Args:
            indicator_name: Name of the indicator (may include parameters)
            
        Returns:
            IndicatorMetadata object if found, None otherwise
        """
        try:
            # Handle variations like "SMA20", "SMA50" → "SMA"
            base_name = self._extract_base_name(indicator_name)
            metadata = self._metadata.get(base_name)
            
            if metadata is None:
                logger.warning(f"No metadata found for indicator '{indicator_name}' (base name: '{base_name}'). "
                             f"Available indicators: {list(self._metadata.keys())}")
            
            return metadata
        except Exception as e:
            logger.error(f"Error retrieving metadata for '{indicator_name}': {e}")
            return None
    
    def _extract_base_name(self, indicator_name: str) -> str:
        """Extract base indicator name from variations like SMA20 → SMA."""
        # First, try exact match (for DSL strategies with custom aliases like "fast", "med_fast")
        if indicator_name in self._metadata:
            return indicator_name
        
        # Remove numbers and underscores to get base name
        base = re.sub(r'\d+', '', indicator_name)
        base = re.sub(r'_.*', '', base)
        
        # Try different case variations to find a match
        # 1. Try uppercase (MACD, RSI, SMA, EMA, VWAP)
        base_upper = base.upper()
        if base_upper in self._metadata:
            return base_upper
        
        # 2. Try title case (Stochastic)
        base_title = base.title()
        if base_title in self._metadata:
            return base_title
        
        # 3. Try original case
        if base in self._metadata:
            return base
        
        # 4. Try the original indicator_name as-is (before any transformations)
        if indicator_name in self._metadata:
            return indicator_name
        
        # Default to uppercase for consistency
        return base_upper
    
    def is_oscillator(self, indicator_name: str) -> bool:
        """Check if indicator is an oscillator."""
        metadata = self.get(indicator_name)
        return metadata and metadata.indicator_type == IndicatorType.OSCILLATOR
    
    def is_overlay(self, indicator_name: str) -> bool:
        """Check if indicator is an overlay."""
        metadata = self.get(indicator_name)
        return metadata and metadata.indicator_type == IndicatorType.OVERLAY


# Global registry instance
metadata_registry = IndicatorMetadataRegistry()
