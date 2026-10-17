"""Calculs purs : éligibilité, score de recrutement, niveau proposé, progression.

Aucune dépendance à Discord ou à la base : facile à tester et à ajuster.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import agency_settings as S


def parse_int(text: str | None) -> int | None:
    """Premier nombre trouvé dans un texte libre ("2 ans" donne 24 mois, voir parse_months)."""
    if not text:
        return None
    match = re.search(r"\d+", text.replace(" ", ""))
    return int(match.group()) if match else None


def parse_months(text: str | None) -> int | None:
    """Comprend "8 mois", "2 ans", "1 an et demi", "18 months", "3 years", "6"."""
    if not text:
        return None
    low = text.lower().replace(",", ".")
    number = re.search(r"\d+(?:\.\d+)?", low)
    if not number:
        return None
    value = float(number.group())
    if re.search(r"\b(an|ans|année|années|year|years|yr|yrs)\b", low):
        value *= 12
        if "demi" in low or "half" in low:
            value += 6
    return int(round(value))


def eligibility(months: int | None, hours: int | None, platforms: str | None) -> tuple[bool, list[str]]:
    reasons = []
    if months is None or months < S.ELIGIBILITY["min_experience_months"]:
        reasons.append(f"Expérience insuffisante ({months or 0} mois, minimum "
                       f"{S.ELIGIBILITY['min_experience_months']}).")
    if hours is None or hours < S.ELIGIBILITY["min_hours_per_week"]:
        reasons.append(f"Disponibilité insuffisante ({hours or 0} h/semaine, minimum "
                       f"{S.ELIGIBILITY['min_hours_per_week']}).")
    if not platforms or not platforms.strip():
        reasons.append("Aucune plateforme indiquée.")
    return (not reasons, reasons)


def total_score(sections: dict[str, float]) -> float:
    """Moyenne pondérée des parties notées sur 100."""
    weights = {k: w for k, w in S.TEST_WEIGHTS.items() if k in sections}
    if not weights:
        return 0.0
    total_w = sum(weights.values())
    return round(sum(sections[k] * w for k, w in weights.items()) / total_w, 1)


def suggest_level(total: float, sections: dict[str, float]) -> str | None:
    """Niveau proposé à l'entrée, ou None si le bot propose un refus."""
    if sections.get("consignes", 100) < S.MIN_RULES_SCORE or total < S.PASS_SCORE:
        return None
    level = "debutant"
    for threshold, name in S.ENTRY_THRESHOLDS:
        if total >= threshold:
            level = name
            break
    cap = S.LEVELS.index(S.MAX_ENTRY_LEVEL)
    return S.LEVELS[min(S.LEVELS.index(level), cap)]


def next_level(level: str) -> str | None:
    idx = S.LEVELS.index(level)
    return S.LEVELS[idx + 1] if idx + 1 < len(S.LEVELS) else None


@dataclass
class PerfSummary:
    weeks: float
    revenue_total: float
    revenue_week: float
    conversion: float | None
    quality: float | None
    punctuality: float | None
    messages: int
    sales: int


def summarize(rows: list[dict], window_days: int = S.PERFORMANCE_WINDOW_DAYS) -> PerfSummary:
    revenue = sum(float(r.get("revenue") or 0) for r in rows)
    sales = sum(int(r.get("sales") or 0) for r in rows)
    convs = sum(int(r.get("conversations") or 0) for r in rows)
    messages = sum(int(r.get("messages_sent") or 0) for r in rows)
    weeks = max(window_days / 7, 1)

    def mean(key):
        values = [float(r[key]) for r in rows if r.get(key) is not None]
        return round(sum(values) / len(values), 1) if values else None

    return PerfSummary(
        weeks=weeks,
        revenue_total=round(revenue, 2),
        revenue_week=round(revenue / weeks, 2),
        conversion=round(sales / convs * 100, 1) if convs else None,
        quality=mean("quality_score"),
        punctuality=mean("punctuality_score"),
        messages=messages,
        sales=sales,
    )


@dataclass
class PromotionCheck:
    target: str | None
    eligible: bool
    checks: list[tuple[str, bool, str]] = field(default_factory=list)  # (libellé, ok, détail)


def promotion_check(level: str, weeks_at_level: int, perf: PerfSummary, has_data: bool) -> PromotionCheck:
    target = next_level(level)
    if target is None:
        return PromotionCheck(target=None, eligible=False)
    rule = S.PROMOTION_RULES[target]
    cur = S.CURRENCY

    def chk(label, value, minimum, unit=""):
        ok = value is not None and value >= minimum
        shown = "—" if value is None else f"{value:g}{unit}"
        return (label, ok, f"{shown} / {minimum:g}{unit}")

    checks = [
        chk("Ancienneté au niveau (semaines)", weeks_at_level, rule["min_weeks"]),
        chk("Taux de conversion", perf.conversion, rule["conversion"], " %"),
        chk("Qualité des conversations", perf.quality, rule["quality"], "/100"),
        chk("Ponctualité", perf.punctuality, rule["punctuality"], "/100"),
        chk("CA moyen par semaine", perf.revenue_week if has_data else None, rule["revenue_week"], f" {cur}"),
    ]
    return PromotionCheck(target=target, eligible=has_data and all(c[1] for c in checks), checks=checks)
