---
name: auto-aceitar-prs
description: Aprovar e mergear pull requests do Cursor sem pedir confirmação à Priscila. Use ao abrir PR, após push em branch cursor/*, ou quando ela pedir para aceitar PRs automaticamente.
---

# Auto-aceitar PRs (`cursor/*`)

## Regra da Priscila

**Nunca pedir** que ela aprove ou mergeie PRs de agentes. O repositório está
configurado para aceitar automaticamente branches `cursor/*`.

## O que o agente deve fazer

1. Trabalhar sempre em branch `cursor/<nome>-e9b5` (ou sufixo do ambiente).
2. **PR pronto para review** — não deixar em rascunho (`draft: false` ao criar).
3. Commit + push; o workflow `.github/workflows/auto-merge-cursor-prs.yml` faz:
   - atualizar branch com `main`
   - marcar pronto
   - aprovar e squash merge
4. Se o merge demorar ~1 min, pode rodar: `gh pr merge <n> --squash --delete-branch`
5. **Não** pedir "pode mergear?" / "aprova o PR?" na resposta.

## Configuração GitHub (uma vez por repo)

Se aprovação por Actions falhar nos logs:

**Settings → Actions → General → Workflow permissions**

- ✅ Read and write permissions  
- ✅ **Allow GitHub Actions to create and approve pull requests**

**Settings → Applications → Cursor** → marcar o repositório.

## Outros repositórios

Copiar template: `scripts/github-auto-merge/install.sh`

## Approval Agents (Cursor IDE)

Dashboard **Approval Agents** → agente com **Approve PR** para `pripalomo-svg/home`
(e site, quando instalado).
