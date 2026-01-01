# SSH Upload Feature for Backtest Results

This feature allows you to upload backtest trade results directly to your Windows VPS via SSH.

## Overview

When you run a backtest using the Universal Backtest Engine, the generated chart includes three buttons:
- **Download Trades as Text File** - Downloads trades locally as a text file
- **Post to Notion** - Posts results to Notion (requires Notion API setup)
- **Send to SSH** - Uploads trade results as JSON to your Windows VPS

## Setup

### 1. Configure Environment Variables

Create a `.env` file in the project root with your SSH credentials:

```bash
cd /Users/paul/Sites/PythonProjects/Trading-MCP
cp .env.example .env
```

Edit the `.env` file and add your SSH password:

```bash
# SSH Configuration
SSH_HOST=win-vps
SSH_USER=paulssh
SSH_PASSWORD=your_actual_password_here
SSH_REMOTE_PATH=C:/Users/paulssh.WIN-QL0R794UPM0/Sites/RustProjects/quad-turn-scalp/backtests/
```

**Important:** The `.env` file is git-ignored and will not be committed to version control.

### 2. Install sshpass (Required for Password Authentication)

The server uses `sshpass` to handle password-based SSH authentication:

**On macOS:**
```bash
brew install sshpass
```

**On Linux:**
```bash
sudo apt-get install sshpass
```

**Note:** If you prefer using SSH keys instead of passwords, you can skip sshpass installation and leave `SSH_PASSWORD` empty in your `.env` file.

### 3. Start the API Server

The API server handles the SSH upload. Start it in a terminal:

```bash
cd /Users/paul/Sites/PythonProjects/Trading-MCP
python api_server.py
```

You should see:
```
🚀 Starting Trading MCP API Server on http://localhost:8000
📡 Endpoints available:
   - POST /notion/backtest-result
   - POST /ssh/upload-backtest
```

**Keep this terminal running while using the upload feature.**

### 4. Verify SSH Connection (Optional)

Test that your SSH credentials work:

```bash
sshpass -p 'your_password' ssh paulssh@win-vps "dir C:\Users\paulssh.WIN-QL0R794UPM0\Sites\RustProjects\quad-turn-scalp\backtests"
```

Or if using SSH keys:
```bash
ssh paulssh@win-vps "dir C:\Users\paulssh.WIN-QL0R794UPM0\Sites\RustProjects\quad-turn-scalp\backtests"
```

## Usage

1. **Run a backtest** using your MCP client
2. **Open the generated HTML chart** in your browser
3. **Click "Send to SSH"** button
4. **Wait for confirmation**: You'll see either:
   - ✅ "Uploaded to win-vps!" (success)
   - ❌ "Error: ..." (with error details)

## File Naming

Files are saved with the format:
```
{SYMBOL}_{TIMEFRAME}_{TIMESTAMP}.json
```

Example:
```
EURUSD_30m_20260101_143022.json
```

## JSON Structure

The uploaded JSON file contains:

```json
{
  "run_id": "EURUSD_20260101_143022",
  "strategy": "Stochastic Quad Rotation",
  "symbol": "EURUSD",
  "timeframe": "30m",
  "period": "2024-01-01 to 2024-12-31",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "generated": "2026-01-01 14:30:22",
  "summary": {
    "total_trades": 45,
    "winners": 28,
    "losers": 17,
    "win_rate": "62.2%",
    "total_pips": "234.5"
  },
  "trades": [
    {
      "run_id": "EURUSD_20260101_143022",
      "number": "1",
      "entry_time": "2024-01-15 10:30:00",
      "direction": "BUY",
      "entry_price": "1.08542",
      "exit_time": "2024-01-15 11:45:00",
      "exit_price": "1.08667",
      "duration": "1:15:00",
      "pips": "+12.5",
      "exit_reason": "Take Profit"
    }
    // ... more trades
  ]
}
```

## Troubleshooting

### "Error: sshpass not found"
Install sshpass:
```bash
# macOS
brew install sshpass

# Linux
sudo apt-get install sshpass
```

### "Error: Connection timeout"
- Check that your VPS is running and accessible
- Verify the SSH_HOST in your `.env` file is correct
- Test SSH connection manually:
  ```bash
  sshpass -p 'your_password' ssh paulssh@win-vps
  ```

### "Error: Permission denied"
- Verify your SSH_PASSWORD in the `.env` file is correct
- Check that the SSH_USER is correct
- Ensure the remote directory exists and is writable

### "Error: fetch failed"
- Make sure the API server is running (`python api_server.py`)
- Check that it's listening on `http://localhost:8000`
- Check browser console for detailed error messages

### Server Not Running
If the API server crashes or stops, just restart it:
```bash
python api_server.py
```

### Password Not Being Read
- Ensure the `.env` file is in the project root directory
- Check that there are no quotes around the password in `.env`
- Restart the API server after changing `.env`

## Running the API Server in the Background

To keep the server running permanently:

### Using tmux (recommended)
```bash
tmux new -s trading-api
python api_server.py
# Press Ctrl+B, then D to detach

# To reattach later:
tmux attach -t trading-api
```

### Using nohup
```bash
nohup python api_server.py > api_server.log 2>&1 &

# To stop later:
pkill -f api_server.py
```

## Dependencies

The API server requires these Python packages:
- `fastapi`
- `uvicorn`
- `pydantic`
- `python-dotenv`

These should already be in your environment. If not:
```bash
pip install fastapi uvicorn pydantic python-dotenv
```

System dependencies:
- `sshpass` (for password-based SSH authentication)

## Security Notes

- The API server runs locally and only accepts connections from localhost
- SSH password is stored in `.env` file which is git-ignored (not committed to repository)
- Files are transferred via SCP (secure copy protocol)
- Temporary files are deleted after successful upload
- For production use, consider using SSH keys instead of passwords
- Never commit the `.env` file to version control
