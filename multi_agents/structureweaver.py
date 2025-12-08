"""
StructureWeaver 0.3 – Baut logische und numerische Verbindungen.
Kompatibel mit Orchestrator 0.4.
"""

from typing import Any, Dict, List


class StructureWeaver:
    def __init__(self, name: str = "StructureWeaver", version: str = "0.3"):
        self.name = name
        self.version = version

    # -----------------------------------------------------------
    # Hilfsfunktionen
    # -----------------------------------------------------------
    def _weave_links(self, data: List[float]) -> List[Dict]:
        links = []
        for i in range(len(data) - 1):
            links.append({"from": i, "to": i + 1, "delta": data[i + 1] - data[i]})
        return links

    # -----------------------------------------------------------
    # Tasks
    # -----------------------------------------------------------
    def structure_analyze(self, seq: List[float]) -> Dict:
        links = self._weave_links(seq)
        return {
            "analysis": {"links": links},
            "debug": {"raw": seq, "links": links},
        }

    def structure_weave(self, seq: List[float]) -> Dict:
        links = self._weave_links(seq)
        return {
            "weave": links,
            "debug": {"raw": seq, "links": links},
        }

    def structure_summary(self, seq: List[float]) -> Dict:
        links = self._weave_links(seq)
        return {
            "summary": {
                "count_links": len(links),
                "avg_delta": sum(l["delta"] for l in links) / len(links) if links else 0,
            },
            "debug": {"raw": seq, "links": links},
        }

    # -----------------------------------------------------------
    # Run-Schnittstelle
    # -----------------------------------------------------------
    def run(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        seq = payload.get("data", [])

        if task == "structure_analyze":
            return self.structure_analyze(seq)

        if task == "structure_weave":
            return self.structure_weave(seq)

        if task == "structure_summary":
            return self.structure_summary(seq)

        return {"error": f"Unknown StructureWeaver task '{task}'", "debug": {}}
