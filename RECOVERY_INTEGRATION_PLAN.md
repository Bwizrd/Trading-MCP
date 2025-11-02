# 🎯 RECOVERY PLAN: Integrating Modular Cartridge System

## Current Status
- ✅ **Git Reset Complete**: Back to working commit `5d1ea87` (vwap test strategy working)
- ✅ **Stashed Changes**: All modular cartridge system changes saved in git stash
- ✅ **Original Config Restored**: Working MCP servers from the original architecture

## Working Architecture (Current)
```
/mcp_servers/
├── charts/trading_charts_mcp.py          # Chart generation server
├── strategies/vwap_strategy/core.py      # VWAP strategy server  
├── data_connectors/ctrader.py            # cTrader data connector
└── data_connectors/influxdb.py           # InfluxDB data connector
```

## Stashed Modular Architecture (To Integrate)
The git stash contains the new modular cartridge system:
- `universal_backtest_mcp.py` - Universal strategy backtest engine
- `modular_chart_mcp.py` - Independent chart generation
- Enhanced `shared/` modules with strategy registry and cartridge system
- Complete JSON export/import workflow

## Integration Plan

### Phase 1: Verify Current Working State
1. **Test Current Setup**: Restart Claude Desktop and verify tools work
2. **Document Working Tools**: List what tools appear and function correctly
3. **Baseline Test**: Run a simple backtest to confirm functionality

### Phase 2: Incremental Integration
1. **Extract Stash Components**: Carefully pull specific files from stash
2. **Add Without Replacing**: Add new modular servers alongside existing ones
3. **Test Each Addition**: Verify each new server works independently

### Phase 3: Selective Migration
1. **Keep Working Servers**: Don't break what currently works
2. **Add Modular Servers**: Add as additional tools, not replacements
3. **Gradual Transition**: Let user choose which tools to use

## Key Files to Extract from Stash

### New Modular Servers (Add Alongside Existing)
- `mcp_servers/universal_backtest_mcp.py` → Rename to avoid conflicts
- `mcp_servers/modular_chart_mcp.py` → Rename to avoid conflicts

### Enhanced Shared Modules (Integrate Carefully)
- `shared/strategy_registry.py` - Strategy cartridge system
- `shared/backtest_engine.py` - Universal backtest engine
- Enhanced `shared/data_connector.py` - Improved data handling

### Integration Strategy
```bash
# 1. List stash contents
git stash show --name-only

# 2. Extract specific files without overwriting
git show stash@{0}:path/to/file > new_file_name.py

# 3. Add as additional servers in config
# Don't replace working servers, add alongside them
```

## Claude Desktop Configuration Strategy

### Current Working Config
```json
{
  "mcpServers": {
    "trading-charts": {...},
    "vwap-strategy": {...},
    "ctrader-connector": {...},
    "influxdb-connector": {...}
  }
}
```

### Target Integrated Config
```json
{
  "mcpServers": {
    // Keep existing working servers
    "trading-charts": {...},
    "vwap-strategy": {...},
    "ctrader-connector": {...},
    "influxdb-connector": {...},
    
    // Add new modular servers
    "universal-backtest-engine": {...},
    "modular-chart-engine": {...}
  }
}
```

## Success Criteria
1. ✅ **Original tools still work** - No regression
2. ✅ **New modular tools available** - Additional functionality
3. ✅ **User can choose** - Use either old or new approach
4. ✅ **JSON export workflow** - Backtest → JSON → Chart pipeline works
5. ✅ **Strategy cartridge system** - Can load and run strategy cartridges

## Recovery Commands

### If Integration Fails
```bash
# Emergency rollback
git reset --hard 5d1ea87
cp claude_desktop_config.example.json "/Users/paul/Library/Application Support/Claude/claude_desktop_config.json"
```

### Continue Integration
```bash
# View stash contents
git stash list
git stash show stash@{0} --name-only

# Extract specific files
git show stash@{0}:mcp_servers/universal_backtest_mcp.py > mcp_servers/universal_backtest_v2.py
git show stash@{0}:mcp_servers/modular_chart_mcp.py > mcp_servers/modular_chart_v2.py
```

## Next Steps
1. **Test Current State**: Verify the reset worked and tools are functional
2. **Extract Key Components**: Pull the valuable parts from the stash
3. **Incremental Addition**: Add new servers alongside existing ones
4. **User Testing**: Let user test both old and new approaches
5. **Gradual Migration**: Phase out old servers only after new ones prove stable

## Lessons Learned
- ❌ **Never replace working systems entirely**
- ✅ **Add alongside existing functionality**
- ✅ **Test each component independently**
- ✅ **Keep rollback options available**
- ✅ **User choice over forced migration**

**The goal is to ADD the modular cartridge system as additional tools, not REPLACE the working system.**