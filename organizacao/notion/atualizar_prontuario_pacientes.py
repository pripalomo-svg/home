#!/usr/bin/env python3
"""Monta prontuário por paciente a partir de pacientes.csv + índice de sessões (PDF/Notion)."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
NOTION = BASE / "notion"
PACIENTES_CSV = BASE / "templates" / "pacientes.csv"
PRONTUARIOS_CSV = BASE / "templates" / "prontuarios.csv"
PAGINAS = NOTION / "paginas_pacientes.json"
OUT = NOTION / "prontuario_por_paciente.json"

# Índice de sessões extraído do PDF exportado do Notion (jul/2026)
SESSOES_PDF: dict[str, list[str]] = {
    "PAC-001": [
        "Maria José 111225",
        "mj16.12.25 (16/12/2025)",
        "maria jose (26/02/2026)",
        "Maria Jose",
    ],
    "PAC-002": [
        "Bia@19/01/2026 21:04 (19/01/2026)",
        "Beatriz Jubilut - Atendimento Online com Dra. Priscila Palomo",
        "bia (25/02/2026)",
        "beatriz (02/02/2026)",
        "Beatriz Jubilut — Sessão 19/01/2026 (19/01/2026)",
        "Beatriz Jubilut - Atendimento Online com Dra. Priscila Palomo",
        "Beatriz Jubilut - Atendimento Online com Dra. Priscila Palomo",
    ],
    "PAC-003": [
        "Luigi Caloi — Sessão realizada (20/01/2026)",
        "luigi",
        "Luigi Caloi — Sessão novembro 2025",
        "Luigi Caloi — Sessão 20/01/2026 (20/01/2026)",
        "luigi 21/04/26 (21/04/2026)",
        "luidy (12/05/2026)",
    ],
    "PAC-004": [
        "Fernando de Castro — Sessão realizada (12/12/2025)",
        "fernado 23/01/26 (23/01/2026)",
        "fernando (22/05/2026)",
        "fernando (29/05/2026)",
    ],
    "PAC-005": [
        "Felipe (Fê) — Sessão realizada (16/12/2025)",
        "Fê (16/12/2025 14:02)",
        "felipe zandona (13/02/2026)",
    ],
    "PAC-006": [
        "Monica — Sessão realizada (21/01/2026)",
        "Monica Mattos — Sessão realizada (11/12/2025)",
        "Monica Mattos — Sessão realizada (14/01/2026)",
        "Monica Mattos — Sessão 04/02/2026 (04/02/2026)",
        "Monica Mattos (04/02/2026)",
        "monica (12/02/2026)",
    ],
    "PAC-007": [
        "Luís Octavio Almeida — presencial semanal (16/04/2026 15:30)",
        "Luís Octavio Almeida — presencial semanal (14/05/2026 15:30)",
    ],
    "PAC-008": [
        "GAbriel (12/12/2025)",
        "gabriel (20/02/2026)",
        "gabriel",
        "gabril (27/05/2026)",
    ],
    "PAC-009": [
        "Bruna — Sessão realizada (20/01/2026)",
        "Bruna — Sessão realizada (13/01/2026)",
        "Bruna — Sessão realizada (20/01/2026)",
        "Bruna 03.02.26 (03/02/2026)",
    ],
    "PAC-010": [
        "Luisa Cabalin — on-line semanal (13/01/2026)",
        "Luisa Cabalin — Sessão 08/12/2025",
        "Luisa Cabalin 081225 (08/12/2025)",
        "Luisa Cabalin Ferreira - Atendimento on-line semanal recorrente",
        "Luisa Cabalin Ferreira - Atendimento on-line semanal recorrente",
        "luisa (28/04/2026)",
    ],
    "PAC-011": [
        "Clara",
        "Clara — Sessão 23/01/2026 (23/01/2026)",
        "clara 25.02.26 (25/02/2026)",
    ],
    "PAC-012": [
        "Lívia — Sessão realizada (10/12/2025)",
        "Lívia — Sessão realizada (19/01/2026)",
        "Lívia — Sessão realizada",
        "Livia on-line (14/01/2026)",
        "livia palidiar 101225 (10/12/2025)",
        "livia (20/02/2026)",
        "livia (26/02/2026)",
        "liv (23/04/2026)",
        "Livia Padiar — Sessão 19/01/2026 (19/01/2026)",
    ],
    "PAC-013": [
        "Sthephanie — Sessão realizada (16/12/2025)",
        "Sthephanie — Sessão realizada (13/01/2026)",
        "Sthephanie — Sessão realizada (20/01/2026)",
        "Stephanie (03/02/2026)",
        "Sthephanie (13/01/2026)",
        "stéphanie 16 de dezembro25 (16/12/2025)",
        "stephanie (12/05/2026)",
        "Sthephanie",
    ],
    "PAC-014": [
        "Claudia — Sessão realizada (16/12/2025)",
        "claudia (16/12/2025)",
        "claudinha (15/01/2026)",
        "claudia (09/02/2026)",
        "Cláudia 22/04/26 (22/04/2026)",
    ],
    "PAC-015": [
        "Márcia — Sessão realizada (14/01/2026)",
        "Márcia (14/01/2026)",
    ],
    "PAC-016": [],
    "PAC-017": [
        "Larissa online (14/05/2026)",
        "Larissa online (12/05/2026)",
        "Larissa (28/05/2026)",
        "larisss (26/05/2026)",
        "larissa (29/04/2026)",
        "Larissa (21/04/2026)",
        "Larissa (23/04/2026)",
        "Lariassa Plausino (21/05/2026)",
    ],
    "PAC-018": [
        "Rochele (28/05/2026)",
        "Rochelle (22/04/2026)",
        "Rochele (29/04/2026)",
    ],
}


def carregar_pacientes() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with PACIENTES_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter=";"):
            cod = (row.get("codigo") or "").strip()
            if cod.startswith("PAC-"):
                rows[cod] = row
    return rows


def markdown_prontuario(cod: str, row: dict, sessoes: list[str]) -> str:
    nome = row.get("nome") or ""
    queixa = row.get("queixa_principal") or "—"
    freq = row.get("frequencia") or "—"
    horario = row.get("dia_horario") or "—"
    inicio = row.get("data_inicio") or "—"
    convenio = row.get("convenio") or "—"
    obs = row.get("observacoes") or "—"
    valor = row.get("valor_sessao") or "—"

    lines = [
        "## Prontuário clínico",
        "<callout icon=\"📋\" color=\"purple_bg\">",
        f"\tDados do paciente e índice de atendimentos (export Notion / PDF jul/2026).",
        "</callout>",
        "<table header-row=\"true\" fit-page-width=\"true\">",
        "\t<tr>",
        "\t\t<td>**Campo**</td>",
        "\t\t<td>**Informação**</td>",
        "\t</tr>",
        f"\t<tr><td>Código</td><td>{cod}</td></tr>",
        f"\t<tr><td>Nome</td><td>{nome}</td></tr>",
        f"\t<tr><td>Queixa principal</td><td>{queixa}</td></tr>",
        f"\t<tr><td>Frequência</td><td>{freq}</td></tr>",
        f"\t<tr><td>Horário</td><td>{horario}</td></tr>",
        f"\t<tr><td>Início do acompanhamento</td><td>{inicio}</td></tr>",
        f"\t<tr><td>Convênio</td><td>{convenio}</td></tr>",
        f"\t<tr><td>Valor sessão</td><td>R$ {valor}</td></tr>",
        f"\t<tr><td>Observações</td><td>{obs}</td></tr>",
        "</table>",
        "",
        f"### Índice de atendimentos ({len(sessoes)})",
        "",
    ]
    if sessoes:
        for i, s in enumerate(sessoes, 1):
            lines.append(f"{i}. {s}")
    else:
        lines.append("_Nenhuma sessão listada no índice ainda._")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def texto_prontuario_db(cod: str, row: dict, sessoes: list[str]) -> str:
    parts = [
        f"PRONTUÁRIO — {cod} — {row.get('nome', '')}",
        f"Queixa: {row.get('queixa_principal') or '—'}",
        f"Horário: {row.get('dia_horario') or '—'} | {row.get('frequencia') or '—'}",
        f"Início: {row.get('data_inicio') or '—'} | Convênio: {row.get('convenio') or 'particular'}",
        "",
        "Índice de atendimentos (Notion):",
    ]
    for s in sessoes:
        parts.append(f"• {s}")
    return "\n".join(parts)


def main():
    pacientes = carregar_pacientes()
    paginas = json.loads(PAGINAS.read_text(encoding="utf-8"))
    resultado = {}

    novos_csv_rows: list[dict] = []
    for cod, row in sorted(pacientes.items()):
        if not cod.startswith("PAC-0") or int(cod.split("-")[1]) > 18:
            continue
        sessoes = SESSOES_PDF.get(cod, [])
        md = markdown_prontuario(cod, row, sessoes)
        texto = texto_prontuario_db(cod, row, sessoes)
        info_pag = paginas.get("pacientes", {}).get(cod, {})
        resultado[cod] = {
            "nome": row.get("nome"),
            "notion_url": info_pag.get("url"),
            "markdown": md,
            "conteudo_db": texto,
            "sessoes_count": len(sessoes),
        }
        data_reg = row.get("data_inicio") or "2026-07-16"
        novos_csv_rows.append(
            {
                "paciente_codigo": cod,
                "data_registro": data_reg,
                "tipo": "evolucao",
                "titulo": f"Prontuário consolidado — {row.get('nome', cod)}",
                "conteudo": texto.replace("\n", " ").strip()[:2000],
                "arquivo": "notion/indice-pdf-2026-07",
            }
        )

    OUT.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

    # Mesclar com prontuarios.csv existente (substituir linha consolidada por código)
    existentes: list[dict] = []
    if PRONTUARIOS_CSV.exists():
        with PRONTUARIOS_CSV.open(encoding="utf-8") as f:
            existentes = list(csv.DictReader(f, delimiter=";"))
    codigos_novos = {r["paciente_codigo"] for r in novos_csv_rows}
    filtrados = [r for r in existentes if r.get("paciente_codigo") not in codigos_novos or not (r.get("titulo") or "").startswith("Prontuário consolidado")]
    merged = filtrados + novos_csv_rows
    with PRONTUARIOS_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["paciente_codigo", "data_registro", "tipo", "titulo", "conteudo", "arquivo"],
            delimiter=";",
        )
        w.writeheader()
        w.writerows(merged)

    print(f"✓ {len(resultado)} prontuários → {OUT}")
    print(f"✓ CSV atualizado → {PRONTUARIOS_CSV}")


if __name__ == "__main__":
    main()
