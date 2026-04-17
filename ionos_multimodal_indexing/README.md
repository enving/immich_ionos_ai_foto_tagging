# Ionos Multimodal Indexer für Immich

Dieses Projekt erweitert Immich um eine leistungsstarke, KI-gestützte Bildanalyse mittels der **IONOS Multimodal API** (basierend auf Mistral). Es analysiert importierte Bilder und speichert detaillierte Metadaten (Objekte, Personen, Szenen, Farben) direkt in der Immich-Datenbank, wodurch diese durchsuchbar werden.

## Funktionen

- **Automatische Indexierung:** Scannet Bilder im Import-Verzeichnis (`library/imported`).
- **Multimodale Analyse:** Nutzt modernste KI, um Bildinhalte zu verstehen.
- **Datenbank-Integration:** Speichert Ergebnisse direkt in PostgreSQL (`asset_metadata` und `asset_exif`).
- **Idempotenz:** Prüft vor jeder API-Anfrage, ob das Bild bereits analysiert wurde (spart Kosten und Zeit).
- **Automatisierung:** Kann per Cronjob regelmäßig laufen.

## Einrichtung

### 1. Voraussetzungen

- Eine laufende Immich-Instanz.
- Ein IONOS Cloud Account mit API-Key für die AI Model Hub.
- Python 3 installiert.

### 2. Konfiguration

Die Konfiguration erfolgt über die `.env` Datei im Hauptverzeichnis (`../.env`). Folgende Variablen müssen gesetzt sein:

```bash
IONOS_API_KEY=dein_api_key
IONOS_API_URL=https://openai.inference.de-txl.ionos.com/v1
IONOS_MODEL=mistralai/Mistral-Small-24B-Instruct
DB_USERNAME=postgres
DB_PASSWORD=dein_db_passwort
DB_DATABASE_NAME=immich
```

### 3. Installation

Abhängigkeiten installieren:

```bash
pip3 install requests psycopg2-binary python-dotenv Pillow
```

## Nutzung

### Manuelle Ausführung

Um den Indexierungsvorgang einmalig manuell zu starten:

```bash
cd ionos_multimodal_indexing
python3 index_images.py
```

Das Skript zeigt einen Fortschrittsbalken und Statistiken an.

### Automatische Ausführung (Cronjob)

Für eine regelmäßige Überprüfung (z.B. stündlich) gibt es ein Wrapper-Skript `run_indexing.sh`.

Einrichtung via `crontab -e`:

```bash
# Läuft jede volle Stunde
0 * * * * /Users/macenving/immich-server/ionos_multimodal_indexing/run_indexing.sh
```

Logs werden in `ionos_multimodal_indexing/logs/cron_run.log` gespeichert.

## Funktionsweise

1.  **Suche:** Das Skript sucht rekursiv nach Bildern in `library/imported`.
2.  **Filterung:** Es prüft anhand des Datei-Hashs (Checksum) in der Immich-Datenbank, ob für dieses Asset bereits ein Eintrag in `asset_metadata` mit dem Key `ionos_analysis` existiert.
3.  **Analyse:** Falls neu, wird das Bild zur IONOS API gesendet.
4.  **Speicherung:**
    -   Volle JSON-Analyse -> `asset_metadata` (für Details).
    -   Beschreibung & Tags -> `asset_exif` (für die Immich-Suche).

## Troubleshooting

-   **Fehler 401 (Unauthorized):** API-Key in `.env` prüfen.
-   **Datenbank-Verbindung fehlgeschlagen:** Sicherstellen, dass der Postgres-Container Port 5432 freigibt (siehe `docker-compose.yml`).