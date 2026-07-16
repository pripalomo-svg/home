#!/usr/bin/env bash
# Instala auto-merge de PRs cursor/* em outro repositório local.
# Uso: ./install.sh /caminho/para/outro-repo
set -euo pipefail

DEST="${1:?Informe o caminho do repositório destino}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$DEST/.github/workflows" "$DEST/.cursor/approval-policies"
cp "$SCRIPT_DIR/workflow.yml" "$DEST/.github/workflows/auto-merge-cursor-prs.yml"
cp "$SCRIPT_DIR/APPROVAL_POLICY.md" "$DEST/APPROVAL_POLICY.md"
cp "$SCRIPT_DIR/ROUTING.md" "$DEST/.cursor/approval-policies/ROUTING.md"

if [ ! -f "$DEST/AGENTS.md" ]; then
  cat > "$DEST/AGENTS.md" <<'EOF'
# Instruções para agentes

## Preferências

1. **PRs do Cursor** (`cursor/*`): aprovar e mergear automaticamente, sem pedir
   permissão manual. Workflow: `.github/workflows/auto-merge-cursor-prs.yml`.
EOF
  echo "Criado AGENTS.md básico."
else
  echo "AGENTS.md já existe — adicione manualmente a preferência de auto-merge (item 4 em home/AGENTS.md)."
fi

echo "Instalado em $DEST"
echo "Próximo passo: commit, push e merge na main do repositório destino."
echo "No GitHub: Settings → Actions → General → 'Allow GitHub Actions to create and approve pull requests'"
