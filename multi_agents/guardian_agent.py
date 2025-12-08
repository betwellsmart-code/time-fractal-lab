"""
guardian_agent.py – Agent 10: GuardianAgent (Saham-Lab HQ Edition)

Zweck:
    Überwacht den vollständigen Systemgesundheitszustand
    anhand eines Multi-Agenten-Snapshots.

Input (payload):
{
    "agent_states": {...},  # Pattern/Structure/Dynamics/...
    "drift": {...},         # DriftAgent Output
    "coherence": {...},     # CoherenceAgent Output
    "anomaly": {...},       # AnomalyAgent Output
    "temporal": {...},      # TemporalSynth Output
    "meta": {...}           # FusionAgent Output
}

Output:
    - global_health (0–1)
    - status (optimal → critical)
    - recommendation
    - health_vector (6-Achsen)
"""

from __future__ import annotations
from typing import Any, Dict

import math


# -------------------------------------------------------
# Utility Layer
# -------------------------------------------------------
def _num(x: Any) -> float:
    """Structual numerification."""
    if isinstance(x, list):
        return float(len(x))
    if isinstance(x, dict):
        return float(len(x.keys()))
    if x is None:
        return 0.0
    return float(len(str(x)))


def _normalize(x: float, max_val: float = 10.0) -> float:
    """Normalize to [0,1]."""
    return min(1.0, max(0.0, x / max_val))


# =======================================================
# Agent 10 – GuardianAgent (HQ)
# =======================================================
class GuardianAgent:

    # ---------------------------------------------------
    # Public API – Orchestrator-kompatibel
    # ---------------------------------------------------
    def run(
        self,
        task: str,
        payload: Dict[str, Any],
        *,
        with_debug: bool = True,
        with_diagnostics: bool = False,
    ) -> Dict[str, Any]:

        try:
            agent_states = payload.get("agent_states", {})
            drift = payload.get("drift", {})
            coherence = payload.get("coherence", {})
            anomaly = payload.get("anomaly", {})
            temporal = payload.get("temporal", {})
            meta = payload.get("meta", {})

        except Exception as e:
            return {
                "ok": False,
                "result": None,
                "debug": {"error": f"Payload error: {e}"},
                "diagnostics": None,
            }

        if task == "guardian_full":
            result, debug = self.guardian_full(
                agent_states, drift, coherence, anomaly, temporal, meta, with_debug
            )
            return {
                "ok": True,
                "result": result,
                "debug": debug if with_debug else {},
                "diagnostics": {},  # reserviert
            }

        if task == "guardian_profile":
            result, debug = self.guardian_profile(
                agent_states, drift, coherence, anomaly, temporal, meta, with_debug
            )
            return {
                "ok": True,
                "result": result,
                "debug": debug if with_debug else {},
                "diagnostics": {},
            }

        return {
            "ok": False,
            "result": None,
            "debug": {"error": f"Unknown GuardianAgent task '{task}'"},
            "diagnostics": None,
        }
    # ---------------------------------------------------
    # HEALTH VECTOR 2.0
    # ---------------------------------------------------
    def _health_vector(
        self,
        agent_states: Dict,
        drift: Dict,
        coherence: Dict,
        anomaly: Dict,
        temporal: Dict,
        meta: Dict,
    ) -> Dict[str, float]:

        # structural health
        strength_pattern = _num(agent_states.get("patterns"))
        strength_struct = _num(agent_states.get("structures"))
        strength_dyn = _num(agent_states.get("dynamics"))

        structural = _normalize((strength_pattern + strength_struct + strength_dyn) / 3.0)

        # drift (low drift = high health)
        drift_vec = drift.get("DriftProfile", {}).get("vector", {})
        drift_vals = [abs(v.get("norm_delta", 0.0)) for v in drift_vec.values()]
        drift_score = 1.0 - (sum(drift_vals) / len(drift_vals) if drift_vals else 0.0)

        # coherence health
        coh_score = coherence.get("CoherenceProfile", {}).get("global_score", 0.0)
        coherence_health = _normalize(coh_score * 10.0)

        # anomaly health
        anom_int = anomaly.get("AnomalyProfile", {}).get("anomaly_intensity", 0.0)
        anomaly_health = 1.0 - _normalize(anom_int * 10.0)

        # temporal health
        avg_div = temporal.get("ChronoMaps", {}).get("avg_divergence", 0.3)
        temporal_health = 1.0 - _normalize(avg_div * 10.0)

        # meta health
        meta_score = meta.get("MetaProfile", {}).get("meta_score", 0.0)
        meta_health = _normalize(meta_score * 10.0)

        return {
            "structural": structural,
            "drift": drift_score,
            "coherence": coherence_health,
            "anomaly": anomaly_health,
            "temporal": temporal_health,
            "meta": meta_health,
        }

    # ---------------------------------------------------
    def _global_score(self, vec: Dict[str, float]) -> float:
        vals = list(vec.values())
        if not vals:
            return 0.0
        return sum(vals) / len(vals)

    # ---------------------------------------------------
    def _classify(self, score: float) -> str:
        if score >= 0.85:
            return "optimal"
        if score >= 0.70:
            return "healthy"
        if score >= 0.50:
            return "degrading"
        if score >= 0.30:
            return "unstable"
        return "critical"

    # ---------------------------------------------------
    def _recommend(self, status: str) -> str:
        if status == "optimal":
            return "no_action"
        if status == "healthy":
            return "recheck_agent_weakest"
        if status == "degrading":
            return "increase_sampling_rate"
        if status == "unstable":
            return "trigger_failsafe"
        if status == "critical":
            return "restart_pipeline"
        return "no_action"

    # ---------------------------------------------------
    def guardian_full(
        self,
        agent_states,
        drift,
        coherence,
        anomaly,
        temporal,
        meta,
        with_debug: bool,
    ):
        vec = self._health_vector(agent_states, drift, coherence, anomaly, temporal, meta)
        global_score = self._global_score(vec)
        status = self._classify(global_score)
        rec = self._recommend(status)

        result = {
            "GuardianProfile": {
                "global_health": global_score,
                "status": status,
                "recommendation": rec,
                "health_vector": vec,
            }
        }

        return result, {"vec": vec, "global_score": global_score, "status": status}

    # ---------------------------------------------------
    def guardian_profile(
        self,
        agent_states,
        drift,
        coherence,
        anomaly,
        temporal,
        meta,
        with_debug: bool,
    ):
        """Detailansicht (ohne Empfehlung)."""
        vec = self._health_vector(agent_states, drift, coherence, anomaly, temporal, meta)
        result = {
            "GuardianProfile": {
                "health_vector": vec,
            }
        }
        return result, {"vec": vec}
if __name__ == "__main__":
    ga = GuardianAgent()
    prev = {"patterns": [1,2], "structures": [3], "dynamics": [1]}
    curr = {"patterns": [1,2,3], "structures": [4], "dynamics": [2]}

    drift = {
        "DriftProfile": {
            "vector": {
                "pattern": {"norm_delta": 0.3},
                "structure": {"norm_delta": 0.1}
            }
        }
    }

    test = ga.run("guardian_full", {
        "agent_states": prev,
        "drift": drift,
        "coherence": {"CoherenceProfile": {"global_score": 0.66}},
        "anomaly": {"AnomalyProfile": {"anomaly_intensity": 0.1}},
        "temporal": {"ChronoMaps": {"avg_divergence": 0.2}},
        "meta": {"MetaProfile": {"meta_score": 0.7}}
    })

    print(test)
