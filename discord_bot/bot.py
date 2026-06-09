import os
import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
API_BASE = os.getenv("REAPER_API_URL", "http://localhost:8093")

if not TOKEN:
    print("ERROR: DISCORD_BOT_TOKEN not set in .env")
    sys.exit(1)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"☠️ REGIME REAPER bot online as {bot.user}")
    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
        else:
            synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Sync failed: {e}")


async def main():
    async with bot:
        from commands import search, analyze, settings, inventory, inspect
        await bot.add_cog(search.SearchCog(bot, API_BASE))
        await bot.add_cog(analyze.AnalyzeCog(bot, API_BASE))
        await bot.add_cog(settings.SettingsCog(bot, API_BASE))
        await bot.add_cog(inventory.InventoryCog(bot, API_BASE))
        await bot.add_cog(inspect.InspectCog(bot, API_BASE))
        await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
