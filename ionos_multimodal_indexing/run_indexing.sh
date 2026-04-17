#!/bin/bash
# Wrapper-Script für den Cronjob
# Wechselt ins Verzeichnis, lädt Umgebungsvariablen und startet den Indexer

# Absolute Pfade verwenden
cd /Users/macenving/immich-server/ionos_multimodal_indexing || exit

# Umgebungsvariablen laden (falls nötig, da Cron eine eingeschränkte Umgebung hat)
if [ -f ../.env ]; then
    export $(grep -v '^#' ../.env | xargs)
fi

# Locking-Mechanismus (verhindert doppelte Ausführung)
LOCKFILE="/tmp/immich_indexing.lock"

if [ -f "$LOCKFILE" ]; then
    # Prüfe, ob der Prozess noch läuft
    PID=$(cat "$LOCKFILE")
    if ps -p $PID > /dev/null; then
        echo "Skript läuft bereits (PID: $PID). Beende..." >> ./logs/cron_run.log
        exit 0
    else
        echo "Lockfile existiert, aber Prozess läuft nicht mehr. Entferne Lockfile..." >> ./logs/cron_run.log
        rm -f "$LOCKFILE"
    fi
fi

# Erstelle Lockfile
echo $$ > "$LOCKFILE"

# Trap zum Entfernen des Lockfiles bei Beendigung
trap 'rm -f "$LOCKFILE"' EXIT

# Logging starten
echo "Strict start: $(date)" >> ./logs/cron_run.log

# Scan anstoßen (damit neue Dateien gefunden werden)
/usr/bin/python3 trigger_immich_scan.py >> ./logs/cron_run.log 2>&1

# Indexer ausführen
/usr/bin/python3 index_images.py >> ./logs/cron_run.log 2>&1

echo "Strict end: $(date)" >> ./logs/cron_run.log
