#!/usr/bin/env python3
"""
Run individual backtests for every weekday in the past month using MCP tool.
Uses the optimal 15/15 SL/TP configuration.
"""

from datetime import datetime, timedelta
import subprocess
import json

def get_weekdays_in_range(start_date, end_date):
    """Get all weekdays (Mon-Fri) between start and end dates."""
    weekdays = []
    current = start_date
    
    while current <= end_date:
        # 0 = Monday, 6 = Sunday
        if current.weekday() < 5:  # Monday to Friday
            weekdays.append(current)
        current += timedelta(days=1)
    
    return weekdays

def main():
    """Run backtests for every weekday in the past month."""
    
    # Calculate date range (past month)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    print(f"\n{'='*80}")
    print(f"MONTHLY BACKTEST ANALYSIS")
    print(f"{'='*80}")
    print(f"Strategy: Stochastic Quad Rotation")
    print(f"Symbol: US500_SB")
    print(f"Timeframe: 1m")
    print(f"SL/TP: 15/15 pips")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*80}")
    
    # Get all weekdays in range
    weekdays = get_weekdays_in_range(start_date, end_date)
    print(f"\nTotal weekdays to test: {len(weekdays)}")
    print(f"\nThis will take approximately {len(weekdays) * 20 / 60:.1f} minutes")
    print(f"(~20 seconds per day)")
    
    input("\nPress Enter to start backtests...")
    
    results = []
    
    for i, date in enumerate(weekdays, 1):
        date_str = date.strftime('%Y-%m-%d')
        
        print(f"\n[{i}/{len(weekdays)}] Testing {date_str}...")
        
        # Note: This would need to be called via the MCP interface
        # For now, just print what would be done
        print(f"   Would run: mcp_universal_backtest_engine_run_strategy_backtest(")
        print(f"       strategy_name='Stochastic Quad Rotation',")
        print(f"       symbol='US500_SB',")
        print(f"       timeframe='1m',")
        print(f"       start_date='{date_str}',")
        print(f"       end_date='{date_str}',")
        print(f"       stop_loss_pips=15,")
        print(f"       take_profit_pips=15,")
        print(f"       auto_chart=false")
        print(f"   )")
    
    print(f"\n{'='*80}")
    print(f"NOTE: This script shows what would be run.")
    print(f"To actually run the backtests, you need to call the MCP tool")
    print(f"for each date individually through the chat interface.")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
