#!/usr/bin/env python3
"""Registra dados extraídos de foto/print no banco organizacao.db.

Uso:
  python3 registrar_foto.py dados/foto_registro.json
  python3 registrar_foto.py dados/foto_registro.json --sem-paineis
"""

from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "organizacao.db"
LOG = BASE / "ultima_atualizacao.json"

MODULOS_CSV = {
    "financas": BASE / "templates" / "financas.csv",
    "pacientes": BASE / "templates" / "pacientes.csv",
    "atendimentos": BASE / "templates" / "atendimentos.csv",
    "agenda": BASE / "templates" / "agenda.csv",
}


def conectar():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def salvar_log(payload: dict, resultado: dict):
    entrada = {
        "quando": datetime.now().isoformat(timespec="seconds"),
        "fonte": payload.get("fonte", "foto"),
        "descricao": payload.get("descricao_foto", ""),
        "modulo": payload.get("modulo"),
        "registros": resultado.get("registros", []),
        "pendentes": resultado.get("pendentes", []),
    }
    historico = []
    if LOG.exists():
        try:
            historico = json.loads(LOG.read_text(encoding="utf-8"))
            if not isinstance(historico, list):
                historico = [historico]
        except json.JSONDecodeError:
            historico = []
    historico.insert(0, entrada)
    LOG.write_text(json.dumps(historico[:50], ensure_ascii=False, indent=2), encoding="utf-8")


def registrar_investimento(conn, reg: dict) -> str:
    nome = reg.get("nome") or "Investimento"
    valor = reg.get("valor_atual")
    if valor is None:
        valor = 0.0
    else:
        valor = float(str(valor).replace(",", "."))
    protocolo = reg.get("protocolo") or ""
    if not protocolo and reg.get("notas"):
        for parte in str(reg["notas"]).split():
            if parte.isdigit() and len(parte) >= 6:
                protocolo = parte
                break
    existente = None
    if protocolo:
        existente = conn.execute(
            "SELECT id FROM investimentos WHERE notas LIKE ?", (f"%{protocolo}%",)
        ).fetchone()
    if not existente:
        existente = conn.execute("SELECT id FROM investimentos WHERE nome = ?", (nome,)).fetchone()
    params = (
        nome,
        reg.get("tipo") or "outro",
        reg.get("instituicao"),
        reg.get("ticker"),
        reg.get("codigo_ativo"),
        valor,
        reg.get("valor_aplicado") or valor,
        reg.get("quantidade"),
        reg.get("preco_unitario"),
        reg.get("taxa_anual"),
        reg.get("data_contratacao"),
        reg.get("data_atualizacao") or datetime.now().strftime("%Y-%m-%d"),
        reg.get("aporte_mensal") or 0,
        reg.get("cor") or "#3b82f6",
        reg.get("notas"),
    )
    if existente:
        conn.execute(
            """UPDATE investimentos SET nome=?, tipo=?, instituicao=?, ticker=?, codigo_ativo=?,
               valor_atual=?, valor_aplicado=?, quantidade=?, preco_unitario=?, taxa_anual=?,
               data_contratacao=?, data_atualizacao=?, aporte_mensal=?, cor=?, notas=?, ativo=1
               WHERE id=?""",
            (*params, existente[0]),
        )
    else:
        conn.execute(
            """INSERT INTO investimentos
               (nome, tipo, instituicao, ticker, codigo_ativo, valor_atual, valor_aplicado,
                quantidade, preco_unitario, taxa_anual, data_contratacao, data_atualizacao,
                aporte_mensal, cor, notas)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            params,
        )
    return nome


def append_csv(modulo: str, registros: list[dict]) -> list[str]:
    path = MODULOS_CSV[modulo]
    if not path.exists():
        raise ValueError(f"CSV não encontrado: {path}")
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        headers = [h for h in (reader.fieldnames or []) if h]
        rows = [{k: (row.get(k) or "") for k in headers} for row in reader]

    adicionados = []
    for reg in registros:
        linha = {h: "" for h in headers}
        for k, v in reg.items():
            if k in linha and v is not None:
                linha[k] = str(v)
        chave = (linha.get("nome") or linha.get("titulo") or linha.get("descricao"), linha.get("notas"))
        if any(
            (r.get("nome") or r.get("titulo") or r.get("descricao"), r.get("notas")) == chave
            for r in rows
        ):
            continue
        rows.append(linha)
        adicionados.append(linha.get("nome") or linha.get("titulo") or linha.get("descricao") or "(registro)")

    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return adicionados


def registrar_nota(conn, reg: dict):
    titulo = reg.get("titulo") or reg.get("nome") or "Registro de foto"
    conteudo = reg.get("conteudo") or reg.get("notas") or json.dumps(reg, ensure_ascii=False)
    conn.execute(
        "INSERT INTO notas (titulo, conteudo, area_id, fixada) VALUES (?,?,?,0)",
        (titulo, conteudo, None),
    )


def registrar_arquivo(conn, reg: dict):
    conn.execute(
        """INSERT INTO arquivos (titulo, caminho, categoria, data_arquivo, tipo_arquivo, descricao)
           VALUES (?,?,?,?,?,?)""",
        (
            reg.get("titulo") or "Documento de foto",
            reg.get("caminho") or "documentos/capturas/",
            reg.get("categoria") or "financeiro",
            reg.get("data_arquivo") or datetime.now().strftime("%Y-%m-%d"),
            reg.get("tipo_arquivo") or "img",
            reg.get("descricao") or reg.get("notas"),
        ),
    )


def importar_modulo(modulo: str):
    py = sys.executable
    subprocess.run([py, str(BASE / "importar_dados.py"), modulo, str(MODULOS_CSV[modulo])], check=True)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.is_absolute():
        path = BASE / path
    sem_paineis = "--sem-paineis" in sys.argv

    payload = json.loads(path.read_text(encoding="utf-8"))
    modulo = payload.get("modulo", "nota")
    registros = payload.get("registros", [])
    if not registros:
        print("Nenhum registro no JSON")
        sys.exit(1)

    if not DB.exists():
        subprocess.run([sys.executable, str(BASE / "organizacao.py"), "init"], check=True)

    resultado = {"registros": [], "pendentes": []}
    conn = conectar()

    try:
        if modulo == "investimentos":
            for reg in registros:
                nome = registrar_investimento(conn, reg)
                resultado["registros"].append(nome)
                if reg.get("valor_atual") is None:
                    resultado["pendentes"].append(f"valor de {nome}")
        elif modulo in MODULOS_CSV:
            nomes = append_csv(modulo, registros)
            importar_modulo(modulo)
            resultado["registros"] = nomes
        elif modulo == "nota":
            for reg in registros:
                registrar_nota(conn, reg)
                resultado["registros"].append(reg.get("titulo") or "nota")
        elif modulo == "arquivo":
            for reg in registros:
                registrar_arquivo(conn, reg)
                resultado["registros"].append(reg.get("titulo") or "arquivo")
        else:
            raise ValueError(f"Módulo desconhecido: {modulo}")

        conn.commit()
        salvar_log(payload, resultado)

        if not sem_paineis:
            subprocess.run([sys.executable, str(BASE / "gerar_dashboard.py")], check=True)
            if modulo == "investimentos":
                subprocess.run([sys.executable, str(BASE / "gerar_investimentos.py")], check=True)

        print(f"✓ Módulo: {modulo}")
        print(f"  Registrados: {len(resultado['registros'])}")
        if resultado["pendentes"]:
            print(f"  Pendentes: {', '.join(resultado['pendentes'])}")
        print(f"  Log: {LOG.name}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
