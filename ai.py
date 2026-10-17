"""Appels à l'IA (Claude) : notation, abonné fictif, push, conseils."""
from __future__ import annotations

import json
import logging
import re

from anthropic import AsyncAnthropic

import agency_settings as S
import config

log = logging.getLogger("ai")
_client: AsyncAnthropic | None = None

CONTEXT = (
    "Contexte : agence qui gère des créatrices de contenu adulte (MYM, OnlyFans). Les « chatteurs » "
    "discutent avec les abonnés au nom des créatrices pour fidéliser et vendre du contenu payant (PPV). "
    "Le travail reste suggestif et commercial ; aucun contenu sexuel explicite n'est attendu ni produit ici."
)
RULES = "Règles de l'agence :\n" + "\n".join(f"- {r}" for r in S.AGENCY_RULES)


def _ai() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


async def _ask(system: str, messages: list[dict], max_tokens: int = 1200) -> str:
    resp = await _ai().messages.create(
        model=config.AI_MODEL, max_tokens=max_tokens, system=system, messages=messages)
    return "".join(block.text for block in resp.content if block.type == "text").strip()


def _json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError(f"Réponse IA sans JSON : {text[:200]}")
    return json.loads(match.group())


def _clean_grade(data: dict) -> dict:
    score = max(0, min(100, int(round(float(data.get("score", 0))))))
    return {
        "score": score,
        "strengths": [str(s) for s in data.get("strengths", [])][:4],
        "weaknesses": [str(s) for s in data.get("weaknesses", [])][:4],
        "feedback": str(data.get("feedback", "")),
    }


GRADE_FORMAT = (
    'Réponds uniquement avec un objet JSON : {{"score": 0-100, "strengths": ["..."], '
    '"weaknesses": ["..."], "feedback": "..."}}. strengths et weaknesses : 1 à 3 points courts en français '
    "pour le responsable. feedback : 2 phrases de conseil adressées au candidat, dans sa langue ({lang})."
)


async def grade_open(section: str, items: list[tuple[str, str]], lang: str) -> dict:
    criteria = {
        "vente": "création de lien, personnalisation, présentation de la valeur du contenu, appel à l'action "
                 "clair, ton naturel et humain, orthographe",
        "objections": "empathie, garder le prix ou n'utiliser que des remises raisonnables, transformer "
                      "l'objection en envie, ne jamais être agressif ni suppliant, respect des règles",
    }[section]
    system = (
        f"{CONTEXT}\n{RULES}\nTu es un recruteur exigeant qui note des candidats chatteurs expérimentés. "
        f"Critères pour cette partie ({section}) : {criteria}. Une réponse vide, hors sujet, robotique ou "
        f"copiée d'un modèle générique vaut moins de 40. 90+ = niveau d'un chatteur d'élite.\n"
        + GRADE_FORMAT.format(lang=lang)
    )
    body = "\n\n".join(f"Question {i}: {q}\nRéponse du candidat : {a}" for i, (q, a) in enumerate(items, 1))
    return _clean_grade(_json(await _ask(system, [{"role": "user", "content": body}])))


async def fan_reply(scenario: dict, history: list[dict], lang: str) -> str:
    language = "français" if lang == "fr" else "anglais"
    system = (
        f"{CONTEXT}\nTu joues un abonné FICTIF dans un exercice de formation pour tester un candidat chatteur. "
        f"Personnage : {scenario['name']}, {scenario['brief']}\n"
        f"Écris en {language}, comme un vrai abonné sur son téléphone : messages courts (1 à 3 phrases), "
        "fautes légères possibles, emojis occasionnels. Reste dans le personnage, réagis à ce que dit le "
        "chatteur, résiste un peu avant d'acheter, et achète seulement si on t'a vraiment convaincu. "
        "Ton flirt reste suggestif, jamais explicite. Ne sors jamais du rôle et ne commente pas l'exercice. "
        "Écris uniquement le message de l'abonné."
    )
    opener = {"role": "user", "content": "[Début de la simulation : envoie ton premier message d'abonné.]"}
    return await _ask(system, [opener, *history], max_tokens=300)


async def grade_simulation(scenario: dict, transcript: list[tuple[str, str]], lang: str,
                           avg_response: float | None) -> dict:
    system = (
        f"{CONTEXT}\n{RULES}\nTu notes une simulation de conversation entre un candidat chatteur et un abonné "
        f"fictif ({scenario['name']} : {scenario['brief']}). Critères : création de lien, personnalisation, "
        "capacité à amener une vente sans forcer, gestion des objections, respect strict des règles (une "
        "violation grave = 30 maximum), naturel et orthographe, cohérence du personnage de la créatrice.\n"
        + GRADE_FORMAT.format(lang=lang)
    )
    convo = "\n".join(f"{who}: {text}" for who, text in transcript)
    if avg_response:
        convo += f"\n\n(Temps de réponse moyen du candidat : {avg_response:.0f} secondes.)"
    return _clean_grade(_json(await _ask(system, [{"role": "user", "content": convo}])))


async def generate_pushes(model: dict, push_type: str, theme: str | None, count: int,
                          avoid: list[str]) -> list[str]:
    language = "français" if model.get("lang", "fr") == "fr" else "anglais"
    system = (
        "Tu es copywriter pour une agence qui accompagne des créatrices de contenu adulte sur MYM et OnlyFans. "
        "Tu écris des messages de masse (« push ») que la créatrice envoie à ses abonnés, dans SA voix.\n"
        f"Créatrice : {model['name']}. Personnalité : {model['persona']}. "
        f"Façon d'écrire : {model.get('style') or 'naturelle'}. Limites à respecter : {model.get('limits') or 'aucune précisée'}.\n"
        "Style humanisé : comme un vrai message tapé au téléphone, phrases courtes, ton complice et "
        "personnel, minuscules parfois, 0 à 3 emojis, longueurs variées, aucune tournure marketing ni "
        "hashtag, aucun mot qui sonne robot (« n'hésite pas », « découvre », « exclusif » à répétition).\n"
        "Ton : chaud, taquin, séduisant, qui donne envie de répondre ou d'ouvrir le contenu. Suggestif "
        "uniquement : pas de description sexuelle explicite ni de vocabulaire cru.\n"
        "Interdits : promettre une rencontre ou un contenu qui n'existe pas, urgence mensongère, toute "
        "allusion à un âge jeune, à l'école ou à un mineur, tout ce qui enfreint les CGU des plateformes.\n"
        f"Langue : {language}. Réponds uniquement avec un JSON : {{\"pushes\": [\"...\", \"...\"]}}."
    )
    brief = f"Type de push : {S.PUSH_TYPES.get(push_type, push_type)}. Nombre : {count}."
    if theme:
        brief += f"\nThème / contenu à mettre en avant : {theme}"
    if avoid:
        brief += "\nNe répète pas ces push récents :\n" + "\n".join(f"- {a}" for a in avoid[:10])
    data = _json(await _ask(system, [{"role": "user", "content": brief}], max_tokens=1500))
    return [str(p).strip() for p in data.get("pushes", []) if str(p).strip()][:count]


async def weekly_advice(name: str, lang: str, stats: str, weaknesses: list[str]) -> str:
    language = "français" if lang == "fr" else "anglais"
    system = (
        f"{CONTEXT}\nTu es le coach d'une équipe de chatteurs. Écris en {language} un conseil de 3 phrases "
        "maximum, concret et motivant, pour la semaine à venir. Pas de formule creuse."
    )
    content = f"Chatteur : {name}\nStatistiques : {stats}\nPoints à travailler : {', '.join(weaknesses) or 'aucun noté'}"
    try:
        return await _ask(system, [{"role": "user", "content": content}], max_tokens=300)
    except Exception:  # le bilan part quand même sans conseil
        log.exception("Conseil hebdo indisponible")
        return ""
