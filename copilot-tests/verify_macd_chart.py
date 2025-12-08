#!/usr/bin/env python3
"""
Detailed verification of MACD chart visualization
"""

import json
import re

# Read the most recent chart
chart_path = "data/charts/EURUSD_MACD_CROSSOVER_STRATEGY_20251204_231705.html"

with open(chart_path, 'r') as f:
    html = f.read()

print("=" * 80)
print("MACD Chart Verification")
print("=" * 80)

# Extract the Plotly data (it's in the JavaScript)
# Look for the data array in Plotly.newPlot
match = re.search(r'Plotly\.newPlot\([^,]+,\s*(\[.*?\]),\s*\{', html, re.DOTALL)

if match:
    print("\n✓ Found Plotly chart data")
    
    # Check for MACD-related traces
    macd_matches = re.findall(r'"name":"([^"]*macd[^"]*)"', html, re.IGNORECASE)
    print(f"\n📊 MACD-related traces found: {len(macd_matches)}")
    for i, name in enumerate(macd_matches, 1):
        print(f"   {i}. {name}")
    
    # Check for subplot configuration
    subplot_match = re.search(r'"annotations":\s*\[(.*?)\]', html, re.DOTALL)
    if subplot_match:
        annotations = subplot_match.group(1)
        subplot_titles = re.findall(r'"text":"([^"]+)"', annotations)
        print(f"\n📐 Subplot titles found: {len(subplot_titles)}")
        for i, title in enumerate(subplot_titles, 1):
            print(f"   {i}. {title}")
    
    # Check for MACD color
    macd_color_matches = re.findall(r'"name":"macd"[^}]*"color":"([^"]+)"', html, re.IGNORECASE)
    if macd_color_matches:
        print(f"\n🎨 MACD line color: {macd_color_matches[0]}")
        if macd_color_matches[0].upper() in ['#2196F3', '#2196f3']:
            print("   ✓ Correct (blue)")
        else:
            print(f"   ❌ Expected #2196F3 (blue), got {macd_color_matches[0]}")
    
    # Check for signal line
    signal_matches = re.findall(r'"name":"([^"]*signal[^"]*)"[^}]*"color":"([^"]+)"', html, re.IGNORECASE)
    if signal_matches:
        print(f"\n🎨 Signal line found:")
        for name, color in signal_matches:
            print(f"   Name: {name}, Color: {color}")
            if color.upper() in ['#FF5722', '#ff5722']:
                print("   ✓ Correct (red)")
            else:
                print(f"   ❌ Expected #FF5722 (red), got {color}")
    
    # Check for histogram
    histogram_matches = re.findall(r'"name":"([^"]*histogram[^"]*)"[^}]*"type":"([^"]+)"', html, re.IGNORECASE)
    if histogram_matches:
        print(f"\n📊 Histogram found:")
        for name, trace_type in histogram_matches:
            print(f"   Name: {name}, Type: {trace_type}")
            if trace_type.lower() == 'bar':
                print("   ✓ Correct (bar chart)")
            else:
                print(f"   ❌ Expected 'bar', got '{trace_type}'")
    
    # Check for zero line (hline at y=0)
    zero_line_matches = re.findall(r'"y":\s*0[,\s]', html)
    print(f"\n📏 Zero line references found: {len(zero_line_matches)}")
    if len(zero_line_matches) > 0:
        print("   ✓ Zero line likely present")
    else:
        print("   ❌ No zero line found")
    
    # Check for yaxis configuration (separate subplots have yaxis2, yaxis3, etc.)
    yaxis_matches = re.findall(r'"yaxis":"(y\d*)"', html)
    unique_yaxes = set(yaxis_matches)
    print(f"\n📊 Y-axes found: {sorted(unique_yaxes)}")
    if len(unique_yaxes) > 1:
        print(f"   ✓ Multiple y-axes suggest separate subplots")
    else:
        print(f"   ❌ Only one y-axis found - MACD may be on price chart")

else:
    print("\n❌ Could not find Plotly chart data")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)

# Final assessment
issues = []

if not macd_color_matches or macd_color_matches[0].upper() not in ['#2196F3', '#2196f3']:
    issues.append("MACD line is not blue (#2196F3)")

if not signal_matches:
    issues.append("Signal line not found")
elif signal_matches[0][1].upper() not in ['#FF5722', '#ff5722']:
    issues.append("Signal line is not red (#FF5722)")

if not histogram_matches:
    issues.append("Histogram not found")
elif histogram_matches[0][1].lower() != 'bar':
    issues.append("Histogram is not rendered as bars")

if len(unique_yaxes) <= 1:
    issues.append("MACD appears to be on price chart, not separate subplot")

if len(zero_line_matches) == 0:
    issues.append("Zero line not found")

if issues:
    print("\n❌ Issues found:")
    for issue in issues:
        print(f"   • {issue}")
else:
    print("\n✅ All requirements verified!")

print(f"\n📁 Chart file: {chart_path}")
print("   Open in browser to visually confirm")
