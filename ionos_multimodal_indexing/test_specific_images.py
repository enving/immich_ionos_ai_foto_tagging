#!/usr/bin/env python3
"""
Testskript für spezifische Bilder aus dem Thanksgiving-Verzeichnis.

Dieses Skript verarbeitet nur eine kleine Auswahl von Bildern zur Überprüfung der IONOS-API-Funktionalität.
"""

import os
import sys
from pathlib import Path
from index_images import send_image_to_ionos_api, save_results_to_database, get_asset_id_from_database

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_specific_images():
    """Testet die Verarbeitung von spezifischen Bildern aus dem Thanksgiving-Verzeichnis."""
    try:
        # Spezifische Bilder, die getestet werden sollen
        test_images = [
            "../library/imported/Thanksgiving und Help Wartenburg Geburtstag Jack u/_1040720.JPG",
            "../library/imported/Thanksgiving und Help Wartenburg Geburtstag Jack u/_1040683.JPG",
            "../library/imported/Thanksgiving und Help Wartenburg Geburtstag Jack u/_1040697.JPG",
            "../library/imported/Thanksgiving und Help Wartenburg Geburtstag Jack u/_1040668.JPG"
        ]

        print("Starte Test mit spezifischen Bildern aus dem Thanksgiving-Verzeichnis...")
        print(f"Testbilder: {len(test_images)}")

        successful_count = 0
        failed_count = 0

        for i, image_path in enumerate(test_images, 1):
            print(f"\nVerarbeite Testbild {i}/{len(test_images)}: {image_path}")

            # Überprüfe, ob die Datei existiert
            if not os.path.exists(image_path):
                print(f"  Fehler: Datei nicht gefunden - {image_path}")
                failed_count += 1
                continue

            # Sende das Bild an die IONOS-API
            print(f"  Sende an IONOS-API...")
            api_response = send_image_to_ionos_api(image_path)

            if not api_response:
                print(f"  Fehler: Keine Antwort von der API für {image_path}")
                failed_count += 1
                continue

            print(f"  Erfolg: API-Antwort erhalten")

            # Zeige einen Teil der API-Antwort an
            description = api_response.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"  Beschreibung (Auszug): {description[:100]}...")

            # Speichere die Ergebnisse in der Datenbank
            if save_results_to_database(image_path, api_response):
                print(f"  Erfolg: Ergebnisse in Datenbank gespeichert")
                successful_count += 1
            else:
                print(f"  Fehler: Datenbankspeicherung fehlgeschlagen")
                failed_count += 1

        print(f"\nTest abgeschlossen!")
        print(f"Erfolgreich: {successful_count}/{len(test_images)}")
        print(f"Fehlgeschlagen: {failed_count}/{len(test_images)}")

        return successful_count > 0

    except Exception as e:
        print(f"Fehler beim Testen der Bilder: {e}")
        return False

if __name__ == "__main__":
    success = test_specific_images()
    sys.exit(0 if success else 1)