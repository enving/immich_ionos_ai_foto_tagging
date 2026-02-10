#!/usr/bin/env python3
"""
Testskript für die IONOS-API.

Dieses Skript sendet ein Testbild an die IONOS-API und zeigt die Ergebnisse an.
"""

import os
import requests
import json
import base64
from dotenv import load_dotenv
from pathlib import Path

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# IONOS-API-Konfiguration
IONOS_API_KEY = os.getenv("IONOS_API_KEY")
IONOS_API_URL = os.getenv("IONOS_API_URL")
IONOS_MODEL = os.getenv("IONOS_MODEL")

def encode_image_to_base64(image_path):
    """Kodiert ein Bild in Base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Fehler beim Kodieren des Bildes {image_path}: {e}")
        return None

def send_image_to_ionos_api(image_path):
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
                            "text": "Beschreibe das Bild detailliert und gib relevante Tags an."
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
            "max_tokens": 1000
        }

        print(f"Sende Anfrage an {IONOS_API_URL}/chat/completions...")
        print(f"Headers: {headers}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(
            f"{IONOS_API_URL}/chat/completions",
            headers=headers,
            json=payload
        )

        print(f"Antwort-Statuscode: {response.status_code}")
        print(f"Antwort-Text: {response.text}")

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Fehler bei der API-Anfrage für {image_path}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Fehler bei der API-Anfrage für {image_path}: {e}")
        return None

if __name__ == "__main__":
    print("Starte den Test der IONOS-API...")

    # Verwende ein Testbild aus dem library/imported-Verzeichnis
    test_image_path = "library/imported/Familie NRW/_1040432-edited.JPG"

    if not os.path.exists(test_image_path):
        print(f"Das Testbild {test_image_path} existiert nicht.")
        exit(1)

    print(f"Testbild: {test_image_path}")

    # Sende das Testbild an die IONOS-API
    api_response = send_image_to_ionos_api(test_image_path)

    if api_response:
        print("Erfolgreiche Antwort von der IONOS-API:")
        print(json.dumps(api_response, indent=2))
    else:
        print("Keine erfolgreiche Antwort von der IONOS-API.")