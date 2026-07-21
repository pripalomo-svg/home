# Exemplos — foto para banco

## Exemplo 1: Tesouro Direto (Nu Invest)

**Foto:** e-mail "protocolo criado com sucesso" — Tesouro Direto e B3

**JSON** (`organizacao/dados/foto_registro.json`):

```json
{
  "modulo": "investimentos",
  "fonte": "foto",
  "descricao_foto": "Confirmação Tesouro Direto Nu Invest",
  "registros": [
    {
      "nome": "Tesouro Direto — protocolo 103681346",
      "protocolo": "103681346",
      "tipo": "tesouro_prefixado",
      "instituicao": "Nu Invest (NU INVESTIMENTOS S.A. - CTVM)",
      "valor_atual": null,
      "data_contratacao": "2026-07-16",
      "notas": "Protocolo criado. Aguardando liquidação."
    }
  ]
}
```

**Comando:**
```bash
cd organizacao && python3 registrar_foto.py dados/foto_registro.json
```

**Resposta à Priscila:**

```markdown
## ✅ Banco atualizado
- **Módulo:** investimentos
- **Entrou:** Tesouro Direto protocolo 103681346 (Nu Invest)
- **Pendente:** valor (não constava na foto)

## 🔗 Ver esta atualização
👉 **Investimentos:** https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main/organizacao/investimentos.html

**No seu PC:** `Imagens\home\organizacao\investimentos.html`
```

---

## Exemplo 2: Recibo de consulta (finanças)

```json
{
  "modulo": "financas",
  "fonte": "foto",
  "descricao_foto": "PIX recebido sessão",
  "registros": [
    {
      "descricao": "Sessão Beatriz Jubilut",
      "valor": "280",
      "data": "2026-07-16",
      "tipo": "receita",
      "categoria": "consultorio"
    }
  ]
}
```

**Link após salvar:** `index.html#financas`

---

## Exemplo 3: Reembolso médico (Cigna)

Não usar `registrar_foto.py`. Seguir `reembolsos/README.md`.

**Link:** `reembolsos/index.html`
