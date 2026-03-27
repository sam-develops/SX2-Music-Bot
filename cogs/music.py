# ============================================
# 🎵 SX2 Music Bot - Music Cog (Updated)
# ============================================

import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import random

# Discord activity "name" max length (Listening to …)
_ACTIVITY_NAME_LIMIT = 128


# ============================================
# 🎵 Song Class
# ============================================
class Song:
    def __init__(self, info):
        self.url = info["url"]
        self.title = info["title"]
        self.duration = info.get("duration", 0)
        self.thumbnail = info.get("thumbnail", "")
        self.webpage_url = info.get("webpage_url", "")

    def format_duration(self):
        mins = self.duration // 60
        secs = self.duration % 60
        return f"{mins}:{secs:02d}"


# ============================================
# 🎛️ MusicPlayer — One per server
# ============================================
class MusicPlayer:
    def __init__(self):
        self.queue = []
        self.current = None
        self.volume = 0.5
        self.loop = False
        self.autoplay = False  # 🆕 autoplay toggle


# ============================================
# 🎵 Music Cog
# ============================================
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    # ----------------------------------------
    # 🔧 Helper Methods
    # ----------------------------------------
    def get_player(self, guild_id):
        if guild_id not in self.players:
            self.players[guild_id] = MusicPlayer()
        return self.players[guild_id]

    def _truncate_activity(self, text: str) -> str:
        if len(text) <= _ACTIVITY_NAME_LIMIT:
            return text
        return text[: _ACTIVITY_NAME_LIMIT - 1] + "…"

    async def _update_presence(self):
        """Show current track while audio is active; otherwise idle text."""
        idle = getattr(self.bot, "idle_presence_name", "🎵 /play")
        for guild in self.bot.guilds:
            vc = guild.voice_client
            if not vc or not (vc.is_playing() or vc.is_paused()):
                continue
            player = self.get_player(guild.id)
            if player.current:
                name = self._truncate_activity(player.current.title)
                await self.bot.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.listening, name=name
                    )
                )
                return
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, name=idle
            )
        )

    def schedule_presence_update(self):
        asyncio.run_coroutine_threadsafe(
            self._update_presence(), self.bot.loop
        )

    def fetch_song(self, query):
        ydl_opts = {"format": "bestaudio/best", "noplaylist": True, "quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if not query.startswith("http"):
                info = ydl.extract_info(f"ytsearch:{query}", download=False)
                info = info["entries"][0]
            else:
                info = ydl.extract_info(query, download=False)
            return Song(info)

    def fetch_related_song(self, title):
        """🆕 Fetches a related song for autoplay"""
        ydl_opts = {"format": "bestaudio/best", "noplaylist": True, "quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search for a related song by adding "mix" to the title
            info = ydl.extract_info(f"ytsearch:{title} mix", download=False)
            # grab second result so it's not the same song
            entries = info.get("entries", [])
            if len(entries) > 1:
                return Song(entries[1])
            elif entries:
                return Song(entries[0])
            return None

    def build_embed(self, song, player):
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**[{song.title}]({song.webpage_url})**",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=song.thumbnail)
        embed.add_field(
            name="⏱️ Duration", value=f"`{song.format_duration()}`", inline=True
        )
        embed.add_field(
            name="🔊 Volume", value=f"`{int(player.volume * 100)}%`", inline=True
        )
        embed.add_field(
            name="🔁 Loop", value="`On` ✅" if player.loop else "`Off` ❌", inline=True
        )
        embed.add_field(
            name="🎵 Autoplay",
            value="`On` ✅" if player.autoplay else "`Off` ❌",
            inline=True,
        )
        embed.add_field(
            name="📋 Songs in Queue", value=f"`{len(player.queue)}`", inline=True
        )
        embed.set_footer(text="SX2 Music Bot 🎵")
        return embed

    def play_next(self, interaction, voice_client, player):
        """Plays next song — supports loop & autoplay"""

        # 🔁 Loop mode — replay current song
        if player.loop and player.current:
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    player.current.url,
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                    options="-vn",
                ),
                volume=player.volume,
            )
            voice_client.play(
                source,
                after=lambda e: self.play_next(interaction, voice_client, player),
            )
            self.schedule_presence_update()

        # 📋 Songs in queue — play next one
        elif player.queue:
            next_song = player.queue.pop(0)
            player.current = next_song
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    next_song.url,
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                    options="-vn",
                ),
                volume=player.volume,
            )
            voice_client.play(
                source,
                after=lambda e: self.play_next(interaction, voice_client, player),
            )
            self.schedule_presence_update()

        # 🎵 Autoplay — fetch related song when queue is empty
        elif player.autoplay and player.current:

            async def auto_fetch():
                try:
                    related = await asyncio.get_event_loop().run_in_executor(
                        None, self.fetch_related_song, player.current.title
                    )
                    if related:
                        player.current = related
                        source = discord.PCMVolumeTransformer(
                            discord.FFmpegPCMAudio(
                                related.url,
                                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                                options="-vn",
                            ),
                            volume=player.volume,
                        )
                        voice_client.play(
                            source,
                            after=lambda e: self.play_next(
                                interaction, voice_client, player
                            ),
                        )
                        await self._update_presence()
                        # Send a message showing autoplay picked a song
                        channel = interaction.channel
                        await channel.send(
                            f"🎵 **Autoplay:** Now playing **{related.title}**"
                        )
                except Exception as e:
                    print(f"Autoplay error: {e}")

            asyncio.run_coroutine_threadsafe(auto_fetch(), self.bot.loop)

        else:
            player.current = None
            self.schedule_presence_update()

    # ----------------------------------------
    # 🎵 /play command
    # ----------------------------------------
    @app_commands.command(name="play", description="Play a song from YouTube!")
    @app_commands.describe(song="Song name or YouTube URL")
    async def play(self, interaction: discord.Interaction, song: str):

        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ Join a voice channel first!", ephemeral=True
            )
            return

        await interaction.response.defer()

        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client
        player = self.get_player(interaction.guild.id)

        if voice_client is None:
            voice_client = await voice_channel.connect()
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        try:
            fetched = await asyncio.get_event_loop().run_in_executor(
                None, self.fetch_song, song
            )
        except Exception:
            await interaction.followup.send("❌ Couldn't find that song!")
            return

        if voice_client.is_playing() or voice_client.is_paused():
            player.queue.append(fetched)
            await interaction.followup.send(
                f"📋 Added to queue: **{fetched.title}** (Position: {len(player.queue)})"
            )
            return

        player.current = fetched
        stats_cog = self.bot.cogs.get("Stats")
        if stats_cog:
            stats_cog.record_play(
                interaction.guild.id, interaction.user.id, fetched.title
            )
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(
                fetched.url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                options="-vn",
            ),
            volume=player.volume,
        )

        voice_client.play(
            source, after=lambda e: self.play_next(interaction, voice_client, player)
        )

        await self._update_presence()
        await interaction.followup.send(embed=self.build_embed(fetched, player))

    # ----------------------------------------
    # ⏸️ /pause
    # ----------------------------------------
    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await self._update_presence()
            await interaction.response.send_message("⏸️ Paused!")
        else:
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )

    # ----------------------------------------
    # ▶️ /resume
    # ----------------------------------------
    @app_commands.command(name="resume", description="Resume the paused song")
    async def resume(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await self._update_presence()
            await interaction.response.send_message("▶️ Resumed!")
        else:
            await interaction.response.send_message(
                "❌ Nothing is paused!", ephemeral=True
            )

    # ----------------------------------------
    # ⏭️ /skip
    # ----------------------------------------
    @app_commands.command(name="skip", description="Skip to the next song")
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("⏭️ Skipped!")
        else:
            await interaction.response.send_message(
                "❌ Nothing to skip!", ephemeral=True
            )

    # ----------------------------------------
    # ⏹️ /stop
    # ----------------------------------------
    @app_commands.command(name="stop", description="Stop music and clear the queue")
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        player = self.get_player(interaction.guild.id)
        if voice_client:
            player.queue.clear()
            player.current = None
            player.loop = False
            voice_client.stop()
            await self._update_presence()
            await interaction.response.send_message("⏹️ Stopped and queue cleared!")
        else:
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )

    # ----------------------------------------
    # 🔊 /volume
    # ----------------------------------------
    @app_commands.command(name="volume", description="Set the volume (0-100)")
    @app_commands.describe(level="Volume level between 0 and 100")
    async def volume(self, interaction: discord.Interaction, level: int):
        voice_client = interaction.guild.voice_client
        player = self.get_player(interaction.guild.id)
        if level < 0 or level > 100:
            await interaction.response.send_message(
                "❌ Volume must be between 0 and 100!", ephemeral=True
            )
            return
        player.volume = level / 100
        if voice_client and voice_client.source:
            voice_client.source.volume = player.volume
        await interaction.response.send_message(f"🔊 Volume set to **{level}%**")

    # ----------------------------------------
    # 🔁 /loop
    # ----------------------------------------
    @app_commands.command(name="loop", description="Toggle loop mode")
    async def loop(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild.id)
        player.loop = not player.loop
        status = "✅ On" if player.loop else "❌ Off"
        await interaction.response.send_message(f"🔁 Loop mode: **{status}**")

    # ----------------------------------------
    # 🔀 /shuffle
    # ----------------------------------------
    @app_commands.command(name="shuffle", description="Shuffle the queue")
    async def shuffle(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild.id)
        if len(player.queue) < 2:
            await interaction.response.send_message(
                "❌ Need at least 2 songs in queue!", ephemeral=True
            )
            return
        random.shuffle(player.queue)
        await interaction.response.send_message("🔀 Queue shuffled!")

    # ----------------------------------------
    # 📋 /queue
    # ----------------------------------------
    @app_commands.command(name="queue", description="Show the current queue")
    async def queue(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild.id)
        embed = discord.Embed(title="📋 Current Queue", color=discord.Color.blurple())

        if player.current:
            embed.add_field(
                name="🎵 Now Playing",
                value=f"**{player.current.title}** `{player.current.format_duration()}`",
                inline=False,
            )
        else:
            embed.add_field(
                name="🎵 Now Playing", value="Nothing playing", inline=False
            )

        if player.queue:
            queue_list = ""
            for i, song in enumerate(player.queue[:10], 1):
                queue_list += f"`{i}.` **{song.title}** `{song.format_duration()}`\n"
            if len(player.queue) > 10:
                queue_list += f"\n*...and {len(player.queue) - 10} more songs*"
            embed.add_field(name="⏭️ Up Next", value=queue_list, inline=False)
        else:
            embed.add_field(name="⏭️ Up Next", value="Queue is empty", inline=False)

        embed.set_footer(
            text=f"🔁 Loop: {'On' if player.loop else 'Off'}  |  "
            f"🎵 Autoplay: {'On' if player.autoplay else 'Off'}  |  "
            f"🔊 Volume: {int(player.volume * 100)}%"
        )
        await interaction.response.send_message(embed=embed)

    # ----------------------------------------
    # 📢 /nowplaying
    # ----------------------------------------
    @app_commands.command(name="nowplaying", description="Show current song info")
    async def nowplaying(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild.id)
        if not player.current:
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )
            return
        await interaction.response.send_message(
            embed=self.build_embed(player.current, player)
        )

    # ----------------------------------------
    # 🗑️ /remove — NEW!
    # ----------------------------------------
    @app_commands.command(name="remove", description="Remove a song from the queue")
    @app_commands.describe(position="Position number of the song to remove")
    async def remove(self, interaction: discord.Interaction, position: int):
        player = self.get_player(interaction.guild.id)

        # Check if queue has songs
        if not player.queue:
            await interaction.response.send_message(
                "❌ The queue is empty!", ephemeral=True
            )
            return

        # Check if position is valid
        if position < 1 or position > len(player.queue):
            await interaction.response.send_message(
                f"❌ Invalid position! Queue has {len(player.queue)} songs.",
                ephemeral=True,
            )
            return

        # Remove the song (position 1 = index 0)
        removed = player.queue.pop(position - 1)
        await interaction.response.send_message(
            f"🗑️ Removed **{removed.title}** from position `{position}`"
        )

    # ----------------------------------------
    # ⏭️ /jumpto — NEW!
    # ----------------------------------------
    @app_commands.command(
        name="jumpto", description="Jump to a specific song in the queue"
    )
    @app_commands.describe(position="Position number to jump to")
    async def jumpto(self, interaction: discord.Interaction, position: int):
        voice_client = interaction.guild.voice_client
        player = self.get_player(interaction.guild.id)

        if not player.queue:
            await interaction.response.send_message(
                "❌ The queue is empty!", ephemeral=True
            )
            return

        if position < 1 or position > len(player.queue):
            await interaction.response.send_message(
                f"❌ Invalid position! Queue has {len(player.queue)} songs.",
                ephemeral=True,
            )
            return

        # Remove all songs before the target position
        player.queue = player.queue[position - 1 :]

        # Stop current song — play_next will handle the rest
        if voice_client and voice_client.is_playing():
            voice_client.stop()

        await interaction.response.send_message(f"⏭️ Jumped to position `{position}`!")

    # ----------------------------------------
    # ⏱️ /seek — NEW!
    # ----------------------------------------
    @app_commands.command(
        name="seek", description="Jump to a timestamp in the current song"
    )
    @app_commands.describe(seconds="Time in seconds to jump to (e.g. 90 = 1:30)")
    async def seek(self, interaction: discord.Interaction, seconds: int):
        voice_client = interaction.guild.voice_client
        player = self.get_player(interaction.guild.id)

        if not voice_client or not voice_client.is_playing():
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )
            return

        if not player.current:
            await interaction.response.send_message(
                "❌ No current song found!", ephemeral=True
            )
            return

        await interaction.response.defer()

        # Stop current audio
        voice_client.stop()

        # Restart from the specified timestamp using FFmpeg's -ss option
        seek_options = {
            "before_options": f"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {seconds}",
            "options": "-vn",
        }

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(player.current.url, **seek_options),
            volume=player.volume,
        )

        voice_client.play(
            source, after=lambda e: self.play_next(interaction, voice_client, player)
        )

        await self._update_presence()

        # Format seconds nicely
        mins = seconds // 60
        secs = seconds % 60
        await interaction.followup.send(
            f"⏱️ Seeked to **{mins}:{secs:02d}** in **{player.current.title}**"
        )

    # ----------------------------------------
    # 🎵 /autoplay — NEW!
    # ----------------------------------------
    @app_commands.command(name="autoplay", description="Toggle autoplay mode")
    async def autoplay(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild.id)
        player.autoplay = not player.autoplay
        status = "✅ On" if player.autoplay else "❌ Off"
        await interaction.response.send_message(
            f"🎵 Autoplay mode: **{status}**\n"
            f"> When queue ends, I'll automatically play related songs!"
            if player.autoplay
            else f"🎵 Autoplay mode: **{status}**"
        )

    # ----------------------------------------
    # 🚪 /leave
    # ----------------------------------------
    @app_commands.command(
        name="leave", description="Make the bot leave the voice channel"
    )
    async def leave(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        player = self.get_player(interaction.guild.id)
        if voice_client:
            player.queue.clear()
            player.current = None
            await voice_client.disconnect()
            await self._update_presence()
            await interaction.response.send_message("👋 Disconnected! See you later!")
        else:
            await interaction.response.send_message(
                "❌ I'm not in a voice channel!", ephemeral=True
            )


# ============================================
# 📦 Setup
# ============================================
async def setup(bot):
    await bot.add_cog(Music(bot))
