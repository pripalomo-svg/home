#!/usr/bin/env python3
"""Traz de volta ao banco as alterações feitas no controle.html.

Uso:
  python3 importar_controle.py reembolsos-controle-2026-07-14.json
  python3 gerar_dashboard.py && python3 gerar_controle.py   # regerar os painéis

Regras:
  - registros com id existente são ATUALIZADOS;
  - registros com id novo são INSERIDOS;
  - registros que sumiram do JSON são REMOVIDOS (com confirmação);
  - os vínculos com documentos são preservados para ids existentes.
"""

import json
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "reembolsos.db"


def get_ou_cria(conn, tabela, nome):
    if not nome:
        return None
    row = conn.execute(f"SELECT id FROM {tabela} WHERE nome = ?", (nome,)).fetchone()
    if row:
        return row[0]
    return conn.execute(f"INSERT INTO {tabela} (nome) VALUES (?)", (nome,)).lastrowid


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    arquivo = Path(sys.argv[1])
    registros = json.loads(arquivo.read_text(encoding="utf-8"))
    if not isinstance(registros, list):
        sys.exit("JSON inválido: esperado uma lista de reembolsos.")

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")

    ids_json = {r["id"] for r in registros if r.get("id") is not None}
    ids_banco = {row[0] for row in conn.execute("SELECT id FROM reembolsos")}

    removidos = ids_banco - ids_json
    if removidos:
        resp = input(f"{len(removidos)} registro(s) foram excluídos no controle "
                     f"(ids {sorted(removidos)}). Remover do banco também? [s/N] ")
        if resp.strip().lower() == "s":
            conn.executemany("DELETE FROM reembolsos WHERE id = ?", [(i,) for i in removidos])

    atualizados = inseridos = 0
    for r in registros:
        obs = r.get("observacoes") or ""
        if r.get("proxima_acao"):
            obs = (obs + " | " if obs else "") + "Próxima ação: " + r["proxima_acao"]
        campos = dict(
            beneficiario_id=get_ou_cria(conn, "beneficiarios", r.get("beneficiario")),
            prestador_id=get_ou_cria(conn, "prestadores", r.get("prestador")),
            tipo=r.get("tipo") or "outro",
            descricao=r.get("descricao"),
            data_atendimento=r.get("data_atendimento"),
            data_pagamento=r.get("data_pagamento"),
            valor_pago=float(r.get("valor_pago") or 0),
            valor_reembolsado=float(r.get("valor_reembolsado") or 0),
            status=r.get("status") or "solicitado",
            situacao=r.get("situacao"),
            n_claim=r.get("n_claim"),
            comentario_cigna=r.get("comentario_cigna"),
            nota_fiscal=r.get("nota_fiscal"),
            observacoes=obs or None,
        )
        if r.get("id") in ids_banco:
            sets = ", ".join(f"{k} = ?" for k in campos)
            conn.execute(f"UPDATE reembolsos SET {sets} WHERE id = ?",
                         (*campos.values(), r["id"]))
            atualizados += 1
        else:
            cols = ", ".join(campos)
            marks = ", ".join("?" for _ in campos)
            conn.execute(
                f"INSERT INTO reembolsos (id, funcionario, origem, {cols}) "
                f"VALUES (?, 'Luisa Juliana Faria Ramalho de Souza', 'controle', {marks})",
                (r.get("id"), *campos.values()),
            )
            inseridos += 1

    conn.commit()
    conn.close()
    print(f"OK: {atualizados} atualizado(s), {inseridos} inserido(s), "
          f"{len(removidos) if removidos else 0} candidato(s) a remoção.")
    print("Agora regenere os painéis: python3 gerar_dashboard.py && python3 gerar_controle.py")


if __name__ == "__main__":
    main()
