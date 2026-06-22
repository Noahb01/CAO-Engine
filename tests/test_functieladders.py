"""Tests voor bijlage 1.3 functieladders (laag 1)."""

import json

import pytest

from functieladders_bijlage_1_3 import (
    FUNCTIELADDERS,
    FUNCTIENIVEAU_MATRIX,
    export_json,
    ladders_met_lege_niveaus,
    ladders_met_pm_verwijzingen,
    lijst_functieladders,
    niveau_karakteristiek,
    zoek_ladder,
    zoek_ladder_op_naam,
)


def test_25_ladders_aanwezig():
    assert len(FUNCTIELADDERS) == 25
    nummers = [l.nummer for l in FUNCTIELADDERS]
    assert nummers == list(range(1, 26))


def test_matrix_dekt_alle_ladders():
    assert set(FUNCTIENIVEAU_MATRIX.keys()) == set(range(1, 26))


def test_intredekeuring_alleen_ladder_1():
    for l in FUNCTIELADDERS:
        if l.nummer == 1:
            assert l.intredekeuring_verplicht is True
        else:
            assert l.intredekeuring_verplicht is False


def test_zoek_ladder():
    ladder = zoek_ladder(1)
    assert ladder is not None
    assert ladder.naam == "Uitvoering"
    assert zoek_ladder(99) is None


def test_zoek_ladder_op_naam():
    ladder = zoek_ladder_op_naam("Maatvoering")
    assert ladder is not None
    assert ladder.nummer == 25


def test_niveau_karakteristiek_ingevuld_en_leeg():
    n5 = niveau_karakteristiek(1, 5)
    assert n5 is not None
    assert n5.status == "ingevuld"
    assert n5.karakteristiek

    n2 = niveau_karakteristiek(1, 2)
    assert n2 is not None
    assert n2.status == "leeg_in_cao"
    assert n2.karakteristiek is None


def test_pm_verwijzingen_administratie_ladder():
    ladder = zoek_ladder(11)
    assert ladder is not None
    assert len(ladder.pm_verwijzingen) == 4
    assert "Boekhouding" in ladder.pm_verwijzingen


def test_ladders_met_pm_verwijzingen():
    pm_ladders = ladders_met_pm_verwijzingen()
    nummers = {item["nummer"] for item in pm_ladders}
    assert 6 in nummers  # Marketing en verkoop
    assert 7 in nummers  # Inkoop
    assert 11 in nummers


def test_lijst_functieladders_structuur():
    lijst = lijst_functieladders()
    assert len(lijst) == 25
    eerste = lijst[0]
    assert set(eerste.keys()) == {
        "nummer",
        "naam",
        "intredekeuring_verplicht",
        "beschikbare_niveaus",
        "lege_niveaus",
        "matrix_niveaus",
        "pm_verwijzingen",
    }


def test_lege_niveaus_niet_verzonnen():
    """Elke lege karakteristiek moet expliciet leeg_in_cao zijn."""
    for ladder in FUNCTIELADDERS:
        for n in ladder.niveaus:
            if n.status == "leeg_in_cao":
                assert n.karakteristiek is None
            else:
                assert n.karakteristiek


def test_export_json_valide():
    data = json.loads(export_json())
    assert len(data) == 25
    assert data[0]["naam"] == "Uitvoering"


def test_ladder_24_en_25_matrix_vs_karakteristieken():
    """CAO-matrix en karakteristieken wijken af — dat moet zichtbaar blijven."""
    l24 = zoek_ladder(24)
    assert l24 is not None
    assert l24.beschikbare_niveaus == [4, 5]
    assert FUNCTIENIVEAU_MATRIX[24] == [1, 2]

    l25 = zoek_ladder(25)
    assert l25 is not None
    assert l25.beschikbare_niveaus == [4]
    assert FUNCTIENIVEAU_MATRIX[25] == [1]


def test_ladders_met_lege_niveaus_niet_leeg():
    result = ladders_met_lege_niveaus()
    assert len(result) > 0
    assert all(item["lege_niveaus"] for item in result)
