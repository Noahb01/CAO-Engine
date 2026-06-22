"""Tests voor contract_generator pipeline."""

from datetime import date

import pytest

from contract_generator import genereer_volledig_voorstel
from functie_ladder_mapping import verrijk_mapping, mapping_voor_functie
from inschalingsmodel import KandidaatInput


def _kandidaat(**kwargs) -> KandidaatInput:
    defaults = {
        "functie_omschrijving": "Werkvoorbereider",
        "jaren_relevante_ervaring": 6.0,
        "leeftijd": 34,
        "peildatum": date(2026, 3, 1),
    }
    defaults.update(kwargs)
    return KandidaatInput(**defaults)


def test_werkvoorbereider_niveau_uit_mapping():
    result = genereer_volledig_voorstel(
        kandidaat=_kandidaat(salarisverwachting_per_uur=24.50),
        kandidaat_naam="Jan Jansen",
        opdrachtgever="Test BV",
        marge_pct=15.0,
    )
    assert result["gebruikt_niveau"] == 3
    assert result["inschaling"].voorgesteld_niveau == 3
    assert result["functieladder"]["nummer"] == 3
    assert "Werkvoorbereider" in result["niveau_bron"]


def test_bevestigd_niveau_overschrijft_mapping():
    result = genereer_volledig_voorstel(
        kandidaat=_kandidaat(),
        kandidaat_naam="Jan Jansen",
        opdrachtgever="Test BV",
        bevestigd_niveau=4,
    )
    assert result["gebruikt_niveau"] == 4
    assert result["voorgesteld_niveau"] == 3
    assert result["niveau_bijgesteld"] is True
    assert "3 naar 4" in result["niveau_bijstelling"]


def test_onbekende_functie_geeft_fout():
    with pytest.raises(ValueError, match="staat niet in de UTA-functielijst"):
        genereer_volledig_voorstel(
            kandidaat=_kandidaat(functie_omschrijving="unieke functie xyz"),
            kandidaat_naam="Jan Jansen",
            opdrachtgever="Test BV",
        )


def test_verrijk_mapping_toelichting_en_matrix_signaal():
    mapping = mapping_voor_functie("Senior projectleider")
    enriched = verrijk_mapping(mapping)
    assert enriched["toelichting"] == mapping.mapping_opmerking
    assert enriched["matrix_signaal"] is not None
    assert "standaard CAO-laddertredes" in enriched["matrix_signaal"]
    assert "mapping_opmerking" not in enriched


def test_werkvoorbereider_geen_matrix_signaal():
    mapping = mapping_voor_functie("Werkvoorbereider")
    enriched = verrijk_mapping(mapping)
    assert enriched["matrix_signaal"] is None


def test_bureau_overzicht_toont_inschaling_keten():
    result = genereer_volledig_voorstel(
        kandidaat=_kandidaat(salarisverwachting_per_uur=24.50),
        kandidaat_naam="Jan Jansen",
        opdrachtgever="Test BV",
        marge_pct=15.0,
    )
    overzicht = result["bureau_overzicht"]
    assert "--- Inschaling ---" in overzicht
    assert "Functietitel:            Werkvoorbereider" in overzicht
    assert "Functieladder:           ladder 3 — Werkvoorbereiding" in overzicht
    assert "Niveau:                  Niveau 3 - Zelfstandig" in overzicht
    assert "CAO PM: zie ook" not in overzicht


def test_bureau_overzicht_niveau_bijstelling_in_keten():
    result = genereer_volledig_voorstel(
        kandidaat=_kandidaat(),
        kandidaat_naam="Jan Jansen",
        opdrachtgever="Test BV",
        bevestigd_niveau=4,
    )
    assert "Niveau handmatig bijgesteld van 3 naar 4" in result["bureau_overzicht"]


def test_bureau_overzicht_pm_als_toelichting_bij_ladder():
    result = genereer_volledig_voorstel(
        kandidaat=_kandidaat(functie_omschrijving="Contractmanager"),
        kandidaat_naam="Test",
        opdrachtgever="Bureau",
    )
    overzicht = result["bureau_overzicht"]
    assert "Verwante ladders voor deze functie:" in overzicht
    assert "CAO PM: zie ook" not in overzicht


def test_kandidaat_overzicht_toont_functietitel_en_niveau():
    result = genereer_volledig_voorstel(
        kandidaat=_kandidaat(),
        kandidaat_naam="Jan Jansen",
        opdrachtgever="Test BV",
    )
    overzicht = result["kandidaat_overzicht"]
    assert "Functietitel:   Werkvoorbereider" in overzicht
    assert "Functieniveau:  Niveau 3 - Zelfstandig" in overzicht
    assert "Functieladder" not in overzicht
    assert "--- Kostprijs" not in overzicht


def test_bureau_overzicht_zonder_functietitel():
    from inschaling_engine_v2 import bereken_tarief_direct

    from contract_generator import genereer_bureau_overzicht

    b = bereken_tarief_direct(functieniveau=4, peildatum=date(2026, 3, 1))
    overzicht = genereer_bureau_overzicht(
        b, "Test", "Bureau", peildatum=date(2026, 3, 1), functie_titel=None
    )
    assert "Functietitel:            niet opgegeven" in overzicht
    assert "Functieladder:           niet van toepassing" in overzicht
