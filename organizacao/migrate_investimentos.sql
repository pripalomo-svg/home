-- Migração: adiciona tabelas de investimentos em banco existente
-- Uso: sqlite3 organizacao.db < migrate_investimentos.sql

.read schema.sql

-- Só insere se tabela vazia
INSERT INTO investimentos_config (chave, valor)
SELECT 'aporte_mensal_global', '500' WHERE NOT EXISTS (SELECT 1 FROM investimentos_config);
INSERT INTO investimentos_config (chave, valor)
SELECT 'anos_projecao', '20' WHERE NOT EXISTS (SELECT 1 FROM investimentos_config WHERE chave='anos_projecao');
INSERT INTO investimentos_config (chave, valor)
SELECT 'taxa_carteira_default', '11' WHERE NOT EXISTS (SELECT 1 FROM investimentos_config WHERE chave='taxa_carteira_default');

INSERT INTO investimentos
(nome, tipo, instituicao, ticker, codigo_ativo, valor_atual, valor_aplicado, quantidade,
 preco_unitario, taxa_anual, data_contratacao, data_atualizacao, aporte_mensal, cor, notas)
SELECT * FROM (VALUES
('Itaú Index Simples Selic RF VGBL', 'vgbl', 'Itaú', NULL, NULL,
 1315.13, 1315.13, NULL, NULL, 11.0, NULL, '2026-07-14', 200, '#ec7000',
 'Fundo RF VGBL atrelado ao Selic.'),
('XPML11 — XP Malls FII', 'fii', 'XP Investimentos', 'XPML11', 'BRXPMLCTF000',
 105.99, 105.99, 1, 105.99, 9.0, NULL, '2026-07-14', 100, '#7c5cde',
 'FII shoppings. 1 cota.'),
('Tesouro Pré-fixado 2029', 'tesouro_prefixado', 'Tesouro Direto', NULL, NULL,
 93.75, 93.75, 1, 93.75, 14.24, '2026-06-16', '2026-07-14', 200, '#10b981',
 'Taxa 14,24% a.a.')
) AS v(nome,tipo,instituicao,ticker,codigo_ativo,valor_atual,valor_aplicado,quantidade,
       preco_unitario,taxa_anual,data_contratacao,data_atualizacao,aporte_mensal,cor,notas)
WHERE NOT EXISTS (SELECT 1 FROM investimentos LIMIT 1);
