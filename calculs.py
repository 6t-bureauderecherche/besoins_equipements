"""Modèle de calcul des besoins en équipements publics (chemin inverse).

Reprend la logique du fichier Excel « Tableau_SBP_SS - CD 22_10_26 ».

On part d'un ratio futur (m² équiv. SBP / habitant), choisi par l'utilisateur, puis :

1. Besoin total brut = ratio futur × population future (scénario de référence, inchangé).
2. La part des annexes dans la SBP totale, observée aujourd'hui, est conservée :
   annexes = besoin brut × part ; SBP bâtiments = besoin brut × (1 − part).
3. Emprise bâtie = SBP bâtiments ÷ niveaux retenus. Avec les mêmes niveaux, plus de SBP
   donne plus de sol ; avec plus de niveaux, moins de sol et des bâtiments plus hauts.
4. Sol total = emprise bâtie + annexes.

Pas de besoin net : on ne retranche pas la couverture actuelle.

Réglages par équipement (vide = pas de changement) :
- ratio_futur (m²/hab.) : remplace le ratio actuel.
- niveaux_supplementaires : niveaux ajoutés aux niveaux actuels, entre 1 et le plafond.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

CLASSES = ["Enseignement", "Santé/Social", "Sport et loisirs", "Culture"]

DATA_PATH = Path(__file__).parent / "data" / "equipements.csv"

# False : on peut saisir n'importe quel nombre de niveaux (simple avertissement au-delà du niveau maximum
# de référence) ; True : le nombre de niveaux est limité au niveau maximum, comme dans le fichier Excel.
PLAFONNER_NIVEAUX = False


def charger_donnees(chemin: Path | str = DATA_PATH) -> pd.DataFrame:
    """Lit les données de référence et les bornes."""
    return pd.read_csv(chemin)


def reglages_vides(df: pd.DataFrame) -> pd.DataFrame:
    """Tableau de réglages par équipement, vide = pas de changement."""
    return pd.DataFrame(
        {
            "type": df["type"],
            "ratio_futur": np.nan,  # m²/hab., remplace le ratio actuel
            "niveaux_supplementaires": np.nan,
        }
    )


def _div(a, b):
    """Division sans erreur : renvoie 0 quand le dénominateur est nul ou négatif."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    out = np.zeros_like(a * b, dtype=float)
    np.divide(a, b, out=out, where=b > 0)
    return out


def _ecart_pct(valeur, base, valide):
    """Écart relatif valeur / base − 1 ; NaN si la base est nulle ou si `valide` est faux."""
    ok = valide & (np.asarray(base, dtype=float) > 0)
    return np.where(ok, _div(valeur, base) - 1, np.nan)


def calculer(df: pd.DataFrame, reglages: pd.DataFrame | None = None) -> pd.DataFrame:
    """Calcule la référence future et la variante pour chaque équipement."""
    if reglages is None:
        reglages = reglages_vides(df)
    reglages = reglages.set_index("type").reindex(df["type"]).reset_index()

    pop = df["population_actuelle"].to_numpy(float)
    emp = df["emprise_batiments_m2"].to_numpy(float)
    ext = df["espaces_exterieurs_m2"].to_numpy(float)
    niv = df["niveaux_actuels"].to_numpy(float)
    niv_max = df["niveaux_max"].to_numpy(float)
    pop_fut = df["population_future_reference"].to_numpy(float)

    # --- situation actuelle
    sbp_bati_auj = emp * niv
    sbp_totale_auj = sbp_bati_auj + ext
    ratio_actuel = _div(sbp_totale_auj, pop)
    part_annexes = _div(ext, sbp_totale_auj)
    sol_auj = emp + ext

    # --- référence future : ratio actuel, mêmes niveaux
    besoin_ref = ratio_actuel * pop_fut  # m² équiv. SBP
    annexes_ref = besoin_ref * part_annexes
    sbp_bati_ref = besoin_ref - annexes_ref
    emprise_ref = _div(sbp_bati_ref, niv)
    sol_ref = emprise_ref + annexes_ref

    # --- variante
    ratio_choisi = reglages["ratio_futur"].astype(float).to_numpy()
    ratio_var = np.where(np.isnan(ratio_choisi), ratio_actuel, ratio_choisi)
    ns = reglages["niveaux_supplementaires"].astype(float).fillna(0.0).to_numpy()
    niv_demande = niv + ns
    borne_haute = niv_max if PLAFONNER_NIVEAUX else np.full_like(niv_max, np.inf)
    niv_var = np.where(niv == 0, 0, np.clip(niv_demande, 1, borne_haute))

    besoin_var = ratio_var * pop_fut
    annexes_var = besoin_var * part_annexes
    sbp_bati_var = besoin_var - annexes_var
    emprise_var = _div(sbp_bati_var, niv_var)
    sol_var = emprise_var + annexes_var

    calculable = niv_var > 0  # sans niveau, l'emprise n'est pas calculable

    # --- alertes
    alertes = []
    for i in range(len(df)):
        a = []
        if niv[i] == 0 and emp[i] > 0:
            a.append("Pas de niveau dans les données : emprise non calculée")
        if niv[i] > 0 and niv_demande[i] > niv_max[i]:
            a.append(f"Niveaux plafonnés à {int(niv_max[i])}" if PLAFONNER_NIVEAUX
                     else f"Au-delà du niveau maximum de référence ({int(niv_max[i])})")
        if niv[i] > 0 and niv_demande[i] < 1:
            a.append("Minimum 1 niveau")
        alertes.append(" · ".join(a))

    return pd.DataFrame(
        {
            "classe": df["classe"],
            "type": df["type"],
            "population_actuelle": pop,
            "population_future": pop_fut,
            "niveaux_actuels": niv,
            "niveaux_max": niv_max,
            "ratio_actuel": ratio_actuel,
            "part_annexes": part_annexes,
            # aujourd'hui
            "sbp_bati_auj_m2": sbp_bati_auj,
            "emprise_auj_m2": emp,
            "annexes_auj_m2": ext,
            "sol_auj_m2": sol_auj,
            # référence future
            "besoin_brut_ref_ha": besoin_ref / 1e4,
            "sbp_bati_ref_m2": sbp_bati_ref,
            "annexes_ref_m2": annexes_ref,
            "emprise_ref_m2": emprise_ref,
            "sol_ref_m2": sol_ref,
            # variante
            "ratio_variante": ratio_var,
            "niveaux_variante": niv_var,
            "besoin_brut_var_ha": besoin_var / 1e4,
            "sbp_bati_var_m2": sbp_bati_var,
            "annexes_var_m2": annexes_var,
            "emprise_var_m2": emprise_var,
            "sol_var_m2": sol_var,
            # écarts
            "ecart_besoin_ha": (besoin_var - besoin_ref) / 1e4,
            "ecart_besoin_pct": _ecart_pct(besoin_var, besoin_ref, np.ones(len(df), dtype=bool)),
            "ecart_emprise_auj_pct": _ecart_pct(emprise_var, emp, calculable),
            "ecart_emprise_ref_pct": _ecart_pct(emprise_var, emprise_ref, calculable),
            "ecart_sol_auj_pct": _ecart_pct(sol_var, sol_auj, calculable),
            "ecart_sol_ref_pct": _ecart_pct(sol_var, sol_ref, calculable),
            "alertes": alertes,
        }
    )


def synthese_par_classe(res: pd.DataFrame) -> pd.DataFrame:
    """Besoins bruts par classe d'équipement, avec une ligne Total."""
    cols = ["besoin_brut_ref_ha", "besoin_brut_var_ha"]
    s = res.groupby("classe", sort=False)[cols].sum().reindex(CLASSES)
    s.loc["Total"] = s.sum()
    s["ecart_besoin_ha"] = s["besoin_brut_var_ha"] - s["besoin_brut_ref_ha"]
    return s
