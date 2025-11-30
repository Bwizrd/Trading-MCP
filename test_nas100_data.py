import asyncio
from shared.data_connector import DataConnector
from datetime import datetime

async def test():
    connector = DataConnector()
    result = await connector.get_market_data(
        symbol='NAS100_SB',
        timeframe='15m',
        start_date=datetime(2025, 11, 23),
        end_date=datetime(2025, 11, 28)
    )
    print(f'Source: {result.source}')
    print(f'Candles: {len(result.data)}')
    if result.data:
        print(f'First: {result.data[0].timestamp}')
        print(f'Last: {result.data[-1].timestamp}')
    else:
        print('No data returned!')

asyncio.run(test())
