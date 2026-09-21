#!/usr/bin/env python3
"""Client Odoo XML-RPC pour Évents & Studios + commandes de lecture courantes.

Toutes les lectures passent le contexte {'lang': 'fr_FR'} : sans lui, Odoo renvoie
les libellés en anglais et le diagnostic est faux.

Identifiants : variables d'environnement ODOO_URL / ODOO_DB / ODOO_USER /
ODOO_PASSWORD, ou fichier ~/.odoo_es.json portant les mêmes clés en minuscules.
Par défaut ODOO_URL = https://manage.eventsetstudios.ci (public, depuis 21/09/2026) ;
secours : http://100.119.180.128:8069 (Tailscale) et eventsetstudios.local (LAN).
Si le connecteur MCP Odoo est présent dans la session, il est utilisé en priorité.
En bac à sable filtré, un refus x-deny-reason sur manage.eventsetstudios.ci bascule
automatiquement sur le MCP.

Helpers ajoutés pour la proposition guidée (scripts/proposal.py) :
    list_invoices(client_id, since_date) — lignes de factures clients, avec
        fallback vers references/referentiel.md si Odoo est injoignable ;
    create_dynamic_field(entity, key, type, value) — plan de création d'un champ
        (sans écriture par défaut, confirm=True pour écrire, jamais sans accord).

Usage :
    python3 odoo.py ping
    python3 odoo.py client "EXP-MOMENTUM"
    python3 odoo.py projet 290
    python3 odoo.py catalogue
    python3 odoo.py equipe
    python3 odoo.py commandes --client 832 --limit 10
    python3 odoo.py factures --client 45 --depuis 2025-08-01
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import xmlrpc.client
from pathlib import Path

CTX = {"lang": "fr_FR"}
DEFAULTS = {"url": "https://manage.eventsetstudios.ci", "db": "odoo_db"}

DYNAMIC_FIELD_TYPES = {"char", "text", "integer", "float", "boolean",
                       "date", "datetime", "selection", "many2one"}


class OdooError(RuntimeError):
    pass


def _credentials() -> dict:
    creds = dict(DEFAULTS)
    cfg = Path.home() / ".odoo_es.json"
    if cfg.exists():
        try:
            creds.update({k: v for k, v in json.loads(cfg.read_text()).items() if v})
        except (ValueError, OSError):
            pass
    for key, env in (("url", "ODOO_URL"), ("db", "ODOO_DB"),
                     ("user", "ODOO_USER"), ("password", "ODOO_PASSWORD")):
        if os.environ.get(env):
            creds[key] = os.environ[env]
    missing = [k for k in ("url", "db", "user", "password") if not creds.get(k)]
    if missing:
        raise OdooError(
            "Identifiants Odoo manquants : " + ", ".join(missing) +
            ". Renseigne ODOO_URL / ODOO_DB / ODOO_USER / ODOO_PASSWORD, "
            "ou ~/.odoo_es.json. Ne devine pas de valeurs."
        )
    return creds


class Odoo:
    def __init__(self, timeout: int = 20):
        c = _credentials()
        self.url, self.db, self.user, self.password = c["url"], c["db"], c["user"], c["password"]
        transport = xmlrpc.client.Transport()
        try:
            common = xmlrpc.client.ServerProxy(
                f"{self.url}/xmlrpc/2/common", transport=transport, allow_none=True)
            self.version = common.version().get("server_serie", "?")
            self.uid = common.authenticate(self.db, self.user, self.password, {})
        except Exception as exc:  # réseau, DNS, hôte hors allowlist, x-deny-reason
            hint = "manage.eventsetstudios.ci hors allowlist (x-deny-reason) ? Bascule sur le connecteur MCP Odoo" \
                if "x-deny" in str(exc).lower() or "deny" in str(exc).lower() else \
                "Adresse principale https://manage.eventsetstudios.ci ; secours Tailscale 100.119.180.128:8069"
            raise OdooError(
                f"Connexion impossible à {self.url} ({exc.__class__.__name__}: {exc}). "
                f"{hint}. N'invente aucun chiffre : bascule sur references/referentiel.md "
                "et dis-le explicitement."
            ) from exc
        if not self.uid:
            raise OdooError("Authentification refusée : vérifie ODOO_USER / ODOO_PASSWORD.")
        self.models = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", allow_none=True)

    def kw(self, model: str, method: str, args=None, kwargs=None):
        kwargs = dict(kwargs or {})
        kwargs.setdefault("context", {}).update(CTX)
        return self.models.execute_kw(
            self.db, self.uid, self.password, model, method, args or [], kwargs)

    def search_read(self, model, domain=None, fields=None, limit=None, order=None):
        kwargs = {"fields": fields or []}
        if limit:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
        return self.kw(model, "search_read", [domain or []], kwargs)

    def has_model(self, model: str) -> bool:
        """Le module maison es_production n'est pas installé partout."""
        return bool(self.search_read("ir.model", [["model", "=", model]], ["id"], limit=1))


# ------------------------------------------------- helpers proposition guidée

def list_invoices(client_id: int | None = None, since_date: str | None = None,
                  limit: int = 200) -> dict:
    """Lignes de factures clients pour le matching (scripts/matching.py).

    Retourne {"source": "odoo"|"referentiel", "invoices": [...]} où chaque ligne
    porte invoice_id, client_id, service_code ("PROD_<product_id>"), category,
    label, unit_price, currency (XOF) et date.

    Échec Odoo (réseau, identifiants, x-deny-reason) → fallback vers
    references/referentiel.md via matching.referentiel_history(), source
    annoncée comme "referentiel". N'invente jamais de chiffres.
    """
    try:
        o = Odoo()
        domain = [["move_type", "=", "out_invoice"], ["state", "=", "posted"]]
        if client_id:
            domain.append(["partner_id", "=", int(client_id)])
        if since_date:
            domain.append(["invoice_date", ">=", since_date])
        moves = o.search_read(
            "account.move", domain,
            ["name", "partner_id", "invoice_date", "amount_total", "currency_id"],
            limit=limit, order="invoice_date desc")
        if not moves:
            return {"source": "odoo", "invoices": []}
        by_id = {m["id"]: m for m in moves}
        lines = o.search_read(
            "account.move.line",
            [["move_id", "in", list(by_id)], ["product_id", "!=", False]],
            ["move_id", "product_id", "name", "quantity", "price_unit",
             "price_subtotal", "product_uom_id"],
            limit=limit * 20)
        out = []
        for l in lines:
            m = by_id.get((l.get("move_id") or [None])[0])
            if not m or not m.get("invoice_date"):
                continue
            prod = l.get("product_id") or [None, ""]
            out.append({
                "invoice_id": m["id"],
                "invoice_name": m.get("name"),
                "client_id": (m.get("partner_id") or [None])[0],
                "service_code": f"PROD_{prod[0]}",
                "category": "",
                "label": l.get("name") or prod[1],
                "unit_price": float(l.get("price_unit") or 0),
                "currency": ((m.get("currency_id") or [None, "XOF"])[1]
                             if isinstance(m.get("currency_id"), list) else "XOF"),
                "date": str(m["invoice_date"])[:10],
            })
        return {"source": "odoo", "invoices": out}
    except Exception as exc:
        try:
            from matching import referentiel_history  # import tardif : pas de cycle
        except ImportError:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from matching import referentiel_history
        lines = referentiel_history()
        if client_id:
            same = [l for l in lines if l.get("client_id") == int(client_id)]
            lines = same or lines  # sans historique client : tout le référentiel
        return {"source": "referentiel",
                "invoices": lines,
                "avertissement": f"Odoo injoignable ({exc.__class__.__name__}) : "
                                 "historique du référentiel embarqué, à annoncer."}


def create_dynamic_field(entity: str, key: str, field_type: str = "char",
                         value=None, confirm: bool = False,
                         o: Odoo | None = None) -> dict:
    """Prépare (ou crée avec confirm=True) un champ dynamique sur `entity`.

    Sans confirm : aucune écriture, retourne le plan exact (modèle
    ir.model.fields, valeurs) pour validation par Lycris — conforme à la règle
    « proposer, faire valider, écrire ». Avec confirm=True : crée le champ
    (jamais sans accord explicite) et retourne son id.
    """
    ftype = (field_type or "char").lower()
    if ftype not in DYNAMIC_FIELD_TYPES:
        raise ValueError(f"type {field_type!r} inconnu — choisir parmi "
                         f"{sorted(DYNAMIC_FIELD_TYPES)}")
    if not key or not key.replace("_", "").isalnum():
        raise ValueError(f"clé {key!r} invalide (lettres/chiffres/_ uniquement)")
    plan = {
        "ok": False,
        "action": "création de champ dynamique (aucune écriture effectuée)",
        "model": "ir.model.fields",
        "values": {
            "name": f"x_{key}",
            "model_id": f"<id ir.model de {entity}>",
            "field_description": key.replace("_", " ").capitalize(),
            "ttype": ftype,
            "state": "manual",
        },
        "valeur_initiale": value,
        "validation_requise": "relancer avec confirm=True après accord explicite",
    }
    if not confirm:
        return plan
    o = o or Odoo()
    if not o.has_model(entity):
        raise OdooError(f"modèle {entity} introuvable dans Odoo")
    models = o.search_read("ir.model", [["model", "=", entity]], ["id"], limit=1)
    vals = dict(plan["values"], model_id=models[0]["id"])
    new_id = o.kw("ir.model.fields", "create", [vals])
    return {"ok": True, "model": "ir.model.fields", "id": new_id,
            "name": vals["name"], "valeur_initiale": value}


# ---------------------------------------------------------------- commandes CLI

def cmd_ping(o: Odoo, _):
    users = o.search_read("res.users", [["id", "=", o.uid]], ["name", "login"])
    print(json.dumps({
        "ok": True, "url": o.url, "db": o.db, "version": o.version, "uid": o.uid,
        "utilisateur": users[0]["name"] if users else None,
        "es_production_installe": o.has_model("es.shooting"),
    }, ensure_ascii=False, indent=2))


def cmd_client(o: Odoo, a):
    q = a.query
    domain = [["id", "=", int(q)]] if q.isdigit() else [["name", "ilike", q]]
    parts = o.search_read("res.partner", domain,
                          ["name", "vat", "phone", "email", "city",
                           "property_payment_term_id", "company_type"], limit=10)
    out = []
    for p in parts:
        cmds = o.search_read(
            "sale.order", [["partner_id", "=", p["id"]], ["state", "in", ["sale", "done"]]],
            ["name", "date_order", "amount_untaxed", "payment_term_id"],
            limit=20, order="date_order desc")
        facs = o.search_read(
            "account.move",
            [["partner_id", "=", p["id"]], ["move_type", "=", "out_invoice"],
             ["state", "=", "posted"]],
            ["name", "invoice_date", "invoice_date_due", "amount_total",
             "amount_residual", "payment_state"],
            limit=20, order="invoice_date desc")
        impayees = [f for f in facs if f.get("amount_residual", 0) > 0]
        out.append({
            "partenaire": p,
            "commandes_confirmees": len(cmds),
            "ca_confirme": sum(c["amount_untaxed"] for c in cmds),
            "dernieres_commandes": cmds[:5],
            "factures_postees": len(facs),
            "factures_impayees": len(impayees),
            "reste_du": sum(f.get("amount_residual", 0) for f in impayees),
        })
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


def cmd_projet(o: Odoo, a):
    pid = int(a.id)
    projs = o.search_read("project.project", [["id", "=", pid]],
                          ["name", "partner_id", "user_id", "account_id",
                           "date_start", "date", "stage_id", "sale_order_id"])
    if not projs:
        print(json.dumps({"erreur": f"projet {pid} introuvable"}, ensure_ascii=False))
        return
    p = projs[0]
    taches = o.search_read("project.task", [["project_id", "=", pid]],
                           ["name", "stage_id", "user_ids", "date_deadline",
                            "state", "effective_hours"], limit=200)
    lignes = []
    if p.get("account_id"):
        lignes = o.search_read(
            "account.analytic.line",
            [["account_id", "=", p["account_id"][0]]],
            ["name", "date", "amount", "unit_amount", "employee_id",
             "product_id", "general_account_id"], limit=500)
    vendu = 0.0
    if p.get("sale_order_id"):
        so = o.search_read("sale.order", [["id", "=", p["sale_order_id"][0]]],
                           ["name", "amount_untaxed", "state", "payment_term_id"])
        vendu = so[0]["amount_untaxed"] if so else 0.0
    couts = sum(l["amount"] for l in lignes if l["amount"] < 0)
    sans_resp = [t["name"] for t in taches if not t.get("user_ids")]
    print(json.dumps({
        "projet": p,
        "vendu_ht": vendu,
        "couts": round(-couts, 2),
        "marge": round(vendu + couts, 2),
        "marge_pct": round((vendu + couts) / vendu * 100, 1) if vendu else None,
        "taches": len(taches),
        "taches_sans_responsable": sans_resp,
        "lignes_analytiques": len(lignes),
    }, ensure_ascii=False, indent=2, default=str))


def cmd_catalogue(o: Odoo, _):
    prods = o.search_read(
        "product.product", [["type", "=", "service"], ["sale_ok", "=", True]],
        ["name", "list_price", "uom_id", "categ_id", "service_tracking"],
        limit=100, order="categ_id, name")
    print(json.dumps(prods, ensure_ascii=False, indent=2, default=str))


def cmd_equipe(o: Odoo, _):
    emps = o.search_read("hr.employee", [], ["name", "job_title", "hourly_cost",
                                             "department_id", "work_email"], limit=100)
    crew = []
    if o.has_model("res.partner"):
        crew = o.search_read("res.partner", [["supplier_rank", ">", 0]],
                             ["name", "phone", "city"], limit=100)
    print(json.dumps({"employes": emps, "fournisseurs_prestataires": crew[:40]},
                     ensure_ascii=False, indent=2, default=str))


def cmd_commandes(o: Odoo, a):
    domain = [["state", "in", ["sale", "done"]]]
    if a.client:
        domain.append(["partner_id", "=", int(a.client)])
    cmds = o.search_read("sale.order", domain,
                         ["name", "partner_id", "date_order", "amount_untaxed",
                          "payment_term_id", "project_ids"],
                         limit=a.limit, order="date_order desc")
    for c in cmds:
        c["lignes"] = o.search_read(
            "sale.order.line", [["order_id", "=", c["id"]]],
            ["product_id", "product_uom_qty", "price_unit", "price_subtotal"])
    print(json.dumps(cmds, ensure_ascii=False, indent=2, default=str))


def cmd_factures(a):
    print(json.dumps(list_invoices(client_id=a.client, since_date=a.depuis,
                                   limit=a.limit),
                     ensure_ascii=False, indent=2, default=str))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ping")
    p = sub.add_parser("client"); p.add_argument("query")
    p = sub.add_parser("projet"); p.add_argument("id")
    sub.add_parser("catalogue")
    sub.add_parser("equipe")
    p = sub.add_parser("commandes")
    p.add_argument("--client"); p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("factures")
    p.add_argument("--client", type=int, help="id res.partner (optionnel)")
    p.add_argument("--depuis", help="date minimale AAAA-MM-JJ (optionnel)")
    p.add_argument("--limit", type=int, default=200)
    a = ap.parse_args()

    if a.cmd == "factures":  # helper avec fallback : pas besoin d'Odoo direct
        cmd_factures(a)
        return
    handlers = {"ping": cmd_ping, "client": cmd_client, "projet": cmd_projet,
                "catalogue": cmd_catalogue, "equipe": cmd_equipe, "commandes": cmd_commandes}
    try:
        handlers[a.cmd](Odoo(), a)
    except OdooError as exc:
        print(json.dumps({"ok": False, "erreur": str(exc)}, ensure_ascii=False, indent=2))
        sys.exit(2)


if __name__ == "__main__":
    main()
