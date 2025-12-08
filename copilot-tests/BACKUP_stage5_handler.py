async def handle_bulk_backtest_strategy(registry: StrategyRegistry, engine: UniversalBacktestEngine, arguments: dict) -> list[TextContent]:
    """Run bulk backtests across multiple symbols, timeframes, and SL/TP combinations."""
    strategy_name = arguments["strategy_name"]
    symbols = arguments["symbols"]
    timeframes = arguments["timeframes"]
    start_date = arguments["start_date"]
    end_date = arguments["end_date"]
    sl_tp_combinations = arguments.get("sl_tp_combinations", [{"stop_loss_pips": 15, "take_profit_pips": 25}])
    
    total_tests = len(symbols) * len(timeframes) * len(sl_tp_combinations)
    
    result_text = f"🚀 **Stage 5: COMPLETE Bulk Backtest**\n\n"
    result_text += f"**Strategy:** {strategy_name}\n"
    result_text += f"**Symbols:** {', '.join(symbols)}\n"
    result_text += f"**Timeframes:** {', '.join(timeframes)}\n"
    result_text += f"**SL/TP Combinations:** {len(sl_tp_combinations)}\n"
    result_text += f"**Period:** {start_date} to {end_date}\n"
    result_text += f"**Total Tests:** {total_tests}\n\n"
    
    # Collect results for all combinations
    results = []
    completed = 0
    
    for sl_tp in sl_tp_combinations:
        stop_loss_pips = sl_tp["stop_loss_pips"]
        take_profit_pips = sl_tp["take_profit_pips"]
        
        for symbol in symbols:
            for timeframe in timeframes:
                completed += 1
                result_text += f"⏳ Running test {completed}/{total_tests}...\r"
                
                try:
                    # Create configuration
                    config = BacktestConfiguration(
                        symbol=symbol,
                        timeframe=timeframe,
                        start_date=start_date,
                        end_date=end_date,
                        initial_balance=10000,
                        risk_per_trade=0.02,
                        stop_loss_pips=stop_loss_pips,
                        take_profit_pips=take_profit_pips
                    )
                    
                    # Get strategy
                    strategy = registry.create_strategy(strategy_name)
                    
                    # Run backtest
                    start_time = datetime.now()
                    backtest_results = await engine.run_backtest(strategy, config)
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    # Store result
                    results.append({
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'stop_loss_pips': stop_loss_pips,
                        'take_profit_pips': take_profit_pips,
                        'total_trades': backtest_results.total_trades,
                        'win_rate': backtest_results.win_rate,
                        'total_pips': backtest_results.total_pips,
                        'profit_factor': backtest_results.profit_factor,
                        'max_drawdown': backtest_results.max_drawdown,
                        'execution_time': execution_time,
                        'status': 'OK'
                    })
                    
                except Exception as e:
                    results.append({
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'stop_loss_pips': stop_loss_pips,
                        'take_profit_pips': take_profit_pips,
                        'total_trades': 0,
                        'win_rate': 0,
                        'total_pips': 0,
                        'profit_factor': 0,
                        'max_drawdown': 0,
                        'execution_time': 0,
                        'status': f'ERROR: {str(e)[:30]}'
                    })
    
    # Display summary
    successful = [r for r in results if r['status'] == 'OK']
    profitable = [r for r in results if r['total_pips'] > 0]
    total_pips = sum(r['total_pips'] for r in results)
    
    result_text = f"🚀 **Stage 5: COMPLETE Bulk Backtest**\n\n"
    result_text += f"**Strategy:** {strategy_name}\n"
    result_text += f"**Total Tests:** {total_tests}\n\n"
    result_text += f"✅ **All Backtests Complete!**\n\n"
    result_text += f"**Summary:**\n"
    result_text += f"• Successful: {len(successful)}/{total_tests}\n"
    result_text += f"• Profitable: {len(profitable)} ({len(profitable)/total_tests*100:.1f}%)\n"
    result_text += f"• Total Pips: {total_pips:+.1f}\n\n"
    
    # Generate improved HTML report (same as Stage 4)
    from datetime import datetime as dt
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    bulk_dir = project_root / "data" / "bulk"
    bulk_dir.mkdir(exist_ok=True)
    
    timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"bulk_report_COMPLETE_{timestamp}.html"
    report_path = bulk_dir / report_filename
    
    # Calculate statistics
    avg_win_rate = sum(r['win_rate'] for r in successful) / len(successful) if successful else 0
    avg_pf = sum(r['profit_factor'] for r in successful) / len(successful) if successful else 0
    best_result = max(results, key=lambda r: r['total_pips']) if results else None
    worst_result = min(results, key=lambda r: r['total_pips']) if results else None
    
    # Generate table rows
    table_rows = ""
    for i, r in enumerate(results, 1):
        pips_class = 'positive' if r['total_pips'] > 0 else 'negative' if r['total_pips'] < 0 else 'neutral'
        table_rows += f"""
                <tr>
                    <td>{i}</td>
                    <td>{r['symbol']}</td>
                    <td>{r['timeframe']}</td>
                    <td>{r['stop_loss_pips']}/{r['take_profit_pips']}</td>
                    <td>{r['total_trades']}</td>
                    <td>{r['win_rate']*100:.1f}%</td>
                    <td class="{pips_class}">{r['total_pips']:+.1f}</td>
                    <td>{r['profit_factor']:.2f}</td>
                    <td>{r['max_drawdown']:.1f}</td>
                    <td>{r['execution_time']:.2f}s</td>
                    <td>{r['status']}</td>
                </tr>
            """
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complete Bulk Backtest - {strategy_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{ background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 30px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); }}
        h1 {{ font-size: 2.5em; margin-bottom: 10px; color: #60a5fa; }}
        .subtitle {{ color: #94a3b8; font-size: 1.1em; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: #1e293b; padding: 20px; border-radius: 8px; border-left: 4px solid #60a5fa; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); }}
        .summary-card h3 {{ color: #94a3b8; font-size: 0.9em; text-transform: uppercase; margin-bottom: 8px; }}
        .summary-card .value {{ font-size: 2em; font-weight: bold; color: #60a5fa; }}
        .summary-card.positive .value {{ color: #10b981; }}
        .summary-card.negative .value {{ color: #ef4444; }}
        .best-worst {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
        .highlight-card {{ background: #1e293b; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); }}
        .highlight-card.best {{ border-left: 4px solid #10b981; }}
        .highlight-card.worst {{ border-left: 4px solid #ef4444; }}
        .highlight-card h3 {{ margin-bottom: 15px; color: #60a5fa; }}
        .highlight-card .detail {{ margin: 8px 0; color: #cbd5e1; }}
        .results-section {{ background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); }}
        .results-section h2 {{ color: #60a5fa; margin-bottom: 20px; font-size: 1.8em; }}
        table {{ width: 100%; border-collapse: collapse; background: #0f172a; border-radius: 8px; overflow: hidden; }}
        thead {{ background: #334155; }}
        th {{ padding: 15px; text-align: left; font-weight: 600; color: #e2e8f0; cursor: pointer; }}
        th:hover {{ background: #475569; }}
        tbody tr {{ border-bottom: 1px solid #334155; transition: background 0.2s; }}
        tbody tr:hover {{ background: #1e293b; }}
        td {{ padding: 12px 15px; }}
        .positive {{ color: #10b981; font-weight: 600; }}
        .negative {{ color: #ef4444; font-weight: 600; }}
        .neutral {{ color: #94a3b8; }}
        .footer {{ margin-top: 30px; text-align: center; color: #64748b; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Complete Bulk Backtest Report</h1>
            <div class="subtitle">
                <strong>Strategy:</strong> {strategy_name} | 
                <strong>Period:</strong> {start_date} to {end_date} | 
                <strong>Generated:</strong> {dt.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </header>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{total_tests}</div>
            </div>
            <div class="summary-card {'positive' if len(profitable) > total_tests/2 else ''}">
                <h3>Profitable</h3>
                <div class="value">{len(profitable)} ({len(profitable)/total_tests*100:.1f}%)</div>
            </div>
            <div class="summary-card {'positive' if total_pips > 0 else 'negative'}">
                <h3>Total Pips</h3>
                <div class="value">{total_pips:+.1f}</div>
            </div>
            <div class="summary-card">
                <h3>Avg Win Rate</h3>
                <div class="value">{avg_win_rate*100:.1f}%</div>
            </div>
            <div class="summary-card">
                <h3>Avg Profit Factor</h3>
                <div class="value">{avg_pf:.2f}</div>
            </div>
        </div>
        
        <div class="best-worst">
            <div class="highlight-card best">
                <h3>🏆 Best Performance</h3>
                {f'''<div class="detail"><strong>Symbol:</strong> {best_result['symbol']}</div>
                <div class="detail"><strong>Timeframe:</strong> {best_result['timeframe']}</div>
                <div class="detail"><strong>SL/TP:</strong> {best_result['stop_loss_pips']}/{best_result['take_profit_pips']}</div>
                <div class="detail"><strong>Total Pips:</strong> {best_result['total_pips']:+.1f}</div>
                <div class="detail"><strong>Win Rate:</strong> {best_result['win_rate']*100:.1f}%</div>
                <div class="detail"><strong>Trades:</strong> {best_result['total_trades']}</div>''' if best_result else '<p>No data</p>'}
            </div>
            <div class="highlight-card worst">
                <h3>⚠️ Worst Performance</h3>
                {f'''<div class="detail"><strong>Symbol:</strong> {worst_result['symbol']}</div>
                <div class="detail"><strong>Timeframe:</strong> {worst_result['timeframe']}</div>
                <div class="detail"><strong>SL/TP:</strong> {worst_result['stop_loss_pips']}/{worst_result['take_profit_pips']}</div>
                <div class="detail"><strong>Total Pips:</strong> {worst_result['total_pips']:+.1f}</div>
                <div class="detail"><strong>Win Rate:</strong> {worst_result['win_rate']*100:.1f}%</div>
                <div class="detail"><strong>Trades:</strong> {worst_result['total_trades']}</div>''' if worst_result else '<p>No data</p>'}
            </div>
        </div>
        
        <div class="results-section">
            <h2>Detailed Results ({total_tests} tests)</h2>
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
                    {table_rows}
                </tbody>
            </table>
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
                const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
                const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
                
                if (!isNaN(aNum) && !isNaN(bNum)) {{
                    return bNum - aNum;
                }}
                return aValue.localeCompare(bValue);
            }});
            
            rows.forEach(row => tbody.appendChild(row));
        }}
    </script>
</body>
</html>
"""
    
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    result_text += f"📊 **HTML Report Generated:**\n`{report_path}`\n\n"
    result_text += f"💡 Open the file in your browser to view the detailed report."
    
    return [TextContent(type="text", text=result_text)]
