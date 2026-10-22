
from pathlib import Path
import random
import pandas as pd

random.seed(42)

# Dossier où enregistrer les données
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Données fictives pour tester le dashboard
themes = {
    "Budget": ["Assemblée nationale", "Gouvernement"],
    "Retraites": ["Sénat", "Syndicats"],
    "Énergie": ["Ministère de l'Énergie", "Gouvernement"],
    "Santé": ["Ministère de la Santé", "Assemblée nationale"],
    "Agriculture": ["Ministère de l'Agriculture", "Syndicats"],
}

medias = [
    "Le Monde",
    "Le Figaro",
    "Franceinfo",
    "Libération",
    "Les Échos",
]

articles = []

for i in range(300):
    theme = random.choice(list(themes))
    acteur = random.choice(themes[theme])
    media = random.choice(medias)

    date = random.choice(
        pd.date_range("2026-09-21", "2026-10-22")
    )

    articles.append({
        "article_id": f"sim_{i+1:04d}",
        "title": f"Article fictif sur {theme} - {i+1}",
        "published_at": date,
        "source": media,
        "url": "",
        "text": f"Contenu fictif concernant {theme}.",
        "theme": theme,
        "theme_score": round(random.uniform(0.6, 1.0), 2),
        "entities": acteur,
        "event_id": f"event_{theme.lower()}",
        "sentiment": random.choice(
            ["positif", "neutre", "négatif"]
        ),
        "is_relevant": True,
        "duplicate_of": "",
    })

df = pd.DataFrame(articles)

output = DATA_DIR / "articles_simules.csv"
df.to_csv(output, index=False, encoding="utf-8-sig")

print(f"{len(df)} articles simulés générés.")
print(f"Fichier créé : {output}")
