"""
Orchestrator Logic – Saham-Lab v0.3
Routing & Input-Analyse für das Multi-Agenten-System.
"""

from typing import Any, Dict, List, Literal, Union


InputType = Literal[
    "patterns",
    "structures",
    "points",
    "dynamics",
    "sequence",
    "multi",
    "unknown",
]


def detect_input_type(data: Any) -> InputType:
    """
    Versucht zu erkennen, was für eine Eingabe wir haben.

    Beispiele:
      - {"patterns": [...]}              -> "patterns"
      - {"structures": [...]}            -> "structures"
      - {"points": [...]}                -> "points"
      - {"motion": [...]}                -> "dynamics"
      - {"patterns","structures",...}    -> "multi"
      - [1,2,3,4]                        -> "sequence"
      - sonst                            -> "unknown"
    """

    # Liste -> Sequenz
    if isinstance(data, list):
        # reine numerische Liste = Pattern-Sequence
        if all(isinstance(x, (int, float)) for x in data):
            return "sequence"
        return "unknown"

    if not isinstance(data, dict):
        return "unknown"

    keys = set(data.keys())

    # Normalisierung von Aliassen
    key_aliases = {
        "pattern": "patterns",
        "pattern_units": "patterns",
        "structure": "structures",
        "structures": "structures",
        "points": "points",
        "point_units": "points",
        "motion": "dynamics",
        "dynamics": "dynamics",
    }

    norm_keys = set()
    for k in keys:
        norm_keys.add(key_aliases.get(k, k))

    # Einzel-Typen
    if "patterns" in norm_keys and len(norm_keys) == 1:
        return "patterns"
    if "structures" in norm_keys and len(norm_keys) == 1:
        return "structures"
    if "points" in norm_keys and len(norm_keys) == 1:
        return "points"
    if "dynamics" in norm_keys and len(norm_keys) == 1:
        return "dynamics"

    # Multi-Agenten-Input
    multi_keys = {"patterns", "structures", "points", "dynamics"}
    if len(norm_keys.intersection(multi_keys)) >= 2:
        return "multi"

    return "unknown"


def determine_pipeline_for_input(input_type: InputType) -> List[str]:
    """
    Mappt den erkannten Input-Typ auf eine Tool-Pipeline.

    Rückgabe ist eine Liste von Tool-Namen, die aufgerufen werden sollen.
    Diese Namen müssen zu den tool.function.name-Einträgen
    und zum PYTHON_TOOL_REGISTRY in run_orchestrator.py passen.
    """

    if input_type == "patterns":
        # Vollanalyse über PatternCore
        return ["patterncore_full"]

    if input_type == "structures":
        return ["structureweaver_full"]

    if input_type == "points":
        return ["pointengine_full"]

    if input_type == "dynamics":
        return ["pointdynamics_full"]

    if input_type == "sequence":
        # Numerische Sequenz -> PatternCore als Standard
        return ["patterncore_full"]

    if input_type == "multi":
        # Einfachste Variante: alles an TemporalSynth delegieren
        # Später: Kette pattern -> structure -> dynamics -> temporal
        return ["temporal_full"]

    # Fallback: Orchestrator lässt Modell selbst Tools wählen (tool_choice="auto")
    return []


def build_system_prompt() -> str:
    """
    Systemprompt für den Orchestrator-Lauf.
    Hier wird erklärt, welche Agenten es gibt und wie sie genutzt werden sollen.
    """

    return (
        "Du bist der zentrale Orchestrator des Saham-Lab Multi-Agenten-Systems.\n"
        "Dir stehen spezialisierte Tools/Agenten zur Verfügung:\n\n"
        "- PatternCore: Mustererkennung in numerischen Sequenzen\n"
        "- StructureWeaver: Strukturelle Verdichtung & Knotenbildung\n"
        "- PointEngine / PointDynamics: Punkt- und Bewegungsanalyse\n"
        "- TemporalSynth: Zeitachsen-Synthese über mehrere Agenten-Ergebnisse\n\n"
        "Wenn der Input klar einem Typ zuzuordnen ist, nutze bevorzugt die "
        "entsprechenden Agenten-Tools.\n"
        "Wenn du mehrere Tools aufrufst, nutze sie in sinnvoller Reihenfolge und "
        "erkläre dem Nutzer, was du getan hast."
    )
