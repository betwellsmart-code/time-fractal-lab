"""
sanity_logic.py – Systemweite Sanity-Checks für Saham-Lab
Kompatibel mit Orchestrator 0.4 (Hybrid-Modus).
"""

from typing import Any, Dict, List


# -----------------------------------------------------------
# Hilfsfunktion: Sanity-Result Builder
# -----------------------------------------------------------
def _result(ok: bool, msg: str, details: Any = None) -> Dict[str, Any]:
    return {
        "ok": ok,
        "msg": msg,
        "details": details,
    }


# -----------------------------------------------------------
# 1) Array-Sanity – Prüft einzelne Sequenzen (Pattern, Structure, Points, Motion)
# -----------------------------------------------------------
def sanity_check_array(arr: Any) -> Dict[str, Any]:
    if arr is None:
        return _result(False, "Array is None.")

    if not isinstance(arr, (list, tuple)):
        return _result(False, f"Array must be list/tuple, got {type(arr).__name__}")

    for i, val in enumerate(arr):
        if not isinstance(val, (int, float)):
            return _result(False, f"Invalid element at index {i}: {val} (type {type(val)})")

    return _result(True, "Array OK.", {"length": len(arr)})


# -----------------------------------------------------------
# 2) Multi-Agent Input Sanity – Für TemporalSynth Full-Pipeline
# -----------------------------------------------------------
def sanity_check_multiagent_input(data: Dict[str, Any]) -> Dict[str, Any]:
    reports = {}
    overall_ok = True

    for key in ["patterns", "structures", "points", "motion"]:
        if key not in data:
            reports[key] = _result(False, f"Missing key '{key}'")
            overall_ok = False
            continue

        sub = sanity_check_array(data[key])
        if not sub["ok"]:
            overall_ok = False
        reports[key] = sub

    return {
        "ok": overall_ok,
        "msg": "Multi-Agent Input Sanity Check",
        "reports": reports,
    }


# -----------------------------------------------------------
# 3) Agent Output Sanity – Prüft Debug-Baum & Struktur
# -----------------------------------------------------------
def sanity_check_agent_output(output: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(output, dict):
        return _result(False, "Agent output must be a dict.")

    if "debug" not in output:
        return _result(False, "Agent output has no 'debug' section.")

    if not isinstance(output["debug"], dict):
        return _result(False, "'debug' must be a dict.")

    return _result(True, "Output OK.", {"keys": list(output.keys())})


# -----------------------------------------------------------
# 4) Sanity Summary – kombiniert mehrere Checks
# -----------------------------------------------------------
def sanity_summary(*checks: Dict[str, Any]) -> Dict[str, Any]:
    combined_ok = all(ch["ok"] for ch in checks)
    return {
        "ok": combined_ok,
        "reports": checks,
    }
