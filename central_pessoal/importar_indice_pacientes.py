#!/usr/bin/env python3
"""Separa um índice consolidado de sessões em prontuários individuais."""

from __future__ import annotations

import argparse
import re
import shutil
import unicodedata
from datetime import date
from pathlib import Path

import app
from importar_conversas import extrair_texto

PACIENTES = [
    ("Maria José", ("Maria José",)),
    ("Beatriz Jubilut", ("Beatriz Jubilut", "Beatriz", "Bia")),
    ("Luigi Caloi", ("Luigi Caloi", "Luigi")),
    ("Fernando de Castro", ("Fernando de Castro",)),
    ("Felipe Zandona Barbosa", ("Felipe Zandona Barbosa", "Felipe", "Fê")),
    ("Monica Mattos Fernandes", ("Monica Mattos Fernandes", "Monica Mattos", "Monica")),
    ("Luís Octavio Almeida", ("Luís Octavio Almeida",)),
    ("Gabriel Gasparetto", ("Gabriel Gasparetto", "Gabriel")),
    ("Bruna Galon Paiva", ("Bruna Galon Paiva", "Bruna")),
    ("Luisa Cabalin", ("Luisa Cabalin",)),
    ("Clara", ("Clara",)),
    ("Lívia Padiar", ("Lívia Padiar", "Lívia")),
    ("Sthephanie", ("Sthephanie", "Stephanie", "Stéphanie")),
    ("Claudia", ("Claudia", "Cláudia")),
    ("Márcia", ("Márcia",)),
    ("Gabrielli", ("Gabrielli",)),
    ("Larissa", ("Larissa",)),
    ("Rochele", ("Rochele", "Rochelle")),
]

CABECALHOS = {
    "beatriz bia": "Beatriz Jubilut",
    "bruna": "Bruna Galon Paiva",
    "clara": "Clara",
    "claudia": "Claudia",
    "fernando de castro": "Fernando de Castro",
    "felipe fe": "Felipe Zandona Barbosa",
    "gabriel": "Gabriel Gasparetto",
    "larissa": "Larissa",
    "livia": "Lívia Padiar",
    "luigi luigi caloi": "Luigi Caloi",
    "luisa cabalin": "Luisa Cabalin",
    "luis octavio almeida": "Luís Octavio Almeida",
    "marcia": "Márcia",
    "maria jose": "Maria José",
    "monica monica mattos": "Monica Mattos Fernandes",
    "rochele ro": "Rochele",
    "sthephanie": "Sthephanie",
}


def normalizar(texto: str) -> str:
    sem_controles = "".join(
        caractere if unicodedata.category(caractere)[0] != "C" else " "
        for caractere in texto
    )
    sem_acentos = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", sem_controles)
        if unicodedata.category(caractere) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", sem_acentos.lower()).strip()


def limpar_linha(linha: str) -> str:
    return re.sub(r"\s+", " ", linha.replace("\x00", " ")).strip()


def separar_por_paciente(texto: str) -> dict[str, list[str]]:
    secoes = {nome: [] for nome, _ in PACIENTES}
    linhas = [limpar_linha(linha) for linha in texto.splitlines()]
    inicio = next(
        (indice for indice, linha in enumerate(linhas) if normalizar(linha) == "pacientes"),
        None,
    )
    if inicio is None:
        raise ValueError("A seção 'Pacientes' não foi encontrada no PDF")

    paciente_atual = None
    for linha in linhas[inicio + 1 :]:
        chave = normalizar(linha)
        if chave.startswith("pac pacientes sessoes por pessoa"):
            continue
        if chave.startswith("pac") and "conversas" in chave:
            break
        if chave == "sessoes sem paciente identificado":
            paciente_atual = None
            continue
        cabecalho = CABECALHOS.get(chave)
        if cabecalho:
            paciente_atual = cabecalho
            continue
        if not paciente_atual or not linha:
            continue
        if re.match(r"^-- \d+ of \d+ --$", linha):
            continue
        if re.match(r"^Pacientes .+ \d+$", linha):
            continue
        secoes[paciente_atual].append(linha)
    return secoes


def encontrar_ou_reservar_paciente(connection, nome: str, aliases: tuple[str, ...]) -> int:
    placeholders = ",".join("?" for _ in aliases)
    existente = connection.execute(
        f"""SELECT id, nome FROM pessoas
            WHERE tipo='paciente' AND nome COLLATE NOCASE IN ({placeholders})
            ORDER BY CASE WHEN nome=? THEN 0 ELSE 1 END LIMIT 1""",
        (*aliases, nome),
    ).fetchone()
    if existente:
        if existente["nome"] != nome:
            connection.execute(
                "UPDATE pessoas SET nome=? WHERE id=?", (nome, existente["id"])
            )
        return existente["id"]

    livre = connection.execute(
        """SELECT p.id FROM pessoas p
           WHERE p.tipo='paciente' AND p.nome GLOB 'Paciente [0-9][0-9]'
             AND NOT EXISTS (SELECT 1 FROM prontuarios r WHERE r.paciente_id=p.id)
             AND NOT EXISTS (SELECT 1 FROM atendimentos a WHERE a.paciente_id=p.id)
             AND NOT EXISTS (SELECT 1 FROM arquivos f WHERE f.pessoa_id=p.id)
           ORDER BY p.id LIMIT 1"""
    ).fetchone()
    if livre:
        connection.execute(
            "UPDATE pessoas SET nome=?, observacoes=? WHERE id=?",
            (nome, "Cadastro criado pelo índice consolidado de sessões.", livre["id"]),
        )
        return livre["id"]
    return connection.execute(
        """INSERT INTO pessoas (nome, tipo, observacoes)
           VALUES (?, 'paciente', ?)""",
        (nome, "Cadastro criado pelo índice consolidado de sessões."),
    ).lastrowid


def conteudo_individual(nome: str, linhas: list[str], fonte: str) -> str:
    introducao = (
        f"Fonte: {fonte}\n\n"
        "Este documento de origem contém apenas um índice de títulos e datas de "
        "sessões; não contém transcrições nem evolução clínica.\n\n"
    )
    if not linhas:
        return introducao + f"Nenhuma sessão detalhada foi listada para {nome}."
    return introducao + "Referências atribuídas a este paciente:\n\n- " + "\n- ".join(linhas)


def importar_indice(caminho: Path) -> dict:
    texto = extrair_texto(caminho)
    secoes = separar_por_paciente(texto)
    app.initialize()
    nome_destino = "Pacientes_Sessoes_por_pessoa.pdf"
    destino_relativo = Path("arquivos") / "pacientes" / "_indices" / nome_destino
    destino = app.BASE_DIR / destino_relativo
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(caminho, destino)

    registros = []
    with app.connect() as connection:
        area_id = connection.execute(
            "SELECT id FROM areas WHERE nome='Consultório'"
        ).fetchone()["id"]
        caminho_banco = destino_relativo.as_posix()
        documento = connection.execute(
            "SELECT id FROM arquivos WHERE caminho=?", (caminho_banco,)
        ).fetchone()
        if documento:
            arquivo_id = documento["id"]
            connection.execute(
                "UPDATE arquivos SET descricao=?, data_documento=? WHERE id=?",
                (
                    "Índice consolidado de sessões por paciente",
                    date.today().isoformat(),
                    arquivo_id,
                ),
            )
        else:
            arquivo_id = connection.execute(
                """INSERT INTO arquivos
                   (area_id, nome, caminho, categoria, descricao, tags, data_documento)
                   VALUES (?, ?, ?, 'referencia', ?, 'pacientes, sessões, índice', ?)""",
                (
                    area_id,
                    nome_destino,
                    caminho_banco,
                    "Índice consolidado de sessões por paciente",
                    date.today().isoformat(),
                ),
            ).lastrowid

        for nome, aliases in PACIENTES:
            paciente_id = encontrar_ou_reservar_paciente(connection, nome, aliases)
            titulo = "Índice consolidado de sessões"
            conteudo = conteudo_individual(nome, secoes[nome], nome_destino)
            existente = connection.execute(
                "SELECT id FROM prontuarios WHERE paciente_id=? AND titulo=?",
                (paciente_id, titulo),
            ).fetchone()
            if existente:
                prontuario_id = existente["id"]
                connection.execute(
                    """UPDATE prontuarios SET conteudo=?, atualizado_em=CURRENT_TIMESTAMP
                       WHERE id=?""",
                    (conteudo, prontuario_id),
                )
            else:
                prontuario_id = connection.execute(
                    """INSERT INTO prontuarios
                       (paciente_id, data_registro, titulo, conteudo)
                       VALUES (?, ?, ?, ?)""",
                    (paciente_id, date.today().isoformat(), titulo, conteudo),
                ).lastrowid
            registros.append(
                {
                    "paciente": nome,
                    "paciente_id": paciente_id,
                    "prontuario_id": prontuario_id,
                    "referencias": len(secoes[nome]),
                }
            )
        connection.commit()

    return {
        "pacientes": registros,
        "arquivo_id": arquivo_id,
        "arquivo": destino_relativo.as_posix(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importa índice consolidado para prontuários individuais"
    )
    parser.add_argument("arquivo", type=Path)
    args = parser.parse_args()
    resultado = importar_indice(args.arquivo)
    for item in resultado["pacientes"]:
        print(f"OK  {item['paciente']} · {item['referencias']} referência(s)")
    print(
        f"\n{len(resultado['pacientes'])} prontuário(s) atualizado(s) · "
        f"{resultado['arquivo']}"
    )


if __name__ == "__main__":
    main()
