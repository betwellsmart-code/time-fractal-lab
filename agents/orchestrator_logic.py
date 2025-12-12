"""
orchestrator_logic.py – Orchestrator v0.9.1 (Titanium Patch)

Der Orchestrator ist der Dirigent des gesamten Saham-Lab Agentensystems.
Er verwaltet:

    – Agenteninstanzen
    – Routing von Tasks
    – Pre-/Post-Checks über SystemControlGate
    – standardisierte Agenten-Outputs
    – Logging & Fehlerhandling

Wichtig:
    In dieser Version ist das frühere 'GuardianGate' vollständig entfernt.
    Stattdessen wird 'SystemControlGate' verwendet, um die Architektur
    konsistent und zukunftssicher zu halten.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

# ================================================================
# Agent-Imports
# ================================================================
try:
    from .patterncore import PatternCore
except ImportError:
    from patterncore import PatternCore  # type: ignore

try:
    from .structureweaver import StructureWeaver
except ImportError:
    from structureweaver import StructureWeaver  # type: ignore

try:
    from .pointengine import PointEngine
except ImportError:
    from pointengine import PointEngine  # type: ignore

try:
    from .pointdynamics import PointDynamics
except ImportError:
    from pointdynamics import PointDynamics  # type: ignore

try:
    from .temporalsynth import TemporalSynth
except ImportError:
    from temporalsynth import TemporalSynth  # type: ignore

try:
    from .coherence_agent import CoherenceAgent
except ImportError:
    from coherence_agent import CoherenceAgent  # type: ignore

try:
    from .anomaly_agent import AnomalyAgent
except ImportError:
    from anomaly_agent import AnomalyAgent  # type: ignore

try:
    from .fusion_agent import FusionAgent
except ImportError:
    from fusion_agent import FusionAgent  # type: ignore

try:
    from .drift_agent import DriftAgent
except ImportError:
    from drift_agent import DriftAgent  # type: ignore

try:
    from .guardian_agent import GuardianAgent
except ImportError:
   from guardian_agent import GuardianCoreAgent as GuardianAgent
 # type: ignore

try:
    from .cluster_agent import ClusterAgent
except ImportError:
    from cluster_agent import ClusterAgent  # type: ignore

try:
    from .horizon_agent import HorizonAgent
except ImportError:
    from horizon_agent import HorizonAgent  # type: ignore

try:
    from .trend_agent import TrendAgent
except ImportError:
    from trend_agent import TrendAgent  # type: ignore

try:
    from .forecast_agent import ForecastAgent
except ImportError:
    from forecast_agent import ForecastAgent  # type: ignore

try:
    from .signature_agent import SignatureAgent
except ImportError:
    from signature_agent import SignatureAgent  # type: ignore


# ================================================================
# Neuer System-Kontroll-Import
# ================================================================
try:
    from .system_control_gate import SystemControlGate
except ImportError:
    from system_control_gate import SystemControlGate  # type: ignore


# OPTIONAL
try:
    from .diagnostic_core import DiagnosticCore
except ImportError:
    try:
        from diagnostic_core import DiagnosticCore  # type: ignore
    except ImportError:
        DiagnosticCore = None  # type: ignore


# ================================================================
# ORCHESTRATOR-KLASSE
# ================================================================
class Orchestrator:
    """
    zentrale Steuerinstanz (Dirigent) des Multi-Agenten-Systems
    """

    # ------------------------------------------------------------
    def __init__(self) -> None:

        # === SystemControlGate aktivieren ===
        self.system_control_gate = SystemControlGate()

        # === Agenten-Registry ===
        self.registry = {
            "pattern": PatternCore(),
            "structure": StructureWeaver(),
            "pointengine": PointEngine(),
            "pointdynamics": PointDynamics(),
            "temporal": TemporalSynth(),
            "coherence": CoherenceAgent(),
            "anomaly": AnomalyAgent(),
            "fusion": FusionAgent(),
            "drift": DriftAgent(),
            "guardian": GuardianAgent(),
            "cluster": ClusterAgent(),
            "horizon": HorizonAgent(),
            "trend": TrendAgent(),
            "forecast": ForecastAgent(),
            "signature": SignatureAgent(),
        }

        if DiagnosticCore:
            self.registry["diagnostic"] = DiagnosticCore()

    # ------------------------------------------------------------
    def list_agents(self) -> List[str]:
        return list(self.registry.keys())

    # ------------------------------------------------------------
    def run_task(
        self,
        agent_name: str,
        task_name: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        if agent_name not in self.registry:
            return {"ok": False, "error": f"Agent '{agent_name}' existiert nicht."}

        agent = self.registry[agent_name]

        # --------------------
        # PRECHECK
        # --------------------
        ok, info = self.system_control_gate.precheck(agent_name, task_name, payload)
        if not ok:
            return {
                "ok": False,
                "stage": "precheck",
                "info": info,
            }

        # --------------------
        # AUSFÜHRUNG
        # --------------------
        try:
            handler = getattr(agent, task_name)
        except Exception:
            return {
                "ok": False,
                "error": f"Agent '{agent_name}' besitzt keinen Task '{task_name}'.",
            }

        try:
            result = handler(payload)
        except Exception as exc:
            return {
                "ok": False,
                "stage": "execution",
                "error": str(exc),
            }

        # --------------------
        # POSTCHECK
        # --------------------
        ok, info = self.system_control_gate.postcheck(agent_name, task_name, payload, result)
        if not ok:
            return {
                "ok": False,
                "stage": "postcheck",
                "info": info,
                "output": result,
            }

        return {
            "ok": True,
            "result": result.get("result"),
            "raw": result,
        }
