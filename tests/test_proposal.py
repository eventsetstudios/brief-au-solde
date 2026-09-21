"""Tests unitaires — scripts/proposal.py + migrations/001 (pytest, sqlite in-memory).

Couvre : migration UP/DOWN (rollback testable), cas A/B/C du matching via
build_proposal, log d'audit, dry-run, champs manquants, conversion proforma.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from matching import CANNOT_CONFIRM  # noqa: E402
from proposal import (  # noqa: E402
    apply_created,
    build_proposal,
    collect_missing,
    proposal_to_proforma,
)

REF = date(2026, 9, 21)
MIGRATION = ROOT / "migrations" / "001_add_pricing_history_and_dynamic_fields.sql"


def inv(iid, client, code, label, price, day, cat="Video"):
    return {"invoice_id": iid, "client_id": client, "service_code": code,
            "category": cat, "label": label, "unit_price": price,
            "currency": "XOF", "date": day}


BRIEF = {
    "brief_id": 123, "client_id": 45,
    "client": {"client_id": 45, "client_nom": "Exemple Client"},
    "contexte": {"objet": "Spot + montage", "dates": "10/2026", "lieux": "Abidjan"},
    "services": [
        {"service_code": "VID_MO1", "label": "Spot 60s", "qty": 1, "unit": "video"},
        {"service_code": "MONT_H", "label": "Montage horaire", "qty": 10, "unit": "hour"},
    ],
    "tarification": {"currency": "XOF", "condition_paiement": "70/30"},
    "currency": "XOF",
}

HISTO = [
    inv(789, 45, "VID_MO1", "Spot 60s diffusion web", 750000, "2026-03-12"),
    inv(790, 45, "VID_MO1", "Spot 60s version reseaux", 690000, "2026-06-01"),
    inv(791, 7, "VID_MO1", "Spot 60s institutionnel", 600000, "2026-05-01"),
    inv(792, 9, "VID_MO1", "Spot 60s festival", 800000, "2026-04-10"),
    inv(800, 45, "MONT_H", "Montage horaire reportage", 25000, "2026-07-15"),
    inv(801, 45, "MONT_H", "Montage horaire captation", 30000, "2026-08-20"),
]


# ------------------------------------------------------------- migration

def _split_migration(text: str) -> tuple[str, str]:
    up, _, down_block = text.partition("DOWN (rollback)")
    downs = [ln.lstrip("- ").strip() for ln in down_block.splitlines()
             if ln.strip().startswith("-- DROP")]
    return up, "\n".join(downs)


def test_migration_up_down_rollback():
    sql = MIGRATION.read_text(encoding="utf-8")
    up, down = _split_migration(sql)
    assert "CREATE TABLE IF NOT EXISTS pricing_history" in up
    assert "CREATE TABLE IF NOT EXISTS dynamic_fields" in up
    assert down.count("DROP TABLE IF EXISTS") == 2

    con = sqlite3.connect(":memory:")
    con.executescript(up)
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"pricing_history", "dynamic_fields"} <= tables

    con.execute(
        "INSERT INTO pricing_history (invoice_id, client_id, service_code, label,"
        " unit_price, currency, invoice_date, source)"
        " VALUES (789, 45, 'VID_MO1', 'Spot 60s', 750000, 'XOF', '2026-03-12', 'odoo')")
    con.execute(
        "INSERT INTO dynamic_fields (entity, field_key, field_type, field_value,"
        " proposal_id, created_by)"
        " VALUES ('crm.lead', 'lieux', 'char', 'Abidjan', 'PROP-1', 'test')")
    with pytest.raises(sqlite3.IntegrityError):  # unicité traçabilité
        con.execute(
            "INSERT INTO dynamic_fields (entity, field_key, proposal_id)"
            " VALUES ('crm.lead', 'lieux', 'PROP-1')")

    con.executescript(down)  # rollback
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "pricing_history" not in tables and "dynamic_fields" not in tables
    con.close()


# ------------------------------------------------------------- cas A / B / C

def test_proposal_cas_a(tmp_path):
    proposal, audit = build_proposal(
        BRIEF, invoices=HISTO, reference_date=REF, computed_by="test",
        proposal_id="PROP-A", log_path=tmp_path / "proposals.log")
    assert proposal["proposal_id"] == "PROP-A"
    assert proposal["currency"] == "XOF"
    assert len(proposal["suggested_items"]) == 2
    vid = proposal["suggested_items"][0]
    assert vid["status"] == "ok"
    assert vid["unit_price_suggested"] == 720000
    assert vid["stats"]["count"] == 4
    assert vid["source_invoices"][0]["invoice_id"] in (789, 790)
    mont = proposal["suggested_items"][1]
    assert mont["unit_price_suggested"] == 27500
    assert proposal["total_suggere"] == 720000 * 1 + 27500 * 10
    assert "4 facture(s)" in proposal["notes"] or "6 facture(s)" in proposal["notes"]
    assert set(audit) == {"proposal_id", "computed_at", "algorithm_version",
                          "source_invoice_ids", "computed_by"}
    assert audit["source_invoice_ids"] == sorted(audit["source_invoice_ids"])
    logged = json.loads((tmp_path / "proposals.log").read_text(encoding="utf-8").strip())
    assert logged["proposal_id"] == "PROP-A"


def test_proposal_cas_b(tmp_path):
    brief = json.loads(json.dumps(BRIEF))
    brief["client_id"] = 99
    brief["client"] = {"client_id": 99, "client_nom": "Nouveau"}
    proposal, _ = build_proposal(brief, invoices=HISTO, reference_date=REF,
                                 proposal_id="PROP-B",
                                 log_path=tmp_path / "proposals.log")
    vid = proposal["suggested_items"][0]
    assert vid["status"] == "ok"  # factures d'autres clients ≤ 13 mois
    assert all("same_client" not in s for s in vid["source_invoices"])


def test_proposal_cas_c_phrase_exacte(tmp_path):
    vieux = [inv(700, 45, "VID_MO1", "Spot 60s archive", 500000, "2024-01-10")]
    proposal, audit = build_proposal(BRIEF, invoices=vieux, reference_date=REF,
                                     proposal_id="PROP-C",
                                     log_path=tmp_path / "proposals.log")
    for it in proposal["suggested_items"]:
        assert it["status"] == "unconfirmed"
        assert it["message"] == CANNOT_CONFIRM
        assert it["stats"] is None
    assert proposal["notes"].startswith(CANNOT_CONFIRM)
    assert audit["source_invoice_ids"] == []


def test_dry_run_n_ecrit_pas_le_log(tmp_path):
    log = tmp_path / "proposals.log"
    build_proposal(BRIEF, invoices=HISTO, reference_date=REF, dry_run=True,
                   log_path=log)
    assert not log.exists()


# ------------------------------------------------------- champs / proforma

def test_collect_missing_et_apply():
    brief = {"client": {"client_nom": "X"}, "services": [{"label": "Spot"}]}
    missing = collect_missing(brief)
    fields = {m["field"] for m in missing}
    assert "client_id" in fields
    assert "services[0].service_code" in fields
    fixed = apply_created(brief, {"client_id": "45", "services[0].service_code": "VID_MO1",
                                  "services[0].qty": "1", "services[0].unit": "video"})
    assert collect_missing({**fixed, "contexte": {"objet": "O"},
                            "tarification": {}}) == []


def test_to_proforma_exclut_non_confirmes():
    proposal, _ = build_proposal(BRIEF, invoices=[], reference_date=REF,
                                 dry_run=True, log_path="/tmp/nonexistent.log")
    pro = proposal_to_proforma(proposal, numero="PRO-2026-001")
    assert pro["lignes"] == []  # tout non confirmé → aucune ligne inventée
    assert pro["tva"] == 0
    assert CANNOT_CONFIRM in pro["notes"]

    ok_proposal, _ = build_proposal(BRIEF, invoices=HISTO, reference_date=REF,
                                    dry_run=True, log_path="/tmp/nonexistent.log")
    pro2 = proposal_to_proforma(ok_proposal, numero="PRO-2026-002")
    assert pro2["lignes"][0] == {"designation": "Spot 60s", "unite": "video",
                                 "qte": 1, "pu": 720000}
    assert set(pro2) >= {"numero", "date", "client", "objet", "lignes", "tva",
                         "condition_paiement", "validite_jours", "notes"}
