#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[immich-doctor] compose status"
docker compose ps immich-server || true

echo
echo "[immich-doctor] ping"
curl -fsS --max-time 3 "http://localhost:2283/api/server/ping" >/dev/null \
  && echo "OK: API responds" \
  || echo "WARN: API not reachable on http://localhost:2283"

echo
echo "[immich-doctor] container path checks"
docker compose exec -T immich-server sh -lc '
  set -e
  for p in /data /data/thumbs /imported; do
    if [ -d "$p" ]; then echo "OK: dir $p"; else echo "WARN: missing dir $p"; fi
  done
'

echo
echo "[immich-doctor] external library configuration"
docker compose exec -T database psql -U postgres -d immich -Atc \
  "select name||' => '||array_to_string(\"importPaths\", ',') from library;" || true

echo
echo "[immich-doctor] asset flags (active/offline/deleted)"
docker compose exec -T database psql -U postgres -d immich -c \
  "select count(*) as total,
          count(*) filter (where \"deletedAt\" is null) as active,
          count(*) filter (where \"deletedAt\" is not null) as deleted,
          count(*) filter (where \"isOffline\"=true) as offline
   from asset;" || true

