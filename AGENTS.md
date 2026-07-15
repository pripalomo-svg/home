# Instruções para agentes — repositório home (Família Palomo)

## Preferências da Priscila (sempre seguir)

1. **Em TODA mensagem/resumo, incluir os links do banco de dados de
   reembolsos** para ela verificar como está ficando:
   - Painel de visualização: https://raw.githack.com/pripalomo-svg/home/main/reembolsos/index.html
   - Controle editável: https://raw.githack.com/pripalomo-svg/home/main/reembolsos/controle.html
   - Pasta no GitHub: https://github.com/pripalomo-svg/home/tree/main/reembolsos
   - Se o trabalho estiver em uma branch ainda não merged, informar também o
     link da branch: `https://raw.githack.com/pripalomo-svg/home/<branch>/reembolsos/index.html`
2. Comunicação direta e concisa, sem elogios desnecessários (ver
   `reembolsos/documentos/referencia/memoria-familia-palomo.md`).

## Sobre o banco de reembolsos (`reembolsos/`)

- `reembolsos.db` (SQLite) é a fonte da verdade; `index.html` (visualização)
  e `controle.html` (edição) são gerados a partir dele.
- Após qualquer mudança no banco, regenerar os dois painéis:
  `python3 importar_dados.py && python3 gerar_dashboard.py && python3 gerar_controle.py`
- Documentos novos vão em `reembolsos/documentos/` (subpastas por categoria)
  e devem ser vinculados aos claims em `importar_dados.py`.
- Antes de adicionar documentos enviados pela usuária, conferir por hash
  (md5sum) se já não existem no repositório — ela costuma reenviar o lote inteiro.
