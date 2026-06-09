import httpx
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional


class SettingsCog(commands.Cog):
    def __init__(self, bot, api_base: str):
        self.bot = bot
        self.api = api_base

    @app_commands.command(name="reaper-settings", description="View current REAPER settings")
    async def view_settings(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.api}/settings", headers={"x-user-role": "viewer"})
                s = resp.json()
        except Exception as e:
            await interaction.followup.send(f"Failed to fetch settings: {e}")
            return

        em = discord.Embed(title="☠️ REAPER SETTINGS", color=0xD4AF37)
        em.add_field(name="Max Price", value=f"${s.get('max_price', '?'):,}", inline=True)
        em.add_field(name="Min Price", value=f"${s.get('min_price', '?'):,}", inline=True)
        em.add_field(name="Max Mileage", value=f"{s.get('max_mileage', '?'):,}", inline=True)
        em.add_field(name="Min Year", value=str(s.get("min_year", "?")), inline=True)
        em.add_field(name="Target Profit", value=f"${s.get('target_profit', '?'):,}", inline=True)
        em.add_field(name="Alert Score", value=str(s.get("alert_score_threshold", "?")), inline=True)
        em.add_field(name="Location", value=s.get("default_location", "?"), inline=True)
        em.add_field(name="Radius", value=f"{s.get('radius_miles', '?')} miles", inline=True)
        await interaction.followup.send(embed=em)

    @app_commands.command(name="reaper-set", description="Update a REAPER setting")
    @app_commands.describe(
        key="Setting name (max_price, max_mileage, location, radius, profit_target, alert_score)",
        value="New value",
    )
    async def set_setting(self, interaction: discord.Interaction, key: str, value: str):
        await interaction.response.defer()

        field_map = {
            "max_price": ("max_price", int),
            "min_price": ("min_price", int),
            "max_mileage": ("max_mileage", int),
            "location": ("default_location", str),
            "radius": ("radius_miles", int),
            "profit_target": ("target_profit", int),
            "alert_score": ("alert_score_threshold", int),
            "min_year": ("min_year", int),
        }

        if key not in field_map:
            await interaction.followup.send(f"Unknown setting: `{key}`. Valid: {', '.join(field_map)}")
            return

        db_field, cast = field_map[key]
        try:
            cast_value = cast(value)
        except ValueError:
            await interaction.followup.send(f"Invalid value `{value}` for setting `{key}`")
            return

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.patch(
                    f"{self.api}/settings",
                    json={db_field: cast_value},
                    headers={"x-user-role": "partner"},
                )
                resp.raise_for_status()
        except Exception as e:
            await interaction.followup.send(f"Failed to update setting: {e}")
            return

        await interaction.followup.send(f"✅ `{key}` updated to `{value}`")
