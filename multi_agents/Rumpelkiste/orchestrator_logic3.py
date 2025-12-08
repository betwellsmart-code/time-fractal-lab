# =====================================================================
# orchestrator_logic.py – Saham-Lab Orchestrator 0.7 (HQ-Fusion Edition)
# =====================================================================

from __future__ import annotations
from typing import Any, Dict, List, Callable
import traceback

# ---------------------------------------------------------
# Agent Imports (pattern → fusion)
# ---------------------------------------------------------
try:
    from multi_agents.patterncore import PatternCore
    from multi_agents.structureweaver import StructureWeaver
    from multi_agents.pointengine import PointEngine
    from multi_agents.pointdynamics import PointDynamics
    from multi_agents.temporalsynth import TemporalSynth
    from multi_agents.coherence_agent import CoherenceAgent
    from multi_agents.anomaly_agent import AnomalyAgent
    from multi_agents.fusion_agent import FusionAgent
except ImportError:
    from patterncore import PatternCore
    from structureweaver import StructureWeaver
    from pointengine import PointEngine
    from pointdynamics import PointDynamics
    from temporalsynth import TemporalSynth
    from coherence_agent import CoherenceAgent
    from anomaly_agent import AnomalyAgent
    from fusion_agent import FusionAgent


# ---------------------------------------------------------
# GuardianGate – Mini-Sanity Layer
# ---------------------------------------------------------
def guardian_gate_input(task: str, payload: Any):
    warnings = []
    if payload is None:
        warnings.append({"source": "guardian_gate", "reason": f"Payload is None for task {task}"})
    return warnings


def guardian_gate_output(task: str, output: Any):
    warnings = []
    if not isinstance(output, dict):
        warnings.append({"source": "guardian_gate", "reason": f"Output of {task} is not a dict"})
    return warnings


# ---------------------------------------------------------
# DiagnosticCore – Mini-Diagnose
# ---------------------------------------------------------
def diagnostic_simple(result: Any, debug: Any):
    return {
        "has_debug": isinstance(debug, dict),
        "debug_keys": list(debug.keys()) if isinstance(debug, dict) else [],
        "result_type": str(type(result)),
    }


# =====================================================================
# ORCHESTRATOR 0.7 – MIT FUSIONAGENT
# =====================================================================
class Orchestrator:

    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self._register_default_agents()

    # ------------------------------------------------------
    # Agent-Registry
    # ------------------------------------------------------
    def _register_default_agents(self):
        errors = {}

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

        try: self.agents["coherence"] = CoherenceAgent()
        except Exception as e: errors["coherence"] = e

        try: self.agents["anomaly"] = AnomalyAgent()
        except Exception as e: errors["anomaly"] = e

        # 🟦 Agent 8 – FusionAgent
        try: self.agents["fusion"] = FusionAgent()
        except Exception as e: errors["fusion"] = e

        if errors:
            print("[WARN] Agent load errors:", errors)

    # ------------------------------------------------------
    def list_agents(self):
        return list(self.agents.keys())

    # ------------------------------------------------------
   class Orchestrator:
    ...
    ...
    # ------------------------------------------------------------
    # Einheitlicher Rückgabe-Wrapper (HQ-Standard)
    # ------------------------------------------------------------
    def _wrap(
        self,
        ok: bool,
        result,
        warnings,
        diagnostics,
        agent: str,
        task: str,
    ):
        return {
            "ok": bool(ok),
            "result": result,
            "warnings": warnings or [],
            "diagnostics": diagnostics,
            "agent": agent,
            "task": task,
        }



    # ------------------------------------------------------
    # Zentrale Agent-Ausführung
    # ------------------------------------------------------
    def _safe_call_agent(self, agent_name: str, task: str, payload: Dict[str, Any], warnings):
        if agent_name not in self.agents:
            warnings.append({"source": "orchestrator", "reason": f"Agent '{agent_name}' not loaded"})
            return None, warnings, None

        agent = self.agents[agent_name]

        # Agent-Aufruf
        try:
            out = agent.run(task, payload, with_debug=True)
        except Exception as e:
            warnings.append({"source": "agent_exception", "reason": str(e)})
            return None, warnings, None

        # Guardian output check
        warnings += guardian_gate_output(task, out)

        diagnostics = diagnostic_simple(out.get("result"), out.get("debug"))

        return out, warnings, diagnostics

    # ------------------------------------------------------
    # Central Dispatcher
    # ------------------------------------------------------
    def run_task(self, task_name: str, payload: Dict[str, Any]):
        warnings = guardian_gate_input(task_name, payload)

        try:
            # PatternCore
            if task_name == "patterncore_summary":
                return self.patterncore_summary(payload.get("data"), warnings=warnings)

            # Coherence
            if task_name == "coherence_full":
                return self.coherence_full(payload.get("data"), warnings=warnings)

            # Anomaly
            if task_name == "anomaly_full":
                return self.anomaly_full(payload.get("data"), warnings=warnings)

            if task_name == "anomaly_profile":
                return self.anomaly_profile(payload.get("data"), warnings=warnings)

            # 🟦 FusionAgent
            if task_name == "fusion_full":
                return self.fusion_full(payload.get("data"), warnings=warnings)

            if task_name == "fusion_profile":
                return self.fusion_profile(payload.get("data"), warnings=warnings)

        except Exception as e:
            return self._wrap(
                ok=False,
                result=None,
                warnings=warnings + [{"source": "dispatcher", "reason": str(e)}],
                task=task_name,
            )

        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings + [{"source": "dispatcher", "reason": f"Unknown task {task_name}"}],
            task=task_name,
        )

    # =====================================================================
    # FUSIONAGENT – Vollständige Integration
    # =====================================================================
    def fusion_full(self, data, warnings=None):
        warnings = warnings or []
        agent_name = "fusion"
        task = "fusion_full"

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name, task, {"data": data}, warnings
        )

        if out is None:
            return self._wrap(ok=False, result=None, warnings=warnings, agent=agent_name, task=task)

        return self._wrap(
            ok=True,
            result=out["result"],
            warnings=warnings,
            diagnostics=diagnostics,
            agent=agent_name,
            task=task,
        )

    def fusion_profile(self, data, warnings=None):
        warnings = warnings or []
        agent_name = "fusion"
        task = "fusion_profile"

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name, task, {"data": data}, warnings
        )

        if out is None:
            return self._wrap(ok=False, result=None, warnings=warnings, agent=agent_name, task=task)

        return self._wrap(
            ok=True,
            result=out["result"],
            warnings=warnings,
            diagnostics=diagnostics,
            agent=agent_name,
            task=task,
        )
# ======================================================================
# DRIFTAGENT-INTEGRATION – EIN GUSS PATCH
# ======================================================================
"""
DriftAgent-Orchestrator-Erweiterung (Snapshot-Level)

Voraussetzung:
    - multi_agents.drift_agent.DriftAgent ist vorhanden
    - Orchestrator-Klasse ist oben definiert
    - _register_default_agents, run_task und _safe_call_agent existieren

Wirkung:
    - registriert Agent "drift" automatisch
    - ergänzt Tasks:
        - "drift_full"
        - "drift_profile"
    - fügt Methoden Orchestrator.drift_full / drift_profile hinzu
    - alles ohne bestehende Definitionen im Kopf bearbeiten zu müssen
"""

try:
    from multi_agents.drift_agent import DriftAgent
except ImportError:
    from drift_agent import DriftAgent


# Original-Methoden sichern
_original_register_default_agents = Orchestrator._register_default_agents
_original_run_task = Orchestrator.run_task


def _register_default_agents_with_drift(self):
    """
    Wrap um die bestehende Agent-Registrierung:
    Ruft zuerst das Original auf, ergänzt dann Agent 9 'drift'.
    """
    _original_register_default_agents(self)
    try:
        self.agents["drift"] = DriftAgent()
    except Exception as e:
        # Nur warnen, Orchestrator soll trotzdem startbar bleiben
        print("[WARN] DriftAgent registration failed:", e)


def _run_task_with_drift(self, task_name: str, payload: dict):
    """
    Erweiterter Dispatcher:
    - behandelt zuerst die Drift-Tasks
    - für alles andere: ursprünglichen Dispatcher verwenden
    """
    warnings = []
    try:
        # Drift-spezifische Tasks zuerst abfangen
        if task_name == "drift_full":
            return self.drift_full(
                payload.get("previous"),
                payload.get("current"),
                warnings=warnings,
            )

        if task_name == "drift_profile":
            return self.drift_profile(
                payload.get("previous"),
                payload.get("current"),
                warnings=warnings,
            )

    except Exception as e:
        # Falls hier etwas schief geht, trotzdem nicht den alten Dispatcher blockieren
        warnings.append({"source": "drift_dispatch", "reason": str(e)})
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent="drift",
            task=task_name,
        )

    # Alle anderen Tasks wie bisher
    return _original_run_task(self, task_name, payload)


# Neue Drift-Methoden definieren und an Orchestrator hängen
def _drift_full(self, previous_snapshot, current_snapshot, warnings=None):
    """
    Vollständige Driftanalyse zwischen zwei Snapshots.
    """
    warnings = warnings or []
    agent_name = "drift"
    task = "drift_full"

    # Nutzung der bestehenden Safe-Call-Logik
    out, warnings, diagnostics = self._safe_call_agent(
        agent_name,
        task,
        {"previous": previous_snapshot, "current": current_snapshot},
        warnings,
    )

    if out is None:
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent=agent_name,
            task=task,
        )

    return self._wrap(
        ok=True,
        result=out.get("result"),
        warnings=warnings,
        diagnostics=diagnostics,
        agent=agent_name,
        task=task,
    )


def _drift_profile(self, previous_snapshot, current_snapshot, warnings=None):
    """
    Liefert das vollständige Drift-Profil (Detailansicht).
    """
    warnings = warnings or []
    agent_name = "drift"
    task = "drift_profile"

    out, warnings, diagnostics = self._safe_call_agent(
        agent_name,
        task,
        {"previous": previous_snapshot, "current": current_snapshot},
        warnings,
    )

    if out is None:
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent=agent_name,
            task=task,
        )

    return self._wrap(
        ok=True,
        result=out.get("result"),
        warnings=warnings,
        diagnostics=diagnostics,
        agent=agent_name,
        task=task,
    )


# Monkey-Patch aktivieren
Orchestrator._register_default_agents = _register_default_agents_with_drift
Orchestrator.run_task = _run_task_with_drift
Orchestrator.drift_full = _drift_full
Orchestrator.drift_profile = _drift_profile

# ======================================================================
# ENDE DRIFTAGENT-PATCH
# ======================================================================
# ======================================================================
# GUARDIANAGENT-INTEGRATION – EIN GUSS PATCH
# ======================================================================
"""
Agent 10 – GuardianAgent
Saham-Lab Orchestrator Erweiterung (ein Guss, zero Schnipsel)

Fügt hinzu:
    - Registrierung:    agents["guardian"]
    - Tasks:            guardian_full, guardian_profile
    - Methoden:         drift_full-Style, sicher, diagnostics-ready
"""

# ------------------------------------------------------------
# Import
# ------------------------------------------------------------
try:
    from multi_agents.guardian_agent import GuardianAgent
except ImportError:
    from guardian_agent import GuardianAgent


# ------------------------------------------------------------
# Originalmethoden sichern
# ------------------------------------------------------------
_original_register_default_agents_G = Orchestrator._register_default_agents
_original_run_task_G = Orchestrator.run_task


# ------------------------------------------------------------
# Erweiterte Agent-Registrierung
# ------------------------------------------------------------
def _register_default_agents_with_guardian(self):
    """
    Ruft zuerst die vorhandene Registrierung auf,
    ergänzt danach Agent 10: 'guardian'.
    """
    _original_register_default_agents_G(self)

    try:
        self.agents["guardian"] = GuardianAgent()
    except Exception as e:
        print("[WARN] GuardianAgent registration failed:", e)


# ------------------------------------------------------------
# Dispatcher-Erweiterung
# ------------------------------------------------------------
def _run_task_with_guardian(self, task_name: str, payload: dict):
    warnings = []

    # Guardian-Tasks zuerst abfangen
    try:
        if task_name == "guardian_full":
            return self.guardian_full(
                payload.get("agent_states"),
                payload.get("drift"),
                payload.get("coherence"),
                payload.get("anomaly"),
                payload.get("temporal"),
                payload.get("meta"),
                warnings=warnings,
            )

        if task_name == "guardian_profile":
            return self.guardian_profile(
                payload.get("agent_states"),
                payload.get("drift"),
                payload.get("coherence"),
                payload.get("anomaly"),
                payload.get("temporal"),
                payload.get("meta"),
                warnings=warnings,
            )

    except Exception as e:
        warnings.append({"source": "guardian_dispatch", "reason": str(e)})
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent="guardian",
            task=task_name,
        )

    # Alle anderen Tasks wie bisher
    return _original_run_task_G(self, task_name, payload)


# ------------------------------------------------------------
# Guardian-Methoden an Orchestrator anhängen
# ------------------------------------------------------------
def _guardian_full(
    self,
    agent_states,
    drift,
    coherence,
    anomaly,
    temporal,
    meta,
    *,
    warnings=None,
):
    warnings = warnings or []
    agent_name = "guardian"
    task = "guardian_full"

    # Safe-Call benutzt dieselbe Logik wie alle Agenten
    out, warnings, diagnostics = self._safe_call_agent(
        agent_name,
        task,
        {
            "agent_states": agent_states,
            "drift": drift,
            "coherence": coherence,
            "anomaly": anomaly,
            "temporal": temporal,
            "meta": meta,
        },
        warnings,
    )

    if out is None:
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent=agent_name,
            task=task,
        )

    return self._wrap(
        ok=True,
        result=out.get("result"),
        warnings=warnings,
        diagnostics=diagnostics,
        agent=agent_name,
        task=task,
    )


def _guardian_profile(
    self,
    agent_states,
    drift,
    coherence,
    anomaly,
    temporal,
    meta,
    *,
    warnings=None,
):
    warnings = warnings or []
    agent_name = "guardian"
    task = "guardian_profile"

    out, warnings, diagnostics = self._safe_call_agent(
        agent_name,
        task,
        {
            "agent_states": agent_states,
            "drift": drift,
            "coherence": coherence,
            "anomaly": anomaly,
            "temporal": temporal,
            "meta": meta,
        },
        warnings,
    )

    if out is None:
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent=agent_name,
            task=task,
        )

    return self._wrap(
        ok=True,
        result=out.get("result"),
        warnings=warnings,
        diagnostics=diagnostics,
        agent=agent_name,
        task=task,
    )


# ------------------------------------------------------------
# Monkey-Patching aktivieren
# ------------------------------------------------------------
Orchestrator._register_default_agents = _register_default_agents_with_guardian
Orchestrator.run_task = _run_task_with_guardian
Orchestrator.guardian_full = _guardian_full
Orchestrator.guardian_profile = _guardian_profile

# ======================================================================
# ENDE GUARDIANAGENT-PATCH
# ======================================================================
# ======================================================================
# CLUSTERAGENT-INTEGRATION – EIN GUSS PATCH
# ======================================================================
"""
Agent 13 – ClusterAgent
Saham-Lab Orchestrator Erweiterung (ein Guss, zero Schnipsel)

Fügt hinzu:
    - Registrierung:  agents["cluster"]
    - Tasks:          "cluster_full", "cluster_profile"
    - Methoden:       Orchestrator.cluster_full / cluster_profile
"""

# ------------------------------------------------------------
# Import
# ------------------------------------------------------------
try:
    from multi_agents.cluster_agent import ClusterAgent
except ImportError:
    from cluster_agent import ClusterAgent


# ------------------------------------------------------------
# Originalmethoden sichern
# ------------------------------------------------------------
_original_register_default_agents_C = Orchestrator._register_default_agents
_original_run_task_C = Orchestrator.run_task


# ------------------------------------------------------------
# Erweiterte Agent-Registrierung
# ------------------------------------------------------------
def _register_default_agents_with_cluster(self):
    """
    Ruft zuerst die vorhandene Registrierung auf,
    ergänzt danach Agent 13: 'cluster'.
    """
    _original_register_default_agents_C(self)

    try:
        self.agents["cluster"] = ClusterAgent()
    except Exception as e:
        print("[WARN] ClusterAgent registration failed:", e)


# ------------------------------------------------------------
# Dispatcher-Erweiterung
# ------------------------------------------------------------
def _run_task_with_cluster(self, task_name: str, payload: dict):
    warnings = []

    # Cluster-Tasks zuerst abfangen
    try:
        if task_name == "cluster_full":
            return self.cluster_full(
                payload.get("values"),
                payload.get("k", 3),
                warnings=warnings,
            )

        if task_name == "cluster_profile":
            return self.cluster_profile(
                payload.get("values"),
                payload.get("k", 3),
                warnings=warnings,
            )

    except Exception as e:
        warnings.append({"source": "cluster_dispatch", "reason": str(e)})
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent="cluster",
            task=task_name,
        )

    # Alle anderen Tasks wie bisher
    return _original_run_task_C(self, task_name, payload)


# ------------------------------------------------------------
# Cluster-Methoden an Orchestrator anhängen
# ------------------------------------------------------------
def _cluster_full(self, values, k=3, *, warnings=None):
    """
    Vollständige Clusteranalyse für eine Zahlenfolge.
    """
    warnings = warnings or []
    agent_name = "cluster"
    task = "cluster_full"

    out, warnings, diagnostics = self._safe_call_agent(
        agent_name,
        task,
        {"values": values, "k": k},
        warnings,
    )

    if out is None:
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent=agent_name,
            task=task,
        )

    return self._wrap(
        ok=True,
        result=out.get("result"),
        warnings=warnings,
        diagnostics=diagnostics,
        agent=agent_name,
        task=task,
    )


def _cluster_profile(self, values, k=3, *, warnings=None):
    """
    Kompakte Profilansicht der Clusterstruktur.
    """
    warnings = warnings or []
    agent_name = "cluster"
    task = "cluster_profile"

    out, warnings, diagnostics = self._safe_call_agent(
        agent_name,
        task,
        {"values": values, "k": k},
        warnings,
    )

    if out is None:
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent=agent_name,
            task=task,
        )

    return self._wrap(
        ok=True,
        result=out.get("result"),
        warnings=warnings,
        diagnostics=diagnostics,
        agent=agent_name,
        task=task,
    )


# ------------------------------------------------------------
# Monkey-Patching aktivieren
# ------------------------------------------------------------
Orchestrator._register_default_agents = _register_default_agents_with_cluster
Orchestrator.run_task = _run_task_with_cluster
Orchestrator.cluster_full = _cluster_full
Orchestrator.cluster_profile = _cluster_profile

# ======================================================================
# ENDE CLUSTERAGENT-PATCH
# ======================================================================
# ======================================================================
# HORIZONAGENT-INTEGRATION – EIN GUSS PATCH
# ======================================================================
"""
Agent 15 – HorizonAgent
Saham-Lab Orchestrator-Erweiterung (Ein Guss, zero Schnipsel)

Fügt hinzu:
    - Registrierung:  agents["horizon"]
    - Tasks:          "horizon_full", "horizon_profile", "horizon_forecast"
    - Methoden:       Orchestrator.horizon_full / horizon_profile / horizon_forecast
"""

# ------------------------------------------------------------
# Import
# ------------------------------------------------------------
try:
    from multi_agents.horizon_agent import HorizonAgent
except ImportError:
    from horizon_agent import HorizonAgent


# ------------------------------------------------------------
# Originalmethoden sichern
# ------------------------------------------------------------
_original_register_default_agents_H = Orchestrator._register_default_agents
_original_run_task_H = Orchestrator.run_task


# ------------------------------------------------------------
# Erweiterte Agent-Registrierung
# ------------------------------------------------------------
def _register_default_agents_with_horizon(self):
    """
    Ruft zuerst die vorhandene Registrierung auf,
    ergänzt danach Agent 15: 'horizon'.
    """
    _original_register_default_agents_H(self)

    try:
        self.agents["horizon"] = HorizonAgent()
    except Exception as e:
        print("[WARN] HorizonAgent registration failed:", e)


# ------------------------------------------------------------
# Dispatcher-Erweiterung
# ------------------------------------------------------------
def _run_task_with_horizon(self, task_name: str, payload: dict):
    warnings = []

    # Horizon-Tasks zuerst abfangen
    try:
        if task_name == "horizon_full":
            return self.horizon_full(
                payload.get("errors", []),
                payload.get("threshold", 1.0),
                warnings=warnings,
            )

        if task_name == "horizon_profile":
            return self.horizon_profile(
                payload.get("errors", []),
                payload.get("threshold", 1.0),
                warnings=warnings,
            )

        if task_name == "horizon_forecast":
            return self.horizon_forecast(
                payload.get("errors", []),
                payload.get("threshold", 1.0),
                warnings=warnings,
            )

    except Exception as e:
        warnings.append({"source": "horizon_dispatch", "reason": str(e)})
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent="horizon",
            task=task_name,
        )

    # Alle anderen Tasks wie bisher
    return _original_run_task_H(self, task_name, payload)


# ------------------------------------------------------------
# Horizon-Methoden an Orchestrator anhängen
# ------------------------------------------------------------
def _horizon_full(self, errors, threshold=1.0, *, warnings=None):
    """
    Vollständige Horizontanalyse für eine Fehlersequenz.
    """
    warnings = warnings or []
    agent_name = "horizon"
    task = "horizon_full"

    out, warnings, diagnostics = self._safe_call_agent(
        agent_name,
        task,
        {"errors": errors, "threshold": threshold},
        warnings,
    )

    if out is None:
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent=agent_name,
            task=task,
        )

    return self._wrap(
        ok=True,
        result=out.get("result"),
        warnings=warnings,
        diagnostics=diagnostics,
        agent=agent_name,
        task=task,
    )


def _horizon_profile(self, errors, threshold=1.0, *, warnings=None):
    """
    Kompakte Profilansicht des Horizonts (ohne Forecast).
    """
    warnings = warnings or []
    agent_name = "horizon"
    task = "horizon_profile"

    out, warnings, diagnostics = self._safe_call_agent(
        agent_name,
        task,
        {"errors": errors, "threshold": threshold},
        warnings,
    )

    if out is None:
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent=agent_name,
            task=task,
        )

    return self._wrap(
        ok=True,
        result=out.get("result"),
        warnings=warnings,
        diagnostics=diagnostics,
        agent=agent_name,
        task=task,
    )


def _horizon_forecast(self, errors, threshold=1.0, *, warnings=None):
    """
    Forecast, wann der Threshold voraussichtlich gerissen wird.
    """
    warnings = warnings or []
    agent_name = "horizon"
    task = "horizon_forecast"

    out, warnings, diagnostics = self._safe_call_agent(
        agent_name,
        task,
        {"errors": errors, "threshold": threshold},
        warnings,
    )

    if out is None:
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent=agent_name,
            task=task,
        )

    return self._wrap(
        ok=True,
        result=out.get("result"),
        warnings=warnings,
        diagnostics=diagnostics,
        agent=agent_name,
        task=task,
    )


# ------------------------------------------------------------
# Monkey-Patching aktivieren
# ------------------------------------------------------------
Orchestrator._register_default_agents = _register_default_agents_with_horizon
Orchestrator.run_task = _run_task_with_horizon
Orchestrator.horizon_full = _horizon_full
Orchestrator.horizon_profile = _horizon_profile
Orchestrator.horizon_forecast = _horizon_forecast

# ======================================================================
# ENDE HORIZONAGENT-PATCH
# ======================================================================
# ======================================================================
# TRENDAGENT-INTEGRATION – EIN GUSS PATCH
# ======================================================================
"""
Agent 18 – TrendAgent
Saham-Lab Orchestrator-Erweiterung (Ein Guss, zero Schnipsel)

Fügt hinzu:
    - Registrierung:  agents["trend"]
    - Tasks:          "trend_full", "trend_profile", "trend_forecast"
    - Methoden:       Orchestrator.trend_full / trend_profile / trend_forecast
"""

# ------------------------------------------------------------
# Import
# ------------------------------------------------------------
try:
    from multi_agents.trend_agent import TrendAgent
except ImportError:
    from trend_agent import TrendAgent


# ------------------------------------------------------------
# Originalmethoden sichern
# ------------------------------------------------------------
_original_register_default_agents_T = Orchestrator._register_default_agents
_original_run_task_T = Orchestrator.run_task


# ------------------------------------------------------------
# Erweiterte Agent-Registrierung
# ------------------------------------------------------------
def _register_default_agents_with_trend(self):
    """
    Ruft zuerst die vorhandene Registrierung auf,
    ergänzt danach Agent 18: 'trend'.
    """
    _original_register_default_agents_T(self)

    try:
        self.agents["trend"] = TrendAgent()
    except Exception as e:
        print("[WARN] TrendAgent registration failed:", e)


# ------------------------------------------------------------
# Dispatcher-Erweiterung
# ------------------------------------------------------------
def _run_task_with_trend(self, task_name: str, payload: dict):
    warnings = []

    # Trend-Tasks zuerst abfangen
    try:
        if task_name == "trend_full":
            return self.trend_full(
                payload.get("values", []),
                warnings=warnings,
            )

        if task_name == "trend_profile":
            return self.trend_profile(
                payload.get("values", []),
                warnings=warnings,
            )

        if task_name == "trend_forecast":
            return self.trend_forecast(
                payload.get("values", []),
                warnings=warnings,
            )

    except Exception as e:
        warnings.append({"source": "trend_dispatch", "reason": str(e)})
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent="trend",
            task=task_name,
        )

    # Alle anderen Tasks wie bisher
    return _original_run_task_T(self, task_name, payload)


# ------------------------------------------------------------
# Trend-Methoden an Orchestrator anhängen
# ------------------------------------------------------------
def _trend_full(self, values, *, warnings=None):
    """
    Vollständige Trendanalyse (Multi-Window + Phase + Score).
    """
    warnings = warnings or []
    agent_name = "trend"
    task = "trend_full"

    out, warnings, diagnostics = self._safe_call_agent(
        agent_name,
        task,
        {"values": values},
        warnings,
    )

    if out is None:
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent=agent_name,
            task=task,
        )

    return self._wrap(
        ok=True,
        result=out.get("result"),
        warnings=warnings,
        diagnostics=diagnostics,
        agent=agent_name,
        task=task,
    )


def _trend_profile(self, values, *, warnings=None):
    """
    Kompakte Trendprofil-Sicht (Regime, Phase, Score).
    """
    warnings = warnings or []
    agent_name = "trend"
    task = "trend_profile"

    out, warnings, diagnostics = self._safe_call_agent(
        agent_name,
        task,
        {"values": values},
        warnings,
    )

    if out is None:
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent=agent_name,
            task=task,
        )

    return self._wrap(
        ok=True,
        result=out.get("result"),
        warnings=warnings,
        diagnostics=diagnostics,
        agent=agent_name,
        task=task,
    )


def _trend_forecast(self, values, *, warnings=None):
    """
    Forecast des Trends (Forward-Projektion auf Basis der TrendEngine).
    """
    warnings = warnings or []
    agent_name = "trend"
    task = "trend_forecast"

    out, warnings, diagnostics = self._safe_call_agent(
        agent_name,
        task,
        {"values": values},
        warnings,
    )

    if out is None:
        return self._wrap(
            ok=False,
            result=None,
            warnings=warnings,
            diagnostics=None,
            agent=agent_name,
            task=task,
        )

    return self._wrap(
        ok=True,
        result=out.get("result"),
        warnings=warnings,
        diagnostics=diagnostics,
        agent=agent_name,
        task=task,
    )


# ------------------------------------------------------------
# Monkey-Patching aktivieren
# ------------------------------------------------------------
Orchestrator._register_default_agents = _register_default_agents_with_trend
Orchestrator.run_task = _run_task_with_trend
Orchestrator.trend_full = _trend_full
Orchestrator.trend_profile = _trend_profile
Orchestrator.trend_forecast = _trend_forecast

# ======================================================================
# ENDE TRENDAGENT-PATCH
# ======================================================================
# ======================================================================
# FORECASTAGENT-INTEGRATION – EIN GUSS PATCH (Agent 12)
# ======================================================================
"""
Agent 12 – ForecastAgent
Saham-Lab Orchestrator-Erweiterung (Ein Guss, HQ-Level)

Fügt hinzu:
    - Registrierung:  agents["forecast"]
    - Tasks:
         * forecast_full
         * forecast_profile
         * forecast_scenarios
    - Methoden:
         * Orchestrator.forecast_full(...)
         * Orchestrator.forecast_profile(...)
         * Orchestrator.forecast_scenarios(...)
"""

# ------------------------------------------------------------
# Import ForecastAgent
# ------------------------------------------------------------
try:
    from multi_agents.forecast_agent import ForecastAgent
except ImportError:
    from forecast_agent import ForecastAgent


# ------------------------------------------------------------
# Originalmethoden sichern
# ------------------------------------------------------------
_original_register_default_agents_FC = Orchestrator._register_default_agents
_original_run_task_FC = Orchestrator.run_task


# ------------------------------------------------------------
# Erweiterte Agent-Registrierung
# ------------------------------------------------------------
def _register_default_agents_with_forecast(self):
    """
    Ruft zuerst die ursprüngliche Registrierung auf,
    ergänzt danach Agent 12: 'forecast'.
    """
    _original_register_default_agents_FC(self)

    try:
        self.agents["forecast"] = ForecastAgent()
    except Exception as e:
        print("[WARN] ForecastAgent registration failed:", e)


# ------------------------------------------------------------
# Dispatcher-Erweiterung (Task-Routing)
# ------------------------------------------------------------
def _run_task_with_forecast(self, task_name: str, payload: dict):
    warnings = []

    # Neue Forecast-Tasks abfangen
    try:
        if task_name == "forecast_full":
            return self.forecast_full(
                payload.get("values", []),
                payload.get("horizon", 10),
                warnings=warnings,
            )

        if task_name == "forecast_profile":
            return self.forecast_profile(
                payload.get("values", []),
                payload.get("horizon", 10),
                warnings=warnings,
            )

        if task_name == "forecast_scenarios":
            return self.forecast_scenarios(
                payload.get("values", []),
                payload.get("horizon", 10),
                warnings=warnings,
            )

    except Exception as e:
        warnings.append({"source": "forecast_dispatch", "reason": str(e)})
        return self._wrap(
            ok=False,
            result=None,
            diagnostics=None,
            warnings=warnings,
            agent="forecast",
            task=task_name,
        )

    # Alles andere geht an den Original-Dispatcher
    return _original_run_task_FC(self, task_name, payload)


# ------------------------------------------------------------
# Forecast-Methoden an Orchestrator anhängen
# ------------------------------------------------------------
def _forecast_full(self, values, horizon=10, *, warnings=None):
    warnings = warnings or []
    agent = "forecast"
    task = "forecast_full"

    out, warnings, diagnostics = self._safe_call_agent(
        agent,
        task,
        {"values": values, "horizon": horizon},
        warnings,
    )

    if out is None:
        return self._wrap(False, None, warnings, None, agent, task)

    return self._wrap(True, out["result"], warnings, diagnostics, agent, task)


def _forecast_profile(self, values, horizon=10, *, warnings=None):
    warnings = warnings or []
    agent = "forecast"
    task = "forecast_profile"

    out, warnings, diagnostics = self._safe_call_agent(
        agent,
        task,
        {"values": values, "horizon": horizon},
        warnings,
    )

    if out is None:
        return self._wrap(False, None, warnings, None, agent, task)

    return self._wrap(True, out["result"], warnings, diagnostics, agent, task)


def _forecast_scenarios(self, values, horizon=10, *, warnings=None):
    warnings = warnings or []
    agent = "forecast"
    task = "forecast_scenarios"

    out, warnings, diagnostics = self._safe_call_agent(
        agent,
        task,
        {"values": values, "horizon": horizon},
        warnings,
    )

    if out is None:
        return self._wrap(False, None, warnings, None, agent, task)

    return self._wrap(True, out["result"], warnings, diagnostics, agent, task)


# ------------------------------------------------------------
# Monkey-Patching aktivieren
# ------------------------------------------------------------
Orchestrator._register_default_agents = _register_default_agents_with_forecast
Orchestrator.run_task = _run_task_with_forecast
Orchestrator.forecast_full = _forecast_full
Orchestrator.forecast_profile = _forecast_profile
Orchestrator.forecast_scenarios = _forecast_scenarios

# ======================================================================
# ENDE FORECASTAGENT-PATCH
# ======================================================================
