/* m10 local front-end. It deliberately works without a chart CDN. */
(function () {
  "use strict";

  const state = { anomalies: [], alerts: [], runs: [], timeseries: [], latestRun: null, overview: null };
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));
  const apiBase = window.M10_API_BASE || "";

  async function api(path, options) {
    const response = await fetch(apiBase + path, options);
    const contentType = response.headers.get("content-type") || "";
    const body = contentType.includes("application/json") ? await response.json() : await response.text();
    if (!response.ok) {
      const message = body && typeof body === "object" ? body.detail || body.message : body;
      throw new Error(message || `服务返回 ${response.status}`);
    }
    return body;
  }

  function pick(obj, keys, fallback) {
    for (const key of keys) {
      if (obj && obj[key] !== undefined && obj[key] !== null) return obj[key];
    }
    return fallback;
  }

  function number(value, digits) {
    const n = Number(value);
    return Number.isFinite(n) ? n.toLocaleString("zh-CN", { maximumFractionDigits: digits || 0 }) : "—";
  }

  function dateText(value) {
    if (!value) return "—";
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleString("zh-CN", { hour12: false });
  }

  function setMessage(message, kind) {
    const target = $("#runMessage");
    target.textContent = message || "";
    target.className = `form-message ${kind || ""}`;
  }

  function nav() {
    $$(".nav-item").forEach((button) => button.addEventListener("click", () => {
      const section = button.dataset.section;
      $$(".nav-item").forEach((item) => item.classList.toggle("active", item === button));
      $$(".page-section").forEach((item) => item.classList.toggle("active", item.id === section));
      if (section === "curve") renderCurve();
    }));
  }

  function updateHealth(healthy, mode) {
    const badge = $("#modeBadge");
    const text = $("#healthText");
    badge.textContent = healthy ? (mode === "cluster" ? "集群模式" : "本地模式") : "服务不可用";
    badge.className = `badge ${healthy ? "badge-ok" : "badge-danger"}`;
    text.textContent = healthy ? "服务已连接" : "请先启动后端服务";
  }

  function renderOverview() {
    const overview = state.overview || {};
    const records = pick(overview, ["record_count", "records", "total_records", "total"], state.timeseries.length);
    const anomalyCount = pick(overview, ["anomaly_count", "anomalies", "total_anomalies"], state.anomalies.length);
    const alertCount = pick(overview, ["alert_count", "alerts", "pending_alerts"], state.alerts.length);
    const clusters = pick(overview, ["cluster_count", "clusters"], countClusters(state.timeseries));
    $("#metricRecords").textContent = number(records);
    $("#metricAnomalies").textContent = number(anomalyCount);
    $("#metricAlerts").textContent = number(alertCount);
    $("#metricClusters").textContent = clusters ? `${number(clusters)} 类` : "—";
    $("#metricAnomalyRate").textContent = records ? `${((Number(anomalyCount) / Number(records)) * 100).toFixed(1)}% 记录被标记` : "等待运行";
    $("#metricRunTime").textContent = state.latestRun ? `${number(pick(state.latestRun, ["duration_ms", "duration"], 0) / 1000, 1)} 秒完成` : "暂无运行";
    $("#latestRunTag").textContent = state.latestRun ? `运行 ${pick(state.latestRun, ["run_id", "id"], "—")}` : "未运行";
    renderLineChart($("#overviewChart"), state.timeseries, "power_kw", false);
    renderClusters($("#overviewClusters"), state.timeseries);
  }

  function countClusters(items) {
    return new Set(items.map((item) => pick(item, ["cluster_id", "cluster"], null)).filter((item) => item !== null)).size;
  }

  function normalizeSeries(items) {
    return (Array.isArray(items) ? items : []).map((item) => ({
      timestamp: pick(item, ["timestamp", "time", "ts"], ""),
      power_kw: Number(pick(item, ["power_kw", "power", "value"], 0)),
      irradiance_w_m2: Number(pick(item, ["irradiance_w_m2", "irradiance"], 0)),
      efficiency_proxy: Number(pick(item, ["efficiency_proxy", "efficiency"], 0)),
      cluster_id: pick(item, ["cluster_id", "cluster"], null),
      is_anomaly: Boolean(pick(item, ["is_anomaly", "anomaly", "is_outlier"], false)),
      station_id: pick(item, ["station_id", "station"], "—"),
    }));
  }

  function renderLineChart(svg, items, metric, large) {
    if (!svg) return;
    const points = normalizeSeries(items).filter((item) => Number.isFinite(item[metric]));
    const empty = large ? $("#curveEmpty") : $("#overviewEmpty");
    if (!points.length) {
      svg.innerHTML = "";
      if (empty) empty.classList.remove("hidden");
      return;
    }
    if (empty) empty.classList.add("hidden");
    const width = large ? 1100 : 900;
    const height = large ? 360 : 260;
    const pad = { left: 42, right: 18, top: 15, bottom: 31 };
    const values = points.map((item) => item[metric]);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    const x = (index) => pad.left + (index / Math.max(points.length - 1, 1)) * (width - pad.left - pad.right);
    const y = (value) => height - pad.bottom - ((value - min) / span) * (height - pad.top - pad.bottom);
    const path = points.map((point, index) => `${index ? "L" : "M"}${x(index).toFixed(2)},${y(point[metric]).toFixed(2)}`).join(" ");
    const area = `${path} L ${x(points.length - 1)},${height - pad.bottom} L ${x(0)},${height - pad.bottom} Z`;
    const grid = [0, .25, .5, .75, 1].map((ratio) => {
      const gy = pad.top + ratio * (height - pad.top - pad.bottom);
      const label = (max - ratio * span).toFixed(metric === "efficiency_proxy" ? 2 : 0);
      return `<line class="grid" x1="${pad.left}" x2="${width - pad.right}" y1="${gy}" y2="${gy}"/><text class="axis-text" x="3" y="${gy + 4}">${label}</text>`;
    }).join("");
    const anomalyDots = points.map((point, index) => point.is_anomaly ? `<circle class="point" cx="${x(index)}" cy="${y(point[metric])}" r="4"/>` : "").join("");
    svg.innerHTML = `<defs><linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#80c5ae" stop-opacity=".34"/><stop offset="1" stop-color="#80c5ae" stop-opacity="0"/></linearGradient></defs>${grid}<path class="area" d="${area}"/><path class="line" d="${path}"/>${anomalyDots}<text class="axis-text" x="${pad.left}" y="${height - 6}">${dateText(points[0].timestamp)}</text><text class="axis-text" text-anchor="end" x="${width - pad.right}" y="${height - 6}">${dateText(points[points.length - 1].timestamp)}</text>`;
  }

  function renderClusters(target, items) {
    const values = normalizeSeries(items).reduce((map, item) => {
      const key = item.cluster_id === null ? "未分组" : `工况 ${item.cluster_id}`;
      map[key] = (map[key] || 0) + 1;
      return map;
    }, {});
    const entries = Object.entries(values);
    if (!entries.length) { target.innerHTML = '<div class="empty-state">暂无工况数据</div>'; return; }
    const max = Math.max(...entries.map(([, value]) => value));
    target.innerHTML = entries.slice(0, 8).map(([label, value]) => `<div class="cluster-bar"><span class="cluster-bar-label">${escapeHtml(label)}</span><div class="cluster-bar-track"><div class="cluster-bar-fill" style="width:${(value / max) * 100}%"></div></div><span class="cluster-bar-value">${number(value)}</span></div>`).join("");
  }

  function renderCurve() {
    const metric = $("#curveMetric").value;
    const titles = { power_kw: "发电功率趋势", irradiance_w_m2: "辐照度趋势", efficiency_proxy: "效率代理值趋势" };
    $("#curveTitle").textContent = titles[metric] || "时序趋势";
    $("#curveSubtitle").textContent = state.latestRun ? `运行 ${pick(state.latestRun, ["run_id", "id"], "—")} · 异常点以红圈标注` : "选择一次运行后查看完整曲线。";
    renderLineChart($("#curveChart"), state.timeseries, metric, true);
  }

  function renderAnomalies() {
    const query = ($("#anomalySearch").value || "").toLowerCase();
    const severity = $("#severityFilter").value;
    const rows = state.anomalies.filter((item) => {
      const text = `${pick(item, ["timestamp", "time"], "")} ${pick(item, ["station_id", "station"], "")}`.toLowerCase();
      return (!query || text.includes(query)) && (!severity || pick(item, ["severity", "level"], "low") === severity);
    });
    $("#anomalyCount").textContent = `${rows.length} 条记录`;
    $("#anomalyTable").innerHTML = rows.length ? rows.map((item) => {
      const level = pick(item, ["severity", "level"], "low");
      return `<tr><td>${escapeHtml(dateText(pick(item, ["timestamp", "time"], "")))}</td><td>${escapeHtml(pick(item, ["station_id", "station"], "—"))}</td><td>${escapeHtml(String(pick(item, ["cluster_id", "cluster"], "—")))}</td><td>${number(pick(item, ["power_kw", "power"], null), 2)}</td><td>${number(pick(item, ["efficiency_proxy", "efficiency"], null), 4)}</td><td>${number(pick(item, ["anomaly_score", "score"], null), 4)}</td><td><span class="severity severity-${level}">${level === "high" ? "高" : level === "medium" ? "中" : "低"}</span></td></tr>`;
    }).join("") : '<tr><td colspan="7" class="table-empty">没有符合条件的异常记录</td></tr>';
  }

  function renderAlerts() {
    const levels = state.alerts.reduce((map, item) => { const level = pick(item, ["severity", "level"], "low"); map[level] = (map[level] || 0) + 1; return map; }, {});
    $("#alertHigh").textContent = number(levels.high || 0);
    $("#alertMedium").textContent = number(levels.medium || 0);
    $("#alertHandled").textContent = number(state.alerts.filter((item) => pick(item, ["status"], "open") === "handled").length);
    $("#alertList").innerHTML = state.alerts.length ? state.alerts.map((item) => {
      const level = pick(item, ["severity", "level"], "low");
      return `<div class="alert-item ${level}"><div class="alert-main"><strong>${escapeHtml(pick(item, ["title", "message"], "检测到异常工况"))}</strong><p>${escapeHtml(pick(item, ["detail", "description"], "请查看异常记录并结合现场情况复核。"))}</p></div><span class="alert-time">${escapeHtml(dateText(pick(item, ["created_at", "timestamp", "time"], "")))}</span></div>`;
    }).join("") : '<div class="empty-panel">暂无告警。完成一次处理运行后，异常记录会按等级生成告警。</div>';
  }

  function renderRuns() {
    $("#runsTable").innerHTML = state.runs.length ? state.runs.map((item) => `<tr><td>${escapeHtml(String(pick(item, ["run_id", "id"], "—")))}</td><td>${escapeHtml(dateText(pick(item, ["created_at", "created"], "")))}</td><td>${escapeHtml(pick(item, ["mode", "runtime_mode"], "local"))}</td><td>${number(pick(item, ["record_count", "records"], null))}</td><td>${number(pick(item, ["anomaly_count", "anomalies"], null))}</td><td>${number(Number(pick(item, ["duration_ms", "duration"], 0)) / 1000, 1)} 秒</td><td><span class="severity severity-${pick(item, ["status"], "low") === "success" ? "low" : "medium"}">${escapeHtml(pick(item, ["status"], "未知"))}</span></td></tr>`).join("") : '<tr><td colspan="7" class="table-empty">暂无运行记录</td></tr>';
  }

  function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char])); }

  async function loadData() {
    try {
      const health = await api("/api/health");
      const runs = await api("/api/runs");
      updateHealth(true, pick(health, ["mode", "runtime_mode"], "local"));
      state.runs = Array.isArray(runs) ? runs : pick(runs, ["items", "data"], []);
      state.latestRun = state.runs[0] || null;
      state.overview = {};
      state.timeseries = [];
      state.anomalies = [];
      state.alerts = [];
      if (state.latestRun) {
        const runId = pick(state.latestRun, ["id", "run_id"], null);
        const [runOverview, runRecords, runAlerts] = await Promise.all([
          api(`/api/runs/${runId}/overview`),
          api(`/api/runs/${runId}/records`),
          api(`/api/runs/${runId}/alerts`),
        ]);
        state.overview = pick(runOverview, ["metrics"], runOverview) || {};
        state.timeseries = Array.isArray(runRecords) ? runRecords : pick(runRecords, ["items", "data"], []);
        state.anomalies = state.timeseries.filter((item) => Boolean(pick(item, ["is_anomaly", "anomaly"], false)));
        state.alerts = Array.isArray(runAlerts) ? runAlerts : pick(runAlerts, ["items", "data"], []);
      }
      renderOverview(); renderCurve(); renderAnomalies(); renderAlerts(); renderRuns();
    } catch (error) {
      updateHealth(false, "local");
      $("#dataNotice").innerHTML = `<strong>服务尚未连接</strong><span>${escapeHtml(error.message)}。可以先查看“导入与运行”页面的说明。</span>`;
    }
  }

  function updateProgress(step, status, message) {
    const items = $$(".progress-item");
    items.forEach((item, index) => {
      item.classList.remove("active", "done", "failed", "pending");
      if (index < step) item.classList.add("done"); else if (index === step) item.classList.add(status === "failed" ? "failed" : "active"); else item.classList.add("pending");
    });
    if (items[step]) items[step].querySelector("small").textContent = message || (status === "done" ? "已完成" : "处理中…");
  }

  async function submitRun(event) {
    event.preventDefault();
    const file = $("#csvFile").files[0];
    const useDemo = $("#useDemo").checked;
    const useReal = $("#useReal").checked;
    if (!file && !useDemo && !useReal) { setMessage("请选择 CSV 文件，或勾选演示数据/真实 PVDAQ 数据。", "error"); return; }
    const button = $("#runButton"); button.disabled = true; button.textContent = "处理中…"; setMessage("正在提交处理任务…", ""); updateProgress(0, "active", "正在提交");
    try {
      let selectedFile = file;
      if (!selectedFile && (useDemo || useReal)) {
        const dataPath = useReal ? "/data/real/pvdaq_2107_2022-06_normalized.csv" : "/data/sample/pv_demo.csv";
        const dataResponse = await fetch(dataPath);
        if (!dataResponse.ok) throw new Error(useReal ? "无法读取项目内 PVDAQ 真实数据切片，请手动选择 CSV 文件。" : "无法读取项目内演示数据，请手动选择 CSV 文件。");
        selectedFile = new File([await dataResponse.blob()], useReal ? "pvdaq_2107_2022-06_normalized.csv" : "pv_demo.csv", { type: "text/csv" });
      }
      const form = new FormData(); form.append("file", selectedFile);
      const importResult = await api(`/api/datasets/import?synthetic_demo=${useDemo ? "true" : "false"}`, { method: "POST", body: form });
      updateProgress(1, "active", "清洗与特征计算");
      const response = await api("/api/runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ dataset_id: Number(pick(importResult, ["id", "dataset_id"], 0)), mode: $("#runMode").value, k: Number($("#clusterK").value), contamination: Number($("#contamination").value) }) });
      updateProgress(2, "active", "工况聚类"); await new Promise((resolve) => setTimeout(resolve, 180)); updateProgress(3, "active", "异常检测与告警"); await new Promise((resolve) => setTimeout(resolve, 180));
      updateProgress(4, "done", "处理完成"); setMessage("处理完成，正在刷新结果。", "ok"); await loadData(); $("#runSummary").innerHTML = `<span class="summary-icon">✓</span><div><strong>本次运行已完成</strong><p>运行编号：${escapeHtml(pick(response, ["run_id", "id"], "—"))}</p></div>`;
    } catch (error) { updateProgress(0, "failed", error.message); setMessage(error.message, "error"); $("#runSummary").innerHTML = `<span class="summary-icon">!</span><div><strong>处理未完成</strong><p>请查看错误信息后修正输入再试。</p></div>`; }
    finally { button.disabled = false; button.textContent = "开始处理"; }
  }

  function downloadAnomalies() {
    const header = ["timestamp", "station_id", "cluster_id", "power_kw", "efficiency_proxy", "anomaly_score", "severity"];
    const rows = state.anomalies.map((item) => header.map((key) => JSON.stringify(pick(item, [key], ""))).join(","));
    const blob = new Blob(["\ufeff" + [header.join(","), ...rows].join("\n")], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "m10-anomalies.csv"; link.click(); URL.revokeObjectURL(link.href);
  }

  function wire() {
    nav();
    const hashSection = window.location.hash.replace(/^#/, "");
    if (hashSection && document.getElementById(hashSection)) {
      const target = document.querySelector(`.nav-item[data-section="${hashSection}"]`);
      if (target) target.click();
    }
    $("#refreshButton").addEventListener("click", loadData); $("#refreshAlerts").addEventListener("click", loadData); $("#refreshRuns").addEventListener("click", loadData); $("#runForm").addEventListener("submit", submitRun); $("#exportAnomalies").addEventListener("click", downloadAnomalies); $("#anomalySearch").addEventListener("input", renderAnomalies); $("#severityFilter").addEventListener("change", renderAnomalies); $("#curveMetric").addEventListener("change", renderCurve); $("#csvFile").addEventListener("change", () => { $("#fileName").textContent = $("#csvFile").files[0]?.name || "选择 CSV 数据文件"; }); loadData();
  }
  document.addEventListener("DOMContentLoaded", wire);
})();
