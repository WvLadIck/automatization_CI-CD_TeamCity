#!/usr/bin/env bash
set -euo pipefail
docker exec "$1" sh -ec '
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --schema-only --no-owner --no-privileges
' | sed '/^\\restrict /d; /^\\unrestrict /d'
