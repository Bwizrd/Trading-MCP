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

from shared.models import Candle, Trade, TradeDirection, TradeResult
from shared.strategy_interface import (
    TradingStrategy, StrategyContext, BacktestConfiguration, 
    BacktestResults, SignalStrength
)
from shared.indicators import indicator_registry, IndicatorRegistry
from shared.data_connector import DataConnector

logger = logging.getLogger(__name__)


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
            
            # 4. Skip fetching execution data for signal-driven architecture
            # Signal-driven mode: fetch 1m data on-demand per signal instead of bulk processing
            execution_candles = None
            logger.info(f"Using signal-driven architecture - execution data will be fetched on-demand for each signal")
            
            # Use the Candle objects directly (no conversion needed)
            strategy_candles = strategy_data.data
            strategy_candles.sort(key=lambda c: c.timestamp)  # Ensure chronological order
            
            # 5. Calculate required indicators
            logger.info(f"Calculating indicators: {strategy.requires_indicators()}")
            indicators_data = self._calculate_indicators(strategy_candles, strategy.requires_indicators())
            
            # 6. Run simulation with dual timeframes
            logger.info("Running dual-timeframe trading simulation...")
            trades = await self._run_dual_timeframe_simulation(
                strategy, strategy_candles, execution_candles, indicators_data, config
            )
            
            # 6. Calculate performance statistics
            logger.info("Calculating performance statistics...")
            stats = self._calculate_performance_stats(trades, config.initial_balance)
            
            # 7. Create results object
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
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
                market_data=strategy_candles  # Include market data for chart generation
            )
            
            logger.info(f"Backtest completed: {results.total_trades} trades, {results.win_rate:.1%} win rate, {results.total_pips:+.1f} pips")
            return results
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
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
                end_date=end_date
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
                    
                    # Create new trade
                    open_trade = Trade(
                        entry_time=candle.timestamp,
                        direction=signal.direction,
                        entry_price=signal.price,
                        stop_loss=self._calculate_stop_loss(signal.price, signal.direction, config.stop_loss_pips),
                        take_profit=self._calculate_take_profit(signal.price, signal.direction, config.take_profit_pips),
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
        config: BacktestConfiguration
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
                strategy, strategy_candles, execution_candles, indicators_data, config
            )
        
        # New optimized mode: signal-driven execution data fetching
        return await self._run_signal_driven_simulation(strategy, strategy_candles, indicators_data, config)
    
    async def _run_legacy_dual_timeframe_simulation(
        self,
        strategy: TradingStrategy,
        strategy_candles: List[Candle],
        execution_candles: List[Candle],
        indicators_data: Dict[str, Dict[datetime, float]],
        config: BacktestConfiguration
    ) -> List[Trade]:
        """Legacy dual-timeframe simulation using pre-fetched execution data."""
        trades = []
        open_trade = None
        pending_signals = []  # Signals waiting for execution
        
        logger.info(f"Running legacy dual-timeframe simulation: {len(strategy_candles)} strategy candles, {len(execution_candles)} execution candles")
        
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
            
            # Generate signal if no open position
            if not open_trade:
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
                    
                    # Create new trade with precise execution price
                    open_trade = Trade(
                        entry_time=exec_candle.timestamp,
                        direction=signal.direction,
                        entry_price=exec_candle.open,  # Use execution candle open price
                        stop_loss=self._calculate_stop_loss(exec_candle.open, signal.direction, config.stop_loss_pips),
                        take_profit=self._calculate_take_profit(exec_candle.open, signal.direction, config.take_profit_pips),
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
        config: BacktestConfiguration
    ) -> List[Trade]:
        """
        Signal-driven simulation that fetches minimal 1m data on-demand.
        
        Instead of fetching all 1m data upfront (10,080 bars for a week),
        this method:
        1. Generates signals on strategy timeframe
        2. For each signal, fetches only ~5-15 minutes of 1m data
        3. Executes trades with precise timing
        
        This reduces data usage by ~96% while maintaining full precision.
        """
        trades = []
        open_trade = None
        historical_candles = []
        
        logger.info(f"Running signal-driven simulation: {len(strategy_candles)} strategy candles")
        
        # Process strategy candles to generate signals
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
            
            # Generate signal if no open position
            if not open_trade:
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
                            logger.info(f"Trade completed: {trade_result.direction.name} @ {trade_result.entry_price:.5f} -> {trade_result.exit_price:.5f} = {trade_result.pips:+.1f} pips")
                    else:
                        logger.warning(f"No execution data available for signal @ {candle.timestamp}")
        
        # Close any remaining open trade at end of period
        if open_trade:
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
            trades.append(open_trade)
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
        
        # Create trade with precise entry
        trade = Trade(
            entry_time=entry_candle.timestamp,
            direction=signal.direction,
            entry_price=entry_candle.open,  # Enter at candle open
            stop_loss=self._calculate_stop_loss(entry_candle.open, signal.direction, config.stop_loss_pips),
            take_profit=self._calculate_take_profit(entry_candle.open, signal.direction, config.take_profit_pips),
            result=None
        )
        
        logger.info(f"Trade opened: {trade.direction.name} @ {trade.entry_price:.5f} (SL: {trade.stop_loss:.5f}, TP: {trade.take_profit:.5f})")
        strategy.on_trade_opened(trade, signal_context)
        
        # Process remaining candles for exit conditions
        for candle in execution_candles:
            if candle.timestamp > entry_candle.timestamp:
                exit_result = self._check_exit_conditions_precise(trade, candle, config)
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
    
    def _check_exit_conditions_precise(self, trade: Trade, candle: Candle, config: BacktestConfiguration) -> Optional[Dict[str, Any]]:
        """Check exit conditions with precise 1-minute candle data."""
        if trade.direction == TradeDirection.BUY:
            # Check stop loss hit during this minute
            if candle.low <= trade.stop_loss:
                return {
                    'price': trade.stop_loss,
                    'result': TradeResult.LOSS
                }
            # Check take profit hit during this minute  
            if candle.high >= trade.take_profit:
                return {
                    'price': trade.take_profit,
                    'result': TradeResult.WIN
                }
        else:  # SELL
            # Check stop loss hit during this minute
            if candle.high >= trade.stop_loss:
                return {
                    'price': trade.stop_loss,
                    'result': TradeResult.LOSS
                }
            # Check take profit hit during this minute
            if candle.low <= trade.take_profit:
                return {
                    'price': trade.take_profit,
                    'result': TradeResult.WIN
                }
        
        return None
    
    def _check_exit_conditions(self, trade: Trade, candle: Candle, config: BacktestConfiguration) -> Optional[Dict[str, Any]]:
        """Check if trade should be closed based on stop loss, take profit, or other conditions."""
        
        if trade.direction == TradeDirection.BUY:
            # Check stop loss
            if candle.low <= trade.stop_loss:
                return {
                    'price': trade.stop_loss,
                    'result': TradeResult.LOSS
                }
            # Check take profit
            if candle.high >= trade.take_profit:
                return {
                    'price': trade.take_profit, 
                    'result': TradeResult.WIN
                }
        
        else:  # SELL
            # Check stop loss
            if candle.high >= trade.stop_loss:
                return {
                    'price': trade.stop_loss,
                    'result': TradeResult.LOSS
                }
            # Check take profit  
            if candle.low <= trade.take_profit:
                return {
                    'price': trade.take_profit,
                    'result': TradeResult.WIN
                }
        
        return None
    
    def _calculate_stop_loss(self, entry_price: float, direction: TradeDirection, stop_loss_pips: float) -> float:
        """Calculate stop loss price."""
        pip_value = 0.0001  # Assuming 4-digit precision for now
        
        if direction == TradeDirection.BUY:
            return entry_price - (stop_loss_pips * pip_value)
        else:
            return entry_price + (stop_loss_pips * pip_value)
    
    def _calculate_take_profit(self, entry_price: float, direction: TradeDirection, take_profit_pips: float) -> float:
        """Calculate take profit price."""
        pip_value = 0.0001  # Assuming 4-digit precision for now
        
        if direction == TradeDirection.BUY:
            return entry_price + (take_profit_pips * pip_value)
        else:
            return entry_price - (take_profit_pips * pip_value)
    
    def _calculate_pips(self, entry_price: float, exit_price: float, direction: TradeDirection, symbol: str) -> float:
        """Calculate pip difference between entry and exit."""
        pip_value = 0.0001  # Assuming 4-digit precision for now
        
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