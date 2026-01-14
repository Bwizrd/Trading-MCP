#!/usr/bin/env python3
"""
Test trailing stops using tick data from InfluxDB.
Loads trades from TradingView CSV and replays them with tick data.
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import json

# Configuration
CTRADER_API = "http://localhost:8020"
CSV_FILE = "tradingview/Stochastic_Quad_Rotation_-_SIMPLE_PEPPERSTONESB_UK100_2026-01-13 (1).csv"
SYMBOL = "UK100"
SYMBOL_ID = 217  # UK100 symbol ID for cTrader API

# Trailing stop settings
TRAILING_ACTIVATION_PIPS = 3   # Activate trailing after 3 pips profit
TRAILING_DISTANCE_PIPS = 2     # Trail 2 pips behind
FIXED_SL_PIPS = 8              # Fixed stop loss (only used before trailing activates)
FIXED_TP_PIPS = None           # No fixed TP when using trailing stops


def load_trades_from_csv(csv_path):
    """Load entry trades from TradingView CSV."""
    df = pd.read_csv(csv_path)
    
    # Filter only entry trades
    entries = df[df['Type'].str.contains('Entry', na=False)].copy()
    
    # Parse datetime
    entries['datetime'] = pd.to_datetime(entries['Date and time'])
    
    # Determine direction
    entries['direction'] = entries['Type'].apply(lambda x: 'long' if 'long' in x.lower() else 'short')
    
    # Get entry price
    entries['entry_price'] = entries['Price GBP']
    
    return entries[['datetime', 'direction', 'entry_price', 'Trade #']].to_dict('records')


def fetch_tick_data(symbol_id, start_time, end_time):
    """Fetch tick data from cTrader API."""
    # Convert to ISO format
    start_iso = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    end_iso = end_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
    # Build API URL
    url = f"{CTRADER_API}/getTickDataFromDB"
    params = {
        'pair': symbol_id,
        'startDate': start_iso,
        'endDate': end_iso,
        'maxTicks': 50000
    }
    
    try:
        print(f"  Requesting: {url}?pair={symbol_id}&startDate={start_iso}&endDate={end_iso}")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # Handle response format: {"data": [...], "symbol": "...", ...}
            if isinstance(result, dict) and 'data' in result:
                data = result['data']
                if isinstance(data, list) and len(data) > 0:
                    # Convert to DataFrame
                    ticks = []
                    for tick in data:
                        ticks.append({
                            'time': pd.to_datetime(tick['timestamp'], unit='ms'),
                            'bid': tick.get('bid'),
                            'ask': tick.get('ask')
                        })
                    return pd.DataFrame(ticks)
                else:
                    print(f"  Warning: Empty data array from API")
                    return pd.DataFrame()
            else:
                print(f"  Warning: Unexpected response format")
                return pd.DataFrame()
        else:
            print(f"  Warning: API returned status {response.status_code}")
            return pd.DataFrame()
        
    except Exception as e:
        print(f"  Error fetching tick data: {e}")
        return pd.DataFrame()


def simulate_trade_with_trailing_stop(entry_time, direction, entry_price, ticks):
    """Simulate a single trade with trailing stop using tick data."""
    
    if ticks.empty:
        return None
    
    # Calculate initial stops
    if direction == 'long':
        initial_sl = entry_price - FIXED_SL_PIPS
        trailing_activation_price = entry_price + TRAILING_ACTIVATION_PIPS
    else:  # short
        initial_sl = entry_price + FIXED_SL_PIPS
        trailing_activation_price = entry_price - TRAILING_ACTIVATION_PIPS
    
    # State
    trailing_active = False
    current_sl = initial_sl
    highest_profit = 0 if direction == 'long' else float('inf')
    
    # Replay ticks
    for idx, tick in ticks.iterrows():
        current_price = tick['bid'] if direction == 'long' else tick['ask']
        
        if pd.isna(current_price):
            continue
        
        # Check if trailing should activate
        if not trailing_active:
            if direction == 'long' and current_price >= trailing_activation_price:
                trailing_active = True
                highest_profit = current_price
                current_sl = highest_profit - TRAILING_DISTANCE_PIPS
            elif direction == 'short' and current_price <= trailing_activation_price:
                trailing_active = True
                highest_profit = current_price
                current_sl = highest_profit + TRAILING_DISTANCE_PIPS
        
        # Update trailing stop (only if already active)
        if trailing_active:
            if direction == 'long':
                if current_price > highest_profit:
                    highest_profit = current_price
                    current_sl = highest_profit - TRAILING_DISTANCE_PIPS
            else:  # short
                if current_price < highest_profit:
                    highest_profit = current_price
                    current_sl = highest_profit + TRAILING_DISTANCE_PIPS
        
        # Check stop loss
        if direction == 'long' and current_price <= current_sl:
            profit = current_price - entry_price
            return {
                'exit_reason': 'trailing_sl' if trailing_active else 'fixed_sl',
                'exit_price': current_price,
                'profit_pips': profit,
                'exit_time': tick['time'],
                'trailing_activated': trailing_active,
                'highest_profit': highest_profit if trailing_active else current_price
            }
        elif direction == 'short' and current_price >= current_sl:
            profit = entry_price - current_price
            return {
                'exit_reason': 'trailing_sl' if trailing_active else 'fixed_sl',
                'exit_price': current_price,
                'profit_pips': profit,
                'exit_time': tick['time'],
                'trailing_activated': trailing_active,
                'highest_profit': highest_profit if trailing_active else current_price
            }
    
    # Trade didn't close within tick data window
    return None


def main():
    print("=" * 80)
    print("TRAILING STOP BACKTEST WITH TICK DATA")
    print("=" * 80)
    print(f"\nSettings:")
    print(f"  Symbol: {SYMBOL}")
    print(f"  Fixed SL: {FIXED_SL_PIPS} pips (before trailing activates)")
    print(f"  Fixed TP: DISABLED (using trailing stop only)")
    print(f"  Trailing Activation: {TRAILING_ACTIVATION_PIPS} pips")
    print(f"  Trailing Distance: {TRAILING_DISTANCE_PIPS} pips")
    print(f"\nLoading trades from: {CSV_FILE}")
    
    # Load trades
    trades = load_trades_from_csv(CSV_FILE)
    print(f"Found {len(trades)} entry trades")
    
    # Filter to last few days only (where tick data exists)
    cutoff_date = datetime.now() - timedelta(days=7)
    recent_trades = [t for t in trades if t['datetime'] > cutoff_date]
    print(f"Processing {len(recent_trades)} recent trades (last 7 days)")
    
    if len(recent_trades) == 0:
        print("\nNo recent trades found. Tick data only available for last 10 days.")
        return
    
    # Process each trade
    results = []
    for i, trade in enumerate(recent_trades[:10], 1):  # Limit to 10 trades for testing
        print(f"\n--- Trade {i}/{min(10, len(recent_trades))} ---")
        print(f"Entry: {trade['datetime']} | {trade['direction'].upper()} @ {trade['entry_price']}")
        
        # Fetch tick data for trade window (assume max 30 minutes)
        start_time = trade['datetime']
        end_time = start_time + timedelta(minutes=30)
        
        print(f"Fetching tick data from {start_time} to {end_time}...")
        ticks = fetch_tick_data(SYMBOL_ID, start_time, end_time)
        
        if ticks.empty:
            print("  ⚠️  No tick data available")
            continue
        
        print(f"  ✓ Loaded {len(ticks)} ticks")
        
        # Simulate trade
        result = simulate_trade_with_trailing_stop(
            trade['datetime'],
            trade['direction'],
            trade['entry_price'],
            ticks
        )
        
        if result:
            print(f"  Exit: {result['exit_reason'].upper()} @ {result['exit_price']}")
            print(f"  Profit: {result['profit_pips']:.1f} pips")
            print(f"  Trailing activated: {result['trailing_activated']}")
            if result['trailing_activated']:
                max_profit = result['highest_profit'] - trade['entry_price'] if trade['direction'] == 'long' else trade['entry_price'] - result['highest_profit']
                print(f"  Max profit reached: {max_profit:.1f} pips")
            print(f"  Duration: {(result['exit_time'] - trade['datetime']).total_seconds():.0f}s")
            
            results.append({
                **trade,
                **result
            })
        else:
            print("  ⚠️  Trade didn't close within tick data window")
    
    # Summary
    if results:
        print("\n" + "=" * 80)
        print("RESULTS SUMMARY")
        print("=" * 80)
        
        df_results = pd.DataFrame(results)
        
        total_pips = df_results['profit_pips'].sum()
        wins = len(df_results[df_results['profit_pips'] > 0])
        losses = len(df_results[df_results['profit_pips'] < 0])
        win_rate = (wins / len(df_results)) * 100 if len(df_results) > 0 else 0
        
        trailing_activated = len(df_results[df_results['trailing_activated'] == True])
        
        print(f"\nTotal Trades: {len(df_results)}")
        print(f"Wins: {wins} | Losses: {losses}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Total Profit: {total_pips:.1f} pips")
        print(f"Avg Profit per Trade: {total_pips / len(df_results):.1f} pips")
        print(f"\nTrailing Stop Activated: {trailing_activated} times ({trailing_activated/len(df_results)*100:.1f}%)")
        
        print("\n" + "=" * 80)
        print("COMPARISON TO FIXED SL/TP")
        print("=" * 80)
        print(f"Fixed 8-pip SL/TP would give: ~{len(df_results) * 0.6 * 8 - len(df_results) * 0.4 * 8:.1f} pips")
        print(f"Trailing stop gave: {total_pips:.1f} pips")
        print(f"Difference: {total_pips - (len(df_results) * 0.6 * 8 - len(df_results) * 0.4 * 8):.1f} pips")
    else:
        print("\n⚠️  No results to analyze. Tick data may not be available for these dates.")


if __name__ == "__main__":
    main()
