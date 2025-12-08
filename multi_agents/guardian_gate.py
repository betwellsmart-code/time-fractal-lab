"""
guardian_gate.py – Sanity 1.0 (operative Gate-Schicht)
------------------------------------------------------

Aufgabe:
- Schnelle, robuste Eingangs- und Ausgangsprüfungen für den Orchestrator.
- Verhindert, dass komplett unbrauchbare Daten in Agenten laufen.
- Stoppt Pipelines NICHT hart (Mode C), sondern liefert Gate-Resultate,
  die der Orchestrator interpretieren kann.

WICHTIG:
- GuardianGate MODIFIZIERT KEINE DATEN.
- Er ist nur Türsteher: markieren, melden, aber nicht anfassen.
"""

from typing import Any, Dict, List


def _gate_result(
    ok: bool,
    *,
    level: str,
    where: str,
    agent: str,
    task: str,
    reason: str,
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return {
        "ok": ok,
        "level": level,        # z.B. "gate"
        "where": where,        # "input" / "output"
        "agent": agent,
        "task": task,
        "reason": reason,
        "details": details or {},
    }


# ---------------------------------------------------------------------------
# Input-Gates
# ---------------------------------------------------------------------------

def gate_array_input(
    seq: Any,
    *,
    agent: str,
    task: str,
    where: str = "input",
) -> Dict[str, Any]:
    """
    Schneller Gatekeeper für 1D-Sequenzen.
    Prüft Typ, List/Tuple, numerische Einträge.
    """
    if seq is None:
        return _gate_result(
            False,
            level="gate",
            where=where,
            agent=agent,
            task=task,
            reason="Sequence is None.",
        )

    if not isinstance(seq, (list, tuple)):
        return _gate_result(
            False,
            level="gate",
            where=where,
            agent=agent,
            task=task,
            reason=f"Sequence must be list/tuple, got {type(seq).__name__}.",
        )

    bad_indices: List[int] = []
    for i, val in enumerate(seq):
        if not isinstance(val, (int, float)):
            bad_indices.append(i)

    if bad_indices:
        return _gate_result(
            False,
            level="gate",
            where=where,
            agent=agent,
            task=task,
            reason="Non-numeric values in sequence.",
            details={"bad_indices": bad_indices},
        )

    return _gate_result(
        True,
        level="gate",
        where=where,
        agent=agent,
        task=task,
        reason="Sequence OK.",
        details={"length": len(seq)},
    )


def gate_multiagent_input(
    data: Dict[str, Any],
    *,
    agent: str,
    task: str,
    keys: List[str],
    where: str = "input",
) -> Dict[str, Any]:
    """
    Gatekeeper für mehrdimensionale Inputs (z.B. TemporalSynth).
    Erwartet ein Dict mit bestimmten Keys (z.B. patterns, structures, points, motion).
    """
    reports: Dict[str, Any] = {}
    all_ok = True

    for key in keys:
        if key not in data:
            all_ok = False
            reports[key] = {
                "ok": False,
                "reason": f"Missing key '{key}'",
            }
            continue

        sub = gate_array_input(data[key], agent=agent, task=task, where=where)
        reports[key] = sub
        if not sub["ok"]:
            all_ok = False

    if not all_ok:
        return _gate_result(
            False,
            level="gate",
            where=where,
            agent=agent,
            task=task,
            reason="Multi-agent input failed Gate checks.",
            details={"reports": reports},
        )

    return _gate_result(
        True,
        level="gate",
        where=where,
        agent=agent,
        task=task,
        reason="Multi-agent input OK.",
        details={"reports": reports},
    )


# ---------------------------------------------------------------------------
# Output-Gate
# ---------------------------------------------------------------------------

def gate_agent_output(
    output: Any,
    *,
    agent: str,
    task: str,
    where: str = "output",
) -> Dict[str, Any]:
    """
    Schnelle Struktursichtung des Agentenoutputs.
    Erwartet:
    - dict
    - optionales 'debug'-Feld als dict
    """
    if not isinstance(output, dict):
        return _gate_result(
            False,
            level="gate",
            where=where,
            agent=agent,
            task=task,
            reason="Agent output must be a dict.",
        )

    if "debug" not in output:
        return _gate_result(
            False,
            level="gate",
            where=where,
            agent=agent,
            task=task,
            reason="Agent output has no 'debug' field.",
        )

    if not isinstance(output["debug"], dict):
        return _gate_result(
            False,
            level="gate",
            where=where,
            agent=agent,
            task=task,
            reason="'debug' field must be a dict.",
        )

    return _gate_result(
        True,
        level="gate",
        where=where,
        agent=agent,
        task=task,
        reason="Agent output structure OK.",
        details={"keys": list(output.keys())},
    )
