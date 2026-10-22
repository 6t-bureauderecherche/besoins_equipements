"""Web app : besoins en équipements publics à l'horizon 2050 (chemin inverse).

Lancer en local :  streamlit run app.py
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from calculs import (
    CLASSES,
    calculer,
    charger_donnees,
    reglages_vides,
    synthese_par_classe,
)

# ---------------------------------------------------------------- palette 6t-2023
MARINE = "#060D53"   # Dark 2 : texte, titres
VIOLET = "#6246D3"   # Light 2 : variante, couleur principale
CORAIL = "#FF717C"   # Accent 1 : hausse
ORANGE = "#FF9433"   # Accent 2 : niveaux ajoutés, répartition
JAUNE = "#F9B421"    # Accent 3
TEAL = "#2A9C8E"     # Accent 4 : baisse
AQUA = "#7FD3CF"     # Accent 5 : référence future
BEIGE = "#EEECE1"    # Accent 6 : aujourd'hui, fonds doux
# ---------------------------------------------------------------- polices (charte 6t, modèle PowerPoint 2023)
# Titres : Brandon Grotesque Bold ; texte : Inter ; pied de page : Sofia Pro Medium.
# Si Brandon Grotesque n'est pas installé sur le poste du lecteur, Montserrat prend le relais.
POLICE = 'Inter, "Helvetica Neue", Arial, sans-serif'
TITRES = '"6tTitre", Montserrat, "Helvetica Neue", Arial, sans-serif'
# ================================================================ TEXTES MODIFIABLES
# Modifiez ici les noms des blocs, des sous-titres et des onglets : le reste du script n'a pas à changer.
TEXTES = {
    # en-tête de la page
    "titre_page": "Besoins en équipements publics à l'horizon 2050",
    "sous_titre_page": "Estimation des besoins en surface d'équipements publics selon la variation du ratio d'équipement (m2/hab).",
    #"tag_page": "Données provisoires · à valider",
    # onglets
    "onglet_1": "Equipements",
    "onglet_2": "Vue d'ensemble",
    "onglet_3": "Données et méthode",
    # menu déroulant
    "menu_equipement": "Choisissez un équipement ",
    # blocs de la page « Par équipement » : (titre, texte d'aide à droite du titre)
    "bloc_1": ("Situation de référence"),
    "bloc_2": ("Ajuster le ratio d'équipements", "le besoin brut est recalculé sur la même population future"),
    "bloc_3": ("Résultat", "Variation du besoin brut en surface (ha équiv. SBP) par rapport à la référence"),
    "bloc_4": ("Répartir le besoin brut", "Emprise de bâtiments à future selon le nombre de niveaux de bâtiments)"),
    # sous-titres du bloc 4
    "bloc_4_niveaux": "Niveaux supplémentaires des bâtiments",
    "bloc_4_batiments": "Hauteur des bâtiments",
    "bloc_4_carres": "Résultat : Emprise de bâtiments (m²)",
    "bloc_4_tableau": "Résultat : SBP, SBP de surfaces annexes, emprise et sol total",
}

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
LOGO = Path(__file__).resolve().parent / "assets" / "logo_6t.png"
LOGO_B64 = base64.b64encode(LOGO.read_bytes()).decode() if LOGO.exists() else ""

st.set_page_config(
    page_title="Besoins en équipements publics 2050",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Montserrat:wght@600;700&display=swap" rel="stylesheet">
<style>
  @font-face { font-family: "6tTitre"; font-weight: 700; font-style: normal;
               src: local("Brandon Grotesque Bold"), local("BrandonGrotesque-Bold"); }
  @font-face { font-family: "6tTitre"; font-weight: 400; font-style: normal;
               src: local("Brandon Grotesque Regular"), local("BrandonGrotesque-Regular"); }
  html, body, [class*="css"], .stMarkdown, button, input { font-family: @POLICE !important; }
  [data-testid="stMarkdownContainer"] :is(p, li, .c-sub, .etape .a, .pill, table.sbp,
  .c-val small) { font-family: @POLICE !important; }
  h1, h2, h3, [data-testid="stHeadingWithActionElements"] *, .stTabs [data-baseweb="tab"],
  [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
  [data-testid="stMarkdownContainer"] h3 { font-family: @TITRES !important; font-weight: 700 !important; }
  [data-testid="stToolbar"], #MainMenu, footer, [data-testid="stSidebar"],
  [data-testid="collapsedControl"] { display: none !important; }
  .block-container { padding-top: 1.6rem; max-width: 1480px; }

  .stApp { background: #F8F8FF; }
  .zone { display: none; }
  [data-testid="stVerticalBlock"]:has(.z1):not(:has([data-testid="stVerticalBlock"] .z1)),
  [data-testid="stVerticalBlock"]:has(.z2):not(:has([data-testid="stVerticalBlock"] .z2)),
  [data-testid="stVerticalBlock"]:has(.z3):not(:has([data-testid="stVerticalBlock"] .z3)),
  [data-testid="stVerticalBlock"]:has(.z4):not(:has([data-testid="stVerticalBlock"] .z4)) {
    border-radius: 12px; padding: 1.2rem 1.8rem 1.5rem 1.8rem; margin-bottom: 2.8rem; }
  [data-testid="stVerticalBlock"]:has(.z1):not(:has([data-testid="stVerticalBlock"] .z1)) {
    background: rgba(42,156,142,.12); border: 1px solid rgba(42,156,142,.40); }
  [data-testid="stVerticalBlock"]:has(.z2):not(:has([data-testid="stVerticalBlock"] .z2)) {
    background: #EFECFB; border: 1px solid rgba(98,70,211,.32); }
  [data-testid="stVerticalBlock"]:has(.z3):not(:has([data-testid="stVerticalBlock"] .z3)) {
    background: rgba(98,70,211,.32); border: 1px solid rgba(98,70,211,.32); }
  [data-testid="stVerticalBlock"]:has(.z4):not(:has([data-testid="stVerticalBlock"] .z4)) {
    background: rgba(255,148,51,.13); border: 1px solid rgba(255,148,51,.50); }
  [data-baseweb="slider"] { filter: grayscale(1); }  /* barre du curseur en gris, quel que soit le thème */
  /* graduations sous la barre : un trait par pas de 1 % (150 pas de -50 % à +100 %), un trait long tous les 10 % */
  [data-baseweb="slider"]::before, [data-baseweb="slider"]::after { content: ""; position: absolute; left: 0; right: 0;
    pointer-events: none; background-repeat: repeat-x, no-repeat; background-position: 0 0, 100% 0; }
  [data-baseweb="slider"]::before { top: 26px; height: 4px;
    background-image: linear-gradient(to right, #8A8F9E 1px, transparent 1px), linear-gradient(#8A8F9E, #8A8F9E);
    background-size: calc((100% - 1px) / 150) 100%, 1px 100%; }
  [data-baseweb="slider"]::after { top: 26px; height: 8px;
    background-image: linear-gradient(to right, #444 1px, transparent 1px), linear-gradient(#444, #444);
    background-size: calc((100% - 1px) / 15) 100%, 1px 100%; }
  .soustitre { font-family: @TITRES; font-size: .78rem; text-transform: uppercase; letter-spacing: .08em;
               color: #5C628F; font-weight: 700; margin: .1rem 0 .4rem 0; }
  .carte.grand { padding: 1.1rem 1.4rem; }
  .carte.grand .c-val { font-size: 2.3rem; }
  .op.grand { padding-top: 2.3rem; }
  .hero { background: linear-gradient(120deg, @MARINE 0%, #2B2A8F 55%, @VIOLET 100%);
          color: white; padding: 1.5rem 1.9rem; border-radius: 12px; margin-bottom: 1.1rem;
          box-shadow: 0 6px 18px rgba(98,70,211,.25); }
  .hero { display: flex; align-items: center; gap: 1.6rem; }
  .hero-logo { background: white; border-radius: 14px; padding: .6rem; flex: none; line-height: 0;
               box-shadow: 0 2px 8px rgba(6,13,83,.25); }
  .hero-logo img { height: 74px; width: auto; display: block; }
  .hero h1 { color: white; margin: 0; font-size: 1.55rem; text-transform: uppercase; letter-spacing: 3px; padding: 0; line-height: 1.3; }
  .hero p { margin: .4rem 0 0 0; opacity: .92; font-size: 1.02rem; }
  .hero .tag { font-family: "Sofia Pro Medium", @POLICE; display: inline-block; background: rgba(255,255,255,.18); border-radius: 999px;
               padding: .12rem .7rem; font-size: .78rem; font-weight: 400; margin-top: .7rem; }

  .stTabs [data-baseweb="tab-list"] { gap: 1.4rem; border-bottom: 1px solid @BEIGE; }
  .stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 1rem; }

  .etape { display: flex; align-items: center; gap: .7rem; margin: .3rem 0 .9rem 0; }
  .etape .num { font-family: @TITRES; width: 2rem; height: 2rem; border-radius: 50%; color: white; display: flex;
                align-items: center; justify-content: center; font-weight: 700; flex: none; }
  .etape .t { font-family: @TITRES; font-weight: 700; font-size: 1.1rem; color: @MARINE; text-transform: uppercase; letter-spacing: 2px; }
  .etape .a { color: #5C628F; font-size: .92rem; margin-left: .2rem; }

  .carte { background: white; border: 1px solid @BEIGE; border-radius: 10px; padding: .85rem 1.1rem;
           box-shadow: 0 1px 5px rgba(6,13,83,.08); }
  .carte.ref { border-top: 4px solid @AQUA; }
  .carte.var { border-top: 4px solid @VIOLET; }
  .carte.rep { border-top: 4px solid @ORANGE; }
  .c-label { font-family: @TITRES; font-size: .74rem; text-transform: uppercase; letter-spacing: .05em; color: #5C628F; font-weight: 700; }
  .c-val { font-family: @TITRES; font-size: 2.05rem; font-weight: 700; line-height: 1.2; color: @MARINE; }
  .carte.var .c-val { color: @VIOLET; }
  .c-val small { font-size: .95rem; font-weight: 600; color: #5C628F; margin-left: .25rem; }
  .c-sub { font-size: .82rem; color: #5C628F; margin-top: .1rem; }
  .op { font-size: 2rem; color: #9AA0C4; text-align: center; padding-top: 1.7rem; font-weight: 300; }


  .pill { display: inline-block; padding: .2rem .7rem; border-radius: 999px; font-size: .82rem;
          font-weight: 700; margin: .15rem .3rem .15rem 0; }
  .pill.haut { background: #FFE3E5; color: #B23A47; }
  .pill.bas { background: #DDF1EE; color: #1B7A6E; }
  .pill.nul { background: @BEIGE; color: #5C628F; }

  table.sbp { width: 100%; border-collapse: collapse; font-size: .86rem; margin-bottom: .4rem; }
  table.sbp th { text-align: right; color: #5C628F; font-weight: 700; border-bottom: 2px solid @BEIGE; padding: .3rem .35rem; }
  table.sbp td { text-align: right; padding: .38rem .35rem; border-bottom: 1px solid #F4F2EA; }
  table.sbp th:first-child, table.sbp td:first-child { text-align: left; font-weight: 600; }
  table.sbp tr.var td { color: @VIOLET; font-weight: 700; }

  .pied { font-family: "Sofia Pro Medium", @POLICE; color: #8A90B5; font-size: .8rem; text-align: center; margin: 2.5rem 0 .5rem 0; }
</style>
"""
for cle_css, val in {"@POLICE": POLICE, "@TITRES": TITRES, "@MARINE": MARINE, "@VIOLET": VIOLET, "@ORANGE": ORANGE,
                     "@AQUA": AQUA, "@BEIGE": BEIGE}.items():
    CSS = CSS.replace(cle_css, val)
CSS = "\n".join(ligne for ligne in CSS.splitlines() if ligne.strip())  # une ligne vide casse le bloc HTML
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- mise en forme
def fr(x: float, dec: int = 1, signe: bool = False) -> str:
    """Nombre au format suisse : 1’234.5 (apostrophe pour les milliers, point pour les décimales)."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    s = f"{x:+,.{dec}f}" if signe else f"{x:,.{dec}f}"
    return s.replace(",", "’")


def pct(x: float, dec: int = 1) -> str:
    return "–" if x is None or np.isnan(x) else fr(x * 100, dec, True) + " %"


def carte(label: str, valeur: str, unite: str = "", sous: str = "", style: str = "ref") -> str:
    u = f"<small>{unite}</small>" if unite else ""
    return (f"<div class='carte {style}'><div class='c-label'>{label}</div>"
            f"<div class='c-val'>{valeur}{u}</div><div class='c-sub'>{sous}</div></div>")


def pastille(texte: str, valeur: float) -> str:
    if valeur is None or np.isnan(valeur) or abs(valeur) < 0.0005:
        classe, fleche = "nul", ""
    elif valeur > 0:
        classe, fleche = "haut", "▲ "
    else:
        classe, fleche = "bas", "▼ "
    return f"<span class='pill {classe}'>{fleche}{texte} {pct(valeur)}</span>"


def bloc(cle_texte: str) -> tuple[str, str]:
    """Lit un nom de bloc dans TEXTES : « Titre » seul, ou (« Titre », « aide »)."""
    v = TEXTES[cle_texte]
    return (v, "") if isinstance(v, str) else (v[0], v[1] if len(v) > 1 else "")


def etape(num: int | None, titre: str, aide: str, couleur: str) -> None:
    """Titre de bloc ; sans numéro (num=None), la pastille n'est pas affichée."""
    pastille_num = f"<div class='num' style='background:{couleur}'>{num}</div>" if num is not None else ""
    aide_html = f"<span class='a'> · {aide}</span>" if aide else ""
    st.markdown(
        f"<div class='etape'>{pastille_num}<div><span class='t'>{titre}</span>{aide_html}</div></div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------- visualisations
def figure_cercles(ref_ha: float, var_ha: float) -> go.Figure:
    """Cercles dont la surface est proportionnelle au besoin brut (référence : rayon fixe)."""
    r_var = np.sqrt(var_ha / ref_ha) if ref_ha > 0 else 0
    r_max = max(1.0, r_var) * 1.12
    fig = go.Figure()
    # le grand cercle est dessiné en premier, le petit par-dessus : les deux couleurs restent lisibles
    cercles = [(1.0, "42,156,142", TEAL, "dash", 2)]  # référence : teal (couleur du bloc 1)
    if r_var:
        cercles.append((r_var, "98,70,211", VIOLET, "solid", 2.5))  # variante : violet
    ref_au_dessus = r_var >= 1.0 or not r_var
    for rang, (r, rgb, couleur, tiret, epaisseur) in enumerate(sorted(cercles, key=lambda c: -c[0])):
        fig.add_shape(type="circle", x0=-r, x1=r, y0=0, y1=2 * r,
                      fillcolor=f"rgba({rgb},{0.45 if rang == 0 else 0.90})",
                      line=dict(color=couleur, width=epaisseur, dash=tiret))
    fig.add_annotation(x=0, y=1 if ref_au_dessus else 1.75, showarrow=False,
                       text=f"<b>{fr(ref_ha)} ha</b><br>référence",
                       font=dict(size=13, color="white" if ref_au_dessus else MARINE))
    if r_var:
        fig.add_annotation(x=0, y=2 * r_var + 0.1 * r_max, text=f"<b>{fr(var_ha)} ha</b> · variante",
                           showarrow=False, font=dict(size=13, color=VIOLET))
    fig.update_xaxes(visible=False, range=[-r_max, r_max])
    fig.update_yaxes(visible=False, range=[-0.05, 2 * r_max + 0.1], scaleanchor="x", scaleratio=1)
    fig.update_layout(height=290, margin=dict(l=0, r=0, t=4, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", separators=".’",
                      font=dict(family=POLICE, color=MARINE))
    return fig


def figure_batiment(niv_actuel: float, niv_retenu: float, niv_max: float) -> go.Figure:
    fig = go.Figure()
    largeur = 0.8
    h_auj, h_var = int(round(niv_actuel)), int(round(niv_retenu))
    commun = min(h_auj, h_var)

    def etage(x0, y, couleur, contour):
        fig.add_shape(type="rect", x0=x0, x1=x0 + largeur, y0=y, y1=y + 0.9,
                      fillcolor=couleur, line=dict(color=contour, width=1.2))

    for f in range(h_auj):
        etage(0, f, BEIGE, "#B9B59C")
    for f in range(h_var):
        if f < commun:
            etage(1.3, f, BEIGE, "#B9B59C")   # niveaux existants : clairs
        else:
            etage(1.3, f, ORANGE, "white")    # niveaux supplémentaires
    fig.add_annotation(x=0.4, y=-0.9, text=f"Aujourd'hui : {h_auj}", showarrow=False, font=dict(size=12, color=MARINE))
    fig.add_annotation(x=1.7, y=-0.9, text=f"Variante : {h_var}", showarrow=False, font=dict(size=12, color=VIOLET))
    fig.update_xaxes(visible=False, range=[-0.5, 2.6])
    fig.update_yaxes(visible=False, range=[-1.4, max(niv_max or 0, h_auj, h_var, 1) + 0.6])
    fig.update_layout(height=290, margin=dict(l=0, r=0, t=4, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", separators=".’",
                      font=dict(family=POLICE, color=MARINE))
    return fig


def figure_emprises(valeurs: list[tuple[str, float, str]]) -> go.Figure:
    """Carrés dont la surface est proportionnelle à l'emprise bâtie (m²)."""
    m = max(v for _, v, _ in valeurs)
    fig = go.Figure()
    x = 0.0
    for nom, v, couleur in valeurs:
        cote = np.sqrt(v / m) if m > 0 else 0
        fig.add_shape(type="rect", x0=x, x1=x + cote, y0=0, y1=cote,
                      fillcolor=couleur, line=dict(color=MARINE, width=1))
        fig.add_annotation(x=x + cote / 2, y=-0.04, yanchor="top", text=f"{nom}<br><b>{fr(v, 0)} m²</b>",
                           showarrow=False, font=dict(size=11, color=MARINE))
        x += max(cote, 0.15) + 0.25
    fig.update_xaxes(visible=False, range=[-0.1, x])
    fig.update_yaxes(visible=False, range=[-0.45, 1.1], scaleanchor="x", scaleratio=1)
    fig.update_layout(height=290, margin=dict(l=0, r=0, t=4, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", separators=".’",
                      font=dict(family=POLICE, color=MARINE))
    return fig


def graphique_classes(synth: pd.DataFrame) -> go.Figure:
    s = synth.loc[CLASSES]
    fig = go.Figure()
    fig.add_bar(y=CLASSES, x=s["besoin_brut_ref_ha"], name="Référence future", orientation="h",
                marker_color=AQUA, hovertemplate="%{y} : %{x:.1f} ha<extra>Référence</extra>")
    fig.add_bar(y=CLASSES, x=s["besoin_brut_var_ha"], name="Variante", orientation="h",
                marker_color=VIOLET, hovertemplate="%{y} : %{x:.1f} ha<extra>Variante</extra>")
    fig.update_layout(
        barmode="group", height=300, margin=dict(l=10, r=10, t=10, b=10),
        font=dict(family=POLICE, color=MARINE),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, x=0),
        xaxis=dict(title="ha équiv. SBP", gridcolor=BEIGE), yaxis=dict(autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", separators=".’",
    )
    return fig


# ---------------------------------------------------------------- données et état
@st.cache_data
def donnees() -> pd.DataFrame:
    return charger_donnees()


DF = donnees()
BASE = calculer(DF)  # référence : valeurs actuelles, indépendantes des réglages
INFO = BASE.set_index("type")

if "reglages" not in st.session_state:
    st.session_state.reglages = {}  # type -> {"ratio": float, "niveaux": int}
if "version" not in st.session_state:
    st.session_state.version = 0


def cle(prefixe: str, equipement: str) -> str:
    return f"{prefixe}_{st.session_state.version}_{equipement}"


def reglage(equipement: str) -> dict:
    ligne = INFO.loc[equipement]
    return st.session_state.reglages.setdefault(
        equipement, {"ratio": float(ligne["ratio_actuel"]), "niveaux": int(ligne["niveaux_actuels"])}
    )


def reinitialiser() -> None:
    st.session_state.reglages = {}
    st.session_state.version += 1


def _pct_curseur(ratio: float, ra: float) -> int:
    return int(np.clip(round((ratio / ra - 1) * 100), -50, 100)) if ra > 0 else 0


def ratio_depuis_curseur(eq: str) -> None:
    ra = float(INFO.loc[eq, "ratio_actuel"])
    r = round(ra * (1 + st.session_state[cle("rs", eq)] / 100), 2)
    st.session_state[cle("rn", eq)] = r
    reglage(eq)["ratio"] = r


def ratio_depuis_nombre(eq: str) -> None:
    ra = float(INFO.loc[eq, "ratio_actuel"])
    r = float(st.session_state[cle("rn", eq)])
    reglage(eq)["ratio"] = r
    st.session_state[cle("rs", eq)] = _pct_curseur(r, ra)


def niveaux_supplementaires_saisis(eq: str) -> None:
    reglage(eq)["niveaux"] = int(INFO.loc[eq, "niveaux_actuels"]) + int(st.session_state[cle("niv", eq)])


def reglages_df() -> pd.DataFrame:
    """Réglages mémorisés -> tableau pour `calculer` (vide si égal à la situation actuelle)."""
    reg = reglages_vides(DF)
    for i, t in enumerate(DF["type"]):
        if t not in st.session_state.reglages:
            continue
        r, ligne = st.session_state.reglages[t], INFO.loc[t]
        if abs(r["ratio"] - ligne["ratio_actuel"]) > 5e-3:
            reg.loc[i, "ratio_futur"] = r["ratio"]
        if r["niveaux"] != ligne["niveaux_actuels"]:
            reg.loc[i, "niveaux_supplementaires"] = r["niveaux"] - ligne["niveaux_actuels"]
    return reg


# ================================================================ en-tête
st.markdown(
    "<div class='hero'>"
    f"<div class='hero-logo'><img src='data:image/png;base64,{LOGO_B64}' alt='6t'></div>"
    f"<div class='hero-txt'><h1>{TEXTES['titre_page']}</h1>"
    f"<p>{TEXTES['sous_titre_page']}</p>"
    + (f"<span class='tag'>{TEXTES['tag_page']}</span>" if TEXTES.get("tag_page") else "")
    + "</div></div>",
    unsafe_allow_html=True,
)

onglet_equipement, onglet_ensemble, onglet_methode = st.tabs(
    [TEXTES["onglet_1"], TEXTES["onglet_2"], TEXTES["onglet_3"]]
)

# ================================================================ PAGE 1 : par équipement
with onglet_equipement:
    c_sel, c_reset = st.columns([4, 1])
    equipement = c_sel.selectbox(
        TEXTES["menu_equipement"],
        list(DF["type"]),
        format_func=lambda t: f"{INFO.loc[t, 'classe']}  ·  {t}",
    )
    c_reset.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
    c_reset.button("↺ Réinitialiser", on_click=reinitialiser, use_container_width=True)

    base = INFO.loc[equipement]
    ra = float(base["ratio_actuel"])
    niv_actuels, niv_max = int(base["niveaux_actuels"]), int(base["niveaux_max"])
    rg = reglage(equipement)

    k_rs, k_rn, k_niv = cle("rs", equipement), cle("rn", equipement), cle("niv", equipement)
    st.session_state.setdefault(k_rn, float(rg["ratio"]))
    st.session_state.setdefault(k_rs, _pct_curseur(rg["ratio"], ra))
    st.session_state.setdefault(k_niv, int(rg["niveaux"]) - niv_actuels)  # niveaux supplémentaires

    res = calculer(DF, reglages_df())
    ligne = res[res["type"] == equipement].iloc[0]


    # ---------------------------------------------------- bloc 1 : référence
    with st.container():
        st.markdown("<span class='zone z1'></span>", unsafe_allow_html=True)
        etape(1, *bloc("bloc_1"), TEAL)
        a, op1, b, op2, c = st.columns([1, 0.12, 1, 0.12, 1])
        a.markdown(carte("Ratio actuel", fr(ra, 2), "m²/hab.",
                         f"{fr(base['population_actuelle'], 0)} hab. · {niv_actuels} niveaux", "ref grand"),
                   unsafe_allow_html=True)
        op1.markdown("<div class='op grand'>×</div>", unsafe_allow_html=True)
        b.markdown(carte("Population future", fr(base["population_future"], 0), "hab.",
                         "scénario de référence, inchangé", "ref grand"), unsafe_allow_html=True)
        op2.markdown("<div class='op grand'>=</div>", unsafe_allow_html=True)
        c.markdown(carte("Besoin brut, référence", fr(base["besoin_brut_ref_ha"]), "ha",
                         "équiv. SBP, au ratio actuel", "ref grand"), unsafe_allow_html=True)

    # ---------------------------------------------------- bloc 2 : ajuster le ratio
    with st.container():
        st.markdown("<span class='zone z2'></span>", unsafe_allow_html=True)
        etape(2, *bloc("bloc_2"), VIOLET)
        s_gauche, s_droite = st.columns(2)
        with s_gauche:
            if ra > 0:
                st.slider("Variation du ratio actuel", -50, 100, key=k_rs, step=1,
                          on_change=ratio_depuis_curseur, args=(equipement,), format="%+d %%")
            else:
                st.info("Cet équipement n'a pas de SBP dans les données (ratio actuel nul) : "
                        "saisissez directement un ratio à tester.")
        with s_droite:
            st.number_input("Ratio futur (m² équiv. SBP / hab.)", min_value=0.0, step=0.5, format="%.2f",
                            key=k_rn, on_change=ratio_depuis_nombre, args=(equipement,))
        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
        a2, op3, b2, op4, c2 = st.columns([1, 0.12, 1, 0.12, 1])
        a2.markdown(carte("Ratio variante", fr(ligne["ratio_variante"], 2), "m²/hab.",
                          f"ratio actuel : {fr(ra, 2)}", "var grand"), unsafe_allow_html=True)
        op3.markdown("<div class='op grand'>×</div>", unsafe_allow_html=True)
        b2.markdown(carte("Population future", fr(base["population_future"], 0), "hab.",
                          "scénario de référence, inchangé", "var grand"), unsafe_allow_html=True)
        op4.markdown("<div class='op grand'>=</div>", unsafe_allow_html=True)
        c2.markdown(carte("Besoin brut, variante", fr(ligne["besoin_brut_var_ha"]), "ha",
                          f"référence : {fr(ligne['besoin_brut_ref_ha'])} ha", "var grand"), unsafe_allow_html=True)

    # ---------------------------------------------------- bloc 3 : résultat
    with st.container():
        st.markdown("<span class='zone z3'></span>", unsafe_allow_html=True)
        etape(None, *bloc("bloc_3"), MARINE)  # bloc Résultat : fait partie du bloc 2, pas de numéro
        v_gauche, v_droite = st.columns([1, 1.6])
        v_gauche.markdown(carte("Variation du besoin brut", pct(ligne["ecart_besoin_pct"]), "",
                                "par rapport à la référence", "var grand"), unsafe_allow_html=True)
        v_gauche.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
        v_gauche.markdown(carte("Écart", fr(ligne["ecart_besoin_ha"], 1, True), "ha",
                                f"référence {fr(ligne['besoin_brut_ref_ha'])} ha → variante "
                                f"{fr(ligne['besoin_brut_var_ha'])} ha", "var grand"), unsafe_allow_html=True)
        v_droite.plotly_chart(figure_cercles(ligne["besoin_brut_ref_ha"], ligne["besoin_brut_var_ha"]),
                              use_container_width=True, config={"displayModeBar": False})

    # ---------------------------------------------------- bloc 4 : répartition
    with st.container():
        st.markdown("<span class='zone z4'></span>", unsafe_allow_html=True)
        etape(3, *bloc("bloc_4"), ORANGE)
        n1, n2, n3 = st.columns([1, 1, 1])
        with n1:
            st.markdown(f"<div class='soustitre'>{TEXTES['bloc_4_niveaux']}</div>", unsafe_allow_html=True)
            if niv_actuels > 0:
                st.number_input("Niveaux supplémentaires", min_value=1 - niv_actuels, max_value=100, step=1,
                                key=k_niv, label_visibility="collapsed", format="%d",
                                on_change=niveaux_supplementaires_saisis, args=(equipement,))
            else:
                st.info("Pas de niveau dans les données : l'emprise bâtie n'est pas calculable.")
            st.markdown(carte("Niveaux retenus", fr(ligne["niveaux_variante"], 0), "niveaux",
                              f"aujourd'hui : {niv_actuels}", "rep"), unsafe_allow_html=True)
        with n2:
            st.markdown(f"<div class='soustitre'>{TEXTES['bloc_4_batiments']}</div>", unsafe_allow_html=True)
            st.plotly_chart(figure_batiment(ligne["niveaux_actuels"], ligne["niveaux_variante"], niv_max),
                            use_container_width=True, config={"displayModeBar": False})
        with n3:
            st.markdown(f"<div class='soustitre'>{TEXTES['bloc_4_carres']}</div>", unsafe_allow_html=True)
            st.plotly_chart(
                figure_emprises([
                    ("Aujourd'hui", ligne["emprise_auj_m2"], BEIGE),
                    ("Réf. future", ligne["emprise_ref_m2"], AQUA),
                    ("Variante", ligne["emprise_var_m2"], ORANGE),
                ]),
                use_container_width=True, config={"displayModeBar": False},
            )

        st.markdown(f"<div class='soustitre' style='margin-top:.8rem'>{TEXTES['bloc_4_tableau']}</div>",
                    unsafe_allow_html=True)

        def ligne_tab(nom, suffixe, style=""):
            return (f"<tr class='{style}'><td>{nom}</td><td>{fr(ligne['sbp_bati_' + suffixe + '_m2'], 0)}</td>"
                    f"<td>{fr(ligne['annexes_' + suffixe + '_m2'], 0)}</td>"
                    f"<td>{fr(ligne['emprise_' + suffixe + '_m2'], 0)}</td>"
                    f"<td>{fr(ligne['sol_' + suffixe + '_m2'], 0)}</td></tr>")

        t1, t2 = st.columns([1.6, 1])
        t1.markdown(
            "<table class='sbp'><tr><th>m²</th><th>SBP bâtiments</th><th>Annexes</th><th>Emprise bâtie</th>"
            "<th>Sol total</th></tr>"
            + ligne_tab("Aujourd'hui", "auj") + ligne_tab("Référence future", "ref") + ligne_tab("Variante", "var", "var")
            + "</table>",
            unsafe_allow_html=True,
        )
        t2.markdown(
            pastille("Emprise bâtie vs aujourd'hui", ligne["ecart_emprise_auj_pct"])
            + pastille("Emprise bâtie vs réf. future", ligne["ecart_emprise_ref_pct"])
            + "<br>"
            + pastille("Sol total vs aujourd'hui", ligne["ecart_sol_auj_pct"])
            + pastille("Sol total vs réf. future", ligne["ecart_sol_ref_pct"]),
            unsafe_allow_html=True,
        )
        if ligne["alertes"]:
            st.warning(ligne["alertes"])

# ================================================================ PAGE 2 : vue d'ensemble
res = calculer(DF, reglages_df())
synth = synthese_par_classe(res)
tot = synth.loc["Total"]
n_regles = len(
    [t for t, r in st.session_state.reglages.items()
     if abs(r["ratio"] - INFO.loc[t, "ratio_actuel"]) > 5e-3 or r["niveaux"] != INFO.loc[t, "niveaux_actuels"]]
)

with onglet_ensemble:
    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    k1.markdown(carte("Besoin brut total, référence", fr(tot["besoin_brut_ref_ha"]), "ha",
                      "ratios actuels × populations futures", "ref"), unsafe_allow_html=True)
    k2.markdown(carte("Besoin brut total, variante", fr(tot["besoin_brut_var_ha"]), "ha",
                      f"{fr(tot['ecart_besoin_ha'], 1, True)} ha vs référence", "var"), unsafe_allow_html=True)
    k3.markdown(carte("Équipements réglés", str(n_regles), f"/ {len(DF)}",
                      "réglages faits dans l'onglet « Par équipement »", "rep"), unsafe_allow_html=True)

    st.markdown("<div class='etape'><div class='t'>Besoin brut par classe d'équipement</div></div>",
                unsafe_allow_html=True)
    st.plotly_chart(graphique_classes(synth), use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div class='etape'><div class='t'>Tous les équipements</div></div>", unsafe_allow_html=True)
    vue = res[[
        "classe", "type", "ratio_actuel", "ratio_variante", "besoin_brut_ref_ha", "besoin_brut_var_ha",
        "ecart_besoin_ha", "niveaux_actuels", "niveaux_variante", "emprise_auj_m2", "emprise_ref_m2",
        "emprise_var_m2", "sol_var_m2", "ecart_emprise_auj_pct", "ecart_emprise_ref_pct", "alertes",
    ]]
    st.dataframe(
        vue.style.hide(axis="index").format({
            "ratio_actuel": lambda x: fr(x, 2), "ratio_variante": lambda x: fr(x, 2),
            "besoin_brut_ref_ha": lambda x: fr(x, 1), "besoin_brut_var_ha": lambda x: fr(x, 1),
            "ecart_besoin_ha": lambda x: fr(x, 1, True),
            "niveaux_actuels": lambda x: fr(x, 0), "niveaux_variante": lambda x: fr(x, 0),
            "emprise_auj_m2": lambda x: fr(x, 0), "emprise_ref_m2": lambda x: fr(x, 0),
            "emprise_var_m2": lambda x: fr(x, 0), "sol_var_m2": lambda x: fr(x, 0),
            "ecart_emprise_auj_pct": pct, "ecart_emprise_ref_pct": pct,
        }), hide_index=True, use_container_width=True,
        column_config={
            "classe": "Classe",
            "type": st.column_config.TextColumn("Équipement", width="large"),
            "ratio_actuel": st.column_config.NumberColumn("Ratio actuel", format="%.2f"),
            "ratio_variante": st.column_config.NumberColumn("Ratio variante", format="%.2f"),
            "besoin_brut_ref_ha": st.column_config.NumberColumn("Besoin brut réf. (ha)", format="%.1f"),
            "besoin_brut_var_ha": st.column_config.NumberColumn("Besoin brut variante (ha)", format="%.1f"),
            "ecart_besoin_ha": st.column_config.NumberColumn("Écart (ha)", format="%+.1f"),
            "niveaux_actuels": st.column_config.NumberColumn("Niveaux actuels", format="%d"),
            "niveaux_variante": st.column_config.NumberColumn("Niveaux variante", format="%d"),
            "emprise_auj_m2": st.column_config.NumberColumn("Emprise aujourd'hui (m²)", format="%.0f"),
            "emprise_ref_m2": st.column_config.NumberColumn("Emprise réf. future (m²)", format="%.0f"),
            "emprise_var_m2": st.column_config.NumberColumn("Emprise variante (m²)", format="%.0f"),
            "sol_var_m2": st.column_config.NumberColumn("Sol total variante (m²)", format="%.0f"),
            "ecart_emprise_auj_pct": st.column_config.NumberColumn("Emprise vs aujourd'hui", format="percent"),
            "ecart_emprise_ref_pct": st.column_config.NumberColumn("Emprise vs réf. future", format="percent"),
            "alertes": st.column_config.TextColumn("Alertes", width="large"),
        },
    )

    tampon = io.BytesIO()
    with pd.ExcelWriter(tampon, engine="openpyxl") as xl:
        res.to_excel(xl, sheet_name="Résultats", index=False)
        synth.to_excel(xl, sheet_name="Synthèse par classe")
    excel_bytes = tampon.getvalue()
    csv_bytes = res.to_csv(index=False).encode("utf-8-sig")
    d1, d2, d3 = st.columns(3)
    d1.download_button("⬇ Télécharger (Excel)", excel_bytes, "variante_besoins_equipements.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)
    d2.download_button("⬇ Télécharger (CSV)", csv_bytes, "variante_besoins_equipements.csv", "text/csv",
                       use_container_width=True)
    if d3.button("Enregistrer sur disque", use_container_width=True):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "variante_besoins_equipements.xlsx").write_bytes(excel_bytes)
        (OUTPUT_DIR / "variante_besoins_equipements.csv").write_bytes(csv_bytes)
        st.success(f"Résultats enregistrés dans `{OUTPUT_DIR}`.")

# ================================================================ PAGE 3 : données et méthode
with onglet_methode:
    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    st.subheader("Méthode : le chemin inverse de la référence")
    s1, s2, s3, s4 = st.columns(4)
    s1.markdown(carte("1 · Ratio futur", "choisi", "", "m² équiv. SBP / hab. ; par défaut le ratio actuel", "ref"),
                unsafe_allow_html=True)
    s2.markdown(carte("2 · Besoin brut", "ratio × pop.", "", "population future inchangée ; pas de besoin net", "var"),
                unsafe_allow_html=True)
    s3.markdown(carte("3 · Répartition", "annexes / SBP", "", "part des annexes d'aujourd'hui conservée", "rep"),
                unsafe_allow_html=True)
    s4.markdown(carte("4 · Emprise", "SBP ÷ niveaux", "", "sol total = emprise + annexes", "var"),
                unsafe_allow_html=True)
    st.markdown(
        """
- **Ratio actuel** = (emprise × niveaux + annexes) ÷ population actuelle.
- **Référence future** = ratio actuel × population future, avec les mêmes niveaux qu'aujourd'hui.
- **Écarts** : comparés à aujourd'hui et à la référence future, sans hypothèse sur l'existant
  (construction neuve ou surélévation).
- **Niveaux** : saisis en niveaux supplémentaires (minimum 1 niveau au total). Au-delà du niveau maximum de référence, un avertissement s'affiche mais le calcul reste possible.
        """
    )
    st.subheader("Données de référence")
    st.caption("Pour modifier ces valeurs, éditez le fichier data/equipements.csv puis relancez l'application.")
    st.dataframe(
        DF[["classe", "type", "population_actuelle", "emprise_batiments_m2", "espaces_exterieurs_m2",
            "niveaux_actuels", "population_future_reference", "niveaux_max", "source_bornes"]]
        .style.hide(axis="index").format({c: (lambda x: fr(x, 0)) for c in [
            "population_actuelle", "emprise_batiments_m2", "espaces_exterieurs_m2", "niveaux_actuels",
            "population_future_reference", "niveaux_max"]}),
        hide_index=True, use_container_width=True,
        column_config={
            "classe": "Classe",
            "type": st.column_config.TextColumn("Équipement", width="large"),
            "population_actuelle": st.column_config.NumberColumn("Pop. actuelle", format="%.0f"),
            "emprise_batiments_m2": st.column_config.NumberColumn("Emprise bâtiments (m²)", format="%.0f"),
            "espaces_exterieurs_m2": st.column_config.NumberColumn("Annexes (m²)", format="%.0f"),
            "niveaux_actuels": st.column_config.NumberColumn("Niveaux actuels", format="%d"),
            "population_future_reference": st.column_config.NumberColumn("Pop. future réf.", format="%.0f"),
            "niveaux_max": st.column_config.NumberColumn("Niveaux max", format="%d"),
            "source_bornes": "Source des bornes",
        },
    )
    st.subheader("Sources et points d'attention")
    st.markdown(
        """
- **École primaire** : règlement genevois RCLEP (rsGE C 1 10.11), annexe ch. 3 et 4. Deux étages sur rez, un étage
  supplémentaire possible (4 niveaux au maximum) ; préaux de 140 m² par classe, soit environ 7 m² par élève.
- **Autres équipements** : bornes provisoires, à faire valider par les services concernés.
- **Populations futures de référence** : valeurs de test (population actuelle + 10 000), à remplacer par les
  projections démographiques par tranche d'âge.
- **Piscines, plages et espaces verts** ont 0 niveau dans les données : pas de SBP ni d'emprise calculable.
- **Équipements très annexés** (centres sportifs : 95 % d'annexes) : les niveaux changent peu le sol total.
        """
    )

st.markdown("<div class='pied'>6t · Besoins en équipements publics à l'horizon 2050 · "
            "Données provisoires, à valider avec les services concernés</div>", unsafe_allow_html=True)
