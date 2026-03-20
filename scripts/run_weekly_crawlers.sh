#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Prefer uv from PATH; fallback to common install location.
if command -v uv >/dev/null 2>&1; then
  UV_BIN="uv"
elif [[ -x "$HOME/.local/bin/uv" ]]; then
  UV_BIN="$HOME/.local/bin/uv"
else
  echo "[ERROR] uv not found in PATH or \$HOME/.local/bin/uv"
  exit 1
fi

echo "[INFO] Starting weekly crawler pipeline at $(date -Is)"

# 1) Refresh links
"$UV_BIN" run python -m gi_wiki_scraper.link_parsers.generate_links
"$UV_BIN" run python -m hsr_wiki_scraper.link_parsers.generate_links

# 2) Incremental parsing
"$UV_BIN" run python -m gi_wiki_scraper.run_all_parsers_incremental
"$UV_BIN" run python -m hsr_wiki_scraper.run_all_parsers_incremental

# 3) Regenerate unified content bundle
"$UV_BIN" run python scripts/generate_all_content.py

echo "[INFO] Weekly crawler pipeline finished at $(date -Is)"
