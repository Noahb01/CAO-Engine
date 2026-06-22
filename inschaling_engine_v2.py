"""
INSCHALING + KOSTPRIJS ENGINE - CAO Bouw & Infra UTA
=====================================================
Versie 2.1 — doorgroeigarantie, starttabel, duurzame inzetbaarheid

- Doorgroeigarantie (art. 4.9.2): effectief minimum op basis van jaren_op_niveau
- Starttabel (art. 4.11): nieuw_in_bouw_infra vertakking
- Individueel Budget / duurzame inzetbaarheid 2,30% in omrekenfactor (art. 4.14)
- Kostprijs MODEL A: bruto × omrekenfactor; marge % op kostprijs
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from cao_data import (
    FUNCTIENIVEAU_KENMERKEN,
    Loonband,
    doorgroei_lijn,
    effectief_minimum,
    get_loonband,
    get_peildatum_tabel,
    get_starttabel,
    valideer_cao_periode,
    valideer_functieniveau,
)
from functieladders_bijlage_1_3 import (
    FUNCTIENIVEAU_MATRIX,
    niveau_karakteristiek,
    zoek_ladder,
)
from functies import zoek_functie


WERKBARE_DAGEN_PER_JAAR = 261
UTA_VAKANTIEDAGEN = 20
UTA_BOVENWETTELIJK = 10
UTA_ROOSTERVRIJE_DAGEN = 15
UTA_KORT_VERZUIM = 3
GEM_FEESTDAGEN = 7

NETTO_WERKBARE_DAGEN = (
    WERKBARE_DAGEN_PER_JAAR
    - UTA_VAKANTIEDAGEN
    - UTA_BOVENWETTELIJK
    - UTA_ROOSTERVRIJE_DAGEN
    - UTA_KORT_VERZUIM
    - GEM_FEESTDAGEN
)


class WerkgeverslastenConfig(BaseModel):
    """Werkgeverspremies en reserveringen. Defaults zijn INDICATIEF."""

    vakantietoeslag_pct: float = Field(8.0, description="CAO: 8% — hard")
    duurzame_inzetbaarheid_pct: float = Field(
        2.30, description="Individueel Budget UTA 2026 (art. 4.14) — hard CAO"
    )
    pensioen_bpfbouw_pct: float = Field(15.9, description="bpfBOUW werkgeversdeel — indicatief")
    sociale_lasten_pct: float = Field(18.0, description="WW/WIA/ZVW — indicatief")
    sociaal_fonds_scholing_pct: float = Field(2.5, description="O&O-fonds — indicatief")
    verzuim_risico_pct: float = Field(4.0, description="Verzuimreserve — indicatief")

    @property
    def som_premies_pct(self) -> float:
        return (
            self.pensioen_bpfbouw_pct
            + self.sociale_lasten_pct
            + self.sociaal_fonds_scholing_pct
            + self.verzuim_risico_pct
        )


class TredePositie(str, Enum):
    MINIMUM = "minimum"
    ONDER = "onderkant"
    MIDDEN = "midden"
    BOVEN = "bovenkant"
    MAXIMUM = "maximum"


_POSITIE_FACTOR = {
    TredePositie.MINIMUM: 0.0,
    TredePositie.ONDER: 0.25,
    TredePositie.MIDDEN: 0.5,
    TredePositie.BOVEN: 0.75,
    TredePositie.MAXIMUM: 1.0,
}


def _round2(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def loon_in_band(band: Loonband, positie: TredePositie) -> float:
    span = band.maximum - band.minimum
    return _round2(band.minimum + span * _POSITIE_FACTOR[positie])


def bereken_omrekenfactor(
    config: Optional[WerkgeverslastenConfig] = None,
    override: Optional[float] = None,
) -> tuple[float, dict]:
    if override is not None:
        return override, {
            "vaste_factor_gebruikt": override,
            "let_op": "Vaste factor opgegeven; opbouw niet berekend.",
        }

    if config is None:
        config = WerkgeverslastenConfig()

    premie_factor = 1 + (
        config.som_premies_pct
        + config.vakantietoeslag_pct
        + config.duurzame_inzetbaarheid_pct
    ) / 100
    productiviteit_correctie = WERKBARE_DAGEN_PER_JAAR / NETTO_WERKBARE_DAGEN
    factor = round(premie_factor * productiviteit_correctie, 4)

    return factor, {
        "vakantietoeslag_pct": config.vakantietoeslag_pct,
        "duurzame_inzetbaarheid_pct": config.duurzame_inzetbaarheid_pct,
        "som_premies_pct": round(config.som_premies_pct, 2),
        "premie_factor": round(premie_factor, 4),
        "werkbare_dagen": WERKBARE_DAGEN_PER_JAAR,
        "netto_werkbare_dagen": NETTO_WERKBARE_DAGEN,
        "productiviteit_correctie": round(productiviteit_correctie, 4),
        "let_op": "Premies zijn INDICATIEF en werkgeverspecifiek.",
    }


class VerwachtingActie(str, Enum):
    CORRIGEER_NAAR_MINIMUM = "corrigeer_naar_minimum"
    BLOKKEER = "blokkeer"


class Inschaling(BaseModel):
    kandidaat_naam: str = ""
    functieniveau: int = Field(..., ge=1, le=6, description="LEIDEND — door inschaler bevestigd.")
    functieladder_nummer: Optional[int] = Field(
        None,
        ge=1,
        le=25,
        description="Optioneel: gekozen functieladder bijlage 1.3 (context + validatie).",
    )
    peildatum: date = Field(default_factory=date.today)
    positie_in_band: TredePositie = TredePositie.MIDDEN
    salarisverwachting_per_uur: Optional[float] = None
    verwachting_actie: VerwachtingActie = VerwachtingActie.CORRIGEER_NAAR_MINIMUM
    nieuw_in_bouw_infra: bool = Field(
        False, description="Nog nooit in bouw & infra: starttabel (max 1 jaar, art. 4.11)."
    )
    starttabel_tweede_halfjaar: bool = Field(
        False, description="Bij starttabel: False=1e halfjaar, True=2e halfjaar."
    )
    jaren_op_niveau: float = Field(
        0.0, ge=0, description="Diensttijd op dit niveau voor doorgroeigarantie (art. 4.9.2)."
    )
    omrekenfactor_override: Optional[float] = Field(
        None, description="Vaste factor i.p.v. opbouw uit premies."
    )
    marge_pct: float = Field(0.0, ge=0, description="Marge % bovenop kostprijs.")


class Resultaat(BaseModel):
    cao_tabel: date
    functieniveau: int
    niveau_naam: str
    functieladder_nummer: Optional[int] = None
    functieladder_naam: Optional[str] = None
    ladder_karakteristiek: Optional[str] = None
    ladder_karakteristiek_status: Optional[str] = None
    band_min: float
    band_max: float
    netto_werkbare_dagen: int
    starttabel_toegepast: bool
    effectief_minimum: float
    doorgroei_percentage: float
    doorgroei_lijn: dict
    bruto_uurloon: float
    bruto_bron: str
    verwachting_status: str
    omrekenfactor: float
    factor_opbouw: dict
    kostprijs_per_uur: float
    marge_pct: float
    facturatie_per_uur: float
    totaal_factor_op_bruto: float
    waarschuwingen: List[str]


class LadderNiveauOptie(BaseModel):
    """Niveau binnen een functieladder — voor selectie (laag 2)."""

    niveau: int
    status: str
    karakteristiek: Optional[str] = None
    in_matrix: bool
    selecteerbaar: bool = Field(
        description="True als niveau in de CAO-matrix voorkomt (aanbevolen keuze).",
    )


def selecteerbare_niveaus(ladder_nummer: int) -> list[LadderNiveauOptie]:
    """Alle niveaus 1–6 voor een ladder, met karakteristiek en matrix-info."""
    ladder = zoek_ladder(ladder_nummer)
    if ladder is None:
        raise ValueError(f"Functieladder {ladder_nummer} niet gevonden (bijlage 1.3).")

    matrix = set(FUNCTIENIVEAU_MATRIX.get(ladder_nummer, []))
    return [
        LadderNiveauOptie(
            niveau=n.niveau,
            status=n.status,
            karakteristiek=n.karakteristiek,
            in_matrix=n.niveau in matrix,
            selecteerbaar=n.niveau in matrix,
        )
        for n in ladder.niveaus
    ]


def valideer_ladder_niveau_keuze(ladder_nummer: int, niveau: int) -> list[str]:
    """Valideer ladder+niveau; retourneert waarschuwingen (geen verzonnen invullingen)."""
    ladder = zoek_ladder(ladder_nummer)
    if ladder is None:
        raise ValueError(f"Functieladder {ladder_nummer} niet gevonden (bijlage 1.3).")

    valideer_functieniveau(niveau)
    kar = niveau_karakteristiek(ladder_nummer, niveau)
    if kar is None:
        raise ValueError(f"Niveau {niveau} is ongeldig voor ladder {ladder_nummer}.")

    waarschuwingen: List[str] = []

    if kar.status == "leeg_in_cao":
        waarschuwingen.append(
            f"CAO bijlage 1.3 heeft geen karakteristiek voor niveau {niveau} "
            f"op ladder '{ladder.naam}'."
        )

    if ladder.intredekeuring_verplicht:
        waarschuwingen.append(
            f"Ladder '{ladder.naam}' vereist intredekeuring (art. 1.1 CAO)."
        )

    if ladder.pm_verwijzingen:
        waarschuwingen.append(
            "CAO PM: zie ook " + ", ".join(ladder.pm_verwijzingen) + "."
        )

    return waarschuwingen


def ladder_context(ladder_nummer: int, niveau: int) -> dict:
    """Metadata over gekozen ladder+niveau voor API/overzichten."""
    ladder = zoek_ladder(ladder_nummer)
    if ladder is None:
        raise ValueError(f"Functieladder {ladder_nummer} niet gevonden.")

    kar = niveau_karakteristiek(ladder_nummer, niveau)
    return {
        "nummer": ladder.nummer,
        "naam": ladder.naam,
        "gekozen_niveau": niveau,
        "intredekeuring_verplicht": ladder.intredekeuring_verplicht,
        "matrix_niveaus": FUNCTIENIVEAU_MATRIX.get(ladder_nummer, []),
        "karakteristiek": kar.karakteristiek if kar else None,
        "karakteristiek_status": kar.status if kar else None,
        "pm_verwijzingen": ladder.pm_verwijzingen,
        "waarschuwingen": valideer_ladder_niveau_keuze(ladder_nummer, niveau),
    }


def _maak_resultaat(
    inschaling: Inschaling,
    cao_datum: date,
    band: Loonband,
    eff_min: float,
    doorgroei_pct: float,
    dg_lijn: dict,
    bruto: float,
    bruto_bron: str,
    verwachting_status: str,
    starttabel_toegepast: bool,
    waarschuwingen: List[str],
    config: Optional[WerkgeverslastenConfig],
    ladder_kar: Optional[str] = None,
    ladder_kar_status: Optional[str] = None,
    ladder_naam: Optional[str] = None,
    ladder_nummer: Optional[int] = None,
) -> Resultaat:
    factor, factor_opbouw = bereken_omrekenfactor(config, inschaling.omrekenfactor_override)
    kostprijs = _round2(bruto * factor)
    facturatie = _round2(kostprijs * (1 + inschaling.marge_pct / 100))
    totaal_factor = _round2(facturatie / bruto) if bruto else 0.0

    if inschaling.omrekenfactor_override is None:
        waarschuwingen.append(
            "Omrekenfactor opgebouwd met INDICATIEVE premies. "
            "Vul werkelijke werkgeverspremies in voor bindende offertes."
        )

    return Resultaat(
        cao_tabel=cao_datum,
        functieniveau=inschaling.functieniveau,
        niveau_naam=FUNCTIENIVEAU_KENMERKEN[inschaling.functieniveau]["naam"],
        functieladder_nummer=ladder_nummer,
        functieladder_naam=ladder_naam,
        ladder_karakteristiek=ladder_kar,
        ladder_karakteristiek_status=ladder_kar_status,
        band_min=band.minimum,
        band_max=band.maximum,
        netto_werkbare_dagen=NETTO_WERKBARE_DAGEN,
        starttabel_toegepast=starttabel_toegepast,
        effectief_minimum=eff_min,
        doorgroei_percentage=doorgroei_pct,
        doorgroei_lijn=dg_lijn,
        bruto_uurloon=bruto,
        bruto_bron=bruto_bron,
        verwachting_status=verwachting_status,
        omrekenfactor=factor,
        factor_opbouw=factor_opbouw,
        kostprijs_per_uur=kostprijs,
        marge_pct=inschaling.marge_pct,
        facturatie_per_uur=facturatie,
        totaal_factor_op_bruto=totaal_factor,
        waarschuwingen=waarschuwingen,
    )


def bereken(
    inschaling: Inschaling,
    config: Optional[WerkgeverslastenConfig] = None,
) -> Resultaat:
    """Volledige inschaling + kostprijs + facturatie."""
    valideer_functieniveau(inschaling.functieniveau)
    valideer_cao_periode(inschaling.peildatum)

    waarschuwingen: List[str] = []
    ladder_naam: Optional[str] = None
    ladder_kar: Optional[str] = None
    ladder_kar_status: Optional[str] = None

    if inschaling.functieladder_nummer is not None:
        ladder = zoek_ladder(inschaling.functieladder_nummer)
        if ladder is None:
            raise ValueError(
                f"Functieladder {inschaling.functieladder_nummer} niet gevonden."
            )
        ladder_naam = ladder.naam
        waarschuwingen.extend(
            valideer_ladder_niveau_keuze(
                inschaling.functieladder_nummer, inschaling.functieniveau
            )
        )
        kar = niveau_karakteristiek(
            inschaling.functieladder_nummer, inschaling.functieniveau
        )
        if kar:
            ladder_kar = kar.karakteristiek
            ladder_kar_status = kar.status

    ladder_kw = {
        "ladder_nummer": inschaling.functieladder_nummer,
        "ladder_naam": ladder_naam,
        "ladder_kar": ladder_kar,
        "ladder_kar_status": ladder_kar_status,
    }

    cao_datum = get_peildatum_tabel(inschaling.peildatum)
    band = get_loonband(inschaling.functieniveau, inschaling.peildatum)

    eff_min, doorgroei_pct = effectief_minimum(band, inschaling.jaren_op_niveau)
    dg_lijn = doorgroei_lijn(band)

    if doorgroei_pct > 1.0:
        waarschuwingen.append(
            f"Doorgroeigarantie (art. 4.9.2): na {inschaling.jaren_op_niveau:.0f} jaar op dit niveau "
            f"is het effectieve minimum EUR {eff_min:.2f} ({doorgroei_pct * 100:.0f}% van tabelminimum), "
            f"niet EUR {band.minimum:.2f}."
        )

    if inschaling.nieuw_in_bouw_infra:
        _, start_bedrag = get_starttabel(
            inschaling.peildatum, inschaling.starttabel_tweede_halfjaar
        )
        if start_bedrag is None:
            waarschuwingen.append(
                "Starttabel-bedrag is voor deze peildatum nog niet bekend (nntb in CAO; "
                "afhankelijk van het wettelijk minimumloon). Doorgerekend met de reguliere band."
            )
        else:
            halfjaar = "2e" if inschaling.starttabel_tweede_halfjaar else "1e"
            bruto_bron = (
                f"STARTTABEL toegepast ({halfjaar} halfjaar, art. 4.11): EUR {start_bedrag:.2f}. "
                f"Geldt max. 1 jaar voor wie nieuw is in bouw & infra."
            )
            return _maak_resultaat(
                inschaling,
                cao_datum,
                band,
                eff_min,
                doorgroei_pct,
                dg_lijn,
                start_bedrag,
                bruto_bron,
                "Starttabel actief; functieniveau-band niet leidend in dit jaar.",
                True,
                waarschuwingen,
                config,
                **ladder_kw,
            )

    voorstel_loon = loon_in_band(band, inschaling.positie_in_band)
    if voorstel_loon < eff_min:
        voorstel_loon = eff_min

    if inschaling.salarisverwachting_per_uur is None:
        return _maak_resultaat(
            inschaling,
            cao_datum,
            band,
            eff_min,
            doorgroei_pct,
            dg_lijn,
            voorstel_loon,
            f"Voorstel op basis van positie '{inschaling.positie_in_band.value}' in de band.",
            "Geen verwachting opgegeven; voorstel uit band gebruikt.",
            False,
            waarschuwingen,
            config,
            **ladder_kw,
        )

    v = inschaling.salarisverwachting_per_uur
    if v < eff_min:
        if inschaling.verwachting_actie == VerwachtingActie.BLOKKEER:
            raise ValueError(
                f"Salarisverwachting EUR {v:.2f} ligt onder het effectieve CAO-minimum "
                f"EUR {eff_min:.2f} (niveau {inschaling.functieniveau}, incl. doorgroeigarantie). "
                f"Berekening geblokkeerd."
            )
        waarschuwingen.append(
            f"Verwachting EUR {v:.2f} onder effectief minimum; doorgerekend met EUR {eff_min:.2f}."
        )
        bron = (
            f"Verwachting EUR {v:.2f} lag ONDER effectief minimum; "
            f"gecorrigeerd naar EUR {eff_min:.2f}."
        )
        return _maak_resultaat(
            inschaling, cao_datum, band, eff_min, doorgroei_pct, dg_lijn,
            eff_min, bron, bron, False, waarschuwingen, config, **ladder_kw,
        )

    if v > band.maximum:
        waarschuwingen.append(
            f"Verwachting EUR {v:.2f} boven maximum; overweeg hoger niveau. "
            f"Doorgerekend met EUR {band.maximum:.2f}."
        )
        bron = (
            f"Verwachting EUR {v:.2f} lag BOVEN maximum; "
            f"begrensd op CAO-maximum EUR {band.maximum:.2f}."
        )
        return _maak_resultaat(
            inschaling, cao_datum, band, eff_min, doorgroei_pct, dg_lijn,
            band.maximum, bron, bron, False, waarschuwingen, config, **ladder_kw,
        )

    span = band.maximum - eff_min
    pct = (v - eff_min) / span * 100 if span > 0 else 0
    bron = f"Verwachting EUR {v:.2f} gebruikt (op {pct:.0f}% van effectief min naar max)."
    return _maak_resultaat(
        inschaling, cao_datum, band, eff_min, doorgroei_pct, dg_lijn,
        _round2(v), bron, bron, False, waarschuwingen, config, **ladder_kw,
    )


def bereken_tarief_direct(
    functieniveau: int,
    peildatum: date,
    basis_uurloon: Optional[float] = None,
    positie_in_band: TredePositie = TredePositie.MIDDEN,
    marge_pct: float = 15.0,
    omrekenfactor_override: Optional[float] = None,
    jaren_op_niveau: float = 0.0,
    nieuw_in_bouw_infra: bool = False,
    starttabel_tweede_halfjaar: bool = False,
    config: Optional[WerkgeverslastenConfig] = None,
) -> Resultaat:
    return bereken(
        Inschaling(
            functieniveau=functieniveau,
            peildatum=peildatum,
            positie_in_band=positie_in_band,
            salarisverwachting_per_uur=basis_uurloon,
            marge_pct=marge_pct,
            omrekenfactor_override=omrekenfactor_override,
            jaren_op_niveau=jaren_op_niveau,
            nieuw_in_bouw_infra=nieuw_in_bouw_infra,
            starttabel_tweede_halfjaar=starttabel_tweede_halfjaar,
        ),
        config,
    )


def vergelijk_marges(
    functieniveau: int,
    peildatum: date,
    basis_uurloon: Optional[float] = None,
    omrekenfactor_override: Optional[float] = None,
    marges_pct: Optional[List[float]] = None,
    jaren_op_niveau: float = 0.0,
    config: Optional[WerkgeverslastenConfig] = None,
) -> List[dict]:
    if marges_pct is None:
        marges_pct = [0, 10, 15, 20, 25, 30, 35, 40]

    basis = bereken_tarief_direct(
        functieniveau,
        peildatum,
        basis_uurloon,
        marge_pct=0,
        omrekenfactor_override=omrekenfactor_override,
        jaren_op_niveau=jaren_op_niveau,
        config=config,
    )
    kostprijs = basis.kostprijs_per_uur
    bruto = basis.bruto_uurloon

    return [
        {
            "marge_pct": m,
            "marge_percentage": m,
            "kostprijs_per_uur": kostprijs,
            "omrekenfactor": basis.omrekenfactor,
            "marge_bedrag_per_uur": _round2(kostprijs * m / 100),
            "facturatie_per_uur": _round2(kostprijs * (1 + m / 100)),
            "facturatie_tarief_per_uur": _round2(kostprijs * (1 + m / 100)),
            "totaal_factor_op_bruto": _round2(kostprijs * (1 + m / 100) / bruto) if bruto else 0,
        }
        for m in marges_pct
    ]


def bouw_inschaling_van_ladder(
    ladder_nummer: int,
    niveau: int,
    peildatum: date,
    kandidaat_naam: str = "",
    salarisverwachting_per_uur: Optional[float] = None,
    positie_in_band: TredePositie = TredePositie.MIDDEN,
    marge_pct: float = 15.0,
    omrekenfactor_override: Optional[float] = None,
    verwachting_actie: VerwachtingActie = VerwachtingActie.CORRIGEER_NAAR_MINIMUM,
    jaren_op_niveau: float = 0.0,
    nieuw_in_bouw_infra: bool = False,
    starttabel_tweede_halfjaar: bool = False,
) -> Inschaling:
    """Bouw Inschaling vanuit bijlage 1.3 functieladder + gekozen niveau."""
    valideer_ladder_niveau_keuze(ladder_nummer, niveau)
    return Inschaling(
        kandidaat_naam=kandidaat_naam,
        functieniveau=niveau,
        functieladder_nummer=ladder_nummer,
        peildatum=peildatum,
        positie_in_band=positie_in_band,
        salarisverwachting_per_uur=salarisverwachting_per_uur,
        verwachting_actie=verwachting_actie,
        omrekenfactor_override=omrekenfactor_override,
        marge_pct=marge_pct,
        jaren_op_niveau=jaren_op_niveau,
        nieuw_in_bouw_infra=nieuw_in_bouw_infra,
        starttabel_tweede_halfjaar=starttabel_tweede_halfjaar,
    )


def bouw_inschaling_van_functie(
    functie_naam: str,
    peildatum: date,
    kandidaat_naam: str = "",
    salarisverwachting_per_uur: Optional[float] = None,
    bevestigd_niveau: Optional[int] = None,
    positie_in_band: TredePositie = TredePositie.MIDDEN,
    marge_pct: float = 15.0,
    omrekenfactor_override: Optional[float] = None,
    verwachting_actie: VerwachtingActie = VerwachtingActie.CORRIGEER_NAAR_MINIMUM,
    jaren_op_niveau: float = 0.0,
    nieuw_in_bouw_infra: bool = False,
    starttabel_tweede_halfjaar: bool = False,
) -> Inschaling:
    functie = zoek_functie(functie_naam)
    if bevestigd_niveau is not None:
        niveau = bevestigd_niveau
    elif functie is not None:
        niveau = functie.indicatief_niveau
    else:
        raise ValueError(
            f"Functie '{functie_naam}' niet in lijst. "
            "Geef bevestigd_niveau op of kies een functie uit de dropdown."
        )

    return Inschaling(
        kandidaat_naam=kandidaat_naam,
        functieniveau=niveau,
        peildatum=peildatum,
        positie_in_band=positie_in_band,
        salarisverwachting_per_uur=salarisverwachting_per_uur,
        verwachting_actie=verwachting_actie,
        omrekenfactor_override=omrekenfactor_override,
        marge_pct=marge_pct,
        jaren_op_niveau=jaren_op_niveau,
        nieuw_in_bouw_infra=nieuw_in_bouw_infra,
        starttabel_tweede_halfjaar=starttabel_tweede_halfjaar,
    )


if __name__ == "__main__":
    def toon(titel: str, inschaling: Inschaling) -> None:
        r = bereken(inschaling)
        print("=" * 68)
        print(titel)
        print("=" * 68)
        print("\n--- HARD (uit de CAO) ---")
        print(f"  CAO-tabel:         {r.cao_tabel.strftime('%d-%m-%Y')}")
        print(f"  Niveau:            {r.niveau_naam}")
        print(f"  Tabelband:         EUR {r.band_min:.2f} - EUR {r.band_max:.2f}")
        print(
            f"  Effectief minimum: EUR {r.effectief_minimum:.2f} "
            f"({r.doorgroei_percentage * 100:.0f}% — art. 4.9.2)"
        )
        print(
            f"  Doorgroeilijn:     0jr EUR {r.doorgroei_lijn['0_jaar']:.2f} | "
            f"2jr EUR {r.doorgroei_lijn['2_jaar_104pct']:.2f} | "
            f"4jr EUR {r.doorgroei_lijn['4_jaar_110pct']:.2f} | "
            f"6jr EUR {r.doorgroei_lijn['6_jaar_116pct']:.2f}"
        )
        print(f"  Starttabel actief: {'JA' if r.starttabel_toegepast else 'nee'}")
        print(f"\n--- GEKOZEN LOON ---")
        print(f"  Bruto uurloon:     EUR {r.bruto_uurloon:.2f}")
        print(f"  Herkomst:          {r.bruto_bron}")
        print(f"\n--- KOSTPRIJS (Model A) ---")
        print(f"  Omrekenfactor:     {r.omrekenfactor}")
        print(f"  Kostprijs/uur:     EUR {r.kostprijs_per_uur:.2f}")
        print(f"  Facturatie ({r.marge_pct:.0f}%):   EUR {r.facturatie_per_uur:.2f}")
        if r.waarschuwingen:
            print("\n--- WAARSCHUWINGEN ---")
            for w in r.waarschuwingen:
                print(f"  ! {w}")
        print()

    toon(
        "CASUS 1 - Ervaren (5 jaar op niveau 3): doorgroeigarantie",
        Inschaling(
            kandidaat_naam="Jan Jansen",
            functieniveau=3,
            peildatum=date(2026, 3, 1),
            positie_in_band=TredePositie.MINIMUM,
            jaren_op_niveau=5,
            salarisverwachting_per_uur=20.00,
            marge_pct=15.0,
        ),
    )
    toon(
        "CASUS 2 - Nieuw in bouw & infra: starttabel (art. 4.11)",
        Inschaling(
            kandidaat_naam="Nieuwe Instromer",
            functieniveau=2,
            peildatum=date(2026, 3, 1),
            nieuw_in_bouw_infra=True,
            starttabel_tweede_halfjaar=False,
            marge_pct=15.0,
        ),
    )
