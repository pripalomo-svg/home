#!/usr/bin/env python3
"""Gera o painel editável (painel.html) a partir de organizador.db.

Uso:  python3 gerar_painel.py

O painel.html é autocontido e funciona offline:
  - vem pré-carregado com todos os dados do banco;
  - permite ADICIONAR, EDITAR e EXCLUIR registros de todas as áreas
    (finanças, vídeos do YouTube, pacientes/prontuários/atendimentos,
    família, projetos, tarefas e catálogo de arquivos);
  - as alterações são salvas automaticamente no navegador (localStorage);
  - exporta JSON para levar as mudanças de volta ao banco
    (python3 importar_painel.py export.json).
"""

import json
import sqlite3
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "organizador.db"
SAIDA = BASE / "painel.html"


def carregar() -> dict:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    def rows(sql):
        return [dict(r) for r in conn.execute(sql)]

    dados = {
        "areas": rows("SELECT * FROM areas ORDER BY id"),
        "financeiro": rows("SELECT * FROM fin_lancamentos ORDER BY data DESC, id DESC"),
        "youtube": rows("SELECT * FROM yt_videos ORDER BY id DESC"),
        "familia_membros": rows("SELECT * FROM familia_membros ORDER BY id"),
        "familia_eventos": rows("SELECT * FROM familia_eventos ORDER BY data, hora"),
        "projetos": rows("SELECT * FROM projetos ORDER BY id"),
        "tarefas": rows("SELECT * FROM tarefas ORDER BY data_limite IS NULL, data_limite"),
        "arquivos": rows("SELECT * FROM arquivos ORDER BY id"),
        "pacientes": [],
    }

    pront = {p["paciente_id"]: p for p in rows("SELECT * FROM prontuarios")}
    atend: dict[int, list] = {}
    for a in rows("SELECT * FROM atendimentos ORDER BY data DESC, hora DESC"):
        atend.setdefault(a["paciente_id"], []).append(a)
    for p in rows("SELECT * FROM pacientes ORDER BY nome"):
        pr = pront.get(p["id"], {})
        p["prontuario"] = {
            k: pr.get(k) for k in (
                "data_abertura", "queixa_principal", "historico",
                "hipotese_diagnostica", "plano_terapeutico", "observacoes")
        }
        p["atendimentos"] = atend.get(p["id"], [])
        dados["pacientes"].append(p)

    conn.close()
    return dados


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Meu Organizador · Painel</title>
<style>
  * { box-sizing:border-box; margin:0; padding:0; }
  :root {
    --bg:#f4f6fb; --card:#fff; --ink:#17203a; --mut:#8a93a8; --line:#e6e9f2;
    --blue:#2f6fed; --green:#0fa968; --amber:#e8930c; --red:#e14b5a; --violet:#7c5cde;
  }
  body { font-family:'Segoe UI',system-ui,Arial,sans-serif; background:var(--bg); color:var(--ink); }
  header { background:linear-gradient(120deg,#141b31,#1d2c54 55%,#28407c); color:#fff;
           padding:20px 32px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; }
  header h1 { font-size:1.3rem; } header h1 em { color:#7ea4ff; font-style:normal; }
  header p { color:rgba(255,255,255,.62); font-size:.76rem; margin-top:4px; }
  .hbtns { display:flex; gap:8px; flex-wrap:wrap; }
  .btn { padding:8px 15px; border-radius:10px; border:none; cursor:pointer; font-size:.8rem;
         font-weight:700; background:rgba(255,255,255,.14); color:#fff; }
  .btn:hover { background:rgba(255,255,255,.25); }
  .btn.primario { background:var(--blue); } .btn.primario:hover { background:#2557c4; }
  .btn.verde { background:var(--green); } .btn.perigo { background:var(--red); }
  .btn.claro { background:#eef1f8; color:var(--ink); } .btn.claro:hover { background:#e0e5f2; }
  .btn.mini { padding:5px 10px; font-size:.74rem; }

  .wrap { max-width:1280px; margin:0 auto; padding:20px 28px 60px; }
  .tabs { display:flex; gap:6px; margin-bottom:18px; flex-wrap:wrap; }
  .tab { padding:9px 18px; border-radius:24px; background:var(--card); border:1px solid var(--line);
         cursor:pointer; font-size:.85rem; font-weight:600; color:#5a647d; }
  .tab.on { background:var(--blue); color:#fff; border-color:var(--blue); }

  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin-bottom:18px; }
  .stat { background:var(--card); border-radius:14px; padding:14px 16px; box-shadow:0 1px 8px rgba(23,32,58,.07); border-top:4px solid var(--blue); }
  .stat.g{border-color:var(--green)} .stat.a{border-color:var(--amber)} .stat.r{border-color:var(--red)} .stat.v{border-color:var(--violet)}
  .stat b { display:block; font-size:1.3rem; font-weight:800; margin-top:4px; }
  .stat span { font-size:.66rem; text-transform:uppercase; letter-spacing:.06em; color:var(--mut); }

  .barra { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:13px; align-items:center; }
  .barra select, .barra input { padding:8px 12px; border:1px solid var(--line); border-radius:9px;
      background:var(--card); font-size:.83rem; color:var(--ink); outline:none; }
  .barra input[type=search] { flex:1; min-width:180px; }
  .barra .esp { flex:1; }

  .panel { background:var(--card); border-radius:14px; box-shadow:0 1px 8px rgba(23,32,58,.07); overflow:auto; }
  table { width:100%; border-collapse:collapse; font-size:.83rem; }
  th { text-align:left; padding:10px 12px; background:#f7f8fc; color:var(--mut); font-size:.68rem;
       text-transform:uppercase; letter-spacing:.05em; border-bottom:1px solid var(--line); white-space:nowrap; }
  td { padding:9px 12px; border-bottom:1px solid #f0f2f8; vertical-align:middle; }
  tr.row { cursor:default; } tr.row:hover { background:#f8faff; } tr.click { cursor:pointer; }
  td.num, th.num { text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; }

  .chip { display:inline-block; padding:3px 10px; border-radius:20px; font-size:.7rem; font-weight:700; white-space:nowrap; }
  .c-verde{background:#e2f6ec;color:#0b7d4d} .c-ambar{background:#fef2dd;color:#a36508}
  .c-azul{background:#e5edff;color:#2b5cc7} .c-verm{background:#fde5e8;color:#bb2c3d}
  .c-roxo{background:#efe9ff;color:#6740c6} .c-cinza{background:#eef1f6;color:#5a647d}
  .muted { color:var(--mut); } .nowrap { white-space:nowrap; }
  .acao { border:none; background:#eef1f8; border-radius:8px; padding:5px 9px; cursor:pointer; font-size:.78rem; margin-left:4px; }
  .acao:hover { background:#dbe3f5; }

  .overlay { display:none; position:fixed; inset:0; background:rgba(15,22,45,.55); z-index:50;
             align-items:flex-start; justify-content:center; padding:38px 16px; overflow:auto; }
  .overlay.on { display:flex; }
  .modal { background:#fff; border-radius:16px; width:660px; max-width:100%; padding:24px 26px 22px;
           box-shadow:0 18px 60px rgba(0,0,0,.3); }
  .modal.larga { width:860px; }
  .modal h2 { font-size:1.05rem; margin-bottom:15px; }
  .fgrid { display:grid; grid-template-columns:1fr 1fr; gap:12px 14px; }
  .fgrid .full { grid-column:1/-1; }
  label { display:block; font-size:.68rem; text-transform:uppercase; letter-spacing:.05em;
          color:var(--mut); margin-bottom:4px; font-weight:700; }
  .modal input, .modal select, .modal textarea { width:100%; padding:9px 11px; border:1px solid var(--line);
      border-radius:9px; font-size:.85rem; color:var(--ink); outline:none; font-family:inherit; }
  .modal input:focus, .modal select:focus, .modal textarea:focus { border-color:var(--blue); }
  .modal-acts { display:flex; justify-content:space-between; margin-top:18px; gap:10px; }
  .modal-acts .dir { display:flex; gap:10px; }

  .agenda-dia { margin-bottom:16px; }
  .agenda-dia h3 { font-size:.8rem; text-transform:uppercase; letter-spacing:.05em; color:var(--mut); margin-bottom:8px; }
  .ag-item { background:var(--card); border-radius:12px; padding:11px 15px; margin-bottom:7px;
             box-shadow:0 1px 5px rgba(23,32,58,.06); display:flex; align-items:center; gap:12px; border-left:4px solid var(--blue); }
  .ag-item.fam { border-color:var(--amber); } .ag-item.tar { border-color:var(--violet); }
  .ag-item .hora { font-weight:800; font-size:.85rem; min-width:48px; color:#3b466b; }
  .ag-item .tit { flex:1; font-size:.87rem; }

  .cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:12px; }
  .cardp { background:var(--card); border-radius:13px; padding:14px 16px; box-shadow:0 1px 6px rgba(23,32,58,.07);
           border-top:4px solid var(--violet); }
  .cardp h4 { font-size:.92rem; margin-bottom:5px; } .cardp p { font-size:.78rem; color:var(--mut); margin-bottom:8px; }
  .cardp .rodape { display:flex; justify-content:space-between; align-items:center; }

  .secao { margin-bottom:26px; }
  .secao > h2 { font-size:.95rem; margin-bottom:10px; display:flex; align-items:center; gap:10px; }

  .pr-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px 14px; margin:10px 0 16px; }
  .pr-grid .full { grid-column:1/-1; }
  .pr-box { background:#f7f8fc; border-radius:10px; padding:10px 13px; }
  .pr-box b { display:block; font-size:.66rem; text-transform:uppercase; letter-spacing:.05em; color:var(--mut); margin-bottom:3px; }
  .pr-box div { font-size:.84rem; white-space:pre-wrap; }
  .vazio { padding:26px; text-align:center; color:var(--mut); font-size:.85rem; }
</style>
</head>
<body>
<header>
  <div>
    <h1>🗂️ Meu <em>Organizador</em></h1>
    <p>Finanças · YouTube · Consultório · Família · Projetos — gerado em __GERADO__ · edições salvas neste navegador</p>
  </div>
  <div class="hbtns">
    <button class="btn verde" onclick="exportarJSON()">⬇ Exportar JSON</button>
    <button class="btn claro" onclick="restaurar()">↺ Restaurar original</button>
  </div>
</header>

<div class="wrap">
  <div class="tabs" id="tabs"></div>
  <div id="conteudo"></div>
</div>

<div class="overlay" id="overlay"><div class="modal" id="modal"></div></div>

<script>
const ORIGINAL = __DADOS__;
const CHAVE = 'organizador-v1';

let D = carregarEstado();
function carregarEstado(){
  try { const s = localStorage.getItem(CHAVE); if (s) return JSON.parse(s); } catch(e){}
  return JSON.parse(JSON.stringify(ORIGINAL));
}
function salvar(){ try { localStorage.setItem(CHAVE, JSON.stringify(D)); } catch(e){} }
function restaurar(){
  if (!confirm('Descartar todas as edições feitas neste navegador e voltar aos dados originais do banco?')) return;
  localStorage.removeItem(CHAVE); D = JSON.parse(JSON.stringify(ORIGINAL)); render();
}
function exportarJSON(){
  const blob = new Blob([JSON.stringify(D, null, 2)], {type:'application/json'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
  a.download = 'organizador-export.json'; a.click();
}
function novoId(lista){ return lista.reduce((m,x)=>Math.max(m, x.id||0), 0) + 1; }
function esc(s){ return (s==null?'':String(s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function brl(v){ return (v==null?0:v).toLocaleString('pt-BR',{style:'currency',currency:'BRL'}); }
function dbr(iso){ if(!iso) return '—'; const [a,m,d] = iso.split('-'); return `${d}/${m}/${a}`; }
function hoje(){ return new Date().toISOString().slice(0,10); }

// ── abas ────────────────────────────────────────────────────────────────────
const ABAS = [
  ['hoje','📅 Hoje & Agenda'], ['fin','💰 Financeiro'], ['yt','🎬 YouTube'],
  ['pac','🩺 Pacientes'], ['fam','👨‍👩‍👧‍👦 Família'], ['proj','✅ Projetos & Tarefas'], ['arq','📁 Arquivos'],
];
let abaAtual = 'hoje';
let buscaPac = '', filtroFinMes = '', buscaFin = '';

function render(){
  salvar();
  document.getElementById('tabs').innerHTML = ABAS.map(([k,t]) =>
    `<div class="tab ${k===abaAtual?'on':''}" onclick="abaAtual='${k}';render()">${t}</div>`).join('');
  const c = document.getElementById('conteudo');
  c.innerHTML = ({hoje:vHoje, fin:vFin, yt:vYt, pac:vPac, fam:vFam, proj:vProj, arq:vArq})[abaAtual]();
}

// ── HOJE / AGENDA ───────────────────────────────────────────────────────────
function itensAgenda(){
  const itens = [];
  for (const p of D.pacientes)
    for (const a of p.atendimentos)
      if (a.status === 'agendado')
        itens.push({data:a.data, hora:a.hora, cls:'', tit:`Atendimento: ${p.nome}`, sub:a.tipo});
  for (const e of D.familia_eventos){
    const m = D.familia_membros.find(x=>x.id===e.membro_id);
    itens.push({data:e.data, hora:e.hora, cls:'fam', tit:e.titulo + (m?` (${m.nome})`:''), sub:e.tipo});
  }
  for (const t of D.tarefas)
    if (t.data_limite && (t.status==='pendente'||t.status==='fazendo'))
      itens.push({data:t.data_limite, hora:null, cls:'tar', tit:`Tarefa: ${t.titulo}`, sub:t.prioridade});
  return itens.filter(i=>i.data).sort((a,b)=>(a.data+(a.hora||'')) < (b.data+(b.hora||'')) ? -1 : 1);
}
function vHoje(){
  const h = hoje();
  const futuros = itensAgenda().filter(i=>i.data >= h);
  const porDia = {};
  for (const i of futuros.slice(0, 40)) (porDia[i.data] = porDia[i.data]||[]).push(i);

  const pend = D.tarefas.filter(t=>t.status==='pendente'||t.status==='fazendo').length;
  const agHoje = futuros.filter(i=>i.data===h).length;
  const mes = h.slice(0,7);
  const saldo = D.financeiro.filter(f=>f.data && f.data.startsWith(mes))
      .reduce((s,f)=>s + (f.tipo==='receita'?f.valor:-f.valor), 0);
  const emProducao = D.youtube.filter(v=>['roteiro','gravacao','edicao'].includes(v.status)).length;

  let html = `<div class="stats">
    <div class="stat"><span>Compromissos hoje</span><b>${agHoje}</b></div>
    <div class="stat v"><span>Tarefas abertas</span><b>${pend}</b></div>
    <div class="stat ${saldo>=0?'g':'r'}"><span>Saldo do mês</span><b>${brl(saldo)}</b></div>
    <div class="stat a"><span>Vídeos em produção</span><b>${emProducao}</b></div>
  </div>`;

  const dias = Object.keys(porDia).sort();
  if (!dias.length) html += `<div class="panel"><div class="vazio">Nenhum compromisso futuro. Agende atendimentos, eventos ou tarefas nas outras abas.</div></div>`;
  for (const d of dias){
    const rot = d===h ? 'Hoje' : dbr(d);
    html += `<div class="agenda-dia"><h3>${rot} · ${d===h?'':diaSemana(d)}</h3>` +
      porDia[d].map(i=>`<div class="ag-item ${i.cls}"><span class="hora">${i.hora||'—'}</span>
        <span class="tit">${esc(i.tit)}</span><span class="chip c-cinza">${esc(i.sub||'')}</span></div>`).join('') +
      `</div>`;
  }
  return html;
}
function diaSemana(iso){
  return ['domingo','segunda','terça','quarta','quinta','sexta','sábado'][new Date(iso+'T12:00:00').getDay()];
}

// ── formulários genéricos ───────────────────────────────────────────────────
function abrirForm(titulo, campos, item, aoSalvar, aoExcluir){
  const ov = document.getElementById('overlay'), md = document.getElementById('modal');
  md.className = 'modal';
  md.innerHTML = `<h2>${titulo}</h2><div class="fgrid">` + campos.map(c=>{
    const v = item && item[c.k] != null ? item[c.k] : (c.def!==undefined?c.def:'');
    const cls = c.full ? 'full' : '';
    if (c.t === 'select')
      return `<div class="${cls}"><label>${c.l}</label><select id="f_${c.k}">` +
        c.op.map(o=>{const [val,rot]=Array.isArray(o)?o:[o,o];
          return `<option value="${esc(val)}" ${String(val)===String(v)?'selected':''}>${esc(rot)}</option>`;}).join('') +
        `</select></div>`;
    if (c.t === 'textarea')
      return `<div class="${cls}"><label>${c.l}</label><textarea id="f_${c.k}" rows="${c.rows||3}">${esc(v)}</textarea></div>`;
    return `<div class="${cls}"><label>${c.l}</label><input id="f_${c.k}" type="${c.t||'text'}" value="${esc(v)}" ${c.t==='number'?'step="0.01"':''}></div>`;
  }).join('') + `</div>
  <div class="modal-acts">
    <div>${item && aoExcluir ? '<button class="btn perigo" id="f_del">🗑 Excluir</button>' : ''}</div>
    <div class="dir">
      <button class="btn claro" onclick="fecharModal()">Cancelar</button>
      <button class="btn primario" id="f_ok">Salvar</button>
    </div>
  </div>`;
  ov.classList.add('on');
  md.querySelector('#f_ok').onclick = () => {
    const out = {};
    for (const c of campos){
      let v = md.querySelector('#f_'+c.k).value;
      if (c.t === 'number') v = v === '' ? 0 : parseFloat(v);
      if (c.num) v = v === '' ? null : parseInt(v);
      if (v === '') v = null;
      out[c.k] = v;
    }
    aoSalvar(out); fecharModal(); render();
  };
  const del = md.querySelector('#f_del');
  if (del) del.onclick = () => { if (confirm('Excluir este registro?')) { aoExcluir(); fecharModal(); render(); } };
}
function fecharModal(){ document.getElementById('overlay').classList.remove('on'); }
document.getElementById('overlay').addEventListener('click', e => { if (e.target.id==='overlay') fecharModal(); });

function opAreas(){ return [['',' — ']].concat(D.areas.map(a=>[a.id, a.icone+' '+a.nome])); }

// ── FINANCEIRO ──────────────────────────────────────────────────────────────
const F_FIN = [
  {k:'data', l:'Data', t:'date', def:''},
  {k:'tipo', l:'Tipo', t:'select', op:[['despesa','Despesa'],['receita','Receita']]},
  {k:'descricao', l:'Descrição', full:true},
  {k:'valor', l:'Valor (R$)', t:'number'},
  {k:'categoria', l:'Categoria'},
  {k:'conta', l:'Conta / cartão'},
  {k:'pago', l:'Situação', t:'select', op:[[1,'Efetivado'],[0,'Previsto']]},
  {k:'recorrente', l:'Recorrente', t:'select', op:[[0,'Não'],[1,'Sim']]},
  {k:'observacoes', l:'Observações', t:'textarea', full:true, rows:2},
];
function formFin(id){
  const item = D.financeiro.find(x=>x.id===id);
  abrirForm(item?'Editar lançamento':'Novo lançamento', F_FIN,
    item || {data:hoje(), pago:1, recorrente:0},
    out => {
      out.pago = parseInt(out.pago); out.recorrente = parseInt(out.recorrente);
      if (item) Object.assign(item, out);
      else D.financeiro.unshift({id:novoId(D.financeiro), ...out});
    },
    item ? () => { D.financeiro = D.financeiro.filter(x=>x.id!==id); } : null);
}
function vFin(){
  const meses = [...new Set(D.financeiro.map(f=>f.data && f.data.slice(0,7)).filter(Boolean))].sort().reverse();
  if (filtroFinMes && !meses.includes(filtroFinMes)) filtroFinMes = '';
  let lista = D.financeiro.filter(f =>
    (!filtroFinMes || (f.data||'').startsWith(filtroFinMes)) &&
    (!buscaFin || JSON.stringify(f).toLowerCase().includes(buscaFin.toLowerCase())));
  lista = [...lista].sort((a,b)=>(b.data||'') < (a.data||'') ? -1 : 1);

  const rec = lista.filter(f=>f.tipo==='receita').reduce((s,f)=>s+f.valor,0);
  const desp = lista.filter(f=>f.tipo==='despesa').reduce((s,f)=>s+f.valor,0);

  return `<div class="stats">
      <div class="stat g"><span>Receitas ${filtroFinMes?'('+filtroFinMes+')':''}</span><b>${brl(rec)}</b></div>
      <div class="stat r"><span>Despesas ${filtroFinMes?'('+filtroFinMes+')':''}</span><b>${brl(desp)}</b></div>
      <div class="stat ${rec-desp>=0?'g':'r'}"><span>Saldo</span><b>${brl(rec-desp)}</b></div>
    </div>
    <div class="barra">
      <select onchange="filtroFinMes=this.value;render()">
        <option value="">Todos os meses</option>
        ${meses.map(m=>`<option ${m===filtroFinMes?'selected':''}>${m}</option>`).join('')}
      </select>
      <input type="search" placeholder="Buscar lançamento..." value="${esc(buscaFin)}"
             oninput="buscaFin=this.value;render()">
      <span class="esp"></span>
      <button class="btn primario" onclick="formFin()">➕ Novo lançamento</button>
    </div>
    <div class="panel"><table>
      <tr><th>Data</th><th>Descrição</th><th>Categoria</th><th>Conta</th><th class="num">Valor</th><th></th><th></th></tr>
      ${lista.map(f=>`<tr class="row">
        <td class="nowrap">${dbr(f.data)}</td>
        <td>${esc(f.descricao)}${f.pago?'':' <span class="chip c-ambar">previsto</span>'}</td>
        <td class="muted">${esc(f.categoria||'—')}</td>
        <td class="muted">${esc(f.conta||'—')}</td>
        <td class="num" style="color:${f.tipo==='receita'?'var(--green)':'var(--red)'};font-weight:700">
          ${f.tipo==='receita'?'+':'−'} ${brl(f.valor)}</td>
        <td><span class="chip ${f.tipo==='receita'?'c-verde':'c-verm'}">${f.tipo}</span></td>
        <td class="num"><button class="acao" onclick="formFin(${f.id})">✏️</button></td>
      </tr>`).join('') || '<tr><td colspan="7" class="vazio">Nenhum lançamento.</td></tr>'}
    </table></div>`;
}

// ── YOUTUBE ─────────────────────────────────────────────────────────────────
const YT_ST = [['ideia','💡 Ideia'],['roteiro','📝 Roteiro'],['gravacao','🎥 Gravação'],
               ['edicao','✂️ Edição'],['agendado','⏰ Agendado'],['publicado','✅ Publicado']];
const F_YT = [
  {k:'titulo', l:'Título', full:true},
  {k:'status', l:'Etapa', t:'select', op:YT_ST},
  {k:'data_prevista', l:'Data prevista', t:'date'},
  {k:'data_publicacao', l:'Data de publicação', t:'date'},
  {k:'link', l:'Link', full:true},
  {k:'notas', l:'Notas / roteiro', t:'textarea', full:true, rows:3},
];
function formYt(id){
  const item = D.youtube.find(x=>x.id===id);
  abrirForm(item?'Editar vídeo':'Novo vídeo', F_YT, item || {status:'ideia'},
    out => { if (item) Object.assign(item, out);
             else D.youtube.unshift({id:novoId(D.youtube), ...out}); },
    item ? () => { D.youtube = D.youtube.filter(x=>x.id!==id); } : null);
}
function vYt(){
  let html = `<div class="barra"><span class="esp"></span>
    <button class="btn primario" onclick="formYt()">➕ Novo vídeo</button></div>`;
  for (const [st, rot] of YT_ST){
    const vids = D.youtube.filter(v=>v.status===st);
    if (!vids.length) continue;
    html += `<div class="secao"><h2>${rot} <span class="chip c-cinza">${vids.length}</span></h2>
      <div class="panel"><table>
      <tr><th>Título</th><th>Prevista</th><th>Publicado</th><th>Link</th><th></th></tr>
      ${vids.map(v=>`<tr class="row">
        <td>${esc(v.titulo)}${v.notas?`<div class="muted" style="font-size:.75rem">${esc(v.notas)}</div>`:''}</td>
        <td class="nowrap">${dbr(v.data_prevista)}</td>
        <td class="nowrap">${dbr(v.data_publicacao)}</td>
        <td>${v.link?`<a href="${esc(v.link)}" target="_blank">abrir ↗</a>`:'—'}</td>
        <td class="num"><button class="acao" onclick="formYt(${v.id})">✏️</button></td>
      </tr>`).join('')}
      </table></div></div>`;
  }
  if (!D.youtube.length) html += `<div class="panel"><div class="vazio">Nenhum vídeo ainda. Comece com uma 💡 ideia!</div></div>`;
  return html;
}

// ── PACIENTES ───────────────────────────────────────────────────────────────
const F_PAC = [
  {k:'nome', l:'Nome', full:true},
  {k:'telefone', l:'Telefone'},
  {k:'email', l:'E-mail'},
  {k:'data_nascimento', l:'Nascimento', t:'date'},
  {k:'convenio', l:'Convênio'},
  {k:'ativo', l:'Situação', t:'select', op:[[1,'Ativo'],[0,'Inativo']]},
  {k:'observacoes', l:'Observações', t:'textarea', full:true, rows:2},
];
const F_PRONT = [
  {k:'data_abertura', l:'Abertura do prontuário', t:'date'},
  {k:'queixa_principal', l:'Queixa principal', t:'textarea', full:true, rows:2},
  {k:'historico', l:'Histórico', t:'textarea', full:true, rows:3},
  {k:'hipotese_diagnostica', l:'Hipótese diagnóstica', t:'textarea', full:true, rows:2},
  {k:'plano_terapeutico', l:'Plano terapêutico', t:'textarea', full:true, rows:2},
  {k:'observacoes', l:'Observações', t:'textarea', full:true, rows:2},
];
const F_ATEND = [
  {k:'data', l:'Data', t:'date'},
  {k:'hora', l:'Hora', t:'time'},
  {k:'tipo', l:'Tipo', t:'select', op:['consulta','retorno','avaliacao','online']},
  {k:'status', l:'Status', t:'select', op:[['agendado','Agendado'],['realizado','Realizado'],['cancelado','Cancelado'],['faltou','Faltou']]},
  {k:'valor', l:'Valor (R$)', t:'number'},
  {k:'pago', l:'Pagamento', t:'select', op:[[0,'Em aberto'],[1,'Pago']]},
  {k:'evolucao', l:'Evolução da sessão', t:'textarea', full:true, rows:4},
];
function formPac(id){
  const item = D.pacientes.find(x=>x.id===id);
  abrirForm(item?'Editar paciente':'Novo paciente', F_PAC, item || {ativo:1},
    out => {
      out.ativo = parseInt(out.ativo);
      if (item) Object.assign(item, out);
      else D.pacientes.push({id:novoId(D.pacientes), ...out,
        prontuario:{data_abertura:hoje()}, atendimentos:[]});
      D.pacientes.sort((a,b)=>(a.nome||'').localeCompare(b.nome||''));
    },
    item ? () => { D.pacientes = D.pacientes.filter(x=>x.id!==id); } : null);
}
function formPront(pacId){
  const p = D.pacientes.find(x=>x.id===pacId);
  abrirForm('Prontuário — '+p.nome, F_PRONT, p.prontuario,
    out => { p.prontuario = out; setTimeout(()=>detalhePac(pacId), 0); });
}
function formAtend(pacId, atId){
  const p = D.pacientes.find(x=>x.id===pacId);
  const item = p.atendimentos.find(a=>a.id===atId);
  abrirForm(item?'Editar atendimento':'Novo atendimento — '+p.nome, F_ATEND,
    item || {data:hoje(), tipo:'consulta', status:'agendado', valor:0, pago:0},
    out => {
      out.pago = parseInt(out.pago);
      if (item) Object.assign(item, out);
      else p.atendimentos.unshift({id:novoId(p.atendimentos), ...out});
      p.atendimentos.sort((a,b)=>((b.data||'')+(b.hora||'')) < ((a.data||'')+(a.hora||'')) ? -1 : 1);
      setTimeout(()=>detalhePac(pacId), 0);
    },
    item ? () => { p.atendimentos = p.atendimentos.filter(a=>a.id!==atId); setTimeout(()=>detalhePac(pacId), 0); } : null);
}
const AT_CHIP = {agendado:'c-azul', realizado:'c-verde', cancelado:'c-cinza', faltou:'c-verm'};
function detalhePac(id){
  const p = D.pacientes.find(x=>x.id===id);
  if (!p) return;
  const pr = p.prontuario || {};
  const ov = document.getElementById('overlay'), md = document.getElementById('modal');
  md.className = 'modal larga';
  md.innerHTML = `
    <h2>🩺 ${esc(p.nome)} ${p.ativo?'':'<span class="chip c-cinza">inativo</span>'}</h2>
    <p class="muted" style="font-size:.8rem;margin-bottom:4px">
      ${esc(p.telefone||'sem telefone')} · ${esc(p.convenio||'—')} · nasc. ${dbr(p.data_nascimento)}</p>
    <div class="pr-grid">
      <div class="pr-box"><b>Queixa principal</b><div>${esc(pr.queixa_principal||'—')}</div></div>
      <div class="pr-box"><b>Hipótese diagnóstica</b><div>${esc(pr.hipotese_diagnostica||'—')}</div></div>
      <div class="pr-box full"><b>Histórico</b><div>${esc(pr.historico||'—')}</div></div>
      <div class="pr-box"><b>Plano terapêutico</b><div>${esc(pr.plano_terapeutico||'—')}</div></div>
      <div class="pr-box"><b>Observações</b><div>${esc(pr.observacoes||'—')}</div></div>
    </div>
    <div class="barra">
      <b style="font-size:.85rem">Atendimentos (${p.atendimentos.length})</b><span class="esp"></span>
      <button class="btn claro mini" onclick="formPac(${p.id})">✏️ Paciente</button>
      <button class="btn claro mini" onclick="formPront(${p.id})">📋 Editar prontuário</button>
      <button class="btn primario mini" onclick="formAtend(${p.id})">➕ Atendimento</button>
    </div>
    <div class="panel" style="max-height:280px"><table>
      <tr><th>Data</th><th>Hora</th><th>Tipo</th><th>Status</th><th class="num">Valor</th><th>Pgto</th><th>Evolução</th><th></th></tr>
      ${p.atendimentos.map(a=>`<tr class="row">
        <td class="nowrap">${dbr(a.data)}</td><td>${esc(a.hora||'—')}</td><td>${esc(a.tipo)}</td>
        <td><span class="chip ${AT_CHIP[a.status]||'c-cinza'}">${a.status}</span></td>
        <td class="num">${brl(a.valor)}</td>
        <td>${a.pago?'<span class="chip c-verde">pago</span>':'<span class="chip c-ambar">aberto</span>'}</td>
        <td class="muted" style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(a.evolucao||'')}</td>
        <td class="num"><button class="acao" onclick="formAtend(${p.id},${a.id})">✏️</button></td>
      </tr>`).join('') || '<tr><td colspan="8" class="vazio">Nenhum atendimento registrado.</td></tr>'}
    </table></div>
    <div class="modal-acts"><div></div>
      <div class="dir"><button class="btn claro" onclick="fecharModal()">Fechar</button></div></div>`;
  ov.classList.add('on');
}
function vPac(){
  const h = hoje();
  const lista = D.pacientes.filter(p =>
    !buscaPac || (p.nome||'').toLowerCase().includes(buscaPac.toLowerCase()));
  const ativos = D.pacientes.filter(p=>p.ativo).length;
  const semana = [];
  for (const p of D.pacientes) for (const a of p.atendimentos)
    if (a.status==='agendado' && a.data>=h) semana.push(a);
  const receber = D.pacientes.flatMap(p=>p.atendimentos)
    .filter(a=>a.status==='realizado' && !a.pago).reduce((s,a)=>s+(a.valor||0),0);

  return `<div class="stats">
      <div class="stat"><span>Pacientes ativos</span><b>${ativos}</b></div>
      <div class="stat a"><span>Sessões agendadas</span><b>${semana.length}</b></div>
      <div class="stat r"><span>A receber (realizadas)</span><b>${brl(receber)}</b></div>
    </div>
    <div class="barra">
      <input type="search" placeholder="Buscar paciente..." value="${esc(buscaPac)}"
             oninput="buscaPac=this.value;render()">
      <span class="esp"></span>
      <button class="btn primario" onclick="formPac()">➕ Novo paciente</button>
    </div>
    <div class="panel"><table>
      <tr><th>Nome</th><th>Telefone</th><th>Convênio</th><th class="num">Sessões feitas</th><th>Próxima sessão</th><th></th></tr>
      ${lista.map(p=>{
        const feitas = p.atendimentos.filter(a=>a.status==='realizado').length;
        const prox = p.atendimentos.filter(a=>a.status==='agendado' && a.data>=h)
                      .map(a=>a.data).sort()[0];
        return `<tr class="row click" onclick="detalhePac(${p.id})">
          <td><b>${esc(p.nome)}</b>${p.ativo?'':' <span class="chip c-cinza">inativo</span>'}</td>
          <td class="muted">${esc(p.telefone||'—')}</td>
          <td class="muted">${esc(p.convenio||'—')}</td>
          <td class="num">${feitas}</td>
          <td class="nowrap">${prox?dbr(prox):'<span class="muted">—</span>'}</td>
          <td class="num"><button class="acao" onclick="event.stopPropagation();detalhePac(${p.id})">📋 Abrir</button></td>
        </tr>`;}).join('') || '<tr><td colspan="6" class="vazio">Nenhum paciente.</td></tr>'}
    </table></div>
    <p class="muted" style="font-size:.75rem;margin-top:8px">Clique no paciente para ver prontuário e atendimentos.</p>`;
}

// ── FAMÍLIA ─────────────────────────────────────────────────────────────────
const F_MEM = [
  {k:'nome', l:'Nome', full:true},
  {k:'parentesco', l:'Parentesco', t:'select', op:['esposa','marido','filho','filha','outro']},
  {k:'data_nascimento', l:'Nascimento', t:'date'},
  {k:'notas', l:'Notas', t:'textarea', full:true, rows:2},
];
function formMem(id){
  const item = D.familia_membros.find(x=>x.id===id);
  abrirForm(item?'Editar membro':'Novo membro da família', F_MEM, item || {},
    out => { if (item) Object.assign(item, out);
             else D.familia_membros.push({id:novoId(D.familia_membros), ...out}); },
    item ? () => { D.familia_membros = D.familia_membros.filter(x=>x.id!==id); } : null);
}
function fEvt(){ return [
  {k:'titulo', l:'Título', full:true},
  {k:'membro_id', l:'Quem', t:'select', num:true, op:[['',' — família toda']].concat(D.familia_membros.map(m=>[m.id, m.nome]))},
  {k:'tipo', l:'Tipo', t:'select', op:['escola','saude','lazer','casa','aniversario','outro']},
  {k:'data', l:'Data', t:'date'},
  {k:'hora', l:'Hora', t:'time'},
  {k:'notas', l:'Notas', t:'textarea', full:true, rows:2},
]; }
function formEvt(id){
  const item = D.familia_eventos.find(x=>x.id===id);
  abrirForm(item?'Editar evento':'Novo evento da família', fEvt(),
    item || {data:hoje(), tipo:'outro'},
    out => { if (item) Object.assign(item, out);
             else D.familia_eventos.push({id:novoId(D.familia_eventos), ...out}); },
    item ? () => { D.familia_eventos = D.familia_eventos.filter(x=>x.id!==id); } : null);
}
function vFam(){
  const evts = [...D.familia_eventos].sort((a,b)=>(a.data+(a.hora||'')) < (b.data+(b.hora||'')) ? -1 : 1);
  return `<div class="secao"><h2>👨‍👩‍👧‍👦 Membros
      <button class="btn primario mini" onclick="formMem()">➕ Adicionar</button></h2>
    <div class="panel"><table>
      <tr><th>Nome</th><th>Parentesco</th><th>Nascimento</th><th>Notas</th><th></th></tr>
      ${D.familia_membros.map(m=>`<tr class="row">
        <td><b>${esc(m.nome)}</b></td><td>${esc(m.parentesco||'—')}</td>
        <td class="nowrap">${dbr(m.data_nascimento)}</td><td class="muted">${esc(m.notas||'')}</td>
        <td class="num"><button class="acao" onclick="formMem(${m.id})">✏️</button></td>
      </tr>`).join('')}
    </table></div></div>
    <div class="secao"><h2>📆 Eventos e compromissos
      <button class="btn primario mini" onclick="formEvt()">➕ Adicionar</button></h2>
    <div class="panel"><table>
      <tr><th>Data</th><th>Hora</th><th>Título</th><th>Quem</th><th>Tipo</th><th></th></tr>
      ${evts.map(e=>{
        const m = D.familia_membros.find(x=>x.id===e.membro_id);
        return `<tr class="row">
          <td class="nowrap">${dbr(e.data)}</td><td>${esc(e.hora||'—')}</td>
          <td>${esc(e.titulo)}${e.notas?`<div class="muted" style="font-size:.75rem">${esc(e.notas)}</div>`:''}</td>
          <td class="muted">${m?esc(m.nome):'família toda'}</td>
          <td><span class="chip c-ambar">${esc(e.tipo||'outro')}</span></td>
          <td class="num"><button class="acao" onclick="formEvt(${e.id})">✏️</button></td>
        </tr>`;}).join('') || '<tr><td colspan="6" class="vazio">Nenhum evento.</td></tr>'}
    </table></div></div>`;
}

// ── PROJETOS & TAREFAS ──────────────────────────────────────────────────────
const F_PROJ = [
  {k:'nome', l:'Nome do projeto', full:true},
  {k:'area_id', l:'Área', t:'select', num:true, op:[]},
  {k:'status', l:'Status', t:'select', op:[['ideia','💡 Ideia'],['ativo','▶ Ativo'],['pausado','⏸ Pausado'],['concluido','✅ Concluído'],['arquivado','📦 Arquivado']]},
  {k:'prioridade', l:'Prioridade', t:'select', op:['baixa','media','alta']},
  {k:'prazo', l:'Prazo', t:'date'},
  {k:'descricao', l:'Descrição', t:'textarea', full:true, rows:3},
];
function formProj(id){
  const campos = F_PROJ.map(c => c.k==='area_id' ? {...c, op:opAreas()} : c);
  const item = D.projetos.find(x=>x.id===id);
  abrirForm(item?'Editar projeto':'Novo projeto', campos,
    item || {status:'ativo', prioridade:'media'},
    out => { if (item) Object.assign(item, out);
             else D.projetos.push({id:novoId(D.projetos), ...out}); },
    item ? () => { D.projetos = D.projetos.filter(x=>x.id!==id);
                   D.tarefas.forEach(t=>{ if (t.projeto_id===id) t.projeto_id = null; }); } : null);
}
function fTar(){ return [
  {k:'titulo', l:'Tarefa', full:true},
  {k:'projeto_id', l:'Projeto', t:'select', num:true, op:[['',' — avulsa']].concat(D.projetos.map(p=>[p.id, p.nome]))},
  {k:'area_id', l:'Área', t:'select', num:true, op:opAreas()},
  {k:'prioridade', l:'Prioridade', t:'select', op:['baixa','media','alta']},
  {k:'data_limite', l:'Prazo', t:'date'},
  {k:'status', l:'Status', t:'select', op:[['pendente','Pendente'],['fazendo','Fazendo'],['concluida','Concluída'],['cancelada','Cancelada']]},
  {k:'notas', l:'Notas', t:'textarea', full:true, rows:2},
]; }
function formTar(id){
  const item = D.tarefas.find(x=>x.id===id);
  abrirForm(item?'Editar tarefa':'Nova tarefa', fTar(),
    item || {status:'pendente', prioridade:'media'},
    out => {
      out.concluida_em = out.status==='concluida' ? (item && item.concluida_em || hoje()) : null;
      if (item) Object.assign(item, out);
      else D.tarefas.push({id:novoId(D.tarefas), ...out});
    },
    item ? () => { D.tarefas = D.tarefas.filter(x=>x.id!==id); } : null);
}
function toggleTarefa(id){
  const t = D.tarefas.find(x=>x.id===id);
  if (!t) return;
  t.status = t.status==='concluida' ? 'pendente' : 'concluida';
  t.concluida_em = t.status==='concluida' ? hoje() : null;
  render();
}
const PJ_CHIP = {ideia:'c-roxo', ativo:'c-azul', pausado:'c-ambar', concluido:'c-verde', arquivado:'c-cinza'};
const PRI_CHIP = {alta:'c-verm', media:'c-ambar', baixa:'c-cinza'};
function vProj(){
  const abertas = D.tarefas.filter(t=>t.status==='pendente'||t.status==='fazendo');
  const feitas = D.tarefas.filter(t=>t.status==='concluida');
  return `<div class="secao"><h2>📌 Projetos
      <button class="btn primario mini" onclick="formProj()">➕ Novo projeto</button></h2>
    <div class="cards">
      ${D.projetos.map(p=>{
        const a = D.areas.find(x=>x.id===p.area_id);
        const nt = D.tarefas.filter(t=>t.projeto_id===p.id && (t.status==='pendente'||t.status==='fazendo')).length;
        return `<div class="cardp" style="border-color:${a?a.cor:'#7c5cde'}">
          <h4>${a?a.icone+' ':''}${esc(p.nome)}</h4>
          <p>${esc(p.descricao||'')}</p>
          <div class="rodape">
            <span><span class="chip ${PJ_CHIP[p.status]||'c-cinza'}">${p.status}</span>
              ${nt?`<span class="chip c-roxo">${nt} tarefa${nt>1?'s':''}</span>`:''}</span>
            <button class="acao" onclick="formProj(${p.id})">✏️</button>
          </div></div>`;}).join('') || '<div class="vazio">Nenhum projeto.</div>'}
    </div></div>
    <div class="secao"><h2>✅ Tarefas abertas (${abertas.length})
      <button class="btn primario mini" onclick="formTar()">➕ Nova tarefa</button></h2>
    <div class="panel"><table>
      <tr><th></th><th>Tarefa</th><th>Projeto / área</th><th>Prazo</th><th>Prioridade</th><th></th></tr>
      ${abertas.map(t=>linhaTarefa(t)).join('') || '<tr><td colspan="6" class="vazio">Nada pendente. 🎉</td></tr>'}
    </table></div></div>
    ${feitas.length?`<div class="secao"><h2>Concluídas (${feitas.length})</h2>
      <div class="panel"><table>${feitas.map(t=>linhaTarefa(t)).join('')}</table></div></div>`:''}`;
}
function linhaTarefa(t){
  const p = D.projetos.find(x=>x.id===t.projeto_id);
  const a = D.areas.find(x=>x.id===t.area_id);
  const done = t.status==='concluida';
  const atrasada = !done && t.data_limite && t.data_limite < hoje();
  return `<tr class="row">
    <td><input type="checkbox" ${done?'checked':''} onchange="toggleTarefa(${t.id})"></td>
    <td style="${done?'text-decoration:line-through;color:var(--mut)':''}">${esc(t.titulo)}
      ${t.notas?`<div class="muted" style="font-size:.75rem">${esc(t.notas)}</div>`:''}</td>
    <td class="muted">${p?esc(p.nome):(a?a.icone+' '+esc(a.nome):'—')}</td>
    <td class="nowrap" style="${atrasada?'color:var(--red);font-weight:700':''}">${dbr(t.data_limite)}</td>
    <td><span class="chip ${PRI_CHIP[t.prioridade]||'c-cinza'}">${t.prioridade||'—'}</span></td>
    <td class="num"><button class="acao" onclick="formTar(${t.id})">✏️</button></td>
  </tr>`;
}

// ── ARQUIVOS ────────────────────────────────────────────────────────────────
function fArq(){ return [
  {k:'titulo', l:'Título', full:true},
  {k:'caminho', l:'Caminho ou link do arquivo', full:true},
  {k:'area_id', l:'Área', t:'select', num:true, op:opAreas()},
  {k:'categoria', l:'Categoria', t:'select', op:['documento','contrato','nota_fiscal','exame','foto','video','planilha','outro']},
  {k:'data', l:'Data', t:'date'},
  {k:'descricao', l:'Descrição', t:'textarea', full:true, rows:2},
]; }
function formArq(id){
  const item = D.arquivos.find(x=>x.id===id);
  abrirForm(item?'Editar arquivo':'Registrar arquivo', fArq(), item || {},
    out => { if (item) Object.assign(item, out);
             else D.arquivos.push({id:novoId(D.arquivos), ...out}); },
    item ? () => { D.arquivos = D.arquivos.filter(x=>x.id!==id); } : null);
}
function vArq(){
  return `<div class="barra">
      <p class="muted" style="font-size:.8rem">Índice de onde está cada arquivo importante — os arquivos em si ficam nas pastas <b>organizador/arquivos/</b> (financeiro, youtube, pacientes, família, projetos) ou em nuvem.</p>
      <span class="esp"></span>
      <button class="btn primario" onclick="formArq()">➕ Registrar arquivo</button>
    </div>
    <div class="panel"><table>
      <tr><th>Título</th><th>Caminho / link</th><th>Área</th><th>Categoria</th><th>Data</th><th></th></tr>
      ${D.arquivos.map(f=>{
        const a = D.areas.find(x=>x.id===f.area_id);
        const ehLink = /^https?:/.test(f.caminho||'');
        return `<tr class="row">
          <td><b>${esc(f.titulo||'—')}</b>${f.descricao?`<div class="muted" style="font-size:.75rem">${esc(f.descricao)}</div>`:''}</td>
          <td>${ehLink?`<a href="${esc(f.caminho)}" target="_blank">${esc(f.caminho)}</a>`:`<code style="font-size:.78rem">${esc(f.caminho)}</code>`}</td>
          <td>${a?a.icone+' '+esc(a.nome):'—'}</td>
          <td class="muted">${esc(f.categoria||'—')}</td>
          <td class="nowrap">${dbr(f.data)}</td>
          <td class="num"><button class="acao" onclick="formArq(${f.id})">✏️</button></td>
        </tr>`;}).join('') || '<tr><td colspan="6" class="vazio">Nenhum arquivo registrado.</td></tr>'}
    </table></div>`;
}

render();
</script>
</body>
</html>
"""


def main() -> None:
    dados = carregar()
    html = (TEMPLATE
            .replace("__DADOS__", json.dumps(dados, ensure_ascii=False))
            .replace("__GERADO__", date.today().strftime("%d/%m/%Y")))
    SAIDA.write_text(html, encoding="utf-8")
    print(f"Painel gerado em {SAIDA} "
          f"({len(dados['pacientes'])} pacientes, {len(dados['financeiro'])} lançamentos, "
          f"{len(dados['tarefas'])} tarefas)")


if __name__ == "__main__":
    main()
