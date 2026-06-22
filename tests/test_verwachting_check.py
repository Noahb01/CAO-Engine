"""Tests voor afgestemde salarisverwachting-check (leidend niveau)."""

from datetime import date

from contract_generator import genereer_volledig_voorstel
from inschalingsmodel import KandidaatInput, check_salarisverwachting


def test_check_gebruikt_effectief_minimum():
    past, opmerking = check_salarisverwachting(
        date(2026, 3, 1),
        functieniveau=3,
        salarisverwachting_per_uur=20.00,
        jaren_op_niveau=5,
    )
    assert past is False
    assert "21.11" in opmerking
    assert "effectief minimum" in opmerking.lower()


def test_check_past_op_leidend_niveau():
    past, opmerking = check_salarisverwachting(
        date(2026, 3, 1),
        functieniveau=3,
        salarisverwachting_per_uur=24.50,
        jaren_op_niveau=0,
    )
    assert past is True
    assert "niveau 3" in opmerking


def test_pipeline_oordeel_matcht_berekening():
    result = genereer_volledig_voorstel(
        kandidaat=KandidaatInput(
            functie_omschrijving="Werkvoorbereider",
            jaren_relevante_ervaring=6,
            leeftijd=34,
            salarisverwachting_per_uur=20.00,
            peildatum=date(2026, 3, 1),
        ),
        kandidaat_naam="Test",
        opdrachtgever="BV",
        bevestigd_niveau=3,
        jaren_op_niveau=5,
    )
    ins = result["inschaling"]
    ber = result["berekening"]
    assert ins.verwachting_past_in_band is False
    assert "21.11" in ins.verwachting_opmerking
    assert ber.bruto_uurloon == 21.11
    assert "21.11" in ber.bruto_bron


def test_pipeline_werkvoorbereider_2450_aligned():
    result = genereer_volledig_voorstel(
        kandidaat=KandidaatInput(
            functie_omschrijving="Werkvoorbereider",
            jaren_relevante_ervaring=6,
            leeftijd=34,
            salarisverwachting_per_uur=24.50,
            peildatum=date(2026, 3, 1),
        ),
        kandidaat_naam="Jan",
        opdrachtgever="BV",
        bevestigd_niveau=3,
    )
    ins = result["inschaling"]
    ber = result["berekening"]
    assert ins.verwachting_past_in_band is True
    assert "niveau 3" in ins.verwachting_opmerking
    assert ber.bruto_uurloon == 24.50
