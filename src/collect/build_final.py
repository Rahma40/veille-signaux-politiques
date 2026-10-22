"""Assemble la base finale pour l'équipe : tes articles collectés + le fichier brut du coéquipier.

Usage (depuis la racine du projet) :
    python src\\collect\\build_final.py                                   (tes articles seulement)
    python src\\collect\\build_final.py data\\raw\\ami\\articles_semaine.csv   (+ fichier du coéquipier)

Entrées : data/raw/articles.csv (GDELT + RSS), articles_semaine.csv (fichier brut du coéquipier,
          converti ici au format commun : titre -> title, media -> source, etc.)
Sorties : data/processed/corpus_final.csv   (15 colonnes du schéma commun)
          data/processed/corpus.db          (SQLite, table « articles »)
          docs/corpus_final_report.md       (chiffres pour documenter le corpus)

Besoin dans le même dossier : collect_backfill.py et clean_corpus.py.
Aucun fichier d'entrée n'est modifié. Rien n'est supprimé : les doublons sont signalés dans duplicate_of.
"""
import csv
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from clean_corpus import find_duplicates, norm_date
from collect_backfill import END, START, article_id, load_existing, normalize_url

COLS = ["article_id", "title", "published_at", "source", "url", "text", "text_status",
        "fetched_at", "theme", "theme_score", "entities", "event_id", "sentiment",
        "is_relevant", "duplicate_of"]
OUT_CSV, OUT_DB = Path("data/processed/corpus_final.csv"), Path("data/processed/corpus.db")
REPORT = Path("docs/corpus_final_report.md")

# --- Réglages de qualité (modifiables) ---
# Fichier du coéquipier : le sujet « 17_octobre » parle surtout du massacre de 1961 (69 titres sur 72),
# pas des manifestations de 2026. On l'exclut. Mettre set() pour tout garder.
EXCLUDE_SUJETS = {"17_octobre"}
# Les articles publiés avant cette date sont écartés (les 47 articles GDELT du 21/09 sont isolés
# et souvent hors sujet). Mettre "" pour tout garder.
MIN_DATE = "2026-10-12"

# Un même média sous plusieurs noms (domaines RSS/GDELT, variantes d'écriture).
SOURCES = {
    "Franceinfo": "franceinfo", "francetvinfo.fr": "franceinfo", "Le Monde.fr": "Le Monde",
    "lemonde.fr": "Le Monde", "lefigaro.fr": "Le Figaro", "liberation.fr": "Libération",
    "leparisien.fr": "Le Parisien", "ouest-france.fr": "Ouest-France", "lepoint.fr": "Le Point",
    "rfi.fr": "RFI", "bfmtv.com": "BFM", "20minutes.fr": "20 Minutes", "lesechos.fr": "Les Echos",
    "humanite.fr": "L'Humanité", "publicsenat.fr": "Public Sénat", "la-croix.com": "La Croix",
    "huffingtonpost.fr": "Le HuffPost", "lejdd.fr": "Le JDD",
    "franceinfo.fr": "franceinfo",
}


def clean_source(s: str) -> str:
    s = s.strip()
    # certains noms sont des adresses complètes : https://www.exemple.fr/ -> exemple.fr
    s = re.sub(r"^https?://", "", s).rstrip("/")
    return SOURCES.get(s.removeprefix("www."), SOURCES.get(s, s))


def main(friend_csv: str = None) -> None:
    final, origin, src_of = {}, Counter(), {}

    # 1) Fichier brut du coéquipier (articles_semaine.csv), converti au format commun
    friend_rows = []
    if friend_csv:
        with open(friend_csv, encoding="utf-8-sig", newline="") as f:
            friend_rows = list(csv.DictReader(f))
    skipped_sujet = 0
    for r in friend_rows:
        url = r["url"].strip()
        if not url:
            continue
        if r.get("sujet", "") in EXCLUDE_SUJETS:
            skipped_sujet += 1
            continue
        aid = article_id(url)
        final[aid] = {
            "article_id": aid, "title": r["titre"], "published_at": r["published_at"],
            "source": r["media"], "url": normalize_url(url), "text": "",
            # lien Google News = redirection : le texte n'est pas récupérable
            "text_status": "empty" if "news.google.com" in url else "pending",
            "fetched_at": "", "theme": "", "theme_score": "", "entities": "",
            "event_id": "", "sentiment": r.get("sentiment", ""), "is_relevant": "",
            "duplicate_of": "",
        }
        src_of[aid] = "fichier du coéquipier"

    # 2) Tes articles collectés
    for aid, r in load_existing().items():
        if aid not in final:
            src_of[aid] = (r["collection_query"].split(":")[0] if r["collection_query"].startswith(("rss", "csv_ami"))
                           else f"GDELT ({r['collection_query']})")
        if aid in final:  # même article déjà présent : on complète le texte s'il manque
            if r["text"] and not final[aid]["text"]:
                final[aid].update(text=r["text"], text_status=r["text_status"], fetched_at=r["fetched_at"])
            continue
        final[aid] = {c: r.get(c, "") for c in COLS}

    rows = list(final.values())
    for r in rows:
        r["published_at"] = norm_date(r["published_at"])
        r["title"] = " ".join(r["title"].split())
        r["source"] = clean_source(r["source"])
    dup = find_duplicates(rows)
    for r in rows:
        r["duplicate_of"] = dup.get(r["article_id"], "")
    before = len(rows)
    if MIN_DATE:
        rows = [r for r in rows if r["published_at"][:10] >= MIN_DATE]
    skipped_date = before - len(rows)
    n_dup = sum(1 for r in rows if r["duplicate_of"])
    rows.sort(key=lambda r: r["published_at"])

    # Contrôles
    assert len({r["article_id"] for r in rows}) == len(rows), "article_id en double"

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)

    OUT_DB.unlink(missing_ok=True)
    con = sqlite3.connect(OUT_DB)
    con.execute("CREATE TABLE articles (" + ", ".join(
        f"{c} TEXT PRIMARY KEY" if c == "article_id" else f"{c} TEXT" for c in COLS) + ")")
    con.executemany(f"INSERT INTO articles VALUES ({','.join('?' * len(COLS))})",
                    [[r[c] for c in COLS] for r in rows])
    con.execute("CREATE INDEX idx_date ON articles(published_at)")
    con.commit()
    con.close()

    top = lambda c, n=10: "\n".join(f"- {k or '(vide)'} : {v}" for k, v in c.most_common(n))
    outside = sum(1 for r in rows if r["published_at"] and not
                  (START.isoformat() <= r["published_at"][:10] <= END.isoformat()))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"# Rapport du corpus final ({datetime.now(timezone.utc):%d/%m/%Y %H:%M} UTC)\n\n"
        f"- Articles : **{len(rows)}** | doublons de titre signalés : **{n_dup}**\n"
        f"- Écartés : {skipped_sujet} (sujet {sorted(EXCLUDE_SUJETS) or '-'} du fichier coéquipier) | "
        f"{skipped_date} publiés avant {MIN_DATE or '-'}\n"
        f"- Sans date : {sum(1 for r in rows if not r['published_at'])} | "
        f"hors période {START} à {END} : {outside}\n"
        f"- Sources différentes : {len({r['source'] for r in rows})}\n\n"
        f"## Origine des articles (après filtres)\n{top(Counter(src_of[r['article_id']] for r in rows))}\n\n"
        f"## Sources (10 premières)\n{top(Counter(r['source'] for r in rows))}\n\n"
        f"## Par jour\n" + "\n".join(f"- {d} : {c}" for d, c in
                                     sorted(Counter(r['published_at'][:10] for r in rows).items())) +
        f"\n\n## Statut du texte\n{top(Counter(r['text_status'] for r in rows))}\n",
        encoding="utf-8")
    print(f"{len(rows)} articles | {n_dup} doublons | {OUT_CSV} | {OUT_DB} | {REPORT}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)