#!/usr/bin/env python3
"""
Debug script to trace through tick-by-tick simulation for one trade.
Shows exactly what the simulator is seeing and deciding.
"""

import asyncio
import httpx
from datetime import datetime, timedelta
import random


async def debug_trade():
    """Pick one trade and show every tick."""
    
    date_str = "2026-01-22"
    sl_pips = 10
    tp_pips = 20
    max_ticks_to_show = 50
    
    deals_url = "http://localhost:8000"
    vps_url = "http://localhost:8020"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Fetch closed positions
        print(f"Fetching closed positions for {date_str}...")
        deals_response = await client.get(f"{deals_url}/deals/{date_str}")
        deals_response.raise_for_status()
        deals_data = deals_response.json()
        
        closed_trades = deals_data.get('closedTrades', [])
        if not closed_trades:
            print(f"❌ No closed trades found for {date_str}")
            return
        
        # Parse positions
        positions = []
        for trade in closed_trades:
            detail = trade.get('closePositionDetail', {})
            entry_price = detail.get('entryPrice', 0)
            exit_price = detail.get('price', 0)
            symbol_id = trade.get('symbolId', 0)
            trade_side = trade.get('tradeSide', 0)
            direction = 'SELL' if trade_side == 1 else 'BUY'
            exit_timestamp_ms = trade.get('executionTimestamp', 0)
            
            if exit_timestamp_ms:
                exit_time = datetime.fromtimestamp(exit_timestamp_ms / 1000)
                positions.append({
                    'dealId': trade.get('id', 0),
                    'symbolId': symbol_id,
                    'direction': direction,
                    'entryPrice': entry_price,
                    'exitPrice': exit_price,
                    'exitTime': exit_time
                })
        
        print(f"Found {len(positions)} closed positions")
        
        # Sort by duration (prefer short trades)
        for pos in positions:
            pos['estimated_entry'] = pos['exitTime'] - timedelta(hours=2)
            pos['duration'] = timedelta(hours=2).total_seconds()  # Estimate
        
        positions.sort(key=lambda p: p['duration'])
        
        # Pick first one (shortest)
        selected = positions[0]
        
        # Symbol mapping
        symbol_map = {
            205: 'NAS100_SB', 220: 'US500_SB', 217: 'UK100_SB', 200: 'GER40_SB',
            219: 'US30_SB', 238: 'XAGUSD_SB', 201: 'HK50_SB', 241: 'XAUUSD_SB',
            188: 'FRA40_SB', 160: 'BTCUSD', 170: 'ETHUSD'
        }
        
        symbol_name = symbol_map.get(selected['symbolId'], f"Symbol_{selected['symbolId']}")
        
        print(f"\n{'='*80}")
        print(f"SELECTED TRADE FOR DEBUG")
        print(f"{'='*80}")
        print(f"Deal ID: {selected['dealId']}")
        print(f"Symbol: {symbol_name} (ID: {selected['symbolId']})")
        print(f"Direction: {selected['direction']}")
        print(f"Entry Price: {selected['entryPrice']}")
        print(f"Entry Time (estimated): {selected['estimated_entry']}")
        print(f"Exit Time (actual): {selected['exitTime']}")
        print(f"Exit Price (actual): {selected['exitPrice']}")
        
        # Fetch symbols to get pair ID
        print(f"\nFetching symbols list...")
        symbols_response = await client.get(f"{vps_url}/symbols")
        symbols_response.raise_for_status()
        symbols_data = symbols_response.json()
        symbols_list = symbols_data.get('symbols', [])
        
        pair_id = None
        base_symbol = symbol_name.replace('_SB', '')
        for sym in symbols_list:
            sym_name = sym.get('name', '')
            if sym_name == symbol_name or sym_name == base_symbol or sym_name == f"{base_symbol}_SB":
                pair_id = sym.get('value')
                break
        
        if not pair_id:
            print(f"❌ Could not find pair ID for {symbol_name}")
            return
        
        print(f"Found pair ID: {pair_id}")
        
        # Step 2: Fetch tick data for this trade
        entry_time = selected['estimated_entry']
        exit_time = selected['exitTime']
        
        # Add buffer to ensure we get ticks
        start_iso = (entry_time - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        end_iso = (exit_time + timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        tick_url = f"{vps_url}/getTickDataFromDB?pair={pair_id}&startDate={start_iso}&endDate={end_iso}&maxTicks=10000"
        
        print(f"\nFetching tick data...")
        print(f"URL: {tick_url}")
        
        tick_response = await client.get(tick_url, timeout=60.0)
        tick_response.raise_for_status()
        tick_data = tick_response.json()
        
        # Parse ticks
        ticks_raw = tick_data.get('data', [])
        ticks_parsed = []
        
        for tick in ticks_raw:
            try:
                ts_ms = tick.get('timestamp', 0)
                ts = datetime.fromtimestamp(ts_ms / 1000) if ts_ms else None
                bid = float(tick.get('bid', 0))
                ask = float(tick.get('ask', 0))
                mid = (bid + ask) / 2 if bid and ask else 0
                
                if ts and bid and ask:
                    ticks_parsed.append({
                        'timestamp': ts,
                        'timestamp_ms': ts_ms,
                        'bid': bid,
                        'ask': ask,
                        'mid': mid
                    })
            except (ValueError, TypeError):
                continue
        
        ticks_parsed.sort(key=lambda t: t['timestamp_ms'])
        
        print(f"Received {len(ticks_raw)} raw ticks")
        print(f"Parsed {len(ticks_parsed)} valid ticks")
        
        if ticks_parsed:
            print(f"First tick: {ticks_parsed[0]['timestamp']}")
            print(f"Last tick: {ticks_parsed[-1]['timestamp']}")
        
        # Step 3: Run simulation with verbose output
        pip_value = 0.1
        entry_price = selected['entryPrice']
        direction = selected['direction']
        
        if direction == "BUY":
            sl_price = entry_price - (sl_pips * pip_value)
            tp_price = entry_price + (tp_pips * pip_value)
        else:  # SELL
            sl_price = entry_price + (sl_pips * pip_value)
            tp_price = entry_price - (tp_pips * pip_value)
        
        print(f"\n{'='*80}")
        print(f"SIMULATION PARAMETERS")
        print(f"{'='*80}")
        print(f"Stop Loss: {sl_pips} pips → Price: {sl_price:.2f}")
        print(f"Take Profit: {tp_pips} pips → Price: {tp_price:.2f}")
        print(f"Pip Value: {pip_value}")
        
        # Find ticks starting from entry
        relevant_ticks = [t for t in ticks_parsed if t['timestamp'] >= entry_time]
        
        print(f"\nTicks after entry time: {len(relevant_ticks)}")
        
        if not relevant_ticks:
            print(f"\n❌ ERROR: No ticks found after entry time!")
            print(f"Entry time: {entry_time}")
            if ticks_parsed:
                print(f"First tick: {ticks_parsed[0]['timestamp']}")
                print(f"Last tick: {ticks_parsed[-1]['timestamp']}")
            return
        
        print(f"\n{'='*80}")
        print(f"TICK-BY-TICK SIMULATION (first {max_ticks_to_show} ticks)")
        print(f"{'='*80}\n")
        print(f"{'Tick':<6} {'Time':<12} {'Bid':<10} {'Ask':<10} {'Mid':<10} {'P/L':<10} {'Status'}")
        print("-" * 90)
        
        ticks_processed = 0
        exit_found = False
        exit_reason = None
        exit_tick = None
        
        for i, tick in enumerate(relevant_ticks):
            ticks_processed += 1
            mid_price = tick['mid']
            
            # Calculate current P/L
            if direction == "BUY":
                current_pl = (mid_price - entry_price) / pip_value
            else:  # SELL
                current_pl = (entry_price - mid_price) / pip_value
            
            # Check SL/TP
            status = "OK"
            if direction == "BUY":
                if mid_price <= sl_price:
                    status = "🛑 STOP_LOSS"
                    exit_found = True
                    exit_reason = "STOP_LOSS"
                    exit_tick = tick
                elif mid_price >= tp_price:
                    status = "✅ TAKE_PROFIT"
                    exit_found = True
                    exit_reason = "TAKE_PROFIT"
                    exit_tick = tick
            else:  # SELL
                if mid_price >= sl_price:
                    status = "🛑 STOP_LOSS"
                    exit_found = True
                    exit_reason = "STOP_LOSS"
                    exit_tick = tick
                elif mid_price <= tp_price:
                    status = "✅ TAKE_PROFIT"
                    exit_found = True
                    exit_reason = "TAKE_PROFIT"
                    exit_tick = tick
            
            # Only show first N ticks
            if i < max_ticks_to_show:
                time_str = tick['timestamp'].strftime('%H:%M:%S')
                print(f"{i+1:<6} {time_str:<12} {tick['bid']:<10.2f} {tick['ask']:<10.2f} {mid_price:<10.2f} {current_pl:<+10.1f} {status}")
            
            if exit_found:
                if i >= max_ticks_to_show:
                    print(f"... (skipped ticks {max_ticks_to_show} to {i})")
                    time_str = tick['timestamp'].strftime('%H:%M:%S')
                    print(f"{i+1:<6} {time_str:<12} {tick['bid']:<10.2f} {tick['ask']:<10.2f} {mid_price:<10.2f} {current_pl:<+10.1f} {status}")
                break
        
        print(f"\n{'='*80}")
        print(f"SIMULATION RESULT")
        print(f"{'='*80}")
        print(f"Ticks Processed: {ticks_processed}")
        
        if exit_found:
            print(f"Exit Reason: {exit_reason}")
            print(f"Exit Time: {exit_tick['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Exit Price: {exit_tick['mid']:.2f}")
            
            if direction == "BUY":
                final_pips = (exit_tick['mid'] - entry_price) / pip_value
            else:
                final_pips = (entry_price - exit_tick['mid']) / pip_value
            
            print(f"Final P/L: {final_pips:+.1f} pips")
        else:
            print(f"Exit Reason: NO_EXIT (ran out of ticks)")
            print(f"Total Ticks Available: {len(relevant_ticks)}")


if __name__ == "__main__":
    asyncio.run(debug_trade())
