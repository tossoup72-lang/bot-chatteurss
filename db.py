"""Accès à la base Supabase.

Le client Supabase est synchrone : chaque appel passe par asyncio.to_thread
pour ne pas bloquer le bot Discord.
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from typing import Any

from supabase import Client, create_client

import config

_client: Client | None = None


def client() -> Client:
    global _client
    if _client is None:
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


async def _run(fn):
    return await asyncio.to_thread(fn)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _first(rows: list[dict]) -> dict | None:
    return rows[0] if rows else None


# --- Candidats ---------------------------------------------------------------
async def get_candidate(discord_id: int) -> dict | None:
    return await _run(lambda: _first(
        client().table("candidates").select("*").eq("discord_id", discord_id).limit(1).execute().data))


async def upsert_candidate(data: dict) -> None:
    data = {**data, "updated_at": _now()}
    await _run(lambda: client().table("candidates").upsert(data, on_conflict="discord_id").execute())


async def update_candidate(discord_id: int, **fields: Any) -> None:
    fields["updated_at"] = _now()
    await _run(lambda: client().table("candidates").update(fields).eq("discord_id", discord_id).execute())


async def list_candidates(statuses: list[str] | None = None, limit: int = 25) -> list[dict]:
    def q():
        query = client().table("candidates").select("*").order("updated_at", desc=True).limit(limit)
        if statuses:
            query = query.in_("status", statuses)
        return query.execute().data
    return await _run(q)


# --- Tests -------------------------------------------------------------------
async def save_test_result(data: dict) -> None:
    await _run(lambda: client().table("test_results").insert(data).execute())


async def latest_test(discord_id: int) -> dict | None:
    return await _run(lambda: _first(
        client().table("test_results").select("*").eq("discord_id", discord_id)
        .order("created_at", desc=True).limit(1).execute().data))


# --- Chatteurs ---------------------------------------------------------------
async def get_chatter(discord_id: int) -> dict | None:
    return await _run(lambda: _first(
        client().table("chatters").select("*").eq("discord_id", discord_id).limit(1).execute().data))


async def upsert_chatter(data: dict) -> None:
    await _run(lambda: client().table("chatters").upsert(data, on_conflict="discord_id").execute())


async def list_chatters(active_only: bool = True) -> list[dict]:
    def q():
        query = client().table("chatters").select("*").order("hired_at")
        if active_only:
            query = query.eq("active", True)
        return query.execute().data
    return await _run(q)


async def set_level(discord_id: int, old_level: str | None, new_level: str, by: int | None, reason: str) -> None:
    def q():
        client().table("chatters").update({"level": new_level, "level_since": _now()}).eq(
            "discord_id", discord_id).execute()
        client().table("level_history").insert({
            "discord_id": discord_id, "old_level": old_level, "new_level": new_level,
            "changed_by": by, "reason": reason,
        }).execute()
    await _run(q)


async def add_level_history(discord_id: int, old_level: str | None, new_level: str, by: int | None, reason: str):
    await _run(lambda: client().table("level_history").insert({
        "discord_id": discord_id, "old_level": old_level, "new_level": new_level,
        "changed_by": by, "reason": reason,
    }).execute())


async def set_chatter_active(discord_id: int, active: bool) -> None:
    await _run(lambda: client().table("chatters").update({"active": active}).eq("discord_id", discord_id).execute())


# --- Performances ------------------------------------------------------------
async def upsert_performance(rows: list[dict]) -> None:
    if rows:
        await _run(lambda: client().table("performance").upsert(
            rows, on_conflict="discord_id,period_start,period_end").execute())


async def performance_since(discord_id: int | None, since: date) -> list[dict]:
    def q():
        query = client().table("performance").select("*").gte("period_end", since.isoformat()).order("period_end")
        if discord_id is not None:
            query = query.eq("discord_id", discord_id)
        return query.execute().data
    return await _run(q)


# --- Objectifs ---------------------------------------------------------------
async def add_objective(discord_id: int | None, week_start: date, text: str, by: int) -> None:
    await _run(lambda: client().table("objectives").insert({
        "discord_id": discord_id, "week_start": week_start.isoformat(), "text": text, "created_by": by,
    }).execute())


async def objectives_for(discord_id: int, week_start: date) -> list[dict]:
    def q():
        rows = client().table("objectives").select("*").eq("week_start", week_start.isoformat()).execute().data
        return [r for r in rows if r["discord_id"] in (None, discord_id)]
    return await _run(q)


# --- Parcours ----------------------------------------------------------------
async def onboarding_done(discord_id: int) -> set[str]:
    rows = await _run(lambda: client().table("onboarding_progress").select("step_key")
                      .eq("discord_id", discord_id).execute().data)
    return {r["step_key"] for r in rows}


async def mark_onboarding(discord_id: int, step_key: str) -> None:
    await _run(lambda: client().table("onboarding_progress").upsert(
        {"discord_id": discord_id, "step_key": step_key}, on_conflict="discord_id,step_key").execute())


# --- Modèles et push ---------------------------------------------------------
async def list_models(active_only: bool = True) -> list[dict]:
    def q():
        query = client().table("model_profiles").select("*").order("name")
        if active_only:
            query = query.eq("active", True)
        return query.execute().data
    return await _run(q)


async def get_model(name: str) -> dict | None:
    pattern = name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return await _run(lambda: _first(
        client().table("model_profiles").select("*").ilike("name", pattern).limit(1).execute().data))


async def upsert_model(data: dict) -> None:
    await _run(lambda: client().table("model_profiles").upsert(data, on_conflict="name").execute())


async def save_push(model_name: str, push_type: str, theme: str | None, content: str) -> int:
    rows = await _run(lambda: client().table("push_suggestions").insert({
        "model_name": model_name, "push_type": push_type, "theme": theme, "content": content,
    }).execute().data)
    return rows[0]["id"]


async def get_push(push_id: int) -> dict | None:
    return await _run(lambda: _first(
        client().table("push_suggestions").select("*").eq("id", push_id).limit(1).execute().data))


async def set_push_status(push_id: int, status: str) -> None:
    await _run(lambda: client().table("push_suggestions").update({"status": status}).eq("id", push_id).execute())


async def recent_pushes(model_name: str, limit: int = 15) -> list[str]:
    rows = await _run(lambda: client().table("push_suggestions").select("content").eq("model_name", model_name)
                      .order("created_at", desc=True).limit(limit).execute().data)
    return [r["content"] for r in rows]
