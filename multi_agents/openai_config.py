"""
openai_config.py – Sichere OpenAI-Initialisierung für Saham-Lab
"""

from openai import OpenAI

# -----------------------------------------------------
# Sicherheitsschalter:
# Wenn False → kein OpenAI-Aufruf, Orchestrator läuft offline
# -----------------------------------------------------
SAHAM_ENABLE_OPENAI = False    # <- Du kannst das später auf True setzen

_client = None


def get_client():
    """
    Gibt einen Singleton-OpenAI-Client zurück.
    Nur wenn SAHAM_ENABLE_OPENAI=True.
    """
    global _client

    if not SAHAM_ENABLE_OPENAI:
        raise RuntimeError("OpenAI ist deaktiviert (SAHAM_ENABLE_OPENAI=False).")

    if _client is None:
        _client = OpenAI()

    return _client
