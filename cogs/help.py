# ============================================
# 📖 SX2 Music Bot - Help Cog (Redesigned)
# ============================================

import discord
from discord import app_commands
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----------------------------------------
    # 📖 /help command
    # ----------------------------------------
    @app_commands.command(name="help", description="Shows all available commands")
    @app_commands.describe(category="Pick a specific category to view")
    @app_commands.choices(
        category=[
            app_commands.Choice(name="🎵 Music", value="music"),
            app_commands.Choice(name="📋 Queue", value="queue"),
            app_commands.Choice(name="🎛️ Controls", value="controls"),
            app_commands.Choice(name="🎶 Lyrics", value="lyrics"),
            app_commands.Choice(name="💾 Playlists", value="playlists"),
            app_commands.Choice(name="🏆 Stats", value="stats"),
            app_commands.Choice(name="ℹ️ Info", value="info"),
        ]
    )
    async def help(self, interaction: discord.Interaction, category: str = None):

        # ── No category → show the main menu ──
        if category is None:
            embed = discord.Embed(color=discord.Color.blurple())

            embed.set_author(
                name="SX2 Music Bot — Command Centre", icon_url=self.bot.user.display_avatar.url
            )

            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

            embed.description = (
                "```\n"
                r"  ___  _  __ ___    __  __ _   _ ____ ___ ____" + "\n"
                r" / __|| \/ /|__ \  |  \/  | | | / ___|_ _/ ___| " + "\n"
                r" \__ \ >  <   / /  | |\/| | | | \___ \| | |    " + "\n"
                r" |___//_/\_\ /_/   |_|  |_|_|_|_|___/___\_____| " + "\n"
                "```\n"
                "> 🎵 Your ultimate music companion for Discord!\n"
                "> Use `/help <category>` for detailed command info\n"
            )

            # Categories grid
            embed.add_field(
                name="╔══ 📚 CATEGORIES ══╗",
                value=(
                    "```\n"
                    "  🎵  Music      │  📋  Queue\n"
                    "  🎛️  Controls   │  🎶  Lyrics\n"
                    "  💾  Playlists  │  🏆  Stats\n"
                    "  ℹ️  Info\n"
                    "```"
                ),
                inline=False,
            )

            # Quick start guide
            embed.add_field(
                name="⚡ Quick Start",
                value=(
                    "**1.** Join a voice channel\n"
                    "**2.** Use `/play <song name>`\n"
                    "**3.** Sit back and enjoy! 🎧"
                ),
                inline=True,
            )

            # Bot stats
            embed.add_field(
                name="📡 Bot Status",
                value=(
                    f"**Servers:** `{len(self.bot.guilds)}`\n"
                    f"**Ping:** `{round(self.bot.latency * 1000)}ms`\n"
                    f"**Commands:** `25+`"
                ),
                inline=True,
            )

            embed.set_footer(
                text="SX2 Music Bot 🎵  •  Made with ❤️ using discord.py  •  /help <category> for more"
            )

            await interaction.response.send_message(embed=embed)
            return

        # ── Category pages ──
        embeds = {
            # 🎵 Music
            "music": {
                "title": "🎵  Music Commands",
                "color": discord.Color.blurple(),
                "fields": [
                    {
                        "name": "▶️  /play <song>",
                        "value": "> Search YouTube and play a song\n> Adds to queue if something is already playing",
                        "inline": False,
                    },
                    {
                        "name": "⏸️  /pause",
                        "value": "> Pause the currently playing song",
                        "inline": False,
                    },
                    {
                        "name": "▶️  /resume",
                        "value": "> Resume a paused song",
                        "inline": False,
                    },
                    {
                        "name": "⏭️  /skip",
                        "value": "> Skip to the next song in queue",
                        "inline": False,
                    },
                    {
                        "name": "⏹️  /stop",
                        "value": "> Stop the music and clear the entire queue",
                        "inline": False,
                    },
                    {
                        "name": "🚪  /leave",
                        "value": "> Disconnect the bot from the voice channel",
                        "inline": False,
                    },
                ],
            },
            # 📋 Queue
            "queue": {
                "title": "📋  Queue Commands",
                "color": discord.Color.blurple(),
                "fields": [
                    {
                        "name": "📋  /queue",
                        "value": "> View all songs currently in the queue",
                        "inline": False,
                    },
                    {
                        "name": "🗑️  /remove <position>",
                        "value": "> Remove a specific song from the queue\n> Example: `/remove 3` removes song #3",
                        "inline": False,
                    },
                    {
                        "name": "⏭️  /jumpto <position>",
                        "value": "> Jump directly to a specific song\n> Example: `/jumpto 5` skips to song #5",
                        "inline": False,
                    },
                    {
                        "name": "🔀  /shuffle",
                        "value": "> Randomly shuffle all songs in the queue",
                        "inline": False,
                    },
                    {
                        "name": "📢  /nowplaying",
                        "value": "> Show the full info card for the current song",
                        "inline": False,
                    },
                ],
            },
            # 🎛️ Controls
            "controls": {
                "title": "🎛️  Control Commands",
                "color": discord.Color.blurple(),
                "fields": [
                    {
                        "name": "🔊  /volume <0-100>",
                        "value": "> Set the playback volume\n> Example: `/volume 80` sets it to 80%",
                        "inline": False,
                    },
                    {
                        "name": "🔁  /loop",
                        "value": "> Toggle loop mode on or off\n> Replays the current song forever when on",
                        "inline": False,
                    },
                    {
                        "name": "⏱️  /seek <seconds>",
                        "value": "> Jump to a specific timestamp in the song\n> Example: `/seek 90` jumps to 1:30",
                        "inline": False,
                    },
                    {
                        "name": "🎵  /autoplay",
                        "value": "> Toggle autoplay mode on or off\n> Auto-suggests related songs when queue ends",
                        "inline": False,
                    },
                ],
            },
            # 🎶 Lyrics
            "lyrics": {
                "title": "🎶  Lyrics Commands",
                "color": discord.Color.blurple(),
                "fields": [
                    {
                        "name": "🎶  /lyrics",
                        "value": "> Get lyrics for the currently playing song\n> Automatically detects what's playing!",
                        "inline": False,
                    },
                    {
                        "name": "🔍  /lyrics <song name>",
                        "value": "> Search lyrics for any song by name\n> Example: `/lyrics Eminem Lose Yourself`",
                        "inline": False,
                    },
                ],
            },
            # 💾 Playlists
            "playlists": {
                "title": "💾  Playlist Commands",
                "color": discord.Color.blurple(),
                "fields": [
                    {
                        "name": "✅  /playlist_create <name>",
                        "value": "> Create a brand new empty playlist\n> Maximum 10 playlists per user",
                        "inline": False,
                    },
                    {
                        "name": "➕  /playlist_add <name> [song]",
                        "value": "> Add a song to a playlist\n> Leave song empty to add currently playing",
                        "inline": False,
                    },
                    {
                        "name": "▶️  /playlist_play <name>",
                        "value": "> Load an entire playlist into the queue",
                        "inline": False,
                    },
                    {
                        "name": "📋  /playlist_list",
                        "value": "> View all your saved playlists",
                        "inline": False,
                    },
                    {
                        "name": "👀  /playlist_view <name>",
                        "value": "> View all songs inside a specific playlist",
                        "inline": False,
                    },
                    {
                        "name": "➖  /playlist_remove <name> <position>",
                        "value": "> Remove a specific song from a playlist",
                        "inline": False,
                    },
                    {
                        "name": "🗑️  /playlist_delete <name>",
                        "value": "> Permanently delete an entire playlist",
                        "inline": False,
                    },
                ],
            },
            # 🏆 Stats
            "stats": {
                "title": "🏆  Stats Commands",
                "color": discord.Color.gold(),
                "fields": [
                    {
                        "name": "🏆  /topsongs",
                        "value": "> Show the top 10 most played songs in this server",
                        "inline": False,
                    },
                    {
                        "name": "👑  /topusers",
                        "value": "> Show the top 10 most active music users",
                        "inline": False,
                    },
                    {
                        "name": "📊  /mystats",
                        "value": "> View your personal music stats and server rank",
                        "inline": False,
                    },
                    {
                        "name": "🗑️  /resetstats",
                        "value": "> Reset all stats for this server\n> ⚠️ Admin only!",
                        "inline": False,
                    },
                ],
            },
            # ℹ️ Info
            "info": {
                "title": "ℹ️  Info Commands",
                "color": discord.Color.blurple(),
                "fields": [
                    {
                        "name": "📖  /help",
                        "value": "> Show the main help menu",
                        "inline": False,
                    },
                    {
                        "name": "📖  /help <category>",
                        "value": "> Show commands for a specific category",
                        "inline": False,
                    },
                    {
                        "name": "ℹ️  /about",
                        "value": "> Show info about this bot including ping and server count",
                        "inline": False,
                    },
                    {
                        "name": "🔗  /invite",
                        "value": "> Get the invite link for this bot",
                        "inline": False,
                    },
                ],
            },
        }

        # Build the category embed
        data = embeds[category]
        embed = discord.Embed(title=data["title"], color=data["color"])
        embed.set_author(name="SX2 Music Bot — Help", icon_url=self.bot.user.display_avatar.url)
        for field in data["fields"]:
            embed.add_field(
                name=field["name"], value=field["value"], inline=field["inline"]
            )
        embed.set_footer(text="SX2 Music Bot 🎵  •  /help to go back to main menu")
        await interaction.response.send_message(embed=embed)

    # ----------------------------------------
    # ℹ️ /about command
    # ----------------------------------------
    @app_commands.command(name="about", description="Shows info about this bot")
    async def about(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="ℹ️  About SX2 Music Bot",
            description=(
                "> A **feature-rich** music bot built with Python!\n"
                "> Stream music, manage playlists, track stats and more."
            ),
            color=discord.Color.blurple(),
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(
            name="🛠️  Built With",
            value=(
                "`Python 3.12`\n"
                "`discord.py`\n"
                "`yt-dlp`\n"
                "`FFmpeg`\n"
                "`lyricsgenius`"
            ),
            inline=True,
        )

        embed.add_field(
            name="✅  Features",
            value=(
                "YouTube Streaming\n"
                "Queue System\n"
                "Lyrics Search\n"
                "Playlist System\n"
                "Music Stats\n"
                "Autoplay & Loop"
            ),
            inline=True,
        )

        embed.add_field(
            name="📡  Live Stats",
            value=(
                f"**Servers:** `{len(self.bot.guilds)}`\n"
                f"**Ping:** `{round(self.bot.latency * 1000)}ms`\n"
                f"**Commands:** `25+`"
            ),
            inline=True,
        )

        embed.set_footer(text="SX2 Music Bot 🎵  •  Made with ❤️ using discord.py")

        await interaction.response.send_message(embed=embed)

    # ----------------------------------------
    # 🔗 /invite command
    # ----------------------------------------
    @app_commands.command(name="invite", description="Get the invite link for this bot")
    async def invite(self, interaction: discord.Interaction):
        permissions = discord.Permissions(
            send_messages=True,
            read_messages=True,
            embed_links=True,
            connect=True,
            speak=True,
            use_voice_activation=True
        )
        invite_link = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=permissions,
            scopes=("bot", "applications.commands")
        )
        
        embed = discord.Embed(
            title="🔗 Invite SX2 Music Bot",
            description=f"Invite the bot to your server by clicking [here]({invite_link})!",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="SX2 Music Bot 🎵")
        
        await interaction.response.send_message(embed=embed)


# ============================================
# 📦 Setup
# ============================================
async def setup(bot):
    await bot.add_cog(Help(bot))
