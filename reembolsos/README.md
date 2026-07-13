# Reembolsos do Plano de Saúde

Banco de dados SQLite para registrar e acompanhar todas as solicitações de
reembolso do plano de saúde, com uma ferramenta de linha de comando em Python
(sem dependências externas — só a biblioteca padrão).

## Estrutura

| Arquivo | Descrição |
| --- | --- |
| `schema.sql` | Esquema do banco (tabelas, índices e visão consolidada) |
| `reembolsos.py` | CLI para criar o banco, adicionar, listar, importar e atualizar reembolsos |
| `template_importacao.csv` | Modelo de CSV para importação em lote |
| `reembolsos.db` | O banco de dados em si (criado ao rodar `init`; não é versionado) |

### Tabelas

- **beneficiarios** — titular e dependentes cobertos pelo plano.
- **prestadores** — médicos, clínicas, laboratórios e terapeutas.
- **reembolsos** — cada solicitação, com valor pago, valor reembolsado,
  datas (atendimento, solicitação, pagamento), protocolo da operadora,
  nota fiscal e status (`solicitado`, `em_analise`, `pago`, `pago_parcial`, `negado`).
- **vw_reembolsos** — visão que junta tudo e calcula a diferença entre o
  valor pago e o reembolsado.

## Como usar

```bash
cd reembolsos

# 1. Criar o banco de dados
python3 reembolsos.py init

# 2. Adicionar um reembolso (modo direto)
python3 reembolsos.py add \
  --beneficiario "Titular" \
  --prestador "Dra. Maria" --especialidade "Dermatologia" \
  --tipo consulta --data 2026-07-01 --valor 450 \
  --protocolo PRT-98765 --nota-fiscal NF-123

# ...ou em modo interativo (pergunta os campos obrigatórios)
python3 reembolsos.py add

# 3. Importar vários de uma vez a partir de um CSV
python3 reembolsos.py importar template_importacao.csv

# 4. Consultar
python3 reembolsos.py listar
python3 reembolsos.py listar --status em_analise
python3 reembolsos.py listar --ano 2026 --beneficiario "Titular"
python3 reembolsos.py resumo

# 5. Atualizar quando a operadora pagar
python3 reembolsos.py atualizar 3 --status pago --valor-reembolsado 315.00 --data-pagamento 2026-07-20
```

Também é possível consultar diretamente com o SQLite:

```bash
sqlite3 reembolsos.db "SELECT * FROM vw_reembolsos ORDER BY data_atendimento DESC;"
```

## Importação em lote

Preencha um CSV com o mesmo cabeçalho de `template_importacao.csv`.
Campos obrigatórios: `beneficiario`, `tipo`, `data_atendimento` (formato
`YYYY-MM-DD`) e `valor_pago`. Os demais podem ficar em branco. Beneficiários
e prestadores novos são cadastrados automaticamente.
