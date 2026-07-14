# Meu Organizador — banco de dados + painel pessoal

Base de dados SQLite e template editável para organizar **tudo em um lugar só**:

- 💰 **Vida financeira** — receitas, despesas, contas, previsto × efetivado, saldo por mês
- 🎬 **Canal do YouTube** — pipeline de vídeos (ideia → roteiro → gravação → edição → publicado)
- 🩺 **Consultório** — pacientes, prontuários (queixa, histórico, hipótese, plano) e atendimentos com data, hora, status, valor e evolução
- 👨‍👩‍👧‍👦 **Família** — esposa e filhos, eventos e compromissos de cada um
- ✅ **Projetos & tarefas** — qualquer projeto de qualquer área, com prazos e prioridades
- 📁 **Arquivos** — índice de onde está cada documento importante

## Comece por aqui

```bash
cd organizador
python3 criar_banco.py --exemplo   # cria organizador.db com 20 pacientes de exemplo
python3 gerar_painel.py            # gera o painel.html
```

Abra **`painel.html`** no navegador. Ele funciona offline e é totalmente
editável: adicione, edite e exclua registros em todas as abas. As alterações
são salvas automaticamente no navegador (localStorage).

Prefere começar do zero, sem exemplos? Use `python3 criar_banco.py`
(cria só as áreas e os 3 membros da família para você renomear).

## O painel (`painel.html`)

| Aba | O que faz |
| --- | --- |
| 📅 Hoje & Agenda | agenda unificada: atendimentos + eventos da família + tarefas com prazo, e resumo do dia |
| 💰 Financeiro | lançamentos com filtro por mês, busca, totais de receitas/despesas/saldo |
| 🎬 YouTube | vídeos agrupados por etapa do pipeline |
| 🩺 Pacientes | lista com sessões feitas e próxima sessão; clique no paciente para abrir o **prontuário** e os **atendimentos** |
| 👨‍👩‍👧‍👦 Família | membros e eventos (escola, saúde, lazer, aniversários) |
| ✅ Projetos & Tarefas | cards de projetos por área + lista de tarefas com checkbox |
| 📁 Arquivos | índice dos seus arquivos (caminho ou link, área, categoria) |

### Fluxo de trabalho

1. Edite à vontade no navegador — tudo fica salvo localmente (localStorage).
2. Quando quiser consolidar no banco: **⬇ Exportar JSON** e rode
   `python3 importar_painel.py organizador-export.json`
   (um backup `.bak` do banco anterior é criado).
3. Regenere o painel: `python3 gerar_painel.py`.
4. **↺ Restaurar original** descarta as edições locais e volta aos dados do banco.

## Estrutura

| Arquivo | Descrição |
| --- | --- |
| `organizador.db` | Banco SQLite com todos os dados |
| `painel.html` | Painel editável (gerado a partir do banco) |
| `schema.sql` | Esquema do banco |
| `criar_banco.py` | Cria/recria o banco (`--exemplo` popula com dados de exemplo) |
| `gerar_painel.py` | Regenera o `painel.html` a partir do banco |
| `importar_painel.py` | Aplica no banco o JSON exportado do painel |
| `arquivos/` | Pastas para guardar os arquivos em si (financeiro, youtube, pacientes, familia, projetos, outros) |

### Tabelas do banco

- **areas** — as áreas da vida (Financeiro, YouTube, Consultório, Família, Pessoal)
- **fin_lancamentos** — receitas e despesas (+ visão `vw_fin_mensal` com saldo por mês)
- **yt_videos** — vídeos do canal e etapa de produção
- **pacientes** / **prontuarios** (1:1) / **atendimentos** — consultório completo (+ visão `vw_pacientes`)
- **familia_membros** / **familia_eventos** — família e compromissos
- **projetos** / **tarefas** — qualquer projeto e suas tarefas
- **arquivos** — índice de documentos
- **vw_agenda** — visão unificada de atendimentos + eventos + tarefas com prazo

Consultas diretas no SQLite:

```bash
sqlite3 organizador.db "SELECT * FROM vw_agenda WHERE data >= date('now') LIMIT 20;"
sqlite3 organizador.db "SELECT * FROM vw_fin_mensal;"
sqlite3 organizador.db "SELECT * FROM vw_pacientes WHERE ativo = 1;"
```

## Dados de exemplo

O banco vem com **20 pacientes fictícios** ("Paciente 01"… "Paciente 20"),
cada um com prontuário e duas sessões (uma realizada e uma agendada), além de
lançamentos financeiros, vídeos, projetos, tarefas e eventos de exemplo —
tudo marcado para você substituir pelos dados reais direto no painel.

Os membros da família ("Esposa", "Filho 1", "Filho 2") também são
placeholders: renomeie na aba 👨‍👩‍👧‍👦 Família.

> **Privacidade**: prontuários são dados sensíveis. O painel funciona 100%
> offline e o `.gitignore` já impede que exports JSON, backups `.bak` e o
> conteúdo de `arquivos/` subam para o repositório. Se este repositório não
> for privado, adicione também `organizador.db` e `painel.html` ao
> `.gitignore` antes de colocar dados reais.
