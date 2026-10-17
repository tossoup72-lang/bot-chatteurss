"""Décisions partagées entre les boutons et les commandes /admin."""
from __future__ import annotations

import logging

import discord

import agency_settings as S
import db
from i18n import t
from utils import apply_level_roles, commission, dm, get_member, level_name

log = logging.getLogger("services")


async def accept_candidate(bot: discord.Client, user_id: int, level: str, by: discord.abc.User) -> str:
    cand = await db.get_candidate(user_id)
    if cand is None:
        return "Candidat introuvable."
    if cand["status"] == "accepted":
        return "Ce candidat est déjà recruté."
    if cand["status"] == "testing":
        return f"<@{user_id}> passe son test en ce moment : attends le résultat pour décider."
    test = await db.latest_test(user_id)
    lang = cand["lang"]
    await db.update_candidate(user_id, status="accepted", decision_by=by.id, decision_reason=f"Niveau {level}")
    existing = await db.get_chatter(user_id)
    await db.upsert_chatter({
        "discord_id": user_id, "username": cand["username"], "lang": lang, "level": level,
        "recruit_score": test["total_score"] if test else None, "active": True,
    })
    await db.add_level_history(user_id, existing["level"] if existing else None, level, by.id, "Recrutement")

    member = await get_member(bot, user_id)
    if member is None:
        return f"Recruté au niveau {level_name(level)}, mais le membre a quitté le serveur."
    await apply_level_roles(member, level)
    await dm(member, t("accepted_dm", lang, name=member.display_name, level=level_name(level, lang),
                       commission=commission(level)))
    onboarding = bot.get_cog("Onboarding")
    if onboarding:
        await onboarding.send_path(member, lang)
    return f"✅ {member.mention} recruté(e) au niveau {level_name(level)} par {by.mention}."


async def reject_candidate(bot: discord.Client, user_id: int, by: discord.abc.User, reason: str = "") -> str:
    cand = await db.get_candidate(user_id)
    if cand is None:
        return "Candidat introuvable."
    if cand["status"] == "accepted":
        return f"<@{user_id}> est déjà recruté(e) : utilise /admin desactiver pour le retirer de l'équipe."
    if cand["status"] == "testing":
        return f"<@{user_id}> passe son test en ce moment : attends le résultat pour décider."
    await db.update_candidate(user_id, status="rejected", decision_by=by.id, decision_reason=reason or None)
    member = await get_member(bot, user_id)
    if member:
        await dm(member, t("rejected_dm", cand["lang"], days=S.REAPPLY_COOLDOWN_DAYS))
    return f"❌ Candidature de <@{user_id}> refusée par {by.mention}." + (f" Motif : {reason}" if reason else "")


async def allow_test(bot: discord.Client, user_id: int, by: discord.abc.User) -> str:
    cand = await db.get_candidate(user_id)
    if cand is None:
        return "Candidat introuvable."
    if cand["status"] in ("accepted", "testing"):
        return f"Rien à faire : <@{user_id}> est déjà {'recruté(e)' if cand['status'] == 'accepted' else 'en test'}."
    await db.update_candidate(user_id, status="allowed", decision_by=by.id, test_attempts=0)
    member = await get_member(bot, user_id)
    if member:
        await dm(member, t("allowed_dm", cand["lang"]))
    return f"🟢 <@{user_id}> est autorisé(e) à passer le test (par {by.mention})."


async def change_level(bot: discord.Client, user_id: int, new_level: str, by: discord.abc.User,
                       reason: str = "") -> str:
    chatter = await db.get_chatter(user_id)
    if chatter is None:
        return "Ce membre n'est pas chatteur."
    old = chatter["level"]
    if old == new_level:
        return f"<@{user_id}> est déjà {level_name(new_level)}."
    await db.set_level(user_id, old, new_level, by.id, reason or "Changement manuel")
    member = await get_member(bot, user_id)
    lang = chatter["lang"]
    if member:
        await apply_level_roles(member, new_level)
        promoted = S.LEVELS.index(new_level) > S.LEVELS.index(old)
        key = "promoted_dm" if promoted else "level_dm"
        await dm(member, t(key, lang, level=level_name(new_level, lang), commission=commission(new_level)))
    arrow = "⬆️" if S.LEVELS.index(new_level) > S.LEVELS.index(old) else "⬇️"
    return f"{arrow} <@{user_id}> : {level_name(old)} → {level_name(new_level)} (par {by.mention})."
