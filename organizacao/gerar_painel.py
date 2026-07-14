#!/usr/bin/env python3
"""Gera o painel.html (template editável e offline) a partir do organizacao.db.

O painel é um único arquivo HTML autossuficiente: abre com dois cliques, funciona
sem internet, e permite adicionar/editar/excluir tudo. As alterações ficam salvas
no próprio navegador (localStorage) e podem ser exportadas em JSON/CSV.

Uso:
    python3 gerar_painel.py
"""
from __future__ import annotations

import json
import os
import sqlite3

AQUI = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(AQUI, "organizacao.db")
SAIDA = os.path.join(AQUI, "painel.html")

# Tabelas exportadas para dentro do painel (ordem importa para resolver refs)
TABELAS = [
    "areas", "projetos", "tarefas", "arquivos",
    "contas", "categorias_fin", "transacoes", "metas",
    "canais", "videos",
    "pacientes", "prontuarios", "atendimentos", "evolucoes",
    "familiares", "eventos",
]


def ler_dados(con: sqlite3.Connection) -> dict:
    con.row_factory = sqlite3.Row
    dados = {}
    for t in TABELAS:
        rows = con.execute(f"SELECT * FROM {t} ORDER BY id").fetchall()
        dados[t] = [dict(r) for r in rows]
    return dados


# --- Opções de campos do tipo "select" ------------------------------------
def op(*pares):
    return [{"value": v, "label": l} for v, l in pares]


STATUS_PROJ = op(("ideia", "💡 Ideia"), ("em_andamento", "🚧 Em andamento"),
                 ("pausado", "⏸️ Pausado"), ("concluido", "✅ Concluído"),
                 ("arquivado", "📦 Arquivado"))
PRIORIDADE = op(("baixa", "Baixa"), ("media", "Média"), ("alta", "Alta"))
STATUS_TAREFA = op(("a_fazer", "A fazer"), ("fazendo", "Fazendo"), ("feito", "✅ Feito"))
TIPO_TRANS = op(("receita", "Receita"), ("despesa", "Despesa"), ("transferencia", "Transferência"))
STATUS_TRANS = op(("previsto", "Previsto"), ("realizado", "Realizado"))
STATUS_VIDEO = op(("ideia", "💡 Ideia"), ("roteiro", "📝 Roteiro"), ("gravacao", "🎥 Gravação"),
                  ("edicao", "✂️ Edição"), ("agendado", "📅 Agendado"), ("publicado", "✅ Publicado"))
STATUS_PAC = op(("ativo", "Ativo"), ("inativo", "Inativo"), ("alta", "Alta"))
TIPO_AT = op(("avaliacao", "Avaliação"), ("consulta", "Consulta"), ("sessao", "Sessão"),
             ("retorno", "Retorno"), ("outro", "Outro"))
MODALIDADE = op(("presencial", "Presencial"), ("online", "Online"))
STATUS_AT = op(("agendado", "Agendado"), ("confirmado", "Confirmado"), ("realizado", "Realizado"),
               ("faltou", "Faltou"), ("cancelado", "Cancelado"))
TIPO_CONTA = op(("corrente", "Corrente"), ("poupanca", "Poupança"), ("cartao", "Cartão"),
                ("dinheiro", "Dinheiro"), ("investimento", "Investimento"), ("outro", "Outro"))
TIPO_CAT = op(("receita", "Receita"), ("despesa", "Despesa"))
CAT_EVENTO = op(("aniversario", "🎂 Aniversário"), ("escola", "🏫 Escola"), ("saude", "🏥 Saúde"),
                ("viagem", "✈️ Viagem"), ("reuniao", "👥 Reunião"), ("financeiro", "💳 Financeiro"),
                ("lembrete", "🔔 Lembrete"), ("outro", "Outro"))


def f(key, label, tipo="text", **kw):
    d = {"key": key, "label": label, "type": tipo}
    d.update(kw)
    return d


# Configuração de cada coleção: rótulo, ícone, campo-rótulo, campos e colunas da tabela
CONFIG = {
    "areas": {
        "label": "Áreas", "icon": "🗂️", "labelField": "nome",
        "fields": [f("nome", "Nome"), f("icone", "Ícone"), f("cor", "Cor", "color"),
                   f("descricao", "Descrição", "textarea"), f("ordem", "Ordem", "number")],
        "list": ["icone", "nome", "descricao", "ordem"],
    },
    "projetos": {
        "label": "Projetos", "icon": "📌", "labelField": "titulo",
        "fields": [f("titulo", "Título"), f("area_id", "Área", "ref", ref="areas"),
                   f("status", "Status", "select", options=STATUS_PROJ),
                   f("prioridade", "Prioridade", "select", options=PRIORIDADE),
                   f("progresso", "Progresso (%)", "number"),
                   f("data_inicio", "Início", "date"), f("data_prazo", "Prazo", "date"),
                   f("data_conclusao", "Conclusão", "date"),
                   f("proxima_acao", "Próxima ação"),
                   f("descricao", "Descrição", "textarea"),
                   f("observacoes", "Observações", "textarea")],
        "list": ["titulo", "area_id", "status", "prioridade", "progresso", "data_prazo", "proxima_acao"],
    },
    "tarefas": {
        "label": "Tarefas", "icon": "✅", "labelField": "titulo",
        "fields": [f("titulo", "Título"), f("status", "Status", "select", options=STATUS_TAREFA),
                   f("prioridade", "Prioridade", "select", options=PRIORIDADE),
                   f("prazo", "Prazo", "date"), f("projeto_id", "Projeto", "ref", ref="projetos"),
                   f("area_id", "Área", "ref", ref="areas"),
                   f("observacoes", "Observações", "textarea")],
        "list": ["titulo", "status", "prioridade", "prazo", "projeto_id", "area_id"],
    },
    "arquivos": {
        "label": "Arquivos", "icon": "📎", "labelField": "titulo",
        "fields": [f("titulo", "Título"), f("categoria", "Categoria"),
                   f("area_id", "Área", "ref", ref="areas"),
                   f("projeto_id", "Projeto", "ref", ref="projetos"),
                   f("caminho", "Caminho/URL"), f("data_arquivo", "Data", "date"),
                   f("tags", "Tags"), f("descricao", "Descrição", "textarea")],
        "list": ["titulo", "categoria", "area_id", "projeto_id", "caminho", "data_arquivo"],
    },
    "contas": {
        "label": "Contas", "icon": "🏦", "labelField": "nome",
        "fields": [f("nome", "Nome"), f("tipo", "Tipo", "select", options=TIPO_CONTA),
                   f("instituicao", "Instituição"), f("saldo_inicial", "Saldo inicial", "money")],
        "list": ["nome", "tipo", "instituicao", "saldo_inicial"],
    },
    "categorias_fin": {
        "label": "Categorias", "icon": "🏷️", "labelField": "nome",
        "fields": [f("nome", "Nome"), f("tipo", "Tipo", "select", options=TIPO_CAT), f("grupo", "Grupo")],
        "list": ["nome", "tipo", "grupo"],
    },
    "transacoes": {
        "label": "Lançamentos", "icon": "💰", "labelField": "descricao",
        "fields": [f("data", "Data", "date"), f("descricao", "Descrição"),
                   f("tipo", "Tipo", "select", options=TIPO_TRANS),
                   f("valor", "Valor", "money"), f("conta_id", "Conta", "ref", ref="contas"),
                   f("categoria_id", "Categoria", "ref", ref="categorias_fin"),
                   f("projeto_id", "Projeto", "ref", ref="projetos"),
                   f("status", "Status", "select", options=STATUS_TRANS),
                   f("recorrente", "Recorrente", "checkbox"),
                   f("observacoes", "Observações", "textarea")],
        "list": ["data", "descricao", "tipo", "valor", "conta_id", "categoria_id", "status"],
    },
    "metas": {
        "label": "Metas", "icon": "🎯", "labelField": "titulo",
        "fields": [f("titulo", "Título"), f("area_id", "Área", "ref", ref="areas"),
                   f("valor_atual", "Valor atual", "number"), f("valor_alvo", "Valor alvo", "number"),
                   f("unidade", "Unidade"), f("prazo", "Prazo", "date"),
                   f("observacoes", "Observações", "textarea")],
        "list": ["titulo", "area_id", "valor_atual", "valor_alvo", "unidade", "prazo"],
    },
    "canais": {
        "label": "Canais", "icon": "📺", "labelField": "nome",
        "fields": [f("nome", "Nome"), f("plataforma", "Plataforma"), f("url", "URL"),
                   f("meta_inscritos", "Meta de inscritos", "number"),
                   f("observacoes", "Observações", "textarea")],
        "list": ["nome", "plataforma", "url", "meta_inscritos"],
    },
    "videos": {
        "label": "Vídeos", "icon": "🎬", "labelField": "titulo",
        "fields": [f("titulo", "Título"), f("canal_id", "Canal", "ref", ref="canais"),
                   f("tema", "Tema"), f("status", "Status", "select", options=STATUS_VIDEO),
                   f("data_ideia", "Ideia em", "date"), f("data_gravacao", "Gravação", "date"),
                   f("data_publicacao", "Publicação", "date"), f("url", "URL"),
                   f("views", "Views", "number"), f("roteiro", "Roteiro", "textarea"),
                   f("observacoes", "Observações", "textarea")],
        "list": ["titulo", "status", "tema", "data_publicacao", "views"],
    },
    "pacientes": {
        "label": "Pacientes", "icon": "🧑‍⚕️", "labelField": "nome",
        "fields": [f("nome", "Nome"), f("data_nascimento", "Nascimento", "date"),
                   f("telefone", "Telefone"), f("email", "E-mail"),
                   f("responsavel", "Responsável"), f("convenio", "Convênio"),
                   f("status", "Status", "select", options=STATUS_PAC),
                   f("observacoes", "Observações", "textarea")],
        "list": ["nome", "convenio", "status", "telefone"],
    },
    "prontuarios": {
        "label": "Prontuários", "icon": "📋", "labelField": "paciente_id",
        "fields": [f("paciente_id", "Paciente", "ref", ref="pacientes"),
                   f("queixa_principal", "Queixa principal", "textarea"),
                   f("historico", "Histórico", "textarea"),
                   f("hipotese_diagnostica", "Hipótese diagnóstica", "textarea"),
                   f("cid", "CID"), f("plano_terapeutico", "Plano terapêutico", "textarea")],
        "list": ["paciente_id", "queixa_principal", "cid"],
    },
    "atendimentos": {
        "label": "Atendimentos", "icon": "📅", "labelField": "data",
        "fields": [f("paciente_id", "Paciente", "ref", ref="pacientes"),
                   f("data", "Data", "date"), f("hora_inicio", "Início", "time"),
                   f("hora_fim", "Fim", "time"), f("tipo", "Tipo", "select", options=TIPO_AT),
                   f("modalidade", "Modalidade", "select", options=MODALIDADE),
                   f("status", "Status", "select", options=STATUS_AT),
                   f("valor", "Valor", "money"), f("pago", "Pago", "checkbox"),
                   f("forma_pagamento", "Forma de pagamento"),
                   f("observacoes", "Observações", "textarea")],
        "list": ["data", "hora_inicio", "paciente_id", "tipo", "status", "valor", "pago"],
    },
    "evolucoes": {
        "label": "Evoluções", "icon": "🗒️", "labelField": "data",
        "fields": [f("prontuario_id", "Prontuário", "ref", ref="prontuarios"),
                   f("atendimento_id", "Atendimento", "ref", ref="atendimentos"),
                   f("data", "Data", "date"), f("conteudo", "Conteúdo", "textarea")],
        "list": ["data", "prontuario_id", "conteudo"],
    },
    "familiares": {
        "label": "Família", "icon": "👪", "labelField": "nome",
        "fields": [f("nome", "Nome"), f("parentesco", "Parentesco"),
                   f("data_nascimento", "Nascimento", "date"), f("telefone", "Telefone"),
                   f("observacoes", "Observações", "textarea")],
        "list": ["nome", "parentesco", "data_nascimento", "telefone"],
    },
    "eventos": {
        "label": "Eventos e datas", "icon": "🗓️", "labelField": "titulo",
        "fields": [f("titulo", "Título"), f("categoria", "Categoria", "select", options=CAT_EVENTO),
                   f("data", "Data", "date"), f("hora", "Hora", "time"),
                   f("familiar_id", "Familiar", "ref", ref="familiares"),
                   f("area_id", "Área", "ref", ref="areas"), f("local", "Local"),
                   f("recorrente", "Anual/recorrente", "checkbox"),
                   f("concluido", "Concluído", "checkbox"),
                   f("observacoes", "Observações", "textarea")],
        "list": ["data", "titulo", "categoria", "familiar_id", "concluido"],
    },
}

# Abas do painel (cada uma renderiza uma ou mais coleções; a visão geral é calculada)
ABAS = [
    {"id": "dashboard", "label": "Visão geral", "icon": "📊", "collections": []},
    {"id": "projetos", "label": "Projetos", "icon": "📌", "collections": ["projetos"]},
    {"id": "tarefas", "label": "Tarefas", "icon": "✅", "collections": ["tarefas"]},
    {"id": "financeiro", "label": "Financeiro", "icon": "💰", "collections": ["transacoes"], "custom": "financeiro"},
    {"id": "youtube", "label": "YouTube", "icon": "🎬", "collections": ["videos"]},
    {"id": "pacientes", "label": "Pacientes", "icon": "🧑‍⚕️", "collections": ["pacientes"]},
    {"id": "prontuarios", "label": "Prontuários", "icon": "📋", "collections": [], "custom": "prontuarios"},
    {"id": "agenda", "label": "Agenda", "icon": "📅", "collections": ["atendimentos"], "custom": "agenda"},
    {"id": "familia", "label": "Família", "icon": "👨‍👩‍👧‍👦", "collections": ["familiares", "eventos"]},
    {"id": "arquivos", "label": "Arquivos", "icon": "📎", "collections": ["arquivos"]},
    {"id": "cadastros", "label": "Cadastros", "icon": "⚙️", "collections": ["areas", "contas", "categorias_fin", "canais", "metas"]},
]


def gerar() -> None:
    con = sqlite3.connect(DB)
    dados = ler_dados(con)
    con.close()

    template = HTML_TEMPLATE
    template = template.replace("/*__DADOS__*/", json.dumps(dados, ensure_ascii=False))
    template = template.replace("/*__CONFIG__*/", json.dumps(CONFIG, ensure_ascii=False))
    template = template.replace("/*__ABAS__*/", json.dumps(ABAS, ensure_ascii=False))

    with open(SAIDA, "w", encoding="utf-8") as fh:
        fh.write(template)
    print(f"Painel gerado em {SAIDA}")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meu Hub de Organização</title>
<style>
:root{
  --bg:#0f172a; --panel:#1e293b; --panel2:#273449; --line:#334155;
  --txt:#e2e8f0; --muted:#94a3b8; --accent:#6366f1; --accent2:#8b5cf6;
  --green:#22c55e; --red:#ef4444; --amber:#f59e0b; --blue:#3b82f6;
}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  background:var(--bg);color:var(--txt);font-size:14px}
header{display:flex;align-items:center;gap:14px;padding:14px 20px;
  background:linear-gradient(90deg,#4f46e5,#7c3aed);color:#fff;position:sticky;top:0;z-index:30}
header h1{font-size:18px;margin:0;font-weight:700}
header .sub{font-size:12px;opacity:.85}
header .actions{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap}
button{font:inherit;cursor:pointer;border:none;border-radius:8px;padding:8px 12px;
  background:var(--accent);color:#fff;transition:.15s}
button:hover{filter:brightness(1.1)}
button.ghost{background:rgba(255,255,255,.15)}
button.sec{background:var(--panel2);color:var(--txt);border:1px solid var(--line)}
button.danger{background:var(--red)}
button.sm{padding:4px 8px;font-size:12px;border-radius:6px}
nav{display:flex;gap:4px;overflow-x:auto;padding:10px 16px;background:var(--panel);
  border-bottom:1px solid var(--line);position:sticky;top:52px;z-index:20}
nav button{background:transparent;color:var(--muted);white-space:nowrap;font-weight:600}
nav button.active{background:var(--panel2);color:#fff}
main{padding:20px;max-width:1400px;margin:0 auto}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:18px}
.card h2{margin:0 0 14px;font-size:16px;display:flex;align-items:center;gap:8px}
.grid{display:grid;gap:14px}
.kpis{grid-template-columns:repeat(auto-fit,minmax(180px,1fr))}
.kpi{background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:16px}
.kpi .v{font-size:26px;font-weight:800}
.kpi .l{font-size:12px;color:var(--muted);margin-top:4px}
.kpi .s{font-size:11px;margin-top:6px}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
.toolbar input[type=search],.toolbar select,input,select,textarea{
  background:var(--panel2);border:1px solid var(--line);color:var(--txt);
  border-radius:8px;padding:8px 10px;font:inherit}
.toolbar .spacer{flex:1}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.03em;cursor:pointer;user-select:none}
tbody tr:hover{background:var(--panel2)}
td .cell{max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tag{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:600}
.muted{color:var(--muted)}
.right{text-align:right}
.pill{padding:2px 8px;border-radius:999px;font-size:11px;font-weight:700}
.bar{height:8px;background:var(--line);border-radius:999px;overflow:hidden;min-width:70px}
.bar>i{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2))}
.empty{color:var(--muted);padding:20px;text-align:center}
.pos{color:var(--green)} .neg{color:var(--red)}
.overlay{position:fixed;inset:0;background:rgba(0,0,0,.6);display:none;align-items:flex-start;
  justify-content:center;z-index:50;padding:30px 14px;overflow:auto}
.overlay.open{display:flex}
.modal{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:22px;
  width:100%;max-width:620px}
.modal h3{margin:0 0 16px}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.field{display:flex;flex-direction:column;gap:5px}
.field.full{grid-column:1/-1}
.field label{font-size:12px;color:var(--muted);font-weight:600}
.field input,.field select,.field textarea{width:100%}
.field textarea{min-height:70px;resize:vertical}
.modal .buttons{display:flex;gap:8px;justify-content:flex-end;margin-top:18px}
.chk{display:flex;align-items:center;gap:8px;font-size:13px}
.chk input{width:auto}
.list-item{padding:10px 0;border-bottom:1px solid var(--line)}
.list-item:last-child{border:0}
.two-col{display:grid;grid-template-columns:280px 1fr;gap:16px}
@media(max-width:760px){.form-grid{grid-template-columns:1fr}.two-col{grid-template-columns:1fr}}
.badge-toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
  background:#111827;border:1px solid var(--line);padding:10px 16px;border-radius:10px;
  opacity:0;transition:.3s;z-index:60}
.badge-toast.show{opacity:1}
h3.section{font-size:14px;color:var(--muted);margin:18px 0 8px;text-transform:uppercase;letter-spacing:.04em}
</style>
</head>
<body>
<header>
  <div>
    <h1>🧭 Meu Hub de Organização</h1>
    <div class="sub">Projetos · Finanças · YouTube · Consultório · Família — tudo em um lugar</div>
  </div>
  <div class="actions">
    <button class="ghost" onclick="App.exportJSON()">⬇️ Exportar JSON</button>
    <button class="ghost" onclick="App.restaurar()">↺ Restaurar original</button>
  </div>
</header>
<nav id="nav"></nav>
<main id="main"></main>

<div class="overlay" id="overlay"><div class="modal" id="modal"></div></div>
<div class="badge-toast" id="toast"></div>

<script>
const DADOS_ORIGINAIS = /*__DADOS__*/;
const CONFIG = /*__CONFIG__*/;
const ABAS = /*__ABAS__*/;
const CHAVE = "hub_organizacao_v1";

const App = {
  dados:null, abaAtual:"dashboard", ordenacao:{},

  init(){
    const salvo = localStorage.getItem(CHAVE);
    this.dados = salvo ? JSON.parse(salvo) : structuredClone(DADOS_ORIGINAIS);
    this.renderNav();
    this.irPara(location.hash.replace("#","") || "dashboard");
  },
  salvar(){ localStorage.setItem(CHAVE, JSON.stringify(this.dados)); },
  toast(msg){ const t=document.getElementById("toast"); t.textContent=msg; t.classList.add("show");
    clearTimeout(this._tt); this._tt=setTimeout(()=>t.classList.remove("show"),1800); },

  restaurar(){
    if(!confirm("Descartar TODAS as edições locais e voltar aos dados originais do banco?"))return;
    this.dados = structuredClone(DADOS_ORIGINAIS); this.salvar(); this.render(); this.toast("Dados restaurados");
  },
  exportJSON(){
    this._baixar(JSON.stringify(this.dados,null,2),"organizacao_export.json","application/json");
    this.toast("JSON exportado");
  },
  _baixar(txt,nome,tipo){
    const b=new Blob([txt],{type:tipo}); const u=URL.createObjectURL(b);
    const a=document.createElement("a"); a.href=u; a.download=nome; a.click(); URL.revokeObjectURL(u);
  },

  // ---- navegação --------------------------------------------------------
  renderNav(){
    document.getElementById("nav").innerHTML = ABAS.map(a=>
      `<button data-aba="${a.id}" onclick="App.irPara('${a.id}')">${a.icon} ${a.label}</button>`).join("");
  },
  irPara(id){
    this.abaAtual=id; location.hash=id;
    document.querySelectorAll("#nav button").forEach(b=>
      b.classList.toggle("active", b.dataset.aba===id));
    this.render();
  },
  render(){
    const aba = ABAS.find(a=>a.id===this.abaAtual) || ABAS[0];
    let html="";
    if(aba.id==="dashboard") html=this.viewDashboard();
    else{
      if(aba.custom==="financeiro") html+=this.viewFinanceiro();
      if(aba.custom==="prontuarios") html+=this.viewProntuarios();
      if(aba.custom==="agenda") html+=this.viewAgenda();
      (aba.collections||[]).forEach(c=> html+=this.viewColecao(c));
    }
    document.getElementById("main").innerHTML=html;
  },

  // ---- helpers de dados -------------------------------------------------
  rows(c){ return this.dados[c]||[]; },
  rowById(c,id){ return this.rows(c).find(r=>r.id==id); },
  labelDe(c,id){
    if(id===null||id===undefined||id==="") return "";
    const cfg=CONFIG[c]; const r=this.rowById(c,id); if(!r) return "";
    let lf=cfg.labelField; const fld=cfg.fields.find(x=>x.key===lf);
    if(fld && fld.type==="ref") return this.labelDe(fld.ref, r[lf]); // resolve aninhado (ex.: prontuário->paciente)
    return r[lf] ?? ("#"+id);
  },
  proximoId(c){ return (this.rows(c).reduce((m,r)=>Math.max(m,+r.id||0),0))+1; },

  // ---- formatação -------------------------------------------------------
  fmtMoeda(v){ return (v==null||v==="")?"":Number(v).toLocaleString("pt-BR",{style:"currency",currency:"BRL"}); },
  fmtData(v){ if(!v) return ""; const p=String(v).slice(0,10).split("-");
    return p.length===3? `${p[2]}/${p[1]}/${p[0]}` : v; },
  escapar(s){ return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); },

  corStatus(v){
    const map={concluido:"var(--green)",feito:"var(--green)",publicado:"var(--green)",realizado:"var(--green)",pago:"var(--green)",
      em_andamento:"var(--blue)",fazendo:"var(--blue)",confirmado:"var(--blue)",agendado:"var(--blue)",
      pausado:"var(--amber)",previsto:"var(--amber)",edicao:"var(--amber)",roteiro:"var(--amber)",gravacao:"var(--amber)",
      arquivado:"var(--muted)",inativo:"var(--muted)",cancelado:"var(--muted)",faltou:"var(--red)",negado:"var(--red)",
      alta:"var(--green)",ativo:"var(--green)",ideia:"var(--accent2)",a_fazer:"var(--muted)"};
    return map[v]||"var(--panel2)";
  },

  celula(cfg, fld, r){
    const v=r[fld.key];
    if(fld.type==="ref") return this.escapar(this.labelDe(fld.ref, v));
    if(fld.type==="money") return `<span class="right">${this.fmtMoeda(v)}</span>`;
    if(fld.type==="date") return this.fmtData(v);
    if(fld.type==="checkbox") return v? "✅":"—";
    if(fld.type==="select"){
      const o=(fld.options||[]).find(o=>o.value===v);
      const lbl=o?o.label:(v||"");
      if(["status","prioridade","categoria"].includes(fld.key) && v)
        return `<span class="pill" style="background:${this.corStatus(v)};color:#fff">${this.escapar(lbl)}</span>`;
      return this.escapar(lbl);
    }
    if(fld.key==="progresso") return this.barra(v);
    return this.escapar(v);
  },
  barra(v){ v=+v||0; return `<div style="display:flex;align-items:center;gap:6px">
    <div class="bar"><i style="width:${v}%"></i></div><span class="muted">${v}%</span></div>`; },

  // ---- coleção genérica (tabela + CRUD) ---------------------------------
  viewColecao(c){
    const cfg=CONFIG[c]; const rows=this.filtrar(c);
    const listCols=cfg.list.map(k=>cfg.fields.find(x=>x.key===k)).filter(Boolean);
    const busca=this._busca?.[c]||"";
    const th=listCols.map(fl=>`<th onclick="App.ordenar('${c}','${fl.key}')">${fl.label}</th>`).join("")+"<th></th>";
    const body = rows.length? rows.map(r=>{
      const tds=listCols.map(fl=>`<td><div class="cell">${this.celula(cfg,fl,r)}</div></td>`).join("");
      return `<tr ondblclick="App.editar('${c}',${r.id})">${tds}
        <td class="right" style="white-space:nowrap">
          <button class="sm sec" onclick="App.editar('${c}',${r.id})">✏️</button>
          <button class="sm danger" onclick="App.excluir('${c}',${r.id})">🗑️</button></td></tr>`;
    }).join("") : `<tr><td colspan="${listCols.length+1}" class="empty">Nada por aqui ainda. Clique em “➕ Novo”.</td></tr>`;

    return `<div class="card" id="col-${c}">
      <h2>${cfg.icon} ${cfg.label} <span class="muted" style="font-weight:400">(${rows.length})</span></h2>
      <div class="toolbar">
        <button onclick="App.novo('${c}')">➕ Novo</button>
        <input type="search" placeholder="Buscar…" value="${this.escapar(busca)}"
          oninput="App.setBusca('${c}',this.value)">
        <div class="spacer"></div>
        <button class="sec" onclick="App.exportCSV('${c}')">⬇️ CSV</button>
      </div>
      <div style="overflow-x:auto"><table><thead><tr>${th}</tr></thead><tbody>${body}</tbody></table></div>
    </div>`;
  },
  setBusca(c,v){ this._busca=this._busca||{}; this._busca[c]=v; this.render(); },
  filtrar(c){
    let rows=[...this.rows(c)]; const cfg=CONFIG[c];
    const q=(this._busca?.[c]||"").toLowerCase().trim();
    if(q) rows=rows.filter(r=>cfg.fields.some(fl=>{
      let v=r[fl.key]; if(fl.type==="ref") v=this.labelDe(fl.ref,v);
      return String(v??"").toLowerCase().includes(q);
    }));
    const ord=this.ordenacao[c];
    if(ord){ const {key,dir}=ord; const fl=cfg.fields.find(x=>x.key===key);
      rows.sort((a,b)=>{ let va=a[key],vb=b[key];
        if(fl&&fl.type==="ref"){va=this.labelDe(fl.ref,va);vb=this.labelDe(fl.ref,vb);}
        if(fl&&["money","number"].includes(fl.type)){va=+va||0;vb=+vb||0;}
        va=va??""; vb=vb??""; return (va>vb?1:va<vb?-1:0)*dir; }); }
    return rows;
  },
  ordenar(c,key){ const o=this.ordenacao[c];
    this.ordenacao[c]=(o&&o.key===key)?{key,dir:-o.dir}:{key,dir:1}; this.render(); },

  // ---- modal de edição --------------------------------------------------
  novo(c){ this.abrirModal(c,null); },
  editar(c,id){ this.abrirModal(c,this.rowById(c,id)); },
  abrirModal(c,row){
    const cfg=CONFIG[c]; const ed=!!row; const r=row||{};
    const campos=cfg.fields.map(fl=>{
      const val=r[fl.key];
      const full=(fl.type==="textarea")?" full":"";
      let input;
      if(fl.type==="textarea") input=`<textarea data-k="${fl.key}">${this.escapar(val)}</textarea>`;
      else if(fl.type==="checkbox") input=`<label class="chk"><input type="checkbox" data-k="${fl.key}" ${val?"checked":""}> sim</label>`;
      else if(fl.type==="select"){
        const opts=`<option value="">—</option>`+(fl.options||[]).map(o=>
          `<option value="${o.value}" ${o.value===val?"selected":""}>${this.escapar(o.label)}</option>`).join("");
        input=`<select data-k="${fl.key}">${opts}</select>`;
      } else if(fl.type==="ref"){
        const opts=`<option value="">—</option>`+this.rows(fl.ref).map(rr=>
          `<option value="${rr.id}" ${rr.id==val?"selected":""}>${this.escapar(this.labelDe(fl.ref,rr.id))}</option>`).join("");
        input=`<select data-k="${fl.key}">${opts}</select>`;
      } else {
        const t=fl.type==="money"||fl.type==="number"?"number":fl.type==="date"?"date":fl.type==="time"?"time":fl.type==="color"?"color":"text";
        const step=fl.type==="money"?' step="0.01"':"";
        input=`<input type="${t}"${step} data-k="${fl.key}" value="${this.escapar(val)}">`;
      }
      return `<div class="field${full}"><label>${fl.label}</label>${input}</div>`;
    }).join("");
    document.getElementById("modal").innerHTML=`
      <h3>${ed?"Editar":"Novo"} — ${cfg.label}</h3>
      <div class="form-grid">${campos}</div>
      <div class="buttons">
        <button class="sec" onclick="App.fecharModal()">Cancelar</button>
        <button onclick="App.gravar('${c}',${ed?r.id:"null"})">💾 Salvar</button>
      </div>`;
    document.getElementById("overlay").classList.add("open");
  },
  fecharModal(){ document.getElementById("overlay").classList.remove("open"); },
  gravar(c,id){
    const cfg=CONFIG[c]; const obj=id?{...this.rowById(c,id)}:{};
    document.querySelectorAll("#modal [data-k]").forEach(el=>{
      const k=el.dataset.k; const fl=cfg.fields.find(x=>x.key===k);
      if(fl.type==="checkbox") obj[k]=el.checked?1:0;
      else if(fl.type==="ref"||fl.type==="select") obj[k]=el.value===""?null:(fl.type==="ref"?+el.value:el.value);
      else if(fl.type==="money"||fl.type==="number") obj[k]=el.value===""?null:+el.value;
      else obj[k]=el.value;
    });
    if(id){ const i=this.rows(c).findIndex(r=>r.id==id); this.dados[c][i]=obj; }
    else { obj.id=this.proximoId(c); this.dados[c].push(obj); }
    this.salvar(); this.fecharModal(); this.render(); this.toast(id?"Alterações salvas":"Registro adicionado");
  },
  excluir(c,id){
    if(!confirm("Excluir este registro?")) return;
    this.dados[c]=this.rows(c).filter(r=>r.id!=id); this.salvar(); this.render(); this.toast("Registro excluído");
  },
  exportCSV(c){
    const cfg=CONFIG[c]; const cols=cfg.fields.map(f=>f.key);
    const head=cfg.fields.map(f=>f.label).join(";");
    const linhas=this.rows(c).map(r=>cols.map(k=>{
      const fl=cfg.fields.find(x=>x.key===k); let v=r[k];
      if(fl.type==="ref") v=this.labelDe(fl.ref,v);
      return `"${String(v??"").replace(/"/g,'""')}"`;
    }).join(";"));
    this._baixar([head,...linhas].join("\n"),c+".csv","text/csv");
    this.toast("CSV exportado");
  },

  // ---- Visão geral ------------------------------------------------------
  hoje(){ return new Date().toISOString().slice(0,10); },
  proximos(dias){ const h=new Date(); const f=new Date(); f.setDate(f.getDate()+dias);
    const a=h.toISOString().slice(0,10), b=f.toISOString().slice(0,10);
    return d=>d&&d>=a&&d<=b; },
  viewDashboard(){
    const proj=this.rows("projetos").filter(p=>p.status==="em_andamento");
    const tarefas=this.rows("tarefas").filter(t=>t.status!=="feito");
    const videosProd=this.rows("videos").filter(v=>v.status!=="publicado");
    const mes=this.hoje().slice(0,7);
    let rec=0,desp=0;
    this.rows("transacoes").forEach(t=>{ if(t.status==="realizado"&&String(t.data).slice(0,7)===mes){
      if(t.tipo==="receita")rec+=+t.valor||0; if(t.tipo==="despesa")desp+=+t.valor||0; }});
    const dentro14=this.proximos(14);
    const at=this.rows("atendimentos").filter(a=>dentro14(a.data)&&["agendado","confirmado"].includes(a.status))
      .sort((a,b)=>a.data<b.data?-1:1);
    const ev=this.rows("eventos").filter(e=>!e.concluido&&dentro14(e.data)).sort((a,b)=>a.data<b.data?-1:1);
    const pacAtivos=this.rows("pacientes").filter(p=>p.status==="ativo").length;

    const kpi=(v,l,s="")=>`<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div>${s?`<div class="s">${s}</div>`:""}</div>`;
    const linhaAt=at.length?at.map(a=>`<div class="list-item">📅 <b>${this.fmtData(a.data)}</b> ${a.hora_inicio||""}
      — ${this.escapar(this.labelDe("pacientes",a.paciente_id))}
      <span class="pill" style="background:${this.corStatus(a.status)};color:#fff">${a.status}</span></div>`).join("")
      :`<div class="empty">Sem atendimentos nos próximos 14 dias.</div>`;
    const linhaEv=ev.length?ev.map(e=>`<div class="list-item">🗓️ <b>${this.fmtData(e.data)}</b> ${e.hora||""}
      — ${this.escapar(e.titulo)} <span class="muted">${e.categoria}</span></div>`).join("")
      :`<div class="empty">Sem eventos nos próximos 14 dias.</div>`;
    const linhaProj=proj.length?proj.map(p=>`<div class="list-item">📌 ${this.escapar(p.titulo)}
      ${this.barra(p.progresso)} <span class="muted">${p.data_prazo?"prazo "+this.fmtData(p.data_prazo):""}
      ${p.proxima_acao?"· próximo: "+this.escapar(p.proxima_acao):""}</span></div>`).join("")
      :`<div class="empty">Nenhum projeto em andamento.</div>`;
    const metas=this.rows("metas").map(m=>{ const pct=m.valor_alvo?Math.min(100,Math.round(100*(+m.valor_atual||0)/m.valor_alvo)):0;
      return `<div class="list-item">🎯 ${this.escapar(m.titulo)} ${this.barra(pct)}
        <span class="muted">${(+m.valor_atual||0).toLocaleString("pt-BR")} / ${(+m.valor_alvo||0).toLocaleString("pt-BR")} ${this.escapar(m.unidade||"")}</span></div>`;
    }).join("")||`<div class="empty">Nenhuma meta cadastrada.</div>`;

    return `<div class="card"><h2>📊 Visão geral</h2>
      <div class="grid kpis">
        ${kpi(proj.length,"Projetos em andamento")}
        ${kpi(tarefas.length,"Tarefas pendentes")}
        ${kpi(pacAtivos,"Pacientes ativos")}
        ${kpi(videosProd.length,"Vídeos em produção")}
        ${kpi(this.fmtMoeda(rec),"Receitas do mês")}
        ${kpi(this.fmtMoeda(desp),"Despesas do mês")}
        ${kpi(`<span class="${rec-desp>=0?'pos':'neg'}">${this.fmtMoeda(rec-desp)}</span>`,"Saldo do mês (realizado)")}
      </div></div>
      <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(320px,1fr))">
        <div class="card"><h2>📅 Próximos atendimentos</h2>${linhaAt}</div>
        <div class="card"><h2>🗓️ Próximos eventos e datas</h2>${linhaEv}</div>
        <div class="card"><h2>📌 Projetos em andamento</h2>${linhaProj}</div>
        <div class="card"><h2>🎯 Metas</h2>${metas}</div>
      </div>`;
  },

  // ---- Financeiro (resumo + tabela) ------------------------------------
  viewFinanceiro(){
    const porMes={};
    this.rows("transacoes").forEach(t=>{ if(t.status!=="realizado")return;
      const m=String(t.data).slice(0,7); porMes[m]=porMes[m]||{r:0,d:0};
      if(t.tipo==="receita")porMes[m].r+=+t.valor||0; if(t.tipo==="despesa")porMes[m].d+=+t.valor||0; });
    const meses=Object.keys(porMes).sort().reverse();
    const linhasMes=meses.length?meses.map(m=>{const o=porMes[m];const s=o.r-o.d;
      return `<tr><td>${m}</td><td class="right pos">${this.fmtMoeda(o.r)}</td>
        <td class="right neg">${this.fmtMoeda(o.d)}</td>
        <td class="right ${s>=0?'pos':'neg'}">${this.fmtMoeda(s)}</td></tr>`;}).join("")
      :`<tr><td colspan="4" class="empty">Sem lançamentos realizados.</td></tr>`;

    const saldos=this.rows("contas").map(c=>{ let s=+c.saldo_inicial||0;
      this.rows("transacoes").forEach(t=>{ if(t.status==="realizado"&&t.conta_id==c.id){
        if(t.tipo==="receita")s+=+t.valor||0; if(t.tipo==="despesa")s-=+t.valor||0; }});
      return `<tr><td>${this.escapar(c.nome)}</td><td class="muted">${c.tipo}</td>
        <td class="right ${s>=0?'pos':'neg'}">${this.fmtMoeda(s)}</td></tr>`; }).join("")
      ||`<tr><td colspan="3" class="empty">Nenhuma conta.</td></tr>`;

    return `<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
      <div class="card"><h2>📆 Resumo por mês (realizado)</h2>
        <table><thead><tr><th>Mês</th><th class="right">Receitas</th><th class="right">Despesas</th><th class="right">Saldo</th></tr></thead>
        <tbody>${linhasMes}</tbody></table></div>
      <div class="card"><h2>🏦 Saldo por conta</h2>
        <table><thead><tr><th>Conta</th><th>Tipo</th><th class="right">Saldo atual</th></tr></thead>
        <tbody>${saldos}</tbody></table>
        <p class="muted" style="font-size:12px">Saldo = saldo inicial + receitas − despesas realizadas.</p></div>
    </div>`;
  },

  // ---- Agenda (lista unificada) ----------------------------------------
  viewAgenda(){
    const itens=[];
    this.rows("atendimentos").forEach(a=>itens.push({data:a.data,hora:a.hora_inicio||"",
      txt:"🩺 "+this.labelDe("pacientes",a.paciente_id)+" — "+a.tipo, st:a.status}));
    this.rows("eventos").forEach(e=>itens.push({data:e.data,hora:e.hora||"",
      txt:(CAT_ICON[e.categoria]||"🗓️")+" "+e.titulo, st:e.concluido?"concluido":"pendente"}));
    const hoje=this.hoje();
    const fut=itens.filter(i=>i.data>=hoje).sort((a,b)=>a.data<b.data?-1:a.data>b.data?1:(a.hora<b.hora?-1:1));
    const linhas=fut.length?fut.map(i=>`<div class="list-item"><b>${this.fmtData(i.data)}</b> ${i.hora}
      — ${this.escapar(i.txt)} <span class="pill" style="background:${this.corStatus(i.st)};color:#fff">${i.st}</span></div>`).join("")
      :`<div class="empty">Nada agendado a partir de hoje.</div>`;
    return `<div class="card"><h2>📅 Próximos compromissos (atendimentos + eventos)</h2>${linhas}</div>`;
  },

  // ---- Prontuários (paciente + prontuário + evoluções) -----------------
  viewProntuarios(){
    const pac=this.rows("pacientes");
    const sel=this._pacSel ?? (pac[0]?pac[0].id:null);
    this._pacSel=sel;
    const opts=pac.map(p=>`<option value="${p.id}" ${p.id==sel?"selected":""}>${this.escapar(p.nome)}</option>`).join("");
    if(sel==null) return `<div class="card"><h2>📋 Prontuários</h2><div class="empty">Cadastre um paciente primeiro.</div></div>`;
    const pront=this.rows("prontuarios").find(p=>p.paciente_id==sel);
    const cfgP=CONFIG.prontuarios;
    const campos=pront? cfgP.fields.filter(f=>f.key!=="paciente_id").map(fl=>`
      <div class="field full"><label>${fl.label}</label>
      <div class="cell" style="white-space:pre-wrap;max-width:none">${this.escapar(pront[fl.key])||'<span class="muted">—</span>'}</div></div>`).join("")
      : `<div class="empty">Este paciente ainda não tem prontuário. <button class="sm" onclick="App.criarProntuario(${sel})">Criar prontuário</button></div>`;
    const evos=pront? this.rows("evolucoes").filter(e=>e.prontuario_id==pront.id).sort((a,b)=>a.data<b.data?1:-1):[];
    const linhasEvo=evos.length?evos.map(e=>`<div class="list-item">
      <b>${this.fmtData(e.data)}</b>
      <button class="sm sec" onclick="App.editar('evolucoes',${e.id})">✏️</button>
      <button class="sm danger" onclick="App.excluir('evolucoes',${e.id})">🗑️</button>
      <div style="white-space:pre-wrap;margin-top:4px">${this.escapar(e.conteudo)}</div></div>`).join("")
      :`<div class="empty">Sem evoluções registradas.</div>`;
    return `<div class="card"><h2>📋 Prontuários</h2>
      <div class="toolbar"><label class="muted">Paciente:</label>
        <select onchange="App.selPac(this.value)">${opts}</select>
        ${pront?`<button class="sec" onclick="App.editar('prontuarios',${pront.id})">✏️ Editar prontuário</button>`:""}
      </div></div>
      <div class="two-col">
        <div class="card"><h2>Ficha clínica</h2><div class="form-grid" style="grid-template-columns:1fr">${campos}</div></div>
        <div class="card"><h2>🗒️ Evoluções</h2>
          ${pront?`<button onclick="App.novaEvolucao(${pront.id})">➕ Nova evolução</button>`:""}
          <div style="margin-top:10px">${linhasEvo}</div></div>
      </div>`;
  },
  selPac(id){ this._pacSel=+id; this.render(); },
  criarProntuario(pacId){ const obj={id:this.proximoId("prontuarios"),paciente_id:+pacId,
    queixa_principal:"",historico:"",hipotese_diagnostica:"",cid:"",plano_terapeutico:""};
    this.dados.prontuarios.push(obj); this.salvar(); this.render(); this.toast("Prontuário criado"); },
  novaEvolucao(prontId){ this.abrirModal("evolucoes",{prontuario_id:+prontId,data:this.hoje()}); },

  init_ready:false
};

const CAT_ICON={aniversario:"🎂",escola:"🏫",saude:"🏥",viagem:"✈️",reuniao:"👥",financeiro:"💳",lembrete:"🔔",outro:"🗓️"};

document.getElementById("overlay").addEventListener("click",e=>{ if(e.target.id==="overlay") App.fecharModal(); });
window.addEventListener("hashchange",()=>{ const h=location.hash.replace("#",""); if(h&&h!==App.abaAtual) App.irPara(h); });
App.init();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    gerar()
