# MACD Signal Bug - Quick Fix Reference

## Root Cause (Identified in Task 1)

**Location**: `shared/strategies/dsl_interpreter/dsl_strategy.py`, method `_evaluate_condition()`

**Bug**: Variable replacement uses naive string replace that breaks compound variable names.

### Current Buggy Code:
```python
def _evaluate_condition(self, condition_str: str, context: Dict[str, float]) -> bool:
    try:
        # Replace variables with actual values
        expression = condition_str
        for var_name, var_value in context.items():
            if var_value is not None:
                old_expr = expression
                expression = expression.replace(var_name, str(var_value))
                # ...
```

### Problem:
When evaluating `'macd > macd_signal'` with context:
```python
{
    'macd': 6.713695842264222e-05,
    'macd_signal': 6.585322514172001e-05,
    'macd_histogram': 1.2837332809222102e-06
}
```

The replacement happens in dictionary order:
1. Replace `macd` → `'6.713695842264222e-05 > macd_signal'`
2. But wait! The first replacement also affected `macd_signal`!
3. Result: `'6.713695842264222e-05 > 6.713695842264222e-05_signal'`
4. Now `_signal` is an unresolved variable
5. Condition evaluation fails

### Evidence from Diagnostic Log:
```
Condition string: 'macd > macd_signal'
Context: {'macd': 6.713695842264222e-05, 'macd_signal': 6.585322514172001e-05, ...}
Replaced 'macd' with 6.713695842264222e-05
Final expression: '6.713695842264222e-05 > 6.713695842264222e-05_signal'
Unresolved variables: ['e', 'e', '_signal']
Current condition result: False
```

## The Fix

### Solution: Sort variables by length (longest first)

Replace this section:
```python
# Replace variables with actual values
expression = condition_str
for var_name, var_value in context.items():
    if var_value is not None:
        old_expr = expression
        expression = expression.replace(var_name, str(var_value))
        if old_expr != expression:
            diagnostic_logger.debug(f"        Replaced '{var_name}' with {var_value}")
```

With this:
```python
# Replace variables with actual values
# Sort by length (longest first) to avoid partial replacements
# e.g., replace 'macd_signal' before 'macd'
expression = condition_str
sorted_vars = sorted(context.items(), key=lambda x: len(x[0]), reverse=True)
for var_name, var_value in sorted_vars:
    if var_value is not None:
        old_expr = expression
        expression = expression.replace(var_name, str(var_value))
        if old_expr != expression:
            diagnostic_logger.debug(f"        Replaced '{var_name}' with {var_value}")
```

### Why This Works:
1. `macd_signal` (11 chars) is replaced first → `'macd > 6.585322514172001e-05'`
2. Then `macd` (4 chars) is replaced → `'6.713695842264222e-05 > 6.585322514172001e-05'`
3. No partial replacements, all variables resolved correctly
4. Condition evaluates properly

### Alternative Solution (More Robust):
Use word boundaries with regex:
```python
import re

expression = condition_str
sorted_vars = sorted(context.items(), key=lambda x: len(x[0]), reverse=True)
for var_name, var_value in sorted_vars:
    if var_value is not None:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(var_name) + r'\b'
        old_expr = expression
        expression = re.sub(pattern, str(var_value), expression)
        if old_expr != expression:
            diagnostic_logger.debug(f"        Replaced '{var_name}' with {var_value}")
```

## Testing the Fix

### Quick Test:
```python
# After applying the fix, run:
python3 test_diagnostic_logging.py

# Check the log:
cat /tmp/dsl_debug.log | grep "Final expression"

# Should see:
# Final expression: '6.713695842264222e-05 > 6.585322514172001e-05'
# (No _signal suffix!)
```

### Full Test:
```python
# Run a backtest with MACD strategy
python3 -c "
from mcp_servers.universal_backtest_engine import run_backtest
result = run_backtest(
    strategy_name='MACD Crossover Strategy',
    symbol='EURUSD',
    days_back=30,
    timeframe='15m'
)
print(f'Total trades: {result[\"total_trades\"]}')
"

# Should see: Total trades: > 0 (not 0!)
```

## Impact

This single-line fix will:
- ✅ Enable MACD crossover detection
- ✅ Generate trade signals on historical data
- ✅ Display markers on charts
- ✅ Work for all indicator-based strategies with compound variable names
- ✅ Not affect time-based strategies (they use simple variable names)

## Files to Modify

1. `shared/strategies/dsl_interpreter/dsl_strategy.py` - Apply the fix
2. Test with existing test files to verify

## Estimated Time

- Fix implementation: 2 minutes
- Testing: 5 minutes
- Total: ~7 minutes to complete the entire investigation!
