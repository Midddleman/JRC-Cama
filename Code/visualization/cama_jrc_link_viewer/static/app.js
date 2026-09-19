const $ = (id) => document.getElementById(id);
const canvas = $("map-canvas");
const ctx = canvas.getContext("2d");
const hitCanvas = document.createElement("canvas");
const hitCtx = hitCanvas.getContext("2d", { willReadFrequently: true });
const state = {
  links: [], byId: new Map(), selectedId: null, detail: null,
  channelReference: null,
  centerLon: 105, centerLat: 35, scale: 10, width: 0, height: 0,
  pointer: null, dragged: false, renderQueued: false,
  mapMode: "pan", penColor: "#163f39", penWidth: 4, strokes: [],
};
const jrcImage = new Image();
jrcImage.src = "/api/jrc.png";
jrcImage.onload = queueRender;
const number = new Intl.NumberFormat("en-US");

function statusColor(link) {
  if (link.jrc_status === 2) return "#118069";
  if (link.jrc_status === 1) return "#d34f45";
  return "#8f9293";
}
function statusText(link) {
  if (link.jrc_status === 2) return "Perennial";
  if (link.jrc_status === 1) return "Non-perennial";
  return "Unresolved";
}
function format(value, digits = 2) {
  return value == null ? "-" : Number(value).toLocaleString("en-US", { maximumFractionDigits: digits });
}
function toScreen(lon, lat) {
  return [state.width / 2 + (lon - state.centerLon) * state.scale,
          state.height / 2 - (lat - state.centerLat) * state.scale];
}
function toGeo(x, y) {
  return [state.centerLon + (x - state.width / 2) / state.scale,
          state.centerLat - (y - state.height / 2) / state.scale];
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
    ctx.fillText(`${Math.round(lon * 10) / 10}E`, x + 4, state.height - 10);
  }
  for (let lat = Math.ceil(bottom / step) * step; lat <= top; lat += step) {
    const y = toScreen(0, lat)[1];
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(state.width, y); ctx.stroke();
    ctx.fillText(`${Math.round(lat * 10) / 10}N`, 8, y - 5);
  }
}
function drawLine(context, link) {
  if (link.downstream_longitude == null || link.downstream_latitude == null) return;
  const [x0, y0] = toScreen(link.longitude, link.latitude);
  const [x1, y1] = toScreen(link.downstream_longitude, link.downstream_latitude);
  context.beginPath(); context.moveTo(x0, y0); context.lineTo(x1, y1); context.stroke();
}
function drawCorridor(corners) {
  if (!corners) return;
  ctx.beginPath();
  corners.forEach(([lon, lat], index) => {
    const [x, y] = toScreen(lon, lat);
    if (index) ctx.lineTo(x, y); else ctx.moveTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = "rgba(46, 65, 58, .11)";
  ctx.fill();
  ctx.strokeStyle = "#314c43";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([6, 4]);
  ctx.stroke();
  ctx.setLineDash([]);
}
function drawStrokes() {
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  for (const stroke of state.strokes) {
    ctx.strokeStyle = stroke.color;
    ctx.fillStyle = stroke.color;
    ctx.lineWidth = stroke.width;
    if (stroke.points.length === 1) {
      const [x, y] = toScreen(...stroke.points[0]);
      ctx.beginPath(); ctx.arc(x, y, stroke.width / 2, 0, 2 * Math.PI); ctx.fill();
      continue;
    }
    ctx.beginPath();
    stroke.points.forEach((point, index) => {
      const [x, y] = toScreen(...point);
      if (index) ctx.lineTo(x, y); else ctx.moveTo(x, y);
    });
    ctx.stroke();
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
    ctx.globalAlpha = 0.52;
    ctx.drawImage(jrcImage, x, y, 70.0095 * state.scale, 50.00325 * state.scale);
    ctx.globalAlpha = 1;
  }
  drawGrid();
  drawCorridor(state.detail?.link.corridor);
  const [west, north] = toGeo(0, 0);
  const [east, south] = toGeo(state.width, state.height);
  if ($("layer-links").checked) {
    state.links.forEach((link, index) => {
      if (link.downstream_longitude == null) return;
      if (Math.max(link.longitude, link.downstream_longitude) < west ||
          Math.min(link.longitude, link.downstream_longitude) > east ||
          Math.max(link.latitude, link.downstream_latitude) < south ||
          Math.min(link.latitude, link.downstream_latitude) > north) return;
      const selected = state.selectedId === link.catchment_id;
      ctx.strokeStyle = statusColor(link);
      ctx.lineWidth = selected ? 3.5 : state.scale < 20 ? 1 : 1.35;
      ctx.globalAlpha = selected ? 1 : 0.82;
      drawLine(ctx, link);
      hitCtx.strokeStyle = idColor(index + 1);
      hitCtx.lineWidth = 7;
      drawLine(hitCtx, link);
    });
    ctx.globalAlpha = 1;
    const selected = state.byId.get(state.selectedId);
    if (selected) {
      ctx.strokeStyle = statusColor(selected);
      ctx.lineWidth = 4;
      drawLine(ctx, selected);
    }
  }
  if ($("layer-points").checked) {
    const offset = state.links.length + 1;
    const dense = state.scale < 22;
    state.links.forEach((link, index) => {
      const [x, y] = toScreen(link.longitude, link.latitude);
      if (x < -8 || y < -8 || x > state.width + 8 || y > state.height + 8) return;
      const selected = state.selectedId === link.catchment_id;
      ctx.beginPath(); ctx.arc(x, y, selected ? 4.5 : dense ? 1.6 : 2.7, 0, 2 * Math.PI);
      ctx.fillStyle = statusColor(link); ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = selected ? 1.5 : dense ? 0.5 : 0.9;
      ctx.stroke();
      hitCtx.beginPath(); hitCtx.arc(x, y, dense ? 4 : 7, 0, 2 * Math.PI);
      hitCtx.fillStyle = idColor(offset + index); hitCtx.fill();
    });
  }
  drawStrokes();
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
  state.centerLon = 105.00475;
  state.centerLat = 35;
  state.scale = Math.min(state.width / 70.0095, state.height / 50.00325) * 0.96;
  queueRender();
}
function zoomAt(factor, x = state.width / 2, y = state.height / 2) {
  const [lon, lat] = toGeo(x, y);
  state.scale = Math.max(2, Math.min(3500, state.scale * factor));
  state.centerLon = lon - (x - state.width / 2) / state.scale;
  state.centerLat = lat + (y - state.height / 2) / state.scale;
  queueRender();
}
function jumpTo(link) {
  const lon1 = link.downstream_longitude ?? link.longitude;
  const lat1 = link.downstream_latitude ?? link.latitude;
  const points = state.detail?.link.corridor || [[link.longitude, link.latitude], [lon1, lat1]];
  const lons = points.map((point) => point[0]);
  const lats = points.map((point) => point[1]);
  state.centerLon = (Math.min(...lons) + Math.max(...lons)) / 2;
  state.centerLat = (Math.min(...lats) + Math.max(...lats)) / 2;
  state.scale = Math.min(
    state.width / Math.max((Math.max(...lons) - Math.min(...lons)) * 2.8, 0.2),
    state.height / Math.max((Math.max(...lats) - Math.min(...lats)) * 2.8, 0.16),
    2000,
  );
  queueRender();
}
function hitAt(x, y) {
  if (x < 0 || y < 0 || x >= state.width || y >= state.height) return null;
  const dpr = hitCanvas.width / state.width;
  const pixel = hitCtx.getImageData(Math.floor(x * dpr), Math.floor(y * dpr), 1, 1).data;
  const index = colorId(pixel);
  if (index >= 1 && index <= state.links.length) return state.links[index - 1];
  const pointIndex = index - state.links.length - 1;
  return pointIndex >= 0 && pointIndex < state.links.length ? state.links[pointIndex] : null;
}
function fact(label, value) {
  return `<div><span>${label}</span><strong>${value}</strong></div>`;
}
function renderDetail(data) {
  const link = data.link;
  $("catchment-id").textContent = number.format(link.catchment_id);
  const cssClass = link.jrc_status === 2 ? "perennial" : link.jrc_status === 1 ? "intermittent" : "no-water";
  $("link-status").innerHTML = `<span class="status-pill ${cssClass}">${statusText(link)}</span><span>${link.jrc_label.replaceAll("_", " ")}</span>`;
  $("link-facts").innerHTML =
    fact("Downstream catchment", format(link.downstream_id, 0)) +
    fact("Link length", link.link_length_m == null ? "-" : `${format(link.link_length_m / 1000, 2)} km`) +
    fact("Upstream area", `${format(link.upstream_area_km2, 0)} km2`) +
    fact("Corridor width", "10 km") +
    fact("JRC perennial cells", format(link.perennial_count, 0)) +
    fact("JRC intermittent cells", format(link.intermittent_count, 0)) +
    fact("Connected blue path", link.connected_path_cells == null ? "-" : `${format(link.connected_path_cells, 0)} cells`) +
    fact("Valid corridor cells", format(link.valid_cell_count, 0));
  renderChannel(data.channel);
  $("download-link").hidden = false;
  $("download-link").href = `/api/catchment/${link.catchment_id}/csv`;
  $("monthly-table").querySelector("tbody").innerHTML = data.months.map((row) =>
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
function renderChannel(channel) {
  $("channel-facts").innerHTML =
    fact("Channel width", channel?.river_width_m == null ? "-" : `${format(channel.river_width_m, 2)} m`) +
    fact("Model bankfull depth", channel?.river_height_m == null ? "-" : `${format(channel.river_height_m, 2)} m`) +
    fact("Model channel length", channel?.river_length_m == null ? "-" : `${format(channel.river_length_m / 1000, 2)} km`);
  const svg = $("channel-section");
  svg.replaceChildren();
  const reference = state.channelReference;
  $("channel-reference").textContent = reference
    ? `Dashed reference: catchment ${format(reference.catchment_id, 0)} (${format(reference.river_width_m, 2)} m wide, ${format(reference.river_height_m, 2)} m deep). Width and depth use fixed square-root scales, capped to fit.`
    : "";
  if (!(channel?.river_width_m > 0 && channel?.river_height_m > 0)) {
    svg.appendChild(svgElement("text", { x: 210, y: 105, "text-anchor": "middle" }, "Channel geometry unavailable"));
    return;
  }
  const top = 64;
  const width = reference?.river_width_m > 0
    ? Math.max(42, Math.min(312, 180 * Math.sqrt(channel.river_width_m / reference.river_width_m)))
    : 180;
  const depth = reference?.river_height_m > 0
    ? Math.max(24, Math.min(120, 60 * Math.sqrt(channel.river_height_m / reference.river_height_m)))
    : 60;
  const left = 210 - width / 2;
  const right = 210 + width / 2;
  const bottom = top + depth;
  svg.appendChild(svgElement("path", {
    d: `M0 ${top} H${left} V${bottom} H${right} V${top} H420 V200 H0 Z`, fill: "#e0e7e1",
  }));
  svg.appendChild(svgElement("path", {
    d: `M0 ${top} H${left} V${bottom} H${right} V${top} H420`, fill: "none", stroke: "#1a7967", "stroke-width": 2.5,
  }));
  if (reference?.river_width_m > 0 && reference?.river_height_m > 0) {
    svg.appendChild(svgElement("path", {
      d: `M120 ${top} V124 H300 V${top}`,
      fill: "none", stroke: "#89958f", "stroke-width": 1.7, "stroke-dasharray": "5 4",
    }));
  }
  svg.appendChild(svgElement("line", {
    x1: left, y1: 40, x2: right, y2: 40, stroke: "#1a7967", "stroke-width": 1.5,
  }));
  svg.appendChild(svgElement("path", {
    d: `M${left} 34 V49 M${right} 34 V49 M${left} 40 l8 -4 v8 Z M${right} 40 l-8 -4 v8 Z`,
    fill: "#1a7967", stroke: "#1a7967", "stroke-width": 1,
  }));
  svg.appendChild(svgElement("text", { x: 210, y: 29, "text-anchor": "middle" },
    `Width ${format(channel.river_width_m, 2)} m`));
  svg.appendChild(svgElement("line", {
    x1: right + 15, y1: top, x2: right + 15, y2: bottom, stroke: "#1a7967", "stroke-width": 1.5,
  }));
  svg.appendChild(svgElement("path", {
    d: `M${right + 8} ${top} H${right + 22} M${right + 8} ${bottom} H${right + 22} M${right + 15} ${top} l-4 8 h8 Z M${right + 15} ${bottom} l-4 -8 h8 Z`,
    fill: "#1a7967", stroke: "#1a7967", "stroke-width": 1,
  }));
  svg.appendChild(svgElement("text", {
    x: right > 310 ? right - 9 : right + 29, y: top + depth / 2 + 4,
    "text-anchor": right > 310 ? "end" : "start",
  }, `${format(channel.river_height_m, 2)} m`));
}
function renderChart() {
  const svg = $("flow-chart");
  svg.replaceChildren();
  svg.setAttribute("viewBox", "0 0 520 245");
  const rows = state.detail?.months || [];
  const metric = $("metric-select").value;
  const max = Math.max(...rows.map((row) => row[metric]).filter((value) => value != null), 1) * 1.08;
  const xPos = (month) => 46 + (month - 1) * 40;
  const yPos = (value) => 194 - (value / max) * 162;
  for (let tick = 0; tick <= 4; tick++) {
    const value = max * tick / 4;
    const y = yPos(value);
    svg.appendChild(svgElement("line", { x1: 46, y1: y, x2: 491, y2: y, stroke: "#e3e9e7" }));
    svg.appendChild(svgElement("text", { x: 39, y: y + 4, "text-anchor": "end", class: "axis-label" }, format(value, 1)));
  }
  for (let month = 1; month <= 12; month++) {
    svg.appendChild(svgElement("text", { x: xPos(month), y: 219, "text-anchor": "middle", class: "axis-label" }, month));
  }
  svg.appendChild(svgElement("text", { x: 491, y: 236, "text-anchor": "end", class: "axis-label" }, "Month"));
  const valid = rows.filter((row) => row[metric] != null);
  const path = valid.map((row, index) => `${index ? "L" : "M"}${xPos(row.month)},${yPos(row[metric])}`).join(" ");
  svg.appendChild(svgElement("path", {
    d: path, fill: "none", stroke: "#137b69", "stroke-width": 2.7,
    "stroke-linecap": "round", "stroke-linejoin": "round",
  }));
  valid.forEach((row) => {
    const circle = svgElement("circle", { cx: xPos(row.month), cy: yPos(row[metric]), r: 3.4, fill: "#137b69" });
    circle.appendChild(svgElement("title", {}, `Month ${row.month}: ${format(row[metric], 3)} m3/s`));
    svg.appendChild(circle);
  });
}
async function selectLink(id, jump = false) {
  const overviewLink = state.byId.get(id);
  if (!overviewLink) {
    $("catchment-search").setCustomValidity("Catchment ID not found");
    $("catchment-search").reportValidity();
    return;
  }
  $("catchment-search").setCustomValidity("");
  const response = await fetch(`/api/catchment/${id}`);
  if (!response.ok) throw new Error(`Could not load catchment ${id}`);
  state.detail = await response.json();
  state.selectedId = id;
  $("catchment-search").value = id;
  renderDetail(state.detail);
  if (jump) jumpTo(overviewLink); else queueRender();
}
async function init() {
  resize();
  try {
    const response = await fetch("/api/overview");
    if (!response.ok) throw new Error("Could not load link data");
    const data = await response.json();
    state.links = data.links;
    state.channelReference = data.channel_reference;
    state.byId = new Map(state.links.map((link) => [link.catchment_id, link]));
    const green = state.links.filter((link) => link.jrc_status === 2).length;
    const red = state.links.filter((link) => link.jrc_status === 1).length;
    $("map-count").textContent = `${number.format(green)} perennial | ${number.format(red)} non-perennial | ${number.format(state.links.length - green - red)} unresolved`;
    $("map-loading").hidden = true;
    const first = state.links.find((link) => link.jrc_status === 2) || state.links[0];
    if (first) await selectLink(first.catchment_id);
    fitAll();
  } catch (error) {
    $("map-loading").textContent = error.message;
  }
}

$("search-button").addEventListener("click", () => {
  const id = Number($("catchment-search").value);
  if (Number.isInteger(id) && id > 0) selectLink(id, true).catch(console.error);
});
$("catchment-search").addEventListener("keydown", (event) => {
  if (event.key === "Enter") $("search-button").click();
});
$("catchment-search").addEventListener("input", () => $("catchment-search").setCustomValidity(""));
$("reset-view").addEventListener("click", fitAll);
$("zoom-in").addEventListener("click", () => zoomAt(1.65));
$("zoom-out").addEventListener("click", () => zoomAt(1 / 1.65));
$("metric-select").addEventListener("change", renderChart);
for (const id of ["layer-jrc", "layer-links", "layer-points"]) $(id).addEventListener("change", queueRender);
function setMapMode(mode) {
  state.mapMode = mode;
  $("mode-pan").setAttribute("aria-pressed", String(mode === "pan"));
  $("mode-draw").setAttribute("aria-pressed", String(mode === "draw"));
  canvas.style.cursor = mode === "draw" ? "crosshair" : "grab";
  $("map-tooltip").hidden = true;
}
function updateDrawingActions() {
  const empty = state.strokes.length === 0;
  $("draw-undo").disabled = empty;
  $("draw-clear").disabled = empty;
}
$("mode-pan").addEventListener("click", () => setMapMode("pan"));
$("mode-draw").addEventListener("click", () => setMapMode("draw"));
for (const swatch of document.querySelectorAll(".pen-swatch")) {
  swatch.addEventListener("click", () => {
    state.penColor = swatch.dataset.color;
    for (const item of document.querySelectorAll(".pen-swatch")) {
      item.setAttribute("aria-pressed", String(item === swatch));
    }
    setMapMode("draw");
  });
}
$("pen-size").addEventListener("input", (event) => {
  state.penWidth = Number(event.target.value);
  $("pen-size-value").textContent = `${state.penWidth} px`;
});
$("draw-undo").addEventListener("click", () => {
  state.strokes.pop();
  updateDrawingActions();
  queueRender();
});
$("draw-clear").addEventListener("click", () => {
  if (!state.strokes.length || !window.confirm("Clear all map annotations?")) return;
  state.strokes.length = 0;
  updateDrawingActions();
  queueRender();
});
$("draw-save").addEventListener("click", () => {
  render();
  const dpr = canvas.width / state.width;
  const footerHeight = Math.round(58 * dpr);
  const output = document.createElement("canvas");
  output.width = canvas.width;
  output.height = canvas.height + footerHeight;
  const exportCtx = output.getContext("2d");
  exportCtx.drawImage(canvas, 0, 0);
  exportCtx.fillStyle = "#fff";
  exportCtx.fillRect(0, canvas.height, output.width, footerHeight);
  exportCtx.fillStyle = "#253432";
  exportCtx.font = `${12 * dpr}px Segoe UI, sans-serif`;
  exportCtx.fillText(`CaMa-Flood / JRC direct links${state.selectedId ? ` | Catchment ${state.selectedId}` : ""}`, 12 * dpr, canvas.height + 20 * dpr);
  exportCtx.font = `${11 * dpr}px Segoe UI, sans-serif`;
  [["#118069", "Perennial"], ["#d34f45", "Non-perennial"], ["#8f9293", "Unresolved"]].forEach(([color, label], index) => {
    const x = (12 + index * 110) * dpr;
    exportCtx.fillStyle = color;
    exportCtx.fillRect(x, canvas.height + 39 * dpr, 17 * dpr, 3 * dpr);
    exportCtx.fillStyle = "#52655e";
    exportCtx.fillText(label, x + 23 * dpr, canvas.height + 44 * dpr);
  });
  output.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `cama_jrc_map_${state.selectedId || "all"}.png`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }, "image/png");
});
canvas.addEventListener("wheel", (event) => {
  event.preventDefault();
  const rect = canvas.getBoundingClientRect();
  zoomAt(event.deltaY < 0 ? 1.2 : 1 / 1.2, event.clientX - rect.left, event.clientY - rect.top);
}, { passive: false });
canvas.addEventListener("pointerdown", (event) => {
  if (state.pointer) return;
  canvas.setPointerCapture(event.pointerId);
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left, y = event.clientY - rect.top;
  state.pointer = { x: event.clientX, y: event.clientY, mode: state.mapMode };
  state.dragged = false;
  if (state.mapMode === "draw") {
    state.strokes.push({ color: state.penColor, width: state.penWidth, points: [toGeo(x, y)] });
    updateDrawingActions();
    $("map-tooltip").hidden = true;
    queueRender();
  }
});
canvas.addEventListener("pointermove", (event) => {
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left, y = event.clientY - rect.top;
  if (state.pointer) {
    const dx = event.clientX - state.pointer.x, dy = event.clientY - state.pointer.y;
    if (state.pointer.mode === "draw") {
      if (Math.abs(dx) + Math.abs(dy) >= 1) {
        state.strokes[state.strokes.length - 1].points.push(toGeo(x, y));
        state.pointer = { x: event.clientX, y: event.clientY, mode: "draw" };
        queueRender();
      }
      return;
    }
    if (Math.abs(dx) + Math.abs(dy) > 2) state.dragged = true;
    state.centerLon -= dx / state.scale;
    state.centerLat += dy / state.scale;
    state.pointer = { x: event.clientX, y: event.clientY };
    $("map-tooltip").hidden = true;
    queueRender();
    return;
  }
  if (state.mapMode === "draw") {
    $("map-tooltip").hidden = true;
    canvas.style.cursor = "crosshair";
    return;
  }
  const hit = hitAt(x, y);
  const tooltip = $("map-tooltip");
  tooltip.hidden = !hit;
  canvas.style.cursor = hit ? "pointer" : "grab";
  if (hit) {
    tooltip.textContent = `CaMa ${hit.catchment_id} to ${hit.downstream_id} | ${statusText(hit)}`;
    tooltip.style.left = `${Math.max(8, Math.min(x + 12, state.width - 230))}px`;
    tooltip.style.top = `${Math.max(y - 28, 8)}px`;
  }
});
canvas.addEventListener("pointerup", (event) => {
  if (state.pointer?.mode === "pan" && !state.dragged) {
    const rect = canvas.getBoundingClientRect();
    const hit = hitAt(event.clientX - rect.left, event.clientY - rect.top);
    if (hit) selectLink(hit.catchment_id).catch(console.error);
  }
  state.pointer = null;
});
canvas.addEventListener("pointercancel", () => { state.pointer = null; });
canvas.addEventListener("pointerleave", () => { $("map-tooltip").hidden = true; });
new ResizeObserver(resize).observe($("map-wrap"));
init();
