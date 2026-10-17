"""Accueil et parcours d'intégration : salons à lire, fiches modèles, plan de chatting."""
from __future__ import annotations

import logging
from datetime import datetime, time, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

import agency_settings as S
import config
import db
from i18n import t
from utils import TZ, StaticView, admin_channel, dm, get_member, parse_ts

log = logging.getLogger("onboarding")
STEP_KEYS = [s["key"] for s in S.ONBOARDING_STEPS]


def _step_text(step: dict, lang: str) -> tuple[str, str]:
    title, description = step.get(lang) or step["fr"]
    if step.get("channel_id"):
        description = f"<#{step['channel_id']}> · {description}"
    return title, description


def path_message(lang: str, done: set[str]) -> dict:
    embed = discord.Embed(title=f"🧭 {t('onb_title', lang)}", description=t("onb_intro", lang),
                          color=discord.Color.from_rgb(233, 30, 99))
    view = StaticView()
    for i, step in enumerate(S.ONBOARDING_STEPS, 1):
        title, description = _step_text(step, lang)
        mark = "✅" if step["key"] in done else f"{i}."
        embed.add_field(name=f"{mark} {title}", value=description, inline=False)
        view.add_item(discord.ui.Button(
            label=f"{i}. {title}"[:80], emoji="✅" if step["key"] in done else None,
            style=discord.ButtonStyle.success if step["key"] in done else discord.ButtonStyle.secondary,
            custom_id=f"cc:onb:{step['key']}", disabled=step["key"] in done))
    embed.set_footer(text=f"{len(done & set(STEP_KEYS))}/{len(STEP_KEYS)}")
    return {"embed": embed, "view": view}


class Onboarding(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_loop.start()

    def cog_unload(self):
        self.daily_loop.cancel()

    async def send_path(self, member: discord.abc.User, lang: str) -> bool:
        done = await db.onboarding_done(member.id)
        return await dm(member, **path_message(lang, done))

    @app_commands.command(name="parcours", description="Ton parcours d'intégration · Your onboarding path")
    async def parcours(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        chatter = await db.get_chatter(interaction.user.id)
        if chatter is None:
            return await interaction.followup.send(t("onb_only_chatters"), ephemeral=True)
        done = await db.onboarding_done(interaction.user.id)
        await interaction.followup.send(ephemeral=True, **path_message(chatter["lang"], done))

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type is not discord.InteractionType.component:
            return
        cid = (interaction.data or {}).get("custom_id", "")
        if not cid.startswith("cc:onb:"):
            return
        await interaction.response.defer()
        chatter = await db.get_chatter(interaction.user.id)
        if chatter is None:
            return await interaction.followup.send(t("onb_only_chatters"), ephemeral=True)
        lang, key = chatter["lang"], cid.split(":", 2)[2]
        await db.mark_onboarding(interaction.user.id, key)
        done = await db.onboarding_done(interaction.user.id)
        await interaction.edit_original_response(**path_message(lang, done))
        step = next((s for s in S.ONBOARDING_STEPS if s["key"] == key), None)
        if step:
            title, _ = _step_text(step, lang)
            await interaction.followup.send(t("onb_step_done", lang, title=title, done=len(done & set(STEP_KEYS)),
                                              total=len(STEP_KEYS)), ephemeral=True)
        if set(STEP_KEYS) <= done:
            await interaction.followup.send(t("onb_complete", lang))
            channel = await admin_channel(self.bot)
            if channel:
                await channel.send(f"🧭 {interaction.user.mention} a terminé son parcours d'intégration : "
                                   "prêt(e) pour un premier shift.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != config.GUILD_ID or not config.WELCOME_CHANNEL_ID or member.bot:
            return
        channel = member.guild.get_channel(config.WELCOME_CHANNEL_ID)
        if channel and config.RECRUITMENT_CHANNEL_ID:
            where = f"<#{config.RECRUITMENT_CHANNEL_ID}>"
            await channel.send(t("welcome_join", "fr", mention=member.mention, channel=where) + "\n" +
                               t("welcome_join", "en", mention=member.mention, channel=where))

    # --- Relances quotidiennes -------------------------------------------
    @tasks.loop(time=time(*S.DAILY_REMINDER_HOUR, tzinfo=TZ))
    async def daily_loop(self):
        try:
            await self.send_reminders()
        except Exception:
            log.exception("Relances quotidiennes interrompues")

    async def send_reminders(self):
        now = datetime.now(timezone.utc)
        for chatter in await db.list_chatters():
            hired = parse_ts(chatter["hired_at"]) or now
            days = (now - hired).days
            if not 1 <= days <= S.ONBOARDING_REMINDER_DAYS or days % 2:
                continue
            left = len(set(STEP_KEYS) - await db.onboarding_done(chatter["discord_id"]))
            member = await get_member(self.bot, chatter["discord_id"]) if left else None
            if member:
                await dm(member, t("onb_reminder", chatter["lang"], left=left))
        for cand in await db.list_candidates(["allowed"], limit=200):
            days = (now - (parse_ts(cand["updated_at"]) or now)).days
            if days in (2, 5):
                member = await get_member(self.bot, cand["discord_id"])
                if member:
                    await dm(member, t("test_reminder", cand["lang"]))

    @daily_loop.before_loop
    async def _wait_ready(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Onboarding(bot))
