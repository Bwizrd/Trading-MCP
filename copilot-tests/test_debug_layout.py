#!/usr/bin/env python3
"""Debug layout issue"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.chart_engine import ChartEngine

engine = ChartEngine()

indicators = {
    "rsi_14": [50.0] * 50,
    "stochastic_14_3_3": [50.0] * 50,
    "macd_12_26_9": [0.001] * 50
}

print("Indicators:", list(indicators.keys()))
print("Sorted:", sorted(indicators.keys()))

layout = engine._determine_subplot_layout(indicators)
print("\nLayout:", layout)
print("Oscillator mapping:", engine._oscillator_mapping)

titles = engine._generate_subplot_titles(layout, "Test", indicators)
print("\nTitles:", titles)
