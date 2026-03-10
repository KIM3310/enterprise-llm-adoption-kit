#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[sanitize] removing local secrets (.env)..."
rm -f .env
rm -f .env.local .env.development .env.production

echo "[sanitize] removing generated runtime data (sqlite/audit/chroma)..."
rm -f app/backend/data/audit.log
rm -f app/backend/data/app.db app/backend/data/app.db-shm app/backend/data/app.db-wal
rm -f app/backend/data/app.db-*
rm -rf app/backend/data/chroma
rm -f app/data/audit.log app/data/app.db app/data/app.db-shm app/data/app.db-wal
rm -f app/data/app.db-*
rm -f app/data/handover_normalized.jsonl
rm -rf app/data/chroma

echo "[sanitize] removing frontend build outputs..."
rm -rf app/frontend/dist

echo "[sanitize] scanning for common secret patterns (best-effort)..."
if command -v rg >/dev/null 2>&1; then
  # This is intentionally broad; it should catch accidental commits before you publish.
  rg -n --hidden --no-ignore-vcs \
    --glob '!.git/**' \
    --glob '!**/.venv/**' \
    --glob '!**/venv/**' \
    --glob '!**/node_modules/**' \
    --glob '!**/dist/**' \
    --glob '!scripts/sanitize_repo.sh' \
    -e 'sk-[A-Za-z0-9]{20,}' \
    -e 'BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY' \
    -e 'AWS_SECRET_ACCESS_KEY' \
    -e 'AWS_ACCESS_KEY_ID' \
    -e 'xox[baprs]-' \
    -e 'ghp_[A-Za-z0-9]+' \
    -e 'AIza[0-9A-Za-z\\-_]{20,}' \
    . || true
else
  echo "[sanitize] rg not found; skipping scan."
fi

echo "[sanitize] done."
