"""Réessaie les articles dont le téléchargement a échoué (text_status = error).

Usage (depuis la racine du projet) :
    python src\\collect\\retry_errors.py

Reprend les lignes « error » de data/raw/articles.csv et de data/raw/ami/resolved.csv.
Une simple requête avec une identité de navigateur classique, une fois par article, pas de contournement
de paywall ni de protection anti-robot. Libération (protégé, résumés RSS à la place) et la page
programme TV sont ignorés. Relançable. Ctrl + C possible : ce qui est fait est sauvegardé.
"""
import time

import requests
import trafilatura

import resolve_google_news as g
from collect_backfill import load_existing, save

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
    "Accept": "text/html,application/xhtml+xml",
}
SKIP = ("liberation.fr", "programmetv.")
PAUSE = 1.5


def fetch_browser(url: str):
    """(texte, statut) : ok > 800 caractères, partial sinon, empty si rien, error si la page est refusée."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return "", "error"
        text = trafilatura.extract(r.text)
        if not text:
            return "", "empty"
        return text, ("ok" if len(text) > 800 else "partial")
    except Exception:
        return "", "error"


def retry(items, get_url, apply):
    """items : liste de dict ; get_url(dict) -> adresse ; apply(dict, texte, statut)."""
    done = 0
    for i, it in enumerate(items, 1):
        url = get_url(it)
        if not url or any(s in url for s in SKIP):
            continue
        text, status = fetch_browser(url)
        if status in ("ok", "partial"):
            apply(it, text, status)
            done += 1
        time.sleep(PAUSE)
        if i % 10 == 0:
            print(f"  {i}/{len(items)} | récupérés : {done}")
    return done


def main() -> None:
    total = 0
    try:
        rows = load_existing()
        err = [r for r in rows.values() if r["text_status"] == "error"]
        print(f"{len(err)} erreurs dans articles.csv")
        total += retry(err, lambda r: r["url"], lambda r, t, s: r.update(text=t, text_status=s))
        save(rows)
        done = g.load_done()
        err = [d for d in done.values() if d["text_status"] == "error" and d["real_url"]]
        print(f"{len(err)} erreurs dans resolved.csv")
        total += retry(err, lambda d: d["real_url"], lambda d, t, s: d.update(text=t, text_status=s))
        g.save(done)
    except KeyboardInterrupt:
        print("Interrompu.")
    print(f"Terminé : {total} articles récupérés. Relance build_final.py pour les voir dans le jeu de données.")


if __name__ == "__main__":
    main()