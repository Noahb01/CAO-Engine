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
