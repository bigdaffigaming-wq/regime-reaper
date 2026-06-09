import httpx
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional


class InventoryCog(commands.Cog):
    def __init__(self, bot, api_base: str):
        self.bot = bot
        self.api = api_base

    @app_commands.command(name="reaper-inventory", description="View active inventory")
    async def view_inventory(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.api}/inventory", headers={"x-user-role": "viewer"})
                items = resp.json()
        except Exception as e:
            await interaction.followup.send(f"Failed to fetch inventory: {e}")
            return

        if not items:
            await interaction.followup.send("No inventory items.")
            return

        em = discord.Embed(title="☠️ REAPER INVENTORY", color=0xD4AF37)
        for item in items[:10]:
            status = item.get("inventory_status", "?").upper()
            invested = item.get("total_invested", 0)
            profit = item.get("net_profit")
            profit_str = f" | Profit: ${profit:,.0f}" if profit is not None else ""
            em.add_field(
                name=f"#{item['id']} — {status}",
                value=f"Invested: ${invested:,.0f}{profit_str}",
                inline=False,
            )
        await interaction.followup.send(embed=em)

    @app_commands.command(name="reaper-bought", description="Mark a listing as bought and add to inventory")
    @app_commands.describe(listing_id="Listing ID", purchase_price="Price you paid")
    async def mark_bought(self, interaction: discord.Interaction, listing_id: int, purchase_price: float):
        await interaction.response.defer()
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api}/inventory/from-listing/{listing_id}",
                    json={"purchase_price": purchase_price},
                    headers={"x-user-role": "partner"},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            await interaction.followup.send(f"Failed: {e}")
            return

        await interaction.followup.send(
            f"✅ Listing #{listing_id} added to inventory. Total invested: ${data.get('total_invested', 0):,.0f}"
        )

    @app_commands.command(name="reaper-sold", description="Mark an inventory item as sold")
    @app_commands.describe(inventory_id="Inventory ID", sale_price="Final sale price")
    async def mark_sold(self, interaction: discord.Interaction, inventory_id: int, sale_price: float):
        await interaction.response.defer()
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api}/inventory/{inventory_id}/mark-sold",
                    json={"sale_price": sale_price},
                    headers={"x-user-role": "partner"},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            await interaction.followup.send(f"Failed: {e}")
            return

        profit = data.get("net_profit", 0)
        roi = data.get("roi_percent", 0)
        days = data.get("days_held", "?")
        emoji = "🟢" if profit > 0 else "🔴"
        await interaction.followup.send(
            f"{emoji} **SOLD** — Inventory #{inventory_id}\n"
            f"Sale Price: ${sale_price:,.0f} | Profit: ${profit:,.0f} | ROI: {roi:.1f}% | Days Held: {days}"
        )
