"""
drift_agent.py – Agent 9: DriftAgent (Saham-Lab HQ-Standard)
------------------------------------------------------------

Zweck:
    Misst die zeitliche Drift zwischen zwei Systemzuständen
    (Snapshots), die aus den Agentenoutputs bestehen.

Variante A – Snapshot-Level:
    payload["previous"] = Snapshot 1 (früherer Zustand)
    payload["current"]  = Snapshot 2 (aktueller Zustand)

Ein Snapshot ist z.B.:

{
    "pattern":   {"summary": {...}},
    "structure": {"summary": {...}},
    "points":    {"summary": {...}},
    "dynamics":  {"summary": {...}},
    "temporal":  {"ChronoMaps": {...}},
    "coherence": {"summary": {...}},
    "anomaly":   {"summary": {...}},
    "fusion":    {"summary": {...}},
}

Ergebnis (drift_full):

{
  "summary": {
    "global_score": float,   # 0.0 = stabil, 1.0 = maximale Drift
    "dominant_axis": str,    # z.B. "anomaly", "fusion", ...
    "drift_label": str       # "stable", "moderate", "strong"
  },
  "vector": {
    "<axis>": {
      "prev": float,
      "curr": float,
      "delta": float,
      "abs_delta": float,
      "norm_delta": float     # 0–1
    },
    ...
  },
  "previous_raw": {...},
  "current_raw": {...},
}
"""

from __future__ import annotations
from typing import Any, Dict, Optional
import math


StateVector = Dict[str, float]


class DriftAgent:
    """
    DriftAgent 1.0 – misst Drift zwischen zwei Multi-Agent-Snapshots.

    Kernideen:
      - arbeitet auf bereits verdichteten Agenten-Outputs
      - erzeugt eine Drift-Vektorstruktur
      - berechnet einen globalen Driftscore
      - liefert eine qualitative Einschätzung
    """

    # ----------------------------------------------------------
    # Public API – Orchestrator-kompatibel
    # ----------------------------------------------------------
    def run(
        self,
        task: str,
        payload: Dict[str, Any],
        *,
        with_debug: bool = True,
        with_diagnostics: bool = False,   # reserviert für später
    ) -> Dict[str, Any]:
        """
        Einheitlicher Einstiegspunkt.

        Unterstützte Tasks:
            - "drift_full"
            - "drift_profile"
        """
        prev = payload.get("previous", None)
        curr = payload.get("current", None)

        if prev is None or curr is None:
            return {
                "ok": False,
                "result": None,
                "debug": {
                    "error": "payload['previous'] und/oder payload['current'] fehlen."
                },
            }

        if task == "drift_full":
            result, debug = self.drift_full(prev, curr, with_debug=with_debug)
            return {
                "ok": True,
                "result": result,
                "debug": debug if with_debug else {},
            }

        if task == "drift_profile":
            profile, debug = self.build_profile(prev, curr, with_debug=with_debug)
            return {
                "ok": True,
                "result": profile,
                "debug": debug if with_debug else {},
            }

        return {
            "ok": False,
            "result": None,
            "debug": {"error": f"Unknown DriftAgent task '{task}'"},
        }

    # ----------------------------------------------------------
    # Snapshot → StateVector
    # ----------------------------------------------------------
    def _safe_get(self, d: Dict[str, Any], *path, default: Optional[float] = None) -> Optional[float]:
        """
        Sicherer Zugriff auf verschachtelte Dicts.
        """
        cur: Any = d
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                return default
            cur = cur[key]
        if isinstance(cur, (int, float)):
            return float(cur)
        return default

    def _extract_state_vector(self, snapshot: Dict[str, Any]) -> StateVector:
        """
        Extrahiert einen kompakten StateVector aus dem Snapshot.
        Alle Werte werden grob auf eine 0–10 Skala normiert.
        """
        sv: StateVector = {}

        # PatternCore – Aktivität (Anzahl aktiver Punkte)
        pattern = snapshot.get("pattern", {})
        sv["pattern"] = self._safe_get(pattern, "summary", "nonzero", default=0.0) or 0.0

        # StructureWeaver – Komplexität
        structure = snapshot.get("structure", {})
        sv["structure"] = self._safe_get(structure, "summary", "complexity", default=0.0) or 0.0

        # PointEngine – Intensität
        points = snapshot.get("points", {})
        sv["points"] = self._safe_get(points, "summary", "intensity", default=0.0) or 0.0

        # PointDynamics – Dynamik-Level
        dynamics = snapshot.get("dynamics", {})
        sv["dynamics"] = self._safe_get(dynamics, "summary", "dynamics", default=0.0) or 0.0

        # TemporalSynth – vereinfachter Signaturbetrag
        temporal = snapshot.get("temporal", {})
        sig = temporal.get("ChronoMaps", {}).get("signature_vector")
        if isinstance(sig, list) and sig:
            sv["temporal"] = sum(abs(float(x)) for x in sig) / len(sig)
        else:
            sv["temporal"] = 0.0

        # CoherenceAgent – Kohärenzwert (0–1)
        coherence = snapshot.get("coherence", {})
        sv["coherence"] = self._safe_get(coherence, "summary", "coherence_score", default=0.0) or 0.0

        # AnomalyAgent – Anomaliedichte (Normierung über 10)
        anomaly = snapshot.get("anomaly", {})
        total_anoms = self._safe_get(anomaly, "summary", "total_anomalies", default=0.0) or 0.0
        sv["anomaly"] = total_anoms

        # FusionAgent – MetaScore (0–1)
        fusion = snapshot.get("fusion", {})
        sv["fusion"] = self._safe_get(fusion, "summary", "meta_score", default=0.0) or 0.0

        return sv
    # ----------------------------------------------------------
    # Drift-Vektor & Normierung
    # ----------------------------------------------------------
    def _compute_drift_vector(self, prev: StateVector, curr: StateVector):
        """
        Erstellt einen Drift-Vektor pro Achse:
            prev, curr, delta, abs_delta, norm_delta (0–1)
        """
        vector: Dict[str, Dict[str, float]] = {}

        axes = sorted(set(prev.keys()) | set(curr.keys()))

        for axis in axes:
            p = float(prev.get(axis, 0.0))
            c = float(curr.get(axis, 0.0))
            delta = c - p
            abs_delta = abs(delta)

            # Normierung: relative Änderung, gekappt auf 1.0
            denom = max(abs(p), abs(c), 1.0)  # damit 0 nicht explodiert
            norm_delta = min(abs_delta / denom, 1.0)

            vector[axis] = {
                "prev": p,
                "curr": c,
                "delta": delta,
                "abs_delta": abs_delta,
                "norm_delta": norm_delta,
            }

        return vector

    # ----------------------------------------------------------
    # Globaler Driftscore
    # ----------------------------------------------------------
    def _compute_global_score(self, vector: Dict[str, Dict[str, float]]) -> float:
        """
        Globaler Driftscore = Durchschnitt der norm_delta-Werte über alle Achsen.

        0.0 = praktisch keine Drift
        1.0 = maximale relative Drift
        """
        vals = [axis_info["norm_delta"] for axis_info in vector.values()]
        if not vals:
            return 0.0
        score = sum(vals) / len(vals)
        return max(0.0, min(1.0, score))

    # ----------------------------------------------------------
    # Drift-Klassifikation
    # ----------------------------------------------------------
    def _classify_drift(self, global_score: float) -> str:
        """
        Ordnet dem globalen Driftscore eine verbale Bezeichnung zu.
        """
        if global_score < 0.15:
            return "stable"
        if global_score < 0.35:
            return "mild"
        if global_score < 0.60:
            return "moderate"
        if global_score < 0.85:
            return "strong"
        return "extreme"

    def _dominant_axis(self, vector: Dict[str, Dict[str, float]]) -> Optional[str]:
        """
        Welche Achse driftet am stärksten? (nach norm_delta)
        """
        best_axis = None
        best_val = -1.0
        for axis, info in vector.items():
            nd = info.get("norm_delta", 0.0)
            if nd > best_val:
                best_val = nd
                best_axis = axis
        return best_axis

    # ----------------------------------------------------------
    # Profilaufbau
    # ----------------------------------------------------------
    def build_profile(
        self,
        previous_snapshot: Dict[str, Any],
        current_snapshot: Dict[str, Any],
        *,
        with_debug: bool = True,
    ):
        debug: Dict[str, Any] = {}

        prev_vec = self._extract_state_vector(previous_snapshot)
        curr_vec = self._extract_state_vector(current_snapshot)

        if with_debug:
            debug["prev_state_vector"] = prev_vec
            debug["curr_state_vector"] = curr_vec

        drift_vec = self._compute_drift_vector(prev_vec, curr_vec)
        if with_debug:
            debug["drift_vector"] = drift_vec

        global_score = self._compute_global_score(drift_vec)
        if with_debug:
            debug["global_score"] = global_score

        label = self._classify_drift(global_score)
        dom_axis = self._dominant_axis(drift_vec)

        profile = {
            "summary": {
                "global_score": global_score,
                "drift_label": label,
                "dominant_axis": dom_axis,
            },
            "vector": drift_vec,
            "previous_raw": previous_snapshot,
            "current_raw": current_snapshot,
        }

        return profile, debug
    # ----------------------------------------------------------
    # Vollständige Pipeline – drift_full
    # ----------------------------------------------------------
    def drift_full(
        self,
        previous_snapshot: Dict[str, Any],
        current_snapshot: Dict[str, Any],
        *,
        with_debug: bool = True,
    ):
        """
        Führt die komplette Driftanalyse durch.
        """
        profile, debug = self.build_profile(
            previous_snapshot,
            current_snapshot,
            with_debug=with_debug,
        )
        return profile, debug


# ======================================================================
# Self-Test
# ======================================================================
if __name__ == "__main__":
    # Einfacher Beispieltest
    prev = {
        "pattern": {"summary": {"nonzero": 3}},
        "structure": {"summary": {"complexity": 4}},
        "points": {"summary": {"intensity": 5}},
        "dynamics": {"summary": {"dynamics": 2}},
        "temporal": {"ChronoMaps": {"signature_vector": [0.2, 0.3]}},
        "coherence": {"summary": {"coherence_score": 0.7}},
        "anomaly": {"summary": {"total_anomalies": 1}},
        "fusion": {"summary": {"meta_score": 0.65}},
    }

    curr = {
        "pattern": {"summary": {"nonzero": 5}},
        "structure": {"summary": {"complexity": 7}},
        "points": {"summary": {"intensity": 9}},
        "dynamics": {"summary": {"dynamics": 4}},
        "temporal": {"ChronoMaps": {"signature_vector": [0.4, 0.6]}},
        "coherence": {"summary": {"coherence_score": 0.5}},
        "anomaly": {"summary": {"total_anomalies": 3}},
        "fusion": {"summary": {"meta_score": 0.55}},
    }

    agent = DriftAgent()
    res = agent.run("drift_full", {"previous": prev, "current": curr}, with_debug=True)

    from pprint import pprint
    print("OK:", res["ok"])
    print("\nSUMMARY:")
    pprint(res["result"]["summary"])
    print("\nVECTOR:")
    pprint(res["result"]["vector"])
