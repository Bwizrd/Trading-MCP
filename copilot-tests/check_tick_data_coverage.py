"""
Check tick data coverage for today up to now.

This script verifies that we have complete tick data coverage from market open
until the current time, and reports any gaps or issues.
"""

import requests
from datetime import datetime, timedelta
import sys


def check_tick_data_coverage(symbol_id: int, symbol_name: str, start_hour: int, start_minute: int):
    """
    Check tick data coverage from market open to now.
    
    Args:
        symbol_id: The pair ID for the API (e.g., 220 for US500_SB)
        symbol_name: Human-readable symbol name
        start_hour: Market open hour (e.g., 14 for 2:30 PM)
        start_minute: Market open minute (e.g., 30)
    """
    # Get today's date
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Market open time
    market_open = today.replace(hour=start_hour, minute=start_minute)
    
    # Current time
    now = datetime.now()
    
    # If before market open, nothing to check
    if now < market_open:
        print(f"⏰ Market hasn't opened yet. Opens at {market_open.strftime('%H:%M')}")
        return
    
    print("=" * 80)
    print(f"TICK DATA COVERAGE CHECK: {symbol_name} (pair {symbol_id})")
    print("=" * 80)
    print(f"Date: {today.strftime('%Y-%m-%d (%A)')}")
    print(f"Market Open: {market_open.strftime('%H:%M')}")
    print(f"Current Time: {now.strftime('%H:%M:%S')}")
    print(f"Expected Coverage: {market_open.strftime('%H:%M')} to {now.strftime('%H:%M')}")
    
    # Calculate expected duration
    expected_minutes = int((now - market_open).total_seconds() / 60)
    print(f"Expected Duration: {expected_minutes} minutes ({expected_minutes / 60:.1f} hours)")
    
    # Fetch tick data
    url = "http://localhost:8000/getTickDataFromDB"
    params = {
        "pair": symbol_id,
        "startDate": market_open.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        "endDate": now.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        "maxTicks": 100000  # Request up to 100k ticks
    }
    
    print("\n" + "=" * 80)
    print("FETCHING DATA...")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Start: {params['startDate']}")
    print(f"End: {params['endDate']}")
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        ticks = data.get('data', [])
        
        if not ticks:
            print("\n❌ NO TICK DATA AVAILABLE")
            print("   The tick data collection may not be running.")
            return
        
        # Analyze the ticks
        print(f"\n✅ Received {len(ticks):,} ticks")
        
        # Get first and last tick times
        first_tick_ts = ticks[0]['timestamp'] / 1000
        last_tick_ts = ticks[-1]['timestamp'] / 1000
        
        first_tick_dt = datetime.fromtimestamp(first_tick_ts)
        last_tick_dt = datetime.fromtimestamp(last_tick_ts)
        
        print("\n" + "=" * 80)
        print("COVERAGE ANALYSIS")
        print("=" * 80)
        print(f"First Tick: {first_tick_dt.strftime('%H:%M:%S')}")
        print(f"Last Tick:  {last_tick_dt.strftime('%H:%M:%S')}")
        
        # Calculate actual duration
        actual_duration = last_tick_dt - first_tick_dt
        actual_minutes = int(actual_duration.total_seconds() / 60)
        print(f"Duration:   {actual_minutes} minutes ({actual_minutes / 60:.1f} hours)")
        
        # Check gaps from expected start
        gap_from_open = first_tick_dt - market_open
        if gap_from_open.total_seconds() > 60:  # More than 1 minute gap
            gap_minutes = int(gap_from_open.total_seconds() / 60)
            print(f"\n⚠️  GAP FROM MARKET OPEN: {gap_minutes} minutes")
            print(f"    Expected: {market_open.strftime('%H:%M')}")
            print(f"    First Tick: {first_tick_dt.strftime('%H:%M')}")
        else:
            print(f"\n✅ Coverage starts on time (within 1 minute of market open)")
        
        # Check if data is up to date
        gap_to_now = now - last_tick_dt
        if gap_to_now.total_seconds() > 300:  # More than 5 minutes behind
            gap_minutes = int(gap_to_now.total_seconds() / 60)
            print(f"\n⚠️  DATA IS STALE: {gap_minutes} minutes behind current time")
            print(f"    Current: {now.strftime('%H:%M:%S')}")
            print(f"    Last Tick: {last_tick_dt.strftime('%H:%M:%S')}")
        else:
            print(f"\n✅ Data is up to date (within 5 minutes)")
        
        # Calculate coverage percentage
        coverage_pct = (actual_minutes / expected_minutes * 100) if expected_minutes > 0 else 0
        print(f"\n📊 Coverage: {coverage_pct:.1f}% of expected trading time")
        
        # Estimate ticks per second
        ticks_per_second = len(ticks) / actual_duration.total_seconds()
        print(f"📈 Tick Rate: {ticks_per_second:.1f} ticks/second")
        
        # Check for gaps within the data
        print("\n" + "=" * 80)
        print("CHECKING FOR GAPS...")
        print("=" * 80)
        
        large_gaps = []
        for i in range(1, len(ticks)):
            prev_ts = ticks[i-1]['timestamp'] / 1000
            curr_ts = ticks[i]['timestamp'] / 1000
            gap_seconds = curr_ts - prev_ts
            
            # Flag gaps larger than 5 minutes
            if gap_seconds > 300:
                prev_dt = datetime.fromtimestamp(prev_ts)
                curr_dt = datetime.fromtimestamp(curr_ts)
                large_gaps.append({
                    'start': prev_dt,
                    'end': curr_dt,
                    'duration': gap_seconds
                })
        
        if large_gaps:
            print(f"⚠️  Found {len(large_gaps)} gaps larger than 5 minutes:")
            for i, gap in enumerate(large_gaps[:10], 1):  # Show first 10
                gap_minutes = int(gap['duration'] / 60)
                print(f"   {i}. {gap['start'].strftime('%H:%M:%S')} → {gap['end'].strftime('%H:%M:%S')} ({gap_minutes} minutes)")
            if len(large_gaps) > 10:
                print(f"   ... and {len(large_gaps) - 10} more")
        else:
            print("✅ No significant gaps detected (all gaps < 5 minutes)")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        if coverage_pct > 95 and gap_to_now.total_seconds() < 300 and not large_gaps:
            print("✅ EXCELLENT: Complete tick data coverage with no issues")
        elif coverage_pct > 80 and gap_to_now.total_seconds() < 600:
            print("✅ GOOD: Mostly complete data with minor gaps")
        elif coverage_pct > 50:
            print("⚠️  PARTIAL: Significant data missing or gaps present")
        else:
            print("❌ POOR: Major data gaps or collection issues")
        
        print(f"\nTicks:    {len(ticks):,}")
        print(f"Coverage: {coverage_pct:.1f}%")
        print(f"Freshness: {int(gap_to_now.total_seconds() / 60)} minutes behind")
        print(f"Gaps:     {len(large_gaps)} (> 5 minutes)")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        print(f"   Response: {e.response.text[:200]}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Main entry point."""
    # Default to US500_SB (pair 220), market hours 14:30-21:00
    symbol_configs = [
        {'id': 220, 'name': 'US500_SB', 'open_hour': 14, 'open_minute': 30},
        {'id': 205, 'name': 'NAS100', 'open_hour': 14, 'open_minute': 30},
        {'id': 219, 'name': 'US30', 'open_hour': 14, 'open_minute': 30},
        {'id': 217, 'name': 'UK100', 'open_hour': 8, 'open_minute': 0},
        {'id': 200, 'name': 'GER40', 'open_hour': 8, 'open_minute': 0},
    ]
    
    # Check which symbol to test (default to first one)
    if len(sys.argv) > 1:
        symbol_arg = sys.argv[1].upper()
        config = next((c for c in symbol_configs if c['name'] == symbol_arg), symbol_configs[0])
    else:
        config = symbol_configs[0]
    
    check_tick_data_coverage(
        config['id'],
        config['name'],
        config['open_hour'],
        config['open_minute']
    )


if __name__ == "__main__":
    main()
