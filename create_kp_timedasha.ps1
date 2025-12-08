$base = "C:\Users\Nomen\Documents\Sandbox\kp_keno_timedasha"

# Ordnerstruktur
$folders = @(
    $base,
    "$base\logs",
    "$base\agents",
    "$base\features",
    "$base\core",
    "$base\tests"
)

foreach ($f in $folders) {
    if (!(Test-Path $f)) {
        New-Item -ItemType Directory -Path $f | Out-Null
    }
}

# Dateien erzeugen
$files = @{
    "$base\run_timedasha.py"        = "# main timedasha runtime"
    "$base\timedasha_log.py"        = "# logging module"
    "$base\features\timedasha_features.py" = "# feature adapter"
    "$base\agents\agent1_patterncore.py"   = "# Agent 1 (PatternCore)"
    "$base\agents\agent4_pointdynamics.py" = "# Agent 4 (PointDynamics)"
    "$base\agents\agent5_temporalsynth.py" = "# Agent 5 (Temporal Synthesis)"
    "$base\core\__init__.py"              = ""
    "$base\README.md"                     = "# KP-KENO-TIMEDASHA Project"
}

foreach ($file in $files.Keys) {
    if (!(Test-Path $file)) {
        New-Item -ItemType File -Path $file -Value $files[$file] | Out-Null
    }
}

Write-Host "Projektstruktur erfolgreich erzeugt!" -ForegroundColor Green
