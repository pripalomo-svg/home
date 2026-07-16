---
name: foto-para-banco
description: Quando a Priscila enviar foto, imagem, print ou PDF visual — extrair dados e registrar no banco correto (organização, reembolsos, etc.) e avisar o que mudou.
---

# Foto → Banco de dados

## Quando usar

Ative esta skill sempre que a Priscila enviar:
- print de app bancário / corretora / Tesouro Direto
- nota fiscal, recibo, boleto, extrato
- foto de documento, agenda, lista
- qualquer imagem com dados para cadastrar

## Fluxo obrigatório

1. **Ler a imagem** — extrair todos os campos visíveis (valores, datas, nomes, protocolos, CNPJ, etc.)
2. **Identificar o módulo** (tabela abaixo)
3. **Salvar registro** em `organizacao/dados/foto_registro.json` (criar se não existir)
4. **Rodar** `python3 organizacao/registrar_foto.py organizacao/dados/foto_registro.json`
5. **Commit + push** se estiver em cloud agent
6. **Responder sempre com:**
   - bloco **✅ Banco atualizado** (o que entrou, onde, campos preenchidos e o que faltou)
   - bloco **Links Seus** (reembolsos + organização — ver `AGENTS.md`)

## Roteamento — qual banco?

| Se a foto mostra… | Módulo | Destino |
|-------------------|--------|---------|
| Investimento, Tesouro, CDB, FII, ação, corretora | `investimentos` | `templates/investimentos.csv` → `investimentos` |
| Gasto, receita, PIX, cartão, fatura | `financas` | `templates/financas.csv` |
| Reembolso médico, Cigna, NF, recibo clínico | `reembolsos` | `reembolsos/` via `reembolsos.py` |
| Paciente, prontuário, sessão | `consultorio` | `templates/pacientes.csv` / `atendimentos.csv` |
| Documento genérico, contrato, PDF | `arquivo` | tabela `arquivos` + pasta `documentos/` |
| Não der para classificar | `nota` | tabela `notas` com texto extraído |

## Formato do JSON (`foto_registro.json`)

```json
{
  "modulo": "investimentos",
  "fonte": "foto",
  "descricao_foto": "Confirmação Tesouro Direto Nu Invest",
  "registros": [
    {
      "nome": "Tesouro Direto — protocolo 103681346",
      "tipo": "tesouro_prefixado",
      "instituicao": "Nu Invest",
      "valor_atual": null,
      "notas": "Protocolo 103681346 criado com sucesso. Aguardando liquidação."
    }
  ]
}
```

Campos `null` = não visível na foto — **não inventar** valores.

## Regras

- **Nunca inventar** telefone, CPF, valor ou nome de paciente
- Se faltar valor obrigatório, cadastrar com `notas` explicando e `valor_atual` só se visível
- Duplicatas: buscar por protocolo, ticker ou data+valor antes de inserir
- Após registrar, regenerar painéis (`ATUALIZAR.bat` ou scripts `gerar_*`)
- Log em `organizacao/ultima_atualizacao.json` — a Priscila pode consultar

## Mensagem padrão ao atualizar

```
✅ Banco atualizado
- Módulo: investimentos
- Adicionado: Tesouro Direto protocolo 103681346 (Nu Invest)
- Pendente: valor (não aparecia na foto)
- Painéis: index.html e investimentos.html regenerados
```
