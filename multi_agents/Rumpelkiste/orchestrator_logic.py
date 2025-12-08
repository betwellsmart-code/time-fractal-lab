"""
Orchestrator 0.5 – Mode C (Samy-Power, voll-autonom)
----------------------------------------------------

Features:
- Agent-Registry (TemporalSynth, PatternCore, StructureWeaver, PointEngine, PointDynamics)
- Sanity 1.0 (guardian_gate): operative Gates vor/nach Agenten
- Sanity 2.0 (diagnostic_core): optionale Diagnoseebene
- Hybrid-Modus:
    - Guardian stoppt NICHT hart, sondern liefert Gate-Resultate + Warnings
    - Orchestrator entscheidet, wie weitergemacht wird (Mode C)
- Convenience-Methoden für häufige Pipelines
- Task-Interface (submit/run_task/run_queue) – einfache Multi-Task-Schicht
"""

from typing import Any, Dict, List, Optional

try:
    # Paketvariante
    from multi_agents.temporalsynth import TemporalSynth
    from multi_agents.patterncore import PatternCore
    from multi_agents.structureweaver import StructureWeaver
    from multi_agents.pointengine import PointEngine
    from multi_agents.pointdynamics import PointDynamics
    from multi_agents.guardian_gate import (
        gate_array_input,
        gate_multiagent_input,
        gate_agent_output,
    )
    from multi_agents.diagnostic_core import full_diagnostic
except ImportError:
    # Fallback: lokaler Import
    from temporalsynth import TemporalSynth
    from patterncore import PatternCore
    from structureweaver import StructureWeaver
    from pointengine import PointEngine
    from pointdynamics import PointDynamics
    from guardian_gate import (
        gate_array_input,
        gate_multiagent_input,
        gate_agent_output,
    )
    from diagnostic_core import full_diagnostic


class Orchestrator:
    """
    Orchestrator 0.5 – Mode C.

    - Voll-autonomer Modus:
        - nutzt Guardian-Gates
        - nutzt optional Diagnostics
        - versucht, bei leicht fehlerhaften Inputs dennoch Ergebnisse zu liefern
    - einfache Task-Queue integriert.
    """

    def __init__(self, version: str = "0.5-modeC") -> None:
        self.version = version
        self.agents: Dict[str, Any] = {}
        self.tasks: List[Dict[str, Any]] = []  # simple in-memory queue

        self._register_default_agents()

    # ------------------------------------------------------------------
    # Agent-Registry
    # ------------------------------------------------------------------
    def _register_default_agents(self) -> None:
        errors: Dict[str, Any] = {}

        try:
            self.agents["temporalsynth"] = TemporalSynth()
        except Exception as e:
            errors["temporalsynth"] = e

        try:
            self.agents["patterncore"] = PatternCore()
        except Exception as e:
            errors["patterncore"] = e

        try:
            self.agents["structureweaver"] = StructureWeaver()
        except Exception as e:
            errors["structureweaver"] = e

        try:
            self.agents["pointengine"] = PointEngine()
        except Exception as e:
            errors["pointengine"] = e

        try:
            self.agents["pointdynamics"] = PointDynamics()
        except Exception as e:
            errors["pointdynamics"] = e

        # Fehler intern merken (könnten später geloggt werden)
        self.agent_errors = errors

    def list_agents(self) -> List[str]:
        return [k for k in self.agents.keys()]

    def has_agent(self, name: str) -> bool:
        return name in self.agents

    # ------------------------------------------------------------------
    # Ergebniswrapper
    # ------------------------------------------------------------------
    def _wrap(
        self,
        *,
        ok: bool,
        result: Any,
        warnings: List[Dict[str, Any]],
        diagnostics: Optional[Dict[str, Any]] = None,
        agent: Optional[str] = None,
        task: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "ok": ok,
            "result": result,
            "warnings": warnings,
            "diagnostics": diagnostics,
            "meta": {
                "orchestrator_version": self.version,
                "agent": agent,
                "task": task,
            },
        }

    # ------------------------------------------------------------------
    # High-Level: TemporalSynth – Full Pipeline
    # ------------------------------------------------------------------
    def temporal_full(
        self,
        patterns: Any,
        structures: Any,
        points: Any,
        motion: Any,
        *,
        with_debug: bool = True,
        with_diagnostics: bool = True,
    ) -> Dict[str, Any]:
        warnings: List[Dict[str, Any]] = []
        diagnostics: Optional[Dict[str, Any]] = None
        agent_name = "temporalsynth"
        task_name = "temporal_full"

        # Guardian-Gate (Input)
        gate = gate_multiagent_input(
            {
                "patterns": patterns,
                "structures": structures,
                "points": points,
                "motion": motion,
            },
            agent=agent_name,
            task=task_name,
            keys=["patterns", "structures", "points", "motion"],
        )
        if not gate["ok"]:
            warnings.append(
                {
                    "source": "guardian_gate",
                    "where": gate["where"],
                    "reason": gate["reason"],
                    "details": gate.get("details", {}),
                }
            )

        if not self.has_agent(agent_name):
            warnings.append(
                {
                    "source": "orchestrator",
                    "where": "agent_lookup",
                    "reason": f"Agent '{agent_name}' not available.",
                }
            )
            return self._wrap(
                ok=False,
                result=None,
                warnings=warnings,
                diagnostics=None,
                agent=agent_name,
                task=task_name,
            )

        ts: TemporalSynth = self.agents[agent_name]  # type: ignore[assignment]

        # Agent-Aufruf
        try:
            out = ts.full_pipeline(
                patterns,
                structures,
                points,
                motion,
                with_debug=with_debug,
            )
        except Exception as e:
            warnings.append(
                {
                    "source": "agent",
                    "where": "call",
                    "reason": "Exception in TemporalSynth.full_pipeline",
                    "exception": str(e),
                }
            )
            return self._wrap(
                ok=False,
                result=None,
                warnings=warnings,
                diagnostics=None,
                agent=agent_name,
                task=task_name,
            )

        # Guardian-Gate (Output)
        gate_out = gate_agent_output(out, agent=agent_name, task=task_name)
        if not gate_out["ok"]:
            warnings.append(
                {
                    "source": "guardian_gate",
                    "where": gate_out["where"],
                    "reason": gate_out["reason"],
                    "details": gate_out.get("details", {}),
                }
            )

        # Optional: Diagnostics 2.0
        if with_diagnostics and isinstance(out, dict):
            try:
                diagnostics = full_diagnostic(
                    agent=agent_name,
                    task=task_name,
                    output=out,
                    patterns=list(patterns),
                    structures=list(structures),
                    points=list(points),
                    motion=list(motion),
                )
            except Exception as e:
                warnings.append(
                    {
                        "source": "diagnostic_core",
                        "where": "call",
                        "reason": "Exception in full_diagnostic",
                        "exception": str(e),
                    }
                )

        return self._wrap(
            ok=True,
            result=out,
            warnings=warnings,
            diagnostics=diagnostics,
            agent=agent_name,
            task=task_name,
        )

    # ------------------------------------------------------------------
    # Convenience-Layer für die anderen Agenten
    # ------------------------------------------------------------------
    def _run_simple_agent_on_seq(
        self,
        *,
        agent_name: str,
        task_name: str,
        seq: Any,
        with_diagnostics: bool = False,
    ) -> Dict[str, Any]:
        warnings: List[Dict[str, Any]] = []
        diagnostics: Optional[Dict[str, Any]] = None

        gate_in = gate_array_input(seq, agent=agent_name, task=task_name)
        if not gate_in["ok"]:
            warnings.append(
                {
                    "source": "guardian_gate",
                    "where": gate_in["where"],
                    "reason": gate_in["reason"],
                    "details": gate_in.get("details", {}),
                }
            )

        if not self.has_agent(agent_name):
            warnings.append(
                {
                    "source": "orchestrator",
                    "where": "agent_lookup",
                    "reason": f"Agent '{agent_name}' not available.",
                }
            )
            return self._wrap(
                ok=False,
                result=None,
                warnings=warnings,
                diagnostics=None,
                agent=agent_name,
                task=task_name,
            )

        agent = self.agents[agent_name]

        if not hasattr(agent, "run"):
            warnings.append(
                {
                    "source": "orchestrator",
                    "where": "agent_interface",
                    "reason": f"Agent '{agent_name}' has no .run() method.",
                }
            )
            return self._wrap(
                ok=False,
                result=None,
                warnings=warnings,
                diagnostics=None,
                agent=agent_name,
                task=task_name,
            )

        try:
            out = agent.run(task_name, {"data": seq})
        except Exception as e:
            warnings.append(
                {
                    "source": "agent",
                    "where": "call",
                    "reason": f"Exception in {agent_name}.run('{task_name}', ...)",
                    "exception": str(e),
                }
            )
            return self._wrap(
                ok=False,
                result=None,
                warnings=warnings,
                diagnostics=None,
                agent=agent_name,
                task=task_name,
            )

        gate_out = gate_agent_output(out, agent=agent_name, task=task_name)
        if not gate_out["ok"]:
            warnings.append(
                {
                    "source": "guardian_gate",
                    "where": gate_out["where"],
                    "reason": gate_out["reason"],
                    "details": gate_out.get("details", {}),
                }
            )

        if with_diagnostics and isinstance(out, dict):
            try:
                diagnostics = full_diagnostic(
                    agent=agent_name,
                    task=task_name,
                    output=out,
                )
            except Exception as e:
                warnings.append(
                    {
                        "source": "diagnostic_core",
                        "where": "call",
                        "reason": "Exception in full_diagnostic",
                        "exception": str(e),
                    }
                )

        return self._wrap(
            ok=True,
            result=out,
            warnings=warnings,
            diagnostics=diagnostics,
            agent=agent_name,
            task=task_name,
        )

    # PatternCore
    def patterncore_summary(self, seq: Any, *, with_diagnostics: bool = False) -> Dict[str, Any]:
        return self._run_simple_agent_on_seq(
            agent_name="patterncore",
            task_name="pattern_summary",
            seq=seq,
            with_diagnostics=with_diagnostics,
        )

    # StructureWeaver
    def structureweaver_summary(self, seq: Any, *, with_diagnostics: bool = False) -> Dict[str, Any]:
        return self._run_simple_agent_on_seq(
            agent_name="structureweaver",
            task_name="structure_summary",
            seq=seq,
            with_diagnostics=with_diagnostics,
        )

    # PointEngine
    def pointengine_summary(self, seq: Any, *, with_diagnostics: bool = False) -> Dict[str, Any]:
        return self._run_simple_agent_on_seq(
            agent_name="pointengine",
            task_name="point_summary",
            seq=seq,
            with_diagnostics=with_diagnostics,
        )

    # PointDynamics
    def pointdynamics_full(self, seq: Any, *, with_diagnostics: bool = False) -> Dict[str, Any]:
        return self._run_simple_agent_on_seq(
            agent_name="pointdynamics",
            task_name="dynamics_full",
            seq=seq,
            with_diagnostics=with_diagnostics,
        )

    # ------------------------------------------------------------------
    # Generische Run-Schnittstelle
    # ------------------------------------------------------------------
    def run_agent(
        self,
        agent_name: str,
        task_name: str,
        payload: Dict[str, Any],
        *,
        with_diagnostics: bool = False,
    ) -> Dict[str, Any]:
        """
        Generische Agentensteuerung – für zukünftige Erweiterungen.
        Erwartet, dass der Agent eine .run(task, payload)-Methode hat.
        """
        warnings: List[Dict[str, Any]] = []
        diagnostics: Optional[Dict[str, Any]] = None

        if not self.has_agent(agent_name):
            warnings.append(
                {
                    "source": "orchestrator",
                    "where": "agent_lookup",
                    "reason": f"Agent '{agent_name}' not available.",
                }
            )
            return self._wrap(
                ok=False,
                result=None,
                warnings=warnings,
                diagnostics=None,
                agent=agent_name,
                task=task_name,
            )

        agent = self.agents[agent_name]
        if not hasattr(agent, "run"):
            warnings.append(
                {
                    "source": "orchestrator",
                    "where": "agent_interface",
                    "reason": f"Agent '{agent_name}' has no .run() method.",
                }
            )
            return self._wrap(
                ok=False,
                result=None,
                warnings=warnings,
                diagnostics=None,
                agent=agent_name,
                task=task_name,
            )

        try:
            out = agent.run(task_name, payload)  # type: ignore[call-arg]
        except Exception as e:
            warnings.append(
                {
                    "source": "agent",
                    "where": "call",
                    "reason": f"Exception in {agent_name}.run('{task_name}', ...)",
                    "exception": str(e),
                }
            )
            return self._wrap(
                ok=False,
                result=None,
                warnings=warnings,
                diagnostics=None,
                agent=agent_name,
                task=task_name,
            )

        gate_out = gate_agent_output(out, agent=agent_name, task=task_name)
        if not gate_out["ok"]:
            warnings.append(
                {
                    "source": "guardian_gate",
                    "where": gate_out["where"],
                    "reason": gate_out["reason"],
                    "details": gate_out.get("details", {}),
                }
            )

        if with_diagnostics and isinstance(out, dict):
            try:
                diagnostics = full_diagnostic(
                    agent=agent_name,
                    task=task_name,
                    output=out,
                )
            except Exception as e:
                warnings.append(
                    {
                        "source": "diagnostic_core",
                        "where": "call",
                        "reason": "Exception in full_diagnostic",
                        "exception": str(e),
                    }
                )

        return self._wrap(
            ok=True,
            result=out,
            warnings=warnings,
            diagnostics=diagnostics,
            agent=agent_name,
            task=task_name,
        )

    # ------------------------------------------------------------------
    # Einfache Task-Queue (Multitask-Layer)
    # ------------------------------------------------------------------
    def submit(self, kind: str, payload: Dict[str, Any]) -> None:
        """
        Fügt eine Aufgabe in die interne Queue ein.
        kind:
            - "temporal_full"
            - "patterncore_summary"
            - "structureweaver_summary"
            - "pointengine_summary"
            - "pointdynamics_full"
        """
        self.tasks.append(
            {
                "kind": kind,
                "payload": payload,
            }
        )

    def run_task(self, kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt eine einzelne Aufgabe aus, ohne Queue.
        """
        if kind == "temporal_full":
            return self.temporal_full(**payload)

        if kind == "patterncore_summary":
            return self.patterncore_summary(payload.get("seq", []))

        if kind == "structureweaver_summary":
            return self.structureweaver_summary(payload.get("seq", []))

        if kind == "pointengine_summary":
            return self.pointengine_summary(payload.get("seq", []))

        if kind == "pointdynamics_full":
            return self.pointdynamics_full(payload.get("seq", []))

        return self._wrap(
            ok=False,
            result=None,
            warnings=[
                {
                    "source": "orchestrator",
                    "where": "task_dispatch",
                    "reason": f"Unknown task kind '{kind}'",
                }
            ],
            diagnostics=None,
            agent=None,
            task=kind,
        )

    def run_queue(self) -> List[Dict[str, Any]]:
        """
        Führt alle Aufgaben in der Queue nacheinander aus.
        Gibt die Liste der Ergebnisse zurück und leert die Queue.
        """
        results: List[Dict[str, Any]] = []
        while self.tasks:
            job = self.tasks.pop(0)
            k = job["kind"]
            pl = job["payload"]
            res = self.run_task(k, pl)
            results.append(res)
        return results


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from pprint import pprint

    orch = Orchestrator()
    print("Agents:", orch.list_agents())

    demo_seq = [1, 0, 2, 0, 3]
    demo_structs = [0, 1, 0, 1, 0]
    demo_points = [0, 0, 5, 0, 0]
    demo_motion = [0, 1, 1, 0, 0]

    print("\nPatternCore:")
    pprint(orch.patterncore_summary(demo_seq))

    print("\nTemporalSynth:")
    pprint(
        orch.temporal_full(
            demo_seq,
            demo_structs,
            demo_points,
            demo_motion,
            with_debug=True,
            with_diagnostics=True,
        )
    )
