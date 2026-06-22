"""
Contract Generator — Transparante overzichten (v2 kostprijsmodel).
"""

from datetime import date
from typing import Optional

from cao_data import FUNCTIENIVEAU_KENMERKEN, UREN_PER_MAAND, get_loontabel, get_peildatum_tabel
from functie_ladder_mapping import mapping_voor_functie, verrijk_mapping
from functieladders_bijlage_1_3 import zoek_ladder
from inschaling_engine_v2 import (
    Inschaling,
    Resultaat,
    TredePositie,
    WerkgeverslastenConfig,
    bereken,
    ladder_context,
    valideer_ladder_niveau_keuze,
)
from inschalingsmodel import (
    Inschalingsresultaat,
    KandidaatInput,
    TredePositie as OordeelTredePositie,
    bereken_loon_in_band,
    check_salarisverwachting,
)


def _format_datum(d: date) -> str:
    return d.strftime("%d-%m-%Y")


def _maandsalaris(uurloon: float) -> float:
    return round(uurloon * UREN_PER_MAAND, 2)


def _resolve_functie_inschaling(
    functie_naam: str,
    bevestigd_niveau: Optional[int],
) -> tuple[int, int, int, str, dict, bool, Optional[str]]:
    """Leid ladder en niveau af uit de UTA-functietitel-mapping."""
    mapping = mapping_voor_functie(functie_naam)
    if mapping is None:
        raise ValueError(
            f"Functietitel '{functie_naam}' staat niet in de UTA-functielijst. "
            "Kies een functietitel uit de lijst."
        )

    enriched = verrijk_mapping(mapping)
    ladder_nr = mapping.functieladder_nummer
    voorgesteld = mapping.voorgesteld_niveau
    niveau = bevestigd_niveau if bevestigd_niveau is not None else voorgesteld
    bijgesteld = niveau != voorgesteld

    ladder = zoek_ladder(ladder_nr)
    ladder_label = ladder.naam if ladder else f"ladder {ladder_nr}"

    if bijgesteld:
        bron = (
            f"Niveau {niveau} bevestigd door inschaler "
            f"(voorstel uit functietitel '{functie_naam}': niveau {voorgesteld}, {ladder_label})."
        )
        bijstelling_tekst = f"Niveau handmatig bijgesteld van {voorgesteld} naar {niveau}."
    else:
        bron = (
            f"Voorstel uit functietitel '{functie_naam}': "
            f"{ladder_label}, niveau {niveau}."
        )
        bijstelling_tekst = None

    valideer_ladder_niveau_keuze(ladder_nr, niveau)
    return niveau, ladder_nr, voorgesteld, bron, enriched, bijgesteld, bijstelling_tekst


def _oordeel_voor_niveau(kandidaat: KandidaatInput, niveau: int) -> Inschalingsresultaat:
    """Oordeel-sectie op basis van het mapping-niveau (niet op ervaring)."""
    tabel = get_loontabel(kandidaat.peildatum)
    gekozen_datum = get_peildatum_tabel(kandidaat.peildatum)
    band = tabel[niveau]
    voorgestelde_positie = OordeelTredePositie.MIDDEN
    voorgesteld_uurloon = bereken_loon_in_band(band, voorgestelde_positie)

    return Inschalingsresultaat(
        peildatum_tabel=gekozen_datum,
        voorgesteld_niveau=niveau,
        niveau_naam=FUNCTIENIVEAU_KENMERKEN[niveau]["naam"],
        loonband_minimum=band.minimum,
        loonband_maximum=band.maximum,
        voorgestelde_positie=voorgestelde_positie,
        voorgesteld_uurloon=voorgesteld_uurloon,
        oordeel_disclaimer=(
            "VOORSTEL, geen bepaling. Het niveau volgt uit de gekozen functietitel "
            "en kan optioneel worden bijgesteld aan de hand van de CAO-karakteristieken. "
            "De positie binnen de band is een keuze van de inschaler op basis van "
            "functie-inhoud en bedrijfsbeleid."
        ),
        verwachting_past_in_band=None,
        verwachting_opmerking="",
    )


def genereer_kandidaat_overzicht(
    berekening: Resultaat,
    kandidaat_naam: str,
    opdrachtgever: str,
    project_naam: Optional[str] = None,
    peildatum: Optional[date] = None,
) -> str:
    """Transparant salarisoverzicht voor de kandidaat (zonder kostprijs/marge)."""
    maand = _maandsalaris(berekening.bruto_uurloon)
    start = peildatum or berekening.cao_tabel

    lines = [
        "=" * 70,
        "SALARISOVERZICHT KANDIDAAT — CAO Bouw & Infra UTA",
        "=" * 70,
        "",
    ]
    if kandidaat_naam and kandidaat_naam.strip():
        lines.append(f"Kandidaat:      {kandidaat_naam.strip()}")
    lines.append(f"Opdrachtgever:  {opdrachtgever}")
    if project_naam:
        lines.append(f"Project:        {project_naam}")
    lines.extend(
        [
            f"Startdatum:     {_format_datum(start)}",
            f"Functieniveau:  {berekening.niveau_naam}",
            f"CAO-tabel:      {_format_datum(berekening.cao_tabel)}",
            "",
            "--- Bruto uurloon ---",
            f"  Bruto uurloon:           €{berekening.bruto_uurloon:.2f}/uur",
            f"  CAO-band:                €{berekening.band_min:.2f} – €{berekening.band_max:.2f}",
            f"  Herkomst:                {berekening.bruto_bron}",
            f"  Indicatief maandsalaris: €{maand:.2f} (op basis van {UREN_PER_MAAND:.2f} uur/maand)",
            "",
            "Dit overzicht toont uw bruto uurloon conform CAO Bouw & Infra.",
            "Kostprijs, werkgeverslasten en bureau-marges zijn niet opgenomen.",
            "=" * 70,
        ]
    )
    return "\n".join(lines)


def genereer_bureau_overzicht(
    berekening: Resultaat,
    kandidaat_naam: str,
    opdrachtgever: str,
    project_naam: Optional[str] = None,
    peildatum: Optional[date] = None,
) -> str:
    """Intern overzicht met Model A kostprijsopbouw."""
    start = peildatum or berekening.cao_tabel
    marge_bedrag = berekening.facturatie_per_uur - berekening.kostprijs_per_uur

    lines = [
        "=" * 70,
        "INTERN BUREAU OVERZICHT — Kostprijs & Marge (Model A)",
        "=" * 70,
        "",
    ]
    if kandidaat_naam and kandidaat_naam.strip():
        lines.append(f"Kandidaat:      {kandidaat_naam.strip()}")
    lines.append(f"Opdrachtgever:  {opdrachtgever}")
    if project_naam:
        lines.append(f"Project:        {project_naam}")
    lines.extend(
        [
            f"Startdatum:     {_format_datum(start)}",
            f"Functieniveau:  {berekening.niveau_naam}",
            "",
            "--- Bruto (CAO) ---",
            f"  Bruto uurloon:           €{berekening.bruto_uurloon:.2f}",
            f"  CAO-band:                €{berekening.band_min:.2f} – €{berekening.band_max:.2f}",
            f"  Effectief minimum:       €{berekening.effectief_minimum:.2f} "
            f"({berekening.doorgroei_percentage * 100:.0f}% — doorgroeigarantie)",
            f"  Starttabel:              {'ja' if berekening.starttabel_toegepast else 'nee'}",
            f"  {berekening.bruto_bron}",
            "",
            "--- Kostprijs (bruto × omrekenfactor) ---",
            f"  Omrekenfactor:           {berekening.omrekenfactor}",
            f"  Netto werkbare dagen:    {berekening.netto_werkbare_dagen}",
            f"  Kostprijs per uur:       €{berekening.kostprijs_per_uur:.2f}/uur",
        ]
    )
    for k, v in berekening.factor_opbouw.items():
        lines.append(f"    {k}: {v}")

    lines.extend(
        [
            "",
            "--- Bureau marge ---",
            f"  Marge:                   {berekening.marge_pct:.0f}% op kostprijs",
            f"  Marge bedrag:            €{marge_bedrag:.2f}/uur",
            "",
            "--- Facturatie ---",
            f"  Facturatie tarief:       €{berekening.facturatie_per_uur:.2f}/uur",
            f"  Totaalfactor op bruto:   {berekening.totaal_factor_op_bruto:.2f}×",
        ]
    )
    if berekening.waarschuwingen:
        lines.extend(["", "--- Waarschuwingen ---"])
        for w in berekening.waarschuwingen:
            lines.append(f"  ! {w}")
    lines.append("=" * 70)
    return "\n".join(lines)


def genereer_marge_vergelijking_tabel(
    functieniveau: int,
    startdatum_contract: date,
    basis_uurloon: Optional[float] = None,
    omrekenfactor_override: Optional[float] = None,
) -> str:
    from inschaling_engine_v2 import vergelijk_marges

    rijen = vergelijk_marges(
        functieniveau,
        startdatum_contract,
        basis_uurloon,
        omrekenfactor_override,
    )
    lines = [
        "=" * 70,
        f"MARGE VERGELIJKING — Functieniveau {functieniveau}",
        "=" * 70,
        f"{'Marge':>8}  {'Kostprijs':>10}  {'Marge €':>10}  {'Facturatie':>10}  {'× bruto':>8}",
        "-" * 70,
    ]
    for r in rijen:
        lines.append(
            f"{r['marge_pct']:>6.0f}%  "
            f"€{r['kostprijs_per_uur']:>8.2f}  "
            f"€{r['marge_bedrag_per_uur']:>8.2f}  "
            f"€{r['facturatie_per_uur']:>8.2f}  "
            f"{r['totaal_factor_op_bruto']:>7.2f}×"
        )
    lines.append("=" * 70)
    return "\n".join(lines)


def genereer_volledig_voorstel(
    kandidaat: KandidaatInput,
    kandidaat_naam: str,
    opdrachtgever: str,
    marge_pct: float = 15.0,
    omrekenfactor_override: Optional[float] = None,
    project_naam: Optional[str] = None,
    bevestigd_niveau: Optional[int] = None,
    bevestigd_uurloon: Optional[float] = None,
    jaren_op_niveau: float = 0.0,
    nieuw_in_bouw_infra: bool = False,
    starttabel_tweede_halfjaar: bool = False,
    config: Optional[WerkgeverslastenConfig] = None,
) -> dict:
    """
    Pipeline: functietitel-mapping → bevestigd niveau → v2 kostprijs → overzichten.
    """
    (
        niveau,
        ladder_nr,
        voorgesteld_niveau,
        niveau_bron,
        functie_mapping,
        niveau_bijgesteld,
        niveau_bijstelling,
    ) = _resolve_functie_inschaling(
        kandidaat.functie_omschrijving,
        bevestigd_niveau,
    )

    inschaling_voorstel = _oordeel_voor_niveau(kandidaat, niveau)

    salaris = bevestigd_uurloon
    if salaris is None and kandidaat.salarisverwachting_per_uur is not None:
        salaris = kandidaat.salarisverwachting_per_uur

    past, verwachting_opmerking = check_salarisverwachting(
        kandidaat.peildatum,
        niveau,
        salaris,
        jaren_op_niveau,
        nieuw_in_bouw_infra,
        starttabel_tweede_halfjaar,
    )
    inschaling_voorstel = inschaling_voorstel.model_copy(
        update={
            "verwachting_past_in_band": past,
            "verwachting_opmerking": verwachting_opmerking,
        }
    )

    ins = Inschaling(
        kandidaat_naam=kandidaat_naam,
        functieniveau=niveau,
        functieladder_nummer=ladder_nr,
        peildatum=kandidaat.peildatum,
        positie_in_band=TredePositie.MIDDEN,
        salarisverwachting_per_uur=salaris,
        marge_pct=marge_pct,
        omrekenfactor_override=omrekenfactor_override,
        jaren_op_niveau=jaren_op_niveau,
        nieuw_in_bouw_infra=nieuw_in_bouw_infra,
        starttabel_tweede_halfjaar=starttabel_tweede_halfjaar,
    )
    berekening = bereken(ins, config)

    functieladder = ladder_context(ladder_nr, niveau)
    functieladder["toelichting"] = functie_mapping.get("toelichting")
    functieladder["matrix_signaal"] = functie_mapping.get("matrix_signaal")

    return {
        "inschaling": inschaling_voorstel,
        "gebruikt_niveau": niveau,
        "voorgesteld_niveau": voorgesteld_niveau,
        "niveau_bijgesteld": niveau_bijgesteld,
        "niveau_bijstelling": niveau_bijstelling,
        "niveau_bron": niveau_bron,
        "functie_mapping": functie_mapping,
        "functieladder": functieladder,
        "berekening": berekening,
        "kandidaat_overzicht": genereer_kandidaat_overzicht(
            berekening, kandidaat_naam, opdrachtgever, project_naam, kandidaat.peildatum
        ),
        "bureau_overzicht": genereer_bureau_overzicht(
            berekening, kandidaat_naam, opdrachtgever, project_naam, kandidaat.peildatum
        ),
    }
