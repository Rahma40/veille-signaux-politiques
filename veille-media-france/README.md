# veille-signaux-politiques
veille-media-france/
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── config/
│   ├── settings.yaml          # période, requêtes GDELT, flux RSS, chemins
│   ├── themes.yaml            # grille de thèmes + mots-clés
│   └── actors.yaml            # partis, syndicats, ministères, alias
├── data/
│   ├── raw/                   # données brutes (non versionné)
│   ├── interim/               # après nettoyage (non versionné)
│   ├── processed/             # après NLP (non versionné)
│   ├── annotation/            # échantillon annoté (versionné)
│   └── sample/                # petit jeu d'exemple (versionné)
├── src/
│   └── veille/
│       ├── __init__.py
│       ├── collect/           # É1
│       │   ├── gdelt.py
│       │   ├── rss.py
│       │   └── fulltext.py    # trafilatura
│       ├── clean/             # É1
│       │   ├── dedup.py
│       │   ├── normalize.py
│       │   └── relevance.py
│       ├── nlp/               # É2
│       │   ├── themes.py
│       │   ├── entities.py
│       │   ├── events.py
│       │   ├── sentiment.py
│       │   └── topics.py      # bonus BERTopic
│       ├── analysis/          # É3
│       │   ├── indicators.py
│       │   └── signals.py
│       ├── db.py              # connexion + schéma SQLite/DuckDB
│       ├── schema.py          # contrat de données partagé
│       └── logging_conf.py
├── dashboard/                 # É3
│   ├── app.py
│   ├── pages/
│   │   ├── 1_vue_ensemble.py
│   │   ├── 2_themes.py
│   │   ├── 3_acteurs.py
│   │   ├── 4_signaux.py
│   │   └── 5_articles.py
│   └── components/
├── scripts/
│   ├── run_pipeline.py        # point d'entrée unique
│   └── make_sample.py         # génère le jeu simulé
├── notebooks/                 # exploration (un sous-dossier par personne)
├── tests/
│   ├── test_collect.py
│   ├── test_clean.py
│   ├── test_nlp.py
│   └── test_schema.py
├── evaluation/
│   ├── evaluate_nlp.py
│   └── results/
├── docs/
│   ├── corpus.md              # sources, période, nombre, limites
│   ├── architecture.md
│   ├── data_contract.md
│   ├── report/                # rapport final
│   └── slides/
└── logs/                      # non versionné
# veille-signaux-politiques — veille-media-france

Dépôt de travail du rôle **É2 (NLP)** : repérage exploratoire de thèmes par embeddings, extraction d'entités, regroupement indicatif par événement, sentiment lexical et évaluation manuelle.

## Lancer

1. Créer un environnement Python 3.10 ou plus récent et installer `pip install -r requirements.txt`.
2. Copier le fichier `corpus_final.csv` reçu dans `data/raw/corpus_final.csv` (il n'est pas versionné).
3. Ouvrir `notebooks/etudiant_2/02_analyse_nlp_embeddings.ipynb` et exécuter les cellules dans l'ordre. Le modèle pré-entraîné est téléchargé au premier lancement.
4. Pour le NER, installer le modèle français : `python -m spacy download fr_core_news_md`. Sans ce modèle, le notebook prévient et poursuit sans NER statistique.
5. Ajouter les annotations à `data/annotation/annotations.csv` en suivant `annotations_template.csv` pour produire les métriques comparables.

## Méthode et choix

Les embeddings Sentence Transformers servent à explorer la proximité sémantique, sans données annotées. Le clustering hiérarchique à seuil laisse émerger un nombre de groupes guidé par la distance ; leurs noms doivent être relus et validés humainement. Une grille de mots-clés transparente fournit une baseline de thèmes. Les entités s'appuient sur spaCy et des alias. Le regroupement d'événements combine similarité, fenêtre temporelle de trois jours et entités communes. Le sentiment lexical est une démonstration basique, pas une mesure fiable de l'opinion.

Le fichier source indique 277 articles du 12 au 22 octobre 2026. Les textes intégraux sont inégalement disponibles ; le notebook combine titre et texte seulement pour les statuts `ok`/`partial`. Les volumes par jour sont biaisés par le changement de méthode de collecte à partir du 19 octobre et par la journée incomplète du 22. La colonne sentiment d'origine est ignorée car sa méthode est inconnue et elle ne couvre qu'un sous-ensemble.

## Structure

Le dossier reprend la structure prévue du dépôt GitHub. Les données brutes, intermédiaires et résultats ne sont pas versionnés. Ce livrable se concentre sur le périmètre étudiant 2.
