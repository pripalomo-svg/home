---
name: foto-para-banco
description: Extrai dados de fotos, prints e imagens enviados pela Priscila e grava no banco SQLite correto (investimentos, finanças, consultório, reembolsos). Use quando a usuária enviar foto, imagem, print, screenshot, comprovante, recibo, extrato ou documento visual para cadastrar.
---

# Foto → banco específico

## Quando aplicar

- Priscila envia **foto, print ou screenshot**
- Pedido implícito ou explícito para **cadastrar / anexar / salvar** dados
- Comprovantes: banco, corretora, Tesouro, Cigna, consultório, NF, boleto

## Fluxo (sempre nesta ordem)

1. **Ler a imagem** — extrair só o que está visível
2. **Escolher módulo** — tabela em [reference.md](reference.md)
3. **Montar** `organizacao/dados/foto_registro.json`
4. **Executar:**
   ```bash
   cd organizacao
   python3 registrar_foto.py dados/foto_registro.json
   ```
5. **Reembolsos médicos:** usar `reembolsos/` (não `registrar_foto.py`) — ver [reference.md](reference.md)
6. **Commit + push** se em cloud agent
7. **Responder** com os 3 blocos abaixo (sem a Priscila pedir link)

## Resposta obrigatória

```markdown
## ✅ Banco atualizado
- **Módulo:** [investimentos | financas | pacientes | …]
- **Entrou:** [resumo do registro]
- **Pendente:** [campos que não apareciam na foto, ou "nenhum"]

## 🔗 Ver esta atualização
👉 **[Título do painel]:** [link específico de links_modulos.json]

**No seu PC:** `Imagens\home\[caminho do arquivo_pc]`

## Links Seus
[catálogo geral — ver AGENTS.md]
```

Link específico: ler `organizacao/dados/links_modulos.json` ou `ultima_atualizacao.json` → campo `link_ver`.

## Regras

| Faça | Não faça |
|------|----------|
| `null` para campo invisível | Inventar telefone, CPF, valor |
| Checar protocolo/ticker antes de duplicar | Pular `registrar_foto.py` |
| Regenerar painéis (script já faz) | Só dizer "salvei" sem link |

## JSON mínimo

```json
{
  "modulo": "investimentos",
  "fonte": "foto",
  "descricao_foto": "o que é a imagem",
  "registros": [{ }]
}
```

Campos por módulo: [reference.md](reference.md)  
Exemplo real (Tesouro Direto): [examples.md](examples.md)

## Script

`organizacao/registrar_foto.py` — grava no banco, atualiza `ultima_atualizacao.json` com `link_ver`, regenera HTML.
