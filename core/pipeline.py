#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
time-fractal-lab – pipeline.py (v0.3)

Author   : Dr. Noreki & EL_Samy
Project  : time-fractal-lab / Saham-Lab
Version  : v0.3.0

Purpose:
    Zentrale Pipeline-Orchestrierung für das Multi-Agenten-System.

    NEU IN v0.3:
    - Integration der AstroSnapshotEngine (Sub/SSL + Drift + Trend)
    - Integration von TemporalSynth (Agent 5) zur Bildung von Zeitblöcken
    - Kontextweitergabe zwischen Agenten über ein gemeinsames context-Objekt

    Architektur:
    - Agent 1–4, 6–9: Platzhalter/Stub-Agents (OK-Meldung, spätere Logik möglich)
    - Agent 5 (TemporalSynthAgent): Echt angebunden an
        * astro_snapshot_engine.AstroSnapshotEngine
        * temporal_synth.TemporalSynth
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from astro_snapshot_engine import AstroSnapshotEngine, Candle
from temporal_synth import TemporalSynth


# ============================================================================
# Logging-Konfiguration
# ============================================================================

logger = logging.getLogger("time_fractal_lab.pipeline")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s :: %(message)s",
    )


# ============================================================================
# Agenten-Grundstruktur
# ============================================================================

@dataclass
class AgentResult:
    agent_id: int
    name: str
    success: bool
    details: Optional[str] = None


class BaseAgent:
    """
    Basisklasse für alle Agenten.
    """

    def __init__(self, agent_id: int, name: str) -> None:
        self.agent_id = agent_id
        self.name = name

    def run(self, context: Dict[str, Any]) -> AgentResult:
        """
        Muss von Unterklassen überschrieben werden.
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Stub-Agenten 1–4, 6–9 (Platzhalter, liefern OK)
# ---------------------------------------------------------------------------

class StubAgent(BaseAgent):
    """
    Einfacher Platzhalter-Agent, der nur OK meldet.
    Später können hier echte Implementierungen ergänzt werden.
    """

    def run(self, context: Dict[str, Any]) -> AgentResult:
        logger.info(
            "Agent %02d [%s] – Stub läuft, keine spezifische Logik.",
            self.agent_id,
            self.name,
        )
        return AgentResult(
            agent_id=self.agent_id,
            name=self.name,
            success=True,
            details="StubAgent – OK",
        )


# ============================================================================
# Agent 5 – TemporalSynth (echte Logik)
# ============================================================================

class TemporalSynthAgent(BaseAgent):
    """
    Agent 5 – nutzt AstroSnapshotEngine und TemporalSynth, um aus
    Kerzen- und Astro-Daten Zeitblöcke abzuleiten.

    Erwartet im context optional:
        - 'candles': List[Candle]
          Wenn nicht vorhanden, erzeugt der Agent Demo-Kerzen (M1, 10 Minuten).

    Schreibt in den context:
        - 'snapshots': Liste von SnapshotRecord-Objekten
        - 'temporal_blocks': Liste von TemporalBlock-Objekten
    """

    def __init__(self, agent_id: int = 5, name: str = "TemporalSynth") -> None:
        super().__init__(agent_id, name)
        self.snapshot_engine = AstroSnapshotEngine()
        self.temporal_synth = TemporalSynth()

    def _build_demo_candles(self) -> List[Candle]:
        """
        Erzeugt eine kleine Demo-Serie von M1-Kerzen, falls keine
        Marktdaten im Kontext vorhanden sind.
        """
        base_ts = datetime(2025, 1, 1, 12, 0, 0)
        candles: List[Candle] = []
        price = 11.0

        for i in range(10):
            ts = base_ts + timedelta(minutes=i)
            o = price
            # einfache alternierende Bewegung
            c = price + (0.01 if i % 2 == 0 else -0.015)
            h = max(o, c) + 0.005
            l = min(o, c) - 0.005
            price = c

            candles.append(
                Candle(
                    timestamp=ts,
                    tf="M1",
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                )
            )

        return candles

    def run(self, context: Dict[str, Any]) -> AgentResult:
        logger.info(
            "Agent %02d [%s] – TemporalSynth startet Analyse.",
            self.agent_id,
            self.name,
        )

        # 1) Kerzenquelle bestimmen
        candles: Optional[List[Candle]] = context.get("candles")
        if not candles:
            logger.info(
                "Agent %02d [%s] – keine Kerzen im Kontext, "
                "verwende Demo-M1-Serie.",
                self.agent_id,
                self.name,
            )
            candles = self._build_demo_candles()
            context["candles"] = candles

        # 2) Astro-Snapshots bauen
        snapshots = self.snapshot_engine.build_snapshots(candles)
        context["snapshots"] = snapshots
        logger.info(
            "Agent %02d [%s] – %d Snapshots erzeugt.",
            self.agent_id,
            self.name,
            len(snapshots),
        )

        # 3) Temporal Blocks berechnen
        blocks = self.temporal_synth.analyze(snapshots)
        context["temporal_blocks"] = blocks
        logger.info(
            "Agent %02d [%s] – %d Temporal Blocks erzeugt.",
            self.agent_id,
            self.name,
            len(blocks),
        )

        return AgentResult(
            agent_id=self.agent_id,
            name=self.name,
            success=True,
            details=f"{len(blocks)} Temporal Blocks erzeugt",
        )


# ============================================================================
# Agenten-Registry
# ============================================================================

def build_agent_registry() -> Dict[int, BaseAgent]:
    """
    Baut die Agenten-Registry mit IDs 1–9.

    1: PatternCore
    2: StructureWeaver
    3: PointEngine
    4: PointDynamics
    5: TemporalSynth (ECHT)
    6: DriftAgent (Stub)
    7: GuardianCore (Stub)
    8: TrendAgent (Stub)
    9: ForecastAgent (Stub)
    """
    registry: Dict[int, BaseAgent] = {
        1: StubAgent(1, "PatternCore"),
        2: StubAgent(2, "StructureWeaver"),
        3: StubAgent(3, "PointEngine"),
        4: StubAgent(4, "PointDynamics"),
        5: TemporalSynthAgent(),
        6: StubAgent(6, "DriftAgent"),
        7: StubAgent(7, "GuardianCore"),
        8: StubAgent(8, "TrendAgent"),
        9: StubAgent(9, "ForecastAgent"),
    }
    return registry


# ============================================================================
# Pipeline-Runner
# ============================================================================

@dataclass
class PipelineResult:
    run_id: str
    success: bool
    agent_results: List[AgentResult]
    context: Dict[str, Any]


class PipelineRunner:
    """
    Orchestriert einen Pipeline-Lauf mit ausgewählten Agenten.
    """

    def __init__(self, agent_registry: Optional[Dict[int, BaseAgent]] = None) -> None:
        self.agent_registry = agent_registry or build_agent_registry()

    def run(
        self,
        agents: Optional[List[int]] = None,
        context: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
    ) -> PipelineResult:
        if agents is None:
            agents = list(self.agent_registry.keys())

        ctx: Dict[str, Any] = context or {}
        run_id = run_id or f"run-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"

        logger.info(
            "Starting pipeline run_id=%s with agents=%s",
            run_id,
            agents,
        )

        agent_results: List[AgentResult] = []
        success = True

        for agent_id in agents:
            agent = self.agent_registry.get(agent_id)
            if agent is None:
                logger.error("Agent ID %s nicht in Registry vorhanden.", agent_id)
                agent_results.append(
                    AgentResult(
                        agent_id=agent_id,
                        name="UNKNOWN",
                        success=False,
                        details="Agent nicht gefunden",
                    )
                )
                success = False
                continue

            try:
                result = agent.run(ctx)
                agent_results.append(result)
                status_text = "OK" if result.success else "FAILED"
                logger.info(
                    "Agent %02d [%s]: %s (%s)",
                    agent.agent_id,
                    agent.name,
                    status_text,
                    result.details or "",
                )
                if not result.success:
                    success = False
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Agent %02d [%s] – Exception: %s",
                    agent.agent_id,
                    agent.name,
                    exc,
                )
                agent_results.append(
                    AgentResult(
                        agent_id=agent.agent_id,
                        name=agent.name,
                        success=False,
                        details=str(exc),
                    )
                )
                success = False

        logger.info(
            "Pipeline run_id=%s finished – success=%s",
            run_id,
            success,
        )

        return PipelineResult(
            run_id=run_id,
            success=success,
            agent_results=agent_results,
            context=ctx,
        )


# ============================================================================
# Demo-Einstiegspunkt
# ============================================================================

def _demo() -> None:
    """
    Einfacher Demo-Lauf:

    - Läuft alle Agenten 1–9 durch.
    - Lässt TemporalSynth echte Zeitblöcke berechnen.
    - Gibt eine kompakte Zusammenfassung auf stdout aus.
    """
    runner = PipelineRunner()
    result = runner.run()

    print(f"Run {result.run_id} – success={result.success}")
    for ar in result.agent_results:
        status = "OK" if ar.success else "FAILED"
        print(f"  - Agent {ar.agent_id:02d} [{ar.name}]: {status} ({ar.details or ''})")

    # Wenn TemporalSynth gelaufen ist, gibt es 'temporal_blocks' im Kontext
    blocks = result.context.get("temporal_blocks") or []
    print(f"\nTemporal Blocks: {len(blocks)}")
    for b in blocks:
        bd = b.to_dict()
        print(
            f"    Block {bd['block_id']} | {bd['start']} → {bd['end']} "
            f"| dur={bd['duration_min']}m | sub={bd['sub']} ssl={bd['ssl']} "
            f"| trend={bd['trend_bias']} | vol={bd['volatility']:.5f}"
        )


if __name__ == "__main__":
    _demo()
