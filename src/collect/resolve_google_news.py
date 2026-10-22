"""Récupère le texte des articles du fichier du coéquipier.

Ses liens Google News (news.google.com/rss/articles/...) sont des redirections : on les
convertit d'abord en vraie adresse d'article, puis on télécharge la page avec trafilatura.
Les liens directs encore « pending » sont aussi téléchargés.

Usage (depuis la racine du projet) :
    pip install googlenewsdecoder trafilatura
    python src\\collect\\resolve_google_news.py data\\raw\\ami\\articles_semaine.csv

Sortie : data/raw/ami/resolved.csv (article_id, google_url, real_url, text, text_status, fetched_at)
Le fichier du coéquipier n'est pas modifié. build_final.py lit resolved.csv s'il existe.

- Durée : environ 5 secondes par article (une dizaine de minutes en tout).
- Relançable : les articles déjà récupérés (ok / partial) sont ignorés, les échecs sont réessayés.
- Ctrl + C possible à tout moment : ce qui est déjà fait est sauvegardé.
"""
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from build_final import EXCLUDE_SUJETS, MIN_DATE
from collect_backfill import article_id, normalize_url

OUT = Path("data/raw/ami/resolved.csv")
FIELDS = ["article_id", "google_url", "real_url", "text", "text_status", "fetched_at"]
PAUSE = 1.0  # secondes entre deux articles
LAST_ERROR = ""  # dernier message d'erreur du décodage, affiché pour comprendre un échec


UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
_decoder = None


def _get_decoder():
    """Un seul client réutilisé, avec un navigateur « classique » et les cookies de consentement
    (depuis l'Europe, Google redirige vers une page de consentement qui bloque le décodage)."""
    global _decoder
    if _decoder is None:
        from googlenewsdecoder import GoogleDecoder
        _decoder = GoogleDecoder(timeout=15, user_agent=UA)
        for name, value in (("CONSENT", "YES+cb"), ("SOCS", "CAI")):
            _decoder.client.cookies.set(name, value, domain=".google.com")
    return _decoder


def decode(url: str) -> str:
    """Adresse réelle d'un lien Google News, ou '' si le décodage échoue."""
    global LAST_ERROR
    fr_url = url + ("&" if "?" in url else "?") + "hl=fr&gl=FR&ceid=FR%3Afr"
    try:
        res = _get_decoder().decode_google_news_url(fr_url, interval=1)
    except Exception as e:
        LAST_ERROR = f"exception {type(e).__name__}: {e}"
        return ""
    if res.get("success") or res.get("status"):  # le nom de la clé dépend de la version
        real = res.get("decoded_url", "")
        if "news.google.com" in real:
            LAST_ERROR = "le résultat est encore un lien Google News"
            return ""
        return real
    LAST_ERROR = str(res.get("message", res))
    return ""


def fetch(url: str):
    """(texte, statut) comme dans collect_backfill.py : ok > 800 caractères, partial sinon."""
    import trafilatura
    try:
        html = trafilatura.fetch_url(url)
        if not html:
            return "", "error"
        text = trafilatura.extract(html)
        if not text:
            return "", "empty"
        return text, ("ok" if len(text) > 800 else "partial")
    except Exception:
        return "", "error"


def load_done() -> dict:
    if not OUT.exists():
        return {}
    with OUT.open(encoding="utf-8", newline="") as f:
        return {r["article_id"]: r for r in csv.DictReader(f)}


def save(done: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(done.values())


def main(friend_csv: str) -> None:
    csv.field_size_limit(10**9)
    with open(friend_csv, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f)
                if r["url"].strip() and r.get("sujet", "") not in EXCLUDE_SUJETS
                and (not MIN_DATE or r["published_at"][:10] >= MIN_DATE)]
    done = load_done()
    todo = [r for r in rows if done.get(article_id(r["url"]), {}).get("text_status") not in ("ok", "partial")]
    print(f"{len(rows)} articles du fichier | {len(rows) - len(todo)} déjà récupérés | {len(todo)} à traiter")
    n_decoded = 0
    try:
        for i, r in enumerate(todo, 1):
            url = r["url"].strip()
            aid = article_id(url)
            if "news.google.com" in url:
                real = decode(url)
                n_decoded += bool(real)
                if not real and i <= 3:
                    print("  décodage impossible :", LAST_ERROR[:300])
            else:
                real = normalize_url(url)
            text, status = fetch(real) if real else ("", "empty")
            done[aid] = {"article_id": aid, "google_url": url, "real_url": real, "text": text,
                         "text_status": status, "fetched_at": datetime.now(timezone.utc).isoformat()}
            if i % 10 == 0:
                save(done)
                n_txt = sum(1 for d in done.values() if d["text_status"] in ("ok", "partial"))
                print(f"  {i}/{len(todo)} | liens décodés : {n_decoded} | avec texte : {n_txt}")
            time.sleep(PAUSE)
    except KeyboardInterrupt:
        print("Interrompu : sauvegarde de ce qui est fait.")
    finally:
        save(done)
    mine = [done[article_id(r["url"])] for r in rows if article_id(r["url"]) in done]
    ok = sum(1 for d in mine if d["text_status"] in ("ok", "partial"))
    print(f"Terminé : {ok}/{len(rows)} avec texte | liens Google décodés cette fois : {n_decoded} | {OUT}")


if __name__ == "__main__":
    main(sys.argv[1]) if len(sys.argv) > 1 else print(__doc__)