"""Variables d'environnement (secrets et identifiants Discord).

Tout ce qui est secret ou propre à ton serveur se règle dans les variables
d'environnement (fichier .env en local, onglet Variables sur Railway).
Les réglages métier (niveaux, commissions, critères, parcours) sont dans
agency_settings.py.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int = 0) -> int:
    value = os.getenv(name, "").strip()
    return int(value) if value.isdigit() else default


# --- Secrets -----------------------------------------------------------------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
# Clé "service_role" (Project Settings > API) : le bot écrit dans la base, ne la partage jamais.
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
AI_MODEL = os.getenv("AI_MODEL", "claude-sonnet-5-5").strip()

# --- Serveur Discord ---------------------------------------------------------
GUILD_ID = _int("GUILD_ID")
OWNER_ID = _int("OWNER_ID")  # toi : seul à accéder au salon des push
TIMEZONE = os.getenv("TIMEZONE", "Europe/Paris")

# Salons
RECRUITMENT_CHANNEL_ID = _int("RECRUITMENT_CHANNEL_ID")  # panneau "Postuler"
TESTS_CHANNEL_ID = _int("TESTS_CHANNEL_ID")  # fils privés de test
ADMIN_CHANNEL_ID = _int("ADMIN_CHANNEL_ID")  # résultats, validations, bilans
PUSH_CHANNEL_ID = _int("PUSH_CHANNEL_ID")  # salon privé toi + bot
WELCOME_CHANNEL_ID = _int("WELCOME_CHANNEL_ID")  # optionnel : accueil des arrivants

# Rôles
STAFF_ROLE_ID = _int("STAFF_ROLE_ID")  # responsables
CANDIDATE_ROLE_ID = _int("CANDIDATE_ROLE_ID")
CHATTER_ROLE_ID = _int("CHATTER_ROLE_ID")
LEVEL_ROLE_IDS = {
    "debutant": _int("ROLE_DEBUTANT_ID"),
    "junior": _int("ROLE_JUNIOR_ID"),
    "confirme": _int("ROLE_CONFIRME_ID"),
    "expert": _int("ROLE_EXPERT_ID"),
}


def check() -> list[str]:
    """Retourne la liste des réglages manquants indispensables au démarrage."""
    missing = []
    for name, value in {
        "DISCORD_TOKEN": DISCORD_TOKEN,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": SUPABASE_KEY,
        "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
        "GUILD_ID": GUILD_ID,
        "OWNER_ID": OWNER_ID,
        "TESTS_CHANNEL_ID": TESTS_CHANNEL_ID,
        "ADMIN_CHANNEL_ID": ADMIN_CHANNEL_ID,
        "PUSH_CHANNEL_ID": PUSH_CHANNEL_ID,
    }.items():
        if not value:
            missing.append(name)
    return missing
