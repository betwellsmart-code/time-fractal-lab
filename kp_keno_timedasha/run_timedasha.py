import datetime
import pytz
import sys
import json

# ---------------------------------------------------------
# Swiss Ephemeris (optional)
# ---------------------------------------------------------

try:
    import swisseph as swe
    HAVE_SWISSEPH = True
except ImportError:
    swe = None
    HAVE_SWISSEPH = False

# ---------------------------------------------------------
# Vimshottari-Konstanten
# ---------------------------------------------------------

DASHA_ORDER = [
    "KETU", "VENUS", "SUN", "MOON", "MARS",
    "RAHU", "JUPITER", "SATURN", "MERCURY"
]

DASHA_YEARS = {
    "KETU": 7,
    "VENUS": 20,
    "SUN": 6,
    "MOON": 10,
    "MARS": 7,
    "RAHU": 18,
    "JUPITER": 16,
    "SATURN": 19,
    "MERCURY": 17,
}

TOTAL_YEARS = 120.0
NAKSHATRA_COUNT = 27
NAKSHATRA_SIZE = 360.0 / NAKSHATRA_COUNT  # 13°20'


# ---------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------

def rotate_order_to(start_lord: str):
    """DASHA_ORDER so drehen, dass start_lord als erstes kommt."""
    if start_lord not in DASHA_ORDER:
        raise ValueError(f"Unbekannter Dasha-Lord: {start_lord}")
    idx = DASHA_ORDER.index(start_lord)
    return DASHA_ORDER[idx:] + DASHA_ORDER[:idx]


def find_interval(segments, t):
    """Finde das Segment, in dem t liegt."""
    for seg in segments:
        if seg["start"] <= t < seg["end"]:
            return seg
    # falls t genau am Ende liegt, nimm das letzte Segment
    return segments[-1]


# ---------------------------------------------------------
# Ort / Ziehungszeit
# ---------------------------------------------------------

def get_wiesbaden_location():
    return {
        "lat": 50.0825,
        "lon": 8.2416,
        "tz": "Europe/Berlin",
    }


def get_draw_time(date):
    tz = pytz.timezone("Europe/Berlin")
    return tz.localize(
        datetime.datetime(date.year, date.month, date.day, 19, 10, 0)
    )


# ---------------------------------------------------------
# Sonnenaufgang
# ---------------------------------------------------------

def fake_sunrise(date, loc):
    """
    Platzhalter: setzt Sonnenaufgang stumpf auf 08:00 Ortszeit.
    Wird verwendet, wenn Swiss Ephemeris nicht verfügbar ist
    oder Sunrise-Berechnung fehlschlägt.
    """
    tz = pytz.timezone(loc["tz"])
    return tz.localize(datetime.datetime(date.year, date.month, date.day, 8, 0, 0))


def swe_sunrise(date, loc):
    """
    Berechnet Sonnenaufgang mit Swiss Ephemeris für den gegebenen Tag und Ort.
    Erwartet, dass swe (pyswisseph) importiert wurde.
    """
    if not HAVE_SWISSEPH:
        return fake_sunrise(date, loc)

    lat = float(loc["lat"])
    lon = float(loc["lon"])

    # Start: 0:00 Ortszeit -> UTC
    tz = pytz.timezone(loc["tz"])
    dt_local_midnight = tz.localize(
        datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
    )
    dt_utc_midnight = dt_local_midnight.astimezone(pytz.utc)

    year = dt_utc_midnight.year
    month = dt_utc_midnight.month
    day = dt_utc_midnight.day
    hour = (
        dt_utc_midnight.hour
        + dt_utc_midnight.minute / 60.0
        + dt_utc_midnight.second / 3600.0
    )

    jd_start = swe.julday(year, month, day, hour)

    rs = swe.rise_trans(
        jd_start,
        swe.SUN,
        lon,
        lat,
        0.0,   # Luftdruck
        0.0,   # Temperatur
        swe.BIT_DISC_CENTER | swe.CALC_RISE
    )

    jd_rise = rs[0]  # erster Eintrag: JD des Ereignisses

    # JD -> UTC-Datetime
    y, m, d, ut_hour = swe.revjul(jd_rise)
    ut_h = int(ut_hour)
    ut_min = int((ut_hour - ut_h) * 60)
    ut_sec = int(round(((ut_hour - ut_h) * 60 - ut_min) * 60))

    dt_utc = datetime.datetime(y, m, d, ut_h, ut_min, ut_sec, tzinfo=pytz.utc)
    return dt_utc.astimezone(tz)


def get_sunrise(date, loc):
    """
    Wrapper: nutze Swiss Ephemeris, falls vorhanden;
    sonst Fallback fake_sunrise.
    """
    if HAVE_SWISSEPH:
        try:
            return swe_sunrise(date, loc)
        except Exception:
            return fake_sunrise(date, loc)
    else:
        return fake_sunrise(date, loc)


# ---------------------------------------------------------
# Mond / Nakshatra / Start-Lord (Lahiri)
# ---------------------------------------------------------

def get_moon_sidereal_longitude(dt_aware, loc):
    """
    Berechnet die siderische Mondlänge (Lahiri) zum gegebenen Zeitpunkt.
    dt_aware: timezone-aware datetime (Ortszeit).
    """
    if not HAVE_SWISSEPH:
        return None  # kein Swiss Ephemeris verfügbar

    # auf UTC umrechnen
    dt_utc = dt_aware.astimezone(pytz.utc)

    year = dt_utc.year
    month = dt_utc.month
    day = dt_utc.day
    hour = (
        dt_utc.hour
        + dt_utc.minute / 60.0
        + dt_utc.second / 3600.0
    )

    jd_ut = swe.julday(year, month, day, hour)

    # Lahiri-Siderik aktivieren
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

    # calc_ut liefert: (xx, retflag)
    # xx = [lon, lat, dist, lon_speed, lat_speed, dist_speed]
    xx, retflag = swe.calc_ut(
        jd_ut,
        swe.MOON,
        swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    )

    lon = xx[0] % 360.0
    return lon


def get_start_lord_for_frame(frame_start, loc):
    """
    Bestimmt den Start-Lord für einen Frame über
    die siderische Mondposition (Lahiri) am Frame-Start.
    """
    moon_lon = get_moon_sidereal_longitude(frame_start, loc)
    if moon_lon is None:
        # Fallback: wenn Swiss Ephemeris nicht verfügbar ist,
        # vorerst KETU als Platzhalter.
        return "KETU"

    nak_index = int(moon_lon / NAKSHATRA_SIZE)  # 0..26, 0 = Ashwini
    dasha_lord = DASHA_ORDER[nak_index % len(DASHA_ORDER)]
    return dasha_lord


def debug_print_moon_info(frame_start, loc, label):
    """
    Optionaler Debugprint: Moon-Lon, Nakshatra und Lord
    für einen Frame-Start.
    """
    moon_lon = get_moon_sidereal_longitude(frame_start, loc)
    if moon_lon is None:
        print(f"[DEBUG {label}] Swiss Ephemeris nicht verfügbar – Moon/Lahiri-Fallback aktiv.")
        return

    nak_index = int(moon_lon / NAKSHATRA_SIZE)
    lord = DASHA_ORDER[nak_index % len(DASHA_ORDER)]
    print(
        f"[DEBUG {label}] Moon(Lahiri) = {moon_lon:.4f}° | "
        f"Nakshatra-Index = {nak_index} | Start-Lord = {lord}"
    )


# ---------------------------------------------------------
# Frames (YEAR / MONTH / WEEK)
# ---------------------------------------------------------

def compute_year_frame(draw_time, loc):
    year = draw_time.year
    start = get_sunrise(datetime.date(year, 1, 1), loc)
    end = get_sunrise(datetime.date(year + 1, 1, 1), loc)
    return {"start": start, "end": end}


def compute_month_frame(draw_time, loc):
    year = draw_time.year
    month = draw_time.month

    start = get_sunrise(datetime.date(year, month, 1), loc)

    if month == 12:
        end = get_sunrise(datetime.date(year + 1, 1, 1), loc)
    else:
        end = get_sunrise(datetime.date(year, month + 1, 1), loc)

    return {"start": start, "end": end}


def compute_week_frame(draw_time, loc):
    """
    Week-Frame: Montag bis Montag, Start jeweils Sonnenaufgang.
    """
    weekday = draw_time.weekday()  # Monday = 0
    monday = draw_time - datetime.timedelta(days=weekday)
    monday_date = monday.date()

    start = get_sunrise(monday_date, loc)
    end = get_sunrise(monday_date + datetime.timedelta(days=7), loc)

    return {"start": start, "end": end}


# ---------------------------------------------------------
# Vimshottari-Skalierung
# ---------------------------------------------------------

def build_maha_segments(frame_start, frame_end, start_lord):
    """
    Skaliert die 9 Maha-Dashas proportional auf den Zeitraum [frame_start, frame_end].
    """
    total_seconds = (frame_end - frame_start).total_seconds()
    order = rotate_order_to(start_lord)

    segments = []
    current = frame_start

    for lord in order:
        fraction = DASHA_YEARS[lord] / TOTAL_YEARS
        duration_seconds = total_seconds * fraction
        seg_start = current
        seg_end = seg_start + datetime.timedelta(seconds=duration_seconds)

        segments.append({
            "lord": lord,
            "start": seg_start,
            "end": seg_end,
        })
        current = seg_end

    segments[-1]["end"] = frame_end
    return segments


def build_sub_segments(parent_start, parent_end):
    """
    Erzeugt Unterdashas (Antar, Praty, ...), gleicher Algorithmus
    wie bei Maha, aber auf den Elternzeitraum skaliert.
    """
    total_seconds = (parent_end - parent_start).total_seconds()
    segments = []
    current = parent_start

    for lord in DASHA_ORDER:
        fraction = DASHA_YEARS[lord] / TOTAL_YEARS
        duration_seconds = total_seconds * fraction
        seg_start = current
        seg_end = seg_start + datetime.timedelta(seconds=duration_seconds)
        segments.append({
            "lord": lord,
            "start": seg_start,
            "end": seg_end,
        })
        current = seg_end

    segments[-1]["end"] = parent_end
    return segments


def compute_active_vimshottari_levels(frame_start, frame_end, draw_time, start_lord):
    """
    Baut die 6 Ebenen (MAHA -> ANTAR -> PRATY -> SOOK -> SUB -> PRANA)
    für einen Zeitraum und ermittelt jeweils den aktiven Dasha
    + Restlaufzeit + Restanteil (0..1).
    """
    levels = {}

    # 1) MAHA
    maha_segments = build_maha_segments(frame_start, frame_end, start_lord)
    maha_active = find_interval(maha_segments, draw_time)
    levels["MAHA"] = maha_active

    # 2) ANTAR
    antar_segments = build_sub_segments(maha_active["start"], maha_active["end"])
    antar_active = find_interval(antar_segments, draw_time)
    levels["ANTAR"] = antar_active

    # 3) PRATY
    praty_segments = build_sub_segments(antar_active["start"], antar_active["end"])
    praty_active = find_interval(praty_segments, draw_time)
    levels["PRATY"] = praty_active

    # 4) SOOK
    sook_segments = build_sub_segments(praty_active["start"], praty_active["end"])
    sook_active = find_interval(sook_segments, draw_time)
    levels["SOOK"] = sook_active

    # 5) SUB
    sub_segments = build_sub_segments(sook_active["start"], sook_active["end"])
    sub_active = find_interval(sub_segments, draw_time)
    levels["SUB"] = sub_active

    # 6) PRANA
    prana_segments = build_sub_segments(sub_active["start"], sub_active["end"])
    prana_active = find_interval(prana_segments, draw_time)
    levels["PRANA"] = prana_active

    # Restlaufzeit + Restanteil hinzufügen
    for name, info in levels.items():
        total = info["end"] - info["start"]
        remaining = info["end"] - draw_time

        # Sicherheitsnetz: Restzeit nicht negativ werden lassen
        if remaining.total_seconds() < 0:
            remaining = datetime.timedelta(0)

        total_seconds = total.total_seconds()
        if total_seconds <= 0:
            remaining_fraction = 0.0
        else:
            remaining_fraction = remaining.total_seconds() / total_seconds
            if remaining_fraction < 0.0:
                remaining_fraction = 0.0
            elif remaining_fraction > 1.0:
                remaining_fraction = 1.0

        info["duration"] = total
        info["remaining"] = remaining
        info["remaining_fraction"] = remaining_fraction

    return levels


# ---------------------------------------------------------
# Hauptlogik / API
# ---------------------------------------------------------

def build_kp_keno_timedasha(date):
    """
    Kernfunktion: baut YEAR / MONTH / WEEK Frames und
    berechnet die aktiven Vimshottari-Ebenen.
    """
    loc = get_wiesbaden_location()
    draw_time = get_draw_time(date)

    frames = {
        "YEAR": compute_year_frame(draw_time, loc),
        "MONTH": compute_month_frame(draw_time, loc),
        "WEEK": compute_week_frame(draw_time, loc),
    }

    result = []

    for frame_name, frame in frames.items():
        start = frame["start"]
        end = frame["end"]

        start_lord = get_start_lord_for_frame(start, loc)

        levels = compute_active_vimshottari_levels(
            frame_start=start,
            frame_end=end,
            draw_time=draw_time,
            start_lord=start_lord,
        )

        result.append({
            "frame": frame_name,
            "start": start,
            "end": end,
            "start_lord": start_lord,
            "levels": levels,
        })

    return result


def build_kp_keno_timedasha_payload(date):
    """
    Baut eine schlanke, KENO-taugliche Struktur:
    YEAR / MONTH / WEEK -> Levels -> Lord + Restlaufzeit (Sekunden)
    + Restanteil (0..1). Datumsangaben als ISO-Strings.
    """
    raw = build_kp_keno_timedasha(date)
    payload = {}

    for block in raw:
        frame = block["frame"]
        frame_entry = {
            "start": block["start"].isoformat(),
            "end": block["end"].isoformat(),
            "start_lord": block["start_lord"],
            "levels": {}
        }

        for lvl_name, info in block["levels"].items():
            remaining_sec = int(info["remaining"].total_seconds())
            remaining_frac = info.get("remaining_fraction", None)

            frame_entry["levels"][lvl_name] = {
                "lord": info["lord"],
                "start": info["start"].isoformat(),
                "end": info["end"].isoformat(),
                "remaining_seconds": remaining_sec,
                "remaining_fraction": remaining_frac,
            }

        payload[frame] = frame_entry

    return payload


# ---------------------------------------------------------
# CLI-Einstieg
# ---------------------------------------------------------

if __name__ == "__main__":
    # Aufruf:
    #   python run_timedasha.py
    #   python run_timedasha.py 2025-12-03
    #   python run_timedasha.py 2025-12-03 --json
    #   python run_timedasha.py 2025-12-03 --debug
    #   python run_timedasha.py 2025-12-03 --json --debug

    args = sys.argv[1:]
    use_json = False
    use_debug = False
    date_arg = None

    for a in args:
        if a == "--json":
            use_json = True
        elif a == "--debug":
            use_debug = True
        else:
            date_arg = a

    if date_arg:
        year, month, day = map(int, date_arg.split("-"))
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()

    if use_json:
        payload = build_kp_keno_timedasha_payload(date)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        data = build_kp_keno_timedasha(date)
        print(f"KP-KENO-TIMEDASHA für Datum: {date}")

        for block in data:
            print("\n====", block["frame"], "====")
            frame_start_str = block["start"].strftime('%Y-%m-%d %H:%M')
            frame_end_str = block["end"].strftime('%Y-%m-%d %H:%M')
            print(f"Frame: {frame_start_str}  →  {frame_end_str}")
            print(f"Start-Lord (Moon/Lahiri): {block['start_lord']}")

            for lvl, info in block["levels"].items():
                # Endzeit ohne Sekunden
                end_str = info["end"].strftime("%Y-%m-%d %H:%M")

                # Restlaufzeit ohne Sekunden
                rem = info["remaining"]
                rem_days = rem.days
                rem_hours = rem.seconds // 3600
                rem_minutes = (rem.seconds // 60) % 60
                rem_str = f"{rem_days}d {rem_hours}h {rem_minutes}m"

                # Prozentwerte
                frac = info.get("remaining_fraction", 0.0)
                perc_str = f"{frac * 100:5.2f}%"

                print(
                    f"{lvl:6s}: {info['lord']:8s}  "
                    f"(bis {end_str}  | Rest: {rem_str}  | {perc_str})"
                )

    if use_debug:
        loc = get_wiesbaden_location()
        draw_time = get_draw_time(date)
        frames = {
            "YEAR": compute_year_frame(draw_time, loc),
            "MONTH": compute_month_frame(draw_time, loc),
            "WEEK": compute_week_frame(draw_time, loc),
        }
        print("\n--- DEBUG Moon/Lahiri pro Frame-Start ---")
        for fname, frame in frames.items():
            debug_print_moon_info(frame["start"], loc, fname)
