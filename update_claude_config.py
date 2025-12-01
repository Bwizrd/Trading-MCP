#!/usr/bin/env python3
"""
Script to automatically update Claude Desktop configuration with Trading MCP servers.
This script will backup your existing config and install the Trading MCP servers.
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime

def get_claude_config_path():
    """Get the Claude Desktop config file path based on OS."""
    home = Path.home()
    
    if os.name == 'nt':  # Windows
        return home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    elif os.name == 'posix':
        if os.uname().sysname == 'Darwin':  # macOS
            return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        else:  # Linux
            return home / ".config" / "Claude" / "claude_desktop_config.json"
    else:
        raise OSError("Unsupported operating system")

def backup_existing_config(config_path):
    """Create a backup of the existing configuration."""
    if config_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = config_path.parent / f"claude_desktop_config_backup_{timestamp}.json"
        shutil.copy2(config_path, backup_path)
        print(f"✅ Backed up existing config to: {backup_path}")
        return backup_path
    return None

def load_existing_config(config_path):
    """Load existing configuration or create empty one."""
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️  Existing config has invalid JSON, creating new one")
            return {}
        except Exception as e:
            print(f"⚠️  Error reading existing config: {e}")
            return {}
    return {}

def get_trading_mcp_config():
    """Get the Trading MCP server configuration."""
    project_root = Path(__file__).parent.absolute()
    
    return {
        "ctrader-connector": {
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "data_connectors" / "ctrader.py")]
        },
        "influxdb-connector": {
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "data_connectors" / "influxdb.py")]
        },
        "universal-backtest-engine": {
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "universal_backtest_engine.py")]
        },
        "modular-chart-engine": {
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "modular_chart_engine.py")]
        }
    }

def verify_mcp_files():
    """Verify all MCP server files exist."""
    project_root = Path(__file__).parent.absolute()
    
    required_files = [
        "mcp_servers/data_connectors/ctrader.py",
        "mcp_servers/data_connectors/influxdb.py",
        "mcp_servers/universal_backtest_engine.py",
        "mcp_servers/modular_chart_engine.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(str(full_path))
    
    if missing_files:
        print("❌ Missing MCP server files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All MCP server files found")
    return True

def update_claude_config():
    """Main function to update Claude Desktop configuration."""
    print("🔧 Updating Claude Desktop Configuration for Trading MCP")
    print("=" * 60)
    
    # Verify MCP files exist
    if not verify_mcp_files():
        print("\n❌ Cannot proceed - missing MCP server files")
        return False
    
    # Get config path
    try:
        config_path = get_claude_config_path()
        print(f"📁 Config file location: {config_path}")
    except OSError as e:
        print(f"❌ Error: {e}")
        return False
    
    # Create config directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Backup existing config
    backup_path = backup_existing_config(config_path)
    
    # Load existing configuration
    config = load_existing_config(config_path)
    
    # Ensure mcpServers section exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Get Trading MCP configuration
    trading_mcp_config = get_trading_mcp_config()
    
    # Check for conflicts
    conflicts = []
    for server_name in trading_mcp_config.keys():
        if server_name in config["mcpServers"]:
            conflicts.append(server_name)
    
    if conflicts:
        print(f"⚠️  Found existing servers that will be overwritten: {', '.join(conflicts)}")
        response = input("Continue? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Operation cancelled")
            return False
    
    # Update configuration
    config["mcpServers"].update(trading_mcp_config)
    
    # Write updated configuration
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Configuration updated successfully!")
    except Exception as e:
        print(f"❌ Error writing config: {e}")
        return False
    
    # Show summary
    print("\n📋 Summary:")
    print(f"   - Config file: {config_path}")
    if backup_path:
        print(f"   - Backup created: {backup_path}")
    print(f"   - Added {len(trading_mcp_config)} MCP servers:")
    for server_name in trading_mcp_config.keys():
        print(f"     • {server_name}")
    
    print("\n🔄 Next Steps:")
    print("   1. Restart Claude Desktop completely")
    print("   2. Check that MCP tools are available in Claude")
    print("   3. If issues occur, restore from backup")
    
    return True

if __name__ == "__main__":
    try:
        success = update_claude_config()
        if success:
            print("\n🎉 Claude Desktop configuration updated successfully!")
        else:
            print("\n❌ Configuration update failed")
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")