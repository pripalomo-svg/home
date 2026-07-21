#!/usr/bin/env python3
"""Preenche dia_horario em templates/pacientes.csv a partir de atendimentos e agenda.

Uso: python3 preencher_pacientes_horarios.py
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
PACIENTES = BASE / "templates" / "pacientes.csv"
ATENDIMENTOS = BASE / "templates" / "atendimentos.csv"
AGENDA = BASE / "templates" / "agenda.csv"

DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def ler_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        headers = [h for h in (reader.fieldnames or []) if h]
        rows = []
        for row in reader:
            rows.append({k: (v or "") for k, v in row.items() if k})
        return headers, rows


def escrever_csv(path: Path, headers: list[str], rows: list[dict]):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def slot_mais_comum(codigo: str) -> tuple[str, str, str] | None:
    """Retorna (dia, hora, modalidade) mais frequente nos atendimentos."""
    if not ATENDIMENTOS.exists():
        return None
    _, ats = ler_csv(ATENDIMENTOS)
    slots = []
    for r in ats:
        if r.get("paciente_codigo") != codigo or not r.get("data"):
            continue
        d = datetime.strptime(r["data"], "%Y-%m-%d")
        dia = DIAS[d.weekday()]
        hora = (r.get("hora_inicio") or "")[:5]
        mod = r.get("modalidade") or "online"
        if hora:
            slots.append((dia, hora, mod))
    if not slots:
        return None
    (dia, hora, mod), _ = Counter(slots).most_common(1)[0]
    return dia, hora, mod


def slot_agenda(codigo: str) -> tuple[str, str, str] | None:
    if not AGENDA.exists():
        return None
    _, evs = ler_csv(AGENDA)
    for r in evs:
        if r.get("paciente_codigo") != codigo or not r.get("data_inicio"):
            continue
        d = datetime.strptime(r["data_inicio"], "%Y-%m-%d")
        dia = DIAS[d.weekday()]
        hora = (r.get("hora_inicio") or "")[:5]
        local = (r.get("local") or "").lower()
        mod = "presencial" if "consult" in local else "online"
        if hora:
            return dia, hora, mod
    return None


def formatar_horario(codigo: str, frequencia: str) -> str:
    slot = slot_mais_comum(codigo) or slot_agenda(codigo)
    if not slot:
        return "a confirmar"
    dia, hora, mod = slot
    h = hora
    if h.endswith(":00"):
        h = h[:-3] + "h"
    else:
        h = h.replace(":", "h")
    texto = f"{dia} {h} {mod}"
    if frequencia == "quinzenal":
        texto += " (quinzenal)"
    return texto


def main():
    headers, rows = ler_csv(PACIENTES)
    n = 0
    for row in rows:
        codigo = row.get("codigo", "")
        if not codigo or codigo in ("PAC-019", "PAC-020"):
            continue
        if not row.get("nome", "").strip():
            continue
        freq = row.get("frequencia") or "semanal"
        novo = formatar_horario(codigo, freq)
        if row.get("dia_horario") != novo:
            row["dia_horario"] = novo
            n += 1
            print(f"  {codigo} {row.get('nome')}: {novo}")
    escrever_csv(PACIENTES, headers, rows)
    print(f"\n✓ {n} horário(s) atualizado(s) em {PACIENTES.name}")
    print("  Telefones: não encontrados no Notion — preencha manualmente ou via cadastro_pacientes.html")


if __name__ == "__main__":
    main()
