"""
system_control_gate.py – SystemControlGate v1.0

Rolle:
    Die SystemControlGate-Komponente fungiert als Sicherheits- und 
    Qualitätskontrollschicht für das gesamte Multi-Agenten-System.

    Sie führt zwei zentrale Aufgaben aus:

    1) Pre-Check:
        – Prüft, ob ein Agent-Task ausgeführt werden sollte.
        – Liefert (ok: bool, info: dict).

    2) Post-Check:
        – Bewertet die Rückgabe eines Agenten.
        – Erkennt Inkonsistenzen, leere Ergebnisse, Fehlerstrukturen.
        – Liefert (ok: bool, info: dict).

Wichtig:
    Dieses Modul ist KEIN Agent.
    Es ist ein Infrastrukturelement des Orchestrators und ersetzt
    das frühere "guardian_gate.py", um Namenskollisionen zu vermeiden.
"""

from __future__ import annotations
from typing import Any, Dict, Tuple


class SystemControlGate:
    """
    SystemControlGate – Pre-/Post-Task-Kontrollinstanz für das
    Saham-Lab Multi-Agenten-System.

    Die Checks sind bewusst generisch gehalten und können später
    erweitert, spezialisiert oder datenbasiert trainiert werden.
    """

    # ================================================================
    # PRECHECK
    # ================================================================
    def precheck(
        self,
        agent_name: str,
        task_name: str,
        payload: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Wird vom Orchestrator VOR jedem Agenten-Aufruf ausgeführt.

        Rückgabe:
            (True, {})    → OK, Task darf laufen
            (False, info) → Blockiert, Orchestrator bricht Task ab
        """

        # Beispiel 1: Agent darf keine leeren Payloads bekommen
        if payload is None:
            return False, {
                "reason": "payload_none",
                "message": f"Task '{task_name}' für Agent '{agent_name}' hat keinen Payload."
            }

        # Beispiel 2: bestimmte Systemaufgaben sind geschützt
        if task_name.lower() in ["shutdown", "reset", "wipe", "danger"]:
            return False, {
                "reason": "restricted_task",
                "message": f"Task '{task_name}' ist durch SystemControlGate blockiert."
            }

        # Beispiel 3: Trend-/Forecast-Agenten brauchen Datenquellen
        if agent_name in ["trend", "forecast"]:
            if "profile" not in payload:
                return False, {
                    "reason": "missing_profile",
                    "message": f"Agent '{agent_name}' benötigt ein Profil im Payload."
                }

        return True, {}

    # ================================================================
    # POSTCHECK
    # ================================================================
    def postcheck(
        self,
        agent_name: str,
        task_name: str,
        payload: Dict[str, Any],
        output: Any,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Wird vom Orchestrator NACH dem Agenten-Aufruf ausgeführt.

        Sucht nach strukturellen Fehlern, leeren Ergebnissen,
        inkonsistenten Werten oder typischen Fehlerindikatoren.
        """

        # Null-Output
        if output is None:
            return False, {
                "reason": "null_output",
                "message": f"Agent '{agent_name}' lieferte kein Ergebnis.",
            }

        # Ergebnis sollte dict-artig sein
        if not isinstance(output, dict):
            return False, {
                "reason": "invalid_type",
                "message": f"Agent '{agent_name}' lieferte keinen dict-kompatiblen Output.",
                "type": str(type(output)),
            }

        # Erwartete Struktur prüfen
        if "result" not in output:
            return False, {
                "reason": "missing_result",
                "message": f"Output des Agenten '{agent_name}' enthält keinen 'result'-Schlüssel.",
                "output": output,
            }

        # Optional: TrendAgent-/ForecastAgent-spezifische Checks
        if agent_name in ["trend", "forecast"]:
            res = output.get("result")
            if res is None:
                return False, {
                    "reason": "invalid_analysis",
                    "message": f"{agent_name.capitalize()}Agent lieferte keine Analyse.",
                }

        return True, {}
