"""Diagnostic : que répond Google quand on demande une page d'article ?

Usage : python src\\collect\\diag_google.py data\\raw\\ami\\articles_semaine.csv
Teste un seul lien, avec quatre variantes, et affiche le code HTTP, la redirection éventuelle,
et si la page contient les données dont le décodeur a besoin (data-n-a-sg).
"""
import csv
import sys

import httpx
from googlenewsdecoder._parse import article_id, params_page_url

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig", newline="")))
url = next(r["url"] for r in rows if "news.google.com" in r["url"])
aid = article_id(url)
FR = "&hl=fr&gl=FR&ceid=FR%3Afr"
for label, src, cookies in [
    ("standard", url, None),
    ("locale FR", url + FR, None),
    ("cookies consentement", url, {"CONSENT": "YES+cb", "SOCS": "CAI"}),
    ("locale FR + cookies", url + FR, {"CONSENT": "YES+cb", "SOCS": "CAI"}),
]:
    try:
        r = httpx.get(params_page_url(aid, src), follow_redirects=False, timeout=15,
                      headers={"User-Agent": UA}, cookies=cookies)
        print(f"{label:22} http {r.status_code} | redirection : {r.headers.get('location', '-')[:90]} "
              f"| données présentes : {'data-n-a-sg' in r.text}")
    except Exception as e:
        print(f"{label:22} erreur : {e}")