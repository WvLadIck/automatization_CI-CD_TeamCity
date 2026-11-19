#!/usr/bin/env bash
set -euo pipefail

mode="$1"
: "${APP_TAG:?Укажите тег успешно собранного образа}"
export APP_TAG
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT

case "$mode" in
  stage) ;;
  backup|prod)
    [[ "$BACKUP_ID" =~ ^[0-9]+$ ]]
    test "$(git rev-parse HEAD^{tree})" = "$STAGE_TREE"
    test "$(sha256sum db/schema.sql | cut -d ' ' -f 1)" = "$STAGE_SCHEMA"
    ;;
  *) exit 2 ;;
esac

docker compose pull app
if [ "$mode" != stage ]; then
  image_id=$(docker image inspect -f '{{.Id}}' "${APP_IMAGE:-wvladick/student-grades-app}:$APP_TAG")
  test "$image_id" = "$STAGE_IMAGE_ID"
fi
docker compose up -d --wait db
db=$(docker compose ps -q db)
bash ci/dump-schema.sh "$db" > "$work/before.sql"

if cmp -s "$work/before.sql" db/schema.sql; then
  echo "Target schema already matches."
else
  echo "Schema before deployment differs from the target:"
  diff -u "$work/before.sql" db/schema.sql || test "$?" -eq 1
  if cmp -s "$work/before.sql" db/schema-history/base.sql; then
    revision=base
  else
    revision=$(docker exec "$db" sh -ec '
      psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT version_num FROM alembic_version"
    ')
    case "$revision" in
      0002|0003) ;;
      *) echo "Unrecognized database revision: $revision" >&2; exit 1 ;;
    esac
  fi
  diff -u "db/schema-history/$revision.sql" "$work/before.sql"
fi

if [ "$mode" = backup ]; then
  bash ci/backup-db.sh "$db" "$BACKUP_ID"
  exit 0
fi
if [ "$mode" = prod ]; then
  backup="$HOME/backups/studentgrades-$BACKUP_ID.dump"
  test -s "$backup"
  docker exec -i "$db" pg_restore --list < "$backup" >/dev/null
fi

docker compose run --rm --no-deps --pull never -T app alembic upgrade head
bash ci/dump-schema.sh "$db" > "$work/after.sql"
diff -u db/schema.sql "$work/after.sql"
echo "Schema after deployment matches:"
sha256sum "$work/after.sql"

docker compose up -d --no-build --no-deps --pull never app
curl --retry 10 --retry-delay 2 --retry-all-errors --fail --silent \
  http://127.0.0.1:5000/ -o /dev/null
docker compose ps

if [ "$mode" = stage ]; then
  marker=$(mktemp "$HOME/studentgrades-stage-release.XXXXXX")
  git rev-parse HEAD^{tree} > "$marker"
  echo "$APP_TAG" >> "$marker"
  mv -- "$marker" "$HOME/studentgrades-stage-release"
fi
