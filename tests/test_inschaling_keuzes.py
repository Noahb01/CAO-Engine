"""Tests voor functie → ladder mapping en gecombineerde keuzes (optie B)."""

from functie_ladder_mapping import FUNCTIE_LADDER_MAPPING, verrijk_mapping
from functies import UTA_FUNCTIES
from inschaling_keuzes import (
    keuze_naar_inschaling,
    lijst_functietitel_keuzes,
    lijst_inschaling_keuzes,
)


def test_alle_uta_functies_hebben_mapping():
    for f in UTA_FUNCTIES:
        assert f.naam in FUNCTIE_LADDER_MAPPING, f"Geen mapping voor {f.naam}"


def test_werkvoorbereider_mapping():
    m = FUNCTIE_LADDER_MAPPING["Werkvoorbereider"]
    assert m.functieladder_nummer == 3
    assert m.voorgesteld_niveau == 3


def test_functietitel_keuzes_label():
    keuzes = lijst_functietitel_keuzes()
    wv = next(k for k in keuzes if k["functie_naam"] == "Werkvoorbereider")
    assert wv["label"] == "Werkvoorbereider"
    assert wv["voorgesteld_niveau"] == 3
    assert "toelichting" in wv
    assert "matrix_signaal" in wv


def test_inschaling_keuzes_zoeken():
    result = lijst_inschaling_keuzes("uitvoerder")
    assert any(k["functie_naam"] == "Uitvoerder" for k in result["functietitels"])


def test_keuze_naar_inschaling_functietitel():
    data = keuze_naar_inschaling("functie:Werkvoorbereider")
    assert data["functieladder_nummer"] == 3
    assert data["bevestigd_niveau"] == 3
    assert data["functie_omschrijving"] == "Werkvoorbereider"
    assert data["keuze_label"] == "Werkvoorbereider"


def test_keuze_naar_inschaling_ladder():
    data = keuze_naar_inschaling("ladder:8", niveau_override=4)
    assert data["functieladder_nummer"] == 8
    assert data["bevestigd_niveau"] == 4
