#!/usr/bin/env python3
"""
Universal Backtest Engine

The "console" that can run any strategy "cartridge" that implements
the TradingStrategy interface.

Phase 1 of gradual migration - new backtest engine alongside existing implementations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging
import os
from pathlib import Path

from shared.models import Candle, Trade, TradeDirection, TradeResult
from shared.strategy_interface import (
    TradingStrategy, StrategyContext, BacktestConfiguration, 
    BacktestResults, SignalStrength
)
from shared.indicators import indicator_registry, IndicatorRegistry
from shared.data_connector import DataConnector
from shared.diagnostics import export_diagnostic_csv, is_diagnostics_enabled

# Configure logging
logger = logging.getLogger(__name__)

# Set up file handler if not already configured
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    
    # Try to create logs directory, but don't fail if we can't
    try:
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(log_dir / 'backtest_engine.log')
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add file handler
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        # If we can't create log file, just use console logging
        pass
    
    # Console handler (always add this)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class UniversalBacktestEngine:
    """
    Universal backtesting engine that can run any strategy.
    
    This is the "console" that accepts any strategy "cartridge" and runs
    standardized backtests with consistent results.
    """
    
    def __init__(self, data_connector=None):
        """
        Initialize the universal backtest engine.
        
        Args:
            data_connector: Data connector for fetching market data (optional for testing)
        """
        self.data_connector = data_connector
        self.indicator_registry = IndicatorRegistry()
    
    async def run_backtest(
        self,
        strategy: TradingStrategy,
        config: BacktestConfiguration,
        execution_timeframe: str = "1m"  # Default to 1-minute for precise execution
    ) -> BacktestResults:
        """
        Run backtest for any strategy using dual-timeframe approach.
        
        - Strategy signals generated on strategy timeframe (config.timeframe)
        - Trade execution simulated on execution timeframe (default 1m)
        
        Args:
            strategy: Strategy instance implementing TradingStrategy interface
            config: Backtest configuration parameters
            execution_timeframe: Timeframe for trade execution simulation (default "1m")
            
        Returns:
            BacktestResults: Standardized results object
        """
        start_time = datetime.now()
        
        try:
            # 1. Validate inputs
            self._validate_inputs(strategy, config)
            
            # 2. Initialize strategy
            if not strategy.is_initialized():
                strategy.initialize()
            
            # 3. Fetch market data for strategy signals (higher timeframe)
            logger.info(f"Fetching strategy data for {config.symbol} {config.timeframe} from {config.start_date} to {config.end_date}")
            strategy_data = await self._fetch_market_data(config)
            
            if not strategy_data.data or len(strategy_data.data) == 0:
                raise ValueError(f"No strategy data available for {config.symbol} in specified period")
            
            # Use the Candle objects directly (no conversion needed)
            strategy_candles = strategy_data.data
            strategy_candles.sort(key=lambda c: c.timestamp)  # Ensure chronological order
            
            # If using tick data (indicated by having many 1-second candles from VPS or InfluxDB),
            # use dual-timeframe approach:
            # - Strategy candles (1m): For indicator calculation and signal generation
            # - Execution candles (ticks): For precise trade execution and SL/TP tracking
            is_tick_data_mode = ("tick" in strategy_data.source.lower()) and len(strategy_candles) > 1000
            execution_candles = None
            
            if is_tick_data_mode:
                logger.info(f"🎯 TICK DATA MODE: Dual-timeframe execution")
                logger.info(f"   - Strategy: {len(strategy_candles)} 1s tick candles → resampling to {config.timeframe}")
                execution_candles = strategy_candles  # Keep ticks for precise execution
                strategy_candles = self._resample_candles_for_indicators(strategy_candles, config.timeframe)
                logger.info(f"   - Signals: {len(strategy_candles)} {config.timeframe} candles (tick-accurate OHLC)")
                logger.info(f"   - Execution: {len(execution_candles)} 1-second tick candles (precise SL/TP)")
            else:
                logger.info(f"Using signal-driven architecture - execution data will be fetched on-demand for each signal")
            
            # 5. Calculate required indicators on strategy candles (1m if tick mode)
            required_indicators = strategy.requires_indicators()
            logger.info(f"Calculating indicators: {required_indicators}")
            indicators_data = self._calculate_indicators(strategy_candles, required_indicators)
            logger.info(f"Calculated {len(indicators_data)} indicators: {list(indicators_data.keys())}")
            
            # 6. Run simulation (dual-timeframe if using ticks)
            # Note: is_tick_data=False because strategy_candles are already resampled to timeframe
            # execution_candles contain ticks for precise SL/TP when is_tick_data_mode=True
            logger.info("Running trading simulation...")
            trades = await self._run_dual_timeframe_simulation(
                strategy, strategy_candles, execution_candles, indicators_data, config, is_tick_data=False
            )
            
            # 6. Calculate performance statistics
            logger.info("Calculating performance statistics...")
            stats = self._calculate_performance_stats(trades, config.initial_balance)
            
            # 7. Create results object
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Convert indicators from Dict[str, Dict[datetime, float]] to Dict[str, List[float]]
            # for chart generation
            indicators_for_chart = {}
            if indicators_data:
                for indicator_name, indicator_dict in indicators_data.items():
                    # Create a list aligned with strategy_candles timestamps
                    indicator_list = []
                    for candle in strategy_candles:
                        value = indicator_dict.get(candle.timestamp, 0.0)
                        indicator_list.append(value)
                    indicators_for_chart[indicator_name.lower()] = indicator_list
                    
                    # Special handling for MACD - extract signal line and histogram
                    if indicator_name.upper() == "MACD":
                        # Get the calculator instance to access signal line and histogram
                        calculator = self.indicator_registry._calculators.get(indicator_name)
                        if calculator and hasattr(calculator, 'get_signal_line'):
                            signal_line = calculator.get_signal_line()
                            histogram = calculator.get_histogram()
                            
                            # Convert to lists aligned with candles
                            signal_list = []
                            histogram_list = []
                            for candle in strategy_candles:
                                signal_list.append(signal_line.get(candle.timestamp, 0.0))
                                histogram_list.append(histogram.get(candle.timestamp, 0.0))
                            
                            indicators_for_chart['macd_signal'] = signal_list
                            indicators_for_chart['macd_histogram'] = histogram_list
                            logger.info(f"Extracted MACD signal line and histogram")
                
                logger.info(f"Prepared {len(indicators_for_chart)} indicators for chart generation")
            
            # For DSL strategies with get_indicator_series, extract their indicators
            if hasattr(strategy, 'get_indicator_series'):
                try:
                    logger.info("Extracting indicators from DSL strategy...")
                    dsl_indicators = strategy.get_indicator_series(strategy_candles)
                    if dsl_indicators:
                        # Merge DSL indicators with existing indicators
                        indicators_for_chart.update(dsl_indicators)
                        logger.info(f"Added {len(dsl_indicators)} DSL indicators: {list(dsl_indicators.keys())}")
                except Exception as e:
                    logger.warning(f"Failed to extract DSL indicators: {e}")
            
            results = BacktestResults(
                strategy_name=strategy.get_name(),
                strategy_version=strategy.get_version(),
                configuration=config,
                trades=trades,
                total_trades=len(trades),
                winning_trades=len([t for t in trades if t.result == TradeResult.WIN]),
                losing_trades=len([t for t in trades if t.result == TradeResult.LOSS]),
                total_pips=stats['total_pips'],
                win_rate=stats['win_rate'],
                profit_factor=stats['profit_factor'],
                average_win=stats['average_win'],
                average_loss=stats['average_loss'],
                largest_win=stats['largest_win'],
                largest_loss=stats['largest_loss'],
                max_drawdown=stats['max_drawdown'],
                max_consecutive_losses=stats['max_consecutive_losses'],
                max_consecutive_wins=stats['max_consecutive_wins'],
                start_time=start_time,
                end_time=end_time,
                execution_time_seconds=execution_time,
                data_source=f"{strategy_data.source} ({'cached' if hasattr(strategy_data, 'cached') and strategy_data.cached else 'fresh'})",
                total_candles_processed=len(strategy_candles),
                market_data=strategy_candles,  # Include market data for chart generation
                indicators=indicators_for_chart,  # Include indicators for chart generation
                diagnostic_csv_path=None  # Will be set if diagnostics enabled
            )
            
            # Export diagnostic CSV if enabled
            if is_diagnostics_enabled():
                logger.info("Diagnostics enabled - exporting detailed CSV...")
                try:
                    # Extract trend filter data if available from DSL strategy
                    trend_filter_data = None
                    
                    # Unwrap DSLStrategyWrapper to get actual DSLStrategy instance
                    actual_strategy = strategy
                    if hasattr(strategy, '_dsl_strategy'):
                        actual_strategy = strategy._dsl_strategy
                        logger.info("Unwrapped DSLStrategyWrapper to access inner DSLStrategy")
                    
                    # Debug: Check strategy attributes
                    logger.info(f"DEBUG: Strategy type: {type(actual_strategy)}")
                    logger.info(f"DEBUG: Has candle_history: {hasattr(actual_strategy, 'candle_history')}")
                    logger.info(f"DEBUG: Has _calculate_trend_strength: {hasattr(actual_strategy, '_calculate_trend_strength')}")
                    logger.info(f"DEBUG: Has min_trend_range_pips: {hasattr(actual_strategy, 'min_trend_range_pips')}")
                    if hasattr(actual_strategy, 'min_trend_range_pips'):
                        logger.info(f"DEBUG: min_trend_range_pips value: {actual_strategy.min_trend_range_pips}")
                    
                    if (hasattr(actual_strategy, 'candle_history') and 
                        hasattr(actual_strategy, '_calculate_trend_strength') and 
                        hasattr(actual_strategy, 'min_trend_range_pips') and
                        actual_strategy.min_trend_range_pips > 0):
                        # Calculate trend filter for each candle point in history
                        logger.info(f"Calculating trend filter data (min_trend_range_pips={actual_strategy.min_trend_range_pips})...")
                        logger.info(f"DEBUG: Starting trend filter calculation for {len(strategy_candles)} candles...")
                        trend_filter_data = {}
                        # Rebuild candle history progressively to get trend strength at each point
                        for i, candle in enumerate(strategy_candles):
                            # Set the strategy's candle history to this point in time
                            actual_strategy.candle_history = strategy_candles[:i+1]
                            # Calculate trend strength at this point
                            trend_strength = actual_strategy._calculate_trend_strength()
                            if trend_strength:
                                trend_filter_data[candle.timestamp] = trend_strength['range']
                        # Restore full candle history
                        actual_strategy.candle_history = strategy_candles
                        logger.info(f"Calculated trend filter for {len(trend_filter_data)} candles")
                        logger.info(f"DEBUG: Trend filter data calculated for {len(trend_filter_data)} candles")
                    else:
                        logger.info(f"DEBUG: Trend filter calculation skipped - conditions not met")
                    
                    csv_path = export_diagnostic_csv(
                        candles=strategy_candles,
                        trades=trades,
                        indicator_series=indicators_for_chart,
                        trend_filter_data=trend_filter_data,
                        strategy_name=strategy.get_name(),
                        symbol=config.symbol
                    )
                    if csv_path:
                        results.diagnostic_csv_path = csv_path
                        logger.info(f"📊 Diagnostic CSV: {csv_path}")
                except Exception as e:
                    logger.error(f"Failed to export diagnostic CSV: {e}", exc_info=True)
            
            logger.info(f"Backtest completed: {results.total_trades} trades, {results.win_rate:.1%} win rate, {results.total_pips:+.1f} pips")
            return results
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}", exc_info=True)
            raise
    
    def _validate_inputs(self, strategy: TradingStrategy, config: BacktestConfiguration):
        """Validate strategy and configuration."""
        if not isinstance(strategy, TradingStrategy):
            raise ValueError("Strategy must implement TradingStrategy interface")
        
        # Validate required indicators are available
        required_indicators = strategy.requires_indicators()
        available_indicators = self.indicator_registry.list_available()
        
        missing_indicators = [ind for ind in required_indicators if ind not in available_indicators]
        if missing_indicators:
            raise ValueError(f"Required indicators not available: {missing_indicators}. Available: {available_indicators}")
    
    async def _fetch_market_data(self, config: BacktestConfiguration) -> Any:
        """Fetch market data for the backtest period."""
        if not self.data_connector:
            raise ValueError("Data connector not available for fetching market data")
        
        try:
            # Convert string dates to datetime objects if needed
            start_date = config.start_date
            end_date = config.end_date
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Use the enhanced data connector to fetch data
            response = await self.data_connector.get_market_data(
                symbol=config.symbol,
                timeframe=config.timeframe,
                start_date=start_date,
                end_date=end_date,
                use_tick_data=getattr(config, 'use_tick_data', False)
            )
            
            logger.info(f"Fetched {len(response.data)} candles from {response.source}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            raise
    
    def _calculate_indicators(self, candles: List[Candle], required_indicators: List[str]) -> Dict[str, Dict[datetime, float]]:
        """Calculate technical indicators for the given candles."""
        if not required_indicators:
            return {}
        
        try:
            # Use the indicator registry to calculate required indicators
            return self.indicator_registry.calculate_indicators(candles, required_indicators)
            
        except Exception as e:
            logger.error(f"Failed to calculate indicators: {e}")
            raise
    
    def _resample_candles_for_indicators(self, candles: List[Candle], target_timeframe: str) -> List[Candle]:
        """
        Resample 1-second candles to target timeframe for indicator calculation.
        This preserves tick-level data for execution while aggregating for proper indicator calculation.
        """
        import pandas as pd
        
        try:
            # Parse timeframe to pandas frequency
            timeframe_map = {
                '1m': '1T', '5m': '5T', '15m': '15T', '30m': '30T',
                '1h': '1H', '4h': '4H', '1d': '1D'
            }
            
            freq = timeframe_map.get(target_timeframe.lower(), '1T')
            
            # Convert candles to DataFrame
            df = pd.DataFrame([{
                'timestamp': c.timestamp,
                'open': c.open,
                'high': c.high,
                'low': c.low,
                'close': c.close,
                'volume': c.volume
            } for c in candles])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Resample to target timeframe
            resampled = df.resample(freq).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            # Convert back to Candle objects
            resampled_candles = []
            for timestamp, row in resampled.iterrows():
                candle = Candle(
                    timestamp=timestamp.to_pydatetime(),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume'])
                )
                resampled_candles.append(candle)
            
            return resampled_candles
            
        except Exception as e:
            logger.error(f"Failed to resample candles: {e}", exc_info=True)
            return candles  # Return original candles if resampling fails
    
    def _map_indicators_to_tick_candles(self, indicators_data: Dict[str, Dict[datetime, float]], 
                                       tick_candles: List[Candle], timeframe: str) -> Dict[str, Dict[datetime, float]]:
        """
        Map minute-level indicator values to all 1-second candles within each minute.
        Each 1-second candle gets the indicator value from its parent minute candle.
        """
        import pandas as pd
        
        try:
            # Parse timeframe to determine grouping period
            timeframe_map = {
                '1m': '1T', '5m': '5T', '15m': '15T', '30m': '30T',
                '1h': '1H', '4h': '4H', '1d': '1D'
            }
            
            freq = timeframe_map.get(timeframe.lower(), '1T')
            
            mapped_indicators = {}
            
            for indicator_name, indicator_values in indicators_data.items():
                mapped_values = {}
                
                # For each 1-second candle, find its parent minute candle's indicator value
                for candle in tick_candles:
                    # Floor the timestamp to the minute boundary
                    minute_timestamp = pd.Timestamp(candle.timestamp).floor(freq).to_pydatetime()
                    
                    # Get the indicator value from the minute candle
                    if minute_timestamp in indicator_values:
                        mapped_values[candle.timestamp] = indicator_values[minute_timestamp]
                
                mapped_indicators[indicator_name] = mapped_values
            
            logger.info(f"Mapped {len(mapped_indicators)} indicators to {len(tick_candles)} tick candles")
            return mapped_indicators
            
        except Exception as e:
            logger.error(f"Failed to map indicators to tick candles: {e}", exc_info=True)
            return indicators_data  # Return original indicators if mapping fails
    
    def _convert_dataframe_to_candles(self, df) -> List[Candle]:
        """Convert pandas DataFrame to list of Candle objects."""
        import pandas as pd
        
        candles = []
        for _, row in df.iterrows():
            candle = Candle(
                timestamp=pd.to_datetime(row['timestamp']).to_pydatetime(),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']) if pd.notna(row['volume']) else 0
            )
            candles.append(candle)
        
        return candles
    
    async def _run_simulation(
        self,
        strategy: TradingStrategy,
        candles: List[Candle],
        indicators_data: Dict[str, Dict[datetime, float]],
        config: BacktestConfiguration
    ) -> List[Trade]:
        """
        Run the trading simulation using the strategy.
        """
        trades = []
        open_trade = None
        historical_candles = []
        
        # CRITICAL FIX: Sort candles in chronological order (oldest first)
        # The data connector returns candles in reverse order, but strategies
        # expect forward chronological processing for correct signal generation
        sorted_candles = sorted(candles, key=lambda c: c.timestamp)
        
        for i, candle in enumerate(sorted_candles):
            # Build historical context (all previous candles)
            historical_candles.append(candle)
            
            # Get indicators for this timestamp
            current_indicators = {}
            for indicator_name, indicator_values in indicators_data.items():
                if candle.timestamp in indicator_values:
                    current_indicators[indicator_name] = indicator_values[candle.timestamp]
            
            # Create strategy context
            context = StrategyContext(
                current_candle=candle,
                historical_candles=historical_candles.copy(),
                indicators=current_indicators,
                current_position=open_trade,
                symbol=config.symbol,
                timeframe=config.timeframe
            )
            
            # Let strategy process the candle
            strategy.on_candle_processed(context)
            
            # Check for exit conditions first (if we have an open trade)
            if open_trade:
                exit_result = self._check_exit_conditions(open_trade, candle, config)
                if exit_result:
                    open_trade.exit_price = exit_result['price']
                    open_trade.exit_time = candle.timestamp
                    open_trade.result = exit_result['result']
                    open_trade.pips = self._calculate_pips(
                        open_trade.entry_price, 
                        open_trade.exit_price, 
                        open_trade.direction,
                        config.symbol
                    )
                    
                    # Notify strategy
                    strategy.on_trade_closed(open_trade, context)
                    
                    trades.append(open_trade)
                    open_trade = None
            
            # Generate new signal (only if no open position)
            if not open_trade and config.max_open_trades > len([t for t in trades if t.result is None]):
                signal = strategy.generate_signal(context)
                
                if signal:
                    logger.info(f"Signal generated: {signal.direction.name} @ {candle.timestamp} - Price: {signal.price:.5f}")
                    
                    # Check if trailing stop is enabled
                    trailing_config = getattr(config, 'trailing_stop', None)
                    trailing_enabled = trailing_config and trailing_config.get('enabled', False)
                    
                    # If trailing stop enabled, set TP to infinity so it never hits
                    tp_value = float('inf') if trailing_enabled else self._calculate_take_profit(signal.price, signal.direction, config.take_profit_pips, config.symbol)
                    
                    # Create new trade
                    open_trade = Trade(
                        entry_time=candle.timestamp,
                        direction=signal.direction,
                        entry_price=signal.price,
                        stop_loss=self._calculate_stop_loss(signal.price, signal.direction, config.stop_loss_pips, config.symbol),
                        take_profit=tp_value,
                        result=None  # Will be set when trade closes
                    )
                    
                    logger.info(f"Trade opened: {open_trade.direction.name} @ {open_trade.entry_price:.5f} (SL: {open_trade.stop_loss:.5f}, TP: {open_trade.take_profit:.5f})")
                    
                    # Notify strategy
                    strategy.on_trade_opened(open_trade, context)
        
        # Close any remaining open trade at the end
        if open_trade:
            last_candle = candles[-1]
            open_trade.exit_price = last_candle.close
            open_trade.exit_time = last_candle.timestamp
            open_trade.result = TradeResult.EOD_CLOSE
            open_trade.pips = self._calculate_pips(
                open_trade.entry_price,
                open_trade.exit_price,
                open_trade.direction,
                config.symbol
            )
            trades.append(open_trade)
        
        return trades
    
    async def _run_dual_timeframe_simulation(
        self,
        strategy: TradingStrategy,
        strategy_candles: List[Candle],
        execution_candles: Optional[List[Candle]],
        indicators_data: Dict[str, Dict[datetime, float]],
        config: BacktestConfiguration,
        is_tick_data: bool = False
    ) -> List[Trade]:
        """
        Run dual-timeframe simulation with signal-driven execution data fetching:
        - Generate signals on strategy timeframe (strategy_candles)
        - Fetch minimal 1m data on-demand for each signal
        - Execute trades with precise entry/exit timing
        
        If execution_candles is provided, falls back to legacy bulk processing.
        """
        if execution_candles is not None:
            # Legacy mode: use pre-fetched execution data
            return await self._run_legacy_dual_timeframe_simulation(
                strategy, strategy_candles, execution_candles, indicators_data, config, is_tick_data
            )
        
        # New optimized mode: signal-driven execution data fetching
        return await self._run_signal_driven_simulation(strategy, strategy_candles, indicators_data, config, is_tick_data)
    
    async def _run_legacy_dual_timeframe_simulation(
        self,
        strategy: TradingStrategy,
        strategy_candles: List[Candle],
        execution_candles: List[Candle],
        indicators_data: Dict[str, Dict[datetime, float]],
        config: BacktestConfiguration,
        is_tick_data: bool = False
    ) -> List[Trade]:
        """Legacy dual-timeframe simulation using pre-fetched execution data."""
        trades = []
        open_trade = None
        pending_signals = []  # Signals waiting for execution
        
        logger.info(f"Running legacy dual-timeframe simulation: {len(strategy_candles)} strategy candles, {len(execution_candles)} execution candles (tick_data={is_tick_data})")
        
        # Process strategy candles to generate signals
        historical_candles = []
        strategy_signals = []
        
        for i, candle in enumerate(strategy_candles):
            historical_candles.append(candle)
            
            # Get indicators for this timestamp
            current_indicators = {}
            for indicator_name, indicator_values in indicators_data.items():
                if candle.timestamp in indicator_values:
                    current_indicators[indicator_name] = indicator_values[candle.timestamp]
            
            # Create strategy context
            context = StrategyContext(
                current_candle=candle,
                historical_candles=historical_candles.copy(),
                indicators=current_indicators,
                current_position=open_trade,
                symbol=config.symbol,
                timeframe=config.timeframe
            )
            
            # Let strategy process the candle
            strategy.on_candle_processed(context)
            
            # CRITICAL: When using tick data, only evaluate signals at minute boundaries
            # This is because indicators are calculated on minute data and forward-filled to seconds
            # Crossover detection requires value changes, which only happen at minute boundaries
            should_evaluate_signal = True
            if is_tick_data:
                # Only evaluate at minute boundaries (seconds == 0)
                should_evaluate_signal = candle.timestamp.second == 0
                if should_evaluate_signal and i % 100 == 0:  # Log every 100th evaluation
                    logger.debug(f"Evaluating signal at minute boundary: {candle.timestamp}")
            
            # Generate signal if no open position
            if not open_trade and should_evaluate_signal:
                signal = strategy.generate_signal(context)
                if signal:
                    strategy_signals.append({
                        'timestamp': candle.timestamp,
                        'signal': signal,
                        'context': context
                    })
                    logger.info(f"Strategy signal generated: {signal.direction.name} @ {candle.timestamp}")
        
        # Now process execution candles with generated signals
        current_signal_index = 0
        
        for exec_candle in execution_candles:
            # Check if we have a pending signal for this time period
            if current_signal_index < len(strategy_signals):
                signal_data = strategy_signals[current_signal_index]
                
                # Execute signal if execution candle is after signal timestamp
                if exec_candle.timestamp >= signal_data['timestamp'] and not open_trade:
                    signal = signal_data['signal']
                    context = signal_data['context']
                    
                    # Check if trailing stop is enabled
                    trailing_config = getattr(config, 'trailing_stop', None)
                    trailing_enabled = trailing_config and trailing_config.get('enabled', False)
                    
                    # If trailing stop enabled, set TP to infinity so it never hits
                    tp_value = float('inf') if trailing_enabled else self._calculate_take_profit(exec_candle.open, signal.direction, config.take_profit_pips, config.symbol)
                    
                    # Create new trade with precise execution price
                    open_trade = Trade(
                        entry_time=exec_candle.timestamp,
                        direction=signal.direction,
                        entry_price=exec_candle.open,  # Use execution candle open price
                        stop_loss=self._calculate_stop_loss(exec_candle.open, signal.direction, config.stop_loss_pips, config.symbol),
                        take_profit=tp_value,
                        result=None
                    )
                    
                    logger.info(f"Trade opened: {open_trade.direction.name} @ {open_trade.entry_price:.5f} (execution @ {exec_candle.timestamp})")
                    strategy.on_trade_opened(open_trade, context)
                    current_signal_index += 1
            
            # Check for exit conditions with precise 1-minute data
            if open_trade:
                exit_result = self._check_exit_conditions_precise(open_trade, exec_candle, config)
                if exit_result:
                    open_trade.exit_price = exit_result['price']
                    open_trade.exit_time = exec_candle.timestamp
                    open_trade.result = exit_result['result']
                    open_trade.pips = self._calculate_pips(
                        open_trade.entry_price,
                        open_trade.exit_price,
                        open_trade.direction,
                        config.symbol
                    )
                    
                    # Find matching strategy context for trade close notification
                    strategy_context = StrategyContext(
                        current_candle=exec_candle,
                        historical_candles=[exec_candle],
                        indicators={},
                        current_position=open_trade,
                        symbol=config.symbol,
                        timeframe="1m"
                    )
                    strategy.on_trade_closed(open_trade, strategy_context)
                    
                    trades.append(open_trade)
                    logger.info(f"Trade closed: {open_trade.direction.name} @ {open_trade.exit_price:.5f} = {open_trade.pips:+.1f} pips ({open_trade.result.name})")
                    open_trade = None
        
        # Close any remaining open trade
        if open_trade:
            last_candle = execution_candles[-1]
            open_trade.exit_price = last_candle.close
            open_trade.exit_time = last_candle.timestamp
            open_trade.result = TradeResult.EOD_CLOSE
            open_trade.pips = self._calculate_pips(
                open_trade.entry_price,
                open_trade.exit_price,
                open_trade.direction,
                config.symbol
            )
            trades.append(open_trade)
        
        return trades
    
    async def _run_signal_driven_simulation(
        self,
        strategy: TradingStrategy,
        strategy_candles: List[Candle],
        indicators_data: Dict[str, Dict[datetime, float]],
        config: BacktestConfiguration,
        is_tick_data: bool = False
    ) -> List[Trade]:
        """
        Signal-driven simulation that fetches minimal 1m data on-demand.
        
        Instead of fetching all 1m data upfront (10,080 bars for a week),
        this method:
        1. Generates signals on strategy timeframe
        2. For each signal, fetches only ~5-15 minutes of 1m data
        3. Executes trades with precise timing
        
        This reduces data usage by ~96% while maintaining full precision.
        
        CRITICAL: Tracks active trades to prevent overlapping positions.
        """
        trades = []
        active_trades = []  # Track all trades that haven't closed yet
        historical_candles = []
        
        logger.info(f"Running signal-driven simulation: {len(strategy_candles)} strategy candles (tick_data={is_tick_data})")
        
        # Process strategy candles to generate signals
        for i, candle in enumerate(strategy_candles):
            historical_candles.append(candle)
            
            # Get indicators for this timestamp
            current_indicators = {}
            for indicator_name, indicator_values in indicators_data.items():
                if candle.timestamp in indicator_values:
                    current_indicators[indicator_name] = indicator_values[candle.timestamp]
            
            # Check if any active trades should be closed by this candle's timestamp
            # (trades that have exit_time <= current candle timestamp)
            still_active = []
            for trade in active_trades:
                if trade.exit_time and trade.exit_time <= candle.timestamp:
                    # Trade has closed before or at this candle
                    logger.debug(f"Trade closed: {trade.direction.name} @ {trade.exit_time} (before current candle @ {candle.timestamp})")
                else:
                    # Trade is still active
                    still_active.append(trade)
            active_trades = still_active
            
            # Determine current position (first active trade, or None)
            current_position = active_trades[0] if active_trades else None
            
            # Create strategy context with current position
            context = StrategyContext(
                current_candle=candle,
                historical_candles=historical_candles.copy(),
                indicators=current_indicators,
                current_position=current_position,
                symbol=config.symbol,
                timeframe=config.timeframe
            )
            
            # Let strategy process the candle
            strategy.on_candle_processed(context)
            
            # CRITICAL: When using tick data, only evaluate signals at minute boundaries
            # This is because indicators are calculated on minute data and forward-filled to seconds
            # Crossover detection requires value changes, which only happen at minute boundaries
            should_evaluate_signal = True
            if is_tick_data:
                # Only evaluate at minute boundaries (seconds == 0)
                should_evaluate_signal = candle.timestamp.second == 0
                if should_evaluate_signal and i % 100 == 0:  # Log every 100th evaluation
                    logger.debug(f"Evaluating signal at minute boundary: {candle.timestamp}")
            
            # Generate signal only if no active position and at minute boundary (for tick data)
            if not current_position and should_evaluate_signal:
                signal = strategy.generate_signal(context)
                if signal:
                    logger.info(f"Signal generated: {signal.direction.name} @ {candle.timestamp}")
                    
                    # DEBUG: Write to file
                    with open('/tmp/backtest_debug.log', 'a') as f:
                        f.write(f"BACKTEST ENGINE: Signal received {signal.direction} @ {candle.timestamp}\n")
                    
                    # Get execution window duration from strategy
                    window_minutes = strategy.get_execution_window_minutes() if hasattr(strategy, 'get_execution_window_minutes') else 1440
                    
                    # Fetch execution window (small amount of 1m data around signal)
                    execution_window = await self._fetch_execution_window(
                        config.symbol, candle.timestamp, config, window_minutes=window_minutes
                    )
                    
                    # DEBUG: Write to file
                    with open('/tmp/backtest_debug.log', 'a') as f:
                        f.write(f"BACKTEST ENGINE: Execution window fetched: {len(execution_window) if execution_window else 0} candles\n")
                    
                    if execution_window:
                        # Execute trade with precise timing
                        trade_result = await self._execute_trade_with_window(
                            signal, execution_window, strategy, context, config
                        )
                        
                        # DEBUG: Write to file
                        with open('/tmp/backtest_debug.log', 'a') as f:
                            f.write(f"BACKTEST ENGINE: Trade result: {trade_result}\n")
                        
                        if trade_result:
                            trades.append(trade_result)
                            active_trades.append(trade_result)  # Add to active trades
                            logger.info(f"Trade completed: {trade_result.direction.name} @ {trade_result.entry_price:.5f} -> {trade_result.exit_price:.5f} = {trade_result.pips:+.1f} pips (entry: {trade_result.entry_time}, exit: {trade_result.exit_time})")
                    else:
                        logger.warning(f"No execution data available for signal @ {candle.timestamp}")
            elif current_position:
                logger.debug(f"Skipping signal generation @ {candle.timestamp} - active position exists (entry: {current_position.entry_time}, direction: {current_position.direction.name})")
        
        # Close any remaining active trades at end of period
        for open_trade in active_trades:
            if not open_trade.exit_time:
                last_candle = strategy_candles[-1]
                open_trade.exit_price = last_candle.close
                open_trade.exit_time = last_candle.timestamp
                open_trade.result = TradeResult.EOD_CLOSE
                open_trade.pips = self._calculate_pips(
                    open_trade.entry_price,
                    open_trade.exit_price,
                    open_trade.direction,
                    config.symbol
                )
                logger.info(f"Trade closed at end: {open_trade.direction.name} @ {open_trade.exit_price:.5f} = {open_trade.pips:+.1f} pips")
        
        return trades
    
    async def _fetch_execution_window(
        self,
        symbol: str,
        signal_time: datetime,
        config: BacktestConfiguration,
        window_minutes: int
    ) -> Optional[List[Candle]]:
        """
        Fetch a small window of 1-minute data around a signal using optimized data connector.
        
        Args:
            symbol: Trading symbol
            signal_time: When the signal was generated
            config: Backtest configuration
            window_minutes: Minutes of 1m data to fetch (default: 15)
            
        Returns:
            List of 1-minute candles or None if unavailable
        """
        try:
            logger.debug(f"Fetching execution window for {symbol} @ {signal_time}")
            
            # Use the optimized execution window method
            response = await self.data_connector.get_execution_window(
                symbol=symbol,
                signal_time=signal_time,
                window_minutes=window_minutes,
                pre_minutes=2
            )
            
            if response.data:
                # Sort chronologically
                candles = sorted(response.data, key=lambda c: c.timestamp)
                logger.debug(f"Fetched {len(candles)} execution candles for window ({response.source})")
                return candles
            else:
                logger.warning(f"No execution data returned from {response.source}")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch execution window: {e}")
            return None
    
    async def _execute_trade_with_window(
        self,
        signal,
        execution_candles: List[Candle],
        strategy: TradingStrategy,
        signal_context: StrategyContext,
        config: BacktestConfiguration
    ) -> Optional[Trade]:
        """
        Execute a trade using a small window of 1-minute data.
        
        CRITICAL FIX: To avoid OHLC ambiguity with trailing stops, we:
        1. Update trailing stop based on PREVIOUS candle
        2. Check exit conditions on CURRENT candle
        This ensures we never use the same candle to both update and trigger the stop.
        
        Args:
            signal: The trading signal to execute
            execution_candles: Small window of 1m candles
            strategy: Strategy instance
            signal_context: Context when signal was generated
            config: Backtest configuration
            
        Returns:
            Completed Trade or None if execution failed
        """
        if not execution_candles:
            return None
        
        # Find the first candle at or after signal time for entry
        entry_candle = None
        for candle in execution_candles:
            if candle.timestamp >= signal_context.current_candle.timestamp:
                entry_candle = candle
                break
        
        if not entry_candle:
            logger.warning("No suitable entry candle found in execution window")
            return None
        
        # Check if trailing stop is enabled
        trailing_config = getattr(config, 'trailing_stop', None)
        trailing_enabled = trailing_config and trailing_config.get('enabled', False)
        
        # If trailing stop enabled, set TP to infinity so it never hits
        tp_value = float('inf') if trailing_enabled else self._calculate_take_profit(entry_candle.open, signal.direction, config.take_profit_pips, config.symbol)
        
        # Create trade with precise entry
        trade = Trade(
            entry_time=entry_candle.timestamp,
            direction=signal.direction,
            entry_price=entry_candle.open,  # Enter at candle open
            stop_loss=self._calculate_stop_loss(entry_candle.open, signal.direction, config.stop_loss_pips, config.symbol),
            take_profit=tp_value,
            result=None
        )
        
        logger.info(f"Trade opened: {trade.direction.name} @ {trade.entry_price:.5f} (SL: {trade.stop_loss:.5f}, TP: {trade.take_profit:.5f})")
        strategy.on_trade_opened(trade, signal_context)
        
        # Process remaining candles for exit conditions
        # CRITICAL: Use previous candle to update trailing stop, current candle to check exit
        previous_candle = entry_candle
        
        for i, candle in enumerate(execution_candles):
            if candle.timestamp > entry_candle.timestamp:
                # Update trailing stop based on PREVIOUS candle (not current)
                if trailing_enabled and previous_candle:
                    self._update_trailing_stop(trade, previous_candle, trailing_config, config.symbol)
                
                # Now check if CURRENT candle hits the stop
                exit_result = self._check_exit_conditions_simple(trade, candle, config, trailing_enabled)
                if exit_result:
                    trade.exit_price = exit_result['price']
                    trade.exit_time = candle.timestamp
                    trade.result = exit_result['result']
                    trade.pips = self._calculate_pips(
                        trade.entry_price,
                        trade.exit_price,
                        trade.direction,
                        config.symbol
                    )
                    
                    # Notify strategy
                    exit_context = StrategyContext(
                        current_candle=candle,
                        historical_candles=[candle],
                        indicators={},
                        current_position=trade,
                        symbol=config.symbol,
                        timeframe="1m"
                    )
                    strategy.on_trade_closed(trade, exit_context)
                    
                    return trade
                
                # Move to next candle
                previous_candle = candle
        
        # If no exit condition met in window, close at last candle
        last_candle = execution_candles[-1]
        trade.exit_price = last_candle.close
        trade.exit_time = last_candle.timestamp
        trade.result = TradeResult.EOD_CLOSE
        trade.pips = self._calculate_pips(
            trade.entry_price,
            trade.exit_price,
            trade.direction,
            config.symbol
        )
        
        return trade
    
    def _check_exit_conditions_simple(self, trade: Trade, candle: Candle, config: BacktestConfiguration, trailing_enabled: bool) -> Optional[Dict[str, Any]]:
        """
        Simple exit check that doesn't update trailing stop.
        Trailing stop should be updated BEFORE calling this method using previous candle.
        
        This separation ensures we never use the same candle to both update and trigger the stop.
        """
        # Use trailing stop level if active, otherwise use fixed stop loss
        active_stop_loss = trade.trailing_stop_level if trade.trailing_stop_level else trade.stop_loss
        
        if trade.direction == TradeDirection.BUY:
            # Check stop loss hit during this minute
            if candle.low <= active_stop_loss:
                return {
                    'price': active_stop_loss,
                    'result': TradeResult.LOSS if trade.entry_price > active_stop_loss else TradeResult.WIN
                }
            # Check take profit hit during this minute ONLY if trailing stop is NOT enabled
            if not trailing_enabled and candle.high >= trade.take_profit:
                return {
                    'price': trade.take_profit,
                    'result': TradeResult.WIN
                }
        else:  # SELL
            # Check stop loss hit during this minute
            if candle.high >= active_stop_loss:
                return {
                    'price': active_stop_loss,
                    'result': TradeResult.LOSS if trade.entry_price < active_stop_loss else TradeResult.WIN
                }
            # Check take profit hit during this minute ONLY if trailing stop is NOT enabled
            if not trailing_enabled and candle.low <= trade.take_profit:
                return {
                    'price': trade.take_profit,
                    'result': TradeResult.WIN
                }
        
        return None
    
    def _check_exit_conditions_precise(self, trade: Trade, candle: Candle, config: BacktestConfiguration) -> Optional[Dict[str, Any]]:
        """
        Check exit conditions with precise 1-minute candle data.
        
        CRITICAL: With OHLC data, we don't know the order of price movements within a candle.
        This creates ambiguity when both trailing stop update and exit occur in the same candle.
        
        Solution: Use PREVIOUS candle to update trailing stop, then check CURRENT candle for exits.
        This ensures we never use information from the same candle to both set and trigger the stop.
        """
        
        # Update trailing stop if enabled - but DON'T check for exit yet
        trailing_config = getattr(config, 'trailing_stop', None)
        trailing_stop_enabled = trailing_config and trailing_config.get('enabled', False)
        
        if trailing_stop_enabled:
            # Update trailing stop based on current candle
            self._update_trailing_stop(trade, candle, trailing_config, config.symbol)
        
        # Use trailing stop level if active, otherwise use fixed stop loss
        active_stop_loss = trade.trailing_stop_level if trade.trailing_stop_level else trade.stop_loss
        
        # CRITICAL: Check if stop loss would be hit BEFORE the high/low that updated the trailing stop
        # With OHLC data, we must assume the worst case: stop is hit before favorable price movement
        if trade.direction == TradeDirection.BUY:
            # For BUY: Check if low hit stop BEFORE high could update trailing stop
            # If candle range is large enough that both could happen, assume stop hit first
            if candle.low <= active_stop_loss:
                # Check if this is a "wide candle" where we can't determine order
                pip_value = self._get_pip_value(config.symbol)
                candle_range_pips = (candle.high - candle.low) / pip_value
                trail_distance = trailing_config.get('trail_distance_pips', 8) if trailing_stop_enabled else 0
                
                # If candle range > trail distance, we can't be sure of order
                # In this case, assume the stop was hit (conservative approach)
                if candle_range_pips > trail_distance and trailing_stop_enabled:
                    logger.warning(f"⚠️  Wide candle detected: {candle_range_pips:.1f} pips > {trail_distance} trail distance")
                    logger.warning(f"   Cannot determine if stop hit before or after high")
                    logger.warning(f"   Assuming stop hit first (conservative)")
                
                return {
                    'price': active_stop_loss,
                    'result': TradeResult.LOSS if trade.entry_price > active_stop_loss else TradeResult.WIN
                }
            # Check take profit hit during this minute ONLY if trailing stop is NOT enabled
            if not trailing_stop_enabled and candle.high >= trade.take_profit:
                return {
                    'price': trade.take_profit,
                    'result': TradeResult.WIN
                }
        else:  # SELL
            # For SELL: Check if high hit stop BEFORE low could update trailing stop
            if candle.high >= active_stop_loss:
                # Check if this is a "wide candle" where we can't determine order
                pip_value = self._get_pip_value(config.symbol)
                candle_range_pips = (candle.high - candle.low) / pip_value
                trail_distance = trailing_config.get('trail_distance_pips', 8) if trailing_stop_enabled else 0
                
                # If candle range > trail distance, we can't be sure of order
                if candle_range_pips > trail_distance and trailing_stop_enabled:
                    logger.warning(f"⚠️  Wide candle detected: {candle_range_pips:.1f} pips > {trail_distance} trail distance")
                    logger.warning(f"   Cannot determine if stop hit before or after low")
                    logger.warning(f"   Assuming stop hit first (conservative)")
                
                return {
                    'price': active_stop_loss,
                    'result': TradeResult.LOSS if trade.entry_price < active_stop_loss else TradeResult.WIN
                }
            # Check take profit hit during this minute ONLY if trailing stop is NOT enabled
            if not trailing_stop_enabled and candle.low <= trade.take_profit:
                return {
                    'price': trade.take_profit,
                    'result': TradeResult.WIN
                }
        
        return None
    
    def _check_exit_conditions(self, trade: Trade, candle: Candle, config: BacktestConfiguration) -> Optional[Dict[str, Any]]:
        """Check if trade should be closed based on stop loss, take profit, or other conditions."""
        
        # Update trailing stop if enabled in strategy configuration
        trailing_config = getattr(config, 'trailing_stop', None)
        trailing_stop_enabled = trailing_config and trailing_config.get('enabled', False)
        
        if trailing_stop_enabled:
            self._update_trailing_stop(trade, candle, trailing_config, config.symbol)
        
        # Use trailing stop level if active, otherwise use fixed stop loss
        active_stop_loss = trade.trailing_stop_level if trade.trailing_stop_level else trade.stop_loss
        
        if trade.direction == TradeDirection.BUY:
            # Check stop loss (or trailing stop)
            if candle.low <= active_stop_loss:
                return {
                    'price': active_stop_loss,
                    'result': TradeResult.LOSS if trade.entry_price > active_stop_loss else TradeResult.WIN
                }
            # Check take profit ONLY if trailing stop is NOT enabled
            if not trailing_stop_enabled and candle.high >= trade.take_profit:
                return {
                    'price': trade.take_profit, 
                    'result': TradeResult.WIN
                }
        
        else:  # SELL
            # Check stop loss (or trailing stop)
            if candle.high >= active_stop_loss:
                return {
                    'price': active_stop_loss,
                    'result': TradeResult.LOSS if trade.entry_price < active_stop_loss else TradeResult.WIN
                }
            # Check take profit ONLY if trailing stop is NOT enabled
            if not trailing_stop_enabled and candle.low <= trade.take_profit:
                return {
                    'price': trade.take_profit,
                    'result': TradeResult.WIN
                }
        
        return None
    
    def _update_trailing_stop(self, trade: Trade, candle: Candle, trailing_config: Dict[str, Any], symbol: str) -> None:
        """
        Update trailing stop loss based on current price movement.
        
        CRITICAL FIX: Uses candle.close instead of candle.high/low to avoid look-ahead bias.
        The trailing stop should trail the CLOSE price, not the high/low, because:
        1. We don't know the high/low until the candle completes
        2. Using high/low creates unrealistic exits (price touches high, then immediately hits trailing stop)
        3. Close price represents the actual market state at candle completion
        
        Args:
            trade: Active trade to update
            candle: Current candle
            trailing_config: Trailing stop configuration with 'activation_pips' and 'trail_distance_pips'
            symbol: Trading symbol for pip calculation
        """
        activation_pips = trailing_config.get('activation_pips', 0)
        trail_distance_pips = trailing_config.get('trail_distance_pips', 4)
        pip_value = self._get_pip_value(symbol)
        
        # Calculate current profit in pips using CLOSE price (not high/low)
        # This avoids look-ahead bias where we use the high to set trailing stop
        # then immediately check if the low hit it within the same candle
        if trade.direction == TradeDirection.BUY:
            current_pips = (candle.close - trade.entry_price) / pip_value
        else:  # SELL
            current_pips = (trade.entry_price - candle.close) / pip_value
        
        # Activate trailing stop once profit exceeds activation threshold
        if current_pips >= activation_pips:
            if trade.direction == TradeDirection.BUY:
                # Trail below current CLOSE (not high)
                new_trailing_stop = candle.close - (trail_distance_pips * pip_value)
                
                # Only move stop loss up, never down
                if trade.trailing_stop_level is None:
                    trade.trailing_stop_level = max(new_trailing_stop, trade.stop_loss)
                else:
                    trade.trailing_stop_level = max(trade.trailing_stop_level, new_trailing_stop)
                    
            else:  # SELL
                # Trail above current CLOSE (not low)
                new_trailing_stop = candle.close + (trail_distance_pips * pip_value)
                
                # Only move stop loss down, never up
                if trade.trailing_stop_level is None:
                    trade.trailing_stop_level = min(new_trailing_stop, trade.stop_loss)
                else:
                    trade.trailing_stop_level = min(trade.trailing_stop_level, new_trailing_stop)
    
    def _get_pip_value(self, symbol: str) -> float:
        """Get pip value based on symbol type."""
        symbol_upper = symbol.upper()
        
        # JPY pairs use 0.01 as pip value (2 decimal places)
        if 'JPY' in symbol_upper:
            return 0.01
        
        # Indices and commodities use different pip values
        if any(idx in symbol_upper for idx in ['NAS100', 'US500', 'US30', 'GER40', 'UK100', 'AUS200', 'JPN225']):
            return 1.0  # Indices typically use 1 point = 1 pip
        
        if any(metal in symbol_upper for metal in ['XAUUSD', 'GOLD', 'XAGUSD', 'SILVER']):
            return 0.01  # Metals use 0.01
        
        # Default for most forex pairs (4 decimal places)
        return 0.0001
    
    def _calculate_stop_loss(self, entry_price: float, direction: TradeDirection, stop_loss_pips: float, symbol: str = "EURUSD") -> float:
        """Calculate stop loss price."""
        pip_value = self._get_pip_value(symbol)
        
        if direction == TradeDirection.BUY:
            return entry_price - (stop_loss_pips * pip_value)
        else:
            return entry_price + (stop_loss_pips * pip_value)
    
    def _calculate_take_profit(self, entry_price: float, direction: TradeDirection, take_profit_pips: float, symbol: str = "EURUSD") -> float:
        """Calculate take profit price."""
        pip_value = self._get_pip_value(symbol)
        
        if direction == TradeDirection.BUY:
            return entry_price + (take_profit_pips * pip_value)
        else:
            return entry_price - (take_profit_pips * pip_value)
    
    def _calculate_pips(self, entry_price: float, exit_price: float, direction: TradeDirection, symbol: str) -> float:
        """Calculate pip difference between entry and exit."""
        pip_value = self._get_pip_value(symbol)
        
        if direction == TradeDirection.BUY:
            return (exit_price - entry_price) / pip_value
        else:
            return (entry_price - exit_price) / pip_value
    
    def _calculate_performance_stats(self, trades: List[Trade], initial_balance: float) -> Dict[str, float]:
        """Calculate comprehensive performance statistics."""
        if not trades:
            return {
                'total_pips': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'max_drawdown': 0.0,
                'max_consecutive_losses': 0,
                'max_consecutive_wins': 0
            }
        
        # Basic stats
        total_pips = sum(trade.pips for trade in trades if trade.pips is not None)
        
        # Classify trades by pips (including EOD_CLOSE trades)
        winning_trades = [t for t in trades if t.pips is not None and t.pips > 0]
        losing_trades = [t for t in trades if t.pips is not None and t.pips < 0]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0.0
        
        # Pip statistics
        winning_pips = [t.pips for t in winning_trades if t.pips is not None]
        losing_pips = [abs(t.pips) for t in losing_trades if t.pips is not None]
        
        average_win = sum(winning_pips) / len(winning_pips) if winning_pips else 0.0
        average_loss = sum(losing_pips) / len(losing_pips) if losing_pips else 0.0
        largest_win = max(winning_pips) if winning_pips else 0.0
        largest_loss = max(losing_pips) if losing_pips else 0.0
        
        # Profit factor
        total_winning_pips = sum(winning_pips) if winning_pips else 0.0
        total_losing_pips = sum(losing_pips) if losing_pips else 0.0
        profit_factor = total_winning_pips / total_losing_pips if total_losing_pips > 0 else float('inf') if total_winning_pips > 0 else 0.0
        
        # Consecutive wins/losses
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_consecutive_wins = 0
        current_consecutive_losses = 0
        
        for trade in trades:
            if trade.result == TradeResult.WIN:
                current_consecutive_wins += 1
                current_consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_consecutive_wins)
            elif trade.result == TradeResult.LOSS:
                current_consecutive_losses += 1
                current_consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
        
        # Calculate drawdown (simplified)
        running_pips = 0.0
        peak_pips = 0.0
        max_drawdown = 0.0
        
        for trade in trades:
            if trade.pips is not None:
                running_pips += trade.pips
                peak_pips = max(peak_pips, running_pips)
                current_drawdown = peak_pips - running_pips
                max_drawdown = max(max_drawdown, current_drawdown)
        
        return {
            'total_pips': total_pips,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'average_win': average_win,
            'average_loss': average_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'max_drawdown': max_drawdown,
            'max_consecutive_losses': max_consecutive_losses,
            'max_consecutive_wins': max_consecutive_wins
        }