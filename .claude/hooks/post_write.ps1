# post_write.ps1
# Runs after every Write or Edit tool call.
# Checks Python syntax and scans for secret leaks.

try {
    $rawInput = $input | Out-String
    $toolInput = $rawInput | ConvertFrom-Json -ErrorAction Stop
    $filePath = $toolInput.file_path
} catch { exit 0 }

if (-not $filePath -or -not (Test-Path $filePath)) { exit 0 }

$ext = [System.IO.Path]::GetExtension($filePath).ToLower()
$fileName = [System.IO.Path]::GetFileName($filePath)

# Python syntax check
if ($ext -eq ".py") {
    $result = python -m py_compile $filePath 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Output ""
        Write-Output "❌ PYTHON SYNTAX ERROR in $fileName"
        Write-Output "$result"
        Write-Output "Fix before proceeding."
        exit 1
    } else {
        Write-Output "✅ Python syntax OK: $fileName"
    }
}

# Secret leak check
$content = Get-Content $filePath -Raw -ErrorAction SilentlyContinue
if ($content) {
    $patterns = @{
        "Google API Key" = "AIza[0-9A-Za-z-_]{35}"
        "Razorpay Key"   = "rzp_(live|test)_[A-Za-z0-9]{14}"
    }
    foreach ($name in $patterns.Keys) {
        if ($content -match $patterns[$name]) {
            Write-Output "🚨 SECRET LEAK in $fileName ($name). Use env vars instead."
            exit 1
        }
    }
}

if ($fileName -eq ".env") {
    Write-Output "⚠️  .env written. Confirm it is in .gitignore."
}

exit 0
