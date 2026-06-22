"""
UTA-functies CAO Bouw & Infra — indicatieve functielijst voor inschaling.

Let op: indicatief_niveau is een HULP bij inschaling (oordeel), geen CAO-bepaling.
Definitieve indeling volgt uit functie-inhoud en FUWA-systematiek.
"""

from typing import Optional

from pydantic import BaseModel


class UTAFunctie(BaseModel):
    naam: str
    categorie: str
    indicatief_niveau: int
    toelichting: str = ""


UTA_FUNCTIES: list[UTAFunctie] = [
    # Administratief
    UTAFunctie(
        naam="Administratief medewerker (startend)",
        categorie="Administratief",
        indicatief_niveau=1,
        toelichting="Eenvoudige administratieve taken onder begeleiding",
    ),
    UTAFunctie(
        naam="Administratief medewerker",
        categorie="Administratief",
        indicatief_niveau=2,
        toelichting="Zelfstandige uitvoering van standaard administratie",
    ),
    UTAFunctie(
        naam="Documentbeheerder",
        categorie="Administratief",
        indicatief_niveau=2,
        toelichting="Beheer van projectdocumentatie en dossiers",
    ),
    UTAFunctie(
        naam="Secretaresse / office support",
        categorie="Administratief",
        indicatief_niveau=2,
    ),
    UTAFunctie(
        naam="Contractbeheerder",
        categorie="Administratief",
        indicatief_niveau=4,
        toelichting="Beheer en opvolging van contracten en afspraken",
    ),
    UTAFunctie(
        naam="Contractmanager",
        categorie="Administratief",
        indicatief_niveau=5,
        toelichting="Strategisch contract- en claimbeheer",
    ),
    # Technisch — werkvoorbereiding & engineering
    UTAFunctie(
        naam="Assistent werkvoorbereider",
        categorie="Technisch",
        indicatief_niveau=1,
    ),
    UTAFunctie(
        naam="Junior werkvoorbereider",
        categorie="Technisch",
        indicatief_niveau=2,
    ),
    UTAFunctie(
        naam="Werkvoorbereider",
        categorie="Technisch",
        indicatief_niveau=3,
        toelichting="Zelfstandige werkvoorbereiding voor uitvoeringsprojecten",
    ),
    UTAFunctie(
        naam="Senior werkvoorbereider",
        categorie="Technisch",
        indicatief_niveau=4,
    ),
    UTAFunctie(
        naam="Hoofd werkvoorbereiding",
        categorie="Technisch",
        indicatief_niveau=5,
    ),
    UTAFunctie(
        naam="Junior calculator",
        categorie="Technisch",
        indicatief_niveau=2,
    ),
    UTAFunctie(
        naam="Calculator",
        categorie="Technisch",
        indicatief_niveau=3,
        toelichting="Kostencalculaties en offertes",
    ),
    UTAFunctie(
        naam="Senior calculator",
        categorie="Technisch",
        indicatief_niveau=4,
    ),
    UTAFunctie(
        naam="Tekenaar (aankomend)",
        categorie="Technisch",
        indicatief_niveau=2,
    ),
    UTAFunctie(
        naam="Tekenaar",
        categorie="Technisch",
        indicatief_niveau=3,
    ),
    UTAFunctie(
        naam="BIM modelleur",
        categorie="Technisch",
        indicatief_niveau=3,
    ),
    UTAFunctie(
        naam="Senior BIM coordinator",
        categorie="Technisch",
        indicatief_niveau=5,
    ),
    UTAFunctie(
        naam="Planontwikkelaar",
        categorie="Technisch",
        indicatief_niveau=3,
    ),
    UTAFunctie(
        naam="Kostenbewaker",
        categorie="Technisch",
        indicatief_niveau=3,
        toelichting="Monitoring van projectkosten en budgetten",
    ),
    # Uitvoerend — bouwplaats & project
    UTAFunctie(
        naam="Hulpuitvoerder",
        categorie="Uitvoerend",
        indicatief_niveau=1,
    ),
    UTAFunctie(
        naam="Toezichthouder",
        categorie="Uitvoerend",
        indicatief_niveau=3,
        toelichting="Toezicht op uitvoering conform tekeningen en specs",
    ),
    UTAFunctie(
        naam="Uitvoerder",
        categorie="Uitvoerend",
        indicatief_niveau=4,
        toelichting="Leiding op de bouwplaats, coördinatie uitvoering",
    ),
    UTAFunctie(
        naam="Senior uitvoerder",
        categorie="Uitvoerend",
        indicatief_niveau=5,
    ),
    UTAFunctie(
        naam="Projectleider (aankomend)",
        categorie="Uitvoerend",
        indicatief_niveau=4,
    ),
    UTAFunctie(
        naam="Projectleider",
        categorie="Uitvoerend",
        indicatief_niveau=5,
    ),
    UTAFunctie(
        naam="Omgevingsmanager",
        categorie="Uitvoerend",
        indicatief_niveau=4,
        toelichting="Coördinatie omgevingsaspecten en stakeholders",
    ),
    UTAFunctie(
        naam="Senior projectleider",
        categorie="Uitvoerend",
        indicatief_niveau=6,
    ),
    UTAFunctie(
        naam="Projectmanager",
        categorie="Uitvoerend",
        indicatief_niveau=6,
    ),
    UTAFunctie(
        naam="Manager uitvoering",
        categorie="Uitvoerend",
        indicatief_niveau=6,
    ),
    UTAFunctie(
        naam="Afdelingshoofd",
        categorie="Uitvoerend",
        indicatief_niveau=6,
    ),
]


def lijst_functies_gegroepeerd() -> dict[str, list[dict]]:
    """Functies gegroepeerd per categorie voor dropdown."""
    grouped: dict[str, list[dict]] = {}
    for f in sorted(UTA_FUNCTIES, key=lambda x: (x.categorie, x.indicatief_niveau, x.naam)):
        grouped.setdefault(f.categorie, []).append(f.model_dump())
    return grouped


def lijst_functies() -> list[dict]:
    return [f.model_dump() for f in UTA_FUNCTIES]


def zoek_functie(naam: str) -> Optional[UTAFunctie]:
    key = naam.strip().lower()
    for f in UTA_FUNCTIES:
        if f.naam.lower() == key:
            return f
    return None
