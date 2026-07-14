#!/usr/bin/env python3
"""Cria o banco central de organização (organizacao.db) a partir do schema.sql
e popula com dados de EXEMPLO (um template para você preencher).

Uso:
    python3 criar_banco.py            # cria o banco com dados de exemplo
    python3 criar_banco.py --vazio    # cria o banco só com a estrutura (sem exemplos)

Rodar de novo recria o banco do zero (apaga o organizacao.db anterior).
"""
from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import date, timedelta

AQUI = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(AQUI, "organizacao.db")
SCHEMA = os.path.join(AQUI, "schema.sql")

HOJE = date(2026, 7, 14)  # data de referência dos exemplos


def d(delta_dias: int) -> str:
    """Data ISO relativa a hoje (facilita ver itens 'próximos' no painel)."""
    return (HOJE + timedelta(days=delta_dias)).isoformat()


def criar_estrutura(con: sqlite3.Connection) -> None:
    with open(SCHEMA, encoding="utf-8") as fh:
        con.executescript(fh.read())


def semear(con: sqlite3.Connection) -> None:
    cur = con.cursor()

    # ---- Áreas da vida -----------------------------------------------------
    areas = [
        ("Financeiro", "💰", "#16a34a", "Contas, receitas, despesas e metas", 1),
        ("YouTube", "🎬", "#dc2626", "Canal, roteiros e publicações", 2),
        ("Consultório", "🩺", "#2563eb", "Pacientes, prontuários e atendimentos", 3),
        ("Família", "👨‍👩‍👧‍👦", "#d97706", "Esposa, filhos e datas importantes", 4),
        ("Pessoal", "🌱", "#7c3aed", "Estudos, saúde e projetos pessoais", 5),
    ]
    cur.executemany(
        "INSERT INTO areas(nome,icone,cor,descricao,ordem) VALUES (?,?,?,?,?)", areas
    )
    area = {row[0]: i + 1 for i, row in enumerate(areas)}

    # ---- Projetos ----------------------------------------------------------
    projetos = [
        (area["YouTube"], "Reformular identidade visual do canal", "Nova vinheta, thumbnails padronizadas e banner.",
         "em_andamento", "alta", 40, d(-20), d(15), None, "Escolher paleta de cores e fonte", ""),
        (area["Consultório"], "Migrar prontuários para este sistema", "Passar os 20 prontuários em papel para o banco.",
         "em_andamento", "alta", 25, d(-10), d(30), None, "Digitar os 5 primeiros prontuários", ""),
        (area["Financeiro"], "Montar reserva de emergência", "Guardar 6 meses de custos fixos.",
         "em_andamento", "media", 55, d(-90), d(120), None, "Transferir aporte do mês", ""),
        (area["Pessoal"], "Curso de atualização profissional", "Concluir a especialização até o fim do ano.",
         "pausado", "media", 60, d(-200), d(160), None, "Retomar módulo 4", ""),
        (area["Família"], "Planejar férias em família", "Viagem nas férias escolares das crianças.",
         "ideia", "baixa", 0, None, d(120), None, "Pesquisar destinos com as crianças", ""),
    ]
    cur.executemany(
        """INSERT INTO projetos(area_id,titulo,descricao,status,prioridade,progresso,
           data_inicio,data_prazo,data_conclusao,proxima_acao,observacoes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        projetos,
    )

    # ---- Tarefas -----------------------------------------------------------
    tarefas = [
        (1, area["YouTube"], "Definir paleta de cores", "fazendo", "alta", d(2), None, ""),
        (1, area["YouTube"], "Criar 5 modelos de thumbnail", "a_fazer", "media", d(9), None, ""),
        (2, area["Consultório"], "Digitar prontuários 1 a 5", "a_fazer", "alta", d(5), None, ""),
        (3, area["Financeiro"], "Automatizar transferência mensal", "a_fazer", "media", d(3), None, ""),
        (None, area["Família"], "Marcar dentista das crianças", "a_fazer", "alta", d(7), None, ""),
        (None, area["Pessoal"], "Renovar CRM/registro profissional", "feito", "media", d(-4), d(-4), ""),
    ]
    cur.executemany(
        """INSERT INTO tarefas(projeto_id,area_id,titulo,status,prioridade,prazo,concluida_em,observacoes)
           VALUES (?,?,?,?,?,?,?,?)""",
        tarefas,
    )

    # ---- Arquivos ----------------------------------------------------------
    arquivos = [
        ("Contrato do consultório", "arquivos/contratos/aluguel-consultorio.pdf", "contrato",
         area["Consultório"], 2, d(-300), "aluguel, consultório", "Contrato de locação da sala"),
        ("Roteiro do próximo vídeo", "arquivos/youtube/roteiro-video-08.docx", "roteiro",
         area["YouTube"], 1, d(-2), "roteiro, youtube", "Rascunho do episódio 8"),
        ("Planilha de imposto de renda", "arquivos/financeiro/irpf-2026.xlsx", "planilha",
         area["Financeiro"], None, d(-30), "imposto, irpf", "Base para a declaração"),
        ("Boletim escolar - 1º filho", "arquivos/familia/boletim-1sem.pdf", "documento",
         area["Família"], None, d(-15), "escola, boletim", ""),
    ]
    cur.executemany(
        """INSERT INTO arquivos(titulo,caminho,categoria,area_id,projeto_id,data_arquivo,tags,descricao)
           VALUES (?,?,?,?,?,?,?,?)""",
        arquivos,
    )

    # ---- Financeiro --------------------------------------------------------
    contas = [
        ("Conta Corrente", "corrente", "Banco principal", 8500.0),
        ("Poupança / Reserva", "poupanca", "Banco principal", 22000.0),
        ("Cartão de Crédito", "cartao", "Banco principal", 0.0),
        ("Dinheiro (consultório)", "dinheiro", None, 300.0),
        ("Investimentos", "investimento", "Corretora", 45000.0),
    ]
    cur.executemany(
        "INSERT INTO contas(nome,tipo,instituicao,saldo_inicial) VALUES (?,?,?,?)", contas
    )

    categorias = [
        ("Consultório", "receita", "trabalho"),
        ("Salário/Pró-labore", "receita", "trabalho"),
        ("YouTube (AdSense)", "receita", "conteudo"),
        ("Moradia", "despesa", "casa"),
        ("Alimentação", "despesa", "casa"),
        ("Educação dos filhos", "despesa", "familia"),
        ("Saúde", "despesa", "familia"),
        ("Consultório (custos)", "despesa", "trabalho"),
        ("Lazer", "despesa", "familia"),
        ("Investimento/Aporte", "despesa", "financeiro"),
    ]
    cur.executemany(
        "INSERT INTO categorias_fin(nome,tipo,grupo) VALUES (?,?,?)", categorias
    )
    catid = {row[0]: i + 1 for i, row in enumerate(categorias)}

    transacoes = [
        (d(-5), "Atendimentos da semana", "receita", 2400.0, 1, catid["Consultório"], 3, "realizado", 0, ""),
        (d(-3), "Aluguel do consultório", "despesa", 1800.0, 1, catid["Consultório (custos)"], 2, "realizado", 1, ""),
        (d(-2), "Mercado do mês", "despesa", 1650.0, 3, catid["Alimentação"], None, "realizado", 0, ""),
        (d(-2), "Mensalidade escolar (2 filhos)", "despesa", 2200.0, 1, catid["Educação dos filhos"], None, "realizado", 1, ""),
        (d(-1), "Receita AdSense YouTube", "receita", 320.0, 1, catid["YouTube (AdSense)"], None, "realizado", 0, ""),
        (d(1), "Aporte reserva de emergência", "despesa", 1000.0, 2, catid["Investimento/Aporte"], 3, "previsto", 1, ""),
        (d(4), "Plano de saúde da família", "despesa", 1400.0, 1, catid["Saúde"], None, "previsto", 1, ""),
    ]
    cur.executemany(
        """INSERT INTO transacoes(data,descricao,tipo,valor,conta_id,categoria_id,projeto_id,status,recorrente,observacoes)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        transacoes,
    )

    metas = [
        (area["Financeiro"], "Reserva de emergência", 60000.0, 22000.0, "R$", d(150), "6 meses de custos"),
        (area["YouTube"], "Inscritos no canal", 10000, 3200, "inscritos", d(300), ""),
        (area["Consultório"], "Sessões por mês", 80, 62, "sessões", None, ""),
    ]
    cur.executemany(
        "INSERT INTO metas(area_id,titulo,valor_alvo,valor_atual,unidade,prazo,observacoes) VALUES (?,?,?,?,?,?,?)",
        metas,
    )

    # ---- YouTube -----------------------------------------------------------
    cur.execute(
        "INSERT INTO canais(nome,plataforma,url,meta_inscritos,observacoes) VALUES (?,?,?,?,?)",
        ("Meu Canal", "YouTube", "https://youtube.com/@meucanal", 10000, "Conteúdo da minha área"),
    )
    videos = [
        (1, "Boas-vindas ao canal", "institucional", "publicado", d(-40), d(-38), d(-35),
         "https://youtu.be/exemplo1", "", 1500, ""),
        (1, "5 erros comuns que atrapalham seu tratamento", "educativo", "edicao", d(-12), d(-4), None,
         "", "Gancho + 5 tópicos + chamada para inscrição", 0, "Faltam legendas"),
        (1, "Rotina de um dia no consultório", "bastidores", "roteiro", d(-3), None, None,
         "", "Roteiro em rascunho", 0, ""),
        (1, "Perguntas e respostas dos inscritos", "interação", "ideia", d(-1), None, None,
         "", "", 0, "Coletar perguntas nos stories"),
    ]
    cur.executemany(
        """INSERT INTO videos(canal_id,titulo,tema,status,data_ideia,data_gravacao,data_publicacao,url,roteiro,views,observacoes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        videos,
    )

    # ---- Consultório: 20 pacientes (fictícios) + prontuários ---------------
    # Nomes fictícios de exemplo — SUBSTITUA pelos dados reais dos seus pacientes.
    exemplos_detalhados = {
        1: ("Ansiedade e insônia", "particular"),
        2: ("Dores lombares recorrentes", "Plano Saúde X"),
        3: ("Acompanhamento pós-cirúrgico", "particular"),
    }
    for i in range(1, 21):
        nome = f"Paciente Exemplo {i:02d}"
        convenio = exemplos_detalhados.get(i, (None, "particular"))[1]
        cur.execute(
            """INSERT INTO pacientes(nome,data_nascimento,telefone,email,responsavel,convenio,status,observacoes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (nome, None, "", "", "", convenio, "ativo",
             "Cadastro de exemplo — preencher com dados reais"),
        )
        paciente_id = cur.lastrowid
        queixa = exemplos_detalhados.get(i, ("A preencher", None))[0]
        cur.execute(
            """INSERT INTO prontuarios(paciente_id,queixa_principal,historico,hipotese_diagnostica,cid,plano_terapeutico)
               VALUES (?,?,?,?,?,?)""",
            (paciente_id, queixa, "", "", "", ""),
        )

    # Atendimentos e evoluções de exemplo para os 3 primeiros pacientes
    atendimentos = [
        (1, d(-14), "09:00", "09:50", "avaliacao", "presencial", "realizado", 200.0, 1, "Pix", ""),
        (1, d(-7), "09:00", "09:50", "sessao", "presencial", "realizado", 200.0, 1, "Pix", ""),
        (1, d(2), "09:00", "09:50", "sessao", "presencial", "confirmado", 200.0, 0, "", ""),
        (2, d(-3), "14:00", "14:50", "consulta", "online", "realizado", 250.0, 1, "Cartão", ""),
        (2, d(5), "14:00", "14:50", "retorno", "online", "agendado", 250.0, 0, "", ""),
        (3, d(1), "16:00", "16:50", "avaliacao", "presencial", "agendado", 200.0, 0, "", ""),
    ]
    cur.executemany(
        """INSERT INTO atendimentos(paciente_id,data,hora_inicio,hora_fim,tipo,modalidade,status,valor,pago,forma_pagamento,observacoes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        atendimentos,
    )

    evolucoes = [
        (1, 1, d(-14), "Primeira avaliação. Queixa de ansiedade e dificuldade para dormir. Definido plano inicial."),
        (1, 2, d(-7), "Relata leve melhora no sono. Mantido plano; orientações de higiene do sono."),
        (2, 4, d(-3), "Avaliação da dor lombar. Solicitados exercícios e reavaliação em 8 dias."),
    ]
    cur.executemany(
        "INSERT INTO evolucoes(prontuario_id,atendimento_id,data,conteudo) VALUES (?,?,?,?)",
        evolucoes,
    )

    # ---- Família -----------------------------------------------------------
    familiares = [
        ("Esposa (nome)", "esposa", d(-12775), "", "Preencher nome e data reais"),
        ("1º Filho (nome)", "filho", d(-2900), "", "Preencher nome e data reais"),
        ("2º Filho (nome)", "filho", d(-1800), "", "Preencher nome e data reais"),
    ]
    cur.executemany(
        "INSERT INTO familiares(nome,parentesco,data_nascimento,telefone,observacoes) VALUES (?,?,?,?,?)",
        familiares,
    )

    eventos = [
        ("Aniversário do 1º filho", "aniversario", 2, area["Família"], d(20), None, "Casa", 1, 0, ""),
        ("Reunião de pais na escola", "escola", None, area["Família"], d(6), "19:00", "Escola", 0, 0, "Levar boletim"),
        ("Consulta pediatra (2º filho)", "saude", 3, area["Família"], d(10), "10:30", "Clínica", 0, 0, ""),
        ("Aniversário de casamento", "aniversario", 1, area["Família"], d(45), None, None, 1, 0, ""),
        ("Gravação do vídeo do mês", "reuniao", None, area["YouTube"], d(8), "15:00", "Estúdio", 0, 0, ""),
        ("Vencimento do plano de saúde", "financeiro", None, area["Financeiro"], d(4), None, None, 1, 0, ""),
    ]
    cur.executemany(
        """INSERT INTO eventos(titulo,categoria,familiar_id,area_id,data,hora,local,recorrente,concluido,observacoes)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        eventos,
    )

    con.commit()


def main() -> None:
    ap = argparse.ArgumentParser(description="Cria o banco central de organização.")
    ap.add_argument("--vazio", action="store_true", help="Não inserir dados de exemplo.")
    args = ap.parse_args()

    if os.path.exists(DB):
        os.remove(DB)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    criar_estrutura(con)
    if not args.vazio:
        semear(con)
    con.close()

    tipo = "vazio (só estrutura)" if args.vazio else "com dados de exemplo"
    print(f"Banco criado em {DB} ({tipo}).")


if __name__ == "__main__":
    main()
