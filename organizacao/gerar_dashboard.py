#!/usr/bin/env python3
"""Gera index.html — Central de Organização Pessoal.

Uso:  python3 gerar_dashboard.py
Abra index.html no navegador (funciona offline).
"""

import json
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "organizacao.db"
SAIDA = BASE / "index.html"


def carregar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    def rows(sql, *args):
        return [dict(r) for r in conn.execute(sql, args)]

    dados = {
        "dashboard": dict(conn.execute("SELECT * FROM vw_dashboard").fetchone() or {}),
        "pessoas": rows("SELECT * FROM pessoas WHERE ativo=1 ORDER BY id"),
        "areas": rows("SELECT * FROM areas ORDER BY ordem"),
        "projetos": rows("SELECT p.*, a.nome AS area_nome FROM projetos p LEFT JOIN areas a ON a.id=p.area_id ORDER BY p.status, p.prioridade DESC"),
        "tarefas": rows("""SELECT t.*, a.nome AS area_nome FROM tarefas t
                          LEFT JOIN areas a ON a.id=t.area_id
                          WHERE t.status IN ('pendente','em_andamento')
                          ORDER BY t.data_prazo NULLS LAST, t.prioridade DESC"""),
        "pacientes": rows("SELECT * FROM vw_pacientes_resumo ORDER BY codigo"),
        "atendimentos": rows("""SELECT at.*, p.nome AS paciente_nome, p.codigo AS paciente_codigo
                                FROM atendimentos at JOIN pacientes p ON p.id=at.paciente_id
                                ORDER BY at.data DESC, at.hora_inicio LIMIT 100"""),
        "prontuarios": rows("""SELECT pr.*, p.nome AS paciente_nome, p.codigo AS paciente_codigo
                               FROM prontuarios pr JOIN pacientes p ON p.id=pr.paciente_id
                               ORDER BY pr.data_registro DESC LIMIT 50"""),
        "youtube_ideias": rows("SELECT * FROM youtube_ideias ORDER BY status, id DESC"),
        "youtube_videos": rows("SELECT * FROM youtube_videos ORDER BY status, data_publicacao DESC"),
        "financas": rows("""SELECT f.*, c.nome AS categoria FROM financas_lancamentos f
                            JOIN financas_categorias c ON c.id=f.categoria_id
                            ORDER BY f.data DESC LIMIT 80"""),
        "financas_mes": rows("SELECT * FROM vw_financas_mes ORDER BY mes DESC, tipo"),
        "arquivos": rows("SELECT * FROM arquivos ORDER BY categoria, titulo"),
        "agenda": rows("SELECT * FROM vw_agenda_proxima"),
        "notas": rows("SELECT n.*, a.nome AS area_nome FROM notas n LEFT JOIN areas a ON a.id=n.area_id ORDER BY n.fixada DESC, n.atualizado DESC"),
    }
    conn.close()
    return dados


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Central de Organização · Priscila Palomo</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  :root{
    --bg:#f4f6fb;--card:#fff;--ink:#17203a;--mut:#8a93a8;--line:#e6e9f2;
    --rose:#e94560;--violet:#7c5cde;--blue:#2f6fed;--green:#0fa968;--amber:#e8930c;
  }
  body{font-family:'Segoe UI',system-ui,Arial,sans-serif;background:var(--bg);color:var(--ink)}
  header{background:linear-gradient(135deg,#1a1a2e,#16213e 55%,#0f3460);color:#fff;padding:22px 32px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
  header h1{font-size:1.45rem;font-weight:800} header h1 em{color:var(--rose);font-style:normal}
  header p{color:rgba(255,255,255,.55);font-size:.8rem;margin-top:4px}
  .badge{background:var(--rose);font-size:.68rem;padding:4px 12px;border-radius:20px;font-weight:700}
  .nav{background:#1a1a2e;display:flex;padding:0 24px;gap:2px;border-bottom:3px solid var(--rose);overflow-x:auto}
  .nav-tab{padding:11px 18px;cursor:pointer;font-size:.82rem;font-weight:600;color:rgba(255,255,255,.45);border-bottom:3px solid transparent;margin-bottom:-3px;white-space:nowrap;transition:.15s}
  .nav-tab:hover{color:#fff;background:rgba(255,255,255,.05)}
  .nav-tab.on{color:#fff;border-bottom-color:var(--rose);background:rgba(233,69,96,.12)}
  .wrap{max-width:1280px;margin:0 auto;padding:22px 28px 60px}
  .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:12px;margin-bottom:20px}
  .stat{background:var(--card);border-radius:12px;padding:14px 16px;box-shadow:0 1px 6px rgba(23,32,58,.07);border-top:4px solid var(--blue)}
  .stat.r{border-color:var(--rose)}.stat.v{border-color:var(--violet)}.stat.g{border-color:var(--green)}.stat.a{border-color:var(--amber)}
  .stat span{font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}
  .stat b{display:block;font-size:1.35rem;font-weight:800;margin-top:3px}
  .stat small{color:var(--mut);font-size:.7rem}
  .section{display:none}.section.on{display:block}
  .panel{background:var(--card);border-radius:13px;box-shadow:0 1px 8px rgba(23,32,58,.07);overflow:hidden;margin-bottom:18px}
  .panel-h{padding:14px 18px 6px;font-size:.95rem;font-weight:700;display:flex;align-items:center;gap:8px}
  .panel-h .cnt{background:#f3f4f6;color:var(--mut);font-size:.68rem;padding:2px 9px;border-radius:20px;font-weight:600}
  .panel-sub{padding:0 18px 10px;font-size:.74rem;color:var(--mut)}
  .filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;align-items:center}
  .filters input,.filters select{padding:8px 12px;border:1px solid var(--line);border-radius:9px;background:var(--card);font-size:.83rem;outline:none}
  .filters input{flex:1;min-width:200px}
  table{width:100%;border-collapse:collapse;font-size:.82rem}
  th{text-align:left;padding:10px 12px;background:#f7f8fc;color:var(--mut);font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid var(--line);white-space:nowrap}
  td{padding:9px 12px;border-bottom:1px solid #f0f2f8;vertical-align:top}
  tr:hover td{background:#f8faff}
  .chip{display:inline-block;padding:2px 10px;border-radius:20px;font-size:.7rem;font-weight:700;white-space:nowrap}
  .st-ativo,.st-confirmado,.st-realizado,.st-feito,.st-publicado{background:#e2f6ec;color:#0b7d4d}
  .st-agendado,.st-pendente,.st-planejado,.st-ideia{background:#e5edff;color:#2b5cc7}
  .st-pausado,.st-tentativo,.st-em_andamento{background:#fef2dd;color:#a36508}
  .st-cancelado,.st-faltou,.st-negado{background:#fde5e8;color:#bb2c3d}
  .st-alta,.st-urgente{background:#fde5e8;color:#bb2c3d}
  .st-media{background:#e5edff;color:#2b5cc7}
  .st-baixa{background:#f3f4f6;color:#6b7280}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  @media(max-width:900px){.grid2{grid-template-columns:1fr}}
  .fam-card{display:flex;align-items:center;gap:14px;padding:14px 18px;border-bottom:1px solid #f0f2f8}
  .fam-avatar{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;color:#fff;font-size:1rem;flex-shrink:0}
  .fam-name{font-weight:700;font-size:.9rem}
  .fam-rel{font-size:.74rem;color:var(--mut)}
  .fam-notes{font-size:.78rem;color:#4b5563;margin-top:3px}
  .file-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px;padding:14px 18px 18px}
  .fc{background:#fafbfe;border:1px solid var(--line);border-radius:10px;padding:12px 14px;display:flex;gap:10px;align-items:flex-start;text-decoration:none;color:inherit;transition:.15s}
  .fc:hover{box-shadow:0 4px 14px rgba(23,32,58,.1);border-color:#c7d7ff;transform:translateY(-1px)}
  .fi{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0;background:#eef3ff}
  .fname{font-size:.82rem;font-weight:600}
  .fmeta{font-size:.7rem;color:var(--mut);margin-top:2px}
  .note-card{padding:14px 18px;border-bottom:1px solid #f0f2f8}
  .note-title{font-weight:700;font-size:.88rem;margin-bottom:4px}
  .note-body{font-size:.8rem;color:#4b5563;white-space:pre-wrap;line-height:1.5}
  .num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
  .receita{color:var(--green);font-weight:700}
  .despesa{color:var(--rose);font-weight:700}
  .saldo-pos{color:var(--green)}.saldo-neg{color:var(--rose)}
  .yt-card{padding:14px 18px;border-bottom:1px solid #f0f2f8;display:flex;gap:12px;align-items:flex-start}
  .yt-ico{font-size:1.4rem;flex-shrink:0}
  .muted{color:var(--mut);font-size:.74rem}
  .link{color:var(--blue);text-decoration:none}.link:hover{text-decoration:underline}
  .area-pill{display:inline-flex;align-items:center;gap:4px;font-size:.72rem;background:#f3f4f6;padding:2px 9px;border-radius:20px}
  footer{text-align:center;padding:30px;font-size:.72rem;color:var(--mut)}
</style>
</head>
<body>
<header>
  <div>
    <h1>Central de <em>Organização</em></h1>
    <p>Priscila Palomo · Família · Consultório · YouTube · Finanças · Projetos</p>
  </div>
  <span class="badge" id="dataHoje"></span>
  <div style="display:flex;gap:8px;flex-wrap:wrap">
    <a href="cadastro_pacientes.html" style="font-size:.78rem;color:#fff;background:rgba(255,255,255,.12);padding:6px 14px;border-radius:8px;text-decoration:none;font-weight:600">✏️ Cadastrar pacientes</a>
    <a href="investimentos.html" style="font-size:.78rem;color:#fff;background:rgba(255,255,255,.12);padding:6px 14px;border-radius:8px;text-decoration:none;font-weight:600">📈 Investimentos</a>
    <a href="../reembolsos/index.html" style="font-size:.78rem;color:#fff;background:rgba(255,255,255,.12);padding:6px 14px;border-radius:8px;text-decoration:none;font-weight:600">🏥 Reembolsos</a>
  </div>
</header>

<nav class="nav" id="nav">
  <div class="nav-tab on" data-sec="visao">🏠 Visão Geral</div>
  <div class="nav-tab" data-sec="familia">👨‍👩‍👧‍👦 Família</div>
  <div class="nav-tab" data-sec="consultorio">🧠 Consultório</div>
  <div class="nav-tab" data-sec="youtube">▶️ YouTube</div>
  <div class="nav-tab" data-sec="financas">💰 Finanças</div>
  <div class="nav-tab" data-sec="invest">📈 Investimentos</div>
  <div class="nav-tab" data-sec="projetos">📋 Projetos</div>
  <div class="nav-tab" data-sec="arquivos">📁 Arquivos</div>
  <div class="nav-tab" data-sec="agenda">📅 Agenda</div>
</nav>

<div class="wrap">

<!-- VISÃO GERAL -->
<div class="section on" id="sec-visao">
  <div class="stats" id="statsVisao"></div>
  <div class="grid2">
    <div class="panel">
      <div class="panel-h">📅 Próximos eventos <span class="cnt" id="cntAgenda"></span></div>
      <div id="agendaResumo"></div>
    </div>
    <div class="panel">
      <div class="panel-h">✅ Tarefas abertas <span class="cnt" id="cntTarefas"></span></div>
      <div id="tarefasResumo"></div>
    </div>
  </div>
  <div class="panel" style="margin-top:16px">
    <div class="panel-h">📌 Notas fixas</div>
    <div id="notasFixas"></div>
  </div>
</div>

<!-- FAMÍLIA -->
<div class="section" id="sec-familia">
  <div class="panel">
    <div class="panel-h">👨‍👩‍👧‍👦 Família Palomo</div>
    <div class="panel-sub">Priscila · Luisa · João Guilherme · Ana Luisa</div>
    <div id="familiaLista"></div>
  </div>
  <div class="panel">
    <div class="panel-h">🏥 Saúde da família</div>
    <div class="panel-sub">Reembolsos e documentos médicos → <a class="link" href="../reembolsos/index.html">Painel de Reembolsos</a></div>
    <div class="file-grid" id="familiaArquivos"></div>
  </div>
</div>

<!-- CONSULTÓRIO -->
<div class="section" id="sec-consultorio">
  <div class="stats" id="statsConsultorio"></div>
  <div class="filters">
    <input type="search" id="buscaPaciente" placeholder="Buscar paciente por nome ou código…">
    <select id="filtroPacStatus"><option value="">Todos os status</option><option value="ativo">Ativo</option><option value="alta">Alta</option><option value="pausado">Pausado</option></select>
  </div>
  <div class="panel">
    <div class="panel-h">🧠 Pacientes <span class="cnt" id="cntPacientes"></span></div>
    <div style="overflow-x:auto"><table><thead><tr>
      <th>Código</th><th>Nome</th><th>Status</th><th>Horário</th><th>Freq.</th><th>Última sessão</th><th>Próxima</th><th>Sessões</th><th>Prontuário</th>
    </tr></thead><tbody id="tbPacientes"></tbody></table></div>
  </div>
  <div class="grid2" style="margin-top:16px">
    <div class="panel">
      <div class="panel-h">📅 Atendimentos recentes</div>
      <div style="overflow-x:auto"><table><thead><tr>
        <th>Data</th><th>Hora</th><th>Paciente</th><th>Tipo</th><th>Status</th><th class="num">Valor</th>
      </tr></thead><tbody id="tbAtendimentos"></tbody></table></div>
    </div>
    <div class="panel">
      <div class="panel-h">📋 Prontuários recentes</div>
      <div style="overflow-x:auto"><table><thead><tr>
        <th>Data</th><th>Paciente</th><th>Tipo</th><th>Título</th>
      </tr></thead><tbody id="tbProntuarios"></tbody></table></div>
    </div>
  </div>
</div>

<!-- YOUTUBE -->
<div class="section" id="sec-youtube">
  <div class="stats" id="statsYoutube"></div>
  <div class="grid2">
    <div class="panel">
      <div class="panel-h">💡 Ideias de vídeo <span class="cnt" id="cntIdeias"></span></div>
      <div id="ytIdeias"></div>
    </div>
    <div class="panel">
      <div class="panel-h">🎬 Vídeos <span class="cnt" id="cntVideos"></span></div>
      <div id="ytVideos"></div>
    </div>
  </div>
</div>

<!-- FINANÇAS -->
<div class="section" id="sec-financas">
  <div class="stats" id="statsFinancas"></div>
  <div class="panel">
    <div class="panel-h">💰 Lançamentos recentes</div>
    <div style="overflow-x:auto"><table><thead><tr>
      <th>Data</th><th>Categoria</th><th>Descrição</th><th>Tipo</th><th class="num">Valor</th><th>Pago</th>
    </tr></thead><tbody id="tbFinancas"></tbody></table></div>
  </div>
</div>

<!-- INVESTIMENTOS -->
<div class="section" id="sec-invest">
  <div class="panel" style="text-align:center;padding:40px 24px">
    <div style="font-size:2.5rem;margin-bottom:12px">📈</div>
    <h2 style="font-size:1.2rem;margin-bottom:8px">Carteira de Investimentos</h2>
    <p style="color:var(--mut);font-size:.85rem;margin-bottom:20px;max-width:480px;margin-left:auto;margin-right:auto">
      Itaú VGBL · XPML11 · Tesouro Pré e mais. Visualize sua carteira e simule quanto terá em 20 anos.
    </p>
    <a href="investimentos.html" style="display:inline-block;background:var(--green);color:#fff;padding:12px 28px;border-radius:10px;text-decoration:none;font-weight:700;font-size:.9rem">Abrir painel de investimentos →</a>
    <p style="color:var(--mut);font-size:.74rem;margin-top:16px">Edite <code>templates/investimentos.csv</code> para adicionar ativos</p>
  </div>
</div>

<!-- PROJETOS -->
<div class="section" id="sec-projetos">
  <div class="panel">
    <div class="panel-h">📋 Projetos <span class="cnt" id="cntProjetos"></span></div>
    <div style="overflow-x:auto"><table><thead><tr>
      <th>Área</th><th>Projeto</th><th>Status</th><th>Prioridade</th><th>Prazo</th><th>Descrição</th>
    </tr></thead><tbody id="tbProjetos"></tbody></table></div>
  </div>
</div>

<!-- ARQUIVOS -->
<div class="section" id="sec-arquivos">
  <div class="filters">
    <input type="search" id="buscaArquivo" placeholder="Buscar arquivo…">
    <select id="filtroArqCat"><option value="">Todas categorias</option></select>
  </div>
  <div class="panel">
    <div class="panel-h">📁 Índice de arquivos <span class="cnt" id="cntArquivos"></span></div>
    <div class="file-grid" id="arqGrid"></div>
  </div>
</div>

<!-- AGENDA -->
<div class="section" id="sec-agenda">
  <div class="panel">
    <div class="panel-h">📅 Agenda (próximos 30 dias)</div>
    <div style="overflow-x:auto"><table><thead><tr>
      <th>Data</th><th>Hora</th><th>Evento</th><th>Tipo</th><th>Paciente</th><th>Local</th><th>Status</th>
    </tr></thead><tbody id="tbAgenda"></tbody></table></div>
  </div>
</div>

</div>
<footer>Gerado por gerar_dashboard.py · Edite dados em organizacao.db ou importe CSV · Regenere com python3 gerar_dashboard.py</footer>

<script>
const D = __DADOS__;

const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const fmt = n => n==null?'—':Number(n).toLocaleString('pt-BR',{minimumFractionDigits:0,maximumFractionDigits:0});
const fmtR = n => n==null?'—':'R$ '+Number(n).toLocaleString('pt-BR',{minimumFractionDigits:2});
const fmtD = d => d?new Date(d+'T12:00:00').toLocaleDateString('pt-BR'):'—';
const chip = (v,cls) => `<span class="chip st-${(cls||v||'').replace(/ /g,'_')}">${v||'—'}</span>`;
const ico = t => ({pdf:'📄',xlsx:'📊',csv:'📈',html:'🌐',doc:'📝',img:'🖼️',video:'🎬'}[t]||'📎');

$('#dataHoje').textContent = new Date().toLocaleDateString('pt-BR',{weekday:'long',day:'numeric',month:'long',year:'numeric'});

// Nav
$$('.nav-tab').forEach(t => t.onclick = () => {
  $$('.nav-tab').forEach(x=>x.classList.remove('on'));
  $$('.section').forEach(x=>x.classList.remove('on'));
  t.classList.add('on');
  $('#sec-'+t.dataset.sec).classList.add('on');
});

const dash = D.dashboard;

// Stats visão
$('#statsVisao').innerHTML = [
  ['Pacientes ativos',dash.pacientes_ativos,'consultório','r'],
  ['Atendimentos hoje',dash.atendimentos_hoje,'agenda do dia','v'],
  ['Esta semana',dash.atendimentos_semana,'atendimentos','blue'],
  ['Tarefas abertas',dash.tarefas_abertas,'pendentes','a'],
  ['Projetos ativos',dash.projetos_ativos,'em andamento','g'],
  ['Vídeos produção',dash.videos_em_producao,'YouTube','r'],
  ['Receita mês',fmtR(dash.receita_mes),'','g'],
  ['Despesa mês',fmtR(dash.despesa_mes),'','r'],
].map(([l,v,d,c])=>`<div class="stat ${c}"><span>${l}</span><b>${v}</b><small>${d}</small></div>`).join('');

// Agenda resumo
const ag = D.agenda.slice(0,8);
$('#cntAgenda').textContent = D.agenda.length;
$('#agendaResumo').innerHTML = ag.length ? `<table><tbody>${ag.map(e=>`<tr>
  <td class="nowrap">${fmtD(e.data_inicio)}</td>
  <td class="muted">${e.hora_inicio||''}</td>
  <td><b>${e.titulo}</b><br><span class="muted">${e.tipo}${e.paciente_nome?' · '+e.paciente_nome:''}</span></td>
  <td>${chip(e.status)}</td>
</tr>`).join('')}</tbody></table>` : '<p style="padding:14px 18px;color:var(--mut)">Nenhum evento nos próximos dias.</p>';

// Tarefas
$('#cntTarefas').textContent = D.tarefas.length;
$('#tarefasResumo').innerHTML = D.tarefas.length ? `<table><tbody>${D.tarefas.slice(0,8).map(t=>`<tr>
  <td><b>${t.titulo}</b><br><span class="muted">${t.area_nome||''}</span></td>
  <td>${chip(t.prioridade)}</td>
  <td class="nowrap">${fmtD(t.data_prazo)}</td>
</tr>`).join('')}</tbody></table>` : '<p style="padding:14px 18px;color:var(--mut)">Nenhuma tarefa aberta.</p>';

// Notas
$('#notasFixas').innerHTML = D.notas.map(n=>`<div class="note-card">
  <div class="note-title">${n.fixada?'📌 ':''}${n.titulo||'Nota'}</div>
  <div class="note-body">${n.conteudo}</div>
</div>`).join('');

// Família
$('#familiaLista').innerHTML = D.pessoas.map(p=>`<div class="fam-card">
  <div class="fam-avatar" style="background:${p.cor}">${(p.apelido||p.nome)[0]}</div>
  <div><div class="fam-name">${p.nome}</div><div class="fam-rel">${p.relacao}${p.apelido?' · '+p.apelido:''}</div>
  ${p.notas?`<div class="fam-notes">${p.notas}</div>`:''}</div>
</div>`).join('');

const arqFam = D.arquivos.filter(a=>a.categoria==='familia'||a.categoria==='medico');
$('#familiaArquivos').innerHTML = arqFam.map(a=>`<a class="fc" href="${a.caminho}" target="_blank">
  <div class="fi">${ico(a.tipo_arquivo)}</div>
  <div><div class="fname">${a.titulo}</div><div class="fmeta">${a.descricao||a.categoria}</div></div>
</a>`).join('');

// Consultório stats
$('#statsConsultorio').innerHTML = [
  ['Pacientes ativos',dash.pacientes_ativos,'','r'],
  ['Sessões esta semana',dash.atendimentos_semana,'','v'],
  ['Prontuários',D.prontuarios.length,'registros recentes','g'],
].map(([l,v,d,c])=>`<div class="stat ${c}"><span>${l}</span><b>${v}</b><small>${d}</small></div>`).join('');

function renderPacientes(){
  const q = $('#buscaPaciente').value.toLowerCase();
  const st = $('#filtroPacStatus').value;
  const lista = D.pacientes.filter(p=>
    (!st||p.status===st) && (!q||p.nome.toLowerCase().includes(q)||(p.codigo||'').toLowerCase().includes(q))
  );
  $('#cntPacientes').textContent = lista.length;
  $('#tbPacientes').innerHTML = lista.map(p=>`<tr>
    <td><b>${p.codigo||'—'}</b></td>
    <td>${p.nome}</td>
    <td>${chip(p.status)}</td>
    <td class="muted">${p.dia_horario||'—'}</td>
    <td class="muted">${p.frequencia||'—'}</td>
    <td class="nowrap">${fmtD(p.ultima_sessao)}</td>
    <td class="nowrap">${fmtD(p.proxima_sessao)}</td>
    <td class="num">${p.sessoes_realizadas||0}</td>
    <td class="num">${p.registros_prontuario||0}</td>
  </tr>`).join('');
}
$('#buscaPaciente').oninput = renderPacientes;
$('#filtroPacStatus').onchange = renderPacientes;
renderPacientes();

$('#tbAtendimentos').innerHTML = D.atendimentos.map(a=>`<tr>
  <td class="nowrap">${fmtD(a.data)}</td>
  <td>${a.hora_inicio||'—'}</td>
  <td>${a.paciente_nome}</td>
  <td>${a.tipo}</td>
  <td>${chip(a.status)}</td>
  <td class="num">${a.valor?fmtR(a.valor):'—'}</td>
</tr>`).join('');

$('#tbProntuarios').innerHTML = D.prontuarios.length ? D.prontuarios.map(p=>`<tr>
  <td class="nowrap">${fmtD(p.data_registro)}</td>
  <td>${p.paciente_nome}</td>
  <td>${p.tipo}</td>
  <td>${p.titulo||p.conteudo.slice(0,60)+'…'}</td>
</tr>`).join('') : '<tr><td colspan="4" style="color:var(--mut);padding:16px">Nenhum prontuário cadastrado ainda. Importe ou adicione via banco.</td></tr>';

// YouTube
$('#statsYoutube').innerHTML = [
  ['Ideias',D.youtube_ideias.length,'no banco','v'],
  ['Em produção',dash.videos_em_producao,'vídeos','r'],
  ['Publicados',D.youtube_videos.filter(v=>v.status==='publicado').length,'total','g'],
].map(([l,v,d,c])=>`<div class="stat ${c}"><span>${l}</span><b>${v}</b><small>${d}</small></div>`).join('');

$('#cntIdeias').textContent = D.youtube_ideias.length;
$('#ytIdeias').innerHTML = D.youtube_ideias.map(i=>`<div class="yt-card">
  <div class="yt-ico">💡</div>
  <div><b>${i.titulo}</b><br><span class="muted">${i.descricao||''}</span><br>${chip(i.status)} ${i.tags?'<span class="muted"> · '+i.tags+'</span>':''}</div>
</div>`).join('');

$('#cntVideos').textContent = D.youtube_videos.length;
$('#ytVideos').innerHTML = D.youtube_videos.length ? D.youtube_videos.map(v=>`<div class="yt-card">
  <div class="yt-ico">🎬</div>
  <div><b>${v.titulo}</b> ${chip(v.status)}<br>
  <span class="muted">${v.data_publicacao?'Publicado: '+fmtD(v.data_publicacao):v.data_gravacao?'Gravação: '+fmtD(v.data_gravacao):''}</span>
  ${v.url?`<br><a class="link" href="${v.url}" target="_blank">Ver no YouTube</a>`:''}</div>
</div>`).join('') : '<p style="padding:14px 18px;color:var(--mut)">Nenhum vídeo cadastrado.</p>';

// Finanças
const saldo = (dash.receita_mes||0) - (dash.despesa_mes||0);
$('#statsFinancas').innerHTML = [
  ['Receita mês',fmtR(dash.receita_mes),'','g'],
  ['Despesa mês',fmtR(dash.despesa_mes),'','r'],
  ['Saldo mês',fmtR(saldo),saldo>=0?'positivo':'negativo', saldo>=0?'g':'r'],
].map(([l,v,d,c])=>`<div class="stat ${c}"><span>${l}</span><b class="${l.includes('Saldo')?(saldo>=0?'saldo-pos':'saldo-neg'):''}">${v}</b><small>${d}</small></div>`).join('');

$('#tbFinancas').innerHTML = D.financas.length ? D.financas.map(f=>`<tr>
  <td class="nowrap">${fmtD(f.data)}</td>
  <td>${f.categoria}</td>
  <td>${f.descricao}</td>
  <td>${chip(f.tipo)}</td>
  <td class="num ${f.tipo}">${fmtR(f.valor)}</td>
  <td>${f.pago?'✅':'⏳'}</td>
</tr>`).join('') : '<tr><td colspan="6" style="color:var(--mut);padding:16px">Nenhum lançamento. Importe templates/financas.csv</td></tr>';

// Projetos
$('#cntProjetos').textContent = D.projetos.length;
$('#tbProjetos').innerHTML = D.projetos.map(p=>`<tr>
  <td><span class="area-pill">${p.area_nome||'—'}</span></td>
  <td><b>${p.titulo}</b></td>
  <td>${chip(p.status)}</td>
  <td>${chip(p.prioridade)}</td>
  <td class="nowrap">${fmtD(p.data_prazo)}</td>
  <td class="muted">${p.descricao||'—'}</td>
</tr>`).join('');

// Arquivos
const cats = [...new Set(D.arquivos.map(a=>a.categoria))].sort();
$('#filtroArqCat').innerHTML = '<option value="">Todas categorias</option>'+cats.map(c=>`<option value="${c}">${c}</option>`).join('');

function renderArquivos(){
  const q = $('#buscaArquivo').value.toLowerCase();
  const cat = $('#filtroArqCat').value;
  const lista = D.arquivos.filter(a=>(!cat||a.categoria===cat)&&(!q||a.titulo.toLowerCase().includes(q)||(a.descricao||'').toLowerCase().includes(q)));
  $('#cntArquivos').textContent = lista.length;
  $('#arqGrid').innerHTML = lista.map(a=>`<a class="fc" href="${a.caminho}" target="_blank">
    <div class="fi">${ico(a.tipo_arquivo)}</div>
    <div><div class="fname">${a.titulo}</div><div class="fmeta">${a.categoria} · ${a.descricao||a.caminho}</div></div>
  </a>`).join('');
}
$('#buscaArquivo').oninput = renderArquivos;
$('#filtroArqCat').onchange = renderArquivos;
renderArquivos();

// Agenda completa
$('#tbAgenda').innerHTML = D.agenda.length ? D.agenda.map(e=>`<tr>
  <td class="nowrap">${fmtD(e.data_inicio)}</td>
  <td>${e.hora_inicio||'—'}</td>
  <td><b>${e.titulo}</b></td>
  <td>${chip(e.tipo)}</td>
  <td>${e.paciente_nome||e.pessoa_nome||'—'}</td>
  <td class="muted">${e.local||'—'}</td>
  <td>${chip(e.status)}</td>
</tr>`).join('') : '<tr><td colspan="7" style="color:var(--mut);padding:16px">Agenda vazia. Importe templates/agenda.csv</td></tr>';
</script>
</body>
</html>"""


def main():
    if not DB.exists():
        raise SystemExit("Banco não encontrado. Rode: python3 organizacao.py init")
    dados = carregar()
    html = TEMPLATE.replace("__DADOS__", json.dumps(dados, ensure_ascii=False))
    SAIDA.write_text(html, encoding="utf-8")
    print(f"✓ Painel gerado: {SAIDA}  ({SAIDA.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
