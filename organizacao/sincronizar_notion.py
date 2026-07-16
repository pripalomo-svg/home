#!/usr/bin/env python3
"""Sincroniza pacientes, atendimentos e prontuários do Notion → organizacao.db

Modos (tenta nesta ordem):
  1. API do Notion — se existir token em NOTION_TOKEN ou notion/token.txt
  2. Export manual — se existir notion/Export.zip ou CSVs em notion/

Uso:
  python3 sincronizar_notion.py
  python3 sincronizar_notion.py --api
  python3 sincronizar_notion.py --export
  python3 sincronizar_notion.py --sem-paineis   # só importa, não gera HTML

Configuração API (uma vez):
  1. https://www.notion.so/my-integrations → New integration
  2. Copie o token → salve em organizacao/notion/token.txt
  3. No Notion, abra cada database → ⋯ → Connections → adicione a integração

Agendamento Windows (automático todo dia):
  Agendador de Tarefas → SINCRONIZAR_NOTION.bat → diário 07:00
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "organizacao.db"
NOTION_DIR = BASE / "notion"
CONFIG = NOTION_DIR / "config.json"
MAP_FILE = NOTION_DIR / "pacientes_map.json"
TOKEN_FILE = NOTION_DIR / "token.txt"
NOTION_VERSION = "2022-06-28"


def conectar():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.strip().lower())


def carregar_mapa() -> dict[str, str]:
    if MAP_FILE.exists():
        raw = json.loads(MAP_FILE.read_text(encoding="utf-8"))
        return {norm(k): v for k, v in raw.items()}
    return {}


def carregar_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def token_notion() -> str | None:
    t = os.environ.get("NOTION_TOKEN", "").strip()
    if t:
        return t
    if TOKEN_FILE.exists():
        t = TOKEN_FILE.read_text(encoding="utf-8").strip()
        return t or None
    return None


def match_codigo(texto: str, mapa: dict[str, str]) -> str | None:
    t = norm(texto)
    if not t:
        return None
    # nomes mais longos primeiro (evita "Maria" pegar antes de "Maria José")
    for alias, codigo in sorted(mapa.items(), key=lambda x: -len(x[0])):
        if alias and alias in t:
            return codigo
    return None


def paciente_id(conn, codigo: str) -> int | None:
    row = conn.execute("SELECT id FROM pacientes WHERE codigo = ?", (codigo,)).fetchone()
    return row[0] if row else None


# ── Notion API ────────────────────────────────────────────────────────────────

def notion_request(token: str, method: str, path: str, body: dict | None = None) -> dict:
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def query_database(token: str, database_id: str) -> list[dict]:
    resultados = []
    cursor = None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        data = notion_request(token, "POST", f"/databases/{database_id}/query", body)
        resultados.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return resultados


def prop_title(props: dict, name: str) -> str:
    p = props.get(name, {})
    if p.get("type") == "title":
        return "".join(t.get("plain_text", "") for t in p.get("title", []))
    return ""


def prop_rich(props: dict, name: str) -> str:
    p = props.get(name, {})
    t = p.get("type")
    if t == "rich_text":
        return "".join(x.get("plain_text", "") for x in p.get("rich_text", []))
    if t == "text":
        return p.get("text", {}).get("content", "")
    return ""


def prop_date(props: dict, name: str) -> str | None:
    p = props.get(name, {})
    if p.get("type") != "date" or not p.get("date"):
        return None
    start = p["date"].get("start", "")
    return start[:10] if start else None


def prop_select(props: dict, name: str) -> str:
    p = props.get(name, {})
    if p.get("type") == "multi_select":
        return ", ".join(x.get("name", "") for x in p.get("multi_select", []))
    if p.get("type") == "select" and p.get("select"):
        return p["select"].get("name", "")
    return ""


def atendimento_existe(conn, paciente_id_: int, data: str, notion_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM atendimentos WHERE paciente_id=? AND (notas LIKE ? OR (data=? AND notas LIKE ?))",
        (paciente_id_, f"%notion:{notion_id}%", data, f"%{notion_id[:8]}%"),
    ).fetchone()
    return row is not None


def prontuario_existe(conn, paciente_id_: int, notion_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM prontuarios WHERE paciente_id=? AND conteudo LIKE ?",
        (paciente_id_, f"%notion:{notion_id}%"),
    ).fetchone()
    return row is not None


def sync_api(conn, token: str, mapa: dict[str, str]) -> tuple[int, int]:
    cfg = carregar_config()
    n_at, n_pr = 0, 0

    # ── Agenda de Sessões → atendimentos
    db_agenda = cfg["databases"]["agenda_sessoes"]
    props_a = cfg["propriedades"]["agenda_sessoes"]
    print(f"  → Agenda de Sessões ({db_agenda[:8]}…)")
    for page in query_database(token, db_agenda):
        pid_notion = page["id"]
        props = page.get("properties", {})
        titulo = prop_title(props, props_a["titulo"])
        data = prop_date(props, props_a["data"])
        notas = prop_rich(props, props_a["notas"])
        if not titulo:
            continue
        codigo = match_codigo(titulo, mapa)
        if not codigo:
            continue
        pac_id = paciente_id(conn, codigo)
        if not pac_id:
            continue
        if not data:
            data = datetime.now().strftime("%Y-%m-%d")
        if atendimento_existe(conn, pac_id, data, pid_notion):
            continue
        modalidade = "online" if "online" in norm(titulo) else "presencial"
        conn.execute(
            """INSERT INTO atendimentos
               (paciente_id, data, tipo, modalidade, status, valor, pago, notas)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                pac_id, data, "sessao", modalidade, "realizado", 280, 1,
                f"notion:{pid_notion} | {titulo}" + (f" | {notas}" if notas else ""),
            ),
        )
        n_at += 1

    # ── Consolidação → prontuários
    db_cons = cfg["databases"]["consolidacao_anotacoes"]
    props_c = cfg["propriedades"]["consolidacao_anotacoes"]
    print(f"  → Consolidação de Anotações ({db_cons[:8]}…)")
    for page in query_database(token, db_cons):
        pid_notion = page["id"]
        props = page.get("properties", {})
        nome = prop_title(props, props_c["paciente"])
        data = prop_date(props, props_c["data"]) or datetime.now().strftime("%Y-%m-%d")
        resumo = prop_rich(props, props_c["resumo"])
        temas = prop_select(props, props_c["temas"])
        if not nome or not resumo:
            continue
        codigo = match_codigo(nome, mapa)
        if not codigo:
            continue
        pac_id = paciente_id(conn, codigo)
        if not pac_id or prontuario_existe(conn, pac_id, pid_notion):
            continue
        conteudo = resumo
        if temas:
            conteudo = f"Temas: {temas}\n\n{resumo}"
        conteudo = f"notion:{pid_notion}\n\n{conteudo}"
        conn.execute(
            """INSERT INTO prontuarios
               (paciente_id, data_registro, tipo, titulo, conteudo)
               VALUES (?,?,?,?,?)""",
            (
                pac_id, data, "evolucao", f"Sessão {data}", conteudo,
            ),
        )
        n_pr += 1

    return n_at, n_pr


def sync_export(conn) -> tuple[int, int]:
    """Usa export ZIP/pasta via importar_notion.py (modo auto)."""
    import importar_notion as ini

    zip_path = NOTION_DIR / "Export.zip"
    if zip_path.exists():
        print(f"  → Export ZIP: {zip_path.name}")
        pasta = ini.extrair_zip(zip_path)
        ini.processar_pasta(conn, pasta, "auto")
    elif any(NOTION_DIR.glob("*.csv")):
        print(f"  → CSVs em {NOTION_DIR}")
        ini.processar_pasta(conn, NOTION_DIR, "auto")
    else:
        print("  ⚠ Nenhum export em notion/ — exporte do Notion ou configure token API")
        return 0, 0
    n_at = conn.execute(
        "SELECT COUNT(*) FROM atendimentos WHERE notas LIKE '%notion%' OR notas LIKE '%Notion%'"
    ).fetchone()[0]
    n_pr = conn.execute(
        "SELECT COUNT(*) FROM prontuarios WHERE conteudo LIKE 'notion:%'"
    ).fetchone()[0]
    return n_at, n_pr


def gerar_paineis():
    subprocess.run([sys.executable, str(BASE / "gerar_dashboard.py")], check=True)
    subprocess.run([sys.executable, str(BASE / "gerar_investimentos.py")], check=True)


def salvar_log(n_at: int, n_pr: int, modo: str):
    log = NOTION_DIR / "ultima_sincronizacao.json"
    log.write_text(
        json.dumps(
            {
                "quando": datetime.now().isoformat(timespec="seconds"),
                "modo": modo,
                "novos_atendimentos": n_at,
                "novos_prontuarios": n_pr,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main():
    if not DB.exists():
        print("Banco não encontrado. Rode: python3 organizacao.py init")
        sys.exit(1)

    flags = set(sys.argv[1:])
    so_api = "--api" in flags
    so_export = "--export" in flags
    sem_paineis = "--sem-paineis" in flags

    print("══ Sincronização Notion → Organização ══\n")
    mapa = carregar_mapa()
    conn = conectar()
    n_at = n_pr = 0
    modo = "nenhum"

    token = token_notion()
    try:
        if token and not so_export:
            print("Modo: API do Notion")
            try:
                n_at, n_pr = sync_api(conn, token, mapa)
                modo = "api"
            except urllib.error.HTTPError as e:
                body = e.read().decode() if e.fp else ""
                print(f"  ✗ Erro API Notion ({e.code}): {body[:200]}")
                if not so_api:
                    print("  → Tentando export manual…")
                    n_at, n_pr = sync_export(conn)
                    modo = "export_fallback"
                else:
                    raise
        elif so_api:
            print("✗ Token não encontrado. Salve em notion/token.txt")
            print("  Veja: notion/COMO_CONFIGURAR_API.md")
            sys.exit(1)
        else:
            print("Modo: export manual (notion/)")
            n_at, n_pr = sync_export(conn)
            modo = "export"

        conn.commit()
        salvar_log(n_at, n_pr, modo)
        print(f"\n✓ Sincronização concluída ({modo})")
        print(f"  Novos atendimentos: {n_at}")
        print(f"  Novos prontuários:  {n_pr}")

        if not sem_paineis:
            print("\nGerando painéis…")
            gerar_paineis()
            print("✓ index.html e investimentos.html atualizados")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
