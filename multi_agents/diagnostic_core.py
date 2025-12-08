"""
diagnostic_core.py – Sanity 2.0 (Diagnostic Core)
-------------------------------------------------

Aufgabe:
- Tiefere Diagnose und Qualitätsbewertung von Sequenzen und Agentenoutputs.
- Wird vom Orchestrator 0.5 im Mode C optional verwendet.
- Verändert niemals Daten – nur Analyse & Scores.

Die Idee:
- Qualitätsscore für Sequenzen
- Extremwertanalyse
- Dichte/Aktivitätsgrad
- Debug-Integritätsprüfung
"""

from typing import Any, Dict, List
import math


def _diag_result(ok: bool, kind: str, details: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ok": ok,
        "kind": kind,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Einzel-Sequence-Analyse
# ---------------------------------------------------------------------------

def analyze_sequence(seq: List[float]) -> Dict[str, Any]:
    if not seq:
        return _diag_result(
            False,
            "sequence",
            {
                "reason": "Empty sequence",
                "length": 0,
            },
        )

    nonzero = [v for v in seq if v != 0]
    zero_count = len(seq) - len(nonzero)

    max_v = max(seq)
    min_v = min(seq)
    span = max_v - min_v

    # einfache "Qualität": Anteil Nicht-Null, normalisierte Spannweite
    density = len(nonzero) / len(seq)
    span_norm = span if span == 0 else min(1.0, abs(span) / (abs(max_v) + 1e-9))

    quality = 0.5 * density + 0.5 * span_norm

    return _diag_result(
        True,
        "sequence",
        {
            "length": len(seq),
            "nonzero": len(nonzero),
            "zero": zero_count,
            "density": density,
            "max": max_v,
            "min": min_v,
            "span": span,
            "span_norm": span_norm,
            "quality": quality,
        },
    )


# ---------------------------------------------------------------------------
# Debug-Tree-Integrität
# ---------------------------------------------------------------------------

def check_debug_integrity(output: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(output, dict):
        return _diag_result(
            False,
            "debug_integrity",
            {"reason": "output is not a dict"},
        )

    dbg = output.get("debug")
    if not isinstance(dbg, dict):
        return _diag_result(
            False,
            "debug_integrity",
            {"reason": "debug field missing or not a dict"},
        )

    # sehr einfacher Check: mindestens 1 Eintrag
    ok = len(dbg.keys()) > 0
    return _diag_result(
        ok,
        "debug_integrity",
        {"keys": list(dbg.keys())},
    )


# ---------------------------------------------------------------------------
# Multi-Agent-Analyse (TemporalSynth / kombinierte Layer)
# ---------------------------------------------------------------------------

def analyze_multiagent_temporal(
    patterns: List[float],
    structures: List[float],
    points: List[float],
    motion: List[float],
) -> Dict[str, Any]:
    seq_reports = {
        "patterns": analyze_sequence(patterns),
        "structures": analyze_sequence(structures),
        "points": analyze_sequence(points),
        "motion": analyze_sequence(motion),
    }

    # grober Kohärenz-Score: Mittel der Einzel-Qualitäten
    qualities = []
    for key, rep in seq_reports.items():
        if rep["ok"]:
            qualities.append(rep["details"]["quality"])
    avg_quality = sum(qualities) / len(qualities) if qualities else 0.0

    return _diag_result(
        True,
        "multiagent_temporal",
        {
            "sequences": seq_reports,
            "avg_quality": avg_quality,
        },
    )


# ---------------------------------------------------------------------------
# Gesamt-Diagnose eines Agentenoutputs (+ optional Multi-Agent-Daten)
# ---------------------------------------------------------------------------

def full_diagnostic(
    *,
    agent: str,
    task: str,
    output: Dict[str, Any],
    patterns: List[float] | None = None,
    structures: List[float] | None = None,
    points: List[float] | None = None,
    motion: List[float] | None = None,
) -> Dict[str, Any]:
    """
    Voll-Diagnose Paket:
    - Debug-Integrität
    - optional Sequenz-/Multi-Agent-Analyse
    """
    reports: List[Dict[str, Any]] = []

    # Debug-Integrität
    reports.append(check_debug_integrity(output))

    # Multi-Agent-Sequenzen
    if patterns is not None and structures is not None and points is not None and motion is not None:
        reports.append(
            analyze_multiagent_temporal(patterns, structures, points, motion)
        )

    all_ok = all(r["ok"] for r in reports)

    return {
        "ok": all_ok,
        "agent": agent,
        "task": task,
        "reports": reports,
    }
