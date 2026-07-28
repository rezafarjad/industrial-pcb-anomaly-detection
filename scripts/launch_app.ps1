param(
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$requirements = Join-Path $projectRoot "requirements.txt"
$fingerprint = Join-Path $projectRoot ".venv\requirements.sha256"

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "First launch: creating the private Python environment..."
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $launcher) {
        & py -3 -m venv (Join-Path $projectRoot ".venv")
    }
    else {
        $launcher = Get-Command python -ErrorAction SilentlyContinue
        if ($null -eq $launcher) {
            throw "Python 3 is not installed. Install it from https://python.org and try again."
        }
        & python -m venv (Join-Path $projectRoot ".venv")
    }
}

$currentHash = (Get-FileHash -LiteralPath $requirements -Algorithm SHA256).Hash
$installedHash = ""
if (Test-Path -LiteralPath $fingerprint) {
    $installedHash = (Get-Content -LiteralPath $fingerprint -Raw).Trim()
}

if ($currentHash -ne $installedHash) {
    Write-Host "Installing or updating app dependencies..."
    & $venvPython -m pip install --disable-pip-version-check --upgrade pip
    & $venvPython -m pip install --disable-pip-version-check -r $requirements
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency installation failed."
    }
    Set-Content -LiteralPath $fingerprint -Value $currentHash -NoNewline
}

$listener = [System.Net.Sockets.TcpListener]::new(
    [System.Net.IPAddress]::Loopback,
    0
)
$listener.Start()
$port = ($listener.LocalEndpoint).Port
$listener.Stop()

Write-Host ""
Write-Host "Starting PCB Visual Inspector at http://localhost:$port"
Write-Host "Keep this window open while using the app. Press Ctrl+C to stop it."
Write-Host ""

$appPath = Join-Path $projectRoot "streamlit_app.py"
$serverLog = Join-Path $projectRoot ".venv\streamlit-server.log"
$serverErrorLog = Join-Path $projectRoot ".venv\streamlit-server-error.log"
$arguments = @(
    "-m",
    "streamlit",
    "run",
    "`"$appPath`"",
    "--server.port",
    $port,
    "--server.headless",
    "true",
    "--browser.gatherUsageStats",
    "false"
)
$server = Start-Process -FilePath $venvPython `
    -ArgumentList $arguments `
    -WorkingDirectory $projectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $serverLog `
    -RedirectStandardError $serverErrorLog `
    -PassThru

$url = "http://localhost:$port"
$healthy = $false
try {
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Milliseconds 500
        if ($server.HasExited) {
            break
        }
        try {
            $response = Invoke-WebRequest -Uri "$url/_stcore/health" `
                -UseBasicParsing `
                -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                $healthy = $true
                break
            }
        }
        catch {
            # The server is still starting.
        }
    }

    if (-not $healthy) {
        if (Test-Path -LiteralPath $serverErrorLog) {
            Get-Content -LiteralPath $serverErrorLog -Tail 30
        }
        throw "The local app server did not become ready."
    }

    if (-not $NoBrowser) {
        Start-Process $url
        Write-Host "The app is ready in your browser."
    }
    while (-not $server.HasExited) {
        Start-Sleep -Seconds 1
        $server.Refresh()
    }
}
finally {
    if (-not $server.HasExited) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    }
}
