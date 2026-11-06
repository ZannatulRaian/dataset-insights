// Dataset Insights frontend. Talks to the FastAPI backend on the same origin.

let datasetId = null;
let columnInfo = { numeric: [], categorical: [] };

const $ = (id) => document.getElementById(id);

// ---------- helpers ----------
function showMessage(text, type) {
  const el = $("message");
  el.textContent = text;
  el.className = "message " + type;
}

function clearMessage() {
  $("message").className = "message hidden";
}

async function api(path, options) {
  const res = await fetch(path, options);
  let body = null;
  try { body = await res.json(); } catch (e) { /* no JSON body */ }
  if (!res.ok) {
    let detail = body && body.detail;
    if (Array.isArray(detail)) detail = detail.map((d) => d.msg).join("; ");
    throw new Error(detail || "Request failed (" + res.status + ")");
  }
  return body;
}

function fmt(v) {
  if (v === null || v === undefined) return "";
  return String(v);
}

// Build a table safely using textContent (no HTML injection from CSV data).
function renderTable(tableEl, headers, rows) {
  tableEl.replaceChildren();
  const thead = document.createElement("thead");
  const hr = document.createElement("tr");
  headers.forEach((h) => {
    const th = document.createElement("th");
    th.textContent = h;
    hr.appendChild(th);
  });
  thead.appendChild(hr);
  tableEl.appendChild(thead);

  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    row.forEach((cell) => {
      const td = document.createElement("td");
      td.textContent = fmt(cell);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  tableEl.appendChild(tbody);
}

function tile(label, value, warn) {
  const div = document.createElement("div");
  div.className = "tile" + (warn ? " warn" : "");
  const v = document.createElement("div");
  v.className = "value";
  v.textContent = value;
  const l = document.createElement("div");
  l.className = "label";
  l.textContent = label;
  div.append(v, l);
  return div;
}

function fillSelect(selectEl, options) {
  selectEl.replaceChildren();
  options.forEach((o) => {
    const opt = document.createElement("option");
    opt.value = o;
    opt.textContent = o;
    selectEl.appendChild(opt);
  });
}

// ---------- loading a dataset ----------
async function onDatasetLoaded(info) {
  datasetId = info.dataset_id;
  showMessage("Loaded " + info.filename + " (" + info.rows + " rows, " + info.columns + " columns).", "success");

  const [preview, summary, cols] = await Promise.all([
    api("/dataset/" + datasetId + "/preview?rows=10"),
    api("/dataset/" + datasetId + "/summary"),
    api("/dataset/" + datasetId + "/columns"),
  ]);
  columnInfo = cols;

  renderOverview(info.quality, summary);
  renderTable($("preview-table"), preview.columns, preview.rows.map((r) => preview.columns.map((c) => r[c])));
  renderStats(summary);
  setupChartControls();
  setupPredictionControls();

  $("results").classList.remove("hidden");
  $("pred-chart").replaceChildren();
  $("prediction-result").classList.add("hidden");
  $("chart").replaceChildren();
  $("results").scrollIntoView({ behavior: "smooth" });
}

function renderOverview(q, summary) {
  const tiles = $("stat-tiles");
  tiles.replaceChildren(
    tile("Rows", q.rows.toLocaleString()),
    tile("Columns", q.columns),
    tile("Missing values", q.total_missing + " (" + q.missing_percent + "%)", q.total_missing > 0),
    tile("Duplicate rows", q.duplicate_rows, q.duplicate_rows > 0)
  );

  const ul = $("insights");
  ul.replaceChildren();
  summary.insights.forEach((text) => {
    const li = document.createElement("li");
    li.textContent = text;
    ul.appendChild(li);
  });

  renderTable(
    $("quality-table"),
    ["Column", "Type", "Missing", "Missing %", "Unique values"],
    q.column_details.map((c) => [c.column, c.dtype, c.missing, c.missing_percent + "%", c.unique])
  );
}

function renderStats(summary) {
  if (summary.numeric.length) {
    renderTable(
      $("numeric-table"),
      ["Column", "Count", "Mean", "Median", "Mode", "Min", "Max", "Std dev"],
      summary.numeric.map((n) => [n.column, n.count, n.mean, n.median, n.mode, n.min, n.max, n.std])
    );
  } else {
    $("numeric-table").replaceChildren();
  }

  if (summary.categorical.length) {
    renderTable(
      $("categorical-table"),
      ["Column", "Count", "Unique", "Top values"],
      summary.categorical.map((c) => [
        c.column, c.count, c.unique,
        c.top.map((t) => t.value + " (" + t.count + ")").join(", "),
      ])
    );
  } else {
    $("categorical-table").replaceChildren();
  }
}

// ---------- charts ----------
function setupChartControls() {
  updateChartControls();
}

function updateChartControls() {
  const type = $("chart-type").value;
  const xSel = $("x-col");
  const ySel = $("y-col");
  $("x-label").classList.toggle("hidden", type === "heatmap");
  $("y-label").classList.toggle("hidden", type !== "scatter");

  if (type === "bar") {
    fillSelect(xSel, columnInfo.categorical.concat(columnInfo.numeric));
  } else {
    fillSelect(xSel, columnInfo.numeric);
  }
  fillSelect(ySel, columnInfo.numeric);
  if (type === "scatter" && columnInfo.numeric.length > 1) ySel.selectedIndex = 1;
}

async function drawChart() {
  const type = $("chart-type").value;
  const params = new URLSearchParams({ chart: type });
  if (type !== "heatmap") params.set("x", $("x-col").value);
  if (type === "scatter") params.set("y", $("y-col").value);

  try {
    clearMessage();
    const fig = await api("/dataset/" + datasetId + "/visualizations?" + params.toString());
    Plotly.newPlot("chart", fig.data, Object.assign({ margin: { t: 50 } }, fig.layout), { responsive: true });
  } catch (err) {
    showMessage(err.message, "error");
  }
}

// ---------- prediction ----------
function setupPredictionControls() {
  fillSelect($("target-col"), columnInfo.numeric);
  renderFeatureChecks();
}

function renderFeatureChecks() {
  const target = $("target-col").value;
  const box = $("feature-list");
  box.replaceChildren();
  columnInfo.numeric.filter((c) => c !== target).forEach((c) => {
    const label = document.createElement("label");
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.value = c;
    label.append(cb, document.createTextNode(" " + c));
    box.appendChild(label);
  });
}

async function trainModel() {
  const features = Array.from($("feature-list").querySelectorAll("input:checked")).map((c) => c.value);
  const btn = $("predict-btn");
  btn.disabled = true;
  try {
    clearMessage();
    const res = await api("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset_id: datasetId, target: $("target-col").value, features: features }),
    });

    $("metric-tiles").replaceChildren(
      tile("R² score", res.r2),
      tile("MAE", res.mae),
      tile("Training rows", res.train_rows),
      tile("Test rows", res.test_rows)
    );
    renderTable($("coef-table"), ["Feature", "Coefficient"],
      Object.entries(res.coefficients).concat([["(intercept)", res.intercept]]));

    $("prediction-result").classList.remove("hidden");
    Plotly.newPlot("pred-chart", res.chart.data, Object.assign({ margin: { t: 50 } }, res.chart.layout), { responsive: true });
  } catch (err) {
    showMessage(err.message, "error");
  } finally {
    btn.disabled = false;
  }
}

// ---------- upload handlers ----------
async function uploadFile() {
  const file = $("file-input").files[0];
  if (!file) { showMessage("Please choose a CSV file first.", "error"); return; }
  const form = new FormData();
  form.append("file", file);
  try {
    clearMessage();
    $("upload-btn").disabled = true;
    const info = await api("/upload", { method: "POST", body: form });
    await onDatasetLoaded(info);
  } catch (err) {
    showMessage(err.message, "error");
  } finally {
    $("upload-btn").disabled = false;
  }
}

async function useSample() {
  const name = $("sample-select").value;
  if (!name) return;
  try {
    clearMessage();
    const info = await api("/samples/" + encodeURIComponent(name), { method: "POST" });
    await onDatasetLoaded(info);
  } catch (err) {
    showMessage(err.message, "error");
  }
}

async function init() {
  try {
    const data = await api("/samples");
    fillSelect($("sample-select"), data.samples);
  } catch (err) {
    showMessage("Could not reach the backend: " + err.message, "error");
  }
  $("upload-btn").addEventListener("click", uploadFile);
  $("sample-btn").addEventListener("click", useSample);
  $("chart-type").addEventListener("change", updateChartControls);
  $("chart-btn").addEventListener("click", drawChart);
  $("target-col").addEventListener("change", renderFeatureChecks);
  $("predict-btn").addEventListener("click", trainModel);
}

init();
