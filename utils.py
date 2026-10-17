"""Petits outils partagés : rôles, permissions, messages privés, dates."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import discord

import agency_settings as S
import config

log = logging.getLogger("utils")
TZ = ZoneInfo(config.TIMEZONE)


def now_local() -> datetime:
    return datetime.now(TZ)


def week_start(day: date | None = None) -> date:
    day = day or now_local().date()
    return day - timedelta(days=day.weekday())


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def level_name(level: str | None, lang: str = "fr") -> str:
    if not level:
        return "—"
    info = S.LEVEL_INFO[level]
    return f"{info['emoji']} {info[lang]}"


def commission(level: str) -> int:
    return S.LEVEL_INFO[level]["commission"]


def is_staff(user: discord.abc.User) -> bool:
    if user.id == config.OWNER_ID:
        return True
    if isinstance(user, discord.Member):
        if user.guild_permissions.administrator:
            return True
        return any(r.id == config.STAFF_ROLE_ID for r in user.roles)
    return False


async def get_member(bot: discord.Client, user_id: int) -> discord.Member | None:
    guild = bot.get_guild(config.GUILD_ID)
    if guild is None:
        return None
    member = guild.get_member(user_id)
    if member is None:
        try:
            member = await guild.fetch_member(user_id)
        except discord.HTTPException:
            return None
    return member


async def dm(user: discord.abc.User, content: str | None = None, **kwargs) -> bool:
    """Envoie un message privé ; renvoie False si l'utilisateur les a fermés."""
    try:
        await user.send(content, **kwargs)
        return True
    except discord.HTTPException:
        log.info("MP impossible pour %s", user)
        return False


async def admin_channel(bot: discord.Client) -> discord.abc.Messageable | None:
    channel = bot.get_channel(config.ADMIN_CHANNEL_ID)
    if channel is None and config.ADMIN_CHANNEL_ID:
        try:
            channel = await bot.fetch_channel(config.ADMIN_CHANNEL_ID)
        except discord.HTTPException:
            return None
    return channel


async def _role_op(member: discord.Member, add: list[int], remove: list[int], reason: str) -> None:
    guild = member.guild
    to_add = [guild.get_role(r) for r in add if r]
    to_remove = [guild.get_role(r) for r in remove if r]
    to_add = [r for r in to_add if r and r not in member.roles]
    to_remove = [r for r in to_remove if r and r in member.roles]
    try:
        if to_remove:
            await member.remove_roles(*to_remove, reason=reason)
        if to_add:
            await member.add_roles(*to_add, reason=reason)
    except discord.Forbidden:
        log.warning("Permissions insuffisantes pour gérer les rôles de %s (place le rôle du bot au-dessus).", member)


async def give_candidate_role(member: discord.Member) -> None:
    await _role_op(member, [config.CANDIDATE_ROLE_ID], [], "Candidature")


async def apply_level_roles(member: discord.Member, level: str) -> None:
    others = [rid for lvl, rid in config.LEVEL_ROLE_IDS.items() if lvl != level]
    await _role_op(member, [config.CHATTER_ROLE_ID, config.LEVEL_ROLE_IDS.get(level, 0)],
                   [config.CANDIDATE_ROLE_ID, *others], f"Niveau {level}")


class StaticView(discord.ui.View):
    """Boutons traités par les listeners on_interaction (custom_id « cc: »).

    La vue est arrêtée dès sa création : discord.py ne la garde pas en mémoire,
    les clics restent gérés après un redémarrage grâce aux listeners.
    """

    def __init__(self):
        super().__init__(timeout=None)
        self.stop()


def bar(value: float | None, maximum: float = 100, width: int = 10) -> str:
    if value is None:
        return "░" * width
    filled = max(0, min(width, round(value / maximum * width)))
    return "█" * filled + "░" * (width - filled)
