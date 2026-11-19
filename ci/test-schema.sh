#!/usr/bin/env bash
set -euo pipefail

name="lr8-$1"
image="$2"
db="$name-db"
password=$(cat /proc/sys/kernel/random/uuid)

mkdir -p reports/schema-history
docker network create "$name" >/dev/null
trap 'docker rm -fv "$db" >/dev/null 2>&1 || true
      docker network rm "$name" >/dev/null 2>&1 || true' EXIT

docker run -d --name "$db" --network "$name" \
  -e POSTGRES_DB=students -e POSTGRES_USER=app_user \
  -e POSTGRES_PASSWORD="$password" postgres:18.6 >/dev/null

for attempt in $(seq 1 30); do
  if docker exec "$db" pg_isready -h 127.0.0.1 -U app_user -d students; then
    break
  fi
  sleep 2
done
docker exec "$db" pg_isready -h 127.0.0.1 -U app_user -d students

alembic_in_test() {
  docker run --rm --network "$name" \
    -e DATABASE_URL="postgresql://app_user:$password@$db/students" \
    "$image" alembic "$@"
}

probe() {
  bash ci/dump-schema.sh "$db"
}
probe > reports/schema-history/base.sql
alembic_in_test upgrade 0002
probe > reports/schema-history/0002.sql
alembic_in_test upgrade 0003
probe > reports/schema-history/0003.sql
alembic_in_test upgrade head
probe > reports/schema.sql
alembic_in_test upgrade 0002:0003 --sql > reports/0002-to-0003.sql
