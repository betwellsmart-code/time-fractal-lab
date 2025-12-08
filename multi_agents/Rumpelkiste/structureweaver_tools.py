# multi_agents/structureweaver_tools.py

from multi_agents.structureweaver_logic import (
    sw_full_pipeline,
    sw_intake,
    sw_transition_mapping,
    sw_path_synthesis,
)

STRUCTUREWEAVER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "structureweaver_full",
            "description": "Führt die komplette StructureWeaver-Pipeline aus.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern_units": {
                        "type": "object",
                        "description": "PatternUnits-Output von PatternCore."
                    }
                },
                "required": ["pattern_units"],
            },
        },
    },

    # Optional Subtools
    {
        "type": "function",
        "function": {
            "name": "structureweaver_intake",
            "description": "Nur die Intake-Phase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern_units": {"type": "object"}
                },
                "required": ["pattern_units"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "structureweaver_transition",
            "description": "Nur Transition-Mapping.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intake_result": {"type": "object"}
                },
                "required": ["intake_result"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "structureweaver_paths",
            "description": "Nur Path-Synthese.",
            "parameters": {
                "type": "object",
                "properties": {
                    "density_result": {"type": "object"}
                },
                "required": ["density_result"],
            },
        },
    },
]


# Python-Wrapper für Orchestrator
def structureweaver_full(pattern_units):
    return sw_full_pipeline(pattern_units)


def structureweaver_intake(pattern_units):
    return sw_intake(pattern_units)


def structureweaver_transition(intake_result):
    return sw_transition_mapping(intake_result)


def structureweaver_paths(density_result):
    return sw_path_synthesis(density_result)
