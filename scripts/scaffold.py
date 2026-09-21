#!/usr/bin/env python3
"""Scaffold NAS Évents & Studios : arborescence standard, tri, nommage, statuts.

Standard : references/production.md. Tout est simulé par défaut (--dry-run) ;
--appliquer écrit réellement (dossiers, déplacements de fichiers).

Usage (racine NAS par défaut : /WORKS/, env NAS_ROOT pour surcharger) :
    python3 scaffold.py --init --client NESTLE --projet MAGGI_TVC --annee 2026
    python3 scaffold.py --init --client X --projet Y --jours 2026-11-14,2026-11-15 --root /tmp/test
    python3 scaffold.py --trier rush001.BRAW V01_export.mp4 --client X --projet Y
    python3 scaffold.py --trier f.mp4 --client X --projet Y --appliquer
    python3 scaffold.py --verifier-nom NESTLE_MAGGI_TVC_V1_2026-09-21.mp4
    python3 scaffold.py --statut --dossier-actif 04_pre-rendus
    python3 scaffold.py --phases --projet "Spot 60s"
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

# Racine NAS par défaut : /WORKS/ (surchageable via env NAS_ROOT).
DEFAULT_NAS_ROOT = os.environ.get("NAS_ROOT", "/WORKS")

TREE = [
    "01_creation/01_brief_refs",
    "01_creation/02_sources",
    "01_creation/03_BAT",
    "02_footages/01_rushs",
    "02_footages/02_audio",
    "02_footages/03_photos_plateau",
    "02_footages/04_stock",
    "03_projets/01_premiere_resolve",
    "03_projets/02_after_effects",
    "04_pre-rendus/V01",
    "04_pre-rendus/V02",
    "04_pre-rendus/V03",
    "05_rendus/01_master_video",
    "05_rendus/02_social_media",
    "05_rendus/03_delivery_package",
]

# Dossier actif → miroir Odoo (statut projet / tâche).
MIROIR_ODOO = {
    "01_creation/01_brief_refs": "Prospect / Pré-production",
    "01_creation/02_sources": "Pré-production",
    "01_creation/03_BAT": "Pré-production (concept validé)",
    "02_footages": "Production",
    "03_projets": "Post-production",
    "04_pre-rendus": "Validation client",
    "05_rendus": "Livré",
}

RUSH_EXTS = {".braw", ".r3d", ".ari", ".cr2", ".arw", ".nef", ".dng", ".wav", ".mp3"}
PROJET_EXTS = {".prproj", ".drp", ".aep", ".psd", ".ai"}
DOC_EXTS = {".pdf", ".docx", ".doc", ".txt", ".md", ".jpg", ".jpeg", ".png"}

NOMMAGE = re.compile(
    r"^(?P<client>[A-Z0-9]+)_(?P<projet>[A-Z0-9]+)_(?P<type>[A-Z0-9x]+?)_"
    r"(?P<tag>V\d+|\d{3}|\d{4}-\d{2}-\d{2})"
    r"(?:_(?P<datefin>\d{4}-\d{2}-\d{2}))?\.(?P<ext>[A-Za-z0-9]+)$"
)
VERSION_RE = re.compile(r"(?:^|_)(V\d{1,2})(?:[_.]|$)")


def projet_root(root: Path, client: str, projet: str, annee: str) -> Path:
    return root / client / annee / projet


def plan_init(client: str, projet: str, annee: str, jours: list[str]) -> list[str]:
    """Liste des dossiers à créer (relatifs à la racine projet)."""
    chemins = list(TREE)
    for i, jour in enumerate(jours, start=1):
        tag = f"J{i:02d}_{jour}"
        for cam in ("A-CAM", "B-CAM", "DRONE"):
            chemins.append(f"02_footages/01_rushs/{tag}_{cam}")
    return chemins


def init_projet(root: Path, client: str, projet: str, annee: str,
                jours: list[str], appliquer: bool = False) -> dict:
    base = projet_root(root, client, projet, annee)
    chemins = plan_init(client, projet, annee, jours)
    crees = []
    if appliquer:
        for rel in chemins:
            (base / rel).mkdir(parents=True, exist_ok=True)
            crees.append(rel)
    return {"base": str(base), "dossiers_prevus": len(chemins),
            "dossiers_crees": len(crees), "plan": chemins if not appliquer else crees}


def trier(fichier: str, jours: list[str] | None = None) -> dict:
    """Classifie un fichier déposé → dossier de destination (sans déplacer)."""
    p = Path(fichier)
    nom, ext = p.stem, p.suffix.lower()
    haut = nom.upper()
    if ext in PROJET_EXTS:
        sous = "01_premiere_resolve" if ext in (".prproj", ".drp") else "02_after_effects"
        return {"fichier": fichier, "destination": f"03_projets/{sous}", "regle": "extension projet"}
    mver = VERSION_RE.search(haut)
    if mver and ext in {".mp4", ".mov", ".mkv"}:
        return {"fichier": fichier, "destination": f"04_pre-rendus/{mver.group(1)}",
                "regle": "export versionné → pré-rendu"}
    if ext in RUSH_EXTS or ("RUSH" in haut or "_A-CAM" in haut or "_B-CAM" in haut or "DRONE" in haut):
        if ext in {".wav", ".mp3"} and "PLATEAU" not in haut and "RUSH" not in haut:
            return {"fichier": fichier, "destination": "02_footages/02_audio", "regle": "audio"}
        jour = ""
        m = re.search(r"(J\d{2}_\d{4}-\d{2}-\d{2})", haut)
        if m:
            jour = m.group(1) + "_"
        cam = "A-CAM"
        if "B-CAM" in haut:
            cam = "B-CAM"
        elif "DRONE" in haut:
            cam = "DRONE"
        return {"fichier": fichier, "destination": f"02_footages/01_rushs/{jour}{cam}",
                "regle": "rush immutable"}
    if any(k in haut for k in ("MASTER", "FINAL", "LIVRAISON")):
        sous = "02_social_media" if ("9X16" in haut or "1X1" in haut or "SOCIAL" in haut) else "01_master_video"
        return {"fichier": fichier, "destination": f"05_rendus/{sous}", "regle": "rendu final"}
    if ext in DOC_EXTS:
        sous = "03_BAT" if "BAT" in haut else ("01_brief_refs" if any(
            k in haut for k in ("BRIEF", "REF", "CONTRAT", "DEVIS")) else "02_sources")
        return {"fichier": fichier, "destination": f"01_creation/{sous}", "regle": "document"}
    return {"fichier": fichier, "destination": None,
            "regle": "refusé au tri — type inconnu, signalé sans déplacement"}


def verifier_nom(fichier: str) -> dict:
    """Contrôle CLIENT_PROJET_TYPE_VERSION_DATE.ext (version, numéro ou date)."""
    m = NOMMAGE.match(Path(fichier).name)
    if not m:
        return {"fichier": fichier, "valide": False,
                "erreur": "format attendu CLIENT_PROJET_TYPE_VERSION_DATE.ext "
                          "(ex. NESTLE_MAGGI_TVC_V1_2026-09-21.mp4, "
                          "SUCAF_EVENT_PHOTO_001.CR2)"}
    d = m.groupdict()
    for cle in ("tag", "datefin"):
        val = d.get(cle) or ""
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", val):
            try:
                date.fromisoformat(val)
            except ValueError:
                return {"fichier": fichier, "valide": False,
                        "erreur": f"date invalide : {val}"}
    champs = {"client": d["client"], "projet": d["projet"], "type": d["type"],
              "version": d["tag"] if d["tag"].startswith("V") else None,
              "numero": d["tag"] if re.fullmatch(r"\d{3}", d["tag"]) else None,
              "date": d["datefin"] or (d["tag"] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d["tag"]) else None)}
    return {"fichier": fichier, "valide": True, "champs": champs}


def miroir_statut(dossier_actif: str) -> dict:
    """Dossier actif → statut Odoo miroir (plus long préfixe gagnant)."""
    actif = dossier_actif.strip().strip("/")
    if actif in MIROIR_ODOO:
        return {"dossier_actif": dossier_actif, "statut_odoo": MIROIR_ODOO[actif]}
    candidats = [k for k in MIROIR_ODOO if actif.startswith(k + "/")]
    if candidats:
        meilleur = max(candidats, key=len)
        return {"dossier_actif": dossier_actif, "statut_odoo": MIROIR_ODOO[meilleur]}
    racine = actif.split("/")[0]
    for cle in ("02_footages", "03_projets", "04_pre-rendus", "05_rendus"):
        if racine == cle:
            return {"dossier_actif": dossier_actif, "statut_odoo": MIROIR_ODOO[cle]}
    if racine == "01_creation":
        return {"dossier_actif": dossier_actif, "statut_odoo": "Pré-production"}
    return {"dossier_actif": dossier_actif, "statut_odoo": None,
            "erreur": "dossier inconnu du pipeline"}


def phases(projet: str) -> dict:
    """Squelette de facturation en 3 phases (montants à chiffrer via proposal.py)."""
    return {
        "projet": projet,
        "phases": [
            {"phase": 1, "nom": "Pré-production",
             "contenu": "Idée, script, direction artistique, repérages",
             "dossiers": ["01_creation"], "produits_catalogue": [106, 110]},
            {"phase": 2, "nom": "Production",
             "contenu": "Tournage / création (jours, équipe, drone, régie)",
             "dossiers": ["02_footages"], "produits_catalogue": [107, 111, 112, 113],
             "te_separee": 119},
            {"phase": 3, "nom": "Post-production",
             "contenu": "Montage, design, étalonnage, mix, exports",
             "dossiers": ["03_projets", "04_pre-rendus", "05_rendus"],
             "produits_catalogue": [109, 110]},
        ],
        "regle": "T&E (119) toujours en ligne séparée ; acompte 70/30 couvre phases 1+2, "
                 "solde à la livraison actée.",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--client", default="CLIENT")
    ap.add_argument("--projet", default="Nom_Projet")
    ap.add_argument("--annee", default="2026")
    ap.add_argument("--jours", default="",
                    help="dates de tournage séparées par des virgules (AAAA-MM-JJ)")
    ap.add_argument("--root", default=DEFAULT_NAS_ROOT,
                    help=f"racine NAS (défaut : {DEFAULT_NAS_ROOT}, env NAS_ROOT)")
    ap.add_argument("--trier", nargs="*", default=None)
    ap.add_argument("--verifier-nom", nargs="*", default=None)
    ap.add_argument("--statut", action="store_true")
    ap.add_argument("--dossier-actif", default="")
    ap.add_argument("--phases", action="store_true")
    ap.add_argument("--appliquer", action="store_true",
                    help="écrit réellement (sinon dry-run : plan affiché)")
    ap.add_argument("--dry-run", action="store_true", help="plan sans écrire (défaut)")
    a = ap.parse_args()

    if a.dry_run and a.appliquer:
        ap.error("choisir --dry-run OU --appliquer, pas les deux")
    appliquer = a.appliquer and not a.dry_run
    jours = [j.strip() for j in a.jours.split(",") if j.strip()]
    sorties = {}

    if a.init:
        sorties["init"] = init_projet(Path(a.root), a.client, a.projet, a.annee,
                                      jours, appliquer=appliquer)
    if a.trier is not None:
        resultats = []
        for f in a.trier:
            r = trier(f)
            if appliquer and r["destination"]:
                dest = projet_root(Path(a.root), a.client, a.projet, a.annee) / r["destination"]
                dest.mkdir(parents=True, exist_ok=True)
                if Path(f).exists():
                    shutil.move(f, dest / Path(f).name)
                    r["deplace"] = True
            resultats.append(r)
        sorties["tri"] = resultats
    if a.verifier_nom is not None:
        sorties["nommage"] = [verifier_nom(f) for f in a.verifier_nom]
    if a.statut:
        sorties["miroir"] = miroir_statut(a.dossier_actif)
    if a.phases:
        sorties["phases"] = phases(a.projet)
    if not sorties:
        ap.error("donner --init, --trier, --verifier-nom, --statut ou --phases")
    print(json.dumps(sorties, ensure_ascii=False, indent=2))
    if a.init and not appliquer:
        print("\n— dry-run : aucun dossier créé — relancer avec --appliquer",
              file=sys.stderr)


if __name__ == "__main__":
    main()
