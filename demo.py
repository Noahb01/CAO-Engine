"""
Demo suite — 9 scenario's voor Infrastructure Compliance Engine (v2).
"""

from datetime import date

from contract_generator import (
    genereer_bureau_overzicht,
    genereer_kandidaat_overzicht,
    genereer_marge_vergelijking_tabel,
    genereer_volledig_voorstel,
)
from inschaling_engine_v2 import (
    Inschaling,
    TredePositie,
    VerwachtingActie,
    bereken,
    bereken_tarief_direct,
)
from inschalingsmodel import KandidaatInput
from cao_data import bereken_maandsalaris, bereken_vier_weken_salaris


def print_header(n: int, titel: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"SCENARIO {n}: {titel}")
    print("=" * 70)


def scenario_1_basis_tariefberekening() -> None:
    print_header(1, "Basis tariefberekening")
    b = bereken_tarief_direct(functieniveau=4, peildatum=date(2025, 6, 1), marge_pct=15)
    print(f"Functieniveau 4, start 01-06-2025, midden band")
    print(f"  Bruto uurloon:     €{b.bruto_uurloon:.2f}")
    print(f"  Omrekenfactor:     {b.omrekenfactor}")
    print(f"  Kostprijs:         €{b.kostprijs_per_uur:.2f}/uur")
    print(f"  Facturatie:        €{b.facturatie_per_uur:.2f}/uur ({b.totaal_factor_op_bruto}× bruto)")


def scenario_2_hoger_loon() -> None:
    print_header(2, "Hoger loon dan CAO-minimum")
    b = bereken_tarief_direct(
        functieniveau=4,
        peildatum=date(2025, 6, 1),
        basis_uurloon=22.50,
        marge_pct=15,
    )
    print(f"Functieniveau 4, bruto €22.50 (band €{b.band_min:.2f} – €{b.band_max:.2f})")
    print(f"  Facturatie:        €{b.facturatie_per_uur:.2f}/uur")


def scenario_3_verwachting_onder_minimum() -> None:
    print_header(3, "Verwachting onder minimum (blokkeren)")
    try:
        bereken(
            Inschaling(
                functieniveau=5,
                peildatum=date(2026, 1, 1),
                salarisverwachting_per_uur=20.00,
                verwachting_actie=VerwachtingActie.BLOKKEER,
            )
        )
        print("  Onverwacht: geen blokkade!")
    except ValueError as e:
        print(f"  ✓ Berekening geblokkeerd:")
        print(f"    {e}")

    b = bereken(
        Inschaling(
            functieniveau=5,
            peildatum=date(2026, 1, 1),
            salarisverwachting_per_uur=20.00,
            verwachting_actie=VerwachtingActie.CORRIGEER_NAAR_MINIMUM,
        )
    )
    print(f"  Met correctie: bruto €{b.bruto_uurloon:.2f} (was €20.00)")


def scenario_4_tabelwisseling() -> None:
    print_header(4, "Automatische tabelwisseling tussen jaren")
    for d in [date(2025, 6, 1), date(2026, 3, 1), date(2027, 6, 1)]:
        b = bereken_tarief_direct(functieniveau=3, peildatum=d)
        print(
            f"  Start {d.strftime('%d-%m-%Y')}: "
            f"tabel {b.cao_tabel.strftime('%d-%m-%Y')}, "
            f"minimum €{b.band_min:.2f}"
        )


def scenario_5_marge_impact() -> None:
    print_header(5, "Impact van verschillende marges")
    print(genereer_marge_vergelijking_tabel(4, date(2026, 1, 1), basis_uurloon=24.00))


def scenario_6_kandidaat_overzicht() -> None:
    print_header(6, "Kandidaat overzicht generatie")
    b = bereken_tarief_direct(
        functieniveau=4,
        peildatum=date(2026, 1, 15),
        basis_uurloon=24.00,
    )
    print(
        genereer_kandidaat_overzicht(
            b,
            kandidaat_naam="Jan Jansen",
            opdrachtgever="Rijkswaterstaat",
            project_naam="A1 Apeldoorn-Zuid",
            peildatum=date(2026, 1, 15),
        )
    )


def scenario_7_bureau_overzicht() -> None:
    print_header(7, "Bureau overzicht (intern)")
    b = bereken_tarief_direct(
        functieniveau=4,
        peildatum=date(2026, 1, 15),
        basis_uurloon=24.00,
        marge_pct=15,
    )
    print(
        genereer_bureau_overzicht(
            b,
            kandidaat_naam="Jan Jansen",
            opdrachtgever="Rijkswaterstaat",
            project_naam="A1 Apeldoorn-Zuid",
            peildatum=date(2026, 1, 15),
        )
    )


def scenario_8_marge_vergelijking() -> None:
    print_header(8, "Marge vergelijkingstabel")
    print(genereer_marge_vergelijking_tabel(3, date(2025, 8, 1)))


def scenario_9_edge_cases() -> None:
    print_header(9, "Edge cases")
    b = bereken_tarief_direct(
        functieniveau=1,
        peildatum=date(2025, 5, 1),
        positie_in_band=TredePositie.MINIMUM,
    )
    print(f"  CAO start (01-05-2025): niveau 1 minimum €{b.bruto_uurloon:.2f}")

    band_max = bereken_tarief_direct(
        functieniveau=6,
        peildatum=date(2027, 12, 31),
        basis_uurloon=41.42,
    )
    print(f"  CAO einde (31-12-2027): niveau 6 max €{band_max.bruto_uurloon:.2f}")

    maand = bereken_maandsalaris(22.50)
    vier = bereken_vier_weken_salaris(22.50)
    print(f"  Maandsalaris bij €22.50/uur:     €{maand:.2f}")
    print(f"  4-weken salaris bij €22.50/uur:  €{vier:.2f}")

    print("\n  --- Volledige pipeline (inschaling → tarief v2) ---")
    voorstel = genereer_volledig_voorstel(
        kandidaat=KandidaatInput(
            functie_omschrijving="Werkvoorbereider",
            salarisverwachting_per_uur=24.50,
            peildatum=date(2026, 3, 1),
        ),
        kandidaat_naam="Jan Jansen",
        opdrachtgever="Rijkswaterstaat",
        project_naam="A1 Apeldoorn-Zuid",
        marge_pct=15,
    )
    ins = voorstel["inschaling"]
    ber = voorstel["berekening"]
    print(f"  Voorstel uit functietitel: niveau {voorstel['voorgesteld_niveau']}")
    print(f"  Gebruikt niveau:           {voorstel['gebruikt_niveau']} ({voorstel['niveau_bron']})")
    print(f"  Facturatie:        €{ber.facturatie_per_uur:.2f}/uur ({ber.totaal_factor_op_bruto}× bruto)")


SCENARIOS = [
    scenario_1_basis_tariefberekening,
    scenario_2_hoger_loon,
    scenario_3_verwachting_onder_minimum,
    scenario_4_tabelwisseling,
    scenario_5_marge_impact,
    scenario_6_kandidaat_overzicht,
    scenario_7_bureau_overzicht,
    scenario_8_marge_vergelijking,
    scenario_9_edge_cases,
]


def main() -> None:
    print("Infrastructure Compliance Engine — Demo Suite (v2)")
    print("CAO Bouw & Infra 2025-2027 — Model A kostprijs")
    for fn in SCENARIOS:
        fn()
    print(f"\n{'=' * 70}")
    print("Alle 9 scenario's succesvol uitgevoerd.")
    print("=" * 70)


if __name__ == "__main__":
    main()
