# SSH Upload - Quick Start Guide

Get your backtest results uploading to your Windows VPS in 5 minutes!

## Quick Setup (3 Steps)

### Step 1: Run the Setup Script

```bash
cd /Users/paul/Sites/PythonProjects/Trading-MCP
./setup_ssh_upload.sh
```

This will:
- Create your `.env` file
- Prompt for SSH credentials
- Check dependencies
- Install missing packages (if you confirm)

**OR manually:**

```bash
# Copy the example env file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

Add your password to `.env`:
```
SSH_PASSWORD=your_actual_password
```

### Step 2: Install sshpass (if needed)

```bash
brew install sshpass
```

### Step 3: Start the API Server

```bash
python api_server.py
```

Keep this terminal running!

## Usage

1. Run a backtest (any strategy)
2. Open the generated HTML chart
3. Click the **"🚀 Send to SSH"** button
4. Wait for confirmation: ✅ "Uploaded to win-vps!"

## What Gets Uploaded?

**File Name Format:**
```
{SYMBOL}_{TIMEFRAME}_{TIMESTAMP}.json
```

Example: `EURUSD_30m_20260101_143022.json`

**Uploaded To:**
```
C:\Users\paulssh.WIN-QL0R794UPM0\Sites\RustProjects\quad-turn-scalp\backtests\
```

**File Contents:**
- Run metadata (symbol, timeframe, dates, strategy)
- Summary statistics (win rate, total pips, etc.)
- Complete trade list with entry/exit data

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "sshpass not found" | `brew install sshpass` |
| "Connection timeout" | Check VPS is running, verify .env credentials |
| "Permission denied" | Check SSH_PASSWORD in .env is correct |
| "Fetch failed" | Ensure API server is running on port 8000 |

## Advanced: Run Server in Background

### Using tmux (Recommended)

```bash
# Start
tmux new -s trading-api
python api_server.py
# Press Ctrl+B, then D to detach

# Resume later
tmux attach -t trading-api
```

### Using nohup

```bash
# Start in background
nohup python api_server.py > api_server.log 2>&1 &

# Stop
pkill -f api_server.py
```

## Environment Variables Reference

All variables in `.env`:

```bash
# Required
SSH_PASSWORD=your_password_here

# Optional (have sensible defaults)
SSH_HOST=win-vps
SSH_USER=paulssh
SSH_REMOTE_PATH=C:/Users/paulssh.WIN-QL0R794UPM0/Sites/RustProjects/quad-turn-scalp/backtests/
```

## File Structure

```
Trading-MCP/
├── .env                    # Your SSH credentials (git-ignored)
├── .env.example            # Template for .env
├── api_server.py           # FastAPI server (handles uploads)
├── setup_ssh_upload.sh     # Automated setup script
├── SSH_UPLOAD_GUIDE.md     # Detailed documentation
└── SSH_UPLOAD_QUICKSTART.md # This file
```

## Security

- ✅ `.env` is git-ignored (never committed)
- ✅ API server only accepts local connections
- ✅ Files transferred via encrypted SCP
- ✅ Temp files deleted after upload

## Need More Help?

See the full documentation: [SSH_UPLOAD_GUIDE.md](SSH_UPLOAD_GUIDE.md)
