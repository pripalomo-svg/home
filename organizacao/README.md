# Central de Organização Pessoal · Priscila Palomo

Sistema para organizar **toda a sua vida** em um só lugar: família, consultório (20 pacientes), YouTube, finanças, projetos, arquivos e agenda.

Funciona **offline** — basta abrir `index.html` no navegador.

## O que tem aqui

| Área | O que organiza |
|------|----------------|
| **Família** | Priscila, Luisa, João Guilherme, Ana Luisa |
| **Consultório** | 20 pacientes, prontuários, atendimentos, horários |
| **YouTube** | Ideias, roteiros, vídeos em produção e publicados |
| **Finanças** | Receitas (consultório, YouTube) e despesas |
| **Projetos** | Tarefas e projetos por área da vida |
| **Arquivos** | Índice de documentos com links |
| **Agenda** | Compromissos unificados (pacientes, família, YouTube) |

## Começar em 3 passos

```bash
cd organizacao
python3 organizacao.py init      # cria o banco com dados iniciais
python3 importar_dados.py todos  # importa exemplos dos templates CSV
python3 gerar_dashboard.py       # gera index.html
```

Abra **`index.html`** no navegador.

## Preencher com seus dados reais

Edite os arquivos na pasta **`templates/`** (separador `;`, encoding UTF-8) e importe:

```bash
python3 importar_dados.py pacientes templates/pacientes.csv
python3 importar_dados.py atendimentos templates/atendimentos.csv
python3 importar_dados.py financas templates/financas.csv
python3 importar_dados.py youtube templates/youtube_videos.csv
python3 importar_dados.py agenda templates/agenda.csv
python3 gerar_dashboard.py   # regenere o painel após cada importação
```

### Templates disponíveis

- `templates/pacientes.csv` — 20 pacientes (nome, telefone, horário, valor, prontuário…)
- `templates/atendimentos.csv` — sessões (data, hora, status, valor, pago)
- `templates/financas.csv` — receitas e despesas
- `templates/youtube_videos.csv` — vídeos do canal
- `templates/agenda.csv` — compromissos
- `templates/projetos.csv` — projetos
- `templates/arquivos.csv` — índice de documentos

## Pacientes — substituir os 20 slots

O banco já vem com **PAC-001 a PAC-020** como placeholders. Para colocar seus pacientes reais:

1. Abra `templates/pacientes.csv`
2. Substitua os nomes (mantenha os códigos PAC-001…PAC-020 ou crie novos)
3. Preencha: `dia_horario`, `frequencia`, `valor_sessao`, `prontuario_path`
4. Importe e regenere o painel

## Prontuários

Os prontuários ficam na tabela `prontuarios` (conteúdo clínico + caminho do arquivo PDF). Por segurança, **não** vão para o CSV de importação — adicione direto no banco ou peça ajuda para criar um importador.

Exemplo SQL:

```sql
INSERT INTO prontuarios (paciente_id, data_registro, tipo, titulo, conteudo)
VALUES (1, '2026-07-08', 'evolucao', 'Sessão 12', 'Paciente relatou melhora na exposição gradual...');
```

## Integração com reembolsos

O painel já linka para o sistema de reembolsos em `../reembolsos/index.html` e a Central de Controle Familiar.

## Comandos úteis

```bash
python3 organizacao.py status    # resumo no terminal
python3 organizacao.py gerar     # regenere o HTML
python3 organizacao.py init --recriar   # recria banco do zero (cuidado!)
```

## Estrutura

```
organizacao/
├── schema.sql           # estrutura do banco
├── seed.sql             # dados iniciais (família, áreas, 20 pacientes)
├── organizacao.db       # banco SQLite (gerado, não versionado)
├── organizacao.py       # init / status / gerar
├── importar_dados.py    # importação CSV
├── gerar_dashboard.py   # gera index.html
├── index.html           # painel visual (gerado)
└── templates/           # CSVs para preencher
```
