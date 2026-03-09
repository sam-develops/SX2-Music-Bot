# 🎵 SX2 Music Bot

> A feature-rich Discord music bot built with Python, discord.py, and Supabase.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![discord.py](https://img.shields.io/badge/discord.py-2.0%2B-5865F2?style=for-the-badge&logo=discord)
![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?style=for-the-badge&logo=supabase)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## ✨ Features

- 🎵 **YouTube Music Streaming** — Play any song by name or URL
- 📋 **Queue System** — Line up multiple songs
- 🔁 **Loop & Shuffle** — Repeat or randomize your queue
- 🎵 **Autoplay** — Auto-suggests related songs when queue ends
- ⏱️ **Seek** — Jump to any timestamp in a song
- 🔊 **Volume Control** — Adjust playback volume (0–100%)
- 🎶 **Lyrics** — Fetch lyrics for any song via Genius
- 💾 **Playlists** — Save and load personal playlists (stored in Supabase)
- 🏆 **Stats** — Track most played songs and top users per server
- 📖 **Help Menu** — Beautiful categorised slash command help system

---

## 📁 Project Structure

```
📁 SX2 Music/
├── 📄 bot.py              ← Main entry point
├── 📄 .env                ← Secret tokens (never upload this!)
├── 📄 .gitignore          ← Keeps secrets out of GitHub
└── 📁 cogs/
    ├── 📄 __init__.py
    ├── 📄 music.py        ← Core music commands
    ├── 📄 lyrics.py       ← Lyrics fetching
    ├── 📄 playlist.py     ← Playlist management (Supabase)
    ├── 📄 stats.py        ← Music stats tracking (Supabase)
    └── 📄 help.py         ← Help & about commands
```

---

## 🚀 Getting Started

### Prerequisites

Make sure you have these installed:

- [Python 3.10+](https://python.org)
- [FFmpeg](https://ffmpeg.org/download.html) — added to system PATH
- A [Discord Developer Account](https://discord.com/developers/applications)
- A [Supabase Account](https://supabase.com) (free)
- A [Genius API Account](https://genius.com/api-clients) (free)

---

### 📦 Installation

**1. Clone the repository**
```bash
git clone https://github.com/sam-develops/SX2-Music-Bot.git
cd SX2-Music-Bot
```

**2. Install dependencies**
```bash
pip install discord.py[voice]
pip install yt-dlp
pip install PyNaCl
pip install python-dotenv
pip install lyricsgenius
pip install supabase==1.2.0
pip install httpx==0.24.1
pip install gotrue==1.3.0
pip install websockets==13.1
```

**3. Set up your `.env` file**

Create a `.env` file in the root folder:
```
DISCORD_TOKEN=your_discord_bot_token
GENIUS_TOKEN=your_genius_api_token
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

**4. Set up Supabase Database**

Run these SQL queries in your Supabase SQL editor:

```sql
-- Playlists
CREATE TABLE playlists (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, name)
);

CREATE TABLE playlist_songs (
    id BIGSERIAL PRIMARY KEY,
    playlist_id BIGINT REFERENCES playlists(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    position INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT NOW()
);

-- Stats
CREATE TABLE song_stats (
    id BIGSERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    song_title TEXT NOT NULL,
    play_count INTEGER DEFAULT 1,
    last_played TIMESTAMP DEFAULT NOW(),
    UNIQUE(guild_id, song_title)
);

CREATE TABLE user_stats (
    id BIGSERIAL PRIMARY KEY,
    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    request_count INTEGER DEFAULT 0,
    UNIQUE(guild_id, user_id)
);
```

**5. Run the bot**
```bash
python bot.py
```

You should see:
```
✅ Loaded cog: help.py
✅ Loaded cog: lyrics.py
✅ Loaded cog: music.py
✅ Loaded cog: playlist.py
✅ Loaded cog: stats.py
✅ Synced slash commands!
✅ Logged in as SX2 Music Bot#1234
```

---

## 🎮 Commands

### 🎵 Music
| Command | Description |
|---|---|
| `/play <song>` | Play a song or add to queue |
| `/pause` | Pause the current song |
| `/resume` | Resume a paused song |
| `/skip` | Skip to the next song |
| `/stop` | Stop music and clear queue |
| `/leave` | Bot leaves voice channel |

### 📋 Queue
| Command | Description |
|---|---|
| `/queue` | View the current queue |
| `/remove <position>` | Remove a song from queue |
| `/jumpto <position>` | Jump to a specific song |
| `/shuffle` | Shuffle the queue |
| `/nowplaying` | Show current song info card |

### 🎛️ Controls
| Command | Description |
|---|---|
| `/volume <0-100>` | Set the volume |
| `/loop` | Toggle loop mode |
| `/seek <seconds>` | Jump to a timestamp |
| `/autoplay` | Toggle autoplay mode |

### 🎶 Lyrics
| Command | Description |
|---|---|
| `/lyrics` | Get lyrics for current song |
| `/lyrics <song>` | Search lyrics for any song |

### 💾 Playlists
| Command | Description |
|---|---|
| `/playlist_create <name>` | Create a new playlist |
| `/playlist_add <name>` | Add current song to playlist |
| `/playlist_play <name>` | Load playlist into queue |
| `/playlist_list` | View all your playlists |
| `/playlist_view <name>` | View songs in a playlist |
| `/playlist_remove <name> <pos>` | Remove a song from playlist |
| `/playlist_delete <name>` | Delete a playlist |

### 🏆 Stats
| Command | Description |
|---|---|
| `/topsongs` | Top 10 most played songs |
| `/topusers` | Top 10 most active users |
| `/mystats` | Your personal stats & rank |
| `/resetstats` | Reset server stats (Admin only) |

### ℹ️ Info
| Command | Description |
|---|---|
| `/help` | Show main help menu |
| `/help <category>` | Show category commands |
| `/about` | Show bot info & ping |

---

## 🔑 Getting Your Tokens

### Discord Bot Token
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** → name it
3. Go to **Bot** tab → click **Reset Token**
4. Copy the token → paste in `.env`
5. Enable **Message Content Intent** and **Server Members Intent**

### Genius API Token
1. Go to [Genius API Clients](https://genius.com/api-clients)
2. Click **New API Client**
3. Fill in app name and website URL (`https://localhost`)
4. Copy **Client Access Token** → paste in `.env`

### Supabase Keys
1. Go to [Supabase](https://supabase.com) → create a project
2. Go to **Project Settings** → **API**
3. Copy **Project URL** and **anon public key** → paste in `.env`

---

## ⚙️ Discord Bot Permissions

When inviting the bot to your server make sure it has:

- ✅ Read Messages
- ✅ Send Messages
- ✅ Embed Links
- ✅ Connect (voice)
- ✅ Speak (voice)
- ✅ Use Slash Commands

---

## 🛠️ Built With

- [Python](https://python.org) — Programming language
- [discord.py](https://discordpy.readthedocs.io) — Discord API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — YouTube audio streaming
- [FFmpeg](https://ffmpeg.org) — Audio processing
- [LyricsGenius](https://github.com/johnwmillr/LyricsGenius) — Lyrics fetching
- [Supabase](https://supabase.com) — Database for playlists & stats

---

## 📄 License

This project is licensed under the MIT License — feel free to use, modify and share!

---

## 👨‍💻 Author

Made with ❤️ by [sam-develops](https://github.com/sam-develops)

---

> ⭐ If you found this useful, consider giving it a star on GitHub!
