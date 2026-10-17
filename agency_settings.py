"""Réglages métier de l'agence : modifie ce fichier pour adapter le bot.

Les chiffres ci-dessous sont des valeurs de départ raisonnables, à ajuster
selon tes conditions réelles (commissions, objectifs, seuils).
"""

# --- Niveaux -----------------------------------------------------------------
# Ordre du plus bas au plus haut. La commission est indicative et s'affiche
# dans /mon-niveau ; c'est ton contrat qui fait foi.
LEVELS = ["debutant", "junior", "confirme", "expert"]
LEVEL_INFO = {
    "debutant": {"fr": "Débutant", "en": "Beginner", "emoji": "🌱", "commission": 8},
    "junior": {"fr": "Junior", "en": "Junior", "emoji": "🔹", "commission": 10},
    "confirme": {"fr": "Confirmé", "en": "Confirmed", "emoji": "🔷", "commission": 12},
    "expert": {"fr": "Expert", "en": "Expert", "emoji": "💎", "commission": 15},
}

# --- Recrutement -------------------------------------------------------------
ELIGIBILITY = {
    "min_experience_months": 6,  # expérience minimale en chatting
    "min_hours_per_week": 20,  # disponibilité minimale
}
REAPPLY_COOLDOWN_DAYS = 30  # délai avant de repostuler après un refus
MAX_TEST_ATTEMPTS = 2

# Poids de chaque partie du test (total = 100)
TEST_WEIGHTS = {
    "consignes": 20,
    "anglais": 15,
    "vente": 20,
    "objections": 20,
    "simulation": 25,
}
PASS_SCORE = 55  # sous ce score, le bot propose un refus
MIN_RULES_SCORE = 60  # le respect des consignes est éliminatoire en dessous
# Score total minimal pour proposer chaque niveau à l'entrée
ENTRY_THRESHOLDS = [(90, "expert"), (78, "confirme"), (65, "junior"), (PASS_SCORE, "debutant")]
# Le niveau Expert se gagne sur le terrain : à l'entrée on plafonne à Confirmé.
MAX_ENTRY_LEVEL = "confirme"

SIMULATION_TURNS = 6  # nombre de messages de l'abonné fictif
OPEN_ANSWER_TIMEOUT = 15 * 60  # secondes pour répondre à une question ouverte
SIMULATION_TIMEOUT = 5 * 60  # secondes par réponse pendant la simulation

# --- Progression (sur les 4 dernières semaines de données importées) ---------
# Pour passer AU niveau indiqué, toutes les conditions doivent être remplies.
PROMOTION_RULES = {
    "junior": {"min_weeks": 2, "conversion": 8.0, "quality": 70, "punctuality": 85, "revenue_week": 300},
    "confirme": {"min_weeks": 4, "conversion": 12.0, "quality": 78, "punctuality": 90, "revenue_week": 800},
    "expert": {"min_weeks": 6, "conversion": 15.0, "quality": 85, "punctuality": 95, "revenue_week": 1500},
}
PERFORMANCE_WINDOW_DAYS = 28
CURRENCY = "€"

# --- Règles de l'agence (utilisées dans les tests et la notation IA) ---------
AGENCY_RULES = [
    "Ne jamais proposer ni accepter de rencontre réelle avec un abonné.",
    "Ne jamais divulguer d'informations personnelles réelles sur la modèle.",
    "Tous les paiements passent par la plateforme, jamais en dehors.",
    "Respecter les prix et les remises autorisées par le plan de chatting.",
    "Respecter les limites de contenu de chaque modèle.",
    "Si un abonné semble mineur : arrêter la conversation et prévenir un responsable immédiatement.",
    "Transmettre ses notes abonnés au chatteur suivant à la fin du shift.",
]

# --- Parcours des nouveaux chatteurs ----------------------------------------
# Remplace les 0 par les ID des salons de ton serveur (clic droit > Copier l'ID).
ONBOARDING_STEPS = [
    {
        "key": "regles",
        "channel_id": 0,
        "fr": ("Règlement de l'agence", "Lis le règlement en entier : horaires, confidentialité, règles de conversation."),
        "en": ("Agency rules", "Read the full rules: schedules, confidentiality, conversation rules."),
    },
    {
        "key": "modeles",
        "channel_id": 0,
        "fr": ("Fiches des modèles", "Étudie chaque fiche : personnalité, façon d'écrire, limites, tarifs, abonnés VIP."),
        "en": ("Model profiles", "Study each profile: personality, writing style, limits, prices, VIP fans."),
    },
    {
        "key": "plan",
        "channel_id": 0,
        "fr": ("Plan de chatting", "Apprends le plan : horaires des push, ordre des PPV, prix et remises autorisées."),
        "en": ("Chatting plan", "Learn the plan: push times, PPV order, prices and allowed discounts."),
    },
    {
        "key": "scripts",
        "channel_id": 0,
        "fr": ("Scripts et exemples", "Parcours les conversations modèles et les réponses aux objections fréquentes."),
        "en": ("Scripts and examples", "Go through example chats and answers to common objections."),
    },
    {
        "key": "planning",
        "channel_id": 0,
        "fr": ("Planning des shifts", "Repère tes créneaux et la procédure de passation entre chatteurs."),
        "en": ("Shift schedule", "Find your slots and the handover procedure between chatters."),
    },
    {
        "key": "rapports",
        "channel_id": 0,
        "fr": ("Rapports de fin de shift", "Regarde comment remplir ton rapport : ventes, notes abonnés, incidents."),
        "en": ("End-of-shift reports", "See how to fill in your report: sales, fan notes, incidents."),
    },
]
ONBOARDING_REMINDER_DAYS = 14  # relances pendant les X premiers jours

# --- Push -------------------------------------------------------------------
# Heures (fuseau de config.TIMEZONE) où le bot propose des push dans ton salon.
PUSH_AUTO_HOURS = [(11, 0), (20, 30)]
PUSH_AUTO_COUNT = 3  # nombre de propositions par modèle et par créneau
PUSH_TYPES = {
    "matin": "Message du matin, réveil complice qui donne envie de répondre",
    "soir": "Message du soir, ambiance intime et taquine",
    "ppv": "Teaser pour un contenu payant (PPV) décrit dans le thème",
    "relance": "Relance d'abonnés inactifs qui n'ont pas répondu depuis longtemps",
    "weekend": "Message spécial week-end",
    "libre": "Thème libre décrit par le responsable",
}

# --- Bilans -----------------------------------------------------------------
WEEKLY_REPORT_DAY = 0  # 0 = lundi
WEEKLY_REPORT_HOUR = (9, 0)
DAILY_REMINDER_HOUR = (10, 0)
