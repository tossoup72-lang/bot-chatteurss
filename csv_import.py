"""Lecture des rapports de performance (CSV exporté de ton outil de suivi).

Colonnes reconnues (français ou anglais, l'ordre n'a pas d'importance) :
  discord_id | chatteur      identifiant Discord, ou pseudo enregistré
  periode_debut, periode_fin    dates AAAA-MM-JJ ou JJ/MM/AAAA
  ca                            chiffre d'affaires généré
  messages_envoyes              messages envoyés
  ventes                        nombre d'achats (PPV, tips…)
  conversations                 abonnés différents avec qui le chatteur a échangé
  qualite                       note qualité 0-100 (relecture d'un responsable)
  ponctualite                   note ponctualité 0-100
Séparateur ; ou , accepté (Excel français exporte avec ;).
"""
from __future__ import annotations

import csv
import io
import unicodedata
from datetime import date, datetime

ALIASES = {
    "discord_id": {"discord_id", "id_discord", "discord", "id"},
    "chatteur": {"chatteur", "chatter", "pseudo", "username", "nom"},
    "period_start": {"periode_debut", "debut", "date_debut", "period_start", "start", "start_date"},
    "period_end": {"periode_fin", "fin", "date_fin", "period_end", "end", "end_date"},
    "revenue": {"ca", "chiffre_affaires", "revenue", "revenu", "ventes_eur", "montant"},
    "messages_sent": {"messages_envoyes", "messages", "messages_sent"},
    "sales": {"ventes", "achats", "sales", "purchases", "nb_ventes"},
    "conversations": {"conversations", "abonnes_contactes", "fans", "chats"},
    "quality_score": {"qualite", "quality", "note_qualite", "quality_score"},
    "punctuality_score": {"ponctualite", "punctuality", "punctuality_score"},
}
REQUIRED = ["period_start", "period_end", "revenue"]

TEMPLATE = (
    "discord_id;chatteur;periode_debut;periode_fin;ca;messages_envoyes;ventes;conversations;qualite;ponctualite\n"
    "123456789012345678;sarah;2026-10-05;2026-10-11;845,50;1320;37;290;82;95\n"
)


def _norm(header: str) -> str:
    text = unicodedata.normalize("NFKD", header).encode("ascii", "ignore").decode().lower().strip()
    for ch in " -./()'":
        text = text.replace(ch, "_")
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_")


def _date(value: str) -> date:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"date illisible « {value} »")


def _num(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip().replace(" ", "").replace(" ", "").replace("€", "").replace("$", "").replace("%", "")
    if not value:
        return None
    if "," in value and "." in value:  # 1.234,56 ou 1,234.56
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    else:
        value = value.replace(",", ".")
    return float(value)


def parse(raw: bytes, name_to_id: dict[str, int]) -> tuple[list[dict], list[str]]:
    """Retourne (lignes prêtes pour la table performance, erreurs lisibles)."""
    text = raw.decode("utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(text.splitlines()[0] if text else ";", delimiters=";,\t")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";"
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        headers = next(reader)
    except StopIteration:
        return [], ["Fichier vide."]

    mapping: dict[int, str] = {}
    for idx, header in enumerate(headers):
        key = _norm(header)
        for field, names in ALIASES.items():
            if key in names:
                mapping[idx] = field
    found = set(mapping.values())
    missing = [f for f in REQUIRED if f not in found]
    if missing:
        return [], [f"Colonnes manquantes : {', '.join(missing)}. Utilise le modèle /admin modele-csv."]
    if "discord_id" not in found and "chatteur" not in found:
        return [], ["Il faut une colonne discord_id ou chatteur."]

    lower_names = {k.lower(): v for k, v in name_to_id.items()}
    rows, errors = [], []
    for line_no, cells in enumerate(reader, start=2):
        if not any(c.strip() for c in cells):
            continue
        rec = {mapping[i]: c for i, c in enumerate(cells) if i in mapping}
        try:
            member_id = None
            raw_id = (rec.get("discord_id") or "").strip()
            if raw_id.isdigit():
                member_id = int(raw_id)
            elif rec.get("chatteur"):
                member_id = lower_names.get(rec["chatteur"].strip().lower())
            if member_id is None:
                raise ValueError("chatteur introuvable (ni discord_id ni pseudo connu)")
            start, end = _date(rec["period_start"]), _date(rec["period_end"])
            if end < start:
                raise ValueError("période inversée")
            sales = int(_num(rec.get("sales")) or 0)
            convs = int(_num(rec.get("conversations")) or 0)
            row = {
                "discord_id": member_id,
                "period_start": start.isoformat(),
                "period_end": end.isoformat(),
                "revenue": round(_num(rec.get("revenue")) or 0.0, 2),
                "messages_sent": int(_num(rec.get("messages_sent")) or 0),
                "sales": sales,
                "conversations": convs,
                "conversion_rate": round(sales / convs * 100, 2) if convs else None,
                "quality_score": _num(rec.get("quality_score")),
                "punctuality_score": _num(rec.get("punctuality_score")),
            }
            for key, label in (("quality_score", "qualite"), ("punctuality_score", "ponctualite")):
                if row[key] is not None and not 0 <= row[key] <= 100:
                    raise ValueError(f"{label} doit être entre 0 et 100")
            rows.append(row)
        except (ValueError, KeyError) as exc:
            errors.append(f"Ligne {line_no} : {exc}")
    return rows, errors
