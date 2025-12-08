# ======================================================================
# BLOCK 1 – SignatureAgent (Core)
# ======================================================================
from __future__ import annotations
from typing import Any, Dict, List
import hashlib
import math


class SignatureAgent:
    """
    Agent 14 – SignatureAgent
    Wandelt beliebige verschachtelte Profile in deterministische,
    normalisierte numerische Vektoren um und erzeugt daraus
    stabile mathematische Signaturen.
    """

    # -----------------------------
    # 1. Flatten (Deterministisch)
    # -----------------------------
    def _flatten(self, obj: Any) -> List[float]:
        vec = []

        if isinstance(obj, dict):
            for k in sorted(obj.keys()):
                vec.extend(self._flatten(obj[k]))

        elif isinstance(obj, list):
            for v in obj:
                vec.extend(self._flatten(v))

        elif isinstance(obj, (int, float)):
            vec.append(float(obj))

        else:
            # Fallback: Länge des Stringrepräsentation
            vec.append(float(len(str(obj))))

        return vec or [0.0]

    # -----------------------------
    # 2. Linear Normalisierung
    # -----------------------------
    def _normalize(self, vec: List[float]) -> List[float]:
        s = sum(abs(v) for v in vec) + 1e-12
        return [v / s for v in vec]
# ======================================================================
# BLOCK 2 – Erweiterte Analyse + Signaturaufbau
# ======================================================================

    # -----------------------------
    # 3. Komplexitätsanalyse
    # -----------------------------
    def _complexity(self, vec: List[float]) -> Dict:
        n = len(vec)
        entropy = 0.0

        if n > 1:
            total = sum(abs(x) for x in vec) + 1e-9
            p = [abs(v) / total for v in vec]
            entropy = -sum(pi * math.log(pi + 1e-12) for pi in p)

        variance = 0.0
        if n > 1:
            mean = sum(vec)/n
            variance = sum((v - mean)**2 for v in vec)/n

        return {
            "length": n,
            "min": min(vec),
            "max": max(vec),
            "entropy": entropy,
            "variance": variance,
        }

    # -----------------------------
    # 4. Signatur generieren
    # -----------------------------
    def build_signature(self, profile: Any) -> Dict:
        raw = self._flatten(profile)
        norm = self._normalize(raw)
        meta = self._complexity(norm)

        sig_str = "|".join(f"{x:.6f}" for x in norm)
        sig_hash = hashlib.sha256(sig_str.encode("utf-8")).hexdigest()[:16]

        return {
            "Signature": {
                "vector": norm,
                "hash": f"SIG-{sig_hash}",
                "complexity": meta,
            },
            "debug": {
                "raw_vector": raw,
                "normalized": norm,
            }
        }
# ======================================================================
# BLOCK 3 – API / Task-Handling
# ======================================================================

    def run(self, task: str, payload: Dict, **_):
        if task == "signature_build":
            prof = payload.get("profile", {})
            out = self.build_signature(prof)
            return {
                "ok": True,
                "result": out,
                "debug": {},
                "diagnostics": None,
            }

        # Unbekannte Tasks:
        return {
            "ok": False,
            "result": None,
            "debug": {"error": f"Unknown task '{task}'"},
            "diagnostics": None,
        }
