#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-duct-tape2/ai-language-partner}"

if ! command -v pbpaste >/dev/null 2>&1; then
  echo "pbpaste is required on macOS" >&2
  exit 2
fi

TOKEN="$(pbpaste | tr -d '\r\n[:space:]')"
if [[ -z "$TOKEN" ]]; then
  echo "clipboard does not contain a GitHub token" >&2
  exit 2
fi

if [[ ! "$TOKEN" =~ ^(ghp_|github_pat_|gho_|ghu_|ghs_|ghr_) ]]; then
  echo "clipboard text does not look like a GitHub token; refusing to use it" >&2
  exit 2
fi

cleanup() {
  printf '' | pbcopy || true
}
trap cleanup EXIT

GITHUB_TOKEN="$TOKEN" scripts/bootstrap_public_github_repo.sh "$REPO"
