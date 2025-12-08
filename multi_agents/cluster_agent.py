"""
cluster_agent.py – Agent 13: ClusterAgent (Saham-Lab HQ Edition)

Zweck:
    Fortgeschrittene Cluster-Analyse über:
        - Zeitwerte (TimeSeries)
        - Wertestrukturen
        - Dynamik (1. Ableitung)
        - Fensterkonsistenz

Output:
    ClusterProfile 2.0
"""

from __future__ import annotations
from typing import List, Dict, Any
import math


def _to_float_list(x: Any) -> List[float]:
    if isinstance(x, list):
        return [float(v) for v in x]
    return []


class ClusterAgent:
    """
    Agent 13 – ClusterAgent
    HQ-Stufe: Multi-Domain Cluster Engine
    """

    def run(
        self,
        task: str,
        payload: Dict[str, Any],
        *,
        with_debug=True,
        with_diagnostics=False,
    ):
        values = _to_float_list(payload.get("values", []))
        k = int(payload.get("k", 3))

        if task == "cluster_full":
            result, debug = self.cluster_full(values, k, with_debug)
            return {
                "ok": True,
                "result": result,
                "debug": debug if with_debug else {},
                "diagnostics": None,
            }

        if task == "cluster_profile":
            result, debug = self.build_profile(values, k, with_debug)
            return {
                "ok": True,
                "result": result,
                "debug": debug if with_debug else {},
                "diagnostics": None,
            }

        return {"ok": False, "result": None, "debug": {"error": f"unknown task {task}"}}
    # ---------------------------------------------------------
    # 1) Basisclusterung (Intervalle)
    # ---------------------------------------------------------
    def _interval_clusters(self, values: List[float], k: int):
        if not values:
            return []

        k = max(1, k)
        vmin, vmax = min(values), max(values)

        if vmin == vmax:
            return [{
                "id": 0,
                "members": list(range(len(values))),
                "centroid": vmin,
                "spread": 0.0,
                "t_range": (0, len(values)-1),
            }]

        step = (vmax - vmin) / k
        bins = [[] for _ in range(k)]

        for idx, v in enumerate(values):
            b = int((v - vmin)/step)
            if b == k: b = k-1
            bins[b].append(idx)

        clusters = []
        for cid, m in enumerate(bins):
            if not m: continue
            cv = [values[i] for i in m]
            clusters.append({
                "id": cid,
                "members": m,
                "centroid": sum(cv)/len(cv),
                "spread": (max(cv)-min(cv)) if len(cv)>1 else 0.0,
                "t_range": (min(m), max(m)),
            })

        return clusters

    # ---------------------------------------------------------
    # 2) Dynamik-Clustering (Ableitung)
    # ---------------------------------------------------------
    def _derivative(self, values: List[float]) -> List[float]:
        if len(values) < 2:
            return [0.0]
        return [values[i+1] - values[i] for i in range(len(values)-1)]

    # ---------------------------------------------------------
    # 3) Cluster-Stärke & -Stabilität
    # ---------------------------------------------------------
    def _cluster_strength(self, clusters: List[Dict]):
        total = sum(len(c["members"]) for c in clusters)
        multi = sum(len(c["members"]) for c in clusters if len(c["members"]) > 1)
        return (multi / total) if total else 0.0

    def _cluster_stability(self, clusters: List[Dict]):
        if not clusters:
            return 0.0
        spreads = [c["spread"] for c in clusters]
        avg = sum(spreads)/len(spreads)
        return max(0.0, min(1.0, 1.0 - avg/(avg+1)))

    # ---------------------------------------------------------
    # 4) Full Pipeline
    # ---------------------------------------------------------
    def cluster_full(self, values: List[float], k: int, with_debug=True):
        base_clusters = self._interval_clusters(values, k)
        dyn_values = self._derivative(values)
        dyn_clusters = self._interval_clusters(dyn_values, k)

        strength = self._cluster_strength(base_clusters)
        stability = self._cluster_stability(base_clusters)
        dyn_strength = self._cluster_strength(dyn_clusters)
        dyn_stability = self._cluster_stability(dyn_clusters)

        result = {
            "ClusterProfile": {
                "k": k,
                "clusters": base_clusters,
                "cluster_strength": strength,
                "cluster_stability": stability,
                "dynamic_strength": dyn_strength,
                "dynamic_stability": dyn_stability,
            }
        }

        debug = {
            "values": values,
            "dyn_values": dyn_values,
            "base_clusters": base_clusters,
            "dyn_clusters": dyn_clusters,
        }

        return result, debug
    def build_profile(self, values: List[float], k: int, with_debug=True):
        full, dbg = self.cluster_full(values, k, with_debug)
        # Profil = konzentrierte Sicht
        prof = full["ClusterProfile"]
        profile = {
            "ClusterProfile": {
                "k": k,
                "cluster_strength": prof["cluster_strength"],
                "cluster_stability": prof["cluster_stability"],
                "dynamic_strength": prof["dynamic_strength"],
                "dynamic_stability": prof["dynamic_stability"],
                "num_clusters": len(prof["clusters"]),
            }
        }
        return profile, dbg


if __name__ == "__main__":
    agent = ClusterAgent()
    vals = [1,2,2,3,10,11,12,50,51,52]
    print(agent.run("cluster_full", {"values": vals, "k": 3}))
