from features.microdata_dukascopy_raw import download_day_ticks, aggregate_ticks

if __name__ == "__main__":
    symbol = "EURUSD"
    day    = "2025-11-05" # Beispieltag

    # Alle 24 Stunden des Tages (Standard)
    df_day = download_day_ticks(symbol, day, hours=None, save_csv=True)

    if df_day is None:
        print("Keine Tickdaten erhalten.")
    else:
        print(df_day.head())
        df_1s = aggregate_ticks(df_day, interval_seconds=1)
        print("1s-Aggregat:")
        print(df_1s.head())
