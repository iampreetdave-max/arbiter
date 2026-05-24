# git_verify.ps1
# Git Agent helper script — commit and push with verification.
# NOTE: Prefer using GitHub MCP (mcp__github-personal__push_files) over this script.
# Use this only as a fallback for local git operations.

param(
    [string]$Message = "",
    [string]$Branch = "main"
)

$base = "C:\Users\PREET\OneDrive\Desktop\HACKATHON"
Set-Location $base

Write-Output "ARBITER GIT AGENT"

if (-not (Test-Path "$base\.git")) {
    git init; git branch -M main
    git remote add origin https://github.com/iampreetdave-max/arbiter.git
}

$status = git status --porcelain 2>&1
if (-not $status) {
    Write-Output "✅ Nothing to commit."
    exit 0
}

git status --short
git add .

if (-not $Message) {
    $Message = "chore: Arbiter build session $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}

git commit -m $Message
if ($LASTEXITCODE -ne 0) { Write-Output "❌ Commit failed."; exit 1 }

$hash = git rev-parse --short HEAD
git push origin $Branch 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Output "✅ PUSHED: $hash — $Message"
} else {
    git push --set-upstream origin $Branch 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Output "✅ PUSHED: $hash" }
    else { Write-Output "❌ Push failed. Check remote or use GitHub MCP instead."; exit 1 }
}
