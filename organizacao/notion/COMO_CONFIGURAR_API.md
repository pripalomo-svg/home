# Configurar sincronização automática com o Notion

## Opção A — API (recomendado, automático)

### 1. Criar integração
1. Acesse https://www.notion.so/my-integrations
2. **+ New integration** → nome: `Organização Priscila`
3. Copie o **Internal Integration Secret** (começa com `ntn_` ou `secret_`)

### 2. Salvar token
Crie o arquivo `notion/token.txt` e cole o token (uma linha só).

Ou defina variável de ambiente:
```bash
set NOTION_TOKEN=seu_token_aqui
```

### 3. Conectar às databases no Notion
Para cada database abaixo, abra no Notion → `⋯` → **Connections** → adicione **Organização Priscila**:

| Database | Link |
|----------|------|
| 📅 Agenda de Sessões | [Abrir](https://app.notion.com/p/1b477a969a0349f589d4dbf4be5ce4a5) |
| Consolidação de Anotações | [Abrir](https://app.notion.com/p/530b270b77d347778d65dfe061ab6540) |

### 4. Testar
```bash
python organizacao.py sincronizar
```

---

## Opção B — Export manual (sem API)

1. No Notion: `⋯` → **Export** → **Markdown & CSV**
2. Salve o ZIP como `organizacao/notion/Export.zip`
3. Rode:
```bash
python organizacao.py sincronizar
```

---

## Agendamento automático (Windows)

Para sincronizar **todo dia** sem fazer nada:

1. Abra **Agendador de Tarefas** do Windows
2. **Criar Tarefa Básica**
3. Nome: `Sincronizar Notion`
4. Disparo: **Diariamente** às 07:00
5. Ação: **Iniciar programa**
6. Programa: caminho completo para `SINCRONIZAR_NOTION.bat`
   - Ex.: `C:\Users\pripa\OneDrive\...\organizacao\SINCRONIZAR_NOTION.bat`
7. Marque **Executar mesmo se o usuário não estiver conectado** (opcional)

---

## O que sincroniza

| Notion | Vai para |
|--------|----------|
| Agenda de Sessões | Atendimentos (sessões realizadas) |
| Consolidação de Anotações | Prontuários (resumos clínicos) |
| Export CSV/ZIP | Detecta automaticamente |

Pacientes já cadastrados (PAC-001 a PAC-018) são reconhecidos pelo nome.

Log da última sync: `notion/ultima_sincronizacao.json`
