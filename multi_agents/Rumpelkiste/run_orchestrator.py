"""
Saham-Lab Orchestrator v1.0
-------------------------------------
Einheitlicher Multi-Agent-Orchestrator für:

- PatternCore
- StructureWeaver
- PointEngine
- PointDynamics
- TemporalSynth

OpenAI optional (Safety-Schalter in openai_config.py)
Tool-Calls werden lokal ausgeführt
"""

# =========================================================
#  IMPORTS
# =========================================================

# 1) Python Standard Library
import os
import sys
import json
from typing import Any, Dict, List

# 2) Third-Party
from loguru import logger

# 3) Saham-Lab Modules
from multi_agents.openai_config import (
    get_client,
    SAHAM_ENABLE_OPENAI,
)

# Tool-Definitionen
from multi_agents.patterncore_tools import PATTERNCORE_TOOLS, patterncore_analyze
from multi_agents.structureweaver_tools import STRUCTUREWEAVER_TOOLS, sw_full_pipeline
from multi_agents.pointengine_tools import POINTENGINE_TOOLS, pe_full_pipeline
from multi_agents.pointdynamics_tools import POINTDYNAMICS_TOOLS, pointdynamics_full
from multi_agents.temporalsynth_tools import TEMPORALSYNTH_TOOLS, ts_full_pipeline

# Kernel für interne Mathematik (PointDynamics 0.1)
from multi_agents.pointdynamics_kernel import pd_kernel_pipeline

# Orchestrator-Logik
from orchestrator_logic import (
    detect_input_type,
    determine_pipeline_for_input,
    build_system_prompt,
)


# =========================================================
#  PYTHON TOOL EXECUTION REGISTRY
# =========================================================

PYTHON_TOOL_REGISTRY = {
    # PatternCore
    "patterncore_full": patterncore_analyze,

    # StructureWeaver
    "structureweaver_full": sw_full_pipeline,

    # PointEngine
    "pointengine_full": pe_full_pipeline,

    # PointDynamics (0.2 Tool Version)
    "pointdynamics_full": pointdynamics_full,

    # TemporalSynth
    "temporal_full": ts_full_pipeline,
}


# Alle Tools für OpenAI (falls aktiviert)
ALL_TOOLS: List[Dict[str, Any]] = (
    PATTERNCORE_TOOLS
    + STRUCTUREWEAVER_TOOLS
    + POINTENGINE_TOOLS
    + POINTDYNAMICS_TOOLS
    + TEMPORALSYNTH_TOOLS
)


# =========================================================
#  INTERNES AUSFÜHRUNGSSYSTEM FÜR TOOLS
# =========================================================

def _execute_tool_locally(name: str, arguments: Any) -> Dict[str, Any]:
    """
    Führt ein Python-Tool lokal aus, ohne OpenAI.
    """
    if isinstance(arguments, str):
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            logger.error(f"Argumente nicht parsebar für Tool {name}: {arguments}")
            return {"error": "Argumente nicht parsebar"}
    else:
        args = arguments or {}

    func = PYTHON_TOOL_REGISTRY.get(name)
    if func is None:
        logger.error(f"Kein registriertes Python-Tool gefunden: {name}")
        return {"error": f"Unbekanntes Tool: {name}"}

    try:
        if isinstance(args, dict):
            result = func(**args)
        else:
            result = func(args)
    except TypeError:
        try:
            result = func(args)
        except Exception as e:
            logger.exception(f"Fehler bei Tool {name}")
            return {"error": f"Toolfehler: {e}"}
    except Exception as e:
        logger.exception(f"Fehler bei Tool {name}")
        return {"error": f"Toolfehler: {e}"}

    try:
        json.dumps(result)
        return result
    except TypeError:
        return {"result": str(result)}


# =========================================================
#  HAUPTFUNKTION
# =========================================================

def run_orchestrator(user_input: Any) -> Any:
    """
    Zentrale Steuereinheit:

    - erkennt Input
    - bestimmt Pipeline
    - ruft Tools lokal aus
    - ruft OpenAI (falls aktiviert)
    - erzeugt finale Antwort
    """

    logger.info("Orchestrator gestartet.")
    logger.debug(f"User Input: {user_input}")

    # ---------------------------
    # OFFLINE-MODUS (NO OPENAI)
    # ---------------------------
    if not SAHAM_ENABLE_OPENAI:
        logger.warning("OpenAI deaktiviert – Offline-Ausführung aktiv.")
        return {
            "offline_mode": True,
            "note": "OpenAI ist deaktiviert. Toolausführung lokal möglich.",
            "tools_available": list(PYTHON_TOOL_REGISTRY.keys()),
        }

    # ---------------------------
    # ONLINE-MODUS (OPENAI)
    # ---------------------------
    client = get_client()
    system_prompt = build_system_prompt()

    input_type = detect_input_type(user_input)
    pipeline = determine_pipeline_for_input(input_type)

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "Hier ist der Input fuer das Saham-Lab-System:\n"
                f"{json.dumps(user_input, ensure_ascii=False)}\n\n"
                "Nutze Tools, um eine strukturierte Auswertung zu liefern."
            ),
        },
    ]

    if pipeline:
        messages.append(
            {
                "role": "system",
                "content": "Vorgeschlagene Pipeline: " + ", ".join(pipeline),
            }
        )

    # ---------------------------
    # PHASE 1 – TOOL PLANUNG
    # ---------------------------
    first = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        tools=ALL_TOOLS,
        tool_choice="auto",
    )

    first_msg = first.choices[0].message
    tool_calls = first_msg.tool_calls or []

    tool_messages = []

    # ---------------------------
    # PHASE 2 – TOOL AUSFÜHRUNG
    # ---------------------------
    for call in tool_calls:
        name = call.function.name
        args = call.function.arguments

        logger.info(f"Tool wird ausgeführt: {name}")
        result = _execute_tool_locally(name, args)

        tool_messages.append(
            {
                "role": "tool",
                "tool_call_id": call.id,
                "name": name,
                "content": json.dumps(result, ensure_ascii=False),
            }
        )

    # ---------------------------
    # PHASE 3 – ENDANTWORT
    # ---------------------------
    messages2 = [
        {"role": "system", "content": system_prompt},
        messages[1],  # input
        first_msg,    # tool choice
        *tool_messages,
    ]

    second = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages2,
    )

    return second.choices[0].message.content


# =========================================================
#  LOKALER TEST
# =========================================================

if __name__ == "__main__":
    logger.add("orchestrator.log", rotation="300 KB")
    print("=== ORCHESTRATOR-TEST ===")

    test_input = {
        "series": [1, 4, 2, 8, 3, 11]
    }

    res = run_orchestrator(test_input)
    print(res)
