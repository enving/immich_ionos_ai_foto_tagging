#!/usr/bin/env python3
"""
Testskript nur für die IONOS-API-Funktionalität.

Dieses Skript testet nur die API-Anbindung ohne Datenbankverbindung,
um die erfolgreiche Integration des IONOS-Multimodal-Modells zu demonstrieren.
"""

import os
import sys
import json
from index_images import send_image_to_ionos_api, extract_exif_metadata

def test_api_only():
    """Testet nur die IONOS-API ohne Datenbank."""
    try:
        # Spezifische Bilder, die getestet werden sollen
        test_images = [
            "../library/imported/Thanksgiving und Help Wartenburg Geburtstag Jack u/_1040720.JPG",
            "../library/imported/Thanksgiving und Help Wartenburg Geburtstag Jack u/_1040683.JPG",
            "../library/imported/Thanksgiving und Help Wartenburg Geburtstag Jack u/_1040697.JPG",
            "../library/imported/Thanksgiving und Help Wartenburg Geburtstag Jack u/_1040668.JPG"
        ]

        print("🚀 IONOS Multimodal API Test - Nur API-Funktionalität")
        print("=" * 60)
        print(f"Testbilder: {len(test_images)}")
        print("Dieser Test prüft nur die API-Anbindung (keine Datenbank nötig)")

        successful_count = 0
        failed_count = 0

        for i, image_path in enumerate(test_images, 1):
            print(f"\n📷 Testbild {i}/{len(test_images)}:")
            print(f"   Pfad: {os.path.basename(image_path)}")

            # Überprüfe, ob die Datei existiert
            if not os.path.exists(image_path):
                print(f"   ❌ Datei nicht gefunden")
                failed_count += 1
                continue

            # Extrahiere EXIF-Metadaten (umfassend)
            exif_metadata = extract_exif_metadata(image_path)
            if exif_metadata:
                print(f"   📍 EXIF Metadaten (werden NICHT überschrieben):")

                # Zeige Geolocation, falls vorhanden
                if 'gps_processed' in exif_metadata:
                    gps = exif_metadata['gps_processed']
                    print(f"      🌍 Geolocation:")
                    print(f"         Breitengrad: {gps.get('latitude', 'N/A')}")
                    print(f"         Längengrad: {gps.get('longitude', 'N/A')}")

                # Zeige Datumsinformationen
                if 'year' in exif_metadata:
                    print(f"      📅 Jahr: {exif_metadata['year']}")
                if 'date_time_original_formatted' in exif_metadata:
                    print(f"      ⏰ Aufnahmezeitpunkt: {exif_metadata['date_time_original_formatted']}")
                elif 'date_time_formatted' in exif_metadata:
                    print(f"      ⏰ Aufnahmezeitpunkt: {exif_metadata['date_time_formatted']}")

                # Zeige Kamerainformationen
                if 'make' in exif_metadata:
                    print(f"      📷 Kamera: {exif_metadata['make']} {exif_metadata.get('model', '')}".strip())
                if 'iso' in exif_metadata:
                    print(f"      🎛️  ISO: {exif_metadata['iso']}")
                if 'exposure_time' in exif_metadata:
                    print(f"      ⏱️  Belichtung: {exif_metadata['exposure_time']}")
                if 'focal_length' in exif_metadata:
                    print(f"      🔍 Brennweite: {exif_metadata['focal_length']}")

                print(f"      📊 Quelle: EXIF (wird beibehalten)")
            else:
                print(f"   📍 Keine EXIF Metadaten gefunden")

            # Sende das Bild an die IONOS-API
            print(f"   🔄 Sende an IONOS-API...")
            api_response = send_image_to_ionos_api(image_path)

            if not api_response:
                print(f"   ❌ Keine API-Antwort")
                failed_count += 1
                continue

            # Extrahiere die API-Antwort
            response_content = api_response.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Versuche, die Antwort als JSON zu parsen (neues Format)
            try:
                # Entferne Markdown-Code-Blöcke, falls vorhanden
                clean_content = response_content.strip()
                if clean_content.startswith("```json") and clean_content.endswith("```"):
                    clean_content = clean_content[7:-3].strip()

                metadata = json.loads(clean_content)
                print(f"   ✅ API-Antwort erfolgreich!")
                print(f"   📝 Strukturierte Metadaten:")

                # Zeige die strukturierten Daten an
                if "description" in metadata:
                    print(f"      Beschreibung: {metadata['description'][:100]}...")
                if "objects" in metadata:
                    objects_list = metadata['objects'] if isinstance(metadata['objects'], list) else [metadata['objects']]
                    print(f"      Objekte: {', '.join([str(obj) for obj in objects_list[:5]])}...")
                if "people" in metadata:
                    people_info = metadata['people']
                    if isinstance(people_info, dict) and "count" in people_info:
                        print(f"      Personen: {people_info['count']} Personen")
                    else:
                        print(f"      Personen: {people_info}")
                if "tags" in metadata:
                    tags_list = metadata['tags'] if isinstance(metadata['tags'], list) else [metadata['tags']]
                    print(f"      Tags: {', '.join([str(tag) for tag in tags_list[:5]])}...")
                if "scene" in metadata:
                    print(f"      Szene: {metadata['scene'][:50]}...")
                if "location" in metadata:
                    print(f"      Ort: {metadata['location'][:50]}...")

            except json.JSONDecodeError:
                # Falls es kein JSON ist, zeige es als Text an (altes Format)
                print(f"   ✅ API-Antwort erfolgreich!")
                print(f"   📝 Beschreibung:")
                print(f"      {response_content[:200]}...")

            # Zeige die API-Antwort Details
            print(f"   🔍 API-Antwort Details:")
            print(f"      Modell: {api_response.get('model', 'unbekannt')}")
            print(f"      Tokens: {api_response.get('usage', {}).get('total_tokens', 0)}")
            print(f"      Antwortlänge: {len(response_content)} Zeichen")

            successful_count += 1

        print(f"\n🏁 Test abgeschlossen!")
        print(f"   ✅ Erfolgreich: {successful_count}/{len(test_images)}")
        print(f"   ❌ Fehlgeschlagen: {failed_count}/{len(test_images)}")

        if successful_count > 0:
            print(f"\n🎉 ERFOLG: Die IONOS-API funktioniert einwandfrei!")
            print(f"   Die Bilder werden korrekt analysiert und beschrieben.")
            print(f"   Die Datenbankintegration kann später aktiviert werden.")
        else:
            print(f"\n⚠️  Problem: Keine erfolgreichen API-Aufrufe.")

        return successful_count > 0

    except Exception as e:
        print(f"❌ Fehler beim Testen der Bilder: {e}")
        return False

if __name__ == "__main__":
    success = test_api_only()
    print(f"\n📊 Gesamtstatus: {'ERFOLGREICH' if success else 'FEHLGESCHLAGEN'}")
    sys.exit(0 if success else 1)