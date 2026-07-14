#!/usr/bin/env python3
"""Importa prontuários (PDF e CSV) para organizacao.db.

Uso:
  python3 importar_prontuarios.py pasta documentos/prontuarios
  python3 importar_prontuarios.py pasta /caminho/para/seus/pdfs
  python3 importar_prontuarios.py csv templates/prontuarios.csv
  python3 importar_prontuarios.py pasta documentos/prontuarios --extrair-texto
  python3 importar_prontuarios.py pasta documentos/prontuarios --atualizar

Estrutura esperada da pasta:
  documentos/prontuarios/PAC-001/arquivo.pdf
  documentos/prontuarios/PAC-001/2026-07-08-evolucao.pdf

Também aceita arquivos soltos com prefixo: PAC-001-prontuario.pdf
"""

import csv
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "organizacao.db"
CODIGO_RE = re.compile(r"PAC-\d{3}", re.IGNORECASE)
DATA_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
TIPOS = {"anamnese", "evolucao", "alta", "encaminhamento", "laudo", "outro"}


def conectar():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def extrair_texto_pdf(caminho: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("  ⚠ pypdf não instalado. Rode: pip install -r requirements.txt")
        return ""
    try:
        reader = PdfReader(str(caminho))
        partes = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                partes.append(t.strip())
        return "\n\n".join(partes).strip()
    except Exception as e:
        print(f"  ⚠ não leu PDF {caminho.name}: {e}")
        return ""


def codigo_de_caminho(caminho: Path, raiz: Path) -> str | None:
    rel = caminho.relative_to(raiz)
    for parte in rel.parts:
        m = CODIGO_RE.search(parte)
        if m:
            return m.group(0).upper()
    m = CODIGO_RE.search(caminho.stem)
    return m.group(0).upper() if m else None


def inferir_data(nome: str) -> str | None:
    m = DATA_RE.search(nome)
    return m.group(1) if m else None


def inferir_tipo(nome: str) -> str:
    base = nome.lower()
    for t in TIPOS:
        if t in base:
            return t
    if "anamnese" in base or "inicial" in base:
        return "anamnese"
    if "alta" in base:
        return "alta"
    if "laudo" in base:
        return "laudo"
    return "evolucao"


def titulo_de_arquivo(caminho: Path) -> str:
    stem = caminho.stem.replace("_", " ").replace("-", " ")
    return stem[:120]


def paciente_id(conn, codigo: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM pacientes WHERE codigo = ?", (codigo,)
    ).fetchone()
    return row[0] if row else None


def prontuario_existe(conn, paciente_id_: int, arquivo_rel: str) -> bool:
  row = conn.execute(
      "SELECT 1 FROM prontuarios WHERE paciente_id=? AND arquivo=?",
      (paciente_id_, arquivo_rel),
  ).fetchone()
  return row is not None


def registrar_arquivo(conn, titulo, caminho_rel, paciente_id_, data_doc=None):
    existe = conn.execute(
        "SELECT id FROM arquivos WHERE caminho = ?", (caminho_rel,)
    ).fetchone()
    if existe:
        return
    conn.execute(
        """INSERT INTO arquivos
           (titulo, caminho, categoria, tipo_arquivo, data_arquivo, paciente_id, descricao)
           VALUES (?,?,?,?,?,?,?)""",
        (titulo, caminho_rel, "consultorio", "pdf", data_doc, paciente_id_, "Prontuário importado"),
    )


def importar_pdf(conn, caminho: Path, raiz: Path, extrair: bool, atualizar: bool) -> bool:
    if caminho.suffix.lower() != ".pdf":
        return False

    codigo = codigo_de_caminho(caminho, raiz)
    if not codigo:
        print(f"  ⚠ sem código PAC-XXX: {caminho.name}")
        return False

    pid = paciente_id(conn, codigo)
    if not pid:
        print(f"  ⚠ paciente {codigo} não cadastrado — cadastre em templates/pacientes.csv")
        return False

    try:
        arquivo_rel = str(caminho.relative_to(BASE)).replace("\\", "/")
    except ValueError:
        arquivo_rel = str(caminho)

    if prontuario_existe(conn, pid, arquivo_rel) and not atualizar:
        return False

    data_reg = inferir_data(caminho.name) or datetime.fromtimestamp(
        caminho.stat().st_mtime
    ).strftime("%Y-%m-%d")
    tipo = inferir_tipo(caminho.name)
    titulo = titulo_de_arquivo(caminho)
    conteudo = extrair_texto_pdf(caminho) if extrair else f"[PDF] {caminho.name}"
    if not conteudo.strip():
        conteudo = f"[PDF sem texto extraível] {caminho.name}"

    if prontuario_existe(conn, pid, arquivo_rel) and atualizar:
        conn.execute(
            """UPDATE prontuarios SET data_registro=?, tipo=?, titulo=?, conteudo=?
               WHERE paciente_id=? AND arquivo=?""",
            (data_reg, tipo, titulo, conteudo, pid, arquivo_rel),
        )
    else:
        conn.execute(
            """INSERT INTO prontuarios
               (paciente_id, data_registro, tipo, titulo, conteudo, arquivo)
               VALUES (?,?,?,?,?,?)""",
            (pid, data_reg, tipo, titulo, conteudo, arquivo_rel),
        )

    registrar_arquivo(conn, titulo, arquivo_rel, pid, data_reg)

    pasta_pac = raiz / codigo
    if pasta_pac.is_dir():
        conn.execute(
            "UPDATE pacientes SET prontuario_path=? WHERE id=?",
            (str(pasta_pac.relative_to(BASE)).replace("\\", "/"), pid),
        )

    print(f"  ✓ {codigo} ← {caminho.name}")
    return True


def importar_pasta(conn, pasta: Path, extrair: bool, atualizar: bool):
    if not pasta.is_dir():
        print(f"Pasta não encontrada: {pasta}")
        return
    pdfs = sorted(pasta.rglob("*.pdf"))
    if not pdfs:
        print(f"Nenhum PDF em {pasta}")
        return
    n = sum(1 for p in pdfs if importar_pdf(conn, p, pasta, extrair, atualizar))
    print(f"→ {n} prontuário(s) importado(s) de {len(pdfs)} PDF(s)")


def importar_csv(conn, path: Path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f, delimiter=";"):
            codigo = (row.get("paciente_codigo") or "").strip().upper()
            if not codigo or not row.get("conteudo", "").strip():
                continue
            pid = paciente_id(conn, codigo)
            if not pid:
                print(f"  ⚠ paciente {codigo} não encontrado")
                continue
            arquivo = (row.get("arquivo") or "").strip() or None
            if arquivo and prontuario_existe(conn, pid, arquivo):
                continue
            conn.execute(
                """INSERT INTO prontuarios
                   (paciente_id, data_registro, tipo, titulo, conteudo, arquivo)
                   VALUES (?,?,?,?,?,?)""",
                (
                    pid,
                    row.get("data_registro") or datetime.now().strftime("%Y-%m-%d"),
                    row.get("tipo") or "evolucao",
                    row.get("titulo") or "Registro",
                    row["conteudo"].strip(),
                    arquivo,
                ),
            )
            if arquivo:
                registrar_arquivo(
                    conn,
                    row.get("titulo") or "Registro",
                    arquivo,
                    pid,
                    row.get("data_registro"),
                )
            print(f"  ✓ {codigo} ← {row.get('titulo', 'registro')}")
    print("→ CSV importado")


def main():
    if not DB.exists():
        print("Banco não encontrado. Rode: python3 organizacao.py init")
        sys.exit(1)
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(0)

    modo = sys.argv[1]
    alvo = Path(sys.argv[2])
    if not alvo.is_absolute():
        alvo = (BASE / alvo).resolve()

    flags = set(sys.argv[3:])
    extrair = "--extrair-texto" in flags or "--extrair" in flags
    atualizar = "--atualizar" in flags

    conn = conectar()
    if modo == "pasta":
        importar_pasta(conn, alvo, extrair, atualizar)
    elif modo == "csv":
        importar_csv(conn, alvo)
    else:
        print(f"Modo desconhecido: {modo}")
        sys.exit(1)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
