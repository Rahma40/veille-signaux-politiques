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