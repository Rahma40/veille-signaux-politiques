"""Backfill de la collecte d'articles via GDELT DOC 2.0, puis récupération du texte.

Usage :
    pip install requests trafilatura
    python collect_backfill.py urls    # étape 1 : métadonnées par jour (idempotent)
    python collect_backfill.py texts   # étape 2 : texte intégral

Relancer `urls` le 24/10 pour compléter jusqu'au 23/10 : les doublons sont ignorés.
"""
import csv
import hashlib
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

START = date(2026, 10, 12)
END = date(2026, 10, 23)
OUT = Path("data/raw/articles.csv")
FIELDS = ["article_id", "title", "published_at", "source", "url", "text",
          "text_status", "fetched_at", "language", "collection_query"]

# Mots-clés larges (institutions / textes / acteurs), pas des thèmes.
QUERY_GROUPS = {
    "institutions": '("Assemblée nationale" OR Sénat OR "Conseil des ministres" OR "Conseil constitutionnel")',
    "textes": '("projet de loi" OR "proposition de loi" OR PLF OR PLFSS OR amendement OR "motion de censure" OR 49.3)',
    "acteurs": '("groupe parlementaire" OR "premier ministre" OR ministre OR syndicat OR "partis politiques")',
    "budget": '(budget OR "retraites" OR "sécurité sociale" OR "loi de finances")',
}
API = "https://api.gdeltproject.org/api/v2/doc/doc"
TRACKING = ("utm_", "fbclid", "gclid", "xtor", "xtref", "at_")


def normalize_url(url: str) -> str:
    p = urlsplit(url.strip())
    q = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith(TRACKING)]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), urlencode(q), ""))


def article_id(url: str) -> str:
    return hashlib.sha1(normalize_url(url).encode()).hexdigest()


def load_existing() -> dict:
    if not OUT.exists():
        return {}
    with OUT.open(encoding="utf-8", newline="") as f:
        return {r["article_id"]: r for r in csv.DictReader(f)}


def save(rows: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows.values())


def gdelt_day(day: date, query: str) -> list:
    params = {
        "query": f"{query} sourcelang:french sourcecountry:france",
        "mode": "artlist", "format": "json", "maxrecords": 250, "sort": "datedesc",
        "startdatetime": day.strftime("%Y%m%d000000"),
        "enddatetime": day.strftime("%Y%m%d235959"),
    }
    for attempt in range(5):
        r = requests.get(API, params=params, timeout=60)
        if r.status_code == 200 and r.text.strip().startswith("{"):
            return r.json().get("articles", [])
        print("   réponse GDELT :", r.status_code, r.text[:150].replace("\n", " "))
        time.sleep(30 * (attempt + 1))  # 429 ou réponse vide : on attend
    print(f"  échec {day} / {query[:30]}")
    return []


def collect_urls() -> None:
    rows = load_existing()
    last = min(END, datetime.now(timezone.utc).date())
    day = START
    while day <= last:
        new = 0
        for name, q in QUERY_GROUPS.items():
            for a in gdelt_day(day, q):
                aid = article_id(a["url"])
                if aid in rows:
                    continue
                seen = datetime.strptime(a["seendate"], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                rows[aid] = {
                    "article_id": aid, "title": a.get("title", ""),
                    "published_at": seen.isoformat(),  # = date de vue par GDELT, approximation
                    "source": a.get("domain", ""), "url": normalize_url(a["url"]),
                    "text": "", "text_status": "pending",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "language": a.get("language", ""), "collection_query": name,
                }
                new += 1
            time.sleep(10)  # limite GDELT : 1 requête / 5 s
        print(f"{day} : +{new} (total {len(rows)})")
        save(rows)
        day += timedelta(days=1)


def fetch_texts() -> None:
    import trafilatura
    rows = load_existing()
    todo = [r for r in rows.values() if r["text_status"] == "pending"]
    print(f"{len(todo)} articles à récupérer")
    for i, r in enumerate(todo, 1):
        try:
            html = trafilatura.fetch_url(r["url"])
            text = trafilatura.extract(html) if html else None
            if not html:
                r["text_status"] = "error"
            elif not text:
                r["text_status"] = "empty"
            else:
                r["text"] = text
                r["text_status"] = "ok" if len(text) > 800 else "partial"
        except Exception:
            r["text_status"] = "error"
        if i % 50 == 0:
            save(rows)
            print(f"  {i}/{len(todo)}")
        time.sleep(1)
    save(rows)


if __name__ == "__main__":
    {"urls": collect_urls, "texts": fetch_texts}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
