# Auto-merge de PRs Cursor — template reutilizável

Copia estes arquivos para **qualquer repositório** da Priscila para que PRs em
branches `cursor/*` sejam atualizados, aprovados e mergeados sem revisão manual.

## Instalação rápida

```bash
# No repositório destino (ex.: pripalomo-svg.github.io)
/path/to/home/scripts/github-auto-merge/install.sh .
git add .github/workflows/auto-merge-cursor-prs.yml APPROVAL_POLICY.md .cursor AGENTS.md
git commit -m "ci: auto-aprovar e mergear PRs cursor/*"
git push
```

## Configuração no GitHub (uma vez por repositório)

1. **Settings → Actions → General → Workflow permissions**
   - *Read and write permissions*
   - ✅ **Allow GitHub Actions to create and approve pull requests**
   - Link direto: `https://github.com/OWNER/REPO/settings/actions` (trocar OWNER/REPO)

2. **Settings → Applications → Cursor** → marcar o repositório.

O workflow roda ao abrir/atualizar PR `cursor/*`, a cada **hora** (cron) e após push na `main`.

## Repositórios da Priscila

| Repositório | Auto-merge |
| --- | --- |
| [home](https://github.com/pripalomo-svg/home) | ✅ ativo |
| [pripalomo-svg.github.io](https://github.com/pripalomo-svg/pripalomo-svg.github.io) | ⏳ instalar (ver acima) |

## Approval Agents (Cursor)

Opcional: criar um Approval Agent no dashboard do Cursor apontando para cada
repositório, com **Approve PR** habilitado. Complementa o workflow do GitHub.
