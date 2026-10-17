"""/admin : résultats, validations, niveaux, import des ventes, objectifs, modèles."""
from __future__ import annotations

import io
import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import agency_settings as S
import csv_import
import db
import services
from cogs.recruitment import apply_panel
from utils import admin_channel, get_member, is_staff, level_name, week_start

log = logging.getLogger("admin")
LEVEL_CHOICES = [app_commands.Choice(name=S.LEVEL_INFO[lvl]["fr"], value=lvl) for lvl in S.LEVELS]
STATUS_CHOICES = [app_commands.Choice(name=n, value=v) for n, v in (
    ("À examiner (non éligibles)", "ineligible"), ("Test débloqué", "allowed"), ("Test en cours", "testing"),
    ("Test terminé, à valider", "tested"), ("Recrutés", "accepted"), ("Refusés", "rejected"))]
STATUS_LABELS = {c.value: c.name for c in STATUS_CHOICES} | {"applied": "Candidature reçue"}


async def _close(message: discord.Message | None, result: str):
    """Ajoute la décision au message d'origine et retire les boutons."""
    if message is None:
        return
    embed = message.embeds[0] if message.embeds else discord.Embed()
    embed.add_field(name="Décision", value=result[:1024], inline=False)
    try:
        await message.edit(embed=embed, view=None)
    except discord.HTTPException:
        pass


class RejectModal(discord.ui.Modal, title="Refuser la candidature"):
    reason = discord.ui.TextInput(label="Motif (interne, facultatif)", required=False, max_length=300,
                                  style=discord.TextStyle.paragraph)

    def __init__(self, user_id: int, message: discord.Message | None):
        super().__init__()
        self.user_id, self.message = user_id, message

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        result = await services.reject_candidate(interaction.client, self.user_id, interaction.user, self.reason.value)
        await _close(self.message, result)
        await interaction.followup.send(result, ephemeral=True)


class LevelSelect(discord.ui.View):
    def __init__(self, user_id: int, message: discord.Message | None, mode: str):
        super().__init__(timeout=300)
        self.user_id, self.message, self.mode = user_id, message, mode
        select = discord.ui.Select(placeholder="Choisis le niveau", options=[
            discord.SelectOption(label=S.LEVEL_INFO[l]["fr"], value=l, emoji=S.LEVEL_INFO[l]["emoji"],
                                 description=f"Commission {S.LEVEL_INFO[l]['commission']} %") for l in S.LEVELS])
        select.callback = self.pick
        self.add_item(select)

    async def pick(self, interaction: discord.Interaction):
        level = interaction.data["values"][0]
        await interaction.response.edit_message(content="⏳ …", view=None)
        if self.mode == "accept":
            result = await services.accept_candidate(interaction.client, self.user_id, level, interaction.user)
        else:
            result = await services.change_level(interaction.client, self.user_id, level, interaction.user)
        await _close(self.message, result)
        await interaction.edit_original_response(content=result)


class ModelModal(discord.ui.Modal):
    def __init__(self, name: str, existing: dict | None):
        super().__init__(title=f"Fiche push : {name}"[:45])
        self.name = name
        e = existing or {}
        self.lang = discord.ui.TextInput(label="Langue des push (fr ou en)", default=e.get("lang", "fr"), max_length=2)
        self.persona = discord.ui.TextInput(label="Personnalité", style=discord.TextStyle.paragraph, max_length=1000,
                                            default=e.get("persona"), placeholder="ex : étudiante en art, douce, "
                                            "joueuse, adore les compliments sur son style")
        self.style = discord.ui.TextInput(label="Façon d'écrire", style=discord.TextStyle.paragraph, required=False,
                                          max_length=600, default=e.get("style"),
                                          placeholder="ex : minuscules, beaucoup de 🙈 et 😇, phrases courtes")
        self.limits = discord.ui.TextInput(label="Limites à respecter", style=discord.TextStyle.paragraph,
                                           required=False, max_length=600, default=e.get("limits"))
        for item in (self.lang, self.persona, self.style, self.limits):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.lang.value.strip().lower()
        await db.upsert_model({"name": self.name, "lang": lang if lang in ("fr", "en") else "fr",
                               "persona": self.persona.value, "style": self.style.value or None,
                               "limits": self.limits.value or None, "active": True})
        await interaction.response.send_message(f"✅ Fiche de **{self.name}** enregistrée pour les push.",
                                                ephemeral=True)


class Admin(commands.Cog):
    admin = app_commands.Group(name="admin", description="Outils des responsables", guild_only=True)

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return is_staff(interaction.user)

    # --- Boutons des messages d'administration ---------------------------
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type is not discord.InteractionType.component:
            return
        cid = (interaction.data or {}).get("custom_id", "")
        if not cid.startswith("cc:adm:"):
            return
        if not is_staff(interaction.user):
            await interaction.response.send_message("Réservé aux responsables.", ephemeral=True)
            return
        parts = cid.split(":")
        action, user_id = parts[2], int(parts[3])
        message = interaction.message
        if action == "reject":
            await interaction.response.send_modal(RejectModal(user_id, message))
        elif action == "choose":
            await interaction.response.send_message("Niveau d'entrée :", view=LevelSelect(user_id, message, "accept"),
                                                    ephemeral=True)
        elif action == "setlevel":
            await interaction.response.send_message("Nouveau niveau :", view=LevelSelect(user_id, message, "level"),
                                                    ephemeral=True)
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            try:
                if action == "allow":
                    result = await services.allow_test(self.bot, user_id, interaction.user)
                elif action == "accept":
                    result = await services.accept_candidate(self.bot, user_id, parts[4], interaction.user)
                elif action == "promote":
                    result = await services.change_level(self.bot, user_id, parts[4], interaction.user,
                                                         "Promotion (critères remplis)")
                else:
                    result = "Action inconnue."
            except Exception:
                log.exception("Action admin %s impossible", cid)
                return await interaction.followup.send("Erreur pendant l'action, regarde les logs puis réessaie.",
                                                       ephemeral=True)
            if result.startswith(("✅", "❌", "🟢", "⬆️", "⬇️", "Recruté")):
                await _close(message, result)
            await interaction.followup.send(result, ephemeral=True)

    # --- Candidats -------------------------------------------------------
    @admin.command(name="candidats", description="Lister les candidatures")
    @app_commands.choices(statut=STATUS_CHOICES)
    async def candidats(self, interaction: discord.Interaction, statut: Optional[app_commands.Choice[str]] = None):
        await interaction.response.defer(ephemeral=True)
        rows = await db.list_candidates([statut.value] if statut else None)
        if not rows:
            return await interaction.followup.send("Aucune candidature.", ephemeral=True)
        lines = []
        for r in rows:
            test = await db.latest_test(r["discord_id"]) if r["status"] in ("tested", "accepted", "rejected") else None
            score = f" · {test['total_score']}/100 → {level_name(test['suggested_level'])}" if test else ""
            lines.append(f"<@{r['discord_id']}> · {STATUS_LABELS.get(r['status'], r['status'])} · "
                         f"{r['experience_months'] or 0} mois{score}")
        embed = discord.Embed(title=f"Candidatures ({statut.name if statut else 'toutes'})",
                              description="\n".join(lines)[:4000], color=discord.Color.blurple())
        await interaction.followup.send(embed=embed, ephemeral=True)

    @admin.command(name="fiche", description="Voir le dossier complet d'un membre")
    async def fiche(self, interaction: discord.Interaction, membre: discord.Member):
        await interaction.response.defer(ephemeral=True)
        cand, test, chatter = (await db.get_candidate(membre.id), await db.latest_test(membre.id),
                               await db.get_chatter(membre.id))
        embed = discord.Embed(title=f"Dossier · {membre.display_name}", color=discord.Color.blurple())
        if cand:
            embed.add_field(name="Candidature", inline=False, value=(
                f"Statut : {STATUS_LABELS.get(cand['status'], cand['status'])} · langue {cand['lang'].upper()}\n"
                f"Expérience : {cand['experience_months'] or 0} mois · {cand['hours_per_week'] or 0} h/sem\n"
                f"Plateformes : {cand['platforms']}\nTentatives de test : {cand['test_attempts']}")[:1024])
        if test:
            sections = " · ".join(f"{k} {v['score']}" for k, v in test["sections"].items())
            embed.add_field(name="Dernier test", inline=False, value=(
                f"**{test['total_score']}/100** → {level_name(test['suggested_level'])}\n{sections}")[:1024])
        if chatter:
            progression = self.bot.get_cog("Progression")
            summary, check = await progression.evaluate(chatter)
            embed.add_field(name="Chatteur", inline=False, value=(
                f"{level_name(chatter['level'])} · actif : {'oui' if chatter['active'] else 'non'}\n"
                f"CA 4 sem. : {summary.revenue_total} {S.CURRENCY} · conversion {summary.conversion or '—'} % · "
                f"qualité {summary.quality or '—'} · ponctualité {summary.punctuality or '—'}\n"
                + (f"Promotion vers {level_name(check.target)} : {'✅ prête' if check.eligible else 'pas encore'}"
                   if check.target else "Niveau maximum")))
        if not (cand or chatter):
            embed.description = "Aucune donnée pour ce membre."
        await interaction.followup.send(embed=embed, ephemeral=True)

    @admin.command(name="valider", description="Recruter un candidat à un niveau")
    @app_commands.choices(niveau=LEVEL_CHOICES)
    async def valider(self, interaction: discord.Interaction, membre: discord.Member,
                      niveau: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(await services.accept_candidate(self.bot, membre.id, niveau.value,
                                                                        interaction.user), ephemeral=True)

    @admin.command(name="refuser", description="Refuser une candidature")
    async def refuser(self, interaction: discord.Interaction, membre: discord.Member, motif: str = ""):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(await services.reject_candidate(self.bot, membre.id, interaction.user, motif),
                                        ephemeral=True)

    @admin.command(name="autoriser", description="Autoriser un candidat non éligible à passer le test")
    async def autoriser(self, interaction: discord.Interaction, membre: discord.Member):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(await services.allow_test(self.bot, membre.id, interaction.user),
                                        ephemeral=True)

    @admin.command(name="panneau", description="Publier le panneau « Postuler » dans ce salon")
    async def panneau(self, interaction: discord.Interaction):
        embed, view = apply_panel()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("Panneau publié ✅", ephemeral=True)

    # --- Chatteurs -------------------------------------------------------
    @admin.command(name="niveau", description="Promouvoir ou rétrograder un chatteur")
    @app_commands.choices(niveau=LEVEL_CHOICES)
    async def niveau(self, interaction: discord.Interaction, membre: discord.Member,
                     niveau: app_commands.Choice[str], motif: str = ""):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(await services.change_level(self.bot, membre.id, niveau.value,
                                                                    interaction.user, motif), ephemeral=True)

    @admin.command(name="desactiver", description="Retirer un chatteur de l'équipe active")
    async def desactiver(self, interaction: discord.Interaction, membre: discord.Member):
        await db.set_chatter_active(membre.id, False)
        await interaction.response.send_message(f"{membre.mention} n'est plus dans l'équipe active.", ephemeral=True)

    @admin.command(name="promotions", description="Chatteurs qui remplissent les conditions du niveau suivant")
    async def promotions(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        progression = self.bot.get_cog("Progression")
        ready = []
        for chatter in await db.list_chatters():
            _, check = await progression.evaluate(chatter)
            if check.eligible:
                ready.append((chatter, check))
        if not ready:
            return await interaction.followup.send("Personne ne remplit encore les conditions.", ephemeral=True)
        channel = await admin_channel(self.bot) or interaction.channel
        for chatter, check in ready[:10]:
            await channel.send(**progression.promotion_card(chatter, check))
        await interaction.followup.send(f"{len(ready[:10])} promotion(s) possible(s) publiée(s) dans {channel.mention}.",
                                        ephemeral=True)

    @admin.command(name="objectif", description="Fixer un objectif de la semaine (à un chatteur ou à toute l'équipe)")
    async def objectif(self, interaction: discord.Interaction, texte: str, membre: Optional[discord.Member] = None):
        await db.add_objective(membre.id if membre else None, week_start(), texte, interaction.user.id)
        target = membre.mention if membre else "toute l'équipe"
        await interaction.response.send_message(f"🎯 Objectif ajouté pour {target} : {texte}", ephemeral=True)

    @admin.command(name="bilan", description="Envoyer le bilan hebdomadaire maintenant")
    async def bilan(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        count = await self.bot.get_cog("Progression").weekly_report()
        await interaction.followup.send(f"Bilan envoyé à {count} chatteur(s) ✅", ephemeral=True)

    # --- Ventes ----------------------------------------------------------
    @admin.command(name="import", description="Importer un rapport de ventes (CSV)")
    async def import_(self, interaction: discord.Interaction, fichier: discord.Attachment):
        await interaction.response.defer(ephemeral=True, thinking=True)
        if not fichier.filename.lower().endswith((".csv", ".txt")):
            return await interaction.followup.send("Envoie un fichier .csv (Excel : Enregistrer sous > CSV).",
                                                   ephemeral=True)
        chatters = await db.list_chatters(active_only=False)
        chatter_ids = {c["discord_id"] for c in chatters}
        names: dict[str, int] = {}
        for c in chatters:
            names[c["username"]] = c["discord_id"]
            member = await get_member(self.bot, c["discord_id"])
            if member:
                names[member.name] = names[member.display_name] = c["discord_id"]
        rows, errors = csv_import.parse(await fichier.read(), names)
        valid = []
        for row in rows:
            if row["discord_id"] in chatter_ids:
                valid.append({**row, "source": fichier.filename, "imported_by": interaction.user.id})
            else:
                errors.append(f"<@{row['discord_id']}> n'est pas enregistré comme chatteur, ligne ignorée.")
        unique: dict[tuple, dict] = {}
        for row in valid:
            key = (row["discord_id"], row["period_start"], row["period_end"])
            if key in unique:
                errors.append(f"<@{key[0]}> : période {key[1]} → {key[2]} en double, dernière ligne gardée.")
            unique[key] = row
        valid = list(unique.values())
        await db.upsert_performance(valid)
        text = f"✅ {len(valid)} ligne(s) importée(s) depuis `{fichier.filename}`."
        if errors:
            text += "\n\n**À corriger :**\n" + "\n".join(errors[:15])
            if len(errors) > 15:
                text += f"\n… et {len(errors) - 15} autre(s)."
        await interaction.followup.send(text[:2000], ephemeral=True)

    @admin.command(name="modele-csv", description="Télécharger le modèle de fichier d'import des ventes")
    async def modele_csv(self, interaction: discord.Interaction):
        file = discord.File(io.BytesIO(csv_import.TEMPLATE.encode("utf-8-sig")), filename="modele_import_ventes.csv")
        await interaction.response.send_message(
            "Une ligne par chatteur et par période (semaine conseillée). Les notes qualité et ponctualité "
            "sont sur 100.", file=file, ephemeral=True)

    # --- Fiches modèles pour les push ------------------------------------
    @admin.command(name="modele", description="Créer ou modifier la fiche d'une modèle pour les push")
    async def modele(self, interaction: discord.Interaction, nom: str):
        existing = await db.get_model(nom.strip())
        await interaction.response.send_modal(ModelModal(existing["name"] if existing else nom.strip(), existing))

    @admin.command(name="modeles", description="Lister les fiches modèles")
    async def modeles(self, interaction: discord.Interaction):
        models = await db.list_models(active_only=False)
        text = "\n".join(f"• **{m['name']}** ({m['lang'].upper()}) : {m['persona'][:80]}" for m in models)
        await interaction.response.send_message((text or "Aucune fiche. Ajoute-en une avec /admin modele.")[:2000],
                                                ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
