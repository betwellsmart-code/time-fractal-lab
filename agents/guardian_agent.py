#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
time-fractal-lab – pipeline.py (v0.4)

Author   : Dr. Noreki & EL_Samy
Project  : time-fractal-lab / Saham-Lab
Version  : v0.4.0

Purpose:
    Zentrale Pipeline-Orchestrierung für das Multi-Agenten-System.

    NEU IN v0.3:
    - Integration der AstroSnapshotEngine (Sub/SSL + Drift + Trend)
    - Integration von TemporalSynth (Agent 5) zur Bildung von Zeitblöcken

    NEU IN v0.4:
    - GuardianCoreAgent (Agent 7) als Systemwächter:
        * prüft Snapshots & Temporal Blocks
        * analysiert Trendverteilung & Blockdauer
        * wertet Agent-Resultate aus
        * schreibt einen GuardianReport in den Kontext
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from astro_snapshot_engine import AstroSnapshotEngine, Candle
# NEU (korrekt, zukunftssicher)
try:
    from .temporalsynth import TemporalSynth
except ImportError:  # fallback, wenn als Skript ausgeführt
    from temporalsynth import TemporalSynth



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
# Stub-Agenten 1–4, 6, 8–9 (Platzhalter, liefern OK)
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
# GuardianCore – Systemwächter (Agent 7)
# ============================================================================

@dataclass
class GuardianReport:
    """
    Zusammengefasster Gesundheitszustand der Pipeline.

    - overall_ok : Gesamteindruck (True/False)
    - issues     : Liste von Textmeldungen (Warnungen / Hinweise)
    - stats      : diverse Kennzahlen (Snapshots, Blocks, Trends, Agents ...)
    - created_at : Zeitstempel der Analyse
    """

    overall_ok: bool
    issues: List[str]
    stats: Dict[str, Any]
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_ok": self.overall_ok,
            "issues": self.issues,
            "stats": self.stats,
            "created_at": self.created_at.isoformat(),
        }


class GuardianCoreAgent(BaseAgent):
    """
    Agent 7 – GuardianCore
    Überwacht die Ergebnisse der Pipeline und bewertet:

    - Existenz & Anzahl von Snapshots und Temporal Blocks
    - Trendverteilung (up/down/neutral)
    - Blockdauern (min/avg/max)
    - Agent-Resultate (Fehlschläge)
    """

    def __init__(self, agent_id: int = 7, name: str = "GuardianCore") -> None:
        super().__init__(agent_id, name)

    def run(self, context: Dict[str, Any]) -> AgentResult:
        logger.info(
            "Agent %02d [%s] – starte Systemanalyse.",
            self.agent_id,
            self.name,
        )

        issues: List[str] = []
        stats: Dict[str, Any] = {}

        # ------------------------------------------------------------------
        # 1) Agent-Ergebnisse prüfen
        # ------------------------------------------------------------------
        agent_results: List[AgentResult] = context.get("agent_results", [])
        failed_agents = [ar for ar in agent_results if not ar.success]

        stats["agents_total"] = len(agent_results)
        stats["agents_failed"] = len(failed_agents)
        stats["failed_agent_names"] = [f"{ar.agent_id}:{ar.name}" for ar in failed_agents]

        if failed_agents:
            issues.append(
                f"{len(failed_agents)} Agent(en) meldeten Fehler: "
                + ", ".join(stats["failed_agent_names"])
            )

        # ------------------------------------------------------------------
        # 2) Snapshots prüfen
        # ------------------------------------------------------------------
        snapshots = context.get("snapshots") or []
        stats["snapshots_count"] = len(snapshots)

        if not snapshots:
            issues.append("Keine Snapshots im Kontext – TemporalSynth evtl. nicht gelaufen.")

        # Trend-Analyse
        if snapshots:
            ups = sum(1 for s in snapshots if s.trend == "up")
            downs = sum(1 for s in snapshots if s.trend == "down")
            neutrals = sum(1 for s in snapshots if s.trend == "neutral")
            total = len(snapshots)

            stats["trend_up"] = ups
            stats["trend_down"] = downs
            stats["trend_neutral"] = neutrals

            if total > 0:
                stats["trend_up_ratio"] = ups / total
                stats["trend_down_ratio"] = downs / total
                stats["trend_neutral_ratio"] = neutrals / total
            else:
                stats["trend_up_ratio"] = 0.0
                stats["trend_down_ratio"] = 0.0
                stats["trend_neutral_ratio"] = 0.0

            # einfache Heuristik: alles neutral = seltsam
            if ups == 0 and downs == 0 and neutrals > 0:
                issues.append("Alle Snapshots sind neutral – mögliche Datenanomalie.")

        # ------------------------------------------------------------------
        # 3) Temporal Blocks analysieren
        # ------------------------------------------------------------------
        blocks = context.get("temporal_blocks") or []
        stats["blocks_count"] = len(blocks)

        if not blocks and snapshots:
            issues.append("Snapshots vorhanden, aber keine Temporal Blocks – TemporalSynth-Problem?")

        if blocks:
            durations = [b.duration_min for b in blocks]
            stats["block_duration_min"] = min(durations)
            stats["block_duration_max"] = max(durations)
            stats["block_duration_avg"] = sum(durations) / max(1, len(durations))

            # sehr kurze oder sehr lange Blöcke markieren
            if stats["block_duration_min"] == 0:
                issues.append("Mindestens ein Block hat 0 Minuten Dauer – Prüfe Zeitstempel.")
            if stats["block_duration_max"] > 240:
                issues.append("Sehr langer Block (>240 Min) – mögliche Drift in Sub/SSL-Logik.")

        # ------------------------------------------------------------------
        # 4) Gesamtbewertung
        # ------------------------------------------------------------------
        overall_ok = len(issues) == 0
        report = GuardianReport(
            overall_ok=overall_ok,
            issues=issues,
            stats=stats,
            created_at=datetime.utcnow(),
        )

        context["guardian_report"] = report
        logger.info(
            "Agent %02d [%s] – GuardianReport erstellt (overall_ok=%s, issues=%d).",
            self.agent_id,
            self.name,
            overall_ok,
            len(issues),
        )

        details = (
            "Guardian OK"
            if overall_ok
            else f"Guardian meldet {len(issues)} Issue(s)"
        )

        return AgentResult(
            agent_id=self.agent_id,
            name=self.name,
            success=True,  # Guardian selbst ist gelaufen
            details=details,
        )


# ============================================================================
# Agenten-Registry
# ============================================================================

def build_agent_registry() -> Dict[int, BaseAgent]:
    """
    Baut die Agenten-Registry mit IDs 1–9.

    1: PatternCore        (Stub)
    2: StructureWeaver    (Stub)
    3: PointEngine        (Stub)
    4: PointDynamics      (Stub)
    5: TemporalSynth      (ECHT)
    6: DriftAgent         (Stub)
    7: GuardianCore       (ECHT)
    8: TrendAgent         (Stub)
    9: ForecastAgent      (Stub)
    """
    registry: Dict[int, BaseAgent] = {
        1: StubAgent(1, "PatternCore"),
        2: StubAgent(2, "StructureWeaver"),
        3: StubAgent(3, "PointEngine"),
        4: StubAgent(4, "PointDynamics"),
        5: TemporalSynthAgent(),
        6: StubAgent(6, "DriftAgent"),
        7: GuardianCoreAgent(),
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
                ar = AgentResult(
                    agent_id=agent_id,
                    name="UNKNOWN",
                    success=False,
                    details="Agent nicht gefunden",
                )
                agent_results.append(ar)
                ctx.setdefault("agent_results", []).append(ar)
                success = False
                continue

            try:
                result = agent.run(ctx)
                agent_results.append(result)
                ctx.setdefault("agent_results", []).append(result)

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
                ar = AgentResult(
                    agent_id=agent.agent_id,
                    name=agent.name,
                    success=False,
                    details=str(exc),
                )
                agent_results.append(ar)
                ctx.setdefault("agent_results", []).append(ar)
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
    - Lässt TemporalSynth Zeitblöcke berechnen.
    - Lässt GuardianCore eine Systembewertung erstellen.
    - Gibt eine kompakte Zusammenfassung auf stdout aus.
    """
    runner = PipelineRunner()
    result = runner.run()

    print(f"Run {result.run_id} – success={result.success}")
    for ar in result.agent_results:
        status = "OK" if ar.success else "FAILED"
        print(f"  - Agent {ar.agent_id:02d} [{ar.name}]: {status} ({ar.details or ''})")

    # Temporal Blocks
    blocks = result.context.get("temporal_blocks") or []
    print(f"\nTemporal Blocks: {len(blocks)}")
    for b in blocks:
        bd = b.to_dict()
        print(
            f"    Block {bd['block_id']} | {bd['start']} → {bd['end']} "
            f"| dur={bd['duration_min']}m | sub={bd['sub']} ssl={bd['ssl']} "
            f"| trend={bd['trend_bias']} | vol={bd['volatility']:.5f}"
        )

    # Guardian-Report
    report: Optional[GuardianReport] = result.context.get("guardian_report")
    print("\nGuardianCore Report:")
    if report is None:
        print("    KEIN REPORT – GuardianCore nicht gelaufen?")
    else:
        rd = report.to_dict()
        print(f"    overall_ok: {rd['overall_ok']}")
        print(f"    issues    : {rd['issues']}")
        print(f"    stats     : {rd['stats']}")


if __name__ == "__main__":
    _demo()
