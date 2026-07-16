#!/usr/bin/env python3
"""Cria a base de dados SQLite (empresa.db) a partir de dados.json.

Os dados foram extraídos dos documentos societários da empresa
PRISCILA PALOMO PSICOLOGIA LTDA (contrato social, declarações de
desimpedimento, enquadramento ME e licenciamento).

Uso:
    python3 criar_banco.py
"""

import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "empresa.db"
JSON_PATH = BASE_DIR / "dados.json"

SCHEMA = """
DROP TABLE IF EXISTS documentos;
DROP TABLE IF EXISTS atividades;
DROP TABLE IF EXISTS socios;
DROP TABLE IF EXISTS empresas;

CREATE TABLE empresas (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_empresarial  TEXT NOT NULL,
    natureza_juridica TEXT,
    enquadramento     TEXT,
    capital_social    REAL,
    data_constituicao TEXT,
    prazo_duracao     TEXT,
    exercicio_social  TEXT,
    conselho_fiscal   TEXT,
    junta_comercial   TEXT,
    logradouro        TEXT,
    numero            TEXT,
    complemento       TEXT,
    bairro            TEXT,
    municipio         TEXT,
    uf                TEXT,
    cep               TEXT
);

CREATE TABLE socios (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id       INTEGER NOT NULL REFERENCES empresas(id),
    nome             TEXT NOT NULL,
    funcao           TEXT,
    nacionalidade    TEXT,
    estado_civil     TEXT,
    data_nascimento  TEXT,
    profissao        TEXT,
    cpf              TEXT,
    rg               TEXT,
    rg_orgao_emissor TEXT,
    cor_raca         TEXT,
    endereco         TEXT,
    participacao     TEXT
);

CREATE TABLE atividades (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER NOT NULL REFERENCES empresas(id),
    cnae       TEXT NOT NULL,
    descricao  TEXT,
    tipo       TEXT
);

CREATE TABLE documentos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id   INTEGER NOT NULL REFERENCES empresas(id),
    arquivo      TEXT NOT NULL,
    tipo         TEXT,
    descricao    TEXT,
    data         TEXT,
    local        TEXT,
    destinatario TEXT,
    paginas      INTEGER,
    assinado     INTEGER NOT NULL DEFAULT 0
);
"""


def main() -> None:
    dados = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)

    emp = dados["empresa"]
    end = emp["endereco"]
    cur = con.execute(
        """INSERT INTO empresas (
               nome_empresarial, natureza_juridica, enquadramento, capital_social,
               data_constituicao, prazo_duracao, exercicio_social, conselho_fiscal,
               junta_comercial, logradouro, numero, complemento, bairro,
               municipio, uf, cep
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            emp["nome_empresarial"], emp["natureza_juridica"], emp["enquadramento"],
            emp["capital_social"], emp["data_constituicao"], emp["prazo_duracao"],
            emp["exercicio_social"], emp["conselho_fiscal"], emp["junta_comercial"],
            end["logradouro"], end["numero"], end["complemento"], end["bairro"],
            end["municipio"], end["uf"], end["cep"],
        ),
    )
    empresa_id = cur.lastrowid

    for s in dados["socios"]:
        con.execute(
            """INSERT INTO socios (
                   empresa_id, nome, funcao, nacionalidade, estado_civil,
                   data_nascimento, profissao, cpf, rg, rg_orgao_emissor,
                   cor_raca, endereco, participacao
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                empresa_id, s["nome"], s["funcao"], s["nacionalidade"],
                s["estado_civil"], s["data_nascimento"], s["profissao"],
                s["cpf"], s["rg"], s["rg_orgao_emissor"], s["cor_raca"],
                s["endereco"], s["participacao"],
            ),
        )

    for a in dados["atividades"]:
        con.execute(
            "INSERT INTO atividades (empresa_id, cnae, descricao, tipo) VALUES (?, ?, ?, ?)",
            (empresa_id, a["cnae"], a["descricao"], a["tipo"]),
        )

    for d in dados["documentos"]:
        con.execute(
            """INSERT INTO documentos (
                   empresa_id, arquivo, tipo, descricao, data, local,
                   destinatario, paginas, assinado
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                empresa_id, d["arquivo"], d["tipo"], d["descricao"], d["data"],
                d["local"], d["destinatario"], d["paginas"], int(d["assinado"]),
            ),
        )

    con.commit()

    resumo = {
        tabela: con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        for tabela in ("empresas", "socios", "atividades", "documentos")
    }
    con.close()

    print(f"Base de dados criada em: {DB_PATH}")
    for tabela, total in resumo.items():
        print(f"  {tabela}: {total} registro(s)")


if __name__ == "__main__":
    main()
