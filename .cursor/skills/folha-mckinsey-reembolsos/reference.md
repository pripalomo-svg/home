# Referência — folha McKinsey

## Arquivos

| Arquivo | Função |
| --- | --- |
| `reembolsos/importar_dados.py` | `FOLHA_MCKINSEY`, `aplicar_folha_mckinsey()`, `DOCUMENTOS`, `VINCULOS` |
| `reembolsos/documentos/referencia/folha-mckinsey-reembolsos-*.pdf` | PDFs arquivados por competência |
| `reembolsos/reembolsos.db` | Fonte da verdade (recriado por `importar_dados.py`) |

## Lógica de status (`aplicar_folha_mckinsey`)

Após importar a planilha, `aplicar_folha_mckinsey(conn)` atualiza por `n_claim`:

| Condição | `status` |
| --- | --- |
| `valor_reembolsado >= valor_pago - 1` | `pago` |
| `valor_reembolsado > 1` (parcial) | `pago_parcial` |
| Acertado na folha com valor simbólico (ex. ≤ R$ 1) | **`pago`** |
| `situacao` | `Acertado na folha MM/AAAA` |
| `data_pagamento` | data acerto folha (ISO) |

**Nunca** marcar folha McKinsey como `negado` só por reembolso baixo na folha.

## Extração do PDF

```bash
pip install pdfplumber  # se necessário
python3 -c "
import pdfplumber
with pdfplumber.open('arquivo.pdf') as pdf:
    print(pdf.pages[0].extract_text())
"
```

Título esperado: `Descritivo de Reembolsos Médicos/Medicamentos em folha de pagamento - [Mês]/[Ano] McKinsey`

Campos por linha: CLAIM NUMBER (9 dígitos), valores com vírgula/ponto (OCR pode separar “7 00,00” → 700,00).

## Exemplo real (jun/2026)

| Claim | Reembolso folha | Acerto | Resultado no banco |
| --- | --- | --- | --- |
| 139159180 | 0,02 | 29/06/2026 | `pago`, R$ 0,02 reembolsado |

## Adicionar documento novo

Em `DOCUMENTOS`:

```python
("referencia/folha-mckinsey-reembolsos-2026-07.pdf", "Descritivo McKinsey — folha jul/2026", "referencia", "2026-07-31", "Claims: …"),
```

Em `VINCULOS`:

```python
"referencia/folha-mckinsey-reembolsos-2026-07.pdf": ["123456789", "987654321"],
```

Um PDF pode vincular a **vários** claims da mesma folha.

## Verificação

```bash
sqlite3 reembolsos/reembolsos.db \
  "SELECT n_claim, status, valor_reembolsado, data_pagamento, situacao FROM reembolsos WHERE n_claim IN ('139159180');"
```

## Duplicatas

- Mesma competência + mesmo `n_claim` → atualizar observação, não duplicar tupla em `FOLHA_MCKINSEY`.
- Mesmo PDF (md5) → não copiar de novo para `documentos/`.
