#!/usr/bin/env bash
set -euo pipefail

release="$HOME/studentgrades-stage-release"
tree=$(sed -n '1p' "$release")
tag=$(sed -n '2p' "$release")
[[ "$tree" =~ ^[0-9a-f]{40}$ ]]
[[ "$tag" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]

export APP_TAG="$tag"
app=$(docker compose ps -q app)
db=$(docker compose ps -q db)
image=$(docker inspect -f '{{.Config.Image}}' "$app")
test "$image" = "${APP_IMAGE:-wvladick/student-grades-app}:$tag"
image_id=$(docker inspect -f '{{.Image}}' "$app")
[[ "$image_id" =~ ^sha256:[0-9a-f]{64}$ ]]

schema=$(bash ci/dump-schema.sh "$db" | sha256sum | cut -d ' ' -f 1)
echo "STAGE schema: $schema; image: $image; ID: $image_id"
echo "##teamcity[setParameter name='stage.schema' value='$schema']"
echo "##teamcity[setParameter name='stage.tree' value='$tree']"
echo "##teamcity[setParameter name='stage.tag' value='$tag']"
echo "##teamcity[setParameter name='stage.imageid' value='$image_id']"
