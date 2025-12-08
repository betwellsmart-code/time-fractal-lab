"""
coherence_agent.py – Agent 6: CoherenceAgent (Saham-Lab)
--------------------------------------------------------

Zweck:
    Misst Kohärenz zwischen den Outputs verschiedener Agenten
    (PatternCore, StructureWeaver, PointEngine, PointDynamics, TemporalSynth, ...).

Version:
    CoherenceAgent 0.5 (A2 – modular, erweiterbar, stabil)

Design:
    - Einziger Einstiegspunkt: CoherenceAgent.run(task, payload, with_debug=..., with_diagnostics=...)
    - Interne Pipeline:
        1) collect()     -> Agentenoutputs einsammeln und in Vektoren übersetzen
        2) normalize()   -> Vektoren 0–1-normalisieren
        3) strengths()   -> Kennwerte (Normen, Dichte, Varianz, Mittelwert)
        4) pairwise()    -> paarweise Kohärenzmatrix
        5) global()      -> globaler Kohärenzscore
        6) build_profile()-> Profil aus allem
        7) coherence_full()-> kompaktes Ergebnis

Hinweis:
    Dieser Agent kennt GuardianGate / DiagnosticCore NICHT direkt.
    Die Kopplung erfolgt im Orchestrator.
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple
import math


class CoherenceAgent:
    """
    CoherenceAgent 0.5 – Meta-Agent für Saham-Lab.

    Er vergleicht die Outputs mehrerer Agenten und liefert:
        - globalen Kohärenzwert (0.0 bis 1.0)
        - paarweise Kohärenzmatrix
        - Stärkekennwerte pro Agent
        - Debug-Baum mit allen Zwischenstufen
    """

    # ------------------------------------------------------------------
    # Public API – Orchestrator-kompatibel
    # ------------------------------------------------------------------
    def run(
        self,
        task: str,
        payload: Dict[str, Any],
        *,
        with_debug: bool = True,
        with_diagnostics: bool = False,  # reserviert für spätere Erweiterungen
    ) -> Dict[str, Any]:
        """
        Einheitliche Aufruf-Signatur für den Orchestrator.

        Erwartet:
            task   : z.B. "coherence_full" oder "coherence_profile"
            payload: {"data": <dict mit agent_name -> output>}

        Rückgabe:
            {
                "ok": bool,
                "result": {...} oder None,
                "debug": {...}   oder {},
            }
        """
        data = payload.get("data", None)

        if not isinstance(data, dict):
            return {
                "ok": False,
                "result": None,
                "debug": {
                    "error": "CoherenceAgent.run erwartet payload['data'] als dict mit Agenten-Outputs."
                },
            }

        if task == "coherence_full":
            result, debug = self.coherence_full(data, with_debug=with_debug)
            return {
                "ok": True,
                "result": result,
                "debug": debug if with_debug else {},
            }

        if task == "coherence_profile":
            profile, debug = self.build_profile(data, with_debug=with_debug)
            return {
                "ok": True,
                "result": profile,
                "debug": debug if with_debug else {},
            }

        # Unbekannter Task
        return {
            "ok": False,
            "result": None,
            "debug": {"error": f"Unknown CoherenceAgent task '{task}'"},
        }

    # ------------------------------------------------------------------
    # Stufe 1 – Collect & Normalise
    # ------------------------------------------------------------------
    def collect(self, outputs: Dict[str, Any]) -> Dict[str, List[float]]:
        """
        Vereinheitlicht Agenten-Outputs in numerische Vektoren.

        Strategie:
            - dict  -> alle numerischen values einsammeln
            - list  -> alle numerischen Elemente übernehmen
            - sonst -> Länge des Strings als Fallback-Feature

        Ergebnis:
            { "agent_name": [v1, v2, ...], ... }
        """
        collected: Dict[str, List[float]] = {}

        for agent_name, out in outputs.items():
            # dict -> numerische Werte
            if isinstance(out, dict):
                vals: List[float] = []
                for v in out.values():
                    if isinstance(v, (int, float)):
                        vals.append(float(v))
                if not vals:
                    # Fallback, falls keine numerischen Werte gefunden wurden
                    vals = [float(len(out))]
                collected[agent_name] = vals

            # list/tuple -> numerische Elemente
            elif isinstance(out, (list, tuple)):
                vals = [float(x) for x in out if isinstance(x, (int, float))]
                if not vals:
                    vals = [float(len(out))]
                collected[agent_name] = vals

            # alles andere -> String-Länge als Feature
            else:
                collected[agent_name] = [float(len(str(out)))]

        return collected

    def _normalize_vector(self, vec: List[float]) -> List[float]:
        """
        Normiert einen Vektor auf den Bereich 0–1 über max-Wert.
        """
        if not vec:
            return [0.0]
        mx = max(abs(v) for v in vec)
        if mx == 0:
            return [0.0 for _ in vec]
        return [v / mx for v in vec]

    def normalize(self, collected: Dict[str, List[float]]) -> Dict[str, List[float]]:
        """
        Normiert alle Agenten-Vektoren einzeln.
        """
        return {name: self._normalize_vector(vec) for name, vec in collected.items()}

    # ------------------------------------------------------------------
    # Stufe 2 – Strengths (Stärkekennzahlen)
    # ------------------------------------------------------------------
    def compute_strength(self, vec: List[float]) -> Dict[str, float]:
        """
        Berechnet mehrere Kennwerte eines normierten Vektors:
            - l1       : Summe der Absolutwerte
            - l2       : euklidische Norm
            - mean     : Durchschnitt
            - density  : Anteil Nicht-Null-Elemente
            - variance : Varianz
        """
        if not vec:
            return {
                "l1": 0.0,
                "l2": 0.0,
                "mean": 0.0,
                "density": 0.0,
                "variance": 0.0,
            }

        length = len(vec)
        l1 = sum(abs(v) for v in vec)
        l2 = math.sqrt(sum(v * v for v in vec))
        mean = sum(vec) / length
        density = sum(1 for v in vec if v != 0.0) / length

        variance = sum((v - mean) ** 2 for v in vec) / length

        return {
            "l1": l1,
            "l2": l2,
            "mean": mean,
            "density": density,
            "variance": variance,
        }

    def strengths(self, normalized: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """
        Berechnet Strength-Profil pro Agent.
        """
        return {
            agent_name: self.compute_strength(vec)
            for agent_name, vec in normalized.items()
        }

    # ------------------------------------------------------------------
    # Stufe 3 – Pairwise Coherence
    # ------------------------------------------------------------------
    def coherence_pairwise(
        self,
        strengths: Dict[str, Dict[str, float]],
    ) -> Dict[str, Dict[str, float]]:
        """
        Berechnet paarweise Kohärenz zwischen Agenten.

        Formel (für jede Kennzahl k):
            coherence_k = 1 - |s1_k - s2_k| / max(s1_k, s2_k, 1e-9)

        Paar-Kohärenz = Durchschnitt über alle Kennzahlen.
        """
        agents = list(strengths.keys())
        matrix: Dict[str, Dict[str, float]] = {}

        for a in agents:
            matrix[a] = {}
            sA = strengths[a]
            for b in agents:
                if a == b:
                    matrix[a][b] = 1.0
                    continue

                sB = strengths[b]
                vals: List[float] = []
                for key in sA.keys():
                    x = sA[key]
                    y = sB.get(key, x)
                    denom = max(abs(x), abs(y), 1e-9)
                    score = 1.0 - abs(x - y) / denom
                    vals.append(score)

                matrix[a][b] = sum(vals) / len(vals) if vals else 0.0

        return matrix

    # ------------------------------------------------------------------
    # Stufe 4 – Globaler Kohärenz-Score
    # ------------------------------------------------------------------
    def global_coherence(self, pairwise: Dict[str, Dict[str, float]]) -> float:
        """
        Globaler Kohärenzscore = Mittelwert aller Off-Diagonalwerte.
        """
        vals: List[float] = []

        for a, row in pairwise.items():
            for b, val in row.items():
                if a == b:
                    continue
                vals.append(val)

        if not vals:
            return 1.0  # triviale Kohärenz, wenn nur ein Agent

        return sum(vals) / len(vals)

    # ------------------------------------------------------------------
    # Stufe 5 – Profil aufbauen
    # ------------------------------------------------------------------
    def build_profile(
        self,
        outputs: Dict[str, Any],
        *,
        with_debug: bool = True,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Baut ein vollständiges Kohärenz-Profil inkl. Debug-Baum.

        Profil:
            {
                "pairwise": {agent_a: {agent_b: score, ...}, ...},
                "global": <float>,
                "strengths": {agent: strength_dict, ...},
                "normalized": {agent: [..], ...},
            }
        """
        debug: Dict[str, Any] = {}

        collected = self.collect(outputs)
        if with_debug:
            debug["collected"] = collected

        normalized = self.normalize(collected)
        if with_debug:
            debug["normalized"] = normalized

        strengths = self.strengths(normalized)
        if with_debug:
            debug["strengths"] = strengths

        pairwise = self.coherence_pairwise(strengths)
        if with_debug:
            debug["pairwise"] = pairwise

        global_c = self.global_coherence(pairwise)
        if with_debug:
            debug["global"] = global_c

        profile: Dict[str, Any] = {
            "pairwise": pairwise,
            "global": global_c,
            "strengths": strengths,
            "normalized": normalized,
        }

        return profile, debug

    # ------------------------------------------------------------------
    # Stufe 6 – Full-Pipeline (kompaktes Ergebnis)
    # ------------------------------------------------------------------
    def coherence_full(
        self,
        outputs: Dict[str, Any],
        *,
        with_debug: bool = True,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Führt die komplette Kohärenz-Pipeline aus und gibt ein
        kompaktes Resultat + Debug-Baum zurück.

        Resultat:
            {
                "coherence": <float>,    # globaler Score
                "pairwise": {...},       # Matrix
                "strengths": {...},      # pro Agent
            }
        """
        profile, debug = self.build_profile(outputs, with_debug=with_debug)

        result = {
            "coherence": profile["global"],
            "pairwise": profile["pairwise"],
            "strengths": profile["strengths"],
        }

        return result, debug


# ----------------------------------------------------------------------
# Optional: Direktstart-Quicktest (manueller Aufruf)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Kleiner Selbsttest, damit HQ den Agenten schnell prüfen kann
    demo_outputs = {
        "patterncore": {"sum": 6, "max": 3},
        "structureweaver": {"nodes": 10, "edges": 7},
        "pointengine": [0, 1, 0, 1, 3],
        "pointdynamics": {"accel": 0.32, "velocity": 1.1},
        "temporalsynth": {"phase": 2, "intensity": 0.8},
    }

    agent = CoherenceAgent()
    res = agent.run("coherence_full", {"data": demo_outputs}, with_debug=True)
    from pprint import pprint

    print("OK:", res["ok"])
    print("RESULT:")
    pprint(res["result"])
    print("\nDEBUG (keys):", list(res["debug"].keys()))
