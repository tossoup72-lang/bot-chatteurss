"""Étape 1 : candidature (/postuler et bouton du panneau de recrutement)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

import agency_settings as S
import db
import scoring
from i18n import t
from utils import StaticView, admin_channel, give_candidate_role, parse_ts

log = logging.getLogger("recruitment")


def start_test_view(lang: str) -> discord.ui.View:
    """Bouton traité par le module Tests (custom_id persistant, survit aux redémarrages)."""
    view = StaticView()
    view.add_item(discord.ui.Button(label=t("btn_start_test", lang), emoji="🧪",
                                    style=discord.ButtonStyle.success, custom_id="cc:starttest"))
    return view


def apply_panel() -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        title="💼 Recrutement chatteurs · Chatter recruitment",
        description=(
            "Tu as de l'expérience en chatting sur MYM, OnlyFans ou Fansly ? Rejoins l'équipe.\n"
            "Rémunération à partir de **8 %**, évolutive selon ton niveau.\n\n"
            "Experienced chatter on MYM, OnlyFans or Fansly? Join the team.\n"
            "Pay starts at **8%** and grows with your level.\n\n"
            "Candidature → test → validation → intégration."
        ),
        color=discord.Color.from_rgb(233, 30, 99),
    )
    view = StaticView()
    view.add_item(discord.ui.Button(label="Postuler · Apply", emoji="✍️",
                                    style=discord.ButtonStyle.primary, custom_id="cc:apply"))
    return embed, view


class ApplicationModal(discord.ui.Modal):
    def __init__(self, cog: "Recruitment", lang: str):
        super().__init__(title=t("modal_title", lang), timeout=1200)
        self.cog, self.lang = cog, lang
        self.experience = discord.ui.TextInput(label=t("q_experience", lang), placeholder=t("q_experience_ph", lang),
                                               max_length=80)
        self.platforms = discord.ui.TextInput(label=t("q_platforms", lang), placeholder=t("q_platforms_ph", lang),
                                              max_length=150)
        self.hours = discord.ui.TextInput(label=t("q_hours", lang), placeholder=t("q_hours_ph", lang), max_length=150)
        self.best = discord.ui.TextInput(label=t("q_best", lang), style=discord.TextStyle.paragraph, max_length=600)
        self.motivation = discord.ui.TextInput(label=t("q_motivation", lang), style=discord.TextStyle.paragraph,
                                               max_length=600)
        for item in (self.experience, self.platforms, self.hours, self.best, self.motivation):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.cog.handle_application(interaction, self.lang, {
            "experience": self.experience.value, "platforms": self.platforms.value,
            "hours": self.hours.value, "best": self.best.value, "motivation": self.motivation.value,
        })


class ConfirmView(discord.ui.View):
    def __init__(self, cog: "Recruitment", lang: str):
        super().__init__(timeout=900)
        self.cog, self.lang = cog, lang
        button = discord.ui.Button(label=t("btn_confirm", lang), style=discord.ButtonStyle.success, emoji="✅")
        button.callback = self.confirm
        self.add_item(button)

    async def confirm(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ApplicationModal(self.cog, self.lang))


class LangView(discord.ui.View):
    def __init__(self, cog: "Recruitment"):
        super().__init__(timeout=900)
        self.cog = cog
        for lang, label, emoji in (("fr", "Français", "🇫🇷"), ("en", "English", "🇬🇧")):
            button = discord.ui.Button(label=label, emoji=emoji, style=discord.ButtonStyle.secondary)
            button.callback = self._pick(lang)
            self.add_item(button)

    def _pick(self, lang: str):
        async def callback(interaction: discord.Interaction):
            await interaction.response.edit_message(content=t("apply_intro", lang), view=ConfirmView(self.cog, lang))
        return callback


class Recruitment(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _blocked(self, user_id: int) -> tuple[str | None, str, dict | None]:
        """(message de blocage ou None, langue, candidature)."""
        cand = await db.get_candidate(user_id)
        chatter = await db.get_chatter(user_id)
        lang = (cand or chatter or {}).get("lang", "fr")
        if chatter and chatter["active"]:
            return t("already_chatter", lang), lang, cand
        if not cand:
            return None, lang, None
        status = cand["status"]
        if status == "accepted":
            return t("already_chatter", lang), lang, cand
        if status == "rejected":
            changed = parse_ts(cand["updated_at"]) or datetime.now(timezone.utc)
            left = S.REAPPLY_COOLDOWN_DAYS - (datetime.now(timezone.utc) - changed).days
            if left > 0:
                return t("cooldown", lang, days=left), lang, cand
            return None, lang, None  # peut repostuler
        if status in ("applied", "ineligible"):
            return t("already_pending", lang), lang, cand
        if status == "testing":
            return t("test_running", lang), lang, cand
        if status == "tested":
            return t("test_review", lang), lang, cand
        return None, lang, cand  # "allowed" : peut lancer le test

    async def start(self, interaction: discord.Interaction):
        message, lang, cand = await self._blocked(interaction.user.id)
        if message:
            await interaction.response.send_message(message, ephemeral=True)
        elif cand and cand["status"] == "allowed":
            await interaction.response.send_message(t("apply_ok", lang), view=start_test_view(lang), ephemeral=True)
        else:
            await interaction.response.send_message(t("choose_lang"), view=LangView(self), ephemeral=True)

    @app_commands.command(name="postuler", description="Postuler comme chatteur · Apply as a chatter")
    @app_commands.guild_only()
    async def postuler(self, interaction: discord.Interaction):
        await self.start(interaction)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type is discord.InteractionType.component and \
                (interaction.data or {}).get("custom_id") == "cc:apply":
            await self.start(interaction)

    async def handle_application(self, interaction: discord.Interaction, lang: str, answers: dict):
        user = interaction.user
        months = scoring.parse_months(answers["experience"])
        hours = scoring.parse_int(answers["hours"])
        ok, reasons = scoring.eligibility(months, hours, answers["platforms"])
        previous = await db.get_candidate(user.id)
        await db.upsert_candidate({
            "discord_id": user.id, "username": str(user), "lang": lang,
            "experience_months": months, "platforms": answers["platforms"], "hours_per_week": hours,
            "availability": answers["hours"], "best_result": answers["best"], "motivation": answers["motivation"],
            "eligible": ok, "eligibility_notes": "\n".join(reasons) or None,
            "status": "allowed" if ok else "ineligible",
            "test_attempts": 0, "decision_by": None, "decision_reason": None,
            "applied_at": datetime.now(timezone.utc).isoformat(),
        })
        if isinstance(user, discord.Member):
            await give_candidate_role(user)

        if ok:
            await interaction.followup.send(t("apply_ok", lang), view=start_test_view(lang), ephemeral=True)
        else:
            await interaction.followup.send(
                t("apply_ineligible", lang, reasons="\n".join(f"• {r}" for r in reasons)), ephemeral=True)

        channel = await admin_channel(self.bot)
        if channel is None:
            return
        embed = discord.Embed(
            title="📝 Nouvelle candidature" + (" (nouvelle tentative)" if previous else ""),
            description=f"{user.mention} · `{user}` · langue **{lang.upper()}**",
            color=discord.Color.green() if ok else discord.Color.orange(),
        )
        embed.add_field(name="Expérience", value=f"{answers['experience']} → {months or 0} mois", inline=True)
        embed.add_field(name="Disponibilité", value=answers["hours"][:1024], inline=True)
        embed.add_field(name="Plateformes", value=answers["platforms"][:1024], inline=False)
        embed.add_field(name="Meilleur résultat", value=answers["best"][:1024], inline=False)
        embed.add_field(name="Motivation", value=answers["motivation"][:1024], inline=False)
        embed.add_field(name="Éligibilité", value="✅ Profil conforme, test débloqué" if ok
                        else "❌ " + "\n".join(reasons), inline=False)
        view = StaticView()
        if not ok:
            view.add_item(discord.ui.Button(label="Autoriser le test", emoji="🟢", style=discord.ButtonStyle.success,
                                            custom_id=f"cc:adm:allow:{user.id}"))
        view.add_item(discord.ui.Button(label="Refuser", emoji="❌", style=discord.ButtonStyle.danger,
                                        custom_id=f"cc:adm:reject:{user.id}"))
        await channel.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Recruitment(bot))
