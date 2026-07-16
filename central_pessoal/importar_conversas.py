#!/usr/bin/env python3
"""Importa PDFs de conversas como pacientes, atendimentos e prontuários."""

from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import app

MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}
PADRAO_ARQUIVO = re.compile(
    r"^(?P<nome>.+?)_(?P<dia>\d{1,2})_de_(?P<mes>[A-Za-zÀ-ÿ]+)_de_"
    r"(?P<ano>\d{4})_(?P<hora>\d{2})(?P<minuto>\d{2})(?:_\d+)?$"
)


@dataclass(frozen=True)
class Conversa:
    paciente: str
    data_hora: datetime
    nome_arquivo: str


def sem_acentos(texto: str) -> str:
    return "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caractere) != "Mn"
    )


def analisar_nome(caminho: Path) -> Conversa:
    correspondencia = PADRAO_ARQUIVO.match(caminho.stem)
    if not correspondencia:
        raise ValueError(
            "Nome fora do padrão: use Paciente_DD_de_mes_de_AAAA_HHMM.pdf"
        )
    partes = correspondencia.groupdict()
    mes_texto = partes["mes"].lower()
    mes = MESES.get(mes_texto) or MESES.get(sem_acentos(mes_texto))
    if not mes:
        raise ValueError(f"Mês inválido no arquivo: {partes['mes']}")
    data_hora = datetime(
        int(partes["ano"]),
        mes,
        int(partes["dia"]),
        int(partes["hora"]),
        int(partes["minuto"]),
    )
    paciente = re.sub(r"\s+", " ", partes["nome"].replace("_", " ")).strip()
    nome_arquivo = (
        f"{partes['nome']}_{int(partes['dia']):02d}_de_{mes_texto}_de_"
        f"{partes['ano']}_{partes['hora']}{partes['minuto']}.pdf"
    )
    return Conversa(paciente, data_hora, nome_arquivo)


def extrair_texto(caminho: Path) -> str:
    from pypdf import PdfReader

    leitor = PdfReader(caminho)
    paginas = [pagina.extract_text() or "" for pagina in leitor.pages]
    texto = "\n\n".join(pagina.strip() for pagina in paginas if pagina.strip()).strip()
    if not texto:
        raise ValueError(f"O PDF não contém texto extraível: {caminho.name}")
    return texto


def pasta_segura(nome: str) -> str:
    normalizado = sem_acentos(nome).replace(" ", "_")
    return re.sub(r"[^A-Za-z0-9_-]", "", normalizado) or "paciente"


def obter_paciente(connection: sqlite3.Connection, nome: str) -> int:
    existente = connection.execute(
        "SELECT id FROM pessoas WHERE tipo='paciente' AND nome = ? COLLATE NOCASE",
        (nome,),
    ).fetchone()
    if existente:
        return existente["id"]
    placeholder = connection.execute(
        """SELECT p.id FROM pessoas p
           WHERE p.tipo='paciente' AND p.nome GLOB 'Paciente [0-9][0-9]'
             AND NOT EXISTS (SELECT 1 FROM atendimentos a WHERE a.paciente_id=p.id)
             AND NOT EXISTS (SELECT 1 FROM prontuarios r WHERE r.paciente_id=p.id)
             AND NOT EXISTS (SELECT 1 FROM arquivos f WHERE f.pessoa_id=p.id)
           ORDER BY p.id LIMIT 1"""
    ).fetchone()
    if placeholder:
        connection.execute(
            """UPDATE pessoas SET nome=?, observacoes=?
               WHERE id=?""",
            (nome, "Cadastro criado pela importação de conversas.", placeholder["id"]),
        )
        return placeholder["id"]
    cursor = connection.execute(
        """INSERT INTO pessoas (nome, tipo, observacoes)
           VALUES (?, 'paciente', ?)""",
        (nome, "Cadastro criado pela importação de conversas."),
    )
    return cursor.lastrowid


def importar_arquivo(caminho: Path) -> dict:
    conversa = analisar_nome(caminho)
    texto = extrair_texto(caminho)
    destino_relativo = (
        Path("arquivos")
        / "pacientes"
        / pasta_segura(conversa.paciente)
        / conversa.nome_arquivo
    )
    destino = app.BASE_DIR / destino_relativo
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(caminho, destino)

    app.initialize()
    with app.connect() as connection:
        paciente_id = obter_paciente(connection, conversa.paciente)
        data_hora = conversa.data_hora.isoformat(timespec="minutes")
        data = conversa.data_hora.date().isoformat()
        titulo = conversa.data_hora.strftime("Sessão de %d/%m/%Y às %H:%M")

        atendimento = connection.execute(
            "SELECT id FROM atendimentos WHERE paciente_id=? AND data_hora=?",
            (paciente_id, data_hora),
        ).fetchone()
        if atendimento:
            atendimento_id = atendimento["id"]
        else:
            atendimento_id = connection.execute(
                """INSERT INTO atendimentos
                   (paciente_id, data_hora, tipo, status, observacoes)
                   VALUES (?, ?, 'consulta', 'realizado', ?)""",
                (paciente_id, data_hora, f"Importado de {conversa.nome_arquivo}"),
            ).lastrowid

        prontuario = connection.execute(
            """SELECT id FROM prontuarios
               WHERE paciente_id=? AND data_registro=? AND titulo=?""",
            (paciente_id, data, titulo),
        ).fetchone()
        if prontuario:
            prontuario_id = prontuario["id"]
            connection.execute(
                """UPDATE prontuarios
                   SET atendimento_id=?, conteudo=?, atualizado_em=CURRENT_TIMESTAMP
                   WHERE id=?""",
                (atendimento_id, texto, prontuario_id),
            )
        else:
            prontuario_id = connection.execute(
                """INSERT INTO prontuarios
                   (paciente_id, atendimento_id, data_registro, titulo, conteudo)
                   VALUES (?, ?, ?, ?, ?)""",
                (paciente_id, atendimento_id, data, titulo, texto),
            ).lastrowid

        area_id = connection.execute(
            "SELECT id FROM areas WHERE nome='Consultório'"
        ).fetchone()["id"]
        caminho_banco = destino_relativo.as_posix()
        documento = connection.execute(
            "SELECT id FROM arquivos WHERE caminho=?", (caminho_banco,)
        ).fetchone()
        if documento:
            arquivo_id = documento["id"]
        else:
            arquivo_id = connection.execute(
                """INSERT INTO arquivos
                   (area_id, pessoa_id, nome, caminho, categoria, descricao,
                    tags, data_documento)
                   VALUES (?, ?, ?, ?, 'prontuario', ?, 'sessão, conversa', ?)""",
                (
                    area_id,
                    paciente_id,
                    conversa.nome_arquivo,
                    caminho_banco,
                    titulo,
                    data,
                ),
            ).lastrowid
        connection.commit()

    return {
        "paciente": conversa.paciente,
        "data_hora": data_hora,
        "prontuario_id": prontuario_id,
        "atendimento_id": atendimento_id,
        "arquivo_id": arquivo_id,
        "arquivo": destino_relativo.as_posix(),
    }


def localizar_pdfs(origem: Path) -> list[Path]:
    if origem.is_file():
        return [origem] if origem.suffix.lower() == ".pdf" else []
    return sorted(caminho for caminho in origem.glob("*.pdf") if caminho.is_file())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importa conversas em PDF para os prontuários locais"
    )
    parser.add_argument("origem", type=Path, help="arquivo PDF ou pasta com PDFs")
    args = parser.parse_args()
    arquivos = localizar_pdfs(args.origem)
    if not arquivos:
        parser.error("Nenhum PDF encontrado na origem informada")
    importados = 0
    erros = 0
    for caminho in arquivos:
        try:
            resultado = importar_arquivo(caminho)
            print(
                f"OK  {resultado['paciente']} · {resultado['data_hora']} · "
                f"{resultado['arquivo']}"
            )
            importados += 1
        except Exception as error:
            print(f"ERRO  {caminho.name}: {error}")
            erros += 1
    print(f"\n{importados} conversa(s) importada(s); {erros} erro(s).")
    raise SystemExit(1 if erros else 0)


if __name__ == "__main__":
    main()
