"""
orchestrator_logic.py – Saham-Lab Orchestrator 0.6 (HQ-Standard)
----------------------------------------------------------------

Steuert alle Agenten:
    1 PatternCore
    2 StructureWeaver
    3 PointEngine
    4 PointDynamics
    5 TemporalSynth
    6 CoherenceAgent
    7 AnomalyAgent

Erweiterbar für:
    8 FusionAgent
    9 DriftAgent
    10 ClusterAgent
    11 SignatureAgent
    12 HorizonAgent

Design:
    - Stabil, logisch modularisiert
    - GuardianGate + DiagnosticCore eingebaut
    - Einheitliche API:
        orchestrator.run_task(task_name, payload)
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, Callable

# Agenten imports (HQ-Standard: try both)
try:
    from multi_agents.patterncore import PatternCore
    from multi_agents.structureweaver import StructureWeaver
    from multi_agents.pointengine import PointEngine
    from multi_agents.pointdynamics import PointDynamics
    from multi_agents.temporalsynth import TemporalSynth
    from multi_agents.coherence_agent import CoherenceAgent
    from multi_agents.anomaly_agent import AnomalyAgent
except ImportError:
    from patterncore import PatternCore
    from structureweaver import StructureWeaver
    from pointengine import PointEngine
    from pointdynamics import PointDynamics
    from temporalsynth import TemporalSynth
    from coherence_agent import CoherenceAgent
    from anomaly_agent import AnomalyAgent


# ---------------------------------------------------------
# GuardianGate – Mini-Sanity-Layer
# ---------------------------------------------------------
def guardian_gate_input(name: str, payload: Any) -> Dict[str, Any]:
    warnings = []
    if payload is None:
        warnings.append({
            "source": "guardian_gate",
            "reason": f"Input for task '{name}' is None."
        })
    return warnings


def guardian_gate_output(name: str, output: Any) -> Dict[str, Any]:
    warnings = []
    if not isinstance(output, dict):
        warnings.append({
            "source": "guardian_gate",
            "reason": f"Output of task '{name}' is not a dict."
        })
    return warnings


# ---------------------------------------------------------
# DiagnosticCore – einfache Diagnose-Hooks
# ---------------------------------------------------------
def diagnostic_simple(result: Any, debug: Any) -> Dict[str, Any]:
    """
    Mini-Diagnose: prüft, ob debug existiert und ob Kernfelder enthalten sind.
    """
    return {
        "has_debug": debug is not None,
        "result_type": str(type(result)),
        "debug_keys": list(debug.keys()) if isinstance(debug, dict) else [],
    }


# =====================================================================
# ORCHESTRATOR 0.6 – HQ-STANDARD
# =====================================================================
class Orchestrator:
    """
    Zentrale Steuerung aller Agenten im Saham-Lab.
    """

    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        """
        Registriert alle verfügbaren Agenten.
        """
        errors = {}

        # Agent 1–5
        try: self.agents["patterncore"] = PatternCore()
        except Exception as e: errors["patterncore"] = e

        try: self.agents["structureweaver"] = StructureWeaver()
        except Exception as e: errors["structureweaver"] = e

        try: self.agents["pointengine"] = PointEngine()
        except Exception as e: errors["pointengine"] = e

        try: self.agents["pointdynamics"] = PointDynamics()
        except Exception as e: errors["pointdynamics"] = e

        try: self.agents["temporalsynth"] = TemporalSynth()
        except Exception as e: errors["temporalsynth"] = e

        # Agent 6
        try: self.agents["coherence"] = CoherenceAgent()
        except Exception as e: errors["coherence"] = e

        # Agent 7 (NEU)
        try: self.agents["anomaly"] = AnomalyAgent()
        except Exception as e: errors["anomaly"] = e

        if errors:
            print("[WARN] Errors during agent registration:", errors)

    # ------------------------------------------------------
    # Utility
    # ------------------------------------------------------
    def has_agent(self, name: str) -> bool:
        return name in self.agents

    def list_agents(self):
        return list(self.agents.keys())

    def _wrap(
        self,
        *,
        ok: bool,
        result: Any,
        warnings: Any = None,
        diagnostics: Any = None,
        agent: str = None,
        task: str = None,
    ) -> Dict[str, Any]:
        return {
            "ok": ok,
            "result": result,
            "warnings": warnings or [],
            "diagnostics": diagnostics,
            "agent": agent,
            "task": task,
        }
    # =====================================================================
    # TASK-DISPATCHER
    # =====================================================================
    def run_task(self, task_name: str, payload: Dict[str, Any]):
        """
        Zentrale Task-Schaltstelle.
        Entscheidet, welcher Agent was ausführt.
        """
        if not isinstance(payload, dict):
            return self._wrap(
                ok=False,
                result=None,
                warnings=[{"source": "orchestrator", "reason": "Payload must be a dict"}],
                task=task_name,
            )

        # GuardianGate – INPUT
        warnings = guardian_gate_input(task_name, payload)

        # Routing
        try:
            if task_name == "patterncore_summary":
                return self.patterncore_summary(payload.get("data"), warnings=warnings)

            if task_name == "coherence_full":
                return self.coherence_full(payload.get("data"), warnings=warnings)

            if task_name == "anomaly_full":
                return self.anomaly_full(payload.get("data"), warnings=warnings)

            if task_name == "anomaly_profile":
                return self.anomaly_profile(payload.get("data"), warnings=warnings)

        except Exception as e:
            return self._wrap(
                ok=False,
                result=None,
                warnings=warnings + [{"source": "exception", "reason": str(e)}],
                agent="unknown",
                task=task_name,
            )

        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings + [{"source": "orchestrator", "reason": f"Unknown task '{task_name}'"}],
            task=task_name,
        )


    # =====================================================================
    # INTERFACE-METHODEN FÜR AGENTEN
    # =====================================================================

    def _safe_call_agent(self, agent_name: str, task_name: str, payload: Dict[str, Any], warnings):
        """
        Vereinheitlichte, abgesicherte Agent-Ausführung.
        """
        if not self.has_agent(agent_name):
            warnings.append({
                "source": "orchestrator",
                "reason": f"Agent '{agent_name}' not registered."
            })
            return None, warnings, None

        agent = self.agents[agent_name]

        try:
            out = agent.run(task_name, payload, with_debug=True)
        except Exception as e:
            warnings.append({
                "source": "agent",
                "reason": f"Exception in {agent_name}: {str(e)}",
            })
            return None, warnings, None

        # GuardianGate OUTPUT
        warnings += guardian_gate_output(task_name, out)

        # Diagnostics
        diagnostics = diagnostic_simple(out.get("result"), out.get("debug"))

        return out, warnings, diagnostics
    # =====================================================================
    # AGENT 7 – AnomalyAgent Integration
    # =====================================================================

    def anomaly_full(self, data, warnings=None):
        warnings = warnings or []
        agent_name = "anomaly"
        task_name = "anomaly_full"

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name, task_name, {"data": data}, warnings
        )

        if out is None:
            return self._wrap(
                ok=False,
                result=None,
                warnings=warnings,
                diagnostics=None,
                agent=agent_name,
                task=task_name,
            )

        return self._wrap(
            ok=True,
            result=out["result"],
            warnings=warnings,
            diagnostics=diagnostics,
            agent=agent_name,
            task=task_name,
        )

    def anomaly_profile(self, data, warnings=None):
        warnings = warnings or []
        agent_name = "anomaly"
        task_name = "anomaly_profile"

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name, task_name, {"data": data}, warnings
        )

        if out is None:
            return self._wrap(
                ok=False,
                result=None,
                warnings=warnings,
                diagnostics=None,
                agent=agent_name,
                task=task_name,
            )

        return self._wrap(
            ok=True,
            result=out["result"],
            warnings=warnings,
            diagnostics=diagnostics,
            agent=agent_name,
            task=task_name,
        )
