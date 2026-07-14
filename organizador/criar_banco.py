#!/usr/bin/env python3
"""Cria (ou recria) o banco organizador.db a partir do schema.sql.

Uso:
    python3 criar_banco.py            # cria o banco vazio (só áreas + família)
    python3 criar_banco.py --exemplo  # cria com 20 pacientes de exemplo,
                                      # prontuários, agenda, finanças e vídeos

Os 20 pacientes de exemplo usam nomes fictícios ("Paciente 01"...) para você
substituir pelos nomes reais direto no painel (painel.html) ou via SQL.
"""

import argparse
import sqlite3
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "organizador.db"
SCHEMA = BASE / "schema.sql"

AREAS = [
    ("Financeiro", "💰", "#0fa968"),
    ("YouTube", "🎬", "#e14b5a"),
    ("Consultório", "🩺", "#2f6fed"),
    ("Família", "👨‍👩‍👧‍👦", "#e8930c"),
    ("Pessoal", "🌱", "#7c5cde"),
]

FAMILIA = [
    ("Esposa", "esposa", None, "Editar com o nome real"),
    ("Filho 1", "filho", None, "Editar com o nome real"),
    ("Filho 2", "filho", None, "Editar com o nome real"),
]


def criar(exemplo: bool) -> None:
    if DB.exists():
        DB.unlink()
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))

    conn.executemany("INSERT INTO areas (nome, icone, cor) VALUES (?,?,?)", AREAS)
    conn.executemany(
        "INSERT INTO familia_membros (nome, parentesco, data_nascimento, notas) VALUES (?,?,?,?)",
        FAMILIA,
    )

    if exemplo:
        popular_exemplo(conn)

    conn.commit()
    conn.close()
    print(f"Banco criado em {DB}" + (" (com dados de exemplo)" if exemplo else ""))


def popular_exemplo(conn: sqlite3.Connection) -> None:
    hoje = date.today()

    # 20 pacientes fictícios, cada um com seu prontuário
    for i in range(1, 21):
        cur = conn.execute(
            "INSERT INTO pacientes (nome, telefone, convenio, observacoes) VALUES (?,?,?,?)",
            (f"Paciente {i:02d}", f"(11) 9____-__{i:02d}",
             "particular" if i % 3 else "plano",
             "Substituir pelo nome e dados reais"),
        )
        pid = cur.lastrowid
        conn.execute(
            """INSERT INTO prontuarios
               (paciente_id, queixa_principal, historico, hipotese_diagnostica, plano_terapeutico)
               VALUES (?,?,?,?,?)""",
            (pid, "Preencher queixa principal", "Preencher histórico",
             "Preencher hipótese diagnóstica", "Sessões semanais"),
        )
        # agenda: espalha as próximas sessões ao longo de 2 semanas úteis
        dia = hoje + timedelta(days=(i % 10) + 1)
        while dia.weekday() >= 5:
            dia += timedelta(days=1)
        hora = f"{8 + (i % 10)}:00".zfill(5)
        conn.execute(
            "INSERT INTO atendimentos (paciente_id, data, hora, tipo, status, valor) VALUES (?,?,?,?,?,?)",
            (pid, dia.isoformat(), hora, "consulta", "agendado", 250.0),
        )
        # e uma sessão já realizada na semana passada
        passada = dia - timedelta(days=7)
        conn.execute(
            """INSERT INTO atendimentos (paciente_id, data, hora, tipo, status, valor, pago, evolucao)
               VALUES (?,?,?,?,?,?,?,?)""",
            (pid, passada.isoformat(), hora, "consulta", "realizado", 250.0, 1,
             "Evolução da sessão — preencher"),
        )

    mes = hoje.strftime("%Y-%m")
    fin = [
        (f"{mes}-05", "receita", "consultório", "Atendimentos da semana", 2500.0, "conta PJ", 1),
        (f"{mes}-05", "receita", "youtube", "AdSense do mês", 800.0, "conta PF", 1),
        (f"{mes}-10", "despesa", "casa", "Aluguel", 3200.0, "conta PF", 1),
        (f"{mes}-12", "despesa", "escola", "Mensalidade escola (2 filhos)", 2400.0, "conta PF", 1),
        (f"{mes}-15", "despesa", "consultório", "Aluguel da sala", 1200.0, "conta PJ", 1),
        (f"{mes}-20", "despesa", "mercado", "Compras do mês", 1500.0, "cartão", 0),
    ]
    conn.executemany(
        """INSERT INTO fin_lancamentos (data, tipo, categoria, descricao, valor, conta, pago)
           VALUES (?,?,?,?,?,?,?)""",
        fin,
    )

    yt = [
        ("Ideia de vídeo — preencher título", "ideia", None, None),
        ("Vídeo em roteiro — preencher", "roteiro", (hoje + timedelta(days=7)).isoformat(), None),
        ("Vídeo publicado — preencher", "publicado", None, (hoje - timedelta(days=3)).isoformat()),
    ]
    conn.executemany(
        "INSERT INTO yt_videos (titulo, status, data_prevista, data_publicacao) VALUES (?,?,?,?)",
        yt,
    )

    area = {n: i + 1 for i, (n, _, _) in enumerate(AREAS)}
    projetos = [
        (area["YouTube"], "Crescer o canal", "Meta de inscritos e ritmo de publicação", "ativo", "alta"),
        (area["Financeiro"], "Organizar vida financeira", "Mapear receitas, despesas e reservas", "ativo", "alta"),
        (area["Consultório"], "Digitalizar prontuários", "Migrar fichas em papel para o banco", "ativo", "media"),
        (area["Família"], "Férias em família", "Planejar destino, datas e orçamento", "ideia", "media"),
    ]
    conn.executemany(
        "INSERT INTO projetos (area_id, nome, descricao, status, prioridade) VALUES (?,?,?,?,?)",
        projetos,
    )

    tarefas = [
        (1, area["YouTube"], "Gravar próximo vídeo", (hoje + timedelta(days=3)).isoformat(), "alta"),
        (2, area["Financeiro"], "Lançar despesas do cartão", (hoje + timedelta(days=2)).isoformat(), "media"),
        (3, area["Consultório"], "Preencher prontuários dos pacientes reais", (hoje + timedelta(days=14)).isoformat(), "alta"),
        (None, area["Família"], "Consulta pediatra — agendar", (hoje + timedelta(days=5)).isoformat(), "media"),
    ]
    conn.executemany(
        "INSERT INTO tarefas (projeto_id, area_id, titulo, data_limite, prioridade) VALUES (?,?,?,?,?)",
        tarefas,
    )

    eventos = [
        (2, (hoje + timedelta(days=4)).isoformat(), "07:30", "Escola — reunião de pais", "escola"),
        (1, (hoje + timedelta(days=10)).isoformat(), "20:00", "Jantar a dois", "lazer"),
        (3, (hoje + timedelta(days=20)).isoformat(), None, "Aniversário — preparar festa", "aniversario"),
    ]
    conn.executemany(
        "INSERT INTO familia_eventos (membro_id, data, hora, titulo, tipo) VALUES (?,?,?,?,?)",
        eventos,
    )

    arquivos = [
        ("arquivos/financeiro/", "Comprovantes e extratos", area["Financeiro"], "documento",
         "Guardar aqui extratos, notas e comprovantes"),
        ("arquivos/youtube/", "Roteiros e thumbnails", area["YouTube"], "video",
         "Material de produção do canal"),
        ("arquivos/pacientes/", "Documentos de pacientes", area["Consultório"], "exame",
         "Exames, encaminhamentos e termos (um subdiretório por paciente)"),
        ("arquivos/familia/", "Documentos da família", area["Família"], "documento",
         "RG, certidões, boletins, carteirinhas"),
    ]
    conn.executemany(
        "INSERT INTO arquivos (caminho, titulo, area_id, categoria, descricao) VALUES (?,?,?,?,?)",
        arquivos,
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exemplo", action="store_true",
                    help="popular com dados de exemplo (20 pacientes etc.)")
    args = ap.parse_args()
    criar(args.exemplo)
