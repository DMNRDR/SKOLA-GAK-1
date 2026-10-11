"""Stiahne verejný Google Drive priečinok (rekurzívne) do lokálneho priečinka.
Preskočí súbory, ktoré už existujú.

Použitie:
    python tools/gdrive_download.py <folder_id> <cieľový_priečinok>
    python tools/gdrive_download.py 19DQgnZNHZ4kpNEp_3WzvzmsC2ULOSzLp ZS_2026-27/Matematika_1/Prednasky
"""
import html
import os
import re
import sys
import urllib.request


def ls(fid):
    url = f"https://drive.google.com/embeddedfolderview?id={fid}"
    h = urllib.request.urlopen(url, timeout=60).read().decode("utf-8")
    return [(html.unescape(t).strip(), u) for u, t in
            re.findall(r'<a href="([^"]+)"[^>]*>.*?flip-entry-title">([^<]*)<', h, re.S)]


def walk(fid, dest):
    os.makedirs(dest, exist_ok=True)
    for name, u in ls(fid):
        name = name.replace("/", "_")
        m = re.search(r"/folders/([\w-]+)", u)
        if m:
            walk(m.group(1), os.path.join(dest, name))
            continue
        m = re.search(r"/file/d/([\w-]+)", u) or re.search(r"id=([\w-]+)", u)
        if not m:
            print("?? preskočené:", name)
            continue
        out = os.path.join(dest, name)
        if os.path.exists(out):
            print("už je:", out)
            continue
        dl = f"https://drive.usercontent.google.com/download?id={m.group(1)}&export=download&confirm=t"
        with urllib.request.urlopen(dl, timeout=300) as r, open(out, "wb") as f:
            f.write(r.read())
        print("nové:", out, os.path.getsize(out), "B")


if __name__ == "__main__":
    walk(sys.argv[1], sys.argv[2])
