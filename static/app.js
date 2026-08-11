const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const number = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });
const compact = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
const sourceSelect = document.querySelector("#source");
let selectors = {};

const configs = {
  vendas: {
    title: 'O pulso das vendas,<br><em>mês a mês.</em>', intro: "Explore faturamento, volume, marcas e presença global.", note: "Fonte: Vendas.xlsx",
    filters: [["year","Ano","anos","Todos"],["month","Mês","meses","Todos","nome","valor"],["brand","Marca","marcas","Todas"],["continent","Continente","continentes","Todos"]]
  },
  violencia: {
    title: 'Um retrato da segurança,<br><em>território a território.</em>', intro: "Analise registros por perfil da vítima, natureza, período, município e meio empregado.", note: "Fonte: Violência_2025.xlsx",
    filters: [["year","Ano","anos","Todos"],["month","Mês","meses","Todos","nome","valor"],["municipality","Município","municipios","Todos"],["nature","Natureza","naturezas","Todas"],["weekday","Dia da semana","dias_semana","Todos"],["means","Meio empregado","meios","Todos"],["gender","Gênero","generos","Todos"]]
  }
};

function escapeHtml(value) { const e = document.createElement("div"); e.textContent = String(value); return e.innerHTML; }
function showStatus(message, persistent=false) { const el=document.querySelector("#status"); el.textContent=message; el.classList.toggle("visible",!!message); if(message&&!persistent)setTimeout(()=>el.classList.remove("visible"),1400); }
function formatDate(value) { return new Intl.DateTimeFormat("pt-BR",{timeZone:"UTC"}).format(new Date(`${value}T00:00:00Z`)); }

function createFilters(data, source) {
  const host=document.querySelector("#filters"); host.innerHTML=""; selectors={};
  configs[source].filters.forEach(([id,label,key,empty,labelKey,valueKey])=>{
    const wrapper=document.createElement("label"); wrapper.textContent=label;
    const select=document.createElement("select"); select.id=id; select.innerHTML=`<option value="">${empty}</option>`;
    (data[key]||[]).forEach(item=>{const option=document.createElement("option"); option.value=valueKey?item[valueKey]:item; option.textContent=labelKey?item[labelKey]:item; select.append(option);});
    wrapper.append(select); host.append(wrapper); selectors[id]=select; select.addEventListener("change",loadDashboard);
  });
  const button=document.createElement("button"); button.type="button"; button.textContent="Limpar filtros"; button.addEventListener("click",()=>{Object.values(selectors).forEach(s=>s.value="");loadDashboard();}); host.append(button);
}

function renderBars(target,data,label,value="ocorrencias",color="coral") {
  if(!data.length){target.innerHTML='<div class="empty">Sem dados para os filtros selecionados</div>';return;}
  const max=Math.max(...data.map(r=>r[value]),1);
  target.innerHTML=data.map(r=>`<div class="bar-row" title="${escapeHtml(r[label])}: ${number.format(r[value])}"><span class="bar-label">${escapeHtml(r[label])}</span><div class="bar-track"><div class="bar-fill ${color}" style="--width:${r[value]/max*100}%"></div></div><span class="bar-value">${compact.format(r[value])}</span></div>`).join("");
}

function renderColumnChart(target,data,label,value="ocorrencias") {
  if(!data.length){target.innerHTML='<div class="empty">Sem dados</div>';return;}
  const max=Math.max(...data.map(r=>r[value]),1);
  target.innerHTML=`<div class="columns">${data.map(r=>`<div class="column-item" title="${escapeHtml(r[label])}: ${number.format(r[value])}"><span class="column-value">${compact.format(r[value])}</span><div class="column" style="--height:${r[value]/max*100}%"></div><small>${escapeHtml(r[label])}</small></div>`).join("")}</div>`;
}

function salesTemplate(){return `<section class="metrics"><article class="metric metric-primary"><span>Faturamento total</span><strong id="revenue">—</strong><small id="records">— registros</small></article><article class="metric"><span>Quantidade vendida</span><strong id="quantity">—</strong><small>unidades no período</small></article><article class="metric metric-product"><span>Produto mais vendido</span><strong id="top-product">—</strong><small id="top-detail">—</small></article></section><section class="grid"><article class="panel panel-wide"><div class="panel-head"><div><p class="eyebrow">Evolução</p><h3>Faturamento e volume por mês</h3></div></div><div id="timeline" class="chart"></div></article><article class="panel"><div class="panel-head"><div><p class="eyebrow">Portfólio</p><h3>Faturamento por marca</h3></div></div><div id="brands" class="bars"></div></article><article class="panel"><div class="panel-head"><div><p class="eyebrow">Alcance</p><h3>Faturamento por continente</h3></div></div><div id="continents" class="bars"></div></article></section>`;}

function violenceTemplate(){const panels=[["month-chart","Calendário","Registros por mês","columns"],["municipalities","Território","Registros por município"],["natures","Tipificação","Registros por natureza"],["day-chart","Calendário","Registros por dia do mês","columns"],["weekdays","Rotina","Registros por dia da semana"],["means-chart","Contexto","Meio empregado"],["gender-chart","Perfil da vítima","Gênero"],["age-chart","Perfil da vítima","Faixa etária"],["school-chart","Perfil da vítima","Escolaridade"],["race-chart","Perfil da vítima","Raça"]];return `<section class="metrics violence-metrics"><article class="metric metric-primary"><span>Registros</span><strong id="occurrences">—</strong><small>linhas após os filtros</small></article><article class="metric"><span>Quantidade informada</span><strong id="reported-quantity">—</strong><small>somente células preenchidas</small></article><article class="metric"><span>Quantidade em kg</span><strong id="quantity-kg">—</strong><small>entorpecentes registrados</small></article><article class="metric"><span>Municípios</span><strong id="municipality-count">—</strong><small>com registros</small></article></section><section class="grid violence-grid">${panels.map(([id,eyebrow,title,type])=>`<article class="panel ${id==='month-chart'?'panel-wide':''}"><div class="panel-head"><div><p class="eyebrow">${eyebrow}</p><h3>${title}</h3></div></div><div id="${id}" class="${type==='columns'?'chart':'bars'}"></div></article>`).join("")}</section>`;}

function renderSales(data){document.querySelector("#revenue").textContent=money.format(data.resumo.faturamento_total);document.querySelector("#quantity").textContent=number.format(data.resumo.quantidade_total);document.querySelector("#records").textContent=`${number.format(data.resumo.registros)} registros`;const top=data.resumo.produto_mais_vendido;document.querySelector("#top-product").textContent=top?.produto||"Sem dados";document.querySelector("#top-detail").textContent=top?`${number.format(top.quantidade)} unidades`:"—";renderColumnChart(document.querySelector("#timeline"),data.por_ano_mes,"ano_mes","faturamento");renderBars(document.querySelector("#brands"),data.por_marca,"marca","faturamento");renderBars(document.querySelector("#continents"),data.por_continente,"continente","faturamento","ink");}

function renderViolence(data){const r=data.resumo;document.querySelector("#occurrences").textContent=number.format(r.ocorrencias);document.querySelector("#reported-quantity").textContent=number.format(r.quantidade_informada);document.querySelector("#quantity-kg").textContent=`${number.format(r.quantidade_kg)} kg`;document.querySelector("#municipality-count").textContent=number.format(r.municipios);renderColumnChart(document.querySelector("#month-chart"),data.por_mes,"rotulo");renderBars(document.querySelector("#municipalities"),data.por_municipio,"municipio");renderBars(document.querySelector("#natures"),data.por_natureza,"natureza");renderColumnChart(document.querySelector("#day-chart"),data.por_dia,"dia");renderBars(document.querySelector("#weekdays"),data.por_dia_semana,"dia_semana","ocorrencias","ink");renderBars(document.querySelector("#means-chart"),data.por_meio_empregado,"meio_empregado");renderBars(document.querySelector("#gender-chart"),data.por_genero,"genero","ocorrencias","ink");renderBars(document.querySelector("#age-chart"),data.por_idade,"idade");renderBars(document.querySelector("#school-chart"),data.por_escolaridade,"escolaridade","ocorrencias","ink");renderBars(document.querySelector("#race-chart"),data.por_raca,"raca");}

function queryParams(source){const p=new URLSearchParams();const map=source==="vendas"?{year:"ano",month:"mes",brand:"marca",continent:"continente"}:{year:"ano",month:"mes",municipality:"municipio",nature:"natureza",weekday:"dia_semana",means:"meio_empregado",gender:"genero"};Object.entries(map).forEach(([id,key])=>{if(selectors[id]?.value)p.set(key,selectors[id].value);});return p;}

async function loadDashboard(){const source=sourceSelect.value;showStatus("Atualizando dados…",true);try{const response=await fetch(`/api/${source}/dashboard?${queryParams(source)}`);if(!response.ok)throw new Error("Falha na API");const data=await response.json();document.querySelector("#dashboard").innerHTML=source==="vendas"?salesTemplate():violenceTemplate();source==="vendas"?renderSales(data):renderViolence(data);showStatus("Dashboard atualizado");}catch(e){console.error(e);showStatus("Não foi possível carregar os dados.",true);}}

async function changeSource(){const source=sourceSelect.value,c=configs[source];document.querySelector("#hero-title").innerHTML=c.title;document.querySelector("#intro").textContent=c.intro;document.querySelector("#source-note").textContent=c.note;showStatus("Carregando fonte…",true);try{const response=await fetch(`/api/${source}/filtros`);const data=await response.json();createFilters(data,source);document.querySelector("#period").textContent=`${formatDate(data.periodo.inicio)} — ${formatDate(data.periodo.fim)}`;await loadDashboard();}catch(e){console.error(e);showStatus("Não foi possível carregar a fonte.",true);}}

sourceSelect.addEventListener("change",changeSource);changeSource();
