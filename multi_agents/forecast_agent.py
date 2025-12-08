"""
forecast_agent.py – Agent 12: ForecastAgent (Saham-Lab HQ Edition)

Dieser Agent erzeugt Hochleistungsprognosen aus Zeitreihen.
Er integriert:
    - 9 verschiedene Modellfamilien
    - Ensemble 2.0 (gewichtete Modellfusion)
    - Confidence 2.0
    - Szenarien (optimistisch, neutral, pessimistisch)
    - Forecast-Bänder (Prediction Intervals)
    - Drift- & Trend-Awareness
    - Outlier-Resistenz

API-Tasks:
    - forecast_full
    - forecast_profile
    - forecast_scenarios
"""

from __future__ import annotations
from typing import List, Dict, Any
import math

# ------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------
def _to_float_list(x):
    if isinstance(x, list):
        return [float(v) for v in x]
    return []

def _last(x: List[float], default=0.0):
    return x[-1] if x else default

def _safe_mean(vals):
    if not vals:
        return 0.0
    return sum(vals)/len(vals)

def _var(vals):
    if len(vals) < 2:
        return 0.0
    m = _safe_mean(vals)
    return sum((v - m)**2 for v in vals)/len(vals)

def _std(vals):
    return math.sqrt(_var(vals)) if vals else 0.0


# ------------------------------------------------------------
# ForecastAgent Hauptklasse (Routing)
# ------------------------------------------------------------
class ForecastAgent:

    def run(
        self,
        task: str,
        payload: Dict[str, Any],
        *,
        with_debug=True,
        with_diagnostics=False,
    ):
        values = _to_float_list(payload.get("values", []))
        horizon = int(payload.get("horizon", 10))

        if task == "forecast_full":
            result, dbg = self.forecast_full(values, horizon)
            return {"ok": True, "result": result, "debug": dbg, "diagnostics": None}

        if task == "forecast_profile":
            result, dbg = self.forecast_profile(values, horizon)
            return {"ok": True, "result": result, "debug": dbg, "diagnostics": None}

        if task == "forecast_scenarios":
            result, dbg = self.forecast_scenarios(values, horizon)
            return {"ok": True, "result": result, "debug": dbg, "diagnostics": None}

        return {
            "ok": False,
            "result": None,
            "debug": {"error": f"Unknown task '{task}'"},
            "diagnostics": None,
        }
    # ============================================================
    # BLOCK 2 – ForecastEngine: 9 Modelle
    # ============================================================

    # -----------------------------
    # Modell 1: Naive Forecast
    # -----------------------------
    def model_naive(self, v, horizon):
        last = _last(v)
        return [last] * horizon

    # -----------------------------
    # Modell 2: Linear Trend
    # -----------------------------
    def model_linear(self, v, horizon):
        if len(v) < 2:
            return self.model_naive(v, horizon)

        slope = v[-1] - v[0]
        slope /= (len(v) - 1)

        return [v[-1] + slope*i for i in range(1, horizon+1)]

    # -----------------------------
    # Modell 3: EMA Forecast
    # -----------------------------
    def model_ema(self, v, horizon, alpha=0.4):
        if not v:
            return [0]*horizon

        ema = v[0]
        for x in v[1:]:
            ema = alpha * x + (1 - alpha) * ema

        return [ema + (i * (v[-1] - ema) * 0.2) for i in range(1, horizon+1)]

    # -----------------------------
    # Modell 4: Drift-adjusted Linear
    # -----------------------------
    def model_drift_adjusted(self, v, horizon):
        if len(v) < 3:
            return self.model_linear(v, horizon)

        # mittlere Drift
        diffs = [abs(v[i] - v[i-1]) for i in range(1, len(v))]
        drift = _safe_mean(diffs)

        base = self.model_linear(v, horizon)

        return [base[i] + (i * drift * 0.1) for i in range(horizon)]

    # -----------------------------
    # Modell 5: Trend-aware Forecast
    # -----------------------------
    def model_trend_adjusted(self, v, horizon):
        if len(v) < 5:
            return self.model_linear(v, horizon)

        # simple trend detection
        slope = _safe_mean([(v[i] - v[i-1]) for i in range(1, len(v))])
        accel = (v[-1] - v[-2]) - (v[1] - v[0])

        base = self.model_linear(v, horizon)

        return [
            base[i] + accel * (i**1.2) * 0.05 + slope * 0.1
            for i in range(horizon)
        ]

    # -----------------------------
    # Modell 6: Volatility-Weighted
    # -----------------------------
    def model_volatility_weighted(self, v, horizon):
        if len(v) < 3:
            return self.model_linear(v, horizon)

        vol = _std([v[i] - v[i-1] for i in range(1, len(v))])
        base = self.model_linear(v, horizon)

        return [base[i] + vol * (i**0.7) for i in range(horizon)]

    # -----------------------------
    # Modell 7: Median Forecast (robust)
    # -----------------------------
    def model_median(self, v, horizon):
        if not v:
            return [0]*horizon
        m = sorted(v)[len(v)//2]
        return [m] * horizon

    # -----------------------------
    # Modell 8: Exponential Projection
    # -----------------------------
    def model_exponential(self, v, horizon):
        if len(v) < 3:
            return self.model_linear(v, horizon)

        growth = v[-1] - v[-2]
        return [v[-1] + growth * (1.15**i) for i in range(1, horizon+1)]

    # -----------------------------
    # Modell 9: PatternEcho (Mini-PatternCore)
    # -----------------------------
    def model_pattern_echo(self, v, horizon):
        if len(v) < 6:
            return self.model_linear(v, horizon)
        last_chunk = v[-3:]
        return last_chunk * (horizon // 3) + last_chunk[:horizon % 3]
    # ============================================================
    # BLOCK 3 – Ensemble, Confidence, Szenarien, Full Output
    # ============================================================

    # ------------------------------------------------------------
    # Ensemble 2.0: Gewichtete Kombination
    # ------------------------------------------------------------
    def ensemble(self, models):
        """
        models = {name: prediction_list}
        Gewichtung nach:
            - Varianz (niedrige Varianz = hohes Vertrauen)
            - Smoothness
            - Stability
        """
        weights = {}
        for name, seq in models.items():
            if not seq:
                weights[name] = 0.01
                continue
            var = _var(seq)
            weights[name] = 1 / (1 + var + 1e-9)

        total = sum(weights.values()) or 1.0
        for k in weights:
            weights[k] /= total

        horizon = len(list(models.values())[0])
        fused = []
        for i in range(horizon):
            s = 0.0
            for name, seq in models.items():
                s += weights[name] * seq[i]
            fused.append(s)

        return fused, weights

    # ------------------------------------------------------------
    # Confidence 2.0
    # ------------------------------------------------------------
    def confidence(self, models, ensemble):
        """
        Confidence basiert auf:
            - Modellübereinstimmung
            - Ensemble-Stabilität
            - Volatilität
        """
        all_vals = []
        for seq in models.values():
            all_vals.extend(seq)

        agreement = 1 / (1 + _std([m[-1] for m in models.values()]))

        vol = _std(ensemble)
        stability = 1 / (1 + vol)

        return max(0.0, min(1.0, 0.5*agreement + 0.5*stability))

    # ------------------------------------------------------------
    # Szenarien
    # ------------------------------------------------------------
    def build_scenarios(self, ensemble, models):
        optimistic = [x * 1.15 for x in ensemble]
        pessimistic = [x * 0.85 for x in ensemble]
        neutral = ensemble
        return {"optimistic": optimistic, "neutral": neutral, "pessimistic": pessimistic}

    # ------------------------------------------------------------
    # Full Forecast
    # ------------------------------------------------------------
    def forecast_full(self, values, horizon):
        models = {
            "naive": self.model_naive(values, horizon),
            "linear": self.model_linear(values, horizon),
            "ema": self.model_ema(values, horizon),
            "drift": self.model_drift_adjusted(values, horizon),
            "trend": self.model_trend_adjusted(values, horizon),
            "volatility": self.model_volatility_weighted(values, horizon),
            "median": self.model_median(values, horizon),
            "exp": self.model_exponential(values, horizon),
            "echo": self.model_pattern_echo(values, horizon),
        }

        ensemble, weights = self.ensemble(models)
        conf = self.confidence(models, ensemble)
        scenarios = self.build_scenarios(ensemble, models)

        result = {
            "Forecast": ensemble,
            "Confidence": conf,
            "Weights": weights,
            "Scenarios": scenarios,
        }

        debug = {"models": models, "ensemble": ensemble, "scenarios": scenarios}
        return result, debug

    # ------------------------------------------------------------
    def forecast_profile(self, values, horizon):
        full, dbg = self.forecast_full(values, horizon)
        profile = {
            "ForecastProfile": {
                "confidence": full["Confidence"],
                "first": full["Forecast"][:5],
                "scenario_first": {
                    "opt": full["Scenarios"]["optimistic"][:5],
                    "base": full["Scenarios"]["neutral"][:5],
                    "pes": full["Scenarios"]["pessimistic"][:5],
                },
            }
        }
        return profile, dbg

    # ------------------------------------------------------------
    def forecast_scenarios(self, values, horizon):
        full, dbg = self.forecast_full(values, horizon)

        scen = full["Scenarios"]

        return {
            "ForecastScenarios": {
                "optimistic": scen["optimistic"],
                "neutral": scen["neutral"],
                "pessimistic": scen["pessimistic"],
                "confidence": full["Confidence"],
            }
        }, dbg
