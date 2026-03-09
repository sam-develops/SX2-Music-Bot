# ============================================
# 💾 SX2 Music Bot - Playlist Cog (Supabase)
# ============================================

import discord
from discord import app_commands
from discord.ext import commands
from supabase import create_client
import os


class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Connect to Supabase
        self.db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    # ----------------------------------------
    # 🔧 Helper Methods
    # ----------------------------------------
    def get_playlist(self, user_id, name):
        """Get a playlist by user and name"""
        result = (
            self.db.table("playlists")
            .select("*")
            .eq("user_id", str(user_id))
            .eq("name", name)
            .execute()
        )
        return result.data[0] if result.data else None

    def get_all_playlists(self, user_id):
        """Get all playlists for a user"""
        result = (
            self.db.table("playlists").select("*").eq("user_id", str(user_id)).execute()
        )
        return result.data

    def get_playlist_songs(self, playlist_id):
        """Get all songs in a playlist"""
        result = (
            self.db.table("playlist_songs")
            .select("*")
            .eq("playlist_id", playlist_id)
            .order("position")
            .execute()
        )
        return result.data

    # ----------------------------------------
    # ✅ /playlist_create
    # ----------------------------------------
    @app_commands.command(name="playlist_create", description="Create a new playlist")
    @app_commands.describe(name="Name of your new playlist")
    async def playlist_create(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()

        # Check if already exists
        existing = self.get_playlist(interaction.user.id, name)
        if existing:
            await interaction.followup.send(
                f"❌ You already have a playlist called **{name}**!", ephemeral=True
            )
            return

        # Check limit
        all_playlists = self.get_all_playlists(interaction.user.id)
        if len(all_playlists) >= 10:
            await interaction.followup.send(
                "❌ You can only have **10 playlists** maximum!", ephemeral=True
            )
            return

        # Create playlist in Supabase
        self.db.table("playlists").insert(
            {"user_id": str(interaction.user.id), "name": name}
        ).execute()

        embed = discord.Embed(
            title="✅ Playlist Created!",
            description=f"**{name}** is ready!\nUse `/playlist_add {name} <song>` to add songs!",
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=embed)

    # ----------------------------------------
    # ➕ /playlist_add
    # ----------------------------------------
    @app_commands.command(name="playlist_add", description="Add a song to a playlist")
    @app_commands.describe(
        name="Name of your playlist",
        song="Song to add (leave empty for currently playing)",
    )
    async def playlist_add(
        self, interaction: discord.Interaction, name: str, song: str = None
    ):
        await interaction.response.defer()

        # Check playlist exists
        playlist = self.get_playlist(interaction.user.id, name)
        if not playlist:
            await interaction.followup.send(
                f"❌ Playlist **{name}** doesn't exist!", ephemeral=True
            )
            return

        # Get song data
        if song is None:
            music_cog = self.bot.cogs.get("Music")
            if music_cog:
                player = music_cog.get_player(interaction.guild.id)
                if player.current:
                    song_title = player.current.title
                    song_url = player.current.webpage_url
                else:
                    await interaction.followup.send(
                        "❌ Nothing is playing! Provide a song name.", ephemeral=True
                    )
                    return
            else:
                await interaction.followup.send(
                    "❌ Provide a song name!", ephemeral=True
                )
                return
        else:
            song_title = song
            song_url = song if song.startswith("http") else f"ytsearch:{song}"

        # Check song limit
        songs = self.get_playlist_songs(playlist["id"])
        if len(songs) >= 50:
            await interaction.followup.send(
                "❌ Playlist is full! Max **50 songs**.", ephemeral=True
            )
            return

        # Add song to Supabase
        self.db.table("playlist_songs").insert(
            {
                "playlist_id": playlist["id"],
                "title": song_title,
                "url": song_url,
                "position": len(songs) + 1,
            }
        ).execute()

        await interaction.followup.send(
            f"✅ Added **{song_title}** to **{name}**!\n"
            f"> Playlist now has `{len(songs) + 1}` songs"
        )

    # ----------------------------------------
    # ▶️ /playlist_play
    # ----------------------------------------
    @app_commands.command(name="playlist_play", description="Load and play a playlist")
    @app_commands.describe(name="Name of the playlist to play")
    async def playlist_play(self, interaction: discord.Interaction, name: str):

        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ Join a voice channel first!", ephemeral=True
            )
            return

        await interaction.response.defer()

        playlist = self.get_playlist(interaction.user.id, name)
        if not playlist:
            await interaction.followup.send(
                f"❌ Playlist **{name}** doesn't exist!", ephemeral=True
            )
            return

        songs = self.get_playlist_songs(playlist["id"])
        if not songs:
            await interaction.followup.send(
                f"❌ Playlist **{name}** is empty!", ephemeral=True
            )
            return

        music_cog = self.bot.cogs.get("Music")
        if not music_cog:
            await interaction.followup.send("❌ Music system not found!")
            return

        player = music_cog.get_player(interaction.guild.id)

        # Add all songs to queue
        from cogs.music import Song

        for song_data in songs:
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
            description=f"**{name}** — `{len(songs)}` songs added to queue!",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Use /play to start! 🎵")
        await interaction.followup.send(embed=embed)

    # ----------------------------------------
    # 📋 /playlist_list
    # ----------------------------------------
    @app_commands.command(name="playlist_list", description="Show all your playlists")
    async def playlist_list(self, interaction: discord.Interaction):
        await interaction.response.defer()

        playlists = self.get_all_playlists(interaction.user.id)

        if not playlists:
            await interaction.followup.send(
                "❌ You don't have any playlists yet!\n"
                "Create one with `/playlist_create <name>`",
                ephemeral=True,
            )
            return

        embed = discord.Embed(title="💾 Your Playlists", color=discord.Color.blurple())

        for playlist in playlists:
            songs = self.get_playlist_songs(playlist["id"])
            embed.add_field(
                name=f"🎵 {playlist['name']}",
                value=f"`{len(songs)}` songs",
                inline=True,
            )

        embed.set_footer(text=f"Total: {len(playlists)}/10 playlists")
        await interaction.followup.send(embed=embed)

    # ----------------------------------------
    # 👀 /playlist_view
    # ----------------------------------------
    @app_commands.command(
        name="playlist_view", description="View songs inside a playlist"
    )
    @app_commands.describe(name="Name of the playlist to view")
    async def playlist_view(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()

        playlist = self.get_playlist(interaction.user.id, name)
        if not playlist:
            await interaction.followup.send(
                f"❌ Playlist **{name}** doesn't exist!", ephemeral=True
            )
            return

        songs = self.get_playlist_songs(playlist["id"])
        if not songs:
            await interaction.followup.send(
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
        await interaction.followup.send(embed=embed)

    # ----------------------------------------
    # ➖ /playlist_remove
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
        await interaction.response.defer()

        playlist = self.get_playlist(interaction.user.id, name)
        if not playlist:
            await interaction.followup.send(
                f"❌ Playlist **{name}** doesn't exist!", ephemeral=True
            )
            return

        songs = self.get_playlist_songs(playlist["id"])

        if position < 1 or position > len(songs):
            await interaction.followup.send(
                f"❌ Invalid position! Playlist has `{len(songs)}` songs.",
                ephemeral=True,
            )
            return

        song_to_remove = songs[position - 1]

        # Delete from Supabase
        self.db.table("playlist_songs").delete().eq(
            "id", song_to_remove["id"]
        ).execute()

        await interaction.followup.send(
            f"🗑️ Removed **{song_to_remove['title']}** from **{name}**!"
        )

    # ----------------------------------------
    # 🗑️ /playlist_delete
    # ----------------------------------------
    @app_commands.command(
        name="playlist_delete", description="Delete one of your playlists"
    )
    @app_commands.describe(name="Name of the playlist to delete")
    async def playlist_delete(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()

        playlist = self.get_playlist(interaction.user.id, name)
        if not playlist:
            await interaction.followup.send(
                f"❌ Playlist **{name}** doesn't exist!", ephemeral=True
            )
            return

        # Delete from Supabase (songs auto-delete due to CASCADE)
        self.db.table("playlists").delete().eq("id", playlist["id"]).execute()

        await interaction.followup.send(f"🗑️ Playlist **{name}** deleted!")


# ============================================
# 📦 Setup
# ============================================
async def setup(bot):
    await bot.add_cog(Playlist(bot))
