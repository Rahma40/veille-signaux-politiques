"""Test et collecte de flux RSS de médias français, au même format que articles.csv.

Usage (depuis la racine du projet) :
    pip install feedparser
    python src\\collect\\collect_rss.py

Affiche un rapport par flux (marche / ne marche pas, nombre d'articles, dates),
puis ajoute les nouveaux articles à data/raw/articles.csv (sans doublons).
"""
import calendar
from datetime import datetime, timezone
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


def entry_date(e):
    t = e.get("published_parsed") or e.get("updated_parsed")
    if not t:
        return None
    return datetime.fromtimestamp(calendar.timegm(t), tz=timezone.utc)


def main() -> None:
    rows = load_existing()
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
    print(f"\nTotal ajoute : {total_new} | total dans articles.csv : {len(rows)}")


if __name__ == "__main__":
    main()