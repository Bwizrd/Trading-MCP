#!/usr/bin/env python3
"""
Bulk Backtest Report Generator

Generates comprehensive HTML reports for bulk backtesting across multiple
symbols and timeframes.
"""

from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import json


class BulkBacktestReportGenerator:
    """Generate HTML reports for bulk backtest results."""
    
    def __init__(self, output_dir: str = "data/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(
        self,
        strategy_name: str,
        results: List[Dict[str, Any]],
        start_date: str,
        end_date: str
    ) -> str:
        """
        Generate comprehensive HTML report for bulk backtest results.
        
        Args:
            strategy_name: Name of the strategy tested
            results: List of backtest results for each symbol/timeframe combination
            start_date: Start date of backtest period
            end_date: End date of backtest period
            
        Returns:
            Path to generated HTML report
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"bulk_backtest_{strategy_name.replace(' ', '_')}_{timestamp}.html"
        filepath = self.output_dir / filename
        
        # Calculate summary statistics
        summary = self._calculate_summary(results)
        
        # Generate HTML
        html = self._generate_html(strategy_name, results, summary, start_date, end_date)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return str(filepath)
    
    def _calculate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics across all results."""
        total_tests = len(results)
        profitable = [r for r in results if r.get('total_pips', 0) > 0]
        
        return {
            'total_tests': total_tests,
            'profitable_count': len(profitable),
            'profitable_pct': (len(profitable) / total_tests * 100) if total_tests > 0 else 0,
            'total_pips': sum(r.get('total_pips', 0) for r in results),
            'avg_win_rate': sum(r.get('win_rate', 0) for r in results) / total_tests if total_tests > 0 else 0,
            'avg_profit_factor': sum(r.get('profit_factor', 0) for r in results) / total_tests if total_tests > 0 else 0,
            'best_result': max(results, key=lambda r: r.get('total_pips', 0)) if results else None,
            'worst_result': min(results, key=lambda r: r.get('total_pips', 0)) if results else None
        }
    
    def _generate_html(
        self,
        strategy_name: str,
        results: List[Dict[str, Any]],
        summary: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> str:
        """Generate HTML content for the report."""
        
        # Generate results table rows
        table_rows = []
        for i, result in enumerate(results, 1):
            pips = result.get('total_pips', 0)
            pips_class = 'positive' if pips > 0 else 'negative' if pips < 0 else 'neutral'
            
            sl_tp = f"{result.get('stop_loss_pips', 0)}/{result.get('take_profit_pips', 0)}"
            
            row = f"""
                <tr>
                    <td>{i}</td>
                    <td>{result.get('symbol', 'N/A')}</td>
                    <td>{result.get('timeframe', 'N/A')}</td>
                    <td>{sl_tp}</td>
                    <td>{result.get('total_trades', 0)}</td>
                    <td>{result.get('win_rate', 0):.1f}%</td>
                    <td class="{pips_class}">{pips:+.1f}</td>
                    <td>{result.get('profit_factor', 0):.2f}</td>
                    <td>{result.get('max_drawdown', 0):.1f}</td>
                    <td>{result.get('execution_time', 0):.2f}s</td>
                    <td>{result.get('status', 'Unknown')}</td>
                </tr>
            """
            table_rows.append(row)
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bulk Backtest Report - {strategy_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #60a5fa;
        }}
        
        .subtitle {{
            color: #94a3b8;
            font-size: 1.1em;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .summary-card {{
            background: #1e293b;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #60a5fa;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }}
        
        .summary-card h3 {{
            color: #94a3b8;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #60a5fa;
        }}
        
        .summary-card.positive .value {{
            color: #10b981;
        }}
        
        .summary-card.negative .value {{
            color: #ef4444;
        }}
        
        .results-section {{
            background: #1e293b;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}
        
        .results-section h2 {{
            color: #60a5fa;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        
        .table-container {{
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #0f172a;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        thead {{
            background: #334155;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #e2e8f0;
            cursor: pointer;
            user-select: none;
        }}
        
        th:hover {{
            background: #475569;
        }}
        
        tbody tr {{
            border-bottom: 1px solid #334155;
            transition: background 0.2s;
        }}
        
        tbody tr:hover {{
            background: #1e293b;
        }}
        
        td {{
            padding: 12px 15px;
        }}
        
        .positive {{
            color: #10b981;
            font-weight: 600;
        }}
        
        .negative {{
            color: #ef4444;
            font-weight: 600;
        }}
        
        .neutral {{
            color: #94a3b8;
        }}
        
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #64748b;
            font-size: 0.9em;
        }}
        
        .best-worst {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .highlight-card {{
            background: #1e293b;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }}
        
        .highlight-card.best {{
            border-left: 4px solid #10b981;
        }}
        
        .highlight-card.worst {{
            border-left: 4px solid #ef4444;
        }}
        
        .highlight-card h3 {{
            margin-bottom: 15px;
            color: #60a5fa;
        }}
        
        .highlight-card .detail {{
            margin: 8px 0;
            color: #cbd5e1;
        }}
        
        .highlight-card .detail strong {{
            color: #e2e8f0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Bulk Backtest Report</h1>
            <div class="subtitle">
                <strong>Strategy:</strong> {strategy_name} | 
                <strong>Period:</strong> {start_date} to {end_date} | 
                <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </header>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{summary['total_tests']}</div>
            </div>
            <div class="summary-card {'positive' if summary['profitable_pct'] > 50 else 'negative'}">
                <h3>Profitable</h3>
                <div class="value">{summary['profitable_count']} ({summary['profitable_pct']:.1f}%)</div>
            </div>
            <div class="summary-card {'positive' if summary['total_pips'] > 0 else 'negative'}">
                <h3>Total Pips</h3>
                <div class="value">{summary['total_pips']:+.1f}</div>
            </div>
            <div class="summary-card">
                <h3>Avg Win Rate</h3>
                <div class="value">{summary['avg_win_rate']:.1f}%</div>
            </div>
            <div class="summary-card">
                <h3>Avg Profit Factor</h3>
                <div class="value">{summary['avg_profit_factor']:.2f}</div>
            </div>
        </div>
        
        <div class="best-worst">
            <div class="highlight-card best">
                <h3>🏆 Best Performance</h3>
                {self._format_highlight(summary['best_result']) if summary['best_result'] else '<p>No data</p>'}
            </div>
            <div class="highlight-card worst">
                <h3>⚠️ Worst Performance</h3>
                {self._format_highlight(summary['worst_result']) if summary['worst_result'] else '<p>No data</p>'}
            </div>
        </div>
        
        <div class="results-section">
            <h2>Detailed Results</h2>
            <div class="table-container">
                <table id="resultsTable">
                    <thead>
                        <tr>
                            <th onclick="sortTable(0)">#</th>
                            <th onclick="sortTable(1)">Symbol</th>
                            <th onclick="sortTable(2)">Timeframe</th>
                            <th onclick="sortTable(3)">SL/TP</th>
                            <th onclick="sortTable(4)">Trades</th>
                            <th onclick="sortTable(5)">Win Rate</th>
                            <th onclick="sortTable(6)">Total Pips</th>
                            <th onclick="sortTable(7)">Profit Factor</th>
                            <th onclick="sortTable(8)">Max DD</th>
                            <th onclick="sortTable(9)">Time</th>
                            <th onclick="sortTable(10)">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by Universal Backtest Engine | Trading MCP System</p>
        </div>
    </div>
    
    <script>
        function sortTable(columnIndex) {{
            const table = document.getElementById('resultsTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            rows.sort((a, b) => {{
                const aValue = a.cells[columnIndex].textContent.trim();
                const bValue = b.cells[columnIndex].textContent.trim();
                
                // Try to parse as number
                const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
                const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
                
                if (!isNaN(aNum) && !isNaN(bNum)) {{
                    return bNum - aNum; // Descending for numbers
                }}
                
                return aValue.localeCompare(bValue);
            }});
            
            rows.forEach(row => tbody.appendChild(row));
        }}
    </script>
</body>
</html>
        """
        
        return html
    
    def _format_highlight(self, result: Dict[str, Any]) -> str:
        """Format a highlight card for best/worst result."""
        if not result:
            return '<p>No data</p>'
        
        sl_tp = f"{result.get('stop_loss_pips', 0)}/{result.get('take_profit_pips', 0)}"
        
        return f"""
            <div class="detail"><strong>Symbol:</strong> {result.get('symbol', 'N/A')}</div>
            <div class="detail"><strong>Timeframe:</strong> {result.get('timeframe', 'N/A')}</div>
            <div class="detail"><strong>SL/TP:</strong> {sl_tp}</div>
            <div class="detail"><strong>Total Pips:</strong> {result.get('total_pips', 0):+.1f}</div>
            <div class="detail"><strong>Win Rate:</strong> {result.get('win_rate', 0):.1f}%</div>
            <div class="detail"><strong>Profit Factor:</strong> {result.get('profit_factor', 0):.2f}</div>
            <div class="detail"><strong>Trades:</strong> {result.get('total_trades', 0)}</div>
        """
