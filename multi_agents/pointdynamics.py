"""
PointDynamics 0.3 – Dynamik-Analyse des Saham-Lab.
Basierend auf rate/velocity/acceleration/impact + Pipeline.
Kompatibel mit Orchestrator 0.4.
"""

from typing import Any, Dict, List


class PointDynamics:
    def __init__(self, name: str = "PointDynamics", version: str = "0.3"):
        self.name = name
        self.version = version

    # -----------------------------------------------------------
    # Kernfunktionen
    # -----------------------------------------------------------
    def rate(self, seq: List[float]) -> float:
        return 0 if len(seq) < 2 else seq[-1] - seq[-2]

    def velocity(self, seq: List[float]) -> float:
        return 0 if len(seq) < 3 else (seq[-1] - seq[-2]) - (seq[-2] - seq[-3])

    def acceleration(self, seq: List[float]) -> float:
        if len(seq) < 4:
            return 0
        d1 = seq[-1] - seq[-2]
        d2 = seq[-2] - seq[-3]
        d3 = seq[-3] - seq[-4]
        return (d1 - d2) - (d2 - d3)

    def impact(self, seq: List[float]) -> float:
        r = self.rate(seq)
        v = self.velocity(seq)
        a = self.acceleration(seq)
        return abs(r) + abs(v) + abs(a)

    def full_pipeline(self, seq: List[float]) -> Dict:
        r = self.rate(seq)
        v = self.velocity(seq)
        a = self.acceleration(seq)
        imp = self.impact(seq)

        return {
            "dynamics": {
                "rate": r,
                "velocity": v,
                "acceleration": a,
                "impact": imp,
            },
            "debug": {"raw": seq},
        }

    # -----------------------------------------------------------
    # Tasks
    # -----------------------------------------------------------
    def run(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        seq = payload.get("data", [])

        if task == "dynamics_full":
            return self.full_pipeline(seq)

        if task == "dynamics_rate":
            return {"rate": self.rate(seq), "debug": {"raw": seq}}

        if task == "dynamics_velocity":
            return {"velocity": self.velocity(seq), "debug": {"raw": seq}}

        if task == "dynamics_accel":
            return {"accel": self.acceleration(seq), "debug": {"raw": seq}}

        if task == "dynamics_impact":
            return {"impact": self.impact(seq), "debug": {"raw": seq}}

        if task == "dynamics_summary":
            return {
                "summary": {
                    "rate": self.rate(seq),
                    "velocity": self.velocity(seq),
                    "acceleration": self.acceleration(seq),
                    "impact": self.impact(seq),
                },
                "debug": {"raw": seq},
            }

        return {"error": f"Unknown PointDynamics task '{task}'", "debug": {}}
