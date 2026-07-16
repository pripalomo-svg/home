---
name: create-database-row
description: Adiciona linhas em bancos SQLite do repositório (organização, reembolsos) e responde à Priscila de forma rápida e resumida, sempre com link direto da atualização. Use ao cadastrar dados, criar registros, importar fotos, CSV, Notion ou qualquer inserção no banco.
---

# create-database-row

## Regra de ouro

**Toda inserção no banco → resposta curta + link específico.** Sem textão. Sem pedir à Priscila para abrir pasta.

## Fluxo

1. Identificar banco/módulo → [reference.md](reference.md)
2. Gravar (script ou importador adequado)
3. Regenerar painel se necessário
4. Responder **só** no formato abaixo

## Formato de resposta (obrigatório)

Máximo ~12 linhas úteis antes dos links fixos.

```markdown
## ✅ Atualizado · [módulo]
**Entrou:** [1 linha]
**Pendente:** [1 linha ou "nada"]

## 🔗 Ver agora
👉 [título]: [link_ver de links_modulos.json ou ultima_atualizacao.json]
PC: `Imagens\home\organizacao\[arquivo]`

## Links
- Reembolsos: [painel](url) · [controle](url)
- Organização: [painel](url) · [investimentos](url) · [links](url) · [ZIP](url)
```

## Scripts por módulo

| Módulo | Comando |
|--------|---------|
| Foto/print | `python3 organizacao/registrar_foto.py organizacao/dados/foto_registro.json` |
| Investimentos CSV | `python3 organizacao/importar_investimentos.py templates/investimentos.csv` |
| Outros CSV | `python3 organizacao/importar_dados.py [modulo] templates/[modulo].csv` |
| Notion | `python3 organizacao/organizacao.py sincronizar` |
| Reembolsos | fluxo em `reembolsos/README.md` |

## Estilo

- Frases curtas. Bullets. Nada de repetir o que já está no painel.
- **Nunca** omitir `🔗 Ver agora` após mudança no banco.
- **Nunca** inventar dados (telefone, valor, CPF).
- Skills relacionadas: `foto-para-banco`, `link-atualizacao`.

## Links base (copiar)

```
REEMBOLSOS_PAINEL=https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/reembolsos/index.html
REEMBOLSOS_CTRL=https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/reembolsos/controle.html
ORG_PAINEL=https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/index.html
ORG_LINKS=https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/links.html
ORG_INV=https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/investimentos.html
ZIP=https://github.com/pripalomo-svg/home/archive/refs/heads/main.zip
```

Mapa módulo → link específico: `organizacao/dados/links_modulos.json`
