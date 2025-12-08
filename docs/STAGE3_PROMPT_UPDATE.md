# Stage 3 Prompt Update: Always Generate DSL

## Problem

Previously, when the LLM encountered a strategy with unsupported indicators or features (like your MACD strategy), it would refuse to generate DSL JSON and explain why it couldn't be done.

**Old Behavior:**
```
❌ This strategy CANNOT be represented in the current DSL format because:
   - MACD is not a supported indicator type
   - Zero line filtering logic not supported
   - Multi-candle wait confirmation not supported
```

## Solution

Updated the Stage 3 prompt to instruct the LLM to **always generate a valid DSL**, even if it needs to simplify or approximate the strategy.

## New Instructions Added

```
2. If the strategy uses unsupported indicators or features:
   - DO NOT refuse to create the DSL
   - SIMPLIFY the strategy to use supported indicators (SMA, EMA, RSI, MACD)
   - APPROXIMATE the behavior using available indicators
   - ADD a comment in the description explaining the simplification
```

## Handling Guidelines

The prompt now includes specific guidance for common scenarios:

### Unsupported Indicators
**Example:** Strategy uses Stochastic Oscillator
**Action:** Use RSI as a similar oscillator indicator

### Complex Multi-Candle Logic
**Example:** Strategy waits 2 candles for confirmation
**Action:** Simplify to single-candle crossover conditions

### Advanced Exit Logic
**Example:** Strategy uses trailing stops
**Action:** Use standard stop loss and take profit

## New Behavior

Now when the LLM encounters unsupported features, it will:

1. ✅ **Generate valid DSL JSON** (not refuse)
2. ✅ **Simplify** the strategy to use supported features
3. ✅ **Document** the simplification in the description
4. ✅ **Approximate** the original behavior as closely as possible

**Example Output:**
```json
{
  "name": "MACD Crossover Strategy",
  "version": "1.0.0",
  "description": "MACD signal line crossover (simplified from original multi-candle confirmation logic)",
  "indicators": [
    {"type": "MACD", "alias": "macd"}
  ],
  "conditions": {
    "buy": {"compare": "macd > macd_signal", "crossover": true},
    "sell": {"compare": "macd < macd_signal", "crossover": true}
  },
  "risk_management": {
    "stop_loss_pips": 25,
    "take_profit_pips": 40
  }
}
```

## Benefits

1. **Always Get Output:** You'll always get a working DSL strategy, even if simplified
2. **Faster Iteration:** No need to go back and simplify manually
3. **Clear Documentation:** The description explains what was simplified
4. **Extensible:** As you add more indicators, strategies become more accurate

## Files Updated

1. `mcp_servers/strategy_builder/prompt_templates.py` - Stage 3 prompt
2. `transcript_strategy_builder.html` - Stage 3 display

## Testing

Try your MACD strategy again with Stage 3. The LLM should now:
- Generate valid MACD DSL JSON
- Include all three MACD values (line, signal, histogram)
- Create working buy/sell conditions
- Add appropriate risk management

## Next Steps

If you encounter strategies that still can't be represented well:
1. Note which indicators/features are missing
2. We can add them to the DSL (like we just did with MACD)
3. The system becomes more powerful over time

The goal is to make the workflow **always productive** - you should always get a working strategy to test, even if it's a simplified version of the original idea.
