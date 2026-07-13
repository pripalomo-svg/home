-- Banco de dados de reembolsos do plano de saúde
-- SQLite 3

PRAGMA foreign_keys = ON;

-- Beneficiários cobertos pelo plano (titular e dependentes)
CREATE TABLE IF NOT EXISTS beneficiarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL UNIQUE,
    parentesco  TEXT DEFAULT 'titular'  -- titular, conjuge, filho(a), etc.
);

-- Prestadores de serviço (médicos, clínicas, laboratórios, terapeutas)
CREATE TABLE IF NOT EXISTS prestadores (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL UNIQUE,
    especialidade TEXT,
    cpf_cnpj      TEXT
);

-- Solicitações de reembolso
CREATE TABLE IF NOT EXISTS reembolsos (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    protocolo          TEXT,                          -- nº do protocolo na operadora
    beneficiario_id    INTEGER NOT NULL REFERENCES beneficiarios(id),
    prestador_id       INTEGER REFERENCES prestadores(id),
    tipo               TEXT NOT NULL,                 -- consulta, exame, terapia, medicamento, outro
    descricao          TEXT,
    data_atendimento   TEXT NOT NULL,                 -- ISO: YYYY-MM-DD
    data_solicitacao   TEXT,
    data_pagamento     TEXT,
    valor_pago         REAL NOT NULL CHECK (valor_pago >= 0),        -- valor desembolsado
    valor_reembolsado  REAL DEFAULT 0 CHECK (valor_reembolsado >= 0),
    status             TEXT NOT NULL DEFAULT 'solicitado'
                       CHECK (status IN ('solicitado', 'em_analise', 'pago', 'pago_parcial', 'negado')),
    nota_fiscal        TEXT,                          -- nº da NF/recibo
    observacoes        TEXT,
    criado_em          TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_reembolsos_data   ON reembolsos(data_atendimento);
CREATE INDEX IF NOT EXISTS idx_reembolsos_status ON reembolsos(status);

-- Visão consolidada para consultas rápidas
CREATE VIEW IF NOT EXISTS vw_reembolsos AS
SELECT
    r.id,
    r.protocolo,
    b.nome                                   AS beneficiario,
    p.nome                                   AS prestador,
    p.especialidade,
    r.tipo,
    r.descricao,
    r.data_atendimento,
    r.data_solicitacao,
    r.data_pagamento,
    r.valor_pago,
    r.valor_reembolsado,
    ROUND(r.valor_pago - r.valor_reembolsado, 2) AS diferenca,
    r.status,
    r.nota_fiscal,
    r.observacoes
FROM reembolsos r
JOIN beneficiarios b ON b.id = r.beneficiario_id
LEFT JOIN prestadores p ON p.id = r.prestador_id;
