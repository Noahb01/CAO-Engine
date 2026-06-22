"""
Mapping UTA-functietitels → CAO functieladder (bijlage 1.3) + voorgesteld niveau.

Suggesties zijn startpunten voor de inschaler, geen automatische CAO-beslissing.
Waar de matrix afwijkt of de match benaderend is, staat dat in mapping_opmerking.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from functieladders_bijlage_1_3 import FUNCTIENIVEAU_MATRIX, zoek_ladder
from functies import UTA_FUNCTIES, zoek_functie


class FunctieLadderMapping(BaseModel):
    functie_naam: str
    functieladder_nummer: int = Field(..., ge=1, le=25)
    voorgesteld_niveau: int = Field(..., ge=1, le=6)
    mapping_opmerking: Optional[str] = None


# Handmatige koppeling per UTA-functietitel.
FUNCTIE_LADDER_MAPPING: dict[str, FunctieLadderMapping] = {
    "Administratief medewerker (startend)": FunctieLadderMapping(
        functie_naam="Administratief medewerker (startend)",
        functieladder_nummer=11,
        voorgesteld_niveau=2,
        mapping_opmerking="CAO heeft geen niveau 1 op ladder Administratie algemeen; niveau 2 als startpunt.",
    ),
    "Administratief medewerker": FunctieLadderMapping(
        functie_naam="Administratief medewerker",
        functieladder_nummer=11,
        voorgesteld_niveau=2,
    ),
    "Documentbeheerder": FunctieLadderMapping(
        functie_naam="Documentbeheerder",
        functieladder_nummer=12,
        voorgesteld_niveau=2,
        mapping_opmerking="Documentbeheer sluit aan bij werkenadministratie.",
    ),
    "Secretaresse / office support": FunctieLadderMapping(
        functie_naam="Secretaresse / office support",
        functieladder_nummer=19,
        voorgesteld_niveau=2,
    ),
    "Contractbeheerder": FunctieLadderMapping(
        functie_naam="Contractbeheerder",
        functieladder_nummer=12,
        voorgesteld_niveau=4,
    ),
    "Contractmanager": FunctieLadderMapping(
        functie_naam="Contractmanager",
        functieladder_nummer=11,
        voorgesteld_niveau=5,
        mapping_opmerking="Contractmanagement sluit het beste aan bij administratie algemeen.",
    ),
    "Assistent werkvoorbereider": FunctieLadderMapping(
        functie_naam="Assistent werkvoorbereider",
        functieladder_nummer=3,
        voorgesteld_niveau=2,
        mapping_opmerking="Niveau 1 op ladder Werkvoorbereiding is leeg in CAO; niveau 2 als instap.",
    ),
    "Junior werkvoorbereider": FunctieLadderMapping(
        functie_naam="Junior werkvoorbereider",
        functieladder_nummer=3,
        voorgesteld_niveau=2,
    ),
    "Werkvoorbereider": FunctieLadderMapping(
        functie_naam="Werkvoorbereider",
        functieladder_nummer=3,
        voorgesteld_niveau=3,
    ),
    "Senior werkvoorbereider": FunctieLadderMapping(
        functie_naam="Senior werkvoorbereider",
        functieladder_nummer=3,
        voorgesteld_niveau=4,
    ),
    "Hoofd werkvoorbereiding": FunctieLadderMapping(
        functie_naam="Hoofd werkvoorbereiding",
        functieladder_nummer=2,
        voorgesteld_niveau=5,
        mapping_opmerking="Leiding werkvoorbereiding valt onder bedrijfsbureau (ladder 2).",
    ),
    "Junior calculator": FunctieLadderMapping(
        functie_naam="Junior calculator",
        functieladder_nummer=4,
        voorgesteld_niveau=2,
    ),
    "Calculator": FunctieLadderMapping(
        functie_naam="Calculator",
        functieladder_nummer=4,
        voorgesteld_niveau=3,
    ),
    "Senior calculator": FunctieLadderMapping(
        functie_naam="Senior calculator",
        functieladder_nummer=4,
        voorgesteld_niveau=4,
    ),
    "Tekenaar (aankomend)": FunctieLadderMapping(
        functie_naam="Tekenaar (aankomend)",
        functieladder_nummer=5,
        voorgesteld_niveau=2,
    ),
    "Tekenaar": FunctieLadderMapping(
        functie_naam="Tekenaar",
        functieladder_nummer=5,
        voorgesteld_niveau=3,
    ),
    "BIM modelleur": FunctieLadderMapping(
        functie_naam="BIM modelleur",
        functieladder_nummer=5,
        voorgesteld_niveau=3,
        mapping_opmerking="BIM sluit aan bij planontwikkeling/tekenkamer.",
    ),
    "Senior BIM coordinator": FunctieLadderMapping(
        functie_naam="Senior BIM coordinator",
        functieladder_nummer=5,
        voorgesteld_niveau=4,
    ),
    "Planontwikkelaar": FunctieLadderMapping(
        functie_naam="Planontwikkelaar",
        functieladder_nummer=5,
        voorgesteld_niveau=3,
    ),
    "Kostenbewaker": FunctieLadderMapping(
        functie_naam="Kostenbewaker",
        functieladder_nummer=12,
        voorgesteld_niveau=3,
        mapping_opmerking="Kostenbewaking sluit aan bij werkenadministratie.",
    ),
    "Hulpuitvoerder": FunctieLadderMapping(
        functie_naam="Hulpuitvoerder",
        functieladder_nummer=1,
        voorgesteld_niveau=3,
        mapping_opmerking="Assistentie op uitvoering; niveaus 1–2 zijn leeg in CAO op ladder Uitvoering.",
    ),
    "Toezichthouder": FunctieLadderMapping(
        functie_naam="Toezichthouder",
        functieladder_nummer=1,
        voorgesteld_niveau=4,
    ),
    "Uitvoerder": FunctieLadderMapping(
        functie_naam="Uitvoerder",
        functieladder_nummer=1,
        voorgesteld_niveau=4,
    ),
    "Senior uitvoerder": FunctieLadderMapping(
        functie_naam="Senior uitvoerder",
        functieladder_nummer=1,
        voorgesteld_niveau=5,
    ),
    "Projectleider (aankomend)": FunctieLadderMapping(
        functie_naam="Projectleider (aankomend)",
        functieladder_nummer=1,
        voorgesteld_niveau=4,
    ),
    "Projectleider": FunctieLadderMapping(
        functie_naam="Projectleider",
        functieladder_nummer=1,
        voorgesteld_niveau=5,
    ),
    "Omgevingsmanager": FunctieLadderMapping(
        functie_naam="Omgevingsmanager",
        functieladder_nummer=24,
        voorgesteld_niveau=4,
        mapping_opmerking="Omgevingsmanagement sluit aan bij KAM-ladder; matrix heeft alleen 1–2.",
    ),
    "Senior projectleider": FunctieLadderMapping(
        functie_naam="Senior projectleider",
        functieladder_nummer=1,
        voorgesteld_niveau=6,
        mapping_opmerking="Niveau 6 staat niet in de CAO-matrix voor ladder Uitvoering.",
    ),
    "Projectmanager": FunctieLadderMapping(
        functie_naam="Projectmanager",
        functieladder_nummer=2,
        voorgesteld_niveau=5,
        mapping_opmerking="Projectmanagement op hoog niveau sluit aan bij bedrijfsbureau.",
    ),
    "Manager uitvoering": FunctieLadderMapping(
        functie_naam="Manager uitvoering",
        functieladder_nummer=1,
        voorgesteld_niveau=6,
        mapping_opmerking="Niveau 6 staat niet in de CAO-matrix voor ladder Uitvoering.",
    ),
    "Afdelingshoofd": FunctieLadderMapping(
        functie_naam="Afdelingshoofd",
        functieladder_nummer=2,
        voorgesteld_niveau=5,
        mapping_opmerking="Afdelingshoofd sluit aan bij bedrijfsbureau.",
    ),
}


def mapping_voor_functie(naam: str) -> Optional[FunctieLadderMapping]:
    return FUNCTIE_LADDER_MAPPING.get(naam)


def _matrix_signaal(ladder_nummer: int, niveau: int) -> Optional[str]:
    matrix = FUNCTIENIVEAU_MATRIX.get(ladder_nummer, [])
    if niveau not in matrix:
        return (
            "Deze functie valt buiten de standaard CAO-laddertredes voor deze ladder. "
            "Bevestig de inschaling op basis van functie-inhoud."
        )
    return None


def verrijk_mapping(m: FunctieLadderMapping) -> dict:
    ladder = zoek_ladder(m.functieladder_nummer)
    functie = zoek_functie(m.functie_naam)

    return {
        "functie_naam": m.functie_naam,
        "categorie": functie.categorie if functie else None,
        "indicatief_niveau": functie.indicatief_niveau if functie else None,
        "functieladder_nummer": m.functieladder_nummer,
        "functieladder_naam": ladder.naam if ladder else None,
        "voorgesteld_niveau": m.voorgesteld_niveau,
        "toelichting": m.mapping_opmerking,
        "matrix_signaal": _matrix_signaal(m.functieladder_nummer, m.voorgesteld_niveau),
    }
