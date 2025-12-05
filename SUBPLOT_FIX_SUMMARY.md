# Subplot Overlap Fix - Summary & Next Steps

## What We Learned from the POC

The POC (`poc_subplot_spacing.py`) **WORKS PERFECTLY** and generates charts with proper spacing. The key findings:

### ✅ Working Formula (from POC)

```python
# 1. Calculate spacing based on number of rows
if num_rows == 2:
    spacing = 0.12
elif num_rows == 3:
    spacing = 0.10
elif num_rows == 4:
    spacing = 0.08
else:  # 5+ rows
    spacing = 0.06

# 2. Calculate available space
total_spacing = (num_rows - 1) * spacing
available_space = 1.0 - total_spacing

# 3. Allocate heights from available space
price_height = 0.45 * available_space
oscillator_total = 0.35 * available_space
volume_height = 0.10 * available_space
pnl_height = 0.10 * available_space

# 4. Build heights list
heights = [price_height]
for _ in range(num_oscillators):
    heights.append(oscillator_total / num_oscillators)
heights.append(volume_height)
heights.append(pnl_height)

# 5. Create subplots with these exact values
fig = make_subplots(
    rows=num_rows,
    cols=1,
    row_heights=heights,
    vertical_spacing=spacing,
    subplot_titles=subplot_titles,
    shared_xaxes=True
)
```

### ❌ What's Wrong with Current Chart Engine

The current `chart_engine.py` has complex logic with:
- Error handling that might be interfering
- `specs` parameter that POC doesn't use
- Fallback logic that might be triggering
- The calculation was updated but something is still causing overlap

## The Solution: Complete Rewrite

Instead of trying to patch the existing code, we should:

1. **Create a new clean implementation** based directly on the POC
2. **Keep it simple** - no complex error handling initially
3. **Test incrementally** - verify spacing works before adding features
4. **Use the exact POC approach** for `make_subplots` call

## Recommended Approach

### Option 1: New Spec (Your Suggestion)
Create a fresh spec that says:
- "Rewrite the chart creation to match the POC exactly"
- "Start with a minimal working version"
- "Add features back incrementally"

### Option 2: Direct Rewrite (Faster)
- Copy the POC's `create_poc_chart()` function structure
- Adapt it to use real backtest data instead of synthetic
- Replace the current `create_comprehensive_chart()` method
- Keep all the indicator routing logic that already works

## Key Differences Between POC and Chart Engine

| Aspect | POC (Works) | Chart Engine (Broken) |
|--------|-------------|----------------------|
| `make_subplots` call | Simple, direct | Has `specs` parameter |
| Error handling | None | Extensive try/catch |
| Fallback logic | None | Multiple fallback paths |
| Spacing calculation | Inline, clear | Method call with logging |
| Height calculation | Inline, clear | Method call with logging |

## What to Keep from Current Chart Engine

The current chart engine has good features we should preserve:
- ✅ Indicator routing logic (`_route_indicator_to_subplot`)
- ✅ MACD multi-component rendering
- ✅ Trade signals and markers
- ✅ Metadata-based indicator handling
- ✅ Color schemes and styling

## What to Replace

- ❌ The entire `create_comprehensive_chart()` method
- ❌ The `_calculate_row_heights()` method (even though we just updated it)
- ❌ The complex error handling around `make_subplots`
- ❌ The fallback logic

## Next Steps

1. Create a new spec or proceed with direct rewrite
2. Copy POC structure into chart engine
3. Test with MACD strategy
4. Verify spacing is perfect
5. Add back error handling (carefully)
6. Test again

The POC proves the math works. We just need to use it exactly as-is in the production code.
