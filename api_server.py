"""
FastAPI server to handle backtest results uploads.
Supports Notion integration and SSH file transfer.
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import pexpect

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Trading MCP API Server")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BacktestResult(BaseModel):
    """Backtest result payload model."""
    run_id: str
    strategy: str
    symbol: str
    timeframe: str
    period: str
    start_date: str
    end_date: str
    generated: str
    summary: Dict[str, Any]
    trades: list


@app.post("/notion/backtest-result")
async def post_to_notion(result: BacktestResult):
    """
    Handle Notion backtest result posting.
    Currently a placeholder - implement Notion API integration as needed.
    """
    try:
        print(f"📝 Received Notion post request for {result.symbol} - {result.strategy}")
        print(f"   Total trades: {result.summary.get('total_trades', 0)}")
        print(f"   Win rate: {result.summary.get('win_rate', 'N/A')}")

        # TODO: Implement actual Notion API integration
        # For now, just return success
        return {
            "status": "success",
            "message": "Posted to Notion (placeholder)",
            "run_id": result.run_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ssh/upload-backtest")
async def upload_to_ssh(result: BacktestResult):
    """
    Upload backtest results to Windows VPS via SSH.

    Reads SSH credentials from environment variables:
    - SSH_HOST: SSH host (default: win-vps)
    - SSH_USER: SSH username (default: paulssh)
    - SSH_PASSWORD: SSH password (required if not using keys)
    - SSH_REMOTE_PATH: Remote path on Windows VPS
    """
    try:
        # Get SSH configuration from environment variables
        ssh_host = os.getenv("SSH_HOST", "win-vps")
        ssh_user = os.getenv("SSH_USER", "paulssh")
        ssh_password = os.getenv("SSH_PASSWORD")
        ssh_remote_path = os.getenv(
            "SSH_REMOTE_PATH",
            "C:/Users/paulssh.WIN-QL0R794UPM0/Sites/RustProjects/quad-turn-scalp/backtests/"
        )

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{result.symbol}_{result.timeframe}_{timestamp}.json"

        # Create temporary local file
        temp_dir = Path("/tmp/trading_uploads")
        temp_dir.mkdir(exist_ok=True)
        local_file = temp_dir / filename

        # Write JSON data
        with open(local_file, 'w') as f:
            json.dump(result.dict(), f, indent=2, default=str)

        print(f"📤 Uploading {filename} to {ssh_host}...")
        print(f"   Using SCP command: scp {local_file} {ssh_host}:{ssh_remote_path}{filename}")

        # Simple approach: just run scp and handle password interactively
        scp_command = f"scp {local_file} {ssh_host}:{ssh_remote_path}{filename}"

        try:
            print(f"   Spawning SCP process...")
            child = pexpect.spawn(scp_command, timeout=30, encoding='utf-8')

            # Enable logging to see what SSH is actually saying
            import sys
            child.logfile_read = sys.stdout

            print(f"   Waiting for password/passphrase prompt or completion...")

            # Wait for password/passphrase prompt or completion
            index = child.expect(['password:', 'Password:', 'passphrase', 'Passphrase', pexpect.EOF, pexpect.TIMEOUT], timeout=30)

            if index in [0, 1, 2, 3]:
                # Password or passphrase prompt received
                print(f"   Password/passphrase prompt detected, sending credentials...")
                child.sendline(ssh_password)
                # Wait for transfer to complete
                child.expect(pexpect.EOF, timeout=30)
            elif index == 4:
                # EOF - command completed (probably using SSH keys)
                print(f"   Transfer completed (no password needed)")
            else:
                # Timeout
                print(f"   Timeout waiting for password prompt")
                raise Exception("SSH connection timeout")

            child.close()

            if child.exitstatus == 0:
                print(f"✅ Successfully uploaded {filename}")
                # Clean up temp file
                local_file.unlink()

                return {
                    "status": "success",
                    "message": f"Successfully uploaded to {ssh_host}",
                    "filename": filename,
                    "remote_path": f"{ssh_remote_path}{filename}"
                }
            else:
                error_msg = f"SCP failed with exit code {child.exitstatus}"
                print(f"❌ {error_msg}")
                raise HTTPException(status_code=500, detail=error_msg)

        except pexpect.TIMEOUT:
            print(f"❌ Upload timeout")
            raise HTTPException(status_code=504, detail="SSH connection timeout")
        except pexpect.EOF:
            print(f"❌ Unexpected EOF")
            raise HTTPException(status_code=500, detail="SSH connection closed unexpectedly")

    except FileNotFoundError as e:
        if "sshpass" in str(e):
            raise HTTPException(
                status_code=500,
                detail="sshpass not found. Install it with: brew install sshpass (macOS) or apt-get install sshpass (Linux)"
            )
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="SSH connection timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


class DiagnosticUploadRequest(BaseModel):
    """Diagnostic CSV upload request model."""
    csv_path: str
    symbol: str
    strategy: str
    date: str  # YYYY-MM-DD format


@app.post("/ssh/upload-diagnostic-csv")
async def upload_diagnostic_csv(request: DiagnosticUploadRequest):
    """
    Upload diagnostic CSV file to Windows VPS via SSH.
    
    Uploads the diagnostic CSV to the diagnostics folder on the remote server.
    Remote path: C:/Users/paulssh.WIN-QL0R794UPM0/Sites/RustProjects/quad-turn-scalp/diagnostics/
    """
    try:
        # Resolve path (handle both relative and absolute paths)
        local_file = Path(request.csv_path)
        if not local_file.is_absolute():
            # If relative, make it relative to project root
            project_root = Path(__file__).parent
            local_file = project_root / request.csv_path
        
        if not local_file.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.csv_path}")
        
        # Get SSH configuration from environment variables
        ssh_host = os.getenv("SSH_HOST", "win-vps")
        ssh_user = os.getenv("SSH_USER", "paulssh")
        ssh_password = os.getenv("SSH_PASSWORD")
        ssh_remote_path = os.getenv(
            "SSH_DIAGNOSTIC_PATH",
            "C:/Users/paulssh.WIN-QL0R794UPM0/Sites/RustProjects/quad-turn-scalp/diagnostics/"
        )
        
        # Generate filename matching local format
        # Format: diagnostic_SYMBOL_STRATEGY_YYYYMMDD_HHMMSS.csv
        # Extract timestamp from original filename if possible, otherwise use current time
        original_filename = local_file.name
        if '_' in original_filename:
            # Try to extract timestamp from original filename
            parts = original_filename.replace('.csv', '').split('_')
            if len(parts) >= 3:
                # Has format: diagnostic_SYMBOL_STRATEGY_TIMESTAMP.csv
                filename = original_filename
            else:
                # Fallback: create new filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                clean_symbol = request.symbol.replace('_SB', '').replace('_', '')
                clean_strategy = request.strategy.replace(' ', '_')
                filename = f"diagnostic_{clean_symbol}_{clean_strategy}_{timestamp}.csv"
        else:
            # Fallback: create new filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_symbol = request.symbol.replace('_SB', '').replace('_', '')
            clean_strategy = request.strategy.replace(' ', '_')
            filename = f"diagnostic_{clean_symbol}_{clean_strategy}_{timestamp}.csv"
        
        print(f"📤 Uploading diagnostic CSV {filename} to {ssh_host}...")
        print(f"   Local file: {local_file}")
        print(f"   Remote path: {ssh_remote_path}{filename}")
        
        # Use SCP to upload the file
        scp_command = f"scp {local_file} {ssh_host}:{ssh_remote_path}{filename}"
        
        try:
            print(f"   Spawning SCP process...")
            child = pexpect.spawn(scp_command, timeout=30, encoding='utf-8')
            
            # Enable logging
            import sys
            child.logfile_read = sys.stdout
            
            print(f"   Waiting for password/passphrase prompt or completion...")
            
            # Wait for password/passphrase prompt or completion
            index = child.expect(['password:', 'Password:', 'passphrase', 'Passphrase', pexpect.EOF, pexpect.TIMEOUT], timeout=30)
            
            if index in [0, 1, 2, 3]:
                # Password or passphrase prompt received
                print(f"   Password/passphrase prompt detected, sending credentials...")
                child.sendline(ssh_password)
                # Wait for transfer to complete
                child.expect(pexpect.EOF, timeout=30)
            elif index == 4:
                # EOF - command completed (probably using SSH keys)
                print(f"   Transfer completed (no password needed)")
            else:
                # Timeout
                print(f"   Timeout waiting for password prompt")
                raise Exception("SSH connection timeout")
            
            child.close()
            
            if child.exitstatus == 0:
                print(f"✅ Successfully uploaded diagnostic CSV: {filename}")
                
                return {
                    "status": "success",
                    "message": f"Successfully uploaded diagnostic CSV to {ssh_host}",
                    "filename": filename,
                    "remote_path": f"{ssh_remote_path}{filename}"
                }
            else:
                error_msg = f"SCP failed with exit code {child.exitstatus}"
                print(f"❌ {error_msg}")
                raise HTTPException(status_code=500, detail=error_msg)
        
        except pexpect.TIMEOUT:
            print(f"❌ Upload timeout")
            raise HTTPException(status_code=504, detail="SSH connection timeout")
        except pexpect.EOF:
            print(f"❌ Unexpected EOF")
            raise HTTPException(status_code=500, detail="SSH connection closed unexpectedly")
    
    except FileNotFoundError as e:
        if "sshpass" in str(e):
            raise HTTPException(
                status_code=500,
                detail="sshpass not found. Install it with: brew install sshpass (macOS) or apt-get install sshpass (Linux)"
            )
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="SSH connection timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Trading MCP API Server",
        "status": "running",
        "endpoints": [
            "/notion/backtest-result",
            "/ssh/upload-backtest",
            "/ssh/upload-diagnostic-csv"
        ]
    }


if __name__ == "__main__":
    print("🚀 Starting Trading MCP API Server on http://localhost:8001")
    print("📡 Endpoints available:")
    print("   - POST /notion/backtest-result")
    print("   - POST /ssh/upload-backtest")
    print("   - POST /ssh/upload-diagnostic-csv")
    uvicorn.run(app, host="0.0.0.0", port=8001)
