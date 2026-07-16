#!/usr/bin/env python3
"""Inicializa e gerencia o banco organizacao.db.

Uso:
  python3 organizacao.py init          # cria/recria o banco
  python3 organizacao.py status        # resumo rápido
  python3 organizacao.py gerar         # gera index.html
  python3 organizacao.py prontuarios   # importa PDFs de documentos/prontuarios/
  python3 organizacao.py notion        # importa export do Notion (pasta notion/)
  python3 organizacao.py sincronizar   # sync automático Notion (API ou export)
  python3 organizacao.py investimentos # gera painel investimentos.html
"""

import sqlite3
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "organizacao.db"
SCHEMA = BASE / "schema.sql"
SEED = BASE / "seed.sql"


def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init(recriar=False):
    if recriar and DB.exists():
        DB.unlink()
    conn = conectar()
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.executescript(SEED.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
    print(f"✓ Banco criado: {DB}")


def status():
    if not DB.exists():
        print("Banco não encontrado. Rode: python3 organizacao.py init")
        return
    conn = conectar()
    dash = dict(conn.execute("SELECT * FROM vw_dashboard").fetchone())
    print("── Central de Organização · Resumo ──")
    for k, v in dash.items():
        label = k.replace("_", " ").title()
        if "receita" in k or "despesa" in k:
            print(f"  {label}: R$ {v:,.2f}")
        else:
            print(f"  {label}: {v}")
    print()
    pacientes = conn.execute(
        "SELECT codigo, nome, status FROM pacientes ORDER BY codigo LIMIT 5"
    ).fetchall()
    print(f"  Pacientes (primeiros 5 de {dash['pacientes_ativos']}):")
    for p in pacientes:
        print(f"    {p['codigo']} — {p['nome']} [{p['status']}]")
    conn.close()


def gerar():
    script = BASE / "gerar_dashboard.py"
    subprocess.run([sys.executable, str(script)], check=True)


def prontuarios(extrair=False, atualizar=False):
    script = BASE / "importar_prontuarios.py"
    pasta = BASE / "documentos" / "prontuarios"
    args = [sys.executable, str(script), "pasta", str(pasta)]
    if extrair:
        args.append("--extrair-texto")
    if atualizar:
        args.append("--atualizar")
    subprocess.run(args, check=True)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "init":
        init(recriar="--recriar" in sys.argv)
    elif cmd == "status":
        status()
    elif cmd == "gerar":
        gerar()
    elif cmd == "prontuarios":
        prontuarios(
            extrair="--extrair" in sys.argv or "--extrair-texto" in sys.argv,
            atualizar="--atualizar" in sys.argv,
        )
    elif cmd == "notion":
        script = BASE / "importar_notion.py"
        pasta = BASE / "notion"
        args = [sys.executable, str(script), "auto", str(pasta)]
        if len(sys.argv) > 2 and not sys.argv[2].startswith("--"):
            args[2] = "zip" if sys.argv[2].endswith(".zip") else "auto"
            args[3] = str(Path(sys.argv[2]).resolve() if Path(sys.argv[2]).is_absolute() else BASE / sys.argv[2])
        subprocess.run(args, check=True)
    elif cmd == "sincronizar":
        script = BASE / "sincronizar_notion.py"
        args = [sys.executable, str(script)] + sys.argv[2:]
        subprocess.run(args, check=True)
    elif cmd == "investimentos":
        subprocess.run([sys.executable, str(BASE / "gerar_investimentos.py")], check=True)
    else:
        print(f"Comando desconhecido: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
