# Instruções para agentes — repositório home (Família Palomo)

## Preferências da Priscila (sempre seguir)

1. **Em TODA conversa sobre reembolsos**, incluir o bloco **Links Seus** no
   formato abaixo (sempre as duas versões do painel e do controle quando houver
   branch de PR aberta; senão, só a principal):

   **Links Seus**
   - 📊 Painel de visualização:
     https://raw.githack.com/pripalomo-svg/home/main/reembolsos/index.html
   - 🗂️ Controle editável:
     https://raw.githack.com/pripalomo-svg/home/main/reembolsos/controle.html
   - 📁 Pasta no GitHub: https://github.com/pripalomo-svg/home/tree/main/reembolsos
   - 💾 Banco SQLite: https://github.com/pripalomo-svg/home/raw/main/reembolsos/reembolsos.db

   Branch atual do PR (atualizar ao mudar de branch): nenhuma aberta no momento
   (PR #7 mergeado na main)
2. Comunicação direta e concisa, sem elogios desnecessários (ver
   `reembolsos/documentos/referencia/memoria-familia-palomo.md`).
3. Existe um lembrete diário automático dos links (workflow
   `.github/workflows/lembrete-links.yml`), que comenta todo dia às 09:00
   (São Paulo) no issue "🔗 Lembrete diário — links do banco de reembolsos".
   Não duplicar esse mecanismo; para parar, fechar o issue e desativar o workflow.
4. **PRs do Cursor** (`cursor/*`): aprovar e mergear automaticamente, sem pedir
   permissão manual. Workflow: `.github/workflows/auto-merge-cursor-prs.yml`.
   Política: `APPROVAL_POLICY.md` e `.cursor/approval-policies/ROUTING.md`.

## Sobre o banco de reembolsos (`reembolsos/`)

- `reembolsos.db` (SQLite) é a fonte da verdade; `index.html` (visualização)
  e `controle.html` (edição) são gerados a partir dele.
- Após qualquer mudança no banco, regenerar os dois painéis:
  `python3 importar_dados.py && python3 gerar_dashboard.py && python3 gerar_controle.py`
- Documentos novos vão em `reembolsos/documentos/` (subpastas por categoria)
  e devem ser vinculados aos claims em `importar_dados.py`.
- Antes de adicionar documentos enviados pela usuária, conferir por hash
  (md5sum) se já não existem no repositório — ela costuma reenviar o lote inteiro.

## Cursor Cloud — instruções técnicas

### O que é este repositório
Além de `reembolsos/`, há `organizacao/` e outros projetos locais. O módulo
`reembolsos/` é um rastreador offline de reembolsos de plano de saúde (pt-BR):
scripts Python + SQLite (`reembolsos.db`) + HTML estático (`index.html`,
`controle.html` com localStorage).

### Ambiente
- Python 3.10+; `sqlite3` na stdlib.
- Dependência externa: `openpyxl` (só em `importar_dados.py`).
- Sem servidor web, API ou suite de testes configurada.

### Comandos (a partir de `reembolsos/`)
- CLI: `python3 reembolsos.py resumo` / `listar` / `add` / `atualizar` / `importar`
- Rebuild do banco: `python3 importar_dados.py`
- Regenerar painéis: `python3 gerar_dashboard.py && python3 gerar_controle.py`
- UI local: `python3 -m http.server 8000` → `index.html` ou `controle.html`

### Gotchas
- `reembolsos.db`, `index.html` e `controle.html` são versionados (artefatos gerados).
- Edições no `controle.html` ficam no localStorage; para persistir no banco, exportar
  JSON e rodar `importar_controle.py`, depois regenerar os painéis.
