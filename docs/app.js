const DATA_URL = "./data/leaderboard-explorer.json";

const TIER_META = {
  closed_source: { label: "Closed Source", color: "#2563eb", symbol: "diamond" },
  open_source_pro: { label: "Open Source Pro", color: "#5c6f87", symbol: "square" },
  open_source_consumer: { label: "Open Source Consumer", color: "#8ab4ff", symbol: "circle" },
  baseline: { label: "Baseline", color: "#9ca9ba", symbol: "x" },
};

const state = {
  data: null,
  metricsByKey: {},
  xMetric: null,
  yMetric: null,
  xScale: "linear",
  search: "",
  showLabels: false,
  completeOnly: true,
  selectedTiers: new Set(Object.keys(TIER_META)),
};

const elements = {
  chart: document.getElementById("chart"),
  chartTitle: document.getElementById("chart-title"),
  chartSubtitle: document.getElementById("chart-subtitle"),
  presetStrip: document.getElementById("preset-strip"),
  xAxis: document.getElementById("x-axis"),
  yAxis: document.getElementById("y-axis"),
  modelSearch: document.getElementById("model-search"),
  showLabels: document.getElementById("show-labels"),
  completeOnly: document.getElementById("complete-only"),
  tierFilter: document.getElementById("tier-filter"),
  tableBody: document.getElementById("table-body"),
  tableSummary: document.getElementById("table-summary"),
};

function formatValue(metric, value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "–";
  }

  switch (metric.format) {
    case "percent":
      return `${value.toFixed(1)}%`;
    case "seconds":
      return `${value.toFixed(2)}s`;
    case "integer":
      return value.toLocaleString();
    default:
      return value.toFixed(1);
  }
}

function metricByKey(key) {
  return state.metricsByKey[key];
}

function defaultScaleForMetric(key) {
  return key === "avg_seconds_per_event" ? "log" : "linear";
}

function populateMetricSelect(selectEl, selectedKey) {
  selectEl.innerHTML = "";
  state.data.metrics.forEach((metric) => {
    const option = document.createElement("option");
    option.value = metric.key;
    option.textContent = metric.label;
    if (metric.key === selectedKey) {
      option.selected = true;
    }
    selectEl.appendChild(option);
  });
}

function buildPresetButtons() {
  elements.presetStrip.innerHTML = "";
  state.data.presets.forEach((preset) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "preset-button";
    button.textContent = preset.label;
    button.addEventListener("click", () => {
      state.xMetric = preset.x;
      state.yMetric = preset.y;
      state.xScale = preset.x_scale || defaultScaleForMetric(preset.x);
      populateMetricSelect(elements.xAxis, state.xMetric);
      populateMetricSelect(elements.yAxis, state.yMetric);
      highlightActivePreset();
      render();
    });
    button.dataset.presetKey = preset.key;
    elements.presetStrip.appendChild(button);
  });
}

function highlightActivePreset() {
  const activePreset = state.data.presets.find(
    (preset) => preset.x === state.xMetric && preset.y === state.yMetric && (preset.x_scale || "linear") === state.xScale,
  );

  [...elements.presetStrip.children].forEach((button) => {
    button.classList.toggle("active", button.dataset.presetKey === activePreset?.key);
  });
}

function buildTierFilters() {
  elements.tierFilter.innerHTML = "";
  Object.entries(TIER_META).forEach(([tierKey, tier]) => {
    const label = document.createElement("label");
    label.className = "tier-chip";

    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = state.selectedTiers.has(tierKey);
    input.addEventListener("change", () => {
      if (input.checked) {
        state.selectedTiers.add(tierKey);
      } else {
        state.selectedTiers.delete(tierKey);
      }
      render();
    });

    const swatch = document.createElement("span");
    swatch.className = "swatch";
    swatch.style.backgroundColor = tier.color;

    const text = document.createElement("span");
    text.textContent = tier.label;

    label.append(input, swatch, text);
    elements.tierFilter.appendChild(label);
  });
}

function getFilteredModels() {
  const search = state.search.trim().toLowerCase();

  return state.data.models.filter((row) => {
    if (!state.selectedTiers.has(row.tier)) {
      return false;
    }
    if (state.completeOnly && row.incomplete) {
      return false;
    }
    if (search && !row.model.toLowerCase().includes(search)) {
      return false;
    }
    if (row[state.xMetric] === null || row[state.yMetric] === null) {
      return false;
    }
    if (state.xScale === "log" && row[state.xMetric] <= 0) {
      return false;
    }
    return true;
  });
}

function chartCompass(xMetric, yMetric) {
  const xWord = xMetric.direction === "lower" ? "lower" : "higher";
  const yWord = yMetric.direction === "lower" ? "lower" : "higher";
  const quadrantMap = {
    "lower-higher": "top-left",
    "higher-higher": "top-right",
    "lower-lower": "bottom-left",
    "higher-lower": "bottom-right",
  };

  return `${quadrantMap[`${xWord}-${yWord}`]} is best: ${xMetric.label.toLowerCase()} ${xWord}, ${yMetric.label.toLowerCase()} ${yWord}.`;
}

function renderChart(rows) {
  const xMetric = metricByKey(state.xMetric);
  const yMetric = metricByKey(state.yMetric);

  const traces = Object.entries(TIER_META).map(([tierKey, tier]) => {
    const tierRows = rows.filter((row) => row.tier === tierKey);
    return {
      type: "scatter",
      mode: state.showLabels ? "markers+text" : "markers",
      name: tier.label,
      x: tierRows.map((row) => row[state.xMetric]),
      y: tierRows.map((row) => row[state.yMetric]),
      text: tierRows.map((row) => row.model),
      customdata: tierRows.map((row) => [
        row.model,
        TIER_META[row.tier].label,
        row.rank_label ?? "–",
        formatValue(metricByKey("cw_pct"), row.cw_pct),
        formatValue(metricByKey("balanced_ots"), row.balanced_ots),
        formatValue(metricByKey("critical_miss"), row.critical_miss),
        formatValue(metricByKey("false_review"), row.false_review),
        formatValue(metricByKey("threat_capture"), row.threat_capture),
        formatValue(metricByKey("mae"), row.mae),
        row.n,
      ]),
      textposition: "top center",
      textfont: {
        family: "IBM Plex Sans, sans-serif",
        size: 11,
        color: "#b7efff",
      },
      hovertemplate:
        "<b>%{customdata[0]}</b><br>" +
        "%{customdata[1]}<br>" +
        "Rank: %{customdata[2]}<br>" +
        "CW: %{customdata[3]}<br>" +
        "Balanced OTS: %{customdata[4]}<br>" +
        "Critical miss: %{customdata[5]}<br>" +
        "False review: %{customdata[6]}<br>" +
        "Threat capture: %{customdata[7]}<br>" +
        "MAE: %{customdata[8]}<br>" +
        "Findings: %{customdata[9]}<extra></extra>",
      marker: {
        size: tierRows.map((row) => (row.incomplete ? 12 : 15)),
        color: tier.color,
        symbol: tier.symbol,
        opacity: 0.92,
        line: {
          color: "#020814",
          width: 1.3,
        },
      },
    };
  });

  const layout = {
    margin: { l: 64, r: 24, t: 24, b: 64 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(1, 10, 22, 0.88)",
    hoverlabel: {
      bgcolor: "#0f172a",
      bordercolor: "#41e8ff",
      align: "left",
      font: {
        family: "IBM Plex Sans, sans-serif",
        size: 12,
        color: "#f8fbff",
      },
    },
    font: {
      family: "IBM Plex Sans, sans-serif",
      color: "#d8f5ff",
    },
    xaxis: {
      title: { text: xMetric.label, font: { color: "#d8f5ff" } },
      type: state.xScale,
      gridcolor: "rgba(65, 232, 255, 0.14)",
      showline: true,
      linecolor: "rgba(65, 232, 255, 0.24)",
      tickfont: { color: "#9fc9dd" },
      zeroline: false,
    },
    yaxis: {
      title: { text: yMetric.label, font: { color: "#d8f5ff" } },
      gridcolor: "rgba(65, 232, 255, 0.14)",
      showline: true,
      linecolor: "rgba(65, 232, 255, 0.24)",
      tickfont: { color: "#9fc9dd" },
      zeroline: false,
    },
    legend: {
      x: 1,
      xanchor: "right",
      y: 1.02,
      orientation: "h",
      bgcolor: "rgba(3, 14, 28, 0.92)",
      bordercolor: "rgba(65, 232, 255, 0.2)",
      font: { color: "#d8f5ff" },
      borderwidth: 1,
    },
  };

  Plotly.react(elements.chart, traces, layout, {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d"],
  });

  elements.chartTitle.textContent = `${yMetric.label} vs ${xMetric.label}`;
  elements.chartSubtitle.textContent = chartCompass(xMetric, yMetric);
}

function renderTable(rows) {
  elements.tableBody.innerHTML = "";

  const sorted = [...rows].sort((a, b) => a.rank_sort - b.rank_sort || a.model.localeCompare(b.model));
  elements.tableSummary.textContent = `${sorted.length} models shown`;

  sorted.forEach((row) => {
    const tr = document.createElement("tr");
    const tierLabel = TIER_META[row.tier].label;
    const incompletePill = row.incomplete ? '<span class="incomplete-pill">Incomplete</span>' : "";
    tr.innerHTML = `
      <td>${row.rank_label ?? "–"}</td>
      <td><span class="model-name">${row.model}</span>${incompletePill}</td>
      <td>${tierLabel}</td>
      <td>${formatValue(metricByKey("balanced_ots"), row.balanced_ots)}</td>
      <td>${formatValue(metricByKey("critical_miss"), row.critical_miss)}</td>
      <td>${formatValue(metricByKey("false_review"), row.false_review)}</td>
      <td>${formatValue(metricByKey("cw_pct"), row.cw_pct)}</td>
      <td>${formatValue(metricByKey("threat_capture"), row.threat_capture)}</td>
    `;
    elements.tableBody.appendChild(tr);
  });
}

function render() {
  const rows = getFilteredModels();
  highlightActivePreset();
  renderChart(rows);
  renderTable(rows);
}

async function init() {
  const response = await fetch(DATA_URL);
  state.data = await response.json();
  state.metricsByKey = Object.fromEntries(state.data.metrics.map((metric) => [metric.key, metric]));

  const defaultPreset = state.data.presets[0];
  state.xMetric = defaultPreset.x;
  state.yMetric = defaultPreset.y;
  state.xScale = defaultPreset.x_scale || defaultScaleForMetric(defaultPreset.x);

  populateMetricSelect(elements.xAxis, state.xMetric);
  populateMetricSelect(elements.yAxis, state.yMetric);
  buildPresetButtons();
  buildTierFilters();
  highlightActivePreset();

  elements.xAxis.addEventListener("change", (event) => {
    state.xMetric = event.target.value;
    state.xScale = defaultScaleForMetric(state.xMetric);
    render();
  });

  elements.yAxis.addEventListener("change", (event) => {
    state.yMetric = event.target.value;
    render();
  });

  elements.modelSearch.addEventListener("input", (event) => {
    state.search = event.target.value;
    render();
  });

  elements.showLabels.addEventListener("change", (event) => {
    state.showLabels = event.target.checked;
    render();
  });

  elements.completeOnly.addEventListener("change", (event) => {
    state.completeOnly = event.target.checked;
    render();
  });

  render();
}

init().catch((error) => {
  elements.chartTitle.textContent = "Explorer failed to load";
  elements.chartSubtitle.textContent = error.message;
  console.error(error);
});
