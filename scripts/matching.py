#!/usr/bin/env python3
"""Matching factures ↔ services pour Évents & Studios (variante pure-python, stdlib seule).

But : retrouver, pour chaque service demandé, les lignes de factures similaires
(≤ 13 mois par défaut), en priorisant celles du même client, et calculer des
statistiques de prix (moyenne, médiane, min, max, écart-type, effectif) avec
leurs sources (IDs factures, dates).

Choix assumé : pas de scikit-learn / numpy / pandas. Le TF-IDF + cosinus est
réimplémenté en pur Python (quelques dizaines de lignes) pour que le skill reste
exécutable partout sans installation (machine de Lycris, NAS sans accès internet).
Si un volume important l'exige un jour, la variante sklearn est documentée dans
le README (même interface, mêmes sorties).

Interface principale :
    find_similar_invoices(client_id, services, months=13, top_n=5)

Règle impérative : sans historique pertinent (aucun score ≥ 0,45), on renvoie
exactement "Je ne peux pas confirmer ça" et on demande une saisie manuelle.
On n'invente jamais un prix.

Scoring (spécification) :
    score = cosinus TF-IDF(description_service ↔ description_ligne)
            + 1.0 si même service_code
            + 0.3 si même catégorie
    avec filtre temporel : facture > `months` mois → facteur 0 (exclue).

Devise : XOF (F CFA) par défaut. Langue : français (stopwords FR + EN).
"""
from __future__ import annotations

import math
import re
import statistics
import unicodedata
from datetime import date, datetime
from typing import Optional

CANNOT_CONFIRM = "Je ne peux pas confirmer ça"
ALGORITHM_VERSION = "matching-1.0.0-purepython"
SIMILARITY_THRESHOLD = 0.45
DEFAULT_MONTHS = 13
DEFAULT_TOP_N = 5
DEFAULT_CURRENCY = "XOF"

STOPWORDS_FR = frozenset("""
au aux avec ce ces dans de des du elle en et eux il ils je la le les leur lui
ma mais me même mes moi mon ne nos notre nous on ou par pas pour qu que qui
sa se ses son sur ta te tes toi ton tu un une vos votre vous c d j l m n s t y
été être avoir faire comme tout tous toute toutes peut plus moins très aussi
sans sous entre vers chez dont où donc or ni car hors périmètre afin
""".split())

STOPWORDS_EN = frozenset("""
a an and are as at be been but by for from has have he in is it its of on or
that the their then there these they this to was will with you your we our
can not no yes if so than too very just about into over after
""".split())

STOPWORDS = STOPWORDS_FR | STOPWORDS_EN


# ------------------------------------------------------------- normalisation

def normalize_text(text: str | None) -> str:
    """lower() + sans accents + sans ponctuation + sans stopwords FR/EN."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [t for t in text.split() if t and t not in STOPWORDS]
    return " ".join(tokens)


def _tokens(text: str | None) -> list[str]:
    return normalize_text(text).split()


def _term_freq(tokens: list[str]) -> dict[str, float]:
    tf: dict[str, float] = {}
    if not tokens:
        return tf
    for t in tokens:
        tf[t] = tf.get(t, 0.0) + 1.0
    n = float(len(tokens))
    return {t: c / n for t, c in tf.items()}


def _idf(doc_tfs: list[dict[str, float]]) -> dict[str, float]:
    """IDF lissé : log((1 + N) / (1 + df)) + 1. Zéro si corpus vide."""
    n = len(doc_tfs)
    if n == 0:
        return {}
    df: dict[str, int] = {}
    for tf in doc_tfs:
        for t in tf:
            df[t] = df.get(t, 0) + 1
    return {t: math.log((1.0 + n) / (1.0 + c)) + 1.0 for t, c in df.items()}


def _tfidf(tf: dict[str, float], idf: dict[str, float]) -> dict[str, float]:
    return {t: f * idf.get(t, 0.0) for t, f in tf.items()}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a.get(t, 0.0) * w for t, w in b.items())
    na = math.sqrt(sum(w * w for w in a.values()))
    nb = math.sqrt(sum(w * w for w in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


# ------------------------------------------------------------------- dates

def parse_date(value: str | date | datetime | None) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def months_between(older: date, newer: date) -> int:
    """Mois calendaires complets entre deux dates (négatif si older > newer)."""
    delta = (newer.year - older.year) * 12 + (newer.month - older.month)
    if newer.day < older.day:
        delta -= 1
    return delta


def within_window(day: date | None, ref: date, months: int) -> bool:
    if day is None:
        return False
    age = months_between(day, ref)
    return 0 <= age <= months


# ------------------------------------------------------------------ scoring

def score_invoice(service: dict, invoice: dict, idf: dict[str, float]) -> float:
    """Score de similarité service ↔ ligne de facture (voir docstring module)."""
    service_text = " ".join(str(service.get(k) or "") for k in ("label", "service_code", "description"))
    invoice_text = " ".join(str(invoice.get(k) or "") for k in ("label", "description"))
    cos = _cosine(
        _tfidf(_term_freq(_tokens(service_text)), idf),
        _tfidf(_term_freq(_tokens(invoice_text)), idf),
    )
    bonus_code = 1.0 if (service.get("service_code") or "") == (invoice.get("service_code") or "") and service.get("service_code") else 0.0
    bonus_cat = 0.0
    if service.get("category") and service.get("category") == invoice.get("category"):
        bonus_cat = 0.3
    return round(cos + bonus_code + bonus_cat, 4)


def compute_stats(prices: list[float]) -> dict:
    """Moyenne, médiane, min, max, écart-type (population), effectif. Entiers XOF."""
    if not prices:
        raise ValueError("compute_stats exige au moins un prix")
    vals = [float(p) for p in prices]
    return {
        "mean": int(round(statistics.mean(vals))),
        "median": int(round(statistics.median(vals))),
        "min": int(round(min(vals))),
        "max": int(round(max(vals))),
        "std": int(round(statistics.pstdev(vals))) if len(vals) > 1 else 0,
        "count": len(vals),
    }


# ------------------------------------------------------- source d'historique

def referentiel_history() -> list[dict]:
    """Historique de secours issu de references/referentiel.md (affaires 2026).

    Utilisé quand Odoo est injoignable. Source annoncée comme "referentiel"
    dans chaque résultat — jamais présentée comme des factures réelles.
    """
    return [
        {"invoice_id": 290, "client_id": 832, "service_code": "PROD_107",
         "category": "Production audiovisuelle",
         "label": "Captation couverture evenement Festival des Grillades Abidjan forfait 2 jours",
         "unit_price": 800000, "currency": "XOF", "date": "2026-09-05"},
        {"invoice_id": 448, "client_id": 832, "service_code": "PROD_107",
         "category": "Production audiovisuelle",
         "label": "Captation couverture evenement Festival des Grillades Grand-Bassam 2 jours",
         "unit_price": 800000, "currency": "XOF", "date": "2026-08-08"},
        {"invoice_id": 448, "client_id": 832, "service_code": "PROD_119",
         "category": "Frais refacturés",
         "label": "Frais regie transport restauration Grand-Bassam 2 jours",
         "unit_price": 400000, "currency": "XOF", "date": "2026-08-08"},
        {"invoice_id": 447, "client_id": 832, "service_code": "PROD_107",
         "category": "Production audiovisuelle",
         "label": "Captation photo video tournee DABOSA 8 etapes forfait",
         "unit_price": 4000000, "currency": "XOF", "date": "2026-07-04"},
        {"invoice_id": 447, "client_id": 832, "service_code": "PROD_119",
         "category": "Frais refacturés",
         "label": "Deplacement hebergement regie tournee DABOSA",
         "unit_price": 1440000, "currency": "XOF", "date": "2026-07-04"},
        {"invoice_id": 343, "client_id": 832, "service_code": "PROD_107",
         "category": "Production audiovisuelle",
         "label": "Campagne Cinquantenaire MAGGI captation photo video regie forfait",
         "unit_price": 4650000, "currency": "XOF", "date": "2026-09-18"},
        {"invoice_id": 343, "client_id": 832, "service_code": "PROD_119",
         "category": "Frais refacturés",
         "label": "Deplacement hebergement regie tournage MAGGI",
         "unit_price": 1680000, "currency": "XOF", "date": "2026-09-18"},
    ]


def get_invoice_history(
    client_id: int | None = None,
    months: int = DEFAULT_MONTHS,
    reference_date: date | None = None,
) -> tuple[list[dict], str]:
    """Historique des lignes de factures : Odoo d'abord, référentiel sinon.

    Retourne (lignes, source) avec source = "odoo" ou "referentiel".
    N'invente jamais : si Odoo échoue, la source "referentiel" est annoncée.
    """
    ref = reference_date or date.today()
    try:
        from odoo import list_invoices  # import tardif : évite le cycle odoo ↔ matching
        payload = list_invoices(client_id=client_id, since_date=None)
        if payload.get("source") == "odoo":
            lines = [l for l in payload["invoices"]
                     if within_window(parse_date(l.get("date")), ref, months)]
            return lines, "odoo"
    except Exception:
        pass
    lines = [l for l in referentiel_history()
             if within_window(parse_date(l.get("date")), ref, months)]
    return lines, "referentiel"


# ---------------------------------------------------------------- interface

def find_similar_invoices(
    client_id: int,
    services: list[dict],
    months: int = DEFAULT_MONTHS,
    top_n: int = DEFAULT_TOP_N,
    invoices: list[dict] | None = None,
    reference_date: date | str | None = None,
) -> dict:
    """Retrouve les factures similaires pour chaque service demandé.

    - Priorise les factures du même client pour le même `service_code`.
    - Ne retient que les factures ≤ `months` mois et de score ≥ 0,45.
    - Sans historique pertinent : statut "unconfirmed" avec exactement
      "Je ne peux pas confirmer ça" + demande de saisie manuelle.

    `invoices` (optionnel) injecte l'historique — utilisé par les tests et le
    mode hors-ligne. Sinon, lecture Odoo puis fallback référentiel.
    Chaque item retourné porte ses sources (IDs factures, dates) et ses stats.
    """
    ref = parse_date(reference_date) if not isinstance(reference_date, date) else reference_date
    ref = ref or date.today()

    source = "fourni"
    if invoices is None:
        invoices, source = get_invoice_history(client_id=client_id, months=months, reference_date=ref)
    else:
        invoices = [l for l in invoices if within_window(parse_date(l.get("date")), ref, months)]

    corpus = [_term_freq(_tokens(" ".join(str(l.get(k) or "") for k in ("label", "description")))) for l in invoices]
    idf = _idf(corpus + [_term_freq(_tokens(" ".join(str(s.get(k) or "") for k in ("label", "service_code", "description")))) for s in services])

    results = []
    for service in services:
        scored = []
        for inv in invoices:
            day = parse_date(inv.get("date"))
            if not within_window(day, ref, months):
                continue
            score = score_invoice(service, inv, idf)
            if score < SIMILARITY_THRESHOLD:
                continue
            scored.append({
                "invoice_id": inv.get("invoice_id"),
                "date": str(day),
                "unit_price": float(inv.get("unit_price") or 0),
                "currency": inv.get("currency") or DEFAULT_CURRENCY,
                "similarity_score": score,
                "same_client": bool(client_id is not None and inv.get("client_id") == client_id),
                "label": inv.get("label") or "",
            })
        # Priorité : même client d'abord, puis meilleur score.
        scored.sort(key=lambda m: (not m["same_client"], -m["similarity_score"]))
        kept = scored[: max(int(top_n), 0)]

        item: dict = {
            "service_code": service.get("service_code"),
            "label": service.get("label"),
            "qty": service.get("qty", 1),
            "unit": service.get("unit", ""),
            "history_source": source,
        }
        if not kept:
            item.update({
                "status": "unconfirmed",
                "message": CANNOT_CONFIRM,
                "action_requise": "Saisie manuelle du prix : aucun historique pertinent (même client ou ≤13 mois, score ≥ 0,45).",
                "matches": [],
                "stats": None,
                "unit_price_suggested": None,
            })
        else:
            item.update({
                "status": "ok",
                "matches": kept,
                "stats": compute_stats([m["unit_price"] for m in kept]),
                # Prix suggéré robuste : la médiane (insensible aux extrêmes).
                "unit_price_suggested": int(round(statistics.median([m["unit_price"] for m in kept]))),
            })
        results.append(item)

    return {
        "client_id": client_id,
        "window_months": months,
        "threshold": SIMILARITY_THRESHOLD,
        "algorithm_version": ALGORITHM_VERSION,
        "results": results,
    }
