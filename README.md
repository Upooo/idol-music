# IDOL Music

Simple & stable music bot for Telegram voice chats.

Built with [Pyrofork](https://github.com/Mayuri-Chan/pyrofork) + [PyTgCalls](https://github.com/pytgcalls/pytgcalls) + [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## Features

- Play music from YouTube in Telegram voice chats
- Queue system with max 5 manual requests
- Autoplay mode (toggle on/off) with smart track rotation
- Multi-language support (English + Bahasa Indonesia)
- Per-group settings stored in MongoDB
- Developer management commands (restart, pull, status, logs)
- Operational log group for monitoring
- Graceful shutdown on restart

## Commands

### Music
| Command | Description | Permission |
|---------|-------------|------------|
| `m!p <query>` / `m!play <query>` | Play or queue a track | Anyone |
| `m!s` / `m!skip` | Skip current track | Admin |
| `m!pause` | Pause playback | Admin |
| `m!resume` | Resume playback | Admin |
| `m!np` | Now playing info | Anyone |
| `m!q` / `m!queue` | View queue | Anyone |
| `m!stop` | Stop and leave VC | Admin |
| `m!leave` | Leave voice chat | Admin |
| `m!autoplay` | Toggle autoplay | Admin |

### System
| Command | Description | Permission |
|---------|-------------|------------|
| `/start` | Welcome message | Anyone |
| `m!help` | Command list | Anyone |
| `m!ping` | Bot latency | Anyone |

### Developer
| Command | Description |
|---------|-------------|
| `m!restart` | Graceful restart |
| `m!pull` | Git pull |
| `m!status` | Uptime, sessions, system info |
| `m!logs [n]` | Tail last n log lines |
| `m!bc <text>` | Broadcast to active chats |

## Setup

### Requirements
- Python 3.10+
- MongoDB (optional, for per-group settings)
- Telegram Bot Token
- Telegram API credentials (api_id + api_hash)
- Assistant account session string

### Installation

```bash
git clone https://github.com/Upooo/idol-music.git
cd idol-music
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python main.py
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram Bot API token |
| `API_ID` | Yes | Telegram API ID |
| `API_HASH` | Yes | Telegram API hash |
| `ASSISTANT_SESSION` | Yes | Pyrogram session string for the assistant account |
| `DEVELOPER_ID` | Yes | Your Telegram user ID |
| `MONGO_URI` | No | MongoDB connection string |
| `LOG_GROUP_ID` | No | Telegram group/channel ID for bot logs |

## Project Structure

```
idol-music/
├── main.py              # Entry point
├── config.py            # Configuration loader
├── bot/
│   └── clients.py       # Pyrogram + PyTgCalls factory
├── music/
│   ├── player.py        # Voice chat player (state machine)
│   ├── session.py       # Per-group music session
│   ├── queue.py         # Async FIFO queue
│   ├── source.py        # yt-dlp integration
│   ├── track.py         # Track dataclass
│   └── manager.py       # Session registry
├── handlers/
│   ├── system.py        # /start, m!help, m!ping
│   ├── music.py         # Music commands
│   └── developer.py     # Developer commands
├── filters/
│   ├── prefix.py        # m! prefix filter
│   └── permissions.py   # Permission helpers
├── strings/
│   ├── __init__.py      # Language loader
│   ├── en.py            # English strings
│   └── id.py            # Indonesian strings
├── db/
│   ├── client.py        # MongoDB connection
│   └── models.py        # Group settings CRUD
└── utils/
    └── log_group.py     # Telegram log group
```

## License

MIT
