"""Textes du bot en français et en anglais."""

STRINGS: dict[str, dict[str, str]] = {
    # --- Candidature ---
    "choose_lang": {"fr": "Choisis ta langue · Choose your language", "en": "Choisis ta langue · Choose your language"},
    "apply_intro": {
        "fr": "**Candidature chatteur**\nLe processus : 1) quelques questions sur ton profil, 2) un test "
              "d'environ 30 à 40 minutes (consignes, anglais, vente, objections, simulation avec un abonné "
              "fictif), 3) validation par un responsable.\n\nEn continuant, tu confirmes avoir **18 ans ou plus** "
              "et tu acceptes que tes réponses soient évaluées et conservées par l'agence.",
        "en": "**Chatter application**\nThe process: 1) a few questions about your profile, 2) a test of about "
              "30 to 40 minutes (rules, English, sales, objections, simulation with a fictional fan), "
              "3) review by a manager.\n\nBy continuing, you confirm you are **18 or older** and agree that "
              "your answers will be evaluated and kept by the agency.",
    },
    "btn_confirm": {"fr": "J'ai 18 ans ou plus, je continue", "en": "I'm 18 or older, continue"},
    "modal_title": {"fr": "Candidature chatteur", "en": "Chatter application"},
    "q_experience": {"fr": "Expérience en chatting (mois ou années)", "en": "Chatting experience (months or years)"},
    "q_experience_ph": {"fr": "ex : 1 an et demi", "en": "e.g. 2 years"},
    "q_platforms": {"fr": "Plateformes déjà travaillées", "en": "Platforms you've worked on"},
    "q_platforms_ph": {"fr": "ex : OnlyFans, MYM, Fansly", "en": "e.g. OnlyFans, Fansly"},
    "q_hours": {"fr": "Heures dispo par semaine et créneaux", "en": "Hours per week and time slots"},
    "q_hours_ph": {"fr": "ex : 35 h, soirs et week-ends", "en": "e.g. 35h, evenings and weekends"},
    "q_best": {"fr": "Ton meilleur résultat (CA, conversion…)", "en": "Your best result (revenue, conversion…)"},
    "q_motivation": {"fr": "Pourquoi notre agence ?", "en": "Why our agency?"},
    "apply_ok": {
        "fr": "Candidature reçue ✅ Ton profil correspond à nos critères. Clique sur **Commencer le test** "
              "quand tu es prêt(e), au calme, avec 30 à 40 minutes devant toi.",
        "en": "Application received ✅ Your profile matches our criteria. Click **Start the test** when you're "
              "ready, somewhere quiet, with 30 to 40 minutes ahead of you.",
    },
    "apply_ineligible": {
        "fr": "Candidature reçue. Ton profil ne correspond pas encore à tous nos critères :\n{reasons}\n"
              "Un responsable va l'examiner et pourra t'autoriser à passer le test.",
        "en": "Application received. Your profile doesn't match all our criteria yet:\n{reasons}\n"
              "A manager will review it and may still allow you to take the test.",
    },
    "already_chatter": {"fr": "Tu fais déjà partie de l'équipe 😉 Tape /mon-niveau.",
                        "en": "You're already on the team 😉 Use /mon-niveau."},
    "already_pending": {"fr": "Ta candidature est en cours d'examen, un responsable te répond bientôt.",
                        "en": "Your application is under review, a manager will get back to you soon."},
    "cooldown": {"fr": "Ta dernière candidature n'a pas été retenue. Tu pourras repostuler dans {days} jour(s).",
                 "en": "Your last application wasn't accepted. You can apply again in {days} day(s)."},
    "btn_start_test": {"fr": "Commencer le test", "en": "Start the test"},
    # --- Test ---
    "must_apply": {"fr": "Postule d'abord avec /postuler.", "en": "Apply first with /postuler."},
    "test_review": {"fr": "Ton test est terminé, un responsable examine tes résultats.",
                    "en": "Your test is done, a manager is reviewing your results."},
    "max_attempts": {"fr": "Tu as utilisé toutes tes tentatives de test.", "en": "You've used all your test attempts."},
    "test_running": {"fr": "Ton test est déjà en cours dans ton fil privé.", "en": "Your test is already running in your private thread."},
    "test_thread": {"fr": "Ton test t'attend ici : {link}", "en": "Your test is waiting for you here: {link}"},
    "test_welcome": {
        "fr": "Salut {mention} 👋 Voici ton test, en 5 parties :\n1. Consignes de l'agence (QCM)\n2. Anglais (QCM)\n"
              "3. Vente (réponses écrites)\n4. Objections (réponses écrites)\n5. Simulation avec un abonné fictif\n\n"
              "Écris comme tu le ferais vraiment avec un abonné. Ce fil est privé : seuls toi et les responsables le voient.",
        "en": "Hi {mention} 👋 Here's your test, in 5 parts:\n1. Agency rules (quiz)\n2. English (quiz)\n"
              "3. Sales (written answers)\n4. Objections (written answers)\n5. Simulation with a fictional fan\n\n"
              "Write exactly as you would with a real fan. This thread is private: only you and managers can see it.",
    },
    "part_consignes": {"fr": "Partie 1 · Consignes de l'agence", "en": "Part 1 · Agency rules"},
    "part_anglais": {"fr": "Partie 2 · Anglais", "en": "Part 2 · English"},
    "part_vente": {"fr": "Partie 3 · Vente", "en": "Part 3 · Sales"},
    "part_objections": {"fr": "Partie 4 · Objections", "en": "Part 4 · Objections"},
    "part_simulation": {"fr": "Partie 5 · Simulation", "en": "Part 5 · Simulation"},
    "qcm_hint": {"fr": "Clique sur la bonne lettre.", "en": "Click the right letter."},
    "write_answer": {"fr": "Écris ta réponse en un seul message ({minutes} min max).",
                     "en": "Write your answer in a single message ({minutes} min max)."},
    "sim_intro": {
        "fr": "Tu discutes avec **{name}**, un abonné fictif. Réponds au nom de la créatrice, comme en vrai. "
              "{turns} échanges, {minutes} min max par réponse. C'est parti 👇",
        "en": "You're chatting with **{name}**, a fictional fan. Reply on behalf of the creator, like for real. "
              "{turns} exchanges, {minutes} min max per reply. Let's go 👇",
    },
    "grading": {"fr": "Correction en cours… ⏳", "en": "Grading in progress… ⏳"},
    "test_done": {
        "fr": "Test terminé ✅ Merci ! Tes résultats sont transmis à un responsable, qui valide la décision finale.",
        "en": "Test complete ✅ Thank you! Your results have been sent to a manager, who makes the final decision.",
    },
    "feedback_title": {"fr": "Tes conseils", "en": "Your tips"},
    "timeout": {"fr": "⏰ Temps écoulé, le test est interrompu. Tu peux le relancer avec /test "
                      "({left} tentative(s) restante(s)).",
                "en": "⏰ Time's up, the test has stopped. You can restart it with /test ({left} attempt(s) left)."},
    "test_error": {"fr": "Un souci technique a interrompu ton test. Un responsable est prévenu, tu pourras le refaire.",
                   "en": "A technical issue stopped your test. A manager has been notified, you'll be able to retake it."},
    "not_yours": {"fr": "Ce bouton n'est pas pour toi.", "en": "This button isn't for you."},
    # --- Décisions ---
    "accepted_dm": {
        "fr": "Félicitations {name} 🎉 Tu rejoins l'équipe au niveau **{level}** (commission de départ : {commission} %). "
              "Ton parcours d'intégration arrive juste en dessous.",
        "en": "Congratulations {name} 🎉 You're joining the team at **{level}** level (starting commission: {commission}%). "
              "Your onboarding path is right below.",
    },
    "rejected_dm": {
        "fr": "Merci pour ta candidature et le temps passé sur le test. Elle n'est pas retenue pour le moment. "
              "Tu pourras repostuler dans {days} jours.",
        "en": "Thank you for applying and for the time spent on the test. It isn't accepted for now. "
              "You can apply again in {days} days.",
    },
    "allowed_dm": {"fr": "Bonne nouvelle : un responsable t'autorise à passer le test. Lance /test quand tu es prêt(e).",
                   "en": "Good news: a manager has allowed you to take the test. Use /test when you're ready."},
    "promoted_dm": {"fr": "Bravo 🚀 Tu passes au niveau **{level}** (commission : {commission} %). Continue comme ça !",
                    "en": "Well done 🚀 You've moved up to **{level}** (commission: {commission}%). Keep it up!"},
    "level_dm": {"fr": "Ton niveau a été mis à jour : **{level}** (commission : {commission} %).",
                 "en": "Your level has been updated: **{level}** (commission: {commission}%)."},
    # --- Parcours ---
    "onb_title": {"fr": "Ton parcours d'intégration", "en": "Your onboarding path"},
    "onb_intro": {"fr": "Parcours ces salons dans l'ordre. Une fois chaque étape faite, clique sur son bouton ✅.",
                  "en": "Go through these channels in order. Once each step is done, click its ✅ button."},
    "onb_step_done": {"fr": "Étape validée : {title} ({done}/{total})", "en": "Step done: {title} ({done}/{total})"},
    "onb_complete": {
        "fr": "Parcours terminé 🎯 Tu connais les modèles et le plan de chatting. Prochaines étapes : ton responsable "
              "planifie ton premier shift, et tu suis tes objectifs avec /objectifs et ta progression avec /mon-niveau.",
        "en": "Path complete 🎯 You know the models and the chatting plan. Next: your manager schedules your first "
              "shift, and you follow your goals with /objectifs and your progress with /mon-niveau.",
    },
    "onb_reminder": {"fr": "Petit rappel 👋 il te reste {left} étape(s) dans ton parcours d'intégration. Tape /parcours.",
                     "en": "Quick reminder 👋 you have {left} step(s) left in your onboarding path. Use /parcours."},
    "onb_only_chatters": {"fr": "Le parcours est réservé aux chatteurs de l'équipe.", "en": "The path is for team chatters only."},
    "test_reminder": {"fr": "Ta candidature est validée mais tu n'as pas encore passé le test. Lance /test quand tu es prêt(e) 💪",
                      "en": "Your application is approved but you haven't taken the test yet. Use /test when you're ready 💪"},
    # --- Progression ---
    "not_chatter": {"fr": "Tu n'es pas encore chatteur dans l'équipe. Pour postuler : /postuler",
                    "en": "You're not on the chatter team yet. To apply: /postuler"},
    "lbl_level": {"fr": "Niveau", "en": "Level"},
    "lbl_commission": {"fr": "Commission", "en": "Commission"},
    "lbl_recruit": {"fr": "Score de recrutement", "en": "Recruitment score"},
    "lbl_perf": {"fr": "Tes 4 dernières semaines", "en": "Your last 4 weeks"},
    "lbl_next": {"fr": "Pour passer {level}", "en": "To reach {level}"},
    "lbl_top": {"fr": "Tu es au niveau maximum 💎", "en": "You're at the top level 💎"},
    "lbl_work": {"fr": "Compétences à travailler", "en": "Skills to work on"},
    "lbl_nodata": {"fr": "Pas encore de données de vente importées.", "en": "No sales data imported yet."},
    "perf_line": {
        "fr": "CA : {revenue} · Ventes : {sales} · Conversion : {conv} · Qualité : {quality} · Ponctualité : {punct}",
        "en": "Revenue: {revenue} · Sales: {sales} · Conversion: {conv} · Quality: {quality} · Punctuality: {punct}",
    },
    "objectives_title": {"fr": "Tes objectifs de la semaine", "en": "Your goals this week"},
    "objectives_set": {"fr": "Fixés par ton responsable", "en": "Set by your manager"},
    "objectives_auto": {"fr": "Pour progresser vers {level}", "en": "To progress towards {level}"},
    "no_objectives": {"fr": "Aucun objectif fixé cette semaine. Concentre-toi sur la qualité de tes conversations.",
                      "en": "No goals set this week. Focus on the quality of your conversations."},
    "weekly_title": {"fr": "Ton bilan de la semaine", "en": "Your weekly report"},
    "weekly_coach": {"fr": "Conseil du coach", "en": "Coach's tip"},
    "promo_ready": {"fr": "Tu remplis les conditions pour passer {level} 🔥 Un responsable va valider.",
                    "en": "You meet the requirements for {level} 🔥 A manager will confirm."},
    "welcome_join": {
        "fr": "Bienvenue {mention} ! Pour rejoindre l'équipe des chatteurs, va dans {channel} et clique sur **Postuler**.",
        "en": "Welcome {mention}! To join the chatter team, go to {channel} and click **Apply**.",
    },
}


def t(key: str, lang: str = "fr", **kwargs) -> str:
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry["fr"]
    return text.format(**kwargs) if kwargs else text
