---
name: folha-mckinsey-reembolsos
description: Processa PDF da folha McKinsey (Descritivo de Reembolsos Médicos/Medicamentos) e marca os claims no banco reembolsos como pago. Use quando a Priscila enviar folha de pagamento McKinsey, descritivo de reembolsos na folha, ou PDF com LUISA JULIANA FARIA RAMALHO DE SOUZA e CLAIM NUMBER.
---

# Folha McKinsey → reembolsos como **pago**

## Quando aplicar

- PDF ou print **“Descritivo de Reembolsos Médicos/Medicamentos em folha de pagamento”** (McKinsey)
- Titular: **Luisa Juliana Faria Ramalho de Souza**
- Colunas típicas: paciente, prestador, valor, reembolso, diferença, **CLAIM NUMBER**, data acerto folha

## Regra da Priscila

**Todo claim que aparecer na folha McKinsey com acerto na folha → status `pago`.**  
(Inclui reembolso simbólico, ex. R$ 0,02 — processo encerrado na folha, não `negado`.)

## Fluxo (ordem fixa)

1. **Hash** — `md5sum` do PDF; se já existir em `reembolsos/documentos/referencia/`, não duplicar arquivo.
2. **Extrair** — `pdfplumber` ou `pdftotext`; para cada linha: `n_claim`, valor reembolsado, data acerto folha (DD/MM/AA), paciente/prestador se legível.
3. **Competência** — mês/ano do título da folha (ex. “Junho/2026” → `2026-06`).
4. **Registrar em** `reembolsos/importar_dados.py`:
   - Adicionar tupla em `FOLHA_MCKINSEY` (sem repetir o mesmo `n_claim` + competência).
   - Copiar PDF para `documentos/referencia/folha-mckinsey-reembolsos-YYYY-MM.pdf`.
   - Incluir em `DOCUMENTOS` e `VINCULOS` (claim → PDF).
5. **Recriar banco e painéis:**
   ```bash
   cd reembolsos
   python3 importar_dados.py && python3 gerar_dashboard.py && python3 gerar_controle.py
   ```
6. **Commit + push** (branch `cursor/...-e9b5` se cloud agent).
7. **Responder** com blocos abaixo + **Links Seus** (`AGENTS.md`).

## Formato da tupla `FOLHA_MCKINSEY`

```python
# (competência YYYY-MM, n_claim, valor_reembolsado, data_acerto ISO, observação)
("2026-06", "139159180", 0.02, "2026-06-29", "Folha jun/2026: …"),
```

A função `aplicar_folha_mckinsey()` já define **status = pago** para acertos na folha (ver [reference.md](reference.md)).

## Resposta obrigatória

```markdown
## ✅ Folha McKinsey processada
- **Competência:** jun/2026
- **Claims atualizados:** 139159180 (Priscila / Akaishi) → **pago**, reembolso R$ 0,02, acerto 29/06/2026
- **PDF:** `documentos/referencia/folha-mckinsey-reembolsos-2026-06.pdf`

## 🔗 Ver esta atualização
👉 **Reembolsos:** https://raw.githack.com/pripalomo-svg/home/main/reembolsos/index.html
(filtrar pelo claim ou beneficiário)

## Links Seus
[bloco completo do AGENTS.md]
```

## Se o claim não existir no banco

- Buscar na planilha `planilha-reembolsos-luisa-12-2025.xlsx` ou criar entrada manual em `importar_extras` **antes** de aplicar a folha.
- Não inventar `n_claim`; usar só o número do PDF.

## Integração

- Fotos de outros tipos → skill `foto-para-banco`
- Link após update → skill `link-atualizacao`

Detalhes técnicos: [reference.md](reference.md)
