# Referência — módulos e bancos

## Roteamento foto → banco

| Conteúdo da foto | `modulo` | Banco / tabela | Planilha (se houver) |
|------------------|----------|----------------|----------------------|
| Tesouro, CDB, FII, ação, corretora | `investimentos` | `organizacao.db` → `investimentos` | `templates/investimentos.csv` |
| Gasto, receita, PIX, fatura | `financas` | `financas_lancamentos` | `templates/financas.csv` |
| Dados de paciente | `pacientes` | `pacientes` | `templates/pacientes.csv` |
| Sessão realizada | `atendimentos` | `atendimentos` | `templates/atendimentos.csv` |
| Compromisso | `agenda` | `agenda` | `templates/agenda.csv` |
| Documento genérico | `arquivo` | `arquivos` | — |
| Não classificável | `nota` | `notas` | — |
| Reembolso Cigna / médico | — | `reembolsos.db` | Ver `reembolsos/README.md` |

## Links específicos (`organizacao/dados/links_modulos.json`)

| `modulo` | `link_painel` |
|----------|---------------|
| `investimentos` | `…/organizacao/investimentos.html` |
| `financas` | `…/organizacao/index.html#financas` |
| `pacientes` | `…/organizacao/cadastro_pacientes.html` |
| `atendimentos` | `…/organizacao/index.html#consultorio` |
| `agenda` | `…/organizacao/index.html#agenda` |
| `reembolsos` | `…/reembolsos/index.html` |

Base URL: `https://htmlpreview.github.io/?https://raw.githubusercontent.com/pripalomo-svg/home/main`

## Campos úteis por módulo

### investimentos
`nome`, `tipo`, `instituicao`, `ticker`, `valor_atual`, `protocolo`, `data_contratacao`, `notas`

Tipos: `vgbl`, `cdb`, `tesouro_prefixado`, `tesouro_selic`, `fii`, `fundo_rf`, `outro`

### financas
`descricao`, `valor`, `data`, `tipo` (receita/despesa), `categoria`

### pacientes
`codigo`, `nome`, `telefone`, `queixa_principal`, `dia_horario`

### atendimentos
`paciente_codigo`, `data`, `hora_inicio`, `modalidade`, `status`, `valor`

## Reembolsos (fluxo separado)

1. Salvar PDF/imagem em `reembolsos/documentos/`
2. Atualizar via `reembolsos/importar_dados.py` ou `reembolsos.py`
3. `python3 gerar_dashboard.py && python3 gerar_controle.py` em `reembolsos/`
4. Link: `reembolsos/index.html`

## Log

`organizacao/ultima_atualizacao.json` — histórico com `link_ver`, `titulo_painel`, `pendentes`.
