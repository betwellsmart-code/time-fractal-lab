#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline.py – Time-Fractal-Lab Multi-Agent Pipeline (Enterprise Version)

Author   : Dr. Noreki & EL_Samy (Development Lead)
Project  : time-fractal-lab / Saham-Lab
Version  : v0.2.0
Purpose  : Provides the central execution pipeline for Agents 0–12
           including orchestration, registry, configuration, logging
           and snapshot-friendly result structures.

This module is designed to be:
- Easy to extend (add new agents or pipelines)
- Sandbox-compatible (no external dependencies beyond stdlib)
- GitHub-friendly (clear structure, docstrings, type hints)
"""

from __future__ import annotations

import abc
import dataclasses
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


# ============================================================================
# 0) LOGGING SETUP
# ============================================================================

def setup_default_logging(level: int = logging.INFO) -> None:
    """
    Configure a simple console logger.
    Can be called from __main__ or from external starter scripts.
    """
    logger = logging.getLogger("time_fractal_lab.pipeline")
    if logger.handlers:
        return  # Already configured

    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(name)s :: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


LOGGER = logging.getLogger("time_fractal_lab.pipeline")


# ============================================================================
# 1) CORE DATA STRUCTURES
# ============================================================================

@dataclasses.dataclass
class AgentConfig:
    """
    Configuration for a single agent.

    - id: Numeric ID (0–12)
    - name: Human-readable name (e.g. 'PatternCore')
    - role: Short description of purpose
    - enabled: Whether this agent is active in the pipeline
    """
    id: int
    name: str
    role: str
    enabled: bool = True


@dataclasses.dataclass
class PipelineConfig:
    """
    Global configuration for the pipeline.

    - debug_mode: If True, more verbose logs and additional debug fields
    - collect_intermediates: If True, stores each agent's payload output
    - default_pipeline: Default ordered list of agent IDs
    - snapshot_dir: Optional directory for JSON snapshots
    """
    debug_mode: bool = True
    collect_intermediates: bool = True
    default_pipeline: Sequence[int] = dataclasses.field(default_factory=lambda: [
        1, 2, 3, 4, 5, 6, 7, 8, 9  # 0 = Orchestrator, 10–12 = optional / advanced
    ])
    snapshot_dir: Optional[Path] = None


@dataclasses.dataclass
class PipelineContext:
    """
    Context object passed through the pipeline.

    - run_id: Unique identifier for this pipeline run
    - metadata: Arbitrary metadata (e.g. chart info, timestamps, scenario)
    - created_at: Run start timestamp
    """
    run_id: str
    metadata: Dict[str, Any]
    created_at: datetime = dataclasses.field(default_factory=datetime.utcnow)


@dataclasses.dataclass
class AgentResult:
    """
    Result of a single agent run.

    - agent_id: Numeric ID (0–12)
    - agent_name: Name of the agent
    - success: True if no exception occurred
    - data: Agent output payload (structured or unstructured)
    - error: Error message if success == False
    - started_at / finished_at: Timestamps for timing
    """
    agent_id: int
    agent_name: str
    success: bool
    data: Any
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


@dataclasses.dataclass
class PipelineReport:
    """
    Aggregated report for a full pipeline run.

    - run_id: Identifier from PipelineContext
    - success: True if all mandatory agents succeeded
    - results: List of AgentResults in execution order
    - metadata: Includes context metadata and pipeline configuration
    """
    run_id: str
    success: bool
    results: List[AgentResult]
    metadata: Dict[str, Any]


# ============================================================================
# 2) BASE AGENT CLASS
# ============================================================================

class AgentBase(abc.ABC):
    """
    Abstract base class for all agents in the Time-Fractal-Lab system.

    Each agent must implement:
    - `run(self, payload, context)` → returns output payload

    Agents should:
    - be side-effect free (or side-effects clearly documented)
    - handle errors gracefully
    - log internally using LOGGER
    """

    def __init__(self, config: AgentConfig) -> None:
        self.config = config

    @property
    def id(self) -> int:
        return self.config.id

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def role(self) -> str:
        return self.config.role

    def is_enabled(self) -> bool:
        return self.config.enabled

    @abc.abstractmethod
    def run(self, payload: Any, context: PipelineContext) -> Any:
        """
        Execute the agent logic.

        Parameters
        ----------
        payload : Any
            The incoming data from previous step (or initial input).
        context : PipelineContext
            Shared context for the pipeline run.

        Returns
        -------
        Any
            The output payload to be passed to the next agent.
        """
        raise NotImplementedError


# ============================================================================
# 3) CONCRETE PLACEHOLDER AGENTS 0–12
# ============================================================================

class OrchestratorAgent(AgentBase):
    """
    Agent 0 – Orchestrator

    High-level conductor. In this simplified version, Orchestrator does not
    transform the payload, but can inject orchestration metadata.
    """

    def run(self, payload: Any, context: PipelineContext) -> Any:
        LOGGER.info("[Orchestrator] Starting orchestration for run_id=%s", context.run_id)
        orchestration_info = {
            "orchestrated_by": "OrchestratorAgent",
            "run_id": context.run_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Merge orchestration info into payload if it is a dict, otherwise wrap.
        if isinstance(payload, dict):
            merged = dict(payload)
            merged["_orchestration"] = orchestration_info
            return merged
        else:
            return {
                "payload": payload,
                "_orchestration": orchestration_info,
            }


class SimpleLoggingAgent(AgentBase):
    """
    Generic placeholder agent.

    Used as a base for the simple placeholder implementations below.
    It logs the incoming payload and appends its own marker.
    """

    def run(self, payload: Any, context: PipelineContext) -> Any:
        LOGGER.debug(
            "[%s] Received payload type=%s for run_id=%s",
            self.name, type(payload).__name__, context.run_id
        )

        marker = {
            "agent_id": self.id,
            "agent_name": self.name,
            "role": self.role,
            "run_timestamp": datetime.utcnow().isoformat(),
        }

        if isinstance(payload, dict):
            out = dict(payload)
            out.setdefault("_trace", [])
            out["_trace"].append(marker)
            return out
        else:
            return {
                "payload": payload,
                "_trace": [marker],
            }


# Define concrete agents via subclassing SimpleLoggingAgent
class PatternCoreAgent(SimpleLoggingAgent):
    pass


class StructureWeaverAgent(SimpleLoggingAgent):
    pass


class PointEngineAgent(SimpleLoggingAgent):
    pass


class PointDynamicsAgent(SimpleLoggingAgent):
    pass


class TemporalSynthAgent(SimpleLoggingAgent):
    pass


class DriftAgent(SimpleLoggingAgent):
    pass


class GuardianCoreAgent(SimpleLoggingAgent):
    pass


class TrendAgent(SimpleLoggingAgent):
    pass


class ForecastAgent(SimpleLoggingAgent):
    pass


class ClusterAgent(SimpleLoggingAgent):
    pass


class SignatureAgent(SimpleLoggingAgent):
    pass


class HorizonAgent(SimpleLoggingAgent):
    pass


# ============================================================================
# 4) AGENT REGISTRY
# ============================================================================

class AgentRegistry:
    """
    Central registry that holds all agent instances by their IDs.

    Responsibilities:
    - instantiate all known agents with their configs
    - provide lookup by ID or by name
    - allow easy extension by adding new agents
    """

    def __init__(self, config: Optional[PipelineConfig] = None) -> None:
        self.config = config or PipelineConfig()
        self._agents_by_id: Dict[int, AgentBase] = {}
        self._initialize_default_agents()

    def _initialize_default_agents(self) -> None:
        """
        Instantiate all 13 agents 0–12 with basic roles.
        """

        def add(agent: AgentBase) -> None:
            self._agents_by_id[agent.id] = agent

        # 0 – Orchestrator
        add(OrchestratorAgent(AgentConfig(
            id=0,
            name="Orchestrator",
            role="Central coordination of the agent pipeline",
        )))

        # 1–12 – Core agents
        add(PatternCoreAgent(AgentConfig(
            id=1,
            name="PatternCore",
            role="Extracts patterns from numerical and symbolic data.",
        )))
        add(StructureWeaverAgent(AgentConfig(
            id=2,
            name="StructureWeaver",
            role="Weaves patterns into higher-level structures.",
        )))
        add(PointEngineAgent(AgentConfig(
            id=3,
            name="PointEngine",
            role="Works with points, KP points, Keno points.",
        )))
        add(PointDynamicsAgent(AgentConfig(
            id=4,
            name="PointDynamics",
            role="Analyses dynamics, changes, and movement between points.",
        )))
        add(TemporalSynthAgent(AgentConfig(
            id=5,
            name="TemporalSynth",
            role="Builds temporal and fractal time models.",
        )))
        add(DriftAgent(AgentConfig(
            id=6,
            name="DriftAgent",
            role="Monitors temporal and structural drift.",
        )))
        add(GuardianCoreAgent(AgentConfig(
            id=7,
            name="GuardianCore",
            role="Quality and stability monitoring.",
        )))
        add(TrendAgent(AgentConfig(
            id=8,
            name="TrendAgent",
            role="Detects medium- and long-range trends.",
        )))
        add(ForecastAgent(AgentConfig(
            id=9,
            name="ForecastAgent",
            role="Generates forecasts based on trends and structures.",
        )))
        add(ClusterAgent(AgentConfig(
            id=10,
            name="ClusterAgent",
            role="Forms clusters of patterns, points or outputs.",
        )))
        add(SignatureAgent(AgentConfig(
            id=11,
            name="SignatureAgent",
            role="Builds mathematical or symbolic signatures.",
        )))
        add(HorizonAgent(AgentConfig(
            id=12,
            name="HorizonAgent",
            role="Determines ranges, limits, and time horizons.",
        )))

    # -- registry API -----------------------------------------------------

    def get(self, agent_id: int) -> AgentBase:
        if agent_id not in self._agents_by_id:
            raise KeyError(f"Agent with id={agent_id} not found in registry.")
        return self._agents_by_id[agent_id]

    def get_optional(self, agent_id: int) -> Optional[AgentBase]:
        return self._agents_by_id.get(agent_id)

    def list_agents(self) -> List[AgentBase]:
        return list(self._agents_by_id.values())

    def list_enabled(self) -> List[AgentBase]:
        return [a for a in self._agents_by_id.values() if a.is_enabled()]


# ============================================================================
# 5) PIPELINE EXECUTION ENGINE
# ============================================================================

class PipelineRunner:
    """
    PipelineRunner executes a sequence of agents on a given payload.

    It:
    - uses AgentRegistry to resolve agent instances
    - executes them in order
    - handles errors without killing the entire run
    - records AgentResult objects
    - can emit snapshot files for later analysis
    """

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        config: Optional[PipelineConfig] = None,
    ) -> None:
        self.config = config or PipelineConfig()
        self.registry = registry or AgentRegistry(self.config)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def run_pipeline(
        self,
        pipeline: Optional[Sequence[int]],
        initial_payload: Any,
        context: PipelineContext,
        mandatory_agents: Optional[Sequence[int]] = None,
    ) -> PipelineReport:
        """
        Execute the given pipeline (sequence of agent IDs).

        Parameters
        ----------
        pipeline : Sequence[int] or None
            Ordered list of agent IDs. If None, use config.default_pipeline.
        initial_payload : Any
            Incoming data fed into the first agent.
        context : PipelineContext
            Shared context object.
        mandatory_agents : Sequence[int], optional
            Agents which must succeed for success=True in the report.

        Returns
        -------
        PipelineReport
        """
        if pipeline is None:
            pipeline = list(self.config.default_pipeline)

        if mandatory_agents is None:
            mandatory_agents = list(pipeline)

        LOGGER.info(
            "Starting pipeline run_id=%s with agents=%s",
            context.run_id, list(pipeline)
        )

        results: List[AgentResult] = []
        payload = initial_payload

        for agent_id in pipeline:
            agent = self.registry.get_optional(agent_id)
            if agent is None:
                LOGGER.error("Agent %s not found in registry – skipping.", agent_id)
                results.append(AgentResult(
                    agent_id=agent_id,
                    agent_name=f"UNKNOWN-{agent_id}",
                    success=False,
                    data=None,
                    error="Agent not registered.",
                ))
                continue

            if not agent.is_enabled():
                LOGGER.info("Agent %s (%s) disabled – skipping.",
                            agent.id, agent.name)
                continue

            LOGGER.debug("Running agent %s (%s)", agent.id, agent.name)

            result = AgentResult(
                agent_id=agent.id,
                agent_name=agent.name,
                success=False,
                data=None,
                started_at=datetime.utcnow(),
            )

            try:
                payload = agent.run(payload, context)
                result.success = True
                result.data = payload
                result.error = None
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception(
                    "Agent %s (%s) raised an exception.",
                    agent.id, agent.name
                )
                result.success = False
                result.error = f"{type(exc).__name__}: {exc!s}"

                # In debug mode we keep payload as-is for inspection
                if self.config.debug_mode:
                    result.data = payload
                else:
                    result.data = None

            result.finished_at = datetime.utcnow()
            results.append(result)

        success = all(
            (r.success for r in results if r.agent_id in mandatory_agents)
        )

        report = PipelineReport(
            run_id=context.run_id,
            success=success,
            results=results,
            metadata={
                "context_metadata": context.metadata,
                "config": dataclasses.asdict(self.config),
                "pipeline": list(pipeline),
                "created_at": context.created_at.isoformat(),
                "finished_at": datetime.utcnow().isoformat(),
            },
        )

        if self.config.snapshot_dir is not None:
            self._write_snapshot(report)

        LOGGER.info(
            "Pipeline run_id=%s finished – success=%s",
            context.run_id, success
        )
        return report

    # ------------------------------------------------------------------ #
    # Snapshot handling
    # ------------------------------------------------------------------ #

    def _write_snapshot(self, report: PipelineReport) -> None:
        """
        Write a JSON snapshot of the pipeline report to snapshot_dir/run_id.json
        """
        snapshot_dir = self.config.snapshot_dir
        if snapshot_dir is None:
            return

        snapshot_dir.mkdir(parents=True, exist_ok=True)
        path = snapshot_dir / f"{report.run_id}.json"

        def serialize_agent_result(res: AgentResult) -> Dict[str, Any]:
            return {
                "agent_id": res.agent_id,
                "agent_name": res.agent_name,
                "success": res.success,
                "data": res.data if self.config.collect_intermediates else None,
                "error": res.error,
                "started_at": res.started_at.isoformat() if res.started_at else None,
                "finished_at": res.finished_at.isoformat() if res.finished_at else None,
            }

        obj = {
            "run_id": report.run_id,
            "success": report.success,
            "results": [serialize_agent_result(r) for r in report.results],
            "metadata": report.metadata,
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

        LOGGER.info("Snapshot written to %s", path)


# ============================================================================
# 6) SIMPLE CONVENIENCE ENTRY POINT
# ============================================================================

def generate_run_id(prefix: str = "run") -> str:
    """
    Generate a simple run_id based on timestamp.
    """
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f")
    return f"{prefix}-{ts}"


def demo_run() -> None:
    """
    Minimal demo run for manual testing.

    You can invoke this by running:
    `python pipeline.py`

    It will:
    - create a default PipelineRunner
    - run the default pipeline (1–9)
    - print a compact summary to stdout
    """
    setup_default_logging(logging.INFO)

    cfg = PipelineConfig(
        debug_mode=True,
        collect_intermediates=True,
        snapshot_dir=None,  # Optional: Path("snapshots")
    )

    registry = AgentRegistry(cfg)
    runner = PipelineRunner(registry=registry, config=cfg)

    context = PipelineContext(
        run_id=generate_run_id("demo"),
        metadata={"scenario": "demo", "source": "pipeline.py"},
    )

    initial_payload: Dict[str, Any] = {
        "note": "Initial payload for demo run.",
    }

    report = runner.run_pipeline(
        pipeline=None,  # use default from cfg
        initial_payload=initial_payload,
        context=context,
    )

    # Compact summary on stdout
    print(f"Run {report.run_id} – success={report.success}")
    for res in report.results:
        status = "OK" if res.success else "FAIL"
        print(f"  - Agent {res.agent_id:02d} [{res.agent_name}]: {status}")


if __name__ == "__main__":
    demo_run()
