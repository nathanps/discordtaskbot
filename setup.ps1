# Discord Task Bot - Setup Script for Windows
# Run this script in PowerShell to set up the bot

$ErrorActionPreference = "Stop"

Write-Host "Discord Task Bot - Setup Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Write-Host "Error: Python 3.10+ required. Found: $pythonVersion" -ForegroundColor Red
            exit 1
        }
        Write-Host "  Found: $pythonVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "Error: Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check git
Write-Host "Checking Git installation..." -ForegroundColor Yellow
try {
    $gitVersion = git --version 2>&1
    Write-Host "  Found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Git not found. Please install Git." -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "  Created venv/" -ForegroundColor Green
} else {
    Write-Host "  venv/ already exists" -ForegroundColor Green
}

# Activate and install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
pip install -r requirements.txt | Out-Null
Write-Host "  Dependencies installed" -ForegroundColor Green

# Create .env if it doesn't exist
Write-Host ""
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"

    $token = Read-Host "Enter your Discord bot token"
    $repoPath = Read-Host "Enter data directory path (or press Enter for current directory)"

    if ([string]::IsNullOrWhiteSpace($repoPath)) {
        $repoPath = "."
    }

    $envContent = @"
DISCORD_TOKEN=$token
REPO_PATH=$repoPath
CSV_FILENAME=tasks.csv
"@
    Set-Content -Path ".env" -Value $envContent
    Write-Host "  Created .env" -ForegroundColor Green
} else {
    Write-Host ".env already exists" -ForegroundColor Green
}

# Initialize data directory
Write-Host ""
Write-Host "Setting up data directory..." -ForegroundColor Yellow

# Read REPO_PATH from .env
$envContent = Get-Content ".env" -Raw
if ($envContent -match 'REPO_PATH=(.+)') {
    $repoPath = $Matches[1].Trim()
    if ($repoPath -eq ".") {
        $repoPath = $PWD
    }

    $serversDir = Join-Path $repoPath "servers"
    if (-not (Test-Path $serversDir)) {
        New-Item -ItemType Directory -Path $serversDir -Force | Out-Null
        Write-Host "  Created servers/ directory" -ForegroundColor Green
    }

    # Initialize git if needed
    $gitDir = Join-Path $repoPath ".git"
    if (-not (Test-Path $gitDir)) {
        Push-Location $repoPath
        git init | Out-Null
        git config user.email "bot@localhost"
        git config user.name "TaskBot"
        Pop-Location
        Write-Host "  Initialized git repository" -ForegroundColor Green
    } else {
        Write-Host "  Git repository already initialized" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To run the bot:" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\Activate.ps1"
Write-Host "  python bot.py"
