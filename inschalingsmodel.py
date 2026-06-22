"""
INSCHALINGSMODEL - CAO Bouw & Infra UTA
========================================

Dit is het deel dat de bestaande tools (Flexpedia, FlexKnowledge) NIET hebben:
de stap van KANDIDAAT -> CORRECT FUNCTIENIVEAU + LOONBANDBREEDTE.

De bestaande tools beginnen bij een gegeven bruto uurloon. Dit model komt
ervoor: het leidt van functie + leeftijd + ervaring naar het juiste niveau
en de bijbehorende loonband, zodat daarna pas de kostprijsberekening volgt.

EERLIJKHEIDSPRINCIPE INGEBOUWD IN DIT MODEL:
- Wat de CAO HARD bepaalt -> de tool berekent het (deterministisch).
- Wat een OORDEEL is -> de tool stelt voor en laat de gebruiker beslissen.
Beide worden expliciet gescheiden in de output, zodat er nooit schijnzekerheid
ontstaat. Een tool die zegt "dit IS de inschaling" terwijl het een oordeel was,
is een aansprakelijkheidsval.
"""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from cao_data import (
    Loonband,
    effectief_minimum,
    get_loonband,
    get_loontabel,
    get_peildatum_tabel,
    get_starttabel,
)


# ===========================================================================
# DEEL 1: WAT DE CAO HARD BEPAALT (deterministisch)
# ===========================================================================

# Functieniveau-omschrijvingen voor UTA (Uitvoerend, Technisch en Administratief
# personeel). Dit zijn indicatieve kenmerken per niveau, bedoeld als HULP bij
# het kiezen van een niveau - NIET als sluitende juridische definitie. De
# definitieve functie-indeling gebeurt via het functie-indelingssysteem van de
# CAO (FUWA-systematiek) en is werkgeversverantwoordelijkheid.
FUNCTIENIVEAU_KENMERKEN = {
    1: {
        "naam": "Niveau 1 - Ondersteunend / startend",
        "kenmerk": "Eenvoudige, routinematige taken onder directe begeleiding. Geen of zeer beperkte ervaring vereist.",
        "indicatie_ervaring": "0-1 jaar",
        "voorbeelden": "Administratief medewerker (startend), assistent werkvoorbereiding",
    },
    2: {
        "naam": "Niveau 2 - Uitvoerend",
        "kenmerk": "Uitvoerende taken met enige zelfstandigheid binnen duidelijke kaders.",
        "indicatie_ervaring": "1-3 jaar",
        "voorbeelden": "Administratief medewerker, junior calculator, tekenaar (aankomend)",
    },
    3: {
        "naam": "Niveau 3 - Zelfstandig uitvoerend",
        "kenmerk": "Zelfstandige uitvoering van taken die vakkennis en ervaring vragen.",
        "indicatie_ervaring": "3-6 jaar",
        "voorbeelden": "Calculator, werkvoorbereider, tekenaar, kostenbewaker",
    },
    4: {
        "naam": "Niveau 4 - Specialist / coordinerend",
        "kenmerk": "Complexe taken, eigen vakgebied, soms aansturing van anderen.",
        "indicatie_ervaring": "5-10 jaar",
        "voorbeelden": "Senior calculator, uitvoerder, projectleider (aankomend)",
    },
    5: {
        "naam": "Niveau 5 - Senior specialist / leidinggevend",
        "kenmerk": "Brede verantwoordelijkheid, leiding over projecten of teams.",
        "indicatie_ervaring": "8-15 jaar",
        "voorbeelden": "Projectleider, senior uitvoerder, hoofd werkvoorbereiding",
    },
    6: {
        "naam": "Niveau 6 - Hogere staf / management",
        "kenmerk": "Strategische of zwaar coordinerende functie met grote verantwoordelijkheid.",
        "indicatie_ervaring": "12+ jaar",
        "voorbeelden": "Senior projectleider, projectmanager, afdelingshoofd",
    },
}


# Jeugdschalen (16 t/m 20 jaar) - Tabel 4.10. Deze zijn HARD leeftijdsafhankelijk.
# Voor de meeste UTA-detacheringssituaties (21+) niet relevant, maar wel nodig
# voor een compleet model. Hier alleen de structuur aangeduid; vul aan indien
# de tool ook jeugd moet ondersteunen.
JEUGD_LET_OP = (
    "Voor 16-20 jaar gelden aparte leeftijds- EN niveau-afhankelijke schalen "
    "(Tabel 4.10). Dit model richt zich op 21+ (Tabel 4.9). Jeugdschalen zijn "
    "puur leeftijdsbepaald en dus volledig deterministisch toe te voegen."
)


# ===========================================================================
# DEEL 2: WAT EEN OORDEEL IS (voorstel, geen zekerheid)
# ===========================================================================

class TredePositie(str, Enum):
    """Waar binnen de min-max band iemand wordt ingeschaald.
    DIT IS HET OORDEEL. De CAO geeft alleen min en max; waar iemand
    daartussen valt is bedrijfsbeleid / onderhandeling."""
    MINIMUM = "minimum"          # Starter in het niveau
    ONDER = "onderkant"          # Beperkte ervaring in het niveau
    MIDDEN = "midden"            # Gemiddelde ervaring
    BOVEN = "bovenkant"          # Ruime ervaring
    MAXIMUM = "maximum"          # Top van het niveau


def stel_niveau_voor(jaren_relevante_ervaring: float) -> tuple[int, str]:
    """
    Stelt een functieniveau VOOR op basis van ervaring.

    LET OP - DIT IS EXPLICIET EEN VOORSTEL, GEEN BEPALING:
    De echte functie-indeling hangt af van functie-inhoud, verantwoordelijkheid
    en het FUWA-indelingssysteem van de CAO - niet alleen van ervaringsjaren.
    Ervaring is slechts EEN indicator. Twee mensen met 6 jaar ervaring kunnen
    in verschillende niveaus vallen afhankelijk van wat ze doen.

    Deze functie geeft daarom een STARTPUNT voor het gesprek, dat de
    gebruiker (recruiter/inschaler) vervolgens bevestigt of bijstelt.
    """
    if jaren_relevante_ervaring < 1:
        return 1, "Voorstel op basis van ervaring; bevestig met functie-inhoud."
    elif jaren_relevante_ervaring < 3:
        return 2, "Voorstel op basis van ervaring; bevestig met functie-inhoud."
    elif jaren_relevante_ervaring < 6:
        return 3, "Voorstel op basis van ervaring; bevestig met functie-inhoud."
    elif jaren_relevante_ervaring < 10:
        return 4, "Voorstel op basis van ervaring; bevestig met functie-inhoud."
    elif jaren_relevante_ervaring < 13:
        return 5, "Voorstel op basis van ervaring; bevestig met functie-inhoud."
    else:
        return 6, "Voorstel op basis van ervaring; bevestig met functie-inhoud."


def bereken_loon_in_band(band: Loonband, positie: TredePositie) -> float:
    """
    Vertaalt een gekozen positie binnen de band naar een concreet uurloon.
    De positie is een OORDEEL; zodra die gekozen is, is het uurloon weer HARD.
    """
    span = band.maximum - band.minimum
    factor = {
        TredePositie.MINIMUM: 0.0,
        TredePositie.ONDER: 0.25,
        TredePositie.MIDDEN: 0.5,
        TredePositie.BOVEN: 0.75,
        TredePositie.MAXIMUM: 1.0,
    }[positie]
    return round(band.minimum + span * factor, 2)


# ===========================================================================
# DEEL 3: DE COMBINATIE - met scheiding hard vs. oordeel
# ===========================================================================

class KandidaatInput(BaseModel):
    """Wat je in een gesprek van een kandidaat hoort."""
    functie_omschrijving: str = Field(..., description="Wat de kandidaat doet, bijv. 'werkvoorbereider'")
    jaren_relevante_ervaring: float = Field(
        0.0, ge=0, description="Niet gebruikt in de hoofd-pipeline; alleen in schaal_in()-demo."
    )
    leeftijd: int = Field(
        21, ge=16, description="Niet gebruikt in berekening (jeugdschalen 4.10 niet geïmplementeerd)."
    )
    salarisverwachting_per_uur: Optional[float] = Field(None, description="Wat de kandidaat noemt")
    peildatum: date = Field(default_factory=date.today)


class Inschalingsresultaat(BaseModel):
    """
    Het resultaat, met expliciete scheiding tussen hard en oordeel.
    Dit is wat de tool toont - en het toont eerlijk wat zeker is en wat niet.
    """
    # --- HARD (uit de CAO) ---
    peildatum_tabel: date
    voorgesteld_niveau: int
    niveau_naam: str
    loonband_minimum: float
    loonband_maximum: float

    # --- OORDEEL (voorstel, bevestiging nodig) ---
    voorgestelde_positie: TredePositie
    voorgesteld_uurloon: float
    oordeel_disclaimer: str

    # --- CHECK op de verwachting van de kandidaat ---
    verwachting_past_in_band: Optional[bool]
    verwachting_opmerking: str


def check_salarisverwachting(
    peildatum: date,
    functieniveau: int,
    salarisverwachting_per_uur: Optional[float],
    jaren_op_niveau: float = 0.0,
    nieuw_in_bouw_infra: bool = False,
    starttabel_tweede_halfjaar: bool = False,
) -> tuple[Optional[bool], str]:
    """
    Controleer salarisverwachting tegen het LEIDENDE niveau (zelfde logica als v2).

    Gebruikt effectief minimum (doorgroeigarantie) en starttabel waar van toepassing.
    """
    if salarisverwachting_per_uur is None:
        return None, "Geen salarisverwachting opgegeven."

    v = salarisverwachting_per_uur
    band = get_loonband(functieniveau, peildatum)
    eff_min, doorgroei_pct = effectief_minimum(band, jaren_op_niveau)
    niveau_label = f"niveau {functieniveau}"

    if nieuw_in_bouw_infra:
        _, start_bedrag = get_starttabel(peildatum, starttabel_tweede_halfjaar)
        if start_bedrag is not None:
            halfjaar = "2e" if starttabel_tweede_halfjaar else "1e"
            if abs(v - start_bedrag) < 0.01:
                return True, (
                    f"Verwachting EUR {v:.2f} komt overeen met starttabel "
                    f"({halfjaar} halfjaar, art. 4.11)."
                )
            return None, (
                f"Starttabel actief: EUR {start_bedrag:.2f} ({halfjaar} halfjaar). "
                f"Verwachting EUR {v:.2f} — band-check op {niveau_label} niet leidend in dit jaar."
            )

    if v < eff_min:
        ondergrens = (
            f"effectief minimum EUR {eff_min:.2f}"
            if doorgroei_pct > 1.0
            else f"CAO-minimum EUR {eff_min:.2f}"
        )
        return False, (
            f"Verwachting EUR {v:.2f} ligt ONDER het {ondergrens} "
            f"op {niveau_label}. Mag niet lager (doorgroeigarantie meegerekend)."
        )

    if v > band.maximum:
        return False, (
            f"Verwachting EUR {v:.2f} ligt BOVEN het CAO-maximum van "
            f"EUR {band.maximum:.2f} op {niveau_label}. Overweeg een hoger niveau."
        )

    span = band.maximum - eff_min
    pct = (v - eff_min) / span * 100 if span > 0 else 0
    doorgroei_note = ""
    if doorgroei_pct > 1.0:
        doorgroei_note = (
            f" Ondergrens is effectief minimum ({doorgroei_pct * 100:.0f}% van tabelmin.), "
            f"niet EUR {band.minimum:.2f}."
        )
    return True, (
        f"Verwachting EUR {v:.2f} past in de band op {niveau_label} "
        f"(op {pct:.0f}% van effectief min naar max).{doorgroei_note}"
    )


def schaal_in(kandidaat: KandidaatInput) -> Inschalingsresultaat:
    """
    De kernfunctie: van kandidaat naar inschalingsVOORSTEL.

    Houdt hard en oordeel strikt gescheiden, en checkt of de
    salarisverwachting van de kandidaat realistisch is binnen de band.
    """
    # HARD: kies tabel
    tabel = get_loontabel(kandidaat.peildatum)
    gekozen_datum = get_peildatum_tabel(kandidaat.peildatum)

    # OORDEEL: stel niveau voor
    niveau, niveau_disclaimer = stel_niveau_voor(kandidaat.jaren_relevante_ervaring)
    band = tabel[niveau]

    # OORDEEL: stel positie binnen band voor op basis van waar de ervaring
    # valt binnen de indicatieve range van het niveau. Ook dit is een voorstel.
    voorgestelde_positie = TredePositie.MIDDEN  # neutraal startpunt
    voorgesteld_uurloon = bereken_loon_in_band(band, voorgestelde_positie)

    # CHECK (ervaring-voorstel): indicatief; pipeline vervangt dit met check op leidend niveau
    past, opmerking = check_salarisverwachting(
        kandidaat.peildatum,
        niveau,
        kandidaat.salarisverwachting_per_uur,
    )

    return Inschalingsresultaat(
        peildatum_tabel=gekozen_datum,
        voorgesteld_niveau=niveau,
        niveau_naam=FUNCTIENIVEAU_KENMERKEN[niveau]["naam"],
        loonband_minimum=band.minimum,
        loonband_maximum=band.maximum,
        voorgestelde_positie=voorgestelde_positie,
        voorgesteld_uurloon=voorgesteld_uurloon,
        oordeel_disclaimer=(
            "VOORSTEL, geen bepaling. " + niveau_disclaimer + " "
            "Het definitieve niveau en de trede binnen de band zijn een keuze "
            "van de inschaler op basis van functie-inhoud en bedrijfsbeleid."
        ),
        verwachting_past_in_band=past,
        verwachting_opmerking=opmerking,
    )


# ===========================================================================
# DEMO
# ===========================================================================

if __name__ == "__main__":
    # Voorbeeld zoals jouw situatie bij het detacheringsbedrijf:
    # kandidaat in gesprek, noemt een verwachting, jij wil snel weten waar dat valt.
    kandidaat = KandidaatInput(
        functie_omschrijving="werkvoorbereider",
        jaren_relevante_ervaring=6,
        leeftijd=34,
        salarisverwachting_per_uur=24.50,
        peildatum=date(2026, 3, 1),
    )

    r = schaal_in(kandidaat)

    print("=" * 70)
    print("INSCHALINGSVOORSTEL - CAO Bouw & Infra UTA")
    print("=" * 70)
    print(f"\nKandidaat: {kandidaat.functie_omschrijving}, "
          f"{kandidaat.jaren_relevante_ervaring} jaar ervaring, "
          f"{kandidaat.leeftijd} jaar")
    print(f"Tabel gebruikt: {r.peildatum_tabel.strftime('%d-%m-%Y')}")

    print("\n--- HARD (uit de CAO, zeker) ---")
    print(f"  Voorgesteld niveau: {r.niveau_naam}")
    print(f"  Loonband: EUR {r.loonband_minimum:.2f} - EUR {r.loonband_maximum:.2f}")

    print("\n--- OORDEEL (voorstel, bevestiging nodig) ---")
    print(f"  Voorgestelde positie: {r.voorgestelde_positie.value}")
    print(f"  Voorgesteld uurloon: EUR {r.voorgesteld_uurloon:.2f}")
    print(f"  {r.oordeel_disclaimer}")

    print("\n--- CHECK op verwachting kandidaat ---")
    print(f"  {r.verwachting_opmerking}")
    print("\n" + "=" * 70)
    print("Vanaf het bevestigde uurloon -> door naar de kostprijsberekening")
    print("(het deel dat de bestaande tools al doen).")
    print("=" * 70)
