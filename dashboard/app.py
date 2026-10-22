
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# =====================================
# CONFIGURATION
# =====================================

st.set_page_config(
    page_title="Veille des signaux politiques",
    page_icon="📊",
    layout="wide"
)

DATA_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "articles_simules.csv"
)


# =====================================
# CHARGEMENT DES DONNÉES
# =====================================

@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)

    data["published_at"] = pd.to_datetime(
        data["published_at"],
        errors="coerce"
    )

    data = data.dropna(subset=["published_at"])

    return data


if not DATA_PATH.exists():
    st.error("Le fichier articles_simules.csv est introuvable.")
    st.info("Lance : python dashboard/generate_data.py")
    st.stop()

df = load_data()

if df.empty:
    st.warning("Le fichier ne contient aucun article valide.")
    st.stop()


# =====================================
# TITRE
# =====================================

st.title("📊 Veille des signaux politiques")

st.caption(
    "Prototype É3 — Analyse de données simulées, "
    "non représentatives de l'actualité réelle."
)


# =====================================
# FILTRES INTERACTIFS
# =====================================

st.sidebar.header("🔎 Filtres")

themes_disponibles = sorted(
    df["theme"].dropna().unique().tolist()
)

medias_disponibles = sorted(
    df["source"].dropna().unique().tolist()
)

themes = st.sidebar.multiselect(
    "Thèmes politiques",
    options=themes_disponibles,
    default=themes_disponibles
)

medias = st.sidebar.multiselect(
    "Médias",
    options=medias_disponibles,
    default=medias_disponibles
)

date_min = df["published_at"].min().date()
date_max = df["published_at"].max().date()

periode = st.sidebar.date_input(
    "Période",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max
)

df_filtre = df[
    df["theme"].isin(themes)
    & df["source"].isin(medias)
].copy()

if len(periode) == 2:
    debut, fin = periode

    df_filtre = df_filtre[
        df_filtre["published_at"].dt.date.between(
            debut, fin
        )
    ]

elif len(periode) == 1:
    st.sidebar.info(
        "Sélectionne une date de fin pour appliquer "
        "le filtre de période."
    )


# =====================================
# VUE D'ENSEMBLE
# =====================================

st.header("Vue d'ensemble")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Articles",
    len(df_filtre)
)

col2.metric(
    "Médias",
    df_filtre["source"].nunique()
)

col3.metric(
    "Thèmes",
    df_filtre["theme"].nunique()
)

if df_filtre.empty:
    st.warning(
        "Aucun article ne correspond aux filtres sélectionnés."
    )
    st.stop()


# =====================================
# GRAPHIQUE 1 : ÉVOLUTION
# =====================================

st.subheader("📈 Évolution des publications")

evolution = (
    df_filtre.groupby(
        df_filtre["published_at"].dt.date
    )
    .size()
    .reset_index(name="articles")
)

fig1 = px.line(
    evolution,
    x="published_at",
    y="articles",
    markers=True,
    title="Nombre d'articles par jour",
    labels={
        "published_at": "Date",
        "articles": "Nombre d'articles"
    }
)

st.plotly_chart(
    fig1,
    use_container_width=True
)


# =====================================
# GRAPHIQUE 2 : THÈMES
# =====================================

st.subheader("📊 Thèmes les plus abordés")

top_themes = (
    df_filtre["theme"]
    .value_counts()
    .reset_index()
)

top_themes.columns = [
    "theme",
    "articles"
]

fig2 = px.bar(
    top_themes,
    x="theme",
    y="articles",
    title="Répartition des articles par thème",
    labels={
        "theme": "Thème politique",
        "articles": "Nombre d'articles"
    }
)

st.plotly_chart(
    fig2,
    use_container_width=True
)


# =====================================
# GRAPHIQUE 3 : ACTEURS
# =====================================

st.subheader("🏛️ Acteurs politiques les plus cités")

top_acteurs = (
    df_filtre["entities"]
    .dropna()
    .value_counts()
    .reset_index()
)

top_acteurs.columns = [
    "acteur",
    "articles"
]

fig3 = px.bar(
    top_acteurs,
    x="acteur",
    y="articles",
    title="Acteurs cités dans les articles",
    labels={
        "acteur": "Acteur politique",
        "articles": "Nombre d'articles"
    }
)

st.plotly_chart(
    fig3,
    use_container_width=True
)


# =====================================
# GRAPHIQUE 4 : MÉDIAS
# =====================================

st.subheader("📰 Couverture par média")

top_medias = (
    df_filtre["source"]
    .value_counts()
    .reset_index()
)

top_medias.columns = [
    "media",
    "articles"
]

fig4 = px.bar(
    top_medias,
    x="media",
    y="articles",
    title="Nombre d'articles par média",
    labels={
        "media": "Média",
        "articles": "Nombre d'articles"
    }
)

st.plotly_chart(
    fig4,
    use_container_width=True
)


# =====================================
# TABLEAU DES ARTICLES
# =====================================

st.subheader("📄 Articles sources")

st.dataframe(
    df_filtre[
        [
            "published_at",
            "title",
            "source",
            "theme",
            "entities"
        ]
    ].sort_values(
        "published_at",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)


# =====================================
# DÉTECTION DES SIGNAUX POLITIQUES
# =====================================

st.divider()

st.header("🚨 Détection des signaux politiques")

st.caption(
    "Analyse expérimentale sur données simulées."
)

# Date de référence : dernière date du corpus
date_reference = df["published_at"].max().normalize()

# Deux périodes de 7 jours
debut_recent = date_reference - pd.Timedelta(days=6)

debut_precedent = date_reference - pd.Timedelta(days=13)

fin_recent = date_reference + pd.Timedelta(days=1)

resultats = []

for theme in sorted(df_filtre["theme"].dropna().unique()):

    articles_theme = df_filtre[
        df_filtre["theme"] == theme
    ]

    # Période récente
    recent = articles_theme[
        (
            articles_theme["published_at"]
            >= debut_recent
        )
        & (
            articles_theme["published_at"]
            < fin_recent
        )
    ]

    # Période précédente
    precedent = articles_theme[
        (
            articles_theme["published_at"]
            >= debut_precedent
        )
        & (
            articles_theme["published_at"]
            < debut_recent
        )
    ]

    nb_recent = len(recent)
    nb_precedent = len(precedent)

    # Calcul de l'évolution
    if nb_precedent > 0:
        evolution_pct = (
            (nb_recent - nb_precedent)
            / nb_precedent
        ) * 100

    else:
        evolution_pct = None

    resultats.append({
        "Thème": theme,
        "Articles précédents": nb_precedent,
        "Articles récents": nb_recent,
        "Évolution (%)": evolution_pct,
        "Médias différents": recent["source"].nunique(),
        "Acteurs différents": recent["entities"].nunique()
    })


df_signaux = pd.DataFrame(resultats)

if df_signaux.empty:
    st.warning("Aucun signal disponible.")
    st.stop()


# =====================================
# SCORE DE SIGNAL POLITIQUE
# =====================================

def calculer_score(ligne):

    evolution = ligne["Évolution (%)"]
    medias = ligne["Médias différents"]
    acteurs = ligne["Acteurs différents"]
    nb_recent = ligne["Articles récents"]

    # Aucun article récent
    if nb_recent == 0:
        return 0.0

    # Couverture stable ou en diminution
    if pd.notna(evolution) and evolution <= 0:
        return 0.0

    # Accélération : 50 points maximum
    if pd.isna(evolution):
        score_evolution = 0
    else:
        score_evolution = min(
            evolution / 100 * 50,
            50
        )

    # Diversité des médias : 30 points maximum
    score_medias = min(
        medias / 5 * 30,
        30
    )

    # Acteurs politiques : 20 points maximum
    score_acteurs = min(
        acteurs / 2 * 20,
        20
    )

    score_total = (
        score_evolution
        + score_medias
        + score_acteurs
    )

    return round(score_total, 1)


df_signaux["Score signal"] = df_signaux.apply(
    calculer_score,
    axis=1
)


# =====================================
# NIVEAUX D'ALERTE
# =====================================

def niveau_alerte(score):

    if score >= 75:
        return "🔴 Signal fort"

    elif score >= 50:
        return "🟠 Signal modéré"

    else:
        return "🟢 Signal faible"


df_signaux["Niveau d'alerte"] = (
    df_signaux["Score signal"].apply(niveau_alerte)
)


# =====================================
# CLASSEMENT DES SIGNAUX
# =====================================

df_signaux = df_signaux.sort_values(
    by=["Score signal", "Évolution (%)"],
    ascending=[False, False],
    na_position="last"
)

st.subheader("Classement des thèmes à surveiller")

st.dataframe(
    df_signaux,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Évolution (%)": st.column_config.NumberColumn(
            "Évolution (%)",
            format="%.1f %%"
        ),
        "Score signal": st.column_config.NumberColumn(
            "Score signal",
            format="%.1f / 100"
        )
    }
)

st.info(
    "Une augmentation de la couverture médiatique "
    "ne constitue pas à elle seule un signal politique "
    "confirmé. Les événements et institutions doivent "
    "être vérifiés à partir des articles sources."
)


# =====================================
# GRAPHIQUE DES SCORES
# =====================================

st.subheader("📊 Intensité des signaux politiques")

fig_signaux = px.bar(
    df_signaux,
    x="Thème",
    y="Score signal",
    color="Score signal",
    color_continuous_scale="YlOrRd",
    range_y=[0, 100],
    title="Classement des signaux politiques (score / 100)",
    labels={
        "Thème": "Thème politique",
        "Score signal": "Score / 100"
    }
)

st.plotly_chart(
    fig_signaux,
    use_container_width=True
)

st.caption(
    "Score expérimental : accélération (50 points), "
    "diversité des médias (30 points), "
    "acteurs cités (20 points). "
    "Les seuils devront être évalués sur des données réelles."
)


# =====================================
# EXPLORATION DES SIGNAUX
# =====================================

st.divider()

st.header("🔎 Explorer un signal politique")

theme_selectionne = st.selectbox(
    "Choisissez un thème à analyser",
    options=df_signaux["Thème"].tolist()
)

articles_signal = df_filtre[
    df_filtre["theme"] == theme_selectionne
].copy()

infos_signal = df_signaux[
    df_signaux["Thème"] == theme_selectionne
].iloc[0]

st.subheader(
    f"Analyse du thème : {theme_selectionne}"
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Score du signal",
    f"{infos_signal['Score signal']}/100"
)

col2.metric(
    "Articles trouvés",
    len(articles_signal)
)

col3.metric(
    "Médias différents",
    articles_signal["source"].nunique()
)

# =====================================
# ARTICLES ASSOCIÉS AU SIGNAL
# =====================================

st.subheader("Articles associés au signal")

articles_affiches = articles_signal[
    [
        "published_at",
        "title",
        "source",
        "entities"
    ]
].sort_values(
    "published_at",
    ascending=False
)

st.dataframe(
    articles_affiches,
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Les articles présentés sont simulés. "
    "Les liens vers les véritables sources seront "
    "ajoutés lors de l'intégration des données É1 et É2."
)
