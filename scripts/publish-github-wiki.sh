#!/usr/bin/env bash
set -euo pipefail
mode="${1:-publish}"
[[ "$mode" == "publish" || "$mode" == "--dry-run" ]] || { echo "Usage: bash scripts/publish-github-wiki.sh [--dry-run]" >&2; exit 2; }
cd "$(git rev-parse --show-toplevel)"
test -f docs/wiki/Home.md
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
git clone --quiet "https://github.com/nyameko/agent-control-plane.wiki.git" "$tmp/wiki"
python3 scripts/prepare_github_wiki.py --source docs/wiki --destination "$tmp/wiki" --repo "nyameko/agent-control-plane"
git -C "$tmp/wiki" add -- '*.md'
git -C "$tmp/wiki" status --short
git -C "$tmp/wiki" diff --cached --quiet && { echo "No changes"; exit 0; }
git -C "$tmp/wiki" diff --cached --stat
[[ "$mode" == "--dry-run" ]] && { echo "Dry run; nothing pushed"; exit 0; }
git -C "$tmp/wiki" commit -m "docs(wiki): sync reviewed ACP guides"
git -C "$tmp/wiki" push origin HEAD
echo "Published to https://github.com/nyameko/agent-control-plane/wiki"
