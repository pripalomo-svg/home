# Política de aprovação automática — repositório home

A titular do repositório prefere que pull requests criados por agentes Cursor
(branches `cursor/*`) sejam **aprovados e mergeados automaticamente**, sem
revisão manual.

## Pode aprovar e mergear automaticamente

- Atualizações de dados, documentos e painéis (`reembolsos/`, `organizacao/`,
  `base-dados-empresa/`, etc.)
- Workflows em `.github/workflows/` que automatizam tarefas rotineiras
- Correções e melhorias incrementais geradas por agentes

## Exige revisão humana

- Exclusão em massa de arquivos ou dados sem substituição equivalente
- Mudanças que tornem o repositório privado/público ou alterem permissões de
  colaboradores
- Alterações de credenciais, tokens ou segredos
