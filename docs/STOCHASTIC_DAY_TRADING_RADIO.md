3. Strategy Concept

How the Quad Rotation Works

The strategy uses four stochastic indicators with different periods:
9-3 Stochastic (Yellow) - Fast, reactive
14-3 Stochastic (Blue) - Medium speed
40-4 Stochastic (White) - Slower
60-10 Stochastic (Magenta) - Slowest, trend confirmation
Entry Logic

LONG Entry Conditions:
ALL four stochastics must be in oversold territory (below your Oversold Level, default 10)
Then, ALL four stochastics must RISE ABOVE the oversold level (rotation begins)
Price must stay in oversold territory for at least 2 bars (Bars in Direction setting)
The 9-3 stochastic D-line must be ≤ 50 when the signal triggers
The 60-10 stochastic must be > 10 (Extreme filter to avoid deep downtrends)
Maximum 8 bars wait time (Max Wait Bars setting)
SHORT Entry Conditions:
ALL four stochastics must be in overbought territory (above your Overbought Level, default 90)
Then, ALL four stochastics must FALL BELOW the overbought level (rotation begins)
Price must stay in overbought territory for at least 2 bars
The 9-3 stochastic D-line must be ≥ 50 when the signal triggers
The 60-10 stochastic must be < 90 (Extreme filter to avoid deep uptrends)
Maximum 8 bars wait time
Exit Logic

The strategy has three exit methods (in order of priority):
1. Safety Net Exit (Highest Priority)
Monitors the 9-3 stochastic D-line
LONG exits when 9-3 D reaches overbought level (default 80)
SHORT exits when 9-3 D reaches oversold level (default 20)
Protects profits by exiting when momentum reverses
2. Trailing Stop (Second Priority - Optional)
Activates after trade reaches specified profit threshold
Follows price at specified distance
Locks in profits as price moves favorably
Only active if "Enable Trailing Stop" is turned ON
3. Swing-Based Stop Loss (Always Active)
LONG: Placed below the lowest low of bars 1-5 at entry
SHORT: Placed above the highest high of bars 1-5 at entry
Adjustable offset in ticks (default: 1 tick)
Protects against major adverse moves


4. Parameter Settings Guide

1. Signal Generation

Oversold Level (Range: 5-20, Default: 10)
All four stochastics must reach this level or below to prepare a LONG signal.
• Lower values = more extreme oversold conditions required
• Recommendation: 10 for ES/NQ, 15 for choppier markets
Overbought Level (Range: 80-95, Default: 90)
All four stochastics must reach this level or above to prepare a SHORT signal.
• Higher values = more extreme overbought conditions required
• Recommendation: 90 for ES/NQ, 85 for choppier markets
Bars in Direction Required (Range: 1-5, Default: 2)
How many consecutive bars all stochastics must stay in oversold/overbought before signal.
• Higher values = more confirmation, fewer trades
• Lower values = faster signals, more trades
• Recommendation: 2 for balance between speed and confirmation
Max Wait Bars After Rotation (Range: 3-20, Default: 8)
How long to wait for entry conditions after rotation starts.
• Prevents stale signals
• Recommendation: 8-10 bars for 1-minute charts
2. Safety Net

Enable Safety Net Rotation Exit (Default: ON)
Master switch for Safety Net exits.
• Recommended: Always ON for profit protection
Safety Net Oversold Exit Level (Range: 10-30, Default: 20)
SHORT trades exit when 9-3 D reaches this level.
• Lower = let trades run longer, more risk
• Higher = exit sooner, less profit potential
• Recommendation: 20 (default), 25 (more conservative)
Safety Net Overbought Exit Level (Range: 70-90, Default: 80)
LONG trades exit when 9-3 D reaches this level.
• Higher = let trades run longer, more risk
• Lower = exit sooner, less profit potential
• Recommendation: 80 (default), 75 (more conservative)
3. Stop Loss

Enable Stop Loss (Default: ON)
Master switch for swing-based stop loss.
• Recommended: Always ON for risk management
Stop Offset Ticks (Range: 0-50, Default: 1)
Additional ticks beyond the swing high/low for stop placement.
• Example: If swing low is 6900.00 and offset is 2 ticks, stop is at 6899.50
• Higher offset = more room, fewer false stops
• Lower offset = tighter stops, more risk of premature exit
• Recommendation: 1-2 ticks for ES/NQ
Enable Trailing Stop (Default: OFF)
Activates trailing stop functionality.
• Works alongside Safety Net (Safety Net has priority)
• Recommended: Test both ON and OFF to see which suits your style
Trailing Stop Distance (Ticks) (Range: 1-50, Default: 8)
How many ticks behind price the trailing stop follows.
• Example: Price at 6910.00, distance 8 ticks → trailing stop at 6908.00
• Smaller distance = tighter trailing, more protection, less profit potential
• Larger distance = looser trailing, more profit potential, less protection
• Recommendation: 6-10 ticks for ES/NQ
Trailing Stop Activation (Ticks Profit) (Range: 0-100, Default: 4)
Trade must be this many ticks in profit before trailing stop activates.
• Prevents trailing stop from activating too early
• Example: Trade at +4 ticks → trailing stop activates
• Recommendation: 4-6 ticks for ES/NQ