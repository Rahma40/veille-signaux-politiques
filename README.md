# Veille média France, octobre 2026

Projet de veille média en affaires publiques : repérer, dans la presse française, des signaux qui précèdent les arbitrages politiques et les positions parlementaires, et les présenter dans un tableau de bord interactif.

**Livraison : vendredi 23 octobre 2026, avant 17h00.**

## Contenu du dépôt

```
src/
  collect/      collecte et construction du jeu de données (É1)
  nlp/          extraction et classification (à compléter par É2)
  dashboard/    tableau de bord (à compléter par É3)
data/           données (non versionnées, voir plus bas)
docs/           rapports et documentation
```

## Installation

Python 3.9 ou plus récent.

```
pip install requests trafilatura feedparser
```

## Construire le jeu de données

Depuis la racine du projet, dans cet ordre :

```
python src\collect\collect_rss.py                                    # articles des flux RSS
python src\collect\collect_backfill.py texts                         # texte intégral des articles
python src\collect\build_final.py data\raw\ami\articles_semaine.csv  # assemblage, nettoyage, export
```

Sorties dans `data/processed/` :
- `corpus_final.csv` : le jeu de données (15 colonnes)
- `corpus.db` : les mêmes données dans une base SQLite (table `articles`)

Rapport de contrôle : `docs/corpus_final_report.md`.

Les données ne sont pas sur GitHub (dossier `data/` ignoré). Elles se partagent par le canal de l'équipe. Le fichier `data/raw/ami/articles_semaine.csv` est le fichier brut d'un coéquipier (recherches Google News sur le mouvement étudiant).

## Le jeu de données

**277 articles, du 12 au 22 octobre 2026, 50 sources.** Un article par ligne.

| Colonne | Contenu |
|---|---|
| `article_id` | SHA-1 de l'URL normalisée |
| `title`, `published_at` (UTC), `source`, `url` | remplies pour tous les articles |
| `text`, `text_status` | texte intégral si `ok` ou `partial` ; sinon `empty`, `error` ou `pending` |
| `fetched_at` | date de collecte (vide pour le fichier du coéquipier) |
| `sentiment` | uniquement pour les articles du coéquipier, méthode inconnue |
| `duplicate_of` | titre quasi identique un même jour (signalé, jamais supprimé) |
| `theme`, `theme_score`, `entities`, `event_id`, `is_relevant` | vides, remplies par le module NLP |

Détails complets : `LISEZMOI_corpus_final.md`.

### Sources et période

| Source | Articles | Période |
|---|---|---|
| Flux RSS : Le Monde, franceinfo, Le Figaro, Libération, Ouest-France, RFI | 163 | 19 au 22 oct. |
| Fichier d'un coéquipier, sujet « mouvement étudiant » | 114 | 12 au 20 oct. |

GDELT a été testé mais n'est pas utilisé : notre connexion a reçu l'erreur 429 (limite de requêtes). Les 47 articles du 21/09 qu'il avait fournis (jour isolé, souvent hors sujet) sont écartés. Le sujet « 17_octobre » du fichier du coéquipier est exclu : 69 de ses 72 titres parlent du massacre de 1961.

### Limites

- Les volumes par jour ne sont pas comparables entre le 12 et le 18/10 (un seul sujet) et à partir du 19/10 (flux RSS).
- Seuls 95 articles sur 277 ont du texte. Libération (50 articles) et Ouest-France bloquent le téléchargement : titres seulement. Les liens Google News (98) n'ont pas de texte.
- Les flux RSS ne gardent que les derniers articles : l'échantillon décrit la couverture de ces sources, pas toute la presse.
- Libération représente 18 % du corpus et peut dominer un classement par source.
- Certaines sources ne sont pas des médias (LDH, La France insoumise, L'Union Étudiante) ; Orange Actualités est probablement un agrégateur.

## Module NLP

À compléter par É2 : méthode de classification, liste des thèmes, extraction des entités, évaluation.

## Tableau de bord

À compléter par É3 : lancement, pages, indicateurs, définition du signal.

## Équipe

À compléter : noms et rôles (É1 collecte et jeu de données, É2 NLP, É3 tableau de bord).
