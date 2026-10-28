$PlannerRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Invoke-ShanmugaPlanner {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("study", "day")]
        [string]$Area,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    $python = Join-Path $PlannerRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $python)) {
        $python = (Get-Command python -ErrorAction SilentlyContinue).Source
    }

    if (-not $python) {
        Write-Error "Python was not found. Create .venv or install Python."
        return 1
    }

    Push-Location $PlannerRoot
    try {
        & $python -m planner $Area @Arguments
        return $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}

function study-planner {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    return Invoke-ShanmugaPlanner -Area study @Arguments
}

function day-planner {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    return Invoke-ShanmugaPlanner -Area day @Arguments
}

function planner {
    param(
        [Parameter(Position = 0)]
        [string]$Command,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    if ([string]::IsNullOrWhiteSpace($Command) -or $Command -in @("help", "-h", "--help")) {
        Write-Host "PLANNER COMMANDS" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  study-planner help       Study tracker commands" -ForegroundColor White
        Write-Host "  day-planner help         Day planner commands" -ForegroundColor White
        Write-Host "  planner study ...        Run a study tracker command" -ForegroundColor White
        Write-Host "  planner day ...          Run a day planner command" -ForegroundColor White
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor DarkGray
        Write-Host "  study-planner subjects" -ForegroundColor DarkGray
        Write-Host "  day-planner plan" -ForegroundColor DarkGray
        return 0
    }

    switch ($Command.ToLowerInvariant()) {
        "study" { return Invoke-ShanmugaPlanner -Area study @Arguments }
        "day" { return Invoke-ShanmugaPlanner -Area day @Arguments }
        default {
            Write-Error "Unknown planner command '$Command'. Run 'planner help'."
            return 2
        }
    }
}
