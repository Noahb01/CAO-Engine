"""Tests voor uur ↔ maand salarisconversie."""

from cao_data import (
    UREN_PER_MAAND,
    bereken_maandsalaris,
    bereken_uurloon_uit_maandsalaris,
)


def test_maand_naar_uur_en_terug():
    uurloon = 24.50
    maand = bereken_maandsalaris(uurloon)
    assert maand == 4246.59
    assert bereken_uurloon_uit_maandsalaris(maand) == uurloon


def test_uren_per_maand_constant():
    assert UREN_PER_MAAND == 173.33
