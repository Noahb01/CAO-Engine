const fmt = (n) => `€${Number(n).toFixed(2)}`;
const fmtDate = (iso) => {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-");
  return `${d}-${m}-${y}`;
};

let werkgeversDefaults = null;
let urenPerMaand = 173.33;

function showError(panelId, message) {
  const el = document.getElementById(`${panelId}-error`);
  el.textContent = message;
  el.classList.add("visible");
}

function hideError(panelId) {
  const el = document.getElementById(`${panelId}-error`);
  el.classList.remove("visible");
}

function showResults(panelId) {
  document.getElementById(`${panelId}-results`).classList.add("visible");
}

function setLoading(btn, loading) {
  btn.disabled = loading;
  btn.dataset.originalText ??= btn.textContent;
  btn.textContent = loading ? "Bezig…" : btn.dataset.originalText;
}

async function apiCall(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.detail;
    throw new Error(
      typeof detail === "string" ? detail : JSON.stringify(detail) || res.statusText
    );
  }
  return data;
}

function readSalarisverwachting(fd) {
  const waarde = fd.get("salarisverwachting_waarde");
  if (!waarde) return {};
  const amount = parseFloat(waarde);
  const eenheid = fd.get("salaris_eenheid") || "uur";
  if (eenheid === "maand") {
    return { salarisverwachting_per_maand: amount };
  }
  return { salarisverwachting_per_uur: amount };
}

function updateSalarisPreview(form) {
  const preview = form.querySelector("[data-salaris-preview]");
  const input = form.querySelector("[data-salaris-input]");
  if (!preview || !input) return;

  const waarde = parseFloat(input.value);
  if (!waarde || Number.isNaN(waarde)) {
    preview.textContent = "";
    return;
  }

  const eenheid = form.querySelector('input[name="salaris_eenheid"]:checked')?.value || "uur";
  if (eenheid === "maand") {
    const uur = waarde / urenPerMaand;
    preview.textContent = `≈ ${fmt(uur)}/uur (op basis van ${urenPerMaand} uur/maand)`;
  } else {
    const maand = waarde * urenPerMaand;
    preview.textContent = `≈ ${fmt(maand)}/maand (op basis van ${urenPerMaand} uur/maand)`;
  }
}

function initSalarisEenheid(form) {
  const input = form.querySelector("[data-salaris-input]");
  if (!input) return;

  const convertOnSwitch = (nieuweEenheid) => {
    const huidige = parseFloat(input.value);
    if (!huidige || Number.isNaN(huidige)) return;
    if (nieuweEenheid === "maand") {
      input.value = (huidige * urenPerMaand).toFixed(2);
    } else {
      input.value = (huidige / urenPerMaand).toFixed(2);
    }
  };

  form.querySelectorAll('input[name="salaris_eenheid"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      convertOnSwitch(radio.value);
      updateSalarisPreview(form);
    });
  });
  input.addEventListener("input", () => updateSalarisPreview(form));
  updateSalarisPreview(form);
}

async function loadAppConstants() {
  try {
    const health = await apiCall("/api/v1/health");
    if (health.uren_per_maand) urenPerMaand = health.uren_per_maand;
  } catch {
    /* fallback 173.33 */
  }
}

function readWerkgeverslasten(fd) {
  return {
    vakantietoeslag_pct: parseFloat(fd.get("vakantietoeslag_pct")),
    duurzame_inzetbaarheid_pct: parseFloat(fd.get("duurzame_inzetbaarheid_pct")),
    pensioen_bpfbouw_pct: parseFloat(fd.get("pensioen_bpfbouw_pct")),
    sociale_lasten_pct: parseFloat(fd.get("sociale_lasten_pct")),
    sociaal_fonds_scholing_pct: parseFloat(fd.get("sociaal_fonds_scholing_pct")),
    verzuim_risico_pct: parseFloat(fd.get("verzuim_risico_pct")),
  };
}

function readCaoOpties(fd) {
  const opts = {
    jaren_op_niveau: parseFloat(fd.get("jaren_op_niveau") || "0"),
    nieuw_in_bouw_infra: fd.get("nieuw_in_bouw_infra") === "on",
    starttabel_tweede_halfjaar: fd.get("starttabel_tweede_halfjaar") === "on",
  };
  return opts;
}

function initStarttabelToggle(form) {
  const nieuw = form.querySelector('[name="nieuw_in_bouw_infra"]');
  const halfjaarWrap =
    form.querySelector("#starttabel-halfjaar-wrap") ||
    form.querySelector(".starttabel-halfjaar-tarief");
  if (!nieuw || !halfjaarWrap) return;

  const sync = () => {
    halfjaarWrap.classList.toggle("hidden", !nieuw.checked);
    if (!nieuw.checked) {
      const cb = halfjaarWrap.querySelector('[name="starttabel_tweede_halfjaar"]');
      if (cb) cb.checked = false;
    }
  };
  nieuw.addEventListener("change", sync);
  sync();
}

function applyFactorMode(fd, payload) {
  const modus = fd.get("factor_modus") || "opbouw";
  if (modus === "vast15") {
    payload.omrekenfactor_override = 1.5;
  } else if (modus === "handmatig") {
    const handmatig = fd.get("omrekenfactor_handmatig");
    if (handmatig) payload.omrekenfactor_override = parseFloat(handmatig);
  }
  payload.werkgeverslasten = readWerkgeverslasten(fd);
}

function renderFactorOpbouw(opbouw, elementId) {
  const el = document.getElementById(elementId);
  if (!opbouw || !Object.keys(opbouw).length) {
    el.classList.add("hidden");
    return;
  }
  const labels = {
    vakantietoeslag_pct: "Vakantietoeslag",
    duurzame_inzetbaarheid_pct: "Duurzame inzetbaarheid",
    som_premies_pct: "Som premies",
    premie_factor: "Premiefactor",
    werkbare_dagen: "Werkbare dagen",
    netto_werkbare_dagen: "Netto werkbare dagen",
    productiviteit_correctie: "Productiviteitscorrectie",
    vaste_factor_gebruikt: "Vaste factor",
    let_op: "Let op",
  };
  const rows = Object.entries(opbouw)
    .map(([k, v]) => `<dt>${labels[k] || k}</dt><dd>${v}</dd>`)
    .join("");
  el.innerHTML = `<strong>Factoropbouw</strong><dl>${rows}</dl>`;
  el.classList.remove("hidden");
}

function updateFactorPreview(form) {
  const modus = form.querySelector('input[name="factor_modus"]:checked')?.value || "opbouw";
  const preview = form.querySelector("[data-factor-preview]");
  const handmatigInput = form.querySelector(".factor-handmatig");
  if (!preview) return;

  if (modus === "handmatig") {
    handmatigInput?.classList.remove("hidden");
    const val = handmatigInput?.value;
    preview.textContent = val ? `Handmatige factor: ${val}×` : "Vul een handmatige factor in.";
  } else {
    handmatigInput?.classList.add("hidden");
    if (modus === "vast15") {
      preview.textContent = "Vaste omrekenfactor: 1,50×";
    } else if (werkgeversDefaults) {
      preview.textContent = `Indicatieve opbouw: ~${werkgeversDefaults.omrekenfactor.toFixed(4)}×`;
    } else {
      preview.textContent = "Opbouw uit premies + roostervrije dagen (~1,88×)";
    }
  }
}

function initFactorModes(form) {
  form.querySelectorAll('input[name="factor_modus"]').forEach((radio) => {
    radio.addEventListener("change", () => updateFactorPreview(form));
  });
  form.querySelectorAll(".premies-grid input").forEach((input) => {
    input.addEventListener("input", () => {
      if (form.querySelector('input[name="factor_modus"]:checked')?.value === "opbouw") {
        updateFactorPreview(form);
      }
    });
  });
  updateFactorPreview(form);
}

async function loadWerkgeversDefaults() {
  try {
    werkgeversDefaults = await apiCall("/api/v1/werkgeverslasten-defaults");
    document.querySelectorAll("form").forEach((form) => {
      const premies = form.querySelector(".premies-grid");
      if (!premies || !werkgeversDefaults.werkgeverslasten) return;
      const w = werkgeversDefaults.werkgeverslasten;
      const set = (name, val) => {
        const el = form.querySelector(`[name="${name}"]`);
        if (el) el.value = val;
      };
      set("vakantietoeslag_pct", w.vakantietoeslag_pct);
      set("duurzame_inzetbaarheid_pct", w.duurzame_inzetbaarheid_pct ?? 2.3);
      set("pensioen_bpfbouw_pct", w.pensioen_bpfbouw_pct);
      set("sociale_lasten_pct", w.sociale_lasten_pct);
      set("sociaal_fonds_scholing_pct", w.sociaal_fonds_scholing_pct);
      set("verzuim_risico_pct", w.verzuim_risico_pct);
      updateFactorPreview(form);
    });
  } catch {
    /* defaults blijven in HTML */
  }
}

function initTabs() {
  document.querySelectorAll("nav [data-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("nav [data-tab]").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.tab).classList.add("active");
    });
  });
}

function initSubtabs(containerId) {
  const container = document.getElementById(containerId);
  container.querySelectorAll("[data-subtab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      container.querySelectorAll("[data-subtab]").forEach((b) => b.classList.remove("active"));
      container.querySelectorAll(".subpanel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.subtab).classList.add("active");
    });
  });
}

function renderMappingContext(data) {
  const fl = data.functieladder;
  const mapping = data.functie_mapping;

  const matrixEl = document.getElementById("ins-matrix-signaal");
  const signaal = fl?.matrix_signaal || mapping?.matrix_signaal;
  if (signaal) {
    matrixEl.textContent = signaal;
    matrixEl.classList.remove("hidden");
  } else {
    matrixEl.classList.add("hidden");
    matrixEl.textContent = "";
  }

  const waaromEl = document.getElementById("ins-waarom-niveau");
  const toelichtingEl = document.getElementById("ins-toelichting");
  const toelichting = fl?.toelichting || mapping?.toelichting;
  if (toelichting) {
    toelichtingEl.textContent = toelichting;
    waaromEl.classList.remove("hidden");
    waaromEl.open = false;
  } else {
    toelichtingEl.textContent = "";
    waaromEl.classList.add("hidden");
  }
}

function renderLadderResult(data) {
  const el = document.getElementById("ins-ladder");
  const fl = data.functieladder;
  if (!fl) {
    el.classList.add("hidden");
    el.innerHTML = "";
    return;
  }

  const karTekst =
    fl.karakteristiek_status === "ingevuld" && fl.karakteristiek
      ? `<p class="karakteristiek-tekst">${fl.karakteristiek}</p>`
      : `<p class="karakteristiek-tekst" style="color:var(--warning)">Geen karakteristiek in CAO bijlage 1.3 voor dit niveau.</p>`;

  const waarschuwingen =
    fl.waarschuwingen?.length
      ? `<ul style="margin:0.5rem 0 0;padding-left:1.2rem;color:var(--muted);font-size:0.85rem">${fl.waarschuwingen
          .map((w) => `<li>${w}</li>`)
          .join("")}</ul>`
      : "";

  el.innerHTML = `
    <h3>Verantwoording inschaling</h3>
    <p style="margin:0.25rem 0 0"><strong>${mappingLabel(data)}</strong></p>
    <p style="margin:0.35rem 0 0;color:var(--muted);font-size:0.85rem">
      CAO-functieladder ${fl.nummer}: ${fl.naam} · niveau ${fl.gekozen_niveau}
      ${data.voorgesteld_niveau && data.voorgesteld_niveau !== fl.gekozen_niveau
        ? ` (voorstel was ${data.voorgesteld_niveau})`
        : ""}
      ${fl.intredekeuring_verplicht ? ' · <span class="badge badge-warn">Intredekeuring verplicht</span>' : ""}
    </p>
    ${karTekst}
    ${waarschuwingen}
  `;
  el.classList.remove("hidden");
}

function mappingLabel(data) {
  const fm = data.functie_mapping;
  if (fm?.functie_naam) return fm.functie_naam;
  return data.berekening?.functieladder_naam || "Functietitel";
}

function renderInschalingResults(data) {
  const ins = data.inschaling;
  const ber = data.berekening;

  renderMappingContext(data);
  renderLadderResult(data);

  const bijstellingEl = document.getElementById("ins-niveau-bijstelling");
  if (data.niveau_bijgesteld && data.niveau_bijstelling) {
    bijstellingEl.textContent = data.niveau_bijstelling;
    bijstellingEl.classList.remove("hidden");
  } else {
    bijstellingEl.classList.add("hidden");
    bijstellingEl.textContent = "";
  }

  document.getElementById("ins-hard").innerHTML = `
    <div class="stat-grid">
      <div class="stat"><div class="label">CAO-tabel</div><div class="value">${fmtDate(ber.cao_tabel)}</div></div>
      <div class="stat"><div class="label">Gebruikt niveau</div><div class="value">${data.gebruikt_niveau}</div></div>
      <div class="stat"><div class="label">Tabel min / max</div><div class="value">${fmt(ber.band_min)} – ${fmt(ber.band_max)}</div></div>
      <div class="stat"><div class="label">Effectief minimum</div><div class="value">${fmt(ber.effectief_minimum)} (${(ber.doorgroei_percentage * 100).toFixed(0)}%)</div></div>
      <div class="stat"><div class="label">Starttabel</div><div class="value">${ber.starttabel_toegepast ? "Ja" : "Nee"}</div></div>
    </div>
    <p style="margin:0.75rem 0 0;font-size:0.85rem;color:var(--muted)">
      Doorgroeilijn: 0jr ${fmt(ber.doorgroei_lijn["0_jaar"])} ·
      2jr ${fmt(ber.doorgroei_lijn["2_jaar_104pct"])} ·
      4jr ${fmt(ber.doorgroei_lijn["4_jaar_110pct"])} ·
      6jr ${fmt(ber.doorgroei_lijn["6_jaar_116pct"])}
    </p>
    <p style="margin:0.5rem 0 0;font-size:0.9rem">${ber.niveau_naam}</p>
    <p class="disclaimer" style="margin-top:0.5rem">${data.niveau_bron}</p>
  `;

  document.getElementById("ins-oordeel").innerHTML = `
    <div class="stat-grid">
      <div class="stat"><div class="label">Gekozen niveau</div><div class="value">${data.gebruikt_niveau}</div></div>
      <div class="stat"><div class="label">Voorstel uit functietitel</div><div class="value">${data.voorgesteld_niveau ?? data.gebruikt_niveau}</div></div>
      <div class="stat"><div class="label">Positie in band</div><div class="value">${ins.voorgestelde_positie}</div></div>
      <div class="stat"><div class="label">Voorgesteld uurloon</div><div class="value">${fmt(ins.voorgesteld_uurloon)}</div></div>
    </div>
    <p class="disclaimer">${ins.oordeel_disclaimer}</p>
  `;

  const checkClass =
    ins.verwachting_past_in_band === true
      ? "check-ok"
      : ins.verwachting_past_in_band === false
        ? "check-warn"
        : "";
  document.getElementById("ins-check").innerHTML = `
    <p class="${checkClass}" style="margin:0 0 0.5rem">${ins.verwachting_opmerking}</p>
    ${
      data.salarisverwachting_per_uur
        ? `<p style="margin:0 0 0.5rem;font-size:0.9rem">Ingevoerd: ${fmt(data.salarisverwachting_per_uur)}/uur · ${fmt(data.salarisverwachting_per_maand)}/maand${
            data.salarisverwachting_eenheid === "maand" ? " (kandidaat gaf maandbedrag op)" : ""
          }</p>`
        : ""
    }
    <p style="margin:0;font-size:0.9rem;color:var(--muted)">${ber.verwachting_status}</p>
  `;

  const margeBedrag = ber.facturatie_per_uur - ber.kostprijs_per_uur;
  document.getElementById("ins-tarief").innerHTML = `
    <div class="stat-grid">
      <div class="stat"><div class="label">Bruto uurloon</div><div class="value">${fmt(ber.bruto_uurloon)}</div></div>
      <div class="stat"><div class="label">Omrekenfactor</div><div class="value">${ber.omrekenfactor}×</div></div>
      <div class="stat"><div class="label">Kostprijs</div><div class="value">${fmt(ber.kostprijs_per_uur)}</div></div>
      <div class="stat"><div class="label">Marge (${ber.marge_pct}%)</div><div class="value">${fmt(margeBedrag)}</div></div>
      <div class="stat highlight"><div class="label">Facturatie</div><div class="value">${fmt(ber.facturatie_per_uur)}/uur</div></div>
      <div class="stat highlight"><div class="label">× bruto</div><div class="value">${ber.totaal_factor_op_bruto.toFixed(2)}×</div></div>
    </div>
    <p class="disclaimer" style="margin-top:0.75rem">${ber.bruto_bron}</p>
  `;

  renderFactorOpbouw(ber.factor_opbouw, "ins-factor-opbouw");

  const warnEl = document.getElementById("ins-waarschuwingen");
  if (ber.waarschuwingen && ber.waarschuwingen.length) {
    warnEl.classList.remove("hidden");
    warnEl.innerHTML =
      "<strong>Waarschuwingen</strong><ul style='margin:0.5rem 0 0;padding-left:1.2rem'>" +
      ber.waarschuwingen.map((w) => `<li>${w}</li>`).join("") +
      "</ul>";
  } else {
    warnEl.classList.add("hidden");
  }

  document.getElementById("ins-kandidaat-doc").textContent = data.kandidaat_overzicht;
  document.getElementById("ins-bureau-doc").textContent = data.bureau_overzicht;
}

async function handleInschaling(e) {
  e.preventDefault();
  hideError("inschaling");
  const btn = e.target.querySelector('button[type="submit"]');
  setLoading(btn, true);

  const fd = new FormData(e.target);
  const functie = fd.get("functie_omschrijving") || document.getElementById("functie-omschrijving-hidden").value;

  if (!functie || !functie.trim()) {
    showError("inschaling", "Kies een functietitel uit de lijst.");
    setLoading(btn, false);
    return;
  }

  const payload = {
    functie_omschrijving: functie.trim(),
    peildatum: fd.get("peildatum"),
    opdrachtgever: fd.get("opdrachtgever"),
    project_naam: fd.get("project_naam") || null,
    marge_pct: parseFloat(fd.get("marge_pct")),
  };

  const kandidaatNaam = (fd.get("kandidaat_naam") || "").trim();
  if (kandidaatNaam) payload.kandidaat_naam = kandidaatNaam;

  const ladderNiveau = fd.get("ladder_niveau") || document.getElementById("ladder-niveau-value").value;
  if (ladderNiveau) {
    payload.bevestigd_niveau = parseInt(ladderNiveau, 10);
  }

  const verwachting = readSalarisverwachting(fd);
  Object.assign(payload, verwachting);

  applyFactorMode(fd, payload);
  Object.assign(payload, readCaoOpties(fd));

  const bevestigdUurloon = fd.get("bevestigd_uurloon");
  if (bevestigdUurloon) payload.bevestigd_uurloon = parseFloat(bevestigdUurloon);

  try {
    const data = await apiCall("/api/v1/inschaling-en-tarief", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderInschalingResults(data);
    showResults("inschaling");
  } catch (err) {
    showError("inschaling", err.message);
  } finally {
    setLoading(btn, false);
  }
}

function renderTariefResults(data) {
  const margeBedrag = data.facturatie_per_uur - data.kostprijs_per_uur;
  document.getElementById("tarief-stats").innerHTML = `
    <div class="stat-grid">
      <div class="stat"><div class="label">CAO-tabel</div><div class="value">${fmtDate(data.cao_tabel)}</div></div>
      <div class="stat"><div class="label">Bruto uurloon</div><div class="value">${fmt(data.bruto_uurloon)}</div></div>
      <div class="stat"><div class="label">CAO-band</div><div class="value">${fmt(data.band_min)} – ${fmt(data.band_max)}</div></div>
      <div class="stat"><div class="label">Omrekenfactor</div><div class="value">${data.omrekenfactor}×</div></div>
      <div class="stat"><div class="label">Kostprijs</div><div class="value">${fmt(data.kostprijs_per_uur)}</div></div>
      <div class="stat"><div class="label">Marge (${data.marge_pct}%)</div><div class="value">${fmt(margeBedrag)}</div></div>
      <div class="stat highlight"><div class="label">Facturatie</div><div class="value">${fmt(data.facturatie_per_uur)}/uur</div></div>
      <div class="stat highlight"><div class="label">× bruto</div><div class="value">${data.totaal_factor_op_bruto.toFixed(2)}×</div></div>
    </div>
    <p class="disclaimer" style="margin-top:0.75rem">${data.bruto_bron}</p>
  `;
  renderFactorOpbouw(data.factor_opbouw, "tarief-factor-opbouw");
}

async function handleTarief(e) {
  e.preventDefault();
  hideError("tarief");
  const btn = e.target.querySelector('button[type="submit"]');
  setLoading(btn, true);

  const fd = new FormData(e.target);
  const payload = {
    functieniveau: parseInt(fd.get("functieniveau"), 10),
    startdatum_contract: fd.get("startdatum_contract"),
    marge_pct: parseFloat(fd.get("marge_pct")),
  };
  const uurloon = fd.get("basis_uurloon");
  if (uurloon) payload.basis_uurloon = parseFloat(uurloon);

  applyFactorMode(fd, payload);
  Object.assign(payload, readCaoOpties(fd));

  try {
    const data = await apiCall("/api/v1/bereken-tarief", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderTariefResults(data);
    showResults("tarief");
  } catch (err) {
    showError("tarief", err.message);
  } finally {
    setLoading(btn, false);
  }
}

function renderCaoResults(data) {
  document.getElementById("cao-stats").innerHTML = `
    <div class="stat-grid">
      <div class="stat"><div class="label">Functieniveau</div><div class="value">${data.functieniveau}</div></div>
      <div class="stat"><div class="label">CAO-tabel</div><div class="value">${fmtDate(data.peildatum_tabel)}</div></div>
      <div class="stat"><div class="label">Minimum uurloon</div><div class="value">${fmt(data.minimum_uurloon)}</div></div>
      <div class="stat"><div class="label">Maximum uurloon</div><div class="value">${fmt(data.maximum_uurloon)}</div></div>
    </div>
    <p style="margin:0.75rem 0 0"><strong>${data.niveau_naam}</strong></p>
    <p style="margin:0.25rem 0 0;color:var(--muted);font-size:0.9rem">Indicatie ervaring: ${data.indicatie_ervaring}</p>
  `;
}

async function handleCao(e) {
  e.preventDefault();
  hideError("cao");
  const btn = e.target.querySelector('button[type="submit"]');
  setLoading(btn, true);

  const fd = new FormData(e.target);
  const fn = fd.get("functieniveau");
  const datum = fd.get("datum");

  try {
    const data = await apiCall(`/api/v1/cao-info?functieniveau=${fn}&datum=${datum}`);
    renderCaoResults(data);
    showResults("cao");
  } catch (err) {
    showError("cao", err.message);
  } finally {
    setLoading(btn, false);
  }
}

function setDefaultDates() {
  const today = new Date().toISOString().slice(0, 10);
  document.querySelectorAll('input[type="date"]').forEach((el) => {
    if (!el.value) el.value = today;
  });
}

let functietitelKeuzes = [];
let selectedFunctie = null;
let currentLadderNiveaus = [];

function setHiddenInschalingFields(functieNaam, ladderNummer, niveau) {
  document.getElementById("functie-omschrijving-hidden").value = functieNaam || "";
  document.getElementById("functieladder-hidden").value = ladderNummer || "";
  document.getElementById("ladder-niveau-value").value = niveau ?? "";
}

function clearNiveauBijstelling() {
  document.getElementById("niveau-bijstelling").classList.add("hidden");
  document.getElementById("ladder-niveau-btns").innerHTML = "";
  document.getElementById("ladder-karakteristiek").classList.add("hidden");
  document.getElementById("niveau-buiten-matrix-hint").classList.add("hidden");
  document.getElementById("niveau-ladder-info").textContent = "";
  currentLadderNiveaus = [];
}

function renderLadderKarakteristiek(niveauOpt) {
  const panel = document.getElementById("ladder-karakteristiek");
  if (!niveauOpt) {
    panel.classList.add("hidden");
    panel.innerHTML = "";
    return;
  }

  panel.classList.remove("hidden");
  if (niveauOpt.status === "ingevuld" && niveauOpt.karakteristiek) {
    panel.classList.remove("empty");
    panel.innerHTML = `
      <h4>CAO-karakteristiek niveau ${niveauOpt.niveau}</h4>
      <p style="margin:0">${niveauOpt.karakteristiek}</p>
    `;
    return;
  }

  panel.classList.add("empty");
  panel.innerHTML = `
    <h4>Niveau ${niveauOpt.niveau}</h4>
    <p style="margin:0">De CAO bijlage 1.3 heeft geen karakteristiek voor dit niveau op deze ladder.</p>
  `;
}

function _ladderNiveauButtons() {
  return [...document.querySelectorAll(".ladder-niveau-btn")];
}

function _updateLadderAria(selectedNiveau) {
  _ladderNiveauButtons().forEach((btn) => {
    const isSelected = parseInt(btn.dataset.niveau, 10) === selectedNiveau;
    btn.setAttribute("aria-checked", isSelected ? "true" : "false");
    btn.tabIndex = isSelected ? 0 : -1;
  });
}

function selectLadderNiveau(niveau, niveauOpt) {
  document.getElementById("ladder-niveau-value").value = niveau;
  _ladderNiveauButtons().forEach((btn) => {
    btn.classList.toggle("selected", parseInt(btn.dataset.niveau, 10) === niveau);
  });
  _updateLadderAria(niveau);
  renderLadderKarakteristiek(niveauOpt);
}

function renderMatrixNiveauButtons(matrixNiveaus, voorgesteld) {
  const container = document.getElementById("ladder-niveau-btns");
  container.innerHTML = "";

  matrixNiveaus.forEach((n) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "ladder-niveau-btn";
    btn.dataset.niveau = n.niveau;
    btn.setAttribute("role", "radio");
    btn.setAttribute("aria-checked", "false");
    btn.tabIndex = -1;
    btn.textContent = n.niveau;
    btn.title =
      n.status === "ingevuld" && n.karakteristiek
        ? n.karakteristiek.slice(0, 120) + (n.karakteristiek.length > 120 ? "…" : "")
        : "Geen karakteristiek in CAO bijlage 1.3";
    if (n.status === "leeg_in_cao") btn.classList.add("leeg-in-cao");
    btn.addEventListener("click", () => selectLadderNiveau(n.niveau, n));
    container.appendChild(btn);
  });

  const inMatrix = matrixNiveaus.some((n) => n.niveau === voorgesteld);
  const hint = document.getElementById("niveau-buiten-matrix-hint");

  if (inMatrix) {
    hint.classList.add("hidden");
    const opt = matrixNiveaus.find((n) => n.niveau === voorgesteld);
    selectLadderNiveau(voorgesteld, opt);
  } else {
    hint.classList.remove("hidden");
    hint.textContent =
      `Voorstel: niveau ${voorgesteld} (valt buiten de standaard laddertredes). ` +
      "Kies een niveau uit de matrix of accepteer het voorstel zonder aanpassing.";
    setHiddenInschalingFields(
      selectedFunctie.functie_naam,
      selectedFunctie.functieladder_nummer,
      voorgesteld
    );
    renderLadderKarakteristiek(null);
  }
}

async function loadNiveauBijstelling(keuze) {
  const wrap = document.getElementById("niveau-bijstelling");
  const info = document.getElementById("niveau-ladder-info");

  clearNiveauBijstelling();
  wrap.classList.remove("hidden");

  const ladderNaam = keuze.functieladder_naam || `ladder ${keuze.functieladder_nummer}`;
  info.textContent = `${ladderNaam} — kies het passende niveau op basis van de CAO-karakteristieken.`;

  try {
    const alleNiveaus = await apiCall(
      `/api/v1/functieladders/${keuze.functieladder_nummer}/niveaus`
    );
    currentLadderNiveaus = alleNiveaus.filter((n) => n.in_matrix);
    renderMatrixNiveauButtons(currentLadderNiveaus, keuze.voorgesteld_niveau);
  } catch (err) {
    showError("inschaling", `Niveaus laden mislukt: ${err.message}`);
    wrap.classList.add("hidden");
  }
}

async function selectFunctietitel(keuze) {
  selectedFunctie = keuze;
  const input = document.getElementById("functietitel-input");
  input.value = keuze.functie_naam;
  setHiddenInschalingFields(
    keuze.functie_naam,
    keuze.functieladder_nummer,
    keuze.voorgesteld_niveau
  );
  hideTypeaheadSuggesties();
  hideError("inschaling");
  await loadNiveauBijstelling(keuze);
}

function hideTypeaheadSuggesties() {
  const list = document.getElementById("functietitel-suggesties");
  list.classList.add("hidden");
  list.innerHTML = "";
}

function renderTypeaheadSuggesties(term) {
  const list = document.getElementById("functietitel-suggesties");
  const q = term.trim().toLowerCase();

  if (!q) {
    hideTypeaheadSuggesties();
    return;
  }

  const matches = functietitelKeuzes.filter((k) => k.zoektekst.includes(q));

  if (!matches.length) {
    hideTypeaheadSuggesties();
    return;
  }

  list.innerHTML = matches
    .slice(0, 12)
    .map(
      (k) =>
        `<li role="option" data-id="${k.id}">${k.label}${
          k.categorie ? `<span class="typeahead-categorie">${k.categorie}</span>` : ""
        }</li>`
    )
    .join("");
  list.classList.remove("hidden");

  list.querySelectorAll("li").forEach((li) => {
    li.addEventListener("mousedown", async (e) => {
      e.preventDefault();
      const keuze = functietitelKeuzes.find((k) => k.id === li.dataset.id);
      if (keuze) await selectFunctietitel(keuze);
    });
  });
}

async function resolveFunctietitelFromInput(value) {
  const trimmed = value.trim();
  if (!trimmed) {
    selectedFunctie = null;
    clearNiveauBijstelling();
    setHiddenInschalingFields("", "", "");
    return;
  }

  const exact = functietitelKeuzes.find(
    (k) => k.functie_naam.toLowerCase() === trimmed.toLowerCase()
  );
  if (exact) {
    await selectFunctietitel(exact);
    return;
  }

  selectedFunctie = null;
  clearNiveauBijstelling();
  setHiddenInschalingFields("", "", "");
}

async function loadInschalingKeuzes() {
  try {
    const data = await apiCall("/api/v1/inschaling-keuzes");
    functietitelKeuzes = data.functietitels || [];

    const defaultKeuze = functietitelKeuzes.find((k) => k.functie_naam === "Werkvoorbereider");
    if (defaultKeuze) {
      await selectFunctietitel(defaultKeuze);
    }
  } catch {
    document.getElementById("functietitel-input").placeholder = "Functietitels niet beschikbaar";
  }
}

function initFunctietitelTypeahead() {
  const input = document.getElementById("functietitel-input");

  input.addEventListener("input", () => {
    renderTypeaheadSuggesties(input.value);
    if (!input.value.trim()) {
      selectedFunctie = null;
      clearNiveauBijstelling();
      setHiddenInschalingFields("", "", "");
    }
  });

  input.addEventListener("focus", () => {
    if (input.value.trim()) {
      renderTypeaheadSuggesties(input.value);
    } else {
      hideTypeaheadSuggesties();
    }
  });

  input.addEventListener("blur", () => {
    setTimeout(() => {
      hideTypeaheadSuggesties();
      resolveFunctietitelFromInput(input.value);
    }, 150);
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Escape") hideTypeaheadSuggesties();
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  initTabs();
  initSubtabs("inschaling-subtabs");
  setDefaultDates();
  await loadAppConstants();
  loadWerkgeversDefaults();
  await loadInschalingKeuzes();

  const formInschaling = document.getElementById("form-inschaling");
  const formTarief = document.getElementById("form-tarief");
  initFactorModes(formInschaling);
  initFactorModes(formTarief);
  initSalarisEenheid(formInschaling);
  initStarttabelToggle(formInschaling);
  initStarttabelToggle(formTarief);
  initFunctietitelTypeahead();

  formInschaling.addEventListener("submit", handleInschaling);
  formTarief.addEventListener("submit", handleTarief);
  document.getElementById("form-cao").addEventListener("submit", handleCao);
});
