"""Vyrobí elaborát Geodézia 1, Zadanie 2 (Meranie vodorovných smerov) ako DOCX a PDF.

Vychádza z Adamovho odovzdaného Zadania 1 (obálka, štýly, hlavičky), technickú správu,
schému merania a zápisník vodorovných smerov generuje nanovo z údajov v JSON súbore.
Chýbajúce údaje (null) sa v dokumente zvýraznia žltou ako [doplniť].

Použitie:
    python tools/geodezia_zadanie2.py            # DOCX + PDF (PDF cez MS Word)
    python tools/geodezia_zadanie2.py --no-pdf   # len DOCX
"""
import json
import re
import shutil
import subprocess
import sys
import zipfile
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
DIR = REPO / "ZS_2026-27" / "Geodezia_1" / "Zadania" / "MOLNAR_GEODEZIA"
TEMPLATE = DIR / "MOLNAR_Zadanie_1_Teodolit.docx"
DATA = DIR / "Zadanie_2_data.json"
OUT = DIR / "MOLNAR_Zadanie_2_Meranie_vodorovnych_smerov.docx"
BUILD = REPO / "tools" / "_build_zadanie2"
sys.stdout.reconfigure(encoding="utf-8")

CC = Decimal("0.0001")
FULL = Decimal(400)


# ---------------------------------------------------------------- výpočty
def norm(v):
    return v % FULL


def mean_two(i, ii):
    """Priemer z I. a II. polohy: II. poloha sa zredukuje o 200 g do blízkosti I."""
    ii_red = ii - 200
    d = (ii_red - i + 200) % FULL - 200
    return norm(i + d / 2).quantize(CC, ROUND_HALF_UP)


def compute(ins):
    """Vráti zápisník: pre každú skupinu priemer a redukciu, pre každý bod výsledný smer."""
    cit = ins.get("citania")
    if not cit:
        return None
    pts = len(cit)
    groups = len(cit[0])
    mean = [[mean_two(Decimal(cit[p][g][0]), Decimal(cit[p][g][1])) for g in range(groups)]
            for p in range(pts)]
    red = [[norm(mean[p][g] - mean[0][g]) for g in range(groups)] for p in range(pts)]
    # 2c = I - (II -+ 200): rozdiel polôh (vplyv kolimačnej chyby)
    dc = [[(Decimal(cit[p][g][0]) - Decimal(cit[p][g][1]) + 200 + 200) % FULL - 200
           for g in range(groups)] for p in range(pts)]
    final = []
    for p in range(pts):
        vals = [red[p][g] for g in range(groups)]
        if p and max(vals) - min(vals) > 200:  # okolo 0/400
            vals = [(v + 200) % FULL - 200 for v in vals]
        final.append(norm(sum(vals) / groups).quantize(CC, ROUND_HALF_UP))
    spread = [max(r) - min(r) for r in red]
    return {"mean": mean, "red": red, "final": final, "dc": dc, "spread": spread}


def gcc(v):
    """Rozdelí hodnotu v gonoch na (g, c, cc) ako reťazce."""
    v = Decimal(v).quantize(CC, ROUND_HALF_UP)
    g = int(v)
    rest = int(((v - g) * 10000).to_integral_value())
    return str(g), f"{rest // 100:02d}", f"{rest % 100:02d}"


def gon(v, sign=False):
    s = f"{Decimal(v).quantize(CC, ROUND_HALF_UP):.4f}".replace(".", ",")
    return ("+" + s if sign and Decimal(v) > 0 else s)


def cc_str(v):
    n = int((Decimal(v) * 10000).to_integral_value(ROUND_HALF_UP))
    return f"{n:+d}".replace("+", "+ ").replace("-", "− ") if n else "0"


# ---------------------------------------------------------------- XML pomôcky
HL = '<w:highlight w:val="yellow"/>'


def runs(text, rpr="", size=None):
    """Text s mini-značkami: _{dolný index}, ^{horný index}, [[doplniť]] = žlté zvýraznenie."""
    out = []
    sz = f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>' if size else ""
    for tok in re.split(r"(_\{[^}]*\}|\^\{[^}]*\}|\[\[[^\]]*\]\]|\t)", text):
        if not tok:
            continue
        extra = ""
        if tok == "\t":
            out.append(f"<w:r><w:rPr>{rpr}{sz}</w:rPr><w:tab/></w:r>")
            continue
        if tok.startswith("_{"):
            tok, extra = tok[2:-1], '<w:vertAlign w:val="subscript"/>'
        elif tok.startswith("^{"):
            tok, extra = tok[2:-1], '<w:vertAlign w:val="superscript"/>'
        elif tok.startswith("[["):
            tok, extra = "[" + tok[2:-2] + "]", HL
        out.append(f'<w:r><w:rPr>{rpr}{extra}{sz}</w:rPr>'
                   f'<w:t xml:space="preserve">{escape(tok)}</w:t></w:r>')
    return "".join(out)


def para(text="", *, bold=False, italic=False, size=None, align=None, before=None, after=120,
         keep=False, tabs=None, page_break=False):
    ppr = ""
    if keep:
        ppr += "<w:keepNext/>"
    if tabs:
        ppr += "<w:tabs>" + "".join(f'<w:tab w:val="{k}" w:pos="{p}"/>' for k, p in tabs) + "</w:tabs>"
    sp = ""
    if before is not None:
        sp += f' w:before="{before}"'
    if after is not None:
        sp += f' w:after="{after}"'
    if sp:
        ppr += f"<w:spacing{sp}/>"
    if align:
        ppr += f'<w:jc w:val="{align}"/>'
    rpr = ("<w:b/><w:bCs/>" if bold else "") + ("<w:i/><w:iCs/>" if italic else "")
    br = '<w:r><w:br w:type="page"/></w:r>' if page_break else ""
    return f"<w:p><w:pPr>{ppr}</w:pPr>{br}{runs(text, rpr, size)}</w:p>"


def heading(text):
    return para(text, bold=True, before=240, after=120, keep=True)


def formula(text, num):
    return para(f"\t{text}\t({num})", tabs=[("center", 4961), ("right", 9865)], after=160)


def cell(text, w, *, bold=False, shade=None, span=1, vmerge=None, size=18, align="center",
         thick=None):
    tcpr = f'<w:tcW w:w="{w}" w:type="dxa"/>'
    if span > 1:
        tcpr += f'<w:gridSpan w:val="{span}"/>'
    if vmerge == "restart":
        tcpr += '<w:vMerge w:val="restart"/>'
    elif vmerge == "cont":
        tcpr += "<w:vMerge/>"
    if thick:
        tcpr += "<w:tcBorders>" + "".join(
            f'<w:{s} w:val="single" w:sz="12" w:space="0" w:color="000000"/>' for s in thick
        ) + "</w:tcBorders>"
    if shade:
        tcpr += f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>'
    tcpr += '<w:vAlign w:val="center"/>'
    rpr = "<w:b/><w:bCs/>" if bold else ""
    p = (f'<w:p><w:pPr><w:spacing w:before="20" w:after="20"/><w:jc w:val="{align}"/></w:pPr>'
         f'{runs(text, rpr, size)}</w:p>')
    return f"<w:tc><w:tcPr>{tcpr}</w:tcPr>{p}</w:tc>"


def table(rows, grid, header_rows=1):
    tw = sum(grid)
    tbl = (f'<w:tbl><w:tblPr><w:tblW w:w="{tw}" w:type="dxa"/><w:jc w:val="center"/>'
           '<w:tblBorders>' + "".join(
               f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
               for s in ("top", "left", "bottom", "right", "insideH", "insideV")) +
           '</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblCellMar>'
           '<w:left w:w="28" w:type="dxa"/><w:right w:w="28" w:type="dxa"/></w:tblCellMar>'
           '</w:tblPr><w:tblGrid>' + "".join(f'<w:gridCol w:w="{g}"/>' for g in grid) +
           "</w:tblGrid>")
    for i, r in enumerate(rows):
        trpr = "<w:cantSplit/>" + ("<w:tblHeader/>" if i < header_rows else "")
        tbl += f"<w:tr><w:trPr>{trpr}</w:trPr>{''.join(r)}</w:tr>"
    return tbl + "</w:tbl>"


# ---------------------------------------------------------------- schéma
def font(size, bold=False):
    for name in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def schema_png(path, st, b1, b2):
    """Schéma skupinovej metódy: I. poloha b1 -> b2 v smere hodín, II. poloha b2 -> b1 späť."""
    import math
    W, H = 2000, 1250
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    S = (560, 980)
    a1, a2 = math.radians(62), math.radians(8)  # smery od vodorovnej osi
    L1, L2 = 820, 1180
    P1 = (S[0] + L1 * math.cos(a1), S[1] - L1 * math.sin(a1))
    P2 = (S[0] + L2 * math.cos(a2), S[1] - L2 * math.sin(a2))
    black, blue, red = (0, 0, 0), (25, 80, 190), (200, 30, 30)

    def arrow(p, q, col, w=7):
        d.line([p, q], fill=col, width=w)
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        for s in (-1, 1):
            d.line([q, (q[0] - 42 * math.cos(ang + s * 0.38), q[1] - 42 * math.sin(ang + s * 0.38))],
                   fill=col, width=w)

    def arc(r, start, end, col, cw):
        """Oblúk okolo S od uhla start po end (v stupňoch, matematicky) so šípkou na konci."""
        pts = []
        n = 60
        for k in range(n + 1):
            t = math.radians(start + (end - start) * k / n)
            pts.append((S[0] + r * math.cos(t), S[1] - r * math.sin(t)))
        d.line(pts, fill=col, width=6, joint="curve")
        q, p = pts[-1], pts[-4]
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        for s in (-1, 1):
            d.line([q, (q[0] - 36 * math.cos(ang + s * 0.45), q[1] - 36 * math.sin(ang + s * 0.45))],
                   fill=col, width=6)
        return pts[len(pts) // 2]

    arrow(S, P1, black)
    arrow(S, P2, black)
    for P, lab in ((P1, b1), (P2, b2)):
        d.ellipse([P[0] - 20, P[1] - 20, P[0] + 20, P[1] + 20], fill=(70, 120, 200), outline=black, width=4)
        d.text((P[0] + 34, P[1] - 30), lab, font=font(60, True), fill=black)
    d.ellipse([S[0] - 24, S[1] - 24, S[0] + 24, S[1] + 24], fill=black)
    d.text((S[0] - 70, S[1] + 34), st, font=font(60, True), fill=black)

    m1 = arc(330, 62, 8, blue, True)
    m2 = arc(520, 8, 62, red, False)
    d.text((m1[0] + 18, m1[1] - 20), "I.", font=font(56, True), fill=blue)
    d.text((m2[0] + 26, m2[1] - 30), "II.", font=font(56, True), fill=red)
    d.text((S[0] + 175, S[1] - 175), "ω", font=font(64), fill=black)
    d.text((S[0] + 215, S[1] - 168), "", font=font(40), fill=black)

    lx, ly = 1180, 70
    d.text((lx, ly), "Legenda", font=font(44, True), fill=black)
    d.line([(lx, ly + 95), (lx + 110, ly + 95)], fill=blue, width=7)
    d.text((lx + 130, ly + 70), f"I. poloha: {b1} → {b2}", font=font(40), fill=black)
    d.line([(lx, ly + 165), (lx + 110, ly + 165)], fill=red, width=7)
    d.text((lx + 130, ly + 140), f"II. poloha: {b2} → {b1}", font=font(40), fill=black)
    d.text((lx, ly + 215), "nulové čítanie na prvý bod:", font=font(40), fill=black)
    d.text((lx, ly + 265), "0 g / 70 g / 140 g (1. / 2. / 3. skupina)", font=font(40), fill=black)
    im.save(path)
    return W, H


def drawing(rid, cx, cy, did, name):
    return (f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="60"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:rPr><w:noProof/></w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
            f'<wp:docPr id="{did}" name="{name}"/><wp:cNvGraphicFramePr>'
            '<a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/>'
            '</wp:cNvGraphicFramePr><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:nvPicPr><pic:cNvPr id="0" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
            '</wp:inline></w:drawing></w:r></w:p>')


# ---------------------------------------------------------------- obsah
def val(x, placeholder="doplniť"):
    return x if x else f"[[{placeholder}]]"


def report(data, res):
    ins = data["pristroje"]
    mer = val(data.get("datum_merania"), "dátum merania")
    miesto = val(data.get("miesto_merania"), "miesto merania")
    names = " a ".join(i["nazov"] for i in ins)
    x = []
    x.append(para("Technická správa", bold=True, size=28, align="center", after=360))

    x.append(heading("1  Definícia úlohy"))
    x.append(para(
        f"Elaborát bol vypracovaný na základe zadania č. 2 z predmetu Geodézia 1, ktoré zadal "
        f"doc. Ing. Marián Marčiš, PhD. dňa {data['zadane']}. Cieľom úlohy bolo odmerať 2 vodorovné "
        f"smery v troch skupinách v dvoch polohách ďalekohľadu prístrojmi {names} a vypočítať "
        f"zápisník meraných vodorovných smerov."))

    x.append(heading("2  Postup merania"))
    x.append(para(
        f"Meranie sme vykonali dňa {mer} ({miesto}). Použili sme optický reiteračný teodolit "
        f"Zeiss THEO 010A s koincidenčným mikrometrom a elektronický teodolit Nivel System DT-2, "
        f"oba na drevenom statíve."))
    x.append(para(
        "Prístroj sme postavili nad stanovisko, zcentrovali a zhorizontovali rovnakým postupom ako "
        "v zadaní č. 1. Vodorovné smery sme merali skupinovou metódou. V I. polohe ďalekohľadu sme "
        "zacielili na prvý bod, nastavili nulové čítanie a v smere chodu hodinových ručičiek sme "
        "zacielili na druhý bod. Potom sme ďalekohľad preložili do II. polohy a smery sme odčítali "
        "v opačnom poradí, najprv na druhý a potom na prvý bod (obr. 1). Jedno meranie v oboch "
        "polohách tvorí jednu skupinu."))
    x.append(para(
        "Aby sa zmenšil vplyv chýb delenia vodorovného kruhu, nulové čítanie na prvý bod sme "
        "v každej skupine posunuli približne o 200^{g} / 3, teda na 0^{g} v 1. skupine, 70^{g} "
        "v 2. skupine a 140^{g} v 3. skupine."))
    x.append(para(
        "Pri teodolite Zeiss THEO 010A sme po zacielení na prvý bod nastavili mikrometrom nulu "
        "a reiteračnou skrutkou otočili vodorovný kruh na požadované čítanie. Pred každým "
        "odčítaním sme mikrometrickou skrutkou skoincidovali dvojrysky a odčítali grády a "
        "desiatky centigónov na kruhu a zvyšok na stupnici mikrometra. Pri prístroji Nivel "
        "System DT-2 sme nulové čítanie nastavili pomocou klávesnice prístroja a smery sme "
        "odčítali priamo z displeja."))
    x.append(f"__SCHEMA__")
    x.append(para("Obr. 1  Schéma merania vodorovných smerov v dvoch polohách ďalekohľadu",
                  size=20, align="center", after=200))

    x.append(heading("3  Postup riešenia úlohy"))
    x.append(para(
        "Namerané smery sú zapísané v zápisníku v prílohe A.1. V každej skupine sme pre každý "
        "bod vypočítali priemer z oboch polôh ďalekohľadu, pričom čítanie v II. polohe sme "
        "zmenšili (zväčšili) o 200^{g}:", keep=True))
    x.append(formula("ψ = (ψ_{I} + (ψ_{II} ∓ 200^{g})) / 2", 1))
    x.append(para("Rozdiel čítaní v oboch polohách slúži ako kontrola merania (vplyv kolimačnej chyby):",
                  keep=True))
    x.append(formula("2c = ψ_{I} − (ψ_{II} ∓ 200^{g})", 2))
    x.append(para("Priemerné smery sme zredukovali na prvý bod, takže smer na prvý bod je v každej "
                  "skupine nulový:", keep=True))
    x.append(formula("ψ_{red,j} = ψ_{j} − ψ_{1}", 3))
    x.append(para("Výsledný smer je aritmetický priemer redukovaných smerov z troch skupín a "
                  "zároveň udáva vodorovný uhol medzi oboma bodmi:", keep=True))
    x.append(formula("ψ̄ = (ψ_{red}^{(1)} + ψ_{red}^{(2)} + ψ_{red}^{(3)}) / 3,     ω = ψ̄_{2} − ψ̄_{1}", 4))
    x.append(para("Výpočty sú v zápisníku v prílohe A.1 a výsledky sú zhrnuté v tab. 1 v tej istej prílohe."))

    x.append(heading("4  Zhodnotenie výsledkov"))
    parts = []
    for i, r in zip(ins, res):
        if r:
            sp = int((r["spread"][1] * 10000).to_integral_value())
            parts.append(f"prístrojom {i['nazov']} sme určili vodorovný uhol ω = {gon(r['final'][1])}^{{g}} "
                         f"(rozdiel redukovaných smerov medzi skupinami najviac {sp}^{{cc}})")
        else:
            parts.append(f"prístrojom {i['nazov']} sme určili vodorovný uhol ω = [[doplniť]]")
    x.append(para("Z troch skupín " + "; ".join(parts) + "."))
    if all(res):
        diff = abs(res[0]["final"][1] - res[1]["final"][1])
        x.append(para(
            f"Rozdiel uhlov z oboch prístrojov je {int((diff * 10000).to_integral_value())}^{{cc}}. "
            "Meraním v dvoch polohách ďalekohľadu sa vylúčil vplyv kolimačnej chyby a chyby "
            "horizontálnej osi, posunom nulového čítania medzi skupinami sa zmenšil vplyv chýb "
            "delenia vodorovného kruhu."))
    else:
        x.append(para("[[porovnanie prístrojov a skupín doplním po zadaní nameraných hodnôt]]"))
    x.append(para(f"V Bratislave, dňa {val(data.get('datum_spravy'), 'dátum')}", before=360, after=480))
    x.append(para("Adam Molnar\t………………………………", tabs=[("left", 6000)], after=0))
    x.append(para("\tpodpis", italic=True, size=18, tabs=[("left", 6800)]))
    return "".join(x)


def protocol(data, res):
    x = []
    x.append(para("Zápisník meraných vodorovných smerov", bold=True, size=28, align="center", after=240))
    grid = [1000, 900, 560] + ([620, 560, 560, 600, 600] * 3) + [700, 600, 600]
    GREEN, BLUE, YEL = "D9EAD3", "DCE6F2", "FFF2CC"
    for n, (ins, r) in enumerate(zip(data["pristroje"], res), 1):
        x.append(para(f"Prístroj: {ins['nazov']}", bold=True, before=120 if n == 1 else 360,
                      after=60, keep=True))
        h1 = [cell("Stanovisko", grid[0], bold=True, vmerge="restart"),
              cell("Bod", grid[1], bold=True, vmerge="restart"),
              cell("Pol.", grid[2], bold=True, vmerge="restart")]
        h2 = [cell("", grid[0], vmerge="cont"), cell("", grid[1], vmerge="cont"),
              cell("", grid[2], vmerge="cont")]
        for g in range(3):
            h1 += [cell(f"{g + 1}. skupina", 1740, bold=True, span=3),
                   cell("priemer / redukcia", 1200, bold=True, span=2, shade=GREEN)]
            h2 += [cell(u, w, bold=True) for u, w in (("g", 620), ("c", 560), ("cc", 560))]
            h2 += [cell(u, 600, bold=True, shade=GREEN) for u in ("c", "cc")]
        h1.append(cell("výsledný smer", 1900, bold=True, span=3, shade=YEL))
        h2 += [cell(u, w, bold=True, shade=YEL) for u, w in (("g", 700), ("c", 600), ("cc", 600))]
        rows = [h1, h2]
        body = ins.get("body") or [None, None]
        cit = ins.get("citania")
        for p in range(2):
            for pol in range(2):
                row = []
                if p == 0 and pol == 0:
                    row.append(cell(ins.get("stanovisko") or "[[ ]]", grid[0], vmerge="restart"))
                else:
                    row.append(cell("", grid[0], vmerge="cont"))
                row.append(cell(body[p] or "[[ ]]", grid[1], vmerge="restart") if pol == 0
                           else cell("", grid[1], vmerge="cont"))
                row.append(cell("I." if pol == 0 else "II.", grid[2]))
                for g in range(3):
                    if cit:
                        rd = gcc(cit[p][g][pol])
                    else:
                        rd = ("", "", "")
                    row += [cell(v, w) for v, w in zip(rd, (620, 560, 560))]
                    if r:
                        v = r["mean"][p][g] if pol == 0 else r["red"][p][g]
                        _, c, ccv = gcc(v)
                    else:
                        c = ccv = ""
                    sh = GREEN if pol == 0 else BLUE
                    row += [cell(c, 600, shade=sh), cell(ccv, 600, shade=sh)]
                if pol == 1 and r:
                    fg = gcc(r["final"][p])
                    row += [cell(v, w, bold=True, shade=YEL) for v, w in zip(fg, (700, 600, 600))]
                else:
                    row += [cell("", w, shade=YEL if pol else None) for w in (700, 600, 600)]
                rows.append(row)
        x.append(table(rows, grid, header_rows=2))
    x.append(para("V riadku I. je v zelenom stĺpci priemer z oboch polôh podľa vzorca (1), v riadku II. "
                  "v modrom stĺpci smer zredukovaný na prvý bod podľa vzorca (3). Grády priemeru a "
                  "redukcie sú rovnaké ako v príslušnom čítaní, preto sa nezapisujú.",
                  size=18, italic=True, before=120))

    x.append(para("Tab. 1  Kontrola polôh a výsledné vodorovné uhly", bold=True, before=240, after=60,
                  keep=True))
    g2 = [2600, 1100, 1500, 1500, 1500, 2400]
    rows = [[cell(t, w, bold=True) for t, w in zip(
        ("Prístroj", "Bod", "2c – 1. sk. [cc]", "2c – 2. sk. [cc]", "2c – 3. sk. [cc]",
         "Výsledný smer [gon]"), g2)]]
    for ins, r in zip(data["pristroje"], res):
        body = ins.get("body") or [None, None]
        for p in range(2):
            row = [cell(ins["nazov"], g2[0], vmerge="restart") if p == 0 else cell("", g2[0], vmerge="cont"),
                   cell(body[p] or "[[ ]]", g2[1])]
            for g in range(3):
                row.append(cell(cc_str(r["dc"][p][g]) if r else "", g2[2 + g]))
            row.append(cell(gon(r["final"][p]) if r else "", g2[5], bold=True))
            rows.append(row)
        row = [cell(f"Uhol ω ({ins['nazov']})", sum(g2[:5]), bold=True, span=5, align="right"),
               cell((gon(r["final"][1]) + " gon") if r else "[[ ]]", g2[5], bold=True, shade=YEL)]
        rows.append(row)
    x.append(table(rows, g2))
    return "".join(x)


# ---------------------------------------------------------------- zostavenie
def set_par_text(p, text):
    first = [True]

    def rep(m):
        if first[0]:
            first[0] = False
            return m.group(1) + escape(text) + "</w:t>"
        return m.group(1) + "</w:t>"
    return re.sub(r"(<w:t(?: [^>]*)?>)[^<]*</w:t>", rep, p)


def build(data, pages="[[ ]]"):
    res = [compute(i) for i in data["pristroje"]]
    if BUILD.exists():
        shutil.rmtree(BUILD)
    with zipfile.ZipFile(TEMPLATE) as z:
        z.extractall(BUILD)
    doc = (BUILD / "word" / "document.xml").read_text(encoding="utf-8")
    spans = [(m.start(), m.end()) for m in re.finditer(r"<w:p[ >].*?</w:p>|<w:p [^>]*/>", doc, re.S)]

    def P(i):
        return doc[spans[i][0]:spans[i][1]]

    # obálka (odseky 0..31, v 31 je koniec 1. sekcie)
    cover_end = spans[31][1]
    cover = doc[:cover_end]
    repl = {5: "Zadanie č. 2", 6: "Meranie vodorovných smerov", 17: "MERANIE VODOROVNÝCH SMEROV",
            21: str(pages), 23: "1", 25: data["zadane"],
            27: data.get("odovzdane") or "[[ ]]"}
    for i, t in sorted(repl.items(), reverse=True):
        a, b = spans[i]
        newp = set_par_text(P(i), t.replace("[[ ]]", ""))
        if "[[" in t:
            newp = newp.replace("<w:rPr>", "<w:rPr>" + HL, 1)
        cover = cover[:a] + newp + cover[b:]

    # schéma
    st = next((i.get("stanovisko") for i in data["pristroje"] if i.get("stanovisko")), None) or "S"
    b = next((i.get("body") for i in data["pristroje"] if i.get("body") and all(i["body"])), None) or ["1", "2"]
    media = BUILD / "word" / "media"
    W, H = schema_png(media / "image1.png", st, b[0], b[1])
    cx = int(14.5 * 360000)
    cy = int(cx * H / W)
    rels = (BUILD / "word" / "_rels" / "document.xml.rels").read_text(encoding="utf-8")
    rid1 = re.search(r'Id="(rId\d+)"[^>]*Target="media/image1.png"', rels).group(1)
    rid2 = re.search(r'Id="(rId\d+)"[^>]*Target="media/image2.png"', rels).group(1)
    rels = re.sub(r'<Relationship [^>]*Target="media/image2.png"/>', "", rels)
    (BUILD / "word" / "_rels" / "document.xml.rels").write_text(rels, encoding="utf-8")
    (media / "image2.png").unlink()

    body = report(data, res).replace("__SCHEMA__", drawing(rid1, cx, cy, 1, "schema.png"))
    sect2 = P(48)
    prilohy = "".join(P(i) for i in range(49, 53))
    prilohy += para("Príloha A.1   Zápisník meraných vodorovných smerov", after=60)
    sect3 = P(54)
    last = doc[doc.rfind("<w:sectPr"):]
    last = (last.replace('<w:pgSz w:w="11906" w:h="16838"/>',
                         '<w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>')
            .replace('w:top="1134" w:right="850" w:bottom="1134" w:left="1134"',
                     'w:top="1134" w:right="1134" w:bottom="850" w:left="1134"'))
    new = cover + body + sect2 + prilohy + sect3 + protocol(data, res) + last
    assert rid2 not in new
    (BUILD / "word" / "document.xml").write_text(new, encoding="utf-8")

    OUT.unlink(missing_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in BUILD.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(BUILD).as_posix())
    shutil.rmtree(BUILD)
    return res


def to_pdf(docx, pdf):
    ps = (f"$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
          f"$d = $w.Documents.Open('{docx}', $false, $true); $d.Fields.Update() | Out-Null; "
          f"$d.SaveAs([ref]'{pdf}', [ref]17); $d.Close([ref]0); $w.Quit()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    res = build(data)
    for i, r in zip(data["pristroje"], res):
        if r:
            print(i["nazov"], "smery:", [gon(v) for v in r["final"]],
                  "rozptyl skupín [cc]:", [int(s * 10000) for s in r["spread"]])
        else:
            print(i["nazov"], ": chýbajú čítania")
    if "--no-pdf" in sys.argv:
        print("DOCX:", OUT)
        return
    pdf = OUT.with_suffix(".pdf")
    to_pdf(OUT, pdf)
    import pymupdf
    n = len(pymupdf.open(pdf))
    build(data, pages=n)  # počet strán na obálku
    to_pdf(OUT, pdf)
    print("DOCX:", OUT)
    print("PDF:", pdf, f"({n} strán)")


if __name__ == "__main__":
    main()
