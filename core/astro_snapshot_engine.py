#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
astro_snapshot_engine.py – Astro–Market Snapshot Engine (v0.2)

Author   : Dr. Noreki & EL_Samy (Development Lead)
Project  : time-fractal-lab / Saham-Lab
Version  : v0.2.0
Purpose  : Erzeugt 1-Minuten-Astro-Snapshots (Sub-Lord + SSL) synchron zu
           Kerzendaten (z. B. EUR/SEK) und annotiert jede Kerze mit
           Trend-Information (up/down/neutral) sowie Vorher/Nachher-Zustand
           und Distanz zu nächsten Sub-/SSL-Wechseln.

NEU IN v0.2:
- Echte KP-orientierte Sub-/Sub-Sub-Lord-Logik
  (Vimshottari-Abfolge, Nakshatra → Sub → SSL)
- Basierend auf der (siderealen) Mond-Position (Lahiri)
- Fallback auf Platzhalter, falls pyswisseph nicht installiert ist

HINWEIS:
- Diese Implementierung bildet die Standard-KP-Idee nach:
  * 27 Nakshatras á 13°20'
  * 9 Dasha-Herrscher (KE, VE, SU, MO, MA, RA, JU, SA, ME)
  * Sub-Lords nach Dasha-Längen (7,20,6,10,7,18,16,19,17)
  * SSL = erneute Unterteilung desselben Sub-Segments
- Fine-Tuning (exakte Tabellen, Ayanamsha-Offsets, Spezialfälle)
  kannst du später noch anpassen.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional

# Optional: Swiss Ephemeris
try:
    import swisseph as swe  # type: ignore[attr-defined]
    HAS_SWISSEPH = True
except Exception:  # noqa: BLE001
    swe = None  # type: ignore[assignment]
    HAS_SWISSEPH = False


# ============================================================================
# 1) GRUNDSTRUKTUREN
# ============================================================================

@dataclass
class Candle:
    """
    Repräsentiert eine einzelne Marktkerze (z. B. EUR/SEK M1).

    timestamp : datetime  -> Kerzen-OPEN-Zeit (wichtiger Referenzpunkt)
    tf        : str       -> Timeframe, z. B. 'M1', 'M3', 'M5', ...
    open      : float
    high      : float
    low       : float
    close     : float
    """

    timestamp: datetime
    tf: str
    open: float
    high: float
    low: float
    close: float


@dataclass
class AstroState:
    """
    Astrologischer Zustand für einen Zeitpunkt.

    Wir fokussieren uns auf:
    - sub      : Sub-Lord
    - ssl      : Sub-Sub-Lord
    - meta     : Zusatzinformationen (z. B. Mondgrad, Nakshatra, Star-Lord)
    """

    sub: str
    ssl: str
    meta: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclass
class SnapshotRecord:
    """
    Fusionierte Astro–Market-Information für eine Kerze.

    - candle : Original-Kerzenobjekt
    - trend  : "up", "down" oder "neutral"
    - astro  : AstroState für diese Kerze
    - prev   : AstroState direkt vorher (optional)
    - next   : AstroState direkt danach (optional)
    - dist_to_next_sub_change : Distanz bis zum nächsten Sub-Lord-Wechsel (in Minuten)
    - dist_to_next_ssl_change : Distanz bis zum nächsten SSL-Wechsel (in Minuten)
    """

    candle: Candle
    trend: str
    astro: AstroState
    prev: Optional[AstroState] = None
    next: Optional[AstroState] = None
    dist_to_next_sub_change: Optional[float] = None
    dist_to_next_ssl_change: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Wandelt den Snapshot in ein JSON-freundliches Dict um.
        """
        return {
            "timestamp": self.candle.timestamp.isoformat(),
            "tf": self.candle.tf,
            "open": self.candle.open,
            "high": self.candle.high,
            "low": self.candle.low,
            "close": self.candle.close,
            "trend": self.trend,
            "astro": {
                "sub": self.astro.sub,
                "ssl": self.astro.ssl,
                "meta": self.astro.meta,
            },
            "prev": None
            if self.prev is None
            else {"sub": self.prev.sub, "ssl": self.prev.ssl, "meta": self.prev.meta},
            "next": None
            if self.next is None
            else {"sub": self.next.sub, "ssl": self.next.ssl, "meta": self.next.meta},
            "dist_to_next_sub_change": self.dist_to_next_sub_change,
            "dist_to_next_ssl_change": self.dist_to_next_ssl_change,
        }


# ============================================================================
# 2) ENGINE-KONFIGURATION
# ============================================================================

@dataclass
class SnapshotEngineConfig:
    """
    Konfiguration für die AstroSnapshotEngine.

    - use_minutes_step: Standardzeitabstand für Snapshots (normal: 1 Minute)
    - track_prev_next : Ob Prev/Next-Zustände berechnet werden sollen
    - track_distances : Ob Distanz zum nächsten Wechsel berechnet werden soll
    - ephe_path       : Pfad zu den Swiss-Ephemeris-Dateien (optional)
    - use_lahiri      : Ob Lahiri-Ayanamsha verwendet wird (Standard: True)
    - anchor          : 'moon' oder später ggf. 'lagna' (aktuell: 'moon')
    """

    use_minutes_step: int = 1
    track_prev_next: bool = True
    track_distances: bool = True
    ephe_path: Optional[str] = None
    use_lahiri: bool = True
    anchor: str = "moon"  # später evtl. "lagna"


# ============================================================================
# 3) KP-NAKSHATRA / SUB / SSL HILFSFUNKTIONEN
# ============================================================================

# Vimshottari-Reihenfolge und Dasha-Längen
DASHA_ORDER = ["KE", "VE", "SU", "MO", "MA", "RA", "JU", "SA", "ME"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]  # Summe = 120

NAKS_TOTAL = 27
NAKS_SPAN_DEG = 360.0 / NAKS_TOTAL  # 13.333... Grad


def normalize_deg(deg: float) -> float:
    """Normiert einen Winkel auf [0, 360)."""
    d = deg % 360.0
    if d < 0:
        d += 360.0
    return d


def compute_nakshatra_index(longitude_deg_sidereal: float) -> int:
    """
    Bestimmt den Nakshatra-Index (0–26) aus der siderealen Ekliptik-Länge.

    0 = erstes Nakshatra (Ashwini, Herr KE)
    """
    lon = normalize_deg(longitude_deg_sidereal)
    idx = int(lon // NAKS_SPAN_DEG)
    if idx >= NAKS_TOTAL:
        idx = NAKS_TOTAL - 1
    return idx


def compute_sub_ssl_for_longitude(longitude_deg_sidereal: float) -> Dict[str, Any]:
    """
    Kernfunktion für KP-Sub/SSL:

    - nimmt sidereale Ekliptik-Länge (Moon oder Lagna)
    - bestimmt:
      * nakshatra_index (0–26)
      * star_lord (Nakshatra-Herrscher)
      * sub_lord
      * ssl (Sub-Sub-Lord)
      * interne Positionsdaten (Grad innerhalb Nakshatra/Sub)

    Rückgabe: Dict mit Schlüsseln:
    - 'nak_index', 'nak_start_deg', 'nak_pos_deg'
    - 'star_lord', 'sub_lord', 'ssl'
    - 'sub_pos_deg', 'ssl_pos_deg'
    """
    lon = normalize_deg(longitude_deg_sidereal)
    nak_index = compute_nakshatra_index(lon)

    nak_start_deg = nak_index * NAKS_SPAN_DEG
    nak_pos_deg = lon - nak_start_deg  # Position innerhalb des Nakshatra

    # Star-Lord: Nakshatra-Index modulo 9 (Ashwini = 0 → KE)
    star_lord_index = nak_index % len(DASHA_ORDER)
    star_lord = DASHA_ORDER[star_lord_index]

    # Sub-Längen (in Grad) für ein Nakshatra (auf Basis Dasha-Jahre)
    base_unit = NAKS_SPAN_DEG / 120.0  # 120 = Summe der Vimshottari-Jahre
    sub_lengths = [years * base_unit for years in DASHA_YEARS]

    # Reihenfolge der Subs ist rotiert, beginnend beim Star-Lord
    order_indices = [(star_lord_index + i) % 9 for i in range(9)]
    ordered_sub_lords = [DASHA_ORDER[i] for i in order_indices]
    ordered_sub_lengths = [sub_lengths[i] for i in order_indices]

    # 1) Sub-Lord bestimmen
    cumulative = 0.0
    sub_lord_index_in_order = 0
    for i, seg_len in enumerate(ordered_sub_lengths):
        if nak_pos_deg < cumulative + seg_len or i == len(ordered_sub_lengths) - 1:
            sub_lord_index_in_order = i
            break
        cumulative += seg_len

    sub_lord = ordered_sub_lords[sub_lord_index_in_order]
    sub_start_deg = cumulative
    sub_span_deg = ordered_sub_lengths[sub_lord_index_in_order]
    sub_pos_deg = nak_pos_deg - sub_start_deg

    # 2) SSL innerhalb des Sub-Segments bestimmen
    # SSL nimmt wieder die Dasha-Reihenfolge, startend ab Sub-Lord
    sub_lord_global_index = DASHA_ORDER.index(sub_lord)
    ssl_order_indices = [
        (sub_lord_global_index + i) % 9 for i in range(9)
    ]
    ordered_ssl_lords = [DASHA_ORDER[i] for i in ssl_order_indices]

    ssl_base_unit = sub_span_deg / 120.0
    ssl_lengths = [years * ssl_base_unit for years in DASHA_YEARS]

    cumulative_ssl = 0.0
    ssl_index_in_order = 0
    for i, seg_len in enumerate(ssl_lengths):
        if sub_pos_deg < cumulative_ssl + seg_len or i == len(ssl_lengths) - 1:
            ssl_index_in_order = i
            break
        cumulative_ssl += seg_len

    ssl_lord = ordered_ssl_lords[ssl_index_in_order]
    ssl_start_deg = cumulative_ssl
    ssl_pos_deg = sub_pos_deg - ssl_start_deg

    return {
        "nak_index": nak_index,
        "nak_start_deg": nak_start_deg,
        "nak_pos_deg": nak_pos_deg,
        "star_lord": star_lord,
        "sub_lord": sub_lord,
        "ssl": ssl_lord,
        "sub_start_deg": sub_start_deg,
        "sub_span_deg": sub_span_deg,
        "sub_pos_deg": sub_pos_deg,
        "ssl_start_deg": ssl_start_deg,
        "ssl_pos_deg": ssl_pos_deg,
    }


# ============================================================================
# 4) SNAPSHOT-ENGINE
# ============================================================================

class AstroSnapshotEngine:
    """
    Kernklasse, die Kerzendaten mit Astro-Sub/SSL-Snapshots verbindet.

    WICHTIG:
    - Für jede Kerze wird ein AstroState erzeugt (Sub + SSL).
    - Trend (up/down/neutral) wird aus OHLC berechnet.
    - Optional: Prev + Next State + Distanz zu Wechseln.

    ANKER (aktuell):
    - 'moon': es wird die Moon-Länge (sidereal, Lahiri) verwendet.
    """

    def __init__(self, config: Optional[SnapshotEngineConfig] = None) -> None:
        self.config = config or SnapshotEngineConfig()

        if HAS_SWISSEPH and self.config.ephe_path:
            swe.set_ephe_path(self.config.ephe_path)

        if HAS_SWISSEPH and self.config.use_lahiri:
            try:
                swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
            except Exception:
                # Falls nicht verfügbar, kein harter Fehler – Nutzer kann nachjustieren
                pass

    # ------------------------------------------------------------------ #
    # Öffentliche Hauptfunktion
    # ------------------------------------------------------------------ #

    def build_snapshots(self, candles: Iterable[Candle]) -> List[SnapshotRecord]:
        """
        Hauptmethode: nimmt eine Liste von Kerzen und erzeugt vollständige
        SnapshotRecords.

        Erwartet:
        - Kerzenliste, idealerweise bereits sortiert nach timestamp.
        """
        candles_list = sorted(list(candles), key=lambda c: c.timestamp)

        # 1) Astro-Snapshot pro Kerze (Sub/SSL) bestimmen
        astro_states: List[AstroState] = [
            self._compute_astro_for_timestamp(c.timestamp) for c in candles_list
        ]

        # 2) Trend bestimmen
        snapshots: List[SnapshotRecord] = []
        for candle, astro in zip(candles_list, astro_states):
            trend = self._compute_trend(candle)
            snapshots.append(
                SnapshotRecord(
                    candle=candle,
                    trend=trend,
                    astro=astro,
                )
            )

        # 3) Prev/Next und Distanzberechnung
        if self.config.track_prev_next or self.config.track_distances:
            self._annotate_prev_next_and_distances(snapshots)

        return snapshots

    # ------------------------------------------------------------------ #
    # Intern: Trend
    # ------------------------------------------------------------------ #

    @staticmethod
    def _compute_trend(candle: Candle) -> str:
        """
        Bestimmt die Kerzenrichtung:
        - "up"     : close > open
        - "down"   : close < open
        - "neutral": close == open
        """
        if candle.close > candle.open:
            return "up"
        if candle.close < candle.open:
            return "down"
        return "neutral"

    # ------------------------------------------------------------------ #
    # Intern: Astro Sub/SSL
    # ------------------------------------------------------------------ #

    def _compute_astro_for_timestamp(self, ts: datetime) -> AstroState:
        """
        Berechnet den AstroState für einen Zeitpunkt.

        FALL 1: Swiss Ephemeris ist verfügbar:
            - Berechne sidereale Mondlänge (Lahiri)
            - Bestimme Nakshatra, Star-Lord, Sub, SSL
        FALL 2: Kein Swiss Ephemeris:
            - Nutze deterministische Platzhalter-Sub/SSL
              (Pipeline & Struktur bleiben testbar)
        """
        if not HAS_SWISSEPH:
            # Fallback: deterministische Pseudo-Werte wie in v0.1
            minute_index = int(ts.timestamp() // 60)
            sub_names = [
                "KE", "VE", "SU", "MO", "MA", "RA", "JU", "SA", "ME"
            ]
            ssl_names = [
                "KE-SSL", "VE-SSL", "SU-SSL", "MO-SSL", "MA-SSL",
                "RA-SSL", "JU-SSL", "SA-SSL", "ME-SSL"
            ]
            sub = sub_names[minute_index % len(sub_names)]
            ssl = ssl_names[minute_index % len(ssl_names)]
            meta = {
                "info": "FALLBACK – pyswisseph nicht installiert",
                "minute_index": minute_index,
            }
            return AstroState(sub=sub, ssl=ssl, meta=meta)

        # ---- MIT SWISS EPHEMERIS --------------------------------------
        # Annahme: ts ist UTC oder wird als UTC interpretiert
        jd_ut = self._datetime_to_jd_utc(ts)

        if self.config.anchor.lower() == "moon":
            # Mond, sidereal
            result, flags = swe.calc_ut(jd_ut, swe.MOON)
            lon_moon_trop = result[0]  # echtes float: ekliptikale Mondlänge
            lon_moon_sid = lon_moon_trop  # dank set_sid_mode bereits sidereal

            info = compute_sub_ssl_for_longitude(lon_moon_sid)
            meta = {
                "anchor": "moon",
                "lon_sidereal": lon_moon_sid,
                "nak_index": info["nak_index"],
                "nak_start_deg": info["nak_start_deg"],
                "nak_pos_deg": info["nak_pos_deg"],
                "star_lord": info["star_lord"],
                "sub_start_deg": info["sub_start_deg"],
                "sub_span_deg": info["sub_span_deg"],
                "sub_pos_deg": info["sub_pos_deg"],
                "ssl_start_deg": info["ssl_start_deg"],
                "ssl_pos_deg": info["ssl_pos_deg"],
            }
            return AstroState(
                sub=info["sub_lord"],
                ssl=info["ssl"],
                meta=meta,
            )

        # Platzhalter für spätere Anchor-Typen (z. B. Lagna)
        # Aktuell wird nur Moon verwendet.
        minute_index = int(ts.timestamp() // 60)
        sub = DASHA_ORDER[minute_index % len(DASHA_ORDER)]
        ssl = DASHA_ORDER[(minute_index * 2) % len(DASHA_ORDER)]
        meta = {
            "info": "ANCHOR-TYP NICHT IMPLEMENTIERT – Fallback",
            "anchor": self.config.anchor,
            "minute_index": minute_index,
        }
        return AstroState(sub=sub, ssl=ssl, meta=meta)

    @staticmethod
    def _datetime_to_jd_utc(ts: datetime) -> float:
        """
        Wandelt ein datetime-Objekt in Julian Day (UT) um.

        - naive datetime wird als UTC interpretiert
        - aware datetime wird nach UTC konvertiert
        """
        if ts.tzinfo is not None:
            ts = ts.astimezone(tz=None).replace(tzinfo=None)

        year = ts.year
        month = ts.month
        day = ts.day
        hour = ts.hour + ts.minute / 60.0 + ts.second / 3600.0 + ts.microsecond / 3_600_000_000.0
        jd_ut = swe.julday(year, month, day, hour)  # type: ignore[arg-type]
        return jd_ut

    # ------------------------------------------------------------------ #
    # Intern: Prev/Next + Distanz
    # ------------------------------------------------------------------ #

    def _annotate_prev_next_and_distances(
        self,
        snapshots: List[SnapshotRecord],
    ) -> None:
        """
        Ergänzt in-place:
        - prev / next AstroState
        - Distanz bis zum nächsten Sub-/SSL-Wechsel (in Minuten)

        Annahme:
        - snapshots sind zeitlich sortiert (M1-Raster)
        """
        if not snapshots:
            return

        # Prev-Referenzen
        if self.config.track_prev_next:
            for i in range(1, len(snapshots)):
                snapshots[i].prev = snapshots[i - 1].astro
            snapshots[0].prev = None

        # Next-Referenzen
        if self.config.track_prev_next:
            for i in range(len(snapshots) - 1):
                snapshots[i].next = snapshots[i + 1].astro
            snapshots[-1].next = None

        # Distanz bis zum nächsten Sub-/SSL-Wechsel
        if self.config.track_distances:
            self._compute_distance_to_next_changes(snapshots)

    @staticmethod
    def _compute_distance_to_next_changes(
        snapshots: List[SnapshotRecord],
    ) -> None:
        """
        Berechnet für jeden Snapshot:
        - dist_to_next_sub_change
        - dist_to_next_ssl_change

        Einheit: Minuten (float)
        """
        n = len(snapshots)
        if n == 0:
            return

        next_sub_change_index: Optional[int] = None
        next_ssl_change_index: Optional[int] = None

        for i in range(n - 1, -1, -1):
            current = snapshots[i]
            ts_current = current.candle.timestamp

            if i < n - 1:
                if snapshots[i + 1].astro.sub != current.astro.sub:
                    next_sub_change_index = i + 1
                if snapshots[i + 1].astro.ssl != current.astro.ssl:
                    next_ssl_change_index = i + 1

            if next_sub_change_index is not None:
                ts_target = snapshots[next_sub_change_index].candle.timestamp
                delta: timedelta = ts_target - ts_current
                current.dist_to_next_sub_change = delta.total_seconds() / 60.0
            else:
                current.dist_to_next_sub_change = None

            if next_ssl_change_index is not None:
                ts_target = snapshots[next_ssl_change_index].candle.timestamp
                delta = ts_target - ts_current
                current.dist_to_next_ssl_change = delta.total_seconds() / 60.0
            else:
                current.dist_to_next_ssl_change = None


# ============================================================================
# 5) HILFSFUNKTIONEN
# ============================================================================

def snapshots_to_json(snapshots: List[SnapshotRecord], indent: int = 2) -> str:
    """
    Wandelt eine Snapshot-Liste in einen JSON-String um.
    """
    data = [s.to_dict() for s in snapshots]
    return json.dumps(data, ensure_ascii=False, indent=indent)


# ============================================================================
# 6) EINFACHER DEMO-LAUF (optional)
# ============================================================================

def _demo() -> None:
    """
    Einfacher Testlauf ohne externe Datenquelle.
    Erzeugt 5 Beispielkerzen im M1-Raster und baut Snapshots.

    Wenn pyswisseph vorhanden ist, werden echte Mond-basierte Sub/SSL
    berechnet, ansonsten die Fallback-Varianten.
    """
    base_ts = datetime(2025, 1, 1, 12, 0, 0)
    candles: List[Candle] = []
    price = 11.0

    for i in range(5):
        ts = base_ts + timedelta(minutes=i)
        o = price
        c = price + (0.01 if i % 2 == 0 else -0.02)
        h = max(o, c) + 0.005
        l = min(o, c) - 0.005
        price = c
        candles.append(
            Candle(
                timestamp=ts,
                tf="M1",
                open=o,
                high=h,
                low=l,
                close=c,
            )
        )

    engine = AstroSnapshotEngine()
    snapshots = engine.build_snapshots(candles)

    print(snapshots_to_json(snapshots))


if __name__ == "__main__":
    _demo()
