# Instruções para agentes — repositório home (Família Palomo)

## Preferências da Priscila (sempre seguir)

1. **Em TODA interação com a Priscila** (qualquer assunto neste repositório),
   incluir o bloco **Links Seus** no final da resposta.

2. **Quando atualizar qualquer banco** (foto, CSV, Notion, reembolsos), incluir:
   - **✅ Banco atualizado** (módulo, o que entrou, pendências)
   - **🔗 Ver esta atualização** — link **específico** do painel alterado (skill `.cursor/skills/link-atualizacao/SKILL.md`)
   - Nunca omitir o link direto; a Priscila não deve pedir.
   - Fotos: skill `.cursor/skills/foto-para-banco/SKILL.md`
   - Mapa de links: `organizacao/dados/links_modulos.json`

   **Links Seus — Reembolsos**
   - 📊 Painel: https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/reembolsos/index.html
   - 🗂️ Controle: https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/reembolsos/controle.html
   - 📁 GitHub: https://github.com/pripalomo-svg/home/tree/main/reembolsos

   **Links Seus — Organização**
   - 🔗 Todos os links: https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/links.html
   - ➕ Como adicionar conteúdo: https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/adicionar_conteudo.html
   - 🏠 Painel: https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/index.html
   - ❓ Guia: https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/como_usar.html
   - 📈 Investimentos: https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/investimentos.html
   - ✏️ Pacientes: https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/cadastro_pacientes.html
   - 📁 GitHub: https://github.com/pripalomo-svg/home/tree/main/organizacao
   - ⬇️ Baixar ZIP: https://github.com/pripalomo-svg/home/archive/refs/heads/main.zip

   **No PC (pasta Imagens):** `C:\Users\SEU_USUARIO\Imagens\home\organizacao\`
2. Comunicação direta e concisa, sem elogios desnecessários (ver
   `reembolsos/documentos/referencia/memoria-familia-palomo.md`).
3. Existe um lembrete diário automático dos links (workflow
   `.github/workflows/lembrete-links.yml`), que comenta todo dia às 09:00
   (São Paulo) no issue "🔗 Lembrete diário — links do banco de reembolsos".
   Não duplicar esse mecanismo; para parar, fechar o issue e desativar o workflow.
4. **PRs do Cursor** (`cursor/*`): aprovar e mergear automaticamente, sem pedir
   permissão manual. Workflow: `.github/workflows/auto-merge-cursor-prs.yml`.
   Política: `APPROVAL_POLICY.md` e `.cursor/approval-policies/ROUTING.md`.
   Template para outros repositórios: `scripts/github-auto-merge/`.

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
