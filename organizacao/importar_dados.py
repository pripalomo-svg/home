#!/usr/bin/env python3
"""Importa dados dos templates CSV para organizacao.db.

Uso:
  python3 importar_dados.py pacientes templates/pacientes.csv
  python3 importar_dados.py atendimentos templates/atendimentos.csv
  python3 importar_dados.py financas templates/financas.csv
  python3 importar_dados.py youtube templates/youtube_videos.csv
  python3 importar_dados.py agenda templates/agenda.csv
  python3 importar_dados.py projetos templates/projetos.csv
  python3 importar_dados.py arquivos templates/arquivos.csv
  python3 importar_dados.py todos   # importa todos os CSV da pasta templates/
"""

import csv
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "organizacao.db"
TEMPLATES = BASE / "templates"


def conectar():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _bool(val):
    return 1 if str(val).strip().lower() in ("1", "sim", "s", "true", "yes") else 0


def _float(val):
    if not val or not str(val).strip():
        return None
    return float(str(val).replace(",", ".").replace("R$", "").strip())


def importar_pacientes(conn, path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if not row.get("nome", "").strip():
                continue
            conn.execute(
                """INSERT INTO pacientes
                   (codigo, nome, telefone, email, data_nascimento, convenio,
                    queixa_principal, status, frequencia, dia_horario, valor_sessao,
                    data_inicio, prontuario_path, observacoes)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(codigo) DO UPDATE SET
                     nome=excluded.nome, telefone=excluded.telefone, email=excluded.email,
                     data_nascimento=excluded.data_nascimento, convenio=excluded.convenio,
                     queixa_principal=excluded.queixa_principal, status=excluded.status,
                     frequencia=excluded.frequencia, dia_horario=excluded.dia_horario,
                     valor_sessao=excluded.valor_sessao, data_inicio=excluded.data_inicio,
                     prontuario_path=excluded.prontuario_path, observacoes=excluded.observacoes""",
                (
                    row.get("codigo") or None,
                    row["nome"].strip(),
                    row.get("telefone") or None,
                    row.get("email") or None,
                    row.get("data_nascimento") or None,
                    row.get("convenio") or None,
                    row.get("queixa_principal") or None,
                    row.get("status") or "ativo",
                    row.get("frequencia") or None,
                    row.get("dia_horario") or None,
                    _float(row.get("valor_sessao")),
                    row.get("data_inicio") or None,
                    row.get("prontuario_path") or None,
                    row.get("observacoes") or None,
                ),
            )
    print(f"  ✓ pacientes ← {path.name}")


def importar_atendimentos(conn, path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if not row.get("paciente_codigo") or not row.get("data"):
                continue
            pid = conn.execute(
                "SELECT id FROM pacientes WHERE codigo = ?", (row["paciente_codigo"],)
            ).fetchone()
            if not pid:
                print(f"  ⚠ paciente não encontrado: {row['paciente_codigo']}")
                continue
            conn.execute(
                """INSERT INTO atendimentos
                   (paciente_id, data, hora_inicio, hora_fim, tipo, modalidade,
                    status, valor, pago, notas)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    pid[0],
                    row["data"],
                    row.get("hora_inicio") or None,
                    row.get("hora_fim") or None,
                    row.get("tipo") or "sessao",
                    row.get("modalidade") or "presencial",
                    row.get("status") or "agendado",
                    _float(row.get("valor")),
                    _bool(row.get("pago", "0")),
                    row.get("notas") or None,
                ),
            )
    print(f"  ✓ atendimentos ← {path.name}")


def importar_financas(conn, path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if not row.get("descricao") or not row.get("valor"):
                continue
            cat = conn.execute(
                "SELECT id FROM financas_categorias WHERE nome = ?",
                (row["categoria"],),
            ).fetchone()
            if not cat:
                conn.execute(
                    "INSERT INTO financas_categorias (nome, tipo) VALUES (?,?)",
                    (row["categoria"], row.get("tipo") or "despesa"),
                )
                cat_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            else:
                cat_id = cat[0]
            conn.execute(
                """INSERT INTO financas_lancamentos
                   (categoria_id, descricao, valor, tipo, data, pago, observacoes)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    cat_id,
                    row["descricao"].strip(),
                    _float(row["valor"]),
                    row.get("tipo") or "despesa",
                    row["data"],
                    _bool(row.get("pago", "1")),
                    row.get("observacoes") or None,
                ),
            )
    print(f"  ✓ financas ← {path.name}")


def importar_youtube(conn, path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if not row.get("titulo"):
                continue
            conn.execute(
                """INSERT INTO youtube_videos
                   (titulo, descricao, status, data_gravacao, data_publicacao,
                    url, duracao_min, roteiro, tags, notas)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    row["titulo"].strip(),
                    row.get("descricao") or None,
                    row.get("status") or "planejado",
                    row.get("data_gravacao") or None,
                    row.get("data_publicacao") or None,
                    row.get("url") or None,
                    int(row["duracao_min"]) if row.get("duracao_min") else None,
                    row.get("roteiro") or None,
                    row.get("tags") or None,
                    row.get("notas") or None,
                ),
            )
    print(f"  ✓ youtube ← {path.name}")


def importar_agenda(conn, path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if not row.get("titulo") or not row.get("data_inicio"):
                continue
            paciente_id = None
            if row.get("paciente_codigo"):
                p = conn.execute(
                    "SELECT id FROM pacientes WHERE codigo = ?",
                    (row["paciente_codigo"],),
                ).fetchone()
                paciente_id = p[0] if p else None
            conn.execute(
                """INSERT INTO agenda
                   (titulo, data_inicio, hora_inicio, data_fim, hora_fim,
                    tipo, local, status, notas, paciente_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    row["titulo"].strip(),
                    row["data_inicio"],
                    row.get("hora_inicio") or None,
                    row.get("data_fim") or None,
                    row.get("hora_fim") or None,
                    row.get("tipo") or "geral",
                    row.get("local") or None,
                    row.get("status") or "confirmado",
                    row.get("notas") or None,
                    paciente_id,
                ),
            )
    print(f"  ✓ agenda ← {path.name}")


def importar_projetos(conn, path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if not row.get("titulo"):
                continue
            area_id = None
            if row.get("area"):
                a = conn.execute(
                    "SELECT id FROM areas WHERE nome = ?", (row["area"],)
                ).fetchone()
                area_id = a[0] if a else None
            conn.execute(
                """INSERT INTO projetos
                   (area_id, titulo, descricao, status, prioridade,
                    data_inicio, data_prazo, tags, notas)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    area_id,
                    row["titulo"].strip(),
                    row.get("descricao") or None,
                    row.get("status") or "ativo",
                    row.get("prioridade") or "media",
                    row.get("data_inicio") or None,
                    row.get("data_prazo") or None,
                    row.get("tags") or None,
                    row.get("notas") or None,
                ),
            )
    print(f"  ✓ projetos ← {path.name}")


def importar_arquivos(conn, path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if not row.get("titulo") or not row.get("caminho"):
                continue
            conn.execute(
                """INSERT INTO arquivos
                   (titulo, caminho, categoria, tipo_arquivo, data_arquivo, descricao, tags)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    row["titulo"].strip(),
                    row["caminho"].strip(),
                    row.get("categoria") or "geral",
                    row.get("tipo_arquivo") or None,
                    row.get("data_arquivo") or None,
                    row.get("descricao") or None,
                    row.get("tags") or None,
                ),
            )
    print(f"  ✓ arquivos ← {path.name}")


IMPORTADORES = {
    "pacientes": importar_pacientes,
    "atendimentos": importar_atendimentos,
    "financas": importar_financas,
    "youtube": importar_youtube,
    "agenda": importar_agenda,
    "projetos": importar_projetos,
    "arquivos": importar_arquivos,
}

MAPA_TODOS = [
    ("pacientes", "pacientes.csv"),
    ("atendimentos", "atendimentos.csv"),
    ("financas", "financas.csv"),
    ("youtube", "youtube_videos.csv"),
    ("agenda", "agenda.csv"),
    ("projetos", "projetos.csv"),
    ("arquivos", "arquivos.csv"),
]


def main():
    if not DB.exists():
        print("Banco não encontrado. Rode: python3 organizacao.py init")
        sys.exit(1)
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    conn = conectar()
    cmd = sys.argv[1]

    if cmd == "todos":
        for tipo, arquivo in MAPA_TODOS:
            path = TEMPLATES / arquivo
            if path.exists() and path.stat().st_size > 200:
                IMPORTADORES[tipo](conn, path)
    elif cmd in IMPORTADORES:
        path = Path(sys.argv[2]) if len(sys.argv) > 2 else TEMPLATES / f"{cmd}.csv"
        if cmd == "youtube":
            path = Path(sys.argv[2]) if len(sys.argv) > 2 else TEMPLATES / "youtube_videos.csv"
        IMPORTADORES[cmd](conn, path)
    else:
        print(f"Tipo desconhecido: {cmd}")
        sys.exit(1)

    conn.commit()
    conn.close()
    print("Importação concluída.")


if __name__ == "__main__":
    main()
