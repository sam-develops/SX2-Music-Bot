# ============================================
# 🎶 SX2 Music Bot - Lyrics Cog
# ============================================

import discord
from discord import app_commands
from discord.ext import commands
import lyricsgenius
import asyncio
import os


# ============================================
# 🎶 Lyrics Cog
# ============================================
class Lyrics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Connect to Genius API using our token from .env
        self.genius = lyricsgenius.Genius(
            os.getenv("GENIUS_TOKEN"),
            skip_non_songs=True,
            excluded_terms=["(Remix)", "(Live)"],
            remove_section_headers=False,
            verbose=False,
        )

    # ----------------------------------------
    # 🎶 /lyrics command
    # ----------------------------------------
    @app_commands.command(name="lyrics", description="Get lyrics for a song!")
    @app_commands.describe(
        song="Song name to search lyrics for (leave empty for current song)"
    )
    async def lyrics(self, interaction: discord.Interaction, song: str = None):

        await interaction.response.defer()

        # If no song provided, try to get currently playing song
        if song is None:
            # Check if music cog is loaded and something is playing
            music_cog = self.bot.cogs.get("Music")
            if music_cog:
                player = music_cog.get_player(interaction.guild.id)
                if player.current:
                    song = player.current.title
                else:
                    await interaction.followup.send(
                        "❌ Nothing is playing! Please provide a song name.",
                        ephemeral=True,
                    )
                    return
            else:
                await interaction.followup.send(
                    "❌ Please provide a song name!", ephemeral=True
                )
                return

        # 🔍 Search for lyrics on Genius
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.genius.search_song(song)
            )
        except Exception as e:
            await interaction.followup.send(
                "❌ Couldn't connect to Genius! Try again later."
            )
            return

        # If no results found
        if result is None:
            await interaction.followup.send(
                f"❌ Couldn't find lyrics for **{song}**! Try a different name."
            )
            return

        # Discord has a 4096 character limit on embeds
        # So we split long lyrics into multiple messages
        lyrics_text = result.lyrics

        # Clean up the lyrics a bit
        # Remove the first line which is usually the song title repeated
        lyrics_lines = lyrics_text.split("\n")
        if lyrics_lines[0].endswith("Lyrics"):
            lyrics_lines = lyrics_lines[1:]
        lyrics_text = "\n".join(lyrics_lines).strip()

        # Split lyrics into chunks of 4000 characters
        chunks = []
        while len(lyrics_text) > 4000:
            # Find the last newline before 4000 chars
            split_at = lyrics_text[:4000].rfind("\n")
            if split_at == -1:
                split_at = 4000
            chunks.append(lyrics_text[:split_at])
            lyrics_text = lyrics_text[split_at:].strip()
        chunks.append(lyrics_text)

        # Send first chunk as main embed
        embed = discord.Embed(
            title=f"🎶 {result.title}",
            description=chunks[0],
            color=discord.Color.blurple(),
            url=result.url,
        )
        embed.set_thumbnail(url=result.song_art_image_url)
        embed.set_author(name=f"👤 {result.artist.name}")
        embed.set_footer(text=f"Lyrics provided by Genius 🎵 | Page 1 of {len(chunks)}")

        await interaction.followup.send(embed=embed)

        # Send remaining chunks if lyrics are too long
        for i, chunk in enumerate(chunks[1:], 2):
            embed = discord.Embed(description=chunk, color=discord.Color.blurple())
            embed.set_footer(
                text=f"Lyrics provided by Genius 🎵 | Page {i} of {len(chunks)}"
            )
            await interaction.channel.send(embed=embed)


# ============================================
# 📦 Setup
# ============================================
async def setup(bot):
    await bot.add_cog(Lyrics(bot))
