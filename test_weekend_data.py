#!/usr/bin/env python3
"""
Test script to verify weekend data retrieval from cTrader connector.
Run on Saturday/Sunday to test weekend functionality.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.data_connector import DataConnector

async def test_weekend_data_retrieval():
    """Test that data connector can retrieve backtest data on weekends."""

    print("=" * 70)
    print("WEEKEND DATA RETRIEVAL TEST")
    print("=" * 70)
    print(f"Current date/time: {datetime.now()}")
    print(f"Day of week: {datetime.now().strftime('%A')}")
    print()

    # Initialize connector
    connector = DataConnector()

    # Test connectivity first
    print("Testing API connectivity...")
    connectivity = await connector.test_connectivity()
    print(f"Status: {connectivity['status']}")
    print(f"Message: {connectivity['message']}")
    print()

    if connectivity['status'] != 'connected':
        print("❌ API server is not responding. Cannot proceed with test.")
        return False

    # Test historical data retrieval
    print("Testing historical data retrieval...")
    end_date = datetime.now() - timedelta(days=3)  # Recent weekday data
    start_date = end_date - timedelta(days=5)

    print(f"Requesting data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    try:
        response = await connector.get_market_data(
            symbol="EURUSD",
            timeframe="1h",
            start_date=start_date,
            end_date=end_date
        )

        print(f"\n✅ Data retrieval successful!")
        print(f"Source: {response.source}")
        print(f"Data points: {len(response.data)}")

        if response.data:
            print(f"First candle: {response.data[0].timestamp} - O:{response.data[0].open}, H:{response.data[0].high}, L:{response.data[0].low}, C:{response.data[0].close}")
            print(f"Last candle: {response.data[-1].timestamp} - O:{response.data[-1].open}, H:{response.data[-1].high}, L:{response.data[-1].low}, C:{response.data[-1].close}")
            return True
        else:
            print("❌ No data returned")
            return False

    except Exception as e:
        print(f"❌ Error during data retrieval: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_weekend_data_retrieval())
    sys.exit(0 if result else 1)
