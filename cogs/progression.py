"""Étape 4 : suivi, objectifs, bilans hebdomadaires et promotions."""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

import agency_settings as S
import ai
import db
import scoring
from i18n import t
from utils import TZ, StaticView, admin_channel, bar, commission, dm, get_member, level_name, now_local, parse_ts, week_start

log = logging.getLogger("progression")
CHECK_EN = {
    "Ancienneté au niveau (semaines)": "Weeks at current level",
    "Taux de conversion": "Conversion rate",
    "Qualité des conversations": "Conversation quality",
    "Ponctualité": "Punctuality",
    "CA moyen par semaine": "Average weekly revenue",
}


def _label(label: str, lang: str) -> str:
    return CHECK_EN.get(label, label) if lang == "en" else label


def _fmt(value, suffix=""):
    return "—" if value is None else f"{value:g}{suffix}"


def perf_line(summary: scoring.PerfSummary, lang: str) -> str:
    return t("perf_line", lang, revenue=f"{summary.revenue_total:g} {S.CURRENCY}", sales=summary.sales,
             conv=_fmt(summary.conversion, " %"), quality=_fmt(summary.quality, "/100"),
             punct=_fmt(summary.punctuality, "/100"))


class Progression(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.weekly_loop.start()

    def cog_unload(self):
        self.weekly_loop.cancel()

    # --- Calculs ---------------------------------------------------------
    async def evaluate(self, chatter: dict) -> tuple[scoring.PerfSummary, scoring.PromotionCheck]:
        since_level = parse_ts(chatter["level_since"]) or datetime.now(timezone.utc)
        days_at_level = (datetime.now(timezone.utc) - since_level).days
        window = min(S.PERFORMANCE_WINDOW_DAYS, max(7, days_at_level))
        since = max(now_local().date() - timedelta(days=window), since_level.astimezone(TZ).date())
        rows = await db.performance_since(chatter["discord_id"], since)
        summary = scoring.summarize(rows, window)
        return summary, scoring.promotion_check(chatter["level"], days_at_level // 7, summary, bool(rows))

    async def weaknesses(self, user_id: int) -> list[str]:
        test = await db.latest_test(user_id)
        if not test:
            return []
        found = []
        for key in ("simulation", "vente", "objections"):
            found += test["sections"].get(key, {}).get("weaknesses", [])
        return found[:3]

    def promotion_card(self, chatter: dict, check: scoring.PromotionCheck) -> dict:
        embed = discord.Embed(
            title=f"⬆️ Promotion possible · {chatter['username']}",
            description=f"<@{chatter['discord_id']}> : {level_name(chatter['level'])} → **{level_name(check.target)}**",
            color=discord.Color.gold())
        embed.add_field(name="Critères", value="\n".join(f"✅ {label} : {detail}" for label, _, detail in check.checks))
        view = StaticView()
        view.add_item(discord.ui.Button(label=f"Promouvoir en {S.LEVEL_INFO[check.target]['fr']}", emoji="⬆️",
                                        style=discord.ButtonStyle.success,
                                        custom_id=f"cc:adm:promote:{chatter['discord_id']}:{check.target}"))
        view.add_item(discord.ui.Button(label="Autre niveau", emoji="🎚️", style=discord.ButtonStyle.secondary,
                                        custom_id=f"cc:adm:setlevel:{chatter['discord_id']}"))
        return {"embed": embed, "view": view}

    # --- Commandes chatteur ----------------------------------------------
    @app_commands.command(name="mon-niveau", description="Ton niveau, ton score et ta progression · Your level")
    async def mon_niveau(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        chatter = await db.get_chatter(interaction.user.id)
        if chatter is None:
            cand = await db.get_candidate(interaction.user.id)
            return await interaction.followup.send(t("not_chatter", cand["lang"] if cand else "fr"), ephemeral=True)
        lang, level = chatter["lang"], chatter["level"]
        summary, check = await self.evaluate(chatter)
        has_data = summary.messages or summary.revenue_total or summary.sales
        embed = discord.Embed(title=f"{level_name(level, lang)} · {interaction.user.display_name}",
                              color=discord.Color.from_rgb(233, 30, 99))
        embed.add_field(name=t("lbl_level", lang), value=level_name(level, lang))
        embed.add_field(name=t("lbl_commission", lang), value=f"{commission(level)} %")
        embed.add_field(name=t("lbl_recruit", lang), value=_fmt(chatter["recruit_score"] and
                                                                 float(chatter["recruit_score"]), "/100"))
        embed.add_field(name=t("lbl_perf", lang), value=perf_line(summary, lang) if has_data else t("lbl_nodata", lang),
                        inline=False)
        if check.target:
            done = sum(ok for _, ok, _ in check.checks)
            lines = [f"`{bar(done, len(check.checks))}` {done}/{len(check.checks)}"]
            lines += [f"{'✅' if ok else '⬜'} {_label(label, lang)} : {detail}" for label, ok, detail in check.checks]
            embed.add_field(name=t("lbl_next", lang, level=level_name(check.target, lang)),
                            value="\n".join(lines), inline=False)
        else:
            embed.add_field(name="💎", value=t("lbl_top", lang), inline=False)
        work = [_label(label, lang) for label, ok, _ in check.checks if not ok and "semaines" not in label]
        work += await self.weaknesses(interaction.user.id)
        if work:
            embed.add_field(name=t("lbl_work", lang), value="\n".join(f"• {w}" for w in work[:5])[:1024], inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def objectives_embed(self, chatter: dict) -> discord.Embed:
        lang = chatter["lang"]
        _, check = await self.evaluate(chatter)
        set_by_staff = await db.objectives_for(chatter["discord_id"], week_start())
        embed = discord.Embed(title=t("objectives_title", lang), color=discord.Color.teal())
        if set_by_staff:
            embed.add_field(name=t("objectives_set", lang), inline=False,
                            value="\n".join(f"🎯 {o['text']}" for o in set_by_staff)[:1024])
        if check.target:
            auto = [f"📈 {_label(label, lang)} : {detail}" for label, ok, detail in check.checks if not ok]
            if auto:
                embed.add_field(name=t("objectives_auto", lang, level=level_name(check.target, lang)),
                                value="\n".join(auto)[:1024], inline=False)
        work = await self.weaknesses(chatter["discord_id"])
        if work:
            embed.add_field(name=t("lbl_work", lang), value="\n".join(f"• {w}" for w in work)[:1024], inline=False)
        if not embed.fields:
            embed.description = t("no_objectives", lang)
        return embed

    @app_commands.command(name="objectifs", description="Tes objectifs de la semaine · Your weekly goals")
    async def objectifs(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        chatter = await db.get_chatter(interaction.user.id)
        if chatter is None:
            return await interaction.followup.send(t("not_chatter"), ephemeral=True)
        await interaction.followup.send(embed=await self.objectives_embed(chatter), ephemeral=True)

    # --- Bilan hebdomadaire ----------------------------------------------
    @tasks.loop(time=time(*S.WEEKLY_REPORT_HOUR, tzinfo=TZ))
    async def weekly_loop(self):
        if now_local().weekday() == S.WEEKLY_REPORT_DAY:
            try:
                await self.weekly_report()
            except Exception:
                log.exception("Bilan hebdomadaire interrompu")

    @weekly_loop.before_loop
    async def _wait_ready(self):
        await self.bot.wait_until_ready()

    async def weekly_report(self) -> int:
        start = week_start() - timedelta(days=7)
        rows = await db.performance_since(None, start)
        by_member: dict[int, list] = defaultdict(list)
        for row in rows:
            by_member[row["discord_id"]].append(row)

        board, no_data, ready, sent = [], [], [], 0
        for chatter in await db.list_chatters():
            uid, lang = chatter["discord_id"], chatter["lang"]
            week = scoring.summarize(by_member.get(uid, []), 7)
            _, check = await self.evaluate(chatter)
            if by_member.get(uid):
                board.append((week.revenue_total, chatter, week))
            else:
                no_data.append(f"<@{uid}>")
            if check.eligible:
                ready.append((chatter, check))

            member = await get_member(self.bot, uid)
            if member is None:
                continue
            embed = discord.Embed(title=t("weekly_title", lang), color=discord.Color.teal(),
                                  description=perf_line(week, lang) if by_member.get(uid) else t("lbl_nodata", lang))
            objectives = await self.objectives_embed(chatter)
            for field in objectives.fields:
                embed.add_field(name=field.name, value=field.value, inline=False)
            if check.eligible:
                embed.add_field(name="🔥", value=t("promo_ready", lang, level=level_name(check.target, lang)),
                                inline=False)
            advice = await ai.weekly_advice(member.display_name, lang, perf_line(week, lang),
                                            await self.weaknesses(uid))
            if advice:
                embed.add_field(name=t("weekly_coach", lang), value=advice[:1024], inline=False)
            if await dm(member, embed=embed):
                sent += 1

        channel = await admin_channel(self.bot)
        if channel:
            board.sort(key=lambda item: item[0], reverse=True)
            lines = [f"**{i}.** <@{c['discord_id']}> · {w.revenue_total:g} {S.CURRENCY} · conv. "
                     f"{_fmt(w.conversion, ' %')} · qualité {_fmt(w.quality)}" for i, (_, c, w) in enumerate(board[:15], 1)]
            embed = discord.Embed(title=f"📊 Bilan de la semaine du {start:%d/%m}",
                                  description="\n".join(lines) or "Aucune donnée importée pour cette semaine.",
                                  color=discord.Color.teal())
            if no_data:
                embed.add_field(name="Sans données", value=", ".join(no_data)[:1024], inline=False)
            embed.set_footer(text=f"{sent} bilan(s) envoyé(s) en MP · import des ventes : /admin import")
            await channel.send(embed=embed)
            for chatter, check in ready:
                await channel.send(**self.promotion_card(chatter, check))
        return sent


async def setup(bot: commands.Bot):
    await bot.add_cog(Progression(bot))
