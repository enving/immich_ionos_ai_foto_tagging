


#!/usr/bin/env python3
"""
Skript zur Indizierung von Bildern mit dem IONOS-Multimodal-Modell.

Dieses Skript liest alle Bilder aus dem library/imported-Verzeichnis,
sendet sie an die IONOS-API und speichert die Ergebnisse in der Immich-Datenbank.
"""

import os
import requests
import json
import base64
import time
from dotenv import load_dotenv
from pathlib import Path
import psycopg2
from psycopg2 import sql
from PIL import Image
import io
import hashlib
from progress_tracker import ProgressTracker


# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# IONOS-API-Konfiguration
IONOS_API_KEY = os.getenv("IONOS_API_KEY")
IONOS_API_URL = os.getenv("IONOS_API_URL")
IONOS_MODEL = os.getenv("IONOS_MODEL")

# Immich-Datenbankkonfiguration
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DATABASE_NAME = os.getenv("DB_DATABASE_NAME")
DB_DATA_LOCATION = os.getenv("DB_DATA_LOCATION")

# Verzeichnis mit den Bildern (unabhängig von UPLOAD_LOCATION, da Immich System-Daten separat liegen)
IMAGE_DIR = os.getenv("IMAGE_DIR", "/Users/macenving/immich-server/library/imported")

# Konfiguration für die Batch-Verarbeitung
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))  # Sekunden zwischen Batches
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

def get_file_checksum(file_path):
    """Berechnet den SHA1-Hash einer Datei (wie von Immich verwendet)."""
    sha1 = hashlib.sha1()
    try:
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(8192)
                if not data:
                    break
                sha1.update(data)
        return sha1.hexdigest()
    except Exception as e:
        print(f"Fehler beim Berechnen des Checksums für {file_path}: {e}")
        return None

def get_asset_id_from_database(image_path):
    """Finde die Asset-ID für ein Bild in der Immich-Datenbank mittels Dateipfad."""
    try:
        conn = get_db_connection()
        if not conn:
            return None

        cursor = conn.cursor()

        # Konvertiere Host-Pfad zu Container-Pfad
        # Host: /Users/macenving/immich-server/library/imported/... -> Container: /imported/...
        host_prefix = "/Users/macenving/immich-server/library/imported/"
        container_prefix = "/imported/"
        
        str_path = str(image_path)
        if str_path.startswith(host_prefix):
            container_path = container_prefix + str_path[len(host_prefix):]
        else:
            # Fallback: versuche den Pfad direkt
            container_path = str_path

        query = sql.SQL("""
            SELECT id FROM asset
            WHERE "originalPath" = %s
            LIMIT 1
        """)

        cursor.execute(query, (container_path,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return result[0] if result else None
    except Exception as e:
        print(f"Fehler beim Abrufen der Asset-ID für {image_path}: {e}")
        return None

def get_db_connection():
    """Stellt eine Verbindung zur Immich-Datenbank her."""
    try:
        conn = psycopg2.connect(
            dbname=DB_DATABASE_NAME,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"Fehler bei der Datenbankverbindung: {e}")
        return None

def resize_image_for_api(image_path, max_size=(1024, 1024), quality=85):
    """Verkleinert ein Bild für die API und gibt es als Bytes zurück."""
    try:
        with Image.open(image_path) as img:
            # Konvertiere zu RGB, falls notwendig (z.B. für RGBA-Bilder)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            # Skaliere das Bild, um die Größe zu reduzieren
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Speichere in einem Bytes-Buffer mit reduzierter Qualität
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            return buffer.getvalue()
    except Exception as e:
        print(f"Fehler beim Verkleinern des Bildes {image_path}: {e}")
        return None

def extract_exif_metadata(image_path):
    """Extrahiert EXIF-Metadaten aus einem Bild, einschließlich Geolocation, Datum, Kamera, etc."""
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif() or {}
            metadata = {}

            # EXIF-Tag-IDs und ihre Bedeutungen
            EXIF_TAGS = {
                36867: 'date_time',  # Datum und Uhrzeit der Aufnahme
                36868: 'date_time_original',  # Datum und Uhrzeit der Originalaufnahme
                36869: 'date_time_digitized',  # Datum und Uhrzeit der Digitalisierung
                34853: 'gps_info',  # GPS-Informationen
                271: 'make',  # Kamerahersteller
                272: 'model',  # Kameramodell
                33434: 'exposure_time',  # Belichtungszeit
                33437: 'f_number',  # Blende
                34855: 'iso',  # ISO-Empfindlichkeit
                37386: 'focal_length',  # Brennweite
                41986: 'exposure_mode',  # Belichtungsmodus
                41987: 'white_balance',  # Weißabgleich
                41988: 'digital_zoom_ratio',  # Digitaler Zoom
                41989: 'focal_length_35mm',  # Brennweite (35mm-Äquivalent)
                41990: 'scene_capture_type',  # Szenenaufnahmetyp
            }

            # Extrahiere alle verfügbaren Metadaten
            for tag_id, value in exif_data.items():
                tag_name = EXIF_TAGS.get(tag_id, str(tag_id))
                metadata[tag_name] = str(value)

            # Spezielle Verarbeitung für GPS-Informationen
            gps_info = exif_data.get(34853)
            if gps_info:
                try:
                    # Extrahiere GPS-Koordinaten
                    lat = gps_info.get(2)  # GPSLatitude
                    lat_ref = gps_info.get(1)  # GPSLatitudeRef
                    lon = gps_info.get(4)  # GPSLongitude
                    lon_ref = gps_info.get(3)  # GPSLongitudeRef

                    if lat and lon and lat_ref and lon_ref:
                        # Konvertiere in Dezimalgrad
                        def convert_to_degrees(value):
                            d = float(value[0][0]) / float(value[0][1])
                            m = float(value[1][0]) / float(value[1][1])
                            s = float(value[2][0]) / float(value[2][1])
                            return d + (m / 60.0) + (s / 3600.0)

                        lat_deg = convert_to_degrees(lat)
                        lon_deg = convert_to_degrees(lon)

                        # Berücksichtige Hemisphäre
                        if lat_ref == 'S':
                            lat_deg = -lat_deg
                        if lon_ref == 'W':
                            lon_deg = -lon_deg

                        metadata['gps_processed'] = {
                            'latitude': lat_deg,
                            'longitude': lon_deg,
                            'source': 'exif'
                        }
                except Exception as e:
                    print(f"Fehler beim Parsen der GPS-Daten für {image_path}: {e}")

            # Extrahiere Datumsinformationen und konvertiere sie
            date_fields = ['date_time', 'date_time_original', 'date_time_digitized']
            for field in date_fields:
                if field in metadata:
                    try:
                        # Versuche, das Datum zu parsen (Format: "YYYY:MM:DD HH:MM:SS")
                        date_str = metadata[field]
                        if ':' in date_str:
                            parts = date_str.split()
                            if len(parts) >= 2:
                                date_part = parts[0].replace(':', '-')
                                time_part = parts[1]
                                metadata[f'{field}_formatted'] = f"{date_part} {time_part}"
                                metadata[f'{field}_date'] = date_part
                                metadata[f'{field}_time'] = time_part
                                # Extrahiere Jahr
                                year = date_part.split('-')[0]
                                metadata['year'] = year
                    except Exception as e:
                        print(f"Fehler beim Parsen des Datums {field} für {image_path}: {e}")

            return metadata
    except Exception as e:
        print(f"Fehler beim Extrahieren der EXIF-Daten für {image_path}: {e}")
        return {}

def encode_image_to_base64(image_path):
    """Kodiert ein Bild in Base64, verkleinert es bei Bedarf für die API."""
    try:
        # Versuche zuerst, das Bild zu verkleinern
        resized_image_bytes = resize_image_for_api(image_path)
        if resized_image_bytes:
            return base64.b64encode(resized_image_bytes).decode("utf-8")

        # Falls die Verkleinerung fehlschlägt, verwende das Originalbild
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Fehler beim Kodieren des Bildes {image_path}: {e}")
        return None

def send_image_to_ionos_api(image_path, retry_count=0):
    """Sendet ein Bild an die IONOS-API und gibt die Antwort zurück."""
    try:
        base64_image = encode_image_to_base64(image_path)
        if not base64_image:
            return None

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {IONOS_API_KEY}"
        }

        payload = {
            "model": IONOS_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analysiere dieses Bild und gib strukturierte Metadaten im JSON-Format zurück. ALLE Texte müssen auf Deutsch sein! Das JSON sollte enthalten: objects (Liste der erkennbaren Objekte auf Deutsch), people (detaillierte Personenbeschreibung mit Anzahl, Geschlecht, Alter, Position, Aktivitäten auf Deutsch), faces (Gesichtsbeschreibungen mit Eigenschaften wie Geschlecht, Alter, Emotionen auf Deutsch), scene (Szene/Beschreibung auf Deutsch), location (vermutlicher Ort auf Deutsch), colors (dominante Farben auf Deutsch), tags (relevante Stichworte auf Deutsch), description (kurze Zusammenfassung auf Deutsch). Antworte nur mit dem JSON-Objekt, ohne zusätzliche Erklärungen. WICHTIG: Alle Texte müssen auf Deutsch sein!"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1500
        }

        response = requests.post(
            f"{IONOS_API_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            return response.json()
        else:
            if retry_count < MAX_RETRIES:
                print(f"Fehler bei der API-Anfrage für {image_path}: {response.status_code} - {response.text}")
                print(f"Neuer Versuch {retry_count + 1}/{MAX_RETRIES}...")
                time.sleep(2 ** retry_count)  # Exponential backoff
                return send_image_to_ionos_api(image_path, retry_count + 1)
            else:
                print(f"Maximale Anzahl von Versuchen erreicht für {image_path}")
                return None
    except Exception as e:
        if retry_count < MAX_RETRIES:
            print(f"Fehler bei der API-Anfrage für {image_path}: {e}")
            print(f"Neuer Versuch {retry_count + 1}/{MAX_RETRIES}...")
            time.sleep(2 ** retry_count)  # Exponential backoff
            return send_image_to_ionos_api(image_path, retry_count + 1)
        else:
            print(f"Maximale Anzahl von Versuchen erreicht für {image_path}: {e}")
            return None


def save_results_to_database(image_path, api_response):
    """Speichert die Ergebnisse der API-Antwort in der Immich-Datenbank."""
    try:
        # Extrahiere den Textinhalt der API-Antwort
        content = api_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Versuche, den Inhalt als JSON zu parsen
        structured_data = None
        description_text = content
        tags = []
        
        try:
            # Manchmal schickt die API Markdown-Blöcke (z.B. ```json ... ```)
            if "```json" in content:
                json_part = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_part = content.split("```")[1].split("```")[0].strip()
            else:
                json_part = content.strip()
                
            structured_data = json.loads(json_part)
            description_text = structured_data.get("description", content)
            tags = structured_data.get("tags", [])
            
            # Stelle sicher, dass tags eine Liste von Strings ist
            if isinstance(tags, list):
                tags = [str(t) for t in tags if t]
            else:
                tags = []
                
        except Exception as e:
            print(f"   ⚠️  JSON-Parse-Warnung für {os.path.basename(str(image_path))}: {e}")
            # Fallback: speichere den Rohtext als structured_data
            structured_data = {"raw_response": content}

        # Finde die Asset-ID für das Bild in der Datenbank (mittels Checksum)
        asset_id = get_asset_id_from_database(image_path)
        if not asset_id:
            print(f"   ⚠️  Keine Asset-ID für {os.path.basename(str(image_path))} (nicht in Immich?)")
            return False

        conn = get_db_connection()
        if not conn:
            return False

        cursor = conn.cursor()

        # 1. Speichere die volle strukturierte Antwort in asset_metadata (JSONB)
        #    Hier landen ALLE Daten: objects, people, faces, scene, location, colors, tags, description
        if structured_data:
            metadata_query = sql.SQL("""
                INSERT INTO asset_metadata ("assetId", key, value)
                VALUES (%s, %s, %s::jsonb)
                ON CONFLICT ("assetId", key)
                DO UPDATE SET
                    value = EXCLUDED.value
            """)
            cursor.execute(metadata_query, (
                asset_id,
                'ionos_analysis',
                json.dumps(structured_data, ensure_ascii=False)
            ))

        # 2. Speichere description + tags in asset_exif (für Immich-Suche)
        exif_query = sql.SQL("""
            UPDATE asset_exif
            SET description = %s,
                tags = %s
            WHERE "assetId" = %s
        """)
        cursor.execute(exif_query, (description_text, tags, asset_id))

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ DB-Fehler für {os.path.basename(str(image_path))}: {e}")
        return False


def is_asset_indexed(asset_id):
    """Prüft, ob für ein Asset bereits eine IONOS-Analyse in der Datenbank vorliegt."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        query = sql.SQL("SELECT 1 FROM asset_metadata WHERE \"assetId\" = %s AND key = 'ionos_analysis'")
        cursor.execute(query, (asset_id,))
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        print(f"Fehler beim Prüfen des Index-Status für {asset_id}: {e}")
        return False

def process_images():
    """Verarbeitet alle Bilder im library/imported-Verzeichnis mit Fortschrittsverfolgung."""
    try:
        image_dir = Path(IMAGE_DIR)
        print(f"Suche nach Bildern in: {image_dir}")
        if not image_dir.exists():
            print(f"Das Verzeichnis {IMAGE_DIR} existiert nicht.")
            return

        image_files = list(image_dir.rglob("*.[jJ][pP][gG]")) + list(image_dir.rglob("*.[pP][nN][gG]"))

        # Filtere bereits verarbeitete Bilder (falls Fortschritt vorhanden)
        tracker = ProgressTracker()
        total_images = len(image_files)
        print(f"Gefundene Bilder: {total_images}")

        # Starte die Verarbeitung mit Fortschrittsverfolgung
        tracker.start_processing(total_images)


        # Batch-Verarbeitung
        for i in range(0, len(image_files), BATCH_SIZE):
            batch = image_files[i:i + BATCH_SIZE]
            print(f"\n📊 Verarbeite Batch {i//BATCH_SIZE + 1} mit {len(batch)} Bildern...")
            print(f"   Fortschritt: {tracker.get_progress()}% ({tracker.stats['processed_images']}/{total_images})")

            for j, image_path in enumerate(batch, 1):
                # Überspringe bereits verarbeitete Bilder
                if tracker.is_processed(str(image_path)):
                    print(f"   ⏭️  Bild {j}/{len(batch)}: {os.path.basename(image_path)} - bereits verarbeitet")
                    continue

                print(f"   🔄 Bild {j}/{len(batch)}: {os.path.basename(image_path)}")

                # WICHTIG: Prüfen, ob Asset-ID existiert (bevor wir die teure API rufen)
                asset_id = get_asset_id_from_database(image_path)
                if not asset_id:
                     print(f"   ⏭️  Bild {j}/{len(batch)}: {os.path.basename(image_path)} - noch nicht in Immich (warte auf Import)")
                     continue

                # Sende das Bild an die IONOS-API
                api_response = send_image_to_ionos_api(image_path)
                if not api_response:
                    error_msg = f"Keine Antwort von der API für {image_path}"
                    print(f"   ❌ {error_msg}")
                    tracker.mark_failed(str(image_path), error_msg)
                    continue

                # Extrahiere Token-Informationen für Kostenberechnung
                tokens_used = api_response.get('usage', {}).get('total_tokens', 0)

                # Speichere die Ergebnisse in der Datenbank
                if save_results_to_database(image_path, api_response):
                    print(f"   ✅ Ergebnisse für {image_path} erfolgreich gespeichert.")
                    tracker.mark_successful(str(image_path), tokens_used)
                else:
                    error_msg = f"Fehler beim Speichern der Ergebnisse für {image_path}"
                    print(f"   ❌ {error_msg}")
                    tracker.mark_failed(str(image_path), error_msg)

            # Rate Limiting zwischen Batches
            if i + BATCH_SIZE < len(image_files):
                print(f"   ⏳ Warte {RATE_LIMIT_DELAY} Sekunden vor dem nächsten Batch...")
                time.sleep(RATE_LIMIT_DELAY)

        # Beende die Verarbeitung und zeige Zusammenfassung
        tracker.end_processing()
        tracker.estimate_cost()
        tracker.print_summary()

        print(f"\n🎉 Alle Bilder verarbeitet!")
        print(f"   📊 Fortschritt: {tracker.get_progress()}%")
        print(f"   💰 Geschätzte Gesamtkosten: {tracker.stats['estimated_cost']}€")
        print(f"   🔢 Gesamt-Tokens: {tracker.stats['total_tokens']:,}")

    except Exception as e:
        print(f"Fehler bei der Verarbeitung der Bilder: {e}")

if __name__ == "__main__":
    print("Starte die Indizierung der Bilder mit dem IONOS-Multimodal-Modell...")
    process_images()
    print("Indizierung abgeschlossen.")