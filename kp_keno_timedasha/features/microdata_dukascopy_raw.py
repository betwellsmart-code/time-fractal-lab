"""
microdata_dukascopy_raw.py
==========================================================
Roh-Downloader für Dukascopy-Tickdaten (EURUSD etc.)
- Lädt .bi5-Dateien direkt vom Dukascopy-Server
- Dekodiert LZMA-komprimierte Tickdaten
- Baut DataFrame mit Timestamp, Bid, Ask, Volumen
- Aggregation auf 1s/5s/10s möglich

Benötigt:
    pip install requests
    pip install pandas
"""

import os
import struct
import lzma
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import requests
import pandas as pd

# Basis-Speicherpfad für Daten
BASE_PATH = os.path.join(os.getcwd(), "data", "dukascopy")
os.makedirs(BASE_PATH, exist_ok=True)


def _build_hour_url(symbol: str, dt: datetime, hour: int) -> str:
    """
    Baut die Dukascopy-URL für einen bestimmten Symbol/Tag/Stunde.
    Achtung: Monat und Tag sind im Dukascopy-Pfad 0-basiert.
    """
    sym = symbol.upper()
    year = dt.year
    month_dir = dt.month - 1   # 0-based
    day_dir = dt.day - 1       # 0-based

    return (
        f"https://datafeed.dukascopy.com/datafeed/"
        f"{sym}/{year}/{month_dir:02d}/{day_dir:02d}/{hour:02d}h_ticks.bi5"
    )


def _decode_bi5(content: bytes, base_dt: datetime) -> pd.DataFrame:
    """
    Dekodiert eine .bi5-Stunde:
    Format pro Tick (Big-Endian, 20 Bytes):
        0-3   : Millisekunden seit Stundenbeginn (uint32)
        4-7   : Bid * 10^5 (int32)
        8-11  : Ask * 10^5 (int32)
        12-15 : BidVolume * 10^3 (int32)
        16-19 : AskVolume * 10^3 (int32)
    """
    if not content:
        return pd.DataFrame()

    try:
        raw = lzma.decompress(content)
    except Exception as e:
        print(f"[WARN] LZMA-Dekompression fehlgeschlagen: {e}")
        return pd.DataFrame()

    if len(raw) % 20 != 0:
        # Unerwartetes Format – trotzdem versuchen wir, was geht
        print(f"[WARN] Unerwartige Raw-Länge: {len(raw)} (nicht Vielfaches von 20)")

    ticks = []
    record_struct = struct.Struct(">IIIII")  # 5x 4 Byte, Big-Endian

    for (millis, bid_i, ask_i, bidvol_i, askvol_i) in record_struct.iter_unpack(raw):
        ts = base_dt + timedelta(milliseconds=millis)
        bid = bid_i / 100000.0
        ask = ask_i / 100000.0
        bid_vol = bidvol_i / 1000.0
        ask_vol = askvol_i / 1000.0
        ticks.append((ts, bid, ask, bid_vol, ask_vol))

    if not ticks:
        return pd.DataFrame()

    df = pd.DataFrame(
        ticks,
        columns=["timestamp", "bid", "ask", "bid_volume", "ask_volume"],
    )
    return df


def download_day_ticks(
    symbol: str,
    date_str: str,
    hours: Optional[List[int]] = None,
    save_csv: bool = True,
) -> Optional[pd.DataFrame]:
    """
    Lädt Tickdaten für EINEN Tag (UTC) für das gegebene Symbol.

    symbol   : z.B. "EURUSD"
    date_str : "YYYY-MM-DD" (z.B. "2024-12-01")
    hours    : Liste von Stunden [0..23]; None = alle 24 Stunden
    save_csv : wenn True, speichert Tagesdaten als CSV unter data/dukascopy/

    Rückgabe:
        DataFrame mit Spalten:
        timestamp (UTC), bid, ask, bid_volume, ask_volume
        oder None, falls keine Daten.
    """
    dt_day = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    if hours is None:
        hours = list(range(24))

    print(f"[INFO] Lade Dukascopy-Ticks für {symbol} am {date_str} (Stunden: {hours})")

    all_chunks = []

    for h in hours:
        base_dt = dt_day.replace(hour=h, minute=0, second=0, microsecond=0)
        url = _build_hour_url(symbol, dt_day, h)
        try:
            resp = requests.get(url, timeout=10)
        except Exception as e:
            print(f"[WARN] HTTP-Fehler {symbol} {date_str} Stunde {h}: {e}")
            continue

        if resp.status_code != 200 or not resp.content:
            # Keine Daten (z.B. Wochenende, Feiertag)
            continue

        hour_df = _decode_bi5(resp.content, base_dt)
        if not hour_df.empty:
            all_chunks.append(hour_df)

    if not all_chunks:
        print("[WARN] Keine Tickdaten für diesen Tag erhalten.")
        return None

    df_day = pd.concat(all_chunks, ignore_index=True)
    df_day.sort_values("timestamp", inplace=True)
    df_day.reset_index(drop=True, inplace=True)

    if save_csv:
        fname = f"{symbol.upper()}_{date_str}.csv"
        fpath = os.path.join(BASE_PATH, fname)
        df_day.to_csv(fpath, index=False)
        print(f"[OK] Tages-Ticks gespeichert in: {fpath}")

    print(f"[OK] Gesamtanzahl Ticks: {len(df_day)}")
    return df_day


def aggregate_ticks(
    df: pd.DataFrame,
    interval_seconds: int = 1,
) -> pd.DataFrame:
    """
    Aggregiert Tickdaten auf Sekundencandles (oder Vielfache).
    interval_seconds: 1, 5, 10, 60, ...
    Ergebnis: OHLC für Bid/Ask.
    """
    if df is None or df.empty:
        print("[WARN] Keine Daten zum Aggregieren.")
        return pd.DataFrame()

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df.set_index("timestamp", inplace=True)

    rule = f"{interval_seconds}s"


    agg = df.resample(rule).agg(
        {
            "bid": ["first", "max", "min", "last"],
            "ask": ["first", "max", "min", "last"],
            "bid_volume": "sum",
            "ask_volume": "sum",
        }
    )

    agg.columns = [
        "bid_open",
        "bid_high",
        "bid_low",
        "bid_close",
        "ask_open",
        "ask_high",
        "ask_low",
        "ask_close",
        "bid_volume_sum",
        "ask_volume_sum",
    ]

    agg.dropna(subset=["bid_open", "ask_open"], inplace=True)
    return agg


if __name__ == "__main__":
    # Mini-Testlauf: ein Tag EURUSD, alle Stunden
    sym = "EURUSD"
    day = "2024-12-01"

    day_df = download_day_ticks(sym, day, hours=None, save_csv=True)
    if day_df is not None:
        print(day_df.head())
        one_sec = aggregate_ticks(day_df, 1)
        print(one_sec.head())
