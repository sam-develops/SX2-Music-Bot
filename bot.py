# ============================================
# 🤖 SX2 Music Bot - Main File
# ============================================

import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# 🔑 Load token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ⚙️ Intents
intents = discord.Intents.default()
intents.message_content = True

# 🤖 Create bot
# NEW - help_command=None disables the default one!
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


# ============================================
# 📦 Load all Cogs automatically
# ============================================
async def load_cogs():
    # Build the absolute path to cogs folder
    # This works no matter where you run the bot from!
    cogs_path = os.path.join(os.path.dirname(__file__), "cogs")

    # If cogs folder doesn't exist, create it automatically
    if not os.path.exists(cogs_path):
        os.makedirs(cogs_path)
        print("📁 Created cogs folder!")
        return

    for filename in os.listdir(cogs_path):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"✅ Loaded cog: {filename}")


# ============================================
# ✅ On Ready
# ============================================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")
    print(f"🎵 SX2 Music Bot is Ready!")


# ============================================
# 🚀 Start everything
# ============================================
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


asyncio.run(main())
