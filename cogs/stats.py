# ============================================
# 🏆 SX2 Music Bot - Stats Cog (Supabase)
# ============================================

import discord
from discord import app_commands
from discord.ext import commands
from supabase import create_client
import os


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    # ----------------------------------------
    # 🔧 Record a play (called from music.py)
    # ----------------------------------------
    def record_play(self, guild_id, user_id, song_title):
        guild_id = str(guild_id)
        user_id = str(user_id)

        # Update or insert song stats
        existing = (
            self.db.table("song_stats")
            .select("*")
            .eq("guild_id", guild_id)
            .eq("song_title", song_title)
            .execute()
        )

        if existing.data:
            # Song exists → increment count
            self.db.table("song_stats").update(
                {
                    "play_count": existing.data[0]["play_count"] + 1,
                    "last_played": "NOW()",
                }
            ).eq("id", existing.data[0]["id"]).execute()
        else:
            # New song → insert
            self.db.table("song_stats").insert(
                {
                    "guild_id": guild_id,
                    "user_id": user_id,
                    "song_title": song_title,
                    "play_count": 1,
                }
            ).execute()

        # Update user stats
        user_existing = (
            self.db.table("user_stats")
            .select("*")
            .eq("guild_id", guild_id)
            .eq("user_id", user_id)
            .execute()
        )

        if user_existing.data:
            self.db.table("user_stats").update(
                {"request_count": user_existing.data[0]["request_count"] + 1}
            ).eq("id", user_existing.data[0]["id"]).execute()
        else:
            self.db.table("user_stats").insert(
                {"guild_id": guild_id, "user_id": user_id, "request_count": 1}
            ).execute()

    # ----------------------------------------
    # 🏆 /topsongs
    # ----------------------------------------
    @app_commands.command(name="topsongs", description="Show the most played songs")
    async def topsongs(self, interaction: discord.Interaction):
        await interaction.response.defer()

        result = (
            self.db.table("song_stats")
            .select("*")
            .eq("guild_id", str(interaction.guild.id))
            .order("play_count", desc=True)
            .limit(10)
            .execute()
        )

        if not result.data:
            await interaction.followup.send(
                "❌ No songs have been played yet!", ephemeral=True
            )
            return

        medals = ["🥇", "🥈", "🥉"]
        embed = discord.Embed(
            title="🏆 Most Played Songs",
            description=f"Top songs in **{interaction.guild.name}**",
            color=discord.Color.gold(),
        )

        song_list = ""
        for i, song in enumerate(result.data, 1):
            medal = medals[i - 1] if i <= 3 else f"`{i}.`"
            song_list += f"{medal} **{song['song_title']}**\n> Played `{song['play_count']}` times\n\n"

        embed.description = song_list
        await interaction.followup.send(embed=embed)

    # ----------------------------------------
    # 👑 /topusers
    # ----------------------------------------
    @app_commands.command(
        name="topusers", description="Show the most active music users"
    )
    async def topusers(self, interaction: discord.Interaction):
        await interaction.response.defer()

        result = (
            self.db.table("user_stats")
            .select("*")
            .eq("guild_id", str(interaction.guild.id))
            .order("request_count", desc=True)
            .limit(10)
            .execute()
        )

        if not result.data:
            await interaction.followup.send("❌ No data yet!", ephemeral=True)
            return

        medals = ["🥇", "🥈", "🥉"]
        embed = discord.Embed(
            title="👑 Top Music Users",
            description=f"Most active DJs in **{interaction.guild.name}**",
            color=discord.Color.gold(),
        )

        user_list = ""
        for i, user in enumerate(result.data, 1):
            medal = medals[i - 1] if i <= 3 else f"`{i}.`"
            user_list += (
                f"{medal} <@{user['user_id']}> — `{user['request_count']}` songs\n"
            )

        embed.description = user_list
        await interaction.followup.send(embed=embed)

    # ----------------------------------------
    # 📊 /mystats
    # ----------------------------------------
    @app_commands.command(name="mystats", description="Show your personal music stats")
    async def mystats(self, interaction: discord.Interaction):
        await interaction.response.defer()

        result = (
            self.db.table("user_stats")
            .select("*")
            .eq("guild_id", str(interaction.guild.id))
            .eq("user_id", str(interaction.user.id))
            .execute()
        )

        if not result.data:
            await interaction.followup.send(
                "❌ You haven't requested any songs yet!", ephemeral=True
            )
            return

        user_data = result.data[0]

        # Get rank
        all_users = (
            self.db.table("user_stats")
            .select("*")
            .eq("guild_id", str(interaction.guild.id))
            .order("request_count", desc=True)
            .execute()
        )

        rank = next(
            (
                i + 1
                for i, u in enumerate(all_users.data)
                if u["user_id"] == str(interaction.user.id)
            ),
            None,
        )

        # Get total plays in server
        total = (
            self.db.table("song_stats")
            .select("play_count")
            .eq("guild_id", str(interaction.guild.id))
            .execute()
        )
        total_plays = sum(s["play_count"] for s in total.data)

        embed = discord.Embed(
            title=f"📊 {interaction.user.display_name}'s Stats",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(
            url=interaction.user.avatar.url if interaction.user.avatar else None
        )
        embed.add_field(
            name="🎵 Songs Requested",
            value=f"`{user_data['request_count']}`",
            inline=True,
        )
        embed.add_field(name="🏆 Server Rank", value=f"`#{rank}`", inline=True)
        embed.add_field(
            name="📈 Server Total", value=f"`{total_plays}` plays", inline=True
        )
        embed.set_footer(text="SX2 Music Bot 🎵")
        await interaction.followup.send(embed=embed)

    # ----------------------------------------
    # 🗑️ /resetstats
    # ----------------------------------------
    @app_commands.command(
        name="resetstats", description="Reset all stats for this server"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def resetstats(self, interaction: discord.Interaction):
        await interaction.response.defer()

        guild_id = str(interaction.guild.id)

        self.db.table("song_stats").delete().eq("guild_id", guild_id).execute()

        self.db.table("user_stats").delete().eq("guild_id", guild_id).execute()

        await interaction.followup.send("🗑️ All stats for this server have been reset!")


# ============================================
# 📦 Setup
# ============================================
async def setup(bot):
    await bot.add_cog(Stats(bot))
