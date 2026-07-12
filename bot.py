# ============================================
# 🤖 SX2 Music Bot - Main File (Native Player)
# ============================================


import discord
from discord.ext import commands
import asyncio
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


# ============================================
# 🌐 Keep-alive HTTP server
# ============================================
# Render "Web Service" instances require the process to bind an open port,
# or the deploy is marked unhealthy ("No open ports detected"). A Discord bot
# makes an OUTBOUND connection and never listens on a port, so we run a tiny
# HTTP server just to satisfy the port scan. Only starts when $PORT is set
# (i.e. on Render); locally it's skipped.
def start_keep_alive():
    port = os.getenv('PORT')
    if not port:
        return

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'SX2 Music Bot is alive')

        def log_message(self, *args):
            pass  # silence per-request logging

    server = HTTPServer(('0.0.0.0', int(port)), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f'🌐 Keep-alive server listening on port {port}')

# 🔑 Load token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

# ⚙️ Intents
# NOTE: This bot is 100% slash commands — it never reads message text,
# so the privileged `message_content` intent is intentionally NOT enabled.
# Enabling it would require toggling it in the Developer Portal or the bot
# fails to log in with PrivilegedIntentsRequired.
intents = discord.Intents.default()

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
    print(f'✅ Logged in as {bot.user}')
    print(f'🎵 SX2 Music Bot is Ready!')


# ============================================
# 🔄 Sync commands ONCE at startup (setup_hook runs before on_ready
# and only fires a single time per process, unlike on_ready which can
# re-fire on every reconnect).
# ============================================
@bot.event
async def setup_hook():
    await load_cogs()

    try:
        if GUILD_ID:
            # Guild sync = commands appear INSTANTLY (global sync can take ~1 hour)
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f'✅ Synced {len(synced)} slash commands to guild {GUILD_ID}!')
        else:
            synced = await bot.tree.sync()
            print(f'✅ Synced {len(synced)} slash commands globally (may take ~1h)!')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

# ============================================
# 🚀 Start everything
# ============================================
async def main():
    if not TOKEN:
        print("❌ DISCORD_TOKEN is not set! Check your .env file.")
        return
    start_keep_alive()  # satisfies Render's port scan (no-op locally)
    async with bot:
        # Cogs are loaded in setup_hook() before login.
        await bot.start(TOKEN)

asyncio.run(main())