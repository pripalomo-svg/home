# Política de aprovação automática

A titular do repositório prefere que pull requests criados por agentes Cursor
(branches `cursor/*`) sejam **aprovados e mergeados automaticamente**, sem
revisão manual.

## Pode aprovar e mergear automaticamente

- Atualizações de conteúdo, dados, documentos e painéis
- Workflows em `.github/workflows/` que automatizam tarefas rotineiras
- Correções e melhorias incrementais geradas por agentes

## Exige revisão humana

- Exclusão em massa de arquivos ou dados sem substituição equivalente
- Mudanças de domínio, DNS, permissões ou visibilidade do repositório
- Alterações de credenciais, tokens ou segredos
