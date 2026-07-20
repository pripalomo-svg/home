#!/usr/bin/env python3
"""Gera contratos_assinados.html a partir de dados/contratos_assinados.json
e dos PDFs em documentos/contratos_assinados/.

Também regenera PDFs a partir de textos de e-mail (.txt/.eml) nessa pasta.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "dados" / "contratos_assinados.json"
PDF_DIR = ROOT / "documentos" / "contratos_assinados"
OUT_HTML = ROOT / "contratos_assinados.html"
BASE = "https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main"


def slug(nome: str) -> str:
    s = re.sub(r"[^\w\s-]", "", nome, flags=re.UNICODE)
    s = re.sub(r"\s+", "_", s.strip())
    return s[:80] or "Paciente"


def parse_email_text(texto: str) -> dict | None:
    """Extrai campos do resumo EmailJS (NOVO CONTRATO DE PACIENTE FINALIZADO)."""
    if "NOVO CONTRATO" not in texto.upper() and "DADOS DO PACIENTE" not in texto.upper():
        return None

    def campo(*labels: str) -> str:
        for lab in labels:
            m = re.search(rf"{re.escape(lab)}\s*:\s*(.+)", texto, re.I)
            if m:
                return m.group(1).strip()
        return ""

    nome = campo("Nome")
    if not nome or nome == "—":
        return None
    return {
        "nome": nome,
        "cpf": campo("CPF"),
        "nascimento": campo("Nascimento"),
        "whatsapp": campo("WhatsApp"),
        "email": campo("E-mail", "Email"),
        "endereco": campo("Endereco", "Endereço"),
        "emergencia": campo("Contato de emergencia", "Contato de emergência"),
        "data_hora": campo("Data e hora"),
        "honorarios": campo("Honorarios", "Honorários", "Valor"),
        "resumo": texto.strip(),
    }


def gerar_pdf(dados: dict, destino: Path) -> Path:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(0, 8, "CONTRATO ASSINADO — Arquivo a partir do e-mail")
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(2)
    linhas = [
        f"Paciente: {dados.get('nome', '—')}",
        f"CPF: {dados.get('cpf', '—')}",
        f"Nascimento: {dados.get('nascimento', '—')}",
        f"WhatsApp: {dados.get('whatsapp', '—')}",
        f"E-mail: {dados.get('email', '—')}",
        f"Endereco: {dados.get('endereco', '—')}",
        f"Emergencia: {dados.get('emergencia', '—')}",
        f"Data/hora (e-mail): {dados.get('data_hora', '—')}",
        f"Honorarios: {dados.get('honorarios', '—')}",
        "",
        "Observacao: PDF regenerado do texto enviado por e-mail (EmailJS).",
        "A assinatura manuscrita digital nao vem no e-mail — confira o PDF original do paciente se disponivel.",
        "",
        "--- Resumo completo ---",
        "",
    ]
    for ln in linhas:
        pdf.multi_cell(0, 5, ln.encode("latin-1", "replace").decode("latin-1"))
    resumo = dados.get("resumo") or ""
    for ln in resumo.splitlines():
        pdf.multi_cell(0, 5, ln.encode("latin-1", "replace").decode("latin-1"))
    destino.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(destino))
    return destino


def carregar() -> dict:
    if JSON_PATH.exists():
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    return {"contratos": [], "destino_email": "pripalomo@gmail.com"}


def processar_textos(data: dict) -> int:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    novos = 0
    existentes = {(c.get("nome") or "").lower() + "|" + (c.get("data_hora") or "") for c in data.get("contratos", [])}
    for path in sorted(PDF_DIR.glob("*")):
        if path.suffix.lower() not in {".txt", ".eml", ".md"}:
            continue
        texto = path.read_text(encoding="utf-8", errors="replace")
        dados = parse_email_text(texto)
        if not dados:
            continue
        key = (dados["nome"].lower() + "|" + (dados.get("data_hora") or ""))
        pdf_name = f"Contrato_Assinado_{slug(dados['nome'])}.pdf"
        pdf_path = PDF_DIR / pdf_name
        if not pdf_path.exists():
            gerar_pdf(dados, pdf_path)
        if key not in existentes:
            data.setdefault("contratos", []).append(
                {
                    "id": f"email-{path.stem}",
                    "nome": dados["nome"],
                    "cpf": dados.get("cpf"),
                    "email": dados.get("email"),
                    "whatsapp": dados.get("whatsapp"),
                    "honorarios": dados.get("honorarios"),
                    "data_hora": dados.get("data_hora"),
                    "arquivo_pdf": f"documentos/contratos_assinados/{pdf_name}",
                    "fonte": "email_texto",
                    "origem_arquivo": path.name,
                }
            )
            existentes.add(key)
            novos += 1
    # index existing PDFs not yet listed
    listed = {c.get("arquivo_pdf") for c in data.get("contratos", [])}
    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        rel = f"documentos/contratos_assinados/{pdf.name}"
        if rel in listed:
            continue
        nome = pdf.stem.replace("Contrato_Assinado_", "").replace("_", " ")
        data.setdefault("contratos", []).append(
            {
                "id": f"pdf-{pdf.stem}",
                "nome": nome,
                "arquivo_pdf": rel,
                "fonte": "pdf",
                "data_hora": None,
            }
        )
        novos += 1
    return novos


def gerar_html(data: dict) -> str:
    contratos = sorted(
        data.get("contratos", []),
        key=lambda c: c.get("data_hora") or c.get("nome") or "",
        reverse=True,
    )
    rows = []
    for c in contratos:
        pdf = c.get("arquivo_pdf") or ""
        link = f'<a href="{pdf}">Baixar PDF</a>' if pdf else "—"
        rows.append(
            "<tr>"
            f"<td>{_esc(c.get('nome'))}</td>"
            f"<td>{_esc(c.get('data_hora') or '—')}</td>"
            f"<td>{_esc(c.get('honorarios') or '—')}</td>"
            f"<td>{_esc(c.get('whatsapp') or '—')}</td>"
            f"<td>{_esc(c.get('email') or '—')}</td>"
            f"<td>{_esc(c.get('fonte') or '—')}</td>"
            f"<td>{link}</td>"
            "</tr>"
        )
    tabela = "\n".join(rows) or (
        '<tr><td colspan="7" class="vazio">Nenhum contrato arquivado ainda. '
        "Cole e-mails abaixo ou coloque PDFs/.txt em documentos/contratos_assinados/</td></tr>"
    )
    atualizado = data.get("atualizado_em") or datetime.now().isoformat(timespec="seconds")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Contratos assinados · Consultório</title>
<style>
:root{{--az:#1a3a5c;--az2:#2056a0;--bg:#f4f6fb;--tx:#17203a;--ci:#6b7280;--ok:#2e7d32;--er:#b91c1c;}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--tx);line-height:1.55;padding:24px 18px 60px;max-width:980px;margin:0 auto}}
h1{{font-size:1.55rem;margin-bottom:6px}} h1 em{{color:#e94560;font-style:normal}}
.sub{{color:var(--ci);font-size:.9rem;margin-bottom:18px}}
.aviso{{background:#fff8e8;border:1px solid #e8d29a;border-left:4px solid #c9a227;border-radius:10px;padding:12px 14px;font-size:.88rem;margin-bottom:18px}}
.card{{background:#fff;border-radius:14px;padding:18px;box-shadow:0 1px 8px rgba(0,0,0,.06);margin-bottom:16px}}
.card h2{{font-size:1.05rem;margin-bottom:10px;color:var(--az)}}
table{{width:100%;border-collapse:collapse;font-size:.86rem}}
th,td{{text-align:left;padding:10px 8px;border-bottom:1px solid #e8ecf3;vertical-align:top}}
th{{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--ci)}}
.vazio{{color:var(--ci);text-align:center;padding:28px 8px}}
textarea{{width:100%;min-height:160px;border:1.5px solid #dde3ec;border-radius:10px;padding:12px;font:inherit;resize:vertical}}
.btn{{display:inline-block;background:var(--az);color:#fff;border:none;border-radius:9px;padding:10px 16px;font-weight:700;cursor:pointer;margin-top:10px}}
.btn:hover{{filter:brightness(1.06)}}
.meta{{font-size:.78rem;color:var(--ci);margin-top:8px}}
.ok{{color:var(--ok);font-weight:600}}.er{{color:var(--er);font-weight:600}}
a{{color:var(--az2)}}
.nav a{{margin-right:12px;font-size:.85rem}}
</style>
</head>
<body>
<p class="nav"><a href="links.html">← Links</a> <a href="contrato_paciente.html">Novo contrato</a> <a href="cadastro_pacientes.html">Pacientes</a></p>
<h1>Contratos <em>assinados</em></h1>
<p class="sub">Arquivo dos contratos enviados ao e-mail · { _esc(data.get('destino_email') or 'pripalomo@gmail.com') } · atualizado { _esc(atualizado) }</p>

<div class="aviso">
  <strong>Histórico do Gmail:</strong> ainda sem acesso à caixa <code>pripalomo@gmail.com</code> neste ambiente
  (login Google bloqueado). O EmailJS envia só o <em>texto</em> do contrato — não anexa o PDF.
  Para recuperar os antigos: no Gmail busque <code>Contrato assinado</code> ou
  <code>NOVO CONTRATO DE PACIENTE FINALIZADO</code>, copie o corpo do e-mail e cole abaixo
  (ou salve .txt/.eml em <code>documentos/contratos_assinados/</code> e rode
  <code>python3 gerar_contratos_assinados.py</code>).
</div>

<div class="card">
  <h2>Arquivo ({len(contratos)})</h2>
  <table>
    <thead><tr><th>Paciente</th><th>Data</th><th>Honorários</th><th>WhatsApp</th><th>E-mail</th><th>Fonte</th><th>PDF</th></tr></thead>
    <tbody>
{tabela}
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Colar e-mail do EmailJS → gerar PDF</h2>
  <p class="meta">Cole o corpo completo do e-mail (começa com NOVO CONTRATO DE PACIENTE FINALIZADO).</p>
  <textarea id="emailTxt" placeholder="NOVO CONTRATO DE PACIENTE FINALIZADO&#10;&#10;Nome: ..."></textarea>
  <button class="btn" type="button" onclick="gerarDoEmail()">Gerar e baixar PDF</button>
  <p id="status" class="meta"></p>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script>
function campo(texto, lab){{
  const re = new RegExp(lab + '\\\\s*:\\\\s*(.+)', 'i');
  const m = texto.match(re);
  return m ? m[1].trim() : '';
}}
function gerarDoEmail(){{
  const t = document.getElementById('emailTxt').value || '';
  const st = document.getElementById('status');
  if(!/NOVO CONTRATO|DADOS DO PACIENTE/i.test(t)){{
    st.innerHTML = '<span class="er">Texto não parece um e-mail de contrato.</span>';
    return;
  }}
  const nome = campo(t, 'Nome');
  if(!nome){{ st.innerHTML = '<span class="er">Nome do paciente não encontrado.</span>'; return; }}
  const {{ jsPDF }} = window.jspdf;
  const doc = new jsPDF({{unit:'mm', format:'a4'}});
  let y = 18; const M=16; const W=210-M*2;
  const linha = (txt, h=6, size=11, bold=false) => {{
    doc.setFont('helvetica', bold?'bold':'normal'); doc.setFontSize(size);
    const ls = doc.splitTextToSize(String(txt), W);
    if(y + ls.length*h > 280){{ doc.addPage(); y=18; }}
    doc.text(ls, M, y); y += ls.length*h;
  }};
  doc.setTextColor(26,58,92);
  linha('CONTRATO ASSINADO — Arquivo do e-mail', 7, 14, true);
  linha('Paciente: ' + nome, 6, 11, true);
  ['CPF','Nascimento','WhatsApp','E-mail','Endereco','Endereço','Contato de emergencia','Contato de emergência','Data e hora','Honorarios','Honorários'].forEach(l=>{{
    const v = campo(t, l); if(v) linha(l + ': ' + v);
  }});
  y += 4; linha('--- Resumo completo ---', 6, 10, true);
  t.split(/\\n/).forEach(ln => linha(ln, 5, 9));
  const fname = 'Contrato_Assinado_' + nome.replace(/\\s+/g,'_') + '.pdf';
  doc.save(fname);
  st.innerHTML = '<span class="ok">PDF baixado: ' + fname + '. Salve em documentos/contratos_assinados/ e rode o gerador.</span>';
}}
</script>
</body>
</html>
"""


def _esc(s) -> str:
    return (
        str(s if s is not None else "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> None:
    data = carregar()
    n = processar_textos(data)
    data["atualizado_em"] = datetime.now().isoformat(timespec="seconds")
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_HTML.write_text(gerar_html(data), encoding="utf-8")
    print(f"OK · {len(data.get('contratos', []))} contratos · +{n} novos · {OUT_HTML.name}")
    print(f"Ver: {BASE}/organizacao/contratos_assinados.html")


if __name__ == "__main__":
    main()
