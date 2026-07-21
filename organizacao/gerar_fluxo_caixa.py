#!/usr/bin/env python3
"""Gera fluxo_caixa.html — entradas, saídas e investimentos por mês.

Lê todos os CSVs da pasta extratos/ (separador ';', colunas:
data;descricao;valor;fluxo;categoria — fluxo: entrada|saida|aplicacao|resgate).

Uso:  python3 gerar_fluxo_caixa.py
Para cobrir mais meses, adicione novos extratos em extratos/ e regenere.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
EXTRATOS = BASE / "extratos"
SAIDA = BASE / "fluxo_caixa.html"

MESES_PT = {
    "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
    "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
    "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro",
}


def carregar():
    """Une os extratos. Lançamentos repetidos DENTRO de um mesmo arquivo são
    legítimos (ex.: duas aplicações iguais no mesmo dia). Entre arquivos
    diferentes, a mesma linha só conta uma vez (extratos sobrepostos):
    para cada lançamento usa-se a maior contagem vista em um único arquivo."""
    contagens = defaultdict(int)
    dados = {}
    for arq in sorted(EXTRATOS.glob("*.csv")):
        no_arquivo = defaultdict(int)
        with open(arq, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f, delimiter=";"):
                if not row.get("data") or not row.get("valor"):
                    continue
                chave = (row["data"], row["descricao"], row["valor"])
                no_arquivo[chave] += 1
                dados[chave] = {
                    "data": row["data"],
                    "descricao": row["descricao"],
                    "valor": float(row["valor"]),
                    "fluxo": row["fluxo"],
                    "categoria": row.get("categoria") or "Outros",
                }
        for chave, qtd in no_arquivo.items():
            contagens[chave] = max(contagens[chave], qtd)

    lancamentos = []
    for chave, qtd in contagens.items():
        lancamentos.extend([dict(dados[chave])] * qtd)
    lancamentos.sort(key=lambda x: x["data"])
    return lancamentos


def resumir(lancamentos):
    meses = defaultdict(lambda: {
        "entradas": 0.0, "saidas": 0.0, "aplicacoes": 0.0, "resgates": 0.0,
        "transf_propria": 0.0,
    })
    categorias = defaultdict(lambda: defaultdict(float))
    invest_categorias = defaultdict(float)

    for lc in lancamentos:
        mes = lc["data"][:7]
        m = meses[mes]
        if lc["fluxo"] == "entrada":
            m["entradas"] += lc["valor"]
            if lc["categoria"] == "Transferência própria":
                m["transf_propria"] += lc["valor"]
            categorias["entrada"][lc["categoria"]] += lc["valor"]
        elif lc["fluxo"] == "saida":
            m["saidas"] += -lc["valor"]
            categorias["saida"][lc["categoria"]] += -lc["valor"]
        elif lc["fluxo"] == "aplicacao":
            m["aplicacoes"] += -lc["valor"]
            invest_categorias[lc["categoria"]] += -lc["valor"]
        elif lc["fluxo"] == "resgate":
            m["resgates"] += lc["valor"]

    linhas = []
    for mes in sorted(meses):
        m = meses[mes]
        invest_liq = m["aplicacoes"] - m["resgates"]
        linhas.append({
            "mes": mes,
            "nome": f"{MESES_PT[mes[5:]]}/{mes[:4]}",
            "entradas": round(m["entradas"], 2),
            "transf_propria": round(m["transf_propria"], 2),
            "saidas": round(m["saidas"], 2),
            "aplicacoes": round(m["aplicacoes"], 2),
            "resgates": round(m["resgates"], 2),
            "invest_liquido": round(invest_liq, 2),
            "saldo": round(m["entradas"] - m["saidas"] - invest_liq, 2),
        })
    cats = {
        "entrada": sorted(categorias["entrada"].items(), key=lambda x: -x[1]),
        "saida": sorted(categorias["saida"].items(), key=lambda x: -x[1]),
        "invest": sorted(invest_categorias.items(), key=lambda x: -x[1]),
    }
    return linhas, cats


TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fluxo de Caixa · Itaú</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  :root{--bg:#0b1020;--card:#141b2e;--card2:#1a2340;--ink:#e8ecf4;--mut:#8b95ad;--line:#2a3555;
    --green:#22c55e;--blue:#3b82f6;--violet:#a78bfa;--amber:#f59e0b;--rose:#f43f5e}
  body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--ink);min-height:100vh}
  header{background:linear-gradient(135deg,#0f172a,#1e3a5f 60%,#0f3460);padding:22px 28px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;border-bottom:1px solid var(--line)}
  header h1{font-size:1.35rem;font-weight:800} header h1 em{color:var(--green);font-style:normal}
  header p{color:var(--mut);font-size:.78rem;margin-top:3px}
  .links a{font-size:.76rem;color:var(--ink);text-decoration:none;background:var(--card2);padding:6px 14px;border-radius:8px;border:1px solid var(--line);margin-left:6px}
  .links a:hover{border-color:var(--blue)}
  .wrap{max-width:1200px;margin:0 auto;padding:22px 24px 60px}
  .aviso{background:rgba(245,158,11,.12);border:1px solid rgba(245,158,11,.4);border-radius:12px;padding:12px 16px;font-size:.8rem;margin-bottom:18px;color:#fbd38d}
  .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:22px}
  .stat{background:var(--card);border-radius:14px;padding:16px 18px;border:1px solid var(--line)}
  .stat span{font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}
  .stat b{display:block;font-size:1.35rem;font-weight:800;margin-top:4px}
  .stat small{color:var(--mut);font-size:.7rem}
  .panel{background:var(--card);border-radius:14px;border:1px solid var(--line);overflow:hidden;margin-bottom:18px}
  .panel-h{padding:14px 18px 8px;font-weight:700;font-size:.95rem}
  .panel-sub{padding:0 18px 12px;font-size:.74rem;color:var(--mut)}
  table{width:100%;border-collapse:collapse;font-size:.82rem}
  th{text-align:left;padding:10px 14px;color:var(--mut);font-size:.67rem;text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid var(--line);background:var(--card2)}
  td{padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:middle}
  tr:hover td{background:rgba(59,130,246,.06)}
  tr.total td{background:var(--card2);font-weight:800;border-top:2px solid var(--line)}
  .num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
  .pos{color:var(--green);font-weight:700}.neg{color:var(--rose);font-weight:700}
  .inv{color:var(--violet);font-weight:700}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
  @media(max-width:960px){.grid2{grid-template-columns:1fr}}
  .bar-row{display:grid;grid-template-columns:200px 1fr 100px;align-items:center;gap:8px;margin-bottom:7px;font-size:.76rem;padding:0 18px}
  .bar-bg{background:var(--card2);border-radius:5px;height:16px;overflow:hidden}
  .bar{height:100%;border-radius:5px}
  .b-green{background:linear-gradient(90deg,#16a34a,#22c55e)}
  .b-rose{background:linear-gradient(90deg,#e11d48,#f43f5e)}
  .b-violet{background:linear-gradient(90deg,#7c3aed,#a78bfa)}
  .pad-b{padding-bottom:18px}
  .filters{display:flex;gap:8px;flex-wrap:wrap;padding:0 18px 12px;align-items:center}
  .filters input,.filters select{padding:8px 12px;border:1px solid var(--line);border-radius:9px;background:var(--bg);color:var(--ink);font-size:.82rem;outline:none}
  .filters input{flex:1;min-width:180px}
  .tag{display:inline-block;padding:2px 9px;border-radius:20px;font-size:.66rem;font-weight:700;background:var(--card2);border:1px solid var(--line)}
  footer{text-align:center;padding:24px;font-size:.7rem;color:var(--mut)}
</style>
</head>
<body>
<header>
  <div>
    <h1>Fluxo de <em>Caixa</em></h1>
    <p>Conta Itaú · Priscila Palomo · período coberto: __PERIODO__</p>
  </div>
  <div class="links">
    <a href="index.html">← Organização</a>
    <a href="investimentos.html">📈 Investimentos</a>
  </div>
</header>
<div class="wrap">
  __AVISO__
  <div class="stats" id="stats"></div>
  <div class="panel">
    <div class="panel-h">📅 Resumo mensal</div>
    <div class="panel-sub">Entradas e saídas = movimentos da conta. Investimentos = aplicações (Cofrinhos/CDB, VGBL, cripto) menos resgates. Saldo = entradas − saídas − investimento líquido.</div>
    <div style="overflow-x:auto"><table>
      <thead><tr>
        <th>Mês</th><th class="num">Entradas</th><th class="num">↳ transf. própria</th>
        <th class="num">Saídas</th><th class="num">Aplicações</th><th class="num">Resgates</th>
        <th class="num">Invest. líquido</th><th class="num">Saldo do mês</th>
      </tr></thead>
      <tbody id="tbMeses"></tbody>
    </table></div>
  </div>
  <div class="grid2">
    <div class="panel">
      <div class="panel-h">🔻 Saídas por categoria</div>
      <div class="pad-b" id="catSaidas"></div>
    </div>
    <div>
      <div class="panel">
        <div class="panel-h">🔺 Entradas por categoria</div>
        <div class="pad-b" id="catEntradas"></div>
      </div>
      <div class="panel">
        <div class="panel-h">📈 Investimentos por tipo (aplicado no período)</div>
        <div class="pad-b" id="catInvest"></div>
      </div>
    </div>
  </div>
  <div class="panel">
    <div class="panel-h">📋 Todos os lançamentos <span style="font-size:.72rem;color:var(--mut);font-weight:400" id="cntLanc"></span></div>
    <div class="filters">
      <input type="search" id="busca" placeholder="Buscar lançamento…">
      <select id="fMes"><option value="">Todos os meses</option></select>
      <select id="fFluxo">
        <option value="">Tudo</option><option value="entrada">Entradas</option>
        <option value="saida">Saídas</option><option value="aplicacao">Aplicações</option>
        <option value="resgate">Resgates</option>
      </select>
    </div>
    <div style="overflow-x:auto;max-height:480px;overflow-y:auto"><table>
      <thead><tr><th>Data</th><th>Descrição</th><th>Categoria</th><th>Fluxo</th><th class="num">Valor</th></tr></thead>
      <tbody id="tbLanc"></tbody>
    </table></div>
  </div>
</div>
<footer>Gerado por gerar_fluxo_caixa.py · Fonte: extratos/*.csv · Adicione novos extratos e regenere</footer>
<script>
const MESES = __MESES__;
const CATS = __CATS__;
const LANC = __LANC__;

const fmt = n => 'R$ ' + Number(n).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
const fmtD = d => new Date(d+'T12:00:00').toLocaleDateString('pt-BR');

const tot = MESES.reduce((a,m)=>({
  e:a.e+m.entradas, s:a.s+m.saidas, ap:a.ap+m.aplicacoes, rg:a.rg+m.resgates, sl:a.sl+m.saldo
}),{e:0,s:0,ap:0,rg:0,sl:0});

document.getElementById('stats').innerHTML = [
  ['Entradas no período', fmt(tot.e), 'inclui transf. própria', 'pos'],
  ['Saídas no período', fmt(tot.s), 'despesas e pagamentos', 'neg'],
  ['Investido (líquido)', fmt(tot.ap-tot.rg), `aplicado ${fmt(tot.ap)} · resgatado ${fmt(tot.rg)}`, 'inv'],
  ['Saldo do período', fmt(tot.sl), tot.sl>=0?'sobrou na conta':'faltou na conta', tot.sl>=0?'pos':'neg'],
].map(([l,v,d,c])=>`<div class="stat"><span>${l}</span><b class="${c}">${v}</b><small>${d}</small></div>`).join('');

document.getElementById('tbMeses').innerHTML = MESES.map(m=>`<tr>
  <td><b>${m.nome}</b></td>
  <td class="num pos">${fmt(m.entradas)}</td>
  <td class="num" style="color:var(--mut)">${fmt(m.transf_propria)}</td>
  <td class="num neg">${fmt(m.saidas)}</td>
  <td class="num inv">${fmt(m.aplicacoes)}</td>
  <td class="num" style="color:var(--amber)">${fmt(m.resgates)}</td>
  <td class="num inv">${fmt(m.invest_liquido)}</td>
  <td class="num ${m.saldo>=0?'pos':'neg'}">${fmt(m.saldo)}</td>
</tr>`).join('') + `<tr class="total">
  <td>TOTAL</td>
  <td class="num pos">${fmt(tot.e)}</td><td></td>
  <td class="num neg">${fmt(tot.s)}</td>
  <td class="num inv">${fmt(tot.ap)}</td>
  <td class="num" style="color:var(--amber)">${fmt(tot.rg)}</td>
  <td class="num inv">${fmt(tot.ap-tot.rg)}</td>
  <td class="num ${tot.sl>=0?'pos':'neg'}">${fmt(tot.sl)}</td>
</tr>`;

function barras(el, dados, classe){
  const max = Math.max(...dados.map(d=>d[1]), 1);
  document.getElementById(el).innerHTML = dados.map(([nome,v])=>`
    <div class="bar-row">
      <span>${nome}</span>
      <div class="bar-bg"><div class="bar ${classe}" style="width:${(v/max*100).toFixed(1)}%"></div></div>
      <span class="num">${fmt(v)}</span>
    </div>`).join('');
}
barras('catSaidas', CATS.saida, 'b-rose');
barras('catEntradas', CATS.entrada, 'b-green');
barras('catInvest', CATS.invest, 'b-violet');

const mesesUnicos = [...new Set(LANC.map(l=>l.data.slice(0,7)))].sort().reverse();
document.getElementById('fMes').innerHTML += mesesUnicos.map(m=>`<option value="${m}">${m}</option>`).join('');

function renderLanc(){
  const q = document.getElementById('busca').value.toLowerCase();
  const fm = document.getElementById('fMes').value;
  const ff = document.getElementById('fFluxo').value;
  const lista = LANC.filter(l=>
    (!fm||l.data.startsWith(fm)) && (!ff||l.fluxo===ff) &&
    (!q||l.descricao.toLowerCase().includes(q)||l.categoria.toLowerCase().includes(q))
  ).slice().reverse();
  document.getElementById('cntLanc').textContent = `(${lista.length})`;
  document.getElementById('tbLanc').innerHTML = lista.map(l=>`<tr>
    <td class="num" style="text-align:left">${fmtD(l.data)}</td>
    <td>${l.descricao}</td>
    <td><span class="tag">${l.categoria}</span></td>
    <td><span class="tag">${l.fluxo}</span></td>
    <td class="num ${l.valor>=0?'pos':'neg'}">${fmt(l.valor)}</td>
  </tr>`).join('');
}
document.getElementById('busca').oninput = renderLanc;
document.getElementById('fMes').onchange = renderLanc;
document.getElementById('fFluxo').onchange = renderLanc;
renderLanc();
</script>
</body>
</html>"""


def main():
    lanc = carregar()
    if not lanc:
        raise SystemExit("Nenhum lançamento em extratos/*.csv")
    linhas, cats = resumir(lanc)
    periodo = f"{lanc[0]['data']} a {lanc[-1]['data']}"

    n_meses = len(linhas)
    aviso = ""
    if n_meses < 6:
        aviso = (
            '<div class="aviso">⚠️ O extrato enviado cobre <b>' + periodo + "</b> "
            f"({n_meses} meses, sendo o primeiro e o último parciais). Para completar os "
            "últimos 6 meses, envie os extratos anteriores (jan–abr/2026) e coloque o CSV "
            "em <code>extratos/</code> — o painel soma tudo automaticamente.</div>"
        )

    html = TEMPLATE
    html = html.replace("__PERIODO__", periodo)
    html = html.replace("__AVISO__", aviso)
    html = html.replace("__MESES__", json.dumps(linhas, ensure_ascii=False))
    html = html.replace("__CATS__", json.dumps(cats, ensure_ascii=False))
    html = html.replace("__LANC__", json.dumps(lanc, ensure_ascii=False))
    SAIDA.write_text(html, encoding="utf-8")

    print(f"✓ Painel fluxo de caixa: {SAIDA}")
    for li in linhas:
        print(
            f"  {li['nome']}: entradas R$ {li['entradas']:>10,.2f} | "
            f"saídas R$ {li['saidas']:>10,.2f} | invest. líq. R$ {li['invest_liquido']:>10,.2f} | "
            f"saldo R$ {li['saldo']:>10,.2f}"
        )


if __name__ == "__main__":
    main()
