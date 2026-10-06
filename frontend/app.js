const form = document.querySelector("#searchForm");
const query = document.querySelector("#query");
const sortBy = document.querySelector("#sortBy");
const limit = document.querySelector("#limit");
const results = document.querySelector("#results");
const count = document.querySelector("#count");
const statusLine = document.querySelector("#status");

async function boot() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    statusLine.textContent = `${data.catalog_size} novels ready`;
  } catch {
    statusLine.textContent = "Diviner is offline";
  }
}

function formatPercent(value) {
  return `${Math.round(value * 100)}%`;
}

function esc(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderRows(rows) {
  count.textContent = `${rows.length} match${rows.length === 1 ? "" : "es"}`;

  if (rows.length === 0) {
    results.innerHTML = `<div class="card">No matches yet. Try describing a genre, trope, mood, or favorite story.</div>`;
    return;
  }

  results.innerHTML = rows.map((row) => {
    const novel = row.novel;
    const tags = [...novel.genres, ...novel.tags].slice(0, 10);
    return `
      <article class="card">
        <div class="card-top">
          <div>
            <h3>${esc(novel.title)}</h3>
            <div class="meta">${esc(novel.author)} | ${esc(novel.source)} | ${esc(novel.status)} | ${novel.chapters} chapters</div>
          </div>
          <div class="score">
            <div>Match ${formatPercent(row.similarity_score)}</div>
            <div>Rating ${novel.rating.toFixed(1)}/5</div>
          </div>
        </div>
        <div class="tags">${tags.map((tag) => `<span class="tag">${esc(tag)}</span>`).join("")}</div>
        <p class="synopsis">${esc(novel.synopsis)}</p>
        <p class="reasons">Why it matched: ${esc(row.reasons.join(" | "))}</p>
        <a href="${esc(novel.url)}" target="_blank" rel="noreferrer">Read on the source site</a>
      </article>
    `;
  }).join("");
}

async function runSearch(event) {
  event.preventDefault();
  const response = await fetch("/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: query.value,
      sort_by: sortBy.value,
      limit: Number(limit.value || 10)
    })
  });

  const rows = await response.json();
  renderRows(rows);
}

form.addEventListener("submit", runSearch);
query.value = "I want a completed academy progression fantasy with a smart main character";
boot();
form.requestSubmit();
