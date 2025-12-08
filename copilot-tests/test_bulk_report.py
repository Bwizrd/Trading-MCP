from shared.bulk_backtest_report import BulkBacktestReportGenerator

# Test report generation
results = [
    {
        'symbol': 'EURUSD_SB',
        'timeframe': '15m',
        'stop_loss_pips': 15,
        'take_profit_pips': 25,
        'total_trades': 10,
        'win_rate': 60.0,
        'total_pips': 50.0,
        'profit_factor': 1.5,
        'max_drawdown': 20.0,
        'execution_time': 1.5,
        'status': '✅ Success'
    }
]

try:
    generator = BulkBacktestReportGenerator()
    print(f"Output dir: {generator.output_dir}")
    report_path = generator.generate_report(
        strategy_name="Test Strategy",
        results=results,
        start_date="2025-11-23",
        end_date="2025-11-28"
    )
    print(f"✅ Report generated: {report_path}")
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    print(traceback.format_exc())
