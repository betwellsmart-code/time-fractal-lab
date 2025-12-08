# ===========================================================
# build.ps1 – Zentrales Build- & Doku-Aktualisierungssystem
# Saham-Lab / KP-KENO-TIMEDASHA
# ===========================================================

$base = "C:\Users\Nomen\Documents\Sandbox\kp_keno_timedasha"
$docs = "$base\docs"
$versionFile = "$docs\CHANGELOG.md"
$todoFile = "$docs\TODO_MASTERLIST.md"
$toolsFile = "$docs\TOOLS_OVERVIEW.md"
$moduleMapFile = "$docs\MODULE_MAP.md"

Write-Host "=== SAHAM-LAB BUILD START ===" -ForegroundColor Cyan

# -----------------------------------------------------------
# 1) AUTOMATISCHES TOOL-VERZEICHNIS UPDATE
# -----------------------------------------------------------
Write-Host "→ Aktualisiere TOOL OVERVIEW..." -ForegroundColor Yellow

$toolList = @("# TOOL OVERVIEW", "", "Automatisch generiert am $(Get-Date)", "")

Get-ChildItem -Path $base -Filter *.py -Recurse |
    ForEach-Object {
        $rel = $_.FullName.Replace($base, "")
        $toolList += "## $($_.Name)"
        $toolList += "Pfad: $rel"
        $toolList += ""
    }

$toolList | Set-Content -Encoding UTF8 $toolsFile


# -----------------------------------------------------------
# 2) AUTOMATISIERTE MODULE_MAP (Dateisystem-Snapshot)
# -----------------------------------------------------------
Write-Host "→ Aktualisiere MODULE MAP..." -ForegroundColor Yellow

$map = @("# MODULE MAP", "", "Struktur automatisch generiert am $(Get-Date)", "")

function Build-Tree($path, $indent="") {
    Get-ChildItem $path | ForEach-Object {
        $map += "$indent- $($_.Name)"
        if ($_.PSIsContainer) {
            Build-Tree $_.FullName ("$indent  ")
        }
    }
}

Build-Tree $base
$map | Set-Content -Encoding UTF8 $moduleMapFile


# -----------------------------------------------------------
# 3) TODO LISTE SYNCEN: Abgehakte Tasks nach unten verschieben
# -----------------------------------------------------------
Write-Host "→ Sortiere TODO-Liste..." -ForegroundColor Yellow

$todoLines = Get-Content $todoFile
$open = $todoLines | Where-Object { $_ -match "^\[ \]" }
$done = $todoLines | Where-Object { $_ -match "^\[x\]" }

@("# TODO MASTERLIST", "",
  "Offene Aufgaben:", $open, "",
  "Erledigt:", $done
) | Set-Content -Encoding UTF8 $todoFile


# -----------------------------------------------------------
# 4) CHANGELOG AUTOMATISCH ERWEITERN
# -----------------------------------------------------------
Write-Host "→ Aktualisiere CHANGELOG..." -ForegroundColor Yellow

$timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm")
$entry = "Auto-Build am $timestamp — Docs aktualisiert."

Add-Content -Encoding UTF8 $versionFile "`n$entry"


# -----------------------------------------------------------
# 5) SMOKE TEST – TimeDasha ausführen
# -----------------------------------------------------------
Write-Host "→ Führe TimeDasha Smoke-Test aus..." -ForegroundColor Yellow

try {
    python "$base\run_timedasha.py" --json | Out-Null
    Write-Host "Smoke-Test erfolgreich." -ForegroundColor Green
} catch {
    Write-Host "Fehler im Smoke-Test!" -ForegroundColor Red
}


# -----------------------------------------------------------
# 6) BUILD ABSCHLUSS
# -----------------------------------------------------------
Write-Host "=== BUILD COMPLETED ===" -ForegroundColor Green
