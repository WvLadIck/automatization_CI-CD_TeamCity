#!/usr/bin/env bash
set -euo pipefail
db="$1"
id="${2:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
[[ "$id" =~ ^[A-Za-z0-9_-]+$ ]]
umask 077
mkdir -p "$HOME/backups"
chmod 700 "$HOME/backups"
target="$HOME/backups/studentgrades-$id.dump"
backup=$(mktemp "$target.part.XXXXXX")
trap 'rm -f -- "$backup"' EXIT

docker exec "$db" sh -ec '
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc
' > "$backup"
test -s "$backup"
docker exec -i "$db" pg_restore --list < "$backup" >/dev/null

mv -- "$backup" "$target"
echo "Backup verified: $target"
ls -lh "$target"
