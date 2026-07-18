#!/usr/bin/env python3
"""Gera prontuarios.html — índice com links para todos os prontuários (Notion)."""
from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent
PAGINAS = BASE / "notion" / "paginas_pacientes.json"
PRONT = BASE / "notion" / "prontuario_por_paciente.json"
PACIENTES = BASE / "templates" / "pacientes.csv"
OUT = BASE / "prontuarios.html"
NOTION_INDICE = "https://app.notion.com/p/943cbf9d373d43efab0d97db85284e73"


def carregar_pacientes() -> list[dict]:
    rows = []
    with PACIENTES.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter=";"):
            cod = (row.get("codigo") or "").strip()
            if cod.startswith("PAC-0") and int(cod.split("-")[1]) <= 18:
                rows.append(row)
    return sorted(rows, key=lambda r: r["codigo"])


def main():
    paginas = json.loads(PAGINAS.read_text(encoding="utf-8"))
    pront = json.loads(PRONT.read_text(encoding="utf-8")) if PRONT.exists() else {}
    pacientes = carregar_pacientes()
    hoje = date.today().isoformat()

    cards = []
    for p in pacientes:
        cod = p["codigo"]
        info = paginas.get("pacientes", {}).get(cod, {})
        pr = pront.get(cod, {})
        nome = p.get("nome") or info.get("nome") or cod
        url = info.get("url", "#")
        sessoes = pr.get("sessoes_count", 0)
        queixa = (p.get("queixa_principal") or "—")[:60]
        horario = p.get("dia_horario") or "—"
        cards.append(
            f"""    <a class="card" href="{url}" target="_blank" rel="noopener">
      <div class="cod">{cod}</div>
      <h2>{nome}</h2>
      <p class="queixa">{queixa}</p>
      <p class="meta">{horario} · {sessoes} sessões no índice</p>
      <span class="go">Abrir prontuário no Notion →</span>
    </a>"""
        )

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Prontuários · Consultório</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  :root{{--bg:#f4f6fb;--card:#fff;--ink:#17203a;--mut:#6b7280;--accent:#7c3aed;--line:#e5e7eb}}
  body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.5}}
  header{{background:linear-gradient(135deg,#4c1d95,#7c3aed);color:#fff;padding:24px 28px}}
  header h1{{font-size:1.5rem;font-weight:800}}
  header p{{opacity:.9;font-size:.88rem;margin-top:6px}}
  .top-links{{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}}
  .top-links a{{color:#fff;background:rgba(255,255,255,.15);padding:6px 14px;border-radius:8px;text-decoration:none;font-size:.8rem}}
  .top-links a:hover{{background:rgba(255,255,255,.28)}}
  .wrap{{max-width:1100px;margin:0 auto;padding:24px 20px 50px}}
  .stats{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:22px}}
  .stat{{background:var(--card);border-radius:12px;padding:14px 18px;box-shadow:0 1px 6px rgba(0,0,0,.05);min-width:140px}}
  .stat b{{display:block;font-size:1.6rem;color:var(--accent)}}
  .stat span{{font-size:.72rem;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}}
  .search{{width:100%;padding:12px 16px;border:1px solid var(--line);border-radius:12px;font-size:1rem;margin-bottom:20px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}}
  .card{{background:var(--card);border-radius:14px;padding:18px 20px;text-decoration:none;color:inherit;display:block;border:1px solid var(--line);box-shadow:0 1px 6px rgba(0,0,0,.04);transition:.15s}}
  .card:hover{{transform:translateY(-2px);border-color:var(--accent);box-shadow:0 8px 24px rgba(124,58,237,.12)}}
  .cod{{font-size:.72rem;font-weight:800;color:var(--accent);letter-spacing:.06em;margin-bottom:4px}}
  .card h2{{font-size:1.05rem;margin-bottom:6px}}
  .queixa{{font-size:.82rem;color:var(--mut);margin-bottom:4px}}
  .meta{{font-size:.75rem;color:#9ca3af}}
  .go{{display:inline-block;margin-top:10px;font-size:.78rem;font-weight:700;color:var(--accent)}}
  footer{{text-align:center;font-size:.72rem;color:var(--mut);padding:20px}}
</style>
</head>
<body>
<header>
  <h1>📋 Prontuários dos Pacientes</h1>
  <p>Um link para cada prontuário — dados clínicos + sessões no Notion · atualizado {hoje}</p>
  <div class="top-links">
    <a href="index.html">🏠 Painel</a>
    <a href="index.html#consultorio">🧠 Consultório</a>
    <a href="links.html">🔗 Links</a>
    <a href="{NOTION_INDICE}" target="_blank" rel="noopener">🗂️ Índice Notion</a>
  </div>
</header>
<div class="wrap">
  <div class="stats">
    <div class="stat"><span>Pacientes</span><b>{len(cards)}</b></div>
    <div class="stat"><span>Fonte</span><b style="font-size:1rem">Notion</b></div>
  </div>
  <input class="search" id="q" type="search" placeholder="Buscar por nome ou código (ex: Bia, PAC-002)…" oninput="filtrar()">
  <div class="grid" id="grid">
{chr(10).join(cards)}
  </div>
</div>
<footer>Priscila Palomo · organizacao/prontuarios.html · pasta Imagens\\home\\organizacao\\</footer>
<script>
function filtrar(){{
  const q=document.getElementById('q').value.toLowerCase();
  document.querySelectorAll('#grid .card').forEach(c=>{{
    c.style.display=c.textContent.toLowerCase().includes(q)?'':'none';
  }});
}}
</script>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"✓ {OUT} ({len(cards)} pacientes)")


if __name__ == "__main__":
    main()
