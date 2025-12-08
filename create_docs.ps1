# ===========================================================
# create_docs.ps1
# Erstellt das vollständige Dokumentationssystem für
# KP-KENO-TIMEDASHA
# ===========================================================

$base = "C:\Users\Nomen\Documents\Sandbox\kp_keno_timedasha"
$docs = "$base\docs"

# Ordner erzeugen
if (!(Test-Path $docs)) {
    New-Item -ItemType Directory -Path $docs | Out-Null
}

# Dateien + Grundinhalt definieren
$files = @{
    "$docs\TOOLS_OVERVIEW.md" = @"
# TOOL OVERVIEW

Übersicht über alle Tools und Python-Module im Projekt.

## run_timedasha.py
Pfad: /kp_keno_timedasha/
Beschreibung:
- Berechnet YEAR/MONTH/WEEK Dashas.
- Kern des KP-KENO-TIMEDASHA-Systems.

## timedasha_log.py
Pfad: /kp_keno_timedasha/
- Erstellt tägliche Logbucheinträge (4 Ebenen: MAHA/ANTAR/PRATY/SOOK).

## features/timedasha_features.py
- Transformiert Dashas in Feature-Vektoren für Agenten.
"@

    "$docs\MODULE_MAP.md" = @"
# MODULE MAP

Projektübersicht:

kp_keno_timedasha/
│   run_timedasha.py
│   timedasha_log.py
│   README.md
│
├── core/       -> Zentrale Kernmodule
├── features/   -> Feature-Adapter (für Agenten)
├── agents/     -> Agent 1, 4, 5
├── logs/       -> Ausgaben & Logfiles
└── tests/      -> Testskripte
"@

    "$docs\AGENTS_OVERVIEW.md" = @"
# AGENTS OVERVIEW

## Agent 1 – PatternCore
Status: IN PLANUNG
Zweck:
- Muster in Zeitlords + Keno-Daten erkennen

## Agent 4 – PointDynamics
Status: OFFEN
Zweck:
- Veränderungen und Übergänge von Zeitmustern analysieren

## Agent 5 – Temporal Synthesis
Status: OFFEN
Zweck:
- Erkenntnisse der anderen Agenten + Zeitdasha zu Metamustern verbinden
"@

    "$docs\DEVELOPMENT_NOTES.md" = @"
# DEVELOPMENT NOTES

Laufende Entwicklungsnotizen, technische Entscheidungen und Beobachtungen.

2025-12-04:
- SUB & PRANA im Tool intern behalten, aber für Menschen ausgeblendet.
- Feature-Adapter timedasha_features.py erstellt.

2025-12-05:
- Berlin-HoraAstro Dasha-Modul als nächster Hauptschritt geplant.
"@

    "$docs\TODO_MASTERLIST.md" = @"
# TODO MASTERLIST

[ ] Agent 1 Grundlogik einbauen
[ ] Agent 4 Grundlogik einbauen
[ ] Agent 5 Grundlogik einbauen
[ ] Berlin HoraAstro Modul starten
[ ] Dasha-Tool integrieren für Stunden/Minuten-Skalierung
[x] Projektstruktur per PS-Script erzeugt
"@

    "$docs\CHANGELOG.md" = @"
# CHANGELOG

## v0.1 – 2025-12-03
- YEAR/MONTH/WEEK TimeDasha implementiert.
- SUB/PRANA integriert.

## v0.2 – 2025-12-04
- Feature-Adapter hinzugefügt.
- Doku-System initialisiert.
"@
}

# Dateien erzeugen
foreach ($file in $files.Keys) {
    $value = $files[$file]
    Set-Content -Path $file -Value $value -Encoding UTF8
}

Write-Host "Dokumentationssystem erfolgreich erzeugt!" -ForegroundColor Green
