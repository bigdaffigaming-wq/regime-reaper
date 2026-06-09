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
VERDICT_EMOJI = {"BUY NOW": "🟢", "NEGOTIATE HARD": "🟡", "MONITOR": "🔵", "WALK AWAY": "🔴"}


class AnalyzeCog(commands.Cog):
    def __init__(self, bot, api_base: str):
        self.bot = bot
        self.api = api_base

    @app_commands.command(name="reaper-analyze", description="Analyze a vehicle listing by text or listing ID")
    @app_commands.describe(
        listing_id="Listing ID already in the system",
        text="Paste listing text to analyze on the fly",
    )
    async def analyze(
        self,
        interaction: discord.Interaction,
        listing_id: Optional[int] = None,
        text: Optional[str] = None,
    ):
        await interaction.response.defer()

        if not listing_id and not text:
            await interaction.followup.send("Provide either a listing_id or paste listing text.")
            return

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if listing_id:
                    resp = await client.post(
                        f"{self.api}/analysis/{listing_id}",
                        headers={"x-user-role": "partner"},
                    )
                else:
                    resp = await client.post(
                        f"{self.api}/analysis/manual",
                        json={"title": text, "price": 0, "description": text},
                        headers={"x-user-role": "viewer"},
                    )
                data = resp.json()
        except Exception as e:
            await interaction.followup.send(f"Analysis failed: {e}")
            return

        verdict = data.get("verdict", "UNKNOWN")
        score = data.get("deal_score", 0)
        profit = data.get("expected_profit", 0)
        repairs = data.get("estimated_repair_cost", 0)
        resale = data.get("estimated_resale_value", 0)
        offer = data.get("recommended_offer", 0)

        color = VERDICT_COLOR.get(verdict, 0xD4AF37)
        em = discord.Embed(
            title=f"☠️ REAPER ANALYSIS — {VERDICT_EMOJI.get(verdict, '')} {verdict}",
            color=color,
        )
        em.add_field(name="Score", value=f"{score}/100", inline=True)
        em.add_field(name="Risk", value=data.get("risk_level", "?").upper(), inline=True)
        em.add_field(name="Expected Profit", value=f"${profit:,.0f}", inline=True)
        em.add_field(name="Est. Repairs", value=f"${repairs:,.0f}", inline=True)
        em.add_field(name="Est. Resale", value=f"${resale:,.0f}", inline=True)
        em.add_field(name="Recommended Offer", value=f"${offer:,.0f}", inline=True)

        import json
        try:
            red = json.loads(data.get("red_flags_json", "[]")) if isinstance(data.get("red_flags_json"), str) else data.get("red_flags", [])
            green = json.loads(data.get("green_flags_json", "[]")) if isinstance(data.get("green_flags_json"), str) else data.get("green_flags", [])
        except Exception:
            red, green = [], []

        if red:
            em.add_field(name="Red Flags", value="\n".join(f"• {r}" for r in red[:5]) or "None", inline=False)
        if green:
            em.add_field(name="Green Flags", value="\n".join(f"• {g}" for g in green[:5]) or "None", inline=False)

        summary = data.get("llm_summary") or data.get("summary")
        if summary:
            em.add_field(name="REAPER Notes", value=summary[:1000], inline=False)

        em.set_footer(text="REGIME REAPER • Harvest Value. Reap Profit.")
        await interaction.followup.send(embed=em)
