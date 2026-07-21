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

## Começar

O banco **`organizacao.db` já vem pronto e versionado** — basta abrir **`index.html`** no navegador.

Para recriar do zero (se quiser):

```bash
cd organizacao
python3 organizacao.py init      # cria o banco com dados iniciais
python3 gerar_dashboard.py       # gera index.html
python3 gerar_investimentos.py   # gera investimentos.html
```

> **Pacientes:** os 20 slots (PAC-001 a PAC-020) estão reservados aguardando as
> informações reais. Quando chegarem, preencha via `cadastro_pacientes.html` ou
> `templates/pacientes.csv` e importe (veja abaixo).
>
> **Investimentos:** todas as aplicações cadastradas (VGBL, XPML11, Tesouro)
> são **da Priscila** — não têm relação com pacientes. Cada ativo tem um campo
> `titular` para deixar isso explícito.

## Preencher com seus dados reais

### Opção A — Formulário visual (recomendado)

Abra **`cadastro_pacientes.html`** no navegador. Preencha os 20 pacientes, exporte o CSV e importe:

```bash
# Salve o arquivo exportado como templates/pacientes.csv
python3 importar_dados.py pacientes templates/pacientes.csv
python3 gerar_dashboard.py
```

O formulário salva rascunho automaticamente no navegador.

### Opção B — Editar CSV direto

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

- `templates/pacientes.csv` — 20 pacientes com horários já distribuídos na semana
- `templates/atendimentos.csv` — sessões (data, hora, status, valor, pago)
- `templates/prontuarios.csv` — registros clínicos em texto
- `templates/financas.csv` — receitas e despesas
- `templates/youtube_videos.csv` — vídeos do canal
- `templates/agenda.csv` — compromissos
- `templates/projetos.csv` — projetos
- `templates/arquivos.csv` — índice de documentos

## Pacientes — substituir os 20 slots

O banco já vem com **PAC-001 a PAC-020** com horários da semana pré-definidos. Para colocar seus pacientes reais:

1. Abra `cadastro_pacientes.html` **ou** `templates/pacientes.csv`
2. Preencha nome, telefone e queixa de cada um
3. Importe e regenere o painel

## Investimentos

Painel dedicado com carteira e **projeção de 20 anos**:

```bash
python3 organizacao.py init          # inclui seus 3 ativos iniciais
python3 gerar_investimentos.py       # gera investimentos.html
# Abra investimentos.html no navegador
```

**Seus ativos cadastrados** (titular: Priscila — aplicações pessoais, não de pacientes):
| Ativo | Titular | Valor | Taxa |
|-------|---------|-------|------|
| Itaú Index Simples Selic VGBL | Priscila | R$ 1.315,13 | 11% a.a. (Selic) |
| XPML11 | Priscila | R$ 105,99 | 9% a.a. (estimativa) |
| Tesouro Pré-fixado | Priscila | R$ 93,75 | 14,24% a.a. (contratada) |

**Adicionar mais:** edite `templates/investimentos.csv` e importe:

```bash
python3 importar_investimentos.py templates/investimentos.csv
python3 gerar_investimentos.py
```

No painel, ajuste o **aporte mensal** e veja quanto terá em 5, 10, 15 e 20 anos.

## Importar do Notion

### Sincronização automática (recomendado)

Configure uma vez a API do Notion e rode:

```bash
python3 organizacao.py sincronizar
# ou no Windows: duplo-clique em SINCRONIZAR_NOTION.bat
```

Para **todo dia sem fazer nada**, agende `SINCRONIZAR_NOTION.bat` no Agendador de Tarefas do Windows (ex.: 07:00).

Guia completo: [`notion/COMO_CONFIGURAR_API.md`](notion/COMO_CONFIGURAR_API.md)

### Export manual (sem API)

Exporte no Notion: `⋯` → **Export** → **Markdown & CSV** → salve como `notion/Export.zip`:

```bash
python3 importar_notion.py zip ~/Downloads/Export.zip
# ou, se já extraiu:
python3 importar_notion.py auto notion/
python3 organizacao.py notion          # atalho (usa pasta notion/)
python3 organizacao.py sincronizar     # também detecta export em notion/
python3 gerar_dashboard.py
```

O script reconhece databases pelo **nome do arquivo** (Pacientes, Finanças, YouTube…) ou pelas **colunas** (Nome, Data, Valor…). Páginas `.md` viram notas.

Guia de export: [`notion/README.md`](notion/README.md)

## Prontuários em PDF

O painel já linka para o sistema de reembolsos em `../reembolsos/index.html` e a Central de Controle Familiar.

## Fluxo de Caixa (extratos bancários)

Painel `fluxo_caixa.html` com **entradas, saídas e investimentos mês a mês**, gerado a partir dos extratos em `extratos/*.csv` (separador `;`, colunas `data;descricao;valor;fluxo;categoria`, fluxo: `entrada|saida|aplicacao|resgate`).

```bash
python3 gerar_fluxo_caixa.py   # regenera fluxo_caixa.html
```

Já incluído: extrato Itaú de 22/04/2026 a 21/07/2026 (conferido com os saldos do PDF). Para cobrir mais meses, adicione novos CSVs em `extratos/` — lançamentos duplicados entre extratos são ignorados automaticamente.

## Como usar foto → banco

Envie uma **foto ou print** no chat do Cursor. O agente usa a skill `foto-para-banco` e registra em:

```bash
python3 registrar_foto.py dados/foto_registro.json
```

Log das atualizações: `ultima_atualizacao.json`

```bash
python3 organizacao.py status    # resumo no terminal
python3 organizacao.py gerar     # regenere o HTML
python3 organizacao.py prontuarios --extrair  # importa PDFs
python3 organizacao.py notion               # importa export Notion
python3 organizacao.py sincronizar          # sync automático Notion
python3 organizacao.py init --recriar       # recria banco do zero (cuidado!)
```

## Estrutura

```
organizacao/
├── schema.sql           # estrutura do banco
├── seed.sql             # dados iniciais (família, áreas, 20 pacientes)
├── organizacao.db       # banco SQLite pronto (versionado)
├── organizacao.py       # init / status / gerar
├── importar_prontuarios.py # importação de PDFs e CSV clínico
├── cadastro_pacientes.html # formulário visual dos 20 pacientes
├── documentos/prontuarios/ # pastas PAC-001 … PAC-020 para PDFs
├── importar_notion.py      # importação do Notion (ZIP / CSV / Markdown)
├── sincronizar_notion.py   # sync automático Notion (API + fallback export)
├── SINCRONIZAR_NOTION.bat  # atalho Windows para sync diário
├── notion/                 # token, config e export do Notion
├── gerar_dashboard.py   # gera index.html
├── index.html           # painel visual (gerado)
└── templates/           # CSVs para preencher
```
