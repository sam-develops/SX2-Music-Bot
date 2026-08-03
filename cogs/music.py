# ============================================
# 🎵 SX2 Music Bot - Music Cog (Native Player)
# ============================================

import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import os
import random

# ============================================
# ⚙️ YT-DLP & FFmpeg Configuration
# ============================================
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

if os.path.exists("cookies.txt"):
    ytdl_format_options['cookiefile'] = "cookies.txt"

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

# ============================================
# 📦 Enums & Stubs
# ============================================
class QueueMode:
    normal = 0
    loop = 1

class AutoPlayMode:
    disabled = 0
    enabled = 1

# ============================================
# 🎵 Song Data Structure
# ============================================
class Song:
    def __init__(self, data: dict):
        self.source_url = data.get('webpage_url') or data.get('url')
        self.stream_url = data.get('url')
        self.url = self.source_url
        self.title = data.get('title') or "Unknown Title"
        self.duration = data.get('duration') or 0  # in seconds
        self.length = int(self.duration * 1000)  # in milliseconds
        self.thumbnail = data.get('thumbnail')
        self.artwork = data.get('thumbnail')
        self.webpage_url = data.get('webpage_url') or self.source_url
        self.uri = self.webpage_url
        self.author = data.get('uploader') or data.get('artist') or "Unknown Artist"

# ============================================
# 📋 Queue Management
# ============================================
class MusicQueue:
    def __init__(self):
        self._queue = []
        self.mode = QueueMode.normal

    def __len__(self):
        return len(self._queue)

    def __iter__(self):
        return iter(self._queue)

    def put(self, item):
        self._queue.append(item)

    def append(self, item):
        self._queue.append(item)

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def pop(self, index=0):
        return self._queue.pop(index)

# ============================================
# 🔊 Guild Voice Player
# ============================================
class GuildPlayer(discord.VoiceClient):
    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        super().__init__(client, channel)
        self.bot = client
        self.queue = MusicQueue()
        self.current = None
        self.autoplay = AutoPlayMode.disabled
        self.volume_level = 0.5  # Default 50%
        self._seeking = False
        self.source_transformer = None

    @property
    def playing(self):
        return self.is_playing()

    @property
    def paused(self):
        return self.is_paused()

    @property
    def volume(self):
        return int(self.volume_level * 100)

    async def set_volume(self, level: int):
        self.volume_level = level / 100.0
        if self.source_transformer:
            self.source_transformer.volume = self.volume_level

    async def play(self, song: Song):
        await self.play_song(song)

    async def play_song(self, song: Song):
        self.current = song
        try:
            loop = asyncio.get_event_loop()

            def is_direct_source(url: str):
                return bool(url and ("videoplayback" in url or url.endswith((".mp3", ".ogg", ".wav", ".flac", ".m4a"))))

            stream_url = song.stream_url
            if not stream_url or (song.source_url and not is_direct_source(song.source_url)):
                # Re-extract the stream URL from the stable video/page source to avoid stale URLs.
                url_to_extract = song.source_url or f"ytsearch1:{song.title}"
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url_to_extract, download=False))
                if 'entries' in data:
                    data = data['entries'][0]

                stream_url = data['url']
                song.stream_url = stream_url
                song.source_url = data.get('webpage_url') or song.source_url
                song.url = song.source_url
                song.webpage_url = data.get('webpage_url') or song.webpage_url
                if data.get('duration'):
                    song.duration = data.get('duration')
                    song.length = int(song.duration * 1000)
            
            # Create FFmpeg PCMAudio source
            audio_source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_options)
            self.source_transformer = discord.PCMVolumeTransformer(audio_source, volume=self.volume_level)
            
            # Use super().play to start playback
            # We must stop current playback first if it exists
            if self.is_playing() or self.is_paused():
                self._seeking = True
                super().stop()
                self._seeking = False
                
            super().play(self.source_transformer, after=self.play_next)
        except Exception as e:
            print(f"Error in play_song: {e}")
            self.current = None
            # Trigger play_next thread-safely
            self.play_next()

    def play_next(self, error=None):
        if error:
            print(f"Playback error: {error}")
        coro = self.process_next_song()
        asyncio.run_coroutine_threadsafe(coro, self.bot.loop)

    async def process_next_song(self):
        if self._seeking:
            return
            
        if self.is_playing() or self.is_paused():
            return

        # Check loop mode
        if self.queue.mode == QueueMode.loop and self.current:
            await self.play_song(self.current)
            return

        if len(self.queue) > 0:
            next_song = self.queue.pop(0)
            await self.play_song(next_song)
        else:
            self.current = None

    async def pause(self, state: bool):
        if state:
            if self.is_playing():
                super().pause()
        else:
            if self.is_paused():
                super().resume()

    async def skip(self):
        if self.is_playing() or self.is_paused():
            super().stop()

    def stop(self):
        self.queue.clear()
        self.current = None
        if self.is_playing() or self.is_paused():
            super().stop()

    async def seek(self, milliseconds: int):
        if not self.current:
            return
        
        seconds = milliseconds // 1000
        self._seeking = True
        if self.is_playing() or self.is_paused():
            super().stop()
        
        # Seek options for ffmpeg
        ffmpeg_options_seek = {
            'before_options': f'-ss {seconds} -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn',
        }
        
        loop = asyncio.get_event_loop()
        try:
            # Refresh the stream URL before seeking if needed.
            if not self.current.stream_url or (
                self.current.source_url and "videoplayback" not in self.current.stream_url
            ):
                data = await loop.run_in_executor(
                    None,
                    lambda: ytdl.extract_info(self.current.source_url, download=False),
                )
                if 'entries' in data:
                    data = data['entries'][0]
                self.current.stream_url = data['url']
                self.current.url = self.current.source_url

            audio_source = discord.FFmpegPCMAudio(self.current.stream_url, **ffmpeg_options_seek)
            self.source_transformer = discord.PCMVolumeTransformer(audio_source, volume=self.volume_level)
            self._seeking = False
            super().play(self.source_transformer, after=self.play_next)
        except Exception as e:
            print(f"Error in seek: {e}")
            self._seeking = False
            self.play_next()


# ============================================
# ⚙️ Music Cog
# ============================================
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------------------------------------
    # 🔧 Helper — Get or create player
    # ----------------------------------------
    async def ensure_player(self, interaction: discord.Interaction):
        """Join voice channel and return player"""

        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ Join a voice channel first!", ephemeral=True
            )
            return None

        voice_channel = interaction.user.voice.channel
        player = interaction.guild.voice_client

        if player is None:
            player = await voice_channel.connect(cls=GuildPlayer)
            player.autoplay = AutoPlayMode.disabled
        elif player.channel != voice_channel:
            await player.move_to(voice_channel)

        return player

    def get_player(self, guild_id: int):
        guild = self.bot.get_guild(guild_id)
        if guild:
            return guild.voice_client
        return None

    async def search_song(self, query: str) -> Song:
        loop = asyncio.get_event_loop()
        is_url = query.startswith("http://") or query.startswith("https://")
        search_query = query if is_url else f"ytsearch1:{query}"
        
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))
        if not data:
            return None
            
        if 'entries' in data:
            entries = data['entries']
            if not entries:
                return None
            song_data = entries[0]
        else:
            song_data = data
            
        return Song(song_data)

    def build_embed(self, track: Song, player: GuildPlayer):
        """Build a Now Playing embed"""
        mins = track.length // 60000
        secs = (track.length // 1000) % 60

        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**[{track.title}]({track.uri})**",
            color=discord.Color.blurple(),
        )

        if track.artwork:
            embed.set_thumbnail(url=track.artwork)

        embed.add_field(name="👤 Artist", value=f"`{track.author}`", inline=True)
        embed.add_field(name="⏱️ Duration", value=f"`{mins}:{secs:02d}`", inline=True)
        embed.add_field(name="🔊 Volume", value=f"`{player.volume}%`", inline=True)
        embed.add_field(
            name="📋 Queue", value=f"`{len(player.queue)}` songs", inline=True
        )
        embed.add_field(
            name="🔁 Loop",
            value=(
                "`On` ✅"
                if player.queue.mode == QueueMode.loop
                else "`Off` ❌"
            ),
            inline=True,
        )
        embed.set_footer(text="SX2 Music Bot 🎵")
        return embed

    # ----------------------------------------
    # 🎵 /play
    # ----------------------------------------
    @app_commands.command(name="play", description="Play a song from YouTube!")
    @app_commands.describe(song="Song name or YouTube URL")
    async def play(self, interaction: discord.Interaction, song: str):
        await interaction.response.defer()

        if not interaction.user.voice:
            await interaction.followup.send(
                "❌ Join a voice channel first!", ephemeral=True
            )
            return

        try:
            voice_channel = interaction.user.voice.channel
            player = interaction.guild.voice_client

            if player is None:
                player = await voice_channel.connect(cls=GuildPlayer)
                player.autoplay = AutoPlayMode.disabled
            elif player.channel != voice_channel:
                await player.move_to(voice_channel)

        except Exception as e:
            await interaction.followup.send(f"❌ Failed to join voice channel: `{e}`")
            print(f"Voice connect error: {e}")
            return

        try:
            track = await self.search_song(song)

            if not track:
                await interaction.followup.send(
                    "❌ No results found! Try a different song name."
                )
                return

        except Exception as e:
            await interaction.followup.send(f"❌ Search failed: `{e}`")
            print(f"Search error: {e}")
            return

        try:
            if player.playing:
                player.queue.put(track)
                await interaction.followup.send(
                    f"📋 Added to queue: **{track.title}**\n"
                    f"> Position: `{len(player.queue)}`"
                )
            else:
                await player.play(track)
                await interaction.followup.send(embed=self.build_embed(track, player))

            stats_cog = self.bot.cogs.get("Stats")
            if stats_cog:
                try:
                    # record_play does blocking Supabase network I/O — run it in
                    # an executor so it doesn't freeze the event loop.
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: stats_cog.record_play(
                            interaction.guild.id, interaction.user.id, track.title
                        ),
                    )
                except Exception as e:
                    print(f"Stats recording failed (non-fatal): {e}")

        except Exception as e:
            await interaction.followup.send(f"❌ Playback failed: `{e}`")
            print(f"Playback error: {e}")

    # ----------------------------------------
    # ⏸️ /pause
    # ----------------------------------------
    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client

        if not player or not player.playing:
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )
            return

        await player.pause(True)
        await interaction.response.send_message("⏸️ Paused!")

    # ----------------------------------------
    # ▶️ /resume
    # ----------------------------------------
    @app_commands.command(name="resume", description="Resume the paused song")
    async def resume(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client

        if not player or not player.paused:
            await interaction.response.send_message(
                "❌ Nothing is paused!", ephemeral=True
            )
            return

        await player.pause(False)
        await interaction.response.send_message("▶️ Resumed!")

    # ----------------------------------------
    # ⏭️ /skip
    # ----------------------------------------
    @app_commands.command(name="skip", description="Skip to the next song")
    async def skip(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client

        if not player or (not player.playing and not player.paused):
            await interaction.response.send_message(
                "❌ Nothing to skip!", ephemeral=True
            )
            return

        await player.skip()
        await interaction.response.send_message("⏭️ Skipped!")

    # ----------------------------------------
    # ⏹️ /stop
    # ----------------------------------------
    @app_commands.command(name="stop", description="Stop music and clear queue")
    async def stop(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client

        if not player:
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )
            return

        player.stop()
        await interaction.response.send_message("⏹️ Stopped and queue cleared!")

    # ----------------------------------------
    # 🔊 /volume
    # ----------------------------------------
    @app_commands.command(name="volume", description="Set the volume (0-100)")
    @app_commands.describe(level="Volume level between 0 and 100")
    async def volume(self, interaction: discord.Interaction, level: int):
        player = interaction.guild.voice_client

        if not player:
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )
            return

        if level < 0 or level > 100:
            await interaction.response.send_message(
                "❌ Volume must be between 0 and 100!", ephemeral=True
            )
            return

        await player.set_volume(level)
        await interaction.response.send_message(f"🔊 Volume set to **{level}%**")

    # ----------------------------------------
    # 🔁 /loop
    # ----------------------------------------
    @app_commands.command(name="loop", description="Toggle loop mode")
    async def loop(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client

        if not player:
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )
            return

        if player.queue.mode == QueueMode.loop:
            player.queue.mode = QueueMode.normal
            await interaction.response.send_message("🔁 Loop mode: **❌ Off**")
        else:
            player.queue.mode = QueueMode.loop
            await interaction.response.send_message("🔁 Loop mode: **✅ On**")

    # ----------------------------------------
    # 🔀 /shuffle
    # ----------------------------------------
    @app_commands.command(name="shuffle", description="Shuffle the queue")
    async def shuffle(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client

        if not player or len(player.queue) < 2:
            await interaction.response.send_message(
                "❌ Need at least 2 songs in queue!", ephemeral=True
            )
            return

        player.queue.shuffle()
        await interaction.response.send_message("🔀 Queue shuffled!")

    # ----------------------------------------
    # 📋 /queue
    # ----------------------------------------
    @app_commands.command(name="queue", description="Show the current queue")
    async def queue(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client

        embed = discord.Embed(title="📋 Current Queue", color=discord.Color.blurple())

        if player and player.current:
            mins = player.current.length // 60000
            secs = (player.current.length // 1000) % 60
            embed.add_field(
                name="🎵 Now Playing",
                value=f"**{player.current.title}** `{mins}:{secs:02d}`",
                inline=False,
            )
        else:
            embed.add_field(
                name="🎵 Now Playing", value="Nothing playing", inline=False
            )

        if player and player.queue:
            queue_list = ""
            for i, track in enumerate(list(player.queue)[:10], 1):
                mins = track.length // 60000
                secs = (track.length // 1000) % 60
                queue_list += f"`{i}.` **{track.title}** `{mins}:{secs:02d}`\n"
            if len(player.queue) > 10:
                queue_list += f"\n*...and {len(player.queue) - 10} more songs*"
            embed.add_field(name="⏭️ Up Next", value=queue_list, inline=False)
        else:
            embed.add_field(name="⏭️ Up Next", value="Queue is empty", inline=False)

        volume = player.volume if player else 100
        loop = player.queue.mode == QueueMode.loop if player else False
        embed.set_footer(
            text=f"🔁 Loop: {'On' if loop else 'Off'}  |  🔊 Volume: {volume}%"
        )
        await interaction.response.send_message(embed=embed)

    # ----------------------------------------
    # 📢 /nowplaying
    # ----------------------------------------
    @app_commands.command(name="nowplaying", description="Show current song info")
    async def nowplaying(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client

        if not player or not player.current:
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=self.build_embed(player.current, player)
        )

    # ----------------------------------------
    # 🗑️ /remove
    # ----------------------------------------
    @app_commands.command(name="remove", description="Remove a song from the queue")
    @app_commands.describe(position="Position number of the song to remove")
    async def remove(self, interaction: discord.Interaction, position: int):
        player = interaction.guild.voice_client

        if not player or not player.queue:
            await interaction.response.send_message(
                "❌ Queue is empty!", ephemeral=True
            )
            return

        if position < 1 or position > len(player.queue):
            await interaction.response.send_message(
                f"❌ Invalid position! Queue has {len(player.queue)} songs.",
                ephemeral=True,
            )
            return

        removed = player.queue.pop(position - 1)
        await interaction.response.send_message(
            f"🗑️ Removed **{removed.title}** from position `{position}`"
        )

    # ----------------------------------------
    # ⏭️ /jumpto
    # ----------------------------------------
    @app_commands.command(name="jumpto", description="Jump to a specific song in queue")
    @app_commands.describe(position="Position number to jump to")
    async def jumpto(self, interaction: discord.Interaction, position: int):
        player = interaction.guild.voice_client

        if not player or not player.queue:
            await interaction.response.send_message(
                "❌ Queue is empty!", ephemeral=True
            )
            return

        if position < 1 or position > len(player.queue):
            await interaction.response.send_message(
                f"❌ Invalid position! Queue has {len(player.queue)} songs.",
                ephemeral=True,
            )
            return

        queue_list = list(player.queue)[position - 1 :]
        player.queue.clear()
        for track in queue_list:
            player.queue.put(track)

        await player.skip()
        await interaction.response.send_message(f"⏭️ Jumped to position `{position}`!")

    # ----------------------------------------
    # ⏱️ /seek
    # ----------------------------------------
    @app_commands.command(name="seek", description="Jump to a timestamp in the song")
    @app_commands.describe(seconds="Time in seconds (e.g. 90 = 1:30)")
    async def seek(self, interaction: discord.Interaction, seconds: int):
        player = interaction.guild.voice_client

        if not player or not player.current:
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )
            return

        await player.seek(seconds * 1000)
        mins = seconds // 60
        secs = seconds % 60
        await interaction.response.send_message(f"⏱️ Seeked to **{mins}:{secs:02d}**")

    # ----------------------------------------
    # 🎵 /autoplay
    # ----------------------------------------
    @app_commands.command(name="autoplay", description="Toggle autoplay mode")
    async def autoplay(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client

        if not player:
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )
            return

        if player.autoplay == AutoPlayMode.enabled:
            player.autoplay = AutoPlayMode.disabled
            await interaction.response.send_message("🎵 Autoplay: **❌ Off**")
        else:
            player.autoplay = AutoPlayMode.enabled
            await interaction.response.send_message("🎵 Autoplay: **✅ On**")

    # ----------------------------------------
    # 🚪 /leave
    # ----------------------------------------
    @app_commands.command(name="leave", description="Make bot leave voice channel")
    async def leave(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client

        if not player:
            await interaction.response.send_message(
                "❌ I'm not in a voice channel!", ephemeral=True
            )
            return

        await player.disconnect()
        await interaction.response.send_message("👋 Disconnected! See you later!")


# ============================================
# 📦 Setup
# ============================================
async def setup(bot):
    await bot.add_cog(Music(bot))
