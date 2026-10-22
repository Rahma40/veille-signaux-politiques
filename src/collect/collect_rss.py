"""Test et collecte de flux RSS de médias français, au même format que articles.csv.

Usage (depuis la racine du projet) :
    pip install feedparser
    python src\\collect\\collect_rss.py

Affiche un rapport par flux (marche / ne marche pas, nombre d'articles, dates),
puis ajoute les nouveaux articles à data/raw/articles.csv (sans doublons).
"""
import calendar
import csv
import html
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import feedparser

from collect_backfill import START, article_id, load_existing, normalize_url, save

# Adresses à vérifier : les médias changent parfois leurs flux.
# Le rapport dira lesquels répondent. Remplacez ou ajoutez-en si besoin.
FEEDS = {
    "lemonde": "https://www.lemonde.fr/politique/rss_full.xml",
    "francetvinfo": "https://www.francetvinfo.fr/politique.rss",
    "lefigaro": "https://www.lefigaro.fr/rss/figaro_politique.xml",
    "liberation": "https://www.liberation.fr/arc/outboundfeeds/rss-all/category/politique/?outputType=xml",
    "leparisien": "https://www.leparisien.fr/arc/outboundfeeds/rss/category/politique/?outputType=xml",
    "ouestfrance": "https://www.ouest-france.fr/rss/une",
    "lepoint": "https://www.lepoint.fr/politique/rss.xml",
    "rfi": "https://www.rfi.fr/fr/france/rss",
}
AGENT = "Mozilla/5.0 (projet etudiant, veille politique)"
SUMMARIES = Path("data/raw/rss_summaries.csv")  # résumé publié par le flux (utile si le texte est bloqué)


def entry_summary(e) -> str:
    """Résumé fourni par le flux (sans HTML), ou '' s'il est trop court ou répète le titre."""
    raw = e.get("summary") or ""
    for c in e.get("content") or []:
        if len(c.get("value", "")) > len(raw):
            raw = c["value"]
    s = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())
    return s if len(s) >= 60 and len(s) > len(e.get("title", "")) + 20 else ""


def load_summaries() -> dict:
    if not SUMMARIES.exists():
        return {}
    with SUMMARIES.open(encoding="utf-8", newline="") as f:
        return {r["article_id"]: r["summary"] for r in csv.DictReader(f)}


def save_summaries(summaries: dict) -> None:
    SUMMARIES.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARIES.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["article_id", "summary"])
        w.writerows(summaries.items())


def entry_date(e):
    t = e.get("published_parsed") or e.get("updated_parsed")
    if not t:
        return None
    return datetime.fromtimestamp(calendar.timegm(t), tz=timezone.utc)


def main() -> None:
    rows = load_existing()
    summaries = load_summaries()
    start = datetime(START.year, START.month, START.day, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc).isoformat()
    print(f"{'flux':14} {'etat':8} {'articles':>8}  plus ancien -> plus recent")
    total_new = 0
    for name, url in FEEDS.items():
        try:
            feed = feedparser.parse(url, agent=AGENT)
        except Exception as ex:
            print(f"{name:14} ERREUR    {ex}")
            continue
        entries = feed.entries
        status = getattr(feed, "status", "?")
        if not entries:
            print(f"{name:14} {'vide/KO':8} {0:>8}  (http {status})")
            continue
        dates = [d for d in (entry_date(e) for e in entries) if d]
        span = f"{min(dates):%d/%m} -> {max(dates):%d/%m}" if dates else "dates inconnues"
        new = 0
        for e in entries:
            link = e.get("link")
            d = entry_date(e)
            if not link or (d and d < start):
                continue
            aid = article_id(link)
            summ = entry_summary(e)
            if summ:
                summaries[aid] = summ
            if aid in rows:
                continue
            rows[aid] = {
                "article_id": aid, "title": e.get("title", ""),
                "published_at": d.isoformat() if d else "",
                "source": urlsplit(link).netloc, "url": normalize_url(link),
                "text": "", "text_status": "pending", "fetched_at": now,
                "language": "fr", "collection_query": f"rss:{name}",
            }
            new += 1
        total_new += new
        print(f"{name:14} {'OK':8} {len(entries):>8}  {span}  (+{new} nouveaux)")
    save(rows)
    save_summaries(summaries)
    print(f"Résumés de flux enregistrés : {len(summaries)} ({SUMMARIES})")
    print(f"\nTotal ajoute : {total_new} | total dans articles.csv : {len(rows)}")


if __name__ == "__main__":
    main()