#!/usr/bin/env python3
"""
DSL Strategy Interpreter

This package contains the Domain Specific Language (DSL) interpreter for trading strategies.
It allows AI tools to create trading strategies by generating JSON configurations instead of code.

CRITICAL: This is a modular component that EXTENDS the existing strategy cartridge system.
It does NOT replace existing VWAP strategies or break the modular architecture.
"""

__version__ = "1.0.0"

# Lazy imports to avoid circular dependencies
def get_dsl_strategy():
    from .dsl_strategy import DSLStrategy
    return DSLStrategy

def get_validator():
    from .schema_validator import validate_dsl_strategy
    return validate_dsl_strategy

def get_dsl_loader():
    from .dsl_loader import DSLLoader
    return DSLLoader

__all__ = ["get_dsl_strategy", "get_validator", "get_dsl_loader"]