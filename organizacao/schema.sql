-- Central de Organização Pessoal · Priscila Palomo
-- SQLite 3 — vida, família, consultório, YouTube, finanças, projetos

PRAGMA foreign_keys = ON;

-- ── Pessoas (família e contatos) ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pessoas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL,
    apelido     TEXT,
    relacao     TEXT NOT NULL DEFAULT 'outro'
                CHECK (relacao IN ('eu', 'conjuge', 'filho', 'filha', 'paciente', 'contato', 'outro')),
    nascimento  TEXT,          -- ISO YYYY-MM-DD
    telefone    TEXT,
    email       TEXT,
    notas       TEXT,
    cor         TEXT DEFAULT '#6b7280',
    ativo       INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);

-- ── Áreas da vida ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS areas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL UNIQUE,
    icone       TEXT DEFAULT '📁',
    cor         TEXT DEFAULT '#3b82f6',
    descricao   TEXT,
    ordem       INTEGER DEFAULT 0
);

-- ── Projetos ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projetos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id         INTEGER REFERENCES areas(id),
    titulo          TEXT NOT NULL,
    descricao       TEXT,
    status          TEXT NOT NULL DEFAULT 'ativo'
                    CHECK (status IN ('ideia', 'ativo', 'pausado', 'concluido', 'arquivado')),
    prioridade      TEXT DEFAULT 'media'
                    CHECK (prioridade IN ('baixa', 'media', 'alta', 'urgente')),
    data_inicio     TEXT,
    data_prazo      TEXT,
    data_conclusao  TEXT,
    responsavel_id  INTEGER REFERENCES pessoas(id),
    tags            TEXT,
    notas           TEXT,
    criado_em       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_projetos_status ON projetos(status);
CREATE INDEX IF NOT EXISTS idx_projetos_area   ON projetos(area_id);

-- ── Tarefas ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tarefas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    projeto_id      INTEGER REFERENCES projetos(id) ON DELETE SET NULL,
    area_id         INTEGER REFERENCES areas(id),
    titulo          TEXT NOT NULL,
    descricao       TEXT,
    status          TEXT NOT NULL DEFAULT 'pendente'
                    CHECK (status IN ('pendente', 'em_andamento', 'feito', 'cancelado')),
    prioridade      TEXT DEFAULT 'media'
                    CHECK (prioridade IN ('baixa', 'media', 'alta', 'urgente')),
    data_prazo      TEXT,
    data_conclusao  TEXT,
    responsavel_id  INTEGER REFERENCES pessoas(id),
    notas           TEXT,
    criado_em       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_tarefas_status ON tarefas(status);
CREATE INDEX IF NOT EXISTS idx_tarefas_prazo  ON tarefas(data_prazo);

-- ── Pacientes (consultório) ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pacientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pessoa_id       INTEGER REFERENCES pessoas(id),
    codigo          TEXT UNIQUE,           -- ex.: PAC-001
    nome            TEXT NOT NULL,
    telefone        TEXT,
    email           TEXT,
    data_nascimento TEXT,
    cpf             TEXT,
    convenio        TEXT,
    queixa_principal TEXT,
    diagnostico     TEXT,
    status          TEXT NOT NULL DEFAULT 'ativo'
                    CHECK (status IN ('ativo', 'alta', 'pausado', 'encaminhado')),
    data_inicio     TEXT,
    data_alta       TEXT,
    valor_sessao    REAL,
    frequencia      TEXT,                  -- ex.: semanal, quinzenal
    dia_horario     TEXT,                  -- ex.: terça 14h
    prontuario_path TEXT,                  -- caminho do arquivo/pasta
    observacoes     TEXT,
    criado_em       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_pacientes_status ON pacientes(status);
CREATE INDEX IF NOT EXISTS idx_pacientes_nome   ON pacientes(nome);

-- ── Atendimentos (sessões e consultas) ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS atendimentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    data            TEXT NOT NULL,         -- ISO YYYY-MM-DD
    hora_inicio     TEXT,                  -- HH:MM
    hora_fim        TEXT,
    tipo            TEXT NOT NULL DEFAULT 'sessao'
                    CHECK (tipo IN ('sessao', 'avaliacao', 'retorno', 'online', 'presencial', 'outro')),
    modalidade      TEXT DEFAULT 'presencial'
                    CHECK (modalidade IN ('presencial', 'online', 'telefone')),
    status          TEXT NOT NULL DEFAULT 'agendado'
                    CHECK (status IN ('agendado', 'confirmado', 'realizado', 'faltou', 'cancelado', 'remarcado')),
    valor           REAL,
    pago            INTEGER DEFAULT 0 CHECK (pago IN (0, 1)),
    notas           TEXT,
    criado_em       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_atendimentos_data     ON atendimentos(data);
CREATE INDEX IF NOT EXISTS idx_atendimentos_paciente ON atendimentos(paciente_id);
CREATE INDEX IF NOT EXISTS idx_atendimentos_status   ON atendimentos(status);

-- ── Prontuários (registros clínicos por sessão) ──────────────────────────────
CREATE TABLE IF NOT EXISTS prontuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id     INTEGER NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    atendimento_id  INTEGER REFERENCES atendimentos(id) ON DELETE SET NULL,
    data_registro   TEXT NOT NULL,         -- ISO YYYY-MM-DD
    tipo            TEXT NOT NULL DEFAULT 'evolucao'
                    CHECK (tipo IN ('anamnese', 'evolucao', 'alta', 'encaminhamento', 'laudo', 'outro')),
    titulo          TEXT,
    conteudo        TEXT NOT NULL,
    confidencial    INTEGER NOT NULL DEFAULT 1 CHECK (confidencial IN (0, 1)),
    arquivo         TEXT,                  -- PDF/doc vinculado
    criado_em       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_prontuarios_paciente ON prontuarios(paciente_id);
CREATE INDEX IF NOT EXISTS idx_prontuarios_data     ON prontuarios(data_registro);

-- ── YouTube ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS youtube_ideias (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo      TEXT NOT NULL,
    descricao   TEXT,
    status      TEXT NOT NULL DEFAULT 'ideia'
                CHECK (status IN ('ideia', 'roteiro', 'gravacao', 'edicao', 'publicado', 'descartado')),
    prioridade  TEXT DEFAULT 'media',
    tags        TEXT,
    notas       TEXT,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS youtube_videos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ideia_id        INTEGER REFERENCES youtube_ideias(id) ON DELETE SET NULL,
    titulo          TEXT NOT NULL,
    descricao       TEXT,
    status          TEXT NOT NULL DEFAULT 'planejado'
                    CHECK (status IN ('planejado', 'roteiro', 'gravado', 'editado', 'agendado', 'publicado', 'arquivado')),
    data_gravacao   TEXT,
    data_publicacao TEXT,
    url             TEXT,
    duracao_min     INTEGER,
    visualizacoes   INTEGER DEFAULT 0,
    likes           INTEGER DEFAULT 0,
    roteiro         TEXT,
    thumbnail_path  TEXT,
    tags            TEXT,
    notas           TEXT,
    criado_em       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_yt_videos_status ON youtube_videos(status);

-- ── Finanças ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS financas_categorias (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL UNIQUE,
    tipo        TEXT NOT NULL CHECK (tipo IN ('receita', 'despesa')),
    area_id     INTEGER REFERENCES areas(id),
    cor         TEXT DEFAULT '#6b7280'
);

CREATE TABLE IF NOT EXISTS financas_lancamentos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id    INTEGER NOT NULL REFERENCES financas_categorias(id),
    descricao       TEXT NOT NULL,
    valor           REAL NOT NULL,
    tipo            TEXT NOT NULL CHECK (tipo IN ('receita', 'despesa')),
    data            TEXT NOT NULL,         -- ISO YYYY-MM-DD
    pago            INTEGER NOT NULL DEFAULT 1 CHECK (pago IN (0, 1)),
    recorrente      INTEGER DEFAULT 0 CHECK (recorrente IN (0, 1)),
    projeto_id      INTEGER REFERENCES projetos(id) ON DELETE SET NULL,
    paciente_id     INTEGER REFERENCES pacientes(id) ON DELETE SET NULL,
    nota_fiscal     TEXT,
    observacoes     TEXT,
    criado_em       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_financas_data      ON financas_lancamentos(data);
CREATE INDEX IF NOT EXISTS idx_financas_categoria ON financas_lancamentos(categoria_id);

-- ── Arquivos (índice de documentos) ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS arquivos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo          TEXT NOT NULL,
    caminho         TEXT NOT NULL,
    categoria       TEXT NOT NULL DEFAULT 'geral'
                    CHECK (categoria IN ('geral', 'medico', 'financeiro', 'youtube', 'consultorio',
                                          'familia', 'projeto', 'contrato', 'fiscal', 'outro')),
    area_id         INTEGER REFERENCES areas(id),
    projeto_id      INTEGER REFERENCES projetos(id) ON DELETE SET NULL,
    pessoa_id       INTEGER REFERENCES pessoas(id) ON DELETE SET NULL,
    paciente_id     INTEGER REFERENCES pacientes(id) ON DELETE SET NULL,
    data_arquivo    TEXT,
    tipo_arquivo    TEXT,                  -- pdf, xlsx, doc, img, video, outro
    descricao       TEXT,
    tags            TEXT,
    criado_em       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_arquivos_categoria ON arquivos(categoria);

-- ── Agenda (eventos unificados) ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agenda (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo          TEXT NOT NULL,
    data_inicio     TEXT NOT NULL,         -- ISO YYYY-MM-DD
    hora_inicio     TEXT,
    data_fim        TEXT,
    hora_fim        TEXT,
    tipo            TEXT NOT NULL DEFAULT 'geral'
                    CHECK (tipo IN ('atendimento', 'familia', 'youtube', 'financeiro',
                                    'medico', 'reuniao', 'prazo', 'lembrete', 'geral')),
    area_id         INTEGER REFERENCES areas(id),
    pessoa_id       INTEGER REFERENCES pessoas(id) ON DELETE SET NULL,
    paciente_id     INTEGER REFERENCES pacientes(id) ON DELETE SET NULL,
    atendimento_id  INTEGER REFERENCES atendimentos(id) ON DELETE SET NULL,
    projeto_id      INTEGER REFERENCES projetos(id) ON DELETE SET NULL,
    local           TEXT,
    status          TEXT DEFAULT 'confirmado'
                    CHECK (status IN ('confirmado', 'tentativo', 'cancelado', 'concluido')),
    lembrete        TEXT,
    notas           TEXT,
    criado_em       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_agenda_data ON agenda(data_inicio);

-- ── Notas rápidas ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo      TEXT,
    conteudo    TEXT NOT NULL,
    area_id     INTEGER REFERENCES areas(id),
    fixada      INTEGER DEFAULT 0 CHECK (fixada IN (0, 1)),
    tags        TEXT,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    atualizado  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ── Visões ───────────────────────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS vw_pacientes_resumo AS
SELECT
    p.id,
    p.codigo,
    p.nome,
    p.status,
    p.telefone,
    p.dia_horario,
    p.frequencia,
    p.valor_sessao,
    p.data_inicio,
    (SELECT COUNT(*) FROM atendimentos a WHERE a.paciente_id = p.id AND a.status = 'realizado') AS sessoes_realizadas,
    (SELECT COUNT(*) FROM atendimentos a WHERE a.paciente_id = p.id AND a.status IN ('agendado','confirmado')) AS proximos_agendados,
    (SELECT MAX(a.data) FROM atendimentos a WHERE a.paciente_id = p.id AND a.status = 'realizado') AS ultima_sessao,
    (SELECT MIN(a.data) FROM atendimentos a WHERE a.paciente_id = p.id AND a.status IN ('agendado','confirmado') AND a.data >= date('now')) AS proxima_sessao,
    (SELECT COUNT(*) FROM prontuarios pr WHERE pr.paciente_id = p.id) AS registros_prontuario
FROM pacientes p;

CREATE VIEW IF NOT EXISTS vw_agenda_proxima AS
SELECT
    ag.*,
    pe.nome AS pessoa_nome,
    pa.nome AS paciente_nome,
    ar.nome AS area_nome
FROM agenda ag
LEFT JOIN pessoas pe ON pe.id = ag.pessoa_id
LEFT JOIN pacientes pa ON pa.id = ag.paciente_id
LEFT JOIN areas ar ON ar.id = ag.area_id
WHERE ag.data_inicio >= date('now', '-7 days')
ORDER BY ag.data_inicio, ag.hora_inicio;

CREATE VIEW IF NOT EXISTS vw_financas_mes AS
SELECT
    strftime('%Y-%m', f.data) AS mes,
    f.tipo,
    c.nome AS categoria,
    SUM(f.valor) AS total,
    COUNT(*) AS qtd
FROM financas_lancamentos f
JOIN financas_categorias c ON c.id = f.categoria_id
GROUP BY mes, f.tipo, c.nome;

CREATE VIEW IF NOT EXISTS vw_dashboard AS
SELECT
    (SELECT COUNT(*) FROM pacientes WHERE status = 'ativo')           AS pacientes_ativos,
    (SELECT COUNT(*) FROM atendimentos WHERE data = date('now'))      AS atendimentos_hoje,
    (SELECT COUNT(*) FROM atendimentos WHERE status IN ('agendado','confirmado') AND data BETWEEN date('now') AND date('now','+7 days')) AS atendimentos_semana,
    (SELECT COUNT(*) FROM tarefas WHERE status IN ('pendente','em_andamento')) AS tarefas_abertas,
    (SELECT COUNT(*) FROM projetos WHERE status = 'ativo')            AS projetos_ativos,
    (SELECT COUNT(*) FROM youtube_videos WHERE status NOT IN ('publicado','arquivado')) AS videos_em_producao,
    (SELECT COUNT(*) FROM agenda WHERE data_inicio BETWEEN date('now') AND date('now','+7 days') AND status != 'cancelado') AS eventos_semana,
    (SELECT COALESCE(SUM(valor),0) FROM financas_lancamentos WHERE tipo='receita' AND strftime('%Y-%m',data)=strftime('%Y-%m','now')) AS receita_mes,
    (SELECT COALESCE(SUM(valor),0) FROM financas_lancamentos WHERE tipo='despesa' AND strftime('%Y-%m',data)=strftime('%Y-%m','now')) AS despesa_mes;
