#!/usr/bin/env python3
"""Importa todos os dados de reembolso da família Palomo para o SQLite.

Fontes:
  - Planilha oficial (documentos/referencia/planilha-reembolsos-luisa-12-2025.xlsx),
    aba "Reembolso Cigna"
  - Print do portal Cigna 2026 (submissões com nº de submissão e CLM)
  - Explanation of Benefits da Cigna (3 PDFs, linha a linha)
  - Notas fiscais e recibos em PDF (vinculados aos claims)

Uso:  python3 importar_dados.py   (recria reembolsos.db do zero)

Requer: openpyxl  (pip install openpyxl)
"""

import re
import sqlite3
from datetime import datetime
from pathlib import Path

import openpyxl

BASE = Path(__file__).resolve().parent
DB = BASE / "reembolsos.db"
XLSX = BASE / "documentos/referencia/planilha-reembolsos-luisa-12-2025.xlsx"

# ---------------------------------------------------------------- helpers

def valor(v):
    """Converte '1.767,54', '500,00', 840, '-' etc. em float ou None."""
    if v is None or v == "-" or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def data_iso(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return s or None


BENEFICIARIOS = {
    "luisa": ("Luisa Juliana Faria Ramalho de Souza", "titular (funcionária McKinsey)", "358.060.038-92"),
    "priscila": ("Priscila da Silva Herbas Palomo", "parceira", "313.050.718-32"),
    "joao": ("João Guilherme Ramalho Palomo", "filho", "592.377.448-89"),
    "ana": ("Ana Luisa Ramalho Palomo", "filha", "608.882.628-25"),
}


def beneficiario_canonico(nome):
    n = (nome or "").lower()
    if "priscila" in n:
        return BENEFICIARIOS["priscila"][0]
    if "joao" in n or "joão" in n:
        return BENEFICIARIOS["joao"][0]
    if "ana luisa" in n or "ana luísa" in n:
        return BENEFICIARIOS["ana"][0]
    if "luisa" in n or "luísa" in n:
        return BENEFICIARIOS["luisa"][0]
    return nome


# prestador: (nome canônico, especialidade)
PRESTADORES_ESPECIALIDADE = {
    "wendy": ("Wendy Paola Ramírez Molano", "Fisioterapia"),
    "rogério|rogerio": ("Rogério Ribeiro de Sousa", "Terapia / Massoterapia"),
    "karine": ("Karine Saito Psicologia Ltda", "Psicologia"),
    "akaishi": ("Instituto de Cirurgia Eduardo Akaishi (Dr. Leonardo Akaishi)", "Psiquiatria / Clínica"),
    "yuan": ("Espaço Yuan Terapias Ltda", "Fisioterapia"),
    "humanitas": ("Humanitas Instituto Integrado de Saúde", "Pediatria (Dra. Tatiana)"),
    "luna": ("Clínica de Pediatria Luna S/S Ltda", "Cirurgia pediátrica (Dr. Luis Ricardo)"),
    "ciresp": ("Ciresp Cirurgiões Especializados SC Ltda (Dr. Ricardo)", "Urologia pediátrica / Cirurgia"),
    "mcavalcante": ("MCavalcanteCosta (Dr. Marcelo Cavalcante Costa)", "Oftalmologia"),
    "fabiane": ("Fabiane Aliotti Serviços Médicos Ltda", "Pediatria"),
    "anthero": ("Luis Anthero Rugoni Peloso", "Ginecologia / Clínica"),
    "fleury": ("Fleury S.A.", "Laboratório"),
    "gerhardt": ("Gerhardt Serviços Médicos (Dra. Clarissa)", "Alergia e Imunologia"),
    "pequenos horm": ("Pequenos Hormônios Serviços Médicos Ltda", "Endocrinologia pediátrica"),
    "saude da vil": ("Saúde da Vila - Odontologia", "Odontologia"),
    "icc": ("ICC Clínica de Radiologia e Diagnósticos", "Radiologia"),
    "kostov": ("Óticas Kostov Mero Ltda", "Ótica"),
    "raiadrogasil": ("RaiaDrogasil S.A.", "Farmácia"),
    "drogaria são paulo|drogaria sao paulo": ("Drogaria São Paulo", "Farmácia"),
    "drogaria x": ("Drogaria X Farmácia", "Farmácia"),
    "alvo": ("Alvo Clínica Médica S/S (Dr. André Luis)", "Cirurgia pediátrica"),
    "luce": ("Luce e Santos Serviços Médicos Ltda", "Consultas médicas"),
    "tkmo": ("TKMO - Instituto Otorrino", "Otorrinolaringologia"),
    "israelita": ("Hospital Albert Einstein (Soc. Benef. Israelita)", "Hospital"),
    "physical therapy": ("Espaço Yuan Terapias Ltda", "Fisioterapia"),
}


def prestador_canonico(nome):
    n = (nome or "").lower()
    for chaves, (canon, esp) in PRESTADORES_ESPECIALIDADE.items():
        if any(k in n for k in chaves.split("|")):
            return canon, esp
    return (nome, None) if nome else (None, None)


TIPOS = {
    "terapia": "terapia", "consulta": "consulta", "consultation": "consulta",
    "honorário": "honorario", "honorario": "honorario", "cirurgia": "cirurgia",
    "outros": "outro", "product": "produto", "remedios": "medicamento",
    "exame": "exame",
}


def tipo_canonico(t):
    return TIPOS.get((t or "").strip().lower(), "outro")


# ---------------------------------------------------------------- setup

def criar_banco():
    if DB.exists():
        DB.unlink()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript((BASE / "schema.sql").read_text(encoding="utf-8"))
    return conn


def seed_beneficiarios(conn):
    for nome, parentesco, cpf in BENEFICIARIOS.values():
        conn.execute(
            "INSERT INTO beneficiarios (nome, parentesco, cpf) VALUES (?, ?, ?)",
            (nome, parentesco, cpf),
        )


def get_beneficiario_id(conn, nome):
    canon = beneficiario_canonico(nome)
    row = conn.execute("SELECT id FROM beneficiarios WHERE nome = ?", (canon,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO beneficiarios (nome) VALUES (?)", (canon,))
    return cur.lastrowid


def get_prestador_id(conn, nome, cnpj=None):
    if not nome:
        return None
    canon, esp = prestador_canonico(nome)
    row = conn.execute("SELECT id FROM prestadores WHERE nome = ?", (canon,)).fetchone()
    if row:
        if cnpj:
            conn.execute(
                "UPDATE prestadores SET cpf_cnpj = COALESCE(cpf_cnpj, ?) WHERE id = ?",
                (str(cnpj), row["id"]),
            )
        return row["id"]
    cur = conn.execute(
        "INSERT INTO prestadores (nome, especialidade, cpf_cnpj) VALUES (?, ?, ?)",
        (canon, esp, str(cnpj) if cnpj else None),
    )
    return cur.lastrowid


# ---------------------------------------------------------------- planilha

def importar_planilha(conn):
    """Importa a aba 'Reembolso Cigna'. Linhas de reconsideração (mesmo claim
    reenviado) atualizam o registro original em vez de duplicar."""
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb["Reembolso Cigna"]
    claim_para_id = {}

    for row in ws.iter_rows(min_row=2, values_only=True):
        (_col0, funcionario, paciente, prestador, cnpj, tipo, data_recibo, vlr,
         reembolsado, diferenca, total_reemb, coment, data_acerto, n_claim,
         documento, novo_claim, texto_recons, situacao, num_nf) = row[:19]

        if not paciente or not isinstance(paciente, str):
            continue  # separador de ano / linhas vazias

        v_pago = valor(vlr)
        if v_pago is None:
            continue
        v_reemb = valor(total_reemb) or 0.0
        claim = str(n_claim) if n_claim else None
        novo = str(novo_claim) if novo_claim and str(novo_claim).isdigit() else None
        situacao_txt = situacao.strip() if isinstance(situacao, str) else None
        nf = str(num_nf) if num_nf else None
        coment_txt = coment.strip().replace("\n", " ") if isinstance(coment, str) else None

        # linha de reenvio de um claim já registrado -> merge
        if claim and claim in claim_para_id:
            rid = claim_para_id[claim]
            conn.execute(
                """UPDATE reembolsos SET
                     situacao = COALESCE(?, situacao),
                     nota_fiscal = COALESCE(?, nota_fiscal),
                     status = CASE WHEN ? IS NOT NULL THEN 'em_analise' ELSE status END
                   WHERE id = ?""",
                (situacao_txt, nf, situacao_txt, rid),
            )
            continue

        obs = None
        d_atend = data_iso(data_recibo)
        if d_atend == "2026-10-02" and claim == "137973185":
            d_atend = "2026-02-10"
            obs = "Data corrigida: planilha trazia 02/10/2026 (formato americano 10/02/26)"

        em_reconsideracao = bool(situacao_txt) and v_reemb == 0
        if em_reconsideracao or reembolsado is None and not data_acerto:
            status = "em_analise"
        elif v_reemb >= v_pago - 1:
            status = "pago"
        elif v_reemb > 1:
            status = "pago_parcial"
        elif data_acerto:
            status = "negado"
        else:
            status = "em_analise"

        cur = conn.execute(
            """INSERT INTO reembolsos
               (funcionario, beneficiario_id, prestador_id, tipo, data_atendimento,
                data_pagamento, valor_pago, valor_reembolsado, status, situacao,
                n_claim, novo_n_claim, comentario_cigna, texto_reconsideracao,
                nota_fiscal, origem, observacoes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'planilha', ?)""",
            (
                "Luisa Juliana Faria Ramalho de Souza",
                get_beneficiario_id(conn, paciente),
                get_prestador_id(conn, prestador, cnpj),
                tipo_canonico(tipo),
                d_atend,
                data_iso(data_acerto),
                v_pago,
                round(v_reemb, 2),
                status,
                situacao_txt,
                claim,
                novo,
                coment_txt,
                texto_recons.strip() if isinstance(texto_recons, str) else None,
                nf,
                obs,
            ),
        )
        rid = cur.lastrowid
        if claim:
            claim_para_id[claim] = rid
        if novo:
            claim_para_id[novo] = rid

    return claim_para_id


# ---------------------------------------------------------------- portal 2026

# (paciente, valor BRL, nº submissão, CLM, data tratamento, tipo, claim na planilha ou None, obs)
PORTAL_2026 = [
    ("Priscila da Silva Herbas Palomo", 3200.00, "824283895253117695", "CLM-20260324Z-012427F5", "2026-01-30", "CONSULTATION", "138032224", None),
    ("Luisa Souza", 580.00, "823989702572059041", "CLM-20260323Z-052C208A", "2026-02-02", "CONSULTATION", None, None),
    ("Priscila da Silva Herbas Palomo", 1260.00, "801882225139048956", "CLM-20260121Z-9313FE9C", "2025-01-08", "CONSULTATION", "134112138", "Reenvio da consulta odontológica Saúde da Vila de 08/01/2025"),
    ("Ana Luisa Ramalho Palomo", 1588.00, "801154650989191579", "CLM-20260119Z-87D7754D", "2025-12-01", "CONSULTATION", None, "Fisioterapia Wendy — 4 sessões de dezembro/2025 (R$397 cada)"),
    ("Luisa Souza", 390.00, "797524013743392698", "CLM-20260109Z-7339F679", "2025-07-25", "CONSULTATION", None, None),
    ("Joao Guilherme Ramalho Palomo", 27.73, "797512909453576893", "CLM-20260109Z-76114909", "2026-01-06", "PRODUCT", None, None),
    ("Luisa Souza", 1376.00, "776089168088236650", "CLM-20251111Z-02D686BE", "2025-11-02", "CONSULTATION", None, "Fisioterapia Wendy — 4 sessões de novembro/2025 (R$344 cada)"),
    ("Luisa Souza", 700.00, "776086905005375992", "CLM-20251111Z-F0409F4C", "2025-10-31", "CONSULTATION", None, None),
    ("Luisa Souza", 895.00, "755489881095999991", "CLM-20250915Z-78298536", "2025-09-12", "PRODUCT", None, "Óculos do João Guilherme — ver EOB claims 136493695 / 137716193"),
    ("Luisa Souza", 595.00, "755488575286285043", "CLM-20250915Z-BE43ACCE", "2025-09-11", "PRODUCT", None, "Armação do João Guilherme — ver EOB claims 136493708"),
]


def importar_portal(conn, claim_para_id):
    for paciente, v, n_sub, clm, data_trat, tipo, claim, obs in PORTAL_2026:
        rid = claim_para_id.get(claim) if claim else None
        if rid is None:
            cur = conn.execute(
                """INSERT INTO reembolsos
                   (funcionario, beneficiario_id, tipo, descricao, data_atendimento,
                    valor_pago, status, situacao, n_claim, origem, observacoes)
                   VALUES (?, ?, ?, ?, ?, ?, 'em_analise', 'Submitted no portal Cigna', ?, 'portal_2026', ?)""",
                (
                    "Luisa Juliana Faria Ramalho de Souza",
                    get_beneficiario_id(conn, paciente),
                    tipo_canonico(tipo),
                    f"Submissão portal Cigna ({clm})",
                    data_trat,
                    v,
                    clm,
                    obs,
                ),
            )
            rid = cur.lastrowid
        conn.execute(
            """INSERT INTO submissoes_portal
               (reembolso_id, paciente, valor_brl, n_submissao, n_clm, data_tratamento, tipo, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'Submitted')""",
            (rid, beneficiario_canonico(paciente), v, n_sub, clm, data_trat, tipo),
        )


# ---------------------------------------------------------------- extras

def importar_extras(conn, claim_para_id):
    """Reembolsos com NF em mãos que ainda não constam na planilha nem no portal."""
    cur = conn.execute(
        """INSERT INTO reembolsos
           (funcionario, beneficiario_id, prestador_id, tipo, descricao,
            data_atendimento, valor_pago, status, situacao, nota_fiscal, origem)
           VALUES (?, ?, ?, 'consulta', ?, '2026-06-24', 690.0, 'solicitado', 'a enviar à Cigna', '1635', 'manual')""",
        (
            "Luisa Juliana Faria Ramalho de Souza",
            get_beneficiario_id(conn, "Joao Guilherme"),
            get_prestador_id(conn, "Gerhardt Servicos Medicos", "31.080.330/0001-68"),
            "Consulta Alergia e Imunologia — Dra. Clarissa Morais Busatto Gerhardt (CRM 152.279)",
        ),
    )
    claim_para_id["NF1635"] = cur.lastrowid

    cur = conn.execute(
        """INSERT INTO reembolsos
           (funcionario, beneficiario_id, prestador_id, tipo, descricao,
            data_atendimento, valor_pago, status, situacao, origem)
           VALUES (?, ?, ?, 'terapia', ?, '2026-06-30', 1600.0, 'solicitado', 'a enviar à Cigna', 'manual')""",
        (
            "Luisa Juliana Faria Ramalho de Souza",
            get_beneficiario_id(conn, "Priscila"),
            get_prestador_id(conn, "Wendy Paola Ramirez Molano", "901.505.418-56"),
            "Fisioterapia — 4 aulas de R$400 (1, 8, 15 e 22/06/2026); "
            "indicação médica: hérnia de disco lombar (relatório Dr. Alvaro Herbas Palomo, 29/06/2026)",
        ),
    )
    claim_para_id["RECIBO-JUN26"] = cur.lastrowid


# ---------------------------------------------------------------- documentos

DOCUMENTOS = [
    # (arquivo, titulo, categoria, data, descricao)
    ("recibos/recibo-fisio-wendy-priscila-set-2025.pdf", "Recibo fisioterapia Wendy — Priscila — set/2025 (R$380)", "recibo", "2025-09-11", "4 aulas de R$95 (8, 15, 22 e 29/09/2025)"),
    ("recibos/recibo-fisio-wendy-joao-guilherme-out-2025.pdf", "Recibo fisioterapia Wendy — João Guilherme — out/2025 (R$688)", "recibo", "2025-10-01", "8 sessões de R$86 (out/2025)"),
    ("recibos/recibo-fisio-wendy-luisa-nov-2025-1376.pdf", "Recibo fisioterapia Wendy — Luisa — nov/2025 (R$1.376)", "recibo", "2025-11-02", "4 sessões de R$344 (3, 10, 17 e 24/11/2025)"),
    ("recibos/recibo-fisio-wendy-luisa-nov-2025-1588.pdf", "Recibo fisioterapia Wendy — Luisa — nov/2025 (R$1.588)", "recibo", "2025-11-02", "4 sessões de R$397 (3, 10, 17 e 24/11/2025)"),
    ("recibos/recibo-fisio-wendy-ana-luisa-dez-2025.pdf", "Recibo fisioterapia Wendy — Ana Luisa — dez/2025 (R$1.588)", "recibo", "2025-12-22", "4 sessões de R$397 (1, 8, 15 e 22/12/2025)"),
    ("recibos/recibo-fisio-wendy-priscila-jun-2026.pdf", "Recibo fisioterapia Wendy — Priscila — jun/2026 (R$1.600)", "recibo", "2026-06-30", "4 aulas de R$400 (1, 8, 15 e 22/06/2026)"),
    ("eob-cigna/eob-2025-09-24.pdf", "EOB Cigna — processado em 24/09/2025", "eob", "2025-09-24", "Claims 136476032, 136492081, 136493645, 136493695, 136493708 — total BRL 8.469,43"),
    ("eob-cigna/eob-2025-11-18.pdf", "EOB Cigna — processado em 18/11/2025", "eob", "2025-11-18", "Claims 137061449, 137073556, 137076305, 137076320 — total BRL 2.929,95"),
    ("eob-cigna/eob-2026-01-17-action-required.pdf", "EOB Cigna — processado em 17/01/2026 (action required)", "eob", "2026-01-17", "Claims 137714308, 137720286, 137723876, 137716136, 137716152, 137716193 — total BRL 9.085,21"),
    ("notas-fiscais/nf-1635-dra-clarissa-joao-guilherme-2026-06-24.pdf", "NF 1635 — Dra. Clarissa (alergologista) — João Guilherme (R$690)", "nota_fiscal", "2026-06-24", "Gerhardt Serviços Médicos — consulta 24/06/2026"),
    ("notas-fiscais/nf-1205-pequenos-hormonios-joao-guilherme-2026-06-16.pdf", "NF 1205 — Pequenos Hormônios (endócrino ped.) — João Guilherme (R$800)", "nota_fiscal", "2026-06-16", "Dra. Ana Paula Teixeira Melo — consulta 16/06/2026"),
    ("notas-fiscais/nf-28083-farmacia-remedios-priscila-2026-06.pdf", "NF 28083 — Drogaria X Farmácia — remédios Priscila (R$398,31)", "nota_fiscal", "2026-06-03", "Medicamentos prescritos pelo Dr. Leonardo (PDF escaneado)"),
    ("notas-fiscais/nf-dra-fabiane-joao-guilherme.pdf", "NF — Dra. Fabiane (pediatra) — João Guilherme", "nota_fiscal", None, "Fabiane Aliotti Serviços Médicos"),
    ("notas-fiscais/nf-33-dra-fabiane-ana-luisa-2026-06-09.pdf", "NF 33 — Dra. Fabiane (pediatra) — Ana Luisa (R$700)", "nota_fiscal", "2026-06-09", "Consulta pediátrica"),
    ("notas-fiscais/nf-5836-dr-marcelo-priscila-2026-03-12.pdf", "NF 5836 — Dr. Marcelo Cavalcante Costa (oftalmo) — Priscila (R$800)", "nota_fiscal", "2026-03-12", "Consulta oftalmológica 12/03/2026"),
    ("notas-fiscais/nf-5835-dr-marcelo-ana-luisa-2026-03-12.pdf", "NF 5835 — Dr. Marcelo Cavalcante Costa (oftalmo) — Ana Luisa (R$800)", "nota_fiscal", "2026-03-12", "Consulta oftalmológica 12/03/2026"),
    ("notas-fiscais/nf-6017-dr-marcelo-joao-guilherme-2026-05-27.pdf", "NF 6017 — Dr. Marcelo Cavalcante Costa (oftalmo) — João Guilherme (R$800)", "nota_fiscal", "2026-05-27", "Consulta oftalmológica 27/05/2026"),
    ("notas-fiscais/nf-577-dr-luis-anthero-priscila-2026-05-29.pdf", "NF 577 — Dr. Luis Anthero Rugoni Peloso — Priscila (R$500)", "nota_fiscal", "2026-06-02", "Consulta médica 29/05/2026 (NF de Osasco)"),
    ("notas-fiscais/nf-6344-dr-andre-luis-joao-guilherme-2025-11-04.pdf", "NF 6344 — Alvo Clínica (Dr. André Luis) — João Guilherme (R$800)", "nota_fiscal", "2025-11-04", "Consulta 04/11/2025 — claim em reconsideração"),
    ("notas-fiscais/nf-709-dr-ricardo-ciresp-joao-guilherme-2025-04-28.pdf", "NF 709 — Ciresp (Dr. Ricardo, urologista ped.) — João Guilherme (R$850)", "nota_fiscal", "2025-04-28", "Honorários 28/04/2025 — claim em reconsideração"),
    ("notas-fiscais/nf-6540-instituto-akaishi-priscila-2026-04-28.pdf", "NF 6540 — Instituto Eduardo Akaishi (Dr. Leonardo) — Priscila (R$700)", "nota_fiscal", "2026-04-28", "Consulta em consultório 28/04/2026"),
    ("notas-fiscais/nf-17553-fleury-priscila-2026-06-08.pdf", "NF 17553 — Fleury — exames de sangue Priscila (R$776,90)", "nota_fiscal", "2026-06-08", "Ficha 4220154315 — exames laboratoriais"),
    ("medicos/pedido-exames-dr-luis-anthero-priscila-2026-06-02.pdf", "Pedido de exames — Dr. Luis Anthero → Priscila", "pedido_exame", "2026-06-02", "Hemograma, hormônios, ultrassons, mamografia, densitometria etc. (CID Z014)"),
    ("medicos/receita-dr-leonardo-priscila-2026-06-03.pdf", "Receita controlada — Dr. Leonardo Akaishi → Priscila", "receita", "2026-06-03", "Desvenlafaxina 100mg + Pregabalina 150mg"),
    ("medicos/relatorio-medico-fisioterapia-priscila-2026-06-29.pdf", "Relatório médico p/ fisioterapia — Dr. Alvaro Herbas Palomo → Priscila", "relatorio_medico", "2026-06-29", "Hérnia de disco lombar L4, L5 e L5-S1 (CID-10 M51.1); indica fisioterapia"),
    ("planos/dental-2026-novos-planos.pdf", "Plano dental 2026 — novos planos", "plano", None, None),
    ("planos/novos-planos-cigna-2026.pdf", "Novos planos Cigna 2026", "plano", None, None),
    ("planos/novos-planos.html", "Novos planos (página HTML)", "plano", None, None),
    ("referencia/central-de-controle-familia-palomo.html", "Central de Controle — Família Palomo (dashboard original)", "referencia", None, None),
    ("referencia/memoria-familia-palomo.md", "Memória / glossário da família Palomo", "referencia", None, None),
    ("referencia/planilha-reembolsos-luisa-12-2025.xlsx", "Planilha de reembolsos médicos (fonte primária)", "referencia", None, None),
    ("referencia/nfse-prefeitura-sp-2026-jan-jun.csv", "NFS-e Prefeitura SP — jan a jun/2026 (CSV)", "referencia", None, None),
]

# vínculos: arquivo -> lista de claims (ou chaves especiais) a que se refere
VINCULOS = {
    "recibos/recibo-fisio-wendy-priscila-set-2025.pdf": ["136626933"],
    "recibos/recibo-fisio-wendy-joao-guilherme-out-2025.pdf": ["137076305"],
    "recibos/recibo-fisio-wendy-luisa-nov-2025-1376.pdf": ["CLM-20251111Z-02D686BE"],
    "recibos/recibo-fisio-wendy-ana-luisa-dez-2025.pdf": ["CLM-20260119Z-87D7754D"],
    "recibos/recibo-fisio-wendy-priscila-jun-2026.pdf": ["RECIBO-JUN26"],
    "medicos/relatorio-medico-fisioterapia-priscila-2026-06-29.pdf": ["RECIBO-JUN26"],
    "eob-cigna/eob-2025-09-24.pdf": ["136476032", "136492081", "136493645", "136493695", "136493708"],
    "eob-cigna/eob-2025-11-18.pdf": ["137061449", "137073556", "137076305", "137076320"],
    "eob-cigna/eob-2026-01-17-action-required.pdf": ["137714308", "137720286", "137723876", "137716136", "137716152", "137716193"],
    "notas-fiscais/nf-1635-dra-clarissa-joao-guilherme-2026-06-24.pdf": ["NF1635"],
    "notas-fiscais/nf-1205-pequenos-hormonios-joao-guilherme-2026-06-16.pdf": ["41411330"],
    "notas-fiscais/nf-28083-farmacia-remedios-priscila-2026-06.pdf": ["41148268"],
    "medicos/receita-dr-leonardo-priscila-2026-06-03.pdf": ["41148268"],
    "notas-fiscais/nf-33-dra-fabiane-ana-luisa-2026-06-09.pdf": ["41143425"],
    "notas-fiscais/nf-5836-dr-marcelo-priscila-2026-03-12.pdf": ["138490297"],
    "notas-fiscais/nf-5835-dr-marcelo-ana-luisa-2026-03-12.pdf": ["138492683"],
    "notas-fiscais/nf-6017-dr-marcelo-joao-guilherme-2026-05-27.pdf": ["41076491"],
    "notas-fiscais/nf-577-dr-luis-anthero-priscila-2026-05-29.pdf": ["NF577"],
    "notas-fiscais/nf-6344-dr-andre-luis-joao-guilherme-2025-11-04.pdf": ["137076320"],
    "notas-fiscais/nf-709-dr-ricardo-ciresp-joao-guilherme-2025-04-28.pdf": ["135081988"],
    "notas-fiscais/nf-6540-instituto-akaishi-priscila-2026-04-28.pdf": ["139159180"],
    "notas-fiscais/nf-17553-fleury-priscila-2026-06-08.pdf": ["41142914"],
    "medicos/pedido-exames-dr-luis-anthero-priscila-2026-06-02.pdf": ["41142914"],
}

PAPEIS = {"recibo": "recibo", "eob": "eob", "nota_fiscal": "nota_fiscal",
          "receita": "receita", "pedido_exame": "pedido_exame",
          "relatorio_medico": "relatorio"}


def importar_documentos(conn, claim_para_id):
    # a NF 577 (Dr. Luis Anthero) não tem nº de claim na planilha; localizar pela NF
    row = conn.execute("SELECT id FROM reembolsos WHERE nota_fiscal = '577'").fetchone()
    if row:
        claim_para_id["NF577"] = row["id"]

    doc_ids = {}
    for arquivo, titulo, categoria, data_doc, desc in DOCUMENTOS:
        cur = conn.execute(
            "INSERT INTO documentos (arquivo, titulo, categoria, data_documento, descricao) VALUES (?, ?, ?, ?, ?)",
            (arquivo, titulo, categoria, data_doc, desc),
        )
        doc_ids[arquivo] = cur.lastrowid

    for arquivo, claims in VINCULOS.items():
        categoria = next(c for a, _t, c, _d, _de in DOCUMENTOS if a == arquivo)
        for claim in claims:
            rid = claim_para_id.get(claim)
            if rid is None:
                row = conn.execute(
                    "SELECT id FROM reembolsos WHERE n_claim = ? OR novo_n_claim = ?",
                    (claim, claim),
                ).fetchone()
                rid = row["id"] if row else None
            if rid:
                conn.execute(
                    "INSERT OR IGNORE INTO reembolso_documentos (reembolso_id, documento_id, papel) VALUES (?, ?, ?)",
                    (rid, doc_ids[arquivo], PAPEIS.get(categoria, categoria)),
                )
    return doc_ids


# ---------------------------------------------------------------- EOB itens

# (claim, paciente, data, BRL, câmbio, USD, não coberto USD, pago USD, resp. paciente USD, tipo, remark)
EOB_ITENS = {
    "eob-cigna/eob-2025-09-24.pdf": ("2025-09-24", [
        ("136476032", "priscila", "2025-08-04", 800.00, 5.4979, 145.51, 0, 145.51, 0, "Outpatient Treatment", None),
        ("136476032", "priscila", "2025-08-11", 800.00, 5.4424, 146.99, 0, 146.99, 0, "Outpatient Treatment", None),
        ("136476032", "priscila", "2025-08-18", 800.00, 5.4373, 147.13, 0, 147.13, 0, "Outpatient Treatment", None),
        ("136476032", "priscila", "2025-08-25", 800.00, 5.4125, 147.81, 0, 147.81, 0, "Outpatient Treatment", None),
        ("136476032", "priscila", "2025-09-01", 800.00, 5.4395, 147.07, 0, 147.07, 0, "Outpatient Treatment", None),
        ("136476032", "priscila", "2025-09-08", 800.00, 5.4188, 147.63, 0, 147.63, 0, "Outpatient Treatment", None),
        ("136476032", "priscila", "2025-09-15", 800.00, 5.3172, 150.46, 0, 150.46, 0, "Outpatient Treatment", None),
        ("136492081", "priscila", "2025-09-08", 537.44, 5.4188, 99.18, 0, 79.34, 19.84, "Prescription Drugs", None),
        ("136492081", "priscila", "2025-09-08", 443.22, 5.4188, 81.79, 0, 65.43, 16.36, "Prescription Drugs", None),
        ("136493645", "joao", "2025-09-08", 44.35, 5.4188, 8.18, 8.18, 0, 8.18, "Non Covered Item", "NC085"),
        ("136493645", "joao", "2025-09-08", 44.35, 5.4188, 8.18, 8.18, 0, 8.18, "Non Covered Item", "NC085"),
        ("136493645", "joao", "2025-09-08", 40.20, 5.4188, 7.42, 7.42, 0, 7.42, "Non Covered Item", "NC085"),
        ("136493645", "joao", "2025-09-08", 22.05, 5.4188, 4.07, 4.07, 0, 4.07, "Non Covered Item", "NC085"),
        ("136493645", "joao", "2025-09-08", 44.67, 5.4188, 8.24, 0, 6.59, 1.65, "Prescription Drugs", None),
        ("136493645", "joao", "2025-09-08", 44.67, 5.4188, 8.24, 0, 6.59, 1.65, "Prescription Drugs", None),
        ("136493645", "joao", "2025-09-08", 61.76, 5.4188, 11.40, 11.40, 0, 11.40, "Non Covered Item", "NC022"),
        ("136493645", "joao", "2025-09-08", 4.99, 5.4188, 0.92, 0.92, 0, 0.92, "Non Covered Item", "NC022"),
        ("136493645", "joao", "2025-09-08", 59.04, 5.4188, 10.90, 10.90, 0, 10.90, "Non Covered Item", "NC022"),
        ("136493645", "joao", "2025-09-08", 32.69, 5.4188, 6.03, 6.03, 0, 6.03, "Non Covered Item", "NC022"),
        ("136493695", "joao", "2025-09-12", 359.80, 5.3553, 67.19, 67.19, 0, 0, "Single Vision Lenses", "PN011"),
        ("136493695", "joao", "2025-09-12", 535.20, 5.3553, 99.94, 99.94, 0, 0, "Frames", "PN011"),
        ("136493708", "joao", "2025-09-11", 595.00, 5.3901, 110.39, 110.39, 0, 0, "Frames", "PN011"),
    ]),
    "eob-cigna/eob-2025-11-18.pdf": ("2025-11-18", [
        ("137061449", "priscila", "2024-08-31", 334.32, 5.6107, 59.59, 59.59, 0, 0, "Diagnostic Lab O/P", "DN009"),
        ("137073556", "priscila", "2025-07-09", 1107.63, 5.5780, 198.57, 0, 158.86, 39.71, "Physician Visit O/V", None),
        ("137076305", "joao", "2025-10-01", 86.00, 5.3300, 16.14, 0, 12.91, 3.23, "Physical Therapy", None),
        ("137076305", "joao", "2025-10-03", 86.00, 5.3350, 16.12, 0, 12.90, 3.22, "Physical Therapy", None),
        ("137076305", "joao", "2025-10-08", 86.00, 5.3442, 16.09, 0, 12.87, 3.22, "Physical Therapy", None),
        ("137076305", "joao", "2025-10-10", 86.00, 5.5207, 15.58, 0, 12.46, 3.12, "Physical Therapy", None),
        ("137076305", "joao", "2025-10-15", 86.00, 5.4549, 15.77, 0, 12.62, 3.15, "Physical Therapy", None),
        ("137076305", "joao", "2025-10-17", 86.00, 5.4101, 15.90, 0, 12.72, 3.18, "Physical Therapy", None),
        ("137076305", "joao", "2025-10-22", 86.00, 5.4004, 15.92, 0, 12.74, 3.18, "Physical Therapy", None),
        ("137076305", "joao", "2025-10-24", 86.00, 5.3912, 15.95, 0, 12.76, 3.19, "Physical Therapy", None),
        ("137076320", "joao", "2025-11-04", 800.00, 5.3990, 148.18, 148.18, 0, 148.18, "Preventive Care", "NC016"),
    ]),
    "eob-cigna/eob-2026-01-17-action-required.pdf": ("2026-01-17", [
        ("137714308", "priscila", "2025-12-01", 800.00, 5.3562, 149.36, 0, 149.36, 0, "Outpatient Treatment", None),
        ("137714308", "priscila", "2025-12-08", 800.00, 5.4310, 147.30, 0, 147.30, 0, "Outpatient Treatment", None),
        ("137714308", "priscila", "2025-12-15", 800.00, 5.4147, 147.75, 0, 147.75, 0, "Outpatient Treatment", None),
        ("137714308", "priscila", "2025-12-22", 800.00, 5.5900, 143.11, 0, 143.11, 0, "Outpatient Treatment", None),
        ("137714308", "priscila", "2025-12-29", 800.00, 5.5704, 143.62, 0, 143.62, 0, "Outpatient Treatment", None),
        ("137720286", "priscila", "2025-12-11", 1767.54, 5.4084, 326.81, 326.81, 0, 326.81, "Non Covered Item", "NC022"),
        ("137723876", "priscila", "2025-12-01", 1588.00, 5.3562, 296.48, 296.48, 0, 0, "Physical Therapy", "PN032"),
        ("137716136", "joao", "2025-11-25", 34.67, 5.3823, 6.44, 0, 5.15, 1.29, "Prescription Drugs", None),
        ("137716152", "joao", "2026-01-06", 800.00, 5.3722, 148.91, 0, 148.91, 0, "Vision Exam", None),
        ("137716193", "joao", "2025-09-12", 359.80, 5.3553, 67.19, 4.31, 49.44, 17.75, "Frames", "NC010"),
        ("137716193", "joao", "2025-09-12", 535.20, 5.3553, 99.94, 99.94, 0, 99.94, "Single Vision Lenses", "NC010"),
    ]),
}


def importar_eob_itens(conn, doc_ids):
    for arquivo, (data_proc, itens) in EOB_ITENS.items():
        did = doc_ids[arquivo]
        for (claim, pac, data_srv, brl, cambio, usd, nao_cob, pago, resp, tipo_srv, remark) in itens:
            conn.execute(
                """INSERT INTO eob_itens
                   (documento_id, n_claim, paciente, data_servico, valor_brl, cambio,
                    valor_usd, nao_coberto_usd, pago_usd, resp_paciente_usd,
                    tipo_servico, remark_code, data_processado)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (did, claim, BENEFICIARIOS[pac][0], data_srv, brl, cambio,
                 usd, nao_cob, pago, resp, tipo_srv, remark, data_proc),
            )


# ---------------------------------------------------------------- main

def main():
    conn = criar_banco()
    seed_beneficiarios(conn)
    claim_para_id = importar_planilha(conn)
    importar_portal(conn, claim_para_id)
    importar_extras(conn, claim_para_id)
    doc_ids = importar_documentos(conn, claim_para_id)
    importar_eob_itens(conn, doc_ids)
    conn.commit()

    n_r = conn.execute("SELECT COUNT(*) FROM reembolsos").fetchone()[0]
    n_d = conn.execute("SELECT COUNT(*) FROM documentos").fetchone()[0]
    n_v = conn.execute("SELECT COUNT(*) FROM reembolso_documentos").fetchone()[0]
    n_e = conn.execute("SELECT COUNT(*) FROM eob_itens").fetchone()[0]
    n_s = conn.execute("SELECT COUNT(*) FROM submissoes_portal").fetchone()[0]
    tot = conn.execute("SELECT SUM(valor_pago), SUM(valor_reembolsado) FROM reembolsos").fetchone()
    print(f"Banco criado: {DB}")
    print(f"  {n_r} reembolsos | {n_d} documentos | {n_v} vínculos | {n_e} itens EOB | {n_s} submissões portal")
    print(f"  Total pago: R$ {tot[0]:,.2f} | Total reembolsado: R$ {tot[1]:,.2f}")
    conn.close()


if __name__ == "__main__":
    main()
