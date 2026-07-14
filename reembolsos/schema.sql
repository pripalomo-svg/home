-- Banco de dados de reembolsos do plano de saúde (Cigna / McKinsey)
-- SQLite 3

PRAGMA foreign_keys = ON;

-- Beneficiários cobertos pelo plano (titular e dependentes)
CREATE TABLE IF NOT EXISTS beneficiarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL UNIQUE,
    parentesco  TEXT DEFAULT 'titular',  -- titular, conjuge, filho(a), etc.
    cpf         TEXT
);

-- Prestadores de serviço (médicos, clínicas, laboratórios, terapeutas)
CREATE TABLE IF NOT EXISTS prestadores (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL UNIQUE,
    especialidade TEXT,
    cpf_cnpj      TEXT
);

-- Solicitações de reembolso (claims)
CREATE TABLE IF NOT EXISTS reembolsos (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    funcionario          TEXT,                       -- titular do plano na empresa
    beneficiario_id      INTEGER NOT NULL REFERENCES beneficiarios(id),
    prestador_id         INTEGER REFERENCES prestadores(id),
    tipo                 TEXT NOT NULL,              -- consulta, exame, terapia, medicamento, produto, cirurgia, honorario, outro
    descricao            TEXT,
    data_atendimento     TEXT NOT NULL,              -- ISO: YYYY-MM-DD (data do recibo/atendimento)
    data_solicitacao     TEXT,
    data_pagamento       TEXT,                       -- data do acerto em folha / pagamento
    valor_pago           REAL NOT NULL CHECK (valor_pago >= 0),        -- valor desembolsado (R$)
    valor_reembolsado    REAL DEFAULT 0 CHECK (valor_reembolsado >= 0),
    status               TEXT NOT NULL DEFAULT 'solicitado'
                         CHECK (status IN ('solicitado', 'em_analise', 'pago', 'pago_parcial', 'negado')),
    situacao             TEXT,                       -- situação textual (ex.: 'enviado ao HR', 'aguardando resposta da cigna')
    n_claim              TEXT,                       -- nº do claim na Cigna
    novo_n_claim         TEXT,                       -- nº do claim após reconsideração
    comentario_cigna     TEXT,                       -- comentário/remark da Cigna
    texto_reconsideracao TEXT,
    nota_fiscal          TEXT,                       -- nº da NF/recibo
    origem               TEXT DEFAULT 'planilha',    -- planilha, eob, portal_2026, manual
    observacoes          TEXT,
    criado_em            TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_reembolsos_data   ON reembolsos(data_atendimento);
CREATE INDEX IF NOT EXISTS idx_reembolsos_status ON reembolsos(status);
CREATE INDEX IF NOT EXISTS idx_reembolsos_claim  ON reembolsos(n_claim);

-- Documentos digitalizados (NFs, recibos, EOBs, receitas, pedidos de exame...)
CREATE TABLE IF NOT EXISTS documentos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo        TEXT NOT NULL UNIQUE,   -- caminho relativo dentro de documentos/
    titulo         TEXT NOT NULL,
    categoria      TEXT NOT NULL,          -- nota_fiscal, recibo, eob, receita, pedido_exame, relatorio_medico, plano, referencia
    data_documento TEXT,                   -- ISO: YYYY-MM-DD
    descricao      TEXT
);

-- Vínculo N:N entre reembolsos e documentos (um EOB cobre vários claims)
CREATE TABLE IF NOT EXISTS reembolso_documentos (
    reembolso_id INTEGER NOT NULL REFERENCES reembolsos(id) ON DELETE CASCADE,
    documento_id INTEGER NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    papel        TEXT,                     -- nota_fiscal, recibo, eob, receita, pedido_exame, relatorio
    PRIMARY KEY (reembolso_id, documento_id)
);

-- Linhas de serviço detalhadas dos Explanation of Benefits da Cigna
CREATE TABLE IF NOT EXISTS eob_itens (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id      INTEGER REFERENCES documentos(id),
    n_claim           TEXT NOT NULL,
    paciente          TEXT NOT NULL,
    data_servico      TEXT NOT NULL,       -- ISO
    valor_brl         REAL NOT NULL,
    cambio            REAL,
    valor_usd         REAL,
    nao_coberto_usd   REAL DEFAULT 0,
    pago_usd          REAL DEFAULT 0,
    resp_paciente_usd REAL DEFAULT 0,
    tipo_servico      TEXT,
    remark_code       TEXT,
    data_processado   TEXT
);

CREATE INDEX IF NOT EXISTS idx_eob_claim ON eob_itens(n_claim);

-- Submissões feitas no novo portal Cigna (2026), com nº de submissão e CLM
CREATE TABLE IF NOT EXISTS submissoes_portal (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    reembolso_id    INTEGER REFERENCES reembolsos(id),
    paciente        TEXT NOT NULL,
    valor_brl       REAL NOT NULL,
    n_submissao     TEXT NOT NULL UNIQUE,
    n_clm           TEXT,
    data_tratamento TEXT,                  -- ISO
    tipo            TEXT,                  -- CONSULTATION, PRODUCT...
    status          TEXT DEFAULT 'Submitted'
);

-- Visão consolidada para consultas rápidas
CREATE VIEW IF NOT EXISTS vw_reembolsos AS
SELECT
    r.id,
    b.nome                                   AS beneficiario,
    p.nome                                   AS prestador,
    p.especialidade,
    r.tipo,
    r.descricao,
    r.data_atendimento,
    r.data_pagamento,
    r.valor_pago,
    r.valor_reembolsado,
    ROUND(r.valor_pago - r.valor_reembolsado, 2) AS diferenca,
    r.status,
    r.situacao,
    r.n_claim,
    r.novo_n_claim,
    r.comentario_cigna,
    r.nota_fiscal,
    r.origem,
    r.observacoes,
    (SELECT GROUP_CONCAT(d.arquivo, '; ')
       FROM reembolso_documentos rd JOIN documentos d ON d.id = rd.documento_id
      WHERE rd.reembolso_id = r.id)             AS documentos
FROM reembolsos r
JOIN beneficiarios b ON b.id = r.beneficiario_id
LEFT JOIN prestadores p ON p.id = r.prestador_id;
