import httpx
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

VERDICT_COLOR = {
    "BUY NOW": 0x6AFF4F,
    "NEGOTIATE HARD": 0xFF9F1C,
    "MONITOR": 0x5865F2,
    "WALK AWAY": 0xC1121F,
}
VERDICT_EMOJI = {
    "BUY NOW": "🟢",
    "NEGOTIATE HARD": "🟡",
    "MONITOR": "🔵",
    "WALK AWAY": "🔴",
}


class SearchCog(commands.Cog):
    def __init__(self, bot, api_base: str):
        self.bot = bot
        self.api = api_base

    @app_commands.command(name="reaper-search", description="Search for vehicle listings across sources")
    @app_commands.describe(
        query="Search query (e.g. Toyota Camry)",
        location="City and state (default: Tampa FL)",
        max_price="Maximum price",
        radius="Search radius in miles",
    )
    async def search(
        self,
        interaction: discord.Interaction,
        query: str,
        location: Optional[str] = "Tampa, FL",
        max_price: Optional[int] = 2500,
        radius: Optional[int] = 75,
    ):
        await interaction.response.defer()

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.api}/search",
                    json={"query": query, "location": location, "max_price": max_price, "radius": radius},
                    headers={"x-user-role": "partner"},
                )
                data = resp.json()
        except Exception as e:
            await interaction.followup.send(f"Search failed: {e}")
            return

        listings = data.get("listings", [])
        if not listings:
            await interaction.followup.send("No results found. Try a broader search.")
            return

        embeds = []
        for l in listings[:5]:
            color = VERDICT_COLOR.get(l.get("verdict", ""), 0xD4AF37)
            em = discord.Embed(
                title=f"☠️ {l.get('title', 'Unknown')}",
                color=color,
                url=l.get("url") or discord.Embed.Empty,
            )
            em.add_field(name="Source", value=l.get("source", "?"), inline=True)
            em.add_field(name="Price", value=f"${l.get('price', 0):,.0f}", inline=True)
            em.add_field(name="Mileage", value=f"{l.get('mileage', 'N/A'):,}" if l.get("mileage") else "N/A", inline=True)
            em.add_field(name="Location", value=l.get("location", "?"), inline=True)
            embeds.append(em)

        await interaction.followup.send(
            content=f"☠️ **REAPER SEARCH** — `{query}` | {len(listings)} results found",
            embeds=embeds,
        )
