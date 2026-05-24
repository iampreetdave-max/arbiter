# stop_guard.ps1
# Runs when Claude is about to stop.
# Enforces HANDOFF.md update, checks git status, scans for secrets.

$base = "C:\Users\PREET\OneDrive\Desktop\HACKATHON"
$handoff = "$base\HANDOFF.md"
$issues = @()

# 1. HANDOFF.md check
if (-not (Test-Path $handoff)) {
    $issues += "CRITICAL: HANDOFF.md missing. Create it before stopping."
} else {
    $ageMinutes = ((Get-Date) - (Get-Item $handoff).LastWriteTime).TotalMinutes
    if ($ageMinutes -gt 10) {
        $issues += "HANDOFF.md last updated $([math]::Round($ageMinutes)) min ago. Update it with: completed work, status, next steps, decisions."
    }
}

# 2. Git uncommitted check
try {
    $gitStatus = git -C $base status --porcelain 2>$null
    if ($gitStatus) {
        $count = ($gitStatus | Measure-Object).Count
        $issues += "GIT: $count file(s) uncommitted. Spawn Git Agent (GitHub MCP) to push before stopping."
    }
} catch {}

# 3. Secret leak scan
try {
    $patterns = @("AIza[0-9A-Za-z-_]{35}", "rzp_(live|test)_[A-Za-z0-9]{14}")
    foreach ($p in $patterns) {
        $hits = Get-ChildItem -Recurse -Path $base -Include "*.py","*.ts","*.tsx","*.js" -ErrorAction SilentlyContinue |
            Select-String -Pattern $p -ErrorAction SilentlyContinue
        if ($hits) { $issues += "SECRET LEAK in $($hits.Filename). Remove and rotate immediately." }
    }
} catch {}

# Output
if ($issues.Count -gt 0) {
    Write-Output ""
    Write-Output "╔══════════════════════════════════════════════╗"
    Write-Output "║    ARBITER SESSION GUARD — ACTION REQUIRED   ║"
    Write-Output "╚══════════════════════════════════════════════╝"
    foreach ($i in $issues) { Write-Output ""; Write-Output "⚠️  $i" }
    Write-Output ""
    exit 1
} else {
    Write-Output "✅ Session guard passed."
    exit 0
}
