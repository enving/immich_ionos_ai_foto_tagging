#!/usr/bin/env python3
"""
Fortschrittsverfolgung für die IONOS-Bildindexierung.

Dieses Skript verwaltet den Fortschritt der Bildverarbeitung,
speichert erfolgreich verarbeitete Bilder und ermöglicht das Fortsetzen.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

class ProgressTracker:
    """Verwaltet den Fortschritt der Bildverarbeitung."""

    def __init__(self, log_dir="logs"):
        """Initialisiert den Fortschritts-Tracker."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.progress_file = self.log_dir / "processing_progress.json"
        self.error_file = self.log_dir / "processing_errors.json"
        self.stats_file = self.log_dir / "processing_stats.json"

        # Lade bestehenden Fortschritt
        self.processed_images = self._load_progress()
        self.error_images = self._load_errors()
        self.stats = self._load_stats()

    def _load_progress(self):
        """Lädt die Liste der bereits verarbeiteten Bilder."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except Exception as e:
                print(f"Fehler beim Laden des Fortschritts: {e}")
        return set()

    def _load_errors(self):
        """Lädt die Liste der Bilder mit Fehlern."""
        if self.error_file.exists():
            try:
                with open(self.error_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Fehler beim Laden der Fehlerliste: {e}")
        return []

    def _load_stats(self):
        """Lädt die Statistiken."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Fehler beim Laden der Statistiken: {e}")
        return {
            'total_images': 0,
            'processed_images': 0,
            'successful_images': 0,
            'failed_images': 0,
            'total_tokens': 0,
            'start_time': None,
            'end_time': None,
            'estimated_cost': 0.0
        }

    def save_progress(self):
        """Speichert den aktuellen Fortschritt."""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.processed_images), f, indent=2, ensure_ascii=False)
            print(f"Fortschritt gespeichert: {len(self.processed_images)} Bilder")
        except Exception as e:
            print(f"Fehler beim Speichern des Fortschritts: {e}")

    def save_errors(self):
        """Speichert die Fehlerliste."""
        try:
            with open(self.error_file, 'w', encoding='utf-8') as f:
                json.dump(self.error_images, f, indent=2, ensure_ascii=False)
            print(f"Fehlerliste gespeichert: {len(self.error_images)} Bilder")
        except Exception as e:
            print(f"Fehler beim Speichern der Fehlerliste: {e}")

    def save_stats(self):
        """Speichert die Statistiken."""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
            print(f"Statistiken gespeichert")
        except Exception as e:
            print(f"Fehler beim Speichern der Statistiken: {e}")

    def mark_successful(self, image_path, tokens_used=0):
        """Markiert ein Bild als erfolgreich verarbeitet."""
        self.processed_images.add(str(image_path))
        self.stats['processed_images'] += 1
        self.stats['successful_images'] += 1
        self.stats['total_tokens'] += tokens_used

        # Speichere regelmäßig
        if self.stats['processed_images'] % 10 == 0:
            self.save_progress()
            self.save_stats()

    def mark_failed(self, image_path, error_message):
        """Markiert ein Bild als fehlgeschlagen."""
        self.error_images.append({
            'image_path': str(image_path),
            'timestamp': datetime.now().isoformat(),
            'error': error_message
        })
        self.stats['processed_images'] += 1
        self.stats['failed_images'] += 1

        # Speichere regelmäßig
        if self.stats['failed_images'] % 5 == 0:
            self.save_errors()
            self.save_stats()

    def start_processing(self, total_images):
        """Startet die Verarbeitung."""
        self.stats['total_images'] = total_images
        self.stats['start_time'] = datetime.now().isoformat()
        self.stats['end_time'] = None
        self.save_stats()

    def end_processing(self):
        """Beendet die Verarbeitung."""
        self.stats['end_time'] = datetime.now().isoformat()
        self.save_stats()

    def is_processed(self, image_path):
        """Überprüft, ob ein Bild bereits verarbeitet wurde."""
        return str(image_path) in self.processed_images

    def get_progress(self):
        """Gibt den aktuellen Fortschritt zurück."""
        if self.stats['total_images'] > 0:
            progress = (self.stats['processed_images'] / self.stats['total_images']) * 100
            return round(progress, 2)
        return 0.0

    def estimate_cost(self):
        """Schätzt die Kosten basierend auf den verwendeten Tokens (IONOS-Preise)."""
        # IONOS-Preise: 1€ pro 1M Input-Tokens + 1€ pro 1M Output-Tokens
        # Annahme: ~50% Input, ~50% Output (konservative Schätzung)
        total_tokens = self.stats['total_tokens']
        input_tokens = total_tokens * 0.5
        output_tokens = total_tokens * 0.5

        input_cost = input_tokens / 1000000  # 1€ pro 1M Input-Tokens
        output_cost = output_tokens / 1000000  # 1€ pro 1M Output-Tokens
        estimated_cost = input_cost + output_cost

        self.stats['estimated_cost'] = round(estimated_cost, 2)
        return estimated_cost

    def print_summary(self):
        """Zeigt eine Zusammenfassung des Fortschritts an."""
        print("\n" + "="*60)
        print("📊 VERARBEITUNGSZUSAMMENFASSUNG")
        print("="*60)

        if self.stats['start_time']:
            start_time = datetime.fromisoformat(self.stats['start_time'])
            print(f"📅 Startzeit: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if self.stats['end_time']:
            end_time = datetime.fromisoformat(self.stats['end_time'])
            print(f"⏰ Endzeit: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"📷 Gesamtbilder: {self.stats['total_images']}")
        print(f"✅ Erfolgreich: {self.stats['successful_images']}")
        print(f"❌ Fehlgeschlagen: {self.stats['failed_images']}")
        print(f"📊 Fortschritt: {self.get_progress()}%")
        print(f"💰 Geschätzte Kosten: {self.stats['estimated_cost']}€")
        print(f"🔢 Verwendete Tokens: {self.stats['total_tokens']:,}")

        if self.stats['processed_images'] > 0:
            avg_tokens = self.stats['total_tokens'] / self.stats['processed_images']
            print(f"📈 Durchschnittliche Tokens pro Bild: {avg_tokens:.1f}")

        print("="*60)

def test_tracker():
    """Testet den Fortschritts-Tracker."""
    tracker = ProgressTracker()

    # Simuliere einige Verarbeitungen
    tracker.start_processing(100)

    for i in range(1, 11):
        image_path = f"test_image_{i}.jpg"
        if i % 3 == 0:
            tracker.mark_failed(image_path, f"Testfehler {i}")
        else:
            tracker.mark_successful(image_path, 1500)

    tracker.end_processing()
    tracker.estimate_cost()
    tracker.print_summary()

    # Speichere alles
    tracker.save_progress()
    tracker.save_errors()
    tracker.save_stats()

if __name__ == "__main__":
    test_tracker()