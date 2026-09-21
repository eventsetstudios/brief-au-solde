#!/usr/bin/env python3
"""Génère la proforma d'Évents & Studios en XLSX et en PDF, à la charte maison.

Charte reprise des documents officiels : bloc société en en-tête avec la baseline,
titre encadré et centré, Verdana, pied de page portant les mentions légales.

Usage :
    python3 proforma.py --data proforma.json --out ./
    python3 proforma.py --data proforma.json --out ./ --formats xlsx

Structure attendue du JSON : voir references/devis.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SOCIETE = {
    "nom": "EVENTS & STUDIOS SARLU",
    "baseline": "Création publicitaire - Production audiovisuelle - Web Agency",
    "forme": "Société à Responsabilité Limitée Unipersonnelle au capital de 1 000 000 F CFA",
    "rccm": "CI-ABJ-2018-B-04133",
    "contribuable": "1807549B",
    "siege": "Abidjan Cocody Riviera 5 — 23 BP 1307 Abidjan 23",
    "tel": "+225 27 22 27 63 77 / 07 07 47 93 06",
    "site": "www.eventsetstudios.ci",
    "email": "contact@eventsetstudios.ci",
    "gerant": "Joël-Christian Lopy",
}
POLICE = "Verdana"


def fcfa(v: float) -> str:
    return f"{int(round(v)):,}".replace(",", " ") + " F CFA"


def totaux(d: dict) -> dict:
    ht = sum(l["qte"] * l["pu"] for l in d["lignes"])
    taux = float(d.get("tva") or 0)
    tva = ht * taux / 100
    return {"ht": ht, "taux": taux, "tva": tva, "ttc": ht + tva}


# --------------------------------------------------------------------- XLSX

def build_xlsx(d: dict, path: Path) -> Path:
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise SystemExit("openpyxl manquant : pip install openpyxl")

    t = totaux(d)
    wb = Workbook()
    ws = wb.active
    ws.title = "Proforma"
    ws.sheet_view.showGridLines = False

    fin = Side(style="thin", color="B0B0B0")
    cadre = Side(style="medium", color="000000")
    box = Border(left=fin, right=fin, top=fin, bottom=fin)

    for col, w in zip("ABCDE", (44, 10, 9, 16, 18)):
        ws.column_dimensions[col].width = w

    def txt(cell, value, *, size=9, bold=False, italic=False, align="left", wrap=False):
        c = ws[cell]
        c.value = value
        c.font = Font(name=POLICE, size=size, bold=bold, italic=italic)
        c.alignment = Alignment(horizontal=align, vertical="center", wrap_text=wrap)
        return c

    ws.merge_cells("A1:E1"); txt("A1", SOCIETE["nom"], size=13, bold=True, align="center")
    ws.merge_cells("A2:E2"); txt("A2", SOCIETE["baseline"], size=8, italic=True, align="center")
    ws.merge_cells("A3:E3"); txt("A3", SOCIETE["forme"], size=7, align="center")

    ws.merge_cells("A5:E5")
    c = txt("A5", "FACTURE PROFORMA", size=12, bold=True, align="center")
    c.border = Border(left=cadre, right=cadre, top=cadre, bottom=cadre)
    ws.row_dimensions[5].height = 24

    cli = d.get("client", {})
    txt("A7", f"N° {d.get('numero', '')}", size=9, bold=True)
    txt("A8", f"Date : {d.get('date', '')}", size=9)
    txt("A9", f"Validité : {d.get('validite_jours', 30)} jours", size=9)
    txt("D7", "CLIENT", size=8, bold=True)
    txt("D8", cli.get("nom", ""), size=9, bold=True)
    txt("D9", cli.get("adresse", ""), size=8)
    if cli.get("rccm"):
        txt("D10", f"RCCM {cli['rccm']}", size=8)
    if cli.get("contribuable"):
        txt("D11", f"CC {cli['contribuable']}", size=8)

    ws.merge_cells("A12:E12")
    txt("A12", f"Objet : {d.get('objet', '')}", size=9, bold=True)

    entetes = ("Désignation", "Unité", "Qté", "Prix unitaire", "Montant")
    for i, h in enumerate(entetes, start=1):
        c = ws.cell(row=14, column=i, value=h)
        c.font = Font(name=POLICE, size=8, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F2340")
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = box
    ws.row_dimensions[14].height = 20

    r = 15
    for l in d["lignes"]:
        montant = l["qte"] * l["pu"]
        vals = (l["designation"], l.get("unite", ""), l["qte"], l["pu"], montant)
        for i, v in enumerate(vals, start=1):
            c = ws.cell(row=r, column=i, value=v)
            c.font = Font(name=POLICE, size=9)
            c.border = box
            if i == 1:
                c.alignment = Alignment(vertical="center", wrap_text=True)
            elif i in (2, 3):
                c.alignment = Alignment(horizontal="center", vertical="center")
            else:
                c.alignment = Alignment(horizontal="right", vertical="center")
                c.number_format = '#,##0" F"'
        r += 1

    def total_row(row, label, value, bold=False, fill=None):
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
        c = ws.cell(row=row, column=1, value=label)
        c.font = Font(name=POLICE, size=9, bold=bold)
        c.alignment = Alignment(horizontal="right", vertical="center")
        c.border = box
        v = ws.cell(row=row, column=5, value=value)
        v.font = Font(name=POLICE, size=9, bold=bold)
        v.alignment = Alignment(horizontal="right", vertical="center")
        v.number_format = '#,##0" F"'
        v.border = box
        if fill:
            for col in range(1, 6):
                ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor=fill)

    r += 1
    total_row(r, "Total HT", t["ht"]); r += 1
    if t["taux"]:
        total_row(r, f"TVA {t['taux']:g} %", t["tva"]); r += 1
        total_row(r, "Total TTC", t["ttc"], bold=True, fill="EEF0F8")
    else:
        total_row(r, "Total (exonéré de TVA)", t["ht"], bold=True, fill="EEF0F8")
    r += 2

    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
    txt(f"A{r}", f"Conditions de paiement : {d.get('condition_paiement', '')}",
        size=9, bold=True); r += 1
    if d.get("notes"):
        ws.merge_cells(start_row=r, start_column=1, end_row=r + 1, end_column=5)
        txt(f"A{r}", d["notes"], size=8, wrap=True); r += 3
    else:
        r += 2

    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
    txt(f"A{r}", "Fait à Abidjan, le " + str(d.get("date", "")), size=8, italic=True); r += 1
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
    txt(f"A{r}", f"{SOCIETE['gerant']}, Gérant", size=9, bold=True); r += 2

    pied = (f"RCCM {SOCIETE['rccm']} · CC {SOCIETE['contribuable']} · {SOCIETE['siege']}",
            f"{SOCIETE['tel']} · {SOCIETE['email']} · {SOCIETE['site']}")
    for ligne in pied:
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
        txt(f"A{r}", ligne, size=7, align="center"); r += 1

    ws.print_area = f"A1:{get_column_letter(5)}{r}"
    wb.save(path)
    return path


# ---------------------------------------------------------------------- PDF

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def _polices():
    """Verdana si le TTF est dans assets/, sinon Helvetica.

    La charte maison est en Verdana, mais la police n'est pas libre de
    redistribution : on ne peut pas l'embarquer dans le skill. Dépose
    Verdana.ttf et Verdana-Bold.ttf (ou verdana.ttf / verdanab.ttf, tels que
    macOS et Windows les nomment) dans assets/ et le PDF les utilisera.
    Helvetica est la substitution la plus proche en métrique.
    """
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        return "Helvetica", "Helvetica-Bold"
    paires = (("Verdana.ttf", "Verdana-Bold.ttf"), ("verdana.ttf", "verdanab.ttf"))
    for normal, bold in paires:
        fn, fb = ASSETS / normal, ASSETS / bold
        if fn.exists() and fb.exists():
            try:
                pdfmetrics.registerFont(TTFont("Verdana", str(fn)))
                pdfmetrics.registerFont(TTFont("Verdana-Bold", str(fb)))
                return "Verdana", "Verdana-Bold"
            except Exception:
                break
    return "Helvetica", "Helvetica-Bold"


def _logo():
    """Logo de l'en-tête, si assets/logo.(png|jpg) existe."""
    for nom in ("logo.png", "logo.jpg", "logo.jpeg"):
        f = ASSETS / nom
        if f.exists():
            return f
    return None


def build_pdf(d: dict, path: Path) -> Path:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                        TableStyle)
    except ImportError:
        raise SystemExit("reportlab manquant : pip install reportlab")

    t = totaux(d)
    base, gras = _polices()
    def st(name, size, **kw):
        kw.setdefault("fontName", base)
        return ParagraphStyle(name, fontSize=size, leading=size * 1.35, **kw)

    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=15 * mm, bottomMargin=20 * mm,
                            title=f"Proforma {d.get('numero', '')}")
    F = []
    lg = _logo()
    if lg:
        from reportlab.platypus import Image
        try:
            from reportlab.lib.utils import ImageReader
            iw, ih = ImageReader(str(lg)).getSize()
            h = 16 * mm
            img = Image(str(lg), width=h * iw / ih, height=h)
            img.hAlign = "CENTER"
            F.append(img)
            F.append(Spacer(1, 3 * mm))
        except Exception:
            pass
    F.append(Paragraph(SOCIETE["nom"], st("s1", 14, alignment=1, fontName=gras)))
    F.append(Paragraph(SOCIETE["baseline"], st("s2", 8, alignment=1,
                                               textColor=colors.HexColor("#555555"))))
    F.append(Paragraph(SOCIETE["forme"], st("s3", 7, alignment=1,
                                            textColor=colors.HexColor("#777777"))))
    F.append(Spacer(1, 8 * mm))

    titre = Table([[Paragraph("FACTURE PROFORMA", st("t", 13, alignment=1, fontName=gras))]],
                  colWidths=[174 * mm])
    titre.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, colors.black),
                               ("TOPPADDING", (0, 0), (-1, -1), 5),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    F.append(titre)
    F.append(Spacer(1, 6 * mm))

    cli = d.get("client", {})
    gauche = (f"<b>N° {d.get('numero','')}</b><br/>Date : {d.get('date','')}<br/>"
              f"Validité : {d.get('validite_jours',30)} jours")
    droite = f"<b>CLIENT</b><br/><b>{cli.get('nom','')}</b><br/>{cli.get('adresse','')}"
    if cli.get("rccm"):
        droite += f"<br/>RCCM {cli['rccm']}"
    if cli.get("contribuable"):
        droite += f"<br/>CC {cli['contribuable']}"
    head = Table([[Paragraph(gauche, st("g", 8.5)), Paragraph(droite, st("d", 8.5))]],
                 colWidths=[92 * mm, 82 * mm])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    F.append(head)
    F.append(Spacer(1, 4 * mm))
    F.append(Paragraph(f"<b>Objet :</b> {d.get('objet','')}", st("o", 9)))
    F.append(Spacer(1, 4 * mm))

    data = [["Désignation", "Unité", "Qté", "Prix unitaire", "Montant"]]
    for l in d["lignes"]:
        data.append([Paragraph(l["designation"], st("l", 8.5)), l.get("unite", ""),
                     f"{l['qte']:g}", fcfa(l["pu"]), fcfa(l["qte"] * l["pu"])])
    n = len(data)
    data.append(["", "", "", "Total HT", fcfa(t["ht"])])
    if t["taux"]:
        data.append(["", "", "", f"TVA {t['taux']:g} %", fcfa(t["tva"])])
        data.append(["", "", "", "Total TTC", fcfa(t["ttc"])])
    else:
        data.append(["", "", "", "Total (exonéré de TVA)", fcfa(t["ht"])])

    tbl = Table(data, colWidths=[84 * mm, 16 * mm, 14 * mm, 30 * mm, 30 * mm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2340")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), gras),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 1), (-1, -1), base),
        ("GRID", (0, 0), (-1, n - 1), 0.4, colors.HexColor("#B0B0B0")),
        ("ALIGN", (1, 1), (2, -1), "CENTER"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEABOVE", (3, n), (-1, n), 0.4, colors.HexColor("#B0B0B0")),
        ("GRID", (3, n), (-1, -1), 0.4, colors.HexColor("#B0B0B0")),
        ("FONTNAME", (3, -1), (-1, -1), gras),
        ("BACKGROUND", (3, -1), (-1, -1), colors.HexColor("#EEF0F8")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    F.append(tbl)
    F.append(Spacer(1, 5 * mm))
    F.append(Paragraph(f"<b>Conditions de paiement :</b> {d.get('condition_paiement','')}",
                       st("cp", 9)))
    if d.get("notes"):
        F.append(Spacer(1, 2 * mm))
        F.append(Paragraph(d["notes"], st("nt", 8, textColor=colors.HexColor("#444444"))))
    F.append(Spacer(1, 10 * mm))
    F.append(Paragraph(f"Fait à Abidjan, le {d.get('date','')}", st("f", 8)))
    F.append(Paragraph(f"<b>{SOCIETE['gerant']}, Gérant</b>", st("s", 9)))

    def pied(canvas, _doc):
        canvas.saveState()
        canvas.setFont(base, 6.5)
        canvas.setFillColor(colors.HexColor("#666666"))
        y = 14 * mm
        for ligne in (
            f"RCCM {SOCIETE['rccm']} · Compte contribuable {SOCIETE['contribuable']} · "
            f"{SOCIETE['siege']}",
            f"{SOCIETE['tel']} · {SOCIETE['email']} · {SOCIETE['site']}",
        ):
            canvas.drawCentredString(A4[0] / 2, y, ligne)
            y -= 8
        canvas.drawRightString(A4[0] - 18 * mm, 8 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    doc.build(F, onFirstPage=pied, onLaterPages=pied)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="fichier JSON de la proforma")
    ap.add_argument("--out", default=".", help="répertoire de sortie")
    ap.add_argument("--formats", default="xlsx,pdf")
    a = ap.parse_args()

    d = json.loads(Path(a.data).read_text(encoding="utf-8"))
    for champ in ("lignes",):
        if not d.get(champ):
            sys.exit(f"champ « {champ} » absent ou vide dans {a.data}")

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    base = f"Proforma_{(d.get('numero') or 'sans-numero').replace('/', '-')}"
    faits = []
    if "xlsx" in a.formats:
        faits.append(str(build_xlsx(d, out / f"{base}.xlsx")))
    if "pdf" in a.formats:
        faits.append(str(build_pdf(d, out / f"{base}.pdf")))

    t = totaux(d)
    print(json.dumps({"fichiers": faits, "total_ht": t["ht"], "total_ttc": t["ttc"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
