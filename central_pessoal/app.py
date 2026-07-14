#!/usr/bin/env python3
"""Servidor local da Central Pessoal, sem dependências externas."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from datetime import date, datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DB_PATH = Path(os.environ.get("CENTRAL_DB_PATH", BASE_DIR / "central.db"))
SCHEMA_PATH = BASE_DIR / "schema.sql"

RESOURCE_CONFIG = {
    "projects": {
        "table": "projetos",
        "fields": ("area_id", "nome", "descricao", "status", "prioridade", "proxima_acao", "prazo"),
        "required": ("area_id", "nome"),
    },
    "tasks": {
        "table": "tarefas",
        "fields": ("projeto_id", "area_id", "titulo", "status", "prioridade", "prazo", "observacoes"),
        "required": ("titulo",),
    },
    "patients": {
        "table": "pessoas",
        "fields": ("nome", "telefone", "email", "observacoes"),
        "required": ("nome",),
        "fixed": {"tipo": "paciente"},
    },
    "appointments": {
        "table": "atendimentos",
        "fields": ("paciente_id", "data_hora", "tipo", "status", "valor", "observacoes"),
        "required": ("paciente_id", "data_hora"),
    },
    "records": {
        "table": "prontuarios",
        "fields": ("paciente_id", "atendimento_id", "data_registro", "titulo", "conteudo"),
        "required": ("paciente_id", "data_registro", "titulo", "conteudo"),
    },
    "finances": {
        "table": "lancamentos",
        "fields": ("data", "descricao", "tipo", "categoria", "valor", "status", "pessoa_id", "projeto_id", "observacoes"),
        "required": ("data", "descricao", "tipo", "categoria", "valor"),
    },
    "files": {
        "table": "arquivos",
        "fields": ("area_id", "projeto_id", "pessoa_id", "nome", "caminho", "categoria", "descricao", "tags", "data_documento"),
        "required": ("area_id", "nome", "caminho"),
    },
}


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(seed: bool = True) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        if seed and not connection.execute("SELECT 1 FROM areas LIMIT 1").fetchone():
            seed_template(connection)


def seed_template(connection: sqlite3.Connection) -> None:
    areas = [
        ("Projetos", "◫", "#5b6cff", "Projetos pessoais e profissionais"),
        ("Consultório", "✚", "#12a879", "Pacientes, agenda e prontuários"),
        ("Finanças", "↗", "#e59b2f", "Receitas, despesas e compromissos"),
        ("YouTube", "▶", "#ef5b5b", "Pautas, produção e publicação"),
        ("Família", "⌂", "#9a6be8", "Rotina familiar e documentos"),
        ("Arquivos", "⌁", "#4c8fac", "Índice geral de documentos"),
    ]
    connection.executemany(
        "INSERT INTO areas (nome, icone, cor, descricao) VALUES (?, ?, ?, ?)", areas
    )
    connection.executemany(
        "INSERT INTO pessoas (nome, tipo) VALUES (?, ?)",
        [("Você", "eu"), ("Esposa", "conjuge"), ("Filho 1", "filho"), ("Filho 2", "filho")]
        + [(f"Paciente {number:02d}", "paciente") for number in range(1, 21)],
    )
    area_ids = {
        row["nome"]: row["id"] for row in connection.execute("SELECT id, nome FROM areas")
    }
    projects = [
        (area_ids["YouTube"], "Canal no YouTube", "Planejamento editorial do canal", "em_andamento", "alta", "Definir a próxima pauta"),
        (area_ids["Consultório"], "Organização do consultório", "Agenda e acompanhamento dos pacientes", "em_andamento", "alta", "Completar os cadastros dos pacientes"),
        (area_ids["Finanças"], "Planejamento financeiro", "Visão mensal da vida financeira", "planejado", "alta", "Registrar despesas fixas"),
        (area_ids["Família"], "Rotina da família", "Compromissos e documentos familiares", "planejado", "media", "Reunir os próximos compromissos"),
        (area_ids["Projetos"], "Caixa de entrada de projetos", "Lugar para capturar ideias antes de organizá-las", "ideia", "media", "Revisar as ideias"),
    ]
    connection.executemany(
        """INSERT INTO projetos
           (area_id, nome, descricao, status, prioridade, proxima_acao)
           VALUES (?, ?, ?, ?, ?, ?)""",
        projects,
    )
    connection.executemany(
        "INSERT INTO tarefas (area_id, titulo, prioridade) VALUES (?, ?, ?)",
        [
            (area_ids["Consultório"], "Personalizar os nomes dos 20 pacientes", "alta"),
            (area_ids["Finanças"], "Cadastrar receitas e despesas recorrentes", "alta"),
            (area_ids["YouTube"], "Criar calendário de conteúdo", "media"),
            (area_ids["Arquivos"], "Indexar as pastas mais importantes", "media"),
        ],
    )


def rows(connection: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict]:
    return [dict(row) for row in connection.execute(query, params).fetchall()]


def dashboard(connection: sqlite3.Connection) -> dict:
    today = date.today().isoformat()
    month = today[:7]
    totals = dict(
        connection.execute(
            """SELECT
                (SELECT COUNT(*) FROM projetos WHERE status NOT IN ('concluido','arquivado')) projetos,
                (SELECT COUNT(*) FROM tarefas WHERE status IN ('aberta','fazendo')) tarefas,
                (SELECT COUNT(*) FROM pessoas WHERE tipo='paciente' AND ativo=1) pacientes,
                (SELECT COUNT(*) FROM arquivos) arquivos"""
        ).fetchone()
    )
    finance = dict(
        connection.execute(
            """SELECT
               COALESCE(SUM(CASE WHEN tipo='receita' THEN valor ELSE 0 END), 0) receitas,
               COALESCE(SUM(CASE WHEN tipo='despesa' THEN valor ELSE 0 END), 0) despesas
               FROM lancamentos WHERE substr(data, 1, 7)=?""",
            (month,),
        ).fetchone()
    )
    return {
        "totals": totals,
        "finance": finance,
        "areas": rows(connection, "SELECT * FROM areas ORDER BY id"),
        "next_appointments": rows(
            connection,
            """SELECT a.*, p.nome paciente FROM atendimentos a
               JOIN pessoas p ON p.id=a.paciente_id
               WHERE a.data_hora>=? AND a.status NOT IN ('cancelado','realizado')
               ORDER BY a.data_hora LIMIT 6""",
            (today,),
        ),
        "priority_tasks": rows(
            connection,
            """SELECT t.*, a.nome area FROM tarefas t
               LEFT JOIN areas a ON a.id=t.area_id
               WHERE t.status IN ('aberta','fazendo')
               ORDER BY CASE t.prioridade WHEN 'alta' THEN 0 WHEN 'media' THEN 1 ELSE 2 END,
                        COALESCE(t.prazo, '9999-12-31') LIMIT 6""",
        ),
        "recent_projects": rows(
            connection,
            """SELECT p.*, a.nome area, a.cor area_cor FROM projetos p
               JOIN areas a ON a.id=p.area_id
               WHERE p.status!='arquivado' ORDER BY p.atualizado_em DESC LIMIT 6""",
        ),
    }


def list_resource(connection: sqlite3.Connection, resource: str, query: dict) -> list[dict]:
    search = query.get("q", [""])[0].strip()
    if resource == "projects":
        sql = """SELECT p.*, a.nome area, a.cor area_cor FROM projetos p
                 JOIN areas a ON a.id=p.area_id"""
        searchable = "p.nome || ' ' || COALESCE(p.descricao,'') || ' ' || COALESCE(p.proxima_acao,'')"
        order = " ORDER BY p.atualizado_em DESC"
    elif resource == "patients":
        sql = "SELECT * FROM pessoas WHERE tipo='paciente' AND ativo=1"
        searchable = "nome || ' ' || COALESCE(telefone,'') || ' ' || COALESCE(email,'')"
        order = " ORDER BY nome"
    elif resource == "appointments":
        sql = """SELECT a.*, p.nome paciente FROM atendimentos a
                 JOIN pessoas p ON p.id=a.paciente_id"""
        searchable = "p.nome || ' ' || COALESCE(a.observacoes,'')"
        order = " ORDER BY a.data_hora DESC"
    elif resource == "records":
        sql = """SELECT r.*, p.nome paciente FROM prontuarios r
                 JOIN pessoas p ON p.id=r.paciente_id"""
        searchable = "p.nome || ' ' || r.titulo || ' ' || r.conteudo"
        order = " ORDER BY r.data_registro DESC"
    elif resource == "finances":
        sql = """SELECT l.*, p.nome pessoa, pr.nome projeto FROM lancamentos l
                 LEFT JOIN pessoas p ON p.id=l.pessoa_id
                 LEFT JOIN projetos pr ON pr.id=l.projeto_id"""
        searchable = "l.descricao || ' ' || l.categoria || ' ' || COALESCE(l.observacoes,'')"
        order = " ORDER BY l.data DESC, l.id DESC"
    elif resource == "files":
        sql = """SELECT f.*, a.nome area, p.nome projeto, pe.nome pessoa FROM arquivos f
                 JOIN areas a ON a.id=f.area_id
                 LEFT JOIN projetos p ON p.id=f.projeto_id
                 LEFT JOIN pessoas pe ON pe.id=f.pessoa_id"""
        searchable = "f.nome || ' ' || f.caminho || ' ' || COALESCE(f.tags,'') || ' ' || COALESCE(f.descricao,'')"
        order = " ORDER BY f.criado_em DESC"
    else:
        sql = """SELECT t.*, a.nome area, p.nome projeto FROM tarefas t
                 LEFT JOIN areas a ON a.id=t.area_id
                 LEFT JOIN projetos p ON p.id=t.projeto_id"""
        searchable = "t.titulo || ' ' || COALESCE(t.observacoes,'')"
        order = " ORDER BY t.status, COALESCE(t.prazo,'9999-12-31')"
    params: tuple = ()
    if search:
        sql += f" WHERE ({searchable}) LIKE ?"
        params = (f"%{search}%",)
    return rows(connection, sql + order, params)


def create_resource(connection: sqlite3.Connection, resource: str, data: dict) -> dict:
    config = RESOURCE_CONFIG[resource]
    missing = [field for field in config["required"] if data.get(field) in (None, "")]
    if missing:
        raise ValueError(f"Campos obrigatórios: {', '.join(missing)}")
    if resource == "appointments":
        try:
            datetime.fromisoformat(str(data["data_hora"]))
        except (TypeError, ValueError) as error:
            raise ValueError("Data ou horário do atendimento inválido") from error
    values = {field: data[field] for field in config["fields"] if field in data}
    values.update(config.get("fixed", {}))
    columns = list(values)
    placeholders = ", ".join("?" for _ in columns)
    cursor = connection.execute(
        f"INSERT INTO {config['table']} ({', '.join(columns)}) VALUES ({placeholders})",
        tuple(values[column] for column in columns),
    )
    connection.commit()
    return dict(
        connection.execute(
            f"SELECT * FROM {config['table']} WHERE id=?", (cursor.lastrowid,)
        ).fetchone()
    )


def update_resource(connection: sqlite3.Connection, resource: str, item_id: int, data: dict) -> dict:
    config = RESOURCE_CONFIG[resource]
    values = {field: data[field] for field in config["fields"] if field in data}
    if not values:
        raise ValueError("Nenhum campo válido para atualizar")
    assignments = ", ".join(f"{field}=?" for field in values)
    if config["table"] == "projetos":
        assignments += ", atualizado_em=CURRENT_TIMESTAMP"
    cursor = connection.execute(
        f"UPDATE {config['table']} SET {assignments} WHERE id=?",
        (*values.values(), item_id),
    )
    if not cursor.rowcount:
        raise LookupError("Registro não encontrado")
    connection.commit()
    return dict(
        connection.execute(
            f"SELECT * FROM {config['table']} WHERE id=?", (item_id,)
        ).fetchone()
    )


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    def send_json(self, data, status=HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def api_parts(self) -> tuple[list[str], dict]:
        parsed = urlparse(self.path)
        return [part for part in parsed.path.split("/") if part], parse_qs(parsed.query)

    def do_GET(self) -> None:
        parts, query = self.api_parts()
        if not parts or parts[0] != "api":
            return super().do_GET()
        try:
            with connect() as connection:
                if parts[1:] == ["dashboard"]:
                    return self.send_json(dashboard(connection))
                if len(parts) == 2 and parts[1] in RESOURCE_CONFIG:
                    return self.send_json(list_resource(connection, parts[1], query))
                if parts[1:] == ["people"]:
                    return self.send_json(rows(connection, "SELECT * FROM pessoas WHERE ativo=1 ORDER BY tipo, nome"))
                if parts[1:] == ["areas"]:
                    return self.send_json(rows(connection, "SELECT * FROM areas ORDER BY id"))
            self.send_json({"error": "Rota não encontrada"}, HTTPStatus.NOT_FOUND)
        except (IndexError, sqlite3.Error) as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)

    def do_POST(self) -> None:
        self.mutate("create")

    def do_PATCH(self) -> None:
        self.mutate("update")

    def mutate(self, action: str) -> None:
        parts, _ = self.api_parts()
        try:
            if len(parts) < 2 or parts[0] != "api" or parts[1] not in RESOURCE_CONFIG:
                return self.send_json({"error": "Rota não encontrada"}, HTTPStatus.NOT_FOUND)
            data = self.read_json()
            with connect() as connection:
                if action == "create" and len(parts) == 2:
                    result = create_resource(connection, parts[1], data)
                    return self.send_json(result, HTTPStatus.CREATED)
                if action == "update" and len(parts) == 3:
                    result = update_resource(connection, parts[1], int(parts[2]), data)
                    return self.send_json(result)
            self.send_json({"error": "Rota não encontrada"}, HTTPStatus.NOT_FOUND)
        except (ValueError, json.JSONDecodeError, sqlite3.IntegrityError) as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except LookupError as error:
            self.send_json({"error": str(error)}, HTTPStatus.NOT_FOUND)


def main() -> None:
    parser = argparse.ArgumentParser(description="Central Pessoal local")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--init-only", action="store_true")
    parser.add_argument("--no-seed", action="store_true")
    args = parser.parse_args()
    initialize(seed=not args.no_seed)
    if args.init_only:
        print(f"Banco preparado em {DB_PATH}")
        return
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Central Pessoal disponível em http://{args.host}:{args.port}")
    print("Os dados ficam somente neste computador. Pressione Ctrl+C para encerrar.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
