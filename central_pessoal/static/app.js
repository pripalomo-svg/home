const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const api = async (path, options = {}) => {
  const response = await fetch(`/api/${path}`, {
    headers: {"Content-Type": "application/json"},
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Não foi possível concluir.");
  return data;
};
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[char]));
const money = (value) => Number(value || 0).toLocaleString("pt-BR", {style: "currency", currency: "BRL"});
const prettyDate = (value, time = false) => {
  if (!value) return "Sem data";
  const parsed = new Date(`${value}${value.length === 10 ? "T12:00:00" : ""}`);
  return parsed.toLocaleDateString("pt-BR", time ? {day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit"} : {});
};
const labels = {
  ideia: "Ideia", planejado: "Planejado", em_andamento: "Em andamento", pausado: "Pausado",
  concluido: "Concluído", arquivado: "Arquivado", aberta: "Aberta", fazendo: "Fazendo",
  concluida: "Concluída", cancelada: "Cancelada", agendado: "Agendado", confirmado: "Confirmado",
  realizado: "Realizado", cancelado: "Cancelado", faltou: "Faltou", previsto: "Previsto",
  pago: "Pago", recebido: "Recebido", atrasado: "Atrasado", receita: "Receita", despesa: "Despesa",
};

const viewConfig = {
  projetos: {resource: "projects", eyebrow: "ORGANIZAÇÃO", title: "Projetos", description: "Transforme ideias soltas em próximas ações claras.", newLabel: "Novo projeto"},
  tarefas: {resource: "tasks", eyebrow: "ORGANIZAÇÃO", title: "Tarefas", description: "Uma lista única para não depender da memória.", newLabel: "Nova tarefa"},
  arquivos: {resource: "files", eyebrow: "DOCUMENTOS", title: "Arquivos", description: "Um índice para encontrar qualquer documento sem movê-lo.", newLabel: "Indexar arquivo"},
  pacientes: {resource: "patients", eyebrow: "CONSULTÓRIO", title: "Pacientes", description: "Cadastros e acesso rápido aos prontuários.", newLabel: "Novo paciente"},
  agenda: {resource: "appointments", eyebrow: "CONSULTÓRIO", title: "Agenda", description: "Atendimentos, datas, valores e situação.", newLabel: "Novo atendimento"},
  financas: {resource: "finances", eyebrow: "VIDA FINANCEIRA", title: "Finanças", description: "Receitas e despesas pessoais e profissionais.", newLabel: "Novo lançamento"},
};

const field = (name, label, type = "text", extra = {}) => ({name, label, type, ...extra});
const forms = {
  projects: [
    field("nome", "Nome do projeto", "text", {required: true, full: true}),
    field("area_id", "Área", "area", {required: true}),
    field("status", "Status", "select", {options: ["ideia", "planejado", "em_andamento", "pausado", "concluido"]}),
    field("prioridade", "Prioridade", "select", {options: ["baixa", "media", "alta"]}),
    field("prazo", "Prazo", "date"),
    field("descricao", "Descrição", "textarea", {full: true}),
    field("proxima_acao", "Próxima ação", "text", {full: true}),
  ],
  tasks: [
    field("titulo", "Tarefa", "text", {required: true, full: true}),
    field("area_id", "Área", "area"),
    field("projeto_id", "Projeto", "project"),
    field("prioridade", "Prioridade", "select", {options: ["baixa", "media", "alta"]}),
    field("prazo", "Prazo", "date"),
    field("observacoes", "Observações", "textarea", {full: true}),
  ],
  patients: [
    field("nome", "Nome do paciente", "text", {required: true, full: true}),
    field("telefone", "Telefone", "tel"),
    field("email", "E-mail", "email"),
    field("observacoes", "Observações cadastrais", "textarea", {full: true}),
  ],
  appointments: [
    field("paciente_id", "Paciente", "patient", {required: true}),
    field("appointment_date", "Data (DD/MM/AAAA)", "text", {required: true, placeholder: "21/07/2026"}),
    field("appointment_time", "Horário", "time", {required: true}),
    field("tipo", "Tipo", "select", {options: ["consulta", "retorno", "avaliacao", "outro"]}),
    field("status", "Status", "select", {options: ["agendado", "confirmado", "realizado", "cancelado", "faltou"]}),
    field("valor", "Valor", "number", {step: ".01", min: "0"}),
    field("observacoes", "Observações da agenda", "textarea", {full: true}),
  ],
  records: [
    field("paciente_id", "Paciente", "patient", {required: true}),
    field("data_registro", "Data", "date", {required: true}),
    field("titulo", "Título do registro", "text", {required: true, full: true}),
    field("conteudo", "Evolução / anotações clínicas", "textarea", {required: true, full: true}),
  ],
  finances: [
    field("descricao", "Descrição", "text", {required: true, full: true}),
    field("data", "Data", "date", {required: true}),
    field("tipo", "Tipo", "select", {options: ["receita", "despesa"]}),
    field("categoria", "Categoria", "text", {required: true}),
    field("valor", "Valor", "number", {required: true, step: ".01", min: "0"}),
    field("status", "Status", "select", {options: ["previsto", "pago", "recebido", "atrasado"]}),
    field("projeto_id", "Projeto relacionado", "project"),
    field("observacoes", "Observações", "textarea", {full: true}),
  ],
  files: [
    field("nome", "Nome do documento", "text", {required: true, full: true}),
    field("caminho", "Caminho no computador", "text", {required: true, full: true}),
    field("area_id", "Área", "area", {required: true}),
    field("projeto_id", "Projeto", "project"),
    field("categoria", "Categoria", "text"),
    field("data_documento", "Data do documento", "date"),
    field("tags", "Tags, separadas por vírgula", "text", {full: true}),
    field("descricao", "Descrição", "textarea", {full: true}),
  ],
};

let currentView = "inicio";
let currentResource = null;
let searchTimer;
let references = {areas: [], patients: [], projects: []};
let presetValues = {};

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2400);
}

async function loadReferences() {
  const [areas, people, projects] = await Promise.all([
    api("areas"), api("people"), api("projects"),
  ]);
  references = {areas, patients: people.filter(person => person.tipo === "paciente"), projects};
}

function renderDashboard(data) {
  const cards = [
    ["lilac", "◫", data.totals.projetos, "Projetos ativos"],
    ["amber", "✓", data.totals.tarefas, "Tarefas abertas"],
    ["mint", "♙", data.totals.pacientes, "Pacientes ativos"],
    ["blue", "⌁", data.totals.arquivos, "Arquivos indexados"],
  ];
  $("#stats").innerHTML = cards.map(card => `
    <div class="stat"><span class="stat-icon ${card[0]}">${card[1]}</span>
      <div><strong>${card[2]}</strong><small>${card[3]}</small></div></div>`).join("");
  $("#dashboard-projects").innerHTML = data.recent_projects.length ? data.recent_projects.slice(0, 4).map(project => `
    <div class="project-item">
      <div class="project-top"><h3>${esc(project.nome)}</h3><span class="status">${esc(labels[project.status] || project.status)}</span></div>
      <p>${esc(project.proxima_acao || project.descricao || "Defina a próxima ação")}</p>
      <div class="project-meta"><span class="tag">${esc(project.area)}</span><span>${project.prazo ? prettyDate(project.prazo) : "Sem prazo"}</span></div>
    </div>`).join("") : empty("Nenhum projeto ativo.");
  $("#dashboard-tasks").innerHTML = data.priority_tasks.length ? data.priority_tasks.map(task => `
    <div class="task"><button class="check" data-complete="${task.id}" aria-label="Concluir tarefa"></button>
      <div><strong>${esc(task.titulo)}</strong><small>${esc(task.area || "Geral")}${task.prazo ? ` · ${prettyDate(task.prazo)}` : ""}</small></div></div>`).join("") : empty("Nenhuma tarefa aberta.");
  $("#dashboard-appointments").innerHTML = data.next_appointments.length ? data.next_appointments.map(item => {
    const appointment = new Date(item.data_hora);
    return `<div class="appointment"><span class="appointment-date">${appointment.toLocaleDateString("pt-BR", {month: "short"}).replace(".", "")}<b>${appointment.getDate()}</b></span>
      <div><strong>${esc(item.paciente)}</strong><small>${appointment.toLocaleTimeString("pt-BR", {hour: "2-digit", minute: "2-digit"})} · ${esc(item.tipo)}</small></div></div>`;
  }).join("") : empty("Nenhum atendimento futuro.");
  const income = data.finance.receitas;
  const expenses = data.finance.despesas;
  $("#finance-summary").innerHTML = `<div class="finance-numbers">
    <div><small>Entradas</small><strong class="positive">${money(income)}</strong></div>
    <div><small>Saídas</small><strong class="negative">${money(expenses)}</strong></div>
    </div><p class="balance"><span>Saldo do mês</span><strong>${money(income - expenses)}</strong></p>`;
}

const empty = message => `<div class="empty">${esc(message)}</div>`;

async function loadDashboard() {
  const data = await api("dashboard");
  renderDashboard(data);
}

function rowMarkup(resource, item) {
  if (resource === "projects") return row(item.nome, item.proxima_acao || item.descricao, item.area, labels[item.status], item.prazo ? prettyDate(item.prazo) : "Sem prazo");
  if (resource === "tasks") return row(item.titulo, item.observacoes, item.area || "Geral", labels[item.status], item.prazo ? prettyDate(item.prazo) : "Sem prazo", `<button class="row-action" data-complete="${item.id}">Concluir</button>`);
  if (resource === "patients") return row(item.nome, item.observacoes, item.telefone || "Sem telefone", item.email || "Sem e-mail", "", `<button class="row-action" data-record="${item.id}">＋ Prontuário</button>`);
  if (resource === "appointments") return row(item.paciente, item.observacoes, prettyDate(item.data_hora, true), item.tipo, labels[item.status]);
  if (resource === "finances") return row(item.descricao, item.observacoes, item.categoria, labels[item.status], money(item.valor), `<span class="${item.tipo === "receita" ? "positive" : "negative"}">${esc(labels[item.tipo])}</span>`);
  if (resource === "files") return row(item.nome, item.caminho, item.area, item.categoria, item.tags || "Sem tags");
  return "";
}

function row(title, subtitle, cellOne, cellTwo, cellThree, action = "") {
  return `<div class="data-row">
    <div class="data-main"><strong>${esc(title)}</strong><small>${esc(subtitle || "Sem observações")}</small></div>
    <div class="data-cell">${esc(cellOne || "—")}</div>
    <div class="data-cell">${esc(cellTwo || "—")}<br>${esc(cellThree || "")}</div>
    <div>${action}</div>
  </div>`;
}

async function loadResource(query = "") {
  const items = await api(`${currentResource}${query ? `?q=${encodeURIComponent(query)}` : ""}`);
  $("#resource-list").innerHTML = items.length ? items.map(item => rowMarkup(currentResource, item)).join("") : empty("Nenhum registro encontrado.");
  $("#result-count").textContent = `${items.length} registro${items.length === 1 ? "" : "s"}`;
}

async function navigate(view) {
  currentView = view;
  currentResource = viewConfig[view]?.resource || null;
  $$(".nav-item").forEach(item => item.classList.toggle("active", item.dataset.view === view));
  $$(".view").forEach(section => section.classList.remove("active"));
  if (view === "inicio") {
    $("#view-inicio").classList.add("active");
    await loadDashboard();
  } else {
    const config = viewConfig[view];
    $("#view-list").classList.add("active");
    $("#list-eyebrow").textContent = config.eyebrow;
    $("#list-title").textContent = config.title;
    $("#list-description").textContent = config.description;
    $("#page-new").textContent = `＋ ${config.newLabel}`;
    $("#filter-pills").innerHTML = `<button class="pill active">Todos</button>`;
    await loadResource($("#global-search").value);
  }
  $(".sidebar").classList.remove("open");
  location.hash = view;
}

function optionMarkup(type) {
  const source = type === "area" ? references.areas : type === "patient" ? references.patients : references.projects;
  return `<option value="">Selecione…</option>${source.map(item => `<option value="${item.id}">${esc(item.nome)}</option>`).join("")}`;
}

function renderField(config) {
  const common = `${config.required ? "required" : ""} ${config.step ? `step="${config.step}"` : ""} ${config.min ? `min="${config.min}"` : ""}`;
  let control;
  if (config.type === "textarea") control = `<textarea name="${config.name}" ${common}></textarea>`;
  else if (config.type === "select") control = `<select name="${config.name}" ${common}>${config.options.map(value => `<option value="${value}">${esc(labels[value] || value)}</option>`).join("")}</select>`;
  else if (["area", "patient", "project"].includes(config.type)) control = `<select name="${config.name}" ${common}>${optionMarkup(config.type)}</select>`;
  else control = `<input name="${config.name}" type="${config.type}" ${common} ${config.placeholder ? `placeholder="${esc(config.placeholder)}"` : ""}>`;
  return `<div class="field ${config.full ? "full" : ""}"><label>${esc(config.label)}</label>${control}</div>`;
}

async function openModal(resource = currentResource, presets = {}) {
  await loadReferences();
  currentResource = resource;
  presetValues = presets;
  const title = resource === "records" ? "Novo prontuário" : {
    projects: "Novo projeto", tasks: "Nova tarefa", patients: "Novo paciente",
    appointments: "Novo atendimento", finances: "Novo lançamento", files: "Indexar arquivo",
  }[resource];
  $("#modal-title").textContent = title;
  $("#form-fields").innerHTML = forms[resource].map(renderField).join("");
  $("#form-error").textContent = "";
  const form = $("#item-form");
  form.reset();
  const defaults = {
    data: new Date().toISOString().slice(0, 10),
    data_registro: new Date().toISOString().slice(0, 10),
    appointment_date: new Date().toLocaleDateString("pt-BR"),
    appointment_time: "09:00",
    status: resource === "finances" ? "previsto" : undefined,
    ...presets,
  };
  Object.entries(defaults).forEach(([key, value]) => {
    if (value !== undefined && form.elements[key]) form.elements[key].value = value;
  });
  $("#modal-overlay").classList.add("open");
  setTimeout(() => form.querySelector("input,select,textarea")?.focus(), 50);
}

function closeModal() {
  $("#modal-overlay").classList.remove("open");
  $("#item-form").reset();
}

async function submitForm(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const data = Object.fromEntries([...formData.entries()].filter(([, value]) => value !== ""));
  try {
    ["area_id", "projeto_id", "paciente_id", "atendimento_id"].forEach(key => {
      if (data[key]) data[key] = Number(data[key]);
    });
    if (currentResource === "appointments") {
      const parts = data.appointment_date.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
      if (!parts) throw new Error("Use a data no formato DD/MM/AAAA.");
      const isoDate = `${parts[3]}-${parts[2]}-${parts[1]}`;
      const check = new Date(`${isoDate}T12:00:00`);
      if (Number.isNaN(check.getTime()) || check.toISOString().slice(0, 10) !== isoDate) {
        throw new Error("Informe uma data válida.");
      }
      data.data_hora = `${isoDate}T${data.appointment_time}`;
      delete data.appointment_date;
      delete data.appointment_time;
    }
    if (data.valor !== undefined) data.valor = Number(data.valor);
    await api(currentResource, {method: "POST", body: JSON.stringify(data)});
    closeModal();
    showToast("Registro salvo com sucesso.");
    await loadReferences();
    if (currentView === "inicio") await loadDashboard();
    else {
      currentResource = viewConfig[currentView].resource;
      await loadResource($("#global-search").value);
    }
  } catch (error) {
    $("#form-error").textContent = error.message;
  }
}

document.addEventListener("click", async event => {
  const nav = event.target.closest("[data-view]");
  const go = event.target.closest("[data-go]");
  const complete = event.target.closest("[data-complete]");
  const record = event.target.closest("[data-record]");
  if (nav) navigate(nav.dataset.view);
  if (go) navigate(go.dataset.go);
  if (complete) {
    await api(`tasks/${complete.dataset.complete}`, {method: "PATCH", body: JSON.stringify({status: "concluida"})});
    showToast("Tarefa concluída.");
    currentView === "inicio" ? await loadDashboard() : await loadResource($("#global-search").value);
  }
  if (record) openModal("records", {paciente_id: record.dataset.record});
});

$("#new-button").addEventListener("click", () => {
  if (currentView === "inicio") navigate("tarefas").then(() => openModal("tasks"));
  else openModal();
});
$("#page-new").addEventListener("click", () => openModal());
$("#modal-close").addEventListener("click", closeModal);
$("#modal-cancel").addEventListener("click", closeModal);
$("#modal-overlay").addEventListener("click", event => { if (event.target === event.currentTarget) closeModal(); });
$("#item-form").addEventListener("submit", submitForm);
$("#mobile-menu").addEventListener("click", () => $(".sidebar").classList.toggle("open"));
$("#global-search").addEventListener("input", event => {
  if (currentView === "inicio") return;
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => loadResource(event.target.value), 180);
});
document.addEventListener("keydown", event => { if (event.key === "Escape") closeModal(); });

const now = new Date();
$("#today-label").textContent = now.toLocaleDateString("pt-BR", {weekday: "long", day: "numeric", month: "long"}).toUpperCase();
loadReferences()
  .then(() => navigate(location.hash.slice(1) in viewConfig || location.hash === "#inicio" ? location.hash.slice(1) : "inicio"))
  .catch(error => showToast(error.message));
