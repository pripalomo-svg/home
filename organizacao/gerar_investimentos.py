#!/usr/bin/env python3
"""Gera investimentos.html — painel de carteira e projeção.

Uso:  python3 gerar_investimentos.py
"""

import json
import math
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "organizacao.db"
SAIDA = BASE / "investimentos.html"


def carregar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    inv = [dict(r) for r in conn.execute("SELECT * FROM vw_investimentos_resumo")]
    totais = dict(conn.execute("SELECT * FROM vw_investimentos_totais").fetchone() or {})
    cfg = {r["chave"]: r["valor"] for r in conn.execute("SELECT * FROM investimentos_config")}
    conn.close()
    return inv, totais, cfg


def projetar_meses(pv, taxa_aa, pmt, meses):
    """Valor futuro com juros compostos mensais + aporte no fim de cada mês."""
    if meses <= 0:
        return pv
    r = taxa_aa / 100 / 12
    if abs(r) < 1e-9:
        return pv + pmt * meses
    fv = pv
    for _ in range(meses):
        fv = fv * (1 + r) + pmt
    return fv


def serie_anual(inv, aporte_global, anos):
    """Gera série ano a ano da carteira total."""
    meses = anos * 12
    patrimonio = sum(i["valor_atual"] for i in inv)
    total_aportes_cadastrados = sum(i.get("aporte_mensal") or 0 for i in inv)

    # Distribui aporte global: usa aportes cadastrados como proporção, ou divide igual
    if total_aportes_cadastrados > 0 and aporte_global > 0:
        fator = aporte_global / total_aportes_cadastrados
        aportes = [(i.get("aporte_mensal") or 0) * fator for i in inv]
    elif aporte_global > 0:
        aportes = [aporte_global / len(inv)] * len(inv) if inv else []
    else:
        aportes = [i.get("aporte_mensal") or 0 for i in inv]

    # Estado por ativo
    saldos = [i["valor_atual"] for i in inv]
    taxas = [i.get("taxa_anual") or 10 for i in inv]

    pontos = [{"ano": 0, "total": round(patrimonio, 2), "aportes_acum": 0}]
    aportes_acum = 0

    for ano in range(1, anos + 1):
        for mes in range(12):
            for j in range(len(saldos)):
                r = taxas[j] / 100 / 12
                saldos[j] = saldos[j] * (1 + r) + aportes[j]
                aportes_acum += aportes[j]
        pontos.append({
            "ano": ano,
            "total": round(sum(saldos), 2),
            "aportes_acum": round(aportes_acum, 2),
        })
    return pontos, aportes


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Investimentos · Carteira & Projeção 20 anos</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  :root{--bg:#0b1020;--card:#141b2e;--card2:#1a2340;--ink:#e8ecf4;--mut:#8b95ad;--line:#2a3555;
    --green:#22c55e;--blue:#3b82f6;--violet:#a78bfa;--amber:#f59e0b;--rose:#f43f5e;--orange:#f97316}
  body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--ink);min-height:100vh}
  header{background:linear-gradient(135deg,#0f172a,#1e3a5f 60%,#0f3460);padding:22px 28px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;border-bottom:1px solid var(--line)}
  header h1{font-size:1.35rem;font-weight:800} header h1 em{color:var(--green);font-style:normal;font-weight:800}
  header p{color:var(--mut);font-size:.78rem;margin-top:3px}
  .links a{font-size:.76rem;color:var(--ink);text-decoration:none;background:var(--card2);padding:6px 14px;border-radius:8px;border:1px solid var(--line);margin-left:6px}
  .links a:hover{border-color:var(--blue)}
  .wrap{max-width:1200px;margin:0 auto;padding:22px 24px 60px}
  .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:22px}
  .stat{background:var(--card);border-radius:14px;padding:16px 18px;border:1px solid var(--line)}
  .stat span{font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}
  .stat b{display:block;font-size:1.5rem;font-weight:800;margin-top:4px;color:var(--green)}
  .stat small{color:var(--mut);font-size:.7rem}
  .grid2{display:grid;grid-template-columns:1.1fr .9fr;gap:18px}
  @media(max-width:960px){.grid2{grid-template-columns:1fr}}
  .panel{background:var(--card);border-radius:14px;border:1px solid var(--line);overflow:hidden;margin-bottom:18px}
  .panel-h{padding:14px 18px 8px;font-weight:700;font-size:.95rem;display:flex;justify-content:space-between;align-items:center}
  .panel-sub{padding:0 18px 12px;font-size:.74rem;color:var(--mut)}
  table{width:100%;border-collapse:collapse;font-size:.82rem}
  th{text-align:left;padding:10px 14px;color:var(--mut);font-size:.67rem;text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid var(--line);background:var(--card2)}
  td{padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:middle}
  tr:hover td{background:rgba(59,130,246,.06)}
  .num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
  .tipo{display:inline-block;padding:2px 9px;border-radius:20px;font-size:.68rem;font-weight:700;background:var(--card2);border:1px solid var(--line)}
  .dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px}
  .alloc{display:flex;height:10px;border-radius:6px;overflow:hidden;margin:12px 18px 18px}
  .alloc div{height:100%}
  .ctrl{background:var(--card2);border-radius:12px;padding:16px 18px;margin:0 18px 18px;border:1px solid var(--line)}
  .ctrl label{font-size:.72rem;color:var(--mut);text-transform:uppercase;letter-spacing:.04em;display:block;margin-bottom:6px}
  .ctrl input[type=range]{width:100%;accent-color:var(--green)}
  .ctrl input[type=number]{width:100%;padding:10px 12px;border-radius:9px;border:1px solid var(--line);background:var(--bg);color:var(--ink);font-size:1rem;font-weight:700}
  .ctrl-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
  .big-result{text-align:center;padding:20px 18px 24px}
  .big-result .val{font-size:2.2rem;font-weight:900;color:var(--green);line-height:1.1}
  .big-result .sub{color:var(--mut);font-size:.8rem;margin-top:6px}
  .chart{padding:8px 18px 18px}
  .bar-row{display:grid;grid-template-columns:36px 1fr 90px;align-items:center;gap:8px;margin-bottom:6px;font-size:.75rem}
  .bar-bg{background:var(--card2);border-radius:5px;height:18px;overflow:hidden}
  .bar{height:100%;border-radius:5px;background:linear-gradient(90deg,var(--blue),var(--green));transition:width .4s}
  .marcos{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;padding:0 18px 18px}
  .marco{background:var(--card2);border-radius:10px;padding:12px;text-align:center;border:1px solid var(--line)}
  .marco b{display:block;font-size:1rem;color:var(--green);margin-top:4px}
  .marco span{font-size:.65rem;color:var(--mut);text-transform:uppercase}
  .legenda{padding:0 18px 14px;font-size:.72rem;color:var(--mut)}
  footer{text-align:center;padding:24px;font-size:.7rem;color:var(--mut)}
  .chip-taxa{color:var(--amber);font-weight:700;font-size:.78rem}
</style>
</head>
<body>
<header>
  <div>
    <h1>Carteira de <em>Investimentos</em></h1>
    <p>Aplicações pessoais de Priscila Palomo (sem relação com pacientes) · Atualizado em <span id="dataRef"></span></p>
  </div>
  <div class="links">
    <a href="index.html">← Organização</a>
    <a href="templates/investimentos.csv">📄 Template CSV</a>
  </div>
</header>
<div class="wrap">
  <div class="stats" id="stats"></div>
  <div class="panel">
    <div class="panel-h">Alocação da carteira</div>
    <div class="alloc" id="allocBar"></div>
    <div class="legenda" id="allocLeg"></div>
  </div>
  <div class="grid2">
    <div class="panel">
      <div class="panel-h">Meus ativos <span style="font-size:.72rem;color:var(--mut);font-weight:400" id="cntAtivos"></span></div>
      <div class="panel-sub">Edite <code style="color:var(--green)">templates/investimentos.csv</code> e rode <code style="color:var(--green)">python3 importar_investimentos.py</code></div>
      <div style="overflow-x:auto"><table>
        <thead><tr>
          <th>Ativo</th><th>Titular</th><th>Tipo</th><th class="num">Valor atual</th>
          <th class="num">Taxa a.a.</th><th class="num">Aporte/mês</th><th>Atualização</th>
        </tr></thead>
        <tbody id="tbInv"></tbody>
      </table></div>
    </div>
    <div class="panel">
      <div class="panel-h">🔮 Projeção · 20 anos</div>
      <div class="panel-sub">Simulação com juros compostos. Não é garantia de retorno.</div>
      <div class="ctrl">
        <div class="ctrl-row">
          <div>
            <label>Aporte mensal total (R$)</label>
            <input type="number" id="aporteGlobal" min="0" step="50" value="500">
          </div>
          <div>
            <label>Anos de projeção</label>
            <input type="number" id="anosProj" min="1" max="40" value="20">
          </div>
        </div>
        <label>Distribuição do aporte (proporcional aos aportes cadastrados por ativo)</label>
        <input type="range" id="sliderAporte" min="0" max="5000" step="50" value="500">
      </div>
      <div class="big-result">
        <div class="val" id="valorFinal">—</div>
        <div class="sub" id="resultadoSub">em 20 anos</div>
      </div>
      <div class="marcos" id="marcos"></div>
      <div class="panel-h" style="font-size:.85rem">Evolução estimada</div>
      <div class="chart" id="chart"></div>
    </div>
  </div>
  <div class="panel">
    <div class="panel-h">📋 Detalhes por ativo (projeção individual)</div>
    <div style="overflow-x:auto"><table>
      <thead><tr>
        <th>Ativo</th><th class="num">Hoje</th><th class="num">Aporte/mês</th>
        <th class="num">Taxa</th><th class="num">Em 20 anos</th><th class="num">Ganho estimado</th>
      </tr></thead>
      <tbody id="tbProj"></tbody>
    </table></div>
  </div>
</div>
<footer>Gerado por gerar_investimentos.py · Edite templates/investimentos.csv · Regenere com python3 gerar_investimentos.py</footer>
<script>
const INV = __INVESTIMENTOS__;
const CFG = __CONFIG__;
const SERIE = __SERIE__;

const fmt = n => 'R$ ' + Number(n).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
const fmtD = d => d ? new Date(d+'T12:00:00').toLocaleDateString('pt-BR') : '—';
const pct = n => Number(n).toFixed(2).replace('.',',') + '%';

document.getElementById('dataRef').textContent = new Date().toLocaleDateString('pt-BR');

const total = INV.reduce((s,i)=>s+i.valor_atual,0);

document.getElementById('stats').innerHTML = [
  ['Patrimônio total', fmt(total), `${INV.length} ativos`],
  ['Maior posição', INV[0]?INV[0].nome.slice(0,22):'—', INV[0]?fmt(INV[0].valor_atual):''],
  ['Aportes cadastrados', fmt(INV.reduce((s,i)=>s+(i.aporte_mensal||0),0))+'/mês', 'soma por ativo'],
  ['Tesouro Pré', INV.find(i=>i.tipo==='tesouro_prefixado')?pct(INV.find(i=>i.tipo==='tesouro_prefixado').taxa_anual):'—', 'taxa contratada'],
].map(([l,v,d])=>`<div class="stat"><span>${l}</span><b>${v}</b><small>${d}</small></div>`).join('');

// Alocação
const cores = INV.map(i=>i.cor||'#3b82f6');
document.getElementById('allocBar').innerHTML = INV.map((i,j)=>
  `<div style="width:${(i.valor_atual/total*100).toFixed(1)}%;background:${cores[j]}" title="${i.nome}"></div>`
).join('');
document.getElementById('allocLeg').innerHTML = INV.map((i,j)=>
  `<span style="margin-right:14px"><span class="dot" style="background:${cores[j]}"></span>${i.ticker||i.nome.slice(0,20)} <b>${(i.valor_atual/total*100).toFixed(1)}%</b></span>`
).join('');

document.getElementById('cntAtivos').textContent = `(${INV.length})`;
document.getElementById('tbInv').innerHTML = INV.map(i=>`<tr>
  <td><span class="dot" style="background:${i.cor}"></span><b>${i.ticker||''}</b> ${i.nome}</td>
  <td><span class="tipo">${i.titular_nome||'Priscila'}</span></td>
  <td><span class="tipo">${i.tipo_label}</span></td>
  <td class="num"><b>${fmt(i.valor_atual)}</b></td>
  <td class="num chip-taxa">${i.taxa_anual?pct(i.taxa_anual):'—'}</td>
  <td class="num">${fmt(i.aporte_mensal||0)}</td>
  <td style="font-size:.74rem;color:var(--mut)">${fmtD(i.data_atualizacao)}</td>
</tr>`).join('');

function projetarMeses(pv, taxaAa, pmt, meses){
  const r = taxaAa/100/12;
  let fv = pv;
  for(let m=0;m<meses;m++) fv = fv*(1+r)+pmt;
  return fv;
}

function calcSerie(aporteGlobal, anos){
  const meses = anos*12;
  const totalAportesCad = INV.reduce((s,i)=>s+(i.aporte_mensal||0),0);
  let aportes;
  if(totalAportesCad>0 && aporteGlobal>0){
    const f = aporteGlobal/totalAportesCad;
    aportes = INV.map(i=>(i.aporte_mensal||0)*f);
  } else if(aporteGlobal>0){
    aportes = INV.map(()=>aporteGlobal/INV.length);
  } else {
    aportes = INV.map(i=>i.aporte_mensal||0);
  }
  const saldos = INV.map(i=>i.valor_atual);
  const pontos = [{ano:0,total:saldos.reduce((a,b)=>a+b,0)}];
  for(let ano=1;ano<=anos;ano++){
    for(let m=0;m<12;m++){
      for(let j=0;j<saldos.length;j++){
        const r=(INV[j].taxa_anual||10)/100/12;
        saldos[j]=saldos[j]*(1+r)+aportes[j];
      }
    }
    pontos.push({ano,total:saldos.reduce((a,b)=>a+b,0)});
  }
  return {pontos, aportes};
}

function atualizar(){
  const aporte = Number(document.getElementById('aporteGlobal').value)||0;
  const anos = Number(document.getElementById('anosProj').value)||20;
  document.getElementById('sliderAporte').value = aporte;
  const {pontos, aportes} = calcSerie(aporte, anos);
  const final = pontos[pontos.length-1].total;
  const investido = total + aporte*anos*12;
  const ganho = final - investido;

  document.getElementById('valorFinal').textContent = fmt(final);
  document.getElementById('resultadoSub').innerHTML =
    `em <b>${anos} anos</b> · aportando <b>${fmt(aporte)}/mês</b><br>`+
    `Total investido: ${fmt(investido)} · Ganho estimado: <span style="color:var(--green)">${fmt(ganho)}</span>`;

  const marcosAnos = [0,5,10,15,20].filter(a=>a<=anos);
  if(!marcosAnos.includes(anos)) marcosAnos.push(anos);
  document.getElementById('marcos').innerHTML = marcosAnos.map(a=>{
    const p = pontos.find(x=>x.ano===a);
    return `<div class="marco"><span>Ano ${a}</span><b>${fmt(p.total)}</b></div>`;
  }).join('');

  const maxV = pontos[pontos.length-1].total;
  document.getElementById('chart').innerHTML = pontos.filter((_,i)=>i%Math.max(1,Math.floor(anos/10))===0||_.ano===anos).map(p=>`
    <div class="bar-row">
      <span>${p.ano}a</span>
      <div class="bar-bg"><div class="bar" style="width:${(p.total/maxV*100).toFixed(1)}%"></div></div>
      <span class="num">${fmt(p.total)}</span>
    </div>`).join('');

  document.getElementById('tbProj').innerHTML = INV.map((inv,j)=>{
    const fv = projetarMeses(inv.valor_atual, inv.taxa_anual||10, aportes[j], anos*12);
    const invTotal = inv.valor_atual + aportes[j]*anos*12;
    return `<tr>
      <td>${inv.nome}</td>
      <td class="num">${fmt(inv.valor_atual)}</td>
      <td class="num">${fmt(aportes[j])}</td>
      <td class="num">${pct(inv.taxa_anual||10)}</td>
      <td class="num"><b style="color:var(--green)">${fmt(fv)}</b></td>
      <td class="num" style="color:var(--amber)">${fmt(fv-invTotal)}</td>
    </tr>`;
  }).join('');
}

document.getElementById('aporteGlobal').oninput = atualizar;
document.getElementById('anosProj').oninput = atualizar;
document.getElementById('sliderAporte').oninput = e => {
  document.getElementById('aporteGlobal').value = e.target.value;
  atualizar();
};

document.getElementById('aporteGlobal').value = CFG.aporte_mensal_global || 500;
atualizar();
</script>
</body>
</html>"""


def main():
    if not DB.exists():
        raise SystemExit("Banco não encontrado. Rode: python3 organizacao.py init")
    inv, totais, cfg = carregar()
    if not inv:
        print("Nenhum investimento. Rode init ou importar_investimentos.py")
    aporte = float(cfg.get("aporte_mensal_global", 500))
    anos = int(cfg.get("anos_projecao", 20))
    serie, _ = serie_anual(inv, aporte, anos)
    html = TEMPLATE
    html = html.replace("__INVESTIMENTOS__", json.dumps(inv, ensure_ascii=False))
    html = html.replace("__CONFIG__", json.dumps(cfg, ensure_ascii=False))
    html = html.replace("__SERIE__", json.dumps(serie, ensure_ascii=False))
    SAIDA.write_text(html, encoding="utf-8")
    pat = totais.get("patrimonio_total", 0)
    print(f"✓ Painel investimentos: {SAIDA}  |  Patrimônio: R$ {pat:,.2f}")


if __name__ == "__main__":
    main()
