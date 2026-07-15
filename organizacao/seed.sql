-- Dados iniciais · Família Palomo + estrutura vazia para preencher

-- Pessoas
INSERT OR IGNORE INTO pessoas (id, nome, apelido, relacao, cor, notas) VALUES
(1, 'Priscila Palomo', 'Priscila', 'eu', '#e94560', 'Dra. em Psicologia. Especialista em fobias. Consultório próprio.'),
(2, 'Luisa Juliana Faria Ramalho de Souza', 'Luisa', 'conjuge', '#7c5cde', 'Parceira. Mãe das crianças.'),
(3, 'João Guilherme', 'JG', 'filho', '#3b82f6', 'Urologia, Oftalmologia, Alergologia'),
(4, 'Ana Luisa', 'Ana Luisa', 'filha', '#10b981', 'Oftalmologia, Pediatra');

-- Áreas da vida
INSERT OR IGNORE INTO areas (id, nome, icone, cor, descricao, ordem) VALUES
(1, 'Família',        '👨‍👩‍👧‍👦', '#e94560', 'Luisa, João Guilherme, Ana Luisa', 1),
(2, 'Consultório',    '🧠',       '#7c5cde', 'Pacientes, prontuários, atendimentos', 2),
(3, 'Finanças',       '💰',       '#10b981', 'Receitas, despesas, reembolsos, impostos', 3),
(4, 'YouTube',        '▶️',       '#ef4444', 'Canal, vídeos, roteiros, ideias', 4),
(5, 'Projetos',       '📋',       '#3b82f6', 'Projetos pessoais e profissionais', 5),
(6, 'Saúde Família',  '🏥',       '#f59e0b', 'Médicos, exames, reembolsos Cigna', 6),
(7, 'Arquivos',       '📁',       '#6b7280', 'Índice de documentos e pastas', 7);

-- Projetos iniciais
INSERT OR IGNORE INTO projetos (area_id, titulo, descricao, status, prioridade) VALUES
(2, 'Organizar 20 prontuários', 'Cadastrar todos os pacientes ativos com prontuário e agenda', 'ativo', 'alta'),
(3, 'Controle financeiro mensal', 'Receitas do consultório + despesas familiares + reembolsos', 'ativo', 'alta'),
(4, 'Canal YouTube — calendário editorial', 'Planejar e publicar vídeos com regularidade', 'ativo', 'media'),
(6, 'Reembolsos Cigna 2026', 'Sistema de reembolsos médicos da família', 'ativo', 'alta'),
(1, 'Agenda familiar', 'Compromissos escola, médicos, atividades das crianças', 'ativo', 'media');

-- Categorias financeiras
INSERT OR IGNORE INTO financas_categorias (nome, tipo, area_id, cor) VALUES
('Consultório — sessões',     'receita',  2, '#7c5cde'),
('Consultório — avaliações',  'receita',  2, '#a78bfa'),
('YouTube — AdSense',         'receita',  4, '#ef4444'),
('Reembolso plano de saúde',  'receita',  6, '#10b981'),
('Outras receitas',           'receita',  3, '#34d399'),
('Aluguel consultório',       'despesa',  2, '#f59e0b'),
('Impostos / NFSe',           'despesa',  3, '#ef4444'),
('Plano de saúde',            'despesa',  6, '#3b82f6'),
('Despesas família',          'despesa',  1, '#e94560'),
('Equipamento YouTube',       'despesa',  4, '#f97316'),
('Outras despesas',           'despesa',  3, '#9ca3af');

-- 20 slots de pacientes (preencher com nomes reais)
INSERT OR IGNORE INTO pacientes (codigo, nome, status, frequencia, observacoes) VALUES
('PAC-001', 'Paciente 01 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-002', 'Paciente 02 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-003', 'Paciente 03 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-004', 'Paciente 04 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-005', 'Paciente 05 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-006', 'Paciente 06 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-007', 'Paciente 07 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-008', 'Paciente 08 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-009', 'Paciente 09 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-010', 'Paciente 10 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-011', 'Paciente 11 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-012', 'Paciente 12 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-013', 'Paciente 13 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-014', 'Paciente 14 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-015', 'Paciente 15 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-016', 'Paciente 16 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-017', 'Paciente 17 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-018', 'Paciente 18 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-019', 'Paciente 19 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real'),
('PAC-020', 'Paciente 20 — preencher nome', 'ativo', 'semanal', 'Substitua pelo nome real');

-- Ideias YouTube (exemplos)
INSERT OR IGNORE INTO youtube_ideias (titulo, descricao, status, tags) VALUES
('Como superar fobias — introdução', 'Vídeo piloto sobre o tema principal do canal', 'ideia', 'fobia,psicologia'),
('Rotina de uma psicóloga', 'Dia a dia no consultório', 'ideia', 'rotina,consultorio'),
('Perguntas frequentes sobre terapia', 'Responder dúvidas comuns dos pacientes', 'ideia', 'terapia,faq');

-- Notas fixas
INSERT OR IGNORE INTO notas (titulo, conteudo, area_id, fixada, tags) VALUES
('Atalhos rápidos', 'controle familiar → reembolsos/index.html\norganização → organizacao/index.html\nEditar dados → python3 organizacao.py', 7, 1, 'atalho'),
('Lembretes importantes', '- Atualizar nomes dos 20 pacientes\n- Cadastrar horários fixos de cada um\n- Vincular prontuários (PDF/pasta)\n- Conferir agenda da semana toda segunda', 2, 1, 'lembrete');

-- Arquivos de referência (links para o que já existe no repo)
INSERT OR IGNORE INTO arquivos (titulo, caminho, categoria, area_id, tipo_arquivo, descricao) VALUES
('Central de Controle Família', '../reembolsos/documentos/referencia/central-de-controle-familia-palomo.html', 'familia', 1, 'html', 'Painel familiar com documentos médicos'),
('Reembolsos — Painel', '../reembolsos/index.html', 'medico', 6, 'html', 'Banco de reembolsos Cigna'),
('Memória Família Palomo', '../reembolsos/documentos/referencia/memoria-familia-palomo.md', 'familia', 1, 'doc', 'Contexto e preferências'),
('Planilha Reembolsos Luisa', '../reembolsos/documentos/referencia/planilha-reembolsos-luisa-12-2025.xlsx', 'financeiro', 6, 'xlsx', 'Planilha de reembolsos médicos'),
('Painel Investimentos', 'investimentos.html', 'financeiro', 3, 'html', 'Carteira e projeção 20 anos');

-- Investimentos · carteira inicial
INSERT OR IGNORE INTO investimentos_config (chave, valor) VALUES
('aporte_mensal_global', '500'),
('anos_projecao', '20'),
('taxa_carteira_default', '11');

INSERT OR IGNORE INTO investimentos
(nome, tipo, instituicao, ticker, codigo_ativo, valor_atual, valor_aplicado, quantidade,
 preco_unitario, taxa_anual, data_contratacao, data_atualizacao, aporte_mensal, cor, notas) VALUES
('Itaú Index Simples Selic RF VGBL', 'vgbl', 'Itaú', NULL, NULL,
 1315.13, 1315.13, NULL, NULL, 11.0, NULL, '2026-07-14', 200, '#ec7000',
 'Fundo RF VGBL atrelado ao Selic. Atualizar valor no app Itaú.'),
('XPML11 — XP Malls FII', 'fii', 'XP Investimentos', 'XPML11', 'BRXPMLCTF000',
 105.99, 105.99, 1, 105.99, 9.0, NULL, '2026-07-14', 100, '#7c5cde',
 'FII de shoppings. Preço unitário/cota. Ajuste quantidade se tiver mais cotas.'),
('Tesouro Pré-fixado 2029', 'tesouro_prefixado', 'Tesouro Direto', NULL, NULL,
 93.75, 93.75, 1, 93.75, 14.24, '2026-06-16', '2026-07-14', 200, '#10b981',
 'Taxa contratada 14,24% a.a. Valor = preço do título. Ajuste quantidade conforme compra.');

