"""
OpenAI-Konfiguration für Saham-Lab Multi-Agenten-System.
Sicher, modular, kein API-Key im Code.
"""

import os
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# .env-Datei automatisch laden, falls vorhanden
ENV_PATH = Path(__file__).resolve().parent / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

def get_api_key() -> str:
    """
    Holt den API-Key aus:
    1. Umgebungsvariable SAHAM_OPENAI_KEY
    2. Datei .env im Agentenverzeichnis
    Wirft Fehlermeldung, wenn keiner vorhanden ist.
    """
    key = os.getenv("SAHAM_OPENAI_KEY")

    if not key:
        raise RuntimeError(
            "❌ OpenAI API-Key fehlt!\n"
            "Bitte setze die Umgebungsvariable SAHAM_OPENAI_KEY "
            "oder lege eine .env mit SAHAM_OPENAI_KEY=... an."
        )

    return key


def get_client() -> OpenAI:
    """
    Erstellt einen OpenAI-Client für alle Agenten.
    Zentralisiert & sicher.
    """
    key = get_api_key()
    client = OpenAI(api_key=key)
    return client
