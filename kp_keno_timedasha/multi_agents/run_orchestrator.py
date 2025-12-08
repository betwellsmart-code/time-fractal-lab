"""
run_orchestrator.py – Saham-Lab Orchestrator v0.3

- Lädt OpenAI-Client (optional, per Safety-Schalter)
- Registriert alle Tools (PatternCore, StructureWeaver, PointEngine, PointDynamics, TemporalSynth)
- Führt Tool-Calls WIRKLICH aus (kein Platzhalter mehr)
- Nutzt orchestrator_logic für Input-Typ & Pipelines
"""

import json
from typing import Any, Dict, List

from loguru import logger

# OpenAI-Konfiguration (mit Safety-Schalter)
from openai_config import (
    get_client,
    SAHAM_ENABLE_OPENAI,  # bool, muss in openai_config.py existieren
)

# Tool-Definitionen (OpenAI-Tool-Objekte)
from patterncore_tools import PATTERNCORE_TOOLS  # Beispielname
from structureweaver_tools import STRUCTUREWEAVER_TOOLS
from pointengine_tools import POINTENGINE_TOOLS
from pointdynamics_tools import POINTDYNAMICS_TOOLS
from temporalsynth_tools import TEMPORALSYNTH_TOOLS

# Logik-Funktionen (Python-Implementierungen)
from patterncore_tools import patterncore_analyze  # ggf. anpassen
from structureweaver_logic import sw_full_pipeline  # ggf. anpassen
from pointengine_logic import pe_full_pipeline      # ggf. anpassen
from pointdynamics_logic import pd_full_pipeline    # ggf. anpassen
from temporalsynth_logic import ts_full_pipeline    # ggf. anpassen

from orchestrator_logic import (
    detect_input_type,
    determine_pipeline_for_input,
    build_system_prompt,
)


# ---------------------------------------------------------
#  PYTHON-TOOL-REGISTRY
#  Verknüpft Tool-Namen (function.name) mit Python-Funktionen.
#  -> Falls deine Toolnamen / Funktionsnamen abweichen: HIER anpassen.
# ---------------------------------------------------------

PYTHON_TOOL_REGISTRY = {
    # PatternCore
    "patterncore_full": patterncore_analyze,

    # StructureWeaver
    "structureweaver_full": sw_full_pipeline,

    # PointEngine / PointDynamics
    "pointengine_full": pe_full_pipeline,
    "pointdynamics_full": pd_full_pipeline,

    # TemporalSynth
    "temporal_full": ts_full_pipeline,
}


# ---------------------------------------------------------
#  Tool-Liste für OpenAI (funktionale Tools)
# ---------------------------------------------------------

ALL_TOOLS: List[Dict[str, Any]] = (
    list(PATTERNCORE_TOOLS)
    + list(STRUCTUREWEAVER_TOOLS)
    + list(POINTENGINE_TOOLS)
    + list(POINTDYNAMICS_TOOLS)
    + list(TEMPORALSYNTH_TOOLS)
)


def _execute_tool_locally(name: str, arguments: Any) -> Dict[str, Any]:
    """
    Führt ein Tool lokal aus, indem die passende Python-Funktion aus dem
    PYTHON_TOOL_REGISTRY aufgerufen wird.

    arguments: kann String (JSON) oder Dict sein.
    Rückgabe: JSON-serialisierbares Dict.
    """
    if isinstance(arguments, str):
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            logger.error(f"Tool-Args für {name} nicht parsebar: {arguments}")
            return {"error": f"Argumente nicht parsebar für {name}"}
    elif isinstance(arguments, dict):
        args = arguments
    else:
        args = {}

    func = PYTHON_TOOL_REGISTRY.get(name)
    if func is None:
        logger.error(f"Kein Python-Tool für {name} registriert.")
        return {"error": f"Kein Python-Tool für {name} registriert."}

    try:
        if isinstance(args, dict):
            result = func(**args)  # versucht, keyword-args zu nutzen
        else:
            result = func(args)
    except TypeError:
        # Fallback: alles als ein Argument
        try:
            result = func(args)
        except Exception as e:
            logger.exception(f"Fehler bei Ausführung von {name}")
            return {"error": f"Fehler in Tool {name}: {e}"}
    except Exception as e:
        logger.exception(f"Fehler bei Ausführung von {name}")
        return {"error": f"Fehler in Tool {name}: {e}"}

    # Ergebnis muss JSON-serialisierbar sein:
    try:
        json.dumps(result)
        return result
    except TypeError:
        logger.warning(f"Tool {name} hat nicht-serialisierbares Ergebnis geliefert.")
        return {"result": str(result)}


def run_orchestrator(user_input: Any) -> Any:
    """
    Haupt-Einstiegspunkt für den Orchestrator.

    - erkennt Input-Typ
    - bestimmt Pipeline
    - ruft OpenAI mit den verfügbaren Tools auf
    - führt Tool-Calls lokal aus
    - gibt finale Modellantwort zurück
    """

    logger.info("Orchestrator gestartet.")
    logger.debug(f"User-Input: {user_input!r}")

    # Safety: OpenAI muss explizit erlaubt sein
    if not SAHAM_ENABLE_OPENAI:
        logger.warning("OpenAI-Nutzung ist deaktiviert (SAHAM_ENABLE_OPENAI=False).")
        return {
            "error": "OpenAI ist deaktiviert. Orchestrator läuft im Offline-Modus.",
            "hint": "Setze SAHAM_ENABLE_OPENAI=True in openai_config.py, "
                    "wenn du Modellaufrufe erlauben willst.",
        }

    client = get_client()

    input_type = detect_input_type(user_input)
    logger.info(f"Detektierter Input-Typ: {input_type}")

    pipeline = determine_pipeline_for_input(input_type)
    logger.info(f"Vorgeschlagene Pipeline: {pipeline if pipeline else 'auto'}")

    system_prompt = build_system_prompt()

    # Erste Phase: Modell entscheidet, welche Tools wie genutzt werden sollen
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "Hier ist der Input für das Saham-Lab-System:\n"
                f"{json.dumps(user_input, ensure_ascii=False)}\n\n"
                "Nutze die verfügbaren Tools, um eine strukturierte Auswertung zu liefern."
            ),
        },
    ]

    # Wenn wir eine klar definierte Pipeline haben, geben wir sie dem Modell als Hinweis
    if pipeline:
        messages.append(
            {
                "role": "system",
                "content": (
                    "Vorgeschlagene Tool-Pipeline (Reihenfolge): "
                    + ", ".join(pipeline)
                ),
            }
        )

    logger.debug("Starte ersten OpenAI-Call (Tool-Planung)...")

    first = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        tools=ALL_TOOLS,
        tool_choice="auto",
    )

    first_msg = first.choices[0].message
    tool_calls = first_msg.tool_calls or []

    logger.info(f"Modell hat {len(tool_calls)} Tool-Calls angefordert.")

    tool_messages: List[Dict[str, Any]] = []

    # Tool-Calls WIRKLICH ausführen
    for tc in tool_calls:
        name = tc.function.name
        arguments = tc.function.arguments

        logger.info(f"Führe Tool {name} aus...")
        result = _execute_tool_locally(name, arguments)

        tool_messages.append(
            {
                "role": "tool",
                "tool_call_id": tc.id,
                "name": name,
                "content": json.dumps(result, ensure_ascii=False),
            }
        )

    # Zweite Phase: Modell interpretiert die Tool-Ergebnisse und formuliert Antwort
    messages2: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        messages[1],  # user input
        first_msg,    # Tool-Auswahl-Nachricht
        *tool_messages,
    ]

    logger.debug("Starte zweiten OpenAI-Call (Synthese)...")

    second = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages2,
    )

    final_msg = second.choices[0].message
    logger.info("Orchestrator abgeschlossen.")

    return final_msg.content


if __name__ == "__main__":
    # Kleiner manueller Test: kann später ersetzt werden
    logger.add("orchestrator.log", rotation="500 KB")

    test_input = {
        "patterns": [1, 2, 3, 2, 5, 8, 13],
        "structures": [{"node": "A"}, {"node": "B"}],
        "motion": [0.1, 0.3, 0.2, 0.9],
    }

    result = run_orchestrator(test_input)
    print("=== ORCHESTRATOR-ERGEBNIS ===")
    print(result)
