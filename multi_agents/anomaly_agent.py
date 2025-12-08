"""
anomaly_agent.py – Agent 7: AnomalyAgent (Saham-Lab)
----------------------------------------------------

Zweck:
    Erkennung von Ausreißern (Anomalien) in numerischen Sequenzen.

Design:
    - Vollständig offline, deterministisch.
    - Orchestrator-kompatible API:
        AnomalyAgent.run(task, payload, with_debug=True, with_diagnostics=False)
    - Debug-Baum im Saham-Lab-Stil.
    - Für einfache Nutzung:
        - Einfache Sequenz: payload["data"] = [1, 2, 3, 99, 2, ...]
        - Mehrere Sequenzen: payload["data"] = {"seriesA": [...], "seriesB": [...]}

Resultatstruktur (anomaly_full):

{
  "series": {
    "<name>": {
      "stats": {...},
      "thresholds": {...},
      "anomalies": [
        {"index": i, "value": v, "z": z, "severity": "severe" | "moderate" | "mild"}
      ]
    },
    ...
  },
  "summary": {
    "total_points": int,
    "total_anomalies": int,
    "by_severity": {"mild": int, "moderate": int, "severe": int}
  }
}

Hinweis:
    GuardianGate / DiagnosticCore werden vom Orchestrator angebunden.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Union
import math


Number = Union[int, float]
Series = List[float]
SeriesMap = Dict[str, Series]


class AnomalyAgent:
    """
    AnomalyAgent 0.7 – Meta-Agent für die Ausreißer-Analyse.

    Unterstützt:
        - Einzel-Sequenzen (liste von Zahlen)
        - Multi-Sequenzen (dict: name -> liste von Zahlen)

    Stufen:
        1) parse_input   -> Datenstruktur vereinheitlichen
        2) normalize     -> optionale Normalisierung (derzeit: passthrough, reserviert)
        3) stats         -> Mittelwert/Std
        4) zscores       -> z-Werte
        5) detect        -> Schwellwert-basierte Anomalien
        6) build_profile -> strukturierter Report
        7) anomaly_full  -> kompakte Ergebnisansicht
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
        with_diagnostics: bool = False,  # reserviert für spätere Erweiterung
    ) -> Dict[str, Any]:
        """
        Einheitlicher Einstiegspunkt für den Orchestrator.

        Erwartet:
            task   : "anomaly_full" oder "anomaly_profile"
            payload: {"data": <sequence or mapping of sequences>}

        Rückgabe:
            {
                "ok": bool,
                "result": {...} oder None,
                "debug": {...} oder {},
            }
        """
        data = payload.get("data", None)

        # Grundvalidierung
        if data is None:
            return {
                "ok": False,
                "result": None,
                "debug": {"error": "payload['data'] fehlt."},
            }

        # Task-Dispatch
        if task == "anomaly_full":
            result, debug = self.anomaly_full(data, with_debug=with_debug)
            return {
                "ok": True,
                "result": result,
                "debug": debug if with_debug else {},
            }

        if task == "anomaly_profile":
            profile, debug = self.build_profile(data, with_debug=with_debug)
            return {
                "ok": True,
                "result": profile,
                "debug": debug if with_debug else {},
            }

        # Unbekannte Aufgabe
        return {
            "ok": False,
            "result": None,
            "debug": {"error": f"Unknown AnomalyAgent task '{task}'"},
        }

    # ------------------------------------------------------------------
    # Stufe 0 – Input vereinheitlichen
    # ------------------------------------------------------------------
    def _to_float_series(self, seq: Any) -> Series:
        """
        Versucht, eine Folge von Zahlen in eine Float-Liste zu konvertieren.
        Nicht-numerische Einträge werden ignoriert.
        """
        if not isinstance(seq, (list, tuple)):
            return []

        out: List[float] = []
        for x in seq:
            if isinstance(x, (int, float)):
                out.append(float(x))
        return out

    def parse_input(self, data: Any) -> SeriesMap:
        """
        Akzeptiert:
            - Liste/Tuple   -> eine Serie "series_0"
            - Dict[str, ..] -> mehrere Serien, Werte werden als Sequenzen interpretiert

        Liefert immer: dict(name -> List[float])
        """
        series_map: SeriesMap = {}

        # Einzel-Sequenz
        if isinstance(data, (list, tuple)):
            series = self._to_float_series(data)
            if series:
                series_map["series_0"] = series
            return series_map

        # Mapping mit mehreren Sequenzen
        if isinstance(data, dict):
            for key, value in data.items():
                seq = self._to_float_series(value)
                if seq:
                    series_map[str(key)] = seq
            return series_map

        # Fallback: unbekannte Struktur -> leere Map
        return {}

    # ------------------------------------------------------------------
    # Stufe 1 – (Optionale) Normalisierung
    # ------------------------------------------------------------------
    def normalize_series(self, series: Series) -> Series:
        """
        Reserviert für zukünftige Normalisierungen.
        Aktuell: passthrough (keine Veränderung).
        """
        return list(series)

    def normalize(self, series_map: SeriesMap) -> SeriesMap:
        """
        Normalisiert alle Serien (aktuell nur Kopie).
        """
        return {name: self.normalize_series(seq) for name, seq in series_map.items()}
    # ------------------------------------------------------------------
    # Stufe 2 – Statistik (Mittelwert & Standardabweichung)
    # ------------------------------------------------------------------
    def compute_stats(self, series: Series) -> Dict[str, float]:
        """
        Berechnet Basisstatistik:
            - mean
            - std
            - min
            - max
        """
        n = len(series)
        if n == 0:
            return {
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0,
            }

        s = sum(series)
        mean = s / n

        var = sum((x - mean) ** 2 for x in series) / n
        std = math.sqrt(var)

        return {
            "mean": mean,
            "std": std,
            "min": min(series),
            "max": max(series),
            "count": n,
        }

    def stats_for_all(self, series_map: SeriesMap) -> Dict[str, Dict[str, float]]:
        """
        Liefert Statistik für alle Serien.
        """
        return {
            name: self.compute_stats(seq)
            for name, seq in series_map.items()
        }

    # ------------------------------------------------------------------
    # Stufe 3 – Z-Scores
    # ------------------------------------------------------------------
    def zscores_for_series(self, series: Series, stats: Dict[str, float]) -> Series:
        """
        Berechnet Z-Scores einer Serie:
            z = (x - mean) / std
        Falls std == 0 -> z = 0.
        """
        n = len(series)
        if n == 0:
            return []

        mean = stats.get("mean", 0.0)
        std = stats.get("std", 0.0)

        if std == 0.0:
            return [0.0 for _ in series]

        return [(x - mean) / std for x in series]

    def zscores_for_all(
        self,
        series_map: SeriesMap,
        stats_map: Dict[str, Dict[str, float]],
    ) -> Dict[str, Series]:
        """
        Berechnet Z-Scores für alle Serien.
        """
        z_map: Dict[str, Series] = {}
        for name, seq in series_map.items():
            stats = stats_map.get(name, {})
            z_map[name] = self.zscores_for_series(seq, stats)
        return z_map

    # ------------------------------------------------------------------
    # Stufe 4 – Anomalien erkennen
    # ------------------------------------------------------------------
    def severity_from_z(self, z: float) -> str:
        """
        Ordnet einem Z-Wert eine Schwere zu.
        """
        az = abs(z)
        if az >= 3.5:
            return "severe"
        if az >= 2.5:
            return "moderate"
        if az >= 1.5:
            return "mild"
        return "none"

    def detect_anomalies_for_series(
        self,
        series: Series,
        zscores: Series,
        *,
        z_min: float = 1.5,
    ) -> List[Dict[str, Any]]:
        """
        Sucht Anomalien in einer Serie basierend auf Z-Werten.

        Nur Werte mit |z| >= z_min werden gemeldet.
        """
        anomalies: List[Dict[str, Any]] = []
        for i, (x, z) in enumerate(zip(series, zscores)):
            if abs(z) < z_min:
                continue
            severity = self.severity_from_z(z)
            if severity == "none":
                continue
            anomalies.append(
                {
                    "index": i,
                    "value": x,
                    "z": z,
                    "severity": severity,
                }
            )
        return anomalies

    def detect_anomalies_for_all(
        self,
        series_map: SeriesMap,
        zscores_map: Dict[str, Series],
        *,
        z_min: float = 1.5,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Liefert Anomalien für alle Serien.
        """
        result: Dict[str, List[Dict[str, Any]]] = {}
        for name, seq in series_map.items():
            zscores = zscores_map.get(name, [])
            anomalies = self.detect_anomalies_for_series(seq, zscores, z_min=z_min)
            result[name] = anomalies
        return result

    # ------------------------------------------------------------------
    # Stufe 5 – Profil aufbauen
    # ------------------------------------------------------------------
    def build_profile(
        self,
        data: Any,
        *,
        with_debug: bool = True,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Baut ein detailliertes Anomalie-Profil über alle Serien.

        Profil:
            {
                "series": {
                    name: {
                        "stats": {...},
                        "thresholds": {...},
                        "anomalies": [...],
                    },
                    ...
                },
                "summary": {...}
            }
        """
        debug: Dict[str, Any] = {}

        # 1) Input vereinheitlichen
        series_map = self.parse_input(data)
        if with_debug:
            debug["series_raw"] = series_map

        # Falls keine verwertbare Serie vorhanden ist
        if not series_map:
            profile = {
                "series": {},
                "summary": {
                    "total_points": 0,
                    "total_anomalies": 0,
                    "by_severity": {"mild": 0, "moderate": 0, "severe": 0},
                },
            }
            if with_debug:
                debug["reason"] = "no_valid_series"
            return profile, debug

        # 2) Normalisieren
        normalized = self.normalize(series_map)
        if with_debug:
            debug["series_normalized"] = normalized

        # 3) Statistik
        stats_map = self.stats_for_all(normalized)
        if with_debug:
            debug["stats"] = stats_map

        # 4) Z-Scores
        z_map = self.zscores_for_all(normalized, stats_map)
        if with_debug:
            debug["zscores"] = z_map

        # 5) Anomalien
        anomalies_map = self.detect_anomalies_for_all(normalized, z_map, z_min=1.5)
        if with_debug:
            debug["anomalies"] = anomalies_map

        # 6) Threshold-Info pro Serie (nur Z-Grenzen dokumentieren)
        thresholds_map: Dict[str, Dict[str, float]] = {}
        for name in series_map.keys():
            thresholds_map[name] = {
                "z_mild": 1.5,
                "z_moderate": 2.5,
                "z_severe": 3.5,
            }
        if with_debug:
            debug["thresholds"] = thresholds_map

        # 7) Gesamt-Summary
        total_points = sum(stats["count"] for stats in stats_map.values())
        total_anomalies = sum(len(a) for a in anomalies_map.values())

        by_severity = {"mild": 0, "moderate": 0, "severe": 0}
        for series_anoms in anomalies_map.values():
            for a in series_anoms:
                sev = a.get("severity", "none")
                if sev in by_severity:
                    by_severity[sev] += 1

        profile_series: Dict[str, Any] = {}
        for name in series_map.keys():
            profile_series[name] = {
                "stats": stats_map.get(name, {}),
                "thresholds": thresholds_map.get(name, {}),
                "anomalies": anomalies_map.get(name, []),
            }

        profile: Dict[str, Any] = {
            "series": profile_series,
            "summary": {
                "total_points": total_points,
                "total_anomalies": total_anomalies,
                "by_severity": by_severity,
            },
        }

        return profile, debug
    # ------------------------------------------------------------------
    # Stufe 6 – Kompaktansicht (anomaly_full)
    # ------------------------------------------------------------------
    def anomaly_full(
        self,
        data: Any,
        *,
        with_debug: bool = True,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Führt die komplette Anomalie-Pipeline aus und liefert ein
        kompaktes Resultat + Debug-Baum.

        Kompaktresultat:
            {
                "series": {... wie in build_profile["series"] ...},
                "summary": {...}
            }

        (Der Unterschied zu build_profile ist hier klein – reserviert
         für spätere Reduktionen / andere Sichten.)
        """
        profile, debug = self.build_profile(data, with_debug=with_debug)
        # Aktuell geben wir das Profil direkt weiter.
        return profile, debug


# ----------------------------------------------------------------------
# Self-Test (Direktstart) – optional, stört Import nicht
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Kleiner Selbsttest zur schnellen Prüfung in der Sandbox
    demo_data = {
        "series_A": [1, 2, 2, 3, 2, 2, 100, 2, 3],
        "series_B": [10, 11, 10.5, 9.8, 10.2, 50, 10.1],
        "series_C": [0, 0, 0, 0, 0],  # keine Varianz
    }

    agent = AnomalyAgent()
    res = agent.run("anomaly_full", {"data": demo_data}, with_debug=True)

    from pprint import pprint

    print("OK:", res["ok"])
    print("\nSUMMARY:")
    pprint(res["result"]["summary"])

    print("\nSERIES KEYS:", list(res["result"]["series"].keys()))
    for name, info in res["result"]["series"].items():
        print(f"\n{name}:")
        print("  Stats:", info["stats"])
        print("  Thresholds:", info["thresholds"])
        print("  #Anomalies:", len(info["anomalies"]))
        if info["anomalies"]:
            print("  First anomaly example:", info["anomalies"][0])

