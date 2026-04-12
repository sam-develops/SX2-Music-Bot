# ============================================
# 🎵 SX2 Music Bot - Music Cog (Lavalink)
# ============================================

import discord
from discord import app_commands
from discord.ext import commands
import wavelink


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
        player: wavelink.Player = interaction.guild.voice_client

        if player is None:
            player = await voice_channel.connect(cls=wavelink.Player)
            player.autoplay = wavelink.AutoPlayMode.disabled
        elif player.channel != voice_channel:
            await player.move_to(voice_channel)

        return player

    def build_embed(self, track: wavelink.Playable, player: wavelink.Player):
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
                if player.queue.mode == wavelink.QueueMode.loop
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
            player: wavelink.Player = interaction.guild.voice_client

            if player is None:
                player = await voice_channel.connect(cls=wavelink.Player)
                player.autoplay = wavelink.AutoPlayMode.disabled
            elif player.channel != voice_channel:
                await player.move_to(voice_channel)

        except Exception as e:
            await interaction.followup.send(f"❌ Failed to join voice channel: `{e}`")
            print(f"Voice connect error: {e}")
            return

        try:
            results = await wavelink.Playable.search(song)

            if not results:
                await interaction.followup.send(
                    "❌ No results found! Try a different song name."
                )
                return

        except Exception as e:
            await interaction.followup.send(f"❌ Search failed: `{e}`")
            print(f"Search error: {e}")
            return

        try:
            track = results

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
                stats_cog.record_play(
                    interaction.guild.id, interaction.user.id, track.title
                )

        except Exception as e:
            await interaction.followup.send(f"❌ Playback failed: `{e}`")
            print(f"Playback error: {e}")

    # ----------------------------------------
    # ⏸️ /pause
    # ----------------------------------------
    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction):
        player: wavelink.Player = interaction.guild.voice_client

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
        player: wavelink.Player = interaction.guild.voice_client

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
        player: wavelink.Player = interaction.guild.voice_client

        if not player or not player.playing:
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
        player: wavelink.Player = interaction.guild.voice_client

        if not player:
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )
            return

        player.queue.clear()
        await player.stop()
        await interaction.response.send_message("⏹️ Stopped and queue cleared!")

    # ----------------------------------------
    # 🔊 /volume
    # ----------------------------------------
    @app_commands.command(name="volume", description="Set the volume (0-100)")
    @app_commands.describe(level="Volume level between 0 and 100")
    async def volume(self, interaction: discord.Interaction, level: int):
        player: wavelink.Player = interaction.guild.voice_client

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
        player: wavelink.Player = interaction.guild.voice_client

        if not player:
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )
            return

        if player.queue.mode == wavelink.QueueMode.loop:
            player.queue.mode = wavelink.QueueMode.normal
            await interaction.response.send_message("🔁 Loop mode: **❌ Off**")
        else:
            player.queue.mode = wavelink.QueueMode.loop
            await interaction.response.send_message("🔁 Loop mode: **✅ On**")

    # ----------------------------------------
    # 🔀 /shuffle
    # ----------------------------------------
    @app_commands.command(name="shuffle", description="Shuffle the queue")
    async def shuffle(self, interaction: discord.Interaction):
        player: wavelink.Player = interaction.guild.voice_client

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
        player: wavelink.Player = interaction.guild.voice_client

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
        loop = player.queue.mode == wavelink.QueueMode.loop if player else False
        embed.set_footer(
            text=f"🔁 Loop: {'On' if loop else 'Off'}  |  🔊 Volume: {volume}%"
        )
        await interaction.response.send_message(embed=embed)

    # ----------------------------------------
    # 📢 /nowplaying
    # ----------------------------------------
    @app_commands.command(name="nowplaying", description="Show current song info")
    async def nowplaying(self, interaction: discord.Interaction):
        player: wavelink.Player = interaction.guild.voice_client

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
        player: wavelink.Player = interaction.guild.voice_client

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

        queue_list = list(player.queue)
        removed = queue_list.pop(position - 1)
        player.queue.clear()
        for track in queue_list:
            player.queue.put(track)

        await interaction.response.send_message(
            f"🗑️ Removed **{removed.title}** from position `{position}`"
        )

    # ----------------------------------------
    # ⏭️ /jumpto
    # ----------------------------------------
    @app_commands.command(name="jumpto", description="Jump to a specific song in queue")
    @app_commands.describe(position="Position number to jump to")
    async def jumpto(self, interaction: discord.Interaction, position: int):
        player: wavelink.Player = interaction.guild.voice_client

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
        player: wavelink.Player = interaction.guild.voice_client

        if not player or not player.playing:
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
        player: wavelink.Player = interaction.guild.voice_client

        if not player:
            await interaction.response.send_message(
                "❌ Nothing is playing!", ephemeral=True
            )
            return

        if player.autoplay == wavelink.AutoPlayMode.enabled:
            player.autoplay = wavelink.AutoPlayMode.disabled
            await interaction.response.send_message("🎵 Autoplay: **❌ Off**")
        else:
            player.autoplay = wavelink.AutoPlayMode.enabled
            await interaction.response.send_message("🎵 Autoplay: **✅ On**")

    # ----------------------------------------
    # 🚪 /leave
    # ----------------------------------------
    @app_commands.command(name="leave", description="Make bot leave voice channel")
    async def leave(self, interaction: discord.Interaction):
        player: wavelink.Player = interaction.guild.voice_client

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
