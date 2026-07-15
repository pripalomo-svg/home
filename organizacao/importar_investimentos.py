#!/usr/bin/env python3
"""Importa investimentos de CSV para organizacao.db.

Uso:  python3 importar_investimentos.py templates/investimentos.csv
"""

import csv
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "organizacao.db"


def _float(v):
    if not v or not str(v).strip():
        return None
    return float(str(v).replace(",", ".").replace("R$", "").replace("%", "").strip())


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "templates" / "investimentos.csv"
    if not path.is_absolute():
        path = BASE / path
    if not DB.exists():
        print("Banco não encontrado. Rode: python3 organizacao.py init")
        sys.exit(1)

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    n = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            nome = (row.get("nome") or "").strip()
            valor = _float(row.get("valor_atual"))
            if not nome or not valor:
                continue
            ticker = (row.get("ticker") or "").strip() or None
            existente = None
            if ticker:
                existente = conn.execute(
                    "SELECT id FROM investimentos WHERE ticker = ?", (ticker,)
                ).fetchone()
            if not existente:
                existente = conn.execute(
                    "SELECT id FROM investimentos WHERE nome = ?", (nome,)
                ).fetchone()
            params = (
                nome,
                row.get("tipo") or "outro",
                row.get("instituicao") or None,
                ticker,
                row.get("codigo_ativo") or None,
                valor,
                _float(row.get("valor_aplicado")) or valor,
                _float(row.get("quantidade")),
                _float(row.get("preco_unitario")),
                _float(row.get("taxa_anual")),
                row.get("data_contratacao") or None,
                row.get("data_atualizacao") or None,
                _float(row.get("aporte_mensal")) or 0,
                row.get("cor") or "#3b82f6",
                row.get("notas") or None,
            )
            if existente:
                conn.execute(
                    """UPDATE investimentos SET
                       nome=?, tipo=?, instituicao=?, ticker=?, codigo_ativo=?,
                       valor_atual=?, valor_aplicado=?, quantidade=?, preco_unitario=?,
                       taxa_anual=?, data_contratacao=?, data_atualizacao=?,
                       aporte_mensal=?, cor=?, notas=?, ativo=1 WHERE id=?""",
                    (*params, existente[0]),
                )
            else:
                conn.execute(
                    """INSERT INTO investimentos
                       (nome, tipo, instituicao, ticker, codigo_ativo, valor_atual,
                        valor_aplicado, quantidade, preco_unitario, taxa_anual,
                        data_contratacao, data_atualizacao, aporte_mensal, cor, notas)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    params,
                )
            n += 1
    conn.commit()
    conn.close()
    print(f"✓ {n} investimento(s) importado(s) de {path.name}")


if __name__ == "__main__":
    main()
