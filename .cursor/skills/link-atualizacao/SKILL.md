---
name: link-atualizacao
description: Após qualquer atualização de banco (foto, CSV, Notion, reembolsos), enviar à Priscila o link EXATO do painel/arquivo alterado — sem ela pedir.
---

# Link específico da atualização

## Regra principal

**Sempre que o banco for atualizado**, a resposta DEVE incluir:

1. **✅ Banco atualizado** (módulo, o que entrou, pendências)
2. **🔗 Ver esta atualização** — **um link direto** para onde a mudança aparece
3. **Links Seus** (catálogo geral — ver `AGENTS.md`)

A Priscila **não precisa pedir** o link. Envie automaticamente.

## Mapa módulo → link (usar este)

Consulte `organizacao/dados/links_modulos.json` ou use a tabela:

| Módulo | Link direto (abrir no navegador) |
|--------|----------------------------------|
| `investimentos` | https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/investimentos.html |
| `financas` | https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/index.html#financas |
| `fluxo_caixa` / `extratos` | https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/fluxo_caixa.html |
| `pacientes` / `consultorio` | https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/index.html#consultorio |
| `atendimentos` | https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/index.html#consultorio |
| `agenda` | https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/index.html#agenda |
| `youtube` | https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/index.html#youtube |
| `projetos` | https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/index.html#projetos |
| `arquivo` | https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/index.html#arquivos |
| `nota` | https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/index.html#visao |
| `reembolsos` | https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/reembolsos/index.html |
| `notion` | https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/index.html#consultorio |

**Cadastro visual de pacientes** (se editou paciente):  
https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/cadastro_pacientes.html

**Log da última mudança:** `organizacao/ultima_atualizacao.json`

## Formato obrigatório na resposta

```markdown
## ✅ Banco atualizado
- **Módulo:** investimentos
- **Entrou:** Tesouro Direto protocolo 103681346 (Nu Invest)
- **Pendente:** valor

## 🔗 Ver esta atualização
👉 **Investimentos:** https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/investimentos.html

**No seu PC:** `Imagens\home\organizacao\investimentos.html`
```

## Quando há mais de um módulo

Liste **um link por módulo** alterado, na mesma ordem das mudanças.

## Integração com foto-para-banco

Após `registrar_foto.py`, leia `ultima_atualizacao.json` — o campo `link_ver` já traz o link correto.

## Nunca

- Enviar só "abra o painel" sem URL
- Enviar só o link genérico `links.html` quando houve atualização específica
- Omitir o bloco **🔗 Ver esta atualização** após mudança no banco
