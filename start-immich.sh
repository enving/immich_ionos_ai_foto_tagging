#!/bin/bash

# Immich Server Starter Script for macOS
# Simple script to start Immich Docker services

echo "🚀 Immich Server Starter"
echo "========================"
echo ""
echo "⏳ Starte Immich Services..."

cd "$(dirname "$0")"
docker compose up -d

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Immich erfolgreich gestartet!"
    echo ""
    echo "📍 Web-UI: http://localhost"
    echo "📍 API: http://localhost:2283"
    echo "📁 Daten: $(pwd)/library"
    echo ""
    echo "⏳ Warten auf vollständigen Start (ca. 30 Sekunden)..."
    sleep 30
    docker compose ps
else
    echo "❌ Fehler beim Starten der Container!"
    exit 1
fi
