"""Vérifie le modèle (chemin inverse : ratio futur -> besoin brut -> SBP bâtiments/annexes -> emprise),
aligné sur le fichier Excel « Tableau_SBP_SS - CD 22_10_26 »."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from calculs import (  # noqa: E402
    calculer,
    charger_donnees,
    reglages_vides,
    synthese_par_classe,
)

DF = charger_donnees()


def _ligne(res, nom):
    return res[res["type"] == nom].iloc[0]


def test_reference_future():
    res = calculer(DF)
    tot = synthese_par_classe(res).loc["Total"]
    assert tot["besoin_brut_ref_ha"] == pytest.approx(1196.42, abs=0.01)
    prim = _ligne(res, "Ecole primaire")
    assert prim["ratio_actuel"] == pytest.approx(35.5865, abs=1e-3)
    assert prim["part_annexes"] == pytest.approx(0.636, abs=1e-3)
    assert prim["besoin_brut_ref_ha"] == pytest.approx(192.274, abs=1e-3)
    # mêmes niveaux, ratio actuel : l'emprise suit la croissance de population
    assert prim["emprise_ref_m2"] == pytest.approx(285174 * 54030 / 44030, rel=1e-9)


def test_sans_reglage_variante_egale_reference():
    res = calculer(DF)
    assert np.allclose(res["besoin_brut_var_ha"], res["besoin_brut_ref_ha"])
    assert np.allclose(res["emprise_var_m2"], res["emprise_ref_m2"])
    assert np.allclose(res["sol_var_m2"], res["sol_ref_m2"])
    assert np.allclose(res["ecart_besoin_ha"], 0)


def test_ratio_42_et_deux_niveaux_en_plus():
    """Scénario de l'Excel : école primaire, ratio futur 42, +2 niveaux."""
    reg = reglages_vides(DF)
    reg.loc[reg["type"] == "Ecole primaire", "ratio_futur"] = 42
    reg.loc[reg["type"] == "Ecole primaire", "niveaux_supplementaires"] = 2
    prim = _ligne(calculer(DF, reg), "Ecole primaire")
    assert prim["niveaux_variante"] == 4
    assert prim["besoin_brut_var_ha"] == pytest.approx(226.926, abs=1e-3)
    assert prim["sbp_bati_var_m2"] == pytest.approx(826018.6, abs=0.5)
    assert prim["annexes_var_m2"] == pytest.approx(1443241.4, abs=0.5)
    assert prim["emprise_var_m2"] == pytest.approx(206504.65, abs=0.5)
    assert prim["ecart_emprise_auj_pct"] == pytest.approx(-0.2759, abs=1e-3)
    assert prim["ecart_emprise_ref_pct"] == pytest.approx(-0.4099, abs=1e-3)
    assert prim["ecart_besoin_ha"] == pytest.approx(226.926 - 192.274, abs=1e-3)


def test_meme_niveaux_plus_de_ratio_donne_plus_de_sol():
    reg = reglages_vides(DF)
    reg.loc[reg["type"] == "Ecole primaire", "ratio_futur"] = 42
    prim = _ligne(calculer(DF, reg), "Ecole primaire")
    assert prim["emprise_var_m2"] > prim["emprise_ref_m2"]
    assert prim["sol_var_m2"] > prim["sol_ref_m2"]


def test_niveaux_libres_avec_avertissement():
    reg = reglages_vides(DF)
    reg["niveaux_supplementaires"] = 3
    prim = _ligne(calculer(DF, reg), "Ecole primaire")
    assert prim["niveaux_variante"] == 5  # 2 + 3, non plafonné
    assert "maximum de référence" in prim["alertes"]


def test_plafond_optionnel(monkeypatch):
    import calculs
    monkeypatch.setattr(calculs, "PLAFONNER_NIVEAUX", True)
    reg = reglages_vides(DF)
    reg["niveaux_supplementaires"] = 3
    prim = _ligne(calculer(DF, reg), "Ecole primaire")
    assert prim["niveaux_variante"] == 4  # plafonné à niveaux_max
    assert "plafonnés" in prim["alertes"]


def test_equipement_sans_niveau():
    reg = reglages_vides(DF)
    reg.loc[reg["type"] == "Piscines", "ratio_futur"] = 5
    pisc = _ligne(calculer(DF, reg), "Piscines")
    assert pisc["emprise_var_m2"] == 0
    assert np.isnan(pisc["ecart_emprise_auj_pct"])
    assert "Pas de niveau" in pisc["alertes"]
