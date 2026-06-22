"""
Inschaling-keuzes: UTA-functietitels als enige gebruikerskeuze.
"""

from __future__ import annotations

from typing import Optional

from functie_ladder_mapping import FUNCTIE_LADDER_MAPPING, verrijk_mapping
from functieladders_bijlage_1_3 import lijst_functieladders, zoek_ladder
from functies import UTA_FUNCTIES


def lijst_functietitel_keuzes() -> list[dict]:
    """UTA-functietitels — alleen de titel zichtbaar voor de gebruiker."""
    keuzes = []
    for f in sorted(UTA_FUNCTIES, key=lambda x: (x.categorie, x.naam)):
        mapping = FUNCTIE_LADDER_MAPPING.get(f.naam)
        if mapping is None:
            continue
        data = verrijk_mapping(mapping)
        keuzes.append(
            {
                "id": f"functie:{f.naam}",
                "type": "functietitel",
                "label": f.naam,
                "zoektekst": " ".join(
                    filter(
                        None,
                        [
                            f.naam.lower(),
                            f.categorie.lower(),
                        ],
                    )
                ),
                **data,
            }
        )
    return keuzes


def lijst_ladder_keuzes() -> list[dict]:
    """Directe functieladder-keuze (intern/API; niet in hoofd-UI)."""
    keuzes = []
    for l in lijst_functieladders():
        keuzes.append(
            {
                "id": f"ladder:{l['nummer']}",
                "type": "ladder",
                "label": f"Ladder {l['nummer']}: {l['naam']}",
                "functie_naam": l["naam"],
                "functieladder_nummer": l["nummer"],
                "functieladder_naam": l["naam"],
                "voorgesteld_niveau": None,
                "indicatief_niveau": None,
                "categorie": None,
                "toelichting": None,
                "matrix_signaal": None,
                "matrix_niveaus": l["matrix_niveaus"],
                "zoektekst": f"{l['nummer']} {l['naam'].lower()} ladder",
            }
        )
    return keuzes


def lijst_inschaling_keuzes(q: Optional[str] = None) -> dict:
    """Functietitel-keuzelijst voor UI, optioneel gefilterd op zoekterm."""
    functietitels = lijst_functietitel_keuzes()

    if q:
        term = q.strip().lower()
        functietitels = [k for k in functietitels if term in k["zoektekst"]]

    return {
        "functietitels": functietitels,
        "totaal": len(functietitels),
    }


def parse_keuze_id(keuze_id: str) -> tuple[str, str]:
    """Retourneert (type, waarde) uit id zoals 'functie:Werkvoorbereider'."""
    if ":" not in keuze_id:
        raise ValueError(f"Ongeldige keuze-id: {keuze_id}")
    kind, value = keuze_id.split(":", 1)
    if kind not in ("functie", "ladder"):
        raise ValueError(f"Onbekend keuzetype: {kind}")
    return kind, value


def keuze_naar_inschaling(keuze_id: str, niveau_override: Optional[int] = None) -> dict:
    """Vertaal UI-keuze naar pipeline-velden."""
    kind, value = parse_keuze_id(keuze_id)

    if kind == "functie":
        from functie_ladder_mapping import mapping_voor_functie

        mapping = mapping_voor_functie(value)
        if mapping is None:
            raise ValueError(f"Geen ladder-mapping voor functie '{value}'.")
        ladder = zoek_ladder(mapping.functieladder_nummer)
        niveau = niveau_override or mapping.voorgesteld_niveau
        enriched = verrijk_mapping(mapping)
        return {
            "functie_omschrijving": value,
            "functieladder_nummer": mapping.functieladder_nummer,
            "bevestigd_niveau": niveau,
            "keuze_label": value,
            "toelichting": enriched.get("toelichting"),
            "matrix_signaal": enriched.get("matrix_signaal"),
            "functieladder_naam": ladder.naam if ladder else None,
        }

    ladder_nummer = int(value)
    ladder = zoek_ladder(ladder_nummer)
    if ladder is None:
        raise ValueError(f"Functieladder {ladder_nummer} niet gevonden.")
    if niveau_override is None:
        raise ValueError(f"Kies een niveau voor ladder {ladder_nummer} ({ladder.naam}).")
    return {
        "functie_omschrijving": ladder.naam,
        "functieladder_nummer": ladder_nummer,
        "bevestigd_niveau": niveau_override,
        "keuze_label": f"Ladder {ladder_nummer}: {ladder.naam}, niveau {niveau_override}",
        "toelichting": None,
        "matrix_signaal": None,
        "functieladder_naam": ladder.naam,
    }
