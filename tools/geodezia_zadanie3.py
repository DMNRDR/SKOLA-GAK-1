"""Vyrobí elaborát Geodézia 1, Zadanie 3 (Osové podmienky teodolitu) ako DOCX a PDF.

Obálku, štýly a hlavičky preberá z Adamovho Zadania 1, pomôcky (tabuľky, vzorce, odseky)
zo skriptu zadania 2. Technickú správu, 4 obrázky a výpočtový protokol generuje z JSON.
Chýbajúce údaje (null / prázdne zoznamy) sa v dokumente zvýraznia žltou ako [doplniť].

Jednotky v JSON: d, h v metroch; čítania a1, a2 na pravítku v milimetroch.

Použitie:
    python tools/geodezia_zadanie3.py            # DOCX + PDF (PDF cez MS Word)
    python tools/geodezia_zadanie3.py --no-pdf   # len DOCX
"""
import json
import math
import re
import shutil
import sys
import zipfile
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geodezia_zadanie2 as z2  # noqa: E402
from geodezia_zadanie2 import para, heading, formula, cell, table, font, drawing, set_par_text, HL  # noqa: E402

REPO = z2.REPO
DIR = z2.DIR
TEMPLATE = z2.TEMPLATE
DATA = DIR / "Zadanie_3_data.json"
OUT = DIR / "MOLNAR_Zadanie_3_Osove_podmienky_teodolitu.docx"
BUILD = REPO / "tools" / "_build_zadanie3"

RHO = Decimal(636620)  # ρ^cc = 200 / π · 10^4
BLACK, BLUE, RED, GRAY = (0, 0, 0), (25, 80, 190), (200, 30, 30), (120, 120, 120)


# ---------------------------------------------------------------- výpočty
def comma(v, places):
    q = Decimal(1).scaleb(-places)
    return f"{Decimal(v).quantize(q, ROUND_HALF_UP):.{places}f}".replace(".", ",")


def compute(task, kind):
    """kind 'c': c = l / (4 d) · ρ;  kind 'i': i = l / (2 h) · ρ.  Vráti None, ak chýbajú údaje."""
    base = task.get("d" if kind == "c" else "h")
    a1, a2 = task.get("a1") or [], task.get("a2") or []
    if not base or not a1 or len(a1) != len(a2):
        return None
    base_mm = Decimal(str(base)) * 1000
    k = 4 if kind == "c" else 2
    rows = []
    for x1, x2 in zip(a1, a2):
        l = abs(Decimal(str(x2)) - Decimal(str(x1)))
        rows.append((Decimal(str(x1)), Decimal(str(x2)), l, l / (k * base_mm) * RHO))
    lm = sum(r[2] for r in rows) / len(rows)
    n = len(rows)
    sl = (sum((r[2] - lm) ** 2 for r in rows) / (n - 1)).sqrt()  # smer. odchýlka jedného l
    slm = sl / Decimal(n).sqrt()                                  # smer. odchýlka priemeru
    return {"rows": rows, "l": lm, "val": lm / (k * base_mm) * RHO, "base": Decimal(str(base)),
            "sl": sl, "slm": slm, "sval": slm / (k * base_mm) * RHO, "k": k}


# ---------------------------------------------------------------- obrázky
def subtext(d, xy, base, sub, size, col, bold=True):
    """Text s dolným indexom (Arial nemá znaky ₁ ₂)."""
    f = font(size, bold)
    d.text(xy, base, font=f, fill=col)
    w = d.textlength(base, font=f)
    d.text((xy[0] + w, xy[1] + size * 0.45), sub, font=font(int(size * 0.62), bold), fill=col)


def supertext(d, xy, base, sup, size, col, bold=False):
    f = font(size, bold)
    d.text(xy, base, font=f, fill=col)
    w = d.textlength(base, font=f)
    d.text((xy[0] + w, xy[1] - size * 0.15), sup, font=font(int(size * 0.62), bold), fill=col)
    return xy[0] + w + d.textlength(sup, font=font(int(size * 0.62), bold))


def new_img(W, H):
    im = Image.new("RGB", (W, H), "white")
    return im, ImageDraw.Draw(im)


def dash(d, p, q, col=BLACK, w=6, seg=(60, 18, 10, 18)):
    """Čiarkobodkovaná čiara (os)."""
    L = math.dist(p, q)
    ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
    t, k = 0.0, 0
    while t < L:
        s = seg[k % len(seg)]
        if k % 2 == 0:
            e = min(t + s, L)
            d.line([(p[0] + ux * t, p[1] + uy * t), (p[0] + ux * e, p[1] + uy * e)], fill=col, width=w)
        t += s
        k += 1


def arrowhead(d, p, q, col=BLACK, w=5, size=34):
    ang = math.atan2(q[1] - p[1], q[0] - p[0])
    for s in (-1, 1):
        d.line([q, (q[0] - size * math.cos(ang + s * 0.4), q[1] - size * math.sin(ang + s * 0.4))],
               fill=col, width=w)


def fig_axes(path):
    """Obr. 1 – osový systém teodolitu: V, H, Z, L (schematicky v čelnom pohľade)."""
    W, H = 2000, 1500
    im, d = new_img(W, H)
    cx = 900
    # podstava a trojnožka
    d.rectangle([cx - 330, 1160, cx + 330, 1230], outline=BLACK, width=6)
    for x in (cx - 290, cx + 290):
        d.line([(x, 1230), (x, 1290)], fill=BLACK, width=10)
    d.rectangle([cx - 400, 1290, cx + 400, 1320], outline=BLACK, width=6)
    # alidáda s libelou
    d.rectangle([cx - 280, 1020, cx + 280, 1160], outline=BLACK, width=6)
    d.rounded_rectangle([cx - 170, 1050, cx + 170, 1110], radius=30, outline=BLACK, width=5)
    d.ellipse([cx - 45, 1062, cx + 45, 1098], outline=BLUE, width=5)
    # vidlica
    for x0 in (cx - 280, cx + 180):
        d.rectangle([x0, 470, x0 + 100, 1020], outline=BLACK, width=6)
    # ďalekohľad (zboku kruh, zámerná os kolmo na obrázok -> naklonená v perspektíve)
    d.ellipse([cx - 150, 420, cx + 150, 720], outline=BLACK, width=7)
    d.ellipse([cx - 70, 500, cx + 70, 640], outline=BLACK, width=5)
    # osi
    dash(d, (cx, 120), (cx, 1450), BLACK, 7)                     # V
    dash(d, (230, 570), (1570, 570), RED, 7)                      # H
    dash(d, (cx - 430, 1000), (cx + 430, 140), BLUE, 7)           # Z (perspektívne)
    dash(d, (330, 1080), (1470, 1080), (0, 130, 60), 7)           # L
    f = font(64, True)
    d.text((cx + 25, 95), "V", font=f, fill=BLACK)
    d.text((1585, 530), "H", font=f, fill=RED)
    d.text((cx + 445, 95), "Z", font=f, fill=BLUE)
    d.text((1485, 1040), "L", font=f, fill=(0, 130, 60))
    # legenda
    lx, ly = 1450, 1170
    fs = font(38)
    for k, (t, c) in enumerate((("V – vertikálna (točná) os", BLACK), ("H – horizontálna os", RED),
                                ("Z – zámerná os", BLUE), ("L – os alidádovej libely", (0, 130, 60)))):
        d.text((lx - 250, ly + 70 * k - 520), t, font=fs, fill=c)
    im.save(path)
    return W, H


def vial(d, x, y, w, h, shift, label, col):
    """Trubicová libela so stupnicou; shift = posun bubliny v dielikoch (1 dielik = 40 px)."""
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, outline=BLACK, width=5)
    m = x + w / 2
    for k in range(-5, 6):
        if k == 0:
            continue
        xx = m + k * 40
        d.line([(xx, y + 12), (xx, y + h - 12)], fill=GRAY, width=3)
    d.line([(m, y - 18), (m, y + h + 18)], fill=BLACK, width=4)
    b = m + shift * 40
    d.ellipse([b - 85, y + 14, b + 85, y + h - 14], outline=col, width=6)
    d.text((x, y - 70), label, font=font(42, True), fill=BLACK)


def fig_libela(path):
    """Obr. 2 – určenie chyby alidádovej libely otočením alidády o 200 g."""
    W, H = 2000, 940
    im, d = new_img(W, H)
    vial(d, 120, 160, 760, 110, 0, "a) bublina urovnaná", BLUE)
    vial(d, 1100, 160, 760, 110, 2, "b) po otočení alidády o 200 gon", RED)
    # kóta 2e
    m = 1100 + 380
    y = 330
    d.line([(m, y), (m + 80, y)], fill=RED, width=5)
    arrowhead(d, (m + 40, y), (m + 80, y), RED)
    arrowhead(d, (m + 40, y), (m, y), RED)
    d.text((m + 10, y + 15), "2e", font=font(46, True), fill=RED)
    vial(d, 120, 600, 760, 110, 1, "c) polovica výchylky rektif. skrutkou", (0, 130, 60))
    vial(d, 1100, 600, 760, 110, 0, "d) druhá polovica stavacími skrutkami", BLUE)
    d.text((120, 860), "e – chyba alidádovej libely; otočením alidády o 200 gon sa chyba zdvojnásobí, "
                       "bublina sa vychýli o 2e", font=font(36), fill=BLACK)
    im.save(path)
    return W, H


def fig_kolimacia(path):
    """Obr. 3 – určenie kolimačnej chyby (dvojité preloženie ďalekohľadu na pravítko)."""
    W, H = 2000, 1000
    im, d = new_img(W, H)
    S = (760, 430)
    P = (110, 430)
    xr = 1650
    c = math.radians(7)
    # pravítko
    d.line([(xr, 120), (xr, 760)], fill=BLACK, width=12)
    for k in range(13):
        d.line([(xr, 150 + k * 50), (xr + 25, 150 + k * 50)], fill=BLACK, width=3)
    # zámery k P (odchýlené o c)
    for s in (1, -1):
        d.line([S, (P[0], S[1] - s * (S[0] - P[0]) * math.tan(c))], fill=GRAY, width=4)
    d.line([S, P], fill=BLACK, width=3)
    # na pravítko: smer 2c od predĺženia
    y0 = S[1]
    ya2 = y0 - (xr - S[0]) * math.tan(2 * c)
    ya1 = y0 + (xr - S[0]) * math.tan(2 * c)
    d.line([S, (xr, y0)], fill=BLACK, width=3)
    d.line([S, (xr, ya2)], fill=RED, width=5)
    d.line([S, (xr, ya1)], fill=BLUE, width=5)
    d.ellipse([S[0] - 16, S[1] - 16, S[0] + 16, S[1] + 16], fill="white", outline=BLACK, width=5)
    d.ellipse([P[0] - 14, P[1] - 14, P[0] + 14, P[1] + 14], fill=BLACK)
    f, fb = font(44), font(54, True)
    d.text((P[0] - 10, P[1] + 25), "P", font=fb, fill=BLACK)
    d.text((S[0] - 15, S[1] + 30), "S", font=fb, fill=BLACK)
    subtext(d, (xr + 40, ya2 - 30), "a", "2", 54, RED)
    subtext(d, (xr + 40, ya1 - 30), "a", "1", 54, BLUE)
    # l kóta
    d.line([(xr - 90, ya2), (xr - 90, ya1)], fill=BLACK, width=4)
    arrowhead(d, (xr - 90, y0), (xr - 90, ya2))
    arrowhead(d, (xr - 90, y0), (xr - 90, ya1))
    d.text((xr - 150, y0 - 30), "l", font=fb, fill=BLACK)
    d.text((S[0] + 260, y0 - 120), "2c", font=f, fill=RED)
    d.text((S[0] + 260, y0 + 60), "2c", font=f, fill=BLUE)
    d.text((S[0] + 470, y0 - 30), "4c", font=f, fill=BLACK)
    d.arc([S[0] - 440, S[1] - 440, S[0] + 440, S[1] + 440],
          -math.degrees(2 * c), math.degrees(2 * c), fill=BLACK, width=4)
    d.text((S[0] - 230, S[1] - 85), "c", font=f, fill=GRAY)
    d.text((S[0] - 230, S[1] + 30), "c", font=f, fill=GRAY)
    # d kóta
    d.line([(S[0], 820), (xr, 820)], fill=BLACK, width=4)
    arrowhead(d, ((S[0] + xr) / 2, 820), (S[0], 820))
    arrowhead(d, ((S[0] + xr) / 2, 820), (xr, 820))
    for x in (S[0], xr):
        d.line([(x, 790), (x, 850)], fill=BLACK, width=4)
    d.text(((S[0] + xr) / 2 - 15, 840), "d", font=fb, fill=BLACK)
    d.text((110, 910), "modrá – zámera po 1. preložení (čítanie a1), červená – po otočení o 200 gon "
                       "a 2. preložení (čítanie a2)", font=font(34), fill=BLACK)
    im.save(path)
    return W, H


def fig_hos(path):
    """Obr. 4 – určenie chyby horizontálnej osi (vysoký bod P a vodorovné pravítko)."""
    W, H = 2000, 1100
    im, d = new_img(W, H)
    # bočný pohľad
    g = 900
    d.line([(60, g), (1280, g)], fill=BLACK, width=5)
    T = (220, 640)
    for x in (140, 220, 300):
        d.line([(T[0], T[1] + 30), (x, g)], fill=BLACK, width=6)
    d.ellipse([T[0] - 45, T[1] - 45, T[0] + 45, T[1] + 45], outline=BLACK, width=6)
    P = (1080, 160)
    d.polygon([(1040, 230), (1080, 160), (1120, 230), (1120, g), (1040, g)], fill=BLACK)
    d.line([T, P], fill=GRAY, width=4)
    d.line([T, (880, T[1])], fill=GRAY, width=3)
    d.text((1060, 95), "P", font=font(54, True), fill=BLACK)
    # kóta h
    xh = 1200
    d.line([(xh, P[1]), (xh, T[1])], fill=BLACK, width=4)
    arrowhead(d, (xh, (P[1] + T[1]) / 2), (xh, P[1]))
    arrowhead(d, (xh, (P[1] + T[1]) / 2), (xh, T[1]))
    d.text((xh + 15, (P[1] + T[1]) / 2 - 30), "h", font=font(54, True), fill=BLACK)
    # pravítko vodorovne pred budovou vo výške horizontu prístroja
    d.rectangle([880, T[1] - 14, 1040, T[1] + 14], fill=(255, 200, 60), outline=BLACK, width=4)
    for xx in range(895, 1040, 20):
        d.line([(xx, T[1] - 14), (xx, T[1] + (2 if (xx - 895) % 40 else 6))], fill=BLACK, width=2)
    d.line([(860, T[1] + 90), (930, T[1] + 18)], fill=BLACK, width=3)
    d.text((700, T[1] + 85), "pravítko", font=font(40, True), fill=BLACK)
    d.text((80, 950), "a) bočný pohľad", font=font(40, True), fill=BLACK)
    # čelný pohľad
    Pt = (1650, 160)
    yb = 760
    d.rectangle([1380, yb - 12, 1920, yb + 12], fill=(255, 200, 60), outline=BLACK, width=4)
    d.text((1385, yb - 70), "pravítko", font=font(40, True), fill=BLACK)
    a1, a2 = (1560, yb), (1740, yb)
    d.line([Pt, a1], fill=BLUE, width=5)
    d.line([Pt, a2], fill=RED, width=5)
    dash(d, Pt, (1650, yb), BLACK, 4, (30, 14, 6, 14))
    d.ellipse([Pt[0] - 14, Pt[1] - 14, Pt[0] + 14, Pt[1] + 14], fill=BLACK)
    fb = font(50, True)
    d.text((Pt[0] - 15, Pt[1] - 80), "P", font=fb, fill=BLACK)
    subtext(d, (a1[0] - 45, yb + 20), "a", "1", 50, BLUE)
    subtext(d, (a2[0] - 5, yb + 20), "a", "2", 50, RED)
    d.line([(a1[0], yb + 110), (a2[0], yb + 110)], fill=BLACK, width=4)
    arrowhead(d, (1650, yb + 110), (a1[0], yb + 110))
    arrowhead(d, (1650, yb + 110), (a2[0], yb + 110))
    d.text((1635, yb + 120), "l", font=fb, fill=BLACK)
    d.text((1660, 430), "h", font=fb, fill=BLACK)
    d.text((1450, 950), "b) čelný pohľad", font=font(40, True), fill=BLACK)
    d.text((80, 1020), "modrá – sklopenie zámery z bodu P na pravítko v I. polohe (a1), "
                       "červená – v II. polohe (a2)", font=font(34), fill=BLACK)
    im.save(path)
    return W, H


# ---------------------------------------------------------------- obsah
def val(x, placeholder="doplniť"):
    return str(x) if x not in (None, "", []) else f"[[{placeholder}]]"


def report(data, res):
    lib = data["libela"]
    ins = data["pristroje"]
    mer = val(data.get("datum_merania"), "dátum merania")
    miesto = val(data.get("miesto_merania"), "miesto merania")
    names = " a ".join(i["nazov"] for i in ins)
    n = len(ins[0]["kolimacia"].get("a1") or [])
    n_txt = str(n) if n else "[[n]]"
    x = [para("Technická správa", bold=True, size=28, align="center", after=360)]

    x.append(heading("1  Definícia úlohy"))
    x.append(para(
        f"Cieľom úlohy bolo vykonať skúšku "
        f"správnosti osových podmienok teodolitu: určiť chybu alidádovej libely a rektifikovať ju "
        f"(prístroj {lib['pristroj']}), určiť kolimačnú chybu a chybu horizontálnej osi "
        f"(prístroje {names})."))
    x.append(para(
        "Teodolit má štyri geometrické osi (obr. 1): vertikálnu (točnú) os V, horizontálnu os H, "
        "zámernú os Z a os alidádovej libely L. Pre správne meranie uhlov musia byť splnené "
        "osové podmienky: os alidádovej libely je kolmá na vertikálnu os (L ⊥ V), zámerná os "
        "je kolmá na horizontálnu os (Z ⊥ H) a horizontálna os je kolmá na vertikálnu os (H ⊥ V). "
        "Nesplnenie podmienok spôsobuje chybu alidádovej libely, kolimačnú chybu c a chybu "
        "horizontálnej osi χ.", keep=True))
    x.append("__FIG1__")
    x.append(para("Obr. 1  Geometrické osi teodolitu", size=20, align="center", after=200))

    x.append(heading("2  Postup merania"))
    x.append(para(
        f"Meranie sme vykonali dňa {mer} ({miesto}). Použili sme optický teodolit {lib['pristroj']}"
        + ", " + " a ".join(
            ("optický teodolit " if "THEO" in i["nazov"] else "elektronickú totálnu stanicu ")
            + i["nazov"]
            for i in ins)
        + ", všetky na statíve. Prístroje sme postavili nad stanovisko a zhorizontovali rovnako ako "
        "v zadaní č. 1."))

    x.append(para("2.1  Chyba alidádovej libely", bold=True, before=120, keep=True))
    x.append(para(
        "Alidádu sme otočili tak, aby bola libela rovnobežná so spojnicou dvoch stavacích skrutiek, "
        "a týmito skrutkami sme bublinu urovnali do stredu. Potom sme alidádu otočili o 200^{g}. "
        "Ak os libely nie je kolmá na vertikálnu os, bublina sa vychýli o dvojnásobok chyby, "
        "teda o 2e (obr. 2). Polovicu výchylky sme odstránili rektifikačnou skrutkou libely a "
        "druhú polovicu stavacími skrutkami. Postup sme opakovali, kým bublina po otočení "
        "o 200^{g} zostala v strede, a nakoniec sme libelu otočili o 100^{g} a urovnali treťou "
        "stavacou skrutkou.", keep=True))
    x.append("__FIG2__")
    x.append(para("Obr. 2  Určenie a rektifikácia chyby alidádovej libely", size=20, align="center", after=200))

    x.append(para("2.2  Kolimačná chyba", bold=True, before=120, keep=True))
    x.append(para(
        "Vo vzdialenosti d od stanoviska S sme vodorovne a kolmo na zámeru upevnili pravítko "
        "s milimetrovým delením. Na opačnej strane sme zacielili na vzdialený bod P vo výške "
        "prístroja, ďalekohľad sme preložili a na pravítku odčítali a_{1}. Potom sme alidádu otočili "
        "o 200^{g}, znova zacielili na bod P, ďalekohľad preložili a odčítali a_{2} (obr. 3). "
        "Zámera sa pri každom preložení odkloní o 2c, takže úsek l medzi čítaniami zodpovedá "
        f"uhlu 4c. Meranie sme opakovali {n_txt}-krát.", keep=True))
    x.append("__FIG3__")
    x.append(para("Obr. 3  Určenie kolimačnej chyby", size=20, align="center", after=200))

    x.append(para("2.3  Chyba horizontálnej osi", bold=True, before=120, keep=True))
    x.append(para(
        "Zvolili sme bod P vysoko nad horizontom prístroja a pod ním vo výške horizontu prístroja "
        "sme vodorovne upevnili pravítko. V I. polohe ďalekohľadu sme zacielili na bod P, "
        "ďalekohľad sme sklopili na pravítko a odčítali a_{1}, v II. polohe sme postup zopakovali "
        "a odčítali a_{2} (obr. 4). Ak horizontálna os nie je kolmá na vertikálnu, zámera pri "
        "sklápaní neopisuje zvislú rovinu a čítania sa líšia o l. Výška h je prevýšenie bodu P "
        "nad pravítkom.", keep=True))
    x.append("__FIG4__")
    x.append(para("Obr. 4  Určenie chyby horizontálnej osi", size=20, align="center", after=200))

    x.append(heading("3  Postup riešenia úlohy"))
    x.append(para(
        "Chybu alidádovej libely sme určili ako polovicu výchylky bubliny po otočení alidády "
        "o 200^{g}:", keep=True))
    x.append(formula("e = v / 2", 1))
    x.append(para("kde v je výchylka bubliny v dielikoch libely.", after=160))
    x.append(para("Pri kolimačnej chybe a chybe horizontálnej osi sme pre každé meranie vypočítali "
                  "úsek na pravítku a jeho priemer z n meraní:", keep=True))
    x.append(formula("l_{j} = |a_{2,j} − a_{1,j}|,     l = Σ l_{j} / n", 2))
    x.append(para("Kolimačnú chybu sme vypočítali zo vzťahu:", keep=True))
    x.append(formula("c^{cc} = l / (4 · d) · ρ^{cc}", 3))
    x.append(para("a chybu horizontálnej osi zo vzťahu:", keep=True))
    x.append(formula("χ^{cc} = l / (2 · h) · ρ^{cc}", 4))
    x.append(para("kde ρ^{cc} = 636 620^{cc} a l, d, h dosadzujeme v rovnakých jednotkách (mm). "
                  "Namerané a vypočítané hodnoty sú vo výpočtovom protokole v prílohe A.1."))

    x.append(heading("4  Zhodnotenie výsledkov"))
    v0, v1 = lib.get("vychylka_pred_dieliky"), lib.get("vychylka_po_dieliky")
    if v0 is not None:
        e = Decimal(str(v0)) / 2
        x.append(para(
            f"Po otočení alidády o 200^{{g}} sa bublina libely prístroja {lib['pristroj']} vychýlila "
            f"o {comma(v0, 1)} dielika, chyba libely bola e = {comma(e, 1)} dielika. "
            + (f"Po rektifikácii bola výchylka {comma(v1, 1)} dielika." if v1 is not None
               else "[[výsledok po rektifikácii]]")))
    else:
        x.append(para(
            f"Alidádovú libelu prístroja {lib['pristroj']} sme rektifikovali postupom podľa časti 2.1, "
            "kým bublina po otočení alidády o 200^{g} nezostala v strede. Výchylky bubliny sme "
            "počas rektifikácie do zápisníka nezaznamenali, preto ich v protokole neuvádzame."))
    parts = []
    for i, r in zip(ins, res):
        c = f"c = {comma(r['c']['val'], 0)}^{{cc}}" if r["c"] else "c = [[doplniť]]"
        h = f"χ = {comma(r['i']['val'], 0)}^{{cc}}" if r["i"] else "χ = [[doplniť]]"
        parts.append(f"prístroj {i['nazov']}: {c}, {h}")
    x.append(para("Z meraní na pravítku sme určili tieto chyby: " + "; ".join(parts) + ". "
                  "Úseky l sú krátke (desatiny až jednotky milimetra) a čítanie na pravítku má "
                  "presnosť približne 0,5 mm, preto treba výsledky brať ako orientačné. Kolimačná "
                  "chyba aj chyba horizontálnej osi sa pri meraní vodorovných uhlov vylúčia meraním "
                  "v dvoch polohách ďalekohľadu."))
    x.append(para(f"V Bratislave, dňa {val(data.get('datum_spravy'), 'dátum')}", before=160, after=280, keep=True))
    x.append(para("Adam Molnar\t………………………………", tabs=[("left", 6000)], after=0, keep=True))
    x.append(para("\tpodpis", italic=True, size=18, tabs=[("left", 6800)]))
    return "".join(x)


def task_table(r, base_label, nrows=4):
    g = [800, 1500, 1500, 1500, 1500, 1500]
    rows = [[cell(t, w, bold=True) for t, w in zip(
        ("n", base_label, "a_{1} [mm]", "a_{2} [mm]", "l [mm]", "hodnota [cc]"), g)]]
    data_rows = r["rows"] if r else [None] * nrows
    for j, row in enumerate(data_rows, 1):
        if row:
            a1, a2, l, v = row
            vals = [str(j), comma(r["base"], 3) if j == 1 else "", comma(a1, 1), comma(a2, 1),
                    comma(l, 1), comma(v, 1)]
        else:
            vals = [str(j), "", "", "", "", ""]
        rows.append([cell(t, w) for t, w in zip(vals, g)])
    return rows, g


def protocol(data, res):
    x = [para("Výpočtový protokol", bold=True, size=28, align="center", after=240)]
    lib = data["libela"]
    YEL = "FFF2CC"
    tn = 0
    v0, v1 = lib.get("vychylka_pred_dieliky"), lib.get("vychylka_po_dieliky")
    if v0 is not None:
      tn = 1
      x.append(para(f"Tab. {tn}  Chyba alidádovej libely – {lib['pristroj']}", bold=True, before=120,
                  after=60, keep=True))
      g = [3400, 3000, 3000]
      rows = [[cell(t, w, bold=True) for t, w in zip(("", "výchylka v [dielik]", "chyba e = v / 2 [dielik]"), g)],
            [cell("pred rektifikáciou", g[0]), cell(comma(v0, 1) if v0 is not None else "", g[1]),
             cell(comma(Decimal(str(v0)) / 2, 1) if v0 is not None else "", g[2], shade=YEL)],
            [cell("po rektifikácii", g[0]), cell(comma(v1, 1) if v1 is not None else "", g[1]),
             cell(comma(Decimal(str(v1)) / 2, 1) if v1 is not None else "", g[2], shade=YEL)]]
      x.append(table(rows, g))
    for kind, title, base, sym, num in (("c", "Kolimačná chyba", "d [m]", "c", 3),
                                        ("i", "Chyba horizontálnej osi", "h [m]", "χ", 4)):
        for ins, r in zip(data["pristroje"], res):
            tn += 1
            rr = r[kind]
            x.append(para(f"Tab. {tn}  {title} – {ins['nazov']}", bold=True, before=140, after=40,
                          keep=True))
            rows, gg = task_table(rr, base)
            res_txt = (f"l = {comma(rr['l'], 3)} mm,   {sym}^{{cc}} = {comma(rr['val'], 0)}^{{cc}}"
                       if rr else f"l = [[ ]] mm,   {sym}^{{cc}} = [[ ]]")
            rows.append([cell("výsledok", sum(gg[:3]), bold=True, span=3,
                              align="right"),
                         cell(res_txt, sum(gg[3:]), bold=True, span=3, shade=YEL)])
            x.append(table(rows, gg))
            if rr:
                k = 4 if kind == "c" else 2
                bl = "d" if kind == "c" else "h"
                bmm = rr["base"] * 1000
                ls = " + ".join(comma(row[2], 1) for row in rr["rows"])
                x.append(para(f"Výpočet: l = ({ls}) / {len(rr['rows'])} = {comma(rr['l'], 3)} mm,   "
                              f"{bl} = {comma(bmm, 0)} mm", size=20, before=80, after=0, keep=True))
                x.append(para(f"{sym}^{{cc}} = {comma(rr['l'], 3)} / ({k} · {comma(bmm, 0)}) · 636 620 "
                              f"= {comma(rr['val'], 1)}^{{cc}} ≐ {comma(rr['val'], 0)}^{{cc}}",
                              size=20, after=0))
                x.append(para(
                    f"Rozbor presnosti: s_{{l}} = √(Σ(l_{{j}} − l)² / (n − 1)) = {comma(rr['sl'], 3)} mm,   "
                    f"s_{{l,priemer}} = s_{{l}} / √n = {comma(rr['slm'], 3)} mm,   "
                    f"s_{{{sym}}} = s_{{l,priemer}} / ({k} · {bl}) · ρ^{{cc}} = {comma(rr['sval'], 0)}^{{cc}}",
                    size=20, after=60))
    tn += 1
    x.append(para(f"Tab. {tn}  Prehľad výsledkov", bold=True, before=140, after=40, keep=True))
    g = [3000, 3200, 3200]
    rows = [[cell(t, w, bold=True) for t, w in zip(("Prístroj", "kolimačná chyba c", "chyba horizontálnej osi χ"), g)]]
    for ins, r in zip(data["pristroje"], res):
        rows.append([cell(ins["nazov"], g[0])] + [
            cell(f"{comma(r[k]['val'], 0)}^{{cc}} ± {comma(r[k]['sval'], 0)}^{{cc}}" if r[k] else "", w,
                 bold=True, shade=YEL) for k, w in (("c", g[1]), ("i", g[2]))])
    x.append(table(rows, g))
    x.append(para("V stĺpci „hodnota“ je chyba vypočítaná z jednotlivého merania; výsledná chyba je "
                  "vypočítaná z priemerného úseku l. Čítania teodolitu Zeiss THEO 020A pri kolimačnej chybe boli "
                  "zapísané v cm a sú prepočítané na mm.", size=18, italic=True, before=120))
    return "".join(x)


# ---------------------------------------------------------------- zostavenie


def add_image(rels, rid, name):
    return rels.replace("</Relationships>",
                        f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/'
                        f'officeDocument/2006/relationships/image" Target="media/{name}"/>'
                        "</Relationships>")


def build(data, pages="[[ ]]"):
    res = [{"c": compute(i["kolimacia"], "c"), "i": compute(i["horizontalna_os"], "i")}
           for i in data["pristroje"]]
    if BUILD.exists():
        shutil.rmtree(BUILD)
    with zipfile.ZipFile(TEMPLATE) as z:
        z.extractall(BUILD)
    doc = (BUILD / "word" / "document.xml").read_text(encoding="utf-8")
    spans = [(m.start(), m.end()) for m in re.finditer(r"<w:p[ >].*?</w:p>|<w:p [^>]*/>", doc, re.S)]

    def P(i):
        return doc[spans[i][0]:spans[i][1]]

    cover = doc[:spans[31][1]]
    repl = {5: "Zadanie č. 3", 6: "Osové podmienky teodolitu", 17: "OSOVÉ PODMIENKY TEODOLITU",
            21: str(pages), 23: "1", 25: data["zadane"], 27: data.get("odovzdane") or "[[ ]]"}
    for i, t in sorted(repl.items(), reverse=True):
        a, b = spans[i]
        newp = set_par_text(P(i), t.replace("[[ ]]", ""))
        if "[[" in t:
            newp = newp.replace("<w:rPr>", "<w:rPr>" + HL, 1)
        cover = cover[:a] + newp + cover[b:]

    media = BUILD / "word" / "media"
    for f in media.glob("*"):
        f.unlink()
    relp = BUILD / "word" / "_rels" / "document.xml.rels"
    rels = re.sub(r'<Relationship [^>]*Target="media/[^"]*"/>', "", relp.read_text(encoding="utf-8"))
    body = report(data, res)
    for k, (fn, wcm, title) in enumerate(FIGS, 1):
        W, H = fn(media / f"fig{k}.png")
        rels = add_image(rels, f"rIdFig{k}", f"fig{k}.png")
        cx = int(wcm * 360000)
        body = body.replace(f"__FIG{k}__", drawing(f"rIdFig{k}", cx, int(cx * H / W), k, f"fig{k}.png"))
    relp.write_text(rels, encoding="utf-8")

    prilohy = "".join(P(i) for i in range(49, 53))
    prilohy += para("Príloha A.1   Výpočtový protokol", after=60)
    last = doc[doc.rfind("<w:sectPr"):]
    new = cover + body + P(48) + prilohy + P(54) + protocol(data, res) + last
    (BUILD / "word" / "document.xml").write_text(new, encoding="utf-8")

    OUT.unlink(missing_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in BUILD.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(BUILD).as_posix())
    shutil.rmtree(BUILD)
    return res


FIGS = ((fig_axes, 10.5, "Geometrické osi teodolitu"),
        (fig_libela, 13.0, "Určenie a rektifikácia chyby alidádovej libely"),
        (fig_kolimacia, 14.5, "Určenie kolimačnej chyby"),
        (fig_hos, 13.5, "Určenie chyby horizontálnej osi"))


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    res = build(data)
    for i, r in zip(data["pristroje"], res):
        print(i["nazov"], {k: (comma(v["val"], 1) + " cc" if v else "chýba") for k, v in r.items()})
    if "--no-pdf" in sys.argv:
        print("DOCX:", OUT)
        return
    pdf = OUT.with_suffix(".pdf")
    pdf.unlink(missing_ok=True)  # aby chyba Wordu nenechala starý PDF
    z2.to_pdf(OUT, pdf)
    if not pdf.exists():
        sys.exit("Word nevytvoril PDF (pravdepodobne poškodený DOCX)")
    n = len(pymupdf.open(pdf))
    build(data, pages=n)
    z2.to_pdf(OUT, pdf)
    print("PDF:", pdf, f"({n} strán)")


if __name__ == "__main__":
    main()
