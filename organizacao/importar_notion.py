#!/usr/bin/env python3
"""Importa exportações do Notion para organizacao.db.

O Notion exporta assim: ⋯ → Export → Markdown & CSV → gera um ZIP.
Dentro do ZIP: um CSV por database + páginas em .md

Uso:
  python3 importar_notion.py zip ~/Downloads/Export.zip
  python3 importar_notion.py pasta ~/Downloads/Export-xxx
  python3 importar_notion.py auto notion/          # detecta tipo de cada CSV
  python3 importar_notion.py pacientes notion/Pacientes.csv
  python3 importar_notion.py projetos notion/Projetos.csv
  python3 importar_notion.py markdown notion/      # importa .md como notas

Tipos: pacientes, atendimentos, projetos, tarefas, financas, youtube,
       agenda, notas, prontuarios, auto
"""

import csv
import re
import sqlite3
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

BASE = Path(__file__).resolve().parent
DB = BASE / "organizacao.db"
NOTION_DIR = BASE / "notion"

# ── Detecção automática por nome de arquivo / colunas ────────────────────────
TIPO_POR_ARQUIVO = [
    (r"pacient|patient|consultório|consultorio|cliente|prontu", "pacientes"),
    (r"atend|sess[aã]o|session|consulta", "atendimentos"),
    (r"finan|gasto|receita|despesa|lançamento|lancamento", "financas"),
    (r"youtube|v[ií]deo|video|canal", "youtube"),
    (r"agenda|calend[aá]rio|calendar|evento", "agenda"),
    (r"projeto|project", "projetos"),
    (r"tarefa|task|to.?do", "tarefas"),
    (r"prontu[aá]rio|evolu[cç][aã]o|anamnese", "prontuarios"),
    (r"nota|note|ideia", "notas"),
]

COLS = {
    "nome": ["name", "nome", "paciente", "título", "titulo", "title", "cliente"],
    "telefone": ["telefone", "phone", "celular", "whatsapp", "tel"],
    "email": ["email", "e-mail", "mail"],
    "nascimento": ["nascimento", "data de nascimento", "birthday", "birth", "aniversário"],
    "convenio": ["convênio", "convenio", "plano", "insurance"],
    "queixa": ["queixa", "motivo", "diagnóstico", "diagnostico", "problema", "tags"],
    "status": ["status", "estado", "situação", "situacao"],
    "frequencia": ["frequência", "frequencia", "freq"],
    "horario": ["horário", "horario", "dia", "dia_horario", "agenda fixa"],
    "valor": ["valor", "preço", "preco", "price", "valor sessão", "valor_sessao"],
    "codigo": ["código", "codigo", "code", "id paciente", "pac"],
    "data": ["data", "date", "quando", "dia"],
    "hora": ["hora", "time", "horário início", "horario inicio", "início", "inicio"],
    "hora_fim": ["hora fim", "fim", "end", "término", "termino"],
    "descricao": ["descrição", "descricao", "description", "detalhes", "notes", "notas"],
    "titulo": ["título", "titulo", "title", "name", "nome", "evento", "assunto"],
    "tipo": ["tipo", "type", "categoria", "category"],
    "categoria": ["categoria", "category", "grupo"],
    "pago": ["pago", "paid", "quitado"],
    "paciente": ["paciente", "patient", "cliente", "name"],
    "local": ["local", "location", "lugar", "endereço"],
    "url": ["url", "link", "youtube"],
    "prioridade": ["prioridade", "priority"],
    "prazo": ["prazo", "deadline", "data limite", "due"],
    "conteudo": ["conteúdo", "conteudo", "content", "texto", "body"],
    "tags": ["tags", "etiquetas", "label"],
    "modalidade": ["modalidade", "formato", "presencial", "online"],
}


def conectar():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def achar_col(headers: list[str], chaves: list[str]) -> str | None:
    norm_h = {norm(h): h for h in headers}
    for k in chaves:
        if k in norm_h:
            return norm_h[k]
    for h in headers:
        nh = norm(h)
        for k in chaves:
            if k in nh or nh in k:
                return h
    return None


def ler_csv(path: Path) -> tuple[list[str], list[dict]]:
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with open(path, newline="", encoding=enc) as f:
                sample = f.read(4096)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Encoding não suportado: {path}")

    delim = ";" if sample.count(";") > sample.count(",") else ","
    with open(path, newline="", encoding=enc) as f:
        reader = csv.DictReader(f, delimiter=delim)
        headers = reader.fieldnames or []
        rows = [dict(r) for r in reader]
    return headers, rows


def detectar_tipo(path: Path, headers: list[str]) -> str | None:
    nome = norm(path.stem)
    for pat, tipo in TIPO_POR_ARQUIVO:
        if re.search(pat, nome):
            return tipo
    cols = " ".join(norm(h) for h in headers)
    if achar_col(headers, COLS["paciente"]) and achar_col(headers, COLS["data"]):
        return "atendimentos"
    if achar_col(headers, COLS["nome"]) and (
        achar_col(headers, COLS["telefone"]) or achar_col(headers, COLS["queixa"])
    ):
        return "pacientes"
    if achar_col(headers, COLS["valor"]) and achar_col(headers, COLS["data"]):
        return "financas"
    if achar_col(headers, COLS["titulo"]) and achar_col(headers, COLS["data"]):
        if "evento" in cols or "agenda" in nome:
            return "agenda"
    if achar_col(headers, COLS["titulo"]) and achar_col(headers, COLS["status"]):
        if "tarefa" in nome or "task" in cols:
            return "tarefas"
        return "projetos"
    if achar_col(headers, COLS["url"]) or "youtube" in nome:
        return "youtube"
    if achar_col(headers, COLS["conteudo"]):
        return "prontuarios"
    return None


def val(row: dict, headers: list[str], chaves: list[str]) -> str:
    col = achar_col(headers, chaves)
    return (row.get(col) or "").strip() if col else ""


def parse_data(s: str) -> str | None:
    s = (s or "").strip()
    if not s:
        return None
    # Notion: "July 14, 2026" ou "2026-07-14" ou "14/07/2026"
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s[:30].split("→")[0].strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    m = re.search(r"(\d{4}-\d{2}-\d{2})", s)
    if m:
        return m.group(1)
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return None


def parse_valor(s: str) -> float | None:
    if not s:
        return None
    s = re.sub(r"[R$\s]", "", s).replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_bool(s: str) -> int:
    return 1 if norm(s) in ("sim", "s", "yes", "true", "1", "pago", "done", "✓", "✅") else 0


def proximo_codigo(conn) -> str:
    row = conn.execute(
        "SELECT codigo FROM pacientes WHERE codigo LIKE 'PAC-%' ORDER BY codigo DESC LIMIT 1"
    ).fetchone()
    if row:
        n = int(row[0].split("-")[1]) + 1
    else:
        n = 1
    return f"PAC-{n:03d}"


def paciente_por_nome(conn, nome: str) -> int | None:
    if not nome:
        return None
    row = conn.execute(
        "SELECT id FROM pacientes WHERE nome = ? COLLATE NOCASE", (nome,)
    ).fetchone()
    if row:
        return row[0]
    row = conn.execute(
        "SELECT id FROM pacientes WHERE nome LIKE ? COLLATE NOCASE", (f"%{nome}%",)
    ).fetchone()
    return row[0] if row else None


def importar_pacientes(conn, path: Path) -> int:
    headers, rows = ler_csv(path)
    n = 0
    for row in rows:
        nome = val(row, headers, COLS["nome"])
        if not nome:
            continue
        codigo = val(row, headers, COLS["codigo"]) or proximo_codigo(conn)
        conn.execute(
            """INSERT INTO pacientes
               (codigo, nome, telefone, email, data_nascimento, convenio, queixa_principal,
                status, frequencia, dia_horario, valor_sessao, data_inicio, observacoes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(codigo) DO UPDATE SET
                 nome=excluded.nome, telefone=excluded.telefone, email=excluded.email,
                 data_nascimento=excluded.data_nascimento, convenio=excluded.convenio,
                 queixa_principal=excluded.queixa_principal, status=excluded.status,
                 frequencia=excluded.frequencia, dia_horario=excluded.dia_horario,
                 valor_sessao=excluded.valor_sessao, observacoes=excluded.observacoes""",
            (
                codigo.upper() if codigo.startswith("PAC") else codigo,
                nome,
                val(row, headers, COLS["telefone"]) or None,
                val(row, headers, COLS["email"]) or None,
                parse_data(val(row, headers, COLS["nascimento"])),
                val(row, headers, COLS["convenio"]) or "particular",
                val(row, headers, COLS["queixa"]) or None,
                (val(row, headers, COLS["status"]) or "ativo").lower(),
                val(row, headers, COLS["frequencia"]) or None,
                val(row, headers, COLS["horario"]) or None,
                parse_valor(val(row, headers, COLS["valor"])),
                parse_data(val(row, headers, COLS["data"])),
                f"Importado do Notion: {path.name}",
            ),
        )
        n += 1
    return n


def importar_atendimentos(conn, path: Path) -> int:
    headers, rows = ler_csv(path)
    n = 0
    for row in rows:
        pac = val(row, headers, COLS["paciente"]) or val(row, headers, COLS["nome"])
        data = parse_data(val(row, headers, COLS["data"]))
        if not pac or not data:
            continue
        pid = paciente_por_nome(conn, pac)
        if not pid:
            cod = proximo_codigo(conn)
            conn.execute(
                "INSERT INTO pacientes (codigo, nome, status) VALUES (?,?,?)",
                (cod, pac, "ativo"),
            )
            pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            """INSERT INTO atendimentos
               (paciente_id, data, hora_inicio, hora_fim, tipo, modalidade, status, valor, pago, notas)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                pid, data,
                val(row, headers, COLS["hora"]) or None,
                val(row, headers, COLS["hora_fim"]) or None,
                val(row, headers, COLS["tipo"]) or "sessao",
                val(row, headers, COLS["modalidade"]) or "presencial",
                (val(row, headers, COLS["status"]) or "realizado").lower(),
                parse_valor(val(row, headers, COLS["valor"])),
                parse_bool(val(row, headers, COLS["pago"])),
                val(row, headers, COLS["descricao"]) or f"Notion: {path.name}",
            ),
        )
        n += 1
    return n


def importar_financas(conn, path: Path) -> int:
    headers, rows = ler_csv(path)
    n = 0
    for row in rows:
        desc = val(row, headers, COLS["descricao"]) or val(row, headers, COLS["titulo"])
        valor = parse_valor(val(row, headers, COLS["valor"]))
        data = parse_data(val(row, headers, COLS["data"]))
        if not desc or not valor or not data:
            continue
        cat_nome = val(row, headers, COLS["categoria"]) or "Importado do Notion"
        tipo_raw = norm(val(row, headers, COLS["tipo"]))
        tipo = "despesa" if any(x in tipo_raw for x in ("despesa", "gasto", "expense", "saída")) else "receita"
        if any(x in tipo_raw for x in ("receita", "income", "entrada")):
            tipo = "receita"
        cat = conn.execute(
            "SELECT id FROM financas_categorias WHERE nome = ?", (cat_nome,)
        ).fetchone()
        if not cat:
            conn.execute(
                "INSERT INTO financas_categorias (nome, tipo) VALUES (?,?)", (cat_nome, tipo)
            )
            cat_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        else:
            cat_id = cat[0]
        conn.execute(
            """INSERT INTO financas_lancamentos
               (categoria_id, descricao, valor, tipo, data, pago, observacoes)
               VALUES (?,?,?,?,?,?,?)""",
            (cat_id, desc, valor, tipo, data, parse_bool(val(row, headers, COLS["pago"]) or "sim"),
             f"Notion: {path.name}"),
        )
        n += 1
    return n


def importar_projetos(conn, path: Path) -> int:
    headers, rows = ler_csv(path)
    n = 0
    for row in rows:
        titulo = val(row, headers, COLS["titulo"]) or val(row, headers, COLS["nome"])
        if not titulo:
            continue
        conn.execute(
            """INSERT INTO projetos (titulo, descricao, status, prioridade, data_prazo, tags, notas)
               VALUES (?,?,?,?,?,?,?)""",
            (
                titulo,
                val(row, headers, COLS["descricao"]) or None,
                (val(row, headers, COLS["status"]) or "ativo").lower(),
                (val(row, headers, COLS["prioridade"]) or "media").lower(),
                parse_data(val(row, headers, COLS["prazo"])),
                val(row, headers, COLS["tags"]) or None,
                f"Importado do Notion: {path.name}",
            ),
        )
        n += 1
    return n


def importar_tarefas(conn, path: Path) -> int:
    headers, rows = ler_csv(path)
    n = 0
    for row in rows:
        titulo = val(row, headers, COLS["titulo"]) or val(row, headers, COLS["nome"])
        if not titulo:
            continue
        conn.execute(
            """INSERT INTO tarefas (titulo, descricao, status, prioridade, data_prazo, notas)
               VALUES (?,?,?,?,?,?)""",
            (
                titulo,
                val(row, headers, COLS["descricao"]) or None,
                (val(row, headers, COLS["status"]) or "pendente").lower(),
                (val(row, headers, COLS["prioridade"]) or "media").lower(),
                parse_data(val(row, headers, COLS["prazo"])),
                f"Notion: {path.name}",
            ),
        )
        n += 1
    return n


def importar_youtube(conn, path: Path) -> int:
    headers, rows = ler_csv(path)
    n = 0
    for row in rows:
        titulo = val(row, headers, COLS["titulo"]) or val(row, headers, COLS["nome"])
        if not titulo:
            continue
        conn.execute(
            """INSERT INTO youtube_videos
               (titulo, descricao, status, data_publicacao, url, tags, notas)
               VALUES (?,?,?,?,?,?,?)""",
            (
                titulo,
                val(row, headers, COLS["descricao"]) or None,
                (val(row, headers, COLS["status"]) or "planejado").lower(),
                parse_data(val(row, headers, COLS["data"])),
                val(row, headers, COLS["url"]) or None,
                val(row, headers, COLS["tags"]) or None,
                f"Notion: {path.name}",
            ),
        )
        n += 1
    return n


def importar_agenda(conn, path: Path) -> int:
    headers, rows = ler_csv(path)
    n = 0
    for row in rows:
        titulo = val(row, headers, COLS["titulo"]) or val(row, headers, COLS["nome"])
        data = parse_data(val(row, headers, COLS["data"]))
        if not titulo or not data:
            continue
        pac = val(row, headers, COLS["paciente"])
        pid = paciente_por_nome(conn, pac) if pac else None
        conn.execute(
            """INSERT INTO agenda
               (titulo, data_inicio, hora_inicio, tipo, local, status, notas, paciente_id)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                titulo, data,
                val(row, headers, COLS["hora"]) or None,
                val(row, headers, COLS["tipo"]) or "geral",
                val(row, headers, COLS["local"]) or None,
                (val(row, headers, COLS["status"]) or "confirmado").lower(),
                val(row, headers, COLS["descricao"]) or f"Notion: {path.name}",
                pid,
            ),
        )
        n += 1
    return n


def importar_prontuarios(conn, path: Path) -> int:
    headers, rows = ler_csv(path)
    n = 0
    for row in rows:
        pac = val(row, headers, COLS["paciente"]) or val(row, headers, COLS["nome"])
        conteudo = val(row, headers, COLS["conteudo"]) or val(row, headers, COLS["descricao"])
        if not pac or not conteudo:
            continue
        pid = paciente_por_nome(conn, pac)
        if not pid:
            continue
        conn.execute(
            """INSERT INTO prontuarios
               (paciente_id, data_registro, tipo, titulo, conteudo)
               VALUES (?,?,?,?,?)""",
            (
                pid,
                parse_data(val(row, headers, COLS["data"])) or datetime.now().strftime("%Y-%m-%d"),
                (val(row, headers, COLS["tipo"]) or "evolucao").lower(),
                val(row, headers, COLS["titulo"]) or "Registro Notion",
                conteudo,
            ),
        )
        n += 1
    return n


def importar_notas_csv(conn, path: Path) -> int:
    headers, rows = ler_csv(path)
    n = 0
    for row in rows:
        conteudo = val(row, headers, COLS["conteudo"]) or val(row, headers, COLS["descricao"])
        titulo = val(row, headers, COLS["titulo"]) or val(row, headers, COLS["nome"])
        if not conteudo and not titulo:
            continue
        conn.execute(
            "INSERT INTO notas (titulo, conteudo, tags) VALUES (?,?,?)",
            (titulo or path.stem, conteudo or titulo, val(row, headers, COLS["tags"]) or "notion"),
        )
        n += 1
    return n


def importar_markdown(conn, pasta: Path) -> int:
    n = 0
    for md in sorted(pasta.rglob("*.md")):
        if md.name.startswith("_") or "node_modules" in str(md):
            continue
        texto = md.read_text(encoding="utf-8", errors="replace").strip()
        if not texto or len(texto) < 10:
            continue
        titulo = md.stem.replace("-", " ").replace("_", " ")
        # primeira linha # Título
        linhas = texto.splitlines()
        if linhas and linhas[0].startswith("#"):
            titulo = linhas[0].lstrip("# ").strip()
        conn.execute(
            "INSERT INTO notas (titulo, conteudo, tags) VALUES (?,?,?)",
            (titulo, texto, f"notion,{md.parent.name}"),
        )
        n += 1
    return n


IMPORTADORES = {
    "pacientes": importar_pacientes,
    "atendimentos": importar_atendimentos,
    "financas": importar_financas,
    "projetos": importar_projetos,
    "tarefas": importar_tarefas,
    "youtube": importar_youtube,
    "agenda": importar_agenda,
    "prontuarios": importar_prontuarios,
    "notas": importar_notas_csv,
}


def processar_csv(conn, path: Path, tipo: str | None) -> tuple[str, int]:
    headers, _ = ler_csv(path)
    if not tipo or tipo == "auto":
        tipo = detectar_tipo(path, headers)
    if not tipo:
        print(f"  ⚠ não detectado: {path.name} (colunas: {', '.join(headers[:6])}…)")
        return "?", 0
    fn = IMPORTADORES.get(tipo)
    if not fn:
        return tipo, 0
    n = fn(conn, path)
    print(f"  ✓ {tipo} ← {path.name} ({n} registros)")
    return tipo, n


def processar_pasta(conn, pasta: Path, tipo: str = "auto"):
    csvs = sorted(pasta.rglob("*.csv"))
    if not csvs:
        print(f"Nenhum CSV em {pasta}")
    total = 0
    for c in csvs:
        _, n = processar_csv(conn, c, tipo if tipo != "auto" else "auto")
        total += n
    mds = importar_markdown(conn, pasta)
    if mds:
        print(f"  ✓ notas ← {mds} arquivo(s) .md")
        total += mds
    print(f"→ {total} registro(s) importado(s)")


def extrair_zip(zip_path: Path) -> Path:
    tmp = TemporaryDirectory(prefix="notion-import-")
    dest = Path(tmp.name)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)
    return dest


def main():
    if not DB.exists():
        print("Banco não encontrado. Rode: python3 organizacao.py init")
        sys.exit(1)
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(0)

    modo = sys.argv[1].lower()
    alvo = Path(sys.argv[2])
    if not alvo.is_absolute():
        alvo = (BASE / alvo).resolve()

    tipo = sys.argv[3].lower() if len(sys.argv) > 3 else "auto"

    conn = conectar()

    if modo == "zip":
        if not alvo.exists():
            print(f"ZIP não encontrado: {alvo}")
            sys.exit(1)
        pasta = extrair_zip(alvo)
        processar_pasta(conn, pasta, tipo)
    elif modo == "pasta" or modo == "auto":
        if not alvo.is_dir():
            NOTION_DIR.mkdir(exist_ok=True)
            print(f"Pasta não encontrada: {alvo}")
            print(f"Coloque o export do Notion em: {NOTION_DIR}")
            sys.exit(1)
        processar_pasta(conn, alvo, tipo)
    elif modo == "markdown":
        n = importar_markdown(conn, alvo)
        print(f"→ {n} nota(s) de arquivos .md")
    elif modo in IMPORTADORES:
        if not alvo.is_file():
            print(f"Arquivo não encontrado: {alvo}")
            sys.exit(1)
        processar_csv(conn, alvo, modo)
    else:
        print(f"Modo desconhecido: {modo}")
        sys.exit(1)

    conn.commit()
    conn.close()
    print("Importação Notion concluída. Rode: python3 gerar_dashboard.py")


if __name__ == "__main__":
    main()
