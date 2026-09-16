let tableData = [];
let bomData = [];
let hot;
let bomHot;

const planColumns = [
  { data: "material", readOnly: true },
  { data: "week", readOnly: true },
  { data: "demand_qty", type: "numeric", readOnly: true },
  { data: "base_supply", type: "numeric", readOnly: true },
  { data: "scenario_supply", type: "numeric" },
  { data: "projected_balance", type: "numeric", readOnly: true },
  { data: "shortage_qty", type: "numeric", readOnly: true },
  { data: "affected_fg", readOnly: true },
];

const planHeaders = [
  "Material",
  "Week",
  "Demand",
  "Base Supply",
  "Scenario Supply",
  "Projected Balance",
  "Shortage Qty",
  "Affected FG",
];

function initPlanTable(rows) {
  tableData = rows;

  if (hot) {
    hot.loadData(tableData);
    refreshArrivalControls();
    return;
  }

  hot = new Handsontable(document.getElementById("hot"), {
    data: tableData,
    columns: planColumns,
    colHeaders: planHeaders,
    rowHeaders: true,
    stretchH: "all",
    height: 430,
    licenseKey: "non-commercial-and-evaluation",
    dropdownMenu: true,
    filters: true,
    contextMenu: true,
    manualColumnResize: true,
    columnSorting: true,
    className: "htMiddle",
    cells(row, col) {
      const props = {};
      if (col === 4) {
        props.className = "htRight supply-cell";
      }
      if (col === 6 && Number(tableData[row]?.shortage_qty) > 0) {
        props.className = "htRight shortage-cell";
      }
      return props;
    },
  });

  refreshArrivalControls();
}

function initBomTable(rows) {
  bomData = rows;

  if (bomHot) {
    bomHot.loadData(bomData);
    return;
  }

  bomHot = new Handsontable(document.getElementById("bomHot"), {
    data: bomData,
    columns: [
      { data: "parent" },
      { data: "component" },
      { data: "qty_per", type: "numeric" },
    ],
    colHeaders: ["Parent", "Component", "Qty per"],
    rowHeaders: true,
    stretchH: "all",
    height: 430,
    minSpareRows: 1,
    licenseKey: "non-commercial-and-evaluation",
    contextMenu: true,
    manualColumnResize: true,
  });
}

function updateSummary(summary) {
  document.getElementById("materialsCount").textContent = summary.materials ?? "-";
  document.getElementById("shortageMaterials").textContent = summary.shortage_materials ?? "-";
  document.getElementById("firstShortage").textContent = summary.first_shortage_week ?? "None";
  document.getElementById("totalShortage").textContent = summary.total_shortage_qty ?? 0;
}

function updateImpact(rows) {
  const target = document.getElementById("impactList");
  const shortageRows = rows.filter((row) => Number(row.shortage_qty) > 0);

  if (!shortageRows.length) {
    target.innerHTML = `
      <div class="impact-item">
        <span>No shortage in current scenario</span>
        <strong>CTB OK</strong>
        <span>-</span>
      </div>
    `;
    return;
  }

  target.innerHTML = shortageRows
    .map(
      (row) => `
        <div class="impact-item">
          <span>${row.material} · ${row.week}</span>
          <strong>-${row.shortage_qty}</strong>
          <span>${row.affected_fg || "No FG mapping"}</span>
        </div>
      `
    )
    .join("");
}

function setStatus(text) {
  document.getElementById("statusText").textContent = text;
}

function setBomStatus(text) {
  document.getElementById("bomStatus").textContent = text;
}

async function loadBase() {
  const res = await fetch("/api/base");
  const data = await res.json();

  if (!res.ok) {
    alert(data.detail || "Failed to load base plan.");
    return;
  }

  initPlanTable(data.rows);
  updateSummary(data.summary);
  updateImpact(data.rows);
  setStatus("Base loaded");
}

async function recalculate() {
  const currentRows = hot.getSourceData();
  const res = await fetch("/api/recalculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rows: currentRows }),
  });
  const data = await res.json();

  initPlanTable(data.rows);
  updateSummary(data.summary);
  updateImpact(data.rows);
  setStatus("Scenario recalculated");
}

async function saveScenario() {
  const name = document.getElementById("scenarioName").value.trim();
  const remark = document.getElementById("scenarioRemark").value.trim();

  if (!name) {
    alert("Please enter a scenario name.");
    return;
  }

  const res = await fetch("/api/scenarios", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, remark, rows: hot.getSourceData() }),
  });
  const data = await res.json();

  if (!res.ok) {
    alert(data.detail || "Failed to save scenario.");
    return;
  }

  await refreshScenarioList();
  setStatus(`Saved: ${name}`);
}

async function refreshScenarioList() {
  const res = await fetch("/api/scenarios");
  const items = await res.json();
  const select = document.getElementById("scenarioSelect");
  select.innerHTML = `<option value="">Select scenario</option>`;

  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = item.name;
    select.appendChild(option);
  });
}

async function loadScenario() {
  const id = document.getElementById("scenarioSelect").value;

  if (!id) {
    alert("Select a scenario first.");
    return;
  }

  const res = await fetch(`/api/scenarios/${id}`);
  const data = await res.json();

  initPlanTable(data.rows);
  updateSummary(data.summary);
  updateImpact(data.rows);
  document.getElementById("scenarioName").value = data.scenario.name;
  document.getElementById("scenarioRemark").value = data.scenario.remark || "";
  setStatus(`Loaded: ${data.scenario.name}`);
}

function refreshArrivalControls() {
  if (!tableData.length) return;

  const materialSelect = document.getElementById("arrivalMaterial");
  const currentMaterial = materialSelect.value;
  const materials = [...new Set(tableData.map((row) => row.material))].sort();

  materialSelect.innerHTML = materials
    .map((item) => `<option value="${item}">${item}</option>`)
    .join("");

  if (materials.includes(currentMaterial)) {
    materialSelect.value = currentMaterial;
  }

  updateArrivalWeeks();
}

function updateArrivalWeeks() {
  const material = document.getElementById("arrivalMaterial").value;
  const weeks = tableData
    .filter((row) => row.material === material)
    .map((row) => row.week);

  const fromSelect = document.getElementById("arrivalFromWeek");
  const toSelect = document.getElementById("arrivalToWeek");
  const options = weeks.map((week) => `<option value="${week}">${week}</option>`).join("");

  fromSelect.innerHTML = options;
  toSelect.innerHTML = options;
  if (weeks.length > 1) toSelect.value = weeks[1];
  fillArrivalQty();
}

function fillArrivalQty() {
  if (!hot) return;

  const material = document.getElementById("arrivalMaterial").value;
  const fromWeek = document.getElementById("arrivalFromWeek").value;
  const row = hot.getSourceData().find(
    (item) => item.material === material && item.week === fromWeek
  );

  document.getElementById("arrivalQty").value = row ? Number(row.scenario_supply) : 0;
}

async function applyArrivalAdjustment() {
  const material = document.getElementById("arrivalMaterial").value;
  const fromWeek = document.getElementById("arrivalFromWeek").value;
  const toWeek = document.getElementById("arrivalToWeek").value;
  const qty = Number(document.getElementById("arrivalQty").value);

  if (!material || !fromWeek || !toWeek || qty <= 0) {
    alert("Complete the arrival adjustment fields first.");
    return;
  }

  if (fromWeek === toWeek) {
    alert("From Week and To Week must be different.");
    return;
  }

  const rows = hot.getSourceData();
  const fromRow = rows.find((row) => row.material === material && row.week === fromWeek);
  const toRow = rows.find((row) => row.material === material && row.week === toWeek);

  if (!fromRow || !toRow) {
    alert("Selected supply rows were not found.");
    return;
  }

  if (Number(fromRow.scenario_supply) < qty) {
    alert("Move quantity is greater than available scenario supply.");
    return;
  }

  fromRow.scenario_supply = Number(fromRow.scenario_supply) - qty;
  toRow.scenario_supply = Number(toRow.scenario_supply) + qty;
  hot.loadData(rows);
  await recalculate();
  setStatus(`${material}: ${fromWeek} → ${toWeek}`);
}

async function loadBom() {
  const res = await fetch("/api/bom");
  const data = await res.json();
  initBomTable(data.rows);
  renderValidation(data.validation);
  setBomStatus(data.validation.valid ? "Valid" : "Needs review");
}

function getBomRows() {
  return bomHot
    .getSourceData()
    .filter(
      (row) => String(row.parent || "").trim() || String(row.component || "").trim()
    )
    .map((row) => ({
      parent: String(row.parent || "").trim(),
      component: String(row.component || "").trim(),
      qty_per: Number(row.qty_per || 0),
    }));
}

function renderValidation(result) {
  const target = document.getElementById("validationList");

  if (result.valid) {
    target.innerHTML = `
      <div class="validation-item ok">✓ No duplicate parent-component relationship</div>
      <div class="validation-item ok">✓ Qty per values are valid</div>
      <div class="validation-item ok">✓ No BOM cycle detected</div>
    `;
    return;
  }

  target.innerHTML = result.errors
    .map((error) => `<div class="validation-item error">✕ ${error}</div>`)
    .join("");
}

async function validateBom() {
  const res = await fetch("/api/bom/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rows: getBomRows() }),
  });
  const result = await res.json();
  renderValidation(result);
  setBomStatus(result.valid ? "Valid" : "Needs review");
  return result.valid;
}

async function saveBom() {
  const res = await fetch("/api/bom", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rows: getBomRows() }),
  });
  const data = await res.json();

  if (!res.ok) {
    renderValidation({
      valid: false,
      errors: Array.isArray(data.detail) ? data.detail : [data.detail || "BOM save failed."],
    });
    setBomStatus("Needs review");
    return;
  }

  renderValidation(data.validation);
  setBomStatus("Saved");
  await loadBase();
  alert("BOM saved. Planning results have been refreshed.");
}

function addBomRow() {
  const rows = bomHot.getSourceData().map((row) => ({ ...row }));
  const insertAt = Math.max(rows.length - 1, 0);

  rows.splice(insertAt, 0, {
    parent: "",
    component: "",
    qty_per: 1,
  });

  bomData = rows;
  bomHot.loadData(rows);
  bomHot.selectCell(insertAt, 0);
}

async function runWhereUsed() {
  const input = document.getElementById("whereUsedInput").value.trim();
  const target = document.getElementById("whereUsedResult");

  if (!input) {
    target.innerHTML = "";
    return;
  }

  const res = await fetch(`/api/where-used/${encodeURIComponent(input)}`);
  const data = await res.json();

  if (!data.paths.length) {
    target.innerHTML = `
      <div class="trace-card">No finished-goods path found for <strong>${input}</strong>.</div>
    `;
    return;
  }

  target.innerHTML = data.paths
    .map((path) => {
      const nodes = path
        .map((node) => `<span class="trace-node">${node}</span>`)
        .join(`<span class="trace-arrow">→</span>`);
      return `<div class="trace-card"><div class="trace-path">${nodes}</div></div>`;
    })
    .join("");
}

function switchView(viewId) {
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("active", view.id === viewId);
  });

  document.querySelectorAll(".nav-item").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === viewId);
  });

  if (viewId === "bomView" && bomHot) setTimeout(() => bomHot.render(), 0);
  if (viewId === "planningView" && hot) setTimeout(() => hot.render(), 0);
}

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => switchView(button.dataset.view));
});

document.getElementById("recalculate").addEventListener("click", recalculate);
document.getElementById("resetBase").addEventListener("click", loadBase);
document.getElementById("saveScenario").addEventListener("click", saveScenario);
document.getElementById("loadScenario").addEventListener("click", loadScenario);
document.getElementById("arrivalMaterial").addEventListener("change", updateArrivalWeeks);
document.getElementById("arrivalFromWeek").addEventListener("change", fillArrivalQty);
document.getElementById("applyArrival").addEventListener("click", applyArrivalAdjustment);
document.getElementById("addBomRow").addEventListener("click", addBomRow);
document.getElementById("validateBom").addEventListener("click", validateBom);
document.getElementById("saveBom").addEventListener("click", saveBom);
document.getElementById("runWhereUsed").addEventListener("click", runWhereUsed);

loadBase();
loadBom();
refreshScenarioList();
runWhereUsed();
