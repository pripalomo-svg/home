-- Organizador pessoal — banco de dados central da vida
-- Áreas: financeiro, YouTube, consultório (pacientes/prontuários/atendimentos),
--        família, projetos/tarefas e catálogo de arquivos.
-- SQLite 3

PRAGMA foreign_keys = ON;

-- Áreas da vida (Financeiro, YouTube, Consultório, Família, Pessoal, Casa...)
CREATE TABLE IF NOT EXISTS areas (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nome   TEXT NOT NULL UNIQUE,
    icone  TEXT,
    cor    TEXT
);

-- ─── Projetos e tarefas ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS projetos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id     INTEGER REFERENCES areas(id),
    nome        TEXT NOT NULL,
    descricao   TEXT,
    status      TEXT NOT NULL DEFAULT 'ativo'
                CHECK (status IN ('ideia','ativo','pausado','concluido','arquivado')),
    prioridade  TEXT DEFAULT 'media' CHECK (prioridade IN ('baixa','media','alta')),
    prazo       TEXT,                          -- ISO: YYYY-MM-DD
    criado_em   TEXT NOT NULL DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS tarefas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    projeto_id   INTEGER REFERENCES projetos(id) ON DELETE SET NULL,
    area_id      INTEGER REFERENCES areas(id),
    titulo       TEXT NOT NULL,
    notas        TEXT,
    data_limite  TEXT,                         -- ISO: YYYY-MM-DD
    prioridade   TEXT DEFAULT 'media' CHECK (prioridade IN ('baixa','media','alta')),
    status       TEXT NOT NULL DEFAULT 'pendente'
                 CHECK (status IN ('pendente','fazendo','concluida','cancelada')),
    concluida_em TEXT
);

CREATE INDEX IF NOT EXISTS idx_tarefas_status ON tarefas(status);
CREATE INDEX IF NOT EXISTS idx_tarefas_data   ON tarefas(data_limite);

-- ─── Vida financeira ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fin_lancamentos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    data        TEXT NOT NULL,                 -- ISO: YYYY-MM-DD
    tipo        TEXT NOT NULL CHECK (tipo IN ('receita','despesa')),
    categoria   TEXT,                          -- salário, consultório, youtube, mercado, escola...
    descricao   TEXT NOT NULL,
    valor       REAL NOT NULL CHECK (valor >= 0),
    conta       TEXT,                          -- banco/cartão/dinheiro
    pago        INTEGER NOT NULL DEFAULT 1,    -- 0 = previsto, 1 = efetivado
    recorrente  INTEGER NOT NULL DEFAULT 0,
    observacoes TEXT
);

CREATE INDEX IF NOT EXISTS idx_fin_data ON fin_lancamentos(data);
CREATE INDEX IF NOT EXISTS idx_fin_tipo ON fin_lancamentos(tipo);

-- ─── Canal do YouTube ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS yt_videos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo          TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'ideia'
                    CHECK (status IN ('ideia','roteiro','gravacao','edicao','agendado','publicado')),
    data_prevista   TEXT,                      -- ISO
    data_publicacao TEXT,                      -- ISO
    link            TEXT,
    notas           TEXT
);

CREATE INDEX IF NOT EXISTS idx_yt_status ON yt_videos(status);

-- ─── Consultório: pacientes, prontuários e atendimentos ────────────────────

CREATE TABLE IF NOT EXISTS pacientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    telefone        TEXT,
    email           TEXT,
    data_nascimento TEXT,                      -- ISO
    convenio        TEXT,                      -- particular, plano...
    ativo           INTEGER NOT NULL DEFAULT 1,
    observacoes     TEXT
);

-- Prontuário 1:1 com o paciente (ficha clínica)
CREATE TABLE IF NOT EXISTS prontuarios (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id          INTEGER NOT NULL UNIQUE REFERENCES pacientes(id) ON DELETE CASCADE,
    data_abertura        TEXT NOT NULL DEFAULT (date('now')),
    queixa_principal     TEXT,
    historico            TEXT,
    hipotese_diagnostica TEXT,
    plano_terapeutico    TEXT,
    observacoes          TEXT
);

CREATE TABLE IF NOT EXISTS atendimentos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    data        TEXT NOT NULL,                 -- ISO
    hora        TEXT,                          -- HH:MM
    tipo        TEXT DEFAULT 'consulta',       -- consulta, retorno, avaliacao, online...
    status      TEXT NOT NULL DEFAULT 'agendado'
                CHECK (status IN ('agendado','realizado','cancelado','faltou')),
    valor       REAL NOT NULL DEFAULT 0,
    pago        INTEGER NOT NULL DEFAULT 0,
    evolucao    TEXT                           -- evolução clínica da sessão
);

CREATE INDEX IF NOT EXISTS idx_atend_data     ON atendimentos(data);
CREATE INDEX IF NOT EXISTS idx_atend_paciente ON atendimentos(paciente_id);

-- ─── Família ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS familia_membros (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    parentesco      TEXT,                      -- esposa, filho(a)...
    data_nascimento TEXT,                      -- ISO
    notas           TEXT
);

CREATE TABLE IF NOT EXISTS familia_eventos (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    membro_id INTEGER REFERENCES familia_membros(id) ON DELETE SET NULL,
    data      TEXT NOT NULL,                   -- ISO
    hora      TEXT,                            -- HH:MM
    titulo    TEXT NOT NULL,
    tipo      TEXT DEFAULT 'outro',            -- escola, saude, lazer, casa, aniversario, outro
    notas     TEXT
);

CREATE INDEX IF NOT EXISTS idx_fam_eventos_data ON familia_eventos(data);

-- ─── Catálogo de arquivos ──────────────────────────────────────────────────
-- Registro de onde está cada arquivo importante (o arquivo em si fica em
-- organizador/arquivos/ ou em qualquer outro lugar — aqui só o índice).

CREATE TABLE IF NOT EXISTS arquivos (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    caminho   TEXT NOT NULL,                   -- caminho ou URL do arquivo
    titulo    TEXT,
    area_id   INTEGER REFERENCES areas(id),
    categoria TEXT,                            -- contrato, nota_fiscal, exame, foto, video, documento...
    data      TEXT,                            -- ISO
    descricao TEXT
);

CREATE INDEX IF NOT EXISTS idx_arquivos_area ON arquivos(area_id);

-- ─── Visões ────────────────────────────────────────────────────────────────

-- Agenda unificada: atendimentos + eventos da família + tarefas com prazo
CREATE VIEW IF NOT EXISTS vw_agenda AS
SELECT 'atendimento' AS origem, a.id, a.data, a.hora,
       'Atendimento: ' || p.nome AS titulo, a.status AS detalhe
  FROM atendimentos a JOIN pacientes p ON p.id = a.paciente_id
UNION ALL
SELECT 'familia', e.id, e.data, e.hora,
       e.titulo || COALESCE(' (' || m.nome || ')', ''), e.tipo
  FROM familia_eventos e LEFT JOIN familia_membros m ON m.id = e.membro_id
UNION ALL
SELECT 'tarefa', t.id, t.data_limite, NULL, t.titulo, t.status
  FROM tarefas t
 WHERE t.data_limite IS NOT NULL AND t.status IN ('pendente','fazendo')
ORDER BY data, hora;

-- Resumo financeiro por mês
CREATE VIEW IF NOT EXISTS vw_fin_mensal AS
SELECT substr(data, 1, 7) AS mes,
       ROUND(SUM(CASE WHEN tipo = 'receita' THEN valor ELSE 0 END), 2) AS receitas,
       ROUND(SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END), 2) AS despesas,
       ROUND(SUM(CASE WHEN tipo = 'receita' THEN valor ELSE -valor END), 2) AS saldo
  FROM fin_lancamentos
 GROUP BY mes
 ORDER BY mes;

-- Pacientes com contagem de atendimentos e próxima sessão agendada
CREATE VIEW IF NOT EXISTS vw_pacientes AS
SELECT p.id, p.nome, p.telefone, p.convenio, p.ativo,
       (SELECT COUNT(*) FROM atendimentos a
         WHERE a.paciente_id = p.id AND a.status = 'realizado')  AS sessoes_realizadas,
       (SELECT MIN(a.data) FROM atendimentos a
         WHERE a.paciente_id = p.id AND a.status = 'agendado'
           AND a.data >= date('now'))                            AS proxima_sessao
  FROM pacientes p;
