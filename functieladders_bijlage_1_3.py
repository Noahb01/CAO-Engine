"""
CAO Bouw & Infra 2025-2027 — Bijlage 1.3 UTA functieladders (laag 1).

Bron: cao Bouw & Infra 2025-2027, bijlage 1.3 (publicatie 19 juni 2025).
Karakteristieken zijn letterlijk overgenomen waar de CAO ze geeft.
Lege niveaus zijn NIET ingevuld — status 'leeg_in_cao'.
PM-verwijzingen zijn overgenomen zonder interpretatie.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class NiveauKarakteristiek(BaseModel):
    niveau: int = Field(..., ge=1, le=6)
    karakteristiek: Optional[str] = None
    status: str = Field(
        ...,
        description="ingevuld | leeg_in_cao",
    )


class Functieladder(BaseModel):
    nummer: int = Field(..., ge=1, le=25)
    naam: str
    intredekeuring_verplicht: bool = False
    niveaus: list[NiveauKarakteristiek]
    pm_verwijzingen: list[str] = Field(default_factory=list)

    @property
    def beschikbare_niveaus(self) -> list[int]:
        return [n.niveau for n in self.niveaus if n.status == "ingevuld"]

    @property
    def lege_niveaus(self) -> list[int]:
        return [n.niveau for n in self.niveaus if n.status == "leeg_in_cao"]


def _n(niveau: int, tekst: Optional[str]) -> NiveauKarakteristiek:
    if tekst and tekst.strip():
        return NiveauKarakteristiek(niveau=niveau, karakteristiek=tekst.strip(), status="ingevuld")
    return NiveauKarakteristiek(niveau=niveau, karakteristiek=None, status="leeg_in_cao")


def _ladder(
    nummer: int,
    naam: str,
    karakteristieken: dict[int, Optional[str]],
    *,
    intredekeuring: bool = False,
    pm: Optional[list[str]] = None,
) -> Functieladder:
    return Functieladder(
        nummer=nummer,
        naam=naam,
        intredekeuring_verplicht=intredekeuring,
        niveaus=[_n(i, karakteristieken.get(i)) for i in range(1, 7)],
        pm_verwijzingen=pm or [],
    )


# Functieniveaumatrix (CAO) — welke niveaus per ladder bestaan volgens de matrix.
# Afwijkingen t.o.v. ingevulde karakteristieken worden in lege_niveaus zichtbaar.
FUNCTIENIVEAU_MATRIX: dict[int, list[int]] = {
    1: [1, 2, 3, 4],
    2: [1, 2, 3, 4, 5],
    3: [1, 2, 3, 4],
    4: [1, 2, 3, 4, 5],
    5: [1, 2, 3, 4],
    6: [1, 2, 3],
    7: [1, 2, 3, 4],
    8: [1, 2, 3, 4, 5, 6],
    9: [1, 2, 3, 4],
    10: [1, 2, 3, 4, 5],
    11: [1, 2, 3, 4, 5],
    12: [1, 2, 3, 4],
    13: [1, 2, 3, 4],
    14: [1, 2, 3, 4, 5, 6],
    15: [1, 2, 3, 4, 5, 6],
    16: [1, 2, 3, 4, 5],
    17: [1, 2, 3],
    18: [1, 2, 3, 4],
    19: [1, 2, 3, 4, 5],
    20: [1, 2, 3, 4],
    21: [1, 2, 3, 4, 5],
    22: [1, 2],
    23: [1, 2, 3, 4, 5, 6],
    24: [1, 2],
    25: [1],
}


FUNCTIELADDERS: list[Functieladder] = [
    _ladder(
        1,
        "Uitvoering",
        {
            6: (
                "Geeft via enkele uitvoerders en/of voorlieden leiding aan de uitvoering van één "
                "of meer middelgrote (wegen)bouwprojecten of een onderdeel van een groot project "
                "met circa 25 medewerkers op het werk (bij strak geprogrammeerde bouwstromen tot "
                "50 medewerkers). Onderhoudt vooral de contacten met leveranciers, onderaannemers "
                "en opzichter(s). Wordt eventueel geassisteerd door een hulpuitvoerder of assistent "
                "voor bijvoorbeeld bouwplaatsorganisatie, maatvoering en werkadministratie."
            ),
            5: (
                "Geeft, via voorlieden of rechtstreeks aan vaklieden, leiding aan de uitvoering van "
                "kleine (wegen)bouwprojecten of delen, respectievelijk fases van grote projecten met "
                "minder dan 20 medewerkers. Roept materiaal af, koopt kleine hoeveelheden zelf in. "
                "Verzorgt zelf planning en kostenbewaking. Woont bouwvergaderingen bij ter assistentie "
                "van de bouwplaatsleiding. Verwerft in overleg met de directie opdrachten voor "
                "onderhoud en kleine verbouwingen op de lokale markt."
            ),
            4: (
                "Geeft leiding aan een ploeg vaklieden met minder dan 10 medewerkers, eventueel met "
                "een meewerkend voorman, belast met de uitvoering van een of enkele kleine "
                "(deel)projecten. Verwerft in overleg met de directie soms kleine opdrachten op de "
                "lokale markt en regelt de personeelsvoorziening op het werk. Verzorgt bij wegenbouw "
                "maatvoering en marketing of opmeten van gebouwen en terreinen. Geeft meetgegevens "
                "door aan de afdeling Calculatie. Assisteert hoofduitvoerders en uitvoerders op grote "
                "projecten."
            ),
            3: (
                "Assisteert uitvoerders bij de dagelijkse werkzaamheden op kleine en middelgrote "
                "projecten met bouwplaatsorganisatie, helpt bij maatvoering, verleent administratieve "
                "assistentie, neemt de stand van het werk op e.d."
            ),
            2: None,
            1: None,
        },
        intredekeuring=True,
    ),
    _ladder(
        2,
        "Bedrijfsbureau",
        {
            6: (
                "Geeft leiding aan een bedrijfsbureau met 5 à 10 medewerkers, belast met bijvoorbeeld "
                "werkvoorbereiding en calculatie en eventueel inkoop voor merendeels middelgrote "
                "utiliteitsbouwprojecten of bijvoorbeeld werkvoorbereiding voor grote woning- of "
                "wegenbouwprojecten."
            ),
            5: (
                "Geeft leiding aan een bedrijfsbureau met enkele medewerkers die werkvoorbereiding en/of "
                "calculatie verzorgen voor middelgrote (wegen)-bouwprojecten, met in totaal maximaal "
                "100 medewerkers op de werken. Zet bij de aanvang van een project de planning- en "
                "kostenbewaking op. Legt in overleg met de commerciële leiding bezoeken af voor het "
                "verwerven van kleine en middelgrote projecten, met hoofdzakelijk technische "
                "problematiek. Overlegt met opdrachtgevers over de prijs. Koopt soms materialen in "
                "of verricht arbeidskundige studies en adviseert de bedrijfsleiding met betrekking "
                "tot werkmethoden, bouwsystemen e.d. Bewaakt mede de bouwkosten en neemt initiatieven "
                "tot bijsturing."
            ),
            4: (
                "Levert specialistische assistentie op grond van opleiding of uitgebreide ervaring bij "
                "het voorbereiden en uitvoeren van grote/middelgrote projecten, levert specialistische "
                "bijdragen op het gebied van bijvoorbeeld calculatie, netwerkplanning, bijzonder "
                "bouwkundig tekenwerk (zoals tunnelbekisting), bouwplaatsinrichting en voortgangs- "
                "en kostenbewaking."
            ),
            3: (
                "Assisteert bij calculatie of werkvoorbereiding, zoals berekening van meer- en "
                "minderwerk, materiaal afroepen of bestellen, in detail uittrekken van bestek en "
                "tekeningen, werkenadministratie en transportplanning. Is bijvoorbeeld belast met de "
                "coördinatie van maatvoering van sparingen op tekeningen of controleert activiteiten "
                "aan de hand van een draaiboek."
            ),
            2: (
                "Tekent schema's, codeert urenbriefjes en dergelijke, verleent assistentie op "
                "aanwijzingen van zijn chef."
            ),
            1: None,
        },
        pm=["Werkvoorbereiding", "Calculatie"],
    ),
    _ladder(
        3,
        "Werkvoorbereiding",
        {
            6: (
                "Geeft leiding aan een afdeling met 5 à 10 medewerkers (soms in combinatie met "
                "Calculatie) voor het opzetten en up-to-date houden van overall-plan en afgeleide "
                "deel- en capaciteitstoewijzingsplannen van grote bouwprojecten. Bepaalt de "
                "kostenstand van het werk. Laat afwijkingen signaleren aan de desbetreffende "
                "projectleiding en levert alternatieven voor bijstelling van het plan. Onderzoekt "
                "alternatieve bouwmethoden."
            ),
            5: (
                "Zet bij de aanvang van projecten het projectbewakingssysteem op. Ziet vervolgens toe "
                "op overname van de werkzaamheden door een of enkele assistenten. Signaleert op grond "
                "van de planning de voortgang en de kosten van middelgrote tot grote werken. "
                "Signaleert de knelpunten. Onderzoekt alternatieve werkmethoden. Maakt manuren-"
                "begroting, materieelplan, bouwplaatsinrichtingsplan ter bewaking van "
                "onderaannemers e.d."
            ),
            4: (
                "Verricht (soms bijgestaan door een enkele assistent) de werkvoorbereiding van grote "
                "projecten. Is daartoe gedetacheerd op het werk. Verzorgt de planning en de "
                "voortgangssignalering of de kostenbewaking. Stelt voor kleine projecten planningen "
                "en manurenbegrotingen op. Signaleert aan de leiding de stand van het werk en de "
                "toeleveringen, verzorgt soms een deel van de materiaalbestellingen en de calculatie "
                "of de werkenadministratie."
            ),
            3: (
                "Stelt voor een klein of middelgroot bouwproject een stroken-planningsschema op volgens "
                "aanwijzingen van zijn chef en/of de bouwplaatsleiding. Codeert urenbriefjes voor "
                "computerverwerking. Stelt termijnbetalingsschema's op aan de hand van gegevens. "
                "Maakt detailtekeningen en kozijnenstaat op aanwijzingen."
            ),
            2: None,
            1: None,
        },
        pm=["Bedrijfsbureau", "Calculatie"],
    ),
    _ladder(
        4,
        "Calculatie",
        {
            6: (
                "Bepaalt in overleg met de verantwoordelijken voor commerciële zaken de bijstelling "
                "van posten 'onder de streep' op de inschrijvingsbegroting. Onderhandelt op "
                "aanwijzingen van de directie of productieleiding over de prijs. Geeft leiding aan "
                "5 à 10 medewerkers van Calculatie, Werkvoorbereiding en eventueel Inkoop. Voert "
                "exploitatieberekeningen uit voor woningbouwprojecten die in eigen beheer worden "
                "gebouwd en verkocht."
            ),
            5: (
                "Overlegt met architect en/of constructeur over alternatieve bouwwijzen. Stelt de "
                "staartposten in de begroting op. Prijst de posten boven de streep af. Beslist over "
                "aanpassing van calculatienormen. Regelt met leveranciers en onderaannemers "
                "materiaalleveranties en dienstverlening en bedingt kortingen op de prijs. Geeft "
                "eventueel leiding aan enkele calculatoren. Voert exploitatieberekeningen uit voor "
                "projecten die in opdracht van projectontwikkelaars zullen worden uitgevoerd."
            ),
            4: (
                "Stelt begrotingsposten op; weegt daarbij alternatieve werkmethoden af. Prijst "
                "hoeveelhedenstaten. Stelt elementenbegroting op op basis van een globaal ontwerp. "
                "Verricht op aanwijzingen onderzoek naar aanpassing van calculatienormen. Maakt "
                "opstellingen voor meer- en minderwerk. Vraagt offertes aan bij leveranciers en "
                "onderaannemers. Bezoekt 'Inlichtingen' of 'Aanwijzingen' van kleine en middelgrote "
                "werken om toelichting te krijgen op bestek en tekeningen. Stelt voor kleine "
                "projecten normen vast op grond van veel ervaring. Verricht soms neventaken in "
                "werkvoorbereiding en/of administratie. Ziet eventueel toe op de werkzaamheden van "
                "een of enkele assistenten."
            ),
            3: (
                "Trekt materiaalhoeveelheden uit aan de hand van bestek en tekeningen. Stelt "
                "standaardbegrotingsposten op met behulp van normen. Vult staartposten in voor "
                "zover standaard."
            ),
            2: (
                "Stelt nacalculaties op aan de hand van de administratie. Vraagt prijsopgave van "
                "materialen of huurmaterieel en bijkomende dienstverlening bij leveranciers."
            ),
            1: None,
        },
        pm=["Bedrijfsbureau", "Werkvoorbereiding"],
    ),
    _ladder(
        5,
        "Planontwikkeling, constructiebureau en tekenkamer",
        {
            6: (
                "Maakt bebouwingsplannen in het kader van uitbreidingsplannen of bouwkundig ontwerp "
                "voor de utiliteitsbouw. Ontwerpt en berekent constructies in beton en staal. "
                "Coördineert de bijdragen van derden en zorgt voor inpassing van bijvoorbeeld "
                "technische installaties in het bouwkundig ontwerp. Voert besprekingen voor het "
                "verkrijgen van vergunningen en dergelijke met overheidsinstanties en met de "
                "opdrachtgever over de aard van het ontwerp. Geeft leiding aan enkele "
                "tekenaars/constructeurs."
            ),
            5: (
                "Ziet toe op en werkt zelf mee aan het uitwerken van bouwkundige ontwerpen voor "
                "woningbouw en kleine utiliteitsbouw. Levert zelf ontwerpschets en aanwijzingen. "
                "Maakt het bestek. Overlegt over het ontwerp met de opdrachtgever en de constructeur "
                "en woont de bouwteamvergaderingen bij. Voert beton- en staalconstructietekenwerk en "
                "-rekenwerk uit voor kleine utiliteitsbouw en woningbouw."
            ),
            4: (
                "Werkt vormtekeningen met hoofdmaten uit in bouwkundige detailtekeningen. Vervaardigt "
                "bestek en tekeningen voor verbouwingen, woningbouw of fabriekshallen op aanwijzingen. "
                "Maakt daarvoor staalconstructie- en betonwapeningstekeningen en voert de daarvoor "
                "noodzakelijke berekeningen uit."
            ),
            3: (
                "Maakt vormtekeningen voor de constructeur of bekistingstekeningen. Maakt eenvoudige "
                "detailtekeningen en bouwkundige werktekeningen, matenplannen, kozijnenstaten etc. "
                "op aanwijzingen."
            ),
            2: None,
            1: None,
        },
    ),
    _ladder(
        6,
        "Marketing en verkoop",
        {
            6: (
                "Levert technische en/of financiële ondersteuning bij verkoopactiviteiten. Overlegt "
                "met potentiële opdrachtgevers en hun adviseurs over de realiseerbaarheid van hun "
                "wensen. Maakt na intern overleg een prijsindicatie of geeft technische oplossingen "
                "voor bouwkundige problemen. Begeleidt de start van het ontwerpproces en schakelt "
                "Calculatie in. Verkoopt zelf kleine tot middelgrote projecten met vooral technische "
                "aspecten, zoals wegenaanleg en fabrieksuitbreidingen."
            ),
            5: (
                "Levert een technische en/of calculatorische bijdrage voor verkoopgesprekken. Geeft "
                "technische oplossingen voor bouwkundige problemen en geeft kostenconsequenties aan. "
                "Beoordeelt de technische en financiële haalbaarheid van wijzigingsvoorstellen. "
                "Levert bijdragen in marktonderzoeken door onderzoeksresultaten samen te vatten en te "
                "analyseren. Behandelt een deel van de vragenlijsten voor selectieprocedures voor "
                "samenstelling van bouwteams. Presenteert voor belangstellenden de mogelijkheden van "
                "het bedrijf."
            ),
            4: (
                "Beheert (computer)bestanden met gegevens over de eigen onderneming, over uitgevoerde "
                "projecten en gegevens over de markt. Werkt deze bestanden bij aan de hand van "
                "interne bronnen en voornamelijk literatuur. Maakt overzichten ten behoeve van de "
                "verkoopbevordering. Verstrekt op aanvraag informatie over het eigen bedrijf en over "
                "uitgevoerde of in uitvoering zijnde projecten. Verkoopt in overleg met de directie "
                "of commerciële leiding op de lokale markt kleine, onderhands uit te voeren "
                "verbouwingen, uitbreidingen, kleine restauraties e.d."
            ),
            3: None,
            2: None,
            1: None,
        },
        pm=["Administratie algemeen"],
    ),
    _ladder(
        7,
        "Inkoop",
        {
            6: (
                "Verzorgt in samenwerking met een assistent de inkoop van bouwmaterialen, materieel "
                "en diensten van derden voor een middelgroot bedrijf of deel van een groot bedrijf. "
                "Laat prijsoffertes aanvragen. Sluit na intern overleg jaarcontracten af voor "
                "omvangrijke leveranties van bepaalde bouwmaterialen (betonijzer etc.). Voert "
                "prijsonderhandelingen en regelt bestellingen en opdrachtverlening aan leveranciers "
                "en onderaannemers."
            ),
            5: (
                "Koopt gereedschappen, afbouwmaterialen en kantoorbenodigdheden in. Verwerft opties op "
                "zandwinning ten behoeve van eventueel uit te voeren wegenbouwprojecten. Onderhoudt "
                "de contacten met leveranciers. Overlegt met directie of commerciële leiding over de "
                "te bedingen leveringscondities en leverancierskeuze. Verzamelt en bewerkt niet "
                "rechtstreeks toegankelijke marktinformatie."
            ),
            4: (
                "Koopt bouwmaterialen en -materieel in op aanwijzingen van zijn chef. Heeft frequent "
                "contact met leveranciers over prijzen en leverdata. Verstrekt prijsinformatie aan "
                "calculators, zorgt voor materiaalmonsters en overlegt met Uitvoering over "
                "hoeveelheden en levertijden."
            ),
            3: (
                "Roept materialen af op basis van raamcontracten. Koopt kleine hoeveelheden materialen "
                "in aan de hand van prijslijsten en prijsopgaven van leveranciers, ter aanvulling "
                "van magazijnvoorraden. Verzorgt de bijbehorende administratie."
            ),
            2: None,
            1: None,
        },
        pm=["Administratie algemeen"],
    ),
    _ladder(
        8,
        "Beheer van materiaal en bouwmateriaal",
        {
            6: (
                "Coördineert de inzet van bedieningspersoneel. Geeft leiding aan onderhoudspersoneel, "
                "dat onderhoud aan het materieel uitvoert in een werkplaats, op het materieelerf of "
                "op de bouwplaats. Ziet toe op de inzet van materieel en bedieningspersoneel. Bewaakt "
                "onderhoudskosten en signaleert de status van het materieel. Adviseert bij aankoop of "
                "vervanging van materieel. Besteedt specialistisch onderhoud uit aan derden."
            ),
            5: (
                "Regelt de inzet van materieel en bedieningspersoneel op een of meer middelgrote tot "
                "grote (wegen)bouwprojecten. Regelt inhuur en verhuur van groot materieel met derden "
                "en stelt daarbij de huurprijzen vast op basis van richtlijnen. Adviseert met betrekking "
                "tot bouwplaatsinrichting, inzet materieel, aanschaf, afstoten en ontwikkeling van "
                "materieel. Bewaakt energieverbruik, afschrijving materieel en materieelkosten per "
                "werk. Houdt toezicht op enige assistenten."
            ),
            4: (
                "Behandelt materieelaanvragen. Stelt schema's op voor inzet materieel en transporten "
                "van materialen (asfalt, beton, elementen e.d.). Regelt inhuur van materieel en "
                "transporten voor derden. Verstrekt informatie over verhuur materieel. Zorgt voor "
                "reparatie en preventief onderhoud. Houdt daartoe enige kleine administraties bij. "
                "Houdt eventueel toezicht op assistenten."
            ),
            3: (
                "Beheert een klein magazijn. Verzorgt administratieve voorraadbewaking en bestelt "
                "hulpmaterieel. Ziet toe op de werkzaamheden van een magazijnbediende of verzorgt "
                "met een ploeg werfpersoneel de opslag en afvoer van materieel en materialen. Regelt "
                "de belading van de vrachtwagens overeenkomstig laad- en transportschema's. Zorgt voor "
                "een doelmatige indeling van het terrein en een verantwoorde opslag. Ziet erop toe dat "
                "het nodige onderhoud wordt verricht, alsook eenvoudige reparatiewerkzaamheden aan "
                "materieel. Verricht een aantal eenvoudige administratieve werkzaamheden."
            ),
            2: (
                "Verzorgt de uitgifte van onderdelen, materialen en/of gereedschappen. Controleert de "
                "aangevoerde goederen en materialen en signaleert wanneer aanvullingen nodig zijn. "
                "Draagt zorg voor een doelmatige indeling en opslag in het magazijn en houdt een "
                "eenvoudige magazijnadministratie bij."
            ),
            1: (
                "Assisteert bij uitpakken, controleren, tellen, sorteren, coderen, opbergen en uitgeven "
                "van goederen in het magazijn, alsmede bij het verzend gereed maken en laden en lossen "
                "van voertuigen."
            ),
        },
    ),
    _ladder(
        9,
        "Onderhoud materieel",
        {
            6: None,
            5: (
                "Geeft leiding aan een groep van (circa 10 medewerkers) onderhoudspersoneel, werkzaam "
                "in een werkplaats, op het materieelerf of op de bouwplaats. Ziet toe op het onderhoud "
                "van bijvoorbeeld bouwkranen, wegenbouwmachines, asfaltinstallaties en vrachtwagens. "
                "Besteedt een deel van het werk uit en bewaakt dit."
            ),
            4: (
                "Houdt toezicht op enkele medewerkers en werkt zelf mee aan het onderhoud van materieel "
                "op de bouwplaats, op het materieelerf of in de werkplaats. Besteedt eventueel "
                "onderhoudswerk uit, koopt hulpmaterialen en onderdelen in volgens richtlijnen. "
                "Verzorgt werkvoorbereiding en taakverdeling. Verricht op grond van uitgebreide opleiding "
                "en/of veel ervaring al het voorkomende onderhoud en montagewerk of een deel van het "
                "gespecialiseerde onderhoud aan bijvoorbeeld kranen, wegenbouwmachines en vrachtwagens."
            ),
            3: (
                "Verricht allerlei vakkundig onderhoud en montagewerk aan (wegen)bouwmaterieel, op "
                "aanwijzingen."
            ),
            2: (
                "Assisteert vaklieden bij het onderhoud van (wegen)bouwmaterieel. Verricht eenvoudige "
                "demontage. Voert smeerbeurten uit. Heft kleine mechanische storingen op. Vervangt "
                "onderdelen, etc."
            ),
            1: None,
        },
    ),
    _ladder(
        10,
        "Kwaliteitscontrole asfalt en/of beton",
        {
            6: (
                "Geeft leiding aan beton- of asfaltproductie, alsmede aan een kwaliteitscontrole-"
                "laboratorium (totaal 5 à 10 medewerkers). Ontwikkelt receptuur, organiseert de "
                "kwaliteitsbewaking van grondstoffen en halffabrikaat. Beheert de apparatuur in "
                "fabriek en laboratorium. Kiest grondstoffenleveranciers en onderhandelt met hen over "
                "leveringscondities."
            ),
            5: (
                "Geeft leiding aan een kwaliteitscontrolelaboratorium (met circa 5 medewerkers) voor "
                "asfalt en/of beton. Stelt de kwaliteitsnormen vast en bepaalt de onderzoeksprocedures. "
                "Stelt volgens receptuur of op basis van bestekeisen asfaltmengsels samen en onderzoekt "
                "of deze mengsels aan de gestelde eisen voldoen aan de hand van proefnemingen. "
                "Onderhoudt externe contacten met materiaaldeskundigen en deskundigen van opdrachtgevers "
                "over materiaalproblematiek. Adviseert de bedrijfsleiding in dezen."
            ),
            4: (
                "Verricht alle voorkomende laboratoriumonderzoeken naar kwaliteit en samenstelling van "
                "grondstoffen en halffabrikaten, alsmede boorkernonderzoek van eindproducten. Ziet toe "
                "op de werkzaamheden van enkele assistenten. Rapporteert via chef aan belanghebbenden. "
                "Geeft receptuur af aan de fabriek. Bestelt grondstoffen op basis van raamcontract."
            ),
            3: (
                "Verricht volgens vastgestelde procedures onderzoek ten aanzien van grondstoffen en "
                "eindproducten van asfalt en/of beton. Analyseert onderzoeksresultaten en geeft op grond "
                "van richtlijnen advies over goed- of afkeuring van grondstoffen, aanpassingen in "
                "receptuur en condities bij het productieproces."
            ),
            2: (
                "Assisteert bij de uitvoering van onderzoeken naar kwaliteit en samenstelling van "
                "grondstoffen, halffabrikaten en eindproducten, zoals het nemen en transporteren van "
                "materiaalmonsters en voorbereiden en uitvoeren van eenvoudige proeven op aanwijzingen."
            ),
            1: None,
        },
    ),
    _ladder(
        11,
        "Administratie algemeen",
        {
            6: (
                "Geeft leiding aan administratieve werkzaamheden, zoals productieadministratie, "
                "risicoverrekening, factuurcontrole en dergelijke, verdeeld over afdelingen met in "
                "totaal 10 à 20 medewerkers. Bewaakt dergelijke administratieve procedures, voert "
                "vernieuwingen in na overleg. Laat overzichten per project maken en analyseert en "
                "beoordeelt deze, rapporteert analyseresultaten aan de bedrijfsleiding."
            ),
            5: (
                "Geeft leiding aan maximaal 10 medewerkers belast met kosten- en/of tijdbewaking, "
                "nacalculatie van projecten of inkoopadministratie. Stelt de te volgen procedures vast. "
                "Controleert en analyseert de gegevens, draagt oplossingen aan voor de gesignaleerde "
                "administratieve problemen. Adviseert bij het uitbrengen van offertes, respectievelijk "
                "de keuze van leveranciers. Assisteert bij prijsonderhandelingen. Bewaakt de afhandeling "
                "van risicoregelingen."
            ),
            4: (
                "Controleert administratieve werkzaamheden van anderen. Maakt samenvattingen van "
                "gegevens en analyseert deze. Signaleert afwijkingen van budgetten, planning en "
                "dergelijke en geeft toelichting. Neemt intern en extern contact op voor het uitzoeken "
                "van administratieve verschillen of onduidelijkheden. Stelt aanvragen voor offertes op. "
                "Bewaakt de levertijden. Stelt op en onderhoudt contacten met de leverancier. Behandelt "
                "schademeldingen, klachten van gebruikers, juridische aangelegenheden en dergelijke "
                "volgens richtlijnen. Signaleert probleemgevallen aan zijn chef."
            ),
            3: (
                "Verzamelt en verwerkt administratieve gegevens volgens vaste procedures ten behoeve "
                "van registraties of periodieke overzichten. Controleert administratieve gegevens door "
                "interne vergelijking, externe navraag van gegevens, berekeningen, e.d. Splitst "
                "gegevens of stelt deze samen volgens diverse vaste sleutels. Stelt eenvoudige "
                "correspondentie op, verricht alle soorten typewerk, controleert voorraden, budgetten "
                "en dergelijke en signaleert afwijkingen."
            ),
            2: (
                "Voert controles op facturen uit door vergelijkingen met staten. Maakt tellingen van "
                "bedragen. Codeert facturen, bonnen en dergelijke volgens vaste voorschriften. Voert "
                "administratieve mutaties uit. Verricht correspondentietypewerk aan de hand van concept "
                "en archiveert facturen en correspondentie."
            ),
            1: None,
        },
        pm=[
            "Werkenadministratie",
            "Salaris- en loonadministratie",
            "Boekhouding",
            "Geautomatiseerde administratie",
        ],
    ),
    _ladder(
        12,
        "Werkenadministratie",
        {
            6: None,
            5: (
                "Zet bij de aanvang van middelgrote en grote projecten de werkenadministratie op. "
                "Geeft leiding aan maximaal 10 medewerkers, belast met werkenadministratie. Maakt "
                "periodiek financiële overzichten per werk en bespreekt deze periodiek met de leiding "
                "van de uitvoering. Controleert loonberekening, facturering, verrekeningen van risico's "
                "en meer- en minderwerk e.d."
            ),
            4: (
                "Administreert volgens voorschriften het onderhanden werk. Verzamelt gegevens voor "
                "nacalculatie, bepaalt de voortgang van het werk en signaleert afwijkingen van het "
                "budget. Maakt volgens voorschrift periodiek een kostenoverzicht met meer- en "
                "minderwerk en doorberekeningen volgens de risicoregeling per project, ter voorbereiding "
                "van de automatische administratie of handboekhouding. Heeft de eindcontrole op "
                "facturen ter voorbereiding van betaalbaarstelling."
            ),
            3: (
                "Verwerkt materiaalbonnen, materieelbonnen, urenbriefjes en dergelijke voor het opstellen "
                "van weekrapporten en periodieke overzichten. Berekent lonen aan de hand van "
                "urenbriefjes, ziekmeldingen, e.d. Typt verslagen van vergaderingen en afrekeningstaten. "
                "Controleert facturen aan de hand van computerlijsten en zoekt verschillen uit door "
                "navraag bij de leverancier."
            ),
            2: (
                "Verzamelt en controleert bonnen, facturen en dergelijke door tellingen en vergelijking "
                "van bedragen; zoekt intern verschillen uit."
            ),
            1: None,
        },
        pm=[
            "Administratie algemeen",
            "Salaris- en loonadministratie",
            "Boekhouding",
            "Geautomatiseerde administratie",
        ],
    ),
    _ladder(
        13,
        "Salaris- en loonadministratie",
        {
            6: (
                "Geeft leiding aan de salaris- en loonadministratie. Ontwikkelt richtlijnen voor de "
                "toepassing van de cao. Stelt regelingen op inzake aanvullende arbeidsvoorwaarden. "
                "Verricht bijvoorbeeld bij reorganisaties of fusies voorbereidende werkzaamheden ten "
                "dienste van overleg met de werknemersorganisaties. Maakt het cijfermatige gedeelte "
                "van het sociaal jaarverslag. Onderhoudt werkcontacten met sociale instellingen, "
                "computercentrum en dergelijke."
            ),
            5: (
                "Verzorgt met een assistent de loon- en salarisadministratie. Verwerkt personeelsmutaties. "
                "Maakt salaris- en loonberekeningen in geval van mutaties. Verzorgt mutaties in de "
                "basisgegevens van de computerinput. Zorgt voor het doorgeven van gegevens aan de "
                "bedrijfsvereniging, het computercentrum en dergelijke. Controleert computeroutput. "
                "Controleert uitkeringen. Maakt en/of controleert de desbetreffende journaalposten "
                "voor het grootboek. Maakt cijfermatige overzichten. Behandelt klachten van het "
                "personeel betreffende loon of salaris of vervult soms de rol van personeelsfunctionaris; "
                "behandelt dan diverse personeelsproblemen of verwijst door naar externe instanties, "
                "bedrijfsleiding of directie. Assisteert bij belastingaangifte. Assisteert bij werving "
                "bouwplaatswerknemers."
            ),
            4: (
                "Verzamelt urengegevens van de werken. Voert delen van de personeels- en/of "
                "loonadministratie uit. Maakt de desbetreffende journaalposten voor het grootboek. "
                "Richt dossiers in, maakt loonberekeningen. Geeft ziekmeldingen door. Behandelt "
                "klachten over het loon of verwijst door. Onderhoudt werkcontacten met een "
                "computercentrum. Beheert een kas."
            ),
            3: (
                "Verzamelt, codeert en verwerkt urenbriefjes en berekent cao-lonen. Verricht diverse "
                "secretariaats- en administratieve taken ter assistentie in de afdeling of op het werk."
            ),
            2: None,
            1: None,
        },
        pm=[
            "Administratie algemeen",
            "Werkenadministratie",
            "Boekhouding",
            "Geautomatiseerde administratie",
        ],
    ),
    _ladder(
        14,
        "Boekhouding",
        {
            6: (
                "Geeft leiding aan de weinig of niet-geautomatiseerde boekhouding en administratie met "
                "10 tot 20 medewerkers, onder andere de afdelingen Boekhouding, Loonadministratie, "
                "soms Werkenadministratie, Interne Dienst, e.d. Behandelt zelf complexe of "
                "vertrouwelijke zaken, zoals salarisadministratie en onderzoek en verbetering van de "
                "procedures. Behandelt problemen met betalingen, het afstemmen van rekeningen en de "
                "waardering van activa op grond van richtlijnen e.d. Geeft via zijn chef toelichting "
                "aan directie en externe accountant. Controleert de afdrachten van premies en "
                "belastingen. Stelt periodieke balansen en winst- en verliesrekeningen op. Bewaakt "
                "en signaleert de kosten- en liquiditeitsontwikkeling. Stemt de verslagleggingen van "
                "enkele kleine werkmaatschappijen op elkaar af."
            ),
            5: (
                "Verricht de boekhoudkundige werkzaamheden voor een kleine bouwonderneming of kleine "
                "werkmaatschappijen; wordt daarin eventueel bijgestaan door assistenten. Verzorgt de "
                "loonadministratie en de loonuitbetaling. Houdt subadministraties bij, zowel "
                "debiteuren, crediteuren, kas, bank en giro. Houdt het grootboek bij. Maakt "
                "periodiek liquiditeitsoverzichten voor de directie. Beheert de kas. Onderhoudt "
                "contacten met klanten, leveranciers, sociale instellingen e.d. Geeft toelichting ter "
                "verklaring van de jaarstukken aan directie en accountant."
            ),
            4: (
                "Geeft leiding aan een deeladministratie met routinematig werk, uitgevoerd door 5 tot "
                "10 medewerkers. Controleert de boekingen. Behandelt zelf de probleemgevallen en "
                "onderhoudt daartoe ook contacten met bijvoorbeeld klanten en leveranciers. Maakt "
                "overzichten en weet hierop toelichting te geven. Voert registraties en opgaven uit "
                "volgens wettelijke regelingen, zoals afdrachten van premies en ziekmeldingen. Voert "
                "eventueel complete boekhouding voor kleine werkeenheden, zoals timmerfabriek en "
                "asfalt- of betoninstallatiebedrijf."
            ),
            3: (
                "Ziet toe op en werkt zelf mee aan het bijhouden van subadministraties (kas, bank, "
                "giro, debiteuren en crediteuren). Behandelt onjuiste of incomplete gegevens, neemt "
                "daartoe eventueel contact op met klanten, leveranciers en anderen ter verificatie "
                "van (betalings)gegevens. Vraagt om assistentie, als dit problemen oplevert. Maakt "
                "loonberekeningen op aanwijzing. Stelt complexe facturen samen en stelt "
                "specificaties op."
            ),
            2: (
                "Sorteert, splitst en codeert factuurbedragen naar het rekeningenstelsel. Splitst "
                "kosten over kostensoorten en kostenplaatsen, een en ander volgens nauwkeurige "
                "voorschriften. Verricht boekhoudingen in sub- en grootboek. Controleert tellingen "
                "en corrigeert boekingsverschillen na interne verificatie. Vraagt bij "
                "probleemgevallen om assistentie."
            ),
            1: (
                "Sorteert en codeert facturen, controleert gegevens door vergelijking met staten."
            ),
        },
        pm=[
            "Administratie algemeen",
            "Werkenadministratie",
            "Salaris- en loonadministratie",
            "Geautomatiseerde administratie",
        ],
    ),
    _ladder(
        15,
        "Geautomatiseerde administratie",
        {
            6: (
                "Geeft leiding aan geautomatiseerde administratie met maximaal 10 medewerkers, op "
                "basis van standaardprogrammatuur voor werkenadministratie, boekhouding, "
                "voorraadbeheer, budgetbewaking en dergelijke. Verzorgt de totale financiële "
                "verslaglegging van een middelgrote onderneming. Past de interne informatieprocedures "
                "en werkregeling aan op het systeem in overleg met de leverancier of besteedt de "
                "computerverwerking uit aan een computerservicebureau. Zorgt voor onderhoud en "
                "verbeteren van computerprogramma's door eigen medewerkers en levert een belangrijke "
                "bijdrage in de systeemanalyse."
            ),
            5: (
                "Verricht, eventueel met enkele assistenten en een minicomputer, de complete "
                "boekhouding voor een klein bedrijf of een werkmaatschappij, of een grote "
                "deeladministratie, zoals werkenadministratie, voor een middelgroot tot groot bedrijf "
                "of besteedt dergelijke werkzaamheden uit aan een computerservicebureau. Maakt zelf "
                "analyses van de gegevens en geeft toelichting op bijvoorbeeld de jaarstukken. "
                "Onderhoudt contacten met het computerservicebureau, met leveranciers, met klanten "
                "e.a. Beheert een kas."
            ),
            4: (
                "Geeft leiding aan 10 tot 20 datatypisten. Verzorgt de werkregeling en de "
                "doorbelasting van verwerkingskosten aan computergebruikers. Behandelt problemen met "
                "gebruikers. Parametreert nieuwe toepassingen. Verzorgt de invoer van diverse "
                "niet-voorgecodeerde gegevens in een geautomatiseerde administratie, bijvoorbeeld "
                "complete boekhouding, personeels- en/of salarisadministratie, e.d. Controleert "
                "output en zoekt fouten uit in overleg met het computercentrum of servicebureau."
            ),
            3: (
                "Verdeelt werk over datatypisten. Assisteert hen bij bedieningsproblemen. Controleert "
                "en verbetert fouten, ook door rechtstreeks ingrijpen via controlebeeldscherm. "
                "Bewaakt de productiestroom en zorgt voor tijdige aflevering. Springt in bij storingen."
            ),
            2: (
                "Voert gecodeerde gegevens en controlegegevens in volgens vaste procedures. Voert "
                "controles uit en verbetert fouten of signaleert problemen. Assisteert bij "
                "werkverdeling. Springt in bij storingen. Verricht ter afwisseling diverse sorteer- "
                "en controletaken op administratieve afdelingen."
            ),
            1: (
                "Voert gecodeerde en gestandaardiseerde gegevens in met een (beeld scherm)terminal."
            ),
        },
        pm=[
            "Administratie algemeen",
            "Werkenadministratie",
            "Salaris- en loonadministratie",
            "Boekhouding",
        ],
    ),
    _ladder(
        16,
        "Computerbediening",
        {
            6: (
                "Geeft leiding aan een klein computercentrum, inclusief het beheer van hard- en "
                "software, met maximaal 10 medewerkers. Koopt hard- en software op basis van "
                "goedgekeurde automatiseringsplannen. Signaleert herhaalde storingen aan de "
                "leverancier en overlegt hoe deze te voorkomen. Ontwikkelt procedures voor gebruik "
                "en beveiliging, bestanden, e.d. Zorgt voor opleiding van bedieningspersoneel."
            ),
            5: (
                "Geeft leiding aan een ploeg van circa 5 computeroperators. Stelt aan de hand van "
                "prioriteiten de werkvolgorde en de procesgang vast en draagt zorg voor de optimale "
                "benutting van computer en randapparatuur. Bedient zelf de controleprocessor bij "
                "niet-routinematige procesgangen. Behandelt incidenten en storingen met "
                "belanghebbenden en leveranciers. Rapporteert over aanhoudende problemen. Zorgt voor "
                "het in goede staat houden van de apparatuur en een correcte dienstverlening."
            ),
            4: (
                "Ziet toe op en werkt zelf mee aan de bediening van een middelgroot computersysteem "
                "door enkele operators. Grijpt in bij storingen en tracht deze te verhelpen. "
                "Signaleert duurzame storingen aan de leiding en aan de leverancier. Verzorgt de "
                "werkregeling op de computer. Overlegt met gebruikers bij stagnaties in de "
                "verwerking. Houdt bezettingsoverzichten bij. Voert doorbelastingen van de kosten uit."
            ),
            3: (
                "Bedient computerapparatuur, zowel randapparatuur als centrale processor op "
                "aanwijzingen. Zorgt bij storingen voor veiligstelling van apparatuur en gegevens. "
                "Signaleert storingen."
            ),
            2: (
                "Assisteert bij de bediening van computerrandapparatuur. Vult kettingformulieren bij. "
                "Sorteert output en maakt deze verzend gereed."
            ),
            1: None,
        },
    ),
    _ladder(
        17,
        "Programmering en systeemanalyse",
        {
            6: (
                "Geeft leiding aan de uitvoering van systeemanalyse in het kader van "
                "automatiseringsprojecten en treedt incidenteel op als projectleider of als "
                "informatieanalist. Coördineert het up-to-date houden van het totale softwarebestand. "
                "Geeft richtlijnen voor technisch systeemontwerp en systeemspecificaties, opdat "
                "deelsystemen op elkaar aansluiten en een optimale procesgang wordt bereikt. Ziet "
                "toe op het testen en invoeren van nieuwe onderdelen van het systeem. Zorgt voor "
                "toegankelijkheid en beveiliging van de informatie. Ontwikkelt procedures voor het "
                "gebruik van het systeem."
            ),
            5: (
                "Het in samenwerking met een informatieanalist vaststellen van de informatiebehoefte, "
                "het maken van een systeemontwerp en specificaties, de verwerking van procedures, "
                "controles, e.d. Het leidinggeven bij het programmeren van systeemontwerpen en zorgen "
                "voor coördinatie bij updating van programmatuur. Het begeleiden van systeemtests, "
                "het opsporen van de oorzaken van storingen of fouten en het coördineren van "
                "dergelijke assistentie bij de invoering."
            ),
            4: (
                "Het opzetten van computerprogramma's in één of andere programmeertaal aan de hand "
                "van stroomschema's of specificaties. Het testen van programma's en het uitzoeken "
                "van fouten en storingen, het aanbrengen van verbeteringen. Incidenteel het aanbrengen "
                "van modificaties in machinetaal. Het verzamelen en vastleggen van programmadocumentatie "
                "en het assisteren bij de invoering van nieuwe onderdelen van het systeem."
            ),
            3: None,
            2: None,
            1: None,
        },
    ),
    _ladder(
        18,
        "Personeelszaken",
        {
            6: (
                "Verzorgt de werving en selectie, introductie en opleiding van het kader- en/of "
                "cao-personeel. Adviseert personeelsleden bij persoonlijke problemen of verwijst hen "
                "door naar interne of externe instanties. Ontwikkelt in overleg richtlijnen, "
                "bijvoorbeeld voor de personeelsvervanging bij ziekte, verlof, vakantie en "
                "dergelijke of met betrekking tot veiligheid op de bouwplaats."
            ),
            5: (
                "Verzorgt de opleiding van het kader- en het cao-personeel in overleg met de "
                "leiding. Verzamelt informatie over externe opleidingen, onderhoudt contacten met "
                "opleidingsinstituten, gaat subsidiemogelijkheden na, bewaakt een opleidingsbudget "
                "en adviseert belangstellenden inzake studiemogelijkheden."
            ),
            4: (
                "Voert een personeelssecretariaat met dossierstelsel en correspondentiearchief. "
                "Verzamelt en bewerkt allerlei personeelsgegevens ter voorbereiding van "
                "personeelsbeleid, sociaal jaarverslag e.d. Geeft personeelsgegevens door aan "
                "interne en externe instanties, verzorgt de externe correspondentie en ziet toe op "
                "de werkzaamheden van enkele assistenten."
            ),
            3: (
                "Assisteert op een personeelsafdeling met het bijhouden van dossiers en archieven. "
                "Behandelt daarbij vertrouwelijke informatie. Typt brieven van concept. Staat "
                "bezoekers te woord en verwijst hen door."
            ),
            2: None,
            1: None,
        },
        pm=["Salaris- en loonadministratie"],
    ),
    _ladder(
        19,
        "Secretariaat",
        {
            6: None,
            5: (
                "Verricht de secretariaatswerkzaamheden voor de directie. Behandelt vertrouwelijke "
                "correspondentie. Behandelt in voorkomende gevallen een deel van de "
                "salarisadministratie, maakt afspraken, selecteert informatie en bezoekers, "
                "verwijst eventueel door. Notuleert directiebesprekingen en loopt de daarbij "
                "vastgelegde afspraken na. Houdt het directiearchief bij. Houdt eventueel toezicht "
                "op een of meer assistenten."
            ),
            4: (
                "Verricht secretariaatswerkzaamheden, bijvoorbeeld voor de directie of voor een "
                "afdeling(schef). Houdt agenda's bij, maakt afspraken op aanwijzingen en loopt deze "
                "na. Verslaat vergaderingen, neemt correspondentie op in steno en werkt deze uit, "
                "ook eventueel in moderne talen. Houdt een archief bij en eventueel het "
                "kantoorbenodigdhedenmagazijn. Heeft wellicht enige nevenactiviteiten in de afdeling."
            ),
            3: (
                "Verricht algemeen en vertrouwelijk typewerk (bijvoorbeeld personeelsinformatie), "
                "ook in de moderne talen. Beheert een klein archief of kantoorbenodigdhedenmagazijn. "
                "Houdt agenda's bij, maakt afsprakenlijstjes tijdens vergaderingen, geeft afspraken "
                "door. Houdt een lijst voor bereikbaarheid van personen bij. Verricht eventueel enkele "
                "administratieve taken met controle voor vergelijking van gegevens uit verschillende "
                "bronnen. Verricht receptie- en telefooncentralewerkzaamheden met veel buitenlandse "
                "contacten."
            ),
            2: (
                "Verricht allerhande typewerk in het Nederlands; bedient telex; behandelt inkomende "
                "en uitgaande post; bedient een telefooncentrale; ontvangt bezoekers en verwijst "
                "deze door. Houdt eventueel een correspondentiearchief bij. Voert diverse gegevens "
                "op aanwijzingen in computer in via terminal. Maakt fotokopieën."
            ),
            1: (
                "Typt facturen aan de hand van lijsten, verricht invoer van getallenreeksen in "
                "computer via terminal, distribueert correspondentie."
            ),
        },
    ),
    _ladder(
        20,
        "Tekstverwerking",
        {
            6: None,
            5: None,
            4: (
                "Geeft leiding aan tekstverwerking door circa 10 medewerkers. Verzorgt de "
                "werkregeling en instructie. Controleert mede het werk voor aflevering. Bestelt "
                "apparatuur en materiaal en zorgt voor onderhoud. Zorgt voor opleiding van de "
                "medewerkers. Weet moderne tekstverwerkende apparatuur te programmeren."
            ),
            3: (
                "Levert vertrouwelijk typewerk en/of typewerk in de moderne talen. Houdt toezicht op "
                "aankomende typisten. Controleert typewerk. Kent het gebruik van moderne "
                "tekstverwerkingsapparatuur en instrueert anderen daarin."
            ),
            2: (
                "Typt Nederlands en één der moderne talen van concept; typt tabellen, formulieren, "
                "correspondentie, e.d. Kán werken met dictafoon en moderne tekstverwerkende "
                "apparatuur."
            ),
            1: (
                "Typt Nederlandse correspondentie van concept en brengt op aanwijzingen correcties aan."
            ),
        },
    ),
    _ladder(
        21,
        "Reproductie",
        {
            6: None,
            5: (
                "Geeft leiding aan het reproduceren van tekeningen, offsetdrukken, fotokopiëren en "
                "allerlei afwerking in een grote reproductieafdeling met 5 tot 10 medewerkers. "
                "Verzorgt de werkvoorbereiding en voortgangscontrole, lost technische problemen op "
                "bij meerkleurendruk, storingen in apparatuur, e.d. Onderhoudt contacten met "
                "leveranciers en beheert de diverse grondstoffen en hulpmaterialen."
            ),
            4: (
                "Geeft leiding aan Reproductie, Postkamer, Kantoorbenodigdhedenmagazijn met totaal "
                "circa 5 medewerkers. Zorgt voor tijdige aflevering van materialen en onderhoud van "
                "de apparatuur of verricht zelf meerkleurenoffsetdrukwerk. Vervaardigt zelf de "
                "platen, kiest kleuren en materialen, adviseert ten aanzien van combinaties, verhelpt "
                "eenvoudige storingen in de apparatuur."
            ),
            3: (
                "Heeft toezicht op en werkt mee aan lichtdruk, fotokopieer- en stencilwerkzaamheden. "
                "Beheert de apparatuur. Verhelpt zelf kleine storingen in de apparatuur. Neemt "
                "eventueel contact op met de leverancier. Zorgt voor voldoende materiaal in voorraad. "
                "Ziet toe op juiste distributie van fotokopieën en de archivering van originelen."
            ),
            2: (
                "Bedient offsetpers voor intern drukwerk of fotokopieerapparatuur; verricht "
                "afwerkwerkzaamheden, alsmede op aanwijzing onderhoud en kleine reparaties aan de "
                "apparatuur. Archiveert originelen, geeft kantoorbenodigdheden uit, signaleert stand "
                "van voorraden aan zijn chef."
            ),
            1: (
                "Maakt lichtdrukken, fotokopieën, stencils en dergelijke op diverse apparatuur. Vult "
                "papier en chemicaliën bij op aanwijzingen. Werkt lichtdrukwerk af door snijden, "
                "nieten, e.d."
            ),
        },
    ),
    _ladder(
        22,
        "Receptie, telefoon, telex",
        {
            6: None,
            5: None,
            4: None,
            3: (
                "Bedient telefooncentrale, telex, teletraceapparatuur en dergelijke, eventueel in de "
                "moderne talen aan de hand van uitgewerkt concept. Ontvangt bezoekers en verwijst "
                "hen door. Verzorgt reservering van vergaderzalen en geeft boodschappen door of "
                "verricht andere neventaken, zoals het beheer van een kleine kas; beheert de "
                "kantoorbenodigdheden, e.d."
            ),
            2: (
                "Bedient een telefooncentrale en ontvangt bezoekers en verwijst hen door. Weet zich "
                "uit te drukken in één of enkele moderne talen."
            ),
            1: None,
        },
    ),
    _ladder(
        23,
        "Interne dienst",
        {
            6: (
                "Geeft leiding aan de Interne Dienst met maximaal 50 medewerkers, verdeeld over "
                "bijvoorbeeld Gebouweninrichting en Onderhoud, Reproductie, Postkamer, Magazijn, "
                "Receptie, Telefoon, Tekstverwerking en Kantine. Treedt op als coördinator, belast "
                "met de uitvoering bij interne verhuizingen en verbouwingen. Koopt na intern overleg "
                "meubilair en kantoormachines. Onderhoudt het zakelijke contact met leveranciers en "
                "schoonmaakdienst. Stemt de diverse werkafspraken en procedures van de afdelingen "
                "van de Interne Dienst op elkaar af en legt een en ander vast in interne regelingen."
            ),
            5: (
                "Geeft leiding aan de Interne Dienst met maximaal 30 medewerkers, verdeeld over "
                "bijvoorbeeld Gebouweninrichting en Onderhoud, Reproductie, Postkamer, Magazijn, "
                "Receptie, Telefoon, Kantine. Organiseert interne verhuizingen; koopt na intern "
                "overleg meubilair, kantoormachines, kantoorbenodigdheden, e.d. Maakt "
                "afleveringsafspraken met leveranciers, onderhoudt het werkcontact met bijvoorbeeld "
                "een schoonmaakbedrijf, een en ander in overleg met Inkoop of Directie, of geeft "
                "leiding aan een afdeling in de Interne Dienst met circa 10 geschoolde vaklieden, "
                "zoals huisdrukkerij, elektromechanisch onderhoud en garage."
            ),
            4: (
                "Verricht gespecialiseerd technisch onderhoud aan installaties in gebouwen, zoals "
                "liften, airconditioning en roltrappen. Wordt daarbij geassisteerd door één of enkele "
                "assistenten, of heeft leiding van een aantal afdelingen van de Interne Dienst, met "
                "circa 10 medewerkers in Kantine, Receptie, Telefooncentrale, Reproductie en "
                "dergelijke of heeft leiding van een dergelijke afdeling als onderdeel van een "
                "grotere interne dienst."
            ),
            3: (
                "Verricht vakkundig onderhoud, zoals timmerwerk, metselwerk, stukadoorswerk, bank-, "
                "las en constructiewerk. Onderhoudt machines en elektrische installaties volgens "
                "voorschriften van de leverancier. Vervangt onderdelen en voert kleine reparaties uit "
                "aan machines en installaties of beschadigd meubilair. Geeft leiding aan "
                "afdelingscombinaties met bijvoorbeeld Postkamer, Kantine en Magazijn, met in totaal "
                "maximaal 10 medewerkers."
            ),
            2: (
                "Verricht onderhoudswerk, zoals het olie verversen, het opheffen van kleine "
                "mechanische storingen, het vervangen van onderdelen in apparaten, het schilderwerk; "
                "verplaatst binnenwanden, richt vergaderzalen in, regelt interne verhuizingen, e.d. "
                "Heeft leiding in een kantine, koopt grondstoffen in, rekent verkochte maaltijden af. "
                "Heeft leiding van een postkamer. Transporteert goederen en documenten met een "
                "personen- of bestelauto. Verzorgt de uitgifte van een "
                "kantoorbenodigdhedenmagazijn."
            ),
            1: (
                "Verricht eenvoudig onderhoudswerk, zoals vervangen van lampen, het reinigen van "
                "apparatuur, het schoonhouden van kantine, gangen en trappen. Zet en serveert koffie "
                "en thee in kantoor en kantine. Bereidt eenvoudige gerechten, zoals soep en "
                "kroketten. Brengt inkomende post rond en maakt uitgaande post verzend gereed."
            ),
        },
    ),
    _ladder(
        24,
        "Kwaliteit, arbeidsomstandigheden en milieu",
        {
            6: None,
            5: (
                "Opzetten, beheren en onderhouden van zorgsystemen op het terrein van kwaliteit en/of "
                "arbeidsomstandigheden en/of milieu. Coördineert activiteiten op deze terreinen. "
                "Draagt zorg voor opstellen van het KAM en/of Arbo en/of milieu jaarplan en "
                "jaarverslag. Bewaakt de uitvoering van het jaarplan. Registreert, analyseert "
                "(bijna) ongevallen en risico's en neemt naar aanleiding daarvan actie. Voert overleg "
                "met deskundigen en begeleidt audits. Adviseert gevraagd en ongevraagd de directie "
                "en andere leidinggevenden. Geeft in voorkomende gevallen leiding aan medewerkers."
            ),
            4: (
                "Beheren en onderhouden van zorgsystemen op het terrein van kwaliteit en/of "
                "arbeidsomstandigheden en/of milieu. Coördineert activiteiten op deze terreinen "
                "binnen de vestiging. Draagt mede zorg voor opstellen van het KAM en/of Arbo en/of "
                "milieu jaarplan en jaarverslag. Bewaakt de uitvoering van het jaarplan op "
                "vestigingsniveau. Registreert, analyseert (bijna)ongevallen en risico's. Geeft "
                "resultaten door aan de arbocoördinator en neemt naar aanleiding daarvan actie. "
                "Voert overleg met deskundigen en begeleidt audits. Adviseert gevraagd en ongevraagd "
                "de directie en andere leidinggevenden."
            ),
            3: None,
            2: None,
            1: None,
        },
    ),
    _ladder(
        25,
        "Maatvoering",
        {
            6: None,
            5: None,
            4: (
                "Realiseert zelfstandig de maatvoering bij bouwprojecten. Zet op basis van (digitale) "
                "werktekeningen en met behulp van de Total Station o.a. het palenplan ten behoeve van "
                "de fundering en een assenstelsel ten behoeve van diverse verdiepingslagen uit. "
                "Signaleert afwijkingen door middel van controles en meldt deze bij de uitvoerder."
            ),
            3: None,
            2: None,
            1: None,
        },
    ),
]

_LADDER_INDEX: dict[int, Functieladder] = {l.nummer: l for l in FUNCTIELADDERS}


def lijst_functieladders() -> list[dict]:
    """Samenvatting voor API/UI: nummer, naam, beschikbare niveaus, lege niveaus, PM-verwijzingen."""
    return [
        {
            "nummer": l.nummer,
            "naam": l.naam,
            "intredekeuring_verplicht": l.intredekeuring_verplicht,
            "beschikbare_niveaus": l.beschikbare_niveaus,
            "lege_niveaus": l.lege_niveaus,
            "matrix_niveaus": FUNCTIENIVEAU_MATRIX.get(l.nummer, []),
            "pm_verwijzingen": l.pm_verwijzingen,
        }
        for l in FUNCTIELADDERS
    ]


def zoek_ladder(nummer: int) -> Optional[Functieladder]:
    return _LADDER_INDEX.get(nummer)


def zoek_ladder_op_naam(naam: str) -> Optional[Functieladder]:
    naam_lc = naam.strip().lower()
    for l in FUNCTIELADDERS:
        if l.naam.lower() == naam_lc:
            return l
    return None


def niveau_karakteristiek(ladder_nummer: int, niveau: int) -> Optional[NiveauKarakteristiek]:
    ladder = zoek_ladder(ladder_nummer)
    if not ladder:
        return None
    for n in ladder.niveaus:
        if n.niveau == niveau:
            return n
    return None


def ladders_met_lege_niveaus() -> list[dict]:
    """Ladders waar de CAO minstens één niveau zonder karakteristiek laat."""
    return [
        {"nummer": l.nummer, "naam": l.naam, "lege_niveaus": l.lege_niveaus}
        for l in FUNCTIELADDERS
        if l.lege_niveaus
    ]


def ladders_met_pm_verwijzingen() -> list[dict]:
    return [
        {"nummer": l.nummer, "naam": l.naam, "pm_verwijzingen": l.pm_verwijzingen}
        for l in FUNCTIELADDERS
        if l.pm_verwijzingen
    ]


def export_json() -> str:
    import json

    return json.dumps(
        [l.model_dump() for l in FUNCTIELADDERS],
        ensure_ascii=False,
        indent=2,
    )


if __name__ == "__main__":
    print(f"Functieladders bijlage 1.3: {len(FUNCTIELADDERS)} ladders")
    ingevuld = sum(len(l.beschikbare_niveaus) for l in FUNCTIELADDERS)
    leeg = sum(len(l.lege_niveaus) for l in FUNCTIELADDERS)
    print(f"Karakteristieken: {ingevuld} ingevuld, {leeg} leeg in CAO")
    print(f"Ladders met PM-verwijzing: {len(ladders_met_pm_verwijzingen())}")
    for item in ladders_met_lege_niveaus():
        print(f"  Ladder {item['nummer']:2d} {item['naam']}: leeg niveau {item['lege_niveaus']}")
