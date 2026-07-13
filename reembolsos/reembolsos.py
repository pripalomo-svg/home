#!/usr/bin/env python3
"""Gerenciador de reembolsos do plano de saúde (SQLite).

Uso:
    python3 reembolsos.py init                      # cria o banco de dados
    python3 reembolsos.py add                       # adiciona um reembolso (interativo)
    python3 reembolsos.py add --beneficiario "Ana" --tipo consulta \
        --data 2026-07-01 --valor 500 --prestador "Dr. Silva" [...]
    python3 reembolsos.py listar [--status pago] [--ano 2026]
    python3 reembolsos.py resumo                    # totais por status, ano e beneficiário
    python3 reembolsos.py importar arquivo.csv      # importa de CSV (ver template)
    python3 reembolsos.py atualizar ID --status pago --valor-reembolsado 350
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "reembolsos.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"

STATUS_VALIDOS = ("solicitado", "em_analise", "pago", "pago_parcial", "negado")


def conectar() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init(_args) -> None:
    conn = conectar()
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
    print(f"Banco de dados criado em {DB_PATH}")


def _obter_ou_criar(conn, tabela: str, nome: str, extras: dict | None = None) -> int:
    row = conn.execute(f"SELECT id FROM {tabela} WHERE nome = ?", (nome,)).fetchone()
    if row:
        return row["id"]
    extras = extras or {}
    colunas = ["nome"] + list(extras.keys())
    valores = [nome] + list(extras.values())
    placeholders = ", ".join("?" for _ in valores)
    cur = conn.execute(
        f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({placeholders})", valores
    )
    return cur.lastrowid


def _inserir_reembolso(conn, dados: dict) -> int:
    beneficiario_id = _obter_ou_criar(conn, "beneficiarios", dados["beneficiario"])
    prestador_id = None
    if dados.get("prestador"):
        prestador_id = _obter_ou_criar(
            conn, "prestadores", dados["prestador"],
            {"especialidade": dados.get("especialidade")},
        )
    cur = conn.execute(
        """INSERT INTO reembolsos
           (protocolo, beneficiario_id, prestador_id, tipo, descricao,
            data_atendimento, data_solicitacao, data_pagamento,
            valor_pago, valor_reembolsado, status, nota_fiscal, observacoes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            dados.get("protocolo"),
            beneficiario_id,
            prestador_id,
            dados["tipo"],
            dados.get("descricao"),
            dados["data_atendimento"],
            dados.get("data_solicitacao"),
            dados.get("data_pagamento"),
            float(dados["valor_pago"]),
            float(dados.get("valor_reembolsado") or 0),
            dados.get("status") or "solicitado",
            dados.get("nota_fiscal"),
            dados.get("observacoes"),
        ),
    )
    return cur.lastrowid


def add(args) -> None:
    dados = {
        "beneficiario": args.beneficiario or input("Beneficiário: ").strip(),
        "prestador": args.prestador,
        "especialidade": args.especialidade,
        "tipo": args.tipo or input("Tipo (consulta/exame/terapia/medicamento/outro): ").strip(),
        "descricao": args.descricao,
        "data_atendimento": args.data or input("Data do atendimento (YYYY-MM-DD): ").strip(),
        "data_solicitacao": args.data_solicitacao,
        "data_pagamento": args.data_pagamento,
        "valor_pago": args.valor if args.valor is not None else float(input("Valor pago (R$): ")),
        "valor_reembolsado": args.valor_reembolsado,
        "status": args.status,
        "protocolo": args.protocolo,
        "nota_fiscal": args.nota_fiscal,
        "observacoes": args.observacoes,
    }
    conn = conectar()
    novo_id = _inserir_reembolso(conn, dados)
    conn.commit()
    conn.close()
    print(f"Reembolso #{novo_id} registrado.")


def listar(args) -> None:
    filtros, params = [], []
    if args.status:
        filtros.append("status = ?")
        params.append(args.status)
    if args.ano:
        filtros.append("strftime('%Y', data_atendimento) = ?")
        params.append(str(args.ano))
    if args.beneficiario:
        filtros.append("beneficiario = ?")
        params.append(args.beneficiario)
    where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    conn = conectar()
    rows = conn.execute(
        f"SELECT * FROM vw_reembolsos {where} ORDER BY data_atendimento DESC", params
    ).fetchall()
    conn.close()

    if not rows:
        print("Nenhum reembolso encontrado.")
        return

    fmt = "{:>4}  {:<10}  {:<15}  {:<12}  {:>10}  {:>12}  {:<12}"
    print(fmt.format("ID", "Data", "Beneficiário", "Tipo", "Pago R$", "Reemb. R$", "Status"))
    print("-" * 90)
    for r in rows:
        print(fmt.format(
            r["id"], r["data_atendimento"], (r["beneficiario"] or "")[:15],
            (r["tipo"] or "")[:12], f"{r['valor_pago']:.2f}",
            f"{r['valor_reembolsado']:.2f}", r["status"],
        ))
    total_pago = sum(r["valor_pago"] for r in rows)
    total_reemb = sum(r["valor_reembolsado"] for r in rows)
    print("-" * 90)
    print(f"{len(rows)} registro(s) | Total pago: R$ {total_pago:.2f} | "
          f"Total reembolsado: R$ {total_reemb:.2f}")


def resumo(_args) -> None:
    conn = conectar()
    print("== Por status ==")
    for r in conn.execute(
        """SELECT status, COUNT(*) qtd, SUM(valor_pago) pago, SUM(valor_reembolsado) reemb
           FROM reembolsos GROUP BY status ORDER BY status"""
    ):
        print(f"  {r['status']:<12} {r['qtd']:>3}x  pago R$ {r['pago']:.2f}  "
              f"reembolsado R$ {r['reemb']:.2f}")

    print("\n== Por ano ==")
    for r in conn.execute(
        """SELECT strftime('%Y', data_atendimento) ano, COUNT(*) qtd,
                  SUM(valor_pago) pago, SUM(valor_reembolsado) reemb
           FROM reembolsos GROUP BY ano ORDER BY ano DESC"""
    ):
        print(f"  {r['ano']}  {r['qtd']:>3}x  pago R$ {r['pago']:.2f}  "
              f"reembolsado R$ {r['reemb']:.2f}")

    print("\n== Por beneficiário ==")
    for r in conn.execute(
        """SELECT b.nome, COUNT(*) qtd, SUM(r.valor_pago) pago,
                  SUM(r.valor_reembolsado) reemb
           FROM reembolsos r JOIN beneficiarios b ON b.id = r.beneficiario_id
           GROUP BY b.nome ORDER BY pago DESC"""
    ):
        print(f"  {r['nome']:<20} {r['qtd']:>3}x  pago R$ {r['pago']:.2f}  "
              f"reembolsado R$ {r['reemb']:.2f}")
    conn.close()


def importar(args) -> None:
    caminho = Path(args.arquivo)
    if not caminho.exists():
        sys.exit(f"Arquivo não encontrado: {caminho}")
    conn = conectar()
    qtd = 0
    with caminho.open(newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            dados = {k: (v.strip() or None) for k, v in linha.items()}
            if not dados.get("beneficiario") or not dados.get("data_atendimento"):
                continue
            _inserir_reembolso(conn, dados)
            qtd += 1
    conn.commit()
    conn.close()
    print(f"{qtd} reembolso(s) importado(s) de {caminho}.")


def atualizar(args) -> None:
    campos, params = [], []
    if args.status:
        campos.append("status = ?")
        params.append(args.status)
    if args.valor_reembolsado is not None:
        campos.append("valor_reembolsado = ?")
        params.append(args.valor_reembolsado)
    if args.data_pagamento:
        campos.append("data_pagamento = ?")
        params.append(args.data_pagamento)
    if args.protocolo:
        campos.append("protocolo = ?")
        params.append(args.protocolo)
    if args.observacoes:
        campos.append("observacoes = ?")
        params.append(args.observacoes)
    if not campos:
        sys.exit("Nada para atualizar. Informe ao menos um campo.")
    params.append(args.id)
    conn = conectar()
    cur = conn.execute(f"UPDATE reembolsos SET {', '.join(campos)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        sys.exit(f"Reembolso #{args.id} não encontrado.")
    print(f"Reembolso #{args.id} atualizado.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reembolsos do plano de saúde")
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("init", help="cria o banco de dados").set_defaults(func=init)

    p_add = sub.add_parser("add", help="adiciona um reembolso")
    p_add.add_argument("--beneficiario")
    p_add.add_argument("--prestador")
    p_add.add_argument("--especialidade")
    p_add.add_argument("--tipo")
    p_add.add_argument("--descricao")
    p_add.add_argument("--data", help="data do atendimento (YYYY-MM-DD)")
    p_add.add_argument("--data-solicitacao")
    p_add.add_argument("--data-pagamento")
    p_add.add_argument("--valor", type=float, help="valor pago (R$)")
    p_add.add_argument("--valor-reembolsado", type=float)
    p_add.add_argument("--status", choices=STATUS_VALIDOS)
    p_add.add_argument("--protocolo")
    p_add.add_argument("--nota-fiscal")
    p_add.add_argument("--observacoes")
    p_add.set_defaults(func=add)

    p_lis = sub.add_parser("listar", help="lista reembolsos")
    p_lis.add_argument("--status", choices=STATUS_VALIDOS)
    p_lis.add_argument("--ano", type=int)
    p_lis.add_argument("--beneficiario")
    p_lis.set_defaults(func=listar)

    sub.add_parser("resumo", help="totais por status, ano e beneficiário").set_defaults(func=resumo)

    p_imp = sub.add_parser("importar", help="importa reembolsos de um CSV")
    p_imp.add_argument("arquivo")
    p_imp.set_defaults(func=importar)

    p_upd = sub.add_parser("atualizar", help="atualiza um reembolso existente")
    p_upd.add_argument("id", type=int)
    p_upd.add_argument("--status", choices=STATUS_VALIDOS)
    p_upd.add_argument("--valor-reembolsado", type=float)
    p_upd.add_argument("--data-pagamento")
    p_upd.add_argument("--protocolo")
    p_upd.add_argument("--observacoes")
    p_upd.set_defaults(func=atualizar)

    args = parser.parse_args()
    if args.comando != "init" and not DB_PATH.exists():
        init(None)
    args.func(args)


if __name__ == "__main__":
    main()
