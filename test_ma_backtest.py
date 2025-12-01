#!/usr/bin/env python3
"""Test MA Crossover backtest directly"""

import asyncio
from datetime import datetime, timedelta
from shared.data_connector import DataConnector
from shared.strategy_registry import StrategyRegistry

async def main():
    # Initialize components
    connector = DataConnector()
    registry = StrategyRegistry()
    
    # Get strategy
    strategy = registry.create_strategy("MA Crossover Strategy")
    print(f"Strategy: {strategy.get_name()}")
    print(f"Description: {strategy.get_description()}")
    
    # Fetch data
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=7)
    
    print(f"\nFetching data...")
    response = await connector.get_market_data(
        symbol="EURUSD_SB",
        timeframe="15m",
        start_date=start_dt,
        end_date=end_dt
    )
    
    candles = response.data
    print(f"Fetched {len(candles)} candles")
    
    # Test strategy on each candle
    from shared.strategy_interface import StrategyContext
    
    signals = []
    for i, candle in enumerate(candles):
        context = StrategyContext(
            current_candle=candle,
            historical_candles=candles[:i],
            current_position=None,
            indicators={}
        )
        
        # Process candle first (this calculates indicators)
        strategy.on_candle_processed(context)
        
        # Then generate signal
        signal = strategy.generate_signal(context)
        if signal:
            signals.append(signal)
            print(f"\n🎯 SIGNAL: {signal.direction} at {candle.timestamp} @ {signal.price}")
    
    print(f"\n=== RESULTS ===")
    print(f"Total Signals: {len(signals)}")
    print(f"Candles Processed: {len(candles)}")

if __name__ == "__main__":
    asyncio.run(main())
