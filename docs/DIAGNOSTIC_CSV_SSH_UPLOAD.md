# Diagnostic CSV SSH Upload Feature

## Overview

This feature allows you to automatically upload diagnostic CSV files to a remote Windows VPS via SSH directly from the backtest chart HTML interface.

## How It Works

### 1. Enable Diagnostics

Set the environment variable in your `.env` file:

```bash
BACKTEST_DIAGNOSTICS=true
```

### 2. Run a Backtest

When you run a backtest with diagnostics enabled, the system will:
- Generate the normal backtest results and chart
- Create a detailed diagnostic CSV file with OHLCV data, all indicators, and trade markers
- Store the CSV path in the `BacktestResults` object

### 3. Upload via Button

In the generated HTML chart, you'll see a **"📊 Send Diagnostic CSV"** button (only appears when diagnostics are enabled).

Click the button to:
- Upload the diagnostic CSV to your remote Windows VPS
- Save it to: `C:\Users\paulssh.WIN-QL0R794UPM0\Sites\RustProjects\quad-turn-scalp\diagnostics\`
- Use a clean filename format: `diagnostic_SYMBOL_YYYYMMDD.csv`

## SSH Configuration

Configure SSH settings in your `.env` file:

```bash
# SSH Configuration
SSH_HOST=win-vps
SSH_USER=paulssh
SSH_PASSWORD=your_password_here
SSH_DIAGNOSTIC_PATH=C:/Users/paulssh.WIN-QL0R794UPM0/Sites/RustProjects/quad-turn-scalp/diagnostics/
```

**Note:** The `SSH_DIAGNOSTIC_PATH` environment variable is optional. If not set, it defaults to the path above.

## API Server

Make sure the API server is running:

```bash
python api_server.py
```

The server will start on `http://localhost:8001` and provides three endpoints:
- `POST /notion/backtest-result` - Post results to Notion
- `POST /ssh/upload-backtest` - Upload backtest JSON to VPS
- `POST /ssh/upload-diagnostic-csv` - Upload diagnostic CSV to VPS

## Button Behavior

The diagnostic button:
- Only appears when diagnostics are enabled and a CSV was generated
- Shows upload progress with status messages
- Displays success (✅) or error (❌) feedback
- Automatically re-enables after 3 seconds on success

## Example Workflow

1. Set `BACKTEST_DIAGNOSTICS=true` in `.env`
2. Run backtest: `mcp_universalback_run_strategy_backtest`
3. Open the generated HTML chart
4. Review the diagnostic CSV locally if needed
5. Click "📊 Send Diagnostic CSV" button
6. CSV is uploaded to Windows VPS diagnostics folder
7. Analyze on remote machine using Excel, Rust tools, etc.

## File Naming

Diagnostic CSV files are named with a clean format:
- Local: `diagnostic_NAS100_Stochastic_Quad_Rotation_20251231_174455.csv`
- Remote: `diagnostic_NAS100_20251231.csv` (simplified for easier access)

The remote filename:
- Removes the strategy name for brevity
- Uses date stamp for organization
- Automatically overwrites files from the same symbol/date

## Benefits

✅ **No manual file transfer** - Upload with one click  
✅ **Clean filenames** - Easy to find and organize  
✅ **Date-based naming** - Track historical analysis  
✅ **Instant feedback** - Know immediately if upload succeeded  
✅ **Integrated workflow** - Everything in one HTML interface

## Troubleshooting

### Button doesn't appear
- Ensure `BACKTEST_DIAGNOSTICS=true` in `.env`
- Verify MCP server loaded the `.env` file (restart if needed)
- Check that diagnostic CSV was actually created

### Upload fails
- Ensure API server is running: `python api_server.py`
- Check SSH credentials in `.env` file
- Verify SSH host is reachable
- Check remote directory exists and has write permissions

### SSH timeout
- Increase timeout in `api_server.py` if needed
- Check network connectivity
- Verify SSH password is correct

## Code Changes

The feature required changes to:

1. **`shared/strategy_interface.py`** - Added `diagnostic_csv_path` field to `BacktestResults`
2. **`shared/backtest_engine.py`** - Store diagnostic CSV path in results
3. **`api_server.py`** - Added `/ssh/upload-diagnostic-csv` endpoint
4. **`shared/chart_engine.py`** - Added button and JavaScript for upload

All changes are backward compatible - existing code continues to work without diagnostics enabled.
