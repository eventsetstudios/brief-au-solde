"""Tests unitaires — scripts/commande.py, bloc matériel (pytest, 100 % hors-ligne).

Couvre : validation des lignes d'exemplaires (equipment_id, quantité, fenêtre),
kits, avertissement porteur manquant, plan d'ops booking draft, non-régression
sans bloc materiel.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from commande import _dossier_nas_fiche, _plan, _ref_nas_depuis_commentaire, _sanitize_dossier, _validate_fiche  # noqa: E402


def _fiche_base(**overrides):
    d = {
        "client": {"id": 832, "nom": "EXP-MOMENTUM", "rccm": "X", "cc": "Y"},
        "opportunite": {"id": None, "nom": "Test"},
        "sessions": [{"nom": "J1", "date_start": "2026-10-20 08:00:00",
                      "date_stop": "2026-10-20 18:00:00", "lieu": "Abidjan",
                      "ville": "Abidjan", "type": "tournage"}],
        "missions": [],
        "responsables": {"charge_projet": {"user_id": 5, "nom": "F"}, "charges_mission": []},
        "equipe": [],
        "materiel": {
            "kits": [{"kit_id": 3, "nom": "Kit son reportage"}],
            "lignes": [
                {"equipment_id": 151, "nom": "Sony FX30", "quantite": 1,
                 "session": "J1", "date_from": "2026-10-20 08:00:00",
                 "date_to": "2026-10-20 18:00:00", "porteur_user_id": 5, "note": ""},
            ],
        },
        "argent": {
            "lignes": [{"product_id": 107, "designation": "Captation", "qte": 1, "pu": 650000}],
            "condition_paiement_id": 27, "taux_tva": 0, "cout_revient": 45000,
        },
        "options": {"confirmer_commande": False, "date_commande": "2026-10-20"},
    }
    d.update(overrides)
    return d


def _ligne(**overrides):
    base = {"equipment_id": 151, "nom": "Sony FX30", "quantite": 1,
            "session": "J1", "date_from": "2026-10-20 08:00:00",
            "date_to": "2026-10-20 18:00:00", "porteur_user_id": 5}
    base.update(overrides)
    return base


def test_fiche_materiel_valide():
    errs, warns = _validate_fiche(_fiche_base())
    assert errs == [] and warns == []


def test_sans_equipment_id_erreur():
    d = _fiche_base()
    d["materiel"]["lignes"] = [_ligne(equipment_id=None)]
    errs, _ = _validate_fiche(d)
    assert any("sans equipment_id" in e for e in errs)


def test_quantite_nulle_erreur():
    d = _fiche_base()
    d["materiel"]["lignes"] = [_ligne(quantite=0)]
    errs, _ = _validate_fiche(d)
    assert any("quantité" in e for e in errs)


def test_fenetre_manquante_ou_invalide_erreur():
    d = _fiche_base()
    d["materiel"]["lignes"] = [_ligne(date_to=None)]
    errs, _ = _validate_fiche(d)
    assert any("sans date_to" in e for e in errs)
    d["materiel"]["lignes"] = [_ligne(date_from="20/10/2026 08:00")]
    errs, _ = _validate_fiche(d)
    assert any("format date" in e for e in errs)
    d["materiel"]["lignes"] = [_ligne(date_from="2026-10-20 18:00:00",
                                      date_to="2026-10-20 08:00:00")]
    errs, _ = _validate_fiche(d)
    assert any("date_to <=" in e for e in errs)


def test_porteur_manquant_avertissement_seulement():
    d = _fiche_base()
    d["materiel"]["lignes"] = [_ligne(porteur_user_id=None)]
    errs, warns = _validate_fiche(d)
    assert errs == []
    assert any("sans porteur" in w for w in warns)


def test_kit_sans_id_erreur():
    d = _fiche_base()
    d["materiel"]["kits"] = [{"nom": "Kit ?"}]
    errs, _ = _validate_fiche(d)
    assert any("sans kit_id" in e for e in errs)


def test_plan_ops_booking_draft():
    plan = _plan(_fiche_base())
    bookings = [o for o in plan["operations"] if o["modele"] == "es.equipment.booking"]
    kits = [o for o in plan["operations"] if "Kit" in o["etape"]]
    assert len(bookings) == 1 and len(kits) == 1
    b = bookings[0]
    assert b["action"] == "create (draft)"
    assert b["details"]["equipment_id"] == 151
    assert b["details"]["porteur_user_id"] == 5
    assert "→" in b["details"]["fenetre"]
    assert plan["resume"]["materiel_reservations"] == 1
    assert plan["resume"]["materiel_kits"] == 1


def test_sans_materiel_pas_d_ops_booking():
    d = _fiche_base()
    d.pop("materiel")
    plan = _plan(d)
    assert not [o for o in plan["operations"] if o["modele"] == "es.equipment.booking"]
    assert plan["resume"]["materiel_reservations"] == 0


# ------------------------------------------------------------------- NAS

def test_sanitize_dossier():
    assert _sanitize_dossier("EXP-MOMENTUM") == "EXP-MOMENTUM"
    assert _sanitize_dossier("Festival des Lumières!") == "FESTIVAL_DES_LUMIERES"
    assert _sanitize_dossier("  Société Générale  ") == "SOCIETE_GENERALE"


def test_ref_nas_depuis_commentaire():
    assert _ref_nas_depuis_commentaire("Blabla\nDossier NAS: EXP-MOMENTUM\nFin") == "EXP-MOMENTUM"
    assert _ref_nas_depuis_commentaire("nas: mon-dossier") == "mon-dossier"
    assert _ref_nas_depuis_commentaire("aucune note") is None
    assert _ref_nas_depuis_commentaire(None) is None


def test_dossier_nas_fiche_puis_notes():
    d = _fiche_base()
    d["client"]["dossier_nas"] = "FICHE-DOSSIER"
    assert _dossier_nas_fiche(d, "Dossier NAS: NOTES-DOSSIER") == ("FICHE-DOSSIER", "fiche")
    d["client"].pop("dossier_nas")
    assert _dossier_nas_fiche(d, "Dossier NAS: NOTES-DOSSIER") == ("NOTES-DOSSIER", "notes client")
    ref, origine = _dossier_nas_fiche(d, None)
    assert ref is None and origine.startswith("non résolu")


def test_dossier_nas_invalide_erreur():
    d = _fiche_base()
    d["client"]["dossier_nas"] = "A/B"
    errs, _ = _validate_fiche(d)
    assert any("dossier_nas" in e for e in errs)


def test_plan_op_nas_avec_ref_fiche():
    d = _fiche_base()
    d["client"]["dossier_nas"] = "EXP-MOMENTUM"
    plan = _plan(d)
    nas = [o for o in plan["operations"] if o["etape"].startswith("NAS")]
    assert len(nas) == 1
    assert nas[0]["details"]["chemin"].startswith("/WORKS/EXP-MOMENTUM/2026/")
    assert "EXP-MOMENTUM" in plan["resume"]["dossier_nas"]


def test_plan_op_nas_a_demander_sans_ref():
    plan = _plan(_fiche_base())
    nas = [o for o in plan["operations"] if o["etape"].startswith("NAS")][0]
    assert "À DEMANDER" in nas["details"]["dossier_client"]
    assert "?CLIENT?" in plan["resume"]["dossier_nas"]
