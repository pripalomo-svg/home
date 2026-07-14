-- Hub pessoal de organização — banco central único
-- SQLite 3. Uma só base para projetos, arquivos, finanças, YouTube,
-- consultório (pacientes/prontuários/atendimentos) e família.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Núcleo: áreas da vida, projetos, tarefas e arquivos
-- ---------------------------------------------------------------------------

-- Grandes áreas da vida (Financeiro, YouTube, Consultório, Família, Pessoal...)
CREATE TABLE IF NOT EXISTS areas (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT NOT NULL UNIQUE,
    icone     TEXT,                       -- emoji para o painel
    cor       TEXT,                       -- cor hex (#rrggbb) usada nos rótulos
    descricao TEXT,
    ordem     INTEGER DEFAULT 0
);

-- Projetos (qualquer iniciativa com começo/fim, ligada a uma área)
CREATE TABLE IF NOT EXISTS projetos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id        INTEGER REFERENCES areas(id) ON DELETE SET NULL,
    titulo         TEXT NOT NULL,
    descricao      TEXT,
    status         TEXT NOT NULL DEFAULT 'ideia'
                   CHECK (status IN ('ideia','em_andamento','pausado','concluido','arquivado')),
    prioridade     TEXT NOT NULL DEFAULT 'media'
                   CHECK (prioridade IN ('baixa','media','alta')),
    progresso      INTEGER DEFAULT 0 CHECK (progresso BETWEEN 0 AND 100),
    data_inicio    TEXT,                  -- ISO YYYY-MM-DD
    data_prazo     TEXT,
    data_conclusao TEXT,
    proxima_acao   TEXT,                  -- o próximo passo concreto
    observacoes    TEXT,
    criado_em      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_projetos_area   ON projetos(area_id);
CREATE INDEX IF NOT EXISTS idx_projetos_status ON projetos(status);
CREATE INDEX IF NOT EXISTS idx_projetos_prazo  ON projetos(data_prazo);

-- Tarefas (passos de um projeto ou soltas do dia a dia)
CREATE TABLE IF NOT EXISTS tarefas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    projeto_id   INTEGER REFERENCES projetos(id) ON DELETE SET NULL,
    area_id      INTEGER REFERENCES areas(id) ON DELETE SET NULL,
    titulo       TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'a_fazer'
                 CHECK (status IN ('a_fazer','fazendo','feito')),
    prioridade   TEXT NOT NULL DEFAULT 'media'
                 CHECK (prioridade IN ('baixa','media','alta')),
    prazo        TEXT,                    -- ISO
    concluida_em TEXT,
    observacoes  TEXT
);

CREATE INDEX IF NOT EXISTS idx_tarefas_projeto ON tarefas(projeto_id);
CREATE INDEX IF NOT EXISTS idx_tarefas_status  ON tarefas(status);

-- Arquivos/documentos organizados por área e/ou projeto
CREATE TABLE IF NOT EXISTS arquivos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo       TEXT NOT NULL,
    caminho      TEXT,                    -- caminho/URL do arquivo
    categoria    TEXT,                    -- contrato, nota, roteiro, foto, planilha, exame...
    area_id      INTEGER REFERENCES areas(id) ON DELETE SET NULL,
    projeto_id   INTEGER REFERENCES projetos(id) ON DELETE SET NULL,
    data_arquivo TEXT,                    -- ISO
    tags         TEXT,                    -- palavras-chave separadas por vírgula
    descricao    TEXT
);

CREATE INDEX IF NOT EXISTS idx_arquivos_area    ON arquivos(area_id);
CREATE INDEX IF NOT EXISTS idx_arquivos_projeto ON arquivos(projeto_id);

-- ---------------------------------------------------------------------------
-- Financeiro
-- ---------------------------------------------------------------------------

-- Contas/carteiras (banco, cartão, dinheiro, investimento)
CREATE TABLE IF NOT EXISTS contas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL UNIQUE,
    tipo          TEXT DEFAULT 'corrente'
                  CHECK (tipo IN ('corrente','poupanca','cartao','dinheiro','investimento','outro')),
    instituicao   TEXT,
    saldo_inicial REAL DEFAULT 0
);

-- Categorias de receita/despesa
CREATE TABLE IF NOT EXISTS categorias_fin (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome  TEXT NOT NULL,
    tipo  TEXT NOT NULL DEFAULT 'despesa' CHECK (tipo IN ('receita','despesa')),
    grupo TEXT,                           -- casa, saúde, educação, consultório, youtube...
    UNIQUE (nome, tipo)
);

-- Lançamentos financeiros (entradas e saídas)
CREATE TABLE IF NOT EXISTS transacoes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    data         TEXT NOT NULL,           -- ISO YYYY-MM-DD
    descricao    TEXT NOT NULL,
    tipo         TEXT NOT NULL DEFAULT 'despesa'
                 CHECK (tipo IN ('receita','despesa','transferencia')),
    valor        REAL NOT NULL CHECK (valor >= 0),
    conta_id     INTEGER REFERENCES contas(id) ON DELETE SET NULL,
    categoria_id INTEGER REFERENCES categorias_fin(id) ON DELETE SET NULL,
    projeto_id   INTEGER REFERENCES projetos(id) ON DELETE SET NULL,
    status       TEXT NOT NULL DEFAULT 'realizado'
                 CHECK (status IN ('previsto','realizado')),
    recorrente   INTEGER NOT NULL DEFAULT 0 CHECK (recorrente IN (0,1)),
    observacoes  TEXT
);

CREATE INDEX IF NOT EXISTS idx_transacoes_data ON transacoes(data);
CREATE INDEX IF NOT EXISTS idx_transacoes_tipo ON transacoes(tipo);

-- Metas (financeiras ou de qualquer área)
CREATE TABLE IF NOT EXISTS metas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id     INTEGER REFERENCES areas(id) ON DELETE SET NULL,
    titulo      TEXT NOT NULL,
    valor_alvo  REAL,
    valor_atual REAL DEFAULT 0,
    unidade     TEXT DEFAULT 'R$',        -- R$, inscritos, kg, sessões...
    prazo       TEXT,
    observacoes TEXT
);

-- ---------------------------------------------------------------------------
-- YouTube (e outros canais de conteúdo)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS canais (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT NOT NULL UNIQUE,
    plataforma    TEXT DEFAULT 'YouTube',
    url           TEXT,
    meta_inscritos INTEGER,
    observacoes   TEXT
);

CREATE TABLE IF NOT EXISTS videos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    canal_id        INTEGER REFERENCES canais(id) ON DELETE SET NULL,
    titulo          TEXT NOT NULL,
    tema            TEXT,
    status          TEXT NOT NULL DEFAULT 'ideia'
                    CHECK (status IN ('ideia','roteiro','gravacao','edicao','agendado','publicado')),
    data_ideia      TEXT,
    data_gravacao   TEXT,
    data_publicacao TEXT,
    url             TEXT,
    roteiro         TEXT,                 -- rascunho/roteiro do vídeo
    views           INTEGER DEFAULT 0,
    observacoes     TEXT
);

CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);

-- ---------------------------------------------------------------------------
-- Consultório: pacientes, prontuários, evoluções e atendimentos
-- (DADOS SENSÍVEIS — ver aviso de LGPD no README)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS pacientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    data_nascimento TEXT,                 -- ISO
    telefone        TEXT,
    email           TEXT,
    responsavel     TEXT,                 -- para menores de idade
    convenio        TEXT,                 -- particular / nome do plano
    status          TEXT NOT NULL DEFAULT 'ativo'
                    CHECK (status IN ('ativo','inativo','alta')),
    observacoes     TEXT,
    criado_em       TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_pacientes_status ON pacientes(status);

-- Prontuário: um por paciente (cabeçalho clínico)
CREATE TABLE IF NOT EXISTS prontuarios (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id          INTEGER NOT NULL UNIQUE REFERENCES pacientes(id) ON DELETE CASCADE,
    queixa_principal     TEXT,
    historico            TEXT,
    hipotese_diagnostica TEXT,
    cid                  TEXT,
    plano_terapeutico    TEXT,
    atualizado_em        TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Atendimentos / agenda do consultório
CREATE TABLE IF NOT EXISTS atendimentos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id    INTEGER NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    data           TEXT NOT NULL,         -- ISO
    hora_inicio    TEXT,                  -- HH:MM
    hora_fim       TEXT,
    tipo           TEXT DEFAULT 'sessao'
                   CHECK (tipo IN ('avaliacao','consulta','sessao','retorno','outro')),
    modalidade     TEXT DEFAULT 'presencial'
                   CHECK (modalidade IN ('presencial','online')),
    status         TEXT NOT NULL DEFAULT 'agendado'
                   CHECK (status IN ('agendado','confirmado','realizado','faltou','cancelado')),
    valor          REAL DEFAULT 0,
    pago           INTEGER NOT NULL DEFAULT 0 CHECK (pago IN (0,1)),
    forma_pagamento TEXT,
    observacoes    TEXT
);

CREATE INDEX IF NOT EXISTS idx_atendimentos_paciente ON atendimentos(paciente_id);
CREATE INDEX IF NOT EXISTS idx_atendimentos_data     ON atendimentos(data);
CREATE INDEX IF NOT EXISTS idx_atendimentos_status   ON atendimentos(status);

-- Evoluções: anotações sessão a sessão dentro do prontuário
CREATE TABLE IF NOT EXISTS evolucoes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    prontuario_id  INTEGER NOT NULL REFERENCES prontuarios(id) ON DELETE CASCADE,
    atendimento_id INTEGER REFERENCES atendimentos(id) ON DELETE SET NULL,
    data           TEXT NOT NULL,         -- ISO
    conteudo       TEXT NOT NULL,
    criado_em      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_evolucoes_prontuario ON evolucoes(prontuario_id);

-- ---------------------------------------------------------------------------
-- Família e agenda pessoal
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS familiares (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    parentesco      TEXT,                 -- esposa, filho, filha...
    data_nascimento TEXT,                 -- ISO
    telefone        TEXT,
    observacoes     TEXT
);

-- Eventos / compromissos pessoais e da família (aniversários, escola, saúde, viagens, lembretes)
CREATE TABLE IF NOT EXISTS eventos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo       TEXT NOT NULL,
    categoria    TEXT DEFAULT 'lembrete'
                 CHECK (categoria IN ('aniversario','escola','saude','viagem','reuniao','financeiro','lembrete','outro')),
    familiar_id  INTEGER REFERENCES familiares(id) ON DELETE SET NULL,
    area_id      INTEGER REFERENCES areas(id) ON DELETE SET NULL,
    data         TEXT NOT NULL,           -- ISO
    hora         TEXT,                    -- HH:MM
    local        TEXT,
    recorrente   INTEGER NOT NULL DEFAULT 0 CHECK (recorrente IN (0,1)),
    concluido    INTEGER NOT NULL DEFAULT 0 CHECK (concluido IN (0,1)),
    observacoes  TEXT
);

CREATE INDEX IF NOT EXISTS idx_eventos_data ON eventos(data);

-- ---------------------------------------------------------------------------
-- Visões consolidadas para consultas rápidas
-- ---------------------------------------------------------------------------

-- Projetos com o nome da área
CREATE VIEW IF NOT EXISTS vw_projetos AS
SELECT p.*, a.nome AS area, a.icone AS area_icone, a.cor AS area_cor
FROM projetos p
LEFT JOIN areas a ON a.id = p.area_id;

-- Pacientes com resumo de atendimentos
CREATE VIEW IF NOT EXISTS vw_pacientes AS
SELECT
    pa.id,
    pa.nome,
    pa.status,
    pa.convenio,
    (SELECT COUNT(*) FROM atendimentos at WHERE at.paciente_id = pa.id) AS total_atendimentos,
    (SELECT COUNT(*) FROM atendimentos at WHERE at.paciente_id = pa.id AND at.status = 'realizado') AS realizados,
    (SELECT MAX(at.data) FROM atendimentos at WHERE at.paciente_id = pa.id AND at.status = 'realizado') AS ultimo_atendimento,
    (SELECT MIN(at.data) FROM atendimentos at WHERE at.paciente_id = pa.id AND at.data >= date('now') AND at.status IN ('agendado','confirmado')) AS proximo_atendimento,
    pr.id AS prontuario_id
FROM pacientes pa
LEFT JOIN prontuarios pr ON pr.paciente_id = pa.id;

-- Resumo financeiro por mês (apenas lançamentos realizados)
CREATE VIEW IF NOT EXISTS vw_financeiro_mensal AS
SELECT
    substr(data, 1, 7) AS mes,
    ROUND(SUM(CASE WHEN tipo = 'receita' THEN valor ELSE 0 END), 2) AS receitas,
    ROUND(SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END), 2) AS despesas,
    ROUND(SUM(CASE WHEN tipo = 'receita' THEN valor
                   WHEN tipo = 'despesa' THEN -valor ELSE 0 END), 2) AS saldo
FROM transacoes
WHERE status = 'realizado'
GROUP BY mes
ORDER BY mes DESC;

-- Agenda unificada: atendimentos + eventos + prazos de projetos/tarefas
CREATE VIEW IF NOT EXISTS vw_agenda AS
SELECT 'atendimento' AS tipo, at.data AS data, at.hora_inicio AS hora,
       (pa.nome || ' — ' || at.tipo) AS titulo, at.status AS status
FROM atendimentos at JOIN pacientes pa ON pa.id = at.paciente_id
UNION ALL
SELECT 'evento' AS tipo, e.data, e.hora, e.titulo,
       CASE WHEN e.concluido = 1 THEN 'concluido' ELSE 'pendente' END
FROM eventos e
UNION ALL
SELECT 'projeto' AS tipo, p.data_prazo, NULL, ('Prazo: ' || p.titulo), p.status
FROM projetos p WHERE p.data_prazo IS NOT NULL AND p.status NOT IN ('concluido','arquivado')
UNION ALL
SELECT 'tarefa' AS tipo, t.prazo, NULL, ('Tarefa: ' || t.titulo), t.status
FROM tarefas t WHERE t.prazo IS NOT NULL AND t.status <> 'feito'
ORDER BY data;
