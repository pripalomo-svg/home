# Base de Dados — Priscila Palomo Psicologia Ltda

Dados extraídos dos documentos societários da empresa **PRISCILA PALOMO PSICOLOGIA LTDA**
(contrato social, declaração de desimpedimento, enquadramento ME e declaração de
licenciamento) e organizados em uma base de dados com visualização web.

## Arquivos

| Arquivo | Descrição |
| --- | --- |
| `dados.json` | Dados estruturados extraídos dos 8 PDFs |
| `criar_banco.py` | Script que gera a base SQLite `empresa.db` a partir do JSON |
| `empresa.db` | Base de dados SQLite (tabelas: `empresas`, `socios`, `atividades`, `documentos`) |
| `index.html` | Página web com a visualização de todos os dados (abre direto no navegador) |

## Como usar

1. **Ver a página web** — abra `index.html` em qualquer navegador (não precisa de servidor):

   ```bash
   xdg-open index.html    # Linux
   open index.html        # macOS
   ```

2. **(Re)gerar a base SQLite**:

   ```bash
   python3 criar_banco.py
   ```

3. **Consultar a base**:

   ```bash
   sqlite3 empresa.db "SELECT arquivo, tipo, assinado FROM documentos;"
   ```

## Modelo de dados

- **empresas** — dados cadastrais da empresa (nome, natureza jurídica, capital, endereço etc.)
- **socios** — quadro societário (vinculado a `empresas` por `empresa_id`)
- **atividades** — atividades econômicas CNAE (principal e secundárias)
- **documentos** — os 8 PDFs arquivados, com tipo, data, destinatário e status de assinatura
