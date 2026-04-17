# immich-server (local notes)

This repo contains a local Immich Docker Compose setup plus recovery notes/scripts.

## Known Pitfalls / What Broke (2026-03-11)

1. Immich API never bound to `:2283` (container unhealthy): Postgres was repeatedly stuck around `system_metadata`, blocking bootstrap before `listen()`.
2. Wrong `UPLOAD_LOCATION` caused Immich to mark most assets deleted/offline (mass change at **2026-03-11 00:00 UTC**).
3. External library path mismatch: DB `library.importPaths={/imported}` but container had no `/imported` mount.
4. Thumbnails path mismatch: Immich served thumbs from `/data/thumbs/...` but they were stored under `./library/immich_system_data/thumbs/...`.

## Docs / Tools

- Recovery runbook: `TROUBLESHOOTING-IMMICH.md`
- Quick health checks: `scripts/immich-doctor.sh`

