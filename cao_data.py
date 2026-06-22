"""
CAO Bouw & Infra 2025-2027 — Gedeeld datamodel voor loontabellen en validatie.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from pydantic import BaseModel, Field


CAO_START = date(2025, 5, 1)
CAO_EINDE = date(2027, 12, 31)
MIN_FUNCTIENIVEAU = 1
MAX_FUNCTIENIVEAU = 6
ADV_PERCENTAGE = 6.8
VAKANTIEGELD_PERCENTAGE = 8.0
UREN_PER_MAAND = 173.33  # 40 uur/week × 52 / 12
UREN_PER_VIER_WEKEN = 160.0  # 40 uur/week × 4


def _round2(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def bereken_maandsalaris(uurloon: float) -> float:
    return _round2(uurloon * UREN_PER_MAAND)


def bereken_uurloon_uit_maandsalaris(maandsalaris: float) -> float:
    """Zet bruto maandsalaris om naar uurloon (CAO: 173,33 uur/maand)."""
    return _round2(maandsalaris / UREN_PER_MAAND)


def bereken_vier_weken_salaris(uurloon: float) -> float:
    return _round2(uurloon * UREN_PER_VIER_WEKEN)


class Loonband(BaseModel):
    """Minimum en maximum uurloon voor een functieniveau op een peildatum."""
    minimum: float
    maximum: float


FUNCTIENIVEAU_KENMERKEN = {
    1: {
        "naam": "Niveau 1 - Ondersteunend / startend",
        "kenmerk": "Eenvoudige, routinematige taken onder directe begeleiding.",
        "indicatie_ervaring": "0-1 jaar",
    },
    2: {
        "naam": "Niveau 2 - Uitvoerend",
        "kenmerk": "Uitvoerende taken met enige zelfstandigheid binnen duidelijke kaders.",
        "indicatie_ervaring": "1-3 jaar",
    },
    3: {
        "naam": "Niveau 3 - Zelfstandig uitvoerend",
        "kenmerk": "Zelfstandige uitvoering van taken die vakkennis en ervaring vragen.",
        "indicatie_ervaring": "3-6 jaar",
    },
    4: {
        "naam": "Niveau 4 - Specialist / coordinerend",
        "kenmerk": "Complexe taken, eigen vakgebied, soms aansturing van anderen.",
        "indicatie_ervaring": "5-10 jaar",
    },
    5: {
        "naam": "Niveau 5 - Senior specialist / leidinggevend",
        "kenmerk": "Brede verantwoordelijkheid, leiding over projecten of teams.",
        "indicatie_ervaring": "8-15 jaar",
    },
    6: {
        "naam": "Niveau 6 - Hogere staf / management",
        "kenmerk": "Strategische of zwaar coordinerende functie met grote verantwoordelijkheid.",
        "indicatie_ervaring": "12+ jaar",
    },
}

# Tabel 4.9 — Salaris UTA-werknemer 21 jaar of ouder
LOONTABELLEN_21PLUS: dict[date, dict[int, Loonband]] = {
    date(2025, 5, 1): {
        1: Loonband(minimum=15.01, maximum=19.55),
        2: Loonband(minimum=16.44, maximum=21.72),
        3: Loonband(minimum=18.27, maximum=24.46),
        4: Loonband(minimum=20.66, maximum=28.08),
        5: Loonband(minimum=23.77, maximum=32.78),
        6: Loonband(minimum=27.82, maximum=38.85),
    },
    date(2025, 7, 1): {
        1: Loonband(minimum=15.16, maximum=19.75),
        2: Loonband(minimum=16.60, maximum=21.94),
        3: Loonband(minimum=18.45, maximum=24.70),
        4: Loonband(minimum=20.87, maximum=28.36),
        5: Loonband(minimum=24.01, maximum=33.11),
        6: Loonband(minimum=28.10, maximum=39.24),
    },
    date(2026, 1, 1): {
        1: Loonband(minimum=15.77, maximum=20.54),
        2: Loonband(minimum=17.26, maximum=22.82),
        3: Loonband(minimum=19.19, maximum=25.69),
        4: Loonband(minimum=21.70, maximum=29.49),
        5: Loonband(minimum=24.97, maximum=34.43),
        6: Loonband(minimum=29.22, maximum=40.81),
    },
    date(2027, 1, 1): {
        1: Loonband(minimum=16.01, maximum=20.85),
        2: Loonband(minimum=17.52, maximum=23.16),
        3: Loonband(minimum=19.48, maximum=26.08),
        4: Loonband(minimum=22.03, maximum=29.93),
        5: Loonband(minimum=25.34, maximum=34.95),
        6: Loonband(minimum=29.66, maximum=41.42),
    },
}

# Tabel starttabel UTA 21+ (art. 4.11) — max. 1 jaar, nieuw in bouw & infra
STARTTABEL_21PLUS: dict[date, dict[str, Optional[float]]] = {
    date(2025, 5, 1): {"halfjaar_1": 14.30, "halfjaar_2": 14.54},
    date(2025, 7, 1): {"halfjaar_1": 14.59, "halfjaar_2": 14.78},
    date(2026, 1, 1): {"halfjaar_1": 14.98, "halfjaar_2": 15.24},
    date(2027, 1, 1): {"halfjaar_1": None, "halfjaar_2": None},
}

# Doorgroeigarantie UTA 21+ (art. 4.9.2) — effectief minimum na diensttijd op niveau
DOORGROEI_GARANTIE: dict[int, float] = {
    0: 1.00,
    2: 1.04,
    4: 1.10,
    6: 1.16,
}


def effectief_minimum(band: Loonband, jaren_op_niveau: float) -> tuple[float, float]:
    """Effectief CAO-minimum na doorgroeigarantie: (bedrag, percentage)."""
    pct = DOORGROEI_GARANTIE[0]
    for drempel in sorted(DOORGROEI_GARANTIE.keys()):
        if jaren_op_niveau >= drempel:
            pct = DOORGROEI_GARANTIE[drempel]
    return _round2(band.minimum * pct), pct


def doorgroei_lijn(band: Loonband) -> dict[str, float]:
    """Minimum bij 0/2/4/6 jaar op niveau (ter info)."""
    return {
        "0_jaar": _round2(band.minimum * 1.00),
        "2_jaar_104pct": _round2(band.minimum * 1.04),
        "4_jaar_110pct": _round2(band.minimum * 1.10),
        "6_jaar_116pct": _round2(band.minimum * 1.16),
    }


def get_starttabel(peildatum: date, tweede_halfjaar: bool = False) -> tuple[date, Optional[float]]:
    """Starttabel-uurloon voor nieuw in bouw & infra. Bedrag kan None zijn (nntb)."""
    valideer_cao_periode(peildatum)
    datums = sorted(STARTTABEL_21PLUS.keys())
    gekozen: Optional[date] = None
    for d in datums:
        if d <= peildatum:
            gekozen = d
        else:
            break
    if gekozen is None:
        raise ValueError(
            f"Peildatum {peildatum} ligt voor de eerste starttabel ({datums[0]})."
        )
    sleutel = "halfjaar_2" if tweede_halfjaar else "halfjaar_1"
    return gekozen, STARTTABEL_21PLUS[gekozen][sleutel]


def valideer_functieniveau(functieniveau: int) -> None:
    if not MIN_FUNCTIENIVEAU <= functieniveau <= MAX_FUNCTIENIVEAU:
        raise ValueError(
            f"Functieniveau moet tussen {MIN_FUNCTIENIVEAU} en "
            f"{MAX_FUNCTIENIVEAU} liggen, got {functieniveau}."
        )


def valideer_cao_periode(peildatum: date) -> None:
    if peildatum < CAO_START or peildatum > CAO_EINDE:
        raise ValueError(
            f"Peildatum {peildatum} valt buiten CAO-periode "
            f"({CAO_START} t/m {CAO_EINDE})."
        )


def get_peildatum_tabel(peildatum: date) -> date:
    """Kies de meest recente CAO-tabel die op of vóór de peildatum ingaat."""
    valideer_cao_periode(peildatum)
    geldige_datums = sorted(LOONTABELLEN_21PLUS.keys())
    gekozen: Optional[date] = None
    for d in geldige_datums:
        if d <= peildatum:
            gekozen = d
        else:
            break
    if gekozen is None:
        raise ValueError(
            f"Peildatum {peildatum} ligt voor de eerste CAO-tabel "
            f"({geldige_datums[0]})."
        )
    return gekozen


def get_loontabel(peildatum: date) -> dict[int, Loonband]:
    """Alle loonbanden voor de geldende tabel op peildatum."""
    peildatum_tabel = get_peildatum_tabel(peildatum)
    return LOONTABELLEN_21PLUS[peildatum_tabel]


def get_loonband(functieniveau: int, peildatum: date) -> Loonband:
    valideer_functieniveau(functieniveau)
    tabel = get_loontabel(peildatum)
    return tabel[functieniveau]


def get_cao_info(functieniveau: int, peildatum: date) -> dict:
    """CAO min/max en metadata voor API."""
    band = get_loonband(functieniveau, peildatum)
    peildatum_tabel = get_peildatum_tabel(peildatum)
    kenmerk = FUNCTIENIVEAU_KENMERKEN[functieniveau]
    return {
        "functieniveau": functieniveau,
        "peildatum": peildatum,
        "peildatum_tabel": peildatum_tabel,
        "minimum_uurloon": band.minimum,
        "maximum_uurloon": band.maximum,
        "niveau_naam": kenmerk["naam"],
        "indicatie_ervaring": kenmerk["indicatie_ervaring"],
    }


def lijst_cao_tabellen() -> list[dict]:
    """Alle beschikbare CAO-tabellen met ingangsdatum."""
    return [
        {
            "ingangsdatum": d.isoformat(),
            "functieniveaus": {
                str(n): {"minimum": b.minimum, "maximum": b.maximum}
                for n, b in sorted(niveaus.items())
            },
        }
        for d, niveaus in sorted(LOONTABELLEN_21PLUS.items())
    ]
