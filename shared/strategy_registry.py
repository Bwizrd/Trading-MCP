#!/usr/bin/env python3
"""
Strategy Registry system for managing trading strategy cartridges.

This module handles strategy discovery, loading, and instantiation.
Strategies are treated as "cartridges" that plug into the universal backtest engine.
"""

from typing import Dict, Type, List, Any
from pathlib import Path
import importlib.util
import inspect
import sys
import os

from .strategy_interface import TradingStrategy

# NUCLEAR STDOUT SILENCING for MCP protocol compliance
class _NullPrint:
    """Silent print replacement to prevent stdout pollution in MCP servers."""
    def __call__(self, *args, **kwargs):
        pass

# Replace print globally in this module to prevent MCP protocol corruption
print = _NullPrint()

import os
import importlib
import inspect
from typing import Dict, List, Type, Any
from pathlib import Path

from shared.strategy_interface import TradingStrategy


class StrategyRegistry:
    """
    Registry for discovering and managing trading strategy implementations.
    
    This acts like a "game console" that can discover and load strategy "cartridges"
    from the strategies directory.
    """
    
    def __init__(self, strategies_directory: str = None):
        """
        Initialize the strategy registry.
        
        Args:
            strategies_directory: Directory to scan for strategy modules
        """
        if strategies_directory is None:
            # Default to shared/strategies directory
            current_dir = Path(__file__).parent
            strategies_directory = current_dir / "strategies"
        
        self.strategies_directory = Path(strategies_directory)
        self._strategies: Dict[str, Type[TradingStrategy]] = {}
        self._strategy_info: Dict[str, Dict[str, Any]] = {}
        
        # Auto-discover strategies on initialization
        self.discover_strategies()
        
        # Auto-discover and integrate DSL strategies
        self.integrate_dsl_strategies()
    
    def discover_strategies(self) -> None:
        """
        Discover all strategy implementations in the strategies directory.
        
        This scans Python files for classes that inherit from TradingStrategy.
        """
        if not self.strategies_directory.exists():
            print(f"Warning: Strategies directory does not exist: {self.strategies_directory}")
            return
        
        # Clear existing registrations
        self._strategies.clear()
        self._strategy_info.clear()
        
        # Scan Python files in strategies directory
        for py_file in self.strategies_directory.glob("*.py"):
            if py_file.name.startswith("__"):
                continue  # Skip __init__.py, __pycache__, etc.
            
            try:
                self._load_strategies_from_file(py_file)
            except Exception as e:
                print(f"Warning: Failed to load strategies from {py_file}: {e}")
    
    def _load_strategies_from_file(self, py_file: Path) -> None:
        """
        Load strategy classes from a Python file.
        
        Args:
            py_file: Path to the Python file to load
        """
        # Convert file path to module name
        module_name = f"shared.strategies.{py_file.stem}"
        
        try:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Find all TradingStrategy subclasses in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Check if it's a TradingStrategy subclass (but not the base class itself)
                if (issubclass(obj, TradingStrategy) and 
                    obj is not TradingStrategy and 
                    obj.__module__ == module_name):
                    
                    self._register_strategy(name, obj)
                    
        except ImportError as e:
            print(f"Warning: Could not import module {module_name}: {e}")
        except Exception as e:
            print(f"Warning: Error processing module {module_name}: {e}")
    
    def _register_strategy(self, class_name: str, strategy_class: Type[TradingStrategy]) -> None:
        """
        Register a strategy class in the registry.
        
        Args:
            class_name: Name of the strategy class
            strategy_class: The strategy class itself
        """
        # Create a temporary instance to get metadata
        try:
            temp_instance = strategy_class()
            strategy_name = temp_instance.get_name()
            
            # Store strategy class and metadata
            self._strategies[strategy_name] = strategy_class
            self._strategy_info[strategy_name] = {
                "class_name": class_name,
                "description": temp_instance.get_description(),
                "version": temp_instance.get_version(),
                "required_indicators": temp_instance.requires_indicators(),
                "default_parameters": temp_instance.get_default_parameters(),
                "module": strategy_class.__module__,
                "file": strategy_class.__module__.replace(".", "/") + ".py"
            }
            
            print(f"✅ Registered strategy: {strategy_name} (v{temp_instance.get_version()})")
            
        except Exception as e:
            print(f"Warning: Could not register strategy {class_name}: {e}")
    
    def get_strategy(self, name: str) -> Type[TradingStrategy]:
        """
        Get a strategy class by name.
        
        Args:
            name: Name of the strategy
            
        Returns:
            Strategy class
            
        Raises:
            KeyError: If strategy is not found
        """
        if name not in self._strategies:
            raise KeyError(f"Strategy '{name}' not found. Available strategies: {list(self._strategies.keys())}")
        
        return self._strategies[name]
    
    def create_strategy(self, name: str, parameters: Dict[str, Any] = None) -> TradingStrategy:
        """
        Create an instance of a strategy by name.
        
        Args:
            name: Name of the strategy
            parameters: Parameters to initialize the strategy with
            
        Returns:
            Initialized strategy instance
        """
        strategy_class = self.get_strategy(name)
        strategy = strategy_class()
        
        if parameters:
            strategy.initialize(parameters)
        else:
            strategy.initialize()
        
        return strategy
    
    def list_strategies(self) -> List[str]:
        """
        Get a list of all registered strategy names.
        
        Returns:
            List of strategy names
        """
        return list(self._strategies.keys())
    
    def get_strategy_info(self, name: str = None) -> Dict[str, Any]:
        """
        Get detailed information about a strategy or all strategies.
        
        Args:
            name: Name of specific strategy, or None for all strategies
            
        Returns:
            Strategy information dictionary
        """
        if name:
            if name not in self._strategy_info:
                raise KeyError(f"Strategy '{name}' not found")
            return self._strategy_info[name]
        else:
            return self._strategy_info.copy()
    
    def integrate_dsl_strategies(self) -> None:
        """
        Integrate DSL strategies with the registry.
        
        This makes DSL strategies appear alongside code-based strategies.
        """
        try:
            # Import DSL components (only if they exist)
            from shared.strategies.dsl_interpreter.dsl_loader import DSLLoader, integrate_dsl_with_strategy_registry
            
            # Create DSL loader and integrate
            dsl_loader = DSLLoader()
            integrate_dsl_with_strategy_registry(self, dsl_loader)
            
        except ImportError:
            # DSL system not available - continue without it
            pass
        except Exception as e:
            print(f"Warning: DSL integration failed: {e}")

    def print_strategy_catalog(self) -> None:
        """Print a formatted catalog of all available strategies."""
        print("\n" + "="*80)
        print("🎮 STRATEGY CARTRIDGE CATALOG")
        print("="*80)
        
        if not self._strategies:
            print("No strategies found. Make sure strategy files are in the strategies directory.")
            return
        
        # Separate code-based and DSL strategies
        code_strategies = {}
        dsl_strategies = {}
        
        for name, info in self._strategy_info.items():
            if info.get('dsl_strategy', False):
                dsl_strategies[name] = info
            else:
                code_strategies[name] = info
        
        # Print code-based strategies
        if code_strategies:
            print("\n📦 CODE-BASED STRATEGIES:")
            for name, info in code_strategies.items():
                print(f"\n   {name} (v{info['version']})")
                print(f"   📝 {info['description']}")
                print(f"   📊 Indicators: {', '.join(info['required_indicators']) if info['required_indicators'] else 'None'}")
                print(f"   ⚙️  Parameters: {len(info['default_parameters'])} available")
                print(f"   📁 File: {info['file']}")
        
        # Print DSL strategies
        if dsl_strategies:
            print(f"\n🤖 DSL STRATEGIES (JSON-Configured):")
            for name, info in dsl_strategies.items():
                print(f"\n   {name} (v{info['version']})")
                print(f"   � {info['description']}")
                if 'timing' in info:
                    print(f"   ⏰ Timing: {info['timing']['reference_time']} → {info['timing']['signal_time']}")
                if 'risk_management' in info:
                    rm = info['risk_management']
                    print(f"   🎯 Risk: {rm['stop_loss_pips']}SL / {rm['take_profit_pips']}TP")
                print(f"   📁 File: {info['file']}")
        
        total_code = len(code_strategies)
        total_dsl = len(dsl_strategies)
        print(f"\n💾 Total strategies: {total_code} code-based + {total_dsl} DSL = {len(self._strategies)} available")
        print("="*80)
    
    def reload_strategies(self) -> None:
        """
        Reload all strategies from the filesystem.
        
        This is useful during development when strategy files are modified.
        """
        print("🔄 Reloading strategy cartridges...")
        
        # Clear import cache for strategy modules
        modules_to_remove = []
        for module_name in list(importlib.sys.modules.keys()):
            if module_name.startswith("shared.strategies."):
                modules_to_remove.append(module_name)
        
        for module_name in modules_to_remove:
            del importlib.sys.modules[module_name]
        
        # Rediscover strategies
        self.discover_strategies()
        
        # Rediscover DSL strategies
        self.integrate_dsl_strategies()
        
        print(f"✅ Reloaded {len(self._strategies)} strategy cartridges")


# Global registry instance
_global_registry = None

def get_strategy_registry() -> StrategyRegistry:
    """
    Get the global strategy registry instance.
    
    Returns:
        Global StrategyRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = StrategyRegistry()
    return _global_registry

def register_strategy(name: str, strategy_class: Type[TradingStrategy]) -> None:
    """
    Register a strategy class manually.
    
    Args:
        name: Name for the strategy
        strategy_class: The strategy class to register
    """
    registry = get_strategy_registry()
    registry._register_strategy(name, strategy_class)

def create_strategy(name: str, parameters: Dict[str, Any] = None) -> TradingStrategy:
    """
    Create a strategy instance by name.
    
    Args:
        name: Name of the strategy
        parameters: Parameters to initialize with
        
    Returns:
        Initialized strategy instance
    """
    registry = get_strategy_registry()
    return registry.create_strategy(name, parameters)

def list_available_strategies() -> List[str]:
    """
    Get list of all available strategy names.
    
    Returns:
        List of strategy names
    """
    registry = get_strategy_registry()
    return registry.list_strategies()


if __name__ == "__main__":
    # Demo/test the registry
    registry = StrategyRegistry()
    registry.print_strategy_catalog()