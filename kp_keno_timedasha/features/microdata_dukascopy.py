# microdata_dukascopy.py
# ==========================================================
# Dukascopy Tick-Downloader für Saham-Lab
# Lädt echte Tickdaten, speichert lokal und erzeugt 1s/5s/10s Zeitreihen
#
# pip install dukascopy
# pip install pandas
#
# Speicherort:
#   data/dukascopy/<symbol>_<YYYY-MM-DD>.csv
# ==========================================================

import os
import pandas as pd
from datetime import datetime
from dukascopy import Downloader

# ----------------------------------------------------------
# Speicherpfad
# ----------------------------------------------------------
BASE_PATH = os.path.join(os.getcwd(), "data", "dukascopy")
os.makedirs(BASE_PATH, exist_ok=True)


def download_ticks(symbol: str, date_from: str, date_to: str):
    """
    Lädt Tickdaten von Dukascopy.
    symbol: "EURUSD"
    date_from: "2024-12-01"
    date_to:   "2024-12-02"
    """

    print(f"[INFO] Lade Tickdaten von Dukascopy für {symbol}: {date_from} → {date_to}")

    d = Downloader()
    df = d.download(symbol, date_from, date_to, timeframe="tick")

    if df is None or df.empty:
        print("[WARN] Keine Daten erhalten.")
        return None

    # Zeit in datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

    # Datei speichern
    fname = f"{symbol}_{date_from}_{date_to}.csv"
    fpath = os.path.join(BASE_PATH, fname)
    df.to_csv(fpath, index=False)

    print(f"[OK] Tickdaten gespeichert in: {fpath}")
    return df


# ----------------------------------------------------------
# Aggregation: Tick → Sekunden-basierte Candles
# ----------------------------------------------------------
def aggregate(df: pd.DataFrame, interval_sec: int = 1):
    """
    Aggregiert Tickdaten in Sekunden-Candles.
    interval_sec: 1, 5, 10 …
    """

    df = df.set_index(pd.to_datetime(df['timestamp'], utc=True))

    price = df['bid']  # als Basispreis

    rule = f"{interval_sec}S"

    agg = df.resample(rule).agg({
        "bid": ["first", "max", "min", "last"],
        "ask": ["first", "max", "min", "last"]
    })

    agg.columns = [
        "bid_open", "bid_high", "bid_low", "bid_close",
        "ask_open", "ask_high", "ask_low", "ask_close"
    ]

    agg = agg.dropna()

    print(f"[OK] Aggregation auf {interval_sec}s abgeschlossen.")
    return agg


if __name__ == "__main__":

    symbol = "EURUSD"
    start = "2024-12-01"
    end   = "2024-12-02"

    ticks = download_ticks(symbol, start, end)

    if ticks is not None:
        sec_1  = aggregate(ticks, 1)
        sec_5  = aggregate(ticks, 5)
        sec_10 = aggregate(ticks, 10)

        print(sec_1.head())
