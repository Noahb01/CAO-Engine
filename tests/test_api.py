"""API-tests met FastAPI TestClient."""

from datetime import date

from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def _inschaling_payload(**overrides):
    payload = {
        "functie_omschrijving": "Werkvoorbereider",
        "peildatum": "2026-03-01",
        "kandidaat_naam": "Jan Jansen",
        "opdrachtgever": "Test BV",
        "marge_pct": 15.0,
    }
    payload.update(overrides)
    return payload


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["kostprijsmodel"] == "Model A (omrekenfactor)"
    assert r.json()["uren_per_maand"] == 173.33


def test_werkgeverslasten_defaults():
    r = client.get("/api/v1/werkgeverslasten-defaults")
    assert r.status_code == 200
    data = r.json()
    assert "werkgeverslasten" in data
    assert "omrekenfactor" in data
    assert "factor_opbouw" in data
    assert data["omrekenfactor"] > 1.9


def test_bereken_tarief():
    r = client.post(
        "/api/v1/bereken-tarief",
        json={
            "functieniveau": 4,
            "startdatum_contract": "2026-03-01",
            "marge_pct": 15.0,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["facturatie_per_uur"] > data["kostprijs_per_uur"]
    assert "factor_opbouw" in data


def test_bereken_tarief_override_15():
    r = client.post(
        "/api/v1/bereken-tarief",
        json={
            "functieniveau": 4,
            "startdatum_contract": "2026-03-01",
            "marge_pct": 15.0,
            "omrekenfactor_override": 1.5,
        },
    )
    assert r.status_code == 200
    assert r.json()["omrekenfactor"] == 1.5


def test_inschaling_en_tarief_functietitel_mapping():
    r = client.post(
        "/api/v1/inschaling-en-tarief",
        json=_inschaling_payload(salarisverwachting_per_uur=24.50),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["gebruikt_niveau"] == 3
    assert data["voorgesteld_niveau"] == 3
    assert data["niveau_bijgesteld"] is False
    assert data["functieladder"]["nummer"] == 3
    assert "berekening" in data
    assert data["berekening"]["facturatie_per_uur"] > 0
    assert data["functie_mapping"]["functie_naam"] == "Werkvoorbereider"


def test_inschaling_en_tarief_niveau_bijstelling():
    r = client.post(
        "/api/v1/inschaling-en-tarief",
        json=_inschaling_payload(bevestigd_niveau=4),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["gebruikt_niveau"] == 4
    assert data["voorgesteld_niveau"] == 3
    assert data["niveau_bijgesteld"] is True
    assert "3 naar 4" in data["niveau_bijstelling"]


def test_inschaling_en_tarief_salaris_per_maand():
    r = client.post(
        "/api/v1/inschaling-en-tarief",
        json=_inschaling_payload(
            salarisverwachting_per_maand=4246.59,
            bevestigd_niveau=3,
        ),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["salarisverwachting_eenheid"] == "maand"
    assert data["salarisverwachting_per_uur"] == 24.50
    assert data["berekening"]["bruto_uurloon"] == 24.50


def test_functieladders_lijst():
    r = client.get("/api/v1/functieladders")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 25
    assert data[0]["nummer"] == 1


def test_functieladder_niveaus():
    r = client.get("/api/v1/functieladders/1/niveaus")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 6
    n4 = next(n for n in data if n["niveau"] == 4)
    assert n4["status"] == "ingevuld"


def test_inschaling_en_tarief_met_bevestigd_niveau():
    r = client.post(
        "/api/v1/inschaling-en-tarief",
        json=_inschaling_payload(
            salarisverwachting_per_uur=24.0,
            bevestigd_niveau=3,
        ),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["functieladder"]["nummer"] == 3
    assert data["berekening"]["functieladder_naam"] == "Werkvoorbereiding"


def test_optie_b_hoofdflow_payload_roundtrip():
    """Hoofdflow: alleen functietitel → afgeleide ladder/niveau in resultaat."""
    payload = _inschaling_payload(
        salarisverwachting_per_uur=24.0,
        jaren_op_niveau=2,
    )
    r = client.post("/api/v1/inschaling-en-tarief", json=payload)
    assert r.status_code == 200
    data = r.json()

    assert data["gebruikt_niveau"] == 3
    assert data["functieladder"]["nummer"] == 3
    assert data["functieladder"]["gekozen_niveau"] == 3
    assert data["functieladder"]["karakteristiek_status"] == "ingevuld"
    assert data["berekening"]["functieladder_nummer"] == 3
    assert data["berekening"]["functieladder_naam"] == "Werkvoorbereiding"
    assert data["berekening"]["ladder_karakteristiek_status"] == "ingevuld"
    assert data["berekening"]["facturatie_per_uur"] > 0


def test_inschaling_keuzes_api():
    r = client.get("/api/v1/inschaling-keuzes")
    assert r.status_code == 200
    data = r.json()
    assert len(data["functietitels"]) == 31
    assert data["totaal"] == 31
    assert data["functietitels"][0]["label"] == data["functietitels"][0]["functie_naam"]


def test_inschaling_zonder_kandidaat_naam():
    payload = _inschaling_payload()
    del payload["kandidaat_naam"]
    r = client.post("/api/v1/inschaling-en-tarief", json=payload)
    assert r.status_code == 200
    assert r.json()["berekening"]["facturatie_per_uur"] > 0


def test_demo_auth_blokkeert_zonder_credentials(monkeypatch):
    monkeypatch.setenv("DEMO_WACHTWOORD", "geheim-demo")
    from api import app as auth_app

    auth_client = TestClient(auth_app)
    assert auth_client.get("/api/v1/health").status_code == 401
    assert auth_client.get("/").status_code == 401
    assert auth_client.get("/static/styles.css").status_code == 401

    ok = auth_client.get("/api/v1/health", auth=("demo", "geheim-demo"))
    assert ok.status_code == 200


def test_demo_auth_verkeerd_wachtwoord(monkeypatch):
    monkeypatch.setenv("DEMO_WACHTWOORD", "geheim-demo")
    from api import app as auth_app

    auth_client = TestClient(auth_app)
    assert auth_client.get("/api/v1/health", auth=("demo", "fout")).status_code == 401
