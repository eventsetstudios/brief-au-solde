"""Tests unitaires — scripts/matching.py (pytest).

Cas couverts :
  A. client AVEC factures même service → priorisées, stats exactes ;
  B. client SANS facture mais factures ≤ 13 mois d'autres clients → suggestions ;
  C. AUCUNE facture pertinente → exactement "Je ne peux pas confirmer ça".
Plus : seuil 0,45, fenêtre 13 mois, stats, bonus catégorie, normalisation.
"""
from __future__ import annotations

import statistics
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from matching import (  # noqa: E402
    CANNOT_CONFIRM,
    SIMILARITY_THRESHOLD,
    compute_stats,
    find_similar_invoices,
    normalize_text,
    score_invoice,
    within_window,
)

REF = date(2026, 9, 21)  # date de référence figée (déterminisme)

VID = {"service_code": "VID_MO1", "label": "Spot 60s", "qty": 1, "unit": "video"}
MONT = {"service_code": "MONT_H", "label": "Montage horaire", "qty": 10, "unit": "hour"}


def inv(iid, client, code, label, price, day, cat="Video"):
    return {"invoice_id": iid, "client_id": client, "service_code": code,
            "category": cat, "label": label, "unit_price": price,
            "currency": "XOF", "date": day}


# ------------------------------------------------------------ normalisation

def test_normalize_accents_ponctuation_stopwords():
    assert normalize_text("Réalisation d'un Spot 60s, et montage !") == \
        "realisation spot 60s montage"
    assert normalize_text("The Video Edit") == "video edit"
    assert normalize_text("") == ""
    assert normalize_text(None) == ""


def test_bonus_categorie_vaut_0_3():
    idf = {}
    base = {"service_code": "X", "label": "spot 60s"}
    same = {"service_code": "Y", "label": "spot 60s", "category": "Video"}
    other = {"service_code": "Y", "label": "spot 60s", "category": "Photo"}
    svc = dict(base, category="Video")
    assert score_invoice(svc, same, idf) - score_invoice(svc, other, idf) == pytest.approx(0.3)


# ------------------------------------------------------------------ stats

def test_compute_stats_correct():
    prices = [600000, 700000, 750000, 800000]
    stats = compute_stats(prices)
    assert stats == {
        "mean": int(round(statistics.mean(prices))),
        "median": int(round(statistics.median(prices))),
        "min": 600000,
        "max": 800000,
        "std": int(round(statistics.pstdev(prices))),
        "count": 4,
    }
    assert stats["mean"] == 712500
    assert stats["median"] == 725000


def test_compute_stats_vide_erreur():
    with pytest.raises(ValueError):
        compute_stats([])


def test_compute_stats_singleton_std_zero():
    assert compute_stats([750000])["std"] == 0


# ------------------------------------------------------------------ fenêtre

def test_fenetre_13_mois_inclus_14_exclu():
    assert within_window(date(2025, 8, 21), REF, 13) is True   # pile 13 mois
    assert within_window(date(2025, 8, 1), REF, 13) is True    # même mois calendaire
    assert within_window(date(2025, 7, 21), REF, 13) is False  # 14 mois
    assert within_window(date(2026, 9, 22), REF, 13) is False  # facture future
    assert within_window(None, REF, 13) is False


# ------------------------------------------------- cas A : client + historique

HISTO_A = [
    inv(789, 45, "VID_MO1", "Spot 60s diffusion web", 750000, "2026-03-12"),
    inv(790, 45, "VID_MO1", "Spot 60s version reseaux", 690000, "2026-06-01"),
    inv(791, 7, "VID_MO1", "Spot 60s institutionnel", 600000, "2026-05-01"),
    inv(792, 9, "VID_MO1", "Spot 60s festival", 800000, "2026-04-10"),
]


def test_cas_a_client_priorise_et_stats():
    out = find_similar_invoices(45, [VID], months=13, top_n=5,
                                invoices=HISTO_A, reference_date=REF)
    (res,) = out["results"]
    assert res["status"] == "ok"
    # Même client d'abord, même avec un libellé moins proche.
    assert res["matches"][0]["same_client"] is True
    assert res["matches"][0]["invoice_id"] in (789, 790)
    assert res["stats"]["count"] == 4
    assert res["unit_price_suggested"] == res["stats"]["median"] == 720000
    assert all(m["similarity_score"] >= SIMILARITY_THRESHOLD for m in res["matches"])
    src = res["matches"][0]
    assert {"invoice_id", "date", "unit_price"} <= set(src)


def test_top_n_respecte():
    out = find_similar_invoices(45, [VID], months=13, top_n=1,
                                invoices=HISTO_A, reference_date=REF)
    assert len(out["results"][0]["matches"]) == 1


# --------------------------------- cas B : autres clients, ≤ 13 mois

HISTO_B = [
    inv(791, 7, "VID_MO1", "Spot 60s institutionnel", 600000, "2026-05-01"),
    inv(792, 9, "VID_MO1", "Spot 60s festival", 800000, "2026-04-10"),
]


def test_cas_b_autres_clients_ok():
    out = find_similar_invoices(99, [VID], months=13, top_n=5,
                                invoices=HISTO_B, reference_date=REF)
    (res,) = out["results"]
    assert res["status"] == "ok"
    assert all(m["same_client"] is False for m in res["matches"])
    assert res["stats"]["count"] == 2
    assert res["unit_price_suggested"] == 700000


# ----------------------------------------- cas C : rien de pertinent

def test_cas_c_vieux_historique_phrase_exacte():
    vieux = [inv(700, 45, "VID_MO1", "Spot 60s archive", 500000, "2024-01-10")]
    out = find_similar_invoices(45, [VID], months=13, top_n=5,
                                invoices=vieux, reference_date=REF)
    (res,) = out["results"]
    assert res["status"] == "unconfirmed"
    assert res["message"] == CANNOT_CONFIRM
    assert res["stats"] is None and res["unit_price_suggested"] is None


def test_cas_c_score_sous_seuil_phrase_exacte():
    lointain = [inv(701, 45, "PLOMB_Z", "Reparation plomberie urgente", 50000, "2026-08-01")]
    out = find_similar_invoices(45, [dict(VID, category="Video")], months=13,
                                top_n=5, invoices=lointain, reference_date=REF)
    (res,) = out["results"]
    assert res["status"] == "unconfirmed"
    assert res["message"] == CANNOT_CONFIRM


def test_cas_c_historique_vide():
    out = find_similar_invoices(45, [VID], months=13, top_n=5,
                                invoices=[], reference_date=REF)
    assert out["results"][0]["message"] == CANNOT_CONFIRM
