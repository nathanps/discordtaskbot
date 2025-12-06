# Discord Task Bot

A simple task management bot for Discord that stores tasks in git-tracked CSV files. Perfect for self-hosting on a NAS or VPS.

## Features

- Create, assign, and track tasks with slash commands
- Tasks stored in CSV files (easy to backup, version controlled)
- Multi-server support (each Discord server gets isolated tasks)
- Git integration for automatic backups and sync
- Works great on Synology, QNAP, or any NAS with Docker

## Commands

| Command | Description |
|---------|-------------|
| `/task <description> [category]` | Create a new task |
| `/tasklist [filter] [limit]` | List tasks (filter: done, all, or category) |
| `/taskmine [limit]` | List tasks assigned to you |
| `/taskdone <id>` | Mark task as done |
| `/taskprogress <id>` | Mark task as in-progress (assigns to you) |
| `/taskassign <id> <user>` | Assign task to someone |
| `/tasknote <id> <note>` | Add a note to a task |
| `/taskdelete <id>` | Delete a task |
| `/taskconfig <channel>` | Set channel for update notifications |

## Quick Start

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** and give it a name
3. Go to **Bot** section → **Add Bot**
4. Copy the bot token (save it for later)
5. Go to **OAuth2** → **URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Permissions: `Send Messages`, `Use Slash Commands`
6. Open the generated URL to invite the bot to your server

### 2. Deploy the Bot

Choose one of the methods below:

---

## Option A: Docker (Recommended)

Best for NAS devices (Synology, QNAP, etc.) or any server with Docker.

### Setup

```bash
# Clone this repo
git clone https://github.com/yourusername/discord-task-bot.git
cd discord-task-bot

# Create data directory
mkdir -p data/servers
cd data && git init && git config user.email "bot@localhost" && git config user.name "TaskBot" && cd ..

# Configure
cp .env.example .env
# Edit .env and add your DISCORD_TOKEN

# Run
docker-compose up -d
```

### Synology NAS

1. Install **Container Manager** from Package Center
2. Create a folder for the bot (e.g., `/volume1/docker/taskbot`)
3. Upload all files to that folder
4. Open Container Manager → **Project** → **Create**
5. Select the folder, set `DISCORD_TOKEN` in environment
6. Start the project

### Updating

```bash
docker-compose down
git pull
docker-compose up -d --build
```

---

## Option B: Python (Direct)

For running directly without Docker.

### Requirements

- Python 3.10+
- Git

### Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/discord-task-bot.git
cd discord-task-bot

# Run setup script
# Linux/Mac:
chmod +x setup.sh && ./setup.sh

# Windows (PowerShell):
.\setup.ps1
```

Or manually:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your token and data path

# Initialize data directory
mkdir -p /path/to/data/servers
cd /path/to/data
git init
git config user.email "bot@localhost"
git config user.name "TaskBot"

# Run
python bot.py
```

### Running as a Service (Linux)

Create `/etc/systemd/system/taskbot.service`:

```ini
[Unit]
Description=Discord Task Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/discord-task-bot
ExecStart=/path/to/discord-task-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable taskbot
sudo systemctl start taskbot
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_TOKEN` | Yes | - | Bot token from Discord Developer Portal |
| `REPO_PATH` | No | `.` | Path to data directory (git repo) |
| `CSV_FILENAME` | No | `tasks.csv` | Filename for task files |

### Data Structure

```
REPO_PATH/
  config.json              # Server settings
  servers/
    123456789/             # Discord server ID
      tasks.csv            # Tasks for this server
    987654321/
      tasks.csv
```

---

## Backup & Restore

Your data is just files in a git repository. To backup:

```bash
# Copy the data folder
cp -r /path/to/data /path/to/backup

# Or push to a remote (if configured)
cd /path/to/data
git remote add origin your-backup-repo
git push -u origin main
```

---

## Troubleshooting

### Commands not showing up

- Wait a few minutes after first run (Discord caches commands)
- Make sure the bot has `applications.commands` scope

### Git errors

```bash
cd /path/to/data
git config user.email "bot@localhost"
git config user.name "TaskBot"
```

### Permission errors

Ensure the bot process can read/write the data directory.

---

## License

MIT License - feel free to use and modify.
