"""
INSCHALING + KOSTPRIJS ENGINE - CAO Bouw & Infra UTA
=====================================================
Versie 2 - gecorrigeerd

WAT IS ER GECORRIGEERD T.O.V. VERSIE 1:
1. Eén bron van waarheid voor het niveau (functiekeuze is leidend, niet
   een aparte ervaringsberekening die een ander niveau oplevert).
2. ADV niet meer als losse 6,8%-opslag. UTA heeft 15 ROOSTERVRIJE DAGEN;
   die verlagen de productieve uren en horen daarom in de omrekenfactor
   via netto werkbare dagen - niet als procentuele toeslag bovenop het loon.
3. Kostprijs volgens MODEL A: bruto uurloon x omrekenfactor. De factor
   bevat alle werkgeverskosten en reserveringen EEN keer. Geen dubbeltelling
   van vakantiegeld (dat zit in de factor, niet er nog eens bovenop).
4. "Verwachting onder minimum" stopt de berekening niet stilzwijgend maar
   dwingt een expliciete keuze af (corrigeer naar minimum, of blokkeer).

EERLIJKHEIDSPRINCIPE (ongewijzigd, en juist nu belangrijker):
- HARD = uit de CAO, zeker. - OORDEEL = voorstel, bevestiging nodig.
- De premiepercentages in de factor zijn WERKGEVERSSPECIFIEK. Ze staan hier
  als configureerbare defaults, NIET als CAO-waarheid. De tool moet de
  gebruiker zijn eigen premies laten invullen; anders is "compliant" een
  loze claim.

Bronnen voor de UTA-regeling: cao Bouw & Infra 2025-2027 (FNV-publicatie),
Bouwend Nederland, BTER-bouw. 15 roostervrije dagen UTA; 20 wettelijke +
10 bovenwettelijke vakantiedagen; 8% vakantietoeslag; pensioen via bpfBOUW.
"""

from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator


# ===========================================================================
# DEEL 1: HARD - CAO-loontabellen (Tabel 4.9, UTA 21+)
# ===========================================================================

class Loonband(BaseModel):
    minimum: float
    maximum: float


LOONTABELLEN_21PLUS = {
    date(2025, 5, 1): {
        1: Loonband(minimum=15.01, maximum=19.55), 2: Loonband(minimum=16.44, maximum=21.72),
        3: Loonband(minimum=18.27, maximum=24.46), 4: Loonband(minimum=20.66, maximum=28.08),
        5: Loonband(minimum=23.77, maximum=32.78), 6: Loonband(minimum=27.82, maximum=38.85),
    },
    date(2025, 7, 1): {
        1: Loonband(minimum=15.16, maximum=19.75), 2: Loonband(minimum=16.60, maximum=21.94),
        3: Loonband(minimum=18.45, maximum=24.70), 4: Loonband(minimum=20.87, maximum=28.36),
        5: Loonband(minimum=24.01, maximum=33.11), 6: Loonband(minimum=28.10, maximum=39.24),
    },
    date(2026, 1, 1): {
        1: Loonband(minimum=15.77, maximum=20.54), 2: Loonband(minimum=17.26, maximum=22.82),
        3: Loonband(minimum=19.19, maximum=25.69), 4: Loonband(minimum=21.70, maximum=29.49),
        5: Loonband(minimum=24.97, maximum=34.43), 6: Loonband(minimum=29.22, maximum=40.81),
    },
    date(2027, 1, 1): {
        1: Loonband(minimum=16.01, maximum=20.85), 2: Loonband(minimum=17.52, maximum=23.16),
        3: Loonband(minimum=19.48, maximum=26.08), 4: Loonband(minimum=22.03, maximum=29.93),
        5: Loonband(minimum=25.34, maximum=34.95), 6: Loonband(minimum=29.66, maximum=41.42),
    },
}

NIVEAU_KENMERKEN = {
    1: "Niveau 1 - Ondersteunend / startend",
    2: "Niveau 2 - Uitvoerend",
    3: "Niveau 3 - Zelfstandig uitvoerend",
    4: "Niveau 4 - Specialist / coordinerend",
    5: "Niveau 5 - Senior specialist / leidinggevend",
    6: "Niveau 6 - Hogere staf / management",
}


# --- HARD: Starttabel UTA 21+ (art. 4.11) ---
# Voor de UTA-werknemer die NOG NIET eerder in bouw & infra heeft gewerkt.
# Geldt maximaal 1 jaar. Bedragen per halfjaar (1e/2e halfjaar).
# "nntb" = nog niet te bepalen (afhankelijk van Wml); daarom None.
STARTTABEL_21PLUS = {
    date(2025, 5, 1): {"halfjaar_1": 14.30, "halfjaar_2": 14.54},
    date(2025, 7, 1): {"halfjaar_1": 14.59, "halfjaar_2": 14.78},
    date(2026, 1, 1): {"halfjaar_1": 14.98, "halfjaar_2": 15.24},
    # 1-7-2026 en 1-1-2027: nntb in de CAO (Wml nog niet bekend)
    date(2027, 1, 1): {"halfjaar_1": None, "halfjaar_2": None},
}


# --- HARD: Doorgroeigarantie (art. 4.9.2) ---
# De UTA-werknemer 21+ heeft uiterlijk na X jaar op een niveau recht op
# een percentage van het MINIMUM van dat niveau. Dit is het effectieve
# minimum dat hoger ligt dan de tabelwaarde naarmate de diensttijd stijgt.
DOORGROEI_GARANTIE = {
    0: 1.00,   # bij indeling: 100% van het minimum
    2: 1.04,   # na 2 jaar: 104%
    4: 1.10,   # na 4 jaar: 110%
    6: 1.16,   # na 6 jaar: 116%
}


def effectief_minimum(band: "Loonband", jaren_op_niveau: float) -> tuple[float, float]:
    """
    Bereken het effectieve CAO-minimum op basis van diensttijd op het niveau.
    Geeft (effectief_minimum, toegepast_percentage) terug.

    Dit is HARD CAO-recht (art. 4.9.2): iemand die al jaren op een niveau zit,
    mag niet meer op het tabelminimum worden betaald.
    """
    drempels = sorted(DOORGROEI_GARANTIE.keys())
    pct = DOORGROEI_GARANTIE[0]
    for drempel in drempels:
        if jaren_op_niveau >= drempel:
            pct = DOORGROEI_GARANTIE[drempel]
    return round(band.minimum * pct, 2), pct


def get_loontabel(peildatum: date):
    datums = sorted(LOONTABELLEN_21PLUS.keys())
    gekozen = None
    for d in datums:
        if d <= peildatum:
            gekozen = d
        else:
            break
    if gekozen is None:
        raise ValueError(f"Peildatum {peildatum} ligt voor de eerste CAO-tabel ({datums[0]}).")
    return gekozen, LOONTABELLEN_21PLUS[gekozen]


def get_starttabel(peildatum: date, tweede_halfjaar: bool = False):
    """Haal het starttabel-uurloon op voor 21+ die nieuw is in bouw & infra.
    Geeft (datum, bedrag) terug. Bedrag kan None zijn (nntb in CAO)."""
    datums = sorted(STARTTABEL_21PLUS.keys())
    gekozen = None
    for d in datums:
        if d <= peildatum:
            gekozen = d
        else:
            break
    if gekozen is None:
        raise ValueError(f"Peildatum {peildatum} ligt voor de eerste starttabel ({datums[0]}).")
    sleutel = "halfjaar_2" if tweede_halfjaar else "halfjaar_1"
    return gekozen, STARTTABEL_21PLUS[gekozen][sleutel]


# ===========================================================================
# DEEL 2: HARD - werkbare dagen en roostervrije dagen (UTA)
# ===========================================================================
# Roostervrije dagen verlagen de PRODUCTIEVE uren: je betaalt voor meer uren
# dan er gefactureerd kunnen worden. Dit is de juiste manier om "ADV" te
# verwerken voor UTA - via de netto werkbare dagen, niet als losse opslag.

WERKBARE_DAGEN_PER_JAAR = 261          # bruto werkbare dagen 2025-2027 (CAO-rekenbasis)
UTA_VAKANTIEDAGEN = 20                  # wettelijk
UTA_BOVENWETTELIJK = 10                 # bovenwettelijke vrije dagen
UTA_ROOSTERVRIJE_DAGEN = 15             # specifiek UTA
UTA_KORT_VERZUIM = 3                    # kort verzuim
GEM_FEESTDAGEN = 7                      # doorbetaalde feestdagen (indicatief)

# Netto werkbare (= productieve) dagen = werkbaar minus alle vrije dagen.
NETTO_WERKBARE_DAGEN = (
    WERKBARE_DAGEN_PER_JAAR
    - UTA_VAKANTIEDAGEN - UTA_BOVENWETTELIJK
    - UTA_ROOSTERVRIJE_DAGEN - UTA_KORT_VERZUIM - GEM_FEESTDAGEN
)  # = 261 - 55 = 206 productieve dagen (indicatief)


# ===========================================================================
# DEEL 3: CONFIGUREERBAAR - werkgeverslasten (NIET CAO-waarheid!)
# ===========================================================================
# Deze percentages verschillen PER WERKGEVER en per jaar. Ze staan hier als
# realistische defaults zodat de tool draait, maar in de echte applicatie
# moet de gebruiker (de werkgever) ze zelf invullen/bevestigen. Daarom een
# eigen klasse met expliciete defaults en bron-aanduiding.

class WerkgeverslastenConfig(BaseModel):
    """Werkgeverspremies en reserveringen. Defaults zijn INDICATIEF.
    De werkgever bevestigt zijn eigen percentages."""
    vakantietoeslag_pct: float = Field(8.0, description="CAO: 8% - dit is wel hard")
    duurzame_inzetbaarheid_pct: float = Field(2.30, description="Individueel Budget, duurzame inzetbaarheid UTA 2026 (art. 4.14) - HARD CAO")
    pensioen_bpfbouw_pct: float = Field(15.9, description="bpfBOUW werkgeversdeel - INDICATIEF, check je regeling")
    sociale_lasten_pct: float = Field(18.0, description="WW/WIA/ZVW etc. - INDICATIEF, werkgeverspecifiek")
    sociaal_fonds_scholing_pct: float = Field(2.5, description="O&O-fonds, scholing - INDICATIEF")
    verzuim_risico_pct: float = Field(4.0, description="Doorbetaling bij ziekte - INDICATIEF")

    @property
    def som_premies_pct(self) -> float:
        """Alle premies die als % over het loon worden geheven."""
        return (self.pensioen_bpfbouw_pct + self.sociale_lasten_pct
                + self.sociaal_fonds_scholing_pct + self.verzuim_risico_pct)


# ===========================================================================
# DEEL 4: OORDEEL - positie in de band
# ===========================================================================

class TredePositie(str, Enum):
    MINIMUM = "minimum"
    ONDER = "onderkant"
    MIDDEN = "midden"
    BOVEN = "bovenkant"
    MAXIMUM = "maximum"


_POSITIE_FACTOR = {
    TredePositie.MINIMUM: 0.0, TredePositie.ONDER: 0.25, TredePositie.MIDDEN: 0.5,
    TredePositie.BOVEN: 0.75, TredePositie.MAXIMUM: 1.0,
}


def loon_in_band(band: Loonband, positie: TredePositie) -> float:
    return round(band.minimum + (band.maximum - band.minimum) * _POSITIE_FACTOR[positie], 2)


# ===========================================================================
# DEEL 5: INPUT
# ===========================================================================

class VerwachtingActie(str, Enum):
    """Wat te doen als de salarisverwachting onder het CAO-minimum ligt."""
    CORRIGEER_NAAR_MINIMUM = "corrigeer_naar_minimum"
    BLOKKEER = "blokkeer"


class Inschaling(BaseModel):
    kandidaat_naam: str = ""
    functieniveau: int = Field(..., ge=1, le=6, description="LEIDEND. Door de inschaler gekozen/bevestigd.")
    peildatum: date = Field(default_factory=date.today)
    positie_in_band: TredePositie = TredePositie.MIDDEN
    salarisverwachting_per_uur: Optional[float] = None
    verwachting_actie: VerwachtingActie = VerwachtingActie.CORRIGEER_NAAR_MINIMUM

    # NIEUW: starttabel-vertakking (art. 4.11)
    nieuw_in_bouw_infra: bool = Field(
        False, description="True = nog nooit eerder in bouw & infra gewerkt. Dan geldt de starttabel (max 1 jaar)."
    )
    starttabel_tweede_halfjaar: bool = Field(
        False, description="Alleen relevant als nieuw_in_bouw_infra=True. False=1e halfjaar, True=2e halfjaar."
    )

    # NIEUW: diensttijd op dit niveau voor de doorgroeigarantie (art. 4.9.2)
    jaren_op_niveau: float = Field(
        0.0, ge=0, description="Aantal jaren dat de werknemer al op dit functieniveau is ingedeeld. Bepaalt het effectieve minimum (104%/110%/116%)."
    )

    # marge-instellingen (bureau)
    omrekenfactor_override: Optional[float] = Field(
        None, description="Als gezet: gebruik deze vaste factor i.p.v. opbouw."
    )
    marge_pct: float = Field(0.0, ge=0, description="Marge als % bovenop de kostprijs (0 = alleen kostprijs).")


# ===========================================================================
# DEEL 6: RESULTAAT
# ===========================================================================

class Resultaat(BaseModel):
    # HARD
    cao_tabel: date
    functieniveau: int
    niveau_naam: str
    band_min: float
    band_max: float
    netto_werkbare_dagen: int

    # NIEUW: starttabel
    starttabel_toegepast: bool
    # NIEUW: doorgroeigarantie (art. 4.9.2)
    effectief_minimum: float          # het minimum na toepassing diensttijd
    doorgroei_percentage: float       # 1.00 / 1.04 / 1.10 / 1.16
    doorgroei_lijn: dict              # min bij 0/2/4/6 jaar, ter info

    # GEKOZEN LOON (na positie + verwachtingscheck)
    bruto_uurloon: float
    bruto_bron: str  # legt uit hoe dit loon tot stand kwam

    # VERWACHTINGSCHECK
    verwachting_status: str

    # KOSTPRIJS (Model A: factor-opbouw)
    omrekenfactor: float
    factor_opbouw: dict
    kostprijs_per_uur: float

    # FACTURATIE
    marge_pct: float
    facturatie_per_uur: float
    waarschuwingen: list[str]


def bereken(inschaling: Inschaling,
            config: Optional[WerkgeverslastenConfig] = None) -> Resultaat:
    if config is None:
        config = WerkgeverslastenConfig()

    waarschuwingen: list[str] = []
    _cfg = config

    # --- HARD: tabel en band ---
    cao_datum, tabel = get_loontabel(inschaling.peildatum)
    band = tabel[inschaling.functieniveau]

    # --- HARD: doorgroeigarantie (art. 4.9.2) ---
    # Bepaal het EFFECTIEVE minimum op basis van diensttijd op dit niveau.
    eff_min, doorgroei_pct = effectief_minimum(band, inschaling.jaren_op_niveau)
    doorgroei_lijn = {
        "0_jaar": round(band.minimum * 1.00, 2),
        "2_jaar_104pct": round(band.minimum * 1.04, 2),
        "4_jaar_110pct": round(band.minimum * 1.10, 2),
        "6_jaar_116pct": round(band.minimum * 1.16, 2),
    }
    if doorgroei_pct > 1.0:
        waarschuwingen.append(
            f"Doorgroeigarantie (art. 4.9.2): na {inschaling.jaren_op_niveau:.0f} jaar op dit niveau "
            f"is het effectieve minimum EUR {eff_min:.2f} ({doorgroei_pct*100:.0f}% van het tabelminimum), "
            f"niet EUR {band.minimum:.2f}."
        )

    # --- STARTTABEL-VERTAKKING (art. 4.11) ---
    starttabel_toegepast = False
    if inschaling.nieuw_in_bouw_infra:
        start_datum, start_bedrag = get_starttabel(
            inschaling.peildatum, inschaling.starttabel_tweede_halfjaar
        )
        if start_bedrag is None:
            waarschuwingen.append(
                "Starttabel-bedrag is voor deze peildatum nog niet bekend (nntb in CAO; "
                "afhankelijk van het wettelijk minimumloon). Doorgerekend met de reguliere band."
            )
        else:
            starttabel_toegepast = True
            bruto = start_bedrag
            halfjaar = "2e" if inschaling.starttabel_tweede_halfjaar else "1e"
            bruto_bron = (
                f"STARTTABEL toegepast ({halfjaar} halfjaar, art. 4.11): EUR {start_bedrag:.2f}. "
                f"Geldt max. 1 jaar voor wie nieuw is in bouw & infra. "
                f"Functieniveau-band ({band.minimum:.2f}-{band.maximum:.2f}) geldt hierna."
            )
            verwachting_status = "Starttabel actief; functieniveau-verwachting niet leidend in dit jaar."
            # bij starttabel slaan we de band-/verwachtingslogica over
            return _maak_resultaat(
                inschaling, cao_datum, band, eff_min, doorgroei_pct, doorgroei_lijn,
                bruto, bruto_bron, verwachting_status, starttabel_toegepast,
                waarschuwingen, _cfg,
            )

    # --- GEKOZEN LOON (reguliere band) ---
    # Startpunt: de gekozen positie in de band (oordeel).
    voorstel_loon = loon_in_band(band, inschaling.positie_in_band)
    # Maar nooit onder het effectieve minimum (doorgroeigarantie).
    if voorstel_loon < eff_min:
        voorstel_loon = eff_min
    bruto_bron = f"Voorstel op basis van positie '{inschaling.positie_in_band.value}' in de band."

    # Verwachting verwerken, indien opgegeven. De ondergrens is het EFFECTIEVE
    # minimum (doorgroeigarantie), niet het tabelminimum.
    if inschaling.salarisverwachting_per_uur is not None:
        v = inschaling.salarisverwachting_per_uur
        if v < eff_min:
            if inschaling.verwachting_actie == VerwachtingActie.BLOKKEER:
                raise ValueError(
                    f"Salarisverwachting EUR {v:.2f} ligt onder het effectieve CAO-minimum "
                    f"EUR {eff_min:.2f} voor niveau {inschaling.functieniveau} "
                    f"(incl. doorgroeigarantie). Berekening geblokkeerd."
                )
            bruto = eff_min
            bruto_bron = (f"Verwachting EUR {v:.2f} lag ONDER het effectieve minimum; "
                          f"gecorrigeerd naar EUR {eff_min:.2f}.")
            waarschuwingen.append(
                f"Let op: verwachte EUR {v:.2f} mocht niet (onder effectief minimum "
                f"EUR {eff_min:.2f}). Doorgerekend met EUR {eff_min:.2f}."
            )
            verwachting_status = bruto_bron
        elif v > band.maximum:
            bruto = band.maximum
            bruto_bron = (f"Verwachting EUR {v:.2f} lag BOVEN maximum; "
                          f"begrensd op CAO-maximum EUR {band.maximum:.2f}.")
            waarschuwingen.append(
                f"Verwachting EUR {v:.2f} boven het maximum van dit niveau. "
                f"Overweeg een hoger niveau. Doorgerekend met EUR {band.maximum:.2f}."
            )
            verwachting_status = bruto_bron
        else:
            bruto = round(v, 2)
            pct = (v - band.minimum) / (band.maximum - band.minimum) * 100
            bruto_bron = f"Verwachting EUR {v:.2f} gebruikt (op {pct:.0f}% van de band)."
            verwachting_status = bruto_bron
    else:
        bruto = voorstel_loon
        verwachting_status = "Geen verwachting opgegeven; voorstel uit band gebruikt."

    return _maak_resultaat(
        inschaling, cao_datum, band, eff_min, doorgroei_pct, doorgroei_lijn,
        bruto, bruto_bron, verwachting_status, starttabel_toegepast,
        waarschuwingen, _cfg,
    )


def _maak_resultaat(inschaling, cao_datum, band, eff_min, doorgroei_pct,
                    doorgroei_lijn, bruto, bruto_bron, verwachting_status,
                    starttabel_toegepast, waarschuwingen,
                    config: Optional["WerkgeverslastenConfig"] = None) -> "Resultaat":
    if config is None:
        config = WerkgeverslastenConfig()

    # --- KOSTPRIJS via MODEL A (omrekenfactor) ---
    if inschaling.omrekenfactor_override is not None:
        factor = inschaling.omrekenfactor_override
        factor_opbouw = {"vaste_factor_gebruikt": factor,
                         "let_op": "Vaste factor opgegeven; opbouw niet berekend."}
    else:
        premie_factor = 1 + (config.som_premies_pct + config.vakantietoeslag_pct
                             + config.duurzame_inzetbaarheid_pct) / 100
        productiviteit_correctie = WERKBARE_DAGEN_PER_JAAR / NETTO_WERKBARE_DAGEN
        factor = round(premie_factor * productiviteit_correctie, 4)
        factor_opbouw = {
            "vakantietoeslag_pct": config.vakantietoeslag_pct,
            "duurzame_inzetbaarheid_pct": config.duurzame_inzetbaarheid_pct,
            "som_premies_pct": round(config.som_premies_pct, 2),
            "premie_factor": round(premie_factor, 4),
            "werkbare_dagen": WERKBARE_DAGEN_PER_JAAR,
            "netto_werkbare_dagen": NETTO_WERKBARE_DAGEN,
            "productiviteit_correctie": round(productiviteit_correctie, 4),
            "let_op": "Premies zijn INDICATIEF en werkgeverspecifiek. Bevestig je eigen percentages.",
        }

    kostprijs = round(bruto * factor, 2)
    facturatie = round(kostprijs * (1 + inschaling.marge_pct / 100), 2)

    if inschaling.omrekenfactor_override is None:
        waarschuwingen.append(
            "Omrekenfactor is opgebouwd met INDICATIEVE premies. Voor een "
            "bindende offerte: vul de werkelijke werkgeverspremies in."
        )

    return Resultaat(
        cao_tabel=cao_datum,
        functieniveau=inschaling.functieniveau,
        niveau_naam=NIVEAU_KENMERKEN[inschaling.functieniveau],
        band_min=band.minimum,
        band_max=band.maximum,
        netto_werkbare_dagen=NETTO_WERKBARE_DAGEN,
        starttabel_toegepast=starttabel_toegepast,
        effectief_minimum=eff_min,
        doorgroei_percentage=doorgroei_pct,
        doorgroei_lijn=doorgroei_lijn,
        bruto_uurloon=bruto,
        bruto_bron=bruto_bron,
        verwachting_status=verwachting_status,
        omrekenfactor=factor,
        factor_opbouw=factor_opbouw,
        kostprijs_per_uur=kostprijs,
        marge_pct=inschaling.marge_pct,
        facturatie_per_uur=facturatie,
        waarschuwingen=waarschuwingen,
    )


# ===========================================================================
# DEMO
# ===========================================================================

if __name__ == "__main__":

    def toon(titel, inschaling):
        r = bereken(inschaling)
        print("=" * 68)
        print(titel)
        print("=" * 68)
        print(f"\n--- HARD (uit de CAO) ---")
        print(f"  CAO-tabel:         {r.cao_tabel.strftime('%d-%m-%Y')}")
        print(f"  Niveau:            {r.niveau_naam}")
        print(f"  Tabelband:         EUR {r.band_min:.2f} - EUR {r.band_max:.2f}")
        print(f"  Effectief minimum: EUR {r.effectief_minimum:.2f} "
              f"({r.doorgroei_percentage*100:.0f}% - doorgroeigarantie art. 4.9.2)")
        print(f"  Doorgroeilijn:     0jr EUR {r.doorgroei_lijn['0_jaar']:.2f} | "
              f"2jr EUR {r.doorgroei_lijn['2_jaar_104pct']:.2f} | "
              f"4jr EUR {r.doorgroei_lijn['4_jaar_110pct']:.2f} | "
              f"6jr EUR {r.doorgroei_lijn['6_jaar_116pct']:.2f}")
        print(f"  Starttabel actief: {'JA' if r.starttabel_toegepast else 'nee'}")

        print(f"\n--- GEKOZEN LOON ---")
        print(f"  Bruto uurloon:     EUR {r.bruto_uurloon:.2f}")
        print(f"  Herkomst:          {r.bruto_bron}")

        print(f"\n--- KOSTPRIJS (Model A) ---")
        print(f"  Omrekenfactor:     {r.omrekenfactor}")
        print(f"  Kostprijs/uur:     EUR {r.kostprijs_per_uur:.2f}")
        print(f"  Facturatie ({r.marge_pct:.0f}%):   EUR {r.facturatie_per_uur:.2f}")

        if r.waarschuwingen:
            print(f"\n--- WAARSCHUWINGEN ---")
            for w in r.waarschuwingen:
                print(f"  ! {w}")
        print()

    # Casus 1: ervaren kandidaat, al 5 jaar op niveau 3 -> doorgroeigarantie 110%
    toon("CASUS 1 - Ervaren (5 jaar op niveau 3): doorgroeigarantie",
         Inschaling(
             kandidaat_naam="Jan Jansen", functieniveau=3,
             peildatum=date(2026, 3, 1), positie_in_band=TredePositie.MINIMUM,
             jaren_op_niveau=5, salarisverwachting_per_uur=20.00, marge_pct=15.0,
         ))

    # Casus 2: nieuw in bouw & infra -> starttabel
    toon("CASUS 2 - Nieuw in bouw & infra: starttabel (art. 4.11)",
         Inschaling(
             kandidaat_naam="Nieuwe Instromer", functieniveau=2,
             peildatum=date(2026, 3, 1), nieuw_in_bouw_infra=True,
             starttabel_tweede_halfjaar=False, marge_pct=15.0,
         ))

    # Casus 3: verwachting onder effectief minimum bij ervaren kandidaat
    toon("CASUS 3 - Verwachting onder effectief minimum",
         Inschaling(
             kandidaat_naam="Test", functieniveau=4,
             peildatum=date(2026, 3, 1), jaren_op_niveau=6,
             salarisverwachting_per_uur=22.00, marge_pct=15.0,
         ))
