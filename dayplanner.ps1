$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = (Get-Command python -ErrorAction SilentlyContinue).Source }
if (-not $Python) { Write-Error "Python was not found. Create .venv or install Python."; exit 1 }
Push-Location $ProjectRoot
& $Python -m planner day @args
$ExitCode = $LASTEXITCODE
Pop-Location
exit $ExitCode
