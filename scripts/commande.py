#!/usr/bin/env python3
"""Génère et exécute la cascade « j'ai une commande » à partir d'une fiche commande JSON.

Par défaut en simulation (--dry-run) : affiche le plan d'écriture complet sans rien
créer. Avec --executer : écrit réellement dans Odoo (via XML-RPC ou MCP fallback)
et affiche chaque identifiant créé.

La fiche commande est la sortie validée du temps 2 (temps 1 = questionnaire).
Voir references/workflow-commande.md pour la structure attendue.

Usage :
    python3 commande.py --fichier fiche_commande.json              # dry-run (défaut)
    python3 commande.py --fichier fiche_commande.json --executer  # écrit
    python3 commande.py --fichier fiche_commande.json --dry-run    # explicite
    python3 commande.py --exemple > fiche_commande.json            # génère un exemple

Fiche JSON minimale attendue (tous les champs illustrés dans --exemple) :
{
  "client": {"id": 42, "nom": "EXP-MOMENTUM", "rccm": "", "cc": "",
             "dossier_nas": "EXP-MOMENTUM"},
  "opportunite": {"id": null, "nom": "Festival X — 2 jours"},
  "apporteur": {"nom": null, "commission": 0},
  "cadrage": {"intention": "...", "type_affaire": "captation", "livrables": "...",
              "droits": "...", "corrections_inclus": 2, "hors_perimetre": "..."},
  "sessions": [
    {"nom": "J1 Abidjan", "date_start": "2026-11-14 08:00:00", "date_stop": "2026-11-14 18:00:00",
     "lieu": "Sofitel Abidjan", "ville": "Abidjan", "type": "tournage"}
  ],
  "missions": [
    # 1 par lieu hors Abidjan ; 0 si tout à Abidjan
    {"nom": "Mission Grand-Bassam", "ville": "Grand-Bassam",
     "date_depart": "2026-11-13", "date_retour": "2026-11-15", "logistique": {"transport": 40000, "hebergement": 60000, "restauration": 30000, "fret": 10000}}
  ],
  "responsables": {
    "charge_projet": {"user_id": 5, "nom": "Frédéric N'guessan"},
    "charges_mission": [{"mission": "Mission Grand-Bassam", "user_id": 7, "nom": "Modeste"}]
  },
  "equipe": [
    {"role": "cadreur", "role_id": 1, "titulaire": {"employee_id": 1, "partner_id": null, "day_rate": 25000, "canal": "timesheet"}, "alternative": {...}},
    {"role": "drone", "role_id": 3, "titulaire": {"partner_id": 42, "day_rate": 50000, "canal": "vendor_bill"}}
  ],
  "materiel": {
    # kits validés (réservation en un clic) + lignes d'exemplaires validées
    "kits": [{"kit_id": 1, "nom": "Kit tournage Sony A7 III"}],
    "lignes": [
      {"equipment_id": 151, "nom": "Sony FX30", "quantite": 1, "session": "J1 Abidjan",
       "date_from": "2026-11-14 08:00:00", "date_to": "2026-11-14 18:00:00",
       "porteur_user_id": 7, "note": ""},
      {"equipment_id": 143, "nom": "Drone DJI Mavic 3 Classic", "quantite": 1, "mission": "Mission Grand-Bassam",
       "date_from": "2026-11-13 08:00:00", "date_to": "2026-11-16 18:00:00",
       "porteur_user_id": 7, "note": ""}
    ]
  },
  "argent": {
    "lignes": [
      {"product_id": 107, "designation": "Captation / couverture d'événement", "qte": 2, "pu": 650000},
      {"product_id": 119, "designation": "Frais refacturés (T&E)", "qte": 1, "pu": 140000}
    ],
    "condition_paiement_id": 27,
    "taux_tva": 0,
    "cout_revient": 352840,
    "marge_pct": 65.0
  },
  "options": {"confirmer_commande": false, "creer_facture_acompte": false, "date_commande": "2026-11-14"}
}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Racine NAS par défaut : /WORKS/ (surchageable via env NAS_ROOT).
NAS_ROOT = os.environ.get("NAS_ROOT", "/WORKS")

# ------------------------------------------------------------------ exemple
EXEMPLE = {
    "client": {"id": 832, "nom": "EXP-MOMENTUM COTE D'IVOIRE", "rccm": "CI-ABJ-2020-B-12345", "cc": "1234567A", "adresse": "Abidjan Cocody"},
    "opportunite": {"id": None, "nom": "Festival des Lumières — 2 jours — Grand-Bassam", "revenu_attendu": 1340000, "probabilite": 90, "date_cloture": "2026-11-20"},
    "apporteur": {"nom": None, "commission": 0},
    "cadrage": {
        "intention": "Couverture photo/vidéo du festival pour diffusion réseaux + highlight 2 min",
        "type_affaire": "captation",
        "livrables": "300 photos retouchées + highlight 2 min (16:9 + 9:16) + 5 capsules 30s, livraison J+7",
        "droits": "Réseaux sociaux 12 mois, non exclusif",
        "corrections_inclus": 2,
        "hors_perimetre": "Habillage graphique 3D, diffusion TV",
        "contraintes_lieu": "Groupe électrogène, accès camion",
        "circuit_validation": "Mme Diallo (com) valide en 48 h",
    },
    "sessions": [
        {"nom": "J1 Grand-Bassam", "date_start": "2026-11-14 08:00:00", "date_stop": "2026-11-14 18:00:00", "lieu": "Village du festival", "ville": "Grand-Bassam", "type": "tournage"},
        {"nom": "J2 Grand-Bassam", "date_start": "2026-11-15 08:00:00", "date_stop": "2026-11-15 18:00:00", "lieu": "Village du festival", "ville": "Grand-Bassam", "type": "tournage"},
    ],
    "missions": [
        {"nom": "Mission Grand-Bassam", "ville": "Grand-Bassam", "date_depart": "2026-11-13", "date_retour": "2026-11-16", "logistique": {"transport": 40000, "hebergement": 60000, "restauration": 30000, "fret": 10000, "location": 0}},
    ],
    "responsables": {
        "charge_projet": {"user_id": 5, "nom": "Frédéric N'guessan"},
        "charges_mission": [
            {"mission": "Mission Grand-Bassam", "user_id": 7, "nom": "Modeste Ahibo"},
        ],
    },
    "equipe": [
        {"role": "cadreur", "role_id": 1, "titulaire": {"employee_id": 1, "partner_id": None, "day_rate": 25000, "canal": "timesheet", "nom": "Modeste Ahibo"}, "alternative": {"employee_id": 2, "day_rate": 20000}},
        {"role": "cadreur", "role_id": 1, "titulaire": {"employee_id": 3, "partner_id": None, "day_rate": 20000, "canal": "timesheet", "nom": "Jordan Anoh"}},
        {"role": "photographe", "role_id": 2, "titulaire": {"employee_id": 4, "partner_id": None, "day_rate": 20000, "canal": "timesheet", "nom": "Ayéhou Joël"}},
        {"role": "drone", "role_id": 3, "titulaire": {"employee_id": None, "partner_id": 42, "day_rate": 50000, "canal": "vendor_bill", "nom": "Doulaye"}},
    ],
    "materiel": {
        "kits": [{"kit_id": 1, "nom": "Kit tournage Sony A7 III"}],
        "lignes": [
            {"equipment_id": 151, "nom": "Sony FX30", "quantite": 1, "session": "J1 Grand-Bassam",
             "date_from": "2026-11-14 08:00:00", "date_to": "2026-11-14 18:00:00",
             "porteur_user_id": 7, "note": ""},
            {"equipment_id": 143, "nom": "Drone DJI Mavic 3 Classic", "quantite": 1, "session": "J2 Grand-Bassam",
             "date_from": "2026-11-15 08:00:00", "date_to": "2026-11-15 18:00:00",
             "porteur_user_id": 7, "note": ""},
        ],
    },
    "argent": {
        "lignes": [
            {"product_id": 107, "designation": "Captation / couverture d'événement", "qte": 2, "pu": 650000},
            {"product_id": 112, "designation": "Captation drone", "qte": 2, "pu": 760000},
            {"product_id": 119, "designation": "Frais refacturés (T&E)", "qte": 1, "pu": 140000},
        ],
        "condition_paiement_id": 27,
        "taux_tva": 0,
        "cout_revient": 632308,
        "notes": "Prix hors TVA (règle octobre 2026). Deux tours de correction inclus.",
    },
    "options": {"confirmer_commande": False, "creer_facture_acompte": False, "date_commande": "2026-11-14", "validite_jours": 30},
}


# ------------------------------------------------------------------ helpers

def _fcfa(v: float) -> str:
    return f"{int(round(v)):,}".replace(",", " ") + " F"


def _sanitize_dossier(nom: str) -> str:
    """Nom de dossier NAS : MAJUSCULES, espaces → _, reste [A-Z0-9_-]."""
    import re
    import unicodedata
    txt = unicodedata.normalize("NFKD", (nom or "")).encode("ascii", "ignore").decode("ascii")
    txt = re.sub(r"[\s]+", "_", txt.strip().upper())
    txt = re.sub(r"[^A-Z0-9_-]", "", txt)
    return re.sub(r"_+", "_", txt).strip("_")


def _ref_nas_depuis_commentaire(commentaire: str | None) -> str | None:
    """Référence dossier NAS lue dans les notes fiche client (ligne 'NAS: X' ou 'Dossier NAS: X')."""
    import re
    for ligne in (commentaire or "").splitlines():
        m = re.match(r"\s*(?:dossier\s+)?nas\s*:\s*(.+?)\s*$", ligne, re.IGNORECASE)
        if m and m.group(1):
            return m.group(1)
    return None


def _dossier_nas_fiche(d: dict, commentaire_partenaire: str | None = None) -> tuple[str | None, str]:
    """Résout le dossier client NAS : fiche d'abord, notes client ensuite.

    Retourne (ref, origine) avec origine = 'fiche' | 'notes client' | 'non résolu'.
    """
    ref = (d.get("client") or {}).get("dossier_nas")
    if ref:
        return ref, "fiche"
    ref = _ref_nas_depuis_commentaire(commentaire_partenaire)
    if ref:
        return ref, "notes client"
    return None, "non résolu — demander le nom de dossier à Lycris"


def _total_ht(lignes) -> float:
    return sum(l["qte"] * l["pu"] for l in lignes)


def _marge(vendu, cout):
    if not vendu:
        return None
    return round((vendu - cout) / vendu * 100, 1)


CONDITIONS_ACOMPTE = {27: 0.70, 36: 0.50, 34: 1.0}
CONDITIONS_SANS_ACOMPTE = {1, 4, 29, 35, 37}


def _validate_fiche(d: dict) -> tuple[list[str], list[str]]:
    errs: list[str] = []
    warns: list[str] = []
    client = d.get("client") or {}
    if not d.get("client") or not d["client"].get("nom"):
        errs.append("client.nom manquant")
    # Dossier NAS : si fixé dans la fiche, il doit être un nom de dossier valide
    import re as _re
    if client.get("dossier_nas") and not _re.fullmatch(r"[A-Za-z0-9 _-]+", client["dossier_nas"]):
        errs.append(f"client.dossier_nas '{client['dossier_nas']}' invalide — proposer "
                    f"'{_sanitize_dossier(client['dossier_nas'])}' (lettres, chiffres, espace, _ et -)")
    # Responsables obligatoires
    resp = d.get("responsables") or {}
    if not resp.get("charge_projet") or not resp["charge_projet"].get("user_id"):
        errs.append("responsables.charge_projet.user_id manquant — la fiche n'est pas validable sans chargé de projet (fields_get: project.project.user_id)")
    missions = d.get("missions") or []
    charges_mission = (resp.get("charges_mission") or [])
    cm_par_mission = {x.get("mission"): x for x in charges_mission}
    for m in missions:
        nom = m.get("nom") or m.get("ville") or "?"
        if nom not in cm_par_mission or not cm_par_mission[nom].get("user_id"):
            errs.append(f"missions: chargé de mission manquant pour '{nom}' — 1 par mission hors Abidjan (fields_get sur es.mission)")
    # Argents
    argent = d.get("argent") or {}
    if not argent.get("lignes"):
        errs.append("argent.lignes vide")
    for l in argent.get("lignes") or []:
        if not l.get("product_id"):
            errs.append(f"ligne sans product_id: {l.get('designation')}")
        if l.get("product_id") in (114, 115, 118) and l.get("pu", 0) <= 1:
            errs.append(f"produit {l['product_id']} à 1 F — prix à fixer avec Lycris, ne pas laisser 1 F")
    # TVA
    date_cmd = (d.get("options") or {}).get("date_commande") or ""
    tva = argent.get("taux_tva")
    if date_cmd >= "2026-10-01" and tva not in (0, 0.0, None, ""):
        errs.append(f"TVA {tva} sur commande du {date_cmd} : règle octobre 2026 = 0 TVA — corriger taux_tva à 0")
    # RCCM/CC — avertissement, ne bloque pas le devis
    if client.get("id") and (not client.get("rccm") or not client.get("cc")):
        warns.append(f"fiche client incomplète : RCCM/CC manquants (rccm='{client.get('rccm')}', cc='{client.get('cc')}') — bloque facture et FNE, à réclamer avant facturation (ne bloque pas le devis)")
    # Marge — avertissement
    lignes = argent.get("lignes") or []
    vendu_tmp = _total_ht(lignes)
    cout_tmp = argent.get("cout_revient") or 0
    marge_tmp = argent.get("marge_pct") if argent.get("marge_pct") is not None else _marge(vendu_tmp, cout_tmp)
    if marge_tmp is not None and marge_tmp < 60:
        warns.append(f"marge {marge_tmp}% < 60% — signaler et proposer : moins de jours, équipe plus légère, locaux, prestation sortie du forfait, ou prix plus haut (seuil 65% visé)")
    elif marge_tmp is not None and marge_tmp < 65:
        warns.append(f"marge {marge_tmp}% < 65% (mais ≥60%) — acceptable, le mentionner en une ligne")
    # Sessions
    if not d.get("sessions"):
        errs.append("sessions vide — au moins 1 session requise")
    # Matériel — lignes d'exemplaires validées (écriture es.equipment.booking au temps 3)
    materiel = d.get("materiel") or {}
    for ml in materiel.get("lignes") or []:
        if not ml.get("equipment_id"):
            errs.append(f"matériel '{ml.get('nom') or '?'}' sans equipment_id — "
                        "lister via equipe.py --materiel, jamais deviner l'id")
        if (ml.get("quantite") or 0) <= 0:
            errs.append(f"matériel '{ml.get('nom') or ml.get('equipment_id')}' : "
                        "quantité ≤ 0 — 1 minimum (à l'unité), N pour le quantitatif")
        for champ in ("date_from", "date_to"):
            if not ml.get(champ):
                errs.append(f"matériel '{ml.get('nom') or ml.get('equipment_id')}' sans {champ} "
                            "— fenêtre obligatoire (conflits calculés dessus)")
        try:
            if ml.get("date_from") and ml.get("date_to"):
                a = datetime.strptime(ml["date_from"], "%Y-%m-%d %H:%M:%S")
                b = datetime.strptime(ml["date_to"], "%Y-%m-%d %H:%M:%S")
                if b <= a:
                    errs.append(f"matériel '{ml.get('nom') or ml.get('equipment_id')}' : date_to <= date_from")
        except ValueError:
            errs.append(f"matériel '{ml.get('nom') or ml.get('equipment_id')}' : format date attendu AAAA-MM-JJ HH:MM:SS")
        if not ml.get("porteur_user_id"):
            warns.append(f"matériel '{ml.get('nom') or ml.get('equipment_id')}' sans porteur — "
                         "holder_id (qui répond de l'unité) à désigner, chargé de mission par défaut")
    for k in materiel.get("kits") or []:
        if not k.get("kit_id"):
            errs.append(f"kit '{k.get('nom') or '?'}' sans kit_id — lister via equipe.py --materiel")
    for s in d.get("sessions") or []:
        if not s.get("date_start") or not s.get("date_stop"):
            errs.append(f"session '{s.get('nom')}' sans date_start/stop")
        try:
            if s.get("date_start") and s.get("date_stop"):
                a = datetime.strptime(s["date_start"], "%Y-%m-%d %H:%M:%S")
                b = datetime.strptime(s["date_stop"], "%Y-%m-%d %H:%M:%S")
                if b <= a:
                    errs.append(f"session '{s.get('nom')}' : date_stop <= date_start")
        except ValueError:
            errs.append(f"session '{s.get('nom')}' : format date attendu AAAA-MM-JJ HH:MM:SS")
    return errs, warns


def _plan(d: dict) -> dict:
    """Construit le plan d'écriture (liste ordonnée d'opérations)."""
    client = d.get("client") or {}
    opport = d.get("opportunite") or {}
    missions = d.get("missions") or []
    sessions = d.get("sessions") or []
    responsables = d.get("responsables") or {}
    equipe = d.get("equipe") or []
    argent = d.get("argent") or {}
    options = d.get("options") or {}

    lignes = argent.get("lignes") or []
    vendu = _total_ht(lignes)
    cout = argent.get("cout_revient") or 0
    marge = argent.get("marge_pct") if argent.get("marge_pct") is not None else _marge(vendu, cout)
    cond = argent.get("condition_paiement_id")
    taux_acompte = CONDITIONS_ACOMPTE.get(cond)
    sans_acompte = cond in CONDITIONS_SANS_ACOMPTE or cond is None

    # Déclencheur projet (Phase C)
    if taux_acompte:
        declencheur = f"encaissement {int(taux_acompte*100)} % (condition {cond})"
    elif sans_acompte:
        declencheur = "accord écrit seul (sans acompte) — signaler que les dates sont bloquées sans avance"
    else:
        declencheur = f"condition {cond} — vérifier déclencheur"

    # TVA
    date_cmd = options.get("date_commande") or ""
    tva = argent.get("taux_tva", 0) or 0
    tva_note = "0 % (règle octobre 2026, date ≥ 01/10/2026)" if date_cmd >= "2026-10-01" else f"{tva} %"

    errs, warns = _validate_fiche(d)

    ops = []
    seq = 1

    # 1 — Opportunité CRM
    ops.append({
        "ordre": seq, "etape": "01 — CRM",
        "modele": "crm.lead", "action": "create_or_write",
        "details": {
            "opportunite_existante_id": opport.get("id"),
            "partner_id": client.get("id"),
            "nom": opport.get("nom") or f"{client.get('nom')} — {d.get('cadrage',{}).get('type_affaire','affaire')}",
            "revenu_attendu": opport.get("revenu_attendu") or vendu,
            "probabilite": opport.get("probabilite") or 90,
            "date_cloture": opport.get("date_cloture") or date_cmd,
            "stage": "Gagnée",
            "note": "Passée à Gagnée lors de la cascade (ou créée si elle n'existe pas). Seule saisie client ; es_finance lira l'opportunité.",
        },
        "garde_fou": "Ne jamais créer de res.partner en silence si client inconnu — proposer la création.",
    })
    seq += 1

    # 2 — Devis
    ops.append({
        "ordre": seq, "etape": "02 — Devis",
        "modele": "sale.order", "action": "create (draft)",
        "details": {
            "partner_id": client.get("id"),
            "opportunity_id": "← id de l'opportunité ci-dessus",
            "date_order": date_cmd,
            "payment_term_id": cond,
            "tva": tva_note,
            "lignes": [{"product_id": l["product_id"], "name": l["designation"], "product_uom_qty": l["qte"], "price_unit": l["pu"], "tax_ids": [] if float(tva or 0) == 0 else "18%"} for l in lignes],
            "total_ht": vendu,
            "cout_revient": cout,
            "marge": f"{_fcfa(vendu - cout)} — {marge}%" if marge is not None else f"{_fcfa(vendu - cout)}",
            "notes": argent.get("notes") or "",
        },
        "garde_fou": "Forfait et T&E sur deux lignes 706100 distinctes. Taxe vide si ≥ 01/10/2026.",
    })
    seq += 1

    # 3 — Confirmation
    ops.append({
        "ordre": seq, "etape": "03-05 — Confirmation",
        "modele": "sale.order", "action": "action_confirm" if options.get("confirmer_commande") else "action_confirm (seulement si explicitement validé au temps 2, sinon reste en brouillon)",
        "details": {
            "effet": "crée project.project + 1 project.task par ligne (sale_project)",
            "a_verifier": [
                "project.project.account_id présent (pas analytic_account_id en v18)",
                "project_id de CHAQUE sale.order.line renseigné (piège projet fantôme '… - MODÈLE — …' MAGGI)",
                "aucun projet recréé à la main",
            ],
            "declencheur_ouverture": declencheur,
        },
        "garde_fou": "Effet comptable — seulement si inclus dans la validation temps 2, sinon BROUILLON.",
    })
    seq += 1

    # 4 — Facture acompte
    if taux_acompte:
        montant_acompte = round(vendu * taux_acompte)
        ops.append({
            "ordre": seq, "etape": "04 — Facture d'acompte",
            "modele": "account.move (out_invoice)", "action": "create (draft) — depuis la même sale.order",
            "details": {
                "montant_acompte": montant_acompte,
                "condition": f"{int(taux_acompte*100)}% à la commande (id {cond})",
                "etat": "brouillon — ne jamais action_post sans validation explicite",
                "rappel": "Acomptes déjà encaissés en paiements non affectés, à lettrer sur la facture.",
                "tva": tva_note,
            },
            "garde_fou": "Cas limite TVA : montrer l'écart si acompte avec TVA / solde sans, laisser arbitrer.",
        })
    else:
        ops.append({
            "ordre": seq, "etape": "04 — Facture d'acompte",
            "modele": "account.move", "action": "aucune — condition sans acompte",
            "details": {"condition": cond, "note": "Aucune facture d'acompte (condition sans acompte). Facturation au solde depuis la même commande."},
            "garde_fou": "Ne pas bloquer l'ouverture en attendant un encaissement qui ne viendra jamais ; signaler le risque trésorerie.",
        })
    seq += 1

    # 5 — es.deal + budget es_finance
    ops.append({
        "ordre": seq, "etape": "05 — Affaire & budget",
        "modele": "es.deal + es_finance (Objectifs et budgets)", "action": "create/write",
        "details": {
            "es.deal": "journal d'étapes à jour ; is_closed = solde encaissé + FNE émise",
            "budget": f"budget = coût de revient validé = {_fcfa(cout)}",
            "fiche_A_venir": "convertie si elle existait (pas de double comptage trésorerie)",
            "ouverture_projet": "bouton 'Ouvrir le projet' seulement quand le déclencheur est atteint",
        },
        "garde_fou": "Ne jamais créer es.finance.pipeline pour une affaire client — es_finance lit le CRM.",
    })
    seq += 1

    # 6 — Production : sessions/missions/affectations/tâches
    for idx, s in enumerate(sessions, start=1):
        ops.append({
            "ordre": seq, "etape": f"07 — Session {idx}",
            "modele": "es.shooting", "action": "create",
            "details": {
                "nom": s.get("nom"),
                "project_id": "← id du projet créé",
                "type": s.get("type") or "tournage",
                "date_start/stop": f"{s.get('date_start')} → {s.get('date_stop')}",
                "lieu": f"{s.get('lieu')} — {s.get('ville')}",
                "analytic_distribution": "← project_id.account_id (100%)",
            },
        })
        seq += 1

    for m in missions:
        ops.append({
            "ordre": seq, "etape": "07 — Mission",
            "modele": "es.mission", "action": "create",
            "details": {
                "nom": m.get("nom"),
                "project_id": "← id du projet",
                "ville": m.get("ville"),
                "dates": f"départ {m.get('date_depart')} → retour {m.get('date_retour')}",
                "logistique_previsionnelle": m.get("logistique") or {},
                "note": "1 mission par lieu hors Abidjan (tournée 4 villes = 4 missions)",
            },
        })
        seq += 1

    for a in equipe:
        tit = a.get("titulaire") or {}
        ops.append({
            "ordre": seq, "etape": "08-09 — Affectation",
            "modele": "es.crew.assignment", "action": "create",
            "details": {
                "role": a.get("role"),
                "role_id": a.get("role_id"),
                "shooting_id": "← session concernée",
                "personne": tit.get("nom") or tit.get("employee_id") or tit.get("partner_id"),
                "employee_id / partner_id": f"{tit.get('employee_id')} / {tit.get('partner_id')}",
                "quantity": 1,
                "day_rate": tit.get("day_rate"),
                "day_rate_is_override": True,
                "canal": tit.get("canal"),
                "quantity_note": "quantity = 1 par jour de cachet, day_rate forcé avec day_rate_is_override tant que défaut ×8 non corrigé",
            },
            "garde_fou": "Vérifier es.crew.ledger avant de rebooker ; signaler les conflits (congés validate, affectations qui chevauchent) sans bloquer.",
        })
        seq += 1

    # Réservations matériel (es.equipment.booking, brouillon) — selon le validé temps 2
    materiel = d.get("materiel") or {}
    for ml in materiel.get("lignes") or []:
        ops.append({
            "ordre": seq, "etape": "08-09 — Réservation matériel",
            "modele": "es.equipment.booking", "action": "create (draft)",
            "details": {
                "equipment_id": ml.get("equipment_id"),
                "nom": ml.get("nom"),
                "quantite": ml.get("quantite") or 1,
                "fenetre": f"{ml.get('date_from')} → {ml.get('date_to')}",
                "session": ml.get("session") or "← première session",
                "mission": ml.get("mission") or "",
                "porteur_user_id": ml.get("porteur_user_id") or "← chargé de mission",
                "note": ml.get("note") or "",
            },
            "garde_fou": "Créée en brouillon ; vérifier conflict_warning après création, "
                         "signaler sans bloquer. day_rate indicatif jamais compté en coût réel.",
        })
        seq += 1
    for k in materiel.get("kits") or []:
        ops.append({
            "ordre": seq, "etape": "08-09 — Kit matériel",
            "modele": "es.equipment.booking (× lignes du kit)", "action": "create (draft, 1 par ligne du kit)",
            "details": {
                "kit_id": k.get("kit_id"),
                "nom": k.get("nom"),
                "note": "Un kit est un raccourci de saisie : 1 réservation brouillon par ligne de contenu, "
                        "sur la fenêtre validée.",
            },
            "garde_fou": "Le kit n'est jamais réservé lui-même ; vérifier chaque ligne (état, conflits).",
        })
        seq += 1

    # Tâches par étape + satellites
    ops.append({
        "ordre": seq, "etape": "07 — Tâches",
        "modele": "project.task", "action": "create (si non déjà créées par sale_project)",
        "details": {
            "etapes": "Pré-production → Production → Post-production → Validation client → Livré",
            "par_session": "4 tâches satellites : J−2 préparation/convocation, J captation, J+1 dérushage/sauvegarde, J+2 intégration",
            "sessions_concernees": len(sessions),
            "total_taches_satellites": len(sessions) * 4,
        },
    })
    seq += 1

    # 7 — Responsables
    cp = responsables.get("charge_projet") or {}
    ops.append({
        "ordre": seq, "etape": "08 — Responsables",
        "modele": "project.project + es.deal + es.mission", "action": "write",
        "details": {
            "charge_projet": f"{cp.get('nom')} (user_id {cp.get('user_id')}) → project.project.user_id + es.deal (fields_get avant écriture)",
            "charges_mission": [f"{x.get('nom')} → mission '{x.get('mission')}' (fields_get sur es.mission)" for x in responsables.get("charges_mission") or []],
            "contrainte": "Toujours un chargé de projet ; 1 par mission si déplacement. Fiche non validable sans eux.",
        },
        "garde_fou": "Lire fields_get pour es.deal / es.mission avant d'écrire ; si pas de res.users, proposer ouverture d'accès ou utilisateur existant — ne crée AUCUN compte seul. Rappel : chargé de projet ne voit pas la marge.",
    })
    seq += 1

    # NAS — arborescence /WORKS (créée au temps 3 : création client ou commande validée)
    ref_nas, origine_nas = _dossier_nas_fiche(d)
    annee_nas = (date_cmd or datetime.now().strftime("%Y-%m-%d"))[:4]
    dossier_projet_nas = _sanitize_dossier(opport.get("nom") or d.get("cadrage", {}).get("type_affaire") or "PROJET")
    ops.append({
        "ordre": seq, "etape": "NAS — Arborescence /WORKS",
        "modele": "dossier NAS", "action": "mkdir -p (via scaffold.init_projet)",
        "details": {
            "racine": NAS_ROOT,
            "dossier_client": ref_nas or "← À DEMANDER à Lycris (ni fiche ni notes client)",
            "origine_dossier": origine_nas,
            "chemin": f"{NAS_ROOT}/{ref_nas or '?CLIENT?'}/{annee_nas}/{dossier_projet_nas}/"
                      "01_creation … 05_rendus",
            "regle": "Si la réf n'existe pas dans les notes fiche client, demander le nom "
                     "de dossier à Lycris ; si elle existe, s'en servir pour créer le reste.",
        },
        "garde_fou": "Création de dossiers seulement — aucun fichier déplacé ni supprimé.",
    })
    seq += 1

    # 8 — Feuilles de service + activités
    ops.append({
        "ordre": seq, "etape": "09 — Feuilles de service & rappels",
        "modele": "report (PDF) + mail.activity", "action": "générer + créer activités",
        "details": {
            "feuilles_de_service": f"{len(sessions)} feuille(s) — lieu, heure convocation, matériel, contact, déroulé — lisibles sur téléphone",
            "activites": ["relance acompte", "confirmation prestataires", "J−2 préparation", "livraison", "solde", "FNE"],
            "canal": "Broullon de message prêt à copier — jamais envoyé par le skill",
        },
        "garde_fou": "Aucun envoi client automatique.",
    })

    return {
        "resume": {
            "client": f"{client.get('nom')} (id {client.get('id')})",
            "affaire": opport.get("nom") or d.get("cadrage", {}).get("type_affaire"),
            "sessions": len(sessions),
            "missions": len(missions),
            "equipe_affectations": len(equipe),
            "dossier_nas": f"{NAS_ROOT}/{ref_nas or '?CLIENT?'}/{annee_nas}/{dossier_projet_nas}/"
                           f" (réf : {origine_nas})",
            "materiel_reservations": len((d.get("materiel") or {}).get("lignes") or []),
            "materiel_kits": len((d.get("materiel") or {}).get("kits") or []),
            "total_vendu_ht": vendu,
            "cout_revient": cout,
            "marge": f"{_fcfa(vendu - cout)} — {marge}%" if marge is not None else _fcfa(vendu - cout),
            "condition_paiement": cond,
            "tva": tva_note,
            "declencheur_ouverture": declencheur,
        },
        "validations": errs,
        "avertissements": warns,
        "operations": ops,
        "gardes_fous": [
            "Ne jamais action_confirm / action_post sans qu'ils aient été explicitement inclus dans la validation temps 2.",
            "Ne jamais envoyer quoi que ce soit à un client.",
            "Ne jamais inventer un chiffre — si Odoo injoignable, le dire.",
            "Toujours {'lang':'fr_FR'} en contexte.",
            "Marge invisible à l'équipe (feuille de service, tâches, fils).",
            "TVA : signaler le cas acompte avec TVA / solde sans, ne jamais corriger seul.",
        ],
    }


def _executer(d: dict, plan: dict):
    """Exécute réellement les écritures. Retourne la liste des (modèle, id) créés."""
    try:
        from odoo import Odoo, OdooError
    except ImportError:
        # fallback : odoo.py est dans le même dossier
        import importlib.util
        spec = importlib.util.spec_from_file_location("odoo", str(Path(__file__).parent / "odoo.py"))
        odoo_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(odoo_mod)
        Odoo = odoo_mod.Odoo
        OdooError = odoo_mod.OdooError

    try:
        o = Odoo()
    except Exception as exc:
        print(json.dumps({"ok": False, "erreur": f"Connexion Odoo impossible: {exc}", "plan": plan}, ensure_ascii=False, indent=2))
        sys.exit(2)

    crees = []

    def _log(modele, oid, note=""):
        crees.append({"modele": modele, "id": oid, "note": note})
        print(f"  ✓ {modele}  id={oid}  {note}")

    client = d.get("client") or {}
    opport = d.get("opportunite") or {}
    missions = d.get("missions") or []
    sessions = d.get("sessions") or []
    equipe = d.get("equipe") or []
    argent = d.get("argent") or {}
    options = d.get("options") or {}
    lignes = argent.get("lignes") or []
    date_cmd = options.get("date_commande") or datetime.now().strftime("%Y-%m-%d")
    cond = argent.get("condition_paiement_id")
    tva = argent.get("taux_tva", 0) or 0

    # Pré-check : modèles maison présents ?
    has_shooting = o.has_model("es.shooting")
    has_mission = o.has_model("es.mission")
    has_assignment = o.has_model("es.crew.assignment")
    has_booking = o.has_model("es.equipment.booking")
    has_deal = o.has_model("es.deal")

    # 1 — Opportunité
    opp_id = opport.get("id")
    if opp_id:
        opp = o.search_read("crm.lead", [["id", "=", int(opp_id)]], ["id", "stage_id"], limit=1)
        if opp:
            # passer en Gagnée : trouver le stage Gagné
            stages = o.search_read("crm.stage", [["is_won", "=", True]], ["id", "name"], limit=1)
            won_id = stages[0]["id"] if stages else opp[0].get("stage_id", [None])[0]
            if won_id:
                o.kw("crm.lead", "write", [[opp_id], {"stage_id": won_id}])
                _log("crm.lead (update stage → Gagnée)", opp_id)
            else:
                _log("crm.lead (déjà existante, stage Gagnée non trouvé)", opp_id, "— vérifier les étapes CRM")
        else:
            opp_id = None

    if not opp_id:
        vals = {
            "name": opport.get("nom") or f"{client.get('nom')} — {d.get('cadrage',{}).get('type_affaire','affaire')}",
            "partner_id": int(client["id"]) if client.get("id") else False,
            "expected_revenue": opport.get("revenu_attendu") or _total_ht(lignes),
            "probability": opport.get("probabilite") or 90,
            "date_deadline": opport.get("date_cloture") or date_cmd,
            "type": "opportunity",
        }
        # retirer les False pour ne pas écraser
        vals = {k: v for k, v in vals.items() if v is not False and v is not None}
        opp_id = o.kw("crm.lead", "create", [vals])
        _log("crm.lead (create)", opp_id, f"→ opportunity {vals['name']}")
        # tenter de passer en Gagnée directement
        stages = o.search_read("crm.stage", [["is_won", "=", True]], ["id"], limit=1)
        if stages:
            o.kw("crm.lead", "write", [[opp_id], {"stage_id": stages[0]["id"]}])
            print(f"    → passée en Gagnée (stage {stages[0]['id']})")

    # 2 — Devis
    # Résoudre tax_ids : si TVA 0, vide ; sinon chercher 18%
    tax_ids = []
    if float(tva or 0) != 0:
        taxes = o.search_read("account.tax", [["amount", "=", float(tva)], ["type_tax_use", "=", "sale"]], ["id"], limit=1)
        if taxes:
            tax_ids = [(6, 0, [taxes[0]["id"]])]
    else:
        tax_ids = [(6, 0, [])]

    order_lines = []
    for l in lignes:
        order_lines.append((0, 0, {
            "product_id": int(l["product_id"]),
            "name": l.get("designation") or l.get("name") or "",
            "product_uom_qty": float(l["qte"]),
            "price_unit": float(l["pu"]),
            "tax_id": tax_ids,
        }))

    so_vals = {
        "partner_id": int(client["id"]) if client.get("id") else False,
        "opportunity_id": int(opp_id) if opp_id else False,
        "date_order": date_cmd,
        "payment_term_id": int(cond) if cond else False,
        "order_line": order_lines,
        "note": argent.get("notes") or "",
    }
    so_vals = {k: v for k, v in so_vals.items() if v is not False and v is not None}
    so_id = o.kw("sale.order", "create", [so_vals])
    _log("sale.order (create draft)", so_id, f"total HT {_fcfa(_total_ht(lignes))} — TVA {tva}%")
    so_name = o.search_read("sale.order", [["id", "=", so_id]], ["name"], limit=1)
    print(f"    → {so_name[0]['name'] if so_name else so_id}")

    # 3 — Confirmation (seulement si demandé)
    project_id = None
    if options.get("confirmer_commande"):
        o.kw("sale.order", "action_confirm", [[so_id]])
        _log("sale.order (action_confirm)", so_id)
        # retrouver le projet
        so = o.search_read("sale.order", [["id", "=", so_id]], ["project_ids"], limit=1)
        pids = so[0].get("project_ids") if so and so[0].get("project_ids") else []
        if pids:
            project_id = pids[0]
            _log("project.project (créé par sale_project)", project_id)
            # vérifs
            proj = o.search_read("project.project", [["id", "=", project_id]], ["name", "account_id", "sale_order_id"], limit=1)
            if proj:
                print(f"    → projet: {proj[0]['name']}  account_id={proj[0].get('account_id')}  sale_order_id={proj[0].get('sale_order_id')}")
                if not proj[0].get("account_id"):
                    print("    ⚠  projet sans account_id — à corriger")
            # vérifier project_id de chaque ligne
            sols = o.search_read("sale.order.line", [["order_id", "=", so_id]], ["id", "product_id", "project_id"])
            for sl in sols:
                if not sl.get("project_id"):
                    print(f"    ⚠  sale.order.line {sl['id']} ({sl.get('product_id')}) sans project_id — piège MAGGI !")
        else:
            print("    ⚠  aucun project_ids après confirmation — sale_project n'a pas créé de projet")
    else:
        print("  ○ sale.order reste en brouillon (confirmer_commande = false → pas d'action_confirm)")

    # Si non confirmé, essayer quand même de créer le projet pour la suite ? Non — on signale
    if not project_id:
        # créer un projet fantôme ? Non — on laisse en attente
        print("  ○ sessions/missions/assignements non créés car pas de project_id (commande en brouillon)")
        print("    → relancer avec --executer et confirmer_commande=true une fois l'acompte encaissé ou l'accord écrit obtenu")
        # On continue quand même si es.shooting peut exister sans projet ? Non, project_id requis.
        # On propose de créer en brouillon pour prévisualiser
        pass

    # 4 — Facture acompte (seulement si avec acompte et demandé)
    cond_acompte = CONDITIONS_ACOMPTE.get(cond)
    if cond_acompte and options.get("creer_facture_acompte"):
        # créer une facture d'acompte en brouillon depuis la commande : méthode Odoo sale.advance
        # Simplification : créer une out_invoice avec une ligne d'acompte
        acompte_montant = round(_total_ht(lignes) * cond_acompte)
        inv_vals = {
            "move_type": "out_invoice",
            "partner_id": int(client["id"]) if client.get("id") else False,
            "invoice_origin": so_name[0]["name"] if so_name else "",
            "invoice_line_ids": [(0, 0, {
                "name": f"Acompte {int(cond_acompte*100)}% — {opport.get('nom') or 'commande'}",
                "quantity": 1,
                "price_unit": float(acompte_montant),
                "tax_ids": tax_ids,
            })],
        }
        if project_id:
            # analytique si possible
            proj = o.search_read("project.project", [["id", "=", project_id]], ["account_id"], limit=1)
            if proj and proj[0].get("account_id"):
                acc = proj[0]["account_id"][0]
                inv_vals["invoice_line_ids"][0][2]["analytic_distribution"] = {str(acc): 100}
        inv_id = o.kw("account.move", "create", [inv_vals])
        _log("account.move (out_invoice draft — acompte)", inv_id, f"{_fcfa(acompte_montant)}")
    elif cond_acompte:
        print(f"  ○ facture d'acompte non créée (creer_facture_acompte = false) — {int(cond_acompte*100)}% = {_fcfa(_total_ht(lignes)*cond_acompte)} en attente d'encaissement")
    else:
        print(f"  ○ pas de facture d'acompte (condition {cond} sans acompte)")

    # 5 — es.deal
    if has_deal and project_id:
        deal_vals = {
            "name": opport.get("nom") or d.get("cadrage", {}).get("type_affaire") or "Affaire",
            "project_id": int(project_id),
            "partner_id": int(client["id"]) if client.get("id") else False,
        }
        # fields_get pour responsable
        try:
            fields = o.kw("es.deal", "fields_get", [], {"attributes": ["string", "type"]})
            # chercher un champ user/responsable
            possible = [k for k in fields if "user" in k.lower() or "respons" in k.lower()]
            if possible:
                deal_vals[possible[0]] = int(responsables.get("charge_projet", {}).get("user_id")) if responsables.get("charge_projet", {}).get("user_id") else False
                print(f"    → champ responsable es.deal détecté: {possible[0]}")
        except Exception:
            pass
        try:
            deal_id = o.kw("es.deal", "create", [deal_vals])
            _log("es.deal", deal_id)
        except Exception as e:
            print(f"    ⚠  es.deal non créé: {e}")
    elif has_deal:
        print("  ○ es.deal non créé (pas de project_id)")

    # budget es_finance
    if project_id:
        # es_finance : chercher le modèle de budget
        for model in ["es.finance.budget", "es.finance.objective", "project.budget"]:
            if o.has_model(model):
                try:
                    b_id = o.kw(model, "create", [{"project_id": int(project_id), "amount": float(d.get("argent", {}).get("cout_revient") or 0), "name": "Budget prévisionnel"}])
                    _log(model, b_id, f"budget = {_fcfa(d.get('argent', {}).get('cout_revient') or 0)}")
                    break
                except Exception as e:
                    print(f"    ○ budget {model} non créé: {e}")
                break

    # 6 — Sessions / Missions / Affectations (si project_id)
    if project_id and has_shooting:
        # fields_get pour responsable session si besoin
        shooting_ids = []
        for s in sessions:
            vals = {
                "project_id": int(project_id),
                "name": s.get("nom") or s.get("lieu") or "Session",
                "date_start": s.get("date_start"),
                "date_stop": s.get("date_stop"),
                "location_name": s.get("lieu") or "",
                "location_city": s.get("ville") or "",
                "shooting_type": s.get("type") or "tournage",
            }
            try:
                sid = o.kw("es.shooting", "create", [vals])
                shooting_ids.append(sid)
                _log("es.shooting", sid, f"{vals['name']} {vals['date_start']}→{vals['date_stop']}")
            except Exception as e:
                print(f"    ⚠  es.shooting '{vals['name']}' non créé: {e}")

        if has_mission and missions:
            mission_ids = []
            for m in missions:
                vals = {
                    "project_id": int(project_id),
                    "name": m.get("nom") or m.get("ville"),
                    "city": m.get("ville") or "",
                    "date_from": m.get("date_depart") or datetime.now().strftime("%Y-%m-%d"),
                    "date_to": m.get("date_retour") or datetime.now().strftime("%Y-%m-%d"),
                }
                # charger le champ responsable réel
                try:
                    fg = o.kw("es.mission", "fields_get", [], {"attributes": ["string", "type"]})
                    # proposer le chargé de mission
                    for cm in responsables.get("charges_mission") or []:
                        if cm.get("mission") == m.get("nom") or cm.get("mission") == m.get("ville"):
                            for cand in [k for k in fg if "user" in k.lower() or "respons" in k.lower() or "manager" in k.lower()]:
                                vals[cand] = int(cm["user_id"])
                                print(f"    → champ responsable es.mission détecté: {cand} = {cm['user_id']}")
                                break
                            break
                except Exception:
                    pass
                try:
                    mid = o.kw("es.mission", "create", [vals])
                    mission_ids.append(mid)
                    _log("es.mission", mid, f"{vals['name']} {vals['city']}")
                except Exception as e:
                    print(f"    ⚠  es.mission '{vals['name']}' non créée: {e}")

        if has_assignment and equipe and shooting_ids:
            for a in equipe:
                tit = a.get("titulaire") or {}
                # affecter sur la première session par défaut ; affiner si besoin
                vals = {
                    "shooting_id": int(shooting_ids[0]),
                    "role_id": int(a["role_id"]) if a.get("role_id") else False,
                    "employee_id": int(tit["employee_id"]) if tit.get("employee_id") else False,
                    "partner_id": int(tit["partner_id"]) if tit.get("partner_id") else False,
                    "quantity": 1,
                    "day_rate": float(tit.get("day_rate") or 0),
                    "day_rate_is_override": True,
                }
                # nettoyer les False
                vals = {k: v for k, v in vals.items() if v is not False and v is not None and v != 0 or k in ("day_rate", "day_rate_is_override", "quantity")}
                if not vals.get("employee_id"):
                    vals.pop("employee_id", None)
                if not vals.get("partner_id"):
                    vals.pop("partner_id", None)
                if not vals.get("role_id"):
                    vals.pop("role_id", None)
                try:
                    aid = o.kw("es.crew.assignment", "create", [vals])
                    _log("es.crew.assignment", aid, f"{a.get('role')} — {tit.get('nom')} — {_fcfa(tit.get('day_rate') or 0)}/j ×1 — {tit.get('canal')}")
                except Exception as e:
                    print(f"    ⚠  affectation {a.get('role')} / {tit.get('nom')} non créée: {e}")

        # Réservations matériel validées (brouillon) — 1 booking par ligne + lignes des kits
        materiel = d.get("materiel") or {}
        if has_booking:
            idx_session = {s.get("nom"): sid for s, sid in zip(sessions, shooting_ids)}
            idx_mission = {m.get("nom"): mid for m, mid in zip(missions, mission_ids)} if has_mission and missions else {}
            lignes_materiel = list(materiel.get("lignes") or [])
            for k in materiel.get("kits") or []:
                try:
                    contenu = o.search_read("es.equipment.kit.line", [["kit_id", "=", int(k["kit_id"])]],
                                            ["equipment_id", "quantity"], limit=50)
                    for cl in contenu:
                        eid = (cl.get("equipment_id") or [None])[0]
                        if eid:
                            lignes_materiel.append({
                                "equipment_id": eid,
                                "nom": (cl.get("equipment_id") or [None, "?"])[1],
                                "quantite": cl.get("quantity") or 1,
                                "date_from": (sessions[0].get("date_start") if sessions else None),
                                "date_to": (sessions[-1].get("date_stop") if sessions else None),
                                "porteur_user_id": (responsables.get("charges_mission") or [{}])[0].get("user_id"),
                                "note": f"issu du kit {k.get('nom')}",
                            })
                except Exception as e:
                    print(f"    ⚠  kit {k.get('nom')} non déplié: {e}")
            for ml in lignes_materiel:
                vals = {
                    "equipment_id": int(ml["equipment_id"]),
                    "project_id": int(project_id),
                    "quantity": int(ml.get("quantite") or 1),
                    "date_from": ml.get("date_from"),
                    "date_to": ml.get("date_to"),
                    "state": "draft",
                    "note": ml.get("note") or "",
                }
                if ml.get("session") and ml["session"] in idx_session:
                    vals["shooting_id"] = idx_session[ml["session"]]
                elif shooting_ids:
                    vals["shooting_id"] = shooting_ids[0]
                if ml.get("mission") and ml["mission"] in idx_mission:
                    vals["mission_id"] = idx_mission[ml["mission"]]
                if ml.get("porteur_user_id"):
                    vals["holder_id"] = int(ml["porteur_user_id"])
                vals = {k2: v for k2, v in vals.items() if v is not None and v != ""}
                try:
                    eq = o.search_read("es.equipment", [["id", "=", int(ml["equipment_id"])]],
                                       ["name", "is_available", "state"], limit=1)
                    if eq and not eq[0].get("is_available"):
                        print(f"    ⚠  {eq[0].get('name')} indisponible (état {eq[0].get('state')}) — réservation quand même posée en brouillon, à arbitrer")
                    bid = o.kw("es.equipment.booking", "create", [vals])
                    _log("es.equipment.booking (draft)", bid,
                         f"{ml.get('nom')} ×{vals.get('quantity')} {vals.get('date_from')}→{vals.get('date_to')}")
                    cw = o.search_read("es.equipment.booking", [["id", "=", bid]],
                                       ["conflict_warning"], limit=1)
                    if cw and cw[0].get("conflict_warning"):
                        print(f"    ⚠  conflit : {cw[0]['conflict_warning']}")
                except Exception as e:
                    print(f"    ⚠  réservation {ml.get('nom')} non créée: {e}")
        elif materiel.get("lignes") or materiel.get("kits"):
            print("  ○ réservations matériel non créées (modèle es.equipment.booking absent)")

        # Tâches satellites (si project_id)
        for sid in shooting_ids:
            for offset, label in [(-2, "J−2 Préparation / convocation"), (0, "J Captation"), (1, "J+1 Dérushage / sauvegarde"), (2, "J+2 Intégration")]:
                try:
                    # récupérer la date de la session
                    s_info = o.search_read("es.shooting", [["id", "=", sid]], ["date_start", "name"], limit=1)
                    base = s_info[0]["date_start"] if s_info and s_info[0].get("date_start") else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    dt = datetime.strptime(base, "%Y-%m-%d %H:%M:%S") if isinstance(base, str) else base
                    from datetime import timedelta
                    deadline = (dt + timedelta(days=offset)).strftime("%Y-%m-%d")
                    # stage : chercher Validation client / Livré si besoin
                    tid = o.kw("project.task", "create", [{
                        "project_id": int(project_id),
                        "name": f"{label} — {s_info[0]['name'] if s_info else sid}",
                        "date_deadline": deadline,
                    }])
                    _log("project.task (satellite)", tid, label)
                except Exception as e:
                    print(f"    ○ tâche satellite {label} non créée: {e}")
                    break

    # 7 — Responsables sur projet
    if project_id and responsables.get("charge_projet", {}).get("user_id"):
        try:
            o.kw("project.project", "write", [[int(project_id)], {"user_id": int(responsables["charge_projet"]["user_id"])}])
            print(f"  ✓ project.project.user_id → {responsables['charge_projet']['nom']} (id {responsables['charge_projet']['user_id']})")
        except Exception as e:
            print(f"    ⚠  project.project.user_id non écrit: {e}")
            # vérifier si res.users existe
            try:
                u = o.search_read("res.users", [["id", "=", int(responsables["charge_projet"]["user_id"])]], ["id", "name"], limit=1)
                if not u:
                    print(f"    → utilisateur {responsables['charge_projet']['user_id']} sans compte res.users — proposer ouverture d'accès ou utilisateur existant, ne pas créer de compte seul")
            except Exception:
                pass

    # NAS — arborescence /WORKS (création client ou commande validée)
    try:
        import importlib.util as _ilu
        _spec = importlib.util.spec_from_file_location(
            "scaffold", str(Path(__file__).parent / "scaffold.py"))
        _scaffold = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_scaffold)
        commentaire = None
        if client.get("id"):
            partenaires = o.search_read("res.partner", [["id", "=", int(client["id"])]],
                                        ["comment"], limit=1)
            commentaire = (partenaires[0].get("comment") or None) if partenaires else None
        ref_nas, origine_nas = _dossier_nas_fiche(d, commentaire)
        if not ref_nas:
            print("  ○ arborescence NAS non créée — réf dossier absente (ni fiche ni notes client) : "
                  "demander le nom de dossier à Lycris, puis relancer")
        else:
            annee_exec = (date_cmd or datetime.now().strftime("%Y-%m-%d"))[:4]
            dossier_projet_exec = _sanitize_dossier(
                opport.get("nom") or d.get("cadrage", {}).get("type_affaire") or "PROJET")
            jours_exec = sorted({(s.get("date_start") or "")[:10] for s in sessions if s.get("date_start")})
            base_nas = Path(NAS_ROOT) / ref_nas / annee_exec / dossier_projet_exec
            try:
                res_nas = _scaffold.init_projet(
                    Path(NAS_ROOT), ref_nas, dossier_projet_exec, annee_exec,
                    jours_exec, appliquer=True)
                _log("dossier NAS", str(base_nas),
                     f"{res_nas['dossiers_crees']} dossiers (réf {origine_nas})")
            except Exception as e:
                print(f"    ⚠  arborescence NAS non créée ({NAS_ROOT} inaccessible ?) : {e}")
                print(f"    → recréer avec : scaffold.py --init --client {ref_nas} "
                      f"--projet {dossier_projet_exec} --root {NAS_ROOT} --appliquer")
            # Consigne la réf dans les notes fiche client si elle vient de la fiche
            if client.get("id") and (d.get("client") or {}).get("dossier_nas") and origine_nas == "fiche":
                try:
                    o.kw("res.partner", "write", [[int(client["id"])], {
                        "comment": ((commentaire or "") + f"\nDossier NAS: {ref_nas}").strip()}])
                    print(f"  ✓ notes client ← Dossier NAS: {ref_nas}")
                except Exception as e:
                    print(f"    ⚠  notes client non mises à jour: {e}")
    except Exception as e:
        print(f"    ⚠  étape NAS ignorée: {e}")

    # 8 — Activités de rappel
    if project_id:
        for summary, days in [("Relance acompte", 1), ("Confirmation prestataires", 2), ("J−2 préparation", 2), ("Livraison", 7), ("Solde", 30), ("FNE", 35)]:
            try:
                o.kw("mail.activity", "create", [{
                    "res_model": "project.project",
                    "res_id": int(project_id),
                    "activity_type_id": 4,  # TODO
                    "summary": summary,
                    "date_deadline": datetime.now().strftime("%Y-%m-%d"),
                    "user_id": int(responsables.get("charge_projet", {}).get("user_id") or o.uid),
                    "note": f"Rappel auto — {summary} — projet {project_id}",
                }])
            except Exception:
                pass
        print("  ✓ activités de rappel créées (relance acompte, J−2, livraison, solde, FNE)")

    print(f"\n✓ Cascade terminée — {len(crees)} enregistrement(s) créé(s)")
    print(json.dumps({"crees": crees}, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fichier", help="chemin vers la fiche commande JSON validée (temps 2)")
    ap.add_argument("--dry-run", action="store_true", default=False, help="affiche le plan sans écrire (défaut)")
    ap.add_argument("--executer", action="store_true", help="exécute réellement les écritures (nécessite validation temps 2)")
    ap.add_argument("--exemple", action="store_true", help="affiche un exemple de fiche JSON sur stdout et sort")
    a = ap.parse_args()

    if a.exemple:
        print(json.dumps(EXEMPLE, ensure_ascii=False, indent=2))
        sys.exit(0)

    if not a.fichier:
        ap.error("--fichier requis (ou --exemple pour voir la structure)")

    p = Path(a.fichier)
    if not p.exists():
        sys.exit(f"Fichier introuvable: {p}")

    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        # Evals embarquent la fiche sous "fiche" ; la commande réelle est à plat
        d = raw.get("fiche") if isinstance(raw, dict) and "fiche" in raw and isinstance(raw["fiche"], dict) else raw
    except Exception as e:
        sys.exit(f"JSON invalide: {e}")

    # --executer prime sur --dry-run ; par défaut dry-run
    executer = a.executer
    dry_run = not executer if not a.dry_run else True
    if a.executer and a.dry_run:
        sys.exit("Choisis --dry-run OU --executer, pas les deux")

    plan = _plan(d)

    # Afficher le plan dans tous les cas
    print(json.dumps(plan, ensure_ascii=False, indent=2))

    # Validations bloquantes
    if plan["validations"]:
        print("\n⚠  Validations à corriger avant d'exécuter :", file=sys.stderr)
        for e in plan["validations"]:
            print(f"  - {e}", file=sys.stderr)
        if executer:
            print("\n✗ Exécution refusée : corrige la fiche puis relance --executer", file=sys.stderr)
            sys.exit(1)
        else:
            print("\n→ Corrige la fiche puis relance avec --executer pour écrire", file=sys.stderr)
    if plan.get("avertissements"):
        print("\n⚠  Avertissements (n'empêchent pas la validation temps 2 mais à signaler à Lycris) :", file=sys.stderr)
        for w in plan["avertissements"]:
            print(f"  - {w}", file=sys.stderr)

    if dry_run or not executer:
        print("\n— Mode simulation (dry-run) : aucune écriture n'a été faite —", file=sys.stderr)
        print("Relance avec --executer après validation du temps 2 pour créer les enregistrements", file=sys.stderr)
        return

    # Executer
    print("\n— Exécution —", file=sys.stderr)
    _executer(d, plan)


if __name__ == "__main__":
    main()
