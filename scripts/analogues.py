#!/usr/bin/env python3
"""Trouve les affaires comparables à celle qu'on s'apprête à chiffrer.

Rapproche par client, par produits du catalogue et par volume de jours, puis
remonte pour chaque affaire ce qui a été vendu, ce que ça a réellement coûté et
la marge constatée. C'est la matière première du chiffrage par analogie.

Nouveau : la suggestion de prix à partir des lignes de factures (≤ 13 mois)
passe par scripts/matching.py en backend (TF-IDF + stats + sources). La
fonction find_similar_invoices y est réexportée ici pour compatibilité.

Usage :
    python3 analogues.py --client 832
    python3 analogues.py --produits 107,112 --jours 2
    python3 analogues.py --client 832 --produits 107 --limit 6
    python3 analogues.py --suggest VID_MO1 --label "Spot 60s" --client 45
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from odoo import Odoo, OdooError

try:
    from matching import (
        CANNOT_CONFIRM,
        DEFAULT_MONTHS,
        DEFAULT_TOP_N,
        compute_stats,
        find_similar_invoices,
    )
except ImportError:  # exécution depuis un autre répertoire
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from matching import (
        CANNOT_CONFIRM,
        DEFAULT_MONTHS,
        DEFAULT_TOP_N,
        compute_stats,
        find_similar_invoices,
    )

__all__ = ["cout_reel", "suggere_prix", "find_similar_invoices",
           "compute_stats", "CANNOT_CONFIRM"]


def cout_reel(o: Odoo, projets: list[int]) -> dict:
    """Coûts analytiques d'un ou plusieurs projets, ventilés par nature."""
    if not projets:
        return {"total": 0.0, "par_nature": {}, "personnes": {}}
    infos = o.search_read("project.project", [["id", "in", projets]], ["account_id"])
    comptes = [p["account_id"][0] for p in infos if p.get("account_id")]
    if not comptes:
        return {"total": 0.0, "par_nature": {}, "personnes": {}}
    lignes = o.search_read(
        "account.analytic.line", [["account_id", "in", comptes]],
        ["name", "amount", "unit_amount", "employee_id", "general_account_id",
         "product_id", "project_id"], limit=2000)
    par_nature: dict[str, float] = {}
    personnes: dict[str, float] = {}
    for l in lignes:
        if l["amount"] >= 0:
            continue
        nature = (l.get("general_account_id") or [None, "non ventilé"])[1]
        par_nature[nature] = round(par_nature.get(nature, 0) - l["amount"], 2)
        if l.get("employee_id"):
            nom = l["employee_id"][1]
            personnes[nom] = round(personnes.get(nom, 0) + (l.get("unit_amount") or 0), 2)
    total = round(sum(par_nature.values()), 2)
    return {"total": total, "par_nature": par_nature, "jours_par_personne": personnes}


def suggere_prix(client_id: int, service_code: str, label: str = "",
                 months: int = DEFAULT_MONTHS, top_n: int = DEFAULT_TOP_N,
                 invoices: list[dict] | None = None) -> dict:
    """Prix suggéré pour un service à partir des factures ≤ `months` mois.

    Backend : scripts/matching.py. Retourne stats + sources, ou exactement
    "Je ne peux pas confirmer ça" sans historique pertinent. N'invente jamais.
    """
    out = find_similar_invoices(
        int(client_id),
        [{"service_code": service_code, "label": label or service_code,
          "qty": 1, "unit": ""}],
        months=months, top_n=top_n, invoices=invoices,
    )
    return out["results"][0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--client", help="id res.partner")
    ap.add_argument("--produits", help="ids product.product séparés par des virgules")
    ap.add_argument("--jours", type=float, help="volume de jours visé, pour le tri")
    ap.add_argument("--limit", type=int, default=4, help="nombre d'affaires à remonter")
    ap.add_argument("--suggest", help="service_code pour une suggestion de prix (backend matching)")
    ap.add_argument("--label", default="", help="libellé du service pour --suggest")
    ap.add_argument("--months", type=int, default=DEFAULT_MONTHS)
    ap.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    a = ap.parse_args()

    if a.suggest:
        if not a.client:
            ap.error("--suggest exige --client")
        print(json.dumps(suggere_prix(int(a.client), a.suggest, a.label,
                                      months=a.months, top_n=a.top_n),
                         ensure_ascii=False, indent=2, default=str))
        return

    if not (a.client or a.produits):
        ap.error("donne au moins --client ou --produits")

    try:
        o = Odoo()
    except OdooError as exc:
        print(json.dumps({"ok": False, "erreur": str(exc)}, ensure_ascii=False, indent=2))
        sys.exit(2)

    produits = [int(x) for x in a.produits.split(",")] if a.produits else []

    # Un rapprochement par client est plus fort qu'un rapprochement par produit :
    # on les collecte séparément pour pouvoir le dire dans la sortie.
    lots = []
    if a.client:
        lots.append(("meme_client", [["state", "in", ["sale", "done"]],
                                     ["partner_id", "=", int(a.client)]]))
    if produits:
        ids = [l["order_id"][0] for l in o.search_read(
            "sale.order.line", [["product_id", "in", produits]], ["order_id"], limit=400)]
        if ids:
            lots.append(("memes_produits", [["state", "in", ["sale", "done"]],
                                            ["id", "in", list(set(ids))]]))

    vus, affaires = set(), []
    for origine, domain in lots:
        for c in o.search_read("sale.order", domain,
                               ["name", "partner_id", "date_order", "amount_untaxed",
                                "payment_term_id", "project_ids"],
                               limit=40, order="date_order desc"):
            if c["id"] in vus:
                continue
            vus.add(c["id"])
            lignes = o.search_read("sale.order.line", [["order_id", "=", c["id"]]],
                                   ["product_id", "product_uom_qty", "price_unit",
                                    "price_subtotal"])
            jours = sum(l["product_uom_qty"] for l in lignes
                        if produits and l.get("product_id")
                        and l["product_id"][0] in produits) or None
            couts = cout_reel(o, c.get("project_ids") or [])
            vendu = c["amount_untaxed"]
            affaires.append({
                "origine": origine,
                "commande": c["name"],
                "client": (c.get("partner_id") or [None, None])[1],
                "date": c["date_order"],
                "vendu_ht": vendu,
                "condition_paiement": (c.get("payment_term_id") or [None, None])[1],
                "lignes": [{"produit": (l.get("product_id") or [None, "?"])[1],
                            "qte": l["product_uom_qty"], "pu": l["price_unit"],
                            "total": l["price_subtotal"]} for l in lignes],
                "jours_vendus": jours,
                "cout_reel": couts["total"],
                "cout_par_nature": couts["par_nature"],
                "jours_par_personne": couts["jours_par_personne"],
                "marge": round(vendu - couts["total"], 2),
                "marge_pct": round((vendu - couts["total"]) / vendu * 100, 1) if vendu else None,
            })

    # Le plus proche d'abord : même client, puis volume de jours voisin.
    def cle(x):
        ecart = abs((x["jours_vendus"] or 0) - a.jours) if a.jours else 0
        return (0 if x["origine"] == "meme_client" else 1, ecart)

    affaires.sort(key=cle)
    retenues = affaires[:a.limit]

    chiffrees = [x for x in retenues if x["cout_reel"] > 0 and x["marge_pct"] is not None]
    synthese = {
        "affaires_trouvees": len(affaires),
        "affaires_retenues": len(retenues),
        "affaires_avec_couts_reels": len(chiffrees),
        "marge_pct_mediane": None,
        "avertissement": None,
    }
    if chiffrees:
        marges = sorted(x["marge_pct"] for x in chiffrees)
        synthese["marge_pct_mediane"] = marges[len(marges) // 2]
    if not chiffrees:
        synthese["avertissement"] = (
            "Aucune affaire comparable ne porte de coûts analytiques : les marges "
            "affichées ne veulent rien dire. Chiffre à partir du catalogue et du coût "
            "de revient, et annonce que le prix est une hypothèse."
        )

    print(json.dumps({"synthese": synthese, "affaires": retenues},
                     ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
