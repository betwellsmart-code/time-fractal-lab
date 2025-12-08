# pointdynamics_logic.py
# Rekonstruktion des ursprünglichen mathematischen Agenten (Agent 4)
# Keine OpenAI-Abhängigkeit. Reine mathematische Kernlogik.

from typing import List, Dict, Any
import math

# -----------------------------
# Hilfsfunktion
# -----------------------------
def _to_list(x: Any) -> List[float]:
    if isinstance(x, list):
        return [float(v) for v in x]
    return []

# -----------------------------
# 1) RATE – Erste Ableitung
# -----------------------------
def pd_rate(values: List[float]) -> List[float]:
    """Berechnet Rate: Differenzen zwischen benachbarten Werten."""
    if len(values) < 2:
        return [0.0]
    return [values[i] - values[i - 1] for i in range(1, len(values))]

# -----------------------------
# 2) VELOCITY – Absolutwerte
# -----------------------------
def pd_velocity(rate: List[float]) -> List[float]:
    """Berechnet Velocity: |Rate|."""
    return [abs(r) for r in rate]

# -----------------------------
# 3) ACCELERATION – 2. Ableitung
# -----------------------------
def pd_acceleration(rate: List[float]) -> List[float]:
    """Berechnet echte mathematische Beschleunigung."""
    if len(rate) < 2:
        return [0.0]
    return [rate[i] - rate[i - 1] for i in range(1, len(rate))]

# -----------------------------
# 4) IMPACT – Dynamische Umschlagpunkte
# -----------------------------
def pd_impact(acc: List[float], threshold: float = 1.0) -> List[int]:
    """Erkennt auffällige Beschleunigungen als Impact-Zonen."""
    impact_idx = []
    for i, a in enumerate(acc):
        if abs(a) >= threshold:
            impact_idx.append(i)
    return impact_idx

# -----------------------------
# 5) FULL PIPELINE – Komplettanalyse
# -----------------------------
def pd_full_pipeline(values: Any) -> Dict:
    """Die komplette ursprüngliche Analyse-Pipeline."""
    vals = _to_list(values)
    rate = pd_rate(vals)
    vel = pd_velocity(rate)
    acc = pd_acceleration(rate)
    impact = pd_impact(acc)

    return {
        "DynamicsUnits": {
            "values": vals,
            "rate": rate,
            "velocity": vel,
            "acceleration": acc,
            "impact_zones": impact
        },
        "debug": {
            "values_raw": vals,
            "rate": rate,
            "velocity": vel,
            "acceleration": acc,
            "impact": impact
        }
    }
