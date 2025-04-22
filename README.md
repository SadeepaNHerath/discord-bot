# Discord Bot

A feature-rich Discord bot with moderation, voice, and general utility commands built with NextCord.

## Features

- **Voice Commands**: Play music, manage queues, control volume, and more
- **Moderation**: Kick, ban, and unban users
- **Utility**: Welcome messages, daily motivational messages, and more

## Requirements

- Python 3.12+
- Poetry for dependency management
- Discord Bot Token
- RapidAPI Key (for joke API)

## Installation

1. Clone the repository
2. Create a `.env` file with required environment variables
3. Install dependencies with Poetry:

```bash
poetry install
```

4. Run the bot:

```bash
poetry run python main.py
```

## Environment Variables

Create a `.env` file with the following variables:

```
DISCORD_BOT=your_bot_token
MENTOR_ID=mentor_user_id
MY_ID=your_discord_id
CHANNEL_ID=announcement_channel_id
DISCORD_SERVER_ID=your_server_id
RAPIDAPI_KEY=your_rapidapi_key
```

## Commands

### Voice Commands
- `!join` - Join a voice channel
- `!leave` - Leave the voice channel
- `!play [song]` - Play a song
- `!queue [song]` - Add song to queue
- `!pause` - Pause current playback
- `!resume` - Resume playback
- `!skip` - Skip current song
- `!stop` - Stop playback
- `!volume [0-100]` - Set volume
- `!nowplaying` - Show current song
- `!viewqueue` - View song queue
- `!clearqueue` - Clear song queue

### Moderation Commands
- `!kick [user] [reason]` - Kick a user
- `!ban [user] [reason]` - Ban a user
- `!unban [user]` - Unban a user

## License

[MIT](LICENSE)
