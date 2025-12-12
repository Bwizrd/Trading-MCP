#!/usr/bin/env python3
"""
Run individual backtests for every weekday in the past month.
Uses the optimal 15/15 SL/TP configuration.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.backtest_engine import UniversalBacktestEngine
from shared.data_connector import DataConnector
from shared.strategies.dsl_interpreter.dsl_loader import load_dsl_strategy
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

def run_backtest_for_date(date_str, strategy_name="Stochastic Quad Rotation", 
                          symbol="US500_SB", timeframe="1m",
                          stop_loss_pips=15, take_profit_pips=15):
    """Run a single backtest for a specific date."""
    
    print(f"\n{'='*80}")
    print(f"Running backtest for {date_str}")
    print(f"{'='*80}")
    
    try:
        # Load strategy
        strategy = load_dsl_strategy(strategy_name)
        
        # Override SL/TP in strategy config
        strategy.stop_loss_pips = stop_loss_pips
        strategy.take_profit_pips = take_profit_pips
        
        # Initialize data connector
        data_connector = DataConnector()
        
        # Fetch data for the single day
        candles = data_connector.fetch_data(
            symbol=symbol,
            start_date=date_str,
            end_date=date_str,
            timeframe=timeframe
        )
        
        if not candles:
            print(f"⚠️  No data available for {date_str}")
            return None
        
        print(f"✓ Loaded {len(candles)} candles")
        
        # Run backtest
        engine = UniversalBacktestEngine(
            strategy=strategy,
            data_connector=data_connector,
            initial_balance=10000,
            risk_per_trade=0.02
        )
        
        results = engine.run_backtest(
            symbol=symbol,
            start_date=date_str,
            end_date=date_str,
            timeframe=timeframe,
            stop_loss_pips=stop_loss_pips,
            take_profit_pips=take_profit_pips
        )
        
        # Print summary
        summary = results['summary']
        print(f"\n📊 Results:")
        print(f"   Trades: {summary['total_trades']}")
        print(f"   Win Rate: {summary['win_rate']*100:.1f}%")
        print(f"   Total Pips: {summary['total_pips']:+.1f}")
        print(f"   Profit Factor: {summary.get('profit_factor', 0):.2f}")
        
        return {
            'date': date_str,
            'trades': summary['total_trades'],
            'wins': summary['winning_trades'],
            'losses': summary['losing_trades'],
            'win_rate': summary['win_rate'],
            'total_pips': summary['total_pips'],
            'profit_factor': summary.get('profit_factor', 0),
            'max_drawdown': results['risk_metrics']['max_drawdown']
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

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
    
    # Run backtests
    results = []
    for date in weekdays:
        date_str = date.strftime('%Y-%m-%d')
        result = run_backtest_for_date(date_str)
        if result:
            results.append(result)
    
    # Generate summary report
    print(f"\n\n{'='*80}")
    print(f"MONTHLY SUMMARY REPORT")
    print(f"{'='*80}")
    
    if not results:
        print("No results to report")
        return
    
    # Calculate aggregates
    total_days = len(results)
    total_trades = sum(r['trades'] for r in results)
    total_wins = sum(r['wins'] for r in results)
    total_losses = sum(r['losses'] for r in results)
    total_pips = sum(r['total_pips'] for r in results)
    
    profitable_days = sum(1 for r in results if r['total_pips'] > 0)
    losing_days = sum(1 for r in results if r['total_pips'] < 0)
    breakeven_days = sum(1 for r in results if r['total_pips'] == 0)
    
    avg_pips_per_day = total_pips / total_days if total_days > 0 else 0
    overall_win_rate = total_wins / total_trades if total_trades > 0 else 0
    
    print(f"\n📅 Days Tested: {total_days}")
    print(f"   Profitable: {profitable_days} ({profitable_days/total_days*100:.1f}%)")
    print(f"   Losing: {losing_days} ({losing_days/total_days*100:.1f}%)")
    print(f"   Breakeven: {breakeven_days}")
    
    print(f"\n📊 Trading Statistics:")
    print(f"   Total Trades: {total_trades}")
    print(f"   Winning Trades: {total_wins}")
    print(f"   Losing Trades: {total_losses}")
    print(f"   Overall Win Rate: {overall_win_rate*100:.1f}%")
    
    print(f"\n💰 Performance:")
    print(f"   Total Pips: {total_pips:+.1f}")
    print(f"   Average Pips/Day: {avg_pips_per_day:+.1f}")
    
    # Best and worst days
    best_day = max(results, key=lambda x: x['total_pips'])
    worst_day = min(results, key=lambda x: x['total_pips'])
    
    print(f"\n🏆 Best Day: {best_day['date']}")
    print(f"   Pips: {best_day['total_pips']:+.1f}")
    print(f"   Trades: {best_day['trades']} ({best_day['wins']}W/{best_day['losses']}L)")
    
    print(f"\n⚠️  Worst Day: {worst_day['date']}")
    print(f"   Pips: {worst_day['total_pips']:+.1f}")
    print(f"   Trades: {worst_day['trades']} ({worst_day['wins']}W/{worst_day['losses']}L)")
    
    # Save detailed results to JSON
    output_file = f"optimization_results/monthly_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'strategy': 'Stochastic Quad Rotation',
            'symbol': 'US500_SB',
            'timeframe': '1m',
            'sl_tp': '15/15',
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            },
            'summary': {
                'total_days': total_days,
                'profitable_days': profitable_days,
                'losing_days': losing_days,
                'total_trades': total_trades,
                'total_wins': total_wins,
                'total_losses': total_losses,
                'overall_win_rate': overall_win_rate,
                'total_pips': total_pips,
                'avg_pips_per_day': avg_pips_per_day
            },
            'daily_results': results
        }, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: {output_file}")
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    main()
