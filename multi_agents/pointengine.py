"""
PointEngine 0.3 – Punktbasierte Berechnungsschicht des Saham-Lab.
Kompatibel mit Orchestrator 0.4.
"""

from typing import Any, Dict, List


class PointEngine:
    def __init__(self, name: str = "PointEngine", version: str = "0.3"):
        self.name = name
        self.version = version

    # -----------------------------------------------------------
    # Hilfsfunktionen
    # -----------------------------------------------------------
    def _rate(self, seq: List[float]) -> float:
        if len(seq) < 2:
            return 0
        return seq[-1] - seq[-2]

    def _velocity(self, seq: List[float]) -> float:
        if len(seq) < 3:
            return 0
        return (seq[-1] - seq[-2]) - (seq[-2] - seq[-3])

    def _acceleration(self, seq: List[float]) -> float:
        if len(seq) < 4:
            return 0
        d1 = seq[-1] - seq[-2]
        d2 = seq[-2] - seq[-3]
        d3 = seq[-3] - seq[-4]
        return (d1 - d2) - (d2 - d3)

    # -----------------------------------------------------------
    # Tasks
    # -----------------------------------------------------------
    def point_calc(self, seq: List[float]) -> Dict:
        return {
            "calc": {
                "rate": self._rate(seq),
                "velocity": self._velocity(seq),
                "acceleration": self._acceleration(seq),
            },
            "debug": {"raw": seq},
        }

    def point_derivatives(self, seq: List[float]) -> Dict:
        return {
            "derivatives": {
                "rate": self._rate(seq),
                "velocity": self._velocity(seq),
                "acceleration": self._acceleration(seq),
            },
            "debug": {"raw": seq},
        }

    def point_summary(self, seq: List[float]) -> Dict:
        r = self._rate(seq)
        v = self._velocity(seq)
        a = self._acceleration(seq)
        return {
            "summary": {"rate": r, "velocity": v, "accel": a},
            "debug": {"raw": seq},
        }

    # -----------------------------------------------------------
    # Run-Schnittstelle
    # -----------------------------------------------------------
    def run(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        seq = payload.get("data", [])

        if task == "point_calc":
            return self.point_calc(seq)

        if task == "point_derivatives":
            return self.point_derivatives(seq)

        if task == "point_summary":
            return self.point_summary(seq)

        return {"error": f"Unknown PointEngine task '{task}'", "debug": {}}
