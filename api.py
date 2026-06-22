"""
FastAPI REST API — Infrastructure Compliance Engine (v2 kostprijsmodel)
"""

from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from cao_data import (
    bereken_maandsalaris,
    bereken_uurloon_uit_maandsalaris,
    bereken_vier_weken_salaris,
    get_cao_info,
    lijst_cao_tabellen,
    UREN_PER_MAAND,
)
from contract_generator import (
    genereer_bureau_overzicht,
    genereer_kandidaat_overzicht,
    genereer_volledig_voorstel,
)
from demo_auth import DemoAuthMiddleware
from functieladders_bijlage_1_3 import lijst_functieladders, zoek_ladder
from inschaling_keuzes import lijst_inschaling_keuzes
from functies import lijst_functies, lijst_functies_gegroepeerd
from inschaling_engine_v2 import (
    TredePositie,
    WerkgeverslastenConfig,
    bereken_omrekenfactor,
    bereken_tarief_direct,
    selecteerbare_niveaus,
    vergelijk_marges,
)
from inschalingsmodel import KandidaatInput

app = FastAPI(
    title="Infrastructure Compliance Engine",
    description="CAO Bouw & Infra 2025-2027 — Inschaling & kostprijs (Model A)",
    version="2.1.0",
)

app.add_middleware(DemoAuthMiddleware)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class WerkgeverslastenRequest(BaseModel):
    vakantietoeslag_pct: float = 8.0
    duurzame_inzetbaarheid_pct: float = 2.30
    pensioen_bpfbouw_pct: float = 15.9
    sociale_lasten_pct: float = 18.0
    sociaal_fonds_scholing_pct: float = 2.5
    verzuim_risico_pct: float = 4.0

    def to_config(self) -> WerkgeverslastenConfig:
        return WerkgeverslastenConfig(**self.model_dump())


class TariefRequest(BaseModel):
    functieniveau: int = Field(..., ge=1, le=6)
    startdatum_contract: date
    basis_uurloon: Optional[float] = None
    positie_in_band: TredePositie = TredePositie.MIDDEN
    marge_pct: float = Field(15.0, ge=0, le=200)
    omrekenfactor_override: Optional[float] = Field(None, ge=1.0, le=3.0)
    werkgeverslasten: Optional[WerkgeverslastenRequest] = None
    jaren_op_niveau: float = Field(0.0, ge=0)
    nieuw_in_bouw_infra: bool = False
    starttabel_tweede_halfjaar: bool = False


class KandidaatOverzichtRequest(TariefRequest):
    kandidaat_naam: Optional[str] = Field(
        None,
        description="Optioneel. Gebruik geen echte namen in de demo.",
    )
    opdrachtgever: str
    project_naam: Optional[str] = None


class BureauOverzichtRequest(KandidaatOverzichtRequest):
    pass


class InschalingRequest(BaseModel):
    functie_omschrijving: str = Field(
        ...,
        description="UTA-functietitel uit de lijst (bijv. 'Werkvoorbereider').",
    )
    salarisverwachting_per_uur: Optional[float] = Field(None, gt=0)
    salarisverwachting_per_maand: Optional[float] = Field(None, gt=0)
    peildatum: date
    kandidaat_naam: Optional[str] = Field(
        None,
        description="Optioneel. Gebruik geen echte namen in de demo.",
    )
    opdrachtgever: str
    project_naam: Optional[str] = None
    marge_pct: float = Field(15.0, ge=0, le=200)
    omrekenfactor_override: Optional[float] = Field(None, ge=1.0, le=3.0)
    werkgeverslasten: Optional[WerkgeverslastenRequest] = None
    bevestigd_niveau: Optional[int] = Field(
        None,
        ge=1,
        le=6,
        description=(
            "Optioneel bijgesteld niveau binnen de ladder. "
            "Weglaten = voorstel uit functietitel-mapping."
        ),
    )
    bevestigd_uurloon: Optional[float] = None
    jaren_op_niveau: float = Field(
        0.0,
        ge=0,
        description="Diensttijd op dit niveau voor doorgroeigarantie (art. 4.9.2).",
    )
    nieuw_in_bouw_infra: bool = False
    starttabel_tweede_halfjaar: bool = False

    @model_validator(mode="after")
    def check_salaris_eenheid(self):
        if (
            self.salarisverwachting_per_uur is not None
            and self.salarisverwachting_per_maand is not None
        ):
            raise ValueError(
                "Geef salarisverwachting per uur OF per maand, niet beide."
            )
        return self


def _resolve_salarisverwachting_uur(req: InschalingRequest) -> Optional[float]:
    if req.salarisverwachting_per_uur is not None:
        return req.salarisverwachting_per_uur
    if req.salarisverwachting_per_maand is not None:
        return bereken_uurloon_uit_maandsalaris(req.salarisverwachting_per_maand)
    return None


def _config_from_request(req) -> Optional[WerkgeverslastenConfig]:
    if getattr(req, "werkgeverslasten", None) is None:
        return None
    return req.werkgeverslasten.to_config()


@app.get("/")
def ui():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/v1/health")
def health():
    return {
        "naam": "Infrastructure Compliance Engine",
        "versie": "2.1.0",
        "kostprijsmodel": "Model A (omrekenfactor)",
        "uren_per_maand": UREN_PER_MAAND,
        "docs": "/docs",
        "ui": "/",
    }


@app.get("/api/v1/werkgeverslasten-defaults")
def api_werkgeverslasten_defaults():
    """Default premies en berekende omrekenfactor (Model A opbouw)."""
    config = WerkgeverslastenConfig()
    factor, opbouw = bereken_omrekenfactor(config)
    return {
        "werkgeverslasten": config.model_dump(),
        "omrekenfactor": factor,
        "factor_opbouw": opbouw,
    }


@app.post("/api/v1/bereken-tarief")
def api_bereken_tarief(req: TariefRequest):
    try:
        return bereken_tarief_direct(
            functieniveau=req.functieniveau,
            peildatum=req.startdatum_contract,
            basis_uurloon=req.basis_uurloon,
            positie_in_band=req.positie_in_band,
            marge_pct=req.marge_pct,
            omrekenfactor_override=req.omrekenfactor_override,
            jaren_op_niveau=req.jaren_op_niveau,
            nieuw_in_bouw_infra=req.nieuw_in_bouw_infra,
            starttabel_tweede_halfjaar=req.starttabel_tweede_halfjaar,
            config=_config_from_request(req),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/api/v1/functies")
def api_functies(gegroepeerd: bool = Query(False)):
    if gegroepeerd:
        return lijst_functies_gegroepeerd()
    return lijst_functies()


@app.get("/api/v1/inschaling-keuzes")
def api_inschaling_keuzes(q: Optional[str] = Query(None, min_length=1)):
    """UTA-functietitels voor inschaling (typeahead)."""
    return lijst_inschaling_keuzes(q)


@app.get("/api/v1/functieladders")
def api_functieladders():
    """Alle 25 functieladders bijlage 1.3 (samenvatting)."""
    return lijst_functieladders()


@app.get("/api/v1/functieladders/{nummer}")
def api_functieladder_detail(nummer: int):
    ladder = zoek_ladder(nummer)
    if ladder is None:
        raise HTTPException(status_code=404, detail=f"Functieladder {nummer} niet gevonden.")
    return ladder.model_dump()


@app.get("/api/v1/functieladders/{nummer}/niveaus")
def api_functieladder_niveaus(nummer: int):
    """Selecteerbare niveaus met karakteristieken voor een ladder."""
    try:
        return selecteerbare_niveaus(nummer)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/api/v1/cao-info")
def api_cao_info(
    functieniveau: int = Query(..., ge=1, le=6),
    datum: date = Query(...),
):
    try:
        return get_cao_info(functieniveau, datum)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/api/v1/cao-tabellen")
def api_cao_tabellen():
    return lijst_cao_tabellen()


@app.post("/api/v1/genereer-kandidaat-overzicht")
def api_genereer_kandidaat_overzicht(req: KandidaatOverzichtRequest):
    try:
        b = bereken_tarief_direct(
            functieniveau=req.functieniveau,
            peildatum=req.startdatum_contract,
            basis_uurloon=req.basis_uurloon,
            positie_in_band=req.positie_in_band,
            marge_pct=req.marge_pct,
            omrekenfactor_override=req.omrekenfactor_override,
            jaren_op_niveau=req.jaren_op_niveau,
            nieuw_in_bouw_infra=req.nieuw_in_bouw_infra,
            starttabel_tweede_halfjaar=req.starttabel_tweede_halfjaar,
            config=_config_from_request(req),
        )
        return {
            "overzicht": genereer_kandidaat_overzicht(
                b,
                req.kandidaat_naam or "",
                req.opdrachtgever,
                req.project_naam,
                req.startdatum_contract,
            ),
            "berekening": b,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/v1/genereer-bureau-overzicht")
def api_genereer_bureau_overzicht(req: BureauOverzichtRequest):
    try:
        b = bereken_tarief_direct(
            functieniveau=req.functieniveau,
            peildatum=req.startdatum_contract,
            basis_uurloon=req.basis_uurloon,
            positie_in_band=req.positie_in_band,
            marge_pct=req.marge_pct,
            omrekenfactor_override=req.omrekenfactor_override,
            jaren_op_niveau=req.jaren_op_niveau,
            nieuw_in_bouw_infra=req.nieuw_in_bouw_infra,
            starttabel_tweede_halfjaar=req.starttabel_tweede_halfjaar,
            config=_config_from_request(req),
        )
        return {
            "overzicht": genereer_bureau_overzicht(
                b,
                req.kandidaat_naam or "",
                req.opdrachtgever,
                req.project_naam,
                req.startdatum_contract,
            ),
            "berekening": b,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/api/v1/marge-vergelijking")
def api_marge_vergelijking(
    functieniveau: int = Query(..., ge=1, le=6),
    startdatum_contract: date = Query(...),
    basis_uurloon: Optional[float] = Query(None),
    omrekenfactor_override: Optional[float] = Query(None, ge=1.0, le=3.0),
):
    try:
        return vergelijk_marges(
            functieniveau,
            startdatum_contract,
            basis_uurloon,
            omrekenfactor_override,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/api/v1/bereken-maandsalaris")
def api_bereken_maandsalaris(uurloon: float = Query(..., gt=0)):
    return {"uurloon": uurloon, "maandsalaris": bereken_maandsalaris(uurloon)}


@app.get("/api/v1/bereken-vier-weken-salaris")
def api_bereken_vier_weken_salaris(uurloon: float = Query(..., gt=0)):
    return {
        "uurloon": uurloon,
        "vier_weken_salaris": bereken_vier_weken_salaris(uurloon),
    }


@app.post("/api/v1/inschaling-en-tarief")
def api_inschaling_en_tarief(req: InschalingRequest):
    """Volledige pipeline: functietitel → mapping → optioneel niveau → kostprijs."""
    try:
        salaris_uur = _resolve_salarisverwachting_uur(req)
        result = genereer_volledig_voorstel(
            kandidaat=KandidaatInput(
                functie_omschrijving=req.functie_omschrijving,
                salarisverwachting_per_uur=salaris_uur,
                peildatum=req.peildatum,
            ),
            kandidaat_naam=req.kandidaat_naam or "",
            opdrachtgever=req.opdrachtgever,
            project_naam=req.project_naam,
            marge_pct=req.marge_pct,
            omrekenfactor_override=req.omrekenfactor_override,
            bevestigd_niveau=req.bevestigd_niveau,
            bevestigd_uurloon=req.bevestigd_uurloon,
            jaren_op_niveau=req.jaren_op_niveau,
            nieuw_in_bouw_infra=req.nieuw_in_bouw_infra,
            starttabel_tweede_halfjaar=req.starttabel_tweede_halfjaar,
            config=_config_from_request(req),
        )
        if salaris_uur is not None:
            result["salarisverwachting_per_uur"] = salaris_uur
            result["salarisverwachting_per_maand"] = bereken_maandsalaris(salaris_uur)
            if req.salarisverwachting_per_maand is not None:
                result["salarisverwachting_eenheid"] = "maand"
            elif req.salarisverwachting_per_uur is not None:
                result["salarisverwachting_eenheid"] = "uur"
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)
