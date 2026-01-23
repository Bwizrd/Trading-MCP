#!/usr/bin/env python3
"""
View trades for a specific date with HTML table output.

Usage:
    python view_trades.py 2026-01-22
"""

import sys
import httpx
from datetime import datetime
import webbrowser
import os

def fetch_trades(date_str):
    """Fetch and parse trades for a specific date."""
    response = httpx.get(f"http://localhost:8000/deals/{date_str}")
    data = response.json()
    closed_trades = data.get('closedTrades', [])
    
    # First pass: Build entry data by positionId
    entry_data = {}
    for trade in closed_trades:
        if 'closePositionDetail' not in trade:
            position_id = trade.get('positionId')
            if position_id:
                entry_data[position_id] = {
                    'entry_time': datetime.fromtimestamp(trade['executionTimestamp'] / 1000),
                    'entry_price': trade['price'],
                    'direction': 'BUY' if trade['tradeSide'] == 1 else 'SELL'
                }
    
    # Second pass: Parse exit deals
    positions = []
    for trade in closed_trades:
        if 'closePositionDetail' not in trade:
            continue
        
        position_id = trade.get('positionId')
        symbol_id = trade.get('symbolId')
        
        entry_info = entry_data.get(position_id, {})
        entry_time = entry_info.get('entry_time', 'Unknown')
        entry_price = trade['closePositionDetail'].get('entryPrice')
        close_price = trade.get('price')
        close_time = datetime.fromtimestamp(trade['executionTimestamp'] / 1000)
        
        direction = entry_info.get('direction')
        if not direction:
            direction = 'SELL' if trade.get('tradeSide') == 1 else 'BUY'
        
        symbol_map = {
            205: 'NAS100_SB',
            219: 'US30_SB', 
            220: 'UK100_SB',
            241: 'XAUUSD_SB',
            217: 'UK100_SB'
        }
        symbol_name = symbol_map.get(symbol_id, f'Symbol_{symbol_id}')
        
        # Calculate price difference in points
        # Using pip_value = 1.0 for all symbols so pips = GBP (for lot size 1)
        if direction == 'BUY':
            price_diff = close_price - entry_price
        else:
            price_diff = entry_price - close_price
        
        # Pips = price difference (so pips match GBP value for easier comparison)
        pips = price_diff
        
        broker_profit_cents = trade.get('profit', 0)
        broker_profit = broker_profit_cents / 100
        
        positions.append({
            'deal_id': trade['dealId'],
            'symbol': symbol_name,
            'direction': direction,
            'entry_time': entry_time,
            'entry_price': entry_price,
            'close_time': close_time,
            'close_price': close_price,
            'pip_value': 1.0,  # Always 1.0 so pips = GBP
            'pips': pips,
            'broker_profit': broker_profit
        })
    
    positions.sort(key=lambda x: x['close_time'])
    return positions

def generate_html(positions, date_str):
    """Generate HTML with trades table."""
    total_pips = sum(p['pips'] for p in positions)
    total_profit = sum(p['broker_profit'] for p in positions)
    wins = len([p for p in positions if p['pips'] > 0])
    losses = len([p for p in positions if p['pips'] < 0])
    win_rate = (wins / len(positions) * 100) if positions else 0
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Trades - {date_str}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: #f5f5f5; 
        }}
        .container {{ 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }}
        h1 {{ 
            color: #333; 
            border-bottom: 3px solid #4CAF50; 
            padding-bottom: 10px; 
        }}
        .summary {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 15px; 
            margin: 20px 0; 
            padding: 20px;
            background: #f9f9f9;
            border-radius: 5px;
        }}
        .stat-box {{ 
            text-align: center; 
            padding: 15px;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }}
        .stat-label {{ 
            color: #666; 
            font-size: 12px; 
            text-transform: uppercase;
            font-weight: bold;
        }}
        .stat-value {{ 
            font-size: 24px; 
            font-weight: bold; 
            color: #333; 
            margin-top: 5px;
        }}
        .positive {{ color: #4CAF50; }}
        .negative {{ color: #f44336; }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0; 
        }}
        th {{ 
            background: #4CAF50; 
            color: white; 
            padding: 12px; 
            text-align: left; 
            font-size: 13px;
            position: sticky;
            top: 0;
        }}
        td {{ 
            padding: 10px; 
            border-bottom: 1px solid #ddd; 
            font-size: 13px;
        }}
        tr:hover {{ background: #f5f5f5; }}
        .copy-btn {{ 
            background: #4CAF50; 
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            margin: 10px 0; 
            font-size: 14px;
            font-weight: bold;
        }}
        .copy-btn:hover {{ background: #45a049; }}
        .copy-btn:active {{ background: #3d8b40; }}
        .copied {{ background: #2196F3 !important; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Trading Report - {date_str}</h1>
        
        <div class="summary">
            <div class="stat-box">
                <div class="stat-label">Total Trades</div>
                <div class="stat-value">{len(positions)}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Win Rate</div>
                <div class="stat-value {'positive' if win_rate >= 50 else 'negative'}">{win_rate:.1f}%</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Wins / Losses</div>
                <div class="stat-value">{wins} / {losses}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Pips</div>
                <div class="stat-value {'positive' if total_pips > 0 else 'negative'}">{total_pips:+.1f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total P/L</div>
                <div class="stat-value {'positive' if total_profit > 0 else 'negative'}">£{total_profit:+.2f}</div>
            </div>
        </div>
        &#128203;
        <button class="copy-btn" onclick="copyTableToClipboard()">📋 Copy Table to Clipboard</button>
        
        <table id="tradesTable">
            <thead>
                <tr>
                    <th>Deal ID</th>
                    <th>Symbol</th>
                    <th>Direction</th>
                    <th>Entry Time</th>
                    <th>Entry Price</th>
                    <th>Close Time</th>
                    <th>Close Price</th>
                    <th>Pip Value</th>
                    <th>Pips</th>
                    <th>P/L (£)</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for pos in positions:
        entry_time_str = pos['entry_time'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(pos['entry_time'], datetime) else str(pos['entry_time'])
        close_time_str = pos['close_time'].strftime('%Y-%m-%d %H:%M:%S')
        pips_class = 'positive' if pos['pips'] > 0 else 'negative'
        
        html += f"""
                <tr>
                    <td>{pos['deal_id']}</td>
                    <td>{pos['symbol']}</td>
                    <td>{pos['direction']}</td>
                    <td>{entry_time_str}</td>
                    <td>{pos['entry_price']:.2f}</td>
                    <td>{close_time_str}</td>
                    <td>{pos['close_price']:.2f}</td>
                    <td>{pos['pip_value']:.1f}</td>
                    <td class="{pips_class}">{pos['pips']:+.1f}</td>
                    <td class="{pips_class}">£{pos['broker_profit']:+.2f}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
        
        <script>
        function copyTableToClipboard() {
            const table = document.getElementById('tradesTable');
            const btn = event.target;
            
            // Create a range and selection
            const range = document.createRange();
            range.selectNode(table);
            window.getSelection().removeAllRanges();
            window.getSelection().addRange(range);
            
            try {
                // Copy to clipboard
                document.execCommand('copy');
                
                // Visual feedback
                btn.innerHTML = '&#9989; Copied!';
                btn.classList.add('copied');
                
                setTimeout(() => {
                    btn.innerHTML = '&#128203; Copy Table to Clipboard';
                    btn.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy: ', err);
                btn.innerHTML = '&#10060; Failed to copy';
            }
            
            window.getSelection().removeAllRanges();
        }
        </script>
    </div>
</body>
</html>
"""
    
    return html

def main():
    if len(sys.argv) != 2:
        print("Usage: python view_trades.py YYYY-MM-DD")
        print("Example: python view_trades.py 2026-01-22")
        sys.exit(1)
    
    date_str = sys.argv[1]
    
    # Validate date format
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format '{date_str}'. Use YYYY-MM-DD")
        sys.exit(1)
    
    print(f"Fetching trades for {date_str}...")
    
    try:
        positions = fetch_trades(date_str)
        
        if not positions:
            print(f"No trades found for {date_str}")
            sys.exit(0)
        
        print(f"Found {len(positions)} trades")
        
        html = generate_html(positions, date_str)
        
        # Create trades folder if it doesn't exist
        trades_dir = "trades"
        os.makedirs(trades_dir, exist_ok=True)
        
        # Save HTML file
        output_file = os.path.join(trades_dir, f"trades_{date_str}.html")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Generated: {output_file}")
        
        # Open in browser
        file_path = os.path.abspath(output_file)
        webbrowser.open(f'file://{file_path}')
        print(f"Opening in browser...")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
