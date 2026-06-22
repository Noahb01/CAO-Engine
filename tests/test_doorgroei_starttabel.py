"""Tests doorgroeigarantie en starttabel (v2.1)."""

from datetime import date

import pytest

from cao_data import effectief_minimum, get_loonband, get_starttabel
from inschaling_engine_v2 import Inschaling, TredePositie, VerwachtingActie, bereken


def test_effectief_minimum_5_jaar_niveau_3():
    band = get_loonband(3, date(2026, 3, 1))
    eff, pct = effectief_minimum(band, 5)
    assert eff == 21.11
    assert pct == 1.10


def test_verwachting_onder_effectief_minimum_wordt_gecorrigeerd():
    r = bereken(
        Inschaling(
            functieniveau=3,
            peildatum=date(2026, 3, 1),
            jaren_op_niveau=5,
            salarisverwachting_per_uur=20.00,
            marge_pct=15.0,
        )
    )
    assert r.effectief_minimum == 21.11
    assert r.bruto_uurloon == 21.11


def test_starttabel_nieuw_in_bouw_infra():
    r = bereken(
        Inschaling(
            functieniveau=2,
            peildatum=date(2026, 3, 1),
            nieuw_in_bouw_infra=True,
            starttabel_tweede_halfjaar=False,
            marge_pct=15.0,
        )
    )
    assert r.starttabel_toegepast is True
    assert r.bruto_uurloon == 14.98


def test_starttabel_nntb_waarschuwing():
    _, bedrag = get_starttabel(date(2027, 6, 1), False)
    assert bedrag is None
    r = bereken(
        Inschaling(
            functieniveau=2,
            peildatum=date(2027, 6, 1),
            nieuw_in_bouw_infra=True,
        )
    )
    assert r.starttabel_toegepast is False
    assert any("nntb" in w.lower() for w in r.waarschuwingen)


def test_blokkeer_onder_effectief_minimum():
    with pytest.raises(ValueError, match="effectieve CAO-minimum"):
        bereken(
            Inschaling(
                functieniveau=3,
                peildatum=date(2026, 3, 1),
                jaren_op_niveau=6,
                salarisverwachting_per_uur=20.00,
                verwachting_actie=VerwachtingActie.BLOKKEER,
            )
        )
