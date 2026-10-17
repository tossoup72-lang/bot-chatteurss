"""Étapes 2 et 3 : test de compétences, notation IA et niveau proposé."""
from __future__ import annotations

import asyncio
import logging
import random
import time

import discord
from discord import app_commands
from discord.ext import commands

import agency_settings as S
import ai
import config
import db
import scoring
from i18n import t
from questions import ENGLISH_QCM, OBJECTION_QUESTIONS, RULES_QCM, SALES_QUESTIONS, SCENARIOS
from utils import StaticView, admin_channel, bar, get_member, level_name

log = logging.getLogger("tests")
SECTION_LABELS = {"consignes": "Consignes", "anglais": "Anglais", "vente": "Vente",
                  "objections": "Objections", "simulation": "Simulation"}


class TestTimeout(Exception):
    pass


class QCMView(discord.ui.View):
    def __init__(self, user_id: int, count: int, lang: str):
        super().__init__(timeout=S.SIMULATION_TIMEOUT)
        self.user_id, self.lang = user_id, lang
        self.choice: int | None = None
        for i in range(count):
            button = discord.ui.Button(label="ABCD"[i], style=discord.ButtonStyle.primary)
            button.callback = self._make(i, button)
            self.add_item(button)

    def _make(self, index: int, button: discord.ui.Button):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(t("not_yours", self.lang), ephemeral=True)
                return
            self.choice = index
            for item in self.children:
                item.disabled = True
            button.style = discord.ButtonStyle.secondary
            await interaction.response.edit_message(view=self)
            self.stop()
        return callback


def _clip(text: str, limit: int = 1024) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


class Tests(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.running: set[int] = set()
        self._tasks: set[asyncio.Task] = set()

    # --- Démarrage -------------------------------------------------------
    @app_commands.command(name="test", description="Passer le test de recrutement · Take the recruitment test")
    @app_commands.guild_only()
    async def test_cmd(self, interaction: discord.Interaction):
        await self.begin(interaction)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type is discord.InteractionType.component and \
                (interaction.data or {}).get("custom_id") == "cc:starttest":
            await self.begin(interaction)

    async def begin(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        uid = interaction.user.id
        cand = await db.get_candidate(uid)
        lang = cand["lang"] if cand else "fr"
        say = interaction.followup.send
        if cand is None:
            return await say(t("must_apply", lang), ephemeral=True)
        if uid in self.running:
            return await say(t("test_running", lang), ephemeral=True)
        status = cand["status"]
        if status == "accepted":
            return await say(t("already_chatter", lang), ephemeral=True)
        if status == "tested":
            return await say(t("test_review", lang), ephemeral=True)
        if status not in ("allowed", "testing"):  # "testing" = test interrompu par un redémarrage
            return await say(t("already_pending", lang), ephemeral=True)
        if cand["test_attempts"] >= S.MAX_TEST_ATTEMPTS:
            return await say(t("max_attempts", lang), ephemeral=True)

        self.running.add(uid)  # bloque un double clic pendant la création du fil
        started = False
        try:
            member = interaction.user if isinstance(interaction.user, discord.Member) else await get_member(self.bot, uid)
            if member is None:
                return await say(t("must_apply", lang), ephemeral=True)
            try:
                channel = self.bot.get_channel(config.TESTS_CHANNEL_ID) or \
                    await self.bot.fetch_channel(config.TESTS_CHANNEL_ID)
                thread = await channel.create_thread(
                    name=f"test-{member.display_name}"[:90], type=discord.ChannelType.private_thread,
                    invitable=False, auto_archive_duration=1440)
                await thread.add_user(member)
            except discord.HTTPException:
                log.exception("Impossible de créer le fil de test (vérifie TESTS_CHANNEL_ID et les permissions)")
                return await say(t("test_error", lang), ephemeral=True)
            attempt = cand["test_attempts"] + 1
            await db.update_candidate(uid, status="testing", test_attempts=attempt)
            await say(t("test_thread", lang, link=thread.mention), ephemeral=True)

            task = asyncio.create_task(self.run(member, thread, lang, attempt))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
            started = True
        finally:
            if not started:
                self.running.discard(uid)

    # --- Déroulé ---------------------------------------------------------
    async def run(self, member: discord.Member, thread: discord.Thread, lang: str, attempt: int):
        uid = member.id
        grading: list[asyncio.Task] = []
        try:
            await thread.send(t("test_welcome", lang, mention=member.mention))
            scores, details = {}, {}

            scores["consignes"], details["consignes"] = await self.qcm(thread, member, lang, "consignes",
                                                                       RULES_QCM[lang])
            scores["anglais"], details["anglais"] = await self.qcm(thread, member, lang, "anglais", ENGLISH_QCM)

            sales = await self.open_questions(thread, member, lang, "vente", SALES_QUESTIONS[lang])
            sales_task = asyncio.create_task(ai.grade_open("vente", sales, lang))
            grading.append(sales_task)
            objections = await self.open_questions(thread, member, lang, "objections", OBJECTION_QUESTIONS[lang])
            obj_task = asyncio.create_task(ai.grade_open("objections", objections, lang))
            grading.append(obj_task)

            scenario, transcript, avg = await self.simulation(thread, member, lang)
            await thread.send(t("grading", lang))
            async with thread.typing():
                sim_grade = await ai.grade_simulation(scenario, transcript, lang, avg)
                sales_grade, obj_grade = await sales_task, await obj_task

            for key, grade in (("vente", sales_grade), ("objections", obj_grade), ("simulation", sim_grade)):
                scores[key] = grade["score"]
                details[key] = grade
            total = scoring.total_score(scores)
            level = scoring.suggest_level(total, scores)

            await db.save_test_result({
                "discord_id": uid, "total_score": total, "suggested_level": level,
                "sections": {k: {"score": scores[k], **(details[k] if isinstance(details[k], dict)
                                                        else {"detail": details[k]})} for k in scores},
                "transcript": {"scenario": scenario, "simulation": transcript,
                               "vente": sales, "objections": objections},
                "avg_response_seconds": round(avg, 1) if avg else None,
            })
            current = await db.get_candidate(uid)
            if current and current["status"] == "testing":  # pas de décision prise entre-temps
                await db.update_candidate(uid, status="tested")

            tips = "\n\n".join(g["feedback"] for g in (sales_grade, obj_grade, sim_grade) if g["feedback"])
            done = discord.Embed(title=t("feedback_title", lang), description=_clip(tips, 4000),
                                 color=discord.Color.blurple())
            await thread.send(t("test_done", lang), embed=done)
            await self.report(member, thread, total, level, scores, details, avg, scenario)
            await thread.edit(archived=True, locked=True)
        except TestTimeout:
            await db.update_candidate(uid, status="allowed")
            await thread.send(t("timeout", lang, left=max(0, S.MAX_TEST_ATTEMPTS - attempt)))
            await thread.edit(archived=True, locked=True)
        except Exception:
            log.exception("Test interrompu pour %s", member)
            try:
                await db.update_candidate(uid, status="allowed", test_attempts=attempt - 1)
                await thread.send(t("test_error", lang))
                channel = await admin_channel(self.bot)
                if channel:
                    await channel.send(f"⚠️ Le test de {member.mention} a planté (voir les logs). "
                                       f"La tentative ne lui est pas comptée.")
            except Exception:
                log.exception("Impossible de signaler l'échec du test de %s", member)
        finally:
            self.running.discard(uid)
            for task in grading:
                if not task.done():
                    task.cancel()
                elif not task.cancelled() and task.exception():
                    log.warning("Notation abandonnée : %s", task.exception())

    async def qcm(self, thread, member, lang, key, items) -> tuple[int, list]:
        await thread.send(embed=discord.Embed(title=t(f"part_{key}", lang), color=discord.Color.dark_magenta()))
        correct, detail = 0, []
        for i, (question, options) in enumerate(items, 1):
            order = list(range(len(options)))
            random.shuffle(order)
            shown = [options[j] for j in order]
            good = order.index(0)
            embed = discord.Embed(title=_clip(f"{i}/{len(items)} · {question}", 256),
                                  description="\n".join(f"**{l}.** {o}" for l, o in zip("ABCD", shown)))
            embed.set_footer(text=t("qcm_hint", lang))
            view = QCMView(member.id, len(shown), lang)
            await thread.send(embed=embed, view=view)
            await view.wait()
            if view.choice is None:
                raise TestTimeout
            ok = view.choice == good
            correct += ok
            detail.append({"question": question, "answer": shown[view.choice], "ok": ok})
        return round(correct / len(items) * 100), detail

    async def _wait_text(self, thread, member, timeout) -> str:
        def check(m: discord.Message):
            return m.channel.id == thread.id and m.author.id == member.id and m.content.strip()
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=timeout)
        except asyncio.TimeoutError:
            raise TestTimeout from None
        return msg.content.strip()[:2000]

    async def open_questions(self, thread, member, lang, key, questions) -> list[tuple[str, str]]:
        await thread.send(embed=discord.Embed(title=t(f"part_{key}", lang), color=discord.Color.dark_magenta()))
        answers = []
        minutes = S.OPEN_ANSWER_TIMEOUT // 60
        for i, question in enumerate(questions, 1):
            embed = discord.Embed(title=f"{i}/{len(questions)}", description=question)
            embed.set_footer(text=t("write_answer", lang, minutes=minutes))
            await thread.send(embed=embed)
            answers.append((question, await self._wait_text(thread, member, S.OPEN_ANSWER_TIMEOUT)))
        return answers

    async def simulation(self, thread, member, lang):
        scenario = random.choice(SCENARIOS[lang])
        await thread.send(embed=discord.Embed(
            title=t("part_simulation", lang), color=discord.Color.dark_magenta(),
            description=t("sim_intro", lang, name=scenario["name"], turns=S.SIMULATION_TURNS,
                          minutes=S.SIMULATION_TIMEOUT // 60)))
        history, transcript, delays = [], [], []
        async with thread.typing():
            fan = await ai.fan_reply(scenario, history, lang)
        for turn in range(S.SIMULATION_TURNS):
            await thread.send(f"**👤 {scenario['name']}** : {fan}")
            started = time.monotonic()
            reply = await self._wait_text(thread, member, S.SIMULATION_TIMEOUT)
            delays.append(time.monotonic() - started)
            history += [{"role": "assistant", "content": fan}, {"role": "user", "content": reply}]
            transcript += [(f"Abonné ({scenario['name']})", fan), ("Candidat", reply)]
            if turn < S.SIMULATION_TURNS - 1:
                async with thread.typing():
                    fan = await ai.fan_reply(scenario, history, lang)
        return scenario, transcript, (sum(delays) / len(delays) if delays else None)

    # --- Rapport pour les responsables -----------------------------------
    async def report(self, member, thread, total, level, scores, details, avg, scenario):
        channel = await admin_channel(self.bot)
        if channel is None:
            return
        verdict = f"Niveau proposé : **{level_name(level)}**" if level else "**Refus proposé**"
        if scores.get("consignes", 100) < S.MIN_RULES_SCORE:
            verdict += " (consignes sous le minimum éliminatoire)"
        color = discord.Color.green() if level else discord.Color.red()
        embed = discord.Embed(title=f"🧪 Résultat de test · {member.display_name}",
                              description=f"{member.mention} · Score total **{total}/100**\n{verdict}", color=color)
        embed.add_field(name="Détail", inline=False, value="\n".join(
            f"`{bar(scores[k])}` **{scores[k]:>3}** {SECTION_LABELS[k]} ({S.TEST_WEIGHTS[k]} %)" for k in scores))

        strengths, weaknesses = [], []
        for key in ("vente", "objections", "simulation"):
            strengths += [f"{SECTION_LABELS[key]} : {s}" for s in details[key]["strengths"]]
            weaknesses += [f"{SECTION_LABELS[key]} : {w}" for w in details[key]["weaknesses"]]
        for key in ("consignes", "anglais"):
            wrong = [d["question"] for d in details[key] if not d["ok"]]
            if wrong:
                weaknesses.append(f"{SECTION_LABELS[key]} : erreur sur « {_clip(wrong[0], 80)} »"
                                  + (f" (+{len(wrong) - 1})" if len(wrong) > 1 else ""))
        embed.add_field(name="Points forts", value=_clip("\n".join(f"• {s}" for s in strengths) or "—"), inline=False)
        embed.add_field(name="Points faibles", value=_clip("\n".join(f"• {w}" for w in weaknesses) or "—"),
                        inline=False)
        embed.add_field(name="Simulation", value=f"Abonné fictif : {scenario['name']}\n"
                        f"Temps de réponse moyen : {avg:.0f} s" if avg else scenario["name"], inline=True)
        embed.add_field(name="Fil du test", value=thread.mention, inline=True)
        embed.set_footer(text="Le score de recrutement reste distinct des performances réelles.")

        view = StaticView()
        if level:
            view.add_item(discord.ui.Button(label=f"Valider ({S.LEVEL_INFO[level]['fr']})", emoji="✅",
                                            style=discord.ButtonStyle.success,
                                            custom_id=f"cc:adm:accept:{member.id}:{level}"))
        view.add_item(discord.ui.Button(label="Choisir le niveau", emoji="🎚️", style=discord.ButtonStyle.secondary,
                                        custom_id=f"cc:adm:choose:{member.id}"))
        view.add_item(discord.ui.Button(label="Refuser", emoji="❌", style=discord.ButtonStyle.danger,
                                        custom_id=f"cc:adm:reject:{member.id}"))
        await channel.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tests(bot))
