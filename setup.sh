#!/bin/bash
# Discord Task Bot - Setup Script for Linux/Mac

set -e

echo "Discord Task Bot - Setup Script"
echo "================================"
echo ""

# Check Python version
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo "Error: Python 3.10+ required. Found: Python $PYTHON_VERSION"
    exit 1
fi
echo "  Found: Python $PYTHON_VERSION"

# Check git
echo "Checking Git installation..."
if ! command -v git &> /dev/null; then
    echo "Error: Git not found. Please install Git."
    exit 1
fi
echo "  Found: $(git --version)"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    echo "  Created venv/"
else
    echo "  venv/ already exists"
fi

# Activate and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt > /dev/null
echo "  Dependencies installed"

# Create .env if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env

    read -p "Enter your Discord bot token: " TOKEN
    read -p "Enter data directory path (or press Enter for current directory): " REPO_PATH

    if [ -z "$REPO_PATH" ]; then
        REPO_PATH="."
    fi

    cat > .env << EOF
DISCORD_TOKEN=$TOKEN
REPO_PATH=$REPO_PATH
CSV_FILENAME=tasks.csv
EOF
    echo "  Created .env"
else
    echo ".env already exists"
fi

# Initialize data directory
echo ""
echo "Setting up data directory..."

# Read REPO_PATH from .env
REPO_PATH=$(grep "REPO_PATH=" .env | cut -d= -f2)
if [ "$REPO_PATH" = "." ]; then
    REPO_PATH=$(pwd)
fi

SERVERS_DIR="$REPO_PATH/servers"
if [ ! -d "$SERVERS_DIR" ]; then
    mkdir -p "$SERVERS_DIR"
    echo "  Created servers/ directory"
fi

# Initialize git if needed
if [ ! -d "$REPO_PATH/.git" ]; then
    pushd "$REPO_PATH" > /dev/null
    git init > /dev/null
    git config user.email "bot@localhost"
    git config user.name "TaskBot"
    popd > /dev/null
    echo "  Initialized git repository"
else
    echo "  Git repository already initialized"
fi

echo ""
echo "Setup complete!"
echo ""
echo "To run the bot:"
echo "  source venv/bin/activate"
echo "  python bot.py"
