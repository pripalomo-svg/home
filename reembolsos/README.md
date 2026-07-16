# Reembolsos do Plano de Saúde — Família Palomo

## 🔗 Links rápidos (abrir no navegador)

| O quê | Link |
| --- | --- |
| **Painel de visualização** | https://raw.githack.com/pripalomo-svg/home/main/reembolsos/index.html |
| **Controle editável** | https://raw.githack.com/pripalomo-svg/home/main/reembolsos/controle.html |
| Pasta no GitHub | https://github.com/pripalomo-svg/home/tree/main/reembolsos |
| Banco SQLite (download) | https://github.com/pripalomo-svg/home/raw/main/reembolsos/reembolsos.db |

Banco de dados SQLite com **todos os reembolsos médicos da família** (plano
Cigna via McKinsey, titular Luisa Juliana Faria Ramalho de Souza), com os
documentos digitalizados (notas fiscais, recibos, EOBs) **vinculados a cada
claim** e um **painel visual** para consulta limpa.

## Como usar no dia a dia

- **`controle.html`** — template **editável** para controlar tudo: adicionar,
  editar e excluir reembolsos, mudar status direto na tabela, anotar a
  próxima ação de cada pendência. As alterações são salvas automaticamente
  no navegador (localStorage) e podem ser exportadas em CSV/JSON.
- **`index.html`** — painel de **visualização** (somente leitura), gerado a
  partir do banco.

### Fluxo do controle editável

1. Abra `controle.html` no navegador.
2. Edite à vontade: "➕ Novo reembolso", ✏️ em cada linha, ou mude o status
   pelo seletor da própria tabela (marcar como "Pago" preenche o valor
   reembolsado automaticamente se estiver vazio).
3. Na aba **⏳ Pendências**, os claims aguardando resposta aparecem do mais
   antigo para o mais novo, com contador de dias (vermelho acima de 45) e um
   campo "próxima ação" para suas anotações.
4. Para levar as alterações de volta ao banco: exporte o **JSON** e rode
   `python3 importar_controle.py arquivo.json`, depois regenere os painéis.
5. "↺ Restaurar original" descarta as edições locais e volta aos dados do
   banco embutidos no arquivo.

## O painel de visualização (`index.html`)

Funciona offline e traz:

- **Reembolsos** — tabela completa com filtros (beneficiário, status, ano,
  tipo), busca livre, ordenação por coluna e detalhes ao clicar na linha
  (nº do claim, comentário da Cigna, glosa, situação, documentos anexados).
- **Documentos** — todos os PDFs organizados por categoria, com link direto.
- **Detalhe EOBs Cigna** — cada linha de serviço dos Explanation of Benefits
  (sessão a sessão, com câmbio, valores em USD e remark codes).
- **Portal Cigna 2026** — submissões com nº de submissão e CLM.
- **Prestadores** — diretório com todos os prestadores (claims, totais,
  período de uso) + indicações ainda sem reembolso (dermatologistas
  pediátricas do diretório do Notion).
- **Resumo** — totais por beneficiário, status, prestador e ano.

## Estrutura

| Arquivo | Descrição |
| --- | --- |
| `reembolsos.db` | Banco SQLite com todos os dados |
| `controle.html` | Template editável de controle (gerado a partir do banco) |
| `index.html` | Painel visual somente leitura (gerado a partir do banco) |
| `schema.sql` | Esquema do banco |
| `importar_dados.py` | Recria o banco a partir da planilha + documentos |
| `gerar_dashboard.py` | Regenera o `index.html` a partir do banco |
| `gerar_controle.py` | Regenera o `controle.html` a partir do banco |
| `importar_controle.py` | Aplica no banco o JSON exportado do controle |
| `reembolsos.py` | CLI para adicionar/listar/atualizar reembolsos |
| `documentos/` | Todos os PDFs, planilha e arquivos de referência |
| `template_importacao.csv` | Modelo de CSV para importação em lote via CLI |

### Pasta `documentos/`

- `notas-fiscais/` — NFs de consultas, exames e farmácia
- `recibos/` — recibos de fisioterapia (Wendy Paola)
- `eob-cigna/` — Explanation of Benefits da Cigna
- `medicos/` — receitas, pedidos de exame e relatórios médicos
- `planos/` — documentação dos planos Cigna/dental 2026
- `referencia/` — planilha original, CSV de NFS-e, dashboard antigo, memória

### Tabelas do banco

- **reembolsos** — cada claim: beneficiário, prestador, valores pago e
  reembolsado, status, nº do claim (e nº de reconsideração), comentário da
  Cigna, nota fiscal, situação atual.
- **documentos** + **reembolso_documentos** — arquivos digitalizados e o
  vínculo N:N com os claims (um EOB cobre vários claims).
- **eob_itens** — linhas de serviço dos EOBs (44 itens: data, BRL, câmbio,
  USD, pago, não coberto, remark code).
- **submissoes_portal** — submissões do portal Cigna 2026 (nº submissão + CLM).
- **beneficiarios** / **prestadores** — cadastro com CPF/CNPJ e especialidade.
- **vw_reembolsos** — visão consolidada com documentos agregados.

## Como atualizar

```bash
cd reembolsos

# Opção A: adicionar um reembolso novo pela CLI
python3 reembolsos.py add --beneficiario "Priscila da Silva Herbas Palomo" \
  --prestador "Fleury S.A." --tipo exame --data 2026-07-10 --valor 500

# Opção B: editar importar_dados.py (listas PORTAL_2026 / EOB_ITENS / extras)
# e recriar o banco do zero:
python3 importar_dados.py

# Sempre que o banco mudar, regenerar o painel:
python3 gerar_dashboard.py
```

Consultas diretas no SQLite:

```bash
sqlite3 reembolsos.db "SELECT * FROM vw_reembolsos WHERE status='em_analise';"
sqlite3 reembolsos.db "SELECT * FROM eob_itens WHERE n_claim='137076305';"
```

## Fontes dos dados

1. Planilha `12_2025 - Reembolsos Médicos - LUISA...xlsx`, aba "Reembolso
   Cigna" (62 linhas de claims 2024–2026; linhas de reconsideração do mesmo
   claim foram mescladas ao registro original).
2. Print do portal Cigna 2026 (10 submissões com nº de submissão/CLM).
3. Três EOBs da Cigna em PDF (set/2025, nov/2025 e jan/2026), extraídos
   linha a linha.
4. Notas fiscais e recibos em PDF, vinculados aos claims correspondentes
   pela coluna DOCUMENTO da planilha, pelo nº da NF ou pelo valor/data.

Observação: o claim 137973185 aparecia na planilha com data 02/10/2026
(formato americano); foi registrado como 10/02/2026 com nota no campo de
observações.
