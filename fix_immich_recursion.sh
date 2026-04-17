#!/bin/bash
set -e

echo "🛑 Stopping Immich..."
docker compose down

echo "🔧 Updating UPLOAD_LOCATION to separate system data from user imports..."
# Use sed to replace the line in .env (MacOS compatible)
sed -i '' 's|UPLOAD_LOCATION=.*|UPLOAD_LOCATION=./library/immich_system_data|' .env
mkdir -p library/immich_system_data

echo "🧹 Cleaning up filesystem junk (recursive thumbnails/videos)..."
rm -rf library/imported/thumbs
rm -rf library/imported/encoded-video
rm -rf library/imported/upload
rm -rf library/imported/profile
rm -rf library/imported/library
rm -rf library/imported/backups

echo "🗄️ Starting Database for cleanup..."
docker compose up -d database

echo "⏳ Waiting for Database..."
sleep 10
until docker compose exec -T database pg_isready -U postgres; do
  echo "Waiting for DB..."
  sleep 2
done

echo "🗑️ Cleaning up Database (Removing ~900k junk assets)..."
docker compose exec -T database psql -U postgres -d immich -c "DELETE FROM asset WHERE \"originalPath\" LIKE '/imported/thumbs/%';"
docker compose exec -T database psql -U postgres -d immich -c "DELETE FROM asset WHERE \"originalPath\" LIKE '/imported/encoded-video/%';"
docker compose exec -T database psql -U postgres -d immich -c "DELETE FROM asset WHERE \"originalPath\" LIKE '/imported/upload/%';"
docker compose exec -T database psql -U postgres -d immich -c "DELETE FROM asset WHERE \"originalPath\" LIKE '/imported/profile/%';"
docker compose exec -T database psql -U postgres -d immich -c "DELETE FROM asset WHERE \"originalPath\" LIKE '/imported/library/%';"

echo "🚀 Restarting Immich..."
docker compose up -d

echo "✅ Done! Verifying asset count..."
sleep 5
docker compose exec -T database psql -U postgres -d immich -c "SELECT count(*) FROM asset;"
