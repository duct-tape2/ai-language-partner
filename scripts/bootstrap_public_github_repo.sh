#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-sinmb79/ai-language-partner}"

if [[ -z "${GITHUB_TOKEN:-}" && -n "${GH_TOKEN:-}" ]]; then
  export GITHUB_TOKEN="$GH_TOKEN"
fi

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "GITHUB_TOKEN or GH_TOKEN is required" >&2
  exit 2
fi

if [[ -n "$(git status --short)" ]]; then
  echo "working tree must be clean before publishing" >&2
  git status --short >&2
  exit 1
fi

python3 scripts/check_public_tree.py
python3 scripts/create_github_repository.py "$REPO"

if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "git@github.com:${REPO}.git"
fi

git push -u origin main

python3 scripts/create_github_labels.py "$REPO"
python3 scripts/create_github_issue_seeds.py "$REPO"

python3 scripts/update_claude_application_evidence.py "$REPO" --dry-run || true
python3 scripts/verify_claude_for_oss_readiness.py "$REPO" || true

echo
echo "Published source, labels, and starter issues."
echo "Phase B will remain unready until 20 unique external contributors have merged PRs."
