"""Nettoyage du corpus (rôle É1) : dates, doublons, hors-sujet, rapport.

Usage (depuis la racine du projet) :
    python src\\collect\\clean_corpus.py

Entrée  : data/raw/articles.csv (jamais modifié)
Sorties : data/interim/articles_clean.csv  (format commun + duplicate_of + is_relevant)
          docs/corpus_report.md            (chiffres pour documenter le corpus)

Rien n'est supprimé : les doublons et hors-sujet sont signalés, pas effacés.
Les noms duplicate_of / is_relevant sont ceux de la sortie NLP : prévenir É2
que ces colonnes sont pré-remplies par des règles simples.
"""
import csv
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from collect_backfill import END, FIELDS, START, load_existing

CLEAN = Path("data/interim/articles_clean.csv")
REPORT = Path("docs/corpus_report.md")

# Première liste de mots politiques : à compléter avec l'équipe.
POLITIQUE = re.compile(
    r"\b(?:gouvernement|minist\w*|assembl\w+|s[ée]nat\w*|d[ée]put\w*|parlement\w*|loi|lois|"
    r"budget\w*|plf\w*|49\.3|censure|[ée]lys[ée]e|matignon|macron|pr[ée]sident\w*|pr[ée]fet\w*|"
    r"lecornu|nu[ñn]ez|darmanin|parti|partis|lfi|rn|ps|insoumis\w*|socialiste\w*|"
    r"r[ée]publicains|[ée]cologistes|syndicat\w*|cgt|cfdt|intersyndicale|gr[èe]ve\w*|"
    r"mobilisation\w*|manifest\w*|r[ée]forme\w*|retraite\w*|imp[ôo]t\w*|fiscal\w*|"
    r"[ée]nergie|agricult\w*|sant[ée]|[ée]ducation|justice|blocus|bloqu\w*|lyc[ée]\w*|"
    r"[ée]tudiant\w*|universit\w*|polic\w*|interpell\w*|rassemblement\w*|cort[èe]ge\w*)\b",
    re.I,
)


def norm_date(s: str) -> str:
    try:
        d = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc).isoformat()
    except Exception:
        return ""


def title_tokens(t: str) -> set:
    t = re.sub(r"\s[-–|]\s(?:\S+\s?){1,3}$", lambda m: m.group(0) if len(m.group(0)) > 25 else "", t.strip())
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return set(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def find_duplicates(rows: list) -> dict:
    """Titres quasi identiques (>= 80 % de mots communs) le même jour."""
    by_day, dup = defaultdict(list), {}
    for r in sorted(rows, key=lambda r: r["published_at"]):
        toks = title_tokens(r["title"])
        for other_id, other in by_day[r["published_at"][:10]]:
            if len(toks) >= 4 and len(other) >= 4 and len(toks & other) / len(toks | other) >= 0.8:
                dup[r["article_id"]] = other_id
                break
        else:
            by_day[r["published_at"][:10]].append((r["article_id"], toks))
    return dup


def top(counter: Counter, n: int = 10) -> str:
    return "\n".join(f"- {k or '(vide)'} : {v}" for k, v in counter.most_common(n))


def main() -> None:
    rows = list(load_existing().values())
    for r in rows:
        r["published_at"] = norm_date(r["published_at"])
        r["title"] = " ".join(r["title"].split())
    dup = find_duplicates(rows)
    for r in rows:
        r["duplicate_of"] = dup.get(r["article_id"], "")
        r["is_relevant"] = int(bool(POLITIQUE.search(f"{r['title']} {r['text'][:2000]}")))

    CLEAN.parent.mkdir(parents=True, exist_ok=True)
    with CLEAN.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS + ["duplicate_of", "is_relevant"])
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    no_date = sum(1 for r in rows if not r["published_at"])
    no_title = sum(1 for r in rows if not r["title"])
    outside = sum(1 for r in rows if r["published_at"] and not
                  (START.isoformat() <= r["published_at"][:10] <= END.isoformat()))
    uniq = [r for r in rows if not r["duplicate_of"]]
    off = sum(1 for r in uniq if not r["is_relevant"])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"# Rapport du corpus ({datetime.now(timezone.utc):%d/%m/%Y %H:%M} UTC)\n\n"
        f"- Articles dans la base brute : **{n}**\n"
        f"- Doublons de titre signalés : **{len(dup)}** | articles uniques : **{len(uniq)}**\n"
        f"- Hors sujet (règle de mots-clés, parmi les uniques) : **{off}**\n"
        f"- Sans date : {no_date} | sans titre : {no_title} | hors période {START} à {END} : {outside}\n\n"
        f"## Par source (10 premières)\n{top(Counter(r['source'] for r in rows))}\n\n"
        f"## Par jour\n" + "\n".join(f"- {d} : {c}" for d, c in sorted(Counter(r['published_at'][:10] for r in rows).items())) +
        f"\n\n## Par statut du texte\n{top(Counter(r['text_status'] for r in rows))}\n\n"
        f"## Par origine de collecte\n{top(Counter(r['collection_query'] for r in rows))}\n",
        encoding="utf-8",
    )
    print(f"{n} articles | {len(dup)} doublons | {off} hors sujet | rapport : {REPORT}")


if __name__ == "__main__":
    main()