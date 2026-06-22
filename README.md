# Infrastructure Compliance Engine

**CAO Bouw & Infra 2025-2027 | Onfeilbare Rekenmachine voor Detachering & Recruitment**

Een Deep Vertical AI startup oplossing die chaos in de infrastructuur-sector elimineert door CAO-tabellen te vertalen naar foutloze contracten en tariefberekeningen.

## 🎯 Kernwaarde Propositie

**Probleem**: Detacheringsbureaus en recruiters worstelen met complexe CAO-berekeningen, resulterend in fouten, compliance issues en onduidelijke contracten.

**Oplossing**: Een onfeilbare rekenmachine die:
- ✅ Automatisch de juiste CAO-tabel selecteert op basis van datum
- ✅ CAO-compliance realtime valideert
- ✅ Kristalheldere contractoverzichten genereert
- ✅ Alle vaagheid wegneemt met volledige transparantie
- ✅ Klaar voor API-integratie in bestaande systemen

## 🏗️ Architectuur

### Componenten

```
contract-generator/
├── cao_data.py                  # CAO-tabellen, validatie, maandsalaris-helpers
├── functieladders_bijlage_1_3.py # 25 functieladders + karakteristieken (bijlage 1.3)
├── functie_ladder_mapping.py    # UTA-functietitel → ladder + voorgesteld niveau
├── inschaling_keuzes.py         # Functietitel-keuzelijst voor UI/API
├── inschaling_engine_v2.py      # Kostprijs Model A (omrekenfactor, marge %)
├── inschalingsmodel.py          # Oordeel-helpers + salarisverwachting-check
├── functies.py                  # UTA-functielijst
├── contract_generator.py        # Pipeline + contractoverzichten
├── api.py                       # FastAPI REST API + web UI
├── demo_auth.py                 # HTTP Basic Auth voor demo-deploy
├── static/                      # Webinterface (index.html, app.js)
├── render.yaml                  # Render Blueprint (optioneel)
├── Procfile                     # Railway / compatibele hosts
├── runtime.txt                  # Python-versie voor hosting
├── demo.py                      # Demo suite
├── tests/                       # pytest
└── requirements.txt
```

### Data Flow (hoofdflow inschaling)

```
Functietitel (UI/API)
    → functie_ladder_mapping          (ladder + voorgesteld niveau)
    → optioneel bevestigd_niveau      (bijstelling binnen ladder, oordeel)
    → inschaling_engine_v2.bereken()  (bruto × omrekenfactor → kostprijs → facturatie)
    → contract_generator              (HARD/OORDEEL + overzichten)
```

Prioriteit functieniveau: **functietitel-mapping** → optioneel **bevestigd_niveau** (bijstelling).

`jaren_op_niveau` beïnvloedt alleen de doorgroeigarantie (104/110/116%), niet het niveau.
Ervaring en leeftijd worden niet gebruikt in de hoofd-pipeline. Jeugdschalen (tabel 4.10) zijn niet geïmplementeerd.

## 🚀 Snelstart

### Installatie

```bash
# Clone/download de bestanden
cd infrastructure-compliance-engine

# Installeer dependencies
pip install -r requirements.txt
```

### Demo Runnen

```bash
# Run de volledige demo suite
python demo.py
```

Dit demonstreert alle 9 scenario's:
1. Basis tariefberekening
2. Hoger loon dan CAO-minimum
3. Compliance schending detectie
4. Automatische tabelwisseling tussen jaren
5. Impact van verschillende marges
6. Kandidaat overzicht generatie
7. Bureau overzicht (intern)
8. Marge vergelijkingstabel
9. Edge cases

### API & Web UI Starten

```bash
# Start FastAPI server (inclusief webinterface op /)
python api.py

# Of met uvicorn:
uvicorn api:app --reload
```

- Web UI: `http://localhost:8000/`
- API docs (Swagger): `http://localhost:8000/docs`

### Demo online zetten (Render / Railway)

De tool is voorbereid als **demo voor externe testers**, niet als productieomgeving.

**Lokaal draaien**

```bash
pip install -r requirements.txt

# Optioneel: toegang beveiligen zoals op Render
export DEMO_WACHTWOORD="kies-een-sterk-wachtwoord"

# Start (luistert op PORT, standaard 8000)
python api.py
# of:
uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
```

Zonder `DEMO_WACHTWOORD` is de app lokaal **open** (handig voor ontwikkeling). Op Render/Railway **altijd** `DEMO_WACHTWOORD` zetten.

**Environment variables**

| Variabele | Verplicht | Beschrijving |
|-----------|-----------|--------------|
| `DEMO_WACHTWOORD` | Ja (deploy) | Gedeeld wachtwoord voor HTTP Basic Auth |
| `DEMO_USERNAME` | Nee | Gebruikersnaam (standaard: `demo`) |
| `PORT` | Automatisch | Door het platform gezet; niet handmatig nodig |

Inloggen in de browser: gebruikersnaam `demo`, wachtwoord = waarde van `DEMO_WACHTWOORD`.

**Deploy op Render**

1. Repository koppelen bij [render.com](https://render.com)
2. Nieuwe **Web Service** → runtime Python
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn api:app --host 0.0.0.0 --port $PORT`
5. Environment: `DEMO_WACHTWOORD` instellen (geheim)
6. Optioneel: `render.yaml` in de repo gebruiken voor Blueprint-deploy

**Deploy op Railway**

1. Repository koppelen; Railway detecteert `Procfile` / `requirements.txt`
2. `DEMO_WACHTWOORD` als variable toevoegen
3. Deploy start automatisch via `Procfile`

**Privacy (demo)**

- Geen database of bestandsopslag van invoer; elke berekening is een losse HTTP-request.
- De server logt geen request-bodies met formuliergegevens.
- Kandidaatnaam is optioneel; gebruik geen echte persoonsgegevens in de demo.

**Disclaimer in de UI**

Bovenaan staat een vaste melding dat dit een indicatieve demo is. HARD (CAO) vs OORDEEL (voorstel) blijft in de resultaten gescheiden.

### Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## 📖 Gebruik

### Basis Voorbeeld (Model A)

```python
from datetime import date
from inschaling_engine_v2 import bereken_tarief_direct

berekening = bereken_tarief_direct(
    functieniveau=4,
    peildatum=date(2026, 3, 1),
    basis_uurloon=24.50,
    marge_pct=15.0,  # 15% op kostprijs
)

print(f"Bruto:      €{berekening.bruto_uurloon:.2f}/uur")
print(f"Kostprijs:  €{berekening.kostprijs_per_uur:.2f}/uur (×{berekening.omrekenfactor})")
print(f"Facturatie: €{berekening.facturatie_per_uur:.2f}/uur")
```

### Volledige pipeline (inschaling + tarief)

```python
from datetime import date
from contract_generator import genereer_volledig_voorstel
from inschalingsmodel import KandidaatInput

result = genereer_volledig_voorstel(
    kandidaat=KandidaatInput(
        functie_omschrijving="Werkvoorbereider",
        salarisverwachting_per_uur=24.50,
        peildatum=date(2026, 3, 1),
    ),
    kandidaat_naam="Jan Jansen",
    opdrachtgever="Rijkswaterstaat",
    marge_pct=15.0,
    bevestigd_niveau=4,  # optioneel: bijstelling binnen ladder
)
print(result["berekening"].facturatie_per_uur)
print(result["voorgesteld_niveau"], result["gebruikt_niveau"])
```

### Contract Genereren

```python
from contract_generator import genereer_kandidaat_overzicht

# Genereer helder overzicht voor kandidaat
overzicht = genereer_kandidaat_overzicht(
    berekening=berekening,
    kandidaat_naam="Jan Jansen",
    opdrachtgever="Rijkswaterstaat",
    project_naam="A1 Apeldoorn-Zuid"
)

print(overzicht)  # Volledige breakdown van salaris
```

### API Gebruik

```bash
# Bereken tarief via API (Model A)
curl -X POST "http://localhost:8000/api/v1/bereken-tarief" \
  -H "Content-Type: application/json" \
  -d '{
    "functieniveau": 4,
    "startdatum_contract": "2026-03-01",
    "basis_uurloon": 24.50,
    "marge_pct": 15,
    "omrekenfactor_override": null,
    "werkgeverslasten": {
      "vakantietoeslag_pct": 8,
      "pensioen_bpfbouw_pct": 15.9,
      "sociale_lasten_pct": 18,
      "sociaal_fonds_scholing_pct": 2.5,
      "verzuim_risico_pct": 4
    }
  }'

# Default premies en omrekenfactor
curl "http://localhost:8000/api/v1/werkgeverslasten-defaults"

# Inschaling + tarief (volledige pipeline)
curl -X POST "http://localhost:8000/api/v1/inschaling-en-tarief" \
  -H "Content-Type: application/json" \
  -d '{
    "functie_omschrijving": "Werkvoorbereider",
    "peildatum": "2026-03-01",
    "kandidaat_naam": "Jan Jansen",
    "opdrachtgever": "Rijkswaterstaat",
    "marge_pct": 15,
    "bevestigd_niveau": 4,
    "jaren_op_niveau": 2
  }'
```

## 🔧 API Endpoints

### Tariefberekening
- `POST /api/v1/bereken-tarief` — Kostprijs + facturatie (Model A)
- `POST /api/v1/inschaling-en-tarief` — Volledige pipeline: functietitel → inschaling → tarief
- `GET /api/v1/inschaling-keuzes` — UTA-functietitels voor typeahead
- `GET /api/v1/functieladders` — Alle 25 functieladders (bijlage 1.3)
- `GET /api/v1/functieladders/{nummer}/niveaus` — Niveaus + karakteristieken per ladder
- `GET /api/v1/werkgeverslasten-defaults` — Default premies + berekende omrekenfactor
- `GET /api/v1/cao-info` — CAO min/max voor functieniveau en datum
- `GET /api/v1/cao-tabellen` — Alle beschikbare CAO-tabellen
- `GET /api/v1/functies` — UTA-functielijst (optioneel gegroepeerd)

### Contract Generatie
- `POST /api/v1/genereer-kandidaat-overzicht` — Transparant overzicht voor kandidaat
- `POST /api/v1/genereer-bureau-overzicht` — Intern overzicht met kostprijsopbouw
- `GET /api/v1/marge-vergelijking` — Vergelijk verschillende marges

### Request-velden (`POST /api/v1/inschaling-en-tarief`)

| Veld | Beschrijving |
|------|--------------|
| `functie_omschrijving` | **Verplicht.** UTA-functietitel (bijv. `Werkvoorbereider`) |
| `bevestigd_niveau` | Optioneel bijgesteld niveau binnen de ladder; weglaten = mapping-voorstel |
| `salarisverwachting_per_uur` | Bruto uurloon dat de kandidaat noemt (optioneel) |
| `salarisverwachting_per_maand` | Alternatief: bruto maandsalaris (173,33 uur/maand); niet combineerbaar met per uur |
| `jaren_op_niveau` | Diensttijd op niveau voor doorgroeigarantie (art. 4.9.2) — beïnvloedt **niet** het niveau |
| `marge_pct` | Marge % bovenop kostprijs (default 15) |
| `omrekenfactor_override` | Vaste factor i.p.v. opbouw (bijv. 1.5); `null` = opbouw uit premies |
| `nieuw_in_bouw_infra` | Starttabel voor nieuwe instromers (art. 4.11) |
| `starttabel_tweede_halfjaar` | Bij starttabel: 2e halfjaar i.p.v. 1e |
| `bevestigd_uurloon` | Optioneel: vast uurloon i.p.v. salarisverwachting |
| `werkgeverslasten` | Optioneel: premies incl. duurzame inzetbaarheid 2,30% |

Response bevat o.a. `voorgesteld_niveau`, `gebruikt_niveau`, `niveau_bijgesteld`, `functie_mapping`, `functieladder`.

### Utilities
- `GET /api/v1/bereken-maandsalaris` - Bereken maandsalaris uit uurloon
- `GET /api/v1/bereken-vier-weken-salaris` - Bereken 4-weken salaris

## 🧮 Rekenlogica (Model A)

Geen aparte ADV-regel meer. Roostervrije dagen (vakantie, ADV, feestdagen) zitten in de **productiviteitscorrectie** van de omrekenfactor.

### Omrekenfactor

```
premie_factor = 1 + (som_premies + vakantietoeslag + duurzame_inzetbaarheid) / 100
productiviteit_correctie = werkbare_dagen / netto_werkbare_dagen   # 260 / 206
omrekenfactor = premie_factor × productiviteit_correctie          # ~1,91 met defaults
```

Hard CAO in factor: vakantietoeslag 8%, duurzame inzetbaarheid 2,30% (art. 4.14). Overige premies zijn **indicatief**.

### Doorgroeigarantie (art. 4.9.2)

Na diensttijd op een niveau geldt een hoger effectief minimum: 100% → 104% (2 jr) → 110% (4 jr) → 116% (6 jr). Input: `jaren_op_niveau`.

### Starttabel (art. 4.11)

Nieuw in bouw & infra: `nieuw_in_bouw_infra=true`, optioneel `starttabel_tweede_halfjaar`. Max. 1 jaar; daarna reguliere band.

Override: `omrekenfactor_override = 1.5` voor vaste 1,5× (gangbaar bij detacheringsbureaus).

### Kostprijs en facturatie

```
kostprijs_per_uur = bruto_uurloon × omrekenfactor
facturatie_per_uur = kostprijs_per_uur × (1 + marge_pct / 100)
```

Voorbeeld: bruto €24,50, factor ~1,88, marge 15% → kostprijs ~€46,06 → facturatie ~€52,97 (~2,16× bruto).

## 📊 Compliance & Validatie

### Automatische Checks

1. **CAO-band**: Salarisverwachting binnen min/max; onder minimum → corrigeren of blokkeren
2. **Datum validatie**: Contract binnen CAO-periode (1-5-2025 tot 31-12-2027)
3. **Functieniveau**: 1–6
4. **Marge**: 0–200% op kostprijs

### Salaris onder minimum

```python
from inschaling_engine_v2 import Inschaling, VerwachtingActie, bereken

try:
    bereken(Inschaling(
        functieniveau=5,
        peildatum=date(2026, 1, 1),
        salarisverwachting_per_uur=20.00,
        verwachting_actie=VerwachtingActie.BLOKKEER,
    ))
except ValueError as e:
    print(e)  # Berekening geblokkeerd
```

## 🎓 Deep Vertical Extensies

### Fase 1: MVP (Huidig)
✅ CAO-data parsing  
✅ Tariefberekening met compliance  
✅ Contract generatie  
✅ REST API  

### Fase 2: Tender Intelligence (Q2 2025)

**Doel**: Voorspel winnende tarieven voor infrastructuur tenders

```python
# tender_prognose.py (toekomstige module)

from datetime import date
from typing import List, Dict
import numpy as np

class TenderPrognose:
    """
    Tender Intelligence Engine
    Voorspelt winnende tarieven op basis van historische data
    """
    
    def __init__(self, historical_tenders: List[Dict]):
        """
        Args:
            historical_tenders: Lijst met gewonnen tenders
                [{
                    'project': 'A1 Apeldoorn',
                    'opdrachtgever': 'RWS',
                    'functieniveau': 4,
                    'gewonnen_tarief': 38.50,
                    'datum': date(2024, 3, 15),
                    'aantal_kandidaten': 5
                }, ...]
        """
        self.tenders = historical_tenders
        self._build_model()
    
    def _build_model(self):
        """Train ML model op historische tender data"""
        # Feature engineering:
        # - Opdrachtgever (overheid vs privaat)
        # - Regio (tarief verschil tussen regio's)
        # - Functieniveau
        # - Seizoen (zomer/winter variatie)
        # - Markt conditie (tight/loose labor market)
        pass
    
    def voorspel_winning_tarief(
        self,
        functieniveau: int,
        opdrachtgever: str,
        tender_datum: date,
        confidence_interval: float = 0.95
    ) -> Dict:
        """
        Voorspel het tarief waarmee je waarschijnlijk de tender wint
        
        Returns:
            {
                'predicted_tarief': 37.50,
                'min_tarief': 35.20,
                'max_tarief': 39.80,
                'win_probability': 0.75,
                'cao_compliant': True,
                'risk_assessment': 'low'
            }
        """
        pass
    
    def benchmark_tegen_markt(
        self,
        eigen_tarief: float,
        functieniveau: int
    ) -> Dict:
        """
        Vergelijk jouw tarief met markt
        
        Returns:
            {
                'eigen_tarief': 38.50,
                'markt_gemiddelde': 36.20,
                'percentiel': 65,  # Je bent duurder dan 65% van markt
                'advies': 'Overweeg tarief verlagen voor competitiviteit'
            }
        """
        pass
```

**Integratie met MVP**:

```python
from inschaling_engine_v2 import bereken_tarief_direct
from tender_prognose import TenderPrognose

# Bereken minimale CAO-conforme tarief
cao_tarief = bereken_tarief_direct(
    functieniveau=4,
    peildatum=date(2027, 1, 1),
    marge_pct=15.0
)

# Voorspel wat concurrent biedt
prognose = TenderPrognose(historical_data)
tender_voorspelling = prognose.voorspel_winning_tarief(
    functieniveau=4,
    opdrachtgever="Rijkswaterstaat",
    tender_datum=date(2027, 1, 15)
)

# Beslissingslogica
if cao_tarief.facturatie_tarief_per_uur <= tender_voorspelling['max_tarief']:
    print(f"✓ Winkans: {tender_voorspelling['win_probability']:.0%}")
    print(f"✓ Jouw tarief: €{cao_tarief.facturatie_tarief_per_uur:.2f}")
    print(f"✓ Voorspelde winnende range: €{tender_voorspelling['min_tarief']:.2f} - €{tender_voorspelling['max_tarief']:.2f}")
else:
    print("⚠️ Jouw tarief ligt boven voorspelde winnende range")
```

### Fase 3: Skills Ontology & Matching (Q3 2025)

**Doel**: Automatisch functieniveau bepalen op basis van skills

```python
# skills_matcher.py (toekomstige module)

class SkillsMatcher:
    """
    Bepaalt automatisch functieniveau op basis van skills en ervaring
    """
    
    # Skills ontology voor Bouw & Infra
    SKILLS_MATRIX = {
        'niveau_1': {
            'required_skills': ['Hulpwerk', 'Handmatig werk'],
            'experience_years': 0,
            'certifications': []
        },
        'niveau_2': {
            'required_skills': ['Timmeren basis', 'Metselwerk basis'],
            'experience_years': 0.5,
            'certifications': []
        },
        'niveau_3': {
            'required_skills': ['Zelfstandig timmeren', 'Beton storten'],
            'experience_years': 2,
            'certifications': ['VCA']
        },
        'niveau_4': {
            'required_skills': ['Complexe constructies', 'Teamleiding'],
            'experience_years': 5,
            'certifications': ['VCA', 'Vakdiploma']
        },
        # ... etc
    }
    
    def bereken_functieniveau(
        self,
        kandidaat_skills: List[str],
        ervaring_jaren: float,
        certificaten: List[str]
    ) -> int:
        """
        Bepaal automatisch het correcte functieniveau
        
        Returns:
            Functieniveau 1-6
        """
        pass
    
    def genereer_contract_voorstel(
        self,
        kandidaat_profiel: Dict
    ) -> Dict:
        """
        Genereer volledig contract voorstel gebaseerd op profiel
        
        Input:
            {
                'naam': 'Jan Jansen',
                'skills': ['Teamleiding', 'Complexe constructies', 'BIM'],
                'ervaring_jaren': 6,
                'certificaten': ['VCA', 'Vakdiploma'],
                'beschikbaarheid': date(2026, 2, 1)
            }
        
        Returns:
            {
                'functieniveau': 4,
                'basis_uurloon': 22.50,
                'facturatie_tarief': 35.80,
                'motivatie': 'Kandidaat heeft 6 jaar ervaring en voldoet 
                              aan alle eisen voor niveau 4...'
            }
        """
        functieniveau = self.bereken_functieniveau(...)
        
        # Gebruik MVP engine voor tariefberekening
        from inschaling_engine_v2 import bereken_tarief_direct
        berekening = bereken_tarief_direct(
            functieniveau=functieniveau,
            peildatum=kandidaat_profiel['beschikbaarheid']
        )
        
        return {
            'functieniveau': functieniveau,
            'berekening': berekening,
            'motivatie': self._generate_motivation(...)
        }
```

### Fase 4: Multi-CAO Support (Q4 2025)

Uitbreiding naar andere CAO's:
- CAO Metalektro
- CAO Installatie
- CAO Technische Groothandel

```python
# cao_selector.py (toekomstige module)

class MultiCAOEngine:
    """Support voor meerdere CAO's"""
    
    def __init__(self):
        self.cao_engines = {
            'bouw_infra': CurrentEngine,
            'metalektro': MetalektroEngine,
            'installatie': InstallatieEngine
        }
    
    def bereken_beste_cao(
        self,
        functie_beschrijving: str,
        kandidaat_skills: List[str]
    ) -> str:
        """
        Bepaal beste toepasselijke CAO op basis van functie
        """
        pass
```

## 🔒 Data Privacy & Security

**Let op**: Deze engine bevat geen persoonlijke data. CAO-tabellen zijn publieke informatie.

Voor productie gebruik:
- ✅ Implementeer authentication op API endpoints
- ✅ Encrypt gevoelige kandidaat data at rest
- ✅ Logging zonder PII (Personally Identifiable Information)
- ✅ GDPR-compliant data retention policy

## 🧪 Testing

```bash
pytest tests/ -v
```

Dekking: `test_omrekenfactor.py`, `test_inschaling_v2.py`, `test_pipeline.py`, `test_api.py`.

## 📈 Metrics & Monitoring

Voor productie deployment:

```python
# metrics.py (toekomstig)

class EngineMetrics:
    """Track engine performance en accuracy"""
    
    metrics = {
        'berekeningen_per_dag': 0,
        'compliance_violations_detected': 0,
        'average_response_time_ms': 0,
        'accuracy_rate': 1.0  # % correcte voorspellingen
    }
```

## 🤝 Contributing

Deze engine is gebouwd als MVP. Toekomstige verbeteringen:

1. **Unit tests** voor alle berekeningen
2. **Performance optimalisatie** voor bulk berekeningen
3. **Caching** voor veelvoorkomende queries
4. **Async API** endpoints
5. **GraphQL** naast REST
6. **React frontend** voor visuele configuratie

## 📝 Licentie

Proprietary - Infrastructure Compliance Engine  
CAO Data © Bouw & Infra

## 📧 Contact

Voor vragen over implementatie of licentie: [contact info]

---

**Built with ❤️ for the Infrastructure Sector**

*Eliminating chaos, one contract at a time.*
