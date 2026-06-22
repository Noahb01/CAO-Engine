"""Tests voor bereken_omrekenfactor (Model A)."""

import pytest

from inschaling_engine_v2 import WerkgeverslastenConfig, bereken_omrekenfactor


def test_default_omrekenfactor_rond_191():
    factor, opbouw = bereken_omrekenfactor()
    assert factor == pytest.approx(1.9094, rel=1e-3)
    assert "duurzame_inzetbaarheid_pct" in opbouw
    assert opbouw["premie_factor"] == pytest.approx(1.507, rel=1e-3)


def test_override_15():
    factor, opbouw = bereken_omrekenfactor(override=1.5)
    assert factor == 1.5
    assert opbouw["vaste_factor_gebruikt"] == 1.5


def test_custom_premies_hogere_factor():
    config = WerkgeverslastenConfig(
        vakantietoeslag_pct=10.0,
        pensioen_bpfbouw_pct=20.0,
        sociale_lasten_pct=20.0,
        sociaal_fonds_scholing_pct=3.0,
        verzuim_risico_pct=5.0,
    )
    default_factor, _ = bereken_omrekenfactor()
    custom_factor, opbouw = bereken_omrekenfactor(config)
    assert custom_factor > default_factor
    assert opbouw["vakantietoeslag_pct"] == 10.0
