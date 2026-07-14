PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    icone TEXT NOT NULL,
    cor TEXT NOT NULL,
    descricao TEXT
);

CREATE TABLE IF NOT EXISTS pessoas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('eu', 'conjuge', 'filho', 'paciente', 'contato')),
    telefone TEXT,
    email TEXT,
    observacoes TEXT,
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projetos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id INTEGER NOT NULL REFERENCES areas(id),
    nome TEXT NOT NULL,
    descricao TEXT,
    status TEXT NOT NULL DEFAULT 'ideia'
        CHECK (status IN ('ideia', 'planejado', 'em_andamento', 'pausado', 'concluido', 'arquivado')),
    prioridade TEXT NOT NULL DEFAULT 'media'
        CHECK (prioridade IN ('baixa', 'media', 'alta')),
    proxima_acao TEXT,
    prazo TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tarefas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projeto_id INTEGER REFERENCES projetos(id) ON DELETE SET NULL,
    area_id INTEGER REFERENCES areas(id),
    titulo TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'aberta'
        CHECK (status IN ('aberta', 'fazendo', 'concluida', 'cancelada')),
    prioridade TEXT NOT NULL DEFAULT 'media'
        CHECK (prioridade IN ('baixa', 'media', 'alta')),
    prazo TEXT,
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS atendimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL REFERENCES pessoas(id),
    data_hora TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'consulta',
    status TEXT NOT NULL DEFAULT 'agendado'
        CHECK (status IN ('agendado', 'confirmado', 'realizado', 'cancelado', 'faltou')),
    valor REAL NOT NULL DEFAULT 0 CHECK (valor >= 0),
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prontuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL REFERENCES pessoas(id),
    atendimento_id INTEGER REFERENCES atendimentos(id) ON DELETE SET NULL,
    data_registro TEXT NOT NULL,
    titulo TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lancamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    descricao TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('receita', 'despesa')),
    categoria TEXT NOT NULL,
    valor REAL NOT NULL CHECK (valor >= 0),
    status TEXT NOT NULL DEFAULT 'previsto'
        CHECK (status IN ('previsto', 'pago', 'recebido', 'atrasado')),
    pessoa_id INTEGER REFERENCES pessoas(id) ON DELETE SET NULL,
    projeto_id INTEGER REFERENCES projetos(id) ON DELETE SET NULL,
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS arquivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id INTEGER NOT NULL REFERENCES areas(id),
    projeto_id INTEGER REFERENCES projetos(id) ON DELETE SET NULL,
    pessoa_id INTEGER REFERENCES pessoas(id) ON DELETE SET NULL,
    nome TEXT NOT NULL,
    caminho TEXT NOT NULL UNIQUE,
    categoria TEXT NOT NULL DEFAULT 'outro',
    descricao TEXT,
    tags TEXT,
    data_documento TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projetos_status ON projetos(status);
CREATE INDEX IF NOT EXISTS idx_tarefas_prazo ON tarefas(prazo);
CREATE INDEX IF NOT EXISTS idx_atendimentos_data ON atendimentos(data_hora);
CREATE INDEX IF NOT EXISTS idx_prontuarios_paciente ON prontuarios(paciente_id, data_registro);
CREATE INDEX IF NOT EXISTS idx_lancamentos_data ON lancamentos(data);
CREATE INDEX IF NOT EXISTS idx_arquivos_area ON arquivos(area_id);
