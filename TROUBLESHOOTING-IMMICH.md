# Immich Troubleshooting / Recovery Notes (This Repo)

This file documents a real recovery performed on 2026-03-11 (Europe/Berlin) after Immich stopped working and the library appeared empty / offline.

## What Happened (Root Causes)

1. **API never listened on port 2283 (container unhealthy)**  
   Symptom: `immich_server` healthcheck failed and nothing was listening on `2283`.  
   Root cause: Postgres got stuck repeatedly on `system_metadata` upserts and Immich bootstrap blocked before binding the HTTP server.

2. **Wrong `UPLOAD_LOCATION` caused a “missing files” cascade**  
   `UPLOAD_LOCATION` was pointed at `./library/immich_system_data` (mostly empty) while the real data lived in `./library/imported` and `./library/upload`.  
   Result: Immich marked almost all assets as deleted at **2026-03-11 00:00 UTC** and set `asset.isOffline=true`.

3. **External library path mismatch: DB expects `/imported` but container did not have it**  
   `library.importPaths` was `{"/imported"}` and assets had `originalPath` like `/imported/...`, but the container only had `/data/...`.  
   Result: UI showed “Datei offline …” even though files existed on the host.

4. **Thumbs path mismatch: Immich tried `/data/thumbs/...` but thumbs were stored elsewhere**  
   Thumbnails were physically under `./library/immich_system_data/thumbs/...`.  
   Result: blurred thumbnails and “Fehler beim Laden des Bildes” with server logs showing `ENOENT` for `/data/thumbs/...`.

## What Was Fixed (Effective Changes)

### Docker / Mounts

- Keep `UPLOAD_LOCATION=./library` (the real root containing `imported/`, `upload/`, etc).
- Add compatibility mounts in `docker-compose.yml`:
  - `${UPLOAD_LOCATION}/imported:/imported` (matches `library.importPaths={/imported}`)
  - `${UPLOAD_LOCATION}/immich_system_data/thumbs:/data/thumbs` (matches where thumbs actually are)
- Force-recreate when env/mounts change:
  - `docker compose up -d --force-recreate immich-server`

### Database

- **Unstuck bootstrap:** swapped out the `system_metadata` table+PK by renaming the old objects and recreating a fresh table, then copying rows (table is tiny).
- **Restore “false deletions”:** reverted the mass-deletion performed at 2026-03-11 00:00 UTC by setting `asset.deletedAt = NULL` for that date.
- **Clear offline flag:** set `asset.isOffline=false` for active external library assets.

## External DB Access (for indexing scripts)

The Python indexing scripts run **outside** Docker and need to connect to the database directly.

**Required:** Expose PostgreSQL port in `docker-compose.yml`:

```yaml
immich_postgres:
  ports:
    - "5432:5432"
```

Without this, you'll get:
```
connection to server at "localhost", port 5432 failed: Connection refused
```

## Fast Checks (When Something Breaks Again)

### 1) Does the API listen?

```sh
docker compose ps immich-server
curl -v --max-time 3 http://localhost:2283/api/server/ping
```

If the container is `unhealthy` and nothing listens, check if Postgres is stuck:

```sh
docker compose exec -T database psql -U postgres -d immich -c \
"select pid, state, wait_event_type, wait_event, now()-query_start as age, left(query,120)
 from pg_stat_activity
 where datname='immich' and pid<>pg_backend_pid()
 order by age desc
 limit 30;"
```

### 2) Are external library paths mountable inside the container?

```sh
docker compose exec -T immich-server sh -lc "test -d /imported && echo ok || echo missing"
docker compose exec -T immich-server sh -lc "test -f '/imported/Photos from 2024/IMG_6353.JPG' && echo ok || echo missing"
```

### 3) Are thumbnails reachable?

If logs show `ENOENT ... /data/thumbs/...` then verify:

```sh
docker compose exec -T immich-server sh -lc "test -d /data/thumbs && echo ok || echo missing"
```

### 4) Did Immich mark everything offline / deleted?

```sql
-- counts
select
  count(*) as total,
  count(*) filter (where "deletedAt" is null) as active,
  count(*) filter (where "deletedAt" is not null) as deleted,
  count(*) filter (where "isOffline"=true) as offline
from asset;

-- external library root prefixes
select split_part("originalPath", '/', 2) as root, count(*)
from asset
where "deletedAt" is null
group by 1
order by 2 desc;

-- external library config
select id, name, "importPaths" from library;
```

## Recovery Snippets (Used Here)

### A) Undo a mass deletion by date (example: 2026-03-11)

```sql
begin;
update asset set "deletedAt" = null
where "deletedAt"::date = '2026-03-11';
commit;
```

### B) Clear offline for active external library assets

```sql
begin;
update asset set "isOffline" = false
where "deletedAt" is null and "libraryId" is not null;
commit;
```

### C) Recreate `system_metadata` (tiny table) if it causes bootstrap stalls

Only do this if Immich won’t bind and Postgres repeatedly hangs on `system_metadata` upserts.

```sql
begin;
alter index system_metadata_pkey rename to system_metadata_pkey_old_YYYYMMDD;
alter table system_metadata rename to system_metadata_bad_YYYYMMDD;
create table system_metadata (
  "key" varchar not null,
  value jsonb not null,
  constraint system_metadata_pkey primary key ("key")
);
insert into system_metadata("key", value)
select "key", value from system_metadata_bad_YYYYMMDD;
commit;
```

## Preventative Notes

- Do not change `UPLOAD_LOCATION` unless you also migrate the on-disk layout.
- If you use external libraries, ensure their `importPaths` match real container paths (mount them explicitly).
- When thumbs are stored outside the standard layout, keep a dedicated mount for `/data/thumbs`.
- Prefer `docker compose up -d --force-recreate immich-server` after changing `.env` or volume mappings.

