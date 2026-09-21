#!/usr/bin/env python3
"""Propose une équipe pour une période donnée, ou liste le matériel disponible.

Croise quatre choses : la disponibilité sur la période (affectation qui chevauche,
congé validé, indisponibilité déclarée), l'expérience du même type d'affaire lue
dans les feuilles de temps, la tenue des délais sur les tâches passées, et le coût
par journée.

Le conflit avertit, il ne bloque pas : c'est Lycris qui arbitre.

Avec --materiel : liste le parc es_production par catégorie (état, disponibles,
hors service), les conflits de réservation sur la période et les kits
prédéfinis — la matière du questionnaire « matériel à utiliser ».

Usage :
    python3 equipe.py --du 2026-10-12 --au 2026-10-13
    python3 equipe.py --du 2026-10-12 --au 2026-10-13 --produits 107,112
    python3 equipe.py --du 2026-10-12 --au 2026-10-13 --jours 2
    python3 equipe.py --du 2026-10-12 --au 2026-10-13 --materiel
    python3 equipe.py --du 2026-10-12 --au 2026-10-13 --materiel --categorie Son
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from odoo import Odoo, OdooError


def _chevauche(d1, f1, d2, f2) -> bool:
    return d1 <= f2 and d2 <= f1


def projets_du_type(o: Odoo, produits: list[int]) -> list[int]:
    """Projets nés de commandes portant ces produits — le passé comparable."""
    if not produits:
        return []
    cmd_ids = {l["order_id"][0] for l in o.search_read(
        "sale.order.line", [["product_id", "in", produits]], ["order_id"], limit=400)
        if l.get("order_id")}
    if not cmd_ids:
        return []
    projets = o.search_read("project.project", [["sale_order_id", "in", list(cmd_ids)]],
                            ["id"], limit=200)
    return [p["id"] for p in projets]


def cmd_materiel(o: Odoo, du: str, au: str, categorie: str | None):
    """Parc es_production : état, conflits de réservation sur la période, kits.

    Sortie = la matière du questionnaire « matériel à utiliser » (série E2) :
    ce qui est proposable, ce qui est en conflit (sans bloquer) et ce qui est
    hors service. Le day_rate affiché est indicatif : il n'entre JAMAIS dans
    le coût réel d'un tournage (amortissement), seule la facture fournisseur
    de sous-location fait foi.
    """
    if not o.has_model("es.equipment"):
        print(json.dumps({"ok": False,
                          "erreur": "module es_production absent — repli : equipment_note "
                                    "(texte libre) sur es.shooting"}, ensure_ascii=False, indent=2))
        sys.exit(2)
    dom = [["active", "=", True]]
    if categorie:
        cats = o.search_read("es.equipment.category", [["name", "ilike", categorie]], ["id"], limit=10)
        if not cats:
            print(json.dumps({"ok": False, "erreur": f"catégorie '{categorie}' introuvable"},
                             ensure_ascii=False, indent=2))
            sys.exit(2)
        dom.append(["category_id", "in", [c["id"] for c in cats]])
    equipements = o.search_read(
        "es.equipment", dom,
        ["name", "category_id", "brand", "model", "quantity", "quantity_available",
         "state", "is_available", "day_rate", "ownership"], limit=500)

    # Réservations qui chevauchent la période et immobilisent le matériel.
    conflits: dict[int, list] = {}
    for b in o.search_read(
            "es.equipment.booking",
            [["date_from", "<=", au + " 23:59:59"],
             ["date_to", ">=", du + " 00:00:00"],
             ["state", "in", ["draft", "confirmed", "out"]]],
            ["equipment_id", "project_id", "shooting_id", "mission_id",
             "quantity", "date_from", "date_to", "state", "holder_id"],
            limit=500):
        if b.get("equipment_id"):
            conflits.setdefault(b["equipment_id"][0], []).append(b)

    parc, indisponibles = [], []
    for e in equipements:
        fiche = {
            "id": e["id"],
            "nom": e["name"],
            "categorie": (e.get("category_id") or [None, "?"])[1],
            "marque_modele": " ".join(x for x in [e.get("brand"), e.get("model")] if x),
            "exemplaires": e.get("quantity"),
            "disponibles": e.get("quantity_available"),
            "etat": e.get("state"),
            "louable": e.get("ownership"),
            "tarif_jour_indicatif": e.get("day_rate") or 0,
            "reservations_chevauchantes": [
                {"projet": (b.get("project_id") or [None, "?"])[1],
                 "du": str(b.get("date_from"))[:16], "au": str(b.get("date_to"))[:16],
                 "etat": b.get("state"),
                 "porteur": (b.get("holder_id") or [None, "?"])[1]}
                for b in conflits.get(e["id"], [])],
        }
        (indisponibles if not e.get("is_available") else parc).append(fiche)

    kits = []
    for k in o.search_read("es.equipment.kit", [["active", "=", True]],
                           ["name", "note"], limit=50):
        lignes = o.search_read("es.equipment.kit.line", [["kit_id", "=", k["id"]]],
                               ["equipment_id", "quantity"], limit=50)
        kits.append({
            "id": k["id"], "nom": k["name"], "note": k.get("note"),
            "contenu": [{"materiel": (l.get("equipment_id") or [None, "?"])[1],
                         "equipment_id": (l.get("equipment_id") or [None])[0],
                         "qte": l.get("quantity")} for l in lignes],
        })

    print(json.dumps({
        "periode": {"du": du, "au": au},
        "proposables": len(parc),
        "hors_service": len(indisponibles),
        "kits": kits,
        "materiel": sorted(parc, key=lambda e: (e["categorie"], e["nom"])),
        "indisponibles": sorted(indisponibles, key=lambda e: (e["categorie"], e["nom"])),
        "regle_cout": "day_rate indicatif uniquement — jamais dans le coût réel ; "
                      "seule la facture fournisseur de sous-location compte.",
    }, ensure_ascii=False, indent=2, default=str))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--du", required=True, help="AAAA-MM-JJ")
    ap.add_argument("--au", required=True, help="AAAA-MM-JJ")
    ap.add_argument("--jours", type=float, default=None,
                    help="jours facturés par personne, pour le coût total")
    ap.add_argument("--produits", help="ids produits du catalogue, pour l'expérience du type")
    ap.add_argument("--materiel", action="store_true",
                    help="liste le parc es_production au lieu de proposer une équipe")
    ap.add_argument("--categorie", help="filtre catégorie matériel (ex. Son, Drone, Lumière)")
    a = ap.parse_args()

    du, au = a.du, a.au
    try:
        datetime.strptime(du, "%Y-%m-%d"), datetime.strptime(au, "%Y-%m-%d")
    except ValueError:
        ap.error("dates attendues au format AAAA-MM-JJ")
    if au < du:
        ap.error("--au est antérieur à --du")

    try:
        o = Odoo()
    except OdooError as exc:
        print(json.dumps({"ok": False, "erreur": str(exc)}, ensure_ascii=False, indent=2))
        sys.exit(2)

    if a.materiel:
        cmd_materiel(o, du, au, a.categorie)
        return

    produits = [int(x) for x in a.produits.split(",")] if a.produits else []
    ref_projets = projets_du_type(o, produits)
    nb_jours = a.jours if a.jours is not None else 1.0

    employes = o.search_read("hr.employee", [["active", "=", True]],
                             ["name", "job_title", "hourly_cost", "user_id",
                              "department_id"], limit=100)

    # Congés validés qui recoupent la période — seul l'état 'validate' bloque.
    conges = o.search_read("hr.leave",
                           [["state", "=", "validate"],
                            ["date_from", "<=", au + " 23:59:59"],
                            ["date_to", ">=", du + " 00:00:00"]],
                           ["employee_id", "date_from", "date_to", "holiday_status_id"],
                           limit=200)
    conge_par_emp: dict[int, list] = {}
    for c in conges:
        if c.get("employee_id"):
            conge_par_emp.setdefault(c["employee_id"][0], []).append(c)

    # Affectations du module maison, si installé.
    aff_par_nom: dict[str, list] = {}
    indispo_partenaires: dict[str, list] = {}
    es_dispo = o.has_model("es.crew.assignment")
    if es_dispo:
        for x in o.search_read("es.crew.assignment",
                               [["date_from", "<=", au + " 23:59:59"],
                                ["date_to", ">=", du + " 00:00:00"],
                                ["state", "in", ["proposed", "confirmed"]]],
                               ["person_name", "role_id", "project_id",
                                "date_from", "date_to", "state"], limit=300):
            aff_par_nom.setdefault(x.get("person_name") or "?", []).append(x)
    if o.has_model("es.crew.unavailability"):
        for x in o.search_read("es.crew.unavailability",
                               [["date_from", "<=", au], ["date_to", ">=", du]],
                               ["partner_id", "date_from", "date_to", "reason"], limit=200):
            if x.get("partner_id"):
                indispo_partenaires.setdefault(x["partner_id"][1], []).append(x)

    # Tâches en cours sur la période — signal de charge, même sans es_production.
    taches = o.search_read("project.task",
                           [["date_deadline", ">=", du], ["date_deadline", "<=", au]],
                           ["name", "user_ids", "project_id", "date_deadline"], limit=300)

    propositions = []
    for e in employes:
        eid, nom = e["id"], e["name"]
        alertes = []

        for c in conge_par_emp.get(eid, []):
            alertes.append(f"congé validé du {c['date_from'][:10]} au {c['date_to'][:10]}")
        for x in aff_par_nom.get(nom, []):
            alertes.append(
                f"déjà affecté ({x.get('state')}) sur "
                f"{(x.get('project_id') or [None, '?'])[1]} "
                f"du {str(x['date_from'])[:10]} au {str(x['date_to'])[:10]}")
        for x in indispo_partenaires.get(nom, []):
            alertes.append(f"indisponibilité déclarée : {x.get('reason') or 'sans motif'}")
        charge = [t["name"] for t in taches
                  if e.get("user_id") and t.get("user_ids")
                  and e["user_id"][0] in t["user_ids"]]
        if charge:
            alertes.append(f"{len(charge)} tâche(s) à échéance sur la période")

        # Expérience : jours déjà passés sur des affaires du même type.
        jours_type = 0.0
        if ref_projets:
            lignes = o.search_read(
                "account.analytic.line",
                [["employee_id", "=", eid], ["project_id", "in", ref_projets]],
                ["unit_amount"], limit=500)
            jours_type = round(sum(l.get("unit_amount") or 0 for l in lignes), 1)

        # Tenue des délais sur l'historique.
        faites = tard = 0
        if e.get("user_id"):
            for t in o.search_read(
                    "project.task",
                    [["user_ids", "in", [e["user_id"][0]]], ["date_deadline", "!=", False]],
                    ["date_deadline", "date_last_stage_update", "state"], limit=200):
                faites += 1
                fin = str(t.get("date_last_stage_update") or "")[:10]
                if fin and fin > str(t["date_deadline"])[:10]:
                    tard += 1
        ponctualite = round((faites - tard) / faites * 100) if faites else None

        cout_jour = e.get("hourly_cost") or 0
        propositions.append({
            "nom": nom,
            "poste": e.get("job_title"),
            "cout_journee": cout_jour,
            "cout_mission": round(cout_jour * nb_jours, 2),
            "jours_sur_ce_type_affaire": jours_type,
            "taches_avec_echeance": faites,
            "ponctualite_pct": ponctualite,
            "disponible": not alertes,
            "alertes": alertes,
        })

    # Disponible d'abord, puis le plus expérimenté sur ce type, puis le moins cher.
    propositions.sort(key=lambda p: (not p["disponible"],
                                     -p["jours_sur_ce_type_affaire"],
                                     p["cout_journee"] or 0))

    dispo = [p for p in propositions if p["disponible"]]
    print(json.dumps({
        "periode": {"du": du, "au": au, "jours_factures": nb_jours},
        "source_disponibilites": ("es_production + congés + tâches" if es_dispo
                                  else "congés + tâches (module es_production absent)"),
        "reference_type_affaire": (f"{len(ref_projets)} projet(s) comparables"
                                   if ref_projets else "aucune, --produits non fourni"),
        "disponibles": len(dispo),
        "cout_equipe_si_3_premiers": round(sum(p["cout_mission"] for p in dispo[:3]), 2),
        "propositions": propositions,
    }, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
