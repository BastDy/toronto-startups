(async function () {
  const $ = (id) => document.getElementById(id);
  const grid = $("grid");
  let data = [];

  try {
    const res = await fetch("startups.json", { cache: "no-store" });
    data = await res.json();
  } catch (e) {
    grid.innerHTML = '<p class="empty">Could not load startups.json.</p>';
    return;
  }

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

  function card(d) {
    const url = d.website || (d.domain ? `https://${d.domain}` : null);
    const name = url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(d.name)}</a>` : esc(d.name);
    const tags = [
      d.sector && `<span class="tag">${esc(d.sector)}</span>`,
      d.stage && d.stage !== "Unknown" && `<span class="tag plain">${esc(d.stage)}</span>`,
      d.city && `<span class="tag plain">${esc(d.city)}</span>`,
      d.employees && `<span class="tag plain">${esc(d.employees)} people</span>`,
      d.hiring && `<span class="tag ok">Hiring</span>`,
      d.status === "acquired" && `<span class="tag warn">Acquired</span>`,
    ].filter(Boolean).join("");
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
      <div class="tags">${tags}</div>
      ${links ? `<div class="links">${links}</div>` : ""}
    </article>`;
  }

  function render() {
    const q = $("q").value.trim().toLowerCase();
    const f = { sector: $("sector").value, stage: $("stage").value, city: $("city").value };
    const rows = data.filter((d) =>
      (!q || [d.name, d.description, d.domain, d.notes].join(" ").toLowerCase().includes(q)) &&
      (!f.sector || d.sector === f.sector) &&
      (!f.stage || d.stage === f.stage) &&
      (!f.city || d.city === f.city) &&
      (!$("hiring").checked || d.hiring) &&
      (!$("verified").checked || d.verified)
    );
    grid.innerHTML = rows.map(card).join("");
    $("count").textContent = `${rows.length} of ${data.length} startups`;
    $("empty").hidden = rows.length > 0;
  }

  for (const id of ["q", "sector", "stage", "city", "hiring", "verified"]) {
    $(id).addEventListener("input", render);
  }
  render();
})();
