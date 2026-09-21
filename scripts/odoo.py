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

Usage :
    python3 odoo.py ping
    python3 odoo.py client "EXP-MOMENTUM"
    python3 odoo.py projet 290
    python3 odoo.py catalogue
    python3 odoo.py equipe
    python3 odoo.py commandes --client 832 --limit 10
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
    a = ap.parse_args()

    handlers = {"ping": cmd_ping, "client": cmd_client, "projet": cmd_projet,
                "catalogue": cmd_catalogue, "equipe": cmd_equipe, "commandes": cmd_commandes}
    try:
        handlers[a.cmd](Odoo(), a)
    except OdooError as exc:
        print(json.dumps({"ok": False, "erreur": str(exc)}, ensure_ascii=False, indent=2))
        sys.exit(2)


if __name__ == "__main__":
    main()
