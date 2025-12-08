import os
import datetime
from run_timedasha import build_kp_keno_timedasha

# ---------------------------------------------------------
# Speicherort für das Logbuch
# ---------------------------------------------------------

def get_log_path():
    folder = os.path.join(
        os.path.expanduser("~"),
        "Documents",
        "Sandbox",
        "kp_keno_timedasha",
    )
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "KENO_TIMEDASHA_LOGBOOK.txt")


# ---------------------------------------------------------
# Formatierte Ausgabe pro Ebene
# ---------------------------------------------------------

def format_level(name, info):
    end_str = info["end"].strftime("%Y-%m-%d %H:%M")

    rem = info["remaining"]
    rem_days = rem.days
    rem_hours = rem.seconds // 3600
    rem_minutes = (rem.seconds // 60) % 60
    rem_str = f"{rem_days}d {rem_hours}h {rem_minutes}m"

    perc = info.get("remaining_fraction", 0.0)
    perc_str = f"{perc * 100:5.2f}%"

    return f"{name:6s}: {info['lord']:8s} | End: {end_str} | Rest: {rem_str} | {perc_str}"


# ---------------------------------------------------------
# Einen kompletten Eintrag erzeugen
# ---------------------------------------------------------

def build_log_entry(date):
    data = build_kp_keno_timedasha(date)

    out = []
    out.append("=" * 40)
    out.append(f"DATE: {date.isoformat()}")
    out.append("=" * 40)
    out.append("")

    for block in data:
        frame = block["frame"]
        frame_start = block["start"].strftime("%Y-%m-%d %H:%M")
        frame_end = block["end"].strftime("%Y-%m-%d %H:%M")

        out.append(f"---- {frame} FRAME ----")
        out.append(f"Start-Lord: {block['start_lord']}")
        out.append(f"Frame: {frame_start} → {frame_end}")
        out.append("")

        for lvl, info in block["levels"].items():
            out.append(format_level(lvl, info))

        out.append("")

    out.append("-" * 40)
    out.append("")

    return "\n".join(out)


# ---------------------------------------------------------
# Speichern im Textlog
# ---------------------------------------------------------

def append_log_entry(date):
    entry = build_log_entry(date)
    path = get_log_path()

    with open(path, "a", encoding="utf-8") as f:
        f.write(entry)

    return path


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]

    if args:
        y, m, d = map(int, args[0].split("-"))
        date = datetime.date(y, m, d)
    else:
        date = datetime.date.today()

    path = append_log_entry(date)
    print(f"Eintrag gespeichert in:\n{path}")
