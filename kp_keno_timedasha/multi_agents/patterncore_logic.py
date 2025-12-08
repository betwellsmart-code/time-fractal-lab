# multi_agents/patterncore_logic.py

def patterncore_analyze(values):
    """Echte PatternCore-Pipeline – Saham-Lab Version."""

    if not values:
        return {"error": "Keine Daten"}

    # 1) Normalisierung
    mean = sum(values) / len(values)
    norm = [v - mean for v in values]

    # 2) Segmentierung
    half = len(norm) // 2
    segments = [norm[:half], norm[half:]]

    # 3) Mustererkennung
    patterns = []
    for seg in segments:
        if not seg:
            continue
        trend = (
            "up" if seg[-1] > seg[0] else
            "down" if seg[-1] < seg[0] else
            "flat"
        )
        patterns.append({"length": len(seg), "trend": trend})

    # 4) Clustering
    clusters = {
        "up":   [p for p in patterns if p["trend"] == "up"],
        "down": [p for p in patterns if p["trend"] == "down"],
        "flat": [p for p in patterns if p["trend"] == "flat"],
    }

    return {
        "PatternUnits": clusters,
        "ScoreMaps": "simple_score_map",
        "HotspotFrames": "simple_hotspots"
    }
