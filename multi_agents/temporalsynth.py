"""
TemporalSynth 0.3 – Offline, class-based, with Tool-API
-------------------------------------------------------

Einheitlicher Agent für Zeitstruktur-Analyse im Saham-Lab.

Features:
- Vollständige Pipeline:
    collect -> normalize -> overlap -> divergence -> phasegrid -> signature
- Class-basierter Agent (TemporalSynth)
- Offline-only (keine OpenAI-Abhängigkeit)
- Tool-API für Orchestrator/Dirigent:
    - TOOL_SPECS: Beschreibung der Funktionen
    - TemporalSynth.invoke_tool(name, **kwargs)

Kompatibel mit:
- direkter Python-Nutzung
- zukünftiger Orchestrator-Anbindung
"""

from typing import Dict, List, Any, Optional
import hashlib


# ---------------------------------------------------------------------------
# Hilfsfunktionen (intern)
# ---------------------------------------------------------------------------

def _to_list(x: Any) -> List[float]:
    """
    Konvertiert beliebige Eingaben in eine Float-Liste.
    Nur Listen werden akzeptiert, alles andere gibt eine leere Liste.
    """
    if isinstance(x, list):
        return x
    return []


# ---------------------------------------------------------------------------
# Kernagent: TemporalSynth
# ---------------------------------------------------------------------------

class TemporalSynth:
    """
    TemporalSynth 0.3 – zentraler Zeitstruktur-Agent.

    Verarbeitet parallele Sequenzen von Agenten-Aktivitäten:
    - patterns
    - structures
    - points
    - motion

    und erzeugt:
    - ChronoMaps (Axis, Overlaps, Divergenz, PhaseGrid, Signatur)
    - Debug-Struktur mit allen Zwischenstufen
    """

    def __init__(self, name: str = "TemporalSynth", version: str = "0.3") -> None:
        self.name = name
        self.version = version

    # ------------------------------------------------------------------
    # STUFE 1 – Collect
    # ------------------------------------------------------------------
    def collect(
        self,
        patterns: Any,
        structures: Any,
        points: Any,
        motion: Any,
    ) -> Dict[str, Any]:
        """
        Collect-Layer: Rohdaten aus den Agenten einsammeln.
        """
        return {
            "stage": "collect",
            "patterns": _to_list(patterns),
            "structures": _to_list(structures),
            "points": _to_list(points),
            "motion": _to_list(motion),
        }

    # ------------------------------------------------------------------
    # STUFE 2 – Normalize
    # ------------------------------------------------------------------
    def normalize(self, collect_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        Master-Zeitachse erstellen und Aktivität pro Agent pro Zeitschritt
        auf eine gemeinsame Achse bringen.
        """
        p = collect_res.get("patterns", [])
        s = collect_res.get("structures", [])
        pt = collect_res.get("points", [])
        m = collect_res.get("motion", [])

        max_len = max(len(p), len(s), len(pt), len(m), 1)
        axis = list(range(max_len))

        def activity(seq: List[float]) -> List[int]:
            act = []
            for i in range(max_len):
                v = seq[i] if i < len(seq) else 0
                # alles != 0 gilt als "aktiv"
                act.append(1 if v != 0 else 0)
            return act

        norm = {
            "stage": "normalize",
            "axis": axis,
            "patterns_act": activity(p),
            "structures_act": activity(s),
            "points_act": activity(pt),
            "motion_act": activity(m),
        }
        return norm

    # ------------------------------------------------------------------
    # STUFE 3 – Overlap
    # ------------------------------------------------------------------
    def overlap(self, norm: Dict[str, Any]) -> Dict[str, Any]:
        """
        Overlaps: Zeitschritte, in denen mehrere Agenten gleichzeitig aktiv sind.
        """
        axis = norm["axis"]
        pa = norm["patterns_act"]
        sa = norm["structures_act"]
        pta = norm["points_act"]
        ma = norm["motion_act"]

        overlaps = []
        for i, t in enumerate(axis):
            active_agents = []
            if pa[i]:
                active_agents.append("patterns")
            if sa[i]:
                active_agents.append("structures")
            if pta[i]:
                active_agents.append("points")
            if ma[i]:
                active_agents.append("motion")
            if len(active_agents) >= 2:
                overlaps.append({"t": t, "agents": active_agents})

        return {
            "stage": "overlap",
            "overlaps": overlaps,
        }

    # ------------------------------------------------------------------
    # STUFE 4 – Divergence
    # ------------------------------------------------------------------
    def divergence(self, norm: Dict[str, Any]) -> Dict[str, Any]:
        """
        Divergenz: Wie stark unterscheiden sich die Agenten-Aktivitäten
        pro Zeitschritt? Einfache Varianz der Aktivitätsvektoren.
        """
        axis = norm["axis"]
        pa = norm["patterns_act"]
        sa = norm["structures_act"]
        pta = norm["points_act"]
        ma = norm["motion_act"]

        div_vec: List[float] = []
        for i, _ in enumerate(axis):
            vals = [pa[i], sa[i], pta[i], ma[i]]
            mean = sum(vals) / 4.0
            var = sum((v - mean) ** 2 for v in vals) / 4.0
            div_vec.append(var)

        avg_div = sum(div_vec) / len(div_vec) if div_vec else 0.0

        return {
            "stage": "divergence",
            "divergence_vector": div_vec,
            "avg_divergence": avg_div,
        }

    # ------------------------------------------------------------------
    # STUFE 5 – PhaseGrid
    # ------------------------------------------------------------------
    def phasegrid(
        self,
        norm: Dict[str, Any],
        overlap_res: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        PhaseGrid: Einfache Phasentypen pro Zeitschritt.
        Klassifikation anhand der aktiven Agenten und Overlaps.
        """
        axis = norm["axis"]
        pa = norm["patterns_act"]
        sa = norm["structures_act"]
        pta = norm["points_act"]
        ma = norm["motion_act"]

        overlap_by_t = {o["t"]: o["agents"] for o in overlap_res.get("overlaps", [])}

        grid: List[Dict[str, Any]] = []
        for i, t in enumerate(axis):
            act_count = pa[i] + sa[i] + pta[i] + ma[i]
            if act_count == 0:
                phase = "quiet"
            elif t in overlap_by_t:
                agents = overlap_by_t[t]
                if "motion" in agents:
                    phase = "motion_sync"
                else:
                    phase = "multi_sync"
            elif ma[i]:
                phase = "motion_only"
            elif pa[i] or sa[i] or pta[i]:
                phase = "single_active"
            else:
                phase = "unknown"
            grid.append({"t": t, "phase": phase})

        return {
            "stage": "phasegrid",
            "grid": grid,
        }

    # ------------------------------------------------------------------
    # STUFE 6 – Signature
    # ------------------------------------------------------------------
    def signature(
        self,
        norm: Dict[str, Any],
        overlap_res: Dict[str, Any],
        div_res: Dict[str, Any],
        phasegrid_res: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Signatur: kompakte Fingerabdrücke aus den vorherigen Strukturen.
        Liefert eine numerische Vektor-Signatur + Hash.
        """
        axis = norm["axis"]
        div_vec = div_res.get("divergence_vector", [])
        overlaps = overlap_res.get("overlaps", [])
        grid = phasegrid_res.get("grid", [])

        total = len(axis) or 1
        quiet = sum(1 for g in grid if g["phase"] == "quiet")
        multi_sync = sum(1 for g in grid if g["phase"] == "multi_sync")
        motion_sync = sum(1 for g in grid if g["phase"] == "motion_sync")

        quiet_ratio = quiet / total
        multi_ratio = multi_sync / total
        motion_ratio = motion_sync / total
        avg_div = div_res.get("avg_divergence", 0.0)
        overlap_count = len(overlaps)

        signature_vector = [
            quiet_ratio,
            multi_ratio,
            motion_ratio,
            avg_div,
            overlap_count,
        ]

        sig_str = "|".join(f"{x:.4f}" for x in signature_vector)
        sig_hash = hashlib.sha256(sig_str.encode("utf-8")).hexdigest()[:16]

        return {
            "stage": "signature",
            "signature_vector": signature_vector,
            "signature_hash": f"TSIG-{sig_hash}",
        }

    # ------------------------------------------------------------------
    # GESAMT-PIPELINE
    # ------------------------------------------------------------------
    def full_pipeline(
        self,
        patterns: Any,
        structures: Any,
        points: Any,
        motion: Any,
        with_debug: bool = True,
    ) -> Dict[str, Any]:
        """
        Volle TemporalSynth-Pipeline.

        Gibt standardmäßig:
        - "ChronoMaps": komprimierte Auswertung
        - "debug": alle Zwischenstufen (abschaltbar)
        """
        collect = self.collect(patterns, structures, points, motion)
        norm = self.normalize(collect)
        overlap_res = self.overlap(norm)
        div_res = self.divergence(norm)
        phasegrid_res = self.phasegrid(norm, overlap_res)
        sig = self.signature(norm, overlap_res, div_res, phasegrid_res)

        result: Dict[str, Any] = {
            "ChronoMaps": {
                "axis": norm["axis"],
                "overlaps": overlap_res["overlaps"],
                "divergence_vector": div_res["divergence_vector"],
                "phasegrid": phasegrid_res["grid"],
                "signature": sig,
            }
        }

        if with_debug:
            result["debug"] = {
                "collect": collect,
                "normalize": norm,
                "overlap": overlap_res,
                "divergence": div_res,
                "phasegrid": phasegrid_res,
                "signature": sig,
            }

        return result

    # ------------------------------------------------------------------
    # GENERISCHE RUN/TOOL-SCHNITTSTELLE FÜR ORCHESTRATOR
    # ------------------------------------------------------------------

    def run(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generische Run-Schnittstelle für Orchestrator/Dirigent.

        task:
            - "temporal_full"
            - "temporal_collect"
            - "temporal_normalize"
            - "temporal_overlap"
            - "temporal_divergence"
            - "temporal_phasegrid"
            - "temporal_signature"

        payload: Parameter entsprechend der Aufgabe.
        """
        if task == "temporal_full":
            return self.full_pipeline(
                payload.get("patterns", []),
                payload.get("structures", []),
                payload.get("points", []),
                payload.get("motion", []),
                with_debug=payload.get("with_debug", True),
            )

        if task == "temporal_collect":
            return self.collect(
                payload.get("patterns", []),
                payload.get("structures", []),
                payload.get("points", []),
                payload.get("motion", []),
            )

        if task == "temporal_normalize":
            return self.normalize(payload.get("collect_result", {}))

        if task == "temporal_overlap":
            return self.overlap(payload.get("normalize_result", {}))

        if task == "temporal_divergence":
            return self.divergence(payload.get("normalize_result", {}))

        if task == "temporal_phasegrid":
            return self.phasegrid(
                payload.get("normalize_result", {}),
                payload.get("overlap_result", {}),
            )

        if task == "temporal_signature":
            return self.signature(
                payload.get("normalize_result", {}),
                payload.get("overlap_result", {}),
                payload.get("divergence_result", {}),
                payload.get("phasegrid_result", {}),
            )

        return {"error": f"Unknown TemporalSynth task: {task}"}

    def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper um .run(), damit ein Orchestrator die gleiche Signatur wie
        bei OpenAI-Toolcalls verwenden kann.
        """
        return self.run(tool_name, arguments)


# ---------------------------------------------------------------------------
# TOOL-SPECS – für Orchestrator/Dirigent (offline, aber kompatibel)
# ---------------------------------------------------------------------------

TOOL_SPECS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "temporal_full",
            "description": "Führt die komplette TemporalSynth-Pipeline aus.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patterns": {"type": "array", "items": {"type": "number"}},
                    "structures": {"type": "array", "items": {"type": "number"}},
                    "points": {"type": "array", "items": {"type": "number"}},
                    "motion": {"type": "array", "items": {"type": "number"}},
                    "with_debug": {"type": "boolean"},
                },
                "required": ["patterns", "structures", "points", "motion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "temporal_collect",
            "description": "Nur die Collect-Phase von TemporalSynth.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patterns": {"type": "array", "items": {"type": "number"}},
                    "structures": {"type": "array", "items": {"type": "number"}},
                    "points": {"type": "array", "items": {"type": "number"}},
                    "motion": {"type": "array", "items": {"type": "number"}},
                },
                "required": ["patterns", "structures", "points", "motion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "temporal_normalize",
            "description": "Normalisiert eine TemporalSynth-Collect-Struktur.",
            "parameters": {
                "type": "object",
                "properties": {
                    "collect_result": {"type": "object"},
                },
                "required": ["collect_result"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "temporal_overlap",
            "description": "Berechnet Overlaps aus einer Normalisierungsstruktur.",
            "parameters": {
                "type": "object",
                "properties": {
                    "normalize_result": {"type": "object"},
                },
                "required": ["normalize_result"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "temporal_divergence",
            "description": "Berechnet Divergenz aus einer Normalisierungsstruktur.",
            "parameters": {
                "type": "object",
                "properties": {
                    "normalize_result": {"type": "object"},
                },
                "required": ["normalize_result"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "temporal_phasegrid",
            "description": "Berechnet PhaseGrid aus Normalisierung + Overlaps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "normalize_result": {"type": "object"},
                    "overlap_result": {"type": "object"},
                },
                "required": ["normalize_result", "overlap_result"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "temporal_signature",
            "description": "Berechnet eine Zeit-Signatur aus allen Zwischenständen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "normalize_result": {"type": "object"},
                    "overlap_result": {"type": "object"},
                    "divergence_result": {"type": "object"},
                    "phasegrid_result": {"type": "object"},
                },
                "required": [
                    "normalize_result",
                    "overlap_result",
                    "divergence_result",
                    "phasegrid_result",
                ],
            },
        },
    },
]


def get_temporalsynth_tools() -> List[Dict[str, Any]]:
    """
    Liefert die Tool-Spezifikationen für TemporalSynth.
    Kann vom Orchestrator importiert werden.
    """
    return TOOL_SPECS


# ---------------------------------------------------------------------------
# BACKWARD-COMPAT: Funktions-Wrapper (falls alte Importe existieren)
# ---------------------------------------------------------------------------

# Eine globale Default-Instanz für einfache Funktionsaufrufe
_default_ts = TemporalSynth()


def ts_collect(patterns, structures, points, motion) -> Dict[str, Any]:
    return _default_ts.collect(patterns, structures, points, motion)


def ts_normalize(collect_res: Dict[str, Any]) -> Dict[str, Any]:
    return _default_ts.normalize(collect_res)


def ts_overlap(norm: Dict[str, Any]) -> Dict[str, Any]:
    return _default_ts.overlap(norm)


def ts_divergence(norm: Dict[str, Any]) -> Dict[str, Any]:
    return _default_ts.divergence(norm)


def ts_phasegrid(norm: Dict[str, Any], overlap_res: Dict[str, Any]) -> Dict[str, Any]:
    return _default_ts.phasegrid(norm, overlap_res)


def ts_signature(
    norm: Dict[str, Any],
    overlap_res: Dict[str, Any],
    div_res: Dict[str, Any],
    phasegrid_res: Dict[str, Any],
) -> Dict[str, Any]:
    return _default_ts.signature(norm, overlap_res, div_res, phasegrid_res)


def ts_full_pipeline(patterns, structures, points, motion) -> Dict[str, Any]:
    return _default_ts.full_pipeline(patterns, structures, points, motion)


# ---------------------------------------------------------------------------
# DEMO
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_patterns = [1, 0, 2, 0, 3]
    demo_structs = [0, 1, 0, 1, 0]
    demo_points = [0, 0, 5, 0, 0]
    demo_motion = [0, 1, 1, 0, 0]

    ts = TemporalSynth()
    res = ts.full_pipeline(
        demo_patterns,
        demo_structs,
        demo_points,
        demo_motion,
        with_debug=False,
    )

    from pprint import pprint
    pprint(res)
