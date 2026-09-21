#!/usr/bin/env python3
"""Proposition guidée Évents & Studios : wizard de questions → matching factures → proposal.json.

Étapes du wizard :
    1. Client (recherche / création)
    2. Contexte projet (objet, dates, lieux)
    3. Livrables & spécifs (un bloc par service)
    4. Tarification & conditions (matching ≤ 13 mois, stats + sources)
    5. Résumé & proposition (proposal.json + log d'audit)

Deux modes :
    - CLI interactif :  python3 proposal.py --start
    - API JSON :        python3 proposal.py --input brief.json --output proposal.json
                        (avec --invoices-json pour le mode hors-ligne / tests)

Règles :
    - français, montants XOF (F CFA) par défaut ;
    - champ manquant → section « création dynamique de champ » avec confirmation
      explicite avant de continuer ;
    - sans historique pertinent : "Je ne peux pas confirmer ça" + saisie manuelle ;
    - chaque proposition écrit un audit JSON dans logs/proposals.log :
      {proposal_id, computed_at, algorithm_version, source_invoice_ids, computed_by} ;
    - --dry-run : calcule sans écrire le log (idempotent) ;
    - --to-proforma : convertit proposal.json au format proforma.py (lignes
      designation/unite/qte/pu, tva 0 par défaut — règle d'octobre 2026).

Identifiants Odoo : ~/.odoo_es.json ou variables ODOO_URL / ODOO_DB /
ODOO_USER / ODOO_PASSWORD. Sans Odoo : fallback référentiel embarqué, annoncé.
"""
from __future__ import annotations

import argparse
import getpass
import json
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

try:
    from matching import (
        ALGORITHM_VERSION,
        CANNOT_CONFIRM,
        DEFAULT_CURRENCY,
        DEFAULT_MONTHS,
        DEFAULT_TOP_N,
        find_similar_invoices,
    )
except ImportError:  # exécution depuis un autre répertoire
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from matching import (
        ALGORITHM_VERSION,
        CANNOT_CONFIRM,
        DEFAULT_CURRENCY,
        DEFAULT_MONTHS,
        DEFAULT_TOP_N,
        find_similar_invoices,
    )

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOG = BASE_DIR / "logs" / "proposals.log"

STEPS = [
    "1/5 Client — recherche ou création",
    "2/5 Contexte projet — objet, dates, lieux",
    "3/5 Livrables & spécifs — un bloc par service",
    "4/5 Tarification & conditions — matching ≤ 13 mois",
    "5/5 Résumé & proposition — proposal.json + audit",
]

# Champs exigés à chaque étape : (clé, question FR, requis)
STEP_FIELDS: dict[str, list[tuple[str, str, bool]]] = {
    "client": [
        ("client_id", "ID client Odoo (0 = nouveau client à créer) ? ", True),
        ("client_nom", "Nom du client ? ", True),
    ],
    "contexte": [
        ("objet", "Objet du projet ? ", True),
        ("dates", "Dates / période (ex. 12-15/11/2026) ? ", False),
        ("lieux", "Lieux de tournage ? ", False),
    ],
    "tarification": [
        ("currency", "Devise [XOF] ? ", False),
        ("condition_paiement", "Condition de paiement (ex. 70/30) ? ", False),
    ],
}


# ------------------------------------------------------- champs dynamiques

def collect_missing(brief: dict) -> list[dict]:
    """Liste les champs manquants avec leurs prompts (section création dynamique)."""
    missing: list[dict] = []
    for step, fields in STEP_FIELDS.items():
        block = brief.get(step, brief) if step in ("client", "contexte", "tarification") else brief
        for key, prompt, required in fields:
            if required and not block.get(key):
                missing.append({"step": step, "field": key, "prompt": prompt})
    for i, svc in enumerate(brief.get("services", [])):
        for key in ("service_code", "label", "qty", "unit"):
            if not svc.get(key):
                missing.append({
                    "step": "livrables",
                    "field": f"services[{i}].{key}",
                    "prompt": f"Service n°{i + 1} — {key} ? ",
                })
    if not brief.get("services"):
        missing.append({"step": "livrables", "field": "services",
                        "prompt": "Au moins un service (code, libellé, quantité, unité) ? "})
    return missing


def prompt_dynamic_fields(missing: list[dict], input_fn=input) -> dict:
    """Affiche la section « création dynamique de champ » et exige confirmation."""
    print("\n— Création dynamique de champ : informations manquantes —")
    created: dict = {}
    for m in missing:
        val = input_fn(f"  [{m['step']}] {m['prompt']}").strip()
        created[m["field"]] = val
    print("\nRécapitulatif des champs à créer :")
    for k, v in created.items():
        print(f"  - {k} = {v!r}")
    ok = input_fn("Confirmer la création de ces champs (tapez OUI) ? ").strip().lower()
    if ok not in ("oui", "o", "yes", "y"):
        print("Création annulée : " + CANNOT_CONFIRM)
        sys.exit(3)
    # Tente l'enregistrement côté Odoo (champ modèle), sinon consigne locale.
    try:
        from odoo import create_dynamic_field
        for k, v in created.items():
            if "." not in k:  # seuls les champs simples sont proposés à Odoo
                print("  Odoo : " + json.dumps(
                    create_dynamic_field("crm.lead", k, "char", v, confirm=False),
                    ensure_ascii=False))
    except Exception as exc:
        print(f"  (Odoo injoignable : champs conservés dans proposal.json — {exc})")
    return created


def apply_created(brief: dict, created: dict) -> dict:
    """Réinjecte les champs créés dans le brief (clés simples + services[i].clé)."""
    import re
    brief = json.loads(json.dumps(brief))
    for k, v in created.items():
        m = re.fullmatch(r"services\[(\d+)\]\.(\w+)", k)
        if m:
            i = int(m.group(1))
            while len(brief.setdefault("services", [])) <= i:
                brief["services"].append({})
            brief["services"][i][m.group(2)] = v
        elif k in ("client_id",):
            brief.setdefault("client", {})[k] = int(v) if str(v).isdigit() else v
        else:
            for step in ("client", "contexte", "tarification"):
                fields = [f for f, _, _ in STEP_FIELDS.get(step, [])]
                if k in fields:
                    brief.setdefault(step, {})[k] = v
                    break
            else:
                brief[k] = v
    return brief


# ------------------------------------------------------------- construction

def build_proposal(
    brief: dict,
    invoices: list[dict] | None = None,
    reference_date=None,
    months: int = DEFAULT_MONTHS,
    top_n: int = DEFAULT_TOP_N,
    computed_by: str | None = None,
    proposal_id: str | None = None,
    dry_run: bool = False,
    log_path: str | Path | None = None,
) -> tuple[dict, dict]:
    """Construit proposal.json + entrée d'audit. Retourne (proposal, audit)."""
    computed_by = computed_by or getpass.getuser()
    proposal_id = proposal_id or f"PROP-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    currency = (brief.get("tarification", {}) or {}).get("currency") or brief.get("currency") or DEFAULT_CURRENCY
    client_id = int((brief.get("client", {}) or {}).get("client_id") or brief.get("client_id") or 0)
    services = brief.get("services") or []

    matching = find_similar_invoices(
        client_id, services, months=months, top_n=top_n,
        invoices=invoices, reference_date=reference_date,
    )

    suggested_items = []
    source_ids: list = []
    confirmed = 0
    for res in matching["results"]:
        item = {
            "service_code": res["service_code"],
            "label": res["label"],
            "qty": res.get("qty", 1),
            "unit": res.get("unit", ""),
            "unit_price_suggested": res["unit_price_suggested"],
            "stats": res["stats"],
            "source_invoices": [
                {"invoice_id": m["invoice_id"], "date": m["date"], "amount": m["unit_price"]}
                for m in res["matches"]
            ],
            "status": res["status"],
        }
        if res["status"] == "unconfirmed":
            item["message"] = res["message"]
            item["action_requise"] = res["action_requise"]
        else:
            confirmed += 1
            source_ids.extend(m["invoice_id"] for m in res["matches"])
        suggested_items.append(item)

    total = sum((it["qty"] or 0) * (it["unit_price_suggested"] or 0) for it in suggested_items)
    proposal = {
        "proposal_id": proposal_id,
        "brief_id": brief.get("brief_id"),
        "client_id": client_id,
        "client_nom": (brief.get("client", {}) or {}).get("client_nom") or brief.get("client_nom"),
        "currency": currency,
        "objet": (brief.get("contexte", {}) or {}).get("objet") or brief.get("objet"),
        "suggested_items": suggested_items,
        "total_suggere": total,
        "notes": (
            f"Basé sur {len(source_ids)} facture(s) similaire(s) (≤{months} mois)."
            if confirmed else CANNOT_CONFIRM + " — saisie manuelle requise."
        ),
        "created_fields": brief.get("created_fields", {}),
        "missing_fields": [],
    }
    audit = {
        "proposal_id": proposal_id,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "algorithm_version": matching["algorithm_version"],
        "source_invoice_ids": sorted(set(source_ids)),
        "computed_by": computed_by,
    }
    if not dry_run:
        log = Path(log_path) if log_path else DEFAULT_LOG
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(audit, ensure_ascii=False) + "\n")
    return proposal, audit


def proposal_to_proforma(
    proposal: dict,
    numero: str = "PRO-XXXX-000",
    date_: str | None = None,
    validite_jours: int = 30,
    condition_paiement: str = "",
    notes: str = "",
) -> dict:
    """Convertit proposal.json au format d'entrée de scripts/proforma.py.

    Lignes : designation / unite / qte / pu. TVA 0 par défaut (règle octobre 2026).
    Les items non confirmés sont exclus et rappelés dans les notes.
    """
    lignes = []
    exclus = []
    for it in proposal.get("suggested_items", []):
        if it.get("status") != "ok" or not it.get("unit_price_suggested"):
            exclus.append(it.get("service_code") or it.get("label"))
            continue
        lignes.append({
            "designation": it.get("label") or it.get("service_code"),
            "unite": it.get("unit") or "",
            "qte": it.get("qty") or 1,
            "pu": it["unit_price_suggested"],
        })
    if exclus:
        notes = (notes + " " if notes else "") + (
            "Exclus (à chiffrer manuellement) : " + ", ".join(exclus)
            + " — " + CANNOT_CONFIRM + "."
        )
    return {
        "numero": numero,
        "date": date_ or date.today().isoformat(),
        "client": {"nom": proposal.get("client_nom") or "", "adresse": "",
                   "rccm": "", "contribuable": ""},
        "objet": proposal.get("objet") or "",
        "lignes": lignes,
        "tva": 0,
        "condition_paiement": condition_paiement,
        "validite_jours": validite_jours,
        "notes": notes or proposal.get("notes", ""),
    }


# ------------------------------------------------------------------- wizard

def wizard_start() -> dict:
    """Wizard CLI interactif en 5 étapes. Retourne le brief complété."""
    print("=== Proposition guidée Évents & Studios ===")
    brief: dict = {}
    for step in STEPS:
        print(f"\n[{step}]")
    # 1. Client
    brief["client"] = {
        "client_id": input("ID client Odoo (0 = nouveau client à créer) ? ").strip(),
        "client_nom": input("Nom du client ? ").strip(),
    }
    # 2. Contexte
    brief["contexte"] = {
        "objet": input("Objet du projet ? ").strip(),
        "dates": input("Dates / période ? ").strip(),
        "lieux": input("Lieux de tournage ? ").strip(),
    }
    # 3. Services
    services = []
    print("Services (vide pour terminer) :")
    while True:
        code = input("  code service (ex. PROD_107, VID_MO1) ? ").strip()
        if not code:
            break
        services.append({
            "service_code": code,
            "label": input("  libellé ? ").strip(),
            "qty": input("  quantité ? ").strip(),
            "unit": input("  unité ? ").strip(),
        })
    brief["services"] = services
    # 4. Tarification
    brief["tarification"] = {
        "currency": input("Devise [XOF] ? ").strip() or "XOF",
        "condition_paiement": input("Condition de paiement ? ").strip(),
    }
    # Champs manquants → création dynamique
    missing = collect_missing(brief)
    if missing:
        created = prompt_dynamic_fields(missing)
        brief = apply_created(brief, created)
        brief["created_fields"] = created
        # qty saisie en texte → entier si possible
        for svc in brief.get("services", []):
            try:
                svc["qty"] = int(svc["qty"])
            except (TypeError, ValueError):
                pass
    return brief


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", action="store_true", help="wizard CLI interactif")
    ap.add_argument("--exemple", action="store_true", help="affiche un brief JSON d'exemple")
    ap.add_argument("--input", help="brief d'entrée (JSON)")
    ap.add_argument("--invoices-json", help="historique de factures hors-ligne (JSON)")
    ap.add_argument("--output", default="proposal.json", help="fichier proposal.json de sortie")
    ap.add_argument("--months", type=int, default=DEFAULT_MONTHS)
    ap.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    ap.add_argument("--set", action="append", default=[],
                    help="champ manquant fourni : --set services[0].qty=10 (répétable)")
    ap.add_argument("--proposal-id", help="identifiant (idempotence / rejeu)")
    ap.add_argument("--dry-run", action="store_true", help="calcule sans écrire logs/proposals.log")
    ap.add_argument("--to-proforma", help="convertit proposal.json → JSON proforma.py")
    ap.add_argument("--numero", default="PRO-XXXX-000")
    a = ap.parse_args()

    if a.exemple:
        print(json.dumps({
            "brief_id": 123, "client_id": 45,
            "client": {"client_id": 45, "client_nom": "Exemple Client"},
            "contexte": {"objet": "Spot + montage", "dates": "", "lieux": ""},
            "services": [
                {"service_code": "VID_MO1", "label": "Spot 60s", "qty": 1, "unit": "video"},
                {"service_code": "MONT_H", "label": "Montage horaire", "qty": 10, "unit": "hour"},
            ],
            "tarification": {"currency": "XOF", "condition_paiement": "70/30"},
            "currency": "XOF",
        }, ensure_ascii=False, indent=2))
        return

    if a.to_proforma:
        proposal = json.loads(Path(a.to_proforma).read_text(encoding="utf-8"))
        print(json.dumps(proposal_to_proforma(proposal, numero=a.numero),
                         ensure_ascii=False, indent=2))
        return

    if a.start:
        brief = wizard_start()
        invoices = None
    elif a.input:
        brief = json.loads(Path(a.input).read_text(encoding="utf-8"))
        invoices = (json.loads(Path(a.invoices_json).read_text(encoding="utf-8"))
                    if a.invoices_json else None)
        if isinstance(invoices, dict):
            invoices = invoices.get("invoices", invoices.get("history", []))
        # --set injecte les champs manquants sans interaction
        if a.set:
            created = dict(s.split("=", 1) for s in a.set)
            brief = apply_created(brief, created)
            brief["created_fields"] = created
        missing = collect_missing(brief)
        if missing:
            print(json.dumps({"ok": False,
                              "message": "Champs manquants : complétez via --set "
                                         "ou relancez en --start (création dynamique).",
                              "missing_fields": missing},
                             ensure_ascii=False, indent=2))
            sys.exit(3)
    else:
        ap.error("utiliser --start, --input ou --to-proforma")

    proposal, audit = build_proposal(
        brief, invoices=invoices, months=a.months, top_n=a.top_n,
        proposal_id=a.proposal_id, dry_run=a.dry_run,
    )
    Path(a.output).write_text(json.dumps(proposal, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    print(json.dumps(proposal, ensure_ascii=False, indent=2))
    print(f"\nAudit : {audit['proposal_id']} — {len(audit['source_invoice_ids'])} facture(s) source "
          f"— {'log écrit' if not a.dry_run else 'dry-run, log non écrit'} "
          f"({DEFAULT_LOG if not a.dry_run else '—'})", file=sys.stderr)


if __name__ == "__main__":
    main()
