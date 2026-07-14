#!/usr/bin/env python3
"""Gera o template de controle editável (controle.html) a partir de reembolsos.db.

Uso:  python3 gerar_controle.py

O controle.html é autocontido e funciona offline:
  - vem pré-carregado com todos os reembolsos do banco;
  - permite ADICIONAR, EDITAR e EXCLUIR reembolsos direto no navegador;
  - as alterações são salvas automaticamente no navegador (localStorage);
  - exporta CSV/JSON e importa JSON de volta;
  - aba de pendências mostra o que está aguardando resposta e a próxima ação.
"""

import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "reembolsos.db"
SAIDA = BASE / "controle.html"


def carregar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    dados = []
    for r in conn.execute("SELECT * FROM vw_reembolsos ORDER BY data_atendimento DESC"):
        d = dict(r)
        d["documentos"] = d["documentos"].split("; ") if d["documentos"] else []
        d["proxima_acao"] = ""
        dados.append(d)
    conn.close()
    return dados


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Controle de Reembolsos · Família Palomo</title>
<style>
  * { box-sizing:border-box; margin:0; padding:0; }
  :root {
    --bg:#f4f6fb; --card:#fff; --ink:#17203a; --mut:#8a93a8; --line:#e6e9f2;
    --blue:#2f6fed; --green:#0fa968; --amber:#e8930c; --red:#e14b5a; --violet:#7c5cde;
  }
  body { font-family:'Segoe UI',system-ui,Arial,sans-serif; background:var(--bg); color:var(--ink); }
  header { background:linear-gradient(120deg,#141b31,#1d2c54 55%,#28407c); color:#fff;
           padding:22px 34px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; }
  header h1 { font-size:1.35rem; } header h1 em { color:#7ea4ff; font-style:normal; }
  header p { color:rgba(255,255,255,.62); font-size:.78rem; margin-top:4px; }
  .hbtns { display:flex; gap:8px; flex-wrap:wrap; }
  .btn { padding:9px 16px; border-radius:10px; border:none; cursor:pointer; font-size:.82rem;
         font-weight:700; background:rgba(255,255,255,.14); color:#fff; }
  .btn:hover { background:rgba(255,255,255,.25); }
  .btn.primario { background:var(--blue); } .btn.primario:hover { background:#2557c4; }
  .btn.verde { background:var(--green); } .btn.perigo { background:var(--red); }
  .btn.claro { background:#eef1f8; color:var(--ink); } .btn.claro:hover { background:#e0e5f2; }

  .wrap { max-width:1280px; margin:0 auto; padding:22px 30px 60px; }
  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(175px,1fr)); gap:13px; margin-bottom:20px; }
  .stat { background:var(--card); border-radius:14px; padding:15px 17px; box-shadow:0 1px 8px rgba(23,32,58,.07); border-top:4px solid var(--blue); }
  .stat.g{border-color:var(--green)} .stat.a{border-color:var(--amber)} .stat.r{border-color:var(--red)}
  .stat b { display:block; font-size:1.35rem; font-weight:800; margin-top:4px; }
  .stat span { font-size:.68rem; text-transform:uppercase; letter-spacing:.06em; color:var(--mut); }
  .stat small { color:var(--mut); font-size:.71rem; }

  .tabs { display:flex; gap:6px; margin-bottom:16px; flex-wrap:wrap; }
  .tab { padding:9px 20px; border-radius:24px; background:var(--card); border:1px solid var(--line);
         cursor:pointer; font-size:.85rem; font-weight:600; color:#5a647d; }
  .tab.on { background:var(--blue); color:#fff; border-color:var(--blue); }

  .filters { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px; align-items:center; }
  .filters select, .filters input { padding:8px 12px; border:1px solid var(--line); border-radius:9px;
      background:var(--card); font-size:.84rem; color:var(--ink); outline:none; }
  .filters input { flex:1; min-width:200px; }

  .panel { background:var(--card); border-radius:14px; box-shadow:0 1px 8px rgba(23,32,58,.07); overflow:auto; }
  table { width:100%; border-collapse:collapse; font-size:.83rem; }
  th { text-align:left; padding:11px 12px; background:#f7f8fc; color:var(--mut); font-size:.69rem;
       text-transform:uppercase; letter-spacing:.05em; border-bottom:1px solid var(--line);
       cursor:pointer; user-select:none; white-space:nowrap; }
  td { padding:9px 12px; border-bottom:1px solid #f0f2f8; vertical-align:middle; }
  tr.row:hover { background:#f8faff; }
  td.num, th.num { text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; }

  .chip { display:inline-block; padding:3px 11px; border-radius:20px; font-size:.71rem; font-weight:700; white-space:nowrap; }
  .st-pago{background:#e2f6ec;color:#0b7d4d} .st-pago_parcial{background:#fef2dd;color:#a36508}
  .st-em_analise{background:#e5edff;color:#2b5cc7} .st-negado{background:#fde5e8;color:#bb2c3d}
  .st-solicitado{background:#efe9ff;color:#6740c6}
  select.status-sel { border:1px solid transparent; border-radius:20px; padding:3px 8px; font-size:.71rem;
      font-weight:700; cursor:pointer; appearance:auto; background:transparent; }
  .doclink { display:inline-flex; align-items:center; gap:4px; font-size:.72rem; color:var(--blue);
             text-decoration:none; background:#eef3ff; padding:2px 8px; border-radius:7px; margin:1px 3px 1px 0; }
  .muted { color:var(--mut); } .nowrap { white-space:nowrap; }
  .acao-btn { border:none; background:#eef1f8; border-radius:8px; padding:5px 9px; cursor:pointer; font-size:.78rem; }
  .acao-btn:hover { background:#dbe3f5; }

  /* modal */
  .overlay { display:none; position:fixed; inset:0; background:rgba(15,22,45,.55); z-index:50;
             align-items:flex-start; justify-content:center; padding:40px 16px; overflow:auto; }
  .overlay.on { display:flex; }
  .modal { background:#fff; border-radius:16px; width:640px; max-width:100%; padding:24px 26px 22px;
           box-shadow:0 18px 60px rgba(0,0,0,.3); }
  .modal h2 { font-size:1.05rem; margin-bottom:16px; }
  .fgrid { display:grid; grid-template-columns:1fr 1fr; gap:12px 14px; }
  .fgrid .full { grid-column:1/-1; }
  label { display:block; font-size:.7rem; text-transform:uppercase; letter-spacing:.05em;
          color:var(--mut); margin-bottom:4px; font-weight:700; }
  .modal input, .modal select, .modal textarea { width:100%; padding:9px 11px; border:1px solid var(--line);
      border-radius:9px; font-size:.85rem; color:var(--ink); outline:none; font-family:inherit; }
  .modal input:focus, .modal select:focus, .modal textarea:focus { border-color:var(--blue); }
  .modal-acts { display:flex; justify-content:space-between; margin-top:18px; gap:10px; }
  .modal-acts .dir { display:flex; gap:10px; }

  /* pendências */
  .pend-card { background:var(--card); border-radius:13px; padding:15px 18px; margin-bottom:10px;
               box-shadow:0 1px 6px rgba(23,32,58,.07); border-left:5px solid var(--amber);
               display:grid; grid-template-columns:1fr auto; gap:6px 16px; }
  .pend-card.vencida { border-left-color:var(--red); }
  .pend-card b { font-size:.88rem; }
  .pend-card .meta { font-size:.76rem; color:var(--mut); margin-top:3px; }
  .pend-card .dias { font-size:1.15rem; font-weight:800; text-align:right; }
  .pend-card .dias small { display:block; font-size:.66rem; color:var(--mut); font-weight:600; }
  .pend-acao { grid-column:1/-1; display:flex; gap:8px; align-items:center; margin-top:6px; }
  .pend-acao input { flex:1; padding:7px 11px; border:1px dashed #c9d2e6; border-radius:8px; font-size:.8rem; outline:none; }
  .pend-acao input:focus { border-color:var(--blue); border-style:solid; }

  .aviso { background:#fff8e8; border:1px solid #f3dfae; color:#7a5b0d; border-radius:11px;
           padding:10px 15px; font-size:.78rem; margin-bottom:16px; }
  .section { display:none; } .section.on { display:block; }
  footer { text-align:center; color:var(--mut); font-size:.73rem; margin-top:32px; }
  @media print { header .hbtns, .tabs, .filters, .acao-btn { display:none!important } }
</style>
</head>
<body>
<header>
  <div>
    <h1>🗂️ Controle de Reembolsos · <em>Família Palomo</em></h1>
    <p>Template editável · alterações salvas automaticamente neste navegador · <span id="salvo-em"></span></p>
  </div>
  <div class="hbtns">
    <button class="btn primario" onclick="abrirModal()">➕ Novo reembolso</button>
    <button class="btn" onclick="exportarCSV()">⬇️ CSV</button>
    <button class="btn" onclick="exportarJSON()">⬇️ JSON</button>
    <button class="btn" onclick="document.getElementById('imp').click()">⬆️ Importar</button>
    <input type="file" id="imp" accept=".json" style="display:none" onchange="importarJSON(event)">
    <button class="btn" onclick="window.print()">🖨️</button>
    <button class="btn perigo" onclick="restaurar()">↺ Restaurar original</button>
  </div>
</header>

<div class="wrap">
  <div class="stats" id="stats"></div>

  <div class="tabs">
    <div class="tab on" data-sec="controle">📋 Todos os reembolsos</div>
    <div class="tab" data-sec="pendencias">⏳ Pendências <span id="pend-n"></span></div>
  </div>

  <div class="section on" id="sec-controle">
    <div class="filters">
      <select id="f-ben"><option value="">Todos os beneficiários</option></select>
      <select id="f-status">
        <option value="">Todos os status</option>
        <option value="solicitado">Solicitado</option><option value="em_analise">Em análise</option>
        <option value="pago">Pago</option><option value="pago_parcial">Pago parcial</option>
        <option value="negado">Negado</option>
      </select>
      <select id="f-ano"><option value="">Todos os anos</option></select>
      <input id="f-busca" placeholder="🔍 Buscar prestador, claim, NF…">
    </div>
    <div class="panel">
      <table>
        <thead><tr>
          <th data-k="data_atendimento">Data</th><th data-k="beneficiario">Beneficiário</th>
          <th data-k="prestador">Prestador</th><th data-k="tipo">Tipo</th>
          <th class="num" data-k="valor_pago">Pago R$</th>
          <th class="num" data-k="valor_reembolsado">Reemb. R$</th>
          <th data-k="status">Status</th><th>Claim / NF</th><th>Docs</th><th></th>
        </tr></thead>
        <tbody id="corpo"></tbody>
        <tfoot><tr id="rodape" style="font-weight:700;background:#f7f8fc"></tr></tfoot>
      </table>
    </div>
  </div>

  <div class="section" id="sec-pendencias">
    <div class="aviso">⏳ Claims <b>em análise</b> ou <b>a enviar</b>, do mais antigo para o mais recente.
      Anote a <b>próxima ação</b> em cada um (ex.: "cobrar HR", "reenviar com NF correta") — fica salvo automaticamente.
      Com mais de 45 dias sem resposta ficam <span style="color:var(--red);font-weight:700">vermelhos</span>.</div>
    <div id="pendlist"></div>
  </div>

  <footer>Template de controle · para levar as alterações de volta ao banco: exporte o JSON e rode <code>python3 importar_controle.py arquivo.json</code></footer>
</div>

<!-- modal -->
<div class="overlay" id="overlay" onclick="if(event.target===this)fecharModal()">
  <div class="modal">
    <h2 id="m-titulo">Novo reembolso</h2>
    <div class="fgrid">
      <div><label>Beneficiário</label><select id="m-ben"></select></div>
      <div><label>Tipo</label><select id="m-tipo">
        <option value="consulta">Consulta</option><option value="exame">Exame</option>
        <option value="terapia">Terapia</option><option value="medicamento">Medicamento</option>
        <option value="produto">Produto</option><option value="cirurgia">Cirurgia</option>
        <option value="honorario">Honorário</option><option value="outro">Outro</option></select></div>
      <div class="full"><label>Prestador</label><input id="m-prest" list="prestadores"><datalist id="prestadores"></datalist></div>
      <div><label>Data do atendimento</label><input type="date" id="m-data"></div>
      <div><label>Data do pagamento/acerto</label><input type="date" id="m-datapag"></div>
      <div><label>Valor pago (R$)</label><input type="number" step="0.01" min="0" id="m-pago"></div>
      <div><label>Valor reembolsado (R$)</label><input type="number" step="0.01" min="0" id="m-reemb"></div>
      <div><label>Status</label><select id="m-status">
        <option value="solicitado">Solicitado</option><option value="em_analise">Em análise</option>
        <option value="pago">Pago</option><option value="pago_parcial">Pago parcial</option>
        <option value="negado">Negado</option></select></div>
      <div><label>Situação (texto livre)</label><input id="m-sit" placeholder="ex.: enviado ao HR"></div>
      <div><label>Nº Claim</label><input id="m-claim"></div>
      <div><label>Nº Nota fiscal</label><input id="m-nf"></div>
      <div class="full"><label>Comentário da Cigna</label><input id="m-coment"></div>
      <div class="full"><label>Observações / próxima ação</label><textarea id="m-obs" rows="2"></textarea></div>
    </div>
    <div class="modal-acts">
      <button class="btn perigo" id="m-del" onclick="excluir()">🗑️ Excluir</button>
      <div class="dir">
        <button class="btn claro" onclick="fecharModal()">Cancelar</button>
        <button class="btn verde" onclick="salvarModal()">💾 Salvar</button>
      </div>
    </div>
  </div>
</div>

<script>
const DADOS_ORIGINAIS = __DADOS__;
const CHAVE = 'palomo-controle-reembolsos-v1';
const ST = {pago:'Pago',pago_parcial:'Pago parcial',em_analise:'Em análise',negado:'Negado',solicitado:'Solicitado'};
const TIPO = {consulta:'Consulta',terapia:'Terapia',honorario:'Honorário',cirurgia:'Cirurgia',
              produto:'Produto',medicamento:'Medicamento',exame:'Exame',outro:'Outro'};
const NOME_CURTO = {'Priscila da Silva Herbas Palomo':'Priscila','João Guilherme Ramalho Palomo':'João Guilherme',
  'Ana Luisa Ramalho Palomo':'Ana Luisa','Luisa Juliana Faria Ramalho de Souza':'Luisa'};
const BENEFICIARIOS = Object.keys(NOME_CURTO);
const curto = n => NOME_CURTO[n]||n;
const fmt = v => (v==null||isNaN(v)?'—':(+v).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2}));
const fmtD = d => d?d.split('-').reverse().join('/'):'—';
const esc = s => (s??'').toString().replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
const sel = id => document.getElementById(id);

/* ---------- estado ---------- */
let dados;
try { dados = JSON.parse(localStorage.getItem(CHAVE)) || null; } catch(e){ dados = null; }
if (!dados) dados = JSON.parse(JSON.stringify(DADOS_ORIGINAIS));

function persistir(){
  localStorage.setItem(CHAVE, JSON.stringify(dados));
  sel('salvo-em').textContent = 'salvo às ' + new Date().toLocaleTimeString('pt-BR');
  desenharTudo();
}
function restaurar(){
  if(confirm('Descartar TODAS as alterações feitas neste navegador e voltar aos dados originais do banco?')){
    localStorage.removeItem(CHAVE);
    dados = JSON.parse(JSON.stringify(DADOS_ORIGINAIS));
    desenharTudo();
  }
}

/* ---------- stats ---------- */
function desenharStats(){
  const tp = dados.reduce((a,r)=>a+(+r.valor_pago||0),0);
  const tr = dados.reduce((a,r)=>a+(+r.valor_reembolsado||0),0);
  const pend = dados.filter(r=>['em_analise','solicitado'].includes(r.status));
  const vp = pend.reduce((a,r)=>a+(+r.valor_pago||0),0);
  sel('stats').innerHTML = `
    <div class="stat"><span>Total de claims</span><b>${dados.length}</b></div>
    <div class="stat"><span>Total pago</span><b>R$ ${fmt(tp)}</b></div>
    <div class="stat g"><span>Total reembolsado</span><b>R$ ${fmt(tr)}</b><small>${tp?(100*tr/tp).toFixed(1):0}% de cobertura</small></div>
    <div class="stat a"><span>Aguardando resposta</span><b>R$ ${fmt(vp)}</b><small>${pend.length} claims</small></div>`;
  sel('pend-n').textContent = `(${pend.length})`;
}

/* ---------- tabela ---------- */
let sortK='data_atendimento', sortDir=-1;
function popularFiltros(){
  sel('f-ben').length=1; sel('f-ano').length=1;
  [...new Set(dados.map(r=>r.beneficiario))].sort().forEach(b=>sel('f-ben').insertAdjacentHTML('beforeend',`<option>${esc(b)}</option>`));
  [...new Set(dados.map(r=>(r.data_atendimento||'').slice(0,4)))].filter(Boolean).sort().reverse()
    .forEach(a=>sel('f-ano').insertAdjacentHTML('beforeend',`<option>${a}</option>`));
}
function filtrar(){
  const b=sel('f-ben').value, s=sel('f-status').value, a=sel('f-ano').value, q=sel('f-busca').value.toLowerCase();
  return dados.filter(r =>
    (!b||r.beneficiario===b)&&(!s||r.status===s)&&(!a||(r.data_atendimento||'').startsWith(a))&&
    (!q||[r.prestador,r.n_claim,r.nota_fiscal,r.comentario_cigna,r.situacao,r.observacoes,r.descricao]
        .some(x=>(x||'').toString().toLowerCase().includes(q))));
}
function desenharTabela(){
  const linhas = filtrar().sort((x,y)=>{
    let a=x[sortK]??'', b=y[sortK]??'';
    if(sortK.startsWith('valor')){a=+a||0;b=+b||0}
    return (a>b?1:a<b?-1:0)*sortDir;
  });
  sel('corpo').innerHTML = linhas.map(r=>`
    <tr class="row">
      <td class="nowrap">${fmtD(r.data_atendimento)}</td>
      <td>${esc(curto(r.beneficiario))}</td>
      <td>${esc(r.prestador||'—')}</td>
      <td>${TIPO[r.tipo]||r.tipo||'—'}</td>
      <td class="num">${fmt(r.valor_pago)}</td>
      <td class="num">${+r.valor_reembolsado?fmt(r.valor_reembolsado):'<span class="muted">—</span>'}</td>
      <td><select class="status-sel st-${r.status}" onchange="mudarStatus(${r.id},this.value)">
        ${Object.entries(ST).map(([k,v])=>`<option value="${k}"${k===r.status?' selected':''}>${v}</option>`).join('')}
      </select></td>
      <td class="nowrap" style="font-size:.72rem">${r.n_claim?esc(r.n_claim):'<span class="muted">—</span>'}${r.nota_fiscal?'<br>NF '+esc(r.nota_fiscal):''}</td>
      <td>${(r.documentos||[]).map(d=>`<a class="doclink" href="documentos/${d}" target="_blank">📄</a>`).join('')||'<span class="muted">—</span>'}</td>
      <td><button class="acao-btn" onclick="abrirModal(${r.id})">✏️</button></td>
    </tr>`).join('');
  const tp=linhas.reduce((a,r)=>a+(+r.valor_pago||0),0), tr2=linhas.reduce((a,r)=>a+(+r.valor_reembolsado||0),0);
  sel('rodape').innerHTML=`<td colspan="4">${linhas.length} registro(s)</td>
    <td class="num">${fmt(tp)}</td><td class="num">${fmt(tr2)}</td><td colspan="4"></td>`;
}
function mudarStatus(id,st){
  const r=dados.find(x=>x.id===id); if(!r)return;
  r.status=st;
  if(st==='pago' && !+r.valor_reembolsado) r.valor_reembolsado=r.valor_pago;
  persistir();
}
document.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{
  const k=th.dataset.k; sortDir=(sortK===k?-sortDir:(k==='data_atendimento'?-1:1)); sortK=k; desenharTabela();
});
['f-ben','f-status','f-ano'].forEach(id=>sel(id).onchange=desenharTabela);
sel('f-busca').oninput=desenharTabela;

/* ---------- pendências ---------- */
function desenharPendencias(){
  const hoje = new Date();
  const pend = dados.filter(r=>['em_analise','solicitado'].includes(r.status))
    .sort((a,b)=>(a.data_atendimento||'')<(b.data_atendimento||'')?-1:1);
  sel('pendlist').innerHTML = pend.length ? pend.map(r=>{
    const d0 = r.data_atendimento? new Date(r.data_atendimento):hoje;
    const dias = Math.floor((hoje-d0)/86400000);
    return `<div class="pend-card${dias>45?' vencida':''}">
      <div>
        <b>${esc(curto(r.beneficiario))} · ${esc(r.prestador||r.descricao||'—')} · R$ ${fmt(r.valor_pago)}</b>
        <div class="meta">${fmtD(r.data_atendimento)} · ${TIPO[r.tipo]||r.tipo||''}
          ${r.n_claim?' · claim '+esc(r.n_claim):''}${r.nota_fiscal?' · NF '+esc(r.nota_fiscal):''}
          ${r.situacao?' · <b>'+esc(r.situacao)+'</b>':''}</div>
        ${r.comentario_cigna?`<div class="meta">💬 Cigna: ${esc(r.comentario_cigna)}</div>`:''}
      </div>
      <div class="dias" style="color:${dias>45?'var(--red)':'var(--amber)'}">${dias}<small>dias</small></div>
      <div class="pend-acao">
        <span style="font-size:.74rem;color:var(--mut);font-weight:700">PRÓXIMA AÇÃO:</span>
        <input value="${esc(r.proxima_acao||'')}" placeholder="ex.: cobrar HR, reenviar com NF correta…"
               onchange="anotarAcao(${r.id},this.value)">
        <button class="acao-btn" onclick="abrirModal(${r.id})">✏️</button>
      </div>
    </div>`;
  }).join('') : '<div class="aviso" style="background:#e9f9f0;border-color:#bfe8cf;color:#116b3f">✅ Nenhuma pendência — tudo respondido!</div>';
}
function anotarAcao(id,txt){ const r=dados.find(x=>x.id===id); if(r){ r.proxima_acao=txt; persistir(); } }

/* ---------- modal ---------- */
let editId = null;
sel('m-ben').innerHTML = BENEFICIARIOS.map(b=>`<option>${b}</option>`).join('');
function popularPrestadores(){
  sel('prestadores').innerHTML = [...new Set(dados.map(r=>r.prestador).filter(Boolean))].sort()
    .map(p=>`<option value="${esc(p)}">`).join('');
}
function abrirModal(id){
  editId = id ?? null;
  const r = id!=null ? dados.find(x=>x.id===id) : null;
  sel('m-titulo').textContent = r? 'Editar reembolso #'+id : 'Novo reembolso';
  sel('m-del').style.display = r? 'block':'none';
  sel('m-ben').value = r?.beneficiario || BENEFICIARIOS[0];
  sel('m-tipo').value = r?.tipo || 'consulta';
  sel('m-prest').value = r?.prestador || '';
  sel('m-data').value = r?.data_atendimento || '';
  sel('m-datapag').value = r?.data_pagamento || '';
  sel('m-pago').value = r?.valor_pago ?? '';
  sel('m-reemb').value = r?.valor_reembolsado ?? '';
  sel('m-status').value = r?.status || 'solicitado';
  sel('m-sit').value = r?.situacao || '';
  sel('m-claim').value = r?.n_claim || '';
  sel('m-nf').value = r?.nota_fiscal || '';
  sel('m-coment').value = r?.comentario_cigna || '';
  sel('m-obs').value = r?.observacoes || '';
  sel('overlay').classList.add('on');
}
function fecharModal(){ sel('overlay').classList.remove('on'); }
function salvarModal(){
  if(!sel('m-data').value){ alert('Informe a data do atendimento.'); return; }
  if(!sel('m-pago').value){ alert('Informe o valor pago.'); return; }
  let r;
  if(editId!=null){ r = dados.find(x=>x.id===editId); }
  else { r = { id: Math.max(0,...dados.map(x=>x.id))+1, documentos:[], origem:'manual', proxima_acao:'' }; dados.unshift(r); }
  r.beneficiario = sel('m-ben').value;
  r.tipo = sel('m-tipo').value;
  r.prestador = sel('m-prest').value || null;
  r.data_atendimento = sel('m-data').value;
  r.data_pagamento = sel('m-datapag').value || null;
  r.valor_pago = +sel('m-pago').value;
  r.valor_reembolsado = +sel('m-reemb').value || 0;
  r.diferenca = +(r.valor_pago - r.valor_reembolsado).toFixed(2);
  r.status = sel('m-status').value;
  r.situacao = sel('m-sit').value || null;
  r.n_claim = sel('m-claim').value || null;
  r.nota_fiscal = sel('m-nf').value || null;
  r.comentario_cigna = sel('m-coment').value || null;
  r.observacoes = sel('m-obs').value || null;
  fecharModal(); persistir();
}
function excluir(){
  if(editId!=null && confirm('Excluir este reembolso do controle?')){
    dados = dados.filter(x=>x.id!==editId);
    fecharModal(); persistir();
  }
}
document.addEventListener('keydown',e=>{ if(e.key==='Escape')fecharModal(); });

/* ---------- exportar / importar ---------- */
function baixar(nome, conteudo, tipo){
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([conteudo],{type:tipo}));
  a.download=nome; a.click(); URL.revokeObjectURL(a.href);
}
function exportarJSON(){
  baixar('reembolsos-controle-'+new Date().toISOString().slice(0,10)+'.json',
         JSON.stringify(dados,null,2),'application/json');
}
function exportarCSV(){
  const cols=['id','beneficiario','prestador','tipo','data_atendimento','data_pagamento',
              'valor_pago','valor_reembolsado','status','situacao','n_claim','nota_fiscal',
              'comentario_cigna','observacoes','proxima_acao'];
  const q=v=>{v=(v??'').toString().replace(/"/g,'""');return /[";\n]/.test(v)?'"'+v+'"':v;};
  const csv=[cols.join(';')].concat(dados.map(r=>cols.map(c=>q(r[c])).join(';'))).join('\n');
  baixar('reembolsos-controle-'+new Date().toISOString().slice(0,10)+'.csv','\ufeff'+csv,'text/csv');
}
function importarJSON(ev){
  const f=ev.target.files[0]; if(!f)return;
  const rd=new FileReader();
  rd.onload=()=>{ try{
      const novo=JSON.parse(rd.result);
      if(!Array.isArray(novo)) throw new Error('formato inválido');
      dados=novo; persistir();
      alert('Importado: '+dados.length+' registros.');
    }catch(e){ alert('Arquivo inválido: '+e.message); } };
  rd.readAsText(f); ev.target.value='';
}

/* ---------- abas ---------- */
function abrirAba(secao){
  const t=document.querySelector(`.tab[data-sec="${secao}"]`); if(!t) return;
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));
  document.querySelectorAll('.section').forEach(x=>x.classList.remove('on'));
  t.classList.add('on'); sel('sec-'+secao).classList.add('on');
}
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{ location.hash=t.dataset.sec; abrirAba(t.dataset.sec); });
if(location.hash) abrirAba(location.hash.slice(1));
window.addEventListener('hashchange',()=>abrirAba(location.hash.slice(1)));

function desenharTudo(){ desenharStats(); popularFiltros(); popularPrestadores(); desenharTabela(); desenharPendencias(); }
desenharTudo();
</script>
</body>
</html>
"""


def main():
    dados = carregar()
    SAIDA.write_text(TEMPLATE.replace("__DADOS__", json.dumps(dados, ensure_ascii=False)),
                     encoding="utf-8")
    print(f"Template de controle gerado: {SAIDA}  ({len(dados)} reembolsos pré-carregados)")


if __name__ == "__main__":
    main()
