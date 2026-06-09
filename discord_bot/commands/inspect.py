import httpx
import discord
from discord import app_commands
from discord.ext import commands

INSPECTION_QUESTIONS = [
    ("Title in seller name?", "title_ok"),
    ("Any check engine light?", "cel"),
    ("Any ABS or airbag lights?", "abs_airbag"),
    ("AC blows cold?", "ac_cold"),
    ("Transmission shifts smooth?", "trans_smooth"),
    ("Any overheating signs?", "overheating"),
    ("Any leaks under car?", "leaks"),
    ("Tires in good shape?", "tires_ok"),
    ("Brakes feel good?", "brakes_ok"),
    ("Test drive smooth?", "test_drive_ok"),
    ("OBD scan clean?", "obd_clean"),
]

# Score adjustments per answer (question_key: (yes_adj, no_adj))
SCORE_ADJUSTMENTS = {
    "title_ok": (2, -10),
    "cel": (-3, 0),
    "abs_airbag": (-2, 0),
    "ac_cold": (2, -3),
    "trans_smooth": (2, -15),
    "overheating": (-15, 2),
    "leaks": (-4, 2),
    "tires_ok": (1, -3),
    "brakes_ok": (1, -2),
    "test_drive_ok": (3, -5),
    "obd_clean": (3, -3),
}


class InspectView(discord.ui.View):
    def __init__(self, listing_id: int, api_base: str):
        super().__init__(timeout=300)
        self.listing_id = listing_id
        self.api = api_base
        self.current = 0
        self.answers: dict[str, bool] = {}
        self.score_adj = 0

    def current_question(self) -> tuple[str, str]:
        return INSPECTION_QUESTIONS[self.current]

    async def ask_next(self, interaction: discord.Interaction):
        if self.current >= len(INSPECTION_QUESTIONS):
            await self.finish(interaction)
            return

        question, key = self.current_question()
        em = discord.Embed(
            title=f"☠️ INSPECTION — Listing #{self.listing_id}",
            description=f"**Question {self.current + 1}/{len(INSPECTION_QUESTIONS)}**\n\n{question}",
            color=0xD4AF37,
        )
        self.clear_items()
        yes_btn = discord.ui.Button(label="Yes ✅", style=discord.ButtonStyle.success, custom_id="yes")
        no_btn = discord.ui.Button(label="No ❌", style=discord.ButtonStyle.danger, custom_id="no")

        yes_btn.callback = self.on_yes
        no_btn.callback = self.on_no
        self.add_item(yes_btn)
        self.add_item(no_btn)

        await interaction.response.edit_message(embed=em, view=self)

    async def on_yes(self, interaction: discord.Interaction):
        _, key = self.current_question()
        self.answers[key] = True
        adj = SCORE_ADJUSTMENTS.get(key, (0, 0))[0]
        self.score_adj += adj
        self.current += 1
        await self.ask_next(interaction)

    async def on_no(self, interaction: discord.Interaction):
        _, key = self.current_question()
        self.answers[key] = False
        adj = SCORE_ADJUSTMENTS.get(key, (0, 0))[1]
        self.score_adj += adj
        self.current += 1
        await self.ask_next(interaction)

    async def finish(self, interaction: discord.Interaction):
        red_flags = []
        green_flags = []

        if not self.answers.get("title_ok"):
            red_flags.append("Title NOT in seller name")
        if self.answers.get("cel"):
            red_flags.append("Check engine light ON")
        if self.answers.get("abs_airbag"):
            red_flags.append("ABS/Airbag lights ON")
        if not self.answers.get("ac_cold"):
            red_flags.append("AC not cold")
        if not self.answers.get("trans_smooth"):
            red_flags.append("Transmission not smooth")
        if self.answers.get("overheating"):
            red_flags.append("Overheating signs present — WALK AWAY")
        if self.answers.get("leaks"):
            red_flags.append("Leaks detected")
        if not self.answers.get("tires_ok"):
            red_flags.append("Tires need replacement")
        if not self.answers.get("brakes_ok"):
            red_flags.append("Brakes need attention")
        if not self.answers.get("test_drive_ok"):
            red_flags.append("Test drive issues noted")
        if not self.answers.get("obd_clean"):
            red_flags.append("OBD codes present")

        if self.answers.get("title_ok"):
            green_flags.append("Title in seller name ✅")
        if self.answers.get("ac_cold"):
            green_flags.append("AC blows cold ✅")
        if self.answers.get("trans_smooth"):
            green_flags.append("Transmission smooth ✅")
        if self.answers.get("obd_clean"):
            green_flags.append("OBD scan clean ✅")
        if self.answers.get("test_drive_ok"):
            green_flags.append("Test drive clean ✅")

        verdict = "WALK AWAY" if "Overheating signs present — WALK AWAY" in red_flags else (
            "NEGOTIATE HARD" if red_flags else "BUY NOW"
        )

        color = {"BUY NOW": 0x6AFF4F, "NEGOTIATE HARD": 0xFF9F1C, "WALK AWAY": 0xC1121F}.get(verdict, 0xD4AF37)

        em = discord.Embed(
            title=f"☠️ INSPECTION COMPLETE — Listing #{self.listing_id}",
            description=f"**Score Adjustment:** {self.score_adj:+d} points\n**Post-Inspection Verdict:** {verdict}",
            color=color,
        )
        if red_flags:
            em.add_field(name="Red Flags", value="\n".join(f"• {r}" for r in red_flags), inline=False)
        if green_flags:
            em.add_field(name="Green Flags", value="\n".join(f"• {g}" for g in green_flags), inline=False)
        em.set_footer(text="REGIME REAPER • Harvest Value. Reap Profit.")

        self.clear_items()
        await interaction.response.edit_message(embed=em, view=self)


class InspectCog(commands.Cog):
    def __init__(self, bot, api_base: str):
        self.bot = bot
        self.api = api_base

    @app_commands.command(name="reaper-inspect", description="Run interactive inspection checklist for a listing")
    @app_commands.describe(listing_id="Listing ID to inspect")
    async def inspect(self, interaction: discord.Interaction, listing_id: int):
        view = InspectView(listing_id, self.api)
        em = discord.Embed(
            title=f"☠️ INSPECTION START — Listing #{listing_id}",
            description="Starting inspection checklist. Answer each question honestly.",
            color=0xD4AF37,
        )
        await interaction.response.send_message(embed=em, view=view)
        await view.ask_next(interaction)
