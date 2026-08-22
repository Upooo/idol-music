# IDOL Music

Telegram voice chat music bot — inspired by Jockie Music.

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in .env
python main.py
```

## Requirements

- Python 3.10+
- FFmpeg installed on system
- Telegram Bot Token
- Telegram API ID & Hash
- Assistant session string (Pyrogram userbot)

## Commands

- `m!p [title]` — Play or queue a track
- `m!s` — Skip
- `m!q` — Queue
- `m!np` — Now playing
- `m!pause` / `m!resume` — Pause/Resume
- `m!stop` — Stop and clear
- `m!leave` — Leave voice chat

## Phase 1 Status

Foundation — hardcoded audio for stack verification.

Acceptance tests:
1. Assistant joins VC → plays audio → stops → leaves
2. Pause → resume works
3. Two groups simultaneously, independent sessions
4. Stream-ended event detected correctly
