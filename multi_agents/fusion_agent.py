"""
fusion_agent.py – Agent 8: FusionAgent (Saham-Lab HQ-Standard)
--------------------------------------------------------------

Zweck:
    Meta-Integrator. Führt die Kernausgaben anderer Agenten
    (PatternCore, StructureWeaver, PointEngine, PointDynamics,
     TemporalSynth, CoherenceAgent, AnomalyAgent)
    zu einer gemeinsamen Meta-Signatur zusammen.

Pipeline:
    collect()      -> extrahiert Kernwerte
    metrics()      -> rechnet alles in vergleichbare Metriken um
    classify()     -> bestimmt qualitative Einstufungen
    build_profile() -> vollständiger Report
    fusion_full()  -> kompakte Ausgabe

Design:
    Voll kompatibel zum Orchestrator, deterministisch, debuggable.
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Optional
import math


class FusionAgent:
    """
    FusionAgent 1.0 – Meta-Fusionsinstanz im Saham-Lab.

    Er vereint:
        - Musteraktivität
        - Strukturdichte
        - Punktintensität
        - Dynamik-Level
        - Zeit-Signaturen (TemporalSynth)
        - Kohärenz (CoherenceAgent)
        - Anomalie-Intensität (AnomalyAgent)

    Ziel:
        Eine robuste, normalisierte Meta-Signatur erzeugen,
        die das Gesamtsystem auf einen Blick beschreibt.
    """

    # ----------------------------------------------------------
    # ORCHESTRATOR-COMPATIBLE API
    # ----------------------------------------------------------
    def run(
        self,
        task: str,
        payload: Dict[str, Any],
        *,
        with_debug: bool = True,
        with_diagnostics: bool = False,
    ) -> Dict[str, Any]:

        data = payload.get("data", None)

        if data is None:
            return {
                "ok": False,
                "result": None,
                "debug": {"error": "payload['data'] fehlt"},
            }

        # Task-Dispatch
        if task == "fusion_full":
            result, debug = self.fusion_full(data, with_debug=with_debug)
            return {
                "ok": True,
                "result": result,
                "debug": debug if with_debug else {},
            }

        if task == "fusion_profile":
            profile, debug = self.build_profile(data, with_debug=with_debug)
            return {
                "ok": True,
                "result": profile,
                "debug": debug if with_debug else {},
            }

        return {
            "ok": False,
            "result": None,
            "debug": {"error": f"Unknown FusionAgent task '{task}'"},
        }

    # ----------------------------------------------------------
    # INPUT NORMALIZATION
    # ----------------------------------------------------------
    def parse_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Erwartet ein Mapping der Art:
            {
                "pattern": {...},
                "structure": {...},
                "points": {...},
                "dynamics": {...},
                "temporal": {...},
                "coherence": {...},
                "anomaly": {...}
            }
        Fehlende Quellen sind erlaubt, werden aber dokumentiert.
        """
        if not isinstance(data, dict):
            return {}

        # Wir kopieren nur Keys, die wir erkennen
        allowed = {
            "pattern",
            "structure",
            "points",
            "dynamics",
            "temporal",
            "coherence",
            "anomaly",
        }

        out = {}
        for k, v in data.items():
            if k in allowed:
                out[k] = v
        return out

    # ----------------------------------------------------------
    # PIPELINE STUFE 1: COLLECT
    # ----------------------------------------------------------
    def collect(self, d: Dict[str, Any]) -> Dict[str, float]:
        """
        Extrahiert Kerninformationen aus allen Quellen.
        Fehlende Quellen werden als None markiert.
        """
        c = {}

        # PatternCore – erwartete Struktur: {"summary": {...}}
        pc = d.get("pattern")
        c["pattern_activity"] = (
            pc.get("summary", {}).get("nonzero") if isinstance(pc, dict) else None
        )

        # StructureWeaver – {"summary": {"complexity": x}}
        sw = d.get("structure")
        c["structure_complexity"] = (
            sw.get("summary", {}).get("complexity")
            if isinstance(sw, dict)
            else None
        )

        # PointEngine – {"summary": {"intensity": x}}
        pe = d.get("points")
        c["point_intensity"] = (
            pe.get("summary", {}).get("intensity")
            if isinstance(pe, dict)
            else None
        )

        # PointDynamics – {"summary": {"dynamics": x}}
        pd = d.get("dynamics")
        c["dynamics_level"] = (
            pd.get("summary", {}).get("dynamics")
            if isinstance(pd, dict)
            else None
        )

        # TemporalSynth – {"ChronoMaps": {"signature_vector": [...]}}
        ts = d.get("temporal")
        c["temporal_signature"] = (
            ts.get("ChronoMaps", {}).get("signature_vector")
            if isinstance(ts, dict)
            else None
        )

        # CoherenceAgent – {"summary": {"coherence_score": x}}
        co = d.get("coherence")
        c["coherence_score"] = (
            co.get("summary", {}).get("coherence_score")
            if isinstance(co, dict)
            else None
        )

        # AnomalyAgent – {"summary": {"total_anomalies": x}}
        an = d.get("anomaly")
        c["anomaly_intensity"] = (
            an.get("summary", {}).get("total_anomalies")
            if isinstance(an, dict)
            else None
        )

        return c
    # ----------------------------------------------------------
    # PIPELINE STUFE 2: METRICS (Normalisierung)
    # ----------------------------------------------------------
    def _norm(self, x: Optional[float], scale: float = 1.0) -> float:
        """
        Normalisiert Werte robust.
        Wenn x fehlt oder nicht brauchbar ist → 0.
        """
        if x is None:
            return 0.0
        try:
            return float(x) / scale
        except:
            return 0.0

    def metrics(self, c: Dict[str, Any]) -> Dict[str, float]:
        """
        Rechnet die gesammelten Werte in einheitliche Normalbereiche um.
        """
        return {
            "pattern_n": self._norm(c.get("pattern_activity"), 10.0),
            "structure_n": self._norm(c.get("structure_complexity"), 10.0),
            "points_n": self._norm(c.get("point_intensity"), 10.0),
            "dynamics_n": self._norm(c.get("dynamics_level"), 10.0),
            "coherence_n": self._norm(c.get("coherence_score"), 1.0),
            "anomaly_n": self._norm(c.get("anomaly_intensity"), 10.0),
            "temporal_vec": c.get("temporal_signature", None),
        }

    # ----------------------------------------------------------
    # PIPELINE STUFE 3: CLASSIFY
    # ----------------------------------------------------------
    def classify(self, m: Dict[str, Any]) -> Dict[str, Any]:
        """
        Klassifiziert die normalisierten Metriken qualitativ.
        """
        def level(x):
            if x >= 0.75:
                return "high"
            if x >= 0.40:
                return "medium"
            return "low"

        return {
            "pattern_level": level(m.get("pattern_n", 0)),
            "structure_level": level(m.get("structure_n", 0)),
            "points_level": level(m.get("points_n", 0)),
            "dynamics_level": level(m.get("dynamics_n", 0)),
            "coherence_level": level(m.get("coherence_n", 0)),
            "anomaly_level": (
                "high" if m.get("anomaly_n", 0) >= 0.5 else "low"
            ),
        }

    # ----------------------------------------------------------
    # PIPELINE STUFE 4: MetaScore 2.0 (HQ-Norm)
    # ----------------------------------------------------------
    def compute_meta_score(self, m: Dict[str, Any]) -> float:
        """
        Fusionierter Score:
            - positieve Quellen pushen hoch
            - Anomalien drücken den Score
            - Temporal-Signatur wird als Aktivierungsgrad genutzt
        """
        pos = (
            m.get("pattern_n", 0)
            + m.get("structure_n", 0)
            + m.get("points_n", 0)
            + m.get("dynamics_n", 0)
            + m.get("coherence_n", 0)
        ) / 5.0

        neg = m.get("anomaly_n", 0)

        tv = m.get("temporal_vec")
        if isinstance(tv, list) and len(tv) > 0:
            temporal_factor = sum(abs(float(x)) for x in tv) / len(tv)
        else:
            temporal_factor = 0.5  # neutral

        # HQ-Formel
        score = (pos * 0.70) + (temporal_factor * 0.20) - (neg * 0.10)

        # clamp 0–1
        return max(0.0, min(1.0, score))

    # ----------------------------------------------------------
    # PIPELINE STUFE 5: PROFILE bauen
    # ----------------------------------------------------------
    def build_profile(self, data: Dict[str, Any], *, with_debug=True):
        debug = {}

        parsed = self.parse_input(data)
        if with_debug:
            debug["parsed"] = parsed

        collect_map = self.collect(parsed)
        if with_debug:
            debug["collect"] = collect_map

        metrics_map = self.metrics(collect_map)
        if with_debug:
            debug["metrics"] = metrics_map

        class_map = self.classify(metrics_map)
        if with_debug:
            debug["classify"] = class_map

        meta_score = self.compute_meta_score(metrics_map)
        if with_debug:
            debug["meta_score"] = meta_score

        profile = {
            "summary": {
                "meta_score": meta_score,
            },
            "classes": class_map,
            "metrics": metrics_map,
            "collect": collect_map,
        }

        return profile, debug
    # ----------------------------------------------------------
    # PIPELINE STUFE 6 – fusion_full (Kompaktsicht)
    # ----------------------------------------------------------
    def fusion_full(self, data: Dict[str, Any], *, with_debug=True):
        profile, debug = self.build_profile(data, with_debug=with_debug)
        return profile, debug


# ======================================================================
# SELF-TEST (optional)
# ======================================================================
if __name__ == "__main__":
    example = {
        "pattern": {"summary": {"nonzero": 4}},
        "structure": {"summary": {"complexity": 6}},
        "points": {"summary": {"intensity": 7}},
        "dynamics": {"summary": {"dynamics": 3}},
        "temporal": {"ChronoMaps": {"signature_vector": [0.2, 0.4, 0.1]}},
        "coherence": {"summary": {"coherence_score": 0.66}},
        "anomaly": {"summary": {"total_anomalies": 1}},
    }

    agent = FusionAgent()
    res = agent.run("fusion_full", {"data": example}, with_debug=True)

    from pprint import pprint
    pprint(res)
