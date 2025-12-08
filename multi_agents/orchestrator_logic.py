"""
orchestrator_logic.py – Saham-Lab Orchestrator 0.8 (HQ Titanium Edition)

Zweck:
    Zentrale Steuerinstanz für alle Saham-Lab-Agenten in der Sandbox.

Agenten (Stand):
    1  PatternCore       (patterncore)
    2  StructureWeaver   (structureweaver)
    3  PointEngine       (pointengine)
    4  PointDynamics     (pointdynamics)
    5  TemporalSynth     (temporalsynth)
    6  CoherenceAgent    (coherence)
    7  AnomalyAgent      (anomaly)
    8  FusionAgent       (fusion)
    9  DriftAgent        (drift)
    10 GuardianAgent     (guardian)
    11 DiagnosticCore    (diagnostic_core) – optional
    12 ForecastAgent     (forecast)
    13 ClusterAgent      (cluster)
    14 SignatureAgent    (signature)
    15 HorizonAgent      (horizon)
    16 TrendAgent        (trend)

Wichtige Methoden:
    - list_agents()
    - run_task(task_name, payload)
    - patterncore_summary(...)
    - temporal_full(...)
    - cluster_full / cluster_profile(...)
    - horizon_full / horizon_profile / horizon_forecast(...)
    - trend_full / trend_profile / trend_forecast(...)
    - forecast_full / forecast_profile / forecast_scenarios(...)
    - signature_build(...)
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

# ------------------------------------------------------------
# Agent-Imports mit fallback
# ------------------------------------------------------------
# Core-Analyse-Agenten
try:
    from .patterncore import PatternCore
except ImportError:  # pragma: no cover
    from patterncore import PatternCore  # type: ignore

try:
    from .structureweaver import StructureWeaver
except ImportError:  # pragma: no cover
    from structureweaver import StructureWeaver  # type: ignore

try:
    from .pointengine import PointEngine
except ImportError:  # pragma: no cover
    from pointengine import PointEngine  # type: ignore

try:
    from .pointdynamics import PointDynamics
except ImportError:  # pragma: no cover
    from pointdynamics import PointDynamics  # type: ignore

try:
    from .temporalsynth import TemporalSynth
except ImportError:  # pragma: no cover
    from temporalsynth import TemporalSynth  # type: ignore

# Meta-/Qualitäts-/Kontrollagenten
try:
    from .coherence_agent import CoherenceAgent
except ImportError:  # pragma: no cover
    from coherence_agent import CoherenceAgent  # type: ignore

try:
    from .anomaly_agent import AnomalyAgent
except ImportError:  # pragma: no cover
    from anomaly_agent import AnomalyAgent  # type: ignore

try:
    from .fusion_agent import FusionAgent
except ImportError:  # pragma: no cover
    from fusion_agent import FusionAgent  # type: ignore

try:
    from .drift_agent import DriftAgent
except ImportError:  # pragma: no cover
    from drift_agent import DriftAgent  # type: ignore

try:
    from .guardian_agent import GuardianAgent
except ImportError:  # pragma: no cover
    from guardian_agent import GuardianAgent  # type: ignore

try:
    from .cluster_agent import ClusterAgent
except ImportError:  # pragma: no cover
    from cluster_agent import ClusterAgent  # type: ignore

try:
    from .horizon_agent import HorizonAgent
except ImportError:  # pragma: no cover
    from horizon_agent import HorizonAgent  # type: ignore

try:
    from .trend_agent import TrendAgent
except ImportError:  # pragma: no cover
    from trend_agent import TrendAgent  # type: ignore

try:
    from .forecast_agent import ForecastAgent
except ImportError:  # pragma: no cover
    from forecast_agent import ForecastAgent  # type: ignore

try:
    from .signature_agent import SignatureAgent
except ImportError:  # pragma: no cover
    from signature_agent import SignatureAgent  # type: ignore

# Optionale Meta-Komponenten (wenn vorhanden)
try:
    from .guardian_gate import GuardianGate
except ImportError:  # pragma: no cover
    try:
        from guardian_gate import GuardianGate  # type: ignore
    except ImportError:  # pragma: no cover
        GuardianGate = None  # type: ignore

try:
    from .diagnostic_core import DiagnosticCore
except ImportError:  # pragma: no cover
    try:
        from diagnostic_core import DiagnosticCore  # type: ignore
    except ImportError:  # pragma: no cover
        DiagnosticCore = None  # type: ignore


# ======================================================================
# Orchestrator-Klasse
# ======================================================================
class Orchestrator:
    """
    Zentrale Dirigentenklasse des Saham-Lab-Systems.

    Verantwortlichkeiten:
        - Verwaltung und Instanziierung aller Agenten
        - Sichere Agenten-Aufrufe
        - Einheitliche Rückgabe (ok / result / warnings / diagnostics / agent / task)
        - Task-Routing (run_task)
        - High-Level-Komfort-Methoden (temporal_full, forecast_full, ...)
    """

    # ------------------------------------------------------------
    # Initialisierung
    # ------------------------------------------------------------
    def __init__(self) -> None:
        self.agents: Dict[str, Any] = {}
        self.guardian_gate: Optional[Any] = None
        self.diagnostic_core: Optional[Any] = None

        self._register_default_agents()
        self._register_meta_components()
        self._build_task_map()

    # ------------------------------------------------------------
    # Agent-Registrierung
    # ------------------------------------------------------------
    def _register_default_agents(self) -> None:
        """Instanziert alle verfügbaren Agenten."""

        # Kernagenten
        try:
            self.agents["patterncore"] = PatternCore()
        except Exception as e:  # pragma: no cover
            print("[WARN] PatternCore init failed:", e)

        try:
            self.agents["structureweaver"] = StructureWeaver()
        except Exception as e:
            print("[WARN] StructureWeaver init failed:", e)

        try:
            self.agents["pointengine"] = PointEngine()
        except Exception as e:
            print("[WARN] PointEngine init failed:", e)

        try:
            self.agents["pointdynamics"] = PointDynamics()
        except Exception as e:
            print("[WARN] PointDynamics init failed:", e)

        try:
            self.agents["temporalsynth"] = TemporalSynth()
        except Exception as e:
            print("[WARN] TemporalSynth init failed:", e)

        # Meta-/Qualitätsagenten
        try:
            self.agents["coherence"] = CoherenceAgent()
        except Exception as e:
            print("[WARN] CoherenceAgent init failed:", e)

        try:
            self.agents["anomaly"] = AnomalyAgent()
        except Exception as e:
            print("[WARN] AnomalyAgent init failed:", e)

        try:
            self.agents["fusion"] = FusionAgent()
        except Exception as e:
            print("[WARN] FusionAgent init failed:", e)

        try:
            self.agents["drift"] = DriftAgent()
        except Exception as e:
            print("[WARN] DriftAgent init failed:", e)

        try:
            self.agents["guardian"] = GuardianAgent()
        except Exception as e:
            print("[WARN] GuardianAgent init failed:", e)

        try:
            self.agents["cluster"] = ClusterAgent()
        except Exception as e:
            print("[WARN] ClusterAgent init failed:", e)

        try:
            self.agents["horizon"] = HorizonAgent()
        except Exception as e:
            print("[WARN] HorizonAgent init failed:", e)

        try:
            self.agents["trend"] = TrendAgent()
        except Exception as e:
            print("[WARN] TrendAgent init failed:", e)

        try:
            self.agents["forecast"] = ForecastAgent()
        except Exception as e:
            print("[WARN] ForecastAgent init failed:", e)

        try:
            self.agents["signature"] = SignatureAgent()
        except Exception as e:
            print("[WARN] SignatureAgent init failed:", e)

    # ------------------------------------------------------------
    # Meta-Komponenten
    # ------------------------------------------------------------
    def _register_meta_components(self) -> None:
        """GuardianGate + DiagnosticCore, falls verfügbar."""
        if GuardianGate is not None:
            try:
                self.guardian_gate = GuardianGate()
            except Exception as e:  # pragma: no cover
                print("[WARN] GuardianGate init failed:", e)

        if DiagnosticCore is not None:
            try:
                self.diagnostic_core = DiagnosticCore()
            except Exception as e:  # pragma: no cover
                print("[WARN] DiagnosticCore init failed:", e)

    # ------------------------------------------------------------
    # Task-Mapping
    # ------------------------------------------------------------
    def _build_task_map(self) -> None:
        """
        Mapping von Tasknamen zu Agentennamen.
        run_task() benutzt diese Map als primären Router.
        """
        self._task_to_agent: Dict[str, str] = {
            # PatternCore
            "patterncore_summary": "patterncore",

            # TemporalSynth
            "temporal_full": "temporalsynth",
            "temporal_profile": "temporalsynth",

            # Cluster
            "cluster_full": "cluster",
            "cluster_profile": "cluster",

            # Horizon
            "horizon_full": "horizon",
            "horizon_profile": "horizon",
            "horizon_forecast": "horizon",

            # Trend
            "trend_full": "trend",
            "trend_profile": "trend",
            "trend_forecast": "trend",

            # Forecast
            "forecast_full": "forecast",
            "forecast_profile": "forecast",
            "forecast_scenarios": "forecast",

            # Signature
            "signature_build": "signature",
        }

    # ------------------------------------------------------------
    # Öffentliche Utility-Methoden
    # ------------------------------------------------------------
    def list_agents(self) -> List[str]:
        """Gibt eine sortierte Liste aller registrierten Agentennamen zurück."""
        return sorted(self.agents.keys())

    # ------------------------------------------------------------
    # Einheitlicher Rückgabe-Wrapper (HQ-Standard)
    # ------------------------------------------------------------
    def _wrap(
        self,
        ok: bool,
        result: Any,
        warnings: Optional[List[Dict[str, Any]]],
        diagnostics: Any,
        agent: str,
        task: str,
    ) -> Dict[str, Any]:
        """
        Einheitliche Rückgabe für alle Agenten und Tasks.
        Wird von allen High-Level-Methoden und von run_task verwendet.
        """
        return {
            "ok": bool(ok),
            "result": result,
            "warnings": warnings or [],
            "diagnostics": diagnostics,
            "agent": agent,
            "task": task,
        }

    # ------------------------------------------------------------
    # Sicherer Agentenaufruf
    # ------------------------------------------------------------
    def _safe_call_agent(
        self,
        agent_name: str,
        task: str,
        payload: Dict[str, Any],
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], Any]:
        """
        Kapselt Agentenaufrufe:
            - prüft Existenz des Agenten
            - fängt Exceptions ab
            - liefert (out, warnings, diagnostics)
        """
        warnings = warnings or []
        diagnostics = None

        agent = self.agents.get(agent_name)
        if agent is None:
            warnings.append(
                {"source": "orchestrator", "reason": f"agent '{agent_name}' not available"}
            )
            return None, warnings, diagnostics

        try:
            out = agent.run(task, payload, with_debug=True, with_diagnostics=True)
            diagnostics = out.get("diagnostics")
            return out, warnings, diagnostics
        except Exception as e:  # pragma: no cover
            warnings.append({"source": agent_name, "reason": repr(e)})
            return None, warnings, diagnostics

    # ------------------------------------------------------------
    # Zentrale Task-Methode
    # ------------------------------------------------------------
    def run_task(self, task_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Allgemeiner Task-Router.
        Basiert primär auf self._task_to_agent,
        ruft den jeweiligen Agenten mit identischem Tasknamen auf.
        """
        agent_name = self._task_to_agent.get(task_name)
        warnings: List[Dict[str, Any]] = []
        diagnostics = None

        if agent_name is None:
            warnings.append(
                {"source": "orchestrator", "reason": f"unknown task '{task_name}'"}
            )
            return self._wrap(False, None, warnings, diagnostics, "n/a", task_name)

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name, task_name, payload, warnings
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task_name)

        # Agent-Resultat extrahieren
        result = out.get("result")
        ok = out.get("ok", True)
        return self._wrap(ok, result, warnings, diagnostics, agent_name, task_name)

    # ==================================================================
    # High-Level Komfortmethoden (für direkte Nutzung im Lab)
    # ==================================================================

    # -----------------------------
    # PatternCore
    # -----------------------------
    def patterncore_summary(
        self,
        values: List[float],
        *,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Komfortmethode für PatternCore – Musterzusammenfassung einer Zahlenfolge.
        """
        warnings = warnings or []
        agent_name = "patterncore"
        task = "patterncore_summary"

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            {"values": values},
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)

    # -----------------------------
    # TemporalSynth
    # -----------------------------
    def temporal_full(
        self,
        patterns: List[float],
        structures: List[float],
        points: List[float],
        motion: List[float],
        *,
        with_debug: bool = True,
        with_diagnostics: bool = True,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Vollständige Temporalanalyse über alle vier Ebenen.
        """
        warnings = warnings or []
        agent_name = "temporalsynth"
        task = "temporal_full"

        payload = {
            "patterns": patterns,
            "structures": structures,
            "points": points,
            "motion": motion,
            "with_debug": with_debug,
            "with_diagnostics": with_diagnostics,
        }

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            payload,
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)

    # -----------------------------
    # ClusterAgent
    # -----------------------------
    def cluster_full(
        self,
        values: List[float],
        k: int = 3,
        *,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        agent_name = "cluster"
        task = "cluster_full"
        warnings = warnings or []

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            {"values": values, "k": k},
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)

    def cluster_profile(
        self,
        values: List[float],
        k: int = 3,
        *,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        agent_name = "cluster"
        task = "cluster_profile"
        warnings = warnings or []

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            {"values": values, "k": k},
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)

    # -----------------------------
    # HorizonAgent
    # -----------------------------
    def horizon_full(
        self,
        errors: List[float],
        threshold: float = 1.0,
        *,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        agent_name = "horizon"
        task = "horizon_full"
        warnings = warnings or []

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            {"errors": errors, "threshold": threshold},
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)

    def horizon_profile(
        self,
        errors: List[float],
        threshold: float = 1.0,
        *,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        agent_name = "horizon"
        task = "horizon_profile"
        warnings = warnings or []

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            {"errors": errors, "threshold": threshold},
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)

    def horizon_forecast(
        self,
        errors: List[float],
        threshold: float = 1.0,
        *,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        agent_name = "horizon"
        task = "horizon_forecast"
        warnings = warnings or []

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            {"errors": errors, "threshold": threshold},
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)

    # -----------------------------
    # TrendAgent
    # -----------------------------
    def trend_full(
        self,
        values: List[float],
        *,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        agent_name = "trend"
        task = "trend_full"
        warnings = warnings or []

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            {"values": values},
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)

    def trend_profile(
        self,
        values: List[float],
        *,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        agent_name = "trend"
        task = "trend_profile"
        warnings = warnings or []

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            {"values": values},
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)

    def trend_forecast(
        self,
        values: List[float],
        *,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        agent_name = "trend"
        task = "trend_forecast"
        warnings = warnings or []

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            {"values": values},
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)

    # -----------------------------
    # ForecastAgent
    # -----------------------------
    def forecast_full(
        self,
        values: List[float],
        horizon: int = 10,
        *,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        agent_name = "forecast"
        task = "forecast_full"
        warnings = warnings or []

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            {"values": values, "horizon": horizon},
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)

    def forecast_profile(
        self,
        values: List[float],
        horizon: int = 10,
        *,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        agent_name = "forecast"
        task = "forecast_profile"
        warnings = warnings or []

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            {"values": values, "horizon": horizon},
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)

    def forecast_scenarios(
        self,
        values: List[float],
        horizon: int = 10,
        *,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        agent_name = "forecast"
        task = "forecast_scenarios"
        warnings = warnings or []

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            {"values": values, "horizon": horizon},
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)

    # -----------------------------
    # SignatureAgent
    # -----------------------------
    def signature_build(
        self,
        profile: Dict[str, Any],
        *,
        warnings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        agent_name = "signature"
        task = "signature_build"
        warnings = warnings or []

        out, warnings, diagnostics = self._safe_call_agent(
            agent_name,
            task,
            {"profile": profile},
            warnings,
        )

        if out is None:
            return self._wrap(False, None, warnings, diagnostics, agent_name, task)

        return self._wrap(True, out.get("result"), warnings, diagnostics, agent_name, task)
