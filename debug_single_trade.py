#!/usr/bin/env python3
"""
Debug Single Trade Tick-by-Tick Analyzer

Usage:
    python debug_single_trade.py 2026-01-22 --trade-index 0 --sl 10 --tp 20
    python debug_single_trade.py 2026-01-22 --deal-id 12345 --sl 10 --tp 20
"""

import httpx
import argparse
from datetime import datetime, timedelta
import webbrowser
import os


def fetch_trade(date_str, trade_index=None, deal_id=None):
    """Fetch a specific trade from the deals API."""
    url = f"http://localhost:8000/deals/{date_str}"
    response = httpx.get(url, timeout=30.0)
    data = response.json()
    closed_trades = data.get('closedTrades', [])
    
    # Build entry data
    entry_data = {}
    for trade in closed_trades:
        if 'closePositionDetail' not in trade:
            position_id = trade.get('positionId')
            if position_id:
                entry_data[position_id] = {
                    'entry_time': datetime.fromtimestamp(trade['executionTimestamp'] / 1000),
                    'entry_price': trade['price'],
                    'direction': 'BUY' if trade['tradeSide'] == 1 else 'SELL',
                    'deal_id': trade['dealId']
                }
    
    # Parse exit deals
    trades = []
    for trade in closed_trades:
        if 'closePositionDetail' not in trade:
            continue
        
        position_id = trade.get('positionId')
        entry_info = entry_data.get(position_id, {})
        
        symbol_map = {205: 'NAS100_SB', 219: 'US30_SB', 220: 'UK100_SB', 241: 'XAUUSD_SB', 217: 'US500_SB'}
        symbol_name = symbol_map.get(trade.get('symbolId'), f"Symbol_{trade.get('symbolId')}")
        
        trades.append({
            'deal_id': trade['dealId'],
            'position_id': position_id,
            'symbol_id': trade.get('symbolId'),
            'symbol_name': symbol_name,
            'entry_time': entry_info.get('entry_time'),
            'entry_price': entry_info.get('entry_price'),
            'exit_time': datetime.fromtimestamp(trade['executionTimestamp'] / 1000),
            'exit_price': trade['price'],
            'direction': entry_info.get('direction'),
            'broker_profit_cents': trade.get('profit', 0),
            'broker_profit': trade.get('profit', 0) / 100
        })
    
    # Select trade
    if deal_id:
        for t in trades:
            if t['deal_id'] == deal_id:
                return t
        raise ValueError(f"Trade with deal_id {deal_id} not found")
    elif trade_index is not None:
        if trade_index < 0 or trade_index >= len(trades):
            raise ValueError(f"Trade index {trade_index} out of range (0-{len(trades)-1})")
        return trades[trade_index]
    else:
        return trades[0]  # Default to first trade


def fetch_ticks(symbol_id, start_time, end_time):
    """Fetch tick data for the trade."""
    # Format timestamps as ISO strings with Z suffix
    start_iso = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_iso = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    url = "http://localhost:8020/getTickDataFromDB"
    params = {
        'pair': symbol_id,  # Use symbol ID directly
        'startDate': start_iso,
        'endDate': end_iso,
        'maxTicks': 50000
    }
    
    response = httpx.get(url, params=params, timeout=60.0)
    data = response.json()
    
    # Check if response has error
    if isinstance(data, dict) and 'error' in data:
        print(f"Error fetching ticks: {data['error']}")
        return []
    
    # Response format: {"data": [...], "symbol": ..., "tick_count": ...}
    tick_list = data.get('data', [])
    
    ticks = []
    for tick_dict in tick_list:
        try:
            # Tick format: {"timestamp": timestamp_ms, "bid": bid, "ask": ask}
            ts_ms = tick_dict.get('timestamp')
            bid = tick_dict.get('bid')
            ask = tick_dict.get('ask')
            
            if ts_ms and bid is not None and ask is not None:
                ts = datetime.fromtimestamp(ts_ms / 1000)
                ticks.append({
                    'timestamp': ts,
                    'timestamp_ms': ts_ms,
                    'bid': float(bid),
                    'ask': float(ask),
                    'mid': (float(bid) + float(ask)) / 2
                })
        except (ValueError, TypeError):
            continue
    
    ticks.sort(key=lambda t: t['timestamp_ms'])
    return ticks


def simulate_trade_detailed(trade, ticks, sl_pips, tp_pips):
    """Simulate trade and record every tick."""
    entry_price = trade['entry_price']
    direction = trade['direction']
    pip_value = 1.0  # Using 1.0 for all symbols
    
    # Spread tolerance for execution (typical spread ~1 pip, allow some slippage)
    spread_tolerance = 1.5  # Allow TP/SL to trigger within 1.5 pips of target
    
    # Calculate SL/TP levels
    if direction == 'BUY':
        sl_price = entry_price - (sl_pips * pip_value)
        tp_price = entry_price + (tp_pips * pip_value)
    else:  # SELL
        sl_price = entry_price + (sl_pips * pip_value)
        tp_price = entry_price - (tp_pips * pip_value)
    
    # Process each tick
    tick_details = []
    exit_result = None
    
    for i, tick in enumerate(ticks):
        if tick['timestamp'] < trade['entry_time']:
            continue
        
        # Calculate current P/L
        if direction == 'BUY':
            current_pl_bid = (tick['bid'] - entry_price) / pip_value
            current_pl_ask = (tick['ask'] - entry_price) / pip_value
            check_price = tick['bid']  # BUY exits at bid
        else:  # SELL
            current_pl_bid = (entry_price - tick['bid']) / pip_value
            current_pl_ask = (entry_price - tick['ask']) / pip_value
            check_price = tick['ask']  # SELL exits at ask
        
        # Check for SL/TP hit (with spread tolerance)
        hit_sl = False
        hit_tp = False
        
        if direction == 'BUY':
            # BUY: check bid price against levels
            if check_price <= sl_price + spread_tolerance:  # Allow tolerance for SL
                hit_sl = True
            elif check_price >= tp_price - spread_tolerance:  # Allow tolerance for TP
                hit_tp = True
        else:  # SELL
            # SELL: check ask price against levels
            if check_price >= sl_price - spread_tolerance:  # Allow tolerance for SL
                hit_sl = True
            elif check_price <= tp_price + spread_tolerance:  # Allow tolerance for TP
                hit_tp = True
        
        tick_details.append({
            'index': i,
            'timestamp': tick['timestamp'],
            'bid': tick['bid'],
            'ask': tick['ask'],
            'mid': tick['mid'],
            'check_price': check_price,
            'current_pl': current_pl_bid if direction == 'BUY' else current_pl_ask,
            'hit_sl': hit_sl,
            'hit_tp': hit_tp
        })
        
        if hit_sl:
            exit_result = {
                'reason': 'STOP_LOSS',
                'exit_price': sl_price,
                'exit_tick_index': i,
                'pips': -sl_pips
            }
            break
        elif hit_tp:
            exit_result = {
                'reason': 'TAKE_PROFIT',
                'exit_price': tp_price,
                'exit_tick_index': i,
                'pips': tp_pips
            }
            break
    
    if not exit_result:
        exit_result = {
            'reason': 'NO_EXIT',
            'exit_price': trade['exit_price'],
            'exit_tick_index': len(tick_details) - 1 if tick_details else 0,
            'pips': 0
        }
    
    return {
        'sl_price': sl_price,
        'tp_price': tp_price,
        'tick_details': tick_details,
        'exit_result': exit_result
    }


def generate_html(trade, simulation, sl_pips, tp_pips, date_str):
    """Generate detailed HTML report."""
    
    # Calculate actual broker result
    if trade['direction'] == 'BUY':
        broker_pips = trade['exit_price'] - trade['entry_price']
    else:
        broker_pips = trade['entry_price'] - trade['exit_price']
    
    # Determine if match
    sim_result = simulation['exit_result']['reason']
    sim_pips = simulation['exit_result']['pips']
    
    matches = abs(broker_pips - sim_pips) < 0.1
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Trade Debug: {trade['symbol_name']} - {date_str}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        .trade-info {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 20px 0;
        }}
        .info-box {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }}
        .info-box label {{
            font-weight: bold;
            color: #7f8c8d;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .info-box .value {{
            font-size: 18px;
            color: #2c3e50;
            margin-top: 5px;
        }}
        .comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .comparison-box {{
            padding: 20px;
            border-radius: 5px;
            border: 2px solid #bdc3c7;
        }}
        .comparison-box.match {{
            border-color: #27ae60;
            background: #d5f4e6;
        }}
        .comparison-box.mismatch {{
            border-color: #e74c3c;
            background: #fadbd8;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 13px;
        }}
        th {{
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .hit-sl {{
            background: #fadbd8 !important;
            font-weight: bold;
        }}
        .hit-tp {{
            background: #d5f4e6 !important;
            font-weight: bold;
        }}
        .positive {{
            color: #27ae60;
            font-weight: bold;
        }}
        .negative {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .neutral {{
            color: #7f8c8d;
        }}
        .direction-BUY {{
            color: #27ae60;
            font-weight: bold;
        }}
        .direction-SELL {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .summary {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Trade Debug Analysis</h1>
        <p><strong>Date:</strong> {date_str} | <strong>Deal ID:</strong> {trade['deal_id']}</p>
        
        <h2>Trade Details</h2>
        <div class="trade-info">
            <div class="info-box">
                <label>Symbol</label>
                <div class="value">{trade['symbol_name']}</div>
            </div>
            <div class="info-box">
                <label>Direction</label>
                <div class="value direction-{trade['direction']}">{trade['direction']}</div>
            </div>
            <div class="info-box">
                <label>Entry Time</label>
                <div class="value">{trade['entry_time'].strftime('%H:%M:%S.%f')[:-3] if trade['entry_time'] else 'Unknown'}</div>
            </div>
            <div class="info-box">
                <label>Entry Price</label>
                <div class="value">{trade['entry_price']:.2f}</div>
            </div>
            <div class="info-box">
                <label>Exit Time (Broker)</label>
                <div class="value">{trade['exit_time'].strftime('%H:%M:%S.%f')[:-3]}</div>
            </div>
            <div class="info-box">
                <label>Exit Price (Broker)</label>
                <div class="value">{trade['exit_price']:.2f}</div>
            </div>
        </div>
        
        <h2>Simulation Parameters</h2>
        <div class="trade-info">
            <div class="info-box">
                <label>Stop Loss</label>
                <div class="value">{sl_pips} pips → {simulation['sl_price']:.2f}</div>
            </div>
            <div class="info-box">
                <label>Take Profit</label>
                <div class="value">{tp_pips} pips → {simulation['tp_price']:.2f}</div>
            </div>
            <div class="info-box">
                <label>Pip Value</label>
                <div class="value">1.0 (pips = GBP)</div>
            </div>
        </div>
        
        <h2>Results Comparison</h2>
        <div class="comparison">
            <div class="comparison-box">
                <h3>🤖 Optimizer Simulation</h3>
                <p><strong>Result:</strong> {sim_result}</p>
                <p><strong>Exit Price:</strong> {simulation['exit_result']['exit_price']:.2f}</p>
                <p><strong>Pips:</strong> <span class="{'positive' if sim_pips > 0 else 'negative' if sim_pips < 0 else 'neutral'}">{sim_pips:+.2f}</span></p>
                <p><strong>GBP:</strong> £{sim_pips:+.2f}</p>
                <p><strong>Tick Index:</strong> {simulation['exit_result']['exit_tick_index']}</p>
            </div>
            <div class="comparison-box {'match' if matches else 'mismatch'}">
                <h3>🏦 Broker Actual</h3>
                <p><strong>Result:</strong> Manual/Broker Exit</p>
                <p><strong>Exit Price:</strong> {trade['exit_price']:.2f}</p>
                <p><strong>Pips:</strong> <span class="{'positive' if broker_pips > 0 else 'negative' if broker_pips < 0 else 'neutral'}">{broker_pips:+.2f}</span></p>
                <p><strong>GBP:</strong> £{trade['broker_profit']:+.2f}</p>
                <p><strong>Match:</strong> {"✅ YES" if matches else "❌ NO"}</p>
            </div>
        </div>
        
        {"<div class='summary'><h3>⚠️ Discrepancy Detected</h3><p>The optimizer simulation result does NOT match broker actual result. This indicates:</p><ul><li>Trade was manually closed before SL/TP hit</li><li>Broker execution differs from tick-level simulation</li><li>Slippage or different execution rules apply</li></ul></div>" if not matches else "<div class='summary'><h3>✅ Results Match</h3><p>The optimizer simulation matches the broker result perfectly.</p></div>"}
        
        <h2>Tick-by-Tick Analysis ({len(simulation['tick_details'])} ticks)</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Timestamp</th>
                    <th>Bid</th>
                    <th>Ask</th>
                    <th>Check Price</th>
                    <th>Current P/L</th>
                    <th>Hit SL?</th>
                    <th>Hit TP?</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for tick in simulation['tick_details']:
        row_class = ''
        status = '✓ Active'
        if tick['hit_sl']:
            row_class = 'hit-sl'
            status = '🛑 SL HIT'
        elif tick['hit_tp']:
            row_class = 'hit-tp'
            status = '🎯 TP HIT'
        
        pl_class = 'positive' if tick['current_pl'] > 0 else 'negative' if tick['current_pl'] < 0 else 'neutral'
        
        html += f"""
                <tr class="{row_class}">
                    <td>{tick['index']}</td>
                    <td>{tick['timestamp'].strftime('%H:%M:%S.%f')[:-3]}</td>
                    <td>{tick['bid']:.2f}</td>
                    <td>{tick['ask']:.2f}</td>
                    <td>{tick['check_price']:.2f}</td>
                    <td class="{pl_class}">{tick['current_pl']:+.2f}</td>
                    <td>{"❌ YES" if tick['hit_sl'] else ""}</td>
                    <td>{"✅ YES" if tick['hit_tp'] else ""}</td>
                    <td>{status}</td>
                </tr>
"""
        
        if tick['hit_sl'] or tick['hit_tp']:
            break
    
    html += """
            </tbody>
        </table>
        
        <div class="summary">
            <h3>Analysis Notes</h3>
            <ul>
                <li><strong>BUY trades:</strong> Enter at ASK, exit at BID (check BID for SL/TP)</li>
                <li><strong>SELL trades:</strong> Enter at BID, exit at ASK (check ASK for SL/TP)</li>
                <li><strong>Pip Value:</strong> 1.0 for all symbols (1 pip = 1 point = £1)</li>
                <li><strong>Red rows:</strong> Stop Loss hit</li>
                <li><strong>Green rows:</strong> Take Profit hit</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def main():
    parser = argparse.ArgumentParser(description='Debug a single trade tick-by-tick')
    parser.add_argument('date', help='Date in YYYY-MM-DD format')
    parser.add_argument('--trade-index', type=int, help='Trade index (0-based)')
    parser.add_argument('--deal-id', type=int, help='Specific deal ID')
    parser.add_argument('--sl', type=float, required=True, help='Stop loss in pips')
    parser.add_argument('--tp', type=float, required=True, help='Take profit in pips')
    
    args = parser.parse_args()
    
    print(f"Fetching trade for {args.date}...")
    trade = fetch_trade(args.date, trade_index=args.trade_index, deal_id=args.deal_id)
    
    print(f"Selected trade: {trade['symbol_name']} {trade['direction']} @ {trade['entry_price']:.2f}")
    print(f"Entry: {trade['entry_time'].strftime('%H:%M:%S') if trade['entry_time'] else 'Unknown'}")
    print(f"Exit: {trade['exit_time'].strftime('%H:%M:%S')} @ {trade['exit_price']:.2f}")
    print(f"Broker P/L: £{trade['broker_profit']:+.2f}")
    print()
    
    print("Fetching tick data...")
    # Add buffer time
    start_time = trade['entry_time'] - timedelta(seconds=30) if trade['entry_time'] else trade['exit_time'] - timedelta(hours=2)
    end_time = trade['exit_time'] + timedelta(seconds=30)
    
    ticks = fetch_ticks(trade['symbol_id'], start_time, end_time)
    print(f"Fetched {len(ticks)} ticks")
    print()
    
    print("Simulating trade...")
    simulation = simulate_trade_detailed(trade, ticks, args.sl, args.tp)
    print(f"Simulation result: {simulation['exit_result']['reason']}")
    print(f"Simulation pips: {simulation['exit_result']['pips']:+.2f}")
    print(f"Ticks processed: {len(simulation['tick_details'])}")
    print()
    
    # Generate HTML
    html = generate_html(trade, simulation, args.sl, args.tp, args.date)
    
    # Save to debug_trades folder
    debug_dir = 'debug_trades'
    os.makedirs(debug_dir, exist_ok=True)
    
    filename = f"debug_trade_{trade['deal_id']}_{args.date}.html"
    filepath = os.path.join(debug_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Generated: {filepath}")
    print()
    
    # Open in browser
    webbrowser.open(f'file://{os.path.abspath(filepath)}')
    print("Opening in browser...")


if __name__ == '__main__':
    main()
