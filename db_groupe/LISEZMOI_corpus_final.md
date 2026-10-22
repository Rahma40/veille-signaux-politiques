# corpus_final.csv / corpus.db

**277 articles, du 12/10/2026 au 22/10/2026, environ 50 sources.** Un article par ligne, `article_id` unique (SHA-1 de l'URL normalisée). Le CSV et la base SQLite (`corpus.db`, table `articles`) contiennent exactement les mêmes lignes.

## D'où viennent les articles
| Origine | Articles | Période | Méthode |
|---|---|---|---|
| Flux RSS (Le Monde, franceinfo, Le Figaro, Libération, Ouest-France, RFI, rubriques politique/une) | 163 | 19 au 22 oct. | `collect_rss.py` + texte récupéré avec `trafilatura` |
| Fichier d'un coéquipier, sujet « mouvement étudiant » (blocus lycées/universités) | 114 | 12 au 20 oct. | Recherches Google News faites par le coéquipier (titres seulement) |

Écartés volontairement : les 72 articles du sujet « 17_octobre » du coéquipier (69 parlent du massacre de **1961**, pas des manifestations de 2026) et 47 articles GDELT du 21/09 (jour isolé, souvent hors sujet, titres abîmés). GDELT a bloqué notre connexion (erreur 429), il n'est donc pas une source du corpus.

## Colonnes
| Colonne | Contenu |
|---|---|
| `article_id`, `title`, `published_at` (UTC), `source`, `url` | remplies pour les 277 articles |
| `text` | texte intégral, uniquement quand `text_status` vaut `ok` ou `partial` |
| `text_status` | `ok` 68, `partial` 27 (souvent un article payant tronqué), `error` 68 (Libération et Ouest-France bloquent le téléchargement), `empty` 98 (liens Google News, texte non récupérable), `pending` 16 (jamais essayé) |
| `fetched_at` | date de collecte, **vide pour les 114 articles du coéquipier** |
| `sentiment` | positif / neutre / négatif, **seulement pour les 114 articles du coéquipier**, méthode inconnue : ne pas s'y fier |
| `duplicate_of` | 1 article signalé (titres quasi identiques le même jour). Rien n'est supprimé : à exclure des comptages |
| `theme`, `theme_score`, `entities`, `event_id`, `is_relevant` | **vides, volontairement** : à remplir par le module NLP |

## À savoir avant de faire des graphiques
- **Utilisez `title`, `published_at` et `source` pour tous les articles.** N'utilisez `text` que si `text_status` est `ok` ou `partial`.
- **Les volumes par jour ne sont pas comparables d'un bout à l'autre.** Du 12 au 18 oct. on a un seul sujet (mouvement étudiant, recherches du coéquipier) ; à partir du 19 oct. on a les flux RSS (20 à 50 derniers articles par flux). Une hausse le 19 oct. vient en partie du changement de méthode. Le 22 oct. est une journée incomplète.
- **Libération = 50 articles, tous sans texte** (titres seulement).
- **Sources qui ne sont pas des médias** : LDH, La France insoumise, L'Union Étudiante, une page programme TV (`programmetv.ouest-france.fr`). Orange Actualités (17 articles) est probablement un agrégateur. À exclure d'un indicateur « diversité des médias ».
- **Le corpus est un échantillon**, pas la totalité de la presse : les flux RSS ne gardent que les derniers articles. Les tendances décrivent la couverture de ces sources, pas l'ensemble de l'actualité.
- Un article de Le Monde parle encore de « 17 octobre 1961 » : il est resté car il vient de nos flux RSS.

## Reconstruire le fichier
```
python src\collect\collect_rss.py
python src\collect\collect_backfill.py texts
python src\collect\build_final.py data\raw\ami\articles_semaine.csv
```
Réglages dans `build_final.py` : `MIN_DATE` (date de début) et `EXCLUDE_SUJETS`.
