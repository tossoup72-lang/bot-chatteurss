"""Salon privé (toi + le bot) : propositions de push humanisés, chauds et taquins."""
from __future__ import annotations

import logging
from datetime import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks

import agency_settings as S
import ai
import config
import db
from utils import TZ, StaticView, now_local

log = logging.getLogger("push")
PINK = discord.Color.from_rgb(233, 30, 99)
TYPE_CHOICES = [app_commands.Choice(name=f"{k} · {v}"[:100], value=k) for k, v in S.PUSH_TYPES.items()]
PUSH_TIMES = [time(h, m, tzinfo=TZ) for h, m in S.PUSH_AUTO_HOURS]


def push_view(push_id: int) -> discord.ui.View:
    view = StaticView()
    view.add_item(discord.ui.Button(label="Utilisé", emoji="✅", style=discord.ButtonStyle.success,
                                    custom_id=f"cc:push:used:{push_id}"))
    view.add_item(discord.ui.Button(label="Autre version", emoji="🔁", style=discord.ButtonStyle.secondary,
                                    custom_id=f"cc:push:again:{push_id}"))
    view.add_item(discord.ui.Button(emoji="🗑️", style=discord.ButtonStyle.danger,
                                    custom_id=f"cc:push:drop:{push_id}"))
    return view


class Push(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.auto_loop.start()

    def cog_unload(self):
        self.auto_loop.cancel()

    async def _channel(self) -> discord.abc.Messageable | None:
        channel = self.bot.get_channel(config.PUSH_CHANNEL_ID)
        if channel is None and config.PUSH_CHANNEL_ID:
            channel = await self.bot.fetch_channel(config.PUSH_CHANNEL_ID)
        return channel

    async def post(self, channel, model: dict, push_type: str, theme: str | None, count: int) -> int:
        avoid = await db.recent_pushes(model["name"])
        pushes = await ai.generate_pushes(model, push_type, theme, count, avoid)
        header = f"💋 **{model['name']}** · {push_type}" + (f" · _{theme}_" if theme else "")
        await channel.send(f"{header} · {len(pushes)} proposition(s)")
        for text in pushes:
            push_id = await db.save_push(model["name"], push_type, theme, text)
            await channel.send(text[:2000], view=push_view(push_id))
        return len(pushes)

    # --- Commande ----------------------------------------------------------
    @app_commands.command(name="push", description="Propositions de push humanisés pour une modèle (salon privé)")
    @app_commands.guild_only()
    @app_commands.rename(type_="type")
    @app_commands.choices(type_=TYPE_CHOICES)
    @app_commands.describe(modele="Nom de la fiche modèle", type_="Type de push",
                           theme="Contenu ou ambiance à mettre en avant", nombre="Nombre de propositions")
    async def push(self, interaction: discord.Interaction, modele: str, type_: app_commands.Choice[str],
                   theme: Optional[str] = None, nombre: app_commands.Range[int, 1, 5] = 3):
        if interaction.user.id != config.OWNER_ID or interaction.channel_id != config.PUSH_CHANNEL_ID:
            return await interaction.response.send_message(
                "Commande réservée au propriétaire, dans le salon des push.", ephemeral=True)
        model = await db.get_model(modele)
        if model is None:
            return await interaction.response.send_message(
                f"Pas de fiche « {modele} ». Crée-la avec /admin modele.", ephemeral=True)
        await interaction.response.defer(thinking=True)
        count = await self.post(interaction.channel, model, type_.value, theme, nombre)
        await interaction.followup.send(f"{count} push prêts 👇" if count else "Aucune proposition, réessaie.")

    @push.autocomplete("modele")
    async def _models(self, interaction: discord.Interaction, current: str):
        models = await db.list_models()
        return [app_commands.Choice(name=m["name"], value=m["name"])
                for m in models if current.lower() in m["name"].lower()][:25]

    # --- Boutons -----------------------------------------------------------
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type is not discord.InteractionType.component:
            return
        cid = (interaction.data or {}).get("custom_id", "")
        if not cid.startswith("cc:push:"):
            return
        if interaction.user.id != config.OWNER_ID:
            return await interaction.response.send_message("Réservé au propriétaire.", ephemeral=True)
        _, _, action, raw_id = cid.split(":")
        push_id = int(raw_id)
        if action == "used":
            await db.set_push_status(push_id, "used")
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Utilisé", emoji="✅", disabled=True,
                                            style=discord.ButtonStyle.success))
            await interaction.response.edit_message(view=view)
        elif action == "drop":
            await db.set_push_status(push_id, "rejected")
            await interaction.response.defer()
            await interaction.message.delete()
        elif action == "again":
            await interaction.response.defer()
            try:
                original = await db.get_push(push_id)
                model = await db.get_model(original["model_name"]) if original else None
                if model is None:
                    return await interaction.followup.send("Fiche modèle introuvable.", ephemeral=True)
                await self.post(interaction.channel, model, original["push_type"], original["theme"], 1)
            except Exception:
                log.exception("Nouvelle version de push impossible")
                await interaction.followup.send("L'IA n'a pas répondu, réessaie dans un instant.", ephemeral=True)

    # --- Propositions automatiques -----------------------------------------
    @tasks.loop(time=PUSH_TIMES)
    async def auto_loop(self):
        try:
            channel = await self._channel()
            models = await db.list_models()
        except Exception:
            log.exception("Push auto : salon ou fiches indisponibles")
            return
        if channel is None or not models:
            return
        push_type = "matin" if now_local().hour < 15 else "soir"
        for model in models:
            try:
                await self.post(channel, model, push_type, None, S.PUSH_AUTO_COUNT)
            except Exception:
                log.exception("Push auto impossible pour %s", model["name"])

    @auto_loop.before_loop
    async def _wait_ready(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Push(bot))
