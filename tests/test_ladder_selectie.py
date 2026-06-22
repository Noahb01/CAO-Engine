"""Tests voor functieladder-selectie (laag 2) in inschaling_engine_v2."""

from datetime import date

import pytest

from contract_generator import genereer_volledig_voorstel
from inschaling_engine_v2 import (
    Inschaling,
    bereken,
    bouw_inschaling_van_ladder,
    ladder_context,
    selecteerbare_niveaus,
    valideer_ladder_niveau_keuze,
)
from inschalingsmodel import KandidaatInput


def test_selecteerbare_niveaus_ladder_1():
    opties = selecteerbare_niveaus(1)
    assert len(opties) == 6
    n4 = next(o for o in opties if o.niveau == 4)
    assert n4.in_matrix is True
    assert n4.status == "ingevuld"
    assert n4.karakteristiek


def test_selecteerbare_niveaus_onbekende_ladder():
    with pytest.raises(ValueError, match="niet gevonden"):
        selecteerbare_niveaus(99)


def test_valideer_ladder_leeg_niveau_waarschuwt():
    waarschuwingen = valideer_ladder_niveau_keuze(1, 2)
    assert any("geen karakteristiek" in w for w in waarschuwingen)


def test_valideer_ladder_intredekeuring():
    waarschuwingen = valideer_ladder_niveau_keuze(1, 4)
    assert any("intredekeuring" in w for w in waarschuwingen)


def test_bouw_inschaling_van_ladder():
    ins = bouw_inschaling_van_ladder(
        ladder_nummer=8,
        niveau=4,
        peildatum=date(2026, 3, 1),
        salarisverwachting_per_uur=22.0,
        marge_pct=15.0,
    )
    assert ins.functieladder_nummer == 8
    assert ins.functieniveau == 4


def test_bereken_met_functieladder_vult_resultaat():
    ins = bouw_inschaling_van_ladder(
        ladder_nummer=8,
        niveau=4,
        peildatum=date(2026, 3, 1),
        salarisverwachting_per_uur=22.0,
    )
    r = bereken(ins)
    assert r.functieladder_nummer == 8
    assert r.functieladder_naam == "Beheer van materiaal en bouwmateriaal"
    assert r.ladder_karakteristiek_status == "ingevuld"
    assert r.ladder_karakteristiek
    assert r.band_min <= r.bruto_uurloon <= r.band_max


def test_ladder_context():
    ctx = ladder_context(11, 4)
    assert ctx["naam"] == "Administratie algemeen"
    assert ctx["gekozen_niveau"] == 4
    assert any("zie ook" in w for w in ctx["waarschuwingen"])


def test_pipeline_met_functietitel():
    result = genereer_volledig_voorstel(
        kandidaat=KandidaatInput(
            functie_omschrijving="Uitvoerder",
            jaren_relevante_ervaring=5,
            leeftijd=35,
            salarisverwachting_per_uur=24.0,
            peildatum=date(2026, 3, 1),
        ),
        kandidaat_naam="Test",
        opdrachtgever="Bureau",
    )
    assert result["gebruikt_niveau"] == 4
    assert "functieladder" in result
    assert result["functieladder"]["nummer"] == 1
    assert result["berekening"].functieladder_naam == "Uitvoering"


def test_pipeline_onbekende_functietitel_fout():
    with pytest.raises(ValueError, match="UTA-functielijst"):
        genereer_volledig_voorstel(
            kandidaat=KandidaatInput(
                functie_omschrijving="Onbekende rol xyz",
                jaren_relevante_ervaring=5,
                leeftijd=35,
                peildatum=date(2026, 3, 1),
            ),
            kandidaat_naam="Test",
            opdrachtgever="Bureau",
        )
