# Gradual Modular System Replacement Plan

## ✅ Step 1: COMPLETED - Verify Old System Works
- All 4 original MCP servers functional in Claude Desktop
- Safety checkpoint committed: `66cad7a`

## 🎯 Step 2: Replace Chart Generation First (Safest)

**Why start here?**
- Charts are the "output" layer - least risk of breaking core logic
- Easy to test and verify functionality
- Quick rollback if issues arise

**Current:** `trading_charts_mcp.py` (hardcoded VWAP charts)
**Replace with:** `modular_chart_engine.py` (uses strategy cartridges)

### Action Plan:
1. **Test new chart server** independently 
2. **Update Claude Desktop config** - replace just the chart server entry
3. **Test in Claude Desktop** - verify chart generation still works
4. **Rollback plan** - revert config if issues

## 🎯 Step 3: Replace Strategy Logic (Medium Risk)

**Current:** `vwap_strategy/core.py` (hardcoded VWAP strategy)
**Replace with:** `universal_backtest_engine.py` (strategy cartridge system)

### Action Plan:
1. Ensure VWAP strategy cartridge exists and works
2. Update config to use universal backtest engine
3. Test all strategy functionality
4. Rollback plan ready

## 🎯 Step 4: Consolidate Data Connectors (Lower Priority)

**Current:** Separate `ctrader.py` and `influxdb.py` servers
**Replace with:** Integrated data connector in modular system

### Action Plan:
1. Test data connector integration
2. Update config to remove separate connector servers
3. Verify data fetching still works

## 🚨 Safety Protocols

### Before Each Step:
- [ ] Commit current working state
- [ ] Test replacement component independently
- [ ] Have exact rollback commands ready

### After Each Step:
- [ ] Test in Claude Desktop immediately
- [ ] Verify all previous functionality still works
- [ ] Document any issues or differences

### Emergency Rollback:
```bash
# Revert to working config
cp claude_desktop_config_backup.json "/Users/paul/Library/Application Support/Claude/claude_desktop_config.json"
# Restart Claude Desktop
```

## 📋 Current Status

**Working Baseline:** Commit `66cad7a`
**Ready for Step 2:** Replace chart generation server

---

**NEXT ACTION:** Test the modular chart engine independently before making any config changes.