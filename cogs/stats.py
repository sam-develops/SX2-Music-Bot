# ============================================
# 🏆 SX2 Music Bot - Stats Cog
# ============================================

import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime


# ============================================
# 🏆 Stats Cog
# ============================================
class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stats_file = "stats.json"
        self.stats = self.load_stats()

    # ----------------------------------------
    # 🔧 Helper Methods
    # ----------------------------------------
    def load_stats(self):
        """Load stats from JSON file"""
        if os.path.exists(self.stats_file):
            with open(self.stats_file, "r") as f:
                return json.load(f)
        return {}

    def save_stats(self):
        """Save stats to JSON file"""
        with open(self.stats_file, "w") as f:
            json.dump(self.stats, f, indent=4)

    def get_guild_stats(self, guild_id):
        """Get or create stats for a server"""
        guild_id = str(guild_id)
        if guild_id not in self.stats:
            self.stats[guild_id] = {
                "songs": {},  # song title → play count
                "total_played": 0,  # total songs played
                "users": {},  # user id → songs they requested
            }
        return self.stats[guild_id]

    def record_play(self, guild_id, user_id, song_title):
        """Record a song being played — called from music cog"""
        guild_stats = self.get_guild_stats(guild_id)
        user_id = str(user_id)

        # Track song play count
        if song_title not in guild_stats["songs"]:
            guild_stats["songs"][song_title] = 0
        guild_stats["songs"][song_title] += 1

        # Track total plays
        guild_stats["total_played"] += 1

        # Track per user requests
        if user_id not in guild_stats["users"]:
            guild_stats["users"][user_id] = 0
        guild_stats["users"][user_id] += 1

        self.save_stats()

    # ----------------------------------------
    # 🏆 /topsongs — Most played songs
    # ----------------------------------------
    @app_commands.command(
        name="topsongs", description="Show the most played songs in this server"
    )
    async def topsongs(self, interaction: discord.Interaction):
        guild_stats = self.get_guild_stats(interaction.guild.id)

        if not guild_stats["songs"]:
            await interaction.response.send_message(
                "❌ No songs have been played yet!", ephemeral=True
            )
            return

        # Sort songs by play count (highest first)
        sorted_songs = sorted(
            guild_stats["songs"].items(), key=lambda x: x[1], reverse=True
        )

        embed = discord.Embed(
            title="🏆 Most Played Songs",
            description=f"Top songs in **{interaction.guild.name}**",
            color=discord.Color.gold(),
        )

        # Medal emojis for top 3
        medals = ["🥇", "🥈", "🥉"]

        song_list = ""
        for i, (title, count) in enumerate(sorted_songs[:10], 1):
            medal = medals[i - 1] if i <= 3 else f"`{i}.`"
            song_list += f"{medal} **{title}**\n> Played `{count}` times\n\n"

        embed.description = song_list
        embed.set_footer(text=f"Total songs played: {guild_stats['total_played']} 🎵")
        await interaction.response.send_message(embed=embed)

    # ----------------------------------------
    # 👑 /topusers — Most active users
    # ----------------------------------------
    @app_commands.command(
        name="topusers", description="Show the most active music users"
    )
    async def topusers(self, interaction: discord.Interaction):
        guild_stats = self.get_guild_stats(interaction.guild.id)

        if not guild_stats["users"]:
            await interaction.response.send_message("❌ No data yet!", ephemeral=True)
            return

        # Sort users by request count
        sorted_users = sorted(
            guild_stats["users"].items(), key=lambda x: x[1], reverse=True
        )

        embed = discord.Embed(
            title="👑 Top Music Users",
            description=f"Most active DJs in **{interaction.guild.name}**",
            color=discord.Color.gold(),
        )

        medals = ["🥇", "🥈", "🥉"]

        user_list = ""
        for i, (user_id, count) in enumerate(sorted_users[:10], 1):
            medal = medals[i - 1] if i <= 3 else f"`{i}.`"
            user_list += f"{medal} <@{user_id}> — `{count}` songs requested\n"

        embed.description = user_list
        embed.set_footer(text=f"Total songs played: {guild_stats['total_played']} 🎵")
        await interaction.response.send_message(embed=embed)

    # ----------------------------------------
    # 📊 /mystats — Personal stats
    # ----------------------------------------
    @app_commands.command(name="mystats", description="Show your personal music stats")
    async def mystats(self, interaction: discord.Interaction):
        guild_stats = self.get_guild_stats(interaction.guild.id)
        user_id = str(interaction.user.id)

        if user_id not in guild_stats["users"]:
            await interaction.response.send_message(
                "❌ You haven't requested any songs yet!", ephemeral=True
            )
            return

        user_requests = guild_stats["users"][user_id]

        # Find user's rank
        sorted_users = sorted(
            guild_stats["users"].items(), key=lambda x: x[1], reverse=True
        )
        rank = next(
            (i + 1 for i, (uid, _) in enumerate(sorted_users) if uid == user_id), None
        )

        embed = discord.Embed(
            title=f"📊 {interaction.user.display_name}'s Stats",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(
            url=interaction.user.avatar.url if interaction.user.avatar else None
        )

        embed.add_field(
            name="🎵 Songs Requested", value=f"`{user_requests}`", inline=True
        )
        embed.add_field(name="🏆 Server Rank", value=f"`#{rank}`", inline=True)
        embed.add_field(
            name="📈 Server Total",
            value=f"`{guild_stats['total_played']}` songs played",
            inline=True,
        )

        embed.set_footer(text="SX2 Music Bot 🎵")
        await interaction.response.send_message(embed=embed)

    # ----------------------------------------
    # 🗑️ /resetstats — Reset server stats
    # ----------------------------------------
    @app_commands.command(
        name="resetstats", description="Reset all music stats for this server"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def resetstats(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)

        if guild_id in self.stats:
            del self.stats[guild_id]
            self.save_stats()

        await interaction.response.send_message(
            "🗑️ All stats for this server have been reset!"
        )


# ============================================
# 📦 Setup
# ============================================
async def setup(bot):
    await bot.add_cog(Stats(bot))
