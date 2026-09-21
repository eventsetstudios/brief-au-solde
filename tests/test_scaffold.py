"""Tests unitaires — scripts/scaffold.py (pytest, dossiers temporaires)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from scaffold import (  # noqa: E402
    TREE,
    init_projet,
    miroir_statut,
    phases,
    trier,
    verifier_nom,
)


def test_init_dry_run_ne_cree_rien(tmp_path):
    res = init_projet(tmp_path, "NESTLE", "MAGGI_TVC", "2026",
                      ["2026-11-14", "2026-11-15"], appliquer=False)
    assert res["dossiers_prevus"] == len(TREE) + 2 * 3  # 2 jours × 3 cams
    assert res["dossiers_crees"] == 0
    assert not (tmp_path / "NESTLE").exists()


def test_init_appliquer_arborescence_complete(tmp_path):
    res = init_projet(tmp_path, "NESTLE", "MAGGI_TVC", "2026",
                      ["2026-11-14"], appliquer=True)
    base = tmp_path / "NESTLE" / "2026" / "MAGGI_TVC"
    assert res["dossiers_crees"] == len(TREE) + 3
    for rel in ["01_creation/03_BAT", "02_footages/01_rushs/J01_2026-11-14_A-CAM",
                "02_footages/01_rushs/J01_2026-11-14_DRONE",
                "04_pre-rendus/V01", "05_rendus/03_delivery_package"]:
        assert (base / rel).is_dir()


def test_tri_rush_export_master_projet_doc():
    assert trier("J01_2026-11-14_A-CAM_001.BRAW")["destination"].startswith(
        "02_footages/01_rushs/")
    assert trier("prise_son.WAV")["destination"] == "02_footages/02_audio"
    assert trier("film_V02.mp4")["destination"] == "04_pre-rendus/V02"
    assert trier("NESTLE_MASTER_16x9.mp4")["destination"] == \
        "05_rendus/01_master_video"
    # versionné = validation, même en 9x16 : seul un MASTER/FINAL sans version part en rendu.
    assert trier("BRAND_SOCIAL_9x16_V2.mp4")["destination"] == "04_pre-rendus/V2"
    assert trier("montage.prproj")["destination"] == \
        "03_projets/01_premiere_resolve"
    assert trier("brief_client.pdf")["destination"] == \
        "01_creation/01_brief_refs"
    inconnu = trier("notes.xyz")
    assert inconnu["destination"] is None and "refusé" in inconnu["regle"]


def test_nommage_exemples_spec():
    assert verifier_nom("NESTLE_MAGGI_TVC_V1_2026-09-21.mp4")["valide"] is True
    assert verifier_nom("SUCAF_EVENT_PHOTO_001.CR2")["valide"] is True
    assert verifier_nom("BRAND_SOCIAL_9x16_V2.mp4")["valide"] is True
    bad = verifier_nom("final2.mp4")
    assert bad["valide"] is False
    bad_date = verifier_nom("X_Y_Z_V1_2026-13-40.mp4")
    assert bad_date["valide"] is False


def test_miroir_odoo():
    assert miroir_statut("01_creation/01_brief_refs")["statut_odoo"].startswith("Prospect")
    assert miroir_statut("02_footages/01_rushs")["statut_odoo"] == "Production"
    assert miroir_statut("03_projets/01_premiere_resolve")["statut_odoo"] == "Post-production"
    assert miroir_statut("04_pre-rendus/V02")["statut_odoo"] == "Validation client"
    assert miroir_statut("05_rendus")["statut_odoo"] == "Livré"
    assert miroir_statut("99_inconnu")["statut_odoo"] is None


def test_phases_facturation():
    p = phases("Spot 60s")
    assert [ph["phase"] for ph in p["phases"]] == [1, 2, 3]
    assert p["phases"][1]["te_separee"] == 119
    assert 107 in p["phases"][1]["produits_catalogue"]
