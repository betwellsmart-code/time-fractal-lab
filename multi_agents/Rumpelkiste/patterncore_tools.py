# multi_agents/patterncore_tools.py

from multi_agents.patterncore_logic import patterncore_analyze

# OpenAI-Tool-Definition (für run_orchestrator.py)
PATTERNCORE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "patterncore_full",
            "description": "Analysiert numerische Sequenzen (PatternCore).",
            "parameters": {
                "type": "object",
                "properties": {
                    "values": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Liste numerischer Werte"
                    }
                },
                "required": ["values"]
            },
        },
    }
]


# Python-Funktion für die Registry im Orchestrator
def patterncore_full(values):
    """Wrapper – entspricht exakt dem Tool-Name."""
    return patterncore_analyze(values)
