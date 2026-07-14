# Meu Hub de Organização

Uma **base de dados única** (SQLite) + um **painel/template editável** (um só
arquivo HTML, funciona offline) para você organizar tudo em um lugar:

- 📌 **Projetos** e ✅ **tarefas** (por área da vida, com prazo, prioridade, progresso e próxima ação)
- 💰 **Vida financeira** — contas, receitas/despesas, resumo por mês, saldo por conta e metas
- 🎬 **Canal no YouTube** — vídeos da ideia à publicação (roteiro, gravação, edição, agendado, publicado)
- 🩺 **Consultório** — pacientes, prontuários, evoluções sessão a sessão e atendimentos/agenda
- 👨‍👩‍👧‍👦 **Família** — esposa, filhos, aniversários e datas importantes
- 📎 **Arquivos** — documentos organizados por área e projeto

Tudo com uma **visão geral** que junta o que importa: próximos atendimentos,
próximos eventos, projetos em andamento, tarefas pendentes e o saldo do mês.

## Como usar no dia a dia

1. Gere a base e o painel (só na primeira vez ou quando quiser recomeçar):
   ```bash
   cd organizacao
   python3 criar_banco.py      # cria organizacao.db com dados de EXEMPLO
   python3 gerar_painel.py     # gera painel.html a partir do banco
   ```
   Prefere começar do zero, sem exemplos? Use `python3 criar_banco.py --vazio`.

2. Abra **`painel.html`** com dois cliques (qualquer navegador). Não precisa de
   internet nem instalar nada.

3. Use as abas no topo. Em cada aba você pode:
   - **➕ Novo** para adicionar um registro;
   - **✏️** (ou duplo-clique na linha) para editar;
   - **🗑️** para excluir;
   - **Buscar** e clicar no cabeçalho para **ordenar**;
   - **⬇️ CSV** para exportar aquela tabela.

   Todas as alterações são salvas **automaticamente no seu navegador**
   (localStorage). Se quiser desfazer tudo, use **↺ Restaurar original**.

4. Para gravar as mudanças de volta no banco (backup permanente):
   - No painel, clique em **⬇️ Exportar JSON**;
   - Rode `python3 importar_painel.py organizacao_export.json`;
   - Regenere o painel: `python3 gerar_painel.py`.

## ⚠️ Privacidade (dados de pacientes — LGPD)

Prontuários e dados de pacientes são **dados sensíveis de saúde**. Recomendações:

- Os dados de exemplo são **fictícios**. Substitua pelos reais só no seu computador.
- Se este repositório for compartilhado/hospedado (ex.: GitHub), **não versione
  seus dados reais**: abra `organizacao/.gitignore` e descomente as linhas
  `organizacao.db` e `painel.html`. Assim eles ficam apenas na sua máquina.
- Faça backups (o próprio `organizacao_export.json` serve de backup).

## Estrutura dos arquivos

| Arquivo | Descrição |
| --- | --- |
| `schema.sql` | Estrutura do banco (todas as tabelas e visões) |
| `criar_banco.py` | Cria o `organizacao.db` (com ou sem dados de exemplo) |
| `gerar_painel.py` | Gera o `painel.html` a partir do banco |
| `importar_painel.py` | Aplica no banco o JSON exportado do painel |
| `organizacao.db` | O banco SQLite com seus dados |
| `painel.html` | O painel/template editável (abre no navegador) |

## O que tem no banco

**Núcleo:** `areas`, `projetos`, `tarefas`, `arquivos`.
**Financeiro:** `contas`, `categorias_fin`, `transacoes`, `metas`.
**Conteúdo:** `canais`, `videos`.
**Consultório:** `pacientes`, `prontuarios`, `evolucoes`, `atendimentos`.
**Família/agenda:** `familiares`, `eventos`.

Visões prontas para consulta direta no SQLite:

```bash
sqlite3 organizacao.db "SELECT * FROM vw_agenda WHERE data >= date('now');"
sqlite3 organizacao.db "SELECT * FROM vw_financeiro_mensal;"
sqlite3 organizacao.db "SELECT nome, proximo_atendimento FROM vw_pacientes;"
sqlite3 organizacao.db "SELECT titulo, area, status FROM vw_projetos WHERE status='em_andamento';"
```

## Como adaptar

- **Novas áreas/categorias/contas:** adicione pela aba **⚙️ Cadastros** do painel.
- **Mudar a estrutura (novos campos/tabelas):** edite `schema.sql` e as listas de
  exemplo em `criar_banco.py`, recrie o banco e regenere o painel. Para expor um
  campo novo no painel, adicione-o em `CONFIG` dentro de `gerar_painel.py`.
