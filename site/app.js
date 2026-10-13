(async function () {
  const $ = (id) => document.getElementById(id);
  const grid = $("grid");
  let data = [];

  try {
    const res = await fetch("startups.json", { cache: "no-store" });
    data = await res.json();
  } catch (e) {
    grid.hidden = false;
    grid.innerHTML = '<p class="empty">Could not load startups.json.</p>';
    return;
  }

  // City centroids. A startup with exact lat/lng (added after verification) uses those instead.
  const CITY = {
    "Toronto": [43.6532, -79.3832], "North York": [43.7615, -79.4111], "Scarborough": [43.7764, -79.2318],
    "Etobicoke": [43.6205, -79.5132], "York": [43.6896, -79.4874], "East York": [43.6911, -79.3277],
    "Mississauga": [43.589, -79.6441], "Brampton": [43.7315, -79.7624], "Markham": [43.8561, -79.337],
    "Vaughan": [43.8361, -79.4983], "Richmond Hill": [43.8828, -79.4403], "Oakville": [43.4675, -79.6877],
    "Burlington": [43.3255, -79.799], "Milton": [43.5183, -79.8774], "Pickering": [43.8384, -79.0868],
    "Ajax": [43.8509, -79.0204], "Whitby": [43.8975, -78.9429], "Oshawa": [43.8971, -78.8658],
    "Newmarket": [44.0592, -79.4613], "Aurora": [44.0065, -79.4504], "Concord": [43.8, -79.48],
    "Thornhill": [43.815, -79.424], "Woodbridge": [43.784, -79.599], "Maple": [43.853, -79.509],
    "Caledon": [43.8668, -79.858],
  };
  const coords = (d) =>
    typeof d.lat === "number" && typeof d.lng === "number" ? [d.lat, d.lng] : CITY[d.city] || null;

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const uniq = (key) => [...new Set(data.map((d) => d[key]).filter(Boolean))].sort();

  function fill(select, values) {
    for (const v of values) {
      const o = document.createElement("option");
      o.value = o.textContent = v;
      select.appendChild(o);
    }
  }
  fill($("sector"), uniq("sector"));
  fill($("stage"), uniq("stage"));
  fill($("city"), uniq("city"));

  const stat = (n, label) => `<div class="stat"><b>${n}</b><span>${label}</span></div>`;
  $("stats").innerHTML =
    stat(data.length, "startups") +
    stat(data.filter((d) => d.hiring).length, "hiring now") +
    stat(uniq("sector").length, "sectors") +
    stat(data.filter((d) => d.verified).length, "verified");

  const siteUrl = (d) => d.website || (d.domain ? `https://${d.domain}` : null);

  function tagsHtml(d) {
    return [
      d.sector && `<span class="tag">${esc(d.sector)}</span>`,
      d.stage && d.stage !== "Unknown" && `<span class="tag plain">${esc(d.stage)}</span>`,
      d.city && `<span class="tag plain">${esc(d.city)}</span>`,
      d.employees && `<span class="tag plain">${esc(d.employees)} people</span>`,
      d.hiring && `<span class="tag ok">Hiring</span>`,
      d.status === "acquired" && `<span class="tag warn">Acquired</span>`,
    ].filter(Boolean).join("");
  }

  function card(d) {
    const url = siteUrl(d);
    const name = url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(d.name)}</a>` : esc(d.name);
    const round = d.last_round
      ? `<p class="round">${esc(d.last_round)}${d.last_round_amount ? " · " + esc(d.last_round_amount) : ""}${d.last_round_date ? " · " + esc(d.last_round_date.slice(0, 7)) : ""}</p>`
      : "";
    const links = [
      d.linkedin && `<a href="${esc(d.linkedin)}" target="_blank" rel="noopener">LinkedIn</a>`,
      d.sources && d.sources[0] && `<a href="${esc(d.sources[0])}" target="_blank" rel="noopener">Source</a>`,
    ].filter(Boolean).join("");
    return `<article class="card">
      <h2>${name}${d.domain ? `<span class="domain">${esc(d.domain)}</span>` : ""}</h2>
      ${d.description ? `<p class="desc">${esc(d.description)}</p>` : ""}
      ${round}
      <div class="tags">${tagsHtml(d)}</div>
      ${links ? `<div class="links">${links}</div>` : ""}
    </article>`;
  }

  function popup(d) {
    const url = siteUrl(d);
    const name = url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(d.name)}</a>` : esc(d.name);
    return `<div class="pop"><h3>${name}</h3>${d.description ? `<p>${esc(d.description)}</p>` : ""}<div class="tags">${tagsHtml(d)}</div></div>`;
  }

  // ---- Map ----
  // Wheel zoom only after a click on the map, so scrolling the page never gets trapped by it.
  const map = L.map("map", { scrollWheelZoom: false }).setView([43.7, -79.42], 10);
  map.on("click focus", () => map.scrollWheelZoom.enable());
  map.on("mouseout blur", () => map.scrollWheelZoom.disable());
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  const cluster = L.markerClusterGroup({ showCoverageOnHover: false, maxClusterRadius: 50 });
  map.addLayer(cluster);
  const icon = (d) => L.divIcon({ className: "", html: `<div class="dot${d.hiring ? " hiring" : ""}"></div>`, iconSize: [14, 14] });

  function drawMap(rows) {
    cluster.clearLayers();
    let placed = 0, exact = 0;
    for (const d of rows) {
      const c = coords(d);
      if (!c) continue;
      cluster.addLayer(L.marker(c, { icon: icon(d), title: d.name }).bindPopup(popup(d)));
      placed++;
      if (typeof d.lat === "number") exact++;
    }
    const off = rows.length - placed;
    $("mapnote").textContent =
      `${exact} of ${placed} pins are at the verified street address, the others sit on their city centre. ` +
      (off ? `${off} startup${off > 1 ? "s" : ""} with an unconfirmed city ${off > 1 ? "are" : "is"} only in the list.` : "");
  }

  // ---- View toggle ----
  let view = "map";
  try { view = localStorage.getItem("view") || "map"; } catch (e) {}
  function setView(v) {
    view = v;
    try { localStorage.setItem("view", v); } catch (e) {}
    document.querySelectorAll(".views button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.view === v)));
    $("mapbox").hidden = v !== "map";
    grid.hidden = v !== "list";
    if (v === "map") map.invalidateSize();
    render();
  }
  document.querySelectorAll(".views button").forEach((b) => b.addEventListener("click", () => setView(b.dataset.view)));

  // ---- Filters ----
  function filtered() {
    const q = $("q").value.trim().toLowerCase();
    const f = { sector: $("sector").value, stage: $("stage").value, city: $("city").value };
    return data.filter((d) =>
      (!q || [d.name, d.description, d.domain, d.notes].join(" ").toLowerCase().includes(q)) &&
      (!f.sector || d.sector === f.sector) &&
      (!f.stage || d.stage === f.stage) &&
      (!f.city || d.city === f.city) &&
      (!$("hiring").checked || d.hiring) &&
      (!$("verified").checked || d.verified)
    );
  }

  function render() {
    const rows = filtered();
    $("count").textContent = `${rows.length} of ${data.length} startups`;
    $("empty").hidden = rows.length > 0;
    if (view === "map") drawMap(rows);
    else grid.innerHTML = rows.map(card).join("");
  }

  for (const id of ["q", "sector", "stage", "city", "hiring", "verified"]) {
    $(id).addEventListener("input", render);
  }
  setView(view);
})();
