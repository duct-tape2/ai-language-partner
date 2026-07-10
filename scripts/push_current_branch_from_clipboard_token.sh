#!/usr/bin/env bash
set -euo pipefail

REMOTE="${1:-origin}"
BRANCH="${2:-$(git branch --show-current)}"

if [[ -z "$BRANCH" ]]; then
  echo "could not determine current git branch" >&2
  exit 2
fi

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

export GITHUB_TOKEN="$TOKEN"

GIT_TERMINAL_PROMPT=0 git \
  -c credential.helper= \
  -c credential.helper='!f() { echo username=x-access-token; echo password=$GITHUB_TOKEN; }; f' \
  push -u "$REMOTE" "$BRANCH"
