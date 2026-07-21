# Notion → Organização

## Sincronização automática (recomendado)

Configure a API uma vez e rode `python3 organizacao.py sincronizar` (ou `SINCRONIZAR_NOTION.bat` no Windows).

Guia: [`COMO_CONFIGURAR_API.md`](COMO_CONFIGURAR_API.md)

---

## Export manual (ZIP / CSV)

1. No Notion: abra a database → `⋯` → **Export** → **Markdown & CSV**
2. Marque **Include subpages** se quiser importar o conteúdo das páginas
3. Extraia o ZIP nesta pasta (`organizacao/notion/`) ou salve como `Export.zip`
4. Rode:

```bash
python3 organizacao.py sincronizar
# ou:
python3 importar_notion.py auto notion/
python3 gerar_dashboard.py
```

## Nomes de arquivo que o sistema reconhece

| Se o CSV se chama… | Vai para… |
|--------------------|-----------|
| Pacientes, Clientes | pacientes |
| Atendimentos, Sessões | atendimentos |
| Finanças, Gastos | financas |
| YouTube, Vídeos | youtube |
| Agenda, Calendário | agenda |
| Projetos | projetos |
| Tarefas, To-do | tarefas |
| Prontuários | prontuarios |

Se o nome não bater, o script tenta adivinhar pelas colunas.

## Colunas do Notion que funcionam

O importador entende nomes em **português e inglês**:

- **Pacientes:** Nome, Telefone, E-mail, Status, Queixa, Horário, Valor
- **Atendimentos:** Paciente, Data, Hora, Status, Valor
- **Finanças:** Descrição, Valor, Data, Categoria, Tipo
- **Projetos/Tarefas:** Nome, Status, Prioridade, Prazo
- **Agenda:** Título, Data, Hora, Local

Páginas exportadas como `.md` viram **notas** no painel.

## Importar um CSV específico

```bash
python3 importar_notion.py pacientes notion/Minha-Base.csv
python3 importar_notion.py zip ~/Downloads/Export.zip
```

## Prontuário por paciente (páginas de conversas)

Cada paciente tem página no Notion (`paginas_pacientes.json`) com seção **Prontuário clínico** (dados do `pacientes.csv` + índice de sessões do export/PDF).

```bash
python3 notion/atualizar_prontuario_pacientes.py   # gera prontuario_por_paciente.json + CSV
python3 importar_prontuarios.py csv templates/prontuarios.csv
python3 gerar_dashboard.py
```

PDF de referência: `documentos/prontuarios/referencia/indice-pacientes-notion-2026-07.pdf`
