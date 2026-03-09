# ============================================
# 💾 SX2 Music Bot - Playlist Cog
# ============================================

import discord
from discord import app_commands
from discord.ext import commands
import json
import os


# ============================================
# 💾 Playlist Cog
# ============================================
class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # This is where we save playlists on your computer
        self.playlists_file = "playlists.json"
        # Load existing playlists when bot starts
        self.playlists = self.load_playlists()

    # ----------------------------------------
    # 🔧 Helper Methods
    # ----------------------------------------
    def load_playlists(self):
        """Load playlists from the JSON file"""
        if os.path.exists(self.playlists_file):
            with open(self.playlists_file, "r") as f:
                return json.load(f)
        # If file doesn't exist yet, start with empty dict
        return {}

    def save_playlists(self):
        """Save playlists to the JSON file"""
        with open(self.playlists_file, "w") as f:
            json.dump(self.playlists, f, indent=4)

    def get_user_playlists(self, user_id):
        """Get all playlists for a specific user"""
        user_id = str(user_id)  # convert to string for JSON key
        if user_id not in self.playlists:
            self.playlists[user_id] = {}
        return self.playlists[user_id]

    # ----------------------------------------
    # 💾 /playlist create — Create a playlist
    # ----------------------------------------
    @app_commands.command(name="playlist_create", description="Create a new playlist")
    @app_commands.describe(name="Name of your new playlist")
    async def playlist_create(self, interaction: discord.Interaction, name: str):
        user_playlists = self.get_user_playlists(interaction.user.id)

        # Check if playlist already exists
        if name in user_playlists:
            await interaction.response.send_message(
                f"❌ You already have a playlist called **{name}**!", ephemeral=True
            )
            return

        # Check playlist limit per user (max 10)
        if len(user_playlists) >= 10:
            await interaction.response.send_message(
                "❌ You can only have **10 playlists** maximum!", ephemeral=True
            )
            return

        # Create the empty playlist
        user_playlists[name] = []
        self.save_playlists()

        embed = discord.Embed(
            title="✅ Playlist Created!",
            description=f"**{name}** is ready!\nUse `/playlist_add {name} <song>` to add songs!",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)

    # ----------------------------------------
    # ➕ /playlist_add — Add a song to playlist
    # ----------------------------------------
    @app_commands.command(
        name="playlist_add", description="Add current song or a song to a playlist"
    )
    @app_commands.describe(
        name="Name of your playlist",
        song="Song to add (leave empty to add currently playing song)",
    )
    async def playlist_add(
        self, interaction: discord.Interaction, name: str, song: str = None
    ):
        user_playlists = self.get_user_playlists(interaction.user.id)

        # Check if playlist exists
        if name not in user_playlists:
            await interaction.response.send_message(
                f"❌ Playlist **{name}** doesn't exist! Create it first with `/playlist_create`",
                ephemeral=True,
            )
            return

        # If no song provided, use currently playing song
        if song is None:
            music_cog = self.bot.cogs.get("Music")
            if music_cog:
                player = music_cog.get_player(interaction.guild.id)
                if player.current:
                    song_data = {
                        "title": player.current.title,
                        "url": player.current.webpage_url,
                    }
                else:
                    await interaction.response.send_message(
                        "❌ Nothing is playing! Provide a song name.", ephemeral=True
                    )
                    return
            else:
                await interaction.response.send_message(
                    "❌ Please provide a song name!", ephemeral=True
                )
                return
        else:
            song_data = {
                "title": song,
                "url": song if song.startswith("http") else f"ytsearch:{song}",
            }

        # Check song limit per playlist (max 50)
        if len(user_playlists[name]) >= 50:
            await interaction.response.send_message(
                "❌ Playlist is full! Max **50 songs** per playlist.", ephemeral=True
            )
            return

        # Add the song
        user_playlists[name].append(song_data)
        self.save_playlists()

        await interaction.response.send_message(
            f"✅ Added **{song_data['title']}** to playlist **{name}**!\n"
            f"> Playlist now has `{len(user_playlists[name])}` songs"
        )

    # ----------------------------------------
    # ▶️ /playlist_play — Load & play a playlist
    # ----------------------------------------
    @app_commands.command(name="playlist_play", description="Load and play a playlist")
    @app_commands.describe(name="Name of the playlist to play")
    async def playlist_play(self, interaction: discord.Interaction, name: str):
        user_playlists = self.get_user_playlists(interaction.user.id)

        # Check if playlist exists
        if name not in user_playlists:
            await interaction.response.send_message(
                f"❌ Playlist **{name}** doesn't exist!", ephemeral=True
            )
            return

        # Check if playlist has songs
        if not user_playlists[name]:
            await interaction.response.send_message(
                f"❌ Playlist **{name}** is empty! Add songs with `/playlist_add`",
                ephemeral=True,
            )
            return

        # Check if user is in voice channel
        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ Join a voice channel first!", ephemeral=True
            )
            return

        await interaction.response.defer()

        # Get music cog to add songs to queue
        music_cog = self.bot.cogs.get("Music")
        if not music_cog:
            await interaction.followup.send("❌ Music system not found!")
            return

        player = music_cog.get_player(interaction.guild.id)

        # Add all playlist songs to queue
        for song_data in user_playlists[name]:
            from cogs.music import Song

            # Create a minimal song object for the queue
            fake_info = {
                "url": song_data["url"],
                "title": song_data["title"],
                "duration": 0,
                "thumbnail": "",
                "webpage_url": song_data["url"],
            }
            player.queue.append(Song(fake_info))

        embed = discord.Embed(
            title="▶️ Playlist Loaded!",
            description=f"**{name}** — `{len(user_playlists[name])}` songs added to queue!",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Use /play to start playing! 🎵")
        await interaction.followup.send(embed=embed)

    # ----------------------------------------
    # 📋 /playlist_list — Show all playlists
    # ----------------------------------------
    @app_commands.command(name="playlist_list", description="Show all your playlists")
    async def playlist_list(self, interaction: discord.Interaction):
        user_playlists = self.get_user_playlists(interaction.user.id)

        if not user_playlists:
            await interaction.response.send_message(
                "❌ You don't have any playlists yet!\n"
                "Create one with `/playlist_create <name>`",
                ephemeral=True,
            )
            return

        embed = discord.Embed(title="💾 Your Playlists", color=discord.Color.blurple())

        for playlist_name, songs in user_playlists.items():
            embed.add_field(
                name=f"🎵 {playlist_name}", value=f"`{len(songs)}` songs", inline=True
            )

        embed.set_footer(text=f"Total playlists: {len(user_playlists)}/10")
        await interaction.response.send_message(embed=embed)

    # ----------------------------------------
    # 👀 /playlist_view — View songs in playlist
    # ----------------------------------------
    @app_commands.command(
        name="playlist_view", description="View songs inside a playlist"
    )
    @app_commands.describe(name="Name of the playlist to view")
    async def playlist_view(self, interaction: discord.Interaction, name: str):
        user_playlists = self.get_user_playlists(interaction.user.id)

        if name not in user_playlists:
            await interaction.response.send_message(
                f"❌ Playlist **{name}** doesn't exist!", ephemeral=True
            )
            return

        songs = user_playlists[name]

        if not songs:
            await interaction.response.send_message(
                f"❌ Playlist **{name}** is empty!", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"💾 Playlist — {name}", color=discord.Color.blurple()
        )

        song_list = ""
        for i, song in enumerate(songs[:20], 1):
            song_list += f"`{i}.` {song['title']}\n"

        if len(songs) > 20:
            song_list += f"\n*...and {len(songs) - 20} more songs*"

        embed.description = song_list
        embed.set_footer(text=f"Total: {len(songs)}/50 songs")
        await interaction.response.send_message(embed=embed)

    # ----------------------------------------
    # 🗑️ /playlist_delete — Delete a playlist
    # ----------------------------------------
    @app_commands.command(
        name="playlist_delete", description="Delete one of your playlists"
    )
    @app_commands.describe(name="Name of the playlist to delete")
    async def playlist_delete(self, interaction: discord.Interaction, name: str):
        user_playlists = self.get_user_playlists(interaction.user.id)

        if name not in user_playlists:
            await interaction.response.send_message(
                f"❌ Playlist **{name}** doesn't exist!", ephemeral=True
            )
            return

        del user_playlists[name]
        self.save_playlists()

        await interaction.response.send_message(
            f"🗑️ Playlist **{name}** has been deleted!"
        )

    # ----------------------------------------
    # ➖ /playlist_remove — Remove a song
    # ----------------------------------------
    @app_commands.command(
        name="playlist_remove", description="Remove a song from a playlist"
    )
    @app_commands.describe(
        name="Name of your playlist", position="Position number of the song to remove"
    )
    async def playlist_remove(
        self, interaction: discord.Interaction, name: str, position: int
    ):
        user_playlists = self.get_user_playlists(interaction.user.id)

        if name not in user_playlists:
            await interaction.response.send_message(
                f"❌ Playlist **{name}** doesn't exist!", ephemeral=True
            )
            return

        songs = user_playlists[name]

        if position < 1 or position > len(songs):
            await interaction.response.send_message(
                f"❌ Invalid position! Playlist has `{len(songs)}` songs.",
                ephemeral=True,
            )
            return

        removed = songs.pop(position - 1)
        self.save_playlists()

        await interaction.response.send_message(
            f"🗑️ Removed **{removed['title']}** from **{name}**!"
        )


# ============================================
# 📦 Setup
# ============================================
async def setup(bot):
    await bot.add_cog(Playlist(bot))
