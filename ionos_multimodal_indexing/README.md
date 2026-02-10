# IONOS Multimodal Image Indexing

Dieses Skript ermöglicht die Indizierung von Bildern mit dem IONOS-Multimodal-Modell (mistral-small-24b) und speichert die Ergebnisse in der Immich-Datenbank.

## Funktionen

- **Multimodale Bildanalyse**: Nutzt das IONOS mistral-small-24b Modell für detaillierte Bildbeschreibungen und Tagging
- **Batch-Verarbeitung**: Verarbeitet Bilder in konfigurierbaren Batches mit Rate Limiting
- **Fehlerbehandlung**: Automatische Wiederholung bei API-Fehlern mit exponentiellem Backoff
- **Datenbankintegration**: Speichert Ergebnisse direkt in der Immich-Datenbank

## Voraussetzungen

- Python 3.8+
- Installierte Abhängigkeiten: `requests`, `python-dotenv`, `psycopg2-binary`, `Pillow`
- Konfigurierte `.env`-Datei mit IONOS-API-Zugangsdaten
- Laufende Immich-Instanz mit PostgreSQL-Datenbank

## Installation

```bash
pip install requests python-dotenv psycopg2-binary Pillow
```

## Konfiguration

Erstelle oder bearbeite die `.env`-Datei mit folgenden Variablen:

```env
# IONOS API Konfiguration
IONOS_API_KEY=dein_api_key
IONOS_API_URL=https://openai.inference.de-txl.ionos.com/v1
IONOS_MODEL=mistralai/Mistral-Small-24B-Instruct

# Immich Datenbank Konfiguration
DB_USERNAME=postgres
DB_PASSWORD=dein_db_passwort
DB_DATABASE_NAME=immich

# Verarbeitungsoptionen (optional)
UPLOAD_LOCATION=./library/imported
BATCH_SIZE=10
RATE_LIMIT_DELAY=1.0
MAX_RETRIES=3
```

## Verwendung

### Alle Bilder indizieren

```bash
python index_images.py
```

### Einzelnes Bild testen

```bash
python test_ionos_api.py
```

## Datenbankstruktur

Das Skript speichert die Ergebnisse in der `asset_metadata`-Tabelle:

- `asset_id`: Verweis auf das Asset in der Immich-Datenbank
- `description`: Detaillierte Bildbeschreibung vom IONOS-Modell
- `tags`: Extrahiere Tags aus der Beschreibung

## Fehlerbehebung

- **Datenbankverbindung fehlgeschlagen**: Überprüfe die Datenbankkonfiguration in `.env`
- **API-Fehler**: Überprüfe den IONOS_API_KEY und die Netzwerkverbindung
- **Bilder nicht gefunden**: Überprüfe den `UPLOAD_LOCATION`-Pfad

## Sicherheitshinweise

- Bewahre den IONOS_API_KEY sicher auf und teile ihn nicht
- Das Skript verwendet HTTPS für die API-Kommunikation
- Die Datenbankverbindung ist lokal auf Port 5432 konfiguriert