#!/usr/bin/env python3
"""Aplica no banco o JSON exportado pelo painel (painel.html).

Uso:
    python3 importar_painel.py organizador-export.json

O banco organizador.db é recriado com exatamente o conteúdo do JSON
(um backup .bak do banco anterior é mantido). Depois, regenere o painel:
    python3 gerar_painel.py
"""

import json
import shutil
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "organizador.db"
SCHEMA = BASE / "schema.sql"


def inserir(conn, tabela: str, linhas: list, colunas: list) -> None:
    if not linhas:
        return
    sql = f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({', '.join('?' * len(colunas))})"
    conn.executemany(sql, [[l.get(c) for c in colunas] for l in linhas])


def main(caminho: str) -> None:
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))

    if DB.exists():
        shutil.copy2(DB, DB.with_suffix(".db.bak"))
        DB.unlink()

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))

    inserir(conn, "areas", dados.get("areas", []), ["id", "nome", "icone", "cor"])
    inserir(conn, "fin_lancamentos", dados.get("financeiro", []),
            ["id", "data", "tipo", "categoria", "descricao", "valor", "conta",
             "pago", "recorrente", "observacoes"])
    inserir(conn, "yt_videos", dados.get("youtube", []),
            ["id", "titulo", "status", "data_prevista", "data_publicacao", "link", "notas"])
    inserir(conn, "familia_membros", dados.get("familia_membros", []),
            ["id", "nome", "parentesco", "data_nascimento", "notas"])
    inserir(conn, "familia_eventos", dados.get("familia_eventos", []),
            ["id", "membro_id", "data", "hora", "titulo", "tipo", "notas"])
    inserir(conn, "projetos", dados.get("projetos", []),
            ["id", "area_id", "nome", "descricao", "status", "prioridade", "prazo"])
    inserir(conn, "tarefas", dados.get("tarefas", []),
            ["id", "projeto_id", "area_id", "titulo", "notas", "data_limite",
             "prioridade", "status", "concluida_em"])
    inserir(conn, "arquivos", dados.get("arquivos", []),
            ["id", "caminho", "titulo", "area_id", "categoria", "data", "descricao"])

    n_atend = 0
    for p in dados.get("pacientes", []):
        conn.execute(
            """INSERT INTO pacientes (id, nome, telefone, email, data_nascimento,
                                      convenio, ativo, observacoes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (p.get("id"), p.get("nome"), p.get("telefone"), p.get("email"),
             p.get("data_nascimento"), p.get("convenio"),
             1 if p.get("ativo") in (1, "1", True, None) else 0,
             p.get("observacoes")),
        )
        pr = p.get("prontuario") or {}
        conn.execute(
            """INSERT INTO prontuarios (paciente_id, data_abertura, queixa_principal,
                                        historico, hipotese_diagnostica,
                                        plano_terapeutico, observacoes)
               VALUES (?,?,?,?,?,?,?)""",
            (p.get("id"), pr.get("data_abertura") or None, pr.get("queixa_principal"),
             pr.get("historico"), pr.get("hipotese_diagnostica"),
             pr.get("plano_terapeutico"), pr.get("observacoes")),
        )
        for a in p.get("atendimentos", []):
            conn.execute(
                """INSERT INTO atendimentos (paciente_id, data, hora, tipo, status,
                                             valor, pago, evolucao)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (p.get("id"), a.get("data"), a.get("hora"),
                 a.get("tipo") or "consulta", a.get("status") or "agendado",
                 a.get("valor") or 0, 1 if a.get("pago") in (1, "1", True) else 0,
                 a.get("evolucao")),
            )
            n_atend += 1

    conn.commit()
    conn.close()
    print(f"Banco atualizado: {len(dados.get('pacientes', []))} pacientes, "
          f"{n_atend} atendimentos, {len(dados.get('financeiro', []))} lançamentos, "
          f"{len(dados.get('tarefas', []))} tarefas. "
          f"Agora rode: python3 gerar_painel.py")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
