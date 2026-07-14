# Minha Central — organização pessoal

Uma central privada e local para organizar projetos, arquivos, vida financeira,
canal no YouTube, família, pacientes, atendimentos e prontuários.

## Começar

Requer somente Python 3. Não instala pacotes e não envia dados para serviços
externos.

```bash
cd central_pessoal
python3 app.py
```

Abra `http://127.0.0.1:8765`. Na primeira execução, o sistema cria
`central.db` com:

- seis áreas: Projetos, Consultório, Finanças, YouTube, Família e Arquivos;
- vinte cadastros de pacientes para personalizar;
- espaços genéricos para você, sua esposa e seus dois filhos;
- cinco projetos iniciais e quatro tarefas de configuração.

Os nomes são propositalmente genéricos para que nenhum dado sensível seja
inventado ou publicado no repositório.

## O que cada seção guarda

- **Projetos:** status, prioridade, prazo e próxima ação.
- **Tarefas:** lista única ligada a uma área ou projeto.
- **Pacientes:** cadastro e criação de registros de prontuário.
- **Agenda:** data, horário, paciente, status e valor dos atendimentos.
- **Finanças:** receitas e despesas, inclusive vinculadas a projetos.
- **Arquivos:** índice com caminho, área, projeto e tags. Os arquivos continuam
  nas pastas originais.

O banco também possui tabelas para prontuários e familiares. O esquema completo
está em `schema.sql`.

## Pastas sugeridas

Use `arquivos/` como ponto de partida:

```text
arquivos/
├── familia/
├── financas/
├── pacientes/
├── projetos/
└── youtube/
```

Dentro de cada pasta, prefira nomes como
`2026-07-14_assunto_descricao.ext`. Não coloque documentos clínicos ou
financeiros no Git.

## Segurança e backup

Prontuários e dados financeiros exigem proteção adicional:

1. execute o sistema somente em `127.0.0.1` (padrão);
2. use criptografia de disco e senha no computador;
3. mantenha backups criptografados do arquivo `central.db`;
4. não sincronize o banco ou prontuários em repositórios Git;
5. restrinja o acesso ao computador e encerre o servidor em máquinas
   compartilhadas.

O servidor local não implementa login. Isso é intencional para uso individual
no próprio computador; não use `--host 0.0.0.0` com dados reais.

## Testes

```bash
python3 -m unittest discover -s tests -v
```
