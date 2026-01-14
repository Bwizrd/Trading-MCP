#!/usr/bin/env python3
"""
DSL Loader

Discovers and loads DSL strategies from JSON files in the dsl_strategies directory.
This integrates with the existing StrategyRegistry to make DSL strategies appear
alongside code-based strategies.

CRITICAL: This extends the existing modular architecture WITHOUT breaking anything.
It works with the existing StrategyRegistry and DataConnector systems.
"""

from typing import Dict, List, Any, Optional, Type
from pathlib import Path
import json
import os

from shared.strategy_interface import TradingStrategy
from .dsl_strategy import DSLStrategy, create_dsl_strategy_from_file
from .schema_validator import validate_dsl_file, DSLValidationError


class DSLLoader:
    """
    DSL Strategy Loader
    
    Discovers, validates, and loads DSL strategies from JSON files.
    This allows the StrategyRegistry to treat DSL strategies like code-based strategies.
    """
    
    def __init__(self, dsl_strategies_directory: str = None):
        """
        Initialize DSL loader.
        
        Args:
            dsl_strategies_directory: Directory containing DSL strategy JSON files
        """
        if dsl_strategies_directory is None:
            # Default to shared/strategies/dsl_strategies
            current_dir = Path(__file__).parent.parent
            dsl_strategies_directory = current_dir / "dsl_strategies"
        
        self.dsl_strategies_directory = Path(dsl_strategies_directory)
        self._dsl_strategies: Dict[str, Dict[str, Any]] = {}
        self._dsl_info: Dict[str, Dict[str, Any]] = {}
        
        # Auto-discover DSL strategies on initialization
        self.discover_dsl_strategies()
    
    def discover_dsl_strategies(self) -> None:
        """
        Discover all DSL strategy JSON files in the dsl_strategies directory.
        
        This scans JSON files and validates them as DSL strategies.
        """
        if not self.dsl_strategies_directory.exists():
            # print(f"DSL strategies directory does not exist: {self.dsl_strategies_directory}")
            return
        
        # Clear existing registrations
        self._dsl_strategies.clear()
        self._dsl_info.clear()
        
        # Scan JSON files in dsl_strategies directory
        for json_file in self.dsl_strategies_directory.glob("*.json"):
            try:
                self._load_dsl_strategy_from_file(json_file)
            except Exception as e:
                import logging; logging.warning(f"Failed to load DSL strategy from {json_file}: {e}")
    
    def _load_dsl_strategy_from_file(self, json_file: Path) -> None:
        """
        Load and validate DSL strategy from JSON file.
        
        Args:
            json_file: Path to DSL strategy JSON file
        """
        try:
            # Validate and load DSL configuration
            dsl_config = validate_dsl_file(str(json_file))
            
            # Register the DSL strategy
            strategy_name = dsl_config["name"]
            
            # Store DSL configuration and metadata
            self._dsl_strategies[strategy_name] = dsl_config
            # Build info dict with conditional timing
            info_dict = {
                "class_name": "DSLStrategy",
                "description": dsl_config["description"],
                "version": dsl_config["version"],
                "required_indicators": [],  # DSL strategies don't require indicators by default
                "default_parameters": dsl_config.get("parameters", {}),
                "module": f"dsl_strategies.{json_file.stem}",
                "file": str(json_file),
                "dsl_strategy": True,  # Mark as DSL strategy
                "conditions": dsl_config["conditions"],
                "risk_management": dsl_config["risk_management"]
            }
            
            # Add timing only if present (time-based strategies)
            if "timing" in dsl_config:
                info_dict["timing"] = dsl_config["timing"]
            
            # Add indicators only if present (indicator-based strategies)
            if "indicators" in dsl_config:
                info_dict["indicators"] = dsl_config["indicators"]
            
            self._dsl_info[strategy_name] = info_dict
            
            # print(f"✅ Registered DSL strategy: {strategy_name} (v{dsl_config['version']})")
            
        except DSLValidationError as e:
            import logging; logging.warning(f"DSL validation failed for {json_file}: {e}")
        except Exception as e:
            import logging; logging.warning(f"Could not load DSL strategy from {json_file}: {e}")
    
    def get_dsl_strategy_names(self) -> List[str]:
        """
        Get list of all DSL strategy names.
        
        Returns:
            List[str]: List of DSL strategy names
        """
        return list(self._dsl_strategies.keys())
    
    def get_dsl_strategy_config(self, name: str) -> Dict[str, Any]:
        """
        Get DSL configuration for a strategy.
        
        Args:
            name: Name of the DSL strategy
            
        Returns:
            Dict[str, Any]: DSL strategy configuration
            
        Raises:
            KeyError: If DSL strategy is not found
        """
        if name not in self._dsl_strategies:
            raise KeyError(f"DSL strategy '{name}' not found. Available: {list(self._dsl_strategies.keys())}")
        
        return self._dsl_strategies[name].copy()
    
    def get_dsl_strategy_info(self, name: str) -> Dict[str, Any]:
        """
        Get detailed information about a DSL strategy.
        
        Args:
            name: Name of the DSL strategy
            
        Returns:
            Dict[str, Any]: DSL strategy information
        """
        if name not in self._dsl_info:
            raise KeyError(f"DSL strategy '{name}' not found")
        
        return self._dsl_info[name].copy()
    
    def create_dsl_strategy(self, name: str, parameters: Dict[str, Any] = None) -> DSLStrategy:
        """
        Create an instance of a DSL strategy by name.
        
        Args:
            name: Name of the DSL strategy
            parameters: Optional parameters to override defaults
            
        Returns:
            DSLStrategy: Initialized DSL strategy instance
        """
        dsl_config = self.get_dsl_strategy_config(name)
        
        # Override parameters if provided
        if parameters:
            if "parameters" not in dsl_config:
                dsl_config["parameters"] = {}
            dsl_config["parameters"].update(parameters)
        
        # Create and initialize DSL strategy
        strategy = DSLStrategy(dsl_config)
        strategy.initialize(parameters)
        
        return strategy
    
    def get_all_dsl_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all DSL strategies.
        
        Returns:
            Dict[str, Dict[str, Any]]: Mapping of strategy names to info
        """
        return self._dsl_info.copy()
    
    def reload_dsl_strategies(self) -> None:
        """
        Reload all DSL strategies from the filesystem.
        
        Useful during development when DSL JSON files are modified.
        """
        # print("🔄 Reloading DSL strategy configurations...")
        self._load_dsl_strategies()
        # print(f"✅ Reloaded {len(self._dsl_strategies)} DSL strategies")
    
    def create_dsl_strategy_file(self, name: str, dsl_config: Dict[str, Any]) -> str:
        """
        Create a new DSL strategy JSON file.
        
        Args:
            name: Name for the strategy file (will be sanitized)
            dsl_config: DSL strategy configuration
            
        Returns:
            str: Path to created file
            
        Raises:
            DSLValidationError: If configuration is invalid
        """
        # Validate configuration first
        from .schema_validator import validate_dsl_strategy
        validate_dsl_strategy(dsl_config)
        
        # Sanitize filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_').lower()
        
        # Create file path
        json_filename = f"{safe_name}.json"
        json_filepath = self.dsl_strategies_directory / json_filename
        
        # Ensure directory exists
        self.dsl_strategies_directory.mkdir(exist_ok=True)
        
        # Write JSON file
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(dsl_config, f, indent=2, ensure_ascii=False)
        
        # Reload strategies to include the new one
        self.discover_dsl_strategies()
        
        return str(json_filepath)
    
    def delete_dsl_strategy_file(self, name: str) -> bool:
        """
        Delete a DSL strategy file.
        
        Args:
            name: Name of the DSL strategy to delete
            
        Returns:
            bool: True if file was deleted successfully
        """
        if name not in self._dsl_info:
            return False
        
        try:
            file_path = Path(self._dsl_info[name]["file"])
            if file_path.exists():
                file_path.unlink()
                
            # Reload strategies to remove the deleted one
            self.discover_dsl_strategies()
            return True
            
        except Exception as e:
            import logging; logging.warning(f"Failed to delete DSL strategy file: {e}")
            return False
    
    def print_dsl_catalog(self) -> None:
        """Print a formatted catalog of all DSL strategies."""
        print("\n" + "="*80)
        print("🤖 DSL STRATEGY CATALOG (JSON-Configured)")
        print("="*80)
        
        if not self._dsl_strategies:
            print("No DSL strategies found. Create JSON files in the dsl_strategies directory.")
            return
        
        for name, info in self._dsl_info.items():
            print(f"\n📋 {name} (v{info['version']})")
            print(f"   {info['description']}")
            print(f"   ⏰ Timing: {info['timing']['reference_time']} → {info['timing']['signal_time']}")
            print(f"   🎯 Risk: {info['risk_management']['stop_loss_pips']}SL / {info['risk_management']['take_profit_pips']}TP")
            print(f"   📁 File: {info['file']}")
        
        print(f"\n🤖 Total DSL strategies available: {len(self._dsl_strategies)}")
        print("="*80)


# Integration functions for StrategyRegistry
def integrate_dsl_with_strategy_registry(strategy_registry, dsl_loader: DSLLoader = None) -> None:
    """
    Integrate DSL strategies with the existing StrategyRegistry.
    
    This makes DSL strategies appear alongside code-based strategies in the registry.
    
    Args:
        strategy_registry: StrategyRegistry instance to extend
        dsl_loader: DSLLoader instance (created if None)
    """
    if dsl_loader is None:
        dsl_loader = DSLLoader()
    
    # Add DSL strategies to the registry's internal storage
    for strategy_name in dsl_loader.get_dsl_strategy_names():
        # Create a DSL strategy "class" that can be instantiated
        def create_dsl_strategy_class(config_name: str):
            class DSLStrategyWrapper(TradingStrategy):
                def __init__(self):
                    self._dsl_loader = dsl_loader
                    self._config_name = config_name
                    dsl_config = self._dsl_loader.get_dsl_strategy_config(config_name)
                    self._dsl_strategy = DSLStrategy(dsl_config)
                    super().__init__()
                
                def get_name(self) -> str:
                    return self._dsl_strategy.get_name()
                
                def get_description(self) -> str:
                    return self._dsl_strategy.get_description()
                
                def get_version(self) -> str:
                    return self._dsl_strategy.get_version()
                
                def get_default_parameters(self) -> Dict[str, Any]:
                    return self._dsl_strategy.get_default_parameters()
                
                def requires_indicators(self) -> List[str]:
                    return self._dsl_strategy.requires_indicators()
                
                def generate_signal(self, context):
                    signal = self._dsl_strategy.generate_signal(context)
                    # DEBUG: Log wrapper signal forwarding
                    if signal:
                        with open('/tmp/dsl_debug.log', 'a') as f:
                            f.write(f"WRAPPER FORWARDING SIGNAL: {signal.direction} @ {signal.price}\n")
                    return signal
                
                def initialize(self, parameters: Dict[str, Any] = None) -> None:
                    super().initialize(parameters)
                    self._dsl_strategy.initialize(parameters)
                
                def on_trade_opened(self, trade, context) -> None:
                    return self._dsl_strategy.on_trade_opened(trade, context)
                
                def on_trade_closed(self, trade, context) -> None:
                    return self._dsl_strategy.on_trade_closed(trade, context)
                
                def on_candle_processed(self, context) -> None:
                    # CRITICAL DEBUG
                    try:
                        with open('/tmp/dsl_debug.log', 'a') as f:
                            f.write(f"WRAPPER on_candle_processed called at {context.current_candle.timestamp}\n")
                    except:
                        pass
                    return self._dsl_strategy.on_candle_processed(context)
                
                def get_indicator_series(self, candles):
                    """Forward get_indicator_series to underlying DSL strategy."""
                    if hasattr(self._dsl_strategy, 'get_indicator_series'):
                        return self._dsl_strategy.get_indicator_series(candles)
                    return {}
                
                def get_execution_window_minutes(self) -> int:
                    """Forward get_execution_window_minutes to underlying DSL strategy."""
                    if hasattr(self._dsl_strategy, 'get_execution_window_minutes'):
                        return self._dsl_strategy.get_execution_window_minutes()
                    return 1440
                
                @property
                def is_indicator_based(self) -> bool:
                    """Expose the underlying DSL strategy's indicator-based flag."""
                    return getattr(self._dsl_strategy, 'is_indicator_based', False)
                
                @property
                def indicator_values(self) -> Dict[str, float]:
                    """Expose the underlying DSL strategy's indicator values."""
                    return getattr(self._dsl_strategy, 'indicator_values', {})
                
                @property
                def trailing_stop(self) -> Optional[Dict[str, Any]]:
                    """Expose the underlying DSL strategy's trailing stop configuration."""
                    return getattr(self._dsl_strategy, 'trailing_stop', None)
            
            return DSLStrategyWrapper
        
        # Register DSL strategy in the registry
        dsl_strategy_class = create_dsl_strategy_class(strategy_name)
        strategy_registry._strategies[strategy_name] = dsl_strategy_class
        
        # Add DSL strategy info
        dsl_info = dsl_loader.get_dsl_strategy_info(strategy_name)
        strategy_registry._strategy_info[strategy_name] = dsl_info
    
    # print(f"✅ Integrated {len(dsl_loader.get_dsl_strategy_names())} DSL strategies with StrategyRegistry")


# Global DSL loader instance
_global_dsl_loader = None

def get_dsl_loader() -> DSLLoader:
    """
    Get the global DSL loader instance.
    
    Returns:
        DSLLoader: Global DSL loader instance
    """
    global _global_dsl_loader
    if _global_dsl_loader is None:
        _global_dsl_loader = DSLLoader()
    return _global_dsl_loader


if __name__ == "__main__":
    # Test DSL loader
    loader = DSLLoader()
    loader.print_dsl_catalog()