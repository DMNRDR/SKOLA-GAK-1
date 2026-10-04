"""Stiahne nové materiály z dokumentového servera AIS STU do ZS_2026-27/.

Prihlasovacie údaje berie z ais_login.txt v koreni repa (1. riadok login, 2. heslo),
inak z premenných prostredia AIS_LOGIN a AIS_PASSWORD.
Použitie:
    python tools/ais_sync.py            # len vypíše, čo by stiahol
    python tools/ais_sync.py --download # naozaj stiahne nové súbory
"""
import hashlib
import html
import http.cookiejar
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://is.stuba.sk"
STUDIUM, OBDOBI = "210387", "739"
ROOT = Path(__file__).resolve().parent.parent / "ZS_2026-27"
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
opener.addheaders = [("User-Agent", "Mozilla/5.0 (ais_sync)")]


def get(url, data=None):
    if data is not None:
        data = urllib.parse.urlencode(data).encode()
    with opener.open(urllib.parse.urljoin(BASE, url), data, timeout=60) as r:
        return r.read(), r.headers


def text(url, data=None):
    body, headers = get(url, data)
    charset = headers.get_content_charset() or "utf-8"
    return body.decode(charset, "replace")


def slug(s):
    s = unicodedata.normalize("NFKD", html.unescape(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^\w.\-]+", "_", s.strip())
    return re.sub(r"_+", "_", s).strip("_")


def links(page):
    for href, label in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', page, re.S):
        yield html.unescape(href), re.sub(r"<[^>]+>", "", label).strip()


def credentials():
    """Najprv ais_login.txt v koreni repa (1. riadok login, 2. heslo), inak premenné prostredia."""
    for f in (ROOT.parent / "ais_login.txt", ROOT.parent / "ais_login.txt.txt"):
        if not f.is_file():
            continue
        lines = [l.strip() for l in f.read_text(encoding="utf-8-sig").splitlines() if l.strip()]
        # povolí aj tvar "ais_login=..." / "ais_password=..."
        lines = [l.split("=", 1)[1].strip() if re.match(r"(?i)ais_(login|password)\s*=", l) else l
                 for l in lines]
        if len(lines) >= 2:
            return lines[0], lines[1]
    return os.environ.get("AIS_LOGIN"), os.environ.get("AIS_PASSWORD")


def login():
    user, pw = credentials()
    if not user or not pw:
        sys.exit("Chýbajú údaje: vytvor ais_login.txt (1. riadok login, 2. heslo).")
    text("/system/login.pl")
    text("/system/login.pl", {
        "credential_0": user, "credential_1": pw, "credential_2": "86400",
        "login": "Prihlásiť sa", "destination": "/auth/", "lang": "sk",
    })
    if not any(c.name == "UISAuth" for c in jar):
        sys.exit("Prihlásenie zlyhalo (chýba cookie UISAuth).")


def courses():
    """Vráti {nazov_predmetu: url_dokumentoveho_servera}."""
    list_url = f"/auth/student/list.pl?studium={STUDIUM};obdobi={OBDOBI};lang=sk"
    page = text(list_url)
    found = {}
    for row in re.split(r"<tr", page):
        name = re.search(r'<a[^>]+href="[^"]*(?:predmet|syllabus)[^"]*"[^>]*>([^<]+)</a>', row)
        ds = re.search(r'href="([^"]*dok_server/slozka\.pl[^"]*)"', row)
        if name and ds:
            label = html.unescape(name.group(1)).replace("\xa0", " ").strip()
            found[label] = urllib.parse.urljoin(BASE + list_url, html.unescape(ds.group(1)))
    return found


def cells(row):
    return [html.unescape(re.sub(r"<[^>]+>", "", c)).replace("\xa0", " ").strip()
            for c in re.findall(r'<td class="odsazena" align="left">(.*?)</td>', row, re.S)]


def crawl(url, path=(), seen=None):
    """Prejde priečinky dokumentového servera, vracia (cesta_priecinkov, nazov, url_na_stiahnutie)."""
    seen = seen if seen is not None else set()
    folder_id = re.search(r"[;?]id=(\d+)", url).group(1)
    if folder_id in seen:
        return
    seen.add(folder_id)
    page = text(url)
    for row in re.split(r"<tr", page)[1:]:
        row = row.split("</tr>")[0]
        dl = re.search(r'href="([^"]*slozka\.pl\?id=\d+;download=\d+[^"]*)"', row)
        name = (cells(row) or [""])[0]
        if dl:
            yield path, name, urllib.parse.urljoin(url, html.unescape(dl.group(1)))
            continue
        sub = re.search(r'<a href="((?:\./)?slozka\.pl\?id=(\d+)[^"]*)"[^>]*>([^<]+)</a>', row)
        if sub and sub.group(2) != folder_id and "=" not in sub.group(1).split("id=")[0][-1:]:
            sub_name = html.unescape(sub.group(3)).strip()
            yield from crawl(urllib.parse.urljoin(url, html.unescape(sub.group(1))),
                             path + (sub_name,), seen)


def target_dir(course_dir, folders, fname):
    joined = (" ".join(folders) + " " + fname).lower()
    joined = unicodedata.normalize("NFKD", joined).encode("ascii", "ignore").decode()
    if re.search(r"\.(vgi|vyk)$", fname.lower()):
        return course_dir / "Data"
    m = re.search(r"priklad (\d+)\.\d+", joined)
    if m:  # Fyzika: príklad 2.3 -> Cvicenia/Cvicenie_2
        return course_dir / "Cvicenia" / f"Cvicenie_{m.group(1)}"
    for key, sub in [("sylab", "Skuska"), ("klasifik", "Skuska"), ("predn", "Prednasky"), ("prezent", "Prednasky"), ("cvic", "Cvicenia"),
                     ("zadan", "Zadania"), ("zapisnik", "Zadania"), ("pracovn", "Pracovne_listy"),
                     ("skusk", "Skuska"), ("podmien", "Skuska"), ("otazk", "Skuska")]:
        if key in joined and (sub != "Pracovne_listy" or (course_dir / sub).exists()):
            return course_dir / sub
    return course_dir / "Dokumenty"


def course_dir_for(name):
    # "B1-GD1 Geodézia 1" -> "Geodezia_1"
    return ROOT / slug(re.sub(r"^\S*\d\S*\s+", "", name))


def main():
    download = "--download" in sys.argv
    login()
    files = [p for p in ROOT.rglob("*") if p.is_file()]
    hashes = {hashlib.sha1(p.read_bytes()).hexdigest() for p in files}
    names = {p.name.lower() for p in files}
    cs = courses()
    if not cs:
        sys.exit("Nenašiel som žiadne predmety s dokumentovým serverom.")
    new = 0
    for name, url in cs.items():
        course_dir = course_dir_for(name)
        print(f"\n== {name} -> {course_dir.name}")
        for folders, label, href in crawl(url):
            body, headers = get(href)
            cd = headers.get("Content-Disposition", "")
            m = re.search(r"filename\*=(?:UTF-8'')?([^;]+)", cd) or re.search(r'filename="?([^";]+)', cd)
            fname = slug(urllib.parse.unquote(m.group(1)) if m else label)
            if hashlib.sha1(body).hexdigest() in hashes or fname.lower() in names:
                continue
            dest = target_dir(course_dir, folders, label + " " + fname)
            print(f"  NOVÝ: {'/'.join(folders) or '.'} / {label} [{fname}, {len(body)} B]"
                  f" -> {dest.relative_to(ROOT.parent)}")
            new += 1
            if download:
                dest.mkdir(parents=True, exist_ok=True)
                (dest / fname).write_bytes(body)
    print(f"\nNových súborov: {new}{'' if download else ' (nič neuložené, spusti s --download)'}")


if __name__ == "__main__":
    main()
