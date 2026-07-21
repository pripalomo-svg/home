#!/usr/bin/env python3
"""Gera o painel index.html a partir de reembolsos.db.

Uso:  python3 gerar_dashboard.py
O arquivo gerado é autocontido (dados embutidos em JSON) e funciona offline —
basta abrir index.html no navegador. Os links de documentos apontam para a
pasta documentos/ ao lado do HTML.
"""

import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "reembolsos.db"
SAIDA = BASE / "index.html"


def carregar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    reembolsos = []
    for r in conn.execute("SELECT * FROM vw_reembolsos ORDER BY data_atendimento DESC"):
        d = dict(r)
        d["documentos"] = d["documentos"].split("; ") if d["documentos"] else []
        reembolsos.append(d)

    docs = [dict(r) for r in conn.execute(
        "SELECT * FROM documentos ORDER BY categoria, data_documento")]

    eob = [dict(r) for r in conn.execute(
        """SELECT e.*, d.arquivo FROM eob_itens e
           LEFT JOIN documentos d ON d.id = e.documento_id
           ORDER BY e.data_processado, e.n_claim, e.data_servico""")]

    portal = [dict(r) for r in conn.execute(
        "SELECT * FROM submissoes_portal ORDER BY data_tratamento DESC")]

    prestadores = [dict(r) for r in conn.execute(
        """SELECT p.*, COUNT(r.id) AS claims,
                  COALESCE(SUM(r.valor_pago),0) AS pago,
                  COALESCE(SUM(r.valor_reembolsado),0) AS reemb,
                  MIN(r.data_atendimento) AS primeira, MAX(r.data_atendimento) AS ultima
           FROM prestadores p LEFT JOIN reembolsos r ON r.prestador_id = p.id
           GROUP BY p.id ORDER BY pago DESC, p.nome""")]

    conn.close()
    return reembolsos, docs, eob, portal, prestadores


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reembolsos Plano de Saúde · Família Palomo</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:#f4f6fb; --card:#fff; --ink:#17203a; --mut:#8a93a8; --line:#e6e9f2;
    --blue:#2f6fed; --green:#0fa968; --amber:#e8930c; --red:#e14b5a; --violet:#7c5cde;
  }
  body { font-family:'Segoe UI',system-ui,Arial,sans-serif; background:var(--bg); color:var(--ink); }
  header { background:linear-gradient(120deg,#141b31,#1d2c54 55%,#28407c); color:#fff; padding:26px 34px; }
  header h1 { font-size:1.45rem; } header h1 em { color:#7ea4ff; font-style:normal; }
  header p { color:rgba(255,255,255,.62); font-size:.82rem; margin-top:5px; }
  .wrap { max-width:1280px; margin:0 auto; padding:24px 30px 60px; }

  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin-bottom:22px; }
  .stat { background:var(--card); border-radius:14px; padding:16px 18px; box-shadow:0 1px 8px rgba(23,32,58,.07); border-top:4px solid var(--blue); }
  .stat.g{border-color:var(--green)} .stat.a{border-color:var(--amber)} .stat.r{border-color:var(--red)} .stat.v{border-color:var(--violet)}
  .stat b { display:block; font-size:1.42rem; font-weight:800; margin-top:4px; }
  .stat span { font-size:.7rem; text-transform:uppercase; letter-spacing:.06em; color:var(--mut); }
  .stat small { color:var(--mut); font-size:.72rem; }

  .tabs { display:flex; gap:6px; margin-bottom:18px; flex-wrap:wrap; }
  .tab { padding:9px 20px; border-radius:24px; background:var(--card); border:1px solid var(--line);
         cursor:pointer; font-size:.85rem; font-weight:600; color:#5a647d; }
  .tab.on { background:var(--blue); color:#fff; border-color:var(--blue); }

  .filters { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px; align-items:center; }
  .filters select, .filters input { padding:8px 12px; border:1px solid var(--line); border-radius:9px;
      background:var(--card); font-size:.84rem; color:var(--ink); outline:none; }
  .filters input { flex:1; min-width:220px; }

  .panel { background:var(--card); border-radius:14px; box-shadow:0 1px 8px rgba(23,32,58,.07); overflow:hidden; }
  table { width:100%; border-collapse:collapse; font-size:.83rem; }
  th { text-align:left; padding:11px 13px; background:#f7f8fc; color:var(--mut); font-size:.7rem;
       text-transform:uppercase; letter-spacing:.05em; border-bottom:1px solid var(--line);
       cursor:pointer; user-select:none; white-space:nowrap; }
  th .arrow { opacity:.5; font-size:.85em; }
  td { padding:10px 13px; border-bottom:1px solid #f0f2f8; vertical-align:top; }
  tr.row:hover { background:#f8faff; cursor:pointer; }
  td.num, th.num { text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; }

  .chip { display:inline-block; padding:3px 11px; border-radius:20px; font-size:.72rem; font-weight:700; white-space:nowrap; }
  .st-pago         { background:#e2f6ec; color:#0b7d4d; }
  .st-pago_parcial { background:#fef2dd; color:#a36508; }
  .st-em_analise   { background:#e5edff; color:#2b5cc7; }
  .st-negado       { background:#fde5e8; color:#bb2c3d; }
  .st-solicitado   { background:#efe9ff; color:#6740c6; }

  .doclink { display:inline-flex; align-items:center; gap:5px; font-size:.74rem; color:var(--blue);
             text-decoration:none; background:#eef3ff; padding:3px 9px; border-radius:7px; margin:2px 3px 0 0; }
  .doclink:hover { background:#dbe6ff; }
  .muted { color:var(--mut); }
  .nowrap { white-space:nowrap; }

  .detail { display:none; background:#fbfcff; }
  .detail.open { display:table-row; }
  .detail td { padding:14px 18px 16px; }
  .detail dl { display:grid; grid-template-columns:170px 1fr; gap:4px 14px; font-size:.8rem; }
  .detail dt { color:var(--mut); } .detail dd { margin:0; }

  .grid2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:22px; }
  @media(max-width:900px){ .grid2{grid-template-columns:1fr} }
  .panel h3 { font-size:.92rem; padding:14px 16px 4px; }
  .panel .sub { font-size:.74rem; color:var(--mut); padding:0 16px 10px; }

  .bar-row { display:grid; grid-template-columns:150px 1fr 110px; align-items:center; gap:10px; padding:5px 16px; font-size:.79rem; }
  .bar-bg { background:#eef0f7; border-radius:6px; height:14px; overflow:hidden; }
  .bar { height:100%; border-radius:6px; background:linear-gradient(90deg,#2f6fed,#7ea4ff); }
  .bar.grn { background:linear-gradient(90deg,#0fa968,#5ed6a3); }

  .doc-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:10px; padding:14px 16px 18px; }
  .doc-card { display:flex; gap:11px; align-items:flex-start; border:1px solid var(--line); border-radius:11px;
              padding:11px 13px; text-decoration:none; color:inherit; background:#fff; transition:.15s; }
  .doc-card:hover { box-shadow:0 4px 14px rgba(23,32,58,.11); transform:translateY(-1px); }
  .doc-ico { width:36px; height:36px; border-radius:9px; display:flex; align-items:center; justify-content:center;
             font-size:1rem; flex-shrink:0; background:#eef3ff; }
  .doc-card b { font-size:.79rem; display:block; }
  .doc-card small { font-size:.71rem; color:var(--mut); }

  .section { display:none; } .section.on { display:block; }
  footer { text-align:center; color:var(--mut); font-size:.74rem; margin-top:34px; }
</style>
</head>
<body>
<header>
  <h1>🏥 Reembolsos do Plano de Saúde · <em>Família Palomo</em></h1>
  <p>Cigna / McKinsey · Titular: Luisa Juliana Faria Ramalho de Souza · Gerado a partir de reembolsos.db</p>
</header>

<div class="wrap">
  <div class="stats" id="stats"></div>

  <div class="tabs">
    <div class="tab on" data-sec="reembolsos">📋 Reembolsos</div>
    <div class="tab" data-sec="documentos">📎 Documentos</div>
    <div class="tab" data-sec="eob">🧾 Detalhe EOBs Cigna</div>
    <div class="tab" data-sec="portal">🌐 Portal Cigna 2026</div>
    <div class="tab" data-sec="prestadores">🩺 Prestadores</div>
    <div class="tab" data-sec="resumo">📊 Resumo</div>
  </div>

  <div class="section on" id="sec-reembolsos">
    <div class="filters">
      <select id="f-ben"><option value="">Todos os beneficiários</option></select>
      <select id="f-status">
        <option value="">Todos os status</option>
        <option value="pago">Pago</option><option value="pago_parcial">Pago parcial</option>
        <option value="em_analise">Em análise</option><option value="negado">Negado</option>
        <option value="solicitado">Solicitado</option>
      </select>
      <select id="f-ano"><option value="">Todos os anos</option></select>
      <select id="f-tipo"><option value="">Todos os tipos</option></select>
      <input id="f-busca" placeholder="🔍 Buscar prestador, claim, NF, comentário…">
    </div>
    <div class="panel">
      <table id="tabela">
        <thead><tr>
          <th data-k="data_atendimento">Data <span class="arrow">↕</span></th>
          <th data-k="beneficiario">Beneficiário <span class="arrow">↕</span></th>
          <th data-k="prestador">Prestador <span class="arrow">↕</span></th>
          <th data-k="tipo">Tipo <span class="arrow">↕</span></th>
          <th class="num" data-k="valor_pago">Pago R$ <span class="arrow">↕</span></th>
          <th class="num" data-k="valor_reembolsado">Reemb. R$ <span class="arrow">↕</span></th>
          <th data-k="status">Status <span class="arrow">↕</span></th>
          <th>Docs</th>
        </tr></thead>
        <tbody id="corpo"></tbody>
        <tfoot><tr id="rodape" style="font-weight:700;background:#f7f8fc"></tr></tfoot>
      </table>
    </div>
  </div>

  <div class="section" id="sec-documentos">
    <div class="panel"><h3>📎 Todos os documentos anexados</h3>
      <p class="sub">Clique para abrir o arquivo (pasta documentos/)</p>
      <div class="doc-grid" id="docgrid"></div>
    </div>
  </div>

  <div class="section" id="sec-eob">
    <div class="panel">
      <h3>🧾 Linhas de serviço dos Explanation of Benefits</h3>
      <p class="sub">Cada sessão/item processado pela Cigna, com câmbio e valores em USD</p>
      <table><thead><tr>
        <th>Processado</th><th>Claim</th><th>Paciente</th><th>Data serviço</th>
        <th>Tipo</th><th class="num">BRL</th><th class="num">USD</th>
        <th class="num">Pago USD</th><th class="num">Não coberto</th><th>Remark</th>
      </tr></thead><tbody id="eobcorpo"></tbody></table>
    </div>
  </div>

  <div class="section" id="sec-portal">
    <div class="panel">
      <h3>🌐 Submissões no portal Cigna (2026)</h3>
      <p class="sub">Claims enviados pelo novo portal, com nº de submissão e CLM</p>
      <table><thead><tr>
        <th>Paciente</th><th>Status</th><th class="num">Valor R$</th>
        <th>Nº Submissão</th><th>CLM</th><th>Data tratamento</th><th>Tipo</th>
      </tr></thead><tbody id="portalcorpo"></tbody></table>
    </div>
  </div>

  <div class="section" id="sec-prestadores">
    <div class="panel">
      <h3>🩺 Diretório de prestadores</h3>
      <p class="sub">Prestadores usados nos reembolsos + indicações ainda sem claim (diretório do Notion)</p>
      <table><thead><tr>
        <th>Nome</th><th>Especialidade</th><th>Endereço / contato</th>
        <th class="num">Claims</th><th class="num">Pago R$</th><th class="num">Reemb. R$</th>
        <th>Período</th><th>Observações</th>
      </tr></thead><tbody id="prestcorpo"></tbody></table>
    </div>
  </div>

  <div class="section" id="sec-resumo">
    <div class="grid2">
      <div class="panel"><h3>👥 Por beneficiário</h3><p class="sub">Valor pago vs. reembolsado (R$)</p><div id="g-ben" style="padding-bottom:14px"></div></div>
      <div class="panel"><h3>🏷️ Por status</h3><p class="sub">Quantidade de claims e valores</p><div id="g-status" style="padding-bottom:14px"></div></div>
      <div class="panel"><h3>🏢 Top prestadores</h3><p class="sub">Pelo valor total pago (R$)</p><div id="g-prest" style="padding-bottom:14px"></div></div>
      <div class="panel"><h3>📅 Por ano do atendimento</h3><p class="sub">Valor pago vs. reembolsado (R$)</p><div id="g-ano" style="padding-bottom:14px"></div></div>
    </div>
  </div>

  <footer>Banco de dados: reembolsos.db · Regerar este painel: <code>python3 gerar_dashboard.py</code></footer>
</div>

<script>
const REEMBOLSOS = __REEMBOLSOS__;
const DOCS = __DOCS__;
const EOB = __EOB__;
const PORTAL = __PORTAL__;
const PRESTADORES = __PRESTADORES__;

const fmt = v => (v==null?'—':v.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2}));
const fmtD = d => d ? d.split('-').reverse().join('/') : '—';
const ST = {pago:'Pago',pago_parcial:'Pago parcial',em_analise:'Em análise',negado:'Negado',solicitado:'Solicitado'};
const NOME_CURTO = {'Priscila da Silva Herbas Palomo':'Priscila','João Guilherme Ramalho Palomo':'João Guilherme',
  'Ana Luisa Ramalho Palomo':'Ana Luisa','Luisa Juliana Faria Ramalho de Souza':'Luisa'};
const curto = n => NOME_CURTO[n] || n;
const TIPO = {consulta:'Consulta',terapia:'Terapia',honorario:'Honorário',cirurgia:'Cirurgia',produto:'Produto',medicamento:'Medicamento',exame:'Exame',outro:'Outro'};
const esc = s => (s??'').toString().replace(/&/g,'&amp;').replace(/</g,'&lt;');

/* ---------- stats ---------- */
(function(){
  const tp = REEMBOLSOS.reduce((a,r)=>a+r.valor_pago,0);
  const tr = REEMBOLSOS.reduce((a,r)=>a+r.valor_reembolsado,0);
  const pend = REEMBOLSOS.filter(r=>['em_analise','solicitado'].includes(r.status));
  const vp = pend.reduce((a,r)=>a+r.valor_pago,0);
  const gl = REEMBOLSOS.filter(r=>['pago','pago_parcial','negado'].includes(r.status))
                       .reduce((a,r)=>a+(r.valor_pago-r.valor_reembolsado),0);
  document.getElementById('stats').innerHTML = `
    <div class="stat"><span>Total de claims</span><b>${REEMBOLSOS.length}</b><small>${DOCS.length} documentos anexados</small></div>
    <div class="stat"><span>Total pago</span><b>R$ ${fmt(tp)}</b><small>desembolsado pela família</small></div>
    <div class="stat g"><span>Total reembolsado</span><b>R$ ${fmt(tr)}</b><small>${(100*tr/tp).toFixed(1)}% de cobertura</small></div>
    <div class="stat a"><span>Pendente de resposta</span><b>R$ ${fmt(vp)}</b><small>${pend.length} claims em análise/a enviar</small></div>
    <div class="stat r"><span>Glosas (não coberto)</span><b>R$ ${fmt(gl)}</b><small>em claims já processados</small></div>`;
})();

/* ---------- tabela de reembolsos ---------- */
let sortK = 'data_atendimento', sortDir = -1;
const sel = id => document.getElementById(id);

function popularFiltros(){
  const bens=[...new Set(REEMBOLSOS.map(r=>r.beneficiario))].sort();
  bens.forEach(b=>sel('f-ben').insertAdjacentHTML('beforeend',`<option>${esc(b)}</option>`));
  const anos=[...new Set(REEMBOLSOS.map(r=>(r.data_atendimento||'').slice(0,4)))].filter(Boolean).sort().reverse();
  anos.forEach(a=>sel('f-ano').insertAdjacentHTML('beforeend',`<option>${a}</option>`));
  const tipos=[...new Set(REEMBOLSOS.map(r=>r.tipo))].sort();
  tipos.forEach(t=>sel('f-tipo').insertAdjacentHTML('beforeend',`<option value="${t}">${TIPO[t]||t}</option>`));
}

function filtrar(){
  const b=sel('f-ben').value, s=sel('f-status').value, a=sel('f-ano').value,
        t=sel('f-tipo').value, q=sel('f-busca').value.toLowerCase();
  return REEMBOLSOS.filter(r =>
    (!b||r.beneficiario===b) && (!s||r.status===s) &&
    (!a||(r.data_atendimento||'').startsWith(a)) && (!t||r.tipo===t) &&
    (!q||[r.prestador,r.n_claim,r.novo_n_claim,r.nota_fiscal,r.comentario_cigna,r.situacao,r.descricao,r.observacoes]
        .some(x=>(x||'').toString().toLowerCase().includes(q))));
}

function render(){
  const linhas = filtrar().sort((x,y)=>{
    let a=x[sortK]??'', b=y[sortK]??'';
    if(typeof a==='number'||typeof b==='number'){a=+a||0;b=+b||0}
    return (a>b?1:a<b?-1:0)*sortDir;
  });
  const corpo = sel('corpo'); corpo.innerHTML='';
  linhas.forEach(r=>{
    const docs = r.documentos.map(d=>`<a class="doclink" href="documentos/${d}" target="_blank" onclick="event.stopPropagation()">📄 ${d.split('/').pop().slice(0,26)}…</a>`).join('');
    corpo.insertAdjacentHTML('beforeend', `
      <tr class="row" onclick="toggle(${r.id})">
        <td class="nowrap">${fmtD(r.data_atendimento)}</td>
        <td>${esc(curto(r.beneficiario))}</td>
        <td>${esc(r.prestador||'—')}</td>
        <td>${TIPO[r.tipo]||r.tipo}</td>
        <td class="num">${fmt(r.valor_pago)}</td>
        <td class="num">${r.valor_reembolsado?fmt(r.valor_reembolsado):'<span class="muted">—</span>'}</td>
        <td><span class="chip st-${r.status}">${ST[r.status]}</span></td>
        <td>${docs||'<span class="muted">—</span>'}</td>
      </tr>
      <tr class="detail" id="det-${r.id}"><td colspan="8"><dl>
        <dt>Beneficiário</dt><dd>${esc(r.beneficiario)}</dd>
        <dt>Prestador</dt><dd>${esc(r.prestador||'—')} ${r.especialidade?'· '+esc(r.especialidade):''}</dd>
        ${r.descricao?`<dt>Descrição</dt><dd>${esc(r.descricao)}</dd>`:''}
        <dt>Nº Claim</dt><dd>${esc(r.n_claim||'—')}${r.novo_n_claim?' → reconsideração: '+esc(r.novo_n_claim):''}</dd>
        ${r.nota_fiscal?`<dt>Nota fiscal</dt><dd>Nº ${esc(r.nota_fiscal)}</dd>`:''}
        ${r.data_pagamento?`<dt>Acerto/pagamento</dt><dd>${fmtD(r.data_pagamento)}</dd>`:''}
        <dt>Diferença (glosa)</dt><dd>R$ ${fmt(r.diferenca)}</dd>
        ${r.situacao?`<dt>Situação</dt><dd>${esc(r.situacao)}</dd>`:''}
        ${r.comentario_cigna?`<dt>Comentário Cigna</dt><dd>${esc(r.comentario_cigna)}</dd>`:''}
        ${r.texto_reconsideracao?`<dt>Texto reconsideração</dt><dd>${esc(r.texto_reconsideracao)}</dd>`:''}
        ${r.observacoes?`<dt>Observações</dt><dd>${esc(r.observacoes)}</dd>`:''}
        <dt>Origem do dado</dt><dd>${esc(r.origem)}</dd>
      </dl></td></tr>`);
  });
  const tp=linhas.reduce((a,r)=>a+r.valor_pago,0), tr=linhas.reduce((a,r)=>a+r.valor_reembolsado,0);
  sel('rodape').innerHTML = `<td colspan="4">${linhas.length} registro(s)</td>
    <td class="num">${fmt(tp)}</td><td class="num">${fmt(tr)}</td><td colspan="2"></td>`;
}
function toggle(id){ document.getElementById('det-'+id).classList.toggle('open'); }

document.querySelectorAll('#tabela th[data-k]').forEach(th=>th.onclick=()=>{
  const k=th.dataset.k; sortDir = (sortK===k? -sortDir : (k==='data_atendimento'?-1:1)); sortK=k; render();
});
['f-ben','f-status','f-ano','f-tipo'].forEach(id=>sel(id).onchange=render);
sel('f-busca').oninput=render;

/* ---------- documentos ---------- */
const ICONES={nota_fiscal:'🧾',recibo:'🪪',eob:'📑',receita:'💊',pedido_exame:'🔬',relatorio_medico:'🩺',plano:'📘',referencia:'🗂️'};
const CATNOME={nota_fiscal:'Nota fiscal',recibo:'Recibo',eob:'EOB Cigna',receita:'Receita',pedido_exame:'Pedido de exame',relatorio_medico:'Relatório médico',plano:'Plano de saúde',referencia:'Referência'};
sel('docgrid').innerHTML = DOCS.map(d=>`
  <a class="doc-card" href="documentos/${d.arquivo}" target="_blank">
    <div class="doc-ico">${ICONES[d.categoria]||'📄'}</div>
    <div><b>${esc(d.titulo)}</b>
    <small>${CATNOME[d.categoria]||d.categoria}${d.data_documento?' · '+fmtD(d.data_documento):''}${d.descricao?'<br>'+esc(d.descricao):''}</small></div>
  </a>`).join('');

/* ---------- EOB ---------- */
sel('eobcorpo').innerHTML = EOB.map(e=>`<tr>
  <td class="nowrap">${fmtD(e.data_processado)}</td><td>${e.n_claim}</td>
  <td>${esc(curto(e.paciente))}</td>
  <td class="nowrap">${fmtD(e.data_servico)}</td><td>${esc(e.tipo_servico||'')}</td>
  <td class="num">${fmt(e.valor_brl)}</td><td class="num">$${fmt(e.valor_usd)}</td>
  <td class="num" style="color:var(--green)">$${fmt(e.pago_usd)}</td>
  <td class="num" style="color:${e.nao_coberto_usd>0?'var(--red)':'inherit'}">$${fmt(e.nao_coberto_usd)}</td>
  <td>${e.remark_code||'<span class="muted">—</span>'}</td></tr>`).join('');

/* ---------- portal ---------- */
sel('portalcorpo').innerHTML = PORTAL.map(p=>`<tr>
  <td>${esc(curto(p.paciente))}</td><td><span class="chip st-em_analise">${p.status}</span></td>
  <td class="num">${fmt(p.valor_brl)}</td><td style="font-variant-numeric:tabular-nums">${p.n_submissao}</td>
  <td style="font-variant-numeric:tabular-nums">${p.n_clm||'—'}</td>
  <td class="nowrap">${fmtD(p.data_tratamento)}</td><td>${p.tipo||''}</td></tr>`).join('');

/* ---------- prestadores ---------- */
sel('prestcorpo').innerHTML = PRESTADORES.map(p=>`<tr>
  <td><b>${esc(p.nome)}</b>${p.cpf_cnpj?`<br><span class="muted" style="font-size:.71rem">${esc(p.cpf_cnpj)}</span>`:''}</td>
  <td>${esc(p.especialidade||'—')}</td>
  <td style="font-size:.76rem">${esc(p.endereco||'—')}${p.telefone?'<br>📞 '+esc(p.telefone):''}</td>
  <td class="num">${p.claims||'<span class="muted">—</span>'}</td>
  <td class="num">${p.claims?fmt(p.pago):'<span class="muted">—</span>'}</td>
  <td class="num">${p.claims?fmt(p.reemb):'<span class="muted">—</span>'}</td>
  <td class="nowrap" style="font-size:.74rem">${p.primeira?fmtD(p.primeira)+'<br>a '+fmtD(p.ultima):'<span class="muted">—</span>'}</td>
  <td style="font-size:.75rem;max-width:280px">${esc(p.observacoes||'')}</td></tr>`).join('');

/* ---------- resumo (barras) ---------- */
function barras(el, dados, duplo){
  const max = Math.max(...dados.map(d=>d.v1));
  el.innerHTML = dados.map(d=>`
    <div class="bar-row"><span title="${esc(d.nome)}">${esc(d.nome.length>20?d.nome.slice(0,19)+'…':d.nome)}</span>
      <div>
        <div class="bar-bg"><div class="bar" style="width:${100*d.v1/max}%"></div></div>
        ${duplo?`<div class="bar-bg" style="margin-top:3px"><div class="bar grn" style="width:${100*d.v2/max}%"></div></div>`:''}
      </div>
      <span class="num">${fmt(d.v1)}${duplo?`<br><span style="color:var(--green)">${fmt(d.v2)}</span>`:''}</span>
    </div>`).join('');
}
function agrupar(chave){
  const m={};
  REEMBOLSOS.forEach(r=>{
    const k = chave(r); if(!k) return;
    m[k]=m[k]||{nome:k,v1:0,v2:0,n:0}; m[k].v1+=r.valor_pago; m[k].v2+=r.valor_reembolsado; m[k].n++;
  });
  return Object.values(m).sort((a,b)=>b.v1-a.v1);
}
barras(sel('g-ben'), agrupar(r=>curto(r.beneficiario)), true);
barras(sel('g-status'), agrupar(r=>`${ST[r.status]} (${REEMBOLSOS.filter(x=>x.status===r.status).length})`), true);
barras(sel('g-prest'), agrupar(r=>r.prestador).slice(0,10), true);
barras(sel('g-ano'), agrupar(r=>(r.data_atendimento||'').slice(0,4)).sort((a,b)=>a.nome<b.nome?-1:1), true);

/* ---------- tabs ---------- */
function abrirAba(sec){
  const t=document.querySelector(`.tab[data-sec="${sec}"]`); if(!t) return;
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));
  document.querySelectorAll('.section').forEach(x=>x.classList.remove('on'));
  t.classList.add('on'); document.getElementById('sec-'+sec).classList.add('on');
}
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{ location.hash=t.dataset.sec; abrirAba(t.dataset.sec); });
if(location.hash) abrirAba(location.hash.slice(1));
window.addEventListener('hashchange',()=>abrirAba(location.hash.slice(1)));

popularFiltros(); render();
</script>
</body>
</html>
"""


def main():
    reembolsos, docs, eob, portal, prestadores = carregar()
    html = (TEMPLATE
            .replace("__REEMBOLSOS__", json.dumps(reembolsos, ensure_ascii=False))
            .replace("__DOCS__", json.dumps(docs, ensure_ascii=False))
            .replace("__EOB__", json.dumps(eob, ensure_ascii=False))
            .replace("__PORTAL__", json.dumps(portal, ensure_ascii=False))
            .replace("__PRESTADORES__", json.dumps(prestadores, ensure_ascii=False)))
    SAIDA.write_text(html, encoding="utf-8")
    print(f"Painel gerado: {SAIDA}  ({len(reembolsos)} reembolsos, {len(docs)} documentos)")


if __name__ == "__main__":
    main()
