# ================================================================
# timedasha_features.py
# Adapter-Modul für Agenten:
#  - PatternCore (Agent 1)
#  - PointDynamics (Agent 4)
#  - Temporal Synthesis (Agent 5)
#
# Liefert klar definierte Zeit-Dasha-Features pro Ziehung:
#   YEAR / MONTH / WEEK × (MAHA, ANTAR, PRATY, SOOK)
#
# SUB & PRANA bleiben im System, werden aber NICHT als
# astrologische Praxis-Features ausgegeben – nur intern verfügbar.
#
# ================================================================

import datetime
from run_timedasha import (
    build_kp_keno_timedasha_payload,
    DASHA_ORDER,
    VISIBLE_LEVELS
)


# ---------------------------------------------------------------
# 1) Symbolische Features erstellen
# ---------------------------------------------------------------

def extract_symbolic_features(date):
    """
    Gibt ein Dictionary zurück, das ALLE sichtbaren Zeitfeatures enthält:
    
    Beispiel:
        {
          "YEAR_MAHA": "VENUS",
          "YEAR_ANTAR": "RAHU",
          "MONTH_PRATY": "MARS",
          "WEEK_SOOK": "RAHU",
          ...
        }
    """
    data = build_kp_keno_timedasha_payload(date)

    features = {}

    for frame_name in ["YEAR", "MONTH", "WEEK"]:
        frame = data[frame_name]
        levels = frame["levels"]

        for lvl in VISIBLE_LEVELS:
            lord = levels[lvl]["lord"]
            feat_name = f"{frame_name}_{lvl}"
            features[feat_name] = lord

    return features


# ---------------------------------------------------------------
# 2) Numerische Encodings der Lords
# ---------------------------------------------------------------

LORD_TO_INDEX = {lord: i for i, lord in enumerate(DASHA_ORDER)}
INDEX_TO_LORD = {i: lord for lord, i in LORD_TO_INDEX.items()}


def encode_lord(lord):
    """Mapping VENUS -> 1, SUN -> 2, usw."""
    return LORD_TO_INDEX.get(lord, -1)


def encode_symbolic_features(symbolic_features):
    """
    Symbolische Features → numerische (für ML-Modelle / Agenten).
    
    Beispiel:
        {"YEAR_MAHA": "VENUS"} → {"YEAR_MAHA": 1}
    """
    encoded = {}

    for key, value in symbolic_features.items():
        encoded[key] = encode_lord(value)

    return encoded


# ---------------------------------------------------------------
# 3) High-Level: Gesamtpaket pro Ziehung
# ---------------------------------------------------------------

def build_feature_package(date):
    """
    Gibt ein sauberes Paket zurück, das Agenten direkt essen können:

    {
       "date": "2025-12-03",
       "symbolic": {...},
       "encoded": {...}
    }
    """
    if isinstance(date, str):
        year, month, day = map(int, date.split("-"))
        date = datetime.date(year, month, day)

    symbolic = extract_symbolic_features(date)
    encoded = encode_symbolic_features(symbolic)

    return {
        "date": date.isoformat(),
        "symbolic": symbolic,
        "encoded": encoded
    }


# ---------------------------------------------------------------
# Optional: CLI-Tool zum Debuggen
# ---------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        y, m, d = map(int, sys.argv[1].split("-"))
        date = datetime.date(y, m, d)
    else:
        date = datetime.date.today()

    pkg = build_feature_package(date)

    print("=== SYMBOLIC FEATURES ===")
    for k, v in pkg["symbolic"].items():
        print(f"{k:15s} = {v}")

    print("\n=== ENCODED FEATURES ===")
    for k, v in pkg["encoded"].items():
        print(f"{k:15s} = {v}")

    print("\nFertig.")
