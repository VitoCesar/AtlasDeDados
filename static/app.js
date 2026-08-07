const selectors = {
  year: document.querySelector("#year"), month: document.querySelector("#month"),
  brand: document.querySelector("#brand"), continent: document.querySelector("#continent")
};
const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const number = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
const compact = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
const monthLabel = new Intl.DateTimeFormat("pt-BR", { month: "short", year: "2-digit", timeZone: "UTC" });

function addOptions(select, values, labelKey, valueKey) {
  values.forEach(item => {
    const option = document.createElement("option");
    option.value = valueKey ? item[valueKey] : item;
    option.textContent = labelKey ? item[labelKey] : item;
    select.append(option);
  });
}

function showStatus(message, persistent = false) {
  const el = document.querySelector("#status");
  el.textContent = message;
  el.classList.toggle("visible", Boolean(message));
  if (message && !persistent) setTimeout(() => el.classList.remove("visible"), 1400);
}

function renderBars(target, data, label, value) {
  if (!data.length) { target.innerHTML = '<div class="empty">Sem dados para os filtros selecionados</div>'; return; }
  const max = Math.max(...data.map(row => row[value]));
  target.innerHTML = data.map(row => `
    <div class="bar-row" title="${row[label]}: ${money.format(row[value])}">
      <span class="bar-label">${row[label]}</span>
      <div class="bar-track"><div class="bar-fill" style="--width:${(row[value] / max) * 100}%"></div></div>
      <span class="bar-value">${compact.format(row[value])}</span>
    </div>`).join("");
}

function pathFor(points) { return points.map((p, i) => `${i ? "L" : "M"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" "); }

function renderTimeline(data) {
  const target = document.querySelector("#timeline");
  if (!data.length) { target.innerHTML = '<div class="empty">Sem dados para os filtros selecionados</div>'; return; }
  const W = 1100, H = 300, left = 58, right = 28, top = 15, bottom = 42;
  const innerW = W - left - right, innerH = H - top - bottom;
  const revenueMax = Math.max(...data.map(d => d.faturamento)) || 1;
  const quantityMax = Math.max(...data.map(d => d.quantidade)) || 1;
  const x = i => left + (data.length === 1 ? innerW / 2 : i * innerW / (data.length - 1));
  const revenuePoints = data.map((d, i) => ({ x: x(i), y: top + innerH - (d.faturamento / revenueMax) * innerH }));
  const quantityPoints = data.map((d, i) => ({ x: x(i), y: top + innerH - (d.quantidade / quantityMax) * innerH }));
  const grid = [0, .25, .5, .75, 1].map(t => {
    const y = top + innerH - t * innerH;
    return `<line class="gridline" x1="${left}" x2="${W-right}" y1="${y}" y2="${y}"/><text class="axis-label" x="0" y="${y+3}">${compact.format(revenueMax*t)}</text>`;
  }).join("");
  const step = Math.max(1, Math.ceil(data.length / 12));
  const labels = data.map((d, i) => i % step ? "" : `<text class="axis-label" text-anchor="middle" x="${x(i)}" y="${H-12}">${monthLabel.format(new Date(`${d.ano_mes}-01T00:00:00Z`)).replace(" de ", "/")}</text>`).join("");
  const area = `${pathFor(revenuePoints)} L${revenuePoints.at(-1).x},${top+innerH} L${revenuePoints[0].x},${top+innerH} Z`;
  const dots = revenuePoints.map((p, i) => `<circle cx="${p.x}" cy="${p.y}" r="4" fill="#ee684f"><title>${data[i].ano_mes}: ${money.format(data[i].faturamento)} · ${number.format(data[i].quantidade)} un.</title></circle>`).join("");
  target.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">${grid}<path class="revenue-area" d="${area}"/><path class="revenue-line" d="${pathFor(revenuePoints)}"/><path class="quantity-line" d="${pathFor(quantityPoints)}"/>${dots}${labels}</svg>`;
}

async function loadDashboard() {
  showStatus("Atualizando dados…", true);
  const params = new URLSearchParams();
  Object.entries(selectors).forEach(([key, select]) => { if (select.value) params.set(key === "year" ? "ano" : key === "month" ? "mes" : key === "brand" ? "marca" : "continente", select.value); });
  try {
    const response = await fetch(`/api/dashboard?${params}`);
    if (!response.ok) throw new Error("Falha na API");
    const data = await response.json();
    document.querySelector("#revenue").textContent = money.format(data.resumo.faturamento_total);
    document.querySelector("#quantity").textContent = number.format(data.resumo.quantidade_total);
    document.querySelector("#records").textContent = `${number.format(data.resumo.registros)} registros analisados`;
    const top = data.resumo.produto_mais_vendido;
    document.querySelector("#top-product").textContent = top?.produto ?? "Sem dados";
    document.querySelector("#top-product-detail").textContent = top ? `${number.format(top.quantidade)} unidades · ${money.format(top.faturamento)}` : "—";
    renderTimeline(data.por_ano_mes);
    renderBars(document.querySelector("#brands"), data.por_marca, "marca", "faturamento");
    renderBars(document.querySelector("#continents"), data.por_continente, "continente", "faturamento");
    showStatus("Dashboard atualizado");
  } catch (error) {
    console.error(error); showStatus("Não foi possível carregar os dados.", true);
  }
}

async function init() {
  try {
    const response = await fetch("/api/filtros");
    const filters = await response.json();
    addOptions(selectors.year, filters.anos); addOptions(selectors.month, filters.meses, "nome", "valor");
    addOptions(selectors.brand, filters.marcas); addOptions(selectors.continent, filters.continentes);
    const formatDate = value => new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
    document.querySelector("#period").textContent = `${formatDate(filters.periodo.inicio)} — ${formatDate(filters.periodo.fim)}`;
    Object.values(selectors).forEach(select => select.addEventListener("change", loadDashboard));
    document.querySelector("#clear").addEventListener("click", () => { Object.values(selectors).forEach(select => select.value = ""); loadDashboard(); });
    await loadDashboard();
  } catch (error) { console.error(error); showStatus("A API não está disponível.", true); }
}

init();
