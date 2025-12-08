"""
horizon_agent.py – Agent 15: HorizonAgent (Saham-Lab HQ Edition)

Zweck:
    Erkennt die Reichweite & Grenzen eines Systems.
    Arbeitet über:
        - Fehlerkurven
        - Trend-Analyse
        - Velocity & Acceleration
        - Divergenzphasen
        - Multi-Domain HorizonScore

API:
    - horizon_full
    - horizon_profile
    - horizon_forecast
"""

from __future__ import annotations
from typing import List, Dict, Any
import math


def _to_float_list(x: Any) -> List[float]:
    if isinstance(x, list):
        return [float(v) for v in x]
    return []


class HorizonAgent:
    """
    Agent 15 – HorizonAgent 2.0
    """

    def run(
        self,
        task: str,
        payload: Dict[str, Any],
        *,
        with_debug=True,
        with_diagnostics=False,
    ):
        errors = _to_float_list(payload.get("errors", []))
        thr = float(payload.get("threshold", 1.0))

        if task == "horizon_full":
            result, dbg = self.horizon_full(errors, thr, with_debug)
            return {"ok": True, "result": result, "debug": dbg, "diagnostics": None}

        if task == "horizon_profile":
            result, dbg = self.horizon_profile(errors, thr, with_debug)
            return {"ok": True, "result": result, "debug": dbg, "diagnostics": None}

        if task == "horizon_forecast":
            result, dbg = self.horizon_forecast(errors, thr, with_debug)
            return {"ok": True, "result": result, "debug": dbg, "diagnostics": None}

        return {"ok": False, "result": None, "debug": {"error": f"Unknown task {task}"}}
    # --------------------------------------
    # Velocity & Acceleration
    # --------------------------------------
    def _velocity(self, values: List[float]) -> List[float]:
        if len(values) < 2: return [0.0]
        return [values[i+1] - values[i] for i in range(len(values)-1)]

    def _acceleration(self, vel: List[float]) -> List[float]:
        if len(vel) < 2: return [0.0]
        return [vel[i+1] - vel[i] for i in range(len(vel)-1)]

    # --------------------------------------
    # Grund-Horizont aus Threshold
    # --------------------------------------
    def _base_horizon(self, errors: List[float], thr: float):
        idx = len(errors)
        for i, e in enumerate(errors):
            if abs(e) >= thr:
                idx = i
                break

        valid = idx
        if valid == 0:
            status = "collapsing"
        elif valid < len(errors) / 3:
            status = "narrow"
        elif valid < (2 * len(errors)) / 3:
            status = "normal"
        else:
            status = "wide"

        return idx, valid, status

    # --------------------------------------
    # Trendanalyse
    # --------------------------------------
    def _trend(self, values: List[float]):
        if len(values) < 3:
            return "flat"

        # Einfacher linearer Trend via Steigung
        x = list(range(len(values)))
        n = len(values)

        sx = sum(x)
        sy = sum(values)
        sxx = sum(a*a for a in x)
        sxy = sum(x[i]*values[i] for i in range(n))

        denom = n*sxx - sx*sx
        if denom == 0:
            return "flat"

        slope = (n*sxy - sx*sy) / denom

        if slope > 0.05: return "rising"
        if slope < -0.05: return "falling"
        return "flat"

    # --------------------------------------
    # HorizonScore multidimensional
    # --------------------------------------
    def _horizon_score(self, base_valid, n, trend, accel):
        score = (base_valid / max(1, n))

        # Trend adjust
        if trend == "rising": score *= 0.7
        if trend == "falling": score *= 1.1

        # Acceleration adjust
        mean_acc = sum(abs(a) for a in accel) / max(1, len(accel))
        if mean_acc > 0.5:
            score *= 0.8

        return max(0.0, min(1.0, score))
    # --------------------------------------
    # FULL PIPELINE
    # --------------------------------------
    def horizon_full(self, errors, thr, with_debug):
        vel = self._velocity(errors)
        acc = self._acceleration(vel)

        h_idx, valid, status = self._base_horizon(errors, thr)
        trend = self._trend(errors)
        score = self._horizon_score(valid, len(errors), trend, acc)

        result = {
            "HorizonProfile": {
                "errors": errors,
                "threshold": thr,
                "horizon_index": h_idx,
                "valid_length": valid,
                "status": status,
                "trend": trend,
                "horizon_score": score,
            }
        }

        debug = {
            "velocity": vel,
            "acceleration": acc,
            "trend": trend,
        }

        return result, debug

    # --------------------------------------
    def horizon_profile(self, errors, thr, with_debug):
        full, dbg = self.horizon_full(errors, thr, with_debug)
        prof = full["HorizonProfile"]

        profile = {
            "HorizonProfile": {
                "valid_length": prof["valid_length"],
                "status": prof["status"],
                "trend": prof["trend"],
                "horizon_score": prof["horizon_score"],
            }
        }
        return profile, dbg

    # --------------------------------------
    # FORECAST
    # --------------------------------------
    def horizon_forecast(self, errors, thr, with_debug):
        """
        Einfaches Modell:
        - extrapoliert Trend
        - schätzt, wann Threshold erreicht wird
        """
        if not errors:
            return {"HorizonForecast": {"prediction": None}}, {}

        vel = self._velocity(errors)
        avg_vel = sum(vel) / len(vel)

        if avg_vel <= 0:
            return {"HorizonForecast": {"prediction": float("inf")}}, {"avg_vel": avg_vel}

        last = errors[-1]
        remaining = max(0.0, thr - last)
        pred = remaining / avg_vel

        return {
            "HorizonForecast": {
                "current": last,
                "threshold": thr,
                "avg_velocity": avg_vel,
                "steps_until_collapse": pred,
            }
        }, {"avg_vel": avg_vel}
