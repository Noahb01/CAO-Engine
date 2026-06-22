"""Tests voor inschaling_engine_v2.bereken()."""

from datetime import date

import pytest

from inschaling_engine_v2 import (
    Inschaling,
    TredePositie,
    VerwachtingActie,
    bereken,
)


def test_verwachting_in_band_gebruikt_verwachting():
    ins = Inschaling(
        functieniveau=4,
        peildatum=date(2026, 3, 1),
        positie_in_band=TredePositie.MIDDEN,
        salarisverwachting_per_uur=24.50,
        marge_pct=15.0,
    )
    r = bereken(ins)
    assert r.bruto_uurloon == 24.50
    assert r.band_min <= r.bruto_uurloon <= r.band_max


def test_facturatie_is_kostprijs_plus_marge():
    ins = Inschaling(
        functieniveau=4,
        peildatum=date(2026, 3, 1),
        salarisverwachting_per_uur=24.50,
        marge_pct=15.0,
    )
    r = bereken(ins)
    verwacht = round(r.kostprijs_per_uur * 1.15, 2)
    assert r.facturatie_per_uur == verwacht
    assert r.totaal_factor_op_bruto == pytest.approx(
        r.facturatie_per_uur / r.bruto_uurloon, abs=0.01
    )


def test_verwachting_onder_minimum_corrigeert():
    ins = Inschaling(
        functieniveau=5,
        peildatum=date(2026, 1, 1),
        salarisverwachting_per_uur=20.00,
        verwachting_actie=VerwachtingActie.CORRIGEER_NAAR_MINIMUM,
        marge_pct=15.0,
    )
    r = bereken(ins)
    assert r.bruto_uurloon == r.band_min
    assert any("effectief minimum" in w.lower() for w in r.waarschuwingen)


def test_verwachting_onder_minimum_blokkeert():
    ins = Inschaling(
        functieniveau=5,
        peildatum=date(2026, 1, 1),
        salarisverwachting_per_uur=20.00,
        verwachting_actie=VerwachtingActie.BLOKKEER,
    )
    with pytest.raises(ValueError, match="geblokkeerd"):
        bereken(ins)
