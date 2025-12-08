"""
PatternCore 0.3 – Klassischer Musterdetektor im Saham-Lab
Kompatibel mit Orchestrator 0.4 (Hybrid + Debugbaum).
"""

from typing import Any, Dict, List


class PatternCore:
    def __init__(self, name: str = "PatternCore", version: str = "0.3"):
        self.name = name
        self.version = version

    # -----------------------------------------------------------
    # Hilfsfunktionen (intern)
    # -----------------------------------------------------------
    def _extract_patterns(self, data: List[float]) -> Dict:
        patterns = []
        for i, v in enumerate(data):
            if v != 0:
                patterns.append({"i": i, "value": v})
        return {"active_points": patterns, "count": len(patterns)}

    def _feature_vector(self, data: List[float]) -> List[float]:
        if not data:
            return []
        return [
            sum(data),
            max(data),
            min(data),
            sum(1 for v in data if v != 0),
        ]

    # -----------------------------------------------------------
    # High-Level Tasks
    # -----------------------------------------------------------
    def pattern_analyze(self, seq: List[float]) -> Dict:
        patt = self._extract_patterns(seq)
        return {
            "analysis": patt,
            "debug": {
                "raw": seq,
                "pattern_positions": patt,
            },
        }

    def pattern_collect(self, seq: List[float]) -> Dict:
        return {
            "collection": list(seq),
            "debug": {"raw": seq},
        }

    def pattern_features(self, seq: List[float]) -> Dict:
        feats = self._feature_vector(seq)
        return {
            "features": feats,
            "debug": {"raw": seq, "feature_vector": feats},
        }

    def pattern_summary(self, seq: List[float]) -> Dict:
        feats = self._feature_vector(seq)
        patt = self._extract_patterns(seq)
        return {
            "summary": {
                "nonzero": patt["count"],
                "sum": feats[0] if feats else 0,
                "max": feats[1] if feats else None,
            },
            "debug": {"raw": seq, "patterns": patt, "features": feats},
        }

    # -----------------------------------------------------------
    # Run-Schnittstelle für Orchestrator
    # -----------------------------------------------------------
    def run(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        seq = payload.get("data", [])

        if task == "pattern_analyze":
            return self.pattern_analyze(seq)

        if task == "pattern_collect":
            return self.pattern_collect(seq)

        if task == "pattern_features":
            return self.pattern_features(seq)

        if task == "pattern_summary":
            return self.pattern_summary(seq)

        return {"error": f"Unknown PatternCore task '{task}'", "debug": {}}
