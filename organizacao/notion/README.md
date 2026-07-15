# Coloque aqui o export do Notion (ZIP extraído ou CSVs soltos)

1. No Notion: abra a database → `⋯` → **Export** → **Markdown & CSV**
2. Marque **Include subpages** se quiser importar o conteúdo das páginas
3. Extraia o ZIP nesta pasta (`organizacao/notion/`)
4. Rode:

```bash
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
