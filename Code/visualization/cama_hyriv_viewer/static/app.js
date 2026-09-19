const $ = (id) => document.getElementById(id);
const state = {
  features: [], reaches: new Map(), points: [], featureById: new Map(),
  network: [], networkById: new Map(), networkBounds: null,
  selectedId: null, detail: null, selectedCatchment: null,
  centerLon: 105, centerLat: 35, scale: 10, width: 0, height: 0,
  pointer: null, dragged: false, renderQueued: false,
};
const canvas = $("map-canvas");
const ctx = canvas.getContext("2d");
const hitCanvas = document.createElement("canvas");
const hitCtx = hitCanvas.getContext("2d", { willReadFrequently: true });
const jrcImage = new Image();
jrcImage.src = "/api/jrc.png";
jrcImage.onload = queueRender;
const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const colors = ["#137b69", "#c46939", "#6d69a7", "#397ea9"];

function statusColor(reach) {
  if (reach.jrc_evidence === "no_water_cells" || reach.jrc_evidence === "outside_raster") return "#8f9293";
  return reach.jrc_status === 2 ? "#118069" : "#d34f45";
}
function pointColor(point) {
  if (point.jrc_evidence === "outside_raster" || point.jrc_status == null) return "#8f9293";
  return point.jrc_status === 2 ? "#118069" : "#d34f45";
}
function statusText(reach) {
  if (reach.jrc_evidence === "outside_raster") return "Outside JRC raster";
  if (reach.jrc_evidence === "no_water_cells") return "Non-perennial / no JRC water cells";
  return reach.jrc_status === 2 ? "Perennial" : "Non-perennial";
}
function matchText(value) {
  return ({ candidate: "Distance candidate", topology_resolved: "Topology resolved", ambiguous: "Ambiguous" })[value] || value;
}
function format(value, digits = 2) {
  return value == null ? "-" : Number(value).toLocaleString("en-US", { maximumFractionDigits: digits });
}
function linesOf(feature) {
  if (Array.isArray(feature)) return feature[3];
  const geom = feature.geometry;
  if (geom.type === "LineString") return [geom.coordinates];
  if (geom.type === "MultiLineString") return geom.coordinates;
  return [];
}
function boundsOf(feature) {
  let west = Infinity, south = Infinity, east = -Infinity, north = -Infinity;
  for (const line of linesOf(feature)) for (const [lon, lat] of line) {
    west = Math.min(west, lon); east = Math.max(east, lon);
    south = Math.min(south, lat); north = Math.max(north, lat);
  }
  return { west, south, east, north };
}
function toScreen(lon, lat) {
  return [state.width / 2 + (lon - state.centerLon) * state.scale,
          state.height / 2 - (lat - state.centerLat) * state.scale];
}
function toGeo(x, y) {
  return [state.centerLon + (x - state.width / 2) / state.scale,
          state.centerLat - (y - state.height / 2) / state.scale];
}
function visible(bounds, viewport) {
  return bounds.east >= viewport.west && bounds.west <= viewport.east &&
         bounds.north >= viewport.south && bounds.south <= viewport.north;
}
function drawFeature(context, feature) {
  context.beginPath();
  for (const line of linesOf(feature)) {
    if (!line.length) continue;
    const [x0, y0] = toScreen(...line[0]);
    context.moveTo(x0, y0);
    for (let i = 1; i < line.length; i++) {
      const [x, y] = toScreen(...line[i]);
      context.lineTo(x, y);
    }
  }
  context.stroke();
}
function idColor(id) {
  return `rgb(${id & 255},${(id >> 8) & 255},${(id >> 16) & 255})`;
}
function colorId(data) {
  return data[0] + data[1] * 256 + data[2] * 65536;
}
function drawGrid() {
  const step = state.scale < 15 ? 10 : state.scale < 40 ? 5 : state.scale < 130 ? 1 : 0.2;
  ctx.strokeStyle = "rgba(63,82,82,.12)";
  ctx.fillStyle = "#6b7777";
  ctx.font = "11px system-ui";
  ctx.lineWidth = 1;
  const [left, top] = toGeo(0, 0);
  const [right, bottom] = toGeo(state.width, state.height);
  for (let lon = Math.ceil(left / step) * step; lon <= right; lon += step) {
    const x = toScreen(lon, 0)[0];
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, state.height); ctx.stroke();
    ctx.fillText(`${Math.round(lon * 10) / 10}°E`, x + 4, state.height - 10);
  }
  for (let lat = Math.ceil(bottom / step) * step; lat <= top; lat += step) {
    const y = toScreen(0, lat)[1];
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(state.width, y); ctx.stroke();
    ctx.fillText(`${Math.round(lat * 10) / 10}°N`, 8, y - 5);
  }
}
function render() {
  state.renderQueued = false;
  if (!state.width || !state.height) return;
  ctx.clearRect(0, 0, state.width, state.height);
  ctx.fillStyle = "#f4f7f7";
  ctx.fillRect(0, 0, state.width, state.height);
  hitCtx.clearRect(0, 0, state.width, state.height);
  if ($("layer-jrc").checked && jrcImage.complete && jrcImage.naturalWidth) {
    const [x, y] = toScreen(70, 60);
    ctx.globalAlpha = 0.46;
    ctx.drawImage(jrcImage, x, y, 70.0095 * state.scale, 50.00325 * state.scale);
    ctx.globalAlpha = 1;
  }
  drawGrid();
  const [west, north] = toGeo(0, 0);
  const [east, south] = toGeo(state.width, state.height);
  const viewport = { west, north, east, south };
  if ($("layer-network").checked) {
    for (let i = 0; i < state.network.length; i++) {
      const river = state.network[i];
      if (!visible(river._bounds, viewport)) continue;
      const selected = state.selectedId === river[0];
      ctx.strokeStyle = selected && !state.reaches.has(river[0]) ? "#334c46" : "#829891";
      ctx.globalAlpha = selected ? 1 : 0.72;
      ctx.lineWidth = selected ? 3 : state.scale < 20 ? 0.85 : 1.2;
      drawFeature(ctx, river);
      if (state.scale >= 18) {
        hitCtx.strokeStyle = idColor(i + 1);
        hitCtx.lineWidth = 5;
        drawFeature(hitCtx, river);
      }
    }
    ctx.globalAlpha = 1;
  }
  if ($("layer-reaches").checked) {
    const offset = state.network.length + 1;
    for (let i = 0; i < state.features.length; i++) {
      const feature = state.features[i];
      if (!visible(feature._bounds, viewport)) continue;
      const reach = state.reaches.get(feature.properties.HYRIV_ID);
      if (!reach) continue;
      ctx.strokeStyle = statusColor(reach);
      ctx.globalAlpha = state.selectedId === reach.hyriv_id ? 1 : 0.78;
      ctx.lineWidth = state.selectedId === reach.hyriv_id ? 3 : 1.2;
      drawFeature(ctx, feature);
      hitCtx.strokeStyle = idColor(offset + i);
      hitCtx.lineWidth = 8;
      drawFeature(hitCtx, feature);
    }
    ctx.globalAlpha = 1;
  }
  if ($("layer-points").checked) {
    const offset = state.network.length + state.features.length + 1;
    const denseView = state.scale < 22;
    state.points.forEach((point, i) => {
      const [x, y] = toScreen(point.longitude, point.latitude);
      if (x < -8 || y < -8 || x > state.width + 8 || y > state.height + 8) return;
      const selected = point.hyriv_id === state.selectedId;
      ctx.beginPath(); ctx.arc(x, y, selected ? 4.4 : denseView ? 1.5 : 2.6, 0, 2 * Math.PI);
      ctx.fillStyle = pointColor(point);
      ctx.fill();
      ctx.lineWidth = selected ? 1.7 : denseView ? 0.6 : 1;
      ctx.strokeStyle = "#ffffff";
      ctx.stroke();
      hitCtx.beginPath(); hitCtx.arc(x, y, denseView ? 4 : 7, 0, 2 * Math.PI);
      hitCtx.fillStyle = idColor(offset + i); hitCtx.fill();
    });
  }
}
function queueRender() {
  if (state.renderQueued) return;
  state.renderQueued = true;
  requestAnimationFrame(render);
}
function resize() {
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const first = state.width === 0;
  state.width = rect.width; state.height = rect.height;
  for (const target of [canvas, hitCanvas]) {
    target.width = Math.round(rect.width * dpr);
    target.height = Math.round(rect.height * dpr);
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  hitCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
  if (first) fitAll(); else queueRender();
}
function fitAll() {
  const bounds = state.networkBounds || [70, 9.99675, 140.0095, 60];
  state.centerLon = (bounds[0] + bounds[2]) / 2;
  state.centerLat = (bounds[1] + bounds[3]) / 2;
  state.scale = Math.min(state.width / (bounds[2] - bounds[0]),
                         state.height / (bounds[3] - bounds[1])) * 0.96;
  queueRender();
}
function zoomAt(factor, x = state.width / 2, y = state.height / 2) {
  const [lon, lat] = toGeo(x, y);
  state.scale = Math.max(2, Math.min(3500, state.scale * factor));
  state.centerLon = lon - (x - state.width / 2) / state.scale;
  state.centerLat = lat + (y - state.height / 2) / state.scale;
  queueRender();
}
function jumpTo(id) {
  const features = state.featureById.get(id) || (state.networkById.has(id) ? [state.networkById.get(id)] : null);
  if (!features) return;
  const bounds = features.reduce((acc, feature) => ({
    west: Math.min(acc.west, feature._bounds.west),
    south: Math.min(acc.south, feature._bounds.south),
    east: Math.max(acc.east, feature._bounds.east),
    north: Math.max(acc.north, feature._bounds.north),
  }), { west: Infinity, south: Infinity, east: -Infinity, north: -Infinity });
  state.centerLon = (bounds.west + bounds.east) / 2;
  state.centerLat = (bounds.south + bounds.north) / 2;
  state.scale = Math.min(state.width / Math.max(bounds.east - bounds.west, 0.65),
                         state.height / Math.max(bounds.north - bounds.south, 0.5)) * 0.62;
  state.scale = Math.min(state.scale, 950);
  queueRender();
}
function hitAt(x, y) {
  const dpr = hitCanvas.width / state.width;
  const pixel = hitCtx.getImageData(Math.floor(x * dpr), Math.floor(y * dpr), 1, 1).data;
  const index = colorId(pixel);
  if (index > 0 && index <= state.network.length) {
    const river = state.network[index - 1];
    return { hyriv_id: river[0], kind: "network" };
  }
  const reachIndex = index - state.network.length - 1;
  if (reachIndex >= 0 && reachIndex < state.features.length) {
    const feature = state.features[reachIndex];
    return { hyriv_id: feature.properties.HYRIV_ID, kind: "reach" };
  }
  const pointIndex = index - state.network.length - state.features.length - 1;
  if (pointIndex >= 0 && pointIndex < state.points.length) {
    const point = state.points[pointIndex];
    return { hyriv_id: point.hyriv_id, kind: "point", catchment_id: point.catchment_id };
  }
  return null;
}
function fact(label, value) {
  return `<div><span>${label}</span><strong>${value}</strong></div>`;
}
function renderUnmatched(river) {
  $("reach-id").textContent = number.format(river[0]);
  $("reach-status").innerHTML = '<span class="status-pill no-water">No CaMa match</span><span>JRC reach status not classified</span>';
  $("reach-facts").innerHTML =
    fact("HydroRIVERS discharge", `${format(river[1], 3)} m³/s`) +
    fact("Next downstream reach", river[2] ? format(river[2], 0) : "-") +
    fact("CaMa catchments", "0") +
    fact("JRC reach status", "Not classified");
  $("download-link").hidden = true;
  $("catchment-count").textContent = "0 catchments";
  $("catchment-table").querySelector("tbody").innerHTML = '<tr><td colspan="4">No assigned CaMa catchment</td></tr>';
  $("selected-catchment").textContent = "No monthly flow";
  $("monthly-table").querySelector("tbody").innerHTML = "";
  $("flow-chart").replaceChildren();
  $("chart-legend").replaceChildren();
}
function renderDetail(data) {
  const reach = data.reach;
  $("reach-id").textContent = number.format(reach.hyriv_id);
  $("reach-status").innerHTML = `<span class="status-pill ${reach.jrc_evidence === "water_cells" ? (reach.jrc_status === 2 ? "perennial" : "intermittent") : "no-water"}">${statusText(reach)}</span><span>${reach.jrc_label.replaceAll("_", " ")}</span>`;
  $("reach-facts").innerHTML =
    fact("CaMa catchments", format(reach.catchment_count, 0)) +
    fact("Next downstream reach", reach.next_down ? format(reach.next_down, 0) : "-") +
    fact("HydroRIVERS discharge", `${format(reach.dis_av_cms, 3)} m³/s`) +
    fact("JRC perennial cells", format(reach.perennial_count, 0)) +
    fact("JRC intermittent cells", format(reach.intermittent_count, 0)) +
    fact("Perennial cell ratio", reach.perennial_ratio == null ? "-" : `${format(reach.perennial_ratio * 100, 1)}%`);
  $("catchment-count").textContent = `${data.catchments.length} catchments`;
  $("download-link").hidden = false;
  $("download-link").href = `/api/reach/${reach.hyriv_id}/csv`;
  const body = $("catchment-table").querySelector("tbody");
  body.innerHTML = "";
  data.catchments.forEach((point) => {
    const row = document.createElement("tr");
    row.tabIndex = 0;
    row.dataset.catchmentId = point.catchment_id;
    row.innerHTML = `<td>${format(point.catchment_id, 0)}</td><td>${format(point.downstream_id, 0)}</td><td>${matchText(point.match_status)}</td><td>${format(point.match_distance_m / 1000, 2)} km</td>`;
    row.addEventListener("click", () => selectCatchment(point.catchment_id));
    row.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectCatchment(point.catchment_id); }
    });
    body.appendChild(row);
  });
  if (!data.catchments.some((point) => point.catchment_id === state.selectedCatchment)) {
    state.selectedCatchment = data.catchments[0]?.catchment_id ?? null;
  }
  selectCatchment(state.selectedCatchment);
}
async function selectReach(id, jump = false, catchmentId = null) {
  if (!state.reaches.has(id) && !state.networkById.has(id)) {
    $("hydro-search").setCustomValidity("Hydro ID not found in displayed layers");
    $("hydro-search").reportValidity();
    return;
  }
  $("hydro-search").setCustomValidity("");
  if (!state.reaches.has(id)) {
    state.detail = null;
    state.selectedId = id;
    state.selectedCatchment = null;
    $("hydro-search").value = id;
    renderUnmatched(state.networkById.get(id));
    if (jump) jumpTo(id); else queueRender();
    return;
  }
  const response = await fetch(`/api/reach/${id}`);
  if (!response.ok) throw new Error(`Could not load reach ${id}`);
  state.detail = await response.json();
  state.selectedId = id;
  state.selectedCatchment = catchmentId;
  $("hydro-search").value = id;
  renderDetail(state.detail);
  if (jump) jumpTo(id); else queueRender();
}
function selectCatchment(id) {
  state.selectedCatchment = id;
  document.querySelectorAll("#catchment-table tbody tr").forEach((row) => {
    row.classList.toggle("selected", Number(row.dataset.catchmentId) === id);
  });
  $("selected-catchment").textContent = id ? `Catchment ${number.format(id)} | m³/s` : "";
  const rows = (state.detail?.months || []).filter((row) => row.catchment_id === id);
  $("monthly-table").querySelector("tbody").innerHTML = rows.map((row) =>
    `<tr><td>${row.month}</td><td>${format(row.min_flow_cms, 3)}</td><td>${format(row.q25_flow_cms, 3)}</td><td>${format(row.median_flow_cms, 3)}</td><td>${format(row.mean_flow_cms, 3)}</td><td>${format(row.q75_flow_cms, 3)}</td><td>${format(row.max_flow_cms, 3)}</td><td>${format(row.mode_flow_cms, 3)}</td></tr>`
  ).join("");
  renderChart();
}
function svgElement(tag, attrs = {}, content = null) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (content != null) node.textContent = content;
  return node;
}
function renderChart() {
  const svg = $("flow-chart");
  svg.replaceChildren();
  svg.setAttribute("viewBox", "0 0 520 245");
  const data = state.detail;
  if (!data) return;
  const metric = $("metric-select").value;
  const valid = data.months.map((row) => row[metric]).filter((value) => value != null);
  const max = Math.max(...valid, 1);
  const yTop = max * 1.08;
  const xPos = (month) => 46 + (month - 1) * 40;
  const yPos = (value) => 194 - (value / yTop) * 162;
  for (let tick = 0; tick <= 4; tick++) {
    const value = yTop * tick / 4;
    const y = yPos(value);
    svg.appendChild(svgElement("line", { x1: 46, y1: y, x2: 491, y2: y, stroke: "#e3e9e7" }));
    svg.appendChild(svgElement("text", { x: 39, y: y + 4, "text-anchor": "end", class: "axis-label" }, format(value, 1)));
  }
  for (let month = 1; month <= 12; month++) {
    svg.appendChild(svgElement("text", { x: xPos(month), y: 219, "text-anchor": "middle", class: "axis-label" }, month));
  }
  svg.appendChild(svgElement("text", { x: 491, y: 236, "text-anchor": "end", class: "axis-label" }, "Month"));
  const legend = $("chart-legend");
  legend.replaceChildren();
  data.catchments.forEach((point, index) => {
    const rows = data.months.filter((row) => row.catchment_id === point.catchment_id && row[metric] != null);
    const color = colors[index % colors.length];
    const selected = point.catchment_id === state.selectedCatchment;
    const path = rows.map((row, i) => `${i ? "L" : "M"}${xPos(row.month)},${yPos(row[metric])}`).join(" ");
    svg.appendChild(svgElement("path", { d: path, fill: "none", stroke: color,
      "stroke-width": selected ? 3.2 : 1.7, opacity: selected ? 1 : 0.68,
      "stroke-linecap": "round", "stroke-linejoin": "round" }));
    if (selected) rows.forEach((row) => {
      const circle = svgElement("circle", { cx: xPos(row.month), cy: yPos(row[metric]), r: 3.5, fill: color });
      circle.appendChild(svgElement("title", {}, `Month ${row.month}: ${format(row[metric], 3)} m³/s`));
      svg.appendChild(circle);
    });
    const item = document.createElement("button");
    item.type = "button";
    item.className = selected ? "chart-key active" : "chart-key";
    item.innerHTML = `<span style="background:${color}"></span>${number.format(point.catchment_id)}`;
    item.addEventListener("click", () => selectCatchment(point.catchment_id));
    legend.appendChild(item);
  });
}
async function init() {
  resize();
  try {
    const [overviewResponse, geometryResponse, networkResponse] = await Promise.all([
      fetch("/api/overview"), fetch("/api/geometry"), fetch("/api/network"),
    ]);
    if (!overviewResponse.ok || !geometryResponse.ok || !networkResponse.ok) throw new Error("Could not load map data");
    const overview = await overviewResponse.json();
    if (overview.points.some((point) => point.jrc_status == null && point.jrc_evidence !== "outside_raster")) {
      throw new Error("Viewer API is outdated; restart the server");
    }
    const geometry = await geometryResponse.json();
    const network = await networkResponse.json();
    if (network.threshold_cms !== 20) throw new Error("Unexpected network discharge threshold");
    state.reaches = new Map(overview.reaches.map((row) => [row.hyriv_id, row]));
    state.points = overview.points;
    state.features = geometry.features;
    state.network = network.reaches;
    state.networkBounds = network.bounds;
    state.network.forEach((river) => {
      river._bounds = boundsOf(river);
      state.networkById.set(river[0], river);
    });
    state.features.forEach((feature) => {
      feature._bounds = boundsOf(feature);
      const id = feature.properties.HYRIV_ID;
      if (!state.featureById.has(id)) state.featureById.set(id, []);
      state.featureById.get(id).push(feature);
    });
    $("map-count").textContent = `${number.format(state.network.length)} rivers >20 | ${number.format(state.reaches.size)} matched | ${number.format(state.points.length)} points`;
    $("map-loading").hidden = true;
    await selectReach(40192081);
    fitAll();
  } catch (error) {
    $("map-loading").textContent = error.message;
  }
}

$("search-button").addEventListener("click", () => {
  const id = Number($("hydro-search").value);
  if (Number.isInteger(id) && id > 0) selectReach(id, true).catch(console.error);
});
$("hydro-search").addEventListener("keydown", (event) => {
  if (event.key === "Enter") $("search-button").click();
});
$("hydro-search").addEventListener("input", () => $("hydro-search").setCustomValidity(""));
$("reset-view").addEventListener("click", fitAll);
$("zoom-in").addEventListener("click", () => zoomAt(1.65));
$("zoom-out").addEventListener("click", () => zoomAt(1 / 1.65));
$("metric-select").addEventListener("change", renderChart);
for (const id of ["layer-jrc", "layer-network", "layer-reaches", "layer-points"]) $(id).addEventListener("change", queueRender);
canvas.addEventListener("wheel", (event) => {
  event.preventDefault();
  const rect = canvas.getBoundingClientRect();
  zoomAt(event.deltaY < 0 ? 1.2 : 1 / 1.2, event.clientX - rect.left, event.clientY - rect.top);
}, { passive: false });
canvas.addEventListener("pointerdown", (event) => {
  canvas.setPointerCapture(event.pointerId);
  state.pointer = { x: event.clientX, y: event.clientY };
  state.dragged = false;
});
canvas.addEventListener("pointermove", (event) => {
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left, y = event.clientY - rect.top;
  if (state.pointer) {
    const dx = event.clientX - state.pointer.x, dy = event.clientY - state.pointer.y;
    if (Math.abs(dx) + Math.abs(dy) > 2) state.dragged = true;
    state.centerLon -= dx / state.scale;
    state.centerLat += dy / state.scale;
    state.pointer = { x: event.clientX, y: event.clientY };
    $("map-tooltip").hidden = true;
    queueRender();
    return;
  }
  const hit = x >= 0 && y >= 0 && x < state.width && y < state.height ? hitAt(x, y) : null;
  const tooltip = $("map-tooltip");
  tooltip.hidden = !hit;
  canvas.style.cursor = hit ? "pointer" : "grab";
  if (hit) {
    tooltip.textContent = hit.kind === "point" ? `CaMa ${hit.catchment_id} | Hydro ${hit.hyriv_id}` :
      state.reaches.has(hit.hyriv_id) ? `Hydro ${hit.hyriv_id}` : `Hydro ${hit.hyriv_id} | no CaMa match`;
    tooltip.style.left = `${Math.min(x + 12, state.width - 230)}px`;
    tooltip.style.top = `${Math.max(y - 28, 8)}px`;
  }
});
canvas.addEventListener("pointerup", (event) => {
  if (!state.dragged) {
    const rect = canvas.getBoundingClientRect();
    const hit = hitAt(event.clientX - rect.left, event.clientY - rect.top);
    if (hit) selectReach(hit.hyriv_id, false, hit.catchment_id || null).catch(console.error);
  }
  state.pointer = null;
});
canvas.addEventListener("pointercancel", () => { state.pointer = null; });
canvas.addEventListener("pointerleave", () => { $("map-tooltip").hidden = true; });
new ResizeObserver(resize).observe($("map-wrap"));
init();
