param(
    [string]$OllamaPath = (Join-Path $env:USERPROFILE 'Documents\Codex\Tools\ollama-local\ollama.exe'),
    [int]$Port = 8011
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$logDirectory = Join-Path $projectRoot 'work'
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Falta el entorno Python. Ejecuta uv sync --frozen desde la carpeta del proyecto.'
}
New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null

try {
    $null = Invoke-RestMethod 'http://127.0.0.1:11435/api/version' -TimeoutSec 3
    Write-Host 'Ollama ya está en ejecución.'
} catch {
    if (-not (Test-Path -LiteralPath $OllamaPath)) {
        $installedOllama = Get-Command ollama -ErrorAction SilentlyContinue
        if (-not $installedOllama) { throw 'No se encuentra Ollama. Indica -OllamaPath con su ruta.' }
        $OllamaPath = $installedOllama.Source
    }
    $env:OLLAMA_HOST = '127.0.0.1:11435'
    $env:OLLAMA_MODELS = Join-Path (Split-Path -Parent $OllamaPath) 'models'
    $env:OLLAMA_MAX_LOADED_MODELS = '1'
    $env:OLLAMA_NUM_PARALLEL = '1'
    $env:OLLAMA_NO_CLOUD = '1'
    Start-Process -FilePath $OllamaPath -ArgumentList 'serve' -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDirectory 'ollama-output.log') `
        -RedirectStandardError (Join-Path $logDirectory 'ollama-error.log') | Out-Null
    Write-Host 'Ollama iniciado. Los modelos deben estar descargados previamente.'
}

$health = $null
try {
    $health = Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 3
} catch {}
if ($null -ne $health) {
    if ($health.scope -ne 'api') { throw 'El puerto lo está utilizando otra aplicación.' }
    Write-Host 'La API ya está en ejecución.'
} else {
    Start-Process -FilePath $pythonPath -WorkingDirectory $projectRoot -WindowStyle Hidden `
        -ArgumentList @('-m', 'uvicorn', 'study_rag.app:app', '--host', '127.0.0.1', '--port', "$Port") `
        -RedirectStandardOutput (Join-Path $logDirectory 'api-output.log') `
        -RedirectStandardError (Join-Path $logDirectory 'api-error.log') | Out-Null
    Write-Host 'API iniciada. Puede tardar unos segundos.'
}
Write-Host "Abre http://localhost:$Port y pulsa Comprobar conexión."
Write-Host 'La base de datos debe estar iniciada por separado en Docker Desktop.'
