#!/bin/bash

# Setup script for SSH Upload feature
# This script helps configure the SSH upload functionality

echo "🚀 Setting up SSH Upload Feature for Trading MCP"
echo "================================================"
echo ""

# Check if .env file exists
if [ -f ".env" ]; then
    echo "✅ .env file already exists"
    read -p "Do you want to update it? (y/N): " update_env
    if [[ ! $update_env =~ ^[Yy]$ ]]; then
        echo "Skipping .env configuration..."
    else
        cp .env .env.backup
        echo "📦 Backed up existing .env to .env.backup"
    fi
else
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
fi

# Prompt for SSH credentials if updating
if [[ $update_env =~ ^[Yy]$ ]] || [ ! -f ".env" ]; then
    echo ""
    echo "Please enter your SSH credentials:"
    read -p "SSH Host [win-vps]: " ssh_host
    ssh_host=${ssh_host:-win-vps}

    read -p "SSH User [paulssh]: " ssh_user
    ssh_user=${ssh_user:-paulssh}

    read -sp "SSH Password: " ssh_password
    echo ""

    read -p "Remote Path [C:/Users/paulssh.WIN-QL0R794UPM0/Sites/RustProjects/quad-turn-scalp/backtests/]: " remote_path
    remote_path=${remote_path:-C:/Users/paulssh.WIN-QL0R794UPM0/Sites/RustProjects/quad-turn-scalp/backtests/}

    # Update .env file
    sed -i.bak "s|SSH_HOST=.*|SSH_HOST=$ssh_host|" .env
    sed -i.bak "s|SSH_USER=.*|SSH_USER=$ssh_user|" .env
    sed -i.bak "s|SSH_PASSWORD=.*|SSH_PASSWORD=$ssh_password|" .env
    sed -i.bak "s|SSH_REMOTE_PATH=.*|SSH_REMOTE_PATH=$remote_path|" .env
    rm .env.bak

    echo "✅ Updated .env file with your credentials"
fi

echo ""
echo "Checking dependencies..."
echo "========================"

# Check for Python packages
echo "Checking Python packages..."
python3 -c "import fastapi" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ fastapi installed"
else
    echo "❌ fastapi not found"
    echo "   Install with: pip install fastapi"
    missing_deps=true
fi

python3 -c "import uvicorn" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ uvicorn installed"
else
    echo "❌ uvicorn not found"
    echo "   Install with: pip install uvicorn"
    missing_deps=true
fi

python3 -c "import dotenv" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ python-dotenv installed"
else
    echo "❌ python-dotenv not found"
    echo "   Install with: pip install python-dotenv"
    missing_deps=true
fi

# Check for sshpass
command -v sshpass >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ sshpass installed"
else
    echo "❌ sshpass not found"
    echo "   Install with: brew install sshpass (macOS) or apt-get install sshpass (Linux)"
    missing_deps=true
fi

if [ "$missing_deps" = true ]; then
    echo ""
    echo "⚠️  Some dependencies are missing. Please install them before running the API server."
    echo ""
    read -p "Install missing Python packages now? (y/N): " install_packages
    if [[ $install_packages =~ ^[Yy]$ ]]; then
        pip install fastapi uvicorn python-dotenv pydantic
    fi
else
    echo ""
    echo "✅ All dependencies are installed!"
fi

echo ""
echo "Setup complete! 🎉"
echo "================"
echo ""
echo "Next steps:"
echo "1. Review your .env file to ensure credentials are correct"
echo "2. Start the API server: python api_server.py"
echo "3. Run a backtest and click the 'Send to SSH' button"
echo ""
echo "For more information, see: SSH_UPLOAD_GUIDE.md"
