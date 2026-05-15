const DATA_URL = "./data/leaderboard-explorer.json";

const TIER_META = {
  closed_source: {
    label: "Closed Source / Vendor API",
    color: "#ff9f43",
    symbol: "diamond",
    textSymbol: "◆",
  },
  open_source_pro: {
    label: "Open Source / Pro Hardware",
    color: "#3f87ff",
    symbol: "square",
    textSymbol: "■",
  },
  open_source_consumer: {
    label: "Open Source / Consumer Hardware",
    color: "#22c55e",
    symbol: "circle",
    textSymbol: "●",
  },
  baseline: {
    label: "Baseline",
    color: "#9ca9ba",
    symbol: "x",
    textSymbol: "✕",
  },
};

const LEADER_SCOPE_META = [
  { key: "overall", label: "Overall" },
  { key: "all_tiers", label: "All tiers" },
  { key: "closed_source", label: "Closed source" },
  { key: "open_source_pro", label: "Open source / pro" },
  { key: "open_source_consumer", label: "Open source / consumer" },
];

const TIER_ORDER = ["closed_source", "open_source_pro", "open_source_consumer"];
const VALID_TABS = new Set(["explorer", "leaders", "models", "charts"]);

const state = {
  data: null,
  metricsByKey: {},
  modelsByName: new Map(),
  xMetric: null,
  yMetric: null,
  xScale: "linear",
  search: "",
  showLabels: false,
  completeOnly: true,
  selectedTiers: new Set(Object.keys(TIER_META)),
  activeTab: "explorer",
  leaderScope: "overall",
  galleryKey: "operational-profile-summary",
  pinnedModels: new Set(),
  chartEventsBound: false,
};

const elements = {
  chart: document.getElementById("chart"),
  chartTitle: document.getElementById("chart-title"),
  chartSubtitle: document.getElementById("chart-subtitle"),
  pinnedSummary: document.getElementById("pinned-summary"),
  pinnedDetails: document.getElementById("pinned-details"),
  clearPins: document.getElementById("clear-pins"),
  presetStrip: document.getElementById("preset-strip"),
  xAxis: document.getElementById("x-axis"),
  yAxis: document.getElementById("y-axis"),
  modelSearchExplorer: document.getElementById("model-search"),
  modelSearchModels: document.getElementById("model-search-models"),
  showLabels: document.getElementById("show-labels"),
  completeOnlyExplorer: document.getElementById("complete-only"),
  completeOnlyModels: document.getElementById("complete-only-models"),
  tierFilterExplorer: document.getElementById("tier-filter"),
  tierFilterModels: document.getElementById("tier-filter-models"),
  tableBody: document.getElementById("table-body"),
  tableSummary: document.getElementById("table-summary"),
  tabButtons: [...document.querySelectorAll(".tab-button")],
  tabViews: [...document.querySelectorAll(".tab-view")],
  leaderScopeStrip: document.getElementById("leader-scope-strip"),
  leaderContent: document.getElementById("leader-content"),
  galleryStrip: document.getElementById("gallery-strip"),
  galleryImage: document.getElementById("gallery-image"),
  galleryTitle: document.getElementById("gallery-title"),
  galleryDescription: document.getElementById("gallery-description"),
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatValue(metric, value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "–";
  }

  switch (metric.format) {
    case "percent":
      return `${value.toFixed(1)}%`;
    case "seconds":
      return `${value.toFixed(2)}s`;
    case "currency_cents":
      return `${value.toFixed(2)}¢`;
    case "integer":
      return value.toLocaleString();
    default:
      return value.toFixed(1);
  }
}

function metricByKey(key) {
  return state.metricsByKey[key];
}

function presetByKey(key) {
  return state.data?.presets.find((preset) => preset.key === key) || null;
}

function selectedPreset() {
  return state.data?.presets.find((preset) => preset.x === state.xMetric && preset.y === state.yMetric) || null;
}

function defaultScaleForMetric(key) {
  return key === "avg_seconds_per_event" ? "log" : "linear";
}

function lookupModelByName(modelName) {
  return state.modelsByName.get(modelName) || null;
}

function applyPreset(preset) {
  state.xMetric = preset.x;
  state.yMetric = preset.y;
  state.xScale = preset.x_scale || defaultScaleForMetric(preset.x);
}

function syncMetricControls() {
  elements.xAxis.value = state.xMetric;
  elements.yAxis.value = state.yMetric;
}

function tierSymbolMarkup(tierKey) {
  const tier = TIER_META[tierKey];
  return `<span class="tier-symbol" style="color:${tier.color}">${tier.textSymbol}</span>`;
}

function modelNameMarkup(row, bold = false) {
  const modelName = escapeHtml(row.model);
  const modelText = bold ? `<b class="model-name">${modelName}</b>` : `<span class="model-name">${modelName}</span>`;
  return `${tierSymbolMarkup(row.tier)}${modelText}`;
}

function modelChipMarkup(row) {
  return `<span class="leader-model-chip">${modelNameMarkup(row)}</span>`;
}

function chartCardMetric(label, value) {
  return `
    <div class="pinned-metric">
      <dt>${escapeHtml(label)}</dt>
      <dd>${escapeHtml(value)}</dd>
    </div>
  `;
}

function syncFilterControls() {
  elements.modelSearchExplorer.value = state.search;
  elements.modelSearchModels.value = state.search;
  elements.completeOnlyExplorer.checked = state.completeOnly;
  elements.completeOnlyModels.checked = state.completeOnly;
  elements.showLabels.checked = state.showLabels;
}

function parseHashState() {
  const rawHash = window.location.hash.replace(/^#/, "");
  if (!rawHash) {
    return {};
  }

  const [tab, query = ""] = rawHash.split("?");
  const params = new URLSearchParams(query);
  return {
    tab,
    preset: params.get("preset"),
    x: params.get("x"),
    y: params.get("y"),
    scale: params.get("scale"),
    scope: params.get("scope"),
    chart: params.get("chart"),
  };
}

function applyHashState() {
  const hashState = parseHashState();

  if (hashState.tab && VALID_TABS.has(hashState.tab)) {
    state.activeTab = hashState.tab;
  }

  if (hashState.preset) {
    const preset = presetByKey(hashState.preset);
    if (preset) {
      applyPreset(preset);
    }
  } else if (hashState.x && hashState.y && metricByKey(hashState.x) && metricByKey(hashState.y)) {
    state.xMetric = hashState.x;
    state.yMetric = hashState.y;
    state.xScale = hashState.scale === "log" ? "log" : defaultScaleForMetric(hashState.x);
  }

  if (hashState.scope && LEADER_SCOPE_META.some((scope) => scope.key === hashState.scope)) {
    state.leaderScope = hashState.scope;
  }

  if (hashState.chart && state.data.chart_gallery.some((chart) => chart.key === hashState.chart)) {
    state.galleryKey = hashState.chart;
  }
}

function syncHashState() {
  if (!state.data) {
    return;
  }

  const params = new URLSearchParams();

  if (state.activeTab === "explorer") {
    const preset = selectedPreset();
    if (preset) {
      params.set("preset", preset.key);
    } else {
      params.set("x", state.xMetric);
      params.set("y", state.yMetric);
      if (state.xScale !== defaultScaleForMetric(state.xMetric)) {
        params.set("scale", state.xScale);
      }
    }
  } else if (state.activeTab === "leaders") {
    if (state.leaderScope !== LEADER_SCOPE_META[0].key) {
      params.set("scope", state.leaderScope);
    }
  } else if (state.activeTab === "charts") {
    const defaultChart = state.data.chart_gallery[0]?.key;
    if (state.galleryKey !== defaultChart) {
      params.set("chart", state.galleryKey);
    }
  }

  const nextHash = params.size ? `#${state.activeTab}?${params.toString()}` : `#${state.activeTab}`;
  if (window.location.hash !== nextHash) {
    window.history.replaceState(null, "", nextHash);
  }
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
  const activePresetKey = selectedPreset()?.key;
  state.data.presets.forEach((preset) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `preset-button${preset.key === activePresetKey ? " active" : ""}`;
    button.textContent = preset.label;
    button.dataset.presetKey = preset.key;
    button.addEventListener("click", () => {
      applyPreset(preset);
      render();
    });
    elements.presetStrip.appendChild(button);
  });
}

function buildTierFilters(container) {
  container.innerHTML = "";
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
    swatch.style.color = tier.color;

    const text = document.createElement("span");
    text.textContent = tier.label;

    label.append(input, swatch, text);
    container.appendChild(label);
  });
}

function buildLeaderScopeButtons() {
  elements.leaderScopeStrip.innerHTML = "";
  LEADER_SCOPE_META.forEach((scope) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `subtab-button${scope.key === state.leaderScope ? " is-active" : ""}`;
    button.textContent = scope.label;
    button.addEventListener("click", () => {
      state.leaderScope = scope.key;
      renderLeaderContent();
      buildLeaderScopeButtons();
    });
    elements.leaderScopeStrip.appendChild(button);
  });
}

function buildGalleryButtons() {
  elements.galleryStrip.innerHTML = "";
  state.data.chart_gallery.forEach((chart) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `subtab-button${chart.key === state.galleryKey ? " is-active" : ""}`;
    button.textContent = chart.title;
    button.addEventListener("click", () => {
      state.galleryKey = chart.key;
      renderGallery();
      buildGalleryButtons();
    });
    elements.galleryStrip.appendChild(button);
  });
}

function renderTabs() {
  elements.tabButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tab === state.activeTab);
  });
  elements.tabViews.forEach((view) => {
    view.classList.toggle("is-active", view.dataset.tabView === state.activeTab);
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

function bindChartEvents() {
  if (state.chartEventsBound || typeof elements.chart.on !== "function") {
    return;
  }

  elements.chart.on("plotly_click", (event) => {
    const modelName = event?.points?.[0]?.customdata?.[0];
    if (!modelName) {
      return;
    }

    if (state.pinnedModels.has(modelName)) {
      state.pinnedModels.delete(modelName);
    } else {
      state.pinnedModels.add(modelName);
    }

    render();
  });

  state.chartEventsBound = true;
}

function renderPinnedDetails(rows) {
  const visibleModels = new Map(rows.map((row) => [row.model, row]));
  const pinnedRows = [...state.pinnedModels].map((modelName) => visibleModels.get(modelName)).filter(Boolean);
  const hiddenPinCount = state.pinnedModels.size - pinnedRows.length;

  elements.clearPins.disabled = state.pinnedModels.size === 0;

  if (pinnedRows.length === 0) {
    elements.pinnedSummary.textContent = hiddenPinCount
      ? `${hiddenPinCount} pinned model${hiddenPinCount === 1 ? "" : "s"} hidden by the current filters or chart axes.`
      : "Click a chart symbol to pin its details here. Click it again to remove it.";
    elements.pinnedDetails.innerHTML = '<p class="pinned-empty">Pinned model cards will appear here for side-by-side comparison.</p>';
    return;
  }

  elements.pinnedSummary.textContent =
    `${pinnedRows.length} model${pinnedRows.length === 1 ? "" : "s"} pinned for comparison.` +
    (hiddenPinCount ? ` ${hiddenPinCount} more hidden by the current filters or chart axes.` : "");

  elements.pinnedDetails.innerHTML = pinnedRows
    .map((row) => {
      const model = lookupModelByName(row.model) || row;
      return `
        <article class="pinned-card">
          <div class="pinned-card-header">
            <span class="model-label">${modelNameMarkup(model, true)}</span>
            <span class="pinned-rank">Rank ${escapeHtml(row.rank_label ?? "–")}</span>
          </div>
          <dl class="pinned-metrics">
            ${chartCardMetric("Quality Score", formatValue(metricByKey("cw_pct"), row.cw_pct))}
            ${chartCardMetric("Balanced OTS", formatValue(metricByKey("balanced_ots"), row.balanced_ots))}
            ${chartCardMetric("Critical Miss", formatValue(metricByKey("critical_miss"), row.critical_miss))}
            ${chartCardMetric("False Review", formatValue(metricByKey("false_review"), row.false_review))}
            ${chartCardMetric("Threat Capture", formatValue(metricByKey("threat_capture"), row.threat_capture))}
            ${chartCardMetric("MAE", formatValue(metricByKey("mae"), row.mae))}
            ${chartCardMetric("Speed", formatValue(metricByKey("avg_seconds_per_event"), row.avg_seconds_per_event))}
            ${chartCardMetric("Run Cost", formatValue(metricByKey("estimated_run_cost_cents"), row.estimated_run_cost_cents))}
            ${chartCardMetric("Findings", String(row.n ?? "–"))}
            ${chartCardMetric("Tier", TIER_META[row.tier].label)}
          </dl>
        </article>
      `;
    })
    .join("");
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
      text: tierRows.map((row) => `${TIER_META[row.tier].textSymbol} ${row.model}`),
      customdata: tierRows.map((row) => [
        row.model,
        modelNameMarkup(row, true),
        TIER_META[row.tier].label,
        row.rank_label ?? "–",
        formatValue(metricByKey("cw_pct"), row.cw_pct),
        formatValue(metricByKey("balanced_ots"), row.balanced_ots),
        formatValue(metricByKey("critical_miss"), row.critical_miss),
        formatValue(metricByKey("false_review"), row.false_review),
        formatValue(metricByKey("threat_capture"), row.threat_capture),
        formatValue(metricByKey("mae"), row.mae),
        formatValue(metricByKey("avg_seconds_per_event"), row.avg_seconds_per_event),
        formatValue(metricByKey("estimated_run_cost_cents"), row.estimated_run_cost_cents),
        row.n,
      ]),
      textposition: "top center",
      textfont: {
        family: "IBM Plex Sans, sans-serif",
        size: 11,
        color: tier.color,
      },
      hovertemplate:
        "%{customdata[1]}<br>" +
        "%{customdata[2]}<br>" +
        "Rank: %{customdata[3]}<br>" +
        "Quality score: %{customdata[4]}<br>" +
        "Balanced OTS: %{customdata[5]}<br>" +
        "Critical miss: %{customdata[6]}<br>" +
        "False review: %{customdata[7]}<br>" +
        "Threat capture: %{customdata[8]}<br>" +
        "MAE: %{customdata[9]}<br>" +
        "Speed: %{customdata[10]}<br>" +
        "Run cost: %{customdata[11]}<br>" +
        "Findings: %{customdata[12]}<extra></extra>",
      marker: {
        size: tierRows.map((row) => {
          if (state.pinnedModels.has(row.model)) {
            return row.incomplete ? 18 : 22;
          }
          return row.incomplete ? 14 : 18;
        }),
        color: tier.color,
        symbol: tier.symbol,
        opacity: 0.92,
        line: {
          color: tierRows.map((row) => (state.pinnedModels.has(row.model) ? "#f8fbff" : "#020814")),
          width: tierRows.map((row) => (state.pinnedModels.has(row.model) ? 2.3 : 1.5)),
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
    clickmode: "event",
    hovermode: "closest",
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
  bindChartEvents();

  elements.chartTitle.textContent = `${yMetric.label} vs ${xMetric.label}`;
  elements.chartSubtitle.textContent = chartCompass(xMetric, yMetric);
}

function renderTable(rows) {
  elements.tableBody.innerHTML = "";

  const sorted = [...rows].sort((a, b) => a.rank_sort - b.rank_sort || a.model.localeCompare(b.model));
  elements.tableSummary.textContent = `${sorted.length} models shown with the current search and tier filters. Sorted by Quality Score (CW%) rank.`;

  sorted.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.rank_label ?? "–"}</td>
      <td><span class="model-label">${modelNameMarkup(row)}</span>${row.incomplete ? '<span class="incomplete-pill">Incomplete</span>' : ""}</td>
      <td>${TIER_META[row.tier].label}</td>
      <td>${formatValue(metricByKey("balanced_ots"), row.balanced_ots)}</td>
      <td>${formatValue(metricByKey("critical_miss"), row.critical_miss)}</td>
      <td>${formatValue(metricByKey("false_review"), row.false_review)}</td>
      <td class="sort-column-cell">${formatValue(metricByKey("cw_pct"), row.cw_pct)}</td>
      <td>${formatValue(metricByKey("threat_capture"), row.threat_capture)}</td>
    `;
    elements.tableBody.appendChild(tr);
  });
}

function renderLeaderTable(rows) {
  return `
    <div class="table-wrap">
      <table class="leader-table">
        <thead>
          <tr>
            <th>Use case</th>
            <th>Suggested model</th>
            <th>Why</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map((row) => {
              const model = lookupModelByName(row.model) || { model: row.model, tier: row.tier };
              return `
                <tr>
                  <td>${escapeHtml(row.use_case)}</td>
                  <td>${modelChipMarkup(model)}</td>
                  <td>${escapeHtml(row.reason)}</td>
                </tr>
              `;
            })
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderLeaderContent() {
  const leaderData = state.data.leaders;

  if (state.leaderScope === "overall") {
    elements.leaderContent.innerHTML = `
      <section class="leader-section">
        <h3>Current Result Summary - Overall</h3>
        <p class="leader-copy">
          The first table ignores deployment tier and shows the current profile leaders across all tested models.
          These are current profile leaders under the selected constraints, not universal winners.
          A model only appears as a recommendation if it also clears minimum usefulness and completeness guardrails.
        </p>
        ${renderLeaderTable(leaderData.overall)}
        <p class="leader-copy">
          There is no single best model. The useful choice depends on whether the deployment optimizes for
          missed-incident avoidance, balanced SOC triage, review-load reduction, cost, latency, data-control boundaries,
          or hardware constraints.
        </p>
      </section>
    `;
    return;
  }

  const renderTierSection = (tierKey) => `
    <section class="leader-section">
      <h3 class="leader-subheading">${leaderData.tier_labels[tierKey]}</h3>
      ${renderLeaderTable(leaderData.by_tier[tierKey] || [])}
    </section>
  `;

  if (state.leaderScope === "all_tiers") {
    elements.leaderContent.innerHTML = `
      <section class="leader-section">
        <h3>Current Result Summary by Model Tier</h3>
        <p class="leader-copy">
          Deployment constraints matter. A vendor API model may be easy to test, but some users need local execution,
          open-source weights, predictable cost, or consumer-hardware feasibility. The following tables show the
          current profile leaders within each model tier.
        </p>
        ${TIER_ORDER.map(renderTierSection).join("")}
      </section>
    `;
    return;
  }

  elements.leaderContent.innerHTML = `
    <section class="leader-section">
      <h3>${leaderData.tier_labels[state.leaderScope]}</h3>
      <p class="leader-copy">
        Current profile leaders within this deployment tier under the published operational constraints.
      </p>
      ${renderLeaderTable(leaderData.by_tier[state.leaderScope] || [])}
    </section>
  `;
}

function renderGallery() {
  const chart = state.data.chart_gallery.find((item) => item.key === state.galleryKey) || state.data.chart_gallery[0];
  elements.galleryImage.src = `./${chart.image_path}`;
  elements.galleryImage.alt = chart.title;
  elements.galleryTitle.textContent = chart.title;
  elements.galleryDescription.textContent = chart.description;
}

function render() {
  syncFilterControls();
  syncMetricControls();
  const filteredRows = getFilteredModels();
  renderTabs();
  buildPresetButtons();
  buildTierFilters(elements.tierFilterExplorer);
  buildTierFilters(elements.tierFilterModels);
  buildLeaderScopeButtons();
  buildGalleryButtons();
  renderChart(filteredRows);
  renderPinnedDetails(filteredRows);
  renderTable(state.data.models.filter((row) => {
    const search = state.search.trim().toLowerCase();
    if (!state.selectedTiers.has(row.tier)) {
      return false;
    }
    if (state.completeOnly && row.incomplete) {
      return false;
    }
    if (search && !row.model.toLowerCase().includes(search)) {
      return false;
    }
    return true;
  }));
  renderLeaderContent();
  renderGallery();
  syncHashState();
}

function bindEvents() {
  elements.tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.activeTab = button.dataset.tab;
      render();
    });
  });

  [elements.modelSearchExplorer, elements.modelSearchModels].forEach((input) => {
    input.addEventListener("input", (event) => {
      state.search = event.target.value;
      render();
    });
  });

  [elements.completeOnlyExplorer, elements.completeOnlyModels].forEach((checkbox) => {
    checkbox.addEventListener("change", (event) => {
      state.completeOnly = event.target.checked;
      render();
    });
  });

  elements.showLabels.addEventListener("change", (event) => {
    state.showLabels = event.target.checked;
    render();
  });

  elements.xAxis.addEventListener("change", (event) => {
    state.xMetric = event.target.value;
    state.xScale = defaultScaleForMetric(state.xMetric);
    render();
  });

  elements.yAxis.addEventListener("change", (event) => {
    state.yMetric = event.target.value;
    render();
  });

  elements.clearPins.addEventListener("click", () => {
    state.pinnedModels.clear();
    render();
  });
}

async function init() {
  const response = await fetch(DATA_URL);
  state.data = await response.json();
  state.metricsByKey = Object.fromEntries(state.data.metrics.map((metric) => [metric.key, metric]));
  state.modelsByName = new Map(state.data.models.map((row) => [row.model, row]));

  const defaultPreset = presetByKey("cw-vs-balanced-ots") || state.data.presets[0];
  applyPreset(defaultPreset);
  state.galleryKey = state.data.chart_gallery[0]?.key || state.galleryKey;

  populateMetricSelect(elements.xAxis, state.xMetric);
  populateMetricSelect(elements.yAxis, state.yMetric);
  applyHashState();
  bindEvents();
  render();
}

init().catch((error) => {
  elements.chartTitle.textContent = "Explorer failed to load";
  elements.chartSubtitle.textContent = error.message;
  console.error(error);
});
