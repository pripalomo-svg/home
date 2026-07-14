#!/usr/bin/env python3
"""Aplica no banco (organizacao.db) as alterações exportadas do painel.

No painel, clique em “⬇️ Exportar JSON” para baixar o arquivo com tudo que você
editou. Depois traga essas mudanças de volta para o banco:

    python3 importar_painel.py organizacao_export.json

O banco é reconstruído a partir do JSON (a estrutura vem do schema.sql).
Regenere o painel depois com:  python3 gerar_painel.py
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(AQUI, "organizacao.db")
SCHEMA = os.path.join(AQUI, "schema.sql")

# Ordem de inserção respeitando dependências (pais antes dos filhos)
ORDEM = [
    "areas", "contas", "categorias_fin", "canais", "familiares",
    "projetos", "tarefas", "arquivos", "transacoes", "metas", "videos",
    "pacientes", "prontuarios", "atendimentos", "evolucoes", "eventos",
]


def colunas(con: sqlite3.Connection, tabela: str) -> list[str]:
    return [r[1] for r in con.execute(f"PRAGMA table_info({tabela})").fetchall()]


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python3 importar_painel.py <arquivo_export.json>")
        sys.exit(1)
    caminho = sys.argv[1]
    with open(caminho, encoding="utf-8") as fh:
        dados = json.load(fh)

    if not os.path.exists(SCHEMA):
        print("schema.sql não encontrado."); sys.exit(1)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = OFF")
    with open(SCHEMA, encoding="utf-8") as fh:
        con.executescript(fh.read())

    total = 0
    for tabela in ORDEM:
        registros = dados.get(tabela)
        if registros is None:
            continue
        cols_tabela = set(colunas(con, tabela))
        con.execute(f"DELETE FROM {tabela}")
        for reg in registros:
            campos = [k for k in reg.keys() if k in cols_tabela]
            marc = ",".join("?" for _ in campos)
            con.execute(
                f"INSERT INTO {tabela} ({','.join(campos)}) VALUES ({marc})",
                [reg[k] for k in campos],
            )
            total += 1

    con.commit()
    con.execute("PRAGMA foreign_keys = ON")
    ok = con.execute("PRAGMA foreign_key_check").fetchall()
    con.close()

    print(f"Importados {total} registros para {DB}.")
    if ok:
        print("Aviso: há violações de chave estrangeira:", ok)
    else:
        print("Regenere o painel:  python3 gerar_painel.py")


if __name__ == "__main__":
    main()
