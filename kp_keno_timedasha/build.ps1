# ===========================================================
# build.ps1 – Saham-Lab Build System (Professional Mode)
# Option B: Docs + Commit-Hash + Auto-Versioning + Auto-Commit
# ===========================================================

$base      = "C:\Users\Nomen\Documents\Sandbox\kp_keno_timedasha"
$docs      = "$base\docs"
$versionFile = "$docs\CHANGELOG.md"
$toolsFile   = "$docs\TOOLS_OVERVIEW.md"
$moduleMap   = "$docs\MODULE_MAP.md"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$buildID   = "build-" + (Get-Date -Format "yyyy-MM-dd-HH-mm")

Write-Host "=== SAHAM-LAB BUILD START (PRO MODE) ===" -ForegroundColor Cyan

# -----------------------------------------------------------
# 1) Commit-Hash laden
# -----------------------------------------------------------
$commit = git rev-parse --short HEAD 2>$null
if (-not $commit) { $commit = "NO-COMMIT" }

# -----------------------------------------------------------
# 2) TOOL OVERVIEW automatisch regenerieren
# -----------------------------------------------------------
Write-Host "→ Generiere TOOL OVERVIEW..." -ForegroundColor Yellow

$toolList = @("# TOOL OVERVIEW", 
              "",
              "Automatisch generiert am $timestamp",
              "Commit: $commit",
              "")

Get-ChildItem -Path $base -Filter *.py -Recurse |
    ForEach-Object {
        $rel = $_.FullName.Replace($base, "")
        $toolList += "## $($_.Name)"
        $toolList += "Pfad: $rel"
        $toolList += ""
    }

$toolList | Set-Content -Encoding UTF8 $toolsFile

# -----------------------------------------------------------
# 3) MODULE MAP neu bauen
# -----------------------------------------------------------
Write-Host "→ Generiere MODULE MAP..." -ForegroundColor Yellow

$map = @("# MODULE MAP", "",
         "Automatisch generiert am $timestamp",
         "Commit: $commit",
         "")

function Build-Tree($path, $indent="") {
    Get-ChildItem $path | ForEach-Object {
        $map += "$indent- $($_.Name)"
        if ($_.PSIsContainer) {
            Build-Tree $_.FullName ("$indent  ")
        }
    }
}

Build-Tree $base
$map | Set-Content -Encoding UTF8 $moduleMap

# -----------------------------------------------------------
# 4) Auto-Versioning in CHANGELOG
# -----------------------------------------------------------
Write-Host "→ Aktualisiere CHANGELOG..." -ForegroundColor Yellow

Add-Content -Encoding UTF8 $versionFile "`n### $buildID"
Add-Content -Encoding UTF8 $versionFile "Zeit: $timestamp"
Add-Content -Encoding UTF8 $versionFile "Commit: $commit"
Add-Content -Encoding UTF8 $versionFile ""

# -----------------------------------------------------------
# 5) Auto-Commit
# -----------------------------------------------------------
Write-Host "→ Führe Auto-Commit durch..." -ForegroundColor Yellow

git add . | Out-Null

try {
    git commit -m "Auto-Build $buildID (Commit: $commit)" | Out-Null
    Write-Host "Auto-Commit erfolgreich." -ForegroundColor Green
} catch {
    Write-Host "Keine Änderungen zum Commit." -ForegroundColor DarkYellow
}

Write-Host "=== BUILD COMPLETED (PRO MODE) ===" -ForegroundColor Green
Write-Host "Build-ID: $buildID" -ForegroundColor Cyan
Write-Host "Commit:  $commit"  -ForegroundColor Cyan
