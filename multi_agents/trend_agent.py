"""
trend_agent.py – Agent 18: TrendAgent (Saham-Lab HQ Edition)

Zweck:
    Erkennt und klassifiziert Trendstrukturen über mehrere Zeitskalen.
    Ermittelt Trendregime, Trendphase, TrendScore und Forecast.

API:
    - trend_full
    - trend_profile
    - trend_forecast
"""

from __future__ import annotations
from typing import List, Dict, Any
import math


# ------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------
def _to_float_list(x: Any) -> List[float]:
    if isinstance(x, list):
        return [float(v) for v in x]
    return []


# ------------------------------------------------------------
# Hauptklasse
# ------------------------------------------------------------
class TrendAgent:

    def run(
        self,
        task: str,
        payload: Dict[str, Any],
        *,
        with_debug=True,
        with_diagnostics=False,
    ):
        values = _to_float_list(payload.get("values", []))

        if task == "trend_full":
            result, dbg = self.trend_full(values, with_debug)
            return {"ok": True, "result": result, "debug": dbg, "diagnostics": None}

        if task == "trend_profile":
            result, dbg = self.trend_profile(values, with_debug)
            return {"ok": True, "result": result, "debug": dbg, "diagnostics": None}

        if task == "trend_forecast":
            result, dbg = self.trend_forecast(values, with_debug)
            return {"ok": True, "result": result, "debug": dbg, "diagnostics": None}

        return {"ok": False, "result": None, "debug": {"error": f"Unknown task {task}"}}
    # ------------------------------------------------------------
    # Slope / SmoothSlope / Drift / Volatility / Acceleration
    # ------------------------------------------------------------
    def slope(self, v: List[float]) -> float:
        return 0.0 if len(v) < 2 else v[-1] - v[0]

    def smooth_slope(self, v: List[float]) -> float:
        if len(v) < 3:
            return self.slope(v)
        diffs = [v[i] - v[i-1] for i in range(1, len(v))]
        return sum(diffs)/len(diffs)

    def drift(self, v: List[float]) -> float:
        if len(v) < 3:
            return 0.0
        diffs = [abs(v[i] - v[i-1]) for i in range(1, len(v))]
        return sum(diffs)/len(diffs)

    def drift_volatility(self, v: List[float]) -> float:
        if len(v) < 4:
            return 0.0
        diffs = [abs(v[i] - v[i-1]) for i in range(1, len(v))]
        m = sum(diffs)/len(diffs)
        var = sum((d - m)**2 for d in diffs)/len(diffs)
        return math.sqrt(var)

    def acceleration(self, v: List[float]) -> float:
        if len(v) < 3:
            return 0.0
        return (v[-1] - v[-2]) - (v[1] - v[0])

    # ------------------------------------------------------------
    # Windowed
    # ------------------------------------------------------------
    def window(self, v: List[float], w: int) -> List[float]:
        return v if len(v) < w else v[-w:]

    def analyze_window(self, v: List[float], w: int) -> Dict[str, float]:
        vw = self.window(v, w)
        return {
            "window": w,
            "slope": self.slope(vw),
            "smooth_slope": self.smooth_slope(vw),
            "drift": self.drift(vw),
            "volatility": self.drift_volatility(vw),
            "acceleration": self.acceleration(vw),
        }
    # ------------------------------------------------------------
    # Regime Classification
    # ------------------------------------------------------------
    def classify_regime(self, ss: float, dr: float) -> str:
        if abs(ss) < 0.01 and dr < 0.02:
            return "FLAT-STABLE"
        if ss > 0 and dr < 0.1:
            return "UP-STABLE"
        if ss > 0 and dr >= 0.1:
            return "UP-CHAOTIC"
        if ss < 0 and dr < 0.1:
            return "DOWN-STABLE"
        if ss < 0 and dr >= 0.1:
            return "DOWN-CHAOTIC"
        return "UNDEFINED"

    # ------------------------------------------------------------
    # Trend Phase Logic
    # ------------------------------------------------------------
    def classify_phase(self, slope_value: float, accel_value: float) -> str:
        if accel_value > 0.05 and slope_value > 0:
            return "TREND_EXPANSION"
        if slope_value > 0.2 and accel_value < 0:
            return "TREND_PEAK"
        if slope_value > 0 and accel_value < -0.1:
            return "TREND_EXHAUSTION"
        if slope_value < 0 and accel_value < -0.05:
            return "TREND_REVERSAL"
        if slope_value < -0.2:
            return "TREND_COLLAPSE"
        return "TREND_INIT"

    # ------------------------------------------------------------
    # Trend Score (0–1)
    # ------------------------------------------------------------
    def trend_score(self, w5, w20, w50):
        slopes = [abs(w5["smooth_slope"]), abs(w20["smooth_slope"]), abs(w50["smooth_slope"])]
        drifts = [w5["drift"], w20["drift"], w50["drift"]]
        vols = [w5["volatility"], w20["volatility"], w50["volatility"]]

        s = sum(slopes)/3.0
        d = sum(drifts)/3.0
        v = sum(vols)/3.0

        score = s - d - 0.5*v
        return max(0.0, min(1.0, score))

    # ------------------------------------------------------------
    # Forecast (Trendprojektion)
    # ------------------------------------------------------------
    def forecast(self, v: List[float], steps=10):
        if not v:
            return [0]*steps
        last = v[-1]
        sl = self.smooth_slope(v)
        return [last + sl*i for i in range(1, steps+1)]

    # ------------------------------------------------------------
    # Full Pipeline
    # ------------------------------------------------------------
    def trend_full(self, values: List[float], with_debug=True):
        w5  = self.analyze_window(values, 5)
        w20 = self.analyze_window(values, 20)
        w50 = self.analyze_window(values, 50)

        regime = self.classify_regime(w20["smooth_slope"], w20["drift"])
        phase  = self.classify_phase(w20["smooth_slope"], w20["acceleration"])
        score  = self.trend_score(w5, w20, w50)

        result = {
            "TrendProfile": {
                "window5": w5,
                "window20": w20,
                "window50": w50,
                "regime": regime,
                "phase": phase,
                "trend_score": score,
            }
        }

        debug = {
            "values": values,
            "w5": w5,
            "w20": w20,
            "w50": w50,
        }

        return result, debug

    # ------------------------------------------------------------
    def trend_profile(self, values: List[float], with_debug=True):
        full, dbg = self.trend_full(values, with_debug)
        prof = full["TrendProfile"]

        profile = {
            "TrendProfile": {
                "regime": prof["regime"],
                "phase": prof["phase"],
                "trend_score": prof["trend_score"],
            }
        }
        return profile, dbg

    # ------------------------------------------------------------
    def trend_forecast(self, values: List[float], with_debug=True):
        pred = self.forecast(values)
        result = {
            "TrendForecast": {
                "prediction": pred,
                "steps": len(pred)
            }
        }
        return result, {"values": values, "prediction": pred}
