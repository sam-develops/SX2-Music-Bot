# ============================================
# 🤖 SX2 Music Bot - Main File (Lavalink)
# ============================================

import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# 🔑 Load token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# ⚙️ Intents
intents = discord.Intents.default()
intents.message_content = True

# 🤖 Create bot
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None        # disables default help command
)

# ============================================
# 📦 Load all Cogs automatically
# ============================================
async def load_cogs():
    cogs_path = os.path.join(os.path.dirname(__file__), 'cogs')
    

    if not os.path.exists(cogs_path):
        os.makedirs(cogs_path)
        print("📁 Created cogs folder!")
        return

    for filename in os.listdir(cogs_path):
        if filename.endswith('.py') and filename != '__init__.py':
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'✅ Loaded cog: {filename}')


# ============================================
# ✅ On Ready
# ============================================
@bot.event
async def on_ready():


    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash commands!')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

    print(f'✅ Logged in as {bot.user}')
    print(f'🎵 SX2 Music Bot is Ready!')

# ============================================
# 🚀 Start everything
# ============================================
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

asyncio.run(main())