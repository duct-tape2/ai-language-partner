#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INTERNAL_BRANCH="${INTERNAL_BRANCH:-codex/directory-first-pr-fast-lane}"
EXTERNAL_DIR="${EXTERNAL_FORGOODFIRSTISSUE_DIR:-/private/tmp/forgoodfirstissue}"
EXTERNAL_BRANCH="${EXTERNAL_FORGOODFIRSTISSUE_BRANCH:-add-ai-language-partner}"

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

require_clean() {
  local cwd="$1"
  if [[ -n "$(git -C "$cwd" status --porcelain)" ]]; then
    echo "refusing to publish from dirty worktree: $cwd" >&2
    git -C "$cwd" status -sb >&2
    exit 3
  fi
}

push_branch() {
  local cwd="$1"
  local remote="$2"
  local branch="$3"
  GIT_TERMINAL_PROMPT=0 git -C "$cwd" \
    -c credential.helper= \
    -c credential.helper='!f() { echo username=x-access-token; echo password=$GITHUB_TOKEN; }; f' \
    push -u "$remote" "$branch"
}

require_clean "$ROOT"
git -C "$ROOT" rev-parse --verify "$INTERNAL_BRANCH" >/dev/null
push_branch "$ROOT" origin "$INTERNAL_BRANCH"
"$ROOT/scripts/create_pr_from_clipboard_token.py" \
  --token-source env \
  --repo duct-tape2/ai-language-partner \
  --head "duct-tape2:${INTERNAL_BRANCH}" \
  --title "docs: add directory first PR fast lane" \
  --body "Adds the directory visitor first-PR fast lane, maintainer response snippets, safer claim guidance, token-safe publish helpers, and template links so contributors from external directories can reach a browser-friendly first PR path." \
  --draft

if [[ -d "$EXTERNAL_DIR/.git" ]]; then
  require_clean "$EXTERNAL_DIR"
  git -C "$EXTERNAL_DIR" rev-parse --verify "$EXTERNAL_BRANCH" >/dev/null
  push_branch "$EXTERNAL_DIR" fork "$EXTERNAL_BRANCH"
  "$ROOT/scripts/create_pr_from_clipboard_token.py" \
    --token-source env \
    --repo github/forgoodfirstissue \
    --head "duct-tape2:${EXTERNAL_BRANCH}" \
    --title "Add AI Language Partner" \
    --body "Repository issues page: https://github.com/duct-tape2/ai-language-partner/issues"
else
  echo "skipping For Good First Issue PR; checkout not found: $EXTERNAL_DIR" >&2
fi
